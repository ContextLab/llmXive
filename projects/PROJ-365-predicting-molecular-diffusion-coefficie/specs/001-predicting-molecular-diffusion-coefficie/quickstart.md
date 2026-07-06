# Quickstart: Predicting Molecular Diffusion Coefficients

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a verified dataset (see `research.md` for current status).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-365-predicting-molecular-diffusion-coefficie
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
    *Note: `requirements.txt` pins CPU-only versions of PyTorch and PyTorch Geometric.*

## Data Setup

1.  **Prepare Raw Data**:
    -   Place your CSV file (with `smiles`, `solvent_type`, `diffusion_coefficient`) in `data/raw/`.
    -   Name it `diffusion_data.csv`.
    -   *If no real data is available, run `python code/generate_synthetic_data.py` to create a test dataset.*

2.  **Verify Checksums**:
    -   Run `python code/check_data_integrity.py` to generate checksums in `data/checksums.txt`.

## Running the Pipeline

### 1. Featurization
Convert raw data to graph representations:
```bash
python code/main.py --step featurize
```
*Output*: `data/processed/featurized_data.jsonl`

### 2. Training
Train the MPNN and Baseline:
```bash
python code/main.py --step train
```
*Output*: `artifacts/models/mpnn_fold_*.pt`, `artifacts/models/baseline_fold_*.pt`

### 3. Evaluation & Analysis
Generate metrics, t-tests, and sensitivity reports:
```bash
python code/main.py --step evaluate
```
*Output*: `artifacts/reports/results.json`

## Validation

Run the contract tests to ensure data and outputs match schemas:
```bash
pytest tests/contract/ -v
```

## Troubleshooting

-   **CUDA Error**: The script explicitly checks for GPU. If you see a GPU error, ensure you are not running on a machine with CUDA enabled, or force CPU: `export CUDA_VISIBLE_DEVICES=""`.
-   **Memory Error**: Reduce the dataset size in `code/config.py` (e.g., `max_samples = 1000`).
-   **SMILES Parsing Error**: Check `data/processed/processing_log.txt` for invalid SMILES strings.
