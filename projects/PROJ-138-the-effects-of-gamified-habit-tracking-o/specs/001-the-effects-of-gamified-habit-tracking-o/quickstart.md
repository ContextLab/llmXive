# Quickstart: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

## Prerequisites
- Python 3.11+
- Git
- Access to the project repository

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-138-the-effects-of-gamified-habit-tracking-o
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
   *Note*: `requirements.txt` now includes `pingouin` for psychometric validation and `scipy` for reliability checks.

## Running the Pipeline

### Step 1: Prepare Data
*Note: Since no verified longitudinal dataset URL is available, the pipeline uses a synthetic data generator by default.*

1. Ensure `data/consent/` exists (even if empty, for the check).
   ```bash
   mkdir -p data/consent
   touch data/consent/.gitkeep
   ```
2. Run the data generation script (simulates the verified source with known parameters):
   ```bash
   python code/data/ingestion.py --generate-synthetic
   ```
   *Output*: `data/raw/synthetic_logs.csv`, `data/processed/weekly_agg.csv`.

### Step 2: Execute Analysis
Run the full analysis pipeline:
```bash
python code/data/validation.py   # Includes Group Balance & Cronbach's α check
python code/analysis/modeling.py # Includes FDR Correction
python code/analysis/survival.py # Includes Event Count Check
python code/analysis/robustness.py
```

### Step 3: Generate Report & Version
Generate the final HTML/PDF report and update artifact hashes:
```bash
python code/reports/generate_report.py
python code/utils/versioning.py
```
*Output*: `reports/analysis_report.html` (or `.pdf`) and updated `state.yaml`.

## Verification
To verify the pipeline works:
1. Check that `data/processed/weekly_agg.csv` contains at least 100 rows.
2. Check that `reports/analysis_report.html` contains a Kaplan-Meier curve and a table of interaction coefficients (with FDR-adjusted p-values).
3. Run tests:
   ```bash
   pytest tests/
   ```

## Troubleshooting
- **Group Imbalance Error**: If the non-gamified group has < 30 users, the pipeline halts. This is expected if the synthetic seed produces an unbalanced split; change the seed.
- **Insufficient Events**: If dropout events < 10 per group, survival analysis is skipped.
- **Convergence Warning**: If `statsmodels` fails to converge, check for collinearity (VIF > 5) in `code/analysis/modeling.py`.
- **Missing Consent**: The pipeline will halt with "Data Insufficiency" if `data/consent/` is missing.