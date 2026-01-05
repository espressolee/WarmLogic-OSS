# Console Overview (WarmLogic-OSS v1)

Purpose: a **read-only governance console** for the demo runtime. Shows runs, decisions, counterexamples, and cohort status using synthetic data.

## Roles
- Internal researcher: inspect runs, decisions, CE entries during experiments.
- Pilot operator (demo): monitor toy runs, CE status.
- Auditor (demo): verify that runs are traceable and replayable.

## Core screens
1) Run overview (`/api/v1/runs` or HTML list)
   - `run_id`, `status`, `verify_status`, timestamps.
   - SLI snapshot (if available): decision_latency_p95_ms, evidence_lag_p95_min, ce_open_count.
2) Run detail (`/api/v1/runs/<run_id>`)
   - govdec summary, decision log, proof/verify artifacts.
3) CE ledger (`/api/v1/ce-ledger`)
   - `ce_id`, `status`, related run, last_updated.
4) Cohorts (`/api/v1/cohorts`)
   - toy cohort entries (advisory/enforce status, last bundle hash).

## Architecture (demo)
- Backend: Flask; reads from filesystem:
  - `out/osctl_runs/<run_id>/run_manifest.json`, `govdec.json`, `decision_log.jsonl`, `verify_report.json`
  - `ledger/Counterexamples_v1.json` (toy) and/or `ce-ledger` JSONL
  - `ledger/External_Repro_Status_v1.json` (toy)
- Frontend: static HTML/JS, read-only.

## Non-goals (v1 demo)
- No auth/RBAC, no write operations.
- Not a production SaaS console; demo/teaching only.
