# API Reference

This document details the public interfaces of the core modules in the llmXive research pipeline.

## Data Pipeline Modules

### `code/data/download.py`
Handles downloading the CodeSearchNet dataset.

- `download_codesearchnet(output_dir: Path) -> Path`: Downloads the dataset and returns the path to the parquet file.
- `main()`: CLI entry point.

### `code/data/extract.py`
Parses raw parquet files to extract top-level function definitions.

- `parse_python_code(code: str) -> Optional[ast.Module]`: Safely parses code string.
- `extract_top_level_functions(module: ast.Module) -> List[str]`: Returns source code of top-level functions.
- `process_parquet_file(file_path: Path) -> Generator[Dict, None, None]`: Yields extracted functions.
- `run_validation()`: CLI entry point.

### `code/data/validate.py`
Validates syntax and import constraints.

- `check_syntax(code: str) -> bool`: Returns True if code is syntactically valid.
- `mock_stdlib_imports(code: str) -> str`: Replaces stdlib imports with mocks.
- `count_external_imports(code: str) -> int`: Counts non-stdlib imports.
- `validate_function(func: Dict) -> Tuple[bool, Optional[str]]`: Returns (is_valid, reason).

### `code/data/sample.py`
Implements stratified sampling logic.

- `count_lines(code: str) -> int`: Counts lines of code.
- `assign_stratum(loc: int) -> str`: Assigns stratum based on LOC.
- `stratified_sample(functions: List[Dict], strata_weights: Dict[str, int]) -> List[Dict]`: Returns sampled list.

## Benchmark Modules

### `code/benchmark/runner.py`
Executes code benchmarks with resource limits.

- `BenchmarkResult`: Dataclass containing `execution_time`, `memory_peak`, `iterations`.
- `run_single_benchmark(code: str, iterations: int) -> BenchmarkResult`: Runs code N times.
- `benchmark_function_pair(original: str, simplified: str, iterations: int) -> Dict`: Compares two functions.
- `run_benchmark_pipeline(pairs_path: Path, output_path: Path)`: Orchestrates full benchmark.

### `code/benchmark/stats.py`
Statistical analysis utilities.

- `check_normality(data: List[float]) -> Tuple[bool, float]`: Shapiro-Wilk test.
- `perform_statistical_test(group1: List[float], group2: List[float]) -> Dict`: Returns p-value and test type.
- `analyze_benchmark_results(results: List[Dict]) -> Dict`: Aggregates means and runs tests.

### `code/benchmark/equivalence.py`
Functional equivalence checking.

- `check_function_equivalence(orig_code: str, simp_code: str, inputs: List[Any]) -> Tuple[bool, DriftLog]`: Verifies outputs match.
- `run_equivalence_check_batch(pairs: List[Dict]) -> List[DriftLog]`: Batch processing.

## Utility Modules

### `code/utils/sandbox.py`
Secure execution environment.

- `run_in_sandbox(code: str, timeout: int = 5, memory_mb: int = 500) -> ExecutionResult`: Executes code with limits.
- `SandboxTimeoutError`: Raised when execution exceeds time limit.
- `SandboxMemoryError`: Raised when execution exceeds memory limit.

### `code/utils/logger.py`
Structured logging.

- `get_logger(name: str) -> logging.Logger`: Returns configured JSON logger.
- `log_stage_start(stage: str)`: Logs stage start.
- `log_stage_complete(stage: str, duration: float)`: Logs stage completion.
- `log_stage_error(stage: str, error: str)`: Logs error details.

### `code/checksum.py`
Artifact versioning.

- `compute_sha256(file_path: Path) -> str`: Computes file hash.
- `save_checksum_manifest(manifest_path: Path, files: List[Path])`: Saves hash manifest.
- `verify_checksums(manifest_path: Path) -> bool`: Verifies current files against manifest.

## Main Orchestrators

- `code/main_data.py`: Runs full data pipeline.
- `code/main_simplify.py`: Runs LLM simplification.
- `code/main_filter_drift.py`: Filters invalid pairs.
- `code/main_benchmark.py`: Runs benchmarking.
- `code/main_statistical_summary.py`: Generates JSON summary.
- `code/main_summary.py`: Generates CSV report.