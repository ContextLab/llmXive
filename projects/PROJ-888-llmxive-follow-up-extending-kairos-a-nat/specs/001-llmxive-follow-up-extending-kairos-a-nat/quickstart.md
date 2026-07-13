# Quickstart: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## Prerequisites

- **Python**: 3.11 or higher
- **System**: Linux (Ubuntu 22.04 recommended for GitHub Actions compatibility)
- **Memory**: At least 8GB RAM (for local testing; 7GB is the hard limit for CI)
- **Disk**: 14GB free space

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to a CPU-only wheel to ensure compatibility with the target CI environment.*

## Data Setup

The project automatically downloads the verified LIBERO dataset on first run.

1.  **Run Data Download**:
    ```bash
    python code/data/download_libero.py
    ```
    This script fetches the Parquet files from the verified HuggingFace URLs and checksums them.

2.  **Verify Data**:
    Check `data/raw/` for the downloaded Parquet files and the `checksums.txt` manifest.

## Running the Pipeline

### 1. Quantization (Phase 1)
Convert continuous data to discrete JSON vectors.
```bash
python code/data/quantize.py --bit-depth 4 --noise-std 0.1 --output-dir data/processed
```
*Options*: `--bit-depth` (4, 8, 16), `--noise-std` (0.0, 0.1, 0.3, 0.5).

### 2. Training (Phase 2)
Train the Kairos adapter on CPU.
```bash
python code/models/training_loop.py --config config/training.yaml --epochs 100
```
*Note*: The training loop includes a 6-hour graceful exit and checkpointing.

### 3. Analysis (Phase 3)
Compute error metrics and statistical tests.
```bash
python code/analysis/stats.py --input data/results/error_metrics.csv --output data/final_report.csv
```

## Testing

Run the full test suite:
```bash
pytest tests/
```

- **Unit Tests**: Verify quantization logic and noise injection.
- **Contract Tests**: Validate JSON outputs against `contracts/*.schema.yaml`.
- **Integration Tests**: Run a mini-pipeline (download -> quantize -> train 1 epoch -> evaluate).

## Resource Monitoring

To verify compliance with the 7GB RAM limit during local runs:
```bash
# Monitor RAM usage in a separate terminal
watch -n 1 'ps aux | grep python'
```
The training script logs peak RAM usage to `logs/training.log`.
