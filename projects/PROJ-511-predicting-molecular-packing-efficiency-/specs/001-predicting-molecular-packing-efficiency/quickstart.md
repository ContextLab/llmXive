# Quickstart: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to the Crystallography Open Database (internet required for download)

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-511-predicting-molecular-packing-efficiency-/
    python -m venv venv
    source venv/bin/activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import rdkit; import torch; print('Dependencies OK')"
    ```

## Running the Pipeline

### Step 1: Data Acquisition & Feature Engineering
Download COD Organic Subset, generate SMILES, and compute features.
```bash
python code/data/download_cod.py
python code/data/generate_smiles.py
python code/data/compute_features.py
```
*Output*: `data/processed/dataset.csv`, `data/data_provenance.json`

### Step 2: Model Training
Train the Baseline and Upper Bound models on the processed dataset.
```bash
python code/models/trainer.py
```
*Output*: `models/baseline_checkpoint.pt`, `models/upper_bound_checkpoint.pt`, `results/training_log.json`

### Step 3: Evaluation & Robustness
Run validation, permutation tests (1,000 shuffles), and threshold sweeps.
```bash
python code/analysis/diagnostics.py
python code/analysis/robustness.py
```
*Output*: `results/validation_report.json`

### Step 4: Generate Report
Create the final HTML report.
```bash
python code/report/generate_report.py
```
*Output*: `results/report.html`

## Validation

Run the contract tests to ensure data and outputs match schemas:
```bash
pytest tests/contract/
```

## Troubleshooting

- **Memory Error**: Ensure `data/processed/dataset.csv` is not loaded entirely into RAM at once if N > 2000. The pipeline uses chunked processing.
- **CUDA Error**: If `ImportError: No module named 'torch.cuda'` appears, ensure the CPU-only version of PyTorch was installed (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
- **Missing SMILES**: If the script fails to generate SMILES, check the CIF coordinates for validity. Corrupt CIFs are logged in `data/logs/parsing_errors.log`.
- **Runtime Error**: If the pipeline exceeds 4 hours, check the `data_provenance.json` to ensure the correct subset was downloaded.