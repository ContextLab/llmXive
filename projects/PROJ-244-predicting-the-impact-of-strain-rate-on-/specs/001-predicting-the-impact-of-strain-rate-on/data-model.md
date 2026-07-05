# Data Model: Predicting the Impact of Strain Rate on the Yield Strength of Metals

## Entities & Relationships

### TensileTestRecord
Represents a single experimental measurement.
*   **Primary Key**: `record_id` (UUID)
*   **Attributes**:
    *   `alloy_family` (string): e.g., "AA-6061", "AISI-4340"
    *   `yield_strength_mpa` (float): Standardized to MPa. **Required**.
    *   `strain_rate_s_inv` (float): Standardized to s⁻¹. **Required**.
    *   `temperature_k` (float): Optional, in Kelvin.
    *   `grain_size_um` (float): Optional, in µm. Can be imputed.
    *   `composition_vector` (list[float]): 10-dimensional vector of elemental fractions.
    *   `source_id` (string): Original ID from NIST/OpenML or "SIMULATED".
    *   `is_imputed` (boolean): True if grain size or composition was imputed.
    *   `imputation_confidence` (float): Correlation score (r) from KNN validation.
    *   `raw_data_hash` (string): SHA-256 of the original raw record.
    *   `is_low_confidence` (boolean): True if KNN correlation r < 0.3.

### AlloyFamily
Categorical grouping for stratification.
*   **Attributes**:
    *   `family_name` (string)
    *   `primary_elements` (list[string])
    *   `sample_count` (int): Count of records in this family.
    *   `is_low_sample` (boolean): True if count < 20.

### ConstitutiveModelParameters
Fitted parameters for empirical models.
*   **Attributes**:
    *   `model_type` (string): "Johnson-Cook" or "Zerilli-Armstrong"
    *   `alloy_family` (string)
    *   `parameters` (dict): e.g., `{"A": 100, "B": 200, "n": 0.5, "C": 0.01, "m": 1.0}`
    *   `fit_r2` (float): R² on training set.

## Data Flow & Transformation Rules

1.  **Ingestion**:
    *   Input: Raw CSV/JSON/XML (or Simulated Generator).
    *   Transformation: Unit conversion (MPa, s⁻¹, µm).
    *   Filter: Drop records where `yield_strength_mpa` or `strain_rate_s_inv` is missing.
    *   Output: `data/raw/standardized.csv`.

2.  **Raw State Preservation**:
    *   Input: `data/raw/standardized.csv`.
    *   Action: Copy to `data/processed/raw_for_sensitivity.csv` BEFORE imputation.
    *   Output: `data/processed/raw_for_sensitivity.csv`.

3.  **Imputation**:
    *   Input: `data/raw/standardized.csv`.
    *   Logic:
        *   If `composition` missing: Impute using `alloy_family` average.
        *   If `grain_size` missing: Impute using KNN (k=5) on **composition and strain rate** (NOT yield strength).
        *   Validation: If KNN correlation `r < 0.3`, flag record as `is_low_confidence=True` and **exclude from sensitivity analysis** (but retain in main dataset per FR-003).
    *   Output: `data/processed/imputed.csv`, `data/processed/low_confidence_report.csv`.

4.  **Splitting**:
    *   Input: `data/processed/imputed.csv`.
 * Logic: Stratified split ([deferred] train, [deferred] test) by `alloy_family`.
    *   Constraint: If `alloy_family` count < 20, exclude from stratification (flag as low-sample).
    *   Output: `data/processed/train.csv`, `data/processed/test.csv`.

5.  **Modeling**:
    *   Input: `train.csv`.
    *   Output: Serialized models (`.pkl`), performance metrics (`.json`).

6.  **Evaluation**:
    *   Input: `test.csv`, `models`, `raw_for_sensitivity.csv`.
    *   Output: Partial dependence plots (`.png`), SHAP summary (`.json`), Wilcoxon p-values, Sensitivity Analysis (`.json`).

## Constraints & Validation

*   **Unit Constraint**: All `yield_strength` must be in [0, 5000] MPa. All `strain_rate` must be in [1e-5, 1e4] s⁻¹.
*   **Composition Constraint**: Sum of `composition_vector` must be 1.0 ± 0.01.
*   **Imputation Constraint**: No synthetic data generation for `yield_strength` or `strain_rate`.
*   **Low Sample Handling**: Families with < 20 samples are excluded from model training but included in the "Low Sample Regime" report.
*   **Target Leakage Prevention**: KNN imputation for grain size uses **only** composition and strain rate. Yield strength is **never** used as a predictor for imputation.
*   **Processing History Note**: Grain size is influenced by processing history (e.g., cooling rate), which is not directly measured. The imputation model uses composition and strain rate as proxies, acknowledging the potential for residual confounding.
