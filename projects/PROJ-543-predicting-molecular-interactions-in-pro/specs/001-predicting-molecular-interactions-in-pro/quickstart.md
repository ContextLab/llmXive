# Quickstart: Predicting Molecular Interactions in Protein-Ligand Complexes

## Prerequisites

- Python 3.11+
- Git
- (Optional) Kaggle CLI for GPU offload (if CPU training is too slow).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-543-predicting-molecular-interactions-in-pro
    ```

2.  **Initialize Git repository and create .gitignore**:
    ```bash
    git init
    echo "data/raw/*" > .gitignore
    echo "data/processed/*" >> .gitignore
    echo "data/results/*" >> .gitignore
    echo "__pycache__/" >> .gitignore
    echo "*.pyc" >> .gitignore
    echo "venv/" >> .gitignore
    ```

3.  **Create and activate the virtual environment**:
    ```bash
    python -m venv code/venv
    source code/venv/bin/activate  # Linux/Mac
    # or: code\venv\Scripts\activate  # Windows
    ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins versions for `torch`, `torch_geometric`, `rdkit`, `black`, `flake8`, etc.*

5.  **Configure linting**:
    Create `pyproject.toml` with Black settings and `setup.cfg` for flake8 as per `requirements.txt`.

6.  **Initialize the data directory structure**:
    ```bash
    mkdir -p data/raw data/processed data/results data/reference
    ```

7.  **Create placeholder pharmacophore reference**:
    ```bash
    echo "[]" > data/reference/pharmacophores.json
    ```

## Running the Pipeline

### 1. Data Ingestion & Graph Construction
Download the PDBbind dataset and construct graphs (with 5.0 Å cutoff).
```bash
python code/main.py --mode ingest --resolution-cutoff 2.0
```
- This will download data to `data/raw/`, filter complexes with resolution > 2.0 Å, and save graphs to `data/processed/`.
- Output: `data/results/sensitivity_analysis.json` (edge count vs. cutoff).

### 2. Model Training
Train the 3-layer GNN.
```bash
python code/main.py --mode train --epochs 50
```
- **CPU Mode**: Runs on default CPU.
- **GPU Mode**: If `CUDA_VISIBLE_DEVICES` is set, it runs on GPU. The pipeline automatically detects if the job exceeds 4 hours on CPU and suggests offloading.

### 3. Interpretability & Validation
Generate importance maps, cluster motifs, and validate against pharmacophores.
```bash
python code/main.py --mode interpret --test-split 0.1
```
- Output: `data/results/interpret/motif_clusters.json` with FDR-corrected p-values and `data/results/metrics.json` with SC-001/SC-003 metrics.

## Verification

Run the unit tests to ensure the environment is set up correctly:
```bash
pytest tests/unit/
```

Run the integration test on a small subset (10 complexes):
```bash
python code/main.py --mode full-pipeline --subset 10
```
- This verifies the end-to-end flow: Ingest -> Train -> Interpret -> Report.

## Troubleshooting

- **Memory Error**: Reduce `--batch-size` in `config.py` or enable `streaming=True` in the ingest script.
- **CUDA Error**: If running on GitHub Actions, the job will automatically offload to Kaggle if a CUDA device is requested but not found locally.
- **Missing PDB Data**: If a complex ID is missing from the Hugging Face source, the script will skip it and log a warning.
