# Quickstart: Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions free-tier runner (or local machine with sufficient RAM)

## Setup

1. **Clone the Repository**
   ```bash
   git clone <repo-url>
   cd projects/PROJ-404-predicting-molecular-surface-charge-dist
   ```

2. **Install Dependencies**
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` includes `torch`, `torch-geometric`, `rdkit`, `datasets`.*

3. **Verify Data Availability**
   The system will automatically download the QM9 dataset from the verified Hugging Face URL on first run. Ensure internet access is available.

## Execution

### 1. Data Loading & Validation
Run the data loader to verify the dataset and memory constraints.
```bash
python code/data/loader.py --check-memory
```
*Expected Output*: Summary of loaded features, memory usage, and validation status (Pass/Fail).

### 2. Preprocessing & Splitting
Generate scaffold-based splits and normalize coordinates.
```bash
python code/data/preprocess.py --seed 42
```
*Expected Output*: `data/processed/splits.json` and normalized tensor files.

### 3. Training
Train the Geometric GNN (SchNet) on CPU.
```bash
python code/train.py --epochs 100 --patience 10 --seed 42
```
*Expected Output*: `models/schnet_model.pt` and `reports/training_log.json`.
*Note*: This step may take up to 6 hours. Early stopping will trigger if validation MAE does not improve for a specified patience period..

### 4. Evaluation & Baseline Comparison
Evaluate the trained model and compare against the 2D baseline.
```bash
python code/eval.py --model models/schnet_model.pt
```
*Expected Output*: `reports/results.md` containing MAE, RMSE, R, and a pass/fail status for the hypothesis (MAE <= 0.05 e).

## Troubleshooting

- **OOM Error**: If the loader fails, reduce the sample size in `code/data/loader.py` (e.g., `max_samples=20000`).
- **CUDA Error**: The script is designed for CPU. If CUDA is detected, force CPU mode by setting `CUDA_VISIBLE_DEVICES=""` or modifying `device="cpu"` in the code.
- **Missing Charges**: If the dataset lacks Merz-Kollman charges, the script will halt with `DATA_SCHEMA_MISMATCH`. Check the Hugging Face dataset schema.

## Success Criteria

- The training loop completes at least 10 epochs.
- The final model MAE is lower than the 2D baseline MAE.
- The `results.md` report is generated with all required metrics.
