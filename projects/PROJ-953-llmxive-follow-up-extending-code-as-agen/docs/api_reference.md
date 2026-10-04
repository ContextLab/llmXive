# API Reference: Code Scripts

This document details the public functions available in the `code/scripts/` module.

## `code/scripts/ingest.py`

Handles downloading and parsing of SWE-bench and AgentBench datasets.

- `load_swe_bench()`: Fetches the SWE-bench subset from HuggingFace.
- `load_agent_bench()`: Fetches the AgentBench subset from HuggingFace.
- `parse_swe_bench(raw_data)`: Parses raw SWE-bench data into a standardized dictionary.
- `parse_agent_bench(raw_data)`: Parses raw AgentBench data into a standardized dictionary.
- `merge_datasets(df_swe, df_agent)`: Combines the two DataFrames.
- `write_to_csv(df, path)`: Writes the merged DataFrame to a CSV file.
- `write_to_json(data, path)`: Writes data to a JSON file.
- `main()`: Entry point for the script.

## `code/scripts/extract_features.py`

Calculates structural metrics and builds dependency graphs.

- `load_ground_truth(csv_path)`: Loads the ground truth CSV.
- `filter_unparseable(df)`: Filters out rows where parsing failed.
- `get_lines_of_code(code)`: Returns the line count.
- `get_cyclomatic_complexity(code)`: Calculates cyclomatic complexity using `radon`.
- `get_dependency_depth(graph)`: Calculates the depth of the dependency graph.
- `calculate_semantic_complexity_score(ast_tree)`: Computes a score based on AST node distribution.
- `extract_graph_and_metrics(code)`: Returns a graph object and a dictionary of metrics.
- `serialize_graph(graph, task_id, output_dir)`: Saves the graph to `data/graphs/{task_id}.json`.
- `load_graph_metrics(graph_dir)`: Loads all graph metrics from the directory.
- `main()`: Entry point for the script.

## `code/scripts/train_model.py`

Trains predictive models and performs sensitivity analysis.

- `load_features(csv_path)`: Loads the features CSV.
- `prepare_train_val_split(df, seed)`: Splits data into train/validation sets.
- `encode_target(series)`: Encodes target labels (e.g., "Pass" vs "Fail") to integers.
- `train_logistic_regression(X_train, y_train)`: Trains a Logistic Regression model.
- `train_random_forest(X_train, y_train)`: Trains a Random Forest model.
- `evaluate_model(model, X_test, y_test)`: Returns accuracy and other metrics.
- `calculate_correlation_coefficient(features, target)`: Computes Pearson correlation.
- `run_sensitivity_analysis(model, X_val, y_val)`: Sweeps thresholds to find optimal FNR.
- `run_training_pipeline()`: Orchestrates the full training flow.
- `main()`: Entry point for the script.

## `code/scripts/baseline_runner.py`

Executes tasks in a sandboxed environment.

- `ExecutionResult`: Dataclass representing the outcome of a task execution.
- `check_gpu_usage()`: Raises an exception if GPU/CUDA is detected.
- `run_with_timeout(func, timeout)`: Runs a function with a timeout.
- `setup_venv()`: Creates a temporary virtual environment.
- `install_dependencies(venv_path, requirements)`: Installs dependencies.
- `run_baseline_task(task)`: Executes a single task and returns an `ExecutionResult`.
- `main()`: Entry point for the script.

## `code/scripts/generate_features.py`

Merges ground truth with calculated metrics.

- `load_graph_metrics(graph_dir)`: Loads metrics from JSON files.
- `merge_ground_truth_with_metrics(gt_df, metrics)`: Joins dataframes.
- `write_features_csv(df, path)`: Writes the final features CSV.
- `main()`: Entry point for the script.

## `code/scripts/update_state.py`

Manages project state files (Constitution Principle V).

- `ensure_state_dirs()`: Creates state directories if missing.
- `load_state(path)`: Loads the state YAML.
- `save_state(state, path)`: Saves the state YAML.
- `update_task_status(task_id, status)`: Updates the status of a specific task.
- `add_artifact(task_id, artifact_path)`: Records an artifact path in the state.
- `main()`: Entry point for the script.

## `code/scripts/checksum_artifacts.py`

Verifies artifact integrity.

- `calculate_sha256(file_path)`: Computes SHA256 hash.
- `verify_artifacts(manifest_path)`: Verifies files against a manifest.
- `write_checksum_manifest(files, output_path)`: Creates a checksum manifest.
- `main()`: Entry point for the script.

## `code/scripts/validate_features.py`

Validates the features dataset.

- `load_features_csv(path)`: Loads the CSV.
- `validate_columns_present(df, required_cols)`: Checks for required columns.
- `validate_no_missing_metrics(df)`: Ensures no NaN values in metric columns.
- `main()`: Entry point for the script.
