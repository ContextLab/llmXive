# Structure-Only Surrogate Model for 2D Material Elastic Moduli

**WARNING: This project is a Surrogate Model.** It does NOT solve the Schrödinger equation or perform first-principles calculations. It is a statistical interpolator trained on pre-computed DFT data.

> "Don't fool yourself — and you are the easiest person to fool." — Richard Feynman

## Project Overview

This project implements a lightweight Graph Neural Network (GNN) to predict the elastic moduli (Young's, Shear, Poisson) of 2D materials. The model is a **surrogate** that interpolates existing Density Functional Theory (DFT) results from public repositories (e.g., Materials Project, AFLOW).

**Key Distinction:**
- **First-Principles (DFT):** Solves the Schrödinger equation to calculate electron density from the Hamiltonian. High computational cost.
- **Surrogate (This Project):** Learns statistical correlations between structural descriptors and pre-computed DFT values. Low computational cost, but **cannot** discover new physics or extrapolate beyond the training distribution.

## Reproducibility & Data Hygiene

To ensure scientific rigor and reproducibility (Constitution Principle I):

- **Random seeds are pinned in `code/utils/config.py`.** This enforces consistent initialization for `torch`, `numpy`, and `random` across all modules.
- **External datasets are fetched from the same canonical source on every run.** The data loader (`code/ingest/download.py`) abstracts over sources (Materials Project, AFLOW) but enforces a single source per execution to prevent data leakage and ensure traceability.
- **Artifact Checksums:** All processed data and model weights are checksummed (SHA256) and recorded in `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml`.

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
3. Set the data source environment variable (optional, defaults to `materials_project`):
 ```bash
 export DATA_SOURCE=materials_project
 ```

## Quickstart

Run the full pipeline (Download -> Parse -> Filter -> Train -> Evaluate):

```bash
# 1. Ingest Data (Download, Parse, Filter, Save)
python code/ingest/pipeline.py

# 2. Train Model
python code/model/train.py

# 3. Evaluate Generalization
python code/model/eval_runner.py

# 4. Analyze Feature Importance
python code/analysis/importance.py --model data/processed/model_v1.pt --data data/processed/graphs_v1.parquet --indices data/processed/split_indices.json --output data/results/feature_importance.json --descriptors composition topology
```

## Project Structure

```
.
├── code/
│ ├── ingest/ # Data download, parsing, filtering
│ ├── model/ # GNN architecture, training, evaluation
│ ├── analysis/ # SHAP, ablation, importance
│ ├── utils/ # Config, logging, memory management
│ └── data_models/ # MaterialGraph schema
├── data/
│ ├── raw/ # Downloaded CIFs and tensors
│ ├── processed/ # Graphs, splits, model checkpoints
│ └── results/ # Metrics, reports, logs
├── docs/ # Methodology, contributing guidelines
├── state/ # Project state and artifact hashes
└── tests/ # Unit and integration tests
```

## Limitations

- **Extrapolation Failure:** The model performs poorly on material families not represented in the training set.
- **No Physics Discovery:** The model learns correlations, not causal physical laws. It cannot predict properties for structures outside the chemical space of the training data.
- **Data Dependency:** Accuracy is limited by the quality and coverage of the underlying DFT dataset.

## Compliance

- **Constitution Principle I (Reproducibility):** Seeds pinned, single canonical source enforced.
- **Constitution Principle V (Versioning Discipline):** Artifact timestamps and checksums tracked.
- **Constitution Principle VI (DFT Ground-Truth Fidelity):** Only independent elastic tensor components are used.

## Citing

If you use this surrogate model or its methodology, please cite the underlying DFT datasets (e.g., Materials Project) and acknowledge this work as a statistical interpolation tool.