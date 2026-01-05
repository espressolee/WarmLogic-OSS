from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import zipfile

from . import config as cfg
from .models import ArtifactRef, ProofManifest, RunManifest
from .utils import (
    ensure_dir,
    generate_run_id,
    get_git_commit,
    now_utc_iso,
    read_jsonl,
    sha256_file,
    validate_json,
    write_json,
)


class RunError(Exception):
    """Raised for fatal run failures."""


def _resolve(path_str: str, root: Path) -> Path:
    path = Path(path_str)
    if path.is_absolute() or path.exists():
        return path
    return root / path


def _build_govdec(run_id: str, verdict: str, witness_exists: bool, failed_axis: Optional[str]) -> Dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "decision_id": f"dec-{run_id}",
        "timestamp": now_utc_iso(),
        "verdict": verdict,
        "witness_path": {"exists": witness_exists, "failed_axis": failed_axis},
    }


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def execute_run(
    *,
    run_id: Optional[str],
    out_dir: Path,
    config_path: Path,
    events_path: Path,
    schemas_root: Path,
    ct_config_path: Optional[Path] = None,
    drift_config_path: Optional[Path] = None,
    cohort_id: Optional[str] = None,
    edition: Optional[str] = None,
    tag: Optional[str] = None,
    no_bundle: bool = False,
    dry_run: bool = False,
    enforce_evidence_refs: bool = False,
) -> Tuple[str, Path]:
    if not config_path.exists():
        raise RunError(f"config not found: {config_path}")
    if not events_path.exists():
        raise RunError(f"events not found: {events_path}")
    run_id = run_id or generate_run_id(cfg.DEFAULT_RUN_ID_PREFIX)
    run_dir = out_dir / run_id
    if not dry_run:
        ensure_dir(run_dir)

    # copy inputs
    if not dry_run:
        events_copy = run_dir / "event_log.jsonl"
        shutil.copy2(events_path, events_copy)
        config_copy = run_dir / Path(config_path).name
        shutil.copy2(config_path, config_copy)
        ct_copy = None
        drift_copy = None
        if ct_config_path:
            ct_copy = run_dir / Path(ct_config_path).name
            shutil.copy2(ct_config_path, ct_copy)
        if drift_config_path:
            drift_copy = run_dir / Path(drift_config_path).name
            shutil.copy2(drift_config_path, drift_copy)
    else:
        events_copy = events_path
        config_copy = config_path
        ct_copy = ct_config_path
        drift_copy = drift_config_path

    # derive govdec/decision/trigger rows
    events_data = read_jsonl(events_copy if events_copy.exists() else events_path)
    decisions: List[Dict[str, Any]] = []
    triggers: List[Dict[str, Any]] = []
    for idx, evt in enumerate(events_data):
        event_id = evt.get("event_id") or evt.get("id") or f"event-{idx+1}"
        evidence_refs = evt.get("evidence_refs") or evt.get("evidence_ref")
        if enforce_evidence_refs and (not evidence_refs):
            raise RunError(f"missing evidence_refs for event {event_id} (CHG-TEAM-A-003 enforcement)")
        decision = {
            "run_id": run_id,
            "event_id": event_id,
            "decision": "PASS",
            "timestamp": now_utc_iso(),
            "witness_path": {"exists": True, "failed_axis": None},
            "evidence_refs": evidence_refs or [],
        }
        decisions.append(decision)
        triggers.append(
            {
                "run_id": run_id,
                "event_id": event_id,
                "trigger": "ACT",
                "timestamp": decision["timestamp"],
                "axis": "AETC",
            }
        )

    govdec = _build_govdec(run_id, "PASS", True, None)

    # write outputs
    govdec_path = run_dir / "govdec.json"
    decision_log_path = run_dir / "decision_log.jsonl"
    trigger_events_path = run_dir / "trigger_events.jsonl"
    run_manifest_path = run_dir / "run_manifest.json"
    proof_manifest_path = run_dir / "proof_manifest.json"
    verify_report_path = run_dir / "verify_report.json"

    if not dry_run:
        write_json(govdec_path, govdec)
        _write_jsonl(decision_log_path, decisions)
        _write_jsonl(trigger_events_path, triggers)

    git_commit = get_git_commit()
    manifest = RunManifest(
        run_id=run_id,
        created_at=now_utc_iso(),
        config={
            "path": str(config_copy.relative_to(run_dir) if not dry_run else config_copy),
            "sha256": sha256_file(config_copy),
        },
        events={
            "path": str(events_copy.relative_to(run_dir) if not dry_run else events_copy),
            "sha256": sha256_file(events_copy),
        },
        ct_config={"path": str(ct_copy.relative_to(run_dir)), "sha256": sha256_file(ct_copy)} if ct_copy else None,
        drift_config={"path": str(drift_copy.relative_to(run_dir)), "sha256": sha256_file(drift_copy)} if drift_copy else None,
        cohort_id=cohort_id,
        edition=edition,
        tag=tag,
        git_commit=git_commit,
        status="SUCCESS" if not dry_run else "DRY_RUN",
        artifacts={
            "govdec": str(govdec_path.relative_to(run_dir)) if not dry_run else "govdec.json",
            "decision_log": str(decision_log_path.relative_to(run_dir)) if not dry_run else "decision_log.jsonl",
            "trigger_events": str(trigger_events_path.relative_to(run_dir)) if not dry_run else "trigger_events.jsonl",
            "proof_manifest": str(proof_manifest_path.relative_to(run_dir)),
            "verify_report": str(verify_report_path.relative_to(run_dir)),
        },
        meta={
            "sources": {
                "config": {"path": str(config_path), "sha256": sha256_file(config_path)},
                "events": {"path": str(events_path), "sha256": sha256_file(events_path)},
                "ct_config": {"path": str(ct_config_path), "sha256": sha256_file(ct_config_path)} if ct_config_path else None,
                "drift_config": {"path": str(drift_config_path), "sha256": sha256_file(drift_config_path)} if drift_config_path else None,
            }
        },
    )

    if not dry_run:
        if not no_bundle:
            bundle_dir = ensure_dir(run_dir / "bundle")
            bundle_path = bundle_dir / "osctl_bundle.zip"
        # manifest must include bundle path before hashing/writing
        if not no_bundle:
            manifest.artifacts["bundle"] = str(bundle_path.relative_to(run_dir))

        write_json(run_manifest_path, manifest.to_dict())

        artifacts = [
            ArtifactRef(path="run_manifest.json", sha256=sha256_file(run_manifest_path), type="manifest"),
            ArtifactRef(path="govdec.json", sha256=sha256_file(govdec_path), type="govdec"),
            ArtifactRef(path="decision_log.jsonl", sha256=sha256_file(decision_log_path), type="decision_log"),
            ArtifactRef(path="trigger_events.jsonl", sha256=sha256_file(trigger_events_path), type="trigger_events"),
            ArtifactRef(path=manifest.events["path"], sha256=manifest.events["sha256"], type="event_log"),
            ArtifactRef(path=manifest.config["path"], sha256=manifest.config["sha256"], type="config"),
        ]
        if manifest.ct_config:
            artifacts.append(ArtifactRef(path=manifest.ct_config["path"], sha256=manifest.ct_config["sha256"], type="ct_config"))
        if manifest.drift_config:
            artifacts.append(ArtifactRef(path=manifest.drift_config["path"], sha256=manifest.drift_config["sha256"], type="drift_config"))

        proof_manifest = ProofManifest(
            run_id=run_id,
            created_at=now_utc_iso(),
            artifacts=artifacts,
            verification={"status": "PENDING", "details": "generated by osctl run"},
        )
        write_json(proof_manifest_path, proof_manifest.to_dict())

        if not no_bundle:
            with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for p in [run_manifest_path, govdec_path, decision_log_path, trigger_events_path, proof_manifest_path, events_copy, config_copy]:
                    zf.write(p, arcname=p.name)

        write_json(verify_report_path, {"run_id": run_id, "overall_status": "PENDING", "checks": []})

        run_schema = schemas_root / "run_manifest.schema.json"
        proof_schema = schemas_root / "proof_manifest.schema.json"
        run_errors = validate_json(manifest.to_dict(), run_schema) if run_schema.exists() else []
        proof_errors = validate_json(proof_manifest.to_dict(), proof_schema) if proof_schema.exists() else []
        if run_errors or proof_errors:
            raise RunError(f"schema validation failed: run={run_errors} proof={proof_errors}")

    return run_id, run_dir


def run_command(args) -> int:
    try:
        enforce_evidence = bool(args.tag and "advisory" in args.tag.lower())
        run_id, run_dir = execute_run(
            run_id=args.run_id,
            out_dir=Path(args.out_dir),
            config_path=_resolve(args.config, Path(args.config_root)),
            events_path=_resolve(args.events, Path(args.config_root)),
            ct_config_path=_resolve(args.ct_config, Path(args.config_root)) if args.ct_config else None,
            drift_config_path=_resolve(args.drift_config, Path(args.config_root)) if args.drift_config else None,
            schemas_root=Path(args.schemas_root),
            cohort_id=args.cohort_id,
            edition=args.edition,
            tag=args.tag,
            no_bundle=args.no_bundle,
            dry_run=args.dry_run,
            enforce_evidence_refs=enforce_evidence,
        )
        summary = {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "status": "SUCCESS" if not args.dry_run else "DRY_RUN",
        }
        print(json.dumps(summary))
        return 0
    except RunError as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}))
        return 2
    except Exception as exc:  # unexpected
        print(json.dumps({"status": "ERROR", "error": str(exc)}))
        return 2
