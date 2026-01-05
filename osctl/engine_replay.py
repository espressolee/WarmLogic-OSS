from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

from .engine_run import execute_run
from .models import RunManifest
from .utils import ensure_dir, read_json, sha256_file, write_json


class ReplayError(Exception):
    """Raised for replay failures."""


def _default_manifest_path(run_id: str, out_dir: Path) -> Path:
    return out_dir / run_id / "run_manifest.json"


def replay_command(args) -> int:
    manifest_path = Path(args.manifest) if args.manifest else _default_manifest_path(args.run_id, Path(args.out_dir))
    if not manifest_path.exists():
        print(json.dumps({"status": "ERROR", "error": f"manifest not found: {manifest_path}"}))
        return 2
    try:
        manifest = RunManifest.from_dict(read_json(manifest_path))
        base_dir = manifest_path.parent
        replay_dir = ensure_dir(base_dir / "replay")
        replay_run_id = f"{manifest.run_id}_replay"

        original_config = Path(manifest.config["path"])
        original_events = Path(manifest.events["path"])
        if not original_config.is_absolute():
            original_config = (base_dir / original_config).resolve()
        if not original_events.is_absolute():
            original_events = (base_dir / original_events).resolve()

        ct_resolved = None
        if manifest.ct_config:
            ct_resolved = Path(manifest.ct_config["path"])
            if not ct_resolved.is_absolute():
                ct_resolved = (base_dir / ct_resolved).resolve()
        drift_resolved = None
        if manifest.drift_config:
            drift_resolved = Path(manifest.drift_config["path"])
            if not drift_resolved.is_absolute():
                drift_resolved = (base_dir / drift_resolved).resolve()

        new_run_id, new_run_dir = execute_run(
            run_id=replay_run_id,
            out_dir=replay_dir,
            config_path=original_config,
            events_path=original_events,
            schemas_root=Path(args.schemas_root),
            cohort_id=manifest.cohort_id,
            edition=manifest.edition,
            tag=manifest.tag,
            no_bundle=args.no_bundle,
            dry_run=args.dry_run,
            ct_config_path=ct_resolved,
            drift_config_path=drift_resolved,
        )

        mismatches: List[str] = []
        if manifest.config.get("sha256") and manifest.config["sha256"] != sha256_file(original_config):
            mismatches.append("config_sha_mismatch")
        if manifest.events.get("sha256") and manifest.events["sha256"] != sha256_file(original_events):
            mismatches.append("events_sha_mismatch")

        summary = {
            "run_id": new_run_id,
            "replay_dir": str(new_run_dir),
            "status": "OK" if not mismatches else "REPLAY_MISMATCH",
            "mismatches": mismatches,
        }
        write_json(new_run_dir / "verify_report.json", {"run_id": new_run_id, "overall_status": summary["status"], "checks": mismatches})
        print(json.dumps(summary))
        return 0 if not mismatches else 1
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}))
        return 2
