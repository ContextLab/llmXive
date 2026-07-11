# API Documentation: Code Summarization Bug Localization Study

This document describes the programmatic interfaces (Python modules) available in the `code/` directory for the "Evaluating the Efficacy of Code Summarization Techniques for Bug Localization" study.

## Overview

The project is structured into three main functional areas:
1. **Data Preparation** (`code/data_prep/`): Scripts to download datasets, generate summaries, and prepare input data.
2. **Analysis** (`code/analysis/`): Statistical analysis pipelines, including McNemar's tests, LME models, and bootstrapping.
3. **Utilities** (`code/utils/`): Helper functions for logging, configuration, data models, and study management.

## Data Preparation API

### `code/data_prep/download_defects4j.py`
Handles fetching and parsing the Defects4J dataset.

- `download_defects4j()`: Fetches the Defects4J archive.
- `parse_defects4j_data(data_path)`: Parses the raw archive into structured data.
- `extract_buggy_methods_from_source(source_path)`: Extracts specific buggy method locations.
- `stratify_methods(methods, config)`: Stratifies methods based on project type/complexity.
- `save_stratified_methods(methods, output_path)`: Saves the stratified list to CSV/JSON.
- `save_stratification_config(config, output_path)`: Saves the stratification parameters.
- `main()`: Entry point for the script.

### `code/data_prep/generate_summaries.py`
Generates code summaries using deterministic simulation and rule-based extraction.

- `load_stratified_methods(input_path)`: Loads methods from the stratified list.
- `extract_first_comment_line(code_snippet)`: Extracts the first comment line from code.
- `parse_method_signature(code_snippet)`: Parses method name, arguments, and return type.
- `generate_llm_sim_summary(method_data)`: Generates a deterministic "LLM-Sim" summary string.
- `generate_rule_summary(method_data)`: Generates a rule-based summary.
- `save_summaries_to_csv(summaries, output_path)`: Saves summaries to a CSV file.
- `main()`: Entry point for the script.

### `code/data_prep/generate_summaries_real_llm.py`
Generates summaries using a real LLM (CodeLlama-7b) for non-CI environments.

- `load_model(model_name)`: Loads the HuggingFace model with 8-bit quantization.
- `generate_llm_summary(model, code_snippet)`: Generates a summary using the loaded model.
- `save_summaries(summaries, output_path)`: Saves the generated summaries.
- `main()`: Entry point for the script.

### `code/data_prep/setup_data_directories.py`
Initializes the required directory structure.

- `setup_data_directories(base_path)`: Creates all necessary subdirectories.
- `main()`: Entry point for the script.

## Analysis API

### `code/analysis/run_statistics.py`
Main orchestration script for statistical analysis.

- `load_interaction_logs(log_path)`: Loads anonymized interaction logs.
- `load_summaries(summary_path)`: Loads generated summaries.
- `compute_topk_accuracy(logs, k)`: Computes Top-K accuracy metrics.
- `compute_speed_metrics(logs)`: Computes time-to-decision metrics.
- `run_mcnemar_tests(logs)`: Runs McNemar's tests for accuracy comparison.
- `run_lme_analysis(logs)`: Runs Linear Mixed-Effects models for speed.
- `compute_effect_sizes(logs)`: Computes Odds Ratios and Cohen's d.
- `run_sensitivity_analysis(logs, thresholds)`: Runs sensitivity analysis across cutoffs.
- `detect_outliers(logs)`: Detects statistical outliers.
- `main()`: Entry point for the script.

### `code/analysis/bootstrap_utils.py`
Utilities for bootstrapping confidence intervals.

- `bootstrap_cohen_d(group1, group2, n_resamples, seed)`: Computes bootstrapped Cohen's d.
- `bootstrap_odds_ratio(successes, failures, n_resamples, seed)`: Computes bootstrapped Odds Ratio.
- `run_lme_model(data)`: Runs the LME model on the provided data.
- `compute_confidence_interval(data, method, confidence)`: Computes CI for a dataset.
- `main()`: Entry point for the script.

### `code/analysis/correction_utils.py`
Utilities for multiple comparison corrections.

- `holm_bonferroni_correction(p_values, alpha)`: Applies Holm-Bonferroni correction.
- `apply_correction_to_dataframe(df, p_value_column, alpha)`: Applies correction to a DataFrame.
- `save_correction_results(results, output_path)`: Saves correction results to JSON.
- `load_correction_results(input_path)`: Loads correction results from JSON.
- `main()`: Entry point for the script.

## Utilities API

### `code/utils/models.py`
Data models for the study.

- `Participant`: Dataclass representing a study participant.
- `Task`: Dataclass representing a bug localization task.
- `Summary`: Dataclass representing a code summary.
- `InteractionLog`: Dataclass representing a participant's interaction log.
- `AnalysisResult`: Dataclass representing analysis results.

