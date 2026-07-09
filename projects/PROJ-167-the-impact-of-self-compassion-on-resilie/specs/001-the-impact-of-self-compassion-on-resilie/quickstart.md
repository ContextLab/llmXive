# Quickstart: The Impact of Self‑Compassion on Resilience to Negative Feedback

## Prerequisites
- Python 3.10+
- Access to GitHub Actions (for CI) or local environment.
- Internet connection (to fetch OSF dataset).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-167-the-impact-of-self-compassion-on-resilie
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only runners.*

## Running the Analysis

### Option 1: Full Pipeline (Recommended)
Run the main script to download, clean, analyze, and generate the report.
```bash
python code/main.py
```
**Expected Output**:
- `data/raw/dataset.csv` (with checksum recorded in `state/...yaml`)
- `data/processed/cleaned_data.csv`
- `output/plots/` (3 PNGs)
- `output/report.html`

**Note on Data Availability**: If the OSF dataset `3k9r2` is missing or inaccessible, the pipeline will terminate immediately with the error: `[DATA_UNAVAILABLE: ...]`. This is an expected outcome if the data source is not available.

### Option 2: Step-by-Step
If you need to inspect intermediate steps:
```bash
# 1. Download and Validate
python code/data_loader.py --fetch

# 2. Preprocess
python code/preprocessing.py

# 3. Run Models
python code/models.py

# 4. Generate Plots
python code/visualization.py

# 5. Generate Report
python code/report_generator.py
```

## Verifying Results
1. Open `output/report.html` in a browser.
2. Check the "Methodological Caveats" section for the "Associational" vs "Causal" flag.
3. Verify that `interaction_pval_adj` is reported for each outcome.
4. Ensure `output/plots/` contains `anxiety_simple_slopes.png`, `rumination_simple_slopes.png`, and `self_efficacy_simple_slopes.png`.

## Troubleshooting
- **Error: `[DATA_UNAVAILABLE: Required columns missing...]`**: The OSF dataset does not match the spec. The pipeline cannot proceed.
- **Error: `[DATA_UNAVAILABLE: Dataset source unreachable...]`**: The OSF source `3k9r2` is not accessible. The project cannot proceed without this specific data.
- **Error: `[POWER_INSUFFICIENT: Sample size < 92...]`**: The dataset has too few participants for the required power.
- **Error: `[BOOTSTRAP_CONVERGENCE_WARNING...]`**: Bootstrap failed to converge; parametric CIs were used instead.
- **Error: `[TIMEOUT: Modeling phase exceeded 30 mins...]`**: The bootstrap or model fitting took too long.