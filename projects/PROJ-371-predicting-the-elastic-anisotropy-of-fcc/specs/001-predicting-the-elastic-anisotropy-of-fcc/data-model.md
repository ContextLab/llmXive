# Data Model: Predicting the Elastic Anisotropy of FCC Metals from Composition

## Entities

### 1. MaterialEntry
Represents a single FCC material entry with computed features.
- **id**: `str` (Unique identifier from source API)
- **formula**: `str` (Chemical formula, e.g., "Cu", "AlNi")
- **source**: `str` ("materials_project" | "aflowlib" | "matbench")
- **c11**: `float` (Elastic constant in GPa)
- **c12**: `float` (Elastic constant in GPa)
- **c44**: `float` (Elastic constant in GPa)
- **a1**: `float` (Calculated anisotropy factor: $2C_{44} / (C_{11} - C_{12})$)
- **atomic_radius_variance**: `float`
- **electronegativity_std**: `float`
- **vec**: `float` (Valence Electron Concentration)
- **is_outlier**: `bool` (Flagged during sensitivity analysis)

### 2. ModelRun
Represents a single training execution.
- **run_id**: `str` (UUID)
- **model_type**: `str` ("random_forest" | "gradient_boosting" | "linear")
- **hyperparameters**: `dict` (JSON string)
- **r2**: `float`
- **mae**: `float`
- **rmse**: `float`
- **timestamp**: `datetime`
- **outlier_threshold**: `float` (e.g., 3.0)

### 3. ValidationReport
Aggregated output of the validation phase.
- **report_id**: `str`
- **total_entries**: `int`
- **physical_violations**: `int` (Count of predictions where $A_1 \le 0$ or $A_1 \ge 3$)
- **violation_rate**: `float` (Calculated as `physical_violations / total_entries`)
- **warning_triggered**: `bool` (True if `violation_rate > 0.05`)
- **coverage_count**: `int` (Number of unique FCC entries)
- **coverage_threshold_met**: `bool` (True if `coverage_count >= 50`)
- **max_r2**: `float` (Maximum R² achieved across all models)
- **benchmark_met**: `bool` (True if `max_r2 >= 0.5`)
- **sensitivity_results**: `list` (List of {threshold, r2} dicts)
- **feature_importance**: `dict` (Aggregated importance across models)
- **associational_statement**: `str` (Standard disclaimer text: "These findings reflect correlations... No causal mechanisms are implied.")

## Data Flow

1.  **Ingest**: `raw_api_data.json` (from MP/AFLOW/MatBench) -> `cleaned_materials.csv` (MaterialEntry).
2.  **Feature Engineering**: `cleaned_materials.csv` -> `features_materials.csv` (adds descriptors).
3.  **Modeling**: `features_materials.csv` -> `model_results.json` (ModelRun).
4.  **Validation**: `model_results.json` -> `validation_report.json` (ValidationReport).
    - *Logic*: `violation_rate` and `warning_triggered` are calculated during validation. `coverage_count` and `coverage_threshold_met` are calculated during data coverage verification. `benchmark_met` is calculated during benchmark evaluation. `associational_statement` is populated by the report generation task.

## Data Constraints

- **A1 Range**: $0 < A_1 < 3$ (Physical constraint, not a data filter).
- **Null Handling**: $C_{ij}$ nulls result in dropped rows.
- **Data Types**: All floats; no categorical encoding needed for descriptors.