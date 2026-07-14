# Quickstart Guide: Predicting Cognitive Decline from Resting-State fMRI

This guide provides the commands to run the full analysis pipeline for Project PROJ-029.
Ensure all dependencies in `code/requirements.txt` are installed before proceeding.

## Prerequisites

- Python 3.11+
- FSL (for `mcflirt` - optional if skipping motion correction, but required for full pipeline)
- Network access to download the dataset (or pre-downloaded data in `data/raw/`)

## Execution Order

Run the following commands in sequence. Each step produces artifacts required by the next.

### 1. Data Ingestion and Filtering
Downloads the OpenNeuro `ds000246` dataset, parses BIDS metadata, and filters for subjects
with longitudinal cognitive scores (MMSE/MOCA).

```bash
python code/01_download_and_filter.py
```
**Outputs:**
- `data/processed/eligible_subjects.csv`
- `data/processed/excluded_subjects.log`

### 2. Preprocessing and Parcellation
(Optional in this run-book if raw data is unavailable, but required for graph metrics)
Loads raw BIDS data, performs motion correction, normalization, and applies the AAL atlas.

```bash
python code/02_preprocess_and_parcellate.py
```
**Outputs:**
- `data/processed/connectivity_matrices/` (NIfTI or NumPy files)

### 3. Graph Metric Computation
Calculates graph-theoretical metrics (degree, efficiency, clustering, path length)
for each subject's connectivity matrix.

```bash
python code/03_compute_graph_metrics.py
```
**Outputs:**
- `data/processed/graph_metrics.csv`

### 4. Collinearity Analysis (Standalone)
**NEW:** Explicitly runs the collinearity check script to verify feature correlations
before modeling, as required by the run-book.

```bash
python code/08_collinearity_check.py
```
**Outputs:**
- `data/processed/collinearity_report.json`

### 5. Model Training
Trains a Random Forest classifier with nested cross-validation to predict cognitive decline.
Includes internal collinearity filtering and feature selection.

```bash
python code/04_train_model.py
```
**Outputs:**
- `data/processed/model.pkl`
- `data/processed/training_config.json`

### 6. Model Evaluation
Evaluates the trained model on the test folds and generates performance metrics.

```bash
python code/05_evaluate_model.py
```
**Outputs:**
- `data/processed/performance_report.json`

### 7. Permutation Test
Runs a permutation test to assess the statistical significance of the model's performance.

```bash
python code/06_permutation_test.py
```
**Outputs:**
- `data/processed/permutation_results.json`

### 8. Sensitivity Analysis
Analyzes model robustness across different decision thresholds and decline definitions.

```bash
python code/07_sensitivity_analysis.py
```
**Outputs:**
- `data/processed/sensitivity_report.json`

### 9. Generate Final Report
Aggregates all results, limitations, and findings into a final markdown report.

```bash
python code/09_generate_report.py
```
**Outputs:**
- `data/artifacts/final_report.md`

### 10. Verify Success Criteria
Checks if the project meets the predefined success criteria (ROC-AUC > 0.5, p < 0.05).

```bash
python code/10_verify_success_criteria.py
```
**Outputs:**
- `data/processed/verification_status.json`
- `data/processed/runtime_report.json`

## Notes

- **Memory Constraints:** The pipeline is designed to run within 7GB RAM. If you encounter memory issues, reduce the `N` parameter in `01_download_and_filter.py`.
- **Runtime:** The full pipeline may take several hours depending on dataset size and permutation count.
- **Data Availability:** If `api.openneuro.org` is unreachable, ensure you have pre-downloaded the dataset to `data/raw/ds000246`.