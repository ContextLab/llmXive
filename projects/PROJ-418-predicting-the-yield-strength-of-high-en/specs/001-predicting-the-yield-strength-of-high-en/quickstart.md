# Quickstart: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

## Prerequisites

- Python 3.11+
- Git
- **Verified Data Source**: A verified URL for HEA compositions must exist in the project's "Verified datasets" block. If not, the pipeline will terminate with `DATA_SOURCE_MISSING`.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-418-predicting-the-yield-strength-of-high-en
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Data Setup

1.  **Download Reference Data**:
    The `WebElements` dataset is downloaded automatically by the pipeline from the verified URL.
    ```bash
    # The download script handles this, but you can manually verify:
    curl -L "https://huggingface.co/datasets/Mandala1/webelements/resolve/main/data/test-00000-of-00001.parquet" -o data/raw/webelements.parquet
    ```

2.  **Verify HEA Composition Data**:
    The pipeline **does not** accept local files for HEA compositions. It requires a verified URL.
    - Check the `research.md` "Verified datasets" block for a valid HEA composition URL.
    - If no such URL exists, the pipeline will terminate with `DATA_SOURCE_MISSING`.
    - **Note**: Do not attempt to place a local CSV file in `data/raw/`. The pipeline is designed to fail if the data source is not verified.

## Running the Pipeline

Execute the main script:

```bash
python code/main.py
```

**What happens**:
1.  **Verify Sources**: Checks for a verified HEA composition URL. If missing, exits with `DATA_SOURCE_MISSING`.
2.  **Download**: Fetches `WebElements` and HEA composition data (if verified URL exists).
3.  **Filter**: Keeps only single-phase alloys tested at 20-25°C.
4.  **Calculate**: Computes δ, Δχ, VEC, mixing entropy, melting variance.
5.  **Train**: Runs RF, GB, and Linear Regression (5-fold CV).
6.  **Validate**: Performs permutation testing (conditional), bootstrap, VIF (baseline only).
7.  **Output**: Writes `output/metrics.json` and plots to `output/plots/`.

## Verification

1.  **Check Metrics**:
    ```bash
    cat output/metrics.json
    ```
    Verify that `R2`, `MAE`, `RMSE` are present for all models.

2.  **Check Data Status**:
    Look for `data_status` in the JSON output to confirm N values and power flags.

3.  **Check Collinearity**:
    Ensure VIF values are reported for the linear baseline. If any VIF > 10, the report will flag "Baseline collinearity detected".

## Troubleshooting

- **Error: "DATA_SOURCE_MISSING"**:
  - No verified HEA composition URL exists in the "Verified datasets" block. The pipeline cannot proceed without a verified source.
- **Error: "Insufficient Power"**:
  - The verified dataset yielded N < 50. Statistical tests were skipped.
- **Error: "Missing elemental property for [Element]"**:
  - The `WebElements` dataset may not have the element. The pipeline will exclude that composition.
- **Runtime > 6 hours**:
  - Reduce `n_estimators` in `code/models/train.py` (default is 50).
  - Reduce bootstrap resamples (default is 1000).