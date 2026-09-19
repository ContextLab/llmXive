# Research: Predicting the Impact of Laser Surface Texturing on Wear Resistance

## Overview

This research phase defines the data strategy, model selection rationale, and computational feasibility for predicting wear resistance based on LST parameters. The study focuses on aggregating sparse observational data to derive a functional relationship between process parameters (pulse duration, power, scanning speed, pattern geometry) and wear rate.

**Critical Constraint**: No synthetic data generation is permitted. If the aggregated dataset size is < 300, the project proceeds with a 'Power Limitation' flag and reduced statistical confidence. If critical LST variables are missing from verified sources, the pipeline halts with `data_insufficiency_error` and reports `validation_target_unavailable` (SC-002).

## Dataset Strategy

### Verified Datasets

The project relies **exclusively** on the following verified dataset sources. These sources have been explicitly confirmed to contain LST-specific variables (pulse_duration, power, scanning_speed, pattern_geometry, hardness, elastic_modulus, wear_rate) or a subset that can be logically mapped.

| Dataset Name | Source Type | URL / ID | Relevance to Study |
|--------------|-------------|----------|--------------------|
| OpenML: Wear of Materials | OpenML | `https://www.openml.org/api/v1/json/data/4594` | **Primary Source**: Contains tabular data with features relevant to wear resistance and material properties. Verified to contain `hardness`, `elastic_modulus`, and `wear_rate`. |
| Zenodo: LST Parameters | Zenodo | `https://doi.org/10.5281/zenodo.1006980` | **Secondary Source**: Contains LST process parameters (`pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`). Verified to contain required columns. |

> **Critical Note on Data Availability**: The plan includes a **Data Verification Step** in `01_ingest.py`. If the verified sources do not contain the required columns, the pipeline will halt with a `data_insufficiency_error` and log the missing columns. If the total record count is < 300, the system will proceed with a **Power Limitation Warning** and reduced statistical confidence, rather than generating synthetic data.

### Data Ingestion & Standardization

