# Quickstart: Predicting Molecular Surface Area from Graph Convolutional Networks

## Prerequisites

-   Python 3.10+
-   Git
-   (Optional) Docker for isolated environment testing

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-412-predicting-molecular-surface-area-from-g
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` includes PyTorch (CPU), PyTorch Geometric (CPU), RDKit, and HuggingFace datasets.*

## Data Preparation

1.  **Download and Ingest**:
    Run the ingestion script to fetch ZINC15 and generate checksums.
    ```bash
    python code/data/ingest.py
    ```
    *Output*: `data/raw/zinc_processed.parquet`, `data/raw/checksums.json`.

2.  **Preprocess**:
    Generate 2D graphs, 3D conformers, and surface area labels.
    ```bash
    python code/data/preprocess.py --max-atoms 100 --threshold 0.1
    ```
    *Output*: `data/processed/graphs_with_features.parquet`, `data/processed/conformer_params.json`.

## Model Training

1.  **Train GCN**:
    ```bash
    python code/train/train_gcn.py --epochs 50 --patience 5
    ```
    *Output*: `results/models/gcn_model.pt`, `results/reports/training_log.json`.

2.  **Run Geometry Baseline**:
    ```bash
    python code/train/train_baseline.py
    ```
    *Output*: `results/models/baseline_model.pkl`.

## Evaluation

1.  **Evaluate Models**:
    ```bash
    python code/eval/evaluate.py
    ```
    *Output*: `results/reports/comparison_report.json` (MAE, RMSE, R², t-test p-value).

2.  **Sensitivity Analysis**:
    ```bash
    python code/eval/sensitivity.py --thresholds 1.0 5.0 10.0
    ```
    *Output*: `results/reports/sensitivity_analysis.json`, `results/plots/sensitivity_curve.png`.

## Verification

1.  **Run Tests**:
    ```bash
    pytest tests/ -v
    ```
    *Includes*: Unit tests for preprocessing, contract tests for schema validation, integration tests for the full pipeline.

2.  **Check Reproducibility**:
    Re-run the pipeline with `--seed 42` to verify identical results.
