# Quickstart Guide: Predicting Cognitive Decline from Resting-State fMRI

This guide provides the exact commands to run the full analysis pipeline for project PROJ-029.

## Prerequisites

- Python 3.11+
- Installed dependencies: `pip install -r code/requirements.txt`
- OpenNeuro dataset `ds000246` (Constitution VI) accessible (downloaded or via API) [UNRESOLVED-CLAIM: c_57400cf4 — status=not_enough_info]

## Directory Structure

Ensure the following directories exist:
- `data/raw/`
- `data/processed/`
- `data/artifacts/`
- `code/`
- `tests/`

## Execution Order

Run the following commands in sequence. Each step produces artifacts required by the next.

### 1. Data Ingestion and Filtering

Download and filter subjects with longitudinal cognitive scores.

```bash
python code/01_download_and_filter.py
```
*Outputs: `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`*

### 2. Preprocessing and Parcellation

Preprocess fMRI data and extract time series using the AAL atlas.

```bash
python code/02_preprocess_and_parcellate.py
```
*Outputs: `data/processed/adjacency_matrices/` (NIfTI or NumPy files)*

### 3. Graph Metric Calculation

Compute network topology metrics (degree, efficiency, etc.).

```bash
python code/03_compute_graph_metrics.py
```
*Outputs: `data/processed/graph_metrics.csv`*

### 4. Collinearity Check (Standalone)

Analyze feature correlations for the run-book verification step.

```bash
python code/08_collinearity_check.py
```
*Outputs: `data/processed/collinearity_report.json`*

### 5. Model Training

Train the Random Forest classifier with nested cross-validation.

```bash
python code/04_train_model.py
```
*Outputs: `data/processed/model.pkl`, `data/processed/model_config.json`*

### 6. Model Evaluation

Calculate performance metrics (ROC-AUC, F1, etc.).

```bash
python code/05_evaluate_model.py
```
*Outputs: `data/processed/performance_report.json`*

### 7. Permutation Test

Validate statistical significance.

```bash
python code/06_permutation_test.py
```
*Outputs: `data/processed/permutation_results.json`*

### 8. Sensitivity Analysis

Assess robustness to threshold variations.

```bash
python code/07_sensitivity_analysis.py
```
*Outputs: `data/processed/sensitivity_report.json`*

### 9. Final Report Generation

Aggregate results into a markdown report.

```bash
python code/09_generate_report.py
```
*Outputs: `data/artifacts/final_report.md`*

### 10. Success Criteria Verification

Verify that all success criteria are met.

```bash
python code/10_verify_success_criteria.py
```
*Outputs: `data/artifacts/verification_status.json`, `data/artifacts/runtime_report.json`*

## Validation

To verify the entire pipeline:

```bash
python code/validate_quickstart.py
```

## Notes

- All scripts use `random_seed=42` for reproducibility. [UNRESOLVED-CLAIM: c_d982698c — status=not_enough_info]
- Ensure sufficient RAM (7GB+) for graph metric calculation. [UNRESOLVED-CLAIM: c_58ecba25 — status=not_enough_info]
- Runtime limits are enforced in specific scripts (e.g., permutation test).