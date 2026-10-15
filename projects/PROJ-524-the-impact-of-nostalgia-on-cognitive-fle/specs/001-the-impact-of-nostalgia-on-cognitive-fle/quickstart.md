# Quick Start Guide

This guide walks you through setting up the environment and running the full analysis pipeline for **PROJ-524**.

## Prerequisites
- Python 3.11 or later
- `git`
- No internet access is required (all data are generated locally).

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

## Running the Full Pipeline (recommended)

```bash
python code/main.py
```

`main.py` orchestrates the following steps:

1. **Data generation** – directly generates a deterministic synthetic dataset (seed = 42, **no external download attempt**) with **256 participants** (128 per condition) to satisfy the a priori power analysis. All outputs are labeled `"validity_status": "simulation"`.
2. **Checksum verification** – ensures stimulus placeholder files are intact.
3. **Cleaning** – applies age filter (FR-001) and MMSE exclusion (FR-006).
4. **Statistical analysis** – Welch's t-test, Bonferroni correction, Hedges' g with 95 % CI, adjusted OLS model, MDES (FR-002–FR-004).
5. **Sensitivity analysis** – threshold sweep and MMSE-exclusion sensitivity (FR-005).
6. **Runtime monitoring** – logs a warning if total runtime > 6 h (FR-007).
7. **Reporting** – writes JSON reports under `data/results/`.

### Output Files
- `data/results/statistical_report.json` – primary test results (simulation).
- `data/results/sensitivity_report.json` – threshold and MMSE-exclusion checks.
- `data/results/exclusion_log.json` – counts of rows removed for each rule.

## Step-by-Step Execution (for debugging)

| Step | Command | Description |
|------|---------|-------------|
| Simulation | `python code/ingestion.py` | Deterministically creates `data/raw/raw_dataset.csv` (no network). |
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
- **Simulation mode**: All runs are simulation-only; check `data/raw/metadata.json` for `"simulation_mode": true`.
- **Runtime warning**: If you see `WARNING: Runtime exceeded 6 hours`, the pipeline continued but you may profile steps for efficiency.
- **Checksum mismatch**: Re-run `python code/utils.py verify_stimuli` after ensuring stimulus files are unchanged.