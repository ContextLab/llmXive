# Quickstart: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace Hub (no token required for public datasets, but recommended for rate limits)
- (Optional) Kaggle account for GPU offload (automatic if CPU fails)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-882-llmxive-follow-up-extending-delta-discri
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline is designed to run end-to-end. It will automatically attempt CPU execution and offload to Kaggle GPU if the Oracle step requires it.

### Step 1: Download and Filter Data
```bash
python code/download_gsm8k.py
```
*Output*: `data/raw/gsm8k_verified.parquet`

### Step 2: Generate Oracle Coefficients (DelTA)
*Note: This step requires GPU. If run on CPU, it will exit with ERR_GPU_REQUIRED to trigger offload.*
```bash
python code/generate_oracle.py
```
*Output*: `data/processed/delta_coefficients.json`
*Checks*: Aborts if variance <= 1e-9 or insufficient data.

### Step 3: Extract Static Features
```bash
python code/extract_features.py
```
*Output*: `data/processed/static_features.parquet`

### Step 4: Train the Predictor Model
*Runs on CPU.*
```bash
python code/models/train.py
```
*Output*: `data/processed/mlp_model.pt`

### Step 5: Evaluate and Generate Metrics
```bash
python code/eval/metrics.py
```
*Output*: `data/processed/predictions.json`

## Verification

To verify the results, inspect the `predictions.json` file:
- Check `metrics.spearman_correlation` against the random baseline.
- Check `metrics.p_value` for statistical significance (< 0.05).
- Check `metrics.classification` to see if the signal is deemed "emergent" or "poor proxies".

## Troubleshooting

- **CUDA Out of Memory**: The script automatically attempts to reduce batch size or use 8-bit quantization. If it still fails, ensure you are running on the Kaggle GPU environment (if triggered).
- **Dataset Not Found**: Ensure internet access is available. The script uses `datasets.load_dataset` which caches data locally.
- **Variance Error**: If `ERR_TRIVIAL_TARGET` is raised, the DelTA coefficients are all identical (likely a bug in the gradient computation or a dataset issue). Check the logs in `data/processed/delta_coefficients.json` for details.
