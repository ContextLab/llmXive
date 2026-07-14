# Quickstart Guide: Predicting Cognitive Decline from Resting-State fMRI

This document provides the exact sequence of commands to run the full analysis pipeline
from raw data download to final report generation.

## Prerequisites

- Python 3.11+
- FSL (for motion correction, optional if pre-processed data is used)
- Internet connection (for OpenNeuro download)

## Installation

```bash
pip install -r code/requirements.txt
```

## Execution Order

Run the following commands in order. Each step produces artifacts required by the next.

### 1. Data Gate & Download
Verify dataset availability and download/filter eligible subjects.
```bash
python code/00_data_gate.py
python code/01_download_and_filter.py
```
*Outputs*: `data/processed/eligible_subjects.csv`, `data/processed/excluded_subjects.log`

### 2. Preprocessing & Parcellation
(Optional: Skip if using pre-processed data from OpenNeuro)
```bash
python code/02_preprocess_and_parcellate.py
```
*Outputs*: `data/processed/connectivity_matrices/` (NIfTI or NumPy files)

### 3. Graph Metric Computation
Calculate network topology metrics.
```bash
python code/03_compute_graph_metrics.py
```
*Outputs*: `data/processed/graph_metrics.csv`

### 4. Collinearity Analysis (Standalone)
Analyze feature correlations before modeling.
```bash
python code/08_collinearity_check.py
```
*Outputs*: `data/processed/collinearity_report.json`

### 5. Model Training
Train Random Forest with nested cross-validation.
```bash
python code/04_train_model.py
```
*Outputs*: `data/processed/model.pkl`, `data/processed/feature_selection_log.json`

### 6. Model Evaluation
Evaluate performance on held-out folds.
```bash
python code/05_evaluate_model.py
```
*Outputs*: `data/processed/performance_report.json`

### 7. Permutation Test
Assess statistical significance.
```bash
python code/06_permutation_test.py
```
*Outputs*: `data/processed/permutation_results.json`

### 8. Sensitivity Analysis
Test robustness to threshold variations.
```bash
python code/07_sensitivity_analysis.py
```
*Outputs*: `data/processed/sensitivity_report.json`

### 9. External Outcome Check
Check for MCI conversion data availability.
```bash
python code/11_external_outcome_check.py
```
*Outputs*: `data/artifacts/limitations.txt`

### 10. Final Report Generation
Aggregate all results into a markdown report.
```bash
python code/09_generate_report.py
```
*Outputs*: `data/artifacts/final_report.md`

### 11. Success Criteria Verification
Verify if the project met success criteria.
```bash
python code/10_verify_success_criteria.py
```
*Outputs*: `data/artifacts/verification_status.txt`, `data/artifacts/runtime_report.json`

## Full Pipeline Execution

To run the entire pipeline sequentially:

```bash
bash code/run_pipeline.sh
```

(Note: Ensure `run_pipeline.sh` is created with the commands above if not already present).