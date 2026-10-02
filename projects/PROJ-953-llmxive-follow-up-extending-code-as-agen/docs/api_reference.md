# API Reference

This document lists the public functions and classes available in the `code/scripts/` modules.

## `code/config/loader.py`

Configuration management module.

- `Config`: Dataclass holding configuration parameters.
- `get_dataset_path(name: str) -> Path`: Returns the path to a dataset.
- `validate_config(config: Config) -> bool`: Validates configuration integrity.
- `get_config() -> Config`: Retrieves the global configuration.
- `get_global_config() -> Config`: Alias for `get_config()`.

## `code/scripts/ingest.py`

Dataset ingestion module.

- `load_swe_bench() -> List[Dict]`: Loads SWE-bench data.
- `load_agent_bench() -> List[Dict]`: Loads AgentBench data.
- `parse_swe_bench(raw_data: List[Dict]) -> List[Dict]`: Parses SWE-bench entries.
- `parse_agent_bench(raw_data: List[Dict]) -> List[Dict]`: Parses AgentBench entries.
- `merge_datasets(df_swe: pd.DataFrame, df_agent: pd.DataFrame) -> pd.DataFrame`: Merges datasets.
- `write_to_csv(df: pd.DataFrame, path: Path) -> None`: Writes dataframe to CSV.
- `write_to_json(data: Any, path: Path) -> None`: Writes data to JSON.
- `main() -> None`: Entry point for the script.

## `code/scripts/baseline_runner.py`

Dynamic execution baseline module.

- `ExecutionResult`: NamedTuple/Class holding execution status (Pass/Fail/Timeout).
- `run_with_timeout(func, timeout: int) -> ExecutionResult`: Runs a function with a timeout.
- `run_baseline_task(task: Dict, env: Path) -> ExecutionResult`: Executes a single task.
- `main() -> None`: Entry point for the script.

## `code/scripts/extract_features.py`

Feature extraction module.

- `load_ground_truth(path: Path) -> pd.DataFrame`: Loads ground truth CSV.
- `filter_unparseable(df: pd.DataFrame) -> pd.DataFrame`: Filters out unparseable tasks.
- `get_lines_of_code(code: str) -> int`: Counts lines of code.
- `get_cyclomatic_complexity(code: str) -> int`: Calculates cyclomatic complexity.
- `get_dependency_depth(code: str) -> int`: Calculates dependency depth.
- `calculate_semantic_complexity_score(code: str) -> float`: Calculates semantic complexity.
- `extract_graph_and_metrics(code: str) -> Tuple[Dict, Dict]`: Extracts graph and metrics.
- `serialize_graph(graph: Dict, path: Path) -> None`: Saves graph to JSON.
- `load_graph_metrics(path: Path) -> List[Dict]`: Loads metrics from graph files.
- `main() -> None`: Entry point for the script.

## `code/scripts/generate_features.py`

Feature generation module.

- `load_graph_metrics(path: Path) -> List[Dict]`: Loads graph metrics.
- `merge_ground_truth_with_metrics(gt: pd.DataFrame, metrics: List[Dict]) -> pd.DataFrame`: Merges data.
- `write_features_csv(df: pd.DataFrame, path: Path) -> None`: Writes features to CSV.
- `main() -> None`: Entry point for the script.

## `code/scripts/train_model.py`

Model training module.

- `load_features(path: Path) -> pd.DataFrame`: Loads features CSV.
- `prepare_train_val_split(df: pd.DataFrame, seed: int) -> Tuple[pd.DataFrame, pd.DataFrame]`: Splits data.
- `encode_target(series: pd.Series) -> np.ndarray`: Encodes target variable.
- `train_logistic_regression(X, y) -> Model`: Trains LR model.
- `train_random_forest(X, y) -> Model`: Trains RF model.
- `evaluate_model(model, X, y) -> Dict`: Evaluates model performance.
- `calculate_correlation_coefficient(X, y) -> float`: Calculates correlation.
- `run_training_pipeline() -> None`: Entry point for the script.

## `code/scripts/sensitivity_analysis.py`

Sensitivity analysis module.

- `load_model_and_features() -> Tuple[Model, pd.DataFrame]`: Loads model and data.
- `calculate_fnr(model, X, y, threshold: float) -> float`: Calculates FNR at a threshold.
- `run_sensitivity_analysis() -> None`: Runs full sweep.
- `main() -> None`: Entry point for the script.

## `code/scripts/identify_threshold.py`

Threshold identification module.

- `load_threshold_sweep(path: Path) -> Dict`: Loads sweep results.
- `identify_optimal_threshold(sweep: Dict) -> float`: Finds optimal threshold.
- `save_decision_boundary(threshold: float, weights: Dict, path: Path) -> None`: Saves decision boundary.
- `main() -> None`: Entry point for the script.

## `code/scripts/generate_model_report.py`

Report generation module.

- `load_threshold_sweep_safe(path: Path) -> Dict`: Loads sweep with safety checks.
- `load_decision_boundary(path: Path) -> Dict`: Loads decision boundary.
- `generate_model_report(sweep: Dict, boundary: Dict) -> Dict`: Generates report.
- `main() -> None`: Entry point for the script.

## `code/scripts/update_state.py`

State management module.

- `ensure_state_dirs() -> None`: Creates state directories.
- `load_state(path: Path) -> Dict`: Loads state file.
- `save_state(state: Dict, path: Path) -> None`: Saves state file.
- `update_task_status(task_id: str, status: str) -> None`: Updates task status.
- `add_artifact(task_id: str, artifact: Dict) -> None`: Adds artifact to state.
- `main() -> None`: Entry point for the script.

## `code/scripts/validate_features.py`

Feature validation module.

- `load_features_csv(path: Path) -> pd.DataFrame`: Loads features.
- `validate_columns_present(df: pd.DataFrame, required: List[str]) -> bool`: Checks columns.
- `validate_no_missing_metrics(df: pd.DataFrame) -> bool`: Checks for missing values.
- `main() -> None`: Entry point for the script.

## `code/scripts/calculate_correlations.py`

Correlation calculation module.

- `encode_target(series: pd.Series) -> np.ndarray`: Encodes target.
- `calculate_correlations(df: pd.DataFrame) -> Dict`: Calculates correlations.
- `main() -> None`: Entry point for the script.

## `code/scripts/optimization_guide.py`

Optimization module.

- `PerformanceMonitor`: Class for monitoring performance.
- `run_stage_parallelized(stage_func, tasks: List) -> List`: Runs stage in parallel.
- `optimize_dataset_loading() -> None`: Optimization routine.
- `optimize_feature_extraction() -> None`: Optimization routine.
- `optimize_model_training() -> None`: Optimization routine.
- `run_optimized_pipeline() -> None`: Runs full optimized pipeline.
- `apply_all_optimizations() -> None`: Applies all optimizations.
- `main() -> None`: Entry point for the script.
