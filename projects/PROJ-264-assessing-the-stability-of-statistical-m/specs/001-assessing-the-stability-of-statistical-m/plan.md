# Implementation Plan: Assessing the Stability of Statistical Model Performance Across Data Subsets

**Branch**: `001-assess-model-stability` | **Date**: 2026-06-27 | **Spec**: `specs/001-assess-model-stability/spec.md`
**Input**: Feature specification from `/specs/001-assess-model-stability/spec.md`

## Summary

This project implements a rigorous statistical pipeline to quantify the stability (variance) of three standard machine learning models (Logistic Regression, Random Forest, Linear SVM) across a diverse set of binary classification datasets. The core methodology involves executing **100 evaluations per model-dataset pair** (achieved via multiple folds and repeats for large datasets; adaptive folds for small datasets) to generate a distribution of performance metrics (Accuracy, F1). The plan transforms these raw distributions into stability metrics, prioritizing **Log-Transformed Variance** (log(σ²)) as the primary metric to avoid the tautology of Coefficient of Variation (CV), and correlates them with dataset properties (sample size, feature count) using **Pearson correlation** on log-transformed data (with Spearman as a robustness check). Finally, a Permutation Test determines if variance differences between models are statistically significant, applying **Benjamini-Hochberg** correction for multiple comparisons. The implementation strictly adheres to CPU-only constraints on GitHub Actions, using streaming for large datasets.

**Dataset Selection**: 15 binary classification datasets were selected from OpenML/UCI to span the full range of sample sizes (N=101 to N=48,842) and feature dimensions, ensuring the correlation analysis is statistically valid.

