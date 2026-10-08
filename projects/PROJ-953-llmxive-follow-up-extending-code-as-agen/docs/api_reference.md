# API Reference: llmXive Code Scripts

This document provides a comprehensive reference for the public functions exposed by the Python modules in the `code/scripts/` directory. These scripts form the core of the llmXive automated science pipeline, handling data ingestion, feature extraction, model training, and state management.

## General Usage

Most scripts are designed to be run as standalone CLI tools:

```bash
python code/scripts/<script_name>.py [arguments]
```

They also expose public functions that can be imported for programmatic use within the pipeline or for testing.

---

## `code/scripts/baseline_runner.py`

Handles the execution of baseline tasks in isolated environments to generate ground truth outcomes.

**Public Functions:**
- `ExecutionResult`: Dataclass representing the outcome of a baseline execution (Pass, Fail, Timeout).
- `check_gpu_usage()`: Verifies if any active CUDA context exists and logs warnings if GPU drivers are present but unused.
- `run_with_timeout(func, timeout)`: Executes a function with a configurable timeout, raising an exception if the limit is exceeded.
- `setup_venv(path)`: Creates a Python virtual environment at the specified path.
- `install_dependencies(venv_path, requirements_file)`: Installs dependencies from a requirements file into the virtual environment.
- `run_baseline_task(task_id, code_diff, timeout=600)`: Orchestrates the setup, execution, and outcome recording for a single task.
- `main()`: Entry point for the CLI script.

**Dependencies:** `time`, `threading`, `subprocess`, `os`, `tempfile`, `shutil`

---

## `code/scripts/calculate_correlations.py`

Computes statistical correlations between structural features and execution outcomes.

**Public Functions:**
- `encode_target(df, target_col)`: Encodes categorical target variables (e.g., Pass/Fail) into numeric format.
- `calculate_correlations(features_df, target_series)`: Calculates Pearson/Spearman correlation coefficients between features and the target.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `sys`, `json`, `pickle`, `numpy`, `pandas`

---

## `code/scripts/checksum_artifacts.py`

Generates and verifies checksums for project artifacts to ensure data integrity (Constitution Principle VIII).

**Public Functions:**
- `calculate_sha256(file_path)`: Computes the SHA-256 hash of a file.
- `verify_artifacts(manifest_path)`: Compares current file checksums against a stored manifest.
- `write_checksum_manifest(directory, manifest_path)`: Scans a directory and writes a JSON manifest of checksums.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `sys`, `hashlib`, `json`, `pathlib`, `typing`

---

## `code/scripts/extract_features.py`

Extracts structural metrics from code artifacts using `tree-sitter` and handles fallback logic for missing semantic nodes.

**Public Functions:**
- `load_ground_truth(csv_path)`: Loads the ground truth CSV file.
- `filter_unparseable(df)`: Filters out rows where the code status is "Unparseable".
- `get_lines_of_code(code_string)`: Counts lines of code.
- `get_cyclomatic_complexity(code_string)`: Calculates cyclomatic complexity.
- `get_dependency_depth(code_string)`: Calculates the maximum dependency depth.
- `calculate_semantic_complexity_score(code_string)`: Calculates semantic complexity; returns `None` if semantic nodes are missing.
- `extract_graph_and_metrics(code_string)`: Extracts the dependency graph and all structural metrics.
- `serialize_graph(graph, task_id)`: Serializes a graph object to JSON.
- `load_graph_metrics(graphs_dir)`: Loads serialized graphs and metrics from disk.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `csv`, `json`, `sys`, `pathlib`, `typing`

---

## `code/scripts/finalize_features.py`

Serializes dependency graphs to disk and merges metrics with ground truth data.

**Public Functions:**
- `serialize_graphs_to_disk(df, graphs_dir)`: Iterates through the dataframe and saves graphs to `data/graphs/{task_id}.json`.
- `finalize_features(ground_truth_path, graphs_dir, output_path)`: Merges ground truth with extracted metrics to produce the final features CSV.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `sys`, `json`, `csv`, `pathlib`, `typing`

---

## `code/scripts/generate_features.py`

Helper script to merge graph metrics with ground truth data.

**Public Functions:**
- `load_graph_metrics(graphs_dir)`: Loads metrics from the graphs directory.
- `merge_ground_truth_with_metrics(ground_truth_df, metrics_dict)`: Merges the two datasets on `task_id`.
- `write_features_csv(df, output_path)`: Writes the final features dataframe to CSV.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `csv`, `json`, `pathlib`, `typing`, `scripts.extract_features`

---

## `code/scripts/generate_ground_truth.py`

Combines baseline execution results with ingested task data to create the final ground truth dataset.

**Public Functions:**
- `load_baseline_results(json_path)`: Loads raw baseline outcomes.
- `load_ingested_tasks(csv_path)`: Loads ingested task data.
- `process_unparseable_tasks(df)`: Flags tasks that could not be parsed.
- `generate_ground_truth(baseline_df, ingested_df)`: Merges and processes data to create the ground truth table.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `csv`, `json`, `pathlib`, `typing`, `scripts.baseline_runner`

---

## `code/scripts/generate_model_report.py`

Generates the final model report including FNR analysis and associational framing.

**Public Functions:**
- `load_threshold_sweep_safe(json_path)`: Safely loads threshold sweep data.
- `load_decision_boundary(pkl_path)`: Loads the decision boundary model.
- `generate_model_report(sweep_data, boundary_data)`: Compiles the final report JSON with FNR, correlation, and framing.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `sys`, `json`, `pickle`, `argparse`, `pathlib`

---

