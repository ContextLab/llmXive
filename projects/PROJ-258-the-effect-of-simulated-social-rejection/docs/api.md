# API Reference: Social Rejection Analysis Pipeline

## `code/config.py`

Centralized configuration for paths, seeds, and thresholds.

### Functions

- `set_random_seed(seed: int) -> None`
 - Sets the random seed for reproducibility across `random`, `numpy`, and `pandas`.
 - **Parameters**:
 - `seed`: Integer seed value.

- `get_path(*segments: str) -> str`
 - Constructs absolute paths relative to the project root.
 - **Parameters**:
 - `segments`: Path components to join.
 - **Returns**: Absolute path string.

### Constants

- `RANDOM_SEED`: Default random seed (42).
- `ALPHA_THRESHOLDS`: Set of alpha values for sensitivity analysis `{0.01, 0.05, 0.1}`.
- `MEMORY_LIMIT_GB`: Default memory limit in GB (7).

---

## `code/data_model.py`

Data structures for the pipeline.

### Classes

- `DesignType(Enum)`
 - `Within-Subjects`: Single-cohort design.
 - `Between-Subjects`: Composite dataset design.

- `@dataclass Dataset`
 - `data: pd.DataFrame`
 - `source: str`
 - `design_type: DesignType`
 - `checksum: Optional[str]`

- `@dataclass PreprocessedRecord`
 - `participant_id: str`
 - `condition: str`
 - `reaction_time: float`
 - `mood_score: float`
 - `is_outlier: bool`

- `@dataclass AnalysisResult`
 - `test_type: str`
 - `f_statistic: float`
 - `p_value: float`
 - `p_fdr: float`
 - `effect_size: float`
 - `ci_lower: float`
 - `ci_upper: float`
 - `design_type: DesignType`

---

## `code/ingest.py`

Data download, validation, and design determination.

### Functions

- `setup_paths() -> Dict[str, str]`
 - Initializes and returns paths for raw, interim, and processed data.

- `get_process_memory_check(threshold_gb: float = 7.0) -> Callable[[], bool]`
 - Returns a function that checks if current RAM usage exceeds the threshold.

- `calculate_file_hash(filepath: str) -> str`
 - Computes SHA-256 hash of a file.

- `save_checksums(checksums: Dict[str, str], output_path: str) -> None`
 - Saves checksums to a JSON file.

- `download_dataset(url: str, output_dir: str) -> str`
 - Downloads a dataset from a URL.
 - **Returns**: Path to the downloaded file.

- `load_dataframe(filepath: str) -> pd.DataFrame`
 - Loads a CSV file into a pandas DataFrame.

- `verify_tasks_in_dataset(df: pd.DataFrame) -> bool`
 - Checks if the dataset contains both Cyberball and Reward tasks.

- `validate_schema(df: pd.DataFrame) -> bool`
 - Validates required columns: `Condition`, `Reaction Time`, `Mood`.

- `verify_single_cohort(df: pd.DataFrame) -> bool`
 - Checks if participant IDs are consistent within a single dataset.

- `log_design_switch(from_type: str, to_type: str, log_path: str) -> None`
 - Logs the transition between design types.

- `validate_composite_datasets(df_rejection: pd.DataFrame, df_reward: pd.DataFrame) -> bool`
 - Matches participant IDs across two datasets.

- `run_ingestion() -> None`
 - Main entry point for the ingestion pipeline.

---

## `code/preprocess.py`

Data cleaning, normalization, and feature extraction.

### Functions

- `clean_data(df: pd.DataFrame) -> pd.DataFrame`
 - Removes missing values and invalid entries.

- `normalize_rt(df: pd.DataFrame) -> pd.DataFrame`
 - Standardizes reaction times (z-score per condition).

- `detect_outliers_iqr(df: pd.DataFrame, group_col: str = 'Condition') -> pd.DataFrame`
 - Flags outliers using the IQR method per group.

- `extract_features(df: pd.DataFrame) -> pd.DataFrame`
 - Computes `mean_rt` and `avg_mood` per participant/condition.

- `save_preprocessed_data(df: pd.DataFrame, output_path: str) -> None`
 - Saves preprocessed data to CSV.

- `run_preprocessing() -> None`
 - Main entry point for the preprocessing pipeline.

---

## `code/analysis.py`

Statistical analysis: ANOVA, FDR, sensitivity.

### Functions

- `run_anova(df: pd.DataFrame, design_type: str) -> Dict[str, Any]`
 - Executes Mixed ANOVA (Within-Subjects) or One-Way ANOVA (Between-Subjects).

- `apply_fdr(p_values: List[float]) -> List[float]`
 - Applies Benjamini-Hochberg FDR correction.

- `sensitivity_sweep(df: pd.DataFrame, alpha_set: Set[float]) -> Dict[str, Any]`
 - Runs analysis across multiple alpha thresholds.

- `save_sensitivity_results(results: Dict[str, Any], output_path: str) -> None`
 - Saves sensitivity analysis results to JSON.

- `run_analysis_pipeline() -> None`
 - Main entry point for the analysis pipeline.

---

## `code/report.py`

Report generation and phrasing enforcement.

### Functions

- `generate_report_logic(results: Dict[str, Any], design_type: str) -> str`
 - Generates report text with appropriate phrasing based on design type.

- `save_final_results(results: Dict[str, Any], design_type: str, output_path: str) -> None`
 - Saves final results to JSON, including `p_fdr` and `design_type`.

- `save_report(report_text: str, output_path: str) -> None`
 - Saves the final report to Markdown.

- `verify_report_constraints(report_path: str) -> bool`
 - Asserts "associational" is present and "causal" is absent for Between-Subjects.

- `calculate_effect_size_ci(results: Dict[str, Any]) -> Tuple[float, float]`
 - Computes confidence intervals for effect sizes.

- `run_reporting_pipeline() -> None`
 - Main entry point for the reporting pipeline.

---

## `code/logging_utils.py`

Memory tracking and logging utilities.

### Functions

- `get_process_memory_mb() -> float`
 - Returns current process memory usage in MB.

- `setup_memory_logger(log_path: str) -> logging.Logger`
 - Configures a logger for memory snapshots.

- `log_memory_snapshot(logger: logging.Logger, stage: str) -> None`
 - Logs memory usage at a specific pipeline stage.
