# Quickstart: Predicting Molecular Refractive Indices

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to a Linux environment (GitHub Actions or local Linux VM).
- 7GB RAM minimum.

## Installation

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-296-predicting-molecular-refractive-indices-/code
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   # Ensure PyTorch Geometric CPU version is installed
   pip install torch-geometric torch-scatter torch-sparse torch-cluster torch-spline-conv -f https://data.pyg.org/whl/torch-2.0.0+cpu.html
   ```

3. **Verify RDKit**:
   ```bash
   python -c "import rdkit; print(rdkit.__version__)"
   ```

## Data Download

Run the download script to fetch the dataset:
```bash
python data/download.py
```
This will:
1. Fetch the verified dataset from Hugging Face.
2. Calculate and store the checksum.
3. Save raw data to `data/raw/`.

## Preprocessing

Process the data and create splits:
```bash
python data/preprocess.py --filter-mw 500 --split-ratio 0.8,0.1,0.1
```
This will:
1. Parse SMILES.
2. Filter molecules with MW > 500.
3. Perform scaffold split.
4. Save `train.csv`, `val.csv`, `test.csv` to `data/processed/`.

## Training

Train the MPNN model:
```bash
python training/train.py --epochs 100 --batch-size 32 --seed 42
```
- **Output**: `models/mpnn.pt`, `logs/training.log`.
- **Time**: ~1-3 hours on CPU.

## Evaluation & Interpretation

Run the full evaluation and attribution pipeline:
```bash
python training/evaluate.py --model models/mpnn.pt
python models/attribution.py --model models/mpnn.pt --output results/attributions.csv
```
- **Output**: `results/metrics.csv`, `results/plots/parity.png`, `results/plots/importance.png`.

## Verification

Check that the pipeline completed successfully:
```bash
python -c "
import pandas as pd
df = pd.read_csv('results/metrics.csv')
assert df['mae_gnn'].iloc[0] < 1.0, 'MAE too high'
assert df['p_value'].iloc[0] < 0.05, 'Not statistically significant'
print('All checks passed.')
"
```
