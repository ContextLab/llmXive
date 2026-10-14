# Quickstart: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites
- Python 3.11+
- Linux environment (GitHub Actions runner or equivalent)
- ≥ 7 GB RAM, ≥ 2 CPU cores

## Installation
```bash
git clone <repo-url>
cd projects/PROJ-883-llmxive-follow-up-extending-omniretrieva
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## End‑to‑End Run
```bash
python -m code.main
```

The command performs the full pipeline:
1. Creates required directories.
2. Generates a small synthetic query set.
3. Enriches each query with a dummy system‑generated plan.
4. Executes the queries using a synthetic latency model.
5. Writes `data/processed/execution_logs.csv` and
   `data/processed/execution_metrics.jsonl`.

## Quick Help
```bash
python -m code.main --help
```
Displays usage information without running the pipeline.

## Notes
* This skeleton does **not** download real datasets or enforce cgroup
  throttling; those capabilities are added in later tasks.
* All generated files are placed under the `data/` hierarchy and are
  reproducible thanks to the fixed random seed in `code/config.py`.