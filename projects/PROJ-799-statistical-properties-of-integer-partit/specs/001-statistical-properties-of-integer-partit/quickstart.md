# Quickstart: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-799-statistical-properties-of-integer-partit
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

## Running the Pipeline

### Step 1: Generate Partition Data

```bash
python code/generate_partitions.py --n_max 50000
```

**Output**: `data/raw/partitions.csv`

### Step 2: Compute Features and Residuals

```bash
python code/feature_engineering.py
```

**Output**: `data/processed/features.csv`

### Step 3: Run Regression Analysis

```bash
python code/regression_analysis.py
```

**Output**: `output/regression_summary.json`, `output/plot_residuals.png`

### Step 4: Cross-Validation and Visualization

```bash
python code/validation.py
```

**Output**: Cross-validation results, additional plots.

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

**Key Tests**:
- `test_generate_partitions`: Validates DP correctness against known values.
- `test_features_non_null`: Ensures no `NaN` in `features.csv`.
- `test_regression_analysis`: Checks model fit and $R^2$.

## Configuration

- **`n_max`**: Set via `--n_max` flag in `generate_partitions.py` (default [deferred]).
- **Random Seed**: Set `RANDOM_SEED` in `code/regression_analysis.py` for reproducibility.

## Troubleshooting

- **Memory Error**: Ensure `n_max` $\le [deferred]$; check `dp` array size (expected ~2-3 GB).
- **Log(0) Error**: The pipeline filters out `p_P_n` = 0; verify `data/raw/partitions.csv` for invalid rows.
- **Import Error**: Ensure virtual environment is activated and dependencies are installed.

## Output Interpretation

- **`R_n`**: Positive values indicate $p_{\mathcal{P}}(n) > Q_{as}(n)$; negative values indicate underestimation.
- **Regression Coefficients**: Significant coefficients (p < 0.05 after correction) indicate density-dependent corrections.
- **$R^2$**: Values $\ge 0.05$ (SC-002) suggest meaningful correlation.
