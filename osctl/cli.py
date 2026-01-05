from __future__ import annotations

import argparse
from pathlib import Path

from . import config as cfg
from .engine_replay import replay_command
from .engine_run import run_command
from .engine_verify import verify_command


def build_parser() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--out-dir", default=str(cfg.DEFAULT_OUT_DIR), help="Root output dir (default: OSCTL_OUT_DIR or out/osctl_runs)")
    parent.add_argument("--config-root", default=str(cfg.DEFAULT_CONFIG_ROOT), help="Root for resolving relative config paths")
    parent.add_argument("--schemas-root", default=str(cfg.DEFAULT_SCHEMAS_ROOT), help="Root for JSON schemas")
    parent.add_argument("--log-level", default="info", choices=cfg.LOG_LEVELS, help="Log level")
    parent.add_argument("--dry-run", action="store_true", help="Validate inputs but do not write files")

    parser = argparse.ArgumentParser(description="WarmLogic osctl run/replay/verify CLI", parents=[parent])

    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Execute a new run and emit artifacts", parents=[parent])
    run_p.add_argument("--config", required=True, help="Runtime config (YAML/JSON)")
    run_p.add_argument("--events", required=True, help="Event log (JSONL)")
    run_p.add_argument("--ct-config", help="CT-safe config (optional)")
    run_p.add_argument("--drift-config", help="Drift/Bounds config (optional)")
    run_p.add_argument("--run-id", help="Optional run id (default: generated)")
    run_p.add_argument("--cohort-id", help="Cohort identifier")
    run_p.add_argument("--edition", help="Edition identifier")
    run_p.add_argument("--tag", help="Tag for this run")
    run_p.add_argument("--no-bundle", action="store_true", help="Skip bundle zip creation")
    run_p.set_defaults(func=run_command)

    replay_p = sub.add_parser("replay", help="Replay an existing run", parents=[parent])
    replay_p.add_argument("--run-id", required=True, help="Run id to replay")
    replay_p.add_argument("--manifest", help="Path to run_manifest.json (defaults to out/<run_id>/run_manifest.json)")
    replay_p.add_argument("--no-bundle", action="store_true", help="Skip bundle zip creation")
    replay_p.set_defaults(func=replay_command)

    verify_p = sub.add_parser("verify", help="Verify artifacts for a run_id", parents=[parent])
    verify_p.add_argument("--run-id", required=True, help="Run id to verify")
    verify_p.add_argument("--run-dir", help="Explicit run directory (default: out/<run_id>)")
    verify_p.add_argument("--proof-manifest", help="Override proof_manifest path")
    verify_p.set_defaults(func=verify_command)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
