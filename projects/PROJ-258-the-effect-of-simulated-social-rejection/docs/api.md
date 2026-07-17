# llmXive Project API Documentation

This document provides the public API surface for the "Effect of Simulated Social Rejection on Neural Responses to Positive Feedback" project.
Generated from source code docstrings and module definitions.

---

## `code/analysis.py`

Statistical analysis module for ANOVA execution, FDR correction, and sensitivity sweeps.

### Public Functions

#### `run_anova(df, design_type)`
Executes the appropriate ANOVA test based on the study design.
- **Parameters**:
 - `df` (pd.DataFrame): The preprocessed dataset.
 - `design_type` (str): Either "Within-Subjects" or "Between-Subjects".
- **Returns**:
 - `Dict`: Results containing F-statistic, p-value, and effect size.
- **Note**: If `design_type` is "Between-Subjects", the function explicitly flags the inability to test causal modulation.

#### `apply_fdr(p_values)`
Applies the Benjamini-Hochberg False Discovery Rate correction.
- **Parameters**:
 - `p_values` (List[float]): List of raw p-values.
- **Returns**:
 - `List[float]`: List of adjusted p-values.

#### `sensitivity_sweep(df, alpha_set)`
Performs a sensitivity analysis across multiple alpha thresholds.
- **Parameters**:
 - `df` (pd.DataFrame): The dataset to analyze.
 - `alpha_set` (Set[float]): Set of alpha values to test (default: {0.01, 0.05, 0.1}).
- **Returns**:
 - `Dict`: A mapping of alpha values to significance results.

#### `save_sensitivity_results(results, output_path)`
Saves the sensitivity sweep results to a JSON file.

#### `run_analysis_pipeline(data_path, output_path)`
Orchestrates the full analysis pipeline: loading data, running ANOVA, applying FDR, and performing sensitivity sweeps.

---

## `code/config.py`

Configuration management for paths, seeds, and thresholds.

### Public Functions

#### `set_random_seed(seed)`
Sets the random seed for reproducibility across numpy and random modules.

#### `get_path(key)`
Retrieves a project path based on a logical key (e.g., "raw_data", "processed_data").

#### `get_alpha_set()`
Returns the configured set of alpha thresholds for sensitivity analysis.

#### `get_memory_threshold_mb()`
Returns the maximum allowed memory usage in megabytes (default: 7 GB).

---

## `code/data_model.py`

Data structures for the project entities.

### Classes

#### `DesignType` (Enum)
Enumerates valid study designs:
- `WITHIN_SUBJECTS`
- `BETWEEN_SUBJECTS`

#### `Dataset`
Dataclass representing a raw dataset source.
- **Fields**: `url`, `status`, `checksum`, `design_type`.

#### `PreprocessedRecord`
Dataclass representing a cleaned data record.
- **Fields**: `participant_id`, `condition`, `reaction_time`, `mood_score`.

#### `AnalysisResult`
Dataclass representing the output of statistical tests.
- **Fields**: `test_type`, `f_stat`, `p_value`, `p_fdr`, `effect_size`, `ci_95`.

---

## `code/ingest.py`

Data ingestion, validation, and design determination logic.

### Public Functions

#### `setup_paths()`
Initializes directory structures and returns path dictionaries.

#### `estimate_dataset_size(manifest)`
Estimates the total size of datasets from a manifest to prevent RAM overflow.
- **Behavior**: Halts execution with exit code 1 if estimated size > 7 GB.

#### `download_dataset(url)`
Downloads a dataset from OpenNeuro. Verifies presence of required tasks (Cyberball/Reward).

#### `load_dataframe(path)`
Loads a CSV or TSV file into a pandas DataFrame.

#### `verify_tasks_in_dataset(df, required_tasks)`
Checks if the dataset contains the necessary experimental tasks.

#### `validate_schema(df)`
Validates that the DataFrame contains required columns (Condition, Reaction Time, Mood).

#### `verify_single_cohort(df)`
Checks if participant IDs are consistent within a single dataset to determine "Within-Subjects" potential.

#### `validate_separate_datasets(df_rejection, df_reward)`
Validates two distinct datasets independently without merging.

#### `check_single_cohort_constraint()`
Ensures that distinct studies are not falsely labeled as "Within-Subjects".

#### `match_ids_across_datasets(df_rejection, df_reward)`
Checks for participant ID overlap across two datasets.

#### `handle_data_unavailable()`
Raises an exception if no valid data source is found.

#### `log_design_switch(event_details)`
Logs the transition from Single-Cohort attempt to Separate-Streams fallback.

#### `write_metadata(design_type)`
Writes the final design type to `data/processed/metadata.json`.

#### `calculate_file_hash(filepath)`
Computes SHA-256 checksum for a file.

#### `save_checksums(hashes, output_path)`
Saves checksums to the project state file.

#### `run_ingestion()`
Main entry point for the ingestion pipeline.

---

## `code/preprocess.py`

Data cleaning, normalization, and feature extraction.

### Public Functions

#### `clean_data(df)`
Removes rows with missing critical values and handles basic data cleaning.

#### `normalize_rt(df)`
Standardizes reaction time data.

#### `detect_outliers_iqr(df, group_col='Condition')`
Flags outliers using the Interquartile Range method per condition group.

#### `extract_features(df)`
Computes summary statistics (mean RT, avg mood) per participant/condition.

#### `save_preprocessed_data(df, output_path)`
Saves the cleaned and feature-extracted data to CSV.

#### `run_preprocessing(input_path, output_path)`
Orchestrates the full preprocessing pipeline.

---

## `code/report.py`

Report generation and constraint verification.

### Public Functions

#### `calculate_effect_size_ci(results)`
Calculates 95% confidence intervals for effect sizes, handling convergence warnings for small N.

#### `generate_report_logic(results, design_type)`
Constructs the content for the final report, injecting "associational" language for Between-Subjects designs.

#### `save_report(content, output_path)`
Writes the final report to `reports/final_report.md`.

#### `verify_report_constraints(report_path)`
Verifies that the report contains required phrases (e.g., "associational") and excludes forbidden terms (e.g., "causal" in results).

#### `save_final_results(results, output_path)`
Saves the final analysis results to JSON, ensuring `p_fdr` and `design_type` are present.

#### `run_reporting_pipeline(data_path, report_path)`
Orchestrates the full reporting pipeline.

---

## `code/logging_utils.py`

Logging and memory monitoring utilities.

### Public Functions

#### `get_process_memory_mb()`
Returns the current memory usage of the process in MB.

#### `setup_memory_logger()`
Configures the logger for memory usage tracking.

#### `log_memory_snapshot()`
Logs the current memory snapshot.

---

## `code/performance_monitor.py`

Performance monitoring and optimization.

### Public Functions

#### `PerformanceMonitor` (Class)
Context manager for tracking execution time and memory usage.

#### `performance_watchdog(func)`
Decorator to monitor performance of a function.

#### `optimize_dataframe_operations(df)`
Applies optimizations to dataframe operations to reduce memory footprint.

#### `run_pipeline_with_monitoring(pipeline_func, *args, **kwargs)`
Runs a pipeline function with full performance monitoring.

---

## `code/cleanup_refactor.py`

Code cleanup and refactoring utilities.

### Public Functions

#### `CodeRefactorer` (Class)
Utility class for refactoring code structures.

#### `main()`
Entry point for the refactoring script.

---

## `code/lint_format_setup.py`

Linting and formatting setup utilities.

### Public Functions

#### `check_tool_installed(tool_name)`
Checks if a specific tool (e.g., black, flake8) is installed.

#### `run_linting()`
Runs the configured linter.

#### `run_formatting_check()`
Runs the configured formatter check.

#### `main()`
Entry point for the lint/format setup script.

---

## `code/create_structure.py`

Project structure creation utilities.

### Public Functions

#### `main()`
Entry point to create the initial project directory structure.