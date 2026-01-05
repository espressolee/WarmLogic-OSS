"""Minimal mock API server to serve run/ledger data for console smoke tests."""
from __future__ import annotations

import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, List


def load_runs(run_root: Path, limit: int = 10) -> List[Dict[str, Any]]:
    items = []
    for run_dir in sorted(run_root.iterdir(), reverse=True):
        if not run_dir.is_dir():
            continue
        manifest = run_dir / "run_manifest.json"
        verify = run_dir / "verify_report.json"
        if not manifest.exists():
            continue
        try:
            man = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            continue
        status = "UNKNOWN"
        if verify.exists():
            try:
                status = json.loads(verify.read_text(encoding="utf-8")).get("overall_status", "UNKNOWN")
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


def load_run_detail(run_root: Path, run_id: str) -> Dict[str, Any]:
    run_dir = run_root / run_id
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    govdec = json.loads((run_dir / "govdec.json").read_text(encoding="utf-8"))
    proof = json.loads((run_dir / "proof_manifest.json").read_text(encoding="utf-8"))
    verify = json.loads((run_dir / "verify_report.json").read_text(encoding="utf-8"))
    return {
        "run_id": run_id,
        "status": verify.get("overall_status", "UNKNOWN"),
        "created_at": manifest.get("created_at"),
        "govdec": govdec,
        "artifacts": manifest.get("artifacts", {}),
        "proof_manifest": proof,
        "verify_report": verify,
    }


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


class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, run_root: Path, ce_ledger: Path, **kwargs):
        self.run_root = run_root
        self.ce_ledger = ce_ledger
        super().__init__(*args, **kwargs)

    def _send(self, code: int, payload: Any) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        path = self.path
        try:
            if path == "/api/v1/runs":
                items = load_runs(self.run_root)
                return self._send(200, {"items": items, "total": len(items)})
            if path.startswith("/api/v1/runs/"):
                parts = path.split("/")
                if len(parts) >= 5 and parts[4] == "decisions":
                    run_id = parts[3]
                    dec_path = self.run_root / run_id / "decision_log.jsonl"
                    items = load_jsonl(dec_path) if dec_path.exists() else []
                    return self._send(200, {"items": items, "total": len(items)})
                if len(parts) >= 5 and parts[4] == "verify":
                    run_id = parts[3]
                    ver_path = self.run_root / run_id / "verify_report.json"
                    verify = json.loads(ver_path.read_text(encoding="utf-8")) if ver_path.exists() else {}
                    return self._send(200, {"items": [verify] if verify else []})
                run_id = parts[3]
                detail = load_run_detail(self.run_root, run_id)
                return self._send(200, detail)
            if path == "/api/v1/ce-ledger":
                items = load_jsonl(self.ce_ledger) if self.ce_ledger.exists() else []
                return self._send(200, {"items": items, "total": len(items)})
        except Exception as exc:  # pragma: no cover - best-effort
            return self._send(500, {"error": str(exc)})
        self._send(404, {"error": "not found"})


def serve(run_root: Path, ce_ledger: Path, port: int) -> None:
    def handler(*args, **kwargs):
        return Handler(*args, run_root=run_root, ce_ledger=ce_ledger, **kwargs)

    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"Serving mock API on 0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock console API server")
    parser.add_argument("--run-root", default="out/osctl_runs", help="osctl run root dir")
    parser.add_argument("--ce-ledger", default="ledger/pilots/TeamA/CE_Ledger_v1.jsonl", help="CE ledger path")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    serve(Path(args.run_root), Path(args.ce_ledger), args.port)
