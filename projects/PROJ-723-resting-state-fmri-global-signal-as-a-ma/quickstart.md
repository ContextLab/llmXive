# Quickstart Guide: Resting‑State fMRI Global Signal Analysis

## Prerequisites

- Python 3.11+
- `pip`

## Installation

```bash
cd projects/PROJ-723-resting-state-fmri-global-signal-as-a-ma
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Pipeline

```bash
python code/main.py
```

This single command runs the full analysis pipeline:

1. **Data Ingestion** – downloads (or uses existing) HCP data, computes the global‑signal standard deviation, applies exclusions, and writes the cleaned dataset.
2. **Modeling** – fits the ridge‑regression model, performs permutation testing, and writes model results.
3. **Diagnostics** – collinearity checks.
4. **Robustness** – sensitivity analyses.
5. **Reporting & Visualisation** – generates the final report and figures.

## Expected Top‑Level Outputs

After successful execution, the following files will be present:

- `data/processed/cleaned_data.csv` – the cleaned subject‑level dataset containing all required predictors and the MWQ score.
- `data/results/final_report.json` – the aggregated report with model performance, null‑distribution p‑values, robustness metrics, and success‑criterion status. [UNRESOLVED-CLAIM: c_87ff18e7 — status=not_enough_info]

Additional artefacts (diagnostics, null‑distribution JSON/PNG, robustness JSON/PNG, etc.) are also generated inside `data/results/` and `figures/`.

## Troubleshooting

- **Missing raw data** – If the HCP data has not been downloaded, the ingestion step will raise a clear error pointing you to the download script. [UNRESOLVED-CLAIM: c_8084e318 — status=not_enough_info]
- **Permission errors** – Ensure the `data/` directories are writable; the pipeline will create any missing folders automatically. [UNRESOLVED-CLAIM: c_6cfa4cb6 — status=not_enough_info]
- **Unexpected failures** – All steps log detailed messages to `data/logs/pipeline.log`. [UNRESOLVED-CLAIM: c_a974dcad — status=not_enough_info] Check this file for diagnostics.
