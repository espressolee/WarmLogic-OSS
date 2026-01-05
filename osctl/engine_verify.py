from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema

from .models import ProofManifest, RunManifest
from .utils import load_schema, read_json, read_jsonl, sha256_file, validate_json, write_json


class VerifyError(Exception):
    """Raised for verify failures."""


def _default_run_dir(run_id: str, out_dir: Path) -> Path:
    return out_dir / run_id


def _add_check(checks: List[Dict[str, Any]], name: str, ok: bool, reason: Optional[str] = None) -> None:
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", **({"reason": reason} if reason else {})})


def verify_command(args) -> int:
    run_dir = Path(args.run_dir) if args.run_dir else _default_run_dir(args.run_id, Path(args.out_dir))
    proof_path = Path(args.proof_manifest) if args.proof_manifest else run_dir / "proof_manifest.json"
    run_manifest_path = run_dir / "run_manifest.json"
    govdec_path = run_dir / "govdec.json"
    decision_log_path = run_dir / "decision_log.jsonl"
    trigger_events_path = run_dir / "trigger_events.jsonl"

    if not proof_path.exists():
        print(json.dumps({"status": "ERROR", "error": f"missing proof manifest: {proof_path}"}))
        return 2

    checks: List[Dict[str, Any]] = []
    errors: List[str] = []
    try:
        proof_manifest = ProofManifest.from_dict(read_json(proof_path))
        run_manifest = RunManifest.from_dict(read_json(run_manifest_path))

        # schema validation (best-effort)
        schemas_root = Path(args.schemas_root)
        for label, obj, filename in [
            ("run_manifest_schema", run_manifest.to_dict(), "run_manifest.schema.json"),
            ("proof_manifest_schema", proof_manifest.to_dict(), "proof_manifest.schema.json"),
        ]:
            schema_file = schemas_root / filename
            errs = validate_json(obj, schema_file) if schema_file.exists() else []
            if errs:
                _add_check(checks, label, False, "; ".join(errs))
            else:
                _add_check(checks, label, True)

        # decision_log schema validation (JSONL)
        decision_schema = load_schema(schemas_root / "decision_log.schema.json")
        if decision_schema and decision_log_path.exists():
            validator = jsonschema.Draft7Validator(decision_schema)
            errs: List[str] = []
            for idx, row in enumerate(read_jsonl(decision_log_path)):
                errs.extend([f"line {idx+1}: {e.message} at {list(e.path)}" for e in validator.iter_errors(row)])
            _add_check(checks, "decision_log_schema", len(errs) == 0, "; ".join(errs) if errs else None)
            errors.extend(errs)

        # trigger_events schema validation (JSONL)
        trigger_schema = load_schema(schemas_root / "trigger_event.schema.json")
        if trigger_schema and trigger_events_path.exists():
            validator = jsonschema.Draft7Validator(trigger_schema)
            errs: List[str] = []
            for idx, row in enumerate(read_jsonl(trigger_events_path)):
                errs.extend([f"line {idx+1}: {e.message} at {list(e.path)}" for e in validator.iter_errors(row)])
            _add_check(checks, "trigger_events_schema", len(errs) == 0, "; ".join(errs) if errs else None)
            errors.extend(errs)

        # artifact existence and hash checks
        for artifact in proof_manifest.artifacts:
            artifact_path = run_dir / artifact.path
            if not artifact_path.exists():
                _add_check(checks, f"artifact_exists:{artifact.path}", False, "missing")
                errors.append(f"missing {artifact.path}")
                continue
            current_hash = sha256_file(artifact_path)
            if current_hash != artifact.sha256:
                _add_check(checks, f"artifact_hash:{artifact.path}", False, f"expected {artifact.sha256}, got {current_hash}")
                errors.append(f"hash mismatch {artifact.path}")
            else:
                _add_check(checks, f"artifact_hash:{artifact.path}", True)

        # minimal invariants
        if govdec_path.exists():
            govdec = read_json(govdec_path)
            wp = govdec.get("witness_path", {})
            ok = isinstance(wp, dict) and "exists" in wp
            _add_check(checks, "govdec_witness_path_present", ok, None if ok else "witness_path missing")
        else:
            _add_check(checks, "govdec_present", False, "govdec missing")
            errors.append("govdec missing")

        # decision_log presence
        _add_check(checks, "decision_log_present", decision_log_path.exists(), None if decision_log_path.exists() else "decision_log missing")
        _add_check(checks, "trigger_events_present", trigger_events_path.exists(), None if trigger_events_path.exists() else "trigger_events missing")

        overall = "PASS" if not errors else "FAIL"
        verify_report = {"run_id": args.run_id, "overall_status": overall, "checks": checks}
        write_json(run_dir / "verify_report.json", verify_report)
        print(json.dumps({"status": overall, "run_id": args.run_id}))
        return 0 if overall == "PASS" else 1
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}))
        return 2
