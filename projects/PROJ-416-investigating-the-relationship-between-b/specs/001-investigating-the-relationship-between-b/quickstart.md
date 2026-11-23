# Quickstart: Investigate Brain Network Dynamics and VR Therapy Response

## Prerequisites

- Python 3.11+
- GB free disk space
- Internet access (to download OpenNeuro data)
- `datalad` installed (`pip install datalad`)

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` will pin `nilearn`, `scikit-learn`, `statsmodels`, `pandas`, `networkx`, `bctpy`, `datalad`.*

## Execution

### Step 1: Data Validation (Critical)
Before running the full pipeline, verify that the dataset contains the required variables.
```bash
python code/data/validate.py --dataset "openneuro" --check-variables "pre_treatment_score,post_treatment_score,anxiety_instrument"
```
- **Success**: Exits 0 and logs "Variables found".
- **Failure**: Exits 1 and logs "Data Unavailable: Missing [variable_name]" or "Invalid Instrument: [name]".

### Step 2: Power Analysis (Gate)
Run the power analysis to determine if the dataset is sufficient.
```bash
python code/analysis/power.py --effect-size 0.15 --alpha 0.05 --power 0.8
```
- **If N < 5**: Exits 1 with "Insufficient Power: N < 5".
- **If 5 <= N < required**: Logs warning and switches to exploratory mode.

### Step 3: Preprocessing & Metric Computation
Run the pipeline on a subset (N=20) to fit within CI constraints.
```bash
python code/main.py --mode full --max-subjects 20 --atlas "Schaefer-100"
```
- This will:
  1.  Download/stream data.
  2.  Preprocess (motion correction, normalization).
  3.  Compute network metrics.
  4.  Exclude subjects with FD > 3mm.

### Step 4: Statistical Analysis & Sensitivity
Run the ANCOVA and sensitivity analysis.
```bash
python code/main.py --mode analysis --correction "fdr" --sweep-motion "2.0,3.0" --sweep-pval "0.01,0.05,0.1" --sweep-outcome "change,residual,raw"
```
- Generates `reports/analysis_report.md` and `reports/sensitivity_analysis.md`.

### Step 5: View Results
Open `reports/analysis_report.md` and `reports/sensitivity_analysis.md` to view the findings, framed as associational (unless randomized metadata is found).

## Troubleshooting

- **Memory Error**: Ensure `streaming=True` is used in `data/download.py`.
- **Collinearity Error**: If VIF > 5, the system automatically runs PCA for exploratory visualization. Primary tests remain univariate.
- **Missing Data**: If the pipeline halts with "Data Unavailable", the verified dataset lacks the required clinical scores. No synthetic data will be generated for hypothesis testing.
- **No VR Data**: If no longitudinal VR dataset is found, the pipeline may halt or switch to proxy data (if configured).