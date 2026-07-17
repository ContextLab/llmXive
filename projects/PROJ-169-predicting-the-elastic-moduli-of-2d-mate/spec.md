# Project Specification: Predicting the Elastic Moduli of 2D Materials

## Project Title
Predicting the Elastic Moduli of 2D Materials from Structure-Only Models

## Problem Statement
Predict the elastic moduli (Young's, Shear, Poisson's ratio) of 2D materials using only their crystal structure, without performing new first-principles calculations. The goal is to build a **Structure-Only Surrogate Model** that interpolates existing DFT data to provide rapid property estimates for new materials.

## User Stories

### US1: Data Ingestion and Graph Construction
As a researcher, I want to download CIF files and elastic tensors from public repositories (Materials Project, AFLOW), filter for 2D materials, and convert them into graph representations so that I have a clean, canonical dataset for training.

**Acceptance Criteria**:
- Script downloads data from a single canonical source per run.
- CIF files are parsed into `MaterialGraph` objects using `pymatgen`.
- Non-2D materials and entries with missing tensors are filtered out.
- Output: `data/processed/graphs_v1.parquet`.

### US2: Lightweight GNN Training and Evaluation
As a researcher, I want to train a lightweight GNN on the constructed dataset and evaluate its performance against held-out DFT values, including intra-family baseline and inter-family drop metrics.

**Acceptance Criteria**:
- Model is CPU-compatible (2-3 layers, hidden dim ≤ 64).
- Splitting is stratified by chemical prototype/space group.
- Metrics: MAPE, RMSE, R² for Young's, Shear, Poisson.
- Output: `data/results/training_logs.json`, `data/results/generalization_metrics.json`.

### US3: Feature Importance and Ablation Analysis
As a researcher, I want to identify which structural descriptors most strongly influence predicted elastic moduli and understand the contribution of different descriptor classes.

**Acceptance Criteria**:
- SHAP interaction values calculated on GNN inputs.
- Permutation importance ranks top 5 structural descriptors.
- Ablation study compares full GNN vs. composition-only baseline.
- Output: `data/results/feature_importance_report.md` (unified ranked list).

## Technical Constraints

1. **Memory**: Peak RAM usage must not exceed 7GB (dynamic sampling).
2. **Data Integrity**: No synthetic data generation; only real DFT data from verified sources.
3. **Terminology**: Must refer to the model as a "Structure-Only Surrogate Model" to distinguish from first-principles methods.
4. **Reproducibility**: All random seeds must be fixed via `utils/config.py`.

## Success Metrics

- **SC-001**: Pipeline runs end-to-end on 7GB RAM.
- **SC-002**: Inter-family generalization drop is measured and reported.
- **SC-003**: Feature importance report identifies top 5 structural drivers.