## `code/scripts/identify_threshold.py`

Identifies optimal decision thresholds based on sensitivity analysis.

**Public Functions:**
- `load_threshold_sweep(json_path)`: Loads threshold sweep results.
- `identify_optimal_threshold(sweep_data)`: Selects the threshold that minimizes FNR while meeting safety constraints.
- `save_decision_boundary(threshold, boundary_path)`: Saves the identified threshold to disk.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `json`, `pickle`, `sys`, `pathlib`, `typing`

---

## `code/scripts/ingest.py`

Downloads and parses datasets from HuggingFace (SWE-bench, AgentBench).

**Public Functions:**
- `load_swe_bench()`: Fetches the SWE-bench subset.
- `load_agent_bench()`: Fetches the AgentBench subset.
- `parse_swe_bench(dataset)`: Parses SWE-bench schema into the project format.
- `parse_agent_bench(dataset)`: Parses AgentBench schema into the project format.
- `merge_datasets(df1, df2)`: Merges parsed datasets.
- `write_to_csv(df, output_path)`: Writes dataframe to CSV.
- `write_to_json(df, output_path)`: Writes dataframe to JSON.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `csv`, `json`, `hashlib`, `sys`, `pathlib`

---

## `code/scripts/optimization_guide.py`

Provides utilities for optimizing pipeline stages and running parallelized operations.

**Public Functions:**
- `PerformanceMonitor`: Class for tracking memory and time usage.
- `run_stage_parallelized(func, items, n_workers)`: Runs a function in parallel across workers.
- `optimize_dataset_loading()`: Applies optimizations to dataset loading.
- `optimize_feature_extraction()`: Applies optimizations to feature extraction.
- `optimize_model_training()`: Applies optimizations to model training.
- `run_optimized_pipeline()`: Executes the full pipeline with optimizations.
- `apply_all_optimizations()`: Convenience function to enable all optimizations.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `sys`, `time`, `json`, `multiprocessing`, `pathlib`

---

## `code/scripts/profile_pipeline.py`

Profiles the pipeline to identify performance bottlenecks.

**Public Functions:**
- `get_memory_usage_mb()`: Returns current memory usage in MB.
- `run_with_profiler(func, *args, **kwargs)`: Runs a function under `cProfile`.
- `run_full_pipeline()`: Profiles the entire pipeline execution.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `sys`, `json`, `cProfile`, `pstats`, `io`

---

## `code/scripts/sensitivity_analysis.py`

Performs sensitivity analysis on model predictions across different thresholds.

**Public Functions:**
- `load_model_and_features(model_path, features_path)`: Loads the trained model and feature data.
- `calculate_fnr(y_true, y_pred)`: Calculates the False Negative Rate.
- `run_sensitivity_analysis(model, features, thresholds)`: Sweeps through thresholds and calculates FNR.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `json`, `pickle`, `numpy`, `pandas`, `pathlib`

---

## `code/scripts/train_model.py`

Trains Logistic Regression and Random Forest models on structural features.

**Public Functions:**
- `load_features(csv_path)`: Loads the features CSV.
- `prepare_train_val_split(df, test_size=0.2, seed=42)`: Splits data into train/validation sets.
- `encode_target(df, target_col)`: Encodes the target column.
- `train_logistic_regression(X_train, y_train)`: Trains a Logistic Regression model.
- `train_random_forest(X_train, y_train)`: Trains a Random Forest model.
- `evaluate_model(model, X_test, y_test)`: Evaluates model performance.
- `calculate_correlation_coefficient(features, target)`: Calculates correlation between features and target.
- `run_sensitivity_analysis(model, features, thresholds)`: Runs sensitivity analysis on the trained model.
- `run_training_pipeline(features_path, output_dir)`: Orchestrates the full training workflow.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `sys`, `json`, `pickle`, `argparse`, `numpy`

---

## `code/scripts/update_state.py`

Manages the project state file (`state/projects/...yaml`) to track task progress and artifacts.

**Public Functions:**
- `ensure_state_dirs()`: Creates necessary state directories.
- `load_state(state_path)`: Loads the current state YAML.
- `save_state(state, state_path)`: Saves the state to YAML.
- `update_task_status(task_id, status)`: Updates the status of a specific task.
- `add_artifact(task_id, artifact_path)`: Records an artifact path in the state.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `yaml`, `pathlib`, `datetime`, `typing`, `config.loader`

---

## `code/scripts/validate_features.py`

Validates the integrity and completeness of the generated features CSV.

**Public Functions:**
- `load_features_csv(csv_path)`: Loads the features CSV.
- `validate_columns_present(df, required_columns)`: Checks for the presence of required columns.
- `validate_no_missing_metrics(df)`: Ensures no missing values in metric columns.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `sys`, `csv`, `json`, `pathlib`, `typing`

---

## `code/scripts/validate_quickstart.py`

Validates the `docs/quickstart.md` file to ensure it enforces the full-environment re-execution baseline.

**Public Functions:**
- `validate_quickstart()`: Parses the quickstart guide and verifies it does not allow static-only shortcuts. Raises an error if the baseline is not enforced.

**Dependencies:** `sys`, `pathlib`

---

## `code/scripts/verify_checksums.py`

Verifies that all expected artifacts are present and have correct checksums.

**Public Functions:**
- `get_expected_artifacts()`: Returns a list of expected artifact paths.
- `verify_directory_populated(directory)`: Checks if a directory contains the expected files.
- `main()`: Entry point for the CLI script.

**Dependencies:** `os`, `sys`, `hashlib`, `json`, `pathlib`, `typing`