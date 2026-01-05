# Runtime SLI / SLO Spec (WarmLogic-OSS v1)

This demo uses a minimal set of SLI/SLO to illustrate runtime health.

## SLI
1) `decision_latency_p95_ms`
   - 95th percentile of `decision_end_ts - decision_start_ts` per run.
   - Source: `decision_log.jsonl`.
2) `evidence_lag_p95_min`
   - 95th percentile of `(evidence_commit_ts - trigger_ts)` for evidence-linked triggers.
   - Source: decision/event logs (if fields exist).
3) `verify_success_rate`
   - Fraction of `osctl verify` executions that PASS (over a window of runs).
   - Source: CI logs or verify outputs.
4) `ce_open_count`
   - Count of CE entries with `status != "MITIGATED"`.
   - Source: CE ledger JSON/JSONL.

## SLO (demo defaults)
- `decision_latency_p95_ms ≤ 500 ms`
- `evidence_lag_p95_min ≤ 60 min`
- `verify_success_rate ≥ 0.99`
- `ce_open_count ≤ 3`

These are illustrative; adjust per pilot or demo as needed.

## Console integration
- Show per-run SLI snapshot on runs list.
- Optional highlight if SLO is violated.
- SLI can be precomputed (JSON per run) or computed on the fly from logs.
