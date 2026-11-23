# API Reference: Research Pipeline Modules

## `code/utils.py`

Core utilities for logging, hashing, and state management.

### Functions
- `set_task_id(task_id: str)`: Sets the global task ID for logging context.
- `get_task_id() -> str`: Returns the current task ID.
- `setup_logging(task_id: str)`: Initializes logging with file and console handlers.
- `get_logger(name: str) -> logging.Logger`: Retrieves a logger instance.
- `compute_sha256(file_path: str) -> str`: Computes SHA256 hash of a file.
- `verify_checksum(file_path: str, expected_hash: str) -> bool`: Verifies file integrity.
- `ensure_directory(path: str)`: Creates a directory if it doesn't exist.

## `code/download_data.py`

Handles HumanEval acquisition and sampling.

### Functions
- `download_humaneval(output_dir: str) -> str`: Downloads HumanEval dataset.
- `verify_file_integrity(file_path: str, expected_hash: str) -> bool`: Checks dataset hash.
- `stratified_sample(dataset: List, n: int) -> List`: Performs stratified sampling.
- `main()`: Entry point for data download.

## `code/generate_code.py`

LLM inference and code generation.

### Functions
- `generate_code_for_task(task: Dict, model: Any) -> str`: Generates code for a single task.
- `generate_code_batch(tasks: List, model: Any) -> List`: Generates code for a batch.
- `log_error(message: str)`: Logs errors to `errors.log`.
- `mark_sample_missing(sample_id: str)`: Marks a sample as missing in results.
- `main()`: Entry point for code generation.

## `code/analyze_metrics.py`

Metric computation and test execution.

### Functions
- `load_test_suites()`: Loads HumanEval test suites.
- `calculate_code_metrics(code: str) -> Dict`: Computes complexity metrics.
- `execute_test_suite(code: str, tests: str) -> bool`: Runs tests and returns pass status.
- `execute_coverage_test(code: str, tests: str) -> float`: Runs coverage and returns branch coverage %.
- `aggregate_metrics_to_json(results: List)`: Saves results to `metrics.json`.
- `main()`: Entry point for analysis.

## `code/statistical_tests.py`

Hypothesis testing and power analysis.

### Functions
- `wilcoxon_signed_rank_test(sample1: List, sample2: List)`: Wilcoxon test.
- `mcnemar_test(confusion_matrix: List)`: McNemar's test.
- `fisher_exact_test(confusion_matrix: List)`: Fisher's exact test.
- `permutation_test_paired(data1: List, data2: List)`: Permutation test.
- `a_priori_power_analysis(effect_size: float, alpha: float)`: A priori power analysis.
- `post_hoc_power_analysis(effect_size: float, n: int, alpha: float)`: Post-hoc power analysis.
- `spearman_correlation(x: List, y: List)`: Spearman correlation.
- `point_biserial_correlation(x: List, y: List)`: Point-biserial correlation for binary y.
- `run_statistical_analysis(metrics: Dict)`: Runs all tests.
- `main()`: Entry point for statistical analysis.

## `code/report_generator.py`

Visualization and report generation.

### Functions
- `plot_histogram(data: List, title: str, path: str)`: Generates histogram.
- `plot_boxplot(data: List, title: str, path: str)`: Generates boxplot.
- `generate_markdown_report(stats: Dict, figures: List) -> str`: Renders Markdown report.
- `format_sensitivity_comparison(metrics: Dict)`: Formats sensitivity data.
- `main()`: Entry point for report generation.

## `code/validate_citations.py`

Citation validation agent.

### Functions
- `validate_citations(text: str) -> List`: Validates citations in text.
- `CitationValidator`: Class for managing citation logic.

## `code/validate_quickstart.py`

Pipeline validation.

### Functions
- `check_directory(path: str)`: Checks if directory exists.
- `check_file(path: str)`: Checks if file exists.
- `verify_json_structure(path: str, schema: Dict)`: Verifies JSON structure.
- `run_pipeline_stage(stage_name: str)`: Executes a pipeline stage.
- `validate_artifacts()`: Validates all required artifacts.
- `main()`: Entry point for validation.
