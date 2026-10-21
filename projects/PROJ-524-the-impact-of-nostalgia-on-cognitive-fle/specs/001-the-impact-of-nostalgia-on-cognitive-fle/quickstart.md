# Quick Start Guide

This guide walks you through setting up the environment and running the analysis pipeline for **PROJ‑524** (re‑scoped to demonstrate the workflow with real WCST outcomes and synthetic stimulus labels).

## Prerequisites
- Python 3.11 or later
- `git`
- No internet access is required after the initial dataset download (the dataset is cached).

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd <project-directory>

# 2. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline (recommended)

```bash
python code/main.py
```

`main.py` orchestrates the following steps in order:

1. **Data Ingestion** – loads a *real* open WCST dataset and adds a **synthetic** `stimulus_type` column (nostalgia vs. control) → `data/raw/wcst_dataset.csv`.  
2. **Checksum Verification** – confirms stimulus placeholder files match `manifest.json`.  
3. **Cleaning** – applies age filter (FR‑001) and MMSE exclusion (FR‑006); writes `data/processed/cleaned_dataset.csv`, `data/processed/wcst_metrics.csv`, and `exclusion_log.json`.  
4. **Statistical Analysis** – Welch’s t‑test, Bonferroni correction, **Cohen’s d** with 95 % CI, MDES, adjusted OLS model → `statistical_report.json`.  
5. **Sensitivity Analyses** – α‑sweep (0.01, 0.04, 0.05, 0.06) and MMSE‑exclusion sensitivity → `sensitivity_report.json`.  
6. **Runtime Monitoring** – logs a warning if total runtime > 6 h (FR‑007).  
7. **Contract Validation** – tests that both JSON files conform to the schemas in `contracts/`.  

### Output Files
- `data/results/statistical_report.json` – primary test results (labeled `"validity_status": "simulation"`).  
- `data/results/sensitivity_report.json` – threshold and MMSE‑exclusion checks.  
- `data/results/exclusion_log.json` – counts of rows removed for each rule.  

## Step‑by‑Step Debugging

| Step | Command | Description |
|------|---------|-------------|
| Ingest data | `python code/ingestion.py` | Loads real WCST data, adds synthetic stimulus labels. |
| Verify stimuli | `python code/utils.py verify_stimuli` | Checks SHA‑256 checksums of placeholder audio files. |
| Clean data | `python code/cleaning.py` | Applies FR‑001 and FR‑006; writes cleaned data, metrics table, and exclusion log. |
| Run analysis | `python code/analysis.py` | Generates `statistical_report.json`. |
| Run sensitivity | `python code/sensitivity.py` | Generates `sensitivity_report.json`. |
| Full run | `python code/main.py` | Executes all steps sequentially. |

## Testing
Run the full test suite to ensure contracts and functional behavior are satisfied:

```bash
pytest -v
```

All tests should pass on the CI runner; failures indicate a violation of a functional requirement or contract.

## Important Note
Because no open dataset includes a genuine nostalgia vs. control manipulation, the `stimulus_type` column is **synthetically assigned**. All results are therefore labeled `"validity_status": "simulation"` and **do not constitute empirical evidence** about the effect of nostalgia. The pipeline demonstrates compliance with the required statistical procedures without making causal claims.

---



