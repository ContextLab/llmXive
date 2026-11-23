# API Reference

This document provides a reference for the core modules in the Digital Decluttering research pipeline.

## Analysis Module (`code/analysis/`)

### `bootstrap_ci.py`
Calculates bootstrapped confidence intervals for statistical metrics.

**Key Functions**:
- `calculate_bootstrap_ci(data: List[float], n_resamples: int = 10000) -> BootstrapResult`
- `run_bootstrap_analysis(baseline: List[float], post: List[float]) -> Dict`

**Classes**:
- `BootstrapResult`: Dataclass containing mean, CI lower, CI upper, and p-value.

### `change_scores.py`
Computes change scores (post - baseline) for participants.

**Key Functions**:
- `calculate_change_score(baseline_val: float, post_val: float) -> float`
- `run_change_score_calculation(input_path: str, output_path: str)`

### `effect_sizes.py`
Calculates Cohen's d and effect size confidence intervals.

**Key Functions**:
- `calculate_cohens_d(group1: List[float], group2: List[float]) -> float`
- `run_effect_size_analysis(data_path: str, output_path: str)`

### `holm_bonferroni.py`
Implements Holm-Bonferroni step-down correction for multiple comparisons.

**Key Functions**:
- `calculate_holm_bonferroni(p_values: List[float]) -> List[float]`
- `run_holm_bonferroni_pipeline(input_path: str, output_path: str)`

### `power_simulation.py`
Performs Monte Carlo power simulations.

**Key Functions**:
- `run_power_simulation(n_iterations: int = 1000, effect_size: float = 0.5) -> Dict`

### `statistical_summary.py`
Aggregates results into a comprehensive summary.

**Key Functions**:
- `aggregate_results() -> Dict`
- `write_summary(output_path: str)`

### `wilcoxon_fallback.py`
Provides Wilcoxon signed-rank test as a fallback for bootstrap failures.

**Key Functions**:
- `run_wilcoxon_test(group1: List[float], group2: List[float]) -> Dict`

## Compliance Module (`code/compliance/`)

### `parse_logs.py`
Parses JSON and CSV compliance logs.

**Key Functions**:
- `parse_json_logs(file_path: str) -> List[Dict]`
- `parse_csv_logs(file_path: str) -> List[Dict]`

### `rules_engine.py`
Evaluates compliance rules (e.g., social media limits).

**Key Functions**:
- `check_compliance_rules(log_entry: Dict) -> ComplianceResult`

**Classes**:
- `ComplianceResult`: Dataclass with `is_compliant` and `violations` fields.

## Pipeline Module (`code/pipeline/`)

### `collect_baseline.py`
Orchestrates baseline data collection.

**Key Functions**:
- `run_baseline_pipeline()`

### `merge_data.py`
Merges baseline and post-intervention datasets.

**Key Functions**:
- `merge_baseline_post(baseline_path: str, post_path: str) -> List[Dict]`

### `validate_quickstart.py`
Validates the quickstart process end-to-end.

**Key Functions**:
- `validate_output_file(file_path: str) -> bool`

## Scoring Module (`code/scoring/`)

### `sart.py`
Scores Sustained Attention to Response Task (SART) data.

**Key Functions**:
- `score_sart_session(trials: List[Dict]) -> Dict`

### `ospan.py`
Scores Operation Span (Ospan) task data.

**Key Functions**:
- `score_ospan_session(trials: List[Dict]) -> Dict`

### `questionnaires.py`
Scores PSS-10 and PANAS questionnaires.

**Key Functions**:
- `score_pss10_session(responses: List[int]) -> int`
- `score_panas_session(responses: List[int]) -> Dict`

### `id_generator.py`
Generates pseudonymous participant IDs.

**Key Functions**:
- `generate_sequence_ids(n: int) -> List[str]`

## Validation Module (`code/validation/`)

### `synthetic_baseline.py`
Generates synthetic baseline data for testing.

**Key Functions**:
- `generate_synthetic_data(n_participants: int) -> List[Dict]`

### `validate_instruments.py`
Validates scoring logic against expected ranges.

**Key Functions**:
- `validate_sart(data: List[Dict]) -> bool`

### `validate_success_criteria.py`
Checks results against predefined success criteria.

**Key Functions**:
- `validate_success_criteria(summary: Dict) -> ValidationResult`

## Visualization Module (`code/viz/`)

### `generate_plots.py`
Generates boxplots and distribution charts.

**Key Functions**:
- `generate_all_plots(data_path: str, output_dir: str)`

## Report Module (`code/report/`)

### `generate_report.py`
Compiles the final research report.

**Key Functions**:
- `generate_report(summary: Dict, power_results: Dict) -> str`

## Configuration Module (`code/config/`)

### `env_config.py`
Manages environment configuration and paths.

**Key Functions**:
- `get_config() -> ProjectConfig`
- `get_path(key: str) -> Path`
