# Quickstart: Predicting the Elastic Moduli of 2D Materials

## Prerequisites

- Python 3.11+
- 7GB+ RAM available (for local testing; CI enforces this limit)
- Internet connection (to download datasets from Materials Project API)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    cd projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    # Install CPU-only PyTorch
    pip install torch --index-url https://download.pytorch.org/whl/cpu

    # Install other dependencies
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed in three main stages: Ingestion, Training, and Analysis.

### Step 1: Data Ingestion & Graph Construction
Download and process the data. This step filters for 2D materials with complete elastic tensors and performs a bias check.
```bash
python code/ingest/download.py --output data/raw
python code/ingest/bias_check.py --input data/raw --output data/bias_report.json
python code/ingest/parse_cif.py --input data/raw --output data/processed
python code/ingest/filter.py --input data/processed --output data/filtered
```
*Expected Output*: `data/filtered/materials.csv`, `data/processed/graphs/`, and `data/bias_report.json`.

### Step 2: Model Training
Train the lightweight GNN with 5-fold cross-validation and Early Stopping.
```bash
python code/model/train.py --data-dir data/filtered --epochs 100 --patience 3 --split-strategy family
```
*Note*: The `--epochs` flag is set to a high value (100) but training will stop early based on validation loss.
*Expected Output*: `code/model/checkpoints/`, `code/model/metrics_report.json`.

### Step 3: Evaluation & Analysis
Compute SHAP interaction values and ablation study results.
```bash
python code/analysis/importance.py --model-path code/model/checkpoints/best.pt --data-dir data/filtered
python code/analysis/ablation.py --model-path code/model/checkpoints/best.pt --data-dir data/filtered
```
*Expected Output*: `code/analysis/shap_results.csv`, `code/analysis/ablation_report.json`.

## Verification

To verify the installation and data pipeline without full training:
```bash
pytest tests/unit/test_parse_cif.py -v
pytest tests/integration/test_pipeline.py --max-samples 10
```

## Troubleshooting

- **DataUnavailableError**: If the dataset contains fewer than 5 unique material families with complete tensors, the pipeline will halt. This is expected behavior per the Data Availability Gate.
- **Memory Error**: If you encounter `RuntimeError: CUDA out of memory` (unexpected on CPU) or `MemoryError`, ensure you are using the CPU-only PyTorch build and that the dataset has been filtered to < 1000 samples.
- **Missing Elastic Tensors**: The unified source ensures this does not happen. If it does, check the `ingest/filter.py` logs.
- **Data Download Fails**: Ensure your network allows access to `materialsproject.org` or the configured API endpoint.