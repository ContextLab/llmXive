# Implementation Plan: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

**Branch**: `001-sensitivity-regression-coefficients` | **Date**: 2026-08-16 | **Spec**: `specs/001-sensitivity-regression-coefficients/spec.md`
**Input**: Feature specification from `specs/001-sensitivity-regression-coefficients/spec.md`

## Summary

This feature implements a computational study to assess how OLS assumption violations (heteroscedasticity, outliers) and collinearity modify the **sensitivity of regression coefficients to dataset subset selection**. The technical approach involves: (1) ingesting verified numerical datasets with continuous outcomes; (2) profiling global violation metrics (Breusch-Pagan, Cook's Distance, Condition Number); (3) performing a resampling experiment to estimate the **rate of convergence** of coefficient variance as a function of sample size; and (4) fitting a **Hierarchical Linear Model (HLM)** to test if global violation metrics moderate this convergence rate. The implementation prioritizes CPU feasibility (limited core count, constrained RAM) with a strict fallback protocol for memory overflow.

## Technical Context

**Language/Version**: Python 3.x  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `pyyaml`, `datasets` (HuggingFace), `pytest`, `linearmodels` (for HLM)  
**Storage**: Local filesystem (`data/` for raw/processed CSV/Parquet, `artifacts/` for JSON/CSV results)  
**Testing**: `pytest` with unit tests for statistical calculations and integration tests for the full pipeline on a small synthetic dataset.  
**Target Platform**: GitHub Actions free-tier runner (Linux, multi-core CPU, 7GB RAM).  
**Project Type**: Research CLI / Simulation Engine  
**Performance Goals**: Complete datasets + A large number of subsets each within 6 hours; individual OLS fit < 0.1s; memory usage < 6GB peak.  
**Constraints**: No external API calls requiring auth; no local GPU assumption; strict adherence to verified dataset URLs.  
**Scale/Scope**: datasets, A large number of total model fits, ~GB of transient I/O (streamed).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates pinned `random_state` in all resampling loops and deterministic dataset fetching via `datasets.load_dataset`. |
| **II. Verified Accuracy** | PASS | All dataset URLs are restricted to the "Verified datasets" block in the spec. No hallucinated citations. |
| **III. Data Hygiene** | PASS | Plan includes checksumming step (`md5sum`) upon download and strict separation of raw vs. processed data. |
| **IV. Single Source of Truth** | PASS | Final regression results will be written to `artifacts/meta_analysis_results.json` which the paper must cite. |
| **V. Versioning Discipline** | PASS | All artifacts will include content hashes in the `state` YAML. |
| **VI. Empirical Validation of Theoretical Assumptions** | PASS | The core experiment explicitly correlates the **rate of convergence** (Outcome) with BP/Cook/Cond (Predictors) to test sensitivity, avoiding circularity. |
| **VII. Non-Circular Derivation of Stability Metrics** | PASS | The outcome is the *slope* of variance vs. sample size, not the variance itself. Predictors are global descriptors. This tests moderation, not a tautology. |

## Project Structure

### Documentation (this feature)

```text
specs/001-sensitivity-regression-coefficients/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset_profile.schema.yaml
│   ├── stability_result.schema.yaml
│   └── meta_analysis.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── ingestion/
│   ├── __init__.py
│   ├── downloader.py      # Handles verified dataset fetching
│   └── profiler.py        # Computes BP, Cook's, Condition Number
├── resampling/
│   ├── __init__.py
│   ├── engine.py          # Generates subsets and fits OLS
│   └── aggregator.py      # Computes empirical SD and convergence slopes
├── analysis/
│   ├── __init__.py
│   └── hlm_analysis.py    # Hierarchical Linear Model for cross-level interaction
├── utils/
│   ├── __init__.py
│   └── validation.py      # Checksums, singularity checks
└── cli.py                 # Entry point

tests/
├── unit/
│   ├── test_profiler.py
│   └── test_resampling.py
├── integration/
│   └── test_full_pipeline.py
└── conftest.py            # Fixtures for small synthetic data
```

**Structure Decision**: Monolithic `src/` structure with clear module separation (Ingestion, Resampling, Analysis) to ensure modularity while keeping the research pipeline linear and easy to debug. No microservices or complex web architecture needed for a simulation study.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Hierarchical Linear Model (HLM)** | To properly model the nested structure (subsets within datasets) and test cross-level interactions. | Simple regression on N=datasets is underpowered and ignores the variance of the estimates. |
| **Streaming Data Loading** | Datasets may exceed 7GB RAM if fully loaded. | Loading full CSVs into Pandas would crash the CI runner; streaming is required for feasibility. |
| **Checkpointing** | -hour timeout risk on 10 datasets. | Running [deferred] fits without intermediate saves risks losing all progress on a timeout. |
| **Singularity Handling** | Subsets may be singular even if full data is not. | A naive `ols.fit()` would crash the entire loop; robust error handling is required for valid statistics. |

## Compute Feasibility

The implementation runs on a GitHub Actions free-tier runner: **A limited number of CPU cores, ~7 GB RAM, A significant disk capacity is required to accommodate the research data., NO local GPU, ≤6 h per job.**

- **CPU-first.** OLS and HLM are CPU-native. The plan uses `statsmodels` and `linearmodels` which run efficiently on CPU.
- **GPU Escape Hatch.** The plan **does not** require GPU for OLS or HLM. A GPU escape hatch is only defined for **memory overflow** (if a dataset > 7GB cannot be streamed efficiently). In that case, the job re-runs on a Kaggle GPU kernel (which has more RAM) to stream/process the data, but the statistical computation remains CPU-based logic. This ensures reproducibility on the primary platform (GitHub Actions) while providing a path for large data.
- **No Synthetic Substitution.** Real data is prioritized. Synthetic data is only generated if real data lacks variance in predictors, using a controlled generator that decouples collinearity and heteroscedasticity.

## Data Availability

- **Prefer OPEN, directly-downloadable datasets.** We use verified HuggingFace datasets with continuous outcomes (e.g., California Housing, Concrete Compressive Strength).
- **Access-gated data is a fatal feasibility flaw.** We do not use ADNI, HCP, or other gated data.
- **Large real datasets: plan to STREAM.** We use `datasets.load_dataset(..., streaming=True)` to process data without loading it all into RAM. Only if streaming fails do we subsample.
