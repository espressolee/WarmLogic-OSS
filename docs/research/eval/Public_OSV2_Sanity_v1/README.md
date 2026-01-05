# Public OS v2 Sanity (Source, v1)

Purpose: define a minimal, fully reproducible OS v2 sanity run using synthetic data only. This directory is the SSOT for the public bundle exported to WarmLogic-OSS.

## Contents
- `config_osv2_sanity.yaml` — toy OS v2 runtime config (synthetic).
- `event_log_sanity.jsonl` — synthetic event log for a few decisions.
- `expected_results.json` — expected verify summary at a high level.

## How to export
Use `scripts/release/export_public_osv2_sanity_bundle.sh` from repo root. By default it copies these files to `../WarmLogic-OSS/docs/research/eval/Public_OSV2_Sanity_v1/` and records the source commit in `SOURCE_COMMIT.txt`.

Example:
```bash
scripts/release/export_public_osv2_sanity_bundle.sh ../WarmLogic-OSS/docs/research/eval/Public_OSV2_Sanity_v1
```

## How to run (main repo)
From repo root:
```bash
RUN_ID=OSV2_PUBLIC_SANITY_V1
OUT=out/public_osv2_sanity

python -m warm_logic_core.osctl.cli run \
  --config docs/research/eval/Public_OSV2_Sanity_Source_v1/config_osv2_sanity.yaml \
  --events docs/research/eval/Public_OSV2_Sanity_Source_v1/event_log_sanity.jsonl \
  --out-dir "$OUT" \
  --schemas-root docs/papers/reflective_os/os_v2/json_schemas \
  --run-id "$RUN_ID" --no-bundle

python -m warm_logic_core.osctl.cli verify \
  --run-id "$RUN_ID" \
  --out-dir "$OUT" \
  --schemas-root docs/papers/reflective_os/os_v2/json_schemas
```

## Notes
- Data is synthetic; safe to publish.
- Keep this directory aligned with OS v2 schemas. Update and re-export when schemas change.
- Expected results are approximate; adjust if rules/config change materially.
