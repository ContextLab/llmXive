# Quickstart: Investigating the Correlation Between Molecular Structure and Dye‑Sensitized Solar Cell Performance

## Prerequisites
- Python 3.10+
- pip
- Git

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-158-investigating-the-correlation-between-mo
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `torch-geometric` installation may require specific version matching with `torch`. The `requirements.txt` will pin compatible versions for CPU.*

## Running the Pipeline

### Step 1: Data Download and Preprocessing
Download the dataset and standardize molecules.
```bash
python code/data/download.py
python code/data/preprocess.py
```
*Output*: `data/processed/graph_data.pt`, `data/failed_molecules.log`

### Step 2: Training and Evaluation
Train GCN and Random Forest models with scaffold-aware CV.
```bash
python code/models/train.py
```
*Output*: `results/metrics.json`, `results/model_artifacts/`

### Step 3: Interpretability
Extract motifs from the trained GCN.
```bash
python code/analysis/interpret.py
```
*Output*: `results/motifs.json`

## Verification
To verify the pipeline on a fresh runner:
1. Delete `data/processed/` and `results/`.
2. Run the commands above sequentially.
3. Check `results/metrics.json` for valid MAE/R² values.
4. Ensure `data/failed_molecules.log` exists (even if empty).

## Troubleshooting
- **CUDA Error**: Ensure `CUDA_VISIBLE_DEVICES=""` is set or remove any `device='cuda'` calls. The code defaults to CPU.
- **Memory Error**: Reduce `batch_size` in `train.py` if OOM occurs (unlikely on this dataset size).
- **Invalid SMILES**: Check `data/failed_molecules.log` for the problematic strings.
