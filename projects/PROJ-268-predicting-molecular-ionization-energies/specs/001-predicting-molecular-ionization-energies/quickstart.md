# Quickstart: Predicting Molecular Ionization Energies

## Prerequisites
- Python 3.11+
- Git
- 7 GB RAM available (local) or access to GitHub Actions (2 CPU, 7 GB RAM).

## Installation

1.  **Clone and Setup**
    ```bash
    git clone <repo-url>
    cd projects/PROJ-268-predicting-molecular-ionization-energies
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

2.  **Verify Dependencies**
    ```bash
    python -c "import torch; import rdkit; print('RDKit and PyTorch ready')"
    ```

## Running the Pipeline

### Option A: Full Pipeline (Download -> Train -> Eval)
```bash
# This will take up to 12 hours on a CPU runner
python code/experiments/train.py --config code/utils/config.yaml
```
*Note: The script automatically handles data download, preprocessing, and splitting. The target variable is -HOMO (proxy for IE).*

### Option B: Step-by-Step

1.  **Download & Preprocess**
    ```bash
    python code/data/download.py
    python code/data/preprocess.py --input data/raw/qm9.parquet --output data/processed/graphs.pt
    ```

2.  **Train Model**
    ```bash
    python code/experiments/train.py --epochs 50 --batch-size 32
    ```

3.  **Run Ablation**
    ```bash
    python code/experiments/ablation.py --model-path code/models/best_model.pth --sigma 0.1 --num-runs 5
    ```
    *Note: The ablation study retrains the model with zeroed features for multiple stochastic runs across baseline and perturbed conditions.*

4.  **Evaluate & Visualize**
    ```bash
    python code/experiments/evaluate.py --model-path code/models/best_model.pth --test-set data/processed/test_set.pt
    ```

## Expected Outputs
- `data/processed/`: Graph datasets and splits.
- `code/models/best_model.pth`: Trained MPNN weights.
- `results/metrics.csv`: MAE, RMSE, Baseline comparisons.
- `results/attribution.json`: Feature importance scores.

## Troubleshooting
- **OOM (Out of Memory)**: Reduce `--batch-size` in `train.py`.
- **Timeout**: The script auto-saves checkpoints. Check `code/models/` for partial results.
- **RDKit Errors**: Ensure SMILES strings are valid. Invalid molecules are logged and skipped.
- **Underpowered Study**: If the pipeline declares the study "underpowered" (N=20k exceeded 6h even after complexity reduction), the results are reported with a clear limitation note.