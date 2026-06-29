# Data Model: Predicting the Impact of Impurities on the Superconductivity of Magnesium Diboride

## Entity Definitions

### 1. DatasetRecord
Represents a single experimental entry for MgB₂.
- **id**: Unique identifier (string).
- **source**: Enum (`"materials_project"`, `"supercon"`).
- **tc_k**: Critical Temperature (float, Kelvin). **Target Variable**.
- **impurities**: JSON object or flattened columns mapping element symbol (str) to concentration (float, atomic %).
  - *Example*: `{"C": 0.5, "Si": 0.2}`.
- **synthesis_temp_k**: Synthesis temperature (float, Kelvin).
- **synthesis_pressure_gpa**: Synthesis pressure (float, GPa).
- **method_flags**: List of strings (e.g., `["solid_state_reaction", "hot_pressing"]`).
- **provenance**: Object containing `query_timestamp` (ISO8601), `data_version` (string), `source_url` (string).
- **impurity_schema_validated**: Boolean (True if the record passed the required column structure check).

### 2. ModelPerformance
Stores evaluation metrics for a trained model variant.
- **model_type**: String (e.g., `"RidgeRegression"`, `"RandomForest"`).
- **hyperparameters**: JSON object of the specific configuration used.
- **r2_train**: Float.
- **r2_test**: Float.
- **mae_train**: Float.
- **mae_test**: Float.
- **fit_timestamp**: ISO8601.

### 3. ImpurityEffect
Derived entity linking an impurity to its impact.
- **element**: String (e.g., `"C"`).
- **delta_tc_per_pct**: Float (K per 1 atomic %).
- **p_value**: Float (from Partial F-test or Feature Permutation Test).
- **is_significant**: Boolean (True if $p < 0.05$).
- **confidence_interval**: Tuple (Lower, Upper) from bootstrap.
- **sample_count**: Integer (Number of samples containing this impurity).
- **collinearity_flag**: Boolean (True if VIF $\ge 5.0$).

## Data Flow

1.  **Raw Ingestion**:
    - Download `dev.tsv` from `taqwa92/cm.mgb2`.
    - Query Materials Project API (if API key provided).
    - **Schema Validation**: Verify presence of `Tc` and `impurity` concentration fields. If missing, attempt regex parsing on `doping_info`/`description` fields using pattern `r'([A-Z][a-z]?)\s*:?\\s*([0-9.]+)%?'`. If parsing fails or required columns are absent, fail with error.
    - Output: `data/raw/mgb2_raw.json` (combined).
2.  **Preprocessing**:
    - Filter: Keep only rows where `tc_k` is not null AND at least one impurity is present.
    - **Sample Size Check**: If total N < 100, halt with error.
    - Convert: Weight % $\to$ Atomic % using atomic weights from `pymatgen`.
    - Handle Ranges: If synthesis temp is "800-900", use midpoint 850 and flag `synthesis_temp_imputed=True`.
    - **Stratification**: Group elements with N < 5 into a 'Rare' bin *only* for train/test split. **No effect sizes are estimated for this bin.**
    - Output: `data/processed/mgb2_clean.csv`.
3.  **Modeling**:
    - Split: Stratified by `impurity_type` (Rare $\to$ "Rare" bin).
    - Train: Ridge, RF, XGBoost.
    - **Significance Testing**:
      - Ridge: Partial F-test.
      - RF/XGB: Feature Permutation Test (N=100).
    - Output: `data/processed/model_results.json`.
4.  **Analysis**:
    - Compute PDP and Significance.
    - **Filtering**: Exclude impurities with N < 5 or p > 0.05 from the "Top 3" and "Rule of Thumb" tables.
    - Output: `data/processed/impurity_effects.json`.

## Constraints & Validations

- **Missing Data**: Rows with missing `tc_k` or missing impurity data are **dropped**, not imputed.
- **Unit Standardization**: All concentrations must be in **atomic %**. All temperatures in **Kelvin**. All pressures in **GPa**.
- **Collinearity**: If VIF $\ge 5.0$, the feature is retained in Ridge Regression but flagged. **No features are removed.**
- **Sample Size**: Pipeline halts if N < 100.
- **Effect Estimation**: No $\Delta T_c$ is reported for elements with N < 5.