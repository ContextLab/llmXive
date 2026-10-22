# Quickstart: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites
- **Python 3.11+** (Linux environment recommended).
- **GitHub Actions free‑tier runner** or any Linux VM with ≥ 2 CPU cores and ≤ 7 GB RAM.
- **cgroups** support (required for CPU throttling).
- No GPU needed.

## Installation
```bash
cd projects/PROJ-883-llmxive-follow-up-extending-omniretrieva

python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies (numpy/pyarrow pinned to a compatible pair)
pip install -r requirements.txt
```

## Verify Environment
```bash
# Lint the codebase (must exit 0)
ruff check code/

# Verify cgroups availability
python -c "import os; assert os.path.isdir('/sys/fs/cgroup'), 'cgroups not available'"

# Verify CLI help flag works
python -m code.main --help
```

## End‑to‑End Run
```bash
# This will:
# 1. Download and checksum the verified datasets.
# 2. Generate queries and reference plans.
# 3. OPTIONAL: run the exhaustive optimal planner on a sampled subset (--run-optimal-planner).
# 4. Calibrate engine overhead (baseline measurement, 5 repetitions).
# 5. Execute the benchmark under cgroups throttling (≤ 1 000 ms CPU quota per query).
# 6. Perform statistical analysis.
# 7. Produce the interaction plot.
python -m code.main
```

### Expected Outputs
- `data/processed/generation_log.json`
- `data/processed/optimal_ground_truth.json` (if `--run-optimal-planner` used)
- `data/processed/baseline_overhead.json`
- `data/processed/execution_logs.csv`
- `data/processed/execution_metric.json`
- `data/results/anova_results.json`
- `data/results/sensitivity_analysis.json`
- `data/results/statistics_results.json`
- `data/results/interaction_plot.png`

## Help
```bash
python -m code.main --help
```
The `--help` flag prints all configurable options, including:
- `--run-optimal-planner` – invoke Phase 0 on the sampled subset.
- `--baseline-reps=N` – number of trivial queries for baseline calibration (default 5).
- `--cpu-quota-ms=1000` – CPU time limit per query (must match FR‑001).

## Tests
```bash
pytest -v
```
All unit and integration tests must pass. Tests include:
- Schema validation against contracts (all four schemas present under `specs/<identifier>-structural-mismatch-cost/contracts/`).
- Successful download of at least one row from each verified dataset.
- Correct handling of cgroups throttling errors (exit code 99) and depth‑overflow warnings.

## Re‑Running a Single Phase (optional)
- **Data download only**: `python -m code.main --stage data_download`
- **Query generation only**: `python -m code.main --stage generate_queries`
- **Benchmark only**: `python -m code.main --stage run_benchmark`
- **Optimal planner only**: `python -m code.main --stage run_optimal_planner`

---

