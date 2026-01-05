from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, send_from_directory


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                rows.append({"raw": line})
    return rows


def list_runs(run_root: Path, limit: int = 50) -> List[Dict[str, Any]]:
    items = []
    for run_dir in sorted(run_root.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        manifest = run_dir / "run_manifest.json"
        verify = run_dir / "verify_report.json"
        if not manifest.exists():
            continue
        man = load_json(manifest)
        status = "UNKNOWN"
        if verify.exists():
            try:
                status = load_json(verify).get("overall_status", "UNKNOWN")
            except Exception:
                status = "UNKNOWN"
        items.append(
            {
                "run_id": man.get("run_id"),
                "status": status,
                "created_at": man.get("created_at"),
                "tag": man.get("tag"),
                "cohort_id": man.get("cohort_id"),
                "artifacts": man.get("artifacts", {}),
            }
        )
        if len(items) >= limit:
            break
    return items


def create_app(run_root: Path, ce_ledger: Path) -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="")

    @app.get("/api/v1/runs")
    def get_runs():
        items = list_runs(run_root)
        return jsonify({"items": items, "total": len(items)})

    @app.get("/api/v1/runs/<run_id>")
    def get_run(run_id: str):
        run_dir = run_root / run_id
        manifest = load_json(run_dir / "run_manifest.json")
        govdec = load_json(run_dir / "govdec.json")
        proof = load_json(run_dir / "proof_manifest.json")
        verify = load_json(run_dir / "verify_report.json") if (run_dir / "verify_report.json").exists() else {}
        return jsonify(
            {
                "run_id": run_id,
                "status": verify.get("overall_status", "UNKNOWN"),
                "created_at": manifest.get("created_at"),
                "govdec": govdec,
                "artifacts": manifest.get("artifacts", {}),
                "proof_manifest": proof,
                "verify_report": verify,
            }
        )

    @app.get("/api/v1/runs/<run_id>/decisions")
    def get_decisions(run_id: str):
        dec_path = run_root / run_id / "decision_log.jsonl"
        items = load_jsonl(dec_path) if dec_path.exists() else []
        return jsonify({"items": items, "total": len(items)})

    @app.get("/api/v1/runs/<run_id>/verify")
    def get_verify(run_id: str):
        ver_path = run_root / run_id / "verify_report.json"
        verify = load_json(ver_path) if ver_path.exists() else {}
        return jsonify({"items": [verify] if verify else []})

    @app.get("/api/v1/ce-ledger")
    def get_ce():
        items = load_jsonl(ce_ledger) if ce_ledger.exists() else []
        return jsonify({"items": items, "total": len(items)})

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    return app


def main():
    parser = argparse.ArgumentParser(description="WarmLogic console backend (minimal)")
    parser.add_argument("--run-root", default="out/osctl_runs", help="Path to osctl runs")
    parser.add_argument("--ce-ledger", default="ledger/pilots/TeamA/CE_Ledger_v1.jsonl", help="Path to CE ledger JSONL")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    app = create_app(Path(args.run_root), Path(args.ce_ledger))
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
