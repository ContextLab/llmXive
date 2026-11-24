# Quick Start Guide

This guide walks you through setting up the environment and running the analysis pipeline for **PROJ‑524** (re‑scoped to use a real, in‑lab collected dataset).

## Prerequisites
- Python 3.11 or later
- `git`
- No internet access is required after the initial repository clone (all data are collected locally).

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

1. **Data Collection** – Researchers run the in‑lab protocol (see `code/collection.py`) to obtain `data/raw/wcst_dataset.csv` with all required columns.  
2. **Stimulus ID Assignment** – `code/stimulus.py` verifies audio file checksums, creates a deterministic `stimulus_id` for each participant, and updates `manifest.json`.  
3. **Checksum Verification** – Confirms stimulus placeholder files match `manifest.json`.  
4. **Cleaning** – Applies age filter (FR‑001) and MMSE exclusion (FR‑006); writes `data/processed/cleaned_dataset.csv`, `data/processed/wcst_metrics.csv`, and `exclusion_log.json`.  
5. **Statistical Analysis** – Welch’s t‑test, Bonferroni correction, **Cohen's d** with 95 % CI, MDES → `statistical_report.json`.  
6. **Sensitivity Analyses** – α‑sweep (0.01, 0.04, 0.05, 0.06) and MMSE‑exclusion sensitivity → `sensitivity_report.json`.  
7. **Runtime Monitoring** – Logs a warning if total runtime > 6 h (FR‑007).  
8. **Contract Validation** – Tests that both JSON files conform to the schemas in `contracts/`.  

### Output Files
- `data/results/statistical_report.json` – primary test results (includes `"validity_status": "verified"`).  
- `data/results/sensitivity_report.json` – threshold and MMSE‑exclusion checks.  
- `data/results/exclusion_log.json` – counts of rows removed for each rule.  

## Step‑by‑Step Debugging

| Step | Command | Description |
|------|---------|-------------|
| Collect data | `python code/collection.py` | Runs the in‑lab data‑collection protocol (manual step; generates `wcst_dataset.csv`). |
| Verify stimuli | `python code/stimulus.py assign_ids` | Checks SHA‑256 checksums and creates `stimulus_id` mapping. |
| Clean data | `python code/cleaning.py` | Applies FR‑001 and FR‑006; writes cleaned data and exclusion log. |
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
The dataset must be **collected in‑lab** as described; the pipeline does not generate synthetic data. Results will reflect the actual effect of nostalgia on cognitive flexibility in the recruited aging adult sample.

---


