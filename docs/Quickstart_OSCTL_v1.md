# Quickstart: osctl Toy Runtime (WarmLogic-OSS v0.1.0)

Prereqs
- Python 3.10+
- macOS/Linux shell

Setup
```bash
cd WarmLogic-OSS
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.
```

Run + Verify
```bash
python -m osctl.cli run \
  --config examples/os_v2_toy/os_v2_config.yaml \
  --events examples/os_v2_toy/event_log_sample.jsonl \
  --out-dir out/osctl_runs \
  --schemas-root examples/os_v2_toy/json_schemas \
  --run-id OSS_TOY_RUN --no-bundle

python -m osctl.cli verify \
  --run-id OSS_TOY_RUN \
  --out-dir out/osctl_runs \
  --schemas-root examples/os_v2_toy/json_schemas
```

Console (optional)
```bash
python -m console.app --run-root out/osctl_runs --host 127.0.0.1 --port 8000
open http://127.0.0.1:8000
```

Notes
- This is a demo; no production SLO/SLA. Evidence/ledger shown are synthetic.
- For full program docs, see the private WarmLogic repo or published papers.
