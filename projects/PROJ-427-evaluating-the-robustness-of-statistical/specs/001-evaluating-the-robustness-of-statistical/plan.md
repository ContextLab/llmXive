# Implementation Plan: Evaluating the Robustness of Statistical Methods to Common Data Errors

**Branch**: `001-evaluate-statistical-robustness` | **Date**: 2026-06-28 | **Spec**: `specs/001-evaluating-the-robustness-of-statistical/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-the-robustness-of-statistical/spec.md`

## Summary

This project implements a reproducible simulation pipeline to evaluate how standard statistical tests (t-test, ANOVA, Chi-squared, Linear Regression) degrade under controlled data errors. The approach involves: (1) downloading verified public datasets, (2) injecting three error types (random value replacement, category misclassification, MCAR missingness) at defined rates ([deferred], [deferred], [deferred], [deferred]), (3) running statistical tests on clean and corrupted data, and (4) aggregating metrics (Type I error, CI coverage, effect size bias). The implementation is constrained to CPU-only execution on GitHub Actions free-tier runners (limited CPU resources, constrained memory).

**Key Parameters**:
- **Error Rates**: [deferred], [deferred], [deferred], [deferred].
- **Error Types**: Random Value Replacement, Category Misclassification, MCAR Missingness.
- **Statistical Tests**: t-test, ANOVA, Chi-squared, Linear Regression.
- **Metrics**: Empirical Type I Error, CI Coverage, Effect Size Bias, Power Loss.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `datasets` (for HuggingFace loading)  
**Storage**: Local file system (`data/raw`, `data/processed`, `results`)  
**Testing**: `pytest` (unit tests for injection logic, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational research / simulation pipeline  
**Performance Goals**: Complete full simulation suite within 6 hours on 2 CPU cores.  
**Constraints**: No GPU usage; memory footprint < 7GB; no external API calls during execution (datasets pre-fetched or loaded via verified URLs).  
**Scale/Scope**: A small number of datasets, error types, error rates, statistical tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Strategy |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; datasets loaded from fixed URLs; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | PASS | Dataset URLs restricted to the `# Verified datasets` block in the prompt; no fabricated citations. |
| **III. Data Hygiene** | PASS | Raw data stored in `data/raw` with checksums; error injection creates new files in `data/processed`; no in-place modification. |
| **IV. Single Source of Truth** | PASS | All metrics calculated by `code/` scripts and saved to `results/`; paper generation reads directly from these files. |
| **V. Versioning Discipline** | PASS | Artifact hashes generated via SHA-256 in `main.py` after each pipeline stage and recorded in the state file. |
| **VI. Systematic Error Injection** | PASS | Plan explicitly defines [deferred], [deferred], [deferred], [deferred] rates and error types (Replacement, Misclassification, MCAR) as per spec. |
| **VII. Comprehensive Test Coverage** | PASS | Plan covers t-test, ANOVA, Chi-squared, Regression across all error types/rates. |

## Configuration Strategy

To satisfy the Constitution's requirement for explicit definition in the design phase:
- **Error Rates**: Defined in `code/config.py` as `We will investigate error rates across a range of low to moderate magnitudes to determine their impact on system performance.`.
- **Test Types**: Defined in `code/config.py` as `TEST_TYPES = ['t_test', 'anova', 'chi_squared', 'linear_regression']`.
- **Seeds**: Defined in `code/config.py` as `BASE_SEED = 42` (incremented per iteration).
- **Minimum N**: `MIN_SAMPLE_SIZE = 30` (post-listwise deletion).

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-the-robustness-of-statistical/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # (Removed: See Fabricated Result Resolution)
```

### Source Code (repository root)

```text
projects/PROJ-427-evaluating-the-robustness-of-statistical/
├── code/
│   ├── __init__.py
│   ├── config.py              # Error rates, seeds, dataset paths
│   ├── data_loader.py         # Fetch/clean datasets
│   ├── error_injector.py      # FR-002: Injection logic
│   ├── statistical_engine.py  # FR-003: Test execution
│   ├── metrics_calculator.py  # FR-004: Type I, CI, Bias
│   ├── visualizer.py          # FR-005: Degradation curves
│   └── main.py                # Orchestration (Hash generation)
├── data/
│   ├── raw/                   # Downloaded datasets (checksummed)
│   └── processed/             # Error-injected versions
├── results/
│   ├── metrics.json           # Aggregated results
│   └── plots/                 # PNG outputs
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single Python package structure (`code/`) to ensure modularity and easy testing. Data is separated into `raw` (immutable) and `processed` (derived). Results are decoupled from code to allow re-plotting without re-running simulations.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly bounded by the spec and CPU constraints. | N/A |