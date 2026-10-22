# Quickstart: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites
- **Python 3.11+** (Linux environment recommended).  
- **GitHub Actions free‑tier runner** or any Linux VM with ≥ 2 CPU cores and ≤ 7 GB RAM.  
- **cgroups** support (required for CPU throttling).  
- No GPU needed.

## Installation
```bash
# Clone the repository (assumed already in the correct project directory)
cd projects/PROJ-883-llmxive-follow-up-extending-omniretrieva

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies (numpy>=2.0 for pyarrow compatibility)
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
# 3. Calibrate engine overhead (baseline measurement).
# 4. Execute the benchmark under cgroups throttling.
# 5. Perform statistical analysis.
# 6. Produce the interaction plot.
python -m code.main
```

### Expected Outputs
- `data/processed/generation_log.json`  
- `data/processed/execution_logs.csv`  
- `data/processed/execution_metric.json`  
- `data/results/anova_results.json`  
- `data/results/sensitivity_analysis.json`  
- `data/results/interaction_plot.png`

## Help
```bash
python -m code.main --help
```
The `--help` flag prints all configurable options (e.g., number of queries, cgroup quota, timeout).

## Tests
```bash
pytest -v
```
All unit and integration tests must pass (indicating a successful execution status). Tests include:
- Schema validation against contracts.  
- Successful download of at least one row from each verified dataset.  
- Correct handling of cgroups throttling errors.

## Re‑Running a Single Phase (optional)
- **Data download only**: `python -m code.main --stage data_download`  
- **Query generation only**: `python -m code.main --stage generate_queries`  
- **Benchmark only**: `python -m code.main --stage run_benchmark`  

Refer to `quickstart.md` for further customization.

---

