#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="$ROOT_DIR"
OUT_DIR="$ROOT_DIR/out/osctl_runs"
mkdir -p "$OUT_DIR"
python -m osctl.cli run \
  --config "$ROOT_DIR/examples/os_v2_toy/os_v2_config.yaml" \
  --events "$ROOT_DIR/examples/os_v2_toy/event_log_sample.jsonl" \
  --out-dir "$OUT_DIR" \
  --schemas-root "$ROOT_DIR/examples/os_v2_toy/json_schemas" \
  --run-id OSS_TOY_RUN --no-bundle
python -m osctl.cli verify \
  --run-id OSS_TOY_RUN \
  --out-dir "$OUT_DIR" \
  --schemas-root "$ROOT_DIR/examples/os_v2_toy/json_schemas"
