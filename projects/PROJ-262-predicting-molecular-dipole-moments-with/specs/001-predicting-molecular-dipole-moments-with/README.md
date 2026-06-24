# Predicting Molecular Dipole Moments with Graph Neural Networks

This repository implements a reproducible pipeline for predicting molecular dipole moments
from 3‑D molecular structures using a lightweight SchNet‑style Graph Neural Network (GNN)
and a Random Forest baseline. The project follows a structured, test‑driven development
process and includes all data preparation, model training, evaluation, attribution, and
statistical analysis steps required for a scientific publication.

## Repository layout

```
projects/
 001-predicting-molecular-dipole-moments/
 code/ # Python source code
 data/
 raw/ # Downloaded QM9 dataset (≈133k molecules) [UNRESOLVED-CLAIM: c_37addd39 — status=not_enough_info]
 processed/ # {{claim:c_9c685cb6}} (OEIS A008299, https://oeis.org/A008299), feature matrices, etc.
 checkpoints/ # Model checkpoints for each seed
 tests/
 unit/ # Unit tests for individual functions
 integration/ # Integration tests (memory profiling, etc.)
 contract/ # JSON‑Schema contract tests
 contracts/ # YAML schema definitions
 specs/
 001-predicting-molecular-dipole-moments/
 README.md # ↗︎ This file
 quickstart.md # Quick start guide
 research.md # Background, related work, and research questions
```

## Development workflow

1. **Setup** – Install dependencies from `requirements.txt` and create a virtual environment.
2. **Data preparation** – Run the data scripts to download QM9, create a reproducible 10 k subset,
 and generate 3‑D and 2‑D feature matrices.
3. **Model training** – Train the GNN and Random Forest models across five random seeds [UNRESOLVED-CLAIM: c_bb7e3d45 — status=not_enough_info].
4. **Evaluation** – Compute MAE / RMSE, validate variance, and generate performance plots.
5. **Attribution & statistics** – Produce permutation importance, saliency maps, and paired
 t‑tests to assess significance of performance differences.
6. **Documentation** – Update this README, the quick‑start guide, and the research background.

For detailed step‑by‑step instructions, see `quickstart.md`.
