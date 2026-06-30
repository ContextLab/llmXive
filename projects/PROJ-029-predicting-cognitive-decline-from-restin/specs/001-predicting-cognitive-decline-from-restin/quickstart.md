# Quickstart: Predicting Cognitive Decline from Resting-State fMRI Network Topology

## Prerequisites

- Python 3.11+
- GitHub Actions free-tier runner (2 CPU, ~7 GB RAM, ~14 GB disk)
- OpenNeuro CLI (optional; for downloading `ds000248`)

## Installation

```bash
# Clone repository
git clone <repo-url>
cd <project-dir>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Running the Pipeline

### Step 1: Download and Filter Data
```bash
python code/01_download_and_filter.py
```
- Downloads `ds000248` from OpenNeuro.
- Filters subjects with non-null MMSE/MOCA at both timepoints.
- Outputs: `data/processed/filtered_subjects.csv`.

### Step 2: Preprocess and Parcellate
```bash
python code/02_preprocess_and_parcellate.py
```
- Applies AAL atlas to generate region-based connectivity matrices.
- Outputs: `data/processed/connectivity_matrices/`.

### Step 3: Compute Graph Metrics
```bash
python code/03_compute_graph_metrics.py
```
- Calculates degree, efficiency, clustering, path length.
- Outputs: `data/processed/graph_metrics.csv`.

### Step 4: Train Model with Nested CV
```bash
python code/04_train_model.py
```
- Train Random Forest with nested cross-validation.
- **Includes nested feature selection** to reduce features to <20.
- Outputs: `data/processed/model.pkl`, `data/processed/cv_results.json`.

### Step 5: Evaluate Model
```bash
python code/05_evaluate_model.py
```
- Computes ROC-AUC, accuracy, F1-score.
- Outputs: `data/processed/performance_report.json`.

### Step 6: Permutation Test
```bash
python code/06_permutation_test.py
```
- Runs multiple label permutations.
- Outputs: `data/processed/permutation_results.json`, p-value.

### Step 7: Sensitivity Analysis
```bash
python code/07_sensitivity_analysis.py
```
- Sweeps thresholds {0.45, 0.50, 0.55} and decline definitions (±1 point).
- Outputs: `data/processed/sensitivity_report.json`.

### Step 8: Collinearity Check
```bash
python code/08_collinearity_check.py
```
- Detects and excludes collinear features (correlation > 0.95).
- Logs excluded features.

### Step 9: Generate Final Report
```bash
python code/09_generate_report.py
```
- Compiles all results into a single report.
- **Includes verification of SC-002 and SC-005**.
- Outputs: `data/artifacts/final_report.md`.

## Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run contract tests
pytest tests/contract/
```

## Troubleshooting

- **Dataset download fails**: Retry up to 3 times with exponential backoff (built-in).
- **Missing MMSE/MOCA**: Subjects excluded; log generated at `data/logs/excluded_subjects.log`.
- **Collinearity detected**: Features with correlation > 0.95 excluded; log at `data/logs/collinearity.log`.
- **Permutation test timeout**: Bounded to 2 hours; if exceeded, partial results saved.
- **Dataset missing labels**: Pipeline halts with `EXIT_CODE_NO_LABELS` and generates a failure report.