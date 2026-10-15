# Quickstart: End‑to‑End Pipeline (Tiny Test Subset)

This document describes a single command that runs the full analysis pipeline on a **tiny test subset** (three CMIP6 models).
The command is self‑contained; once the repository is cloned and dependencies are installed, executing it will:

1. Download a minimal test shard of the CMIP6 dataset (three models).
2. Ingest, impute, and standardise the data.
3. Fit a B‑spline basis, perform functional PCA, and run the Leave‑One‑Out (LOO) jackknife robustness assessment.
4. Generate visualisations and a JSON summary.
5. Write all artefacts to `data/artifacts/end_to_end_demo/`.

## Prerequisites

- Python 3.11+
- Git
- Internet access (to download the test shard from HuggingFace)

## Setup

```bash
# 1️⃣ Clone the repository and enter the project directory
git clone <repository‑url>
cd projects/PROJ-231-statistical-analysis-of-publicly-availab

# 2️⃣ Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run the full pipeline on the tiny subset

```bash
# Single command – everything is done automatically
python code/main.py --test-subset
```

*Explanation of the flag*:

- `--test-subset` tells the pipeline to limit the ensemble to a **pre‑selected three‑model test shard** (downloaded automatically by `code/ingestion.py`).
- No additional arguments are required; the script handles data download, processing, FPCA, jackknife, visualisation, and state‑hash updates.

## Expected output

After successful execution, the following artefacts will be present:

```
data/artifacts/end_to_end_demo/
├── plots/
│ ├── mode_1.png
│ ├── mode_2.png
│ └── mode_3.png
├── jackknife_metrics.json # stability metrics per component
├── variance_metrics.json # cumulative variance, threshold info
├── summary.json # high‑level JSON summary of the run
└── log.txt # pipeline log (ends with “Pipeline completed successfully”)
```

You can verify the run completed correctly with:

```bash
ls -R data/artifacts/end_to_end_demo/
cat data/artifacts/end_to_end_demo/log.txt | tail -n 1
```

The final line of the log should read:

```
Pipeline completed successfully
```

## Troubleshooting

- **Missing internet connection** – the script will abort with a clear error pointing to the failed download step. Re‑run after restoring connectivity.
- **Insufficient memory** – the tiny subset is designed to run comfortably on the GitHub Actions free tier (< 7 GB RAM). If you encounter OOM, ensure you are using the `--test-subset` flag (the full dataset requires more resources).
- **State file not updated** – check file permissions for `state/projects/PROJ-231-statistical-analysis-of-publicly-availab.yaml`. The pipeline will raise an exception if it cannot write the state file.

## Running the full (non‑test) pipeline

When you are ready to analyse the complete CMIP6 ensemble, simply omit the flag:

```bash
python code/main.py
```

This will stream the full dataset, perform the same analysis, and store results under `data/artifacts/` (without the `end_to_end_demo` sub‑directory).
