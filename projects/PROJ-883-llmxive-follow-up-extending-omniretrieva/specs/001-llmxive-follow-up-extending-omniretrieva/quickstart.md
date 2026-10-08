# Quickstart: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Prerequisites

- Python 3.11+
- Access to a Linux environment (GitHub Actions or local Linux).
- 7GB+ RAM, 2+ CPU cores.
- Internet access to download HuggingFace datasets and DBpedia.

## Installation

1. **Clone and Setup**:
   ```bash
   cd projects/PROJ-883-llmxive-follow-up-extending-omniretrieva
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Verify Dependencies**:
   ```bash
   python -c "import pandas, scipy, statsmodels, networkx, rdflib; print('All dependencies OK')"
   ```

3. **Linting Configuration**:
   Ensure `.ruff.toml` and `pyproject.toml` are present.
   ```bash
   ruff check code/
   ```

## Running the Benchmark

### 1. Data Preparation
The system will automatically download and verify datasets from the verified URLs upon the first run.
```bash
python code/data_loader.py --prepare
```
*Output*: `data/raw/` populated with parquet and RDF files. Checksums recorded.

### 2. Generate Queries & Ground Truth
Generates synthetic queries with known complexity levels and computes ground truth plans.
```bash
python code/query_generator.py --levels 1 2 3 4 --count 500 --seed 42
python code/ground_truth_engine.py --input data/processed/generation_log.json --output data/processed/generation_log.json
```
*Output*: `data/processed/generation_log.json` (with `ground_truth_plan` populated).

### 3. Execute Benchmark
Runs the queries against simulated engines with CPU throttling.
```bash
python code/benchmark_runner.py --throttle cgroups --timeout 60
```
*Note*: If `cgroups` fails (no root), it falls back to `time_only` and logs the mode.
*Output*: `data/processed/execution_logs.csv`.

### 4. Statistical Analysis
Performs ANCOVA and sensitivity analysis.
```bash
python code/stats.py --input data/processed/execution_logs.csv
```
*Output*: `data/results/anova_results.json`, `data/results/sensitivity_analysis.json`.

### 5. Visualization (Optional)
Generates the interaction plot.
```bash
python code/visualize.py --input data/processed/execution_logs.csv --output data/results/interaction_plot.png
```

## Troubleshooting

- **Error: "cgroups not available"**: The runner will log a warning and proceed with `time_only` mode. This is acceptable for relative latency comparisons but not absolute CPU constraints.
- **Error: "Dataset missing"**: Ensure you have network access. The script uses `datasets.load_dataset` with the verified URLs.
- **Error: "Complexity level non-integer"**: The generator enforces integer depth. If this occurs, check the `query_generator.py` logic.
- **Error: "Depth insufficient"**: The run aborted because real data (Spider/DBpedia) did not support the required depth. Check the dataset source.

## Reproducibility

To reproduce the exact results:
1. Set `SEED=42` in `code/config.py`.
2. Use the same dataset versions (checksums in `state/...yaml`).
3. Run the full pipeline in order.