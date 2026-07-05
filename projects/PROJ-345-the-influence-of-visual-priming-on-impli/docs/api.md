# API Reference

## `code/config.py`
Manages project paths and random seed initialization.

### Functions
- `get_path(key: str) -> Path`: Returns the absolute path for a given configuration key (e.g., 'raw', 'processed').
- `set_seed(seed: int) -> None`: Sets the random seed for reproducibility.
- `ensure_directories() -> None`: Creates all required data and state directories.

## `code/data/ingest.py`
Handles downloading and validating IAT datasets.

### Functions
- `download_file_from_osf(osf_id: str, filename: str) -> Path`: Downloads a file from OSF.
- `calculate_checksum(filepath: Path) -> str`: Calculates MD5 checksum of a file.
- `save_checksum(filepath: Path, checksum: str) -> None`: Records checksum in state.
- `load_iat_csv(filepath: Path) -> pd.DataFrame`: Loads and validates IAT CSV.
- `extract_trial_data(df: pd.DataFrame) -> pd.DataFrame`: Extracts trial-level metrics.
- `ingest_iat_data() -> None`: Main entry point for ingestion.

## `code/data/linkage.py`
Derives stimulus IDs from trial data.

### Functions
- `derive_stimulus_id_from_trial_id(trial_id: str) -> Optional[str]`: Maps trial ID to stimulus.
- `run_linkage_derivation() -> None`: Executes linkage derivation for all trials.

## `code/data/preprocess.py`
Derives stimulus metadata and checks for confounding.

### Functions
- `load_human_rated_ambiguity() -> Optional[pd.DataFrame]`: Loads human-rated ambiguity if available.
- `derive_synthetic_ambiguity() -> pd.DataFrame`: Generates synthetic ambiguity scores.
- `check_confounding() -> Dict`: Checks for confounding between prime and trial order.
- `run_preprocessing() -> None`: Main entry point for preprocessing.

## `code/models/lmm.py`
Fits Linear Mixed-Effects Models.

### Functions
- `aggregate_to_stimulus_level(df: pd.DataFrame) -> pd.DataFrame`: Aggregates data to stimulus level.
- `fit_lmm_with_retry(formula: str, data: pd.DataFrame) -> MixedLMResults`: Fits LMM with optimizer retry.
- `run_lmm_analysis() -> None`: Main entry point for modeling.

## `code/models/metrics.py`
Calculates statistical metrics and effect sizes.

### Functions
- `calculate_vif(df: pd.DataFrame) -> Dict[str, float]`: Calculates Variance Inflation Factor.
- `benjamini_hochberg(p_values: List[float]) -> List[float]`: Applies FDR correction.
- `calculate_cohens_d(group1: np.array, group2: np.array) -> float`: Calculates Cohen's d.
- `run_sensitivity_analysis() -> None`: Runs alpha sensitivity analysis.

## `code/viz/plots.py`
Generates visualizations.

### Functions
- `generate_interaction_plot(df: pd.DataFrame) -> Path`: Creates interaction plot.
- `generate_coefficient_table(model_results: pd.DataFrame) -> Path`: Creates coefficient table.

## `code/reports/generate_report.py`
Compiles analysis results into a PDF.

### Functions
- `generate_report_pdf() -> Path`: Generates the final PDF report.