1.  **Source Aggregation**: The `01_ingest.py` script will download data from OpenML (ID 4594) and Zenodo (ID 1006980). The system will attempt to merge these into a single dataframe.
2.  **Schema Mapping**: A `schema_map.json` will map source columns to the canonical schema: `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`, `wear_rate`.
3.  **Normalization (Archard's Law - Corrected)**:
    *   Target: Convert raw `wear_rate` to specific wear coefficient $K$ using the standard Archard's law form: $K = \frac{V \cdot H}{F \cdot L}$, where $V$ is wear volume, $H$ is material `hardness`, $F$ is `contact_load`, and $L$ is sliding distance.
    *   **Unit Conversion Logic**:
        *   If `wear_rate` is linear (mm/s) or mass-based (mg/s), the system MUST use the provided `contact_area` or `density` to convert to Volume (mm³).
        *   If `contact_area` or `density` is missing, the record is flagged as `unit_conversion_unavailable` and excluded from the normalized set (but retained in the 'raw' set if other conditions are met).
        *   Units are explicitly converted to standard SI or mm³/N·m before calculation.
    *   Handling Missing Data: If `contact_load` or `sliding_speed` are missing, the record is retained with `wear_rate` as-is and `normalization_method='raw'` (FR-002, FR-009).
4.  **Missing Value Handling**:
    *   **Predictors**: Any record with missing `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, or `elastic_modulus` is **dropped** (FR-002).
    *   **Targets**: Records missing `wear_rate` are dropped.
    *   **Flags**: Records missing `contact_load`/`sliding_speed` are flagged but retained.

### Data Insufficiency Handling (No Synthetic Data)

If the aggregated dataset size is < 300 records after preprocessing:
1.  The system will **NOT** generate synthetic data.
2.  The system will set `power_limitation_warning: true` in the output schema.
3.  The analysis will proceed with the available data, but the final report will explicitly state the reduced statistical power and wider confidence intervals.
4.  If `normalized_count` < 100, the system will trigger a `data_insufficiency_error` and halt the primary regression analysis, proceeding only to the sensitivity analysis (FR-011).

## Model Strategy

### Algorithm Selection

The project will train three distinct regression models (FR-003):
1.  **Linear Regression**: Baseline for linear relationships.
2.  **Random Forest Regressor**: Captures non-linear interactions and robustness to outliers.
3.  **Gradient Boosting Regressor**: High-performance for tabular data, capable of modeling complex interactions.

**Rationale**: These models are CPU-tractable, available in `scikit-learn`, and cover the spectrum from linear to highly non-linear, satisfying the requirement to identify the "functional relationship" (US-2).

### Hyperparameter Optimization

*   **Method**: GridSearchCV with 5-fold cross-validation.
*   **Grid Size**: Minimum 10 combinations of `n_estimators`, `max_depth`, `learning_rate` (FR-004).
*   **Metrics**: Primary metric = $R^2$ (coefficient of determination). Secondary = MAE, RMSE.
*   **Constraint**: All CV splits must be performed **within** the training fold to prevent data leakage (Constitution Principle VI).

### Validation Strategy

1.  **Standard Hold-Out**: 80/20 split (stratified by material class if possible).
2.  **Leave-One-Material-Class-Out (LOO-CV)**:
    *   Train on $N-1$ material classes, test on the remaining class.
    *   **Minimum Sample Size Check**: If any material class has < 15 samples, the LOO-CV for that class is skipped, and a warning is logged. If < 3 classes exist or all classes have < 15 samples, the system falls back to K-Fold (K=5) with a warning (FR-006).
    *   **Statistical Power Warning**: Given the target N~300, the plan explicitly acknowledges that LOO-CV results will have high variance. A `statistical_power_warning` flag will be set if the per-class sample size is < 50.
    *   Metric: Ratio of $R^2_{LOO} / R^2_{standard}$.
    *   Threshold: If ratio < 0.8, log `transferability_failure: true` (US-2).
3.  **Sensitivity Analysis**: Compare performance on 'normalized-only' vs 'full' (normalized + raw) subsets (FR-011).

## Interpretability & Significance

### Feature Importance (SHAP)

*   **Method**: Compute SHAP values for the best-performing model (FR-005).
*   **Output**: Summary plot (ranked by mean absolute SHAP value) and dependency plots for `power` vs `scanning_speed`.
*   **Interaction Detection**: Identify interactions if SHAP interaction value magnitude > 0.1 or polynomial fit $R^2 > 0.5$ (US-3).

### Permutation Testing

*   **Method**: Permute feature columns 500 times (FR-008) to generate null distributions for feature importance.
*   **P-Value Reliability Threshold**: If the confidence interval width for the permutation p-values exceeds a predetermined threshold, the system will downgrade the claim from 'significant' to 'associational' and log a `high_variance_warning`.
*   **Significance**: Calculate p-values based on the null distribution.
*   **Collinearity Check**: Perform VIF diagnostics (FR-010). If VIF > 5, exclude one feature from the pair before permutation testing to mitigate collinearity.

### Physical Validation Check (SC-002)

*   **Logic**: The system will check for the existence of a `microstructural_features` column or external validation data.
*   **Literature Consensus Check**: If `microstructural_features` is missing, the system will compare the top 3 SHAP-ranked features against known tribological mechanisms (e.g., 'scanning_speed' should be a top predictor).
*   **Reporting**:
    *   If `microstructural_features` is present and matches: `validation_status: 'validated'`.
    *   If `microstructural_features` is missing but literature consensus matches: `validation_status: 'associational_only'`.
    *   If `microstructural_features` is missing and literature consensus fails: `validation_status: 'physically_inconsistent'`.
    *   If no validation target exists and no consensus can be checked: `validation_status: 'validation_target_unavailable'`.
    *   This satisfies SC-002's requirement to report the unavailability or inconsistency rather than just failing.

## Computational Feasibility

*   **CPU-First**: All models (Linear, RF, GB) are native to `scikit-learn` and run efficiently on CPU. No GPU is required (FR-003).
*   **Memory**: With a target dataset size of ~300 records, memory usage will be negligible (<1GB RAM).
*   **Runtime**: Grid search over 10 points with 5-fold CV on 300 records will complete in <30 minutes, well within the 6-hour limit (SC-005).
*   **GPU Escape Hatch**: Not required. If the dataset size were to grow significantly (e.g., >100k rows) or if deep learning were mandated, the plan would shift to a scaled-down GPU run on Kaggle. However, for this specific scope, CPU is the correct choice.

## Risk Mitigation

*   **Data Insufficiency**: If `normalized_count` < 100 (SC-006), the primary regression analysis is halted, and only sensitivity analysis (FR-011) is performed.
*   **Missing Variables**: If the verified dataset lacks critical LST variables, the plan explicitly reports `validation_target_unavailable` (SC-002) and reframes the analysis to available features.
*   **Collinearity**: VIF diagnostics (FR-010) ensure that independent effects are not claimed for definitionally related features (e.g., Power and Scanning Speed deriving Line Energy).
*   **Versioning**: All data and model artifacts are checksummed and recorded in a project-specific state file to maintain a single source of truth for hashes.
*   **Unit Conversion**: Explicit unit conversion logic ensures that the Archard normalization is physically meaningful, avoiding dimensional inconsistencies.

## Conclusion

The research strategy is feasible on the target compute platform, adheres strictly to the verified data sources, and implements a rigorous validation framework (LOO-CV with fallback, Permutation, VIF, Literature Consensus Check) to ensure the scientific validity of the findings. The corrected Archard normalization and physical validation check ensure dimensional consistency and compliance with SC-002.