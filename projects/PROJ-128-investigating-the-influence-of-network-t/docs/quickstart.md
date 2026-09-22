# Quickstart Guide: Investigating the Influence of Network Topology on Spontaneous Brain Activity

This guide provides step-by-step instructions to set up the environment, fetch real data, and run the full pipeline end-to-end.

## Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- At least 14 GB of free disk space (for raw and processed HCP data)
- At least 8 GB of RAM (CPU-only execution)
- A stable internet connection (to download HCP data from OpenNeuro)

## 1. Environment Setup

### Clone and Navigate
```bash
cd PROJ-128-investigating-the-influence-of-network-t
```

### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies
Install all required packages defined in `requirements.txt`:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

*Note: This installs `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `statsmodels`, `scipy`, `pyyaml`, and `datasets`.*

## 2. Data Acquisition

The pipeline requires real HCP (Human Connectome Project) data. We fetch this programmatically from OpenNeuro using the `datasets` library (Hugging Face).

The pipeline expects data in `data/raw/hcp/`. The scripts below will automatically download the necessary dMRI and fMRI files if they are missing.

**Manual Download (Optional):**
If you prefer to download manually, ensure the directory structure matches:
- `data/raw/hcp/sub-<ID>/func/sub-<ID>_task-rest_bold.nii.gz`
- `data/raw/hcp/sub-<ID>/dwi/sub-<ID>_dwi.nii.gz`
- `data/raw/hcp/sub-<ID>/dwi/sub-<ID>_dwi.bval`
- `data/raw/hcp/sub-<ID>/dwi/sub-<ID>_dwi.bvec`

## 3. Running the Pipeline

The main entry point is `code/main.py`. It orchestrates:
1. Structural graph metric calculation (global efficiency, clustering, modularity).
2. Dynamic functional state extraction (LOO K-Means).
3. Correlation analysis.
4. Report generation.

### Execute the Full Pipeline
```bash
python code/main.py
```

**What this does:**
- Loads real HCP data from `data/raw/hcp/`.
- Preprocesses dMRI/fMRI.
- Computes structural metrics with density sensitivity analysis.
- Computes dynamic metrics using Leave-One-Out K-Means.
- Runs correlation analysis with FDR correction.
- Generates `data/processed/structural_metrics.csv`, `data/processed/dynamic_metrics.csv`, `data/processed/correlation_results.csv`, and `data/reports/final_report.json`.
- Logs exclusions to `data/logs/exclusion_log.json`.

**Expected Duration:** ~30-60 minutes on a standard CPU (depending on cohort size and RAM).

### Run Validation Script (Optional)
To verify the pipeline produced all expected artifacts:
```bash
python code/validate_quickstart.py
```

## 4. Output Artifacts

After successful execution, verify the following files exist:

- **Processed Metrics:**
 - `data/processed/structural_metrics.csv`
 - `data/processed/dynamic_metrics.csv`
 - `data/processed/correlation_results.csv`
 - `data/processed/structural_density_sensitivity.csv`
 - `data/processed/sensitivity_comparison.csv`

- **Reports & Logs:**
 - `data/reports/final_report.json`
 - `data/logs/exclusion_log.json`
 - `data/processed/completeness_report.json`

## 5. Troubleshooting

### "No module named 'nilearn'"
Ensure you activated the virtual environment and ran `pip install -r requirements.txt`.

### "Data not found"
The pipeline attempts to download data automatically. If this fails, check your internet connection or manually download the HCP 1200 release subset from OpenNeuro and place it in `data/raw/hcp/`.

### "Out of Memory"
The pipeline is optimized for CPU and low memory usage. If you encounter memory errors, try reducing the `WINDOW_LENGTH_BASELINE` in `code/config.py` or processing a smaller subset of subjects.

## 6. Next Steps

- Review the generated `data/reports/final_report.json` for associational language compliance.
- Inspect `data/processed/sensitivity_comparison.csv` to verify robustness to window length (20 TR vs 30 TR).
- Check `data/processed/structural_density_sensitivity.csv` for graph density stability.

For detailed API documentation, refer to the docstrings in the `code/` modules.