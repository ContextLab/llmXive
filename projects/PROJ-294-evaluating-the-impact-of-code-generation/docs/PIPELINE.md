# Pipeline Execution Guide

This document describes the execution order and dependencies of the automated science pipeline.

## Execution Order

The pipeline runs in the following stages:

1. **Validation (T007b)**
 - **Script**: `code/validate_citations.py`
 - **Action**: Validates citations in `state/citations.yaml`.
 - **Gate**: If validation fails, the pipeline aborts immediately.

2. **Data Acquisition (T010, T011)**
 - **Script**: `code/download_data.py`
 - **Action**: Downloads HumanEval from HuggingFace, verifies integrity, and performs stratified sampling.
 - **Output**: `data/raw/humaneval.json`

3. **Code Generation (T012, T028, T029)**
 - **Script**: `code/generate_code.py`
 - **Action**: Generates code using CodeGen-350M, and optionally CodeLlama variants for sensitivity analysis.
 - **Output**: `data/generated/code_samples.json`

4. **Metrics Analysis (T014a, T014b, T015, T042, T017)**
 - **Script**: `code/analyze_metrics.py`
 - **Action**: Calculates Cyclomatic Complexity, Halstead Volume, Pass Rate, and Branch Coverage.
 - **Output**: `data/analysis/metrics.json`

5. **Sensitivity Merge (T041a, T041b, T041c)**
 - **Script**: `code/merge_sensitivity_metrics.py`
 - **Action**: Merges sensitivity analysis results, resolves conflicts, and versioning.
 - **Output**: `data/analysis/metrics_v{N}.json`

6. **Sensitivity Computation (T045, T046)**
 - **Script**: `code/statistical_tests.py` (partial)
 - **Action**: Computes effect sizes and delta calculations.
 - **Output**: `data/analysis/sensitivity_metrics.json`

7. **Statistical Testing (T020-T024, T040)**
 - **Script**: `code/statistical_tests.py`
 - **Action**: Performs Wilcoxon, McNemar, Permutation tests, and Power Analysis.
 - **Output**: `data/analysis/statistical_results.json`

8. **Report Generation (T030-T032)**
 - **Script**: `code/report_generator.py`
 - **Action**: Generates figures and compiles the final Markdown report.
 - **Output**: `results_report.md`, `results/figures/`

## Dependencies

- **Phase 1 (Setup)**: No dependencies.
- **Phase 2 (Foundational)**: Depends on Phase 1. Blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2. Includes sensitivity data merge (T041c).
- **Phase 3.5 (Sensitivity)**: Depends on Phase 3.
- **Phase 4 (US2)**: Depends on Phase 3 (T041c).
- **Phase 5 (US3)**: Depends on Phase 4 and T046.

## Error Handling

- **Citation Validation Failure**: Pipeline aborts with `SystemExit(1)`.
- **Data Download Failure**: Retries with exponential backoff (T043). Fails loudly if real source is unreachable.
- **Code Generation Failure**: Logs to `errors.log` and marks samples as missing.
- **Metric Calculation Failure**: Records `[deferred]` for coverage, logs error.

## Configuration

- **API Keys**: Set `HF_API_TOKEN` for HuggingFace Inference API.
- **Model Paths**: Configure local model paths in `code/generate_code.py` if using local models.
- **Logging**: Logs are written to `logs/pipeline.log` with timestamp and task ID.

## Troubleshooting

- **Missing Data**: Check `data/raw/` and `data/generated/` directories.
- **Statistical Errors**: Ensure sufficient sample size (n ≥ 38) for power analysis.
- **Visualization Errors**: Verify `matplotlib` installation and font availability.
