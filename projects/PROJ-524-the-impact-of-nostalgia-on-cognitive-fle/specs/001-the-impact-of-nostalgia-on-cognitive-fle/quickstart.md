# Quick Start Guide

This guide walks you through setting up the environment and running the full analysis pipeline for **PROJ‑524**.

## Prerequisites
- Python 3.11 or later
- `git`
- Internet access (to download optional open datasets or stimulus placeholders)

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd <project-directory>

# 2. Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Directory Setup
The first run will create necessary folders under `data/`:

```bash
python -c "import pathlib, os; [pathlib.Path(p).mkdir(parents=True, exist_ok=True) for p in ['data/raw','data/processed','data/stimuli','data/results']]"
```

## Running the Full Pipeline (recommended)

```bash
python code/main.py
```

`main.py` orchestrates the following steps:

1. **Data ingestion** – attempts to download an open WCST dataset; if unavailable, generates synthetic data.  
2. **Checksum verification** – ensures stimulus files are intact.  
3. **Cleaning** – applies age filter (FR‑001) and optional MMSE exclusion (FR‑006).  
4. **Statistical analysis** – Welch’s t‑test, Bonferroni correction, Cohen’s d, MDES (FR‑002‑FR‑004).  
5. **Sensitivity analysis** – threshold sweep and MMSE‑exclusion sensitivity (FR‑005).  
6. **Runtime monitoring** – logs a warning if total runtime > 6 h (FR‑007).  
7. **Reporting** – writes JSON reports and logs under `data/results/`.  

### Output Files
- `data/results/statistical_report.json` – primary test results.  
- `data/results/sensitivity_report.json` – threshold and MMSE‑exclusion checks.  
- `data/results/exclusion_log.json` – counts of rows removed for each rule.  

## Step‑by‑Step Execution (for debugging)

| Step | Command | Description |
|------|---------|-------------|
| Ingestion / Simulation | `python code/ingestion.py` | Downloads or creates `data/raw/raw_dataset.csv`. |
| Checksum Verification | `python code/utils.py verify_stimuli` | Confirms stimulus file integrity. |
| Cleaning | `python code/cleaning.py` | Produces `data/processed/cleaned_dataset.csv`. |
| Analysis | `python code/analysis.py` | Generates `statistical_report.json`. |
| Sensitivity | `python code/sensitivity.py` | Generates `sensitivity_report.json`. |
| Full Report | `python code/main.py` | Runs all above in order. |

## Testing
Run the test suite to ensure contracts and functional behavior are satisfied:

```bash
pytest -v
```

All tests should pass on the CI runner; failures indicate a violation of a functional requirement or contract.

## Troubleshooting
- **Missing dataset**: The pipeline will automatically fall back to synthetic data; check `data/raw/metadata.json` for `"simulation_mode": true`.  
- **Runtime warning**: If you see `WARNING: Runtime exceeded 6 hours`, the pipeline continued but you may need to profile steps for efficiency.  
- **Checksum mismatch**: Re‑run `python code/utils.py verify_stimuli` after ensuring stimulus files are unchanged.

---
