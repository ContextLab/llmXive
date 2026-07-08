# Quickstart: The Impact of Perceived AI Personality Consistency on User Trust (Revised Scope)

## Prerequisites

- Python 3.11+
- Git
- Sufficient Disk Space (for raw data + processing)
- GB+ RAM (GitHub Actions Free Tier compatible)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-502-the-impact-of-perceived-ai-personality-c
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
    *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only runners.*

## Running the Pipeline

### 1. Data Ingestion
Download and filter the dataset.
```bash
python code/ingestion.py --config code/config.yaml
```
- **Output**: `data/processed/sessions_filtered.parquet`.
- **Check**: Ensure `sessions_filtered.parquet` contains only sessions with ≥3 turns.

### 2. Metric Computation
Compute consistency and lagged engagement indicators.
```bash
python code/metrics.py --input data/processed/sessions_filtered.parquet --output data/processed/sessions_metrics.csv
```
- **Output**: `data/processed/sessions_metrics.csv`.
- **Note**: This step uses dynamic batching to stay within 7GB RAM.

### 3. Statistical Analysis
Run GLM and Linear Regression.
```bash
python code/analysis.py --input data/processed/sessions_metrics.csv --output output/results.json
```
- **Output**: `output/results.json` (coefficients, p-values), `output/figures/*.png`.

### 4. Verification
Run the test suite to verify metric calculations and schema compliance.
```bash
pytest tests/ -v --cov=code
```

## Configuration

- **Fallback Model**: Set `SENTIMENT_MODEL_FALLBACK` environment variable to use an alternative CPU model.
  ```bash
  export SENTIMENT_MODEL_FALLBACK="distilbert-base-uncased-finetuned-sst-2-english"
  ```
- **Memory Limit**: Adjust `MAX_RAM_GB` in `code/config.yaml` if running on a different machine.

## Troubleshooting

- **OOM Error**: The script automatically reduces batch size. If it fails, check `MAX_RAM_GB` in config.
- **Model Load Error**: Verify internet connectivity for HuggingFace model download. If offline, ensure the model is cached in `~/.cache/huggingface`.
- **Validity Flag**: The Proxy Validity Analysis has been removed. The study proceeds with the explicit acknowledgment that findings are limited to human dialogue dynamics.