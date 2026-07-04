# Quickstart: Linking Resting‑State fMRI Entropy to Creative Problem Solving

## Prerequisites

- Python 3.11+
- Access to HCP pre-processed 4-D NIfTI files (downloaded automatically via script from OpenNeuro/HCP S3 bucket).
- `Creative_Problem_Solving.csv` (phenotype file) in `data/raw/` (if not bundled with the automated download).

## Installation

1.  **Clone the repository** and navigate to the project root.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins CPU-only versions of `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `nibabel`.*

## Data Preparation

The pipeline automatically downloads pre-processed fMRI data from the verified OpenNeuro/HCP S3 bucket (ds000030) to `data/raw/`.
```text
data/
└── raw/
    ├── HCP_Subject_001.nii.gz
    ├── HCP_Subject_002.nii.gz
    ...
    └── Creative_Problem_Solving.csv  # (Optional: if not bundled)
```
*If the `Creative_Problem_Solving.csv` is missing, the pipeline will halt with a clear error message.*

## Running the Pipeline

### 1. Standard Execution
Run the main pipeline to compute entropy, fit models, and generate results:
```bash
python code/main.py
```
*This will:*
- Load and scrub data (including automated S3 download if needed).
- Compute MSE (Global + Networks).
- Fit OLS models with Robust SEs.
- Apply FDR correction.
- Generate `data/processed/entropy_metrics.csv` and `data/processed/model_results.csv`.

### 2. Sensitivity Analysis
To run the full sensitivity sweep (re-computing AUC for `r` ∈ {0.15, 0.20, 0.25}):
```bash
python code/sensitivity.py --sweep
```
*This will instrument RAM and runtime for each iteration and output `data/processed/sensitivity_results.csv`.*

### 3. Validation
To check data quality and sample size constraints:
```bash
python code/utils.py --validate
```
*This checks for N < 30 and reports peak RAM usage.*

## Output Files

| File | Description |
| :--- | :--- |
| `data/processed/entropy_metrics.csv` | Parcel-level and network-level entropy values. |
| `data/processed/model_results.csv` | OLS coefficients, p-values, and FDR-adjusted p-values. |
| `data/logs/motion_exclusions.log` | Subjects excluded due to high motion (FD > 0.2mm). |
| `data/logs/missing_data.log` | Subjects excluded due to < 100 frames or missing phenotype. |
| `data/processed/sensitivity_results.csv` | Results of the `r` parameter sweep. |

## Troubleshooting

- **Error: "Missing phenotype file"**: Ensure `Creative_Problem_Solving.csv` exists in `data/raw/`.
- **Error: "Insufficient RAM"**: The pipeline is optimized for a specific memory constraint. If this occurs, reduce the number of scales or subjects in `config.py`.
- **Error: "N < 30"**: The analysis has halted due to insufficient sample size after motion exclusion. Check `missing_data.log`.