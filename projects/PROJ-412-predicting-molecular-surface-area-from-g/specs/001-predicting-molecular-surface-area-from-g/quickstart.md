# Quickstart: Predicting Molecular Surface Area from Graph Convolutional Networks

## Prerequisites

- Python 3.11+
- Git
- 7 GB+ RAM (recommended)
- Internet connection (for dataset download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-412-predicting-molecular-surface-area-from-g
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` includes `torch` (CPU), `rdkit`, `pandas`, `scikit-learn`, `datasets`.*

4.  **Verify installation**:
    ```bash
    python -c "import rdkit; import torch; print('RDKit and PyTorch loaded successfully')"
    ```

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### Step 1: Data Ingestion & Preprocessing
Downloads ZINC15, generates 2D graphs and 3D conformers, and splits the data.
```bash
python code/main.py --stage preprocess
```
*Outputs*: `data/processed/paired_dataset.parquet`, `data/processed/conformer_params.json`.

### Step 2: Model Training
Trains the GCN and the 2D Topology Baseline.
```bash
python code/main.py --stage train
```
*Outputs*: `results/models/gcn_model.pt`, `results/models/baseline_model.pkl`.

### Step 3: Evaluation & Sensitivity Analysis
Compares models, performs t-tests, and runs sensitivity analysis.
```bash
python code/main.py --stage eval
```
*Outputs*: `results/reports/evaluation_report.md`, `results/plots/sensitivity_curve.png`.

## Verification

To verify the pipeline ran correctly:
1.  Check `data/raw/checksums.json` for valid checksums.
2.  Inspect `results/reports/evaluation_report.md` for the paired t-test p-value.
3.  Run unit tests:
    ```bash
    pytest tests/unit/ -v
    ```
4.  Run contract tests:
    ```bash
    pytest tests/contract/ -v
    ```

## Troubleshooting

- **RAM Error**: If you encounter OOM errors, the dataset may be too large. The pipeline automatically streams data. If issues persist, reduce the `max_samples` parameter in `code/main.py`.
- **3D Generation Failure**: If >10% of molecules fail 3D generation, check `data/processed/failure_report.csv`. This may indicate poor quality SMILES in the source.
- **CUDA Error**: If you have a GPU but want to force CPU, set `CUDA_VISIBLE_DEVICES=""` before running.
