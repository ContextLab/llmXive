# Quickstart: Evaluating Resting‑State fMRI Entropy as a Biomarker for Attention‑Deficit Traits

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the verified dataset URLs (OpenNeuro ds).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-709-evaluating-resting-state-fmri-entropy-as
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

### 1. Data Download & Preprocessing
Run the data download and preprocessing script. This will fetch the verified dataset (ds000305), perform motion scrubbing, and compute entropy.

```bash
python code/main.py --mode preprocess
```

*   **Output**: `data/processed/subject_entropy_features.csv`, `data/processed/exclusions.log`.

### 2. Model Training & Evaluation
Train the Ridge Regression and Logistic Ridge models, perform permutation testing, and generate the sensitivity analysis.

```bash
python code/main.py --mode train
```

*   **Output**: `data/processed/model_metrics.json`, plots (saved to `data/figures/`).

### 3. Validation
Run the test suite to ensure the pipeline meets the spec's acceptance criteria.

```bash
pytest tests/ -v
```

## Expected Outputs

*   **`subject_entropy_features.csv`**: 200 entropy columns per subject.
*   **`model_metrics.json`**: Performance metrics (r, AUC) for all three models.
*   **`exclusions.log`**: List of subjects excluded due to motion or short time series.
*   **`figures/`**: Sensitivity plots (r=0.15, 0.20, 0.25) and permutation histograms.

## Troubleshooting

*   **Memory Error**: If you encounter OOM errors, reduce the number of subjects in `config.yaml` (e.g., `max_subjects: 50`).
*   **Missing Data**: If the verified dataset URLs fail, the pipeline will automatically switch to synthetic data mode for **code validation only**. Check `data/processed/data_source.txt` to confirm. **Note**: Synthetic data results are excluded from scientific reporting.
*   **CUDA Errors**: Ensure no GPU-specific libraries are imported. The code is strictly CPU-bound.
