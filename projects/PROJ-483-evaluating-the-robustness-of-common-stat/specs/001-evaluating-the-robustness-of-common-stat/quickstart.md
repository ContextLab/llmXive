# Quickstart: Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or local environment with sufficient RAM.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-483-evaluating-the-robustness-of-common-stat
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Simulation

### Step 1: Download Datasets
The system will automatically download the verified UCI datasets to `data/raw/`.
```bash
python code/main.py --action download
```
*Output*: `data/raw/uci_wine_quality_red.csv`, `data/raw/uci_har.csv`, etc.

### Step 2: Configure Dependency Injection
Edit `data/dependency_manifest.yaml` to define the configurations (or use the default).
```yaml
# Example entry: Cluster-Effect Injection (Hierarchical)
configurations:
  - dataset_id: uci_wine_quality_red
    test_type: t_test
    dependency:
      type: cluster_effect
      strength: 0.3
    n_replications: 10000
    seed: 42
```

### Step 3: Run the Simulation
Execute the Monte Carlo simulation.
```bash
python code/main.py --action simulate --config data/dependency_manifest.yaml
```
*Output*:
- `results/type1_error_rates.csv`
- `results/power_analysis.csv`
- `results/perf_log.json` (T032b)
- `results/logistic_models.pkl` (Constitution VII)

### Step 4: Generate Visualizations
```bash
python code/main.py --action plot --input results/type1_error_rates.csv
```
*Output*: `results/figures/error_rate_curves.png`

## Verification & Reproducibility

To verify the results (T034):
1. Run the full pipeline again with a different seed or on a fresh runner.
2. Compare the `observed_error_rate` and `ci_lower`/`ci_upper` values. They should be within the expected Monte Carlo variance.
3. Check `state.yaml` for updated artifact hashes.

```bash
python code/main.py --action verify
```

## Troubleshooting

- **Memory Error**: If the dataset is too large, enable streaming in `code/data_loader.py` (set `streaming=True`).
- **Timeout**: Ensure `n_replications` is set to 10,000. If it exceeds 6 hours, reduce to a lower threshold (note this in the report).
- **Missing Data**: Ensure the verified URLs are accessible. If a dataset is removed, the script will fail with a clear error.
