# Pipeline Architecture

## Execution Flow

The pipeline is orchestrated by `code/main.py`. It supports two distinct execution modes: **Synthetic** and **External**.

### 1. Synthetic Flow (MVP Validation)

Used to validate the entire pipeline without relying on external data availability.

1. **Download Phase**: Skips external fetch, writes `verification_log.json` indicating "Synthetic Mode".
2. **Synthetic Generation**:
 - Calls `code/data/synthetic_gen.py` to generate 5000 rows of synthetic data.
 - Output: `data/raw/synthetic_data.csv`.
3. **Preprocessing**:
 - Loads raw data.
 - Calculates molecular descriptors via `code/data/descriptors.py`.
 - Filters Type I isotherms, normalizes units, handles missing values.
 - Detects outliers (identical descriptors, conflicting targets).
 - Output: `data/processed/processed_data.csv` and `data/processed/outliers.csv`.
4. **Training**:
 - Performs material-level split.
 - Trains Linear, RF, and GB models.
 - Output: `models/` directory with saved model artifacts.
5. **Evaluation**:
 - Calculates R², RMSE, MAE.
 - Runs permutation tests and FDR correction.
6. **SHAP & Diagnostics**:
 - Generates SHAP summary plots.
 - Since this is synthetic data, consensus checks (SC-002) are skipped or marked as "N/A" in reports.

### 2. External Flow (Scientific Validation)

Used to validate scientific hypotheses against real literature data.

1. **Download Phase**: Attempts to fetch from NIST (if configured) or loads the pre-curated `data/external/kr_cnt.csv`.
2. **Preprocessing**:
 - Validates data against `contracts/dataset.schema.yaml`.
 - Calculates descriptors.
 - Filters and normalizes.
3. **Training**: Same as Synthetic Flow.
4. **Evaluation**: Same as Synthetic Flow.
5. **SHAP & Consensus Validation**:
 - **SC-002 Check**: Compares top SHAP features against the consensus list. Generates `data/validation/sc002_match_report.json`.
 - **SC-003 Check**: Retains only the top 3 features, retrains the model, and verifies R² >= 0.60. Generates `data/validation/sc003_r2_report.json`.
 - **Diagnostics**: If R² < 0.5, generates a diagnostic report suggesting non-linear effects.

## Data Contracts

All data artifacts must conform to schemas defined in `contracts/`.

- **`contracts/dataset.schema.yaml`**: Defines required columns (e.g., `material_id`, `polarizability`, `langmuir_capacity`), data types, and value ranges.
- **`contracts/model_output.schema.yaml`**: Defines the structure of model evaluation results and SHAP outputs.

The `code/data/validate_schema.py` module is used to enforce these contracts at runtime.

## Error Handling

- **Missing Data**: If external data is missing and synthetic mode is not selected, the pipeline fails loudly with a clear error message.
- **Schema Violations**: If loaded data does not match the schema, the pipeline halts and logs the specific validation errors.
- **Outliers**: Detected outliers are written to `data/processed/outliers.csv` but do not halt the pipeline; they are logged for review.

## Configuration

Configuration is managed via environment variables and command-line arguments:

- `--mode`: `synthetic` or `external`.
- `--data-path`: Optional override for external data location.
- `--output-dir`: Optional override for output directory.
