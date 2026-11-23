# Quickstart: Assessing Uncertainty Quantification Techniques for Machine‑Learning Predicted Material Properties

## Prerequisites

*   Python 3.10+
*   Git
*   Access to Hugging Face Hub (no token required for public datasets)

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-764-assessing-uncertainty-quantification-tec
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins versions for `torch`, `gpytorch`, `scikit-learn`, `datasets`.*

## Data Download & Preprocessing

Run the data pipeline to download the OQMD subset, validate, split, and transform:

```bash
python code/data/download.py
python code/data/validation.py
python code/data/preprocess.py
```

**Expected Outputs**:
*   `data/raw/oqmd_subset.parquet` (Checksummed)
*   `data/processed/raw_train.csv`, `raw_val.csv`, `raw_test.csv`
*   `data/processed/pca_transformer.pkl`
*   `data/validation_report.json`

## Training & UQ Inference

Execute the full pipeline (training, inference, evaluation) with a 5-hour timeout:

```bash
# Set environment variable for timeout (optional, default is 5h)
export PIPELINE_TIMEOUT=18000

python code/main.py
```

**What this runs**:
1.  **Baseline NN**: Trains and saves `results/models/baseline_nn_arch.pt`.
2.  **Deep Ensemble**: Trains 5 models, saves to `results/models/ensemble/`.
3.  **MC-Dropout**: Trains model, runs 30 passes, saves predictions.
4.  **Sparse GP**: Fits PCA, trains GP, saves predictions.
5.  **Evaluation**: Computes ECE, Interval Scores, and Screening Precision.

**Expected Outputs**:
*   `results/models/` (Checkpoints)
*   `results/predictions/uq_predictions_*.csv`
*   `results/metrics/calibration_summary.csv`

## Verification

Run the test suite to verify contract compliance and result integrity:

```bash
pytest tests/ -v
```

**Key Checks**:
*   Model parameter count ≤ 10,000.
*   Prediction CSVs contain required columns.
*   ECE values are within theoretical bounds.
*   Screening precision > random baseline (if applicable).

## Troubleshooting

*   **Timeout**: If the pipeline exceeds 5 hours, check `results/logs/timeout.log`. Reduce dataset size in `config.yaml` (e.g., `max_samples: 5000`).
*   **GP Convergence**: If Sparse GP fails, check `results/logs/gp_error.log`. The pipeline will fallback to Ensemble/MC-Dropout results.
*   **Missing Data**: Check `data/validation_report.json` for excluded rows.
