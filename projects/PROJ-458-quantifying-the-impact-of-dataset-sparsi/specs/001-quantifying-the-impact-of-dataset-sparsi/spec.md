# Specification: Quantifying the Impact of Dataset Sparsity on Model Performance

## 1. Overview
This project quantifies how dataset sparsity (reduced training data volume) affects the predictive performance and uncertainty calibration of materials property models.

## 2. Functional Requirements
### FR-001: Data Retrieval
Retrieve at least 150,000 material entries from the Materials Project API.
### FR-002: Filtering
Filter entries to retain only those with valid formation energy and DFT-computed status.
### FR-003: Representative Stratified Sample (RSS)
Create a Representative Stratified Sample (RSS) of 30,000 entries from the filtered pool. The RSS must preserve the distribution of formation energy. From this RSS, generate 7 strictly nested stratified subsets at sparsity levels: 1, 2, 5, 10, 25, 50, 100 percent.
### FR-004: Imputation
Apply mean imputation for missing descriptors, calculated only on the training pool (excluding the fixed test set).
### FR-005: Model Training
Train Gaussian Process Regression (GPR) and Random Forest (RF) models on CPU only. Evaluate on a fixed, independent test set.
### FR-006: Statistical Analysis
Perform Linear Mixed-Effects Modeling (LMM) with the formula `error ~ sparsity_level + (1|seed)` to analyze the impact of sparsity levels on error, accounting for nested random effects of seeds.
### FR-007: Sensitivity Analysis
Calculate slope variance between consecutive sparsity levels. The threshold for acceptable stability is slope variance < 10%.
### FR-008: Reporting
Generate a final report summarizing findings as associational evidence.
### FR-009: Test Set Independence
Partition a fixed test set (5,000 rows) from the raw pool BEFORE any filtering or imputation statistics are calculated to ensure strict independence.

## 3. Success Criteria
### SC-001: Metrics
Log RMSE, MAE, Predictive Variance, and Calibration Slope for all models and sparsity levels.
### SC-002: Visualization
Generate learning curves with error bars showing error vs. dataset size.
### SC-003: Significance
Apply pairwise contrasts with Tukey-adjusted p-values to LMM results to determine statistical significance between sparsity levels (p < 0.05).

## 4. User Stories
### US-1: Data Pipeline
As a researcher, I want to download and preprocess a large corpus of materials data so that I have a valid input pool for sparsity analysis.
### US-2: Sparsity & Training
As a researcher, I want to generate nested sparsity subsets and train models on CPU so that I can measure performance degradation.
### US-3: Analysis
As a researcher, I want to perform statistical analysis (LMM) and visualization so that I can validate the impact of sparsity and generate research artifacts.

## 5. Assumptions
- The Materials Project API is accessible.
- **Requires MP_API_KEY environment variable** to be set for authentication.
- Sufficient CPU resources are available for model training.
- The "no authentication barriers" assumption from previous drafts is incorrect; authentication is required.

## 6. Constraints
- No GPU usage for training.
- No synthetic data generation; all data must come from the real Materials Project API.
- Strict data leakage prevention: Test set must be split before any training statistics are computed.
