# Quickstart: Predicting Phase‑Change Suitability with Machine‑Learning

This guide shows how to reproduce the entire analysis on a fresh GitHub Actions runner (or locally) in < 5 minutes.

## Prerequisites
- Python 3.11 (installed via `pyenv` or system Python).
- Internet access (to download the open PCM dataset, OMDB structures, and NIST validation set).
- Optional: an API key for the Materials Project (not required for the default run).

## Setup

```bash
# 1. Clone the repository (assume you are in the project root)
git clone
cd phase-change-ml

# 2. Create a clean virtual environment
python -m venv.venv
source.venv/bin/activate

# 3. Install exact dependencies
pip install -r requirements.txt
```

## Run the Full Pipeline

```bash
# The top‑level Makefile orchestrates the ordered tasks.
make all
```

`make all` executes the following steps (see `plan.md` for details):

1. **Download data** – streams the PCM parquet file into `data/raw/pcm.parquet`.
2. **Download structures** – pulls CIFs from the OMDB structures dataset into `data/raw/omdb_structures/`.
3. **Compute elemental descriptors** – produces `data/processed/elemental_features.csv`.
4. **(Optional) Build crystal graphs** – runs only for compounds with a CIF; missing‑structure rows receive `has_structure=0` and are logged.
5. **Merge features & create train/val/test splits** – `data/processed/full_dataset.csv`.
6. **Train baseline models** – Random Forest & XGBoost; results in `data/results/baseline_*.json`.
7. **Train shallow MLP baseline** – CPU‑only PyTorch model; results in `data/results/deep_mlp.json`.
8. **SHAP analysis** – `data/results/shap_importances.json`.
9. **Symbolic regression (PySR)** – `data/results/pysr_formulas.json`.
10. **Threshold & feature‑importance sweeps** – `data/results/threshold_sweep.json`.
11. **External validation** – applies symbolic rules to the **NIST PCM** dataset; outputs `data/results/external_validation.json`.
12. **Generate report & figures** – PDF/HTML in `paper/`.

All intermediate files are checksum‑verified; re‑running `make all` will skip already‑validated steps.

## Reproducibility Guarantees (Principle I)

Every script starts with:

```python
import random, numpy as np, torch
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
```

The same seeds are stored in `config/seeds.yaml`. This ensures deterministic results across runs.

## Inspect Results

```bash
# Example: view baseline performance
cat data/results/baseline_metrics.json | jq.

# Example: view the best symbolic formula
jq -r '.formulas[0]' data/results/pysr_formulas.json

# Example: view correlation between MLP and interpretable model predictions
jq -r '.pearson_corr' data/results/deep_mlp.json
```

## Customization

- **Change label threshold**: edit `config/label.yaml` (default 150 J/g).
- **Enable crystal‑graph generation**: set `USE_GRAPH=True` in `config/feature.yaml`.
- **Adjust random seed**: modify `config/seeds.yaml`; all scripts read the same seed for reproducibility (Principle I).

## Expected Outputs (summary)

| Artifact | Description |
|----------|-------------|
| `data/results/baseline_metrics.json` | R², MAE, RMSE for RF & XGBoost. |
| `data/results/deep_mlp.json` | MLP performance and Pearson correlation with SHAP‑ranked predictions (≤ 0.8 required). |
| `data/results/shap_importances.json` | Ranked feature importances (SHAP values). |
| `data/results/pysr_formulas.json` | Symbolic formulas with R² ≥ 0.0. |
| `data/results/threshold_sweep.json` | Performance across five latent‑heat thresholds. |
| `data/results/external_validation.json` | Top‑20 ranking accuracy ≥ 60 % on the independent NIST PCM set (SC‑003). |
| `paper/figures/` | PNG/PDF figures ready for manuscript insertion. |

All files conform to the JSON/YAML schemas in `contracts/`. Re‑run the pipeline on a fresh runner to verify reproducibility (Principle I).
