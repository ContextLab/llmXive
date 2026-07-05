# Implementation Plan: Robustness of Statistical Tests to Data Contamination

**Branch**: `001-robustness-contamination` | **Date**: 2024-05-22 | **Spec**: `specs/001-robustness-contamination/spec.md`
**Input**: Feature specification from `specs/001-robustness-contamination/spec.md`

## Summary

This feature implements a Monte Carlo simulation study to evaluate the robustness of standard parametric tests (Student's t-test, ANOVA) against data contamination (Gaussian noise, adversarial outliers). The system will generate synthetic contaminated datasets from verified UCI sources (UCI HAR, UCI Wine), run multiple iterations of hypothesis tests under varying contamination rates and thresholds, and compare the empirical Type I error rates and statistical power against lightweight robust estimators (trimmed mean, Winsorized mean). The output includes visualizations of error inflation and power loss, adhering to strict memory and compute constraints of a free-tier GitHub Actions runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `requests`  
**Storage**: Local filesystem (`data/`, `results/`), CSV/JSON formats  
**Testing**: `pytest` (unit tests for contamination logic, integration tests for simulation pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational Research / Simulation  
**Performance Goals**: Complete full simulation suite (2 datasets, **A sufficient number of iterations per condition**, multiple contamination levels/thresholds) within 6 hours on 2 CPU cores, 7 GB RAM.  
**Constraints**: No GPU usage; memory usage capped at a moderate level; no in-place data modification; fixed random seed; strict adherence to verified dataset URLs.  
**Scale/Scope**: Multiple datasets (UCI HAR, UCI Wine), contamination rates ([deferred], [deferred], [deferred], [deferred]), contamination magnitude thresholds (σ, multiple σ), Multiple test types (Standard, Robust), **A sufficient number of iterations per condition to ensure statistical convergence** (totaling [deferred] tests).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Spec Deviation Log

| Spec Requirement | Deviation | Rationale |
| :--- | :--- | :--- |
| **FR-003**: Use Iris, Wine, Breast Cancer | **Substituted**: UCI HAR, UCI Wine | Iris and Breast Cancer are not available in the "# Verified datasets" block. UCI Shopper and DROP were rejected due to categorical/NLP modality mismatches. UCI HAR (numeric sensor) and UCI Wine (numeric tabular) are the only verified numeric sources suitable for t-test simulation. **Validity Note**: Generalization is limited to numeric tabular and sensor-derived data; semantic differences are acknowledged in `research.md`. **Spec Root Cause**: The spec mandates specific datasets that lack verified sources, forcing this substitution. |
| **FR-007**: Report "causal findings" | **Interpreted**: Report "associational observations" | The spec text contains a logical contradiction ("causal findings" vs "avoiding causal claims"). The plan implements the scientifically valid "associational" interpretation but flags the spec text for correction. |
| **User Story 2**: "Shuffle labels" for Type I error | **Corrected**: Resample from single homogeneous population | Shuffling labels on classification data destroys distributional properties and conflates label noise with feature contamination. The plan uses resampling from a single group to ensure a true null hypothesis without distorting the data structure. |
| **SC-005**: Sweep "contamination threshold" | **Implemented**: Magnitude {σ, 10σ} | The User Story acceptance criteria lack explicit detail on this sweep. The plan implements the SC-005 requirement explicitly, distinguishing between *rate* (fraction of data) and *threshold* (magnitude of outlier). |
| **Iteration Count** | **Clarified**: 1000 **per condition** | The original plan ambiguity (total vs per condition) risked statistical insufficiency. Clarified to 1000 per condition to meet SC-001 (CI width < 0.02). **Note**: A sufficient sample size per condition yields a CI width of a narrow magnitude., slightly exceeding the strict <0.02 target; a fallback to 1500 is proposed if strict compliance is required. |
| **FR-003 Iteration Count** | **Flagged**: Ambiguous "n=1000" | The spec states "n=1000 iterations" without specifying "per condition". This ambiguity could lead to statistical insufficiency. Flagged for spec revision. |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seed fixed to a constant value. External datasets fetched from verified HuggingFace URLs (UCI HAR, UCI Wine). `requirements.txt` pins versions. **Note**: Dataset substitution (HAR/Wine vs Iris/Wine/Breast Cancer) is documented in Spec Deviation Log. |
| **II. Verified Accuracy** | **PASS** | All dataset citations restricted to the "# Verified datasets" block. `validate_citations.py` script run as a blocking gate before data download (see Quickstart). |
| **III. Data Hygiene** | **PASS** | Raw data downloaded to `data/raw/` with checksums. Contaminated data written to `data/processed/` with derivation logs. `checksum_artifacts.py` updates `state/` manifest. |
| **IV. Single Source of Truth** | **PASS** | All results derived strictly from `code/` execution on `data/`. No hand-typed statistics. |
| **V. Versioning Discipline** | **PASS** | `checksum_artifacts.py` script generates content hashes for scripts and data, updating `state/` manifest. Workflow steps explicitly include this execution. |

## Project Structure

### Documentation (this feature)

```text
specs/001-robustness-contamination/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-040-robustness-of-statistical-tests-to-data-/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── download_datasets.py
│   │   ├── generate_contamination.py
│   │   └── run_simulation.py
│   ├── utils/
│   │   ├── robust_estimators.py
│   │   └── stats_helpers.py
│   ├── viz/
│   │   └── plot_results.py
│   └── validation/
│       ├── validate_citations.py
│       └── checksum_artifacts.py
├── data/
│   ├── raw/              # Downloaded original datasets
│   ├── processed/        # Contaminated datasets
│   └── results/          # Simulation outputs (CSV/JSON)
├── tests/
│   ├── unit/
│   │   ├── test_contamination.py
│   │   └── test_robust_estimators.py
│   └── integration/
│       └── test_simulation_pipeline.py
└── docs/
    └── paper_draft.md
```

**Structure Decision**: Single project structure selected. The code is organized into logical modules (`data`, `utils`, `viz`) within a `code/` directory to facilitate isolated testing and reproducible execution. This aligns with the "library/cli" pattern suitable for computational research, avoiding unnecessary web/mobile overhead.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Monte Carlo Simulation (1000 iterations per condition)** | Required by FR-003 and SC-001 to estimate empirical error rates with sufficient precision (CI width < 0.02). A fixed number of iterations across all conditions would yield an insufficient sample size per cell, failing the statistical requirement. | Single-run testing provides no statistical confidence intervals and cannot detect rare error inflation events. |
| **Multiple Contamination Levels & Thresholds** | Required by FR-002, SC-005, and User Story 2 to perform sensitivity analysis and map the "robustness curve." | Testing only one level fails to characterize behavior across the full range of data quality issues. |
| **Robust Estimator Implementation** | Required by FR-004 to answer the "can they mitigate?" research question. | Relying solely on standard tests fails to address the core hypothesis of the feature. |
| **Dataset Substitution** | Required by data resource constraints (verified URLs). | Using unverified or non-numeric datasets would violate Constitution Principle II and III. |