# Implementation Plan: Evaluating the Robustness of Statistical Methods to Common Data Errors

**Branch**: `001-evaluate-statistical-robustness` | **Date**: 2024-05-21 | **Spec**: `specs/001-evaluating-the-robustness-of-statistical/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-robustness-of-statistical/spec.md`

## Summary

This project implements a reproducible simulation pipeline to evaluate how common data errors (random value replacement, category misclassification, and MCAR missingness) degrade the performance of standard statistical tests (t-test, ANOVA, chi-squared, linear regression). The system generates ground-truth datasets, injects errors at controlled rates (**[deferred], [deferred], [deferred], [deferred]**), executes statistical tests, and calculates empirical Type I error rates, confidence interval (CI) coverage, and effect size bias. All results are aggregated into degradation curves and summary tables.

The pipeline strictly separates **Synthetic Data** (used for calculating Bias and CI Coverage against known parameters) from **Real-World Data** (used for calculating Type I Error via permutation and Power loss). This separation ensures methodological rigor and prevents circular validation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`  
**Storage**: Local CSV/Parquet files under `data/`; no external database.  
**Testing**: `pytest` with contract tests against schema definitions.  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, 7GB RAM, no GPU).  
**Project Type**: Computational research pipeline / CLI tool.  
**Performance Goals**: Complete full simulation suite (all error types, rates, and tests) within 6 hours.  
**Constraints**: CPU-only execution; no GPU libraries; data subsets to fit <7GB RAM; strict reproducibility via pinned seeds.  
**Scale/Scope**: Multiple diverse datasets; error types; error rates; statistical tests; A sufficient number of simulation iterations per configuration.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | **Compliant** | All random seeds pinned in `code/`. External datasets fetched from verified URLs. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **Compliant** | Citations in `research.md` limited to verified dataset URLs provided in the spec. No fabricated results; all metrics computed from simulation runs. |
| **III. Data Hygiene** | **Compliant** | Raw data checksummed in `state/`. Derivations (corrupted data) written to new files. PII scan passed (synthetic/public data only). |
| **IV. Single Source of Truth** | **Compliant** | Figures/tables in final report trace to `data/` artifacts and `code/` execution logs. No hand-typed numbers. |
| **V. Versioning Discipline** | **Compliant** | Content hashes tracked in `state/`. Artifacts updated on change. |
| **VI. Systematic Error Injection** | **Compliant** | Error rates (**[deferred], [deferred], [deferred], [deferred]**) and types (replacement, misclassification, MCAR) strictly implemented as per spec. Parameters recorded in logs. |
| **VII. Comprehensive Test Coverage** | **Compliant** | All 4 tests (**t-test, ANOVA, chi-squared, regression**) run across all specified error types/rates. All 4 metrics (Type I, CI coverage, bias, degradation) reported. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-robustness-of-statistical/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── aggregation_schema.schema.yaml
    ├── dataset.schema.yaml
    ├── dataset_schema.schema.yaml
    ├── error_config.schema.yaml
    ├── evaluation_results.schema.yaml
    ├── inference_metric.schema.yaml
    ├── injection.schema.yaml
    ├── metrics_schema.schema.yaml
    └── result.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-427-evaluating-the-robustness-of-statistical/
├── code/
│   ├── __init__.py
│   ├── download.py          # Fetches verified datasets
│   ├── inject.py            # Error injection logic (FR-002)
│   ├── analyze.py           # Statistical tests & metric calculation (FR-003, FR-004)
│   ├── visualize.py         # Degradation curves (FR-005)
│   └── main.py              # Orchestration script
├── data/
│   ├── raw/                 # Downloaded clean datasets
│   ├── corrupted/           # Generated error-injected datasets
│   └── results/             # Simulation output logs (JSON/CSV)
├── tests/
│   ├── contract/            # Schema validation tests
│   ├── integration/         # Pipeline end-to-end tests
│   └── unit/                # Logic tests (injection rates, metric calcs)
├── docs/
│   └── ...
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The workflow is linear (Download → Inject → Analyze → Visualize), making a monolithic `code/` directory with modular scripts efficient and easy to maintain. No separate frontend/backend required.

## Computational Task Ordering

To ensure a functional pipeline and avoid circular dependencies:
1.  **Data Preparation**: Download and clean real datasets; generate synthetic datasets with known parameters.
2.  **Error Injection**: Apply error types at defined rates to the clean datasets.
3.  **Analysis**: Run statistical tests on the corrupted datasets.
4.  **Aggregation**: Compute metrics (Type I, CI, Bias) from the test results.
5.  **Visualization**: Generate degradation curves from the aggregated metrics.

This order ensures that data is available before analysis, and analysis results are available before visualization.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | The design adheres strictly to the spec. Complexity is driven by the need for rigorous simulation (multiple error types, rates, and statistical tests) rather than architectural over-engineering. |
