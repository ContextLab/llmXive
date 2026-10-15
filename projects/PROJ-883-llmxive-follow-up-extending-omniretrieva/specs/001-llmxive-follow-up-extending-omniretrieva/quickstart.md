# Quickstart: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites
- Python 3.11+
- Linux environment (GitHub Actions runner or equivalent)
- >= 7 GB RAM, >= 2 CPU cores

## Installation
```bash
cd projects/PROJ-883-llmxive-follow-up-extending-omniretrieva
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lint
```bash
ruff check code/
```

## End-to-End Run
```bash
python -m code.main
```

The command performs the skeleton pipeline:
1. Creates the required directories (`data/raw/`, `data/processed/`,
   `data/results/`, `tests/unit/`, `tests/integration/`).
2. Generates a small deterministic query set (seed from `code/config.py`,
   overridable with `--seed`).
3. Attaches a system-generated plan (depth-1 lookahead heuristic) and a
   deterministic reference plan to each query.
4. Measures real wall-clock latency per query (no `time.sleep` or
   simulated delays).
5. Writes `data/processed/execution_logs.csv` with columns
   `query_id,source_type,complexity_level,latency_ms,timestamp,translation_error,success_flag,timeout_flag,synthetic_flag,throttling_mode`.
6. Writes a durable run manifest (row counts + SHA-256 checksum) to
   `data/results/pipeline_manifest.json`.

## Quick Help
```bash
python -m code.main --help
```
Displays usage information and exits with status 0.

## Tests
```bash
python -m pytest -v
```

## Notes
- This skeleton does not yet download real datasets or enforce cgroups
  throttling; those capabilities are added in later tasks (T003, T007,
  T008, T009).
- All generated files live under the `data/` hierarchy; the run manifest
  under `data/results/` provides durable, committed evidence of each run.
- Query generation is deterministic thanks to the pinned seed in
  `code/config.py`.
