# llmXive API Reference

This document provides the complete API reference for the `code/` modules in the llmXive project.
All modules are designed to be imported relative to the `code/` directory.

## Table of Contents

1. [Data Acquisition & Processing](#data-acquisition--processing)
 - [fetch_github](#fetch_github)
 - [classify_prs](#classify_prs)
 - [extract_metrics](#extract_metrics)
 - [save_labeled_dataset](#save_labeled_dataset)
 - [save_metrics](#save_metrics)
 - [optimize_metrics_extraction](#optimize_metrics_extraction)
2. [Analysis](#analysis)
 - [complexity](#complexity)
 - [statistical_tests](#statistical_tests)
 - [visualizations](#visualizations)
 - [sensitivity_analysis](#sensitivity_analysis)
 - [generate_results_report](#generate_results_report)
 - [generate_final_report](#generate_final_report)
 - [generate_final_report_pdf](#generate_final_report_pdf)
 - [optimize_complexity_processing](#optimize_complexity_processing)
 - [save_complexity_scores](#save_complexity_scores)
3. [Audit & Validation](#audit--validation)
 - [manual_validation](#manual_validation)
4. [Utilities](#utilities)
 - [config](#config)
 - [logging](#logging)
 - [seeds](#seeds)
 - [checksum](#checksum)
 - [batch_processor](#batch_processor)
5. [Setup](#setup)
 - [setup_directories](#setup_directories)

---

## Data Acquisition & Processing

### fetch_github
**Module:** `code/data/fetch_github.py`

Handles fetching Pull Requests from GitHub with rate limiting, backoff, and watchdog mechanisms.

**Public API:**
- `watchdog_handler(signum, frame)`: Signal handler for watchdog timeout.
- `setup_watchdog(timeout_seconds: int)`: Configures the watchdog timer.
- `calculate_checksum(data: bytes) -> str`: Generates SHA-256 checksum for raw payloads.
- `fetch_prs_from_repo(repo: str, limit: int) -> List[Dict]`: Fetches PRs from a single repo.
- `save_prs_to_raw(prs: List[Dict], output_dir: str)`: Saves raw JSON with checksums.
- `run_batch_fetch()`: Orchestrates the batch fetching process.
- `main()`: CLI entry point.

**Example Usage:**
```python
from data.fetch_github import run_batch_fetch

if __name__ == "__main__":
 run_batch_fetch()
```

### classify_prs
**Module:** `code/data/classify_prs.py`

Classifies PRs as `llm` or `human` based on signatures and secondary detectors (entropy/n-grams).

**Public API:**
- `is_llm_bot(author: str)`: Checks if author is a known LLM bot.
- `is_human_bot(author: str)`: Checks if author is a known infrastructure bot (e.g., dependabot).
- `has_llm_signature(message: str)`: Detects LLM signatures in commit messages.
- `calculate_confidence_score(signature_match: bool, bot_type: str) -> float`: Normalized confidence.
- `calculate_code_entropy(diff_text: str) -> float`: Computes Shannon entropy of the diff.
- `calculate_ngram_anomaly_score(diff_text: str) -> float`: Detects synthetic n-gram patterns.
- `compute_secondary_detector_score(entropy: float, anomaly: float) -> float`: Aggregates secondary scores.
- `load_prs_from_raw(input_dir: str) -> List[Dict]`: Loads raw PR data.
- `extract_diff_text(pr: Dict) -> str`: Extracts diff content from PR payload.
- `classify_prs(prs: List[Dict]) -> List[Dict]`: Applies classification logic to a list of PRs.
- `save_classified_prs(classified_prs: List[Dict], output_path: str)`: Saves classification results.
- `run_classification()`: Main pipeline runner.
- `main()`: CLI entry point.

**Example Usage:**
```python
from data.classify_prs import run_classification

if __name__ == "__main__":
 run_classification()
```

### extract_metrics
**Module:** `code/data/extract_metrics.py`

Extracts review metrics (comments, time-to-merge, cycles) and joins with complexity scores.

**Public API:**
- `setup_logging_and_config()`: Initializes logger and config.
- `load_prs_labeled(input_path: str) -> List[Dict]`: Loads labeled PRs.
- `load_complexity_scores(input_path: str) -> List[Dict]`: Loads complexity scores.
- `parse_timestamp(ts_str: str) -> datetime`: Parses ISO timestamps.
- `calculate_time_to_merge_minutes(pr: Dict) -> float`: Calculates duration.
- `calculate_review_cycles(pr: Dict) -> int`: Counts review cycles.
- `extract_comment_count(pr: Dict) -> int`: Counts comments.
- `extract_pr_metrics(pr: Dict) -> Dict`: Extracts all metrics for a single PR.
- `join_and_save_metrics(labeled_prs: List[Dict], complexity_scores: List[Dict], output_path: str)`: Joins and saves.
- `run_extraction()`: Main pipeline runner.
- `main()`: CLI entry point.

**Example Usage:**
```python
from data.extract_metrics import run_extraction

if __name__ == "__main__":
 run_extraction()
```

### save_labeled_dataset
**Module:** `code/data/save_labeled_dataset.py`

Consolidates classified PR data into the final labeled dataset CSV.

**Public API:**
- `setup_logging_and_config()`: Initializes logger and config.
- `load_classified_prs(input_path: str) -> List[Dict]`: Loads classified data.
- `save_labeled_dataset(classified_prs: List[Dict], output_path: str)`: Saves to CSV.
- `run_save_labeled_dataset()`: Main pipeline runner.
- `main()`: CLI entry point.

**Example Usage:**
```python
from data.save_labeled_dataset import run_save_labeled_dataset

if __name__ == "__main__":
 run_save_labeled_dataset()
```

### save_metrics
**Module:** `code/data/save_metrics.py`

Utility to save extracted metrics to CSV.

**Public API:**
- `setup_logging_and_config()`: Initializes logger and config.
- `load_metrics_from_json(input_path: str) -> List[Dict]`: Loads metrics JSON.
- `save_metrics_to_csv(metrics: List[Dict], output_path: str)`: Saves to CSV.
- `run_save_metrics()`: Main pipeline runner.
- `main()`: CLI entry point.

**Example Usage:**
```python
from data.save_metrics import run_save_metrics

if __name__ == "__main__":
 run_save_metrics()
```

### optimize_metrics_extraction
**Module:** `code/data/optimize_metrics_extraction.py`

Optimized batch processing for metrics extraction.

**Public API:**
- `process_metrics_batch(batch: List[Dict]) -> List[Dict]`: Processes a batch of PRs.
- `run_optimized_metrics_extraction()`: Runs the optimized pipeline.
- `main()`: CLI entry point.

**Example Usage:**
```python
from data.optimize_metrics_extraction import run_optimized_metrics_extraction

if __name__ == "__main__":
 run_optimized_metrics_extraction()
```

---

## Analysis

### complexity
**Module:** `code/analysis/complexity.py`

Computes Cyclomatic Complexity and Lines of Code (LOC) for PR diffs with memory safeguards.

**Public API:**
- `get_memory_usage_mb() -> float`: Returns current memory usage.
- `check_memory_and_fallback(threshold_mb: int = 6000) -> bool`: Checks memory and triggers fallback if needed.
- `calculate_loc(code: str) -> int`: Counts lines of code.
- `calculate_cyclomatic_complexity(code: str) -> int`: Calculates cyclomatic complexity.
- `analyze_diff_complexity(diff_text: str) -> Dict`: Analyzes a single diff.
- `compute_complexity_for_prs(prs: List[Dict]) -> List[Dict]`: Processes a list of PRs.
- `main()`: CLI entry point.

**Example Usage:**
```python
from analysis.complexity import compute_complexity_for_prs

# prs = [...]
# results = compute_complexity_for_prs(prs)
```

### statistical_tests
**Module:** `code/analysis/statistical_tests.py`

Performs Mann-Whitney U (primary) and t-tests (sensitivity) for group comparisons.

**Public API:**
- `load_metrics_data(input_path: str) -> List[Dict]`: Loads metrics data.
- `group_by_source_type(metrics: List[Dict]) -> Dict[str, List]`: Groups by `source_type`.
- `calculate_cohens_d(group1: List[float], group2: List[float]) -> float`: Computes effect size.
- `verify_alpha_assumption(alpha: float = 0.05)`: Validates alpha assumption.
- `perform_independent_t_test(group1: List[float], group2: List[float]) -> Dict`: Runs t-test.
- `run_analysis_for_metric(group1: List[float], group2: List[float], metric_name: str) -> Dict`: Runs full analysis for a metric.
- `run_statistical_tests(metrics: List[Dict]) -> Dict`: Orchestrates all tests.
- `main()`: CLI entry point.

**Example Usage:**
```python
from analysis.statistical_tests import run_statistical_tests

# metrics = [...]
# results = run_statistical_tests(metrics)
```

### visualizations
**Module:** `code/analysis/visualizations.py`

Generates boxplots, histograms, and correlation plots.

**Public API:**
- `load_metrics_for_viz(input_path: str) -> List[Dict]`: Loads metrics.
- `generate_boxplots(data: List[Dict], output_path: str)`: Creates boxplots PDF.
- `generate_histograms(data: List[Dict], output_path: str)`: Creates histograms PDF.
- `generate_correlation_plot(data: List[Dict], output_path: str)`: Creates correlation plot.
- `run_visualization_pipeline()`: Runs full viz pipeline.
- `main()`: CLI entry point.

**Example Usage:**
```python
from analysis.visualizations import run_visualization_pipeline

if __name__ == "__main__":
 run_visualization_pipeline()
```

### sensitivity_analysis
**Module:** `code/analysis/sensitivity_analysis.py`

Re-runs statistical tests on the secondary detector cohort.

**Public API:**
- `load_metrics_with_detector_scores(input_path: str) -> List[Dict]`: Loads data with detector scores.
- `filter_by_detector_cohort(data: List[Dict], threshold: float) -> List[Dict]`: Filters high-confidence cohort.
- `run_sensitivity_tests(filtered_data: List[Dict]) -> Dict`: Runs tests on filtered data.
- `save_sensitivity_results(results: Dict, output_path: str)`: Saves results.
- `run_sensitivity_analysis()`: Main pipeline runner.
- `main()`: CLI entry point.

**Example Usage:**
```python
from analysis.sensitivity_analysis import run_sensitivity_analysis

if __name__ == "__main__":
 run_sensitivity_analysis()
```

### generate_results_report
**Module:** `code/analysis/generate_results_report.py`

Aggregates statistical findings into a JSON report.

**Public API:**
- `load_json_file(path: str) -> Dict`: Loads JSON.
- `aggregate_results(stats_results: Dict) -> Dict`: Aggregates results.
- `generate_results_report()`: Generates the final report JSON.
- `main()`: CLI entry point.

**Example Usage:**
```python
from analysis.generate_results_report import generate_results_report

if __name__ == "__main__":
 generate_results_report()
```

### generate_final_report
**Module:** `code/analysis/generate_final_report.py`

Compiles text-based research summary, checking gate status.

**Public API:**
- `setup_logging_and_config()`: Initializes logger and config.
- `load_json_file(path: str) -> Dict`: Loads JSON.
- `load_gate_status(path: str) -> Dict`: Loads gate status.
- `load_results(path: str) -> Dict`: Loads results.
- `load_visualization_summary(path: str) -> Dict`: Loads viz summary.
- `compile_limitations() -> List[str]`: Compiles limitations list.
- `generate_report_content(results: Dict, limitations: List[str]) -> str`: Generates report text.
- `save_report(content: str, output_path: str)`: Saves report.
- `generate_final_report()`: Main pipeline runner.
- `main()`: CLI entry point.

**Example Usage:**
```python
from analysis.generate_final_report import generate_final_report

if __name__ == "__main__":
 generate_final_report()
```

### generate_final_report_pdf
**Module:** `code/analysis/generate_final_report_pdf.py`

Generates the final research report as a PDF with plots.

**Public API:**
- `setup_logging_and_config()`: Initializes logger and config.
- `load_json_file(path: str) -> Dict`: Loads JSON.
- `load_csv_file(path: str) -> List[Dict]`: Loads CSV.
- `load_metrics_data(path: str) -> List[Dict]`: Loads metrics.
- `load_results(path: str) -> Dict`: Loads results.
- `load_gate_status(path: str) -> Dict`: Loads gate status.
- `calculate_correlation_coefficients(data: List[Dict]) -> Dict`: Calculates correlations.
- `group_data_by_source(data: List[Dict]) -> Dict`: Groups data.
- `create_summary_panel()`: Creates summary section.
- `create_methodology_section()`: Creates methodology section.
- `create_results_section(results: Dict)`: Creates results section.
- `create_discussion_section()`: Creates discussion section.
- `create_limitations_section()`: Creates limitations section.
- `create_plots_section()`: Creates plots section.
- `generate_final_report_pdf()`: Main pipeline runner.
- `main()`: CLI entry point.

**Example Usage:**
```python
from analysis.generate_final_report_pdf import generate_final_report_pdf

if __name__ == "__main__":
 generate_final_report_pdf()
```

### optimize_complexity_processing
**Module:** `code/analysis/optimize_complexity_processing.py`

Optimized batch processing for complexity analysis.

**Public API:**
- `process_complexity_batch(batch: List[Dict]) -> List[Dict]`: Processes a batch.
- `run_optimized_complexity_analysis()`: Runs optimized pipeline.
- `main()`: CLI entry point.

**Example Usage:**
```python
from analysis.optimize_complexity_processing import run_optimized_complexity_analysis

if __name__ == "__main__":
 run_optimized_complexity_analysis()
```

### save_complexity_scores
**Module:** `code/analysis/save_complexity_scores.py`

Saves computed complexity scores to CSV.

**Public API:**
- `setup_logging_and_config()`: Initializes logger and config.
- `load_labeled_prs(input_path: str) -> List[Dict]`: Loads labeled PRs.
- `extract_pr_diff(pr: Dict) -> str`: Extracts diff.
- `calculate_complexity_score(diff: str) -> float`: Calculates score.
- `save_complexity_scores(scores: List[Dict], output_path: str)`: Saves to CSV.
- `main()`: CLI entry point.

**Example Usage:**
```python
from analysis.save_complexity_scores import save_complexity_scores

# scores = [...]
# save_complexity_scores(scores, "data/processed/complexity_scores.csv")
```

---

## Audit & Validation

### manual_validation
**Module:** `code/audit/manual_validation.py`

Handles manual audit sampling, error rate calculation, and gate checking.

**Public API:**
- `get_audit_config() -> Dict`: Retrieves audit configuration.
- `load_labeled_prs(input_path: str) -> List[Dict]`: Loads labeled PRs.
- `calculate_sample_size(total_n: int, min_threshold: int) -> int`: Calculates stratified sample size.
- `select_stratified_sample(prs: List[Dict], sample_size: int) -> List[Dict]`: Selects sample.
- `execute_human_judgment_checklist(sample: List[Dict]) -> List[Dict]`: Simulates/records human judgment.
- `calculate_error_rate(manual_results: List[Dict], automated_labels: List[Dict]) -> float`: Computes error rate.
- `save_error_rate(rate: float, output_path: str)`: Saves error rate.
- `save_audit_results(results: List[Dict], output_path: str)`: Saves audit log.
- `run_manual_validation()`: Main pipeline runner.
- `main()`: CLI entry point.

**Example Usage:**
```python
from audit.manual_validation import run_manual_validation

if __name__ == "__main__":
 run_manual_validation()
```

---

## Utilities

### config
**Module:** `code/utils/config.py`

Centralized configuration management.

**Public API:**
- `get_path(name: str) -> Path`: Retrieves path for a named resource.
- `get_repo_list() -> List[str]`: Retrieves list of repos.
- `get_api_settings() -> Dict`: Retrieves API settings.
- `get_classification_thresholds() -> Dict`: Retrieves thresholds.
- `get_audit_settings() -> Dict`: Retrieves audit settings.
- `get_complexity_settings() -> Dict`: Retrieves complexity settings.
- `get_config_summary() -> Dict`: Returns a summary of all config.
- `main()`: CLI entry point.

**Example Usage:**
```python
from utils.config import get_repo_list

repos = get_repo_list()
```

### logging
**Module:** `code/utils/logging.py`

Logging infrastructure with PII filtering and rotation.

**Public API:**
- `PIIFilter`: Class that masks PII in log messages.
- `get_log_directory() -> Path`: Returns log directory.
- `setup_logging(script_name: str) -> logging.Logger`: Sets up logging.
- `get_logger(name: str) -> logging.Logger`: Gets logger instance.
- `rotate_logs()`: Handles log rotation.
- `init_logger_for_script(script_name: str) -> logging.Logger`: Initializes for a specific script.
- `main()`: CLI entry point.

**Example Usage:**
```python
from utils.logging import get_logger

logger = get_logger("my_script")
logger.info("Starting process")
```

### seeds
**Module:** `code/utils/seeds.py`

Random seed management for reproducibility.

**Public API:**
- `SeedManager`: Class to manage random states.
- `set_global_seed(seed: int)`: Sets global seed.
- `get_seed_manager() -> SeedManager`: Gets manager instance.
- `sample_with_seed(data: List, n: int, seed: int) -> List`: Samples data with seed.
- `get_random_state(seed: int) -> Any`: Gets random state.
- `set_random_state(state: Any)`: Sets random state.
- `main()`: CLI entry point.

**Example Usage:**
```python
from utils.seeds import set_global_seed

set_global_seed(42)
```

### checksum
**Module:** `code/utils/checksum.py`

SHA-256 checksumming utilities.

**Public API:**
- `calculate_checksum(file_path: Union[str, Path]) -> str`: Calculates checksum.
- `verify_checksum(file_path: Union[str, Path], expected: str) -> bool`: Verifies checksum.
- `generate_checksum_manifest(file_list: List[str], output_path: str)`: Generates manifest.
- `load_checksum_manifest(manifest_path: str) -> Dict`: Loads manifest.
- `main()`: CLI entry point.

**Example Usage:**
```python
from utils.checksum import calculate_checksum

checksum = calculate_checksum("data/raw/file.json")
```

### batch_processor
**Module:** `code/utils/batch_processor.py`

Utilities for batch processing and memory optimization.

**Public API:**
- `get_memory_usage_mb() -> float`: Gets memory usage.
- `force_gc_if_needed()`: Forces GC if needed.
- `memory_monitor()`: Context manager for memory monitoring.
- `chunked_reader(file_path: str, chunk_size: int)`: Reads file in chunks.
- `process_in_batches(data: List, batch_size: int, processor: Callable)`: Processes in batches.
- `load_json_batch(file_path: str) -> List[Dict]`: Loads JSON batch.
- `save_batch_to_json(data: List, output_path: str)`: Saves JSON batch.
- `optimize_dataframe_memory(df)`: Optimizes DataFrame memory.
- `main()`: CLI entry point.

**Example Usage:**
```python
from utils.batch_processor import process_in_batches

# process_in_batches(data, 100, my_processor)
```

---

## Setup

### setup_directories
**Module:** `code/setup_directories.py`

Creates required project directories.

**Public API:**
- `create_directories()`: Creates all required directories.
- `main()`: CLI entry point.

**Example Usage:**
```python
from setup_directories import create_directories

create_directories()
```
