# Implementation Plan: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy

**Project ID**: PROJ-509
**Status**: Active
**Version**: 1.2.0

## Executive Summary

This project evaluates the correlation between compositional features (mean/variance of elemental properties) and predicted formation energy in inorganic materials using the MP-2020.12.1 dataset. We will train Random Forest and Gradient Boosting models, validate feature importances, and generate Accumulated Local Effects (ALE) plots to understand non-linear relationships.

## Objectives

1. Download and process the MP-2020.12.1 dataset from the Materials Project.
2. Compute mean and variance descriptors for elemental properties (electronegativity, radius, valence, melting point, ionization energy).
3. Train Random Forest and Gradient Boosting models to predict formation energy.
4. Validate model performance with R², MAE, and RMSE metrics.
5. Extract and validate feature importances using tree-based and permutation methods.
6. Generate ALE plots for top-ranked features to assess non-linearity.
7. Perform statistical tests to compare model performance.

## Data Sources

- **Primary**: MP-2020.12.1 dataset via MPDS API (requires `MPDS_API_KEY`).
- **Fallback**: Checksummed CSV file at `data/raw/mp-2020.csv` (if API fails).
- **Elemental Properties**: Loaded from `pymatgen` or `matminer` libraries.

## Methodology

### Phase 1: Setup (Shared Infrastructure)

- Initialize project structure (`data/`, `code/`, `tests/`, `contracts/`).
- Configure dependencies (`requirements.txt`).
- Set up linting and formatting tools.

### Phase 2: Foundational (Blocking Prerequisites)

- Create directory structure for raw, processed, and evaluation data.
- Define JSON/CSV schemas for datasets and model outputs.
- Implement configuration management (`config.py`).
- Set up logging and error handling infrastructure.
- Implement sampling and chemical family assignment utilities.

### Phase 3: User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1)

- **Goal**: Download MP dataset, filter for inorganic compounds, compute descriptors.
- **Tasks**:
 - Download dataset via MPDS API (with fallback).
 - Verify checksum and data availability.
 - Filter for inorganic compounds.
 - Perform stratified sampling by chemical family if dataset exceeds `ROW_THRESHOLD`.
 - Compute mean and variance descriptors for elemental properties.
 - Detect and cap outliers.
 - Validate final dataset against schema.

### Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

- **Goal**: Train RF and GB models, evaluate performance, validate split integrity.
- **Tasks**:
 - Load processed dataset and perform stratified split by chemical family.
 - Train Random Forest and Gradient Boosting models.
 - Calculate R², MAE, RMSE on validation split.
 - Calculate Total Variation Distance (TVD) between train/val distributions.
 - Detect overfitting and calculate overfitting ratio.
 - Save model artifacts and metrics.
 - Perform paired t-test comparing model performance.

### Phase 5: User Story 3 - Feature Importance Ranking and Sensitivity Analysis (Priority: P3)

- **Goal**: Extract feature importances, validate with permutation importance, generate ALE plots.
- **Tasks**:
 - Extract feature importances from trained Random Forest model.
 - Calculate permutation importance and validate correlation with tree-based importances.
 - Rank features and output top descriptors.
 - Generate SHAP interaction values for top features.
 - Generate ALE plots for top features.
 - Calculate non-linearity scores for ALE plots.
 - Perform Multi-Collinearity Check (VIF) for descriptor stability.

### Phase 6: Polish & Cross-Cutting Concerns

- Update documentation (`README.md`).
- Refactor code to remove unused imports and enforce line length.
- Run end-to-end validation.
- Generate final research summary.

### Phase 7: Plan & Spec Updates

- Update plan.md to reflect implementation details and required artifacts.

## Single Source of Truth

The following artifacts are the **Single Source of Truth** for the project's results and must be preserved and versioned:

- `data/evaluation/model_metrics.json`: Contains final R², MAE, RMSE, overfitting ratio, and predictive power status. **This is the authoritative source for model performance per FR-004.**
- `data/evaluation/permutation_importance.json`: Contains permutation importance scores, correlation metrics, and validation status.
- `data/evaluation/feature_ranking.json`: Contains ranked list of top descriptors based on feature importance.
- `data/evaluation/vif_scores.json`: Contains Variance Inflation Factor scores for diagnosing multi-collinearity.
- `data/evaluation/statistical_tests.json`: Contains results of paired t-tests and other statistical comparisons.
- `data/evaluation/cv_scores.json`: Contains cross-validation scores for internal tuning/debugging (not the primary metric).
- `data/evaluation/sampling_statistics.json`: Contains Kolmogorov-Smirnov test results for sampling validation.
- `data/evaluation/ale_metrics.json`: Contains non-linearity scores for ALE plots.
- `data/evaluation/dataset_verification.json`: Contains checksum and verification status of the raw dataset.
- `data/evaluation/sampling_manifest.json`: Contains metadata about the sampling process (if applied).

## Success Criteria

- **SC-001**: Dataset contains ≥1000 rows after filtering/sampling.
- **SC-002**: All descriptor columns are non-null numeric values.
- **SC-003**: Models complete training within 3 hours on 2-core CPU.
- **SC-004**: R² > 0.0 (or explicitly recorded as negative per FR-004b).
- **SC-005**: TVD ≤ 0.05 between training and validation chemical family distributions.
- **SC-006**: Correlation (r ≥ 0.8) between tree-based and permutation importances.
- **SC-007**: ALE plots generated for top-ranked features with non-linearity scores logged.

## Risk Mitigation

- **Data Availability**: Fallback to checksummed local file if API fails. Fail loudly if both fail.
- **Memory Constraints**: Use chunked reading and stratified sampling if dataset exceeds `ROW_THRESHOLD`.
- **Negative R²**: Explicitly record and log negative R² values without converting to null/zero (FR-004b).
- **Multi-Collinearity**: Perform VIF check and flag if VIF > 10.

## Timeline

- **Phase 1-2**: 2 days
- **Phase 3**: 3 days
- **Phase 4**: 3 days
- **Phase 5**: 2 days
- **Phase 6-7**: 2 days
- **Total**: ~12 days

## Dependencies

- Python 3.8+
- `pymatgen`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `pyyaml`, `mpdsapi`, `shap`, `eli5`, `statsmodels`, `psutil`
- MPDS API key (`MPDS_API_KEY` environment variable)

## Notes

- All sampling is stratified by **Chemical Family** to preserve structural diversity.
- The hold-out validation split R² is the **Single Source of Truth** for model performance (FR-004).
- Cross-validation scores are for internal tuning/debugging only.
- All artifacts must be versioned and checksummed for reproducibility.
