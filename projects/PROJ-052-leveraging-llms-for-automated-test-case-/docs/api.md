# API Documentation

This document provides the API reference for the `code/` modules in the llmXive project.
It is generated based on the docstrings and public interfaces defined in the source files.

## Module: `analyzer`

Statistical analysis utilities for coverage metrics.

### Functions

#### `check_normality(data: List[float]) -> Tuple[float, float]`
Perform the Shapiro-Wilk test for normality on the provided data.
- **Parameters:**
 - `data`: A list of float values representing coverage differences.
- **Returns:**
 - A tuple `(statistic, p_value)` from the Shapiro-Wilk test.

#### `run_statistical_test(group1: List[float], group2: List[float]) -> Dict[str, Any]`
Select and run the appropriate statistical test based on normality.
- **Logic:**
 - If normality holds (p > 0.10), runs a paired t-test.
 - Otherwise, runs a Wilcoxon signed-rank test.
- **Returns:**
 - A dictionary containing `test_type`, `statistic`, `p_value`, and `conclusion`.

#### `calculate_effect_size(group1: List[float], group2: List[float]) -> Dict[str, float]`
Calculate effect size metrics (Cohen's d or Rank-biserial correlation).
- **Returns:**
 - A dictionary with `cohens_d` and `rank_biserial` values.

#### `interpret_cohen_d(d: float) -> str`
Return a qualitative interpretation of Cohen's d value.

#### `interpret_rank_biserial(r: float) -> str`
Return a qualitative interpretation of the Rank-biserial correlation.

#### `run_power_analysis(n: int, effect_size: float, alpha: float = 0.05) -> Dict[str, float]`
Perform post-hoc power analysis.
- **Returns:**
 - A dictionary with `achieved_power` and `required_n`.

#### `calculate_confidence_intervals(data: List[float], confidence: float = 0.95) -> Dict[str, float]`
Calculate confidence intervals for the mean of the data.
- **Returns:**
 - A dictionary with `mean`, `ci_low`, and `ci_high`.

#### `main()`
Entry point for running the analysis module directly.

---

## Module: `config`

Configuration management and environment variable handling.

### Functions

#### `init_runtime_tracker() -> None`
Initialize the runtime tracking timer.

#### `check_runtime_limit() -> None`
Raises `RuntimeLimitExceeded` if the elapsed time exceeds the configured limit.

#### `get_sample_limit() -> int`
Retrieve the configured sample limit from environment variables.

#### `get_timeout_compile() -> int`
Retrieve the compilation timeout threshold (seconds).

#### `get_timeout_exec() -> int`
Retrieve the execution timeout threshold (seconds).

#### `get_timeout_inference() -> int`
Retrieve the inference timeout threshold (seconds).

#### `get_runtime_limit() -> int`
Retrieve the maximum allowed runtime in seconds.

#### `get_model_path() -> str`
Retrieve the path to the quantized model file.

#### `get_data_dir() -> Path`
Retrieve the project data directory path.

#### `get_output_dir() -> Path`
Retrieve the project output directory path.

#### `get_logs_dir() -> Path`
Retrieve the project logs directory path.

#### `ensure_directories() -> None`
Ensure all required project directories exist.

---

## Module: `data_loader`

Data sourcing, streaming, and integrity management.

### Exceptions

#### `DataFetchError`
Raised when the real data source fails to fetch.

#### `MemoryExceededError`
Raised when RAM usage exceeds the 7GB threshold.

### Functions

#### `load_state(path: str) -> Dict[str, Any]`
Load the project state from a YAML file.

#### `save_state(state: Dict[str, Any], path: str) -> None`
Save the project state to a YAML file.

#### `record_checksum(key: str, value: str) -> None`
Record a checksum in the project state.

#### `compute_sha256(file_path: str) -> str`
Compute the SHA-256 hash of a file.

#### `fetch_defects4j_data() -> None`
Fetch the Defects4J dataset using streaming to handle large files.

#### `load_defects4j_data() -> Any`
Load the Defects4J dataset into memory (chunked processing).

#### `verify_data_integrity() -> bool`
Verify the integrity of the loaded data against recorded checksums.

#### `extract_changed_lines() -> Dict[str, Dict[str, List[int]]]`
Parse commit diffs and extract changed line numbers.
- **Returns:**
 - A dictionary mapping `project_id` to `bug_id` to a list of changed lines.

#### `extract_bug_fix_description(bug_metadata: Dict[str, Any]) -> str`
Format bug metadata into a prompt string for the LLM.

#### `log_fallback_prompt_usage(prompt_length: int, status: str) -> None`
Log warnings for ambiguous prompts to `data/metrics.json`.

#### `filter_pairable_samples() -> Dict[str, Any]`
Identify samples with valid manual baselines and log exclusion rates.

#### `ensure_data_loaded_and_integrity_recorded() -> None`
Main entry point to ensure data is loaded and checksums are recorded.

#### `main()`
Entry point for running the data loader module directly.

---

## Module: `llm_generator`

LLM model loading and test code generation.

### Functions

#### `load_model(model_path: str) -> Any`
Load the quantized model (Q4_K_M) using `llama-cpp-python`.
- **Constraint:** Monitors RAM usage; raises `MemoryExceededError` if > 7GB.

#### `generate_from_prompt(prompt: str, model: Any, temperature: float = 0.0, seed: int = 42) -> str`
Generate text from the model given a prompt.

#### `generate_test_code(bug_description: str, model: Any) -> str`
Generate JUnit test code for a specific bug description.

#### `validate_syntax_java(code: str, temp_dir: str) -> bool`
Validate generated Java code using `javac`.
- **Returns:**
 - `True` if syntax is valid, `False` otherwise.

#### `main()`
Entry point for running the LLM generator module directly.

---

## Module: `main`

Pipeline orchestration and execution control.

### Exceptions

#### `RuntimeLimitExceeded`
Raised when the runtime limit is exceeded.

#### `SampleLimitExceeded`
Raised when the sample limit is exceeded.

### Functions

#### `check_sample_limit(count: int) -> None`
Raises `SampleLimitExceeded` if the processed count exceeds the limit.

#### `run_pipeline() -> None`
Execute the full pipeline: data loading, generation, execution, and analysis.

#### `main()`
CLI entry point for the project.

---

## Module: `report_generator`

Report generation and formatting.

### Functions

#### `generate_final_report(analysis_results: Dict[str, Any]) -> None`
Generate the final markdown report and JSON analysis results.
- **Deliverables:**
 - `data/final_report.md`
 - `data/analysis_results.json`

#### `generate_markdown_report(data: Dict[str, Any]) -> str`
Format analysis results into a Markdown string.

---

## Module: `test_executor`

Test compilation, execution, and coverage measurement.

### Exceptions

#### `CompilationFailedError`
Raised when Java compilation fails after retries.

#### `ExecutionError`
Raised when test execution fails.

### Classes

#### `ExecutionResult`
Dataclass holding the result of a test execution.

### Functions

#### `retry_compile(java_file: str, max_attempts: int = 3) -> bool`
Attempt to compile a Java file with retry logic.

#### `compile_test(java_file: str) -> bool`
Compile a single test file.

#### `extract_compilation_error(log_output: str) -> List[str]`
Extract specific compilation error strings using regex.

#### `update_csv_for_failed_test(record: Dict[str, Any], errors: List[str]) -> Dict[str, Any]`
Update a coverage record for a failed test.

#### `parse_jacoco_xml(xml_path: str) -> Dict[str, Any]`
Parse JaCoCo XML output to extract line-level coverage.

#### `run_with_jacoco(test_file: str, target_class: str) -> ExecutionResult`
Instrument classes and run tests with JaCoCo.

#### `calculate_coverage_ratio(covered_lines: List[int], total_lines: List[int]) -> float`
Calculate the coverage percentage on specific changed lines.

#### `generate_coverage_csv(records: List[Dict[str, Any]]) -> None`
Write aggregated coverage records to `data/coverage_metrics.csv`.

#### `main()`
Entry point for running the test executor module directly.

---

## Module: `validate_schemas`

Artifact validation against JSON schemas.

### Functions

#### `load_schema(schema_path: str) -> Dict[str, Any]`
Load a JSON schema from a file.

#### `validate_artifact(artifact_path: str, schema_path: str) -> bool`
Validate a single artifact against its schema.

#### `validate_all_artifacts() -> None`
Validate all output artifacts in `data/` against `contracts/`.

#### `main()`
Entry point for running the schema validator module directly.

---

## Module: `run_extract_bug_description`

Utility to extract bug descriptions.

### Functions

#### `main()`
Entry point for the script.

---

## Module: `run_extract_changed_lines`

Utility to extract changed lines.

### Functions

#### `main()`
Entry point for the script.