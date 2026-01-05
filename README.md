<<<<<<< HEAD
# WarmLogic-OSS
Evidence-centric AI governance tools: PASS / ACT / CT-safe evaluation harness, specs, and examples (public subset).
=======
# WarmLogic OSS Runtime (Demo)

This repository is a **public, self-contained subset** of the WarmLogic program. It ships:
- A toy **osctl** runtime (run / verify / replay) for a small, synthetic workload.
- A minimal **example workload** (OS v2–style event log + config + schemas).
- A lightweight **console** to browse runs, decisions, counterexamples, and cohort status.
- Documentation and scripts for reproducible experiments.

**Goal:** make governance/evidence/replayability tangible without exposing private pilots or sensitive artifacts. This is *not* a production deployment or full WarmLogic program dump.

---

## Components

### 1) osctl (toy runtime CLI)
- Location: `osctl/`
- Commands (v0.1):
  - `osctl run` — ingest event log + config → `run_manifest`, `govdec`, `decision_log`.
  - `osctl verify` — schema/invariant checks (witness-path presence, bundle hashes).
  - `osctl replay` — re-run using recorded manifest to demonstrate replayability.
- See `docs/Quickstart_OSCTL_v1.md` for full CLI examples.

### 2) Example workload: `os_v2_toy`
- Location: `osctl/examples/os_v2_toy/`
- Files:
  - `event_log_sample.jsonl` — synthetic event log.
  - `os_v2_config.yaml` — toy config (rules/thresholds/output).
  - `json_schemas/*.json` — schema checks for run/proof/decision logs.
  - `run_osctl.sh` — one-liner to run + verify.
- Designed to be safe, fast, and aligned with the OS v2 paper narrative at a high level.

### 3) Console (read-only governance console)
- Location: `console/`
- Backend exposes:
  - `/api/v1/runs`, `/api/v1/runs/<run_id>`, `/api/v1/runs/<run_id>/decisions`, `/api/v1/runs/<run_id>/verify`
  - `/api/v1/ce-ledger`, `/api/v1/cohorts`
- Frontend: static HTML/JS (read-only). Intended for inspection/teaching, not production.
- See `docs/Console_Overview_v1.md`.

### 4) Docs
- `docs/OSS_Overview_v1.md` — what/why is exported.
- `docs/Quickstart_OSCTL_v1.md` — step-by-step for the toy runtime.
- `docs/Console_Overview_v1.md` — roles/screens/endpoints.
- `docs/Runtime_SLI_SLO_Spec_v1.md` — SLI/SLO definitions used in the demo.
- `docs/research/eval/Public_OSV2_Sanity_v1/README.md` — public OS v2 sanity bundle (synthetic data, reproducible).

---

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.

# Run toy workload
bash osctl/examples/os_v2_toy/run_osctl.sh

# Or manually:
python -m osctl.cli run \
  --config osctl/examples/os_v2_toy/os_v2_config.yaml \
  --events osctl/examples/os_v2_toy/event_log_sample.jsonl \
  --out-dir out/osctl_runs_demo \
  --schemas-root osctl/examples/os_v2_toy/json_schemas \
  --run-id DEMO_RUN_001 --no-bundle

python -m osctl.cli verify \
  --run-id DEMO_RUN_001 \
  --out-dir out/osctl_runs_demo \
  --schemas-root osctl/examples/os_v2_toy/json_schemas

# Console (optional)
python -m console.app --run-root out/osctl_runs_demo --host 127.0.0.1 --port 8000
# Open http://127.0.0.1:8000
```

---

## CI (suggested)
- `.github/workflows/oss-ci.yml` runs:
  - osctl toy run + verify
  - console smoke (API responds with 200)

---

## License
Apache License 2.0 (see `LICENSE`). No production warranty; this is a demo-only artifact.
>>>>>>> fbf5cfb (feat: initial OSS demo runtime (osctl + console + docs))
