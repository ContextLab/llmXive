# Quickstart: Predicting Molecular Surface Area from Graph Convolutional Networks

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or local environment with 7 GB+ RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-412-predicting-molecular-surface-area-from-g
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
    *Note: Ensure `torch` is installed as the CPU-only wheel.*

## Running the Pipeline

### 1. Data Ingestion & Preprocessing
Generates the 2D graph features and 3D surface area labels.
```bash
python code/data/ingest.py --source zircon15 --output data/processed/molecules.parquet
python code/data/preprocess.py --input data/processed/molecules.parquet --output data/processed/graphs.parquet
```
*Output: `data/processed/graphs.parquet` containing SMILES, graph features, and surface area labels.*

### 2. Data Splitting
Splits data into train/test sets stratified by molecular weight.
```bash
python code/data/split.py --input data/processed/graphs.parquet --output data/splits/
```
*Output: `data/splits/train.parquet`, `data/splits/test.parquet`.*

### 3. Model Training
Trains the GCN and the Geometry-Based Baseline.
```bash
python code/models/train.py --train data/splits/train.parquet --test data/splits/test.parquet
```
*Output: `results/gcn_model.pt`, `results/baseline_model.pkl`.*

### 4. Evaluation & Sensitivity Analysis
Evaluates models, performs t-tests, and runs the threshold sweep.
```bash
python code/eval/metrics.py --model-gcn results/gcn_model.pt --model-baseline results/baseline_model.pkl --test data/splits/test.parquet
python code/eval/sensitivity.py --predictions data/processed/predictions.parquet
```
*Output: `results/report.md`, `data/processed/sensitivity_results.parquet`.*

## Verification

To verify the pipeline integrity:
```bash
pytest tests/contract/ -v
pytest tests/unit/ -v
```
*Ensure all contract tests pass against the defined YAML schemas.*

## Troubleshooting

- **OOM (Out of Memory)**: Reduce `batch_size` in `code/models/train.py` or filter molecules with > 80 atoms in `preprocess.py`.
- **Conformer Failure**: If >10% of molecules fail 3D generation, check `preprocess.py` parameters (increase `num_attempts` or switch to `ETKDGv3`).
- **CUDA Error**: Ensure `torch` is the CPU version. Run `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