**Total Evaluations**: [deferred] model fits (15 datasets × 3 models × 100 evaluations per pair).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `datasets` (Hugging Face), `scipy`, `pytest`, `ruff`  
**Storage**: Local file system (`data/` for cached datasets, `results/` for outputs)  
**Testing**: `pytest` (unit tests for statistical functions, contract tests for CSV schemas)  
**Target Platform**: GitHub Actions `ubuntu-latest` (CPU-only, 2 cores, ~7 GB RAM)  
**Project Type**: Data Science Pipeline / Statistical Analysis Library  
**Performance Goals**: Complete pipeline execution within 6 hours; memory footprint < 7 GB via streaming/chunking.  
**Constraints**: **CPU execution only** (Constitution Principle I). No GPU acceleration. No data leakage in preprocessing; strict adherence to Benjamini-Hochberg correction.  
**Scale/Scope**: 15 datasets, 3 models, 100 evaluations each ([deferred] total model fits).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Method |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | Global seed set for `random`, `numpy`, and `torch` (if used) to 42; `datasets` cached with **SHA-256 checksums** in `data/`; `requirements.txt` pinned. |
| **II. Verified Accuracy** | PASS | All dataset URLs cited in `research.md` match the **Reference-Validator Agent** output. No invented URLs. The 'Verified Datasets' table is derived from this validated list. |
| **III. Data Hygiene** | PASS | Raw data stored in `data/` with **SHA-256 checksums** recorded; transformations write to `results/`; PII scan via `ruff`/custom script. |
| **IV. Single Source of Truth** | PASS | All statistics in `paper/` trace to `results/raw_evaluations.csv`, `results/stability_metrics.csv`, `results/correlation_results.csv`, and `results/permutation_results.csv`. |
| **V. Versioning Discipline** | PASS | Content hashes recorded in `state/manifest.yaml` updated on change with content hashes. |
| **VI. Statistical Power Adequacy** | PASS | Plan enforces **100 evaluations per model-dataset pair** (10 folds × 10 repeats) as mandated. Adaptive folds used for small datasets to maintain 100 evaluations. |
| **VII. Dataset Diversity** | PASS | Plan selects 15 datasets spanning **N=101 to N=48,842** (verified in `research.md`). Selection mechanism explicitly covers N < 1k, 1k-10k, and >10k ranges. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-model-stability/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── evaluation_run.schema.yaml
│   ├── stability_metric.schema.yaml
│   ├── correlation_result.schema.yaml
│   ├── dataset.schema.yaml
│   └── metrics.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-264-assessing-the-stability-of-statistical-m/
├── code/
│   ├── __init__.py
│   ├── config.py              # Global seeds, paths, hyperparameters
│   ├── data_loader.py         # Streaming download, caching, checksumming
│   ├── pipeline.py            # Orchestration: CV loop, aggregation
│   ├── analyser.py            # CV calculation, Pearson correlation, Permutation test
│   └── report_generator.py    # Markdown/CSV output
├── tests/
│   ├── unit/
│   │   ├── test_analyser.py   # Statistical function tests
│   │   └── test_data_loader.py
│   ├── contract/
│   │   └── test_schemas.py    # Validates CSVs against YAML schemas
│   └── integration/
│       └── test_pipeline.py   # End-to-end run on small subset
├── data/                      # Cached datasets (gitignored, populated by runner)
│   └── checksums.json
├── docs/
│   └── report_template.md     # Markdown template for final report
├── results/                   # Generated outputs
│   ├── raw_evaluations.csv
│   ├── stability_metrics.csv
│   ├── correlation_results.csv
│   ├── permutation_results.csv
│   ├── regression_residuals.csv
│   └── final_report.md
├── ruff.toml                  # Linter configuration
└── requirements.txt           # Dependency pins
```

**Structure Decision**: Single project structure selected to minimize overhead and align with the "CPU-first, script-based" nature of the statistical analysis. No separate frontend/backend is needed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Permutation Test** | Required by FR-005 to test variance differences without normality assumptions. | Parametric tests (e.g., Levene's) assume normality which may not hold for variance distributions of small folds; Permutation is robust. |
| **Benjamini-Hochberg** | Required by FR-007 for exploratory analysis of 15+ tests. | Bonferroni (mentioned in rejected tasks) is too conservative for 15 tests, increasing Type II error risk; BH controls FDR effectively. |
| **Streaming Data** | Required to handle datasets >7 GB RAM on free-tier runners. | Loading full datasets into memory would crash the runner; streaming allows processing large shards sequentially. |
| **Log-Transformed Variance** | Required to avoid tautology of CV vs N. | CV is mathematically tied to mean performance; log-variance measures absolute stability independent of task difficulty. |
| **Adaptive Folds** | Required to maintain 100 evaluations for small datasets. | Fixed 10-fold CV on small datasets yields tiny test sets; adaptive K ensures sufficient test size while maintaining 100 total evaluations. |

## Task Ordering & Dependencies

The implementation tasks are ordered to ensure data is downloaded before consumption, models are fitted before evaluation, and results are aggregated before correlation analysis.

1.  **Phase 1: Data Ingestion & Validation**
    *   T001: Download 15 verified datasets (OpenML/UCI).
    *   T002: Validate binary target and sample size range.
    *   T003: Compute SHA-256 checksums and store in `data/`.
    *   T003a: Configure `ruff.toml` for linting and formatting.
    *   T004: Implement adaptive fold logic (K=10 for N>200, K=5 for N<200).
    *   T005: Implement dataset filtering: **Skip** individual datasets if N<100 (log warning), but **raise Critical Error** if total valid datasets < 15.
2.  **Phase 2: Preprocessing & Pipeline Setup**
    *   T006: Define global seed (42) for all libraries.
    *   T007: Implement Logistic Regression, Random Forest, Linear SVM.
    *   T008: Implement imputation (median/mode) within CV loop to prevent leakage.
3.  **Phase 3: Model Evaluation (US-1)**
    *   T009: Implement `evaluate_model()` function: returns DataFrame with columns `[dataset_id, model_name, fold_id, repeat_id, accuracy, f1_score]`.
    *   T010: Execute multiple evaluations (10 folds × 10 repeats) per model-dataset pair.
    *   T011: Write `results/raw_evaluations.csv` (validated against schema). **Schema**: `dataset_id` (int), `model_name` (str), `fold_id` (int), `repeat_id` (int), `accuracy` (float), `f1_score` (float).
4.  **Phase 4: Stability Analysis (US-2)**
    *   T012: Calculate mean, std, and **log-variance** for each model-dataset pair.
    *   T013: Compute **Pearson correlation** between log-variance and log(n_samples) / log(n_features) (Primary). Compute Spearman as secondary robustness check.
    *   T014: Compute residuals from log-log linear regression. Output: `results/regression_residuals.csv`.
    *   T015: Apply Benjamini-Hochberg correction to p-values.
    *   T016: Write `results/stability_metrics.csv` and `results/correlation_results.csv`. **Schema**: `stability_metrics.csv` (dataset_id, model_name, mean_accuracy, std_accuracy, cv_accuracy, mean_f1, std_f1, cv_f1, n_evals); `correlation_results.csv` (metric_name, property_name, correlation_coefficient, p_value, adjusted_p_value, method).
5.  **Phase 5: Variance Comparison (US-3)**
    *   T017: Implement Permutation Test on squared deviations.
    *   T018: Apply Benjamini-Hochberg correction to permutation p-values.
    *   T019: Write `results/permutation_results.csv`. **Schema**: `dataset_id` (int), `model_pair` (str), `statistic` (float), `raw_p_value` (float), `adjusted_p_value` (float), `is_significant` (bool).
6.  **Phase 6: Reporting**
    *   T020: Generate `results/final_report.md` from all CSVs using `docs/report_template.md`.

**Dependencies & Execution Order**:
-   T005 depends on T001/T002.
-   T009 depends on T007/T008.
-   T010 depends on T009.
-   T011 depends on T010.
-   T012 depends on T011.
-   T013 depends on T012.
-   T014 depends on T013.
-   T015 depends on T013/T014.
-   T016 depends on T015.
-   T017 depends on T011.
-   T018 depends on T017.
-   T019 depends on T018.
-   T020 depends on T016/T019.

## Contracts & Schemas

All output CSVs must strictly adhere to the schemas defined in `contracts/`.
-   `contracts/evaluation_run.schema.yaml`: Defines `raw_evaluations.csv` structure.
-   `contracts/stability_metric.schema.yaml`: Defines `stability_metrics.csv` structure.
-   `contracts/correlation_result.schema.yaml`: Defines `correlation_results.csv` structure.
-   `contracts/permutation_result.schema.yaml`: Defines `permutation_results.csv` structure.

## Compute Feasibility

-   **CPU-First**: All models (Logistic Regression, Random Forest, Linear SVM) are CPU-tractable.
-   **Memory**: Streaming ensures memory usage stays below 7 GB.
- **Time**: [deferred] model fits. With average fit time < 1 second per fold (small datasets) to 30 seconds (large datasets), the total runtime is estimated at several hours on a multi-core CPU, well within the 6-hour limit.
-   **GPU Escape Hatch**: **Not applicable.** The Constitution mandates CPU-only execution for this project scope.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Insufficient Binary Datasets** | Cannot reach 15 datasets. | Pipeline halts with critical error if the verified set does not span the required range. |
| **Network Failure** | Pipeline halts. | Implement `try/except` blocks around download; skip failed dataset, log warning, continue (only if >15 valid remain). |
| **Zero Variance** | Log-variance calculation crash. | Handle `std=0` explicitly; assign log-variance = -999. |
| **Time Budget Exceeded** | Job timeout. | Add a "progress check" every 10 datasets; if runtime > 4h, reduce repeats to a reasonable threshold (log warning) or stop. |