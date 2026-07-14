# API Reference

## Data Module (`code/data/`)

### `synthetic_gen.py`
Generates synthetic adsorption data for pipeline validation.

- `generate_synthetic_data(n_samples: int = 5000) -> pd.DataFrame`
 - Creates a DataFrame with random molecular descriptors and correlated isotherm parameters.
 - Adds noise and random correlations to simulate real-world complexity.

- `main()`
 - Entry point for script execution. Writes output to `data/raw/synthetic_data.csv`.

### `download.py`
Handles external data fetching and verification.

- `attempt_nist_fetch() -> Optional[pd.DataFrame]`
 - Attempts to download data from NIST (placeholder logic).
- `attempt_fallback_fetch() -> Optional[pd.DataFrame]`
 - Attempts alternative fetch methods.
- `write_verification_log(status: str, message: str) -> None`
 - Writes a JSON log file (`data/verification_log.json`) recording the fetch attempt status.

### `load_external.py`
Loads manually curated external datasets.

- `load_external_data(path: str) -> pd.DataFrame`
 - Loads a CSV file and validates it against the dataset schema.
- `validate_external_data(df: pd.DataFrame) -> bool`
 - Returns True if the DataFrame conforms to `contracts/dataset.schema.yaml`.

### `preprocess.py`
Cleans and prepares data for modeling.

- `filter_type_isotherms(df: pd.DataFrame) -> pd.DataFrame`
 - Filters for Type I isotherms.
- `normalize_units(df: pd.DataFrame) -> pd.DataFrame`
 - Ensures units are consistent (e.g., m²/g for surface area).
- `detect_outliers(df: pd.DataFrame) -> pd.DataFrame`
 - Identifies rows with identical descriptors but conflicting targets.
- `preprocess_pipeline(raw_path: str) -> pd.DataFrame`
 - Orchestrates the full preprocessing workflow.

### `descriptors.py`
Calculates molecular descriptors using RDKit.

- `calculate_descriptors(smiles: str) -> Dict[str, float]`
 - Returns a dictionary of descriptors (MW, PSA, Polarizability, Kinetic Diameter, etc.).
- `calculate_descriptors_batch(df: pd.DataFrame, smiles_col: str) -> pd.DataFrame`
 - Vectorized calculation for a DataFrame.

## Models Module (`code/models/`)

### `train.py`
Manages model training and splitting.

- `material_level_split(df: pd.DataFrame, test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]`
 - Splits data by `material_id` to prevent data leakage.
- `train_models(train_df: pd.DataFrame) -> Dict[str, Any]`
 - Trains Linear, RF, and GB models. Returns fitted estimators.

### `evaluate.py`
Calculates performance metrics and statistical significance.

- `calculate_metrics(model, X_test, y_test) -> Dict[str, float]`
 - Returns R², RMSE, MAE.
- `benjamini_hochberg_fdr(p_values: List[float]) -> List[float]`
 - Applies FDR correction to a list of p-values.

### `null_comparison.py`
Implements baseline comparison.

- `predict_mean_null_model(y_train) -> float`
 - Returns the mean of the training target.
- `compare_models(model_metrics, null_metrics) -> Dict`
 - Compares model performance against the null baseline.

## Interpret Module (`code/interpret/`)

### `shap_analysis.py`
Generates SHAP plots and performs consensus validation.

- `generate_shap_summary_plot(model, X_test) -> None`
 - Saves a SHAP summary plot to `figures/shap_summary.png`.
- `validate_consensus(top_features: List[str]) -> Dict`
 - Checks if top features match the literature consensus list.
 - Returns a report for `data/validation/sc002_match_report.json`.
- `retrain_top_features(model, X, y, top_n: int = 3) -> Dict`
 - Retains only top N features, retrains, and returns the new R² score.
 - Used to generate `data/validation/sc003_r2_report.json`.

### `diagnostics.py`
Diagnoses model failures.

- `diagnose_nonlinearity(X, y) -> Dict`
 - Generates a report suggesting non-linear effects if R² is low.

## Orchestrator (`code/main.py`)

- `run_full_pipeline(mode: str = 'synthetic')`
 - Executes the entire workflow based on the selected mode.
- `run_synthetic_flow()`
 - Executes the synthetic data pipeline.
- `run_external_flow()`
 - Executes the external data pipeline with validation checks.
