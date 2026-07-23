# Feature Specification: Predicting Personal Sleep Quality from Resting-State fMRI Connectivity

## Overview
This project implements a machine learning pipeline to predict individual sleep quality scores from resting-state functional connectivity (rs-fMRI) data. The analysis uses data from the Human Connectome Project (HCP) 1200 Subjects Release.

## User Stories

### US1: End-to-End Data Pipeline
As a researcher, I want to obtain preprocessed whole-brain functional connectivity vectors for every HCP participant with Sleep questionnaire data, so that I can use them as features for predictive modeling.

**Acceptance Criteria:**
1. Download raw HCP minimally preprocessed CIFTI files and behavioral data.
2. Filter subjects to those with valid Sleep Scores and exclude those with >0.3mm framewise displacement.
3. Preprocess time series (Schaefer parcellation, nuisance regression, band-pass filtering).
4. Compute pairwise Pearson correlations, apply Fisher-z transformation, and extract upper-triangular vectors.
5. Save connectivity vectors as `.npy` files.

### US2: Predictive Modeling & Statistical Validation
As a researcher, I want to train an elastic-net regression model on connectivity features, evaluate out-of-sample performance, and assess statistical significance, so that I can determine if sleep quality is predictable from brain connectivity.

**Acceptance Criteria:**
1. Implement nested cross-validation with inner-loop hyperparameter tuning.
2. Ensure VarianceThreshold and PCA are fitted strictly within the training fold (no data leakage).
3. Run 1,000 label permutations on a stratified subset of 100 subjects to generate a null distribution.
4. Compute empirical p-value from the null distribution.
5. Perform bootstrap resampling of aggregated out-of-sample predictions to compute a 95% confidence interval for R².
6. Enforce resource limits (CPU-only, ≤6 GB RAM, 5-hour wall-clock timeout).

### US3: Interpretation & Visualization
As a researcher, I want to identify which brain connections drive the prediction and visualize them on a cortical surface, so that I can interpret the biological meaning of the model.

**Acceptance Criteria:**
1. Extract non-zero elastic-net coefficients from the trained model.
2. Map coefficients back to brain edges using the Schaefer atlas.
3. Generate a brain-surface plot highlighting top predictive connections.
4. Handle edge cases (e.g., zero coefficients, failed mappings) gracefully.

## Functional Requirements

### FR-001: Data Preprocessing
The system shall preprocess rs-fMRI time series using:
- Schaefer 400-region parcellation
- Nuisance regression (5 motion parameters, WM, CSF)
- Band-pass filtering (0.01–0.1 Hz)

### FR-002: Feature Engineering
The system shall compute pairwise Pearson correlations between all region pairs, apply Fisher-z transformation, and extract the upper-triangular vector (excluding diagonal) as the feature vector.

### FR-003: Nested Cross-Validation
The system shall implement nested cross-validation with:
- Outer loop: 5-fold stratified split for evaluation
- Inner loop: 3-fold stratified split for hyperparameter tuning
- All feature selection (VarianceThreshold, PCA) must be fitted ONLY on the training fold of each iteration.

### FR-004: Model Training
The system shall train an ElasticNetCV model with:
- L1 ratio grid: [0.1, 0.5, 0.9]
- Alpha grid: log-spaced from 1e-4 to 1e2
- Max iterations: 1000

### FR-005: Out-of-Sample Predictions
The system shall output predictions for all subjects in the outer fold, saved as `data/processed/predictions.npy` (shape: [n_subjects, 1]).

### FR-006: Permutation Test (AMENDED)
The system shall perform a permutation test to assess statistical significance:
- **AMENDMENT**: Due to compute constraints (5-hour wall-clock limit), the permutation test will run on a **stratified random subset of 100 subjects** (instead of the full dataset).
- **Number of permutations**: 1,000
- **Procedure**: For each permutation, randomly shuffle labels, re-run the entire nested CV pipeline (including inner-loop tuning and variance-thresholding), and record the R² score.
- **Output**: Null distribution saved as `data/results/null_distribution.npy`.
- **Validation**: The subset size (N=100) is validated by the power analysis in T037a, which confirms that with expected effect size R²=0.05, alpha=0.05, the power exceeds 0.8.
- **Reference**: See Task T022a for spec amendment details and T037a for power analysis validation.

### FR-007: Bootstrap Confidence Interval
The system shall perform bootstrap resampling of aggregated out-of-sample predictions (loaded from `data/processed/predictions.npy`) to compute a 95% confidence interval for R².

### FR-008: Feature Interpretation
The system shall extract non-zero elastic-net coefficients from the trained model and map them back to brain edges using the Schaefer atlas.

### FR-009: Resource Limits
The system shall:
- Enforce CPU-only execution (no GPU)
- Monitor RAM usage and abort if >6 GB
- Enforce a 5-hour wall-clock timeout using signal handlers
- Gracefully flush partial results on abort

### FR-010: Structured Logging
The system shall log all operations in structured JSON format, including seeds, hyperparameters, and data hashes, to `data/logs/pipeline_run.json`.

## Data Model

### Inputs
- HCP 1200 Subjects Release (minimally preprocessed CIFTI files)
- HCP behavioral data (Sleep Score, framewise displacement, etc.)

### Intermediate Artifacts
- `data/processed/valid_subjects.txt`: List of subject IDs with valid Sleep Scores and FD < 0.3mm
- `data/processed/connectivity_vectors/*.npy`: Connectivity vectors for each subject
- `data/processed/predictions.npy`: Out-of-sample predictions from nested CV
- `data/processed/model.pkl`: Trained ElasticNetCV model

### Outputs
- `data/results/null_distribution.npy`: Null distribution from permutation test
- `data/results/bootstrap_ci.json`: Bootstrap confidence interval for R²
- `data/results/sensitivity_analysis.json`: Sensitivity analysis results (if completed)
- `data/results/plot_top_edges.png`: Brain-surface visualization of top predictive edges
- `data/results/ResultReport.json`: Comprehensive report with all metrics, p-values, CIs, and artifact paths

## Non-Functional Requirements

### SC-001: Data Integrity
All downloaded files must be verified via SHA256 checksums. Checksums must be recorded in `data/raw/manifest.json`.

### SC-002: Reproducibility
All random seeds must be set and logged. All hyperparameters must be logged.

### SC-003: Partial State Reporting
If the sensitivity analysis is incomplete (due to time limits), the output must explicitly flag `status: 'partial'` and list `missing_combinations`.

### SC-004: Edge Case Handling
The system shall handle edge cases gracefully:
- If the model has zero non-zero coefficients, generate a placeholder visualization.
- If <50 edges are found, plot all available and log a warning.
- If edge mapping fails, log a warning and continue.

### SC-005: CI Compatibility
All scripts must run on CPU-only CI with limited vCPU and GB RAM without GPU dependencies.

### SC-006: Audit Trail
All operations must be logged to `data/logs/pipeline_run.json` with timestamps, parameters, and data hashes.

## Dependencies
- Python 3.9+
- nilearn
- scikit-learn
- pandas
- numpy
- nibabel
- networkx
- scipy
- psutil
- seaborn
- matplotlib
- hcp_data (for real data fetching)

## Implementation Notes
- VarianceThreshold and PCA MUST be fitted within the training fold of every CV iteration (Critical Methodological Correction).
- Permutation test runs on a stratified subset of 100 subjects (Amendment to FR-006) to meet compute constraints. This is validated by T037a (power analysis) and documented in T022a.
- All scripts must write their declared output files to disk; in-memory results are insufficient.
- Graceful shutdown logic is integrated into T022 and T024 to ensure partial results are saved if time limits are hit.