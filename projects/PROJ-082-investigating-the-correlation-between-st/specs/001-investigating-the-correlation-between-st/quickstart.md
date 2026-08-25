# Quickstart: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

## Prerequisites

- Python 3.11+
- `pip`
- A standard GitHub Actions runner (or local machine with similar specs)

## Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   cd projects/PROJ-082-investigating-the-correlation-between-st
   ```

2. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running the Pipeline

The pipeline is designed to run end-to-end. It automatically detects the number of studies and pivots if necessary.

### Step 1: Generate Synthetic Data (For Testing)
Since no real dataset exists, generate a synthetic dataset that mimics the expected distribution of studies.
```bash
python code/utils/generate_synthetic_literature.py --count 15 --seed 42 --config bonferroni
```
*This creates `data/raw/synthetic_literature.csv` with exactly 5 distinct tracts (for SC-004).*

### Step 2: Run the Full Pipeline
Execute the main orchestrator script:
```bash
python code/main.py --input data/raw/synthetic_literature.csv --output output/
```

**Expected Behavior**:
- If `N >= 10`: Performs meta-analysis, calculates $I^2$, runs Egger's test (with warning if 10-19), applies Holm-Bonferroni correction, runs MLM sensitivity analysis, and generates plots.
- If `N < 10`: Skips quantitative analysis, generates a `narrative_summary.md` instead.

### Step 3: View Results
- **JSON Reports**: `output/meta_analysis_results.json`, `output/bias_assessment.json`, `output/mlm_results.json`
- **Plots**: `output/forest_plot.png`, `output/funnel_plot.png`
- **Narrative**: `output/narrative_summary.md` (if applicable)

## Testing

Run the unit tests to verify edge cases (e.g., N < 10, missing values, pivot logic):
```bash
pytest tests/ -v
```

**Key Test Cases**:
- `test_pivot_logic`: Verifies that N < 10 triggers narrative mode.
- `test_egger_skip`: Verifies Egger's test is skipped for N < 10.
- `test_egger_low_power`: Verifies "Low Power Warning" for 10 <= N < 20.
- `test_bonferroni`: Verifies Holm-Bonferroni correction is applied for N >= 10 and k >= 2.
- `test_mlm`: Verifies MLM sensitivity analysis runs and compares with primary model.

## Troubleshooting

- **Convergence Warning**: If the random-effects model fails to converge, the system falls back to a fixed-effects model and logs a warning.
- **Missing Tract Names**: If a study lacks a tract name, it is excluded from the Holm-Bonferroni correction but included in the overall count if `r` and `n` are present.
- **Memory Error**: Unlikely given the small data size, but if it occurs, reduce the synthetic dataset size.
- **Real Data Validator**: If `data/processed/real_data_status.json` is missing, ensure `code/data/real_data_validator.py` has run successfully.