### `code/utils/config_manager.py`
Environment and configuration management.

- `Config`: Class representing the configuration object.
- `get_config()`: Retrieves the singleton configuration instance.

### `code/utils/logging_utils.py`
Logging infrastructure.

- `setup_logging(log_level)`: Configures the logging system.
- `get_logger(name)`: Retrieves a logger instance.
- `ErrorHandler`: Class for handling and logging errors.
- `main()`: Entry point for the script.

### `code/utils/interaction_logger.py`
Handles logging of participant interactions.

- `setup_logger()`: Sets up the interaction logger.
- `load_raw_logs(path)`: Loads raw interaction logs.
- `save_raw_logs(logs, path)`: Saves raw interaction logs.
- `log_interaction(participant_id, task_id, condition, timestamp, line)`: Logs a single interaction.
- `detect_dropout(logs)`: Detects participants who dropped out.
- `flag_partial_data(logs)`: Flags logs with incomplete data.
- `get_participant_summary(participant_id, logs)`: Gets summary for a participant.
- `process_all_participants(logs)`: Processes logs for all participants.
- `main()`: Entry point for the script.

### `code/utils/anonymize_logs.py`
Handles data anonymization.

- `setup_logger()`: Sets up the anonymization logger.
- `load_raw_logs(path)`: Loads raw logs.
- `create_anonymization_mapping(logs)`: Creates a mapping of IDs to anonymous tokens.
- `anonymize_logs(logs, mapping)`: Anonymizes the logs.
- `save_anonymized_logs(logs, path)`: Saves anonymized logs.
- `save_anonymization_mapping(mapping, path)`: Saves the mapping for reference (securely).
- `main()`: Entry point for the script.

### `code/utils/assignment_generator.py`
Generates task assignments (Latin Square design).

- `generate_latin_square(size)`: Generates a Latin Square matrix.
- `assign_conditions(participants, tasks, matrix)`: Assigns conditions to participants.
- `generate_cohort_assignments(cohort_size)`: Generates assignments for a full cohort.
- `save_assignments(assignments, path)`: Saves assignments to JSON.
- `main()`: Entry point for the script.

### `code/utils/latency_calibrator.py`
Verifies timestamp precision.

- `measure_timestamp_precision()`: Measures system timestamp precision.
- `run_calibration()`: Runs the full calibration procedure.
- `main()`: Entry point for the script.

### `code/utils/hash_artifacts.py`
Generates and verifies SHA-256 hashes for reproducibility.

- `hash_file(path)`: Generates hash for a file.
- `hash_directory(path)`: Generates hash for a directory.
- `verify_file_hash(path, expected_hash)`: Verifies a file's hash.
- `save_hashes(hashes, path)`: Saves hashes to a manifest.
- `load_hashes(path)`: Loads hashes from a manifest.
- `generate_manifest(artifacts)`: Generates a manifest of artifacts.
- `main()`: Entry point for the script.

### `code/utils/generate_artifact_hashes.py`
Collects artifacts and generates their hashes.

- `collect_artifacts(base_path)`: Collects all relevant artifacts.
- `generate_hashes(artifacts)`: Generates hashes for collected artifacts.
- `main()`: Entry point for the script.

### `code/utils/generate_baseline_results.py`
Generates baseline results for reproducibility checks.

- `load_analysis_results(path)`: Loads analysis results.
- `save_baseline_results(results, path)`: Saves baseline results.
- `verify_input_data()`: Verifies input data integrity.
- `main()`: Entry point for the script.

### `code/utils/generate_reproducibility_package.py`
Creates the final reproducibility package.

- `should_exclude(path)`: Checks if a path should be excluded.
- `create_reproducibility_package(output_path)`: Creates the tarball.
- `main()`: Entry point for the script.

### `code/utils/secure_consent_storage.py`
Manages secure storage for consent forms.

- `ensure_consent_directory(path)`: Ensures the consent directory exists.
- `enforce_file_permissions(path)`: Sets file permissions to 600.
- `enforce_directory_permissions(path)`: Sets directory permissions to 700.
- `ensure_gitignore_exclusion()`: Ensures `.gitignore` excludes consent data.
- `secure_consent_storage(path)`: Main function to secure consent storage.
- `main()`: Entry point for the script.

### `code/utils/startup_runner.py`
Runs startup checks and calibrations.

- `run_startup_checks()`: Runs all startup checks (latency, config, etc.).
- `main()`: Entry point for the script.

## Entry Points

Most modules include a `main()` function intended to be run as a script.
Example usage:

```bash
python code/data_prep/download_defects4j.py
python code/analysis/run_statistics.py
```

## Dependencies

Refer to `requirements.txt` for the full list of dependencies. Key libraries include:
- `pandas`
- `numpy`
- `statsmodels`
- `scikit-learn`
- `torch` (for real LLM tasks)
- `transformers` (for real LLM tasks)