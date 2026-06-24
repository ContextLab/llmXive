# Quickstart

This guide walks you through the end‑to‑end execution of the dipole‑moment prediction pipeline.
All commands assume you are in the repository root and have a Python 3.11 environment
with the packages listed in `projects/001-predicting-molecular-dipole-moments/code/requirements.txt`.

## 1. Set up the environment

```bash
# Create and activate a virtual environment
python -m venv.venv
source.venv/bin/activate

# Install required packages
pip install -r projects/001-predicting-molecular-dipole-moments/code/requirements.txt
```

## 2. Download and prepare the QM9 dataset

```bash
# Download the full QM9 dataset (cached in data/raw/)
python projects/001-predicting-molecular-dipole-moments/code/data/download_qm9.py

# Create a reproducible 10k random subset [UNRESOLVED-CLAIM: c_dff82a5b — status=not_enough_info]
python projects/001-predicting-molecular-dipole-moments/code/data/create_subset.py

# Extract 3‑D coordinates and construct bond connectivity
python projects/001-predicting-molecular-dipole-moments/code/data/preprocess_3d.py

# Generate 2‑D Morgan fingerprints and Coulomb matrices
python projects/001-predicting-molecular-dipole-moments/code/data/extract_2d_descriptors.py
```

After these steps the following files should exist:

- `data/processed/molecules_10k.parquet`
- `data/processed/features_3d.parquet`
- `data/processed/features_2d.parquet`

## 3. Train models

```bash
# Train the SchNet‑style GNN (5 seeds, early stopping) [UNRESOLVED-CLAIM: c_5b1ce5a7 — status=not_enough_info]
python projects/001-predicting-molecular-dipole-moments/code/training/train_gnn.py

# Train the Random Forest baseline (5 seeds) [UNRESOLVED-CLAIM: c_bdf45a06 — status=not_enough_info]
python projects/001-predicting-molecular-dipole-moments/code/training/train_rf.py
```

Checkpoints are saved under `data/checkpoints/` and metrics under `results/metrics.csv`.

## 4. Evaluate performance

```bash
python projects/001-predicting-molecular-dipole-moments/code/training/evaluate.py
python projects/001-predicting-molecular-dipole-moments/code/analysis/generate_performance_plots.py
```

The generated plots are stored in `results/figures/`.

## 5. Attribution & statistical significance

```bash
# Permutation importance for Random Forest
python projects/001-predicting-molecular-dipole-moments/code/attribution/permutation_importance.py

# Saliency mapping for GNN
python projects/001-predicting-molecular-dipole-moments/code/attribution/saliency_mapping.py

# Paired t‑test across seeds
python projects/001-predicting-molecular-dipole-moments/code/analysis/statistical_tests.py
```

Results:
- `results/attributions.json` – Feature importance rankings.
- `results/significance.csv` – p‑values for paired t‑tests.

## 6. Validate pipeline constraints

```bash
# {{claim:c_121d794c}} (Wikidata Q135076778, https://www.wikidata.org/wiki/Q135076778), CPU cores (≤2), and total runtime (≤6 h)
python projects/001-predicting-molecular-dipole-moments/code/utils/memory_constraint.py
python projects/001-predicting-molecular-dipole-moments/code/utils/cpu_constraint.py
python projects/001-predicting-molecular-dipole-moments/code/utils/pipeline_time_limit.py
```

## 7. Run the full end‑to‑end demo

For a single‑command demonstration that runs the entire pipeline (subject to the
constraints above), execute:

```bash
bash scripts/run_full_pipeline.sh
```

The script orchestrates all steps, logs progress, and produces a final summary
`results/summary.txt`.

## 8. Testing

```bash
pytest -vv
```

All unit, integration, and contract tests should pass.
