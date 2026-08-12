# Quickstart: Zero-Shot Drift Detection for AgentDoG 1.5

## Prerequisites

-   Python 3.11+
-   `pip`
-   Access to Hugging Face (for `datasets` library)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Dependencies*: `datasets`, `sentence-transformers`, `scikit-learn`, `pandas`, `numpy`, `torch`, `statsmodels`, `openai`, `pytest`.

3.  **Verify environment**:
    ```bash
    python code/config.py --verify
    # Expected: RANDOM_SEED=42, MAX_RAM_GB=7, BATCH_SIZE=64
    ```

## Running the Pipeline

The pipeline consists of three main stages: Data Fetching, Drift Scoring, and Validation.

### Step 1: Fetch & Prepare Data
Downloads the `AI45Research/ATBench` dataset and computes taxonomy centroids from the *AgentDoG 1.5* paper.
```bash
python -m code.data_loader --streaming --output data/raw/atbench.parquet
python -m code.taxonomy_builder --source "agentdog_1_5_paper" --output data/processed/taxonomy_centroids.json
```
*Note*: This step streams the data to avoid memory overflow. The taxonomy is derived from external definitions.

### Step 2: Compute Drift Scores
Calculates the drift score for every log entry.
```bash
python -m code.drift_scoring --input data/raw/atbench.parquet --taxonomy data/processed/taxonomy_centroids.json --output data/processed/drift_results.csv
```
*Output*: `drift_results.csv` containing `log_id`, `drift_score`, `review_flag`.

### Step 3: Validate & Compare
Performs statistical validation and baseline comparison.
```bash
# For CI (using Gold-Standard Proxy)
python -m code.validation --drift data/processed/drift_results.csv --ground_truth data/raw/atbench.parquet --annotations data/processed/gold_standard_proxy.csv --output data/processed/validation_report.json

# For Production (using real human annotations)
python -m code.validation --drift data/processed/drift_results.csv --ground_truth data/raw/atbench.parquet --annotations data/processed/human_annotations.csv --output data/processed/validation_report.json
```
*Output*: `validation_report.json` with p-values, Cohen's d, Kappa scores, AUC-ROC, and inference time.

## Verification

Run the test suite to ensure contract compliance:
```bash
pytest tests/ -v
```

## Troubleshooting

-   **Memory Error**: Ensure `--streaming` is used in `data_loader`.
-   **Missing Taxonomy**: If `taxonomy_centroids.json` is missing, run `taxonomy_builder` first.
-   **Reproducibility**: Delete `data/` and re-run to verify checksums match.
-   **Timestamps**: If timestamps are missing in source, they are derived deterministically from `log_id`.
