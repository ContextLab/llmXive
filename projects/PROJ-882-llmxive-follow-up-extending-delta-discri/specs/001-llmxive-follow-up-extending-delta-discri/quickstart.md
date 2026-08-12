# Quickstart: llmXive follow-up: extending "DelTA"

## Prerequisites

*   Python 3.11+
*   Git
*   Access to HuggingFace (for dataset download)
*   (Optional) Kaggle account for GPU offload (if CPU fails)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-882-llmxive-follow-up-extending-delta-discri
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins versions for `transformers`, `torch`, `datasets`, `scikit-learn`, `nltk`, `scipy`, `pandas`, `pyarrow`, `sentence-transformers`.*

4.  **Download NLP models**:
    ```bash
    python -m nltk.downloader punkt stopwords averaged_perceptron_tagger
    ```

## Execution

The pipeline is designed to run end-to-end.

### Step 1: Data Download
```bash
python code/data/download_gsm8k.py
```
*   Downloads GSM8K, filters for verified solutions, and saves to `data/raw/gsm8k_verified.parquet`.
*   **Check**: Verify `data/raw/gsm8k_verified.parquet` exists and has > 500 rows.

### Step 2: Oracle Generation (Ground Truth)
```bash
python code/models/generate_oracle.py
```
*   Loads Llama-3-8B. If this fails (OOM/Timeout), it automatically switches to Llama-3-1B.
*   Computes DelTA coefficients.
*   **Note**: This step is computationally intensive. If running on a CPU-only CI runner, it may take up to 6 hours. If it fails due to OOM, the system will auto-offload to a GPU.
*   **Check**: Verify `data/processed/delta_coefficients.json` exists and variance > 1e-9.

### Step 3: Feature Extraction
```bash
python code/data/extract_features.py
```
*   Extracts n-grams, POS, and semantic similarity using **sentence-transformers/all-MiniLM-L6-v2**.
*   **Check**: Verify `data/processed/static_features.parquet` exists.

### Step 4: Model Training
```bash
python code/models/train.py
```
*   Trains the 2-layer MLP on CPU.
*   **Check**: Verify `data/processed/mlp_model.pt` exists.

### Step 5: Evaluation
```bash
python code/eval/metrics.py
```
*   Computes Spearman correlation, cluster-robust permutation test, and feature importance.
*   **Check**: Verify `data/processed/metrics_report.json` and `data/processed/predictions.json`.

## Testing

Run the test suite:
```bash
pytest tests/
```

## Troubleshooting

*   **OOM Error in Oracle Step**: If the script crashes with "CUDA out of memory" or "CPU out of memory", the execution stage will retry on a Kaggle GPU. If 8B fails, it will automatically switch to 1B.
*   **Variance Check Failed**: If `generate_oracle.py` exits with "Variance <= 1e-9", the DelTA algorithm failed to find a signal. Check the model loading and input data.
*   **Missing Dependencies**: Ensure `requirements.txt` is up to date and installed in the virtual environment.
