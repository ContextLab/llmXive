# Quickstart: Machine-Learned Potentials for Transition-Metal Catalysis

## Prerequisites

*   Python 3.11+
*   `pip` or `conda`
*   Access to the project repository

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or: venv\Scripts\activate  # Windows
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for CPU-only compatibility (e.g., `torch` CPU wheel).*

## Data Setup

1.  **Download Datasets**: Run the ingestion script to fetch verified datasets.
    ```bash
    python src/data/ingest.py --fetch
    ```
    *This script downloads from the verified URLs and computes checksums.*
2.  **Verify Data**:
    ```bash
    python src/data/ingest.py --verify
    ```

## Running the Pipeline

### 1. Graph Construction
Convert raw geometries to graph representations.
```bash
python src/data/graph_construction.py
```
*Output: `data/processed/graphs.parquet`*

### 2. Training
Train an ensemble of SchNet models (CPU-only).
```bash
python src/models/ensemble.py --epochs 30 --seed 42
```
*Output: `models/ensemble_weights/` and `data/processed/training_metrics.json`*

### 3. Prediction & Evaluation
Generate predictions and compute metrics.
```bash
python src/models/predict.py --test-split
```
*Output: `data/processed/predictions.parquet` and `data/processed/metrics.json`*

### 4. Analysis
Perform feature attribution and statistical testing.
```bash
python src/analysis/feature_importance.py
python src/analysis/statistics.py
```
*Output: `data/results/feature_importance.csv` and `data/results/statistical_tests.json`*

## Verification

To ensure reproducibility, run the full pipeline from scratch:
```bash
./scripts/run_full_pipeline.sh
```
*This script executes all steps in order and validates checksums.*

## Troubleshooting

*   **Memory Error**: Reduce `--batch-size` in `ensemble.py`.
*   **CUDA Error**: Ensure `torch` is installed with CPU support (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
*   **Data Scarcity**: If <120 reactions are found, the pipeline will flag this in logs but proceed with available data (FR-001b).
