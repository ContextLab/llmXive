# Quickstart: Predicting Rate Constants of SN1 Reactions

## Prerequisites

-   Python 3.11+
-   Git
-   Sufficient RAM (recommended for smooth operation, with a minimum threshold below the recommended level)
-   Internet connection (for dataset download)

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-373-predicting-rate-constants-of-sn1-reactio/code
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for `torch` (CPU), `rdkit`, `scikit-learn`, `shap`, `pandas`.*

## Running the Pipeline

### Step 1: Ingest and Process Data
Download the verified dataset, parse SMILES, filter SN1 substrates, and compute descriptors.
```bash
python data/ingest.py
python data/clean.py
python data/descriptors.py
python data/split.py
```
*Output: `data/processed/train.csv`, `val.csv`, `test.csv`, `data/raw/checksums.txt`*

### Step 2: Train Baseline and MPNN
Train a linear regression baseline and a 4-layer MPNN with random hyperparameter search.
```bash
python models/train.py
```
*Output: `artifacts/best_model.pt`, `artifacts/metrics.json`*

### Step 3: Statistical Validation
Run bootstrap comparison, VIF diagnostics, and sensitivity analysis.
```bash
python models/evaluate.py
python analysis/collinearity.py
python analysis/sensitivity.py
```
*Output: `artifacts/statistical_report.md`, `artifacts/vif_flags.json`*

### Step 4: Interpretability
Generate SHAP plots and perturbation studies.
```bash
python analysis/interpret.py
```
*Output: `artifacts/shap_summary.png`, `artifacts/perturbation_results.csv`*

### Step 5: Full End-to-End Run
Run the entire pipeline from scratch (requires several hours on CPU).
```bash
python main.py
```

## Verifying Results

-   **Data Quality**: Check `data/processed/exclusion_report.jsonl` for the exclusion rate. It should be < 5% (SC-005).
-   **Performance**: Check `artifacts/metrics.json`. The MPNN `test_r2` should be compared against the linear baseline.
-   **Runtime**: The `main.py` output should log total runtime. It must be ≤ 6 hours (SC-002).

## Troubleshooting

-   **Memory Error**: If `MemoryError` occurs, reduce the dataset size in `config.py` (e.g., `MAX_SAMPLES = 5000`).
-   **SMILES Parsing Failure**: Check `exclusion_report.jsonl` for "ambiguous structure" or "parsing failed" errors.
-   **Slow Training**: Ensure `device='cpu'` is set in `models/mpnn.py`. Do not install `torch` with CUDA support.
