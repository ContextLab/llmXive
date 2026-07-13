# Implementation Plan: Assessing the Reliability of Statistical Power Calculations in Real-World Datasets

**Branch**: `001-assessing-power-reliability` | **Date**: 2026-07-13 | **Spec**: `specs/001-assessing-the-reliability-of-statistical/spec.md`

## Summary

This project implements a computational pipeline to assess the reliability of standard theoretical statistical power calculations (specifically for two-sample t-tests) by comparing them against empirical power estimates derived from bootstrapping on real-world datasets. The core approach involves loading a diverse set of public datasets (sourced from UCI/OpenML), systematically inducing specific assumption violations (heavy-tailed noise, heterogeneity, and time-series autocorrelation *only where appropriate*), and quantifying the bias between the *clean theoretical baseline* and the *perturbed empirical result*. The implementation strictly adheres to CPU-only constraints, ensuring feasibility on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `pytest`, `requests`  
**Storage**: Local file system (CSV/Parquet) under `data/`; results stored as JSON/CSV under `data/processed/`.  
**Testing**: `pytest` with contract tests validating JSON schemas and bootstrap validity checks.  
**Target Platform**: Linux (GitHub Actions Free Tier: A minimal computing environment (e.g., a dual-core CPU and several gigabytes of RAM) is sufficient to execute the research question and method described in [Reference].).  
**Project Type**: Computational Research Pipeline / CLI Tool.  
**Performance Goals**: Total runtime ≤ 6 hours for 10 datasets × 3 violation types × 1000 bootstrap iterations. Memory usage < 6GB to allow overhead.  
**Constraints**: No GPU, no large model training, strict random seed pinning for reproducibility.  
**Scale/Scope**: Multiple diverse datasets (continuous, count, binary), Several violation types (conditional), A sufficient number of bootstrap iterations per condition, sensitivity analysis on multiple thresholds.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Requirement | Plan Compliance |
|-----------|-------------|-----------------|
| **I. Reproducibility** | Random seeds pinned; external datasets fetched from canonical sources. | **Compliant**: `code/` will enforce `np.random.seed(None)

The specific value to remove/generalize: 'None'

Rewritten passage:` and use verified UCI/OpenML URLs. |
| **II. Verified Accuracy** | Citations verified against primary sources. | **Compliant**: The Reference-Validator Agent will be invoked during the data acquisition phase to verify all dataset URLs against the primary UCI/OpenML sources before processing begins. |
| **III. Data Hygiene** | Checksums recorded; no in-place modification; PII scan. | **Compliant**: `data/` will store raw checksums; transformations write to new files; no PII expected in public datasets. |
| **IV. Single Source of Truth** | Figures/Stats trace to `data/` and `code/`. | **Compliant**: All results written to structured JSON; paper generation will parse these files only. |
| **V. Versioning Discipline** | Content hashes for artifacts. | **Compliant**: `state/projects/PROJ-061-assessing-the-reliability-of-statistical.yaml` will track artifact hashes; the pipeline will update the `updated_at` timestamp upon every write to this state file. |
| **VI. Simulation Fidelity** | Record specific violation parameters (df, AR coeff, etc.). | **Compliant**: `PowerEstimate` schema includes `violation_type`, `parameter`, and `achieved_magnitude`. |
| **VII. Dataset Diversity** | ≥10 datasets covering continuous, count, binary outcomes. | **Compliant**: Research phase will select multiple datasets from UCI/OpenML explicitly covering continuous, count, and binary outcome types. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assessing-the-reliability-of-statistical/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Drafted in this phase, finalized in Phase 1
│   ├── power_estimate.schema.yaml
│   └── violation_config.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
projects/PROJ-061-assessing-the-reliability-of-statistical/
├── code/
│   ├── __init__.py
│   ├── main.py                  # Entry point for pipeline execution
│   ├── config.py                # Hyperparameters, seeds, dataset list
│   ├── loaders.py               # Dataset loading and validation (UCI/OpenML)
│   ├── power_theory.py          # Theoretical power calculation (statsmodels/scipy)
│   ├── power_empirical.py       # Bootstrap simulation engine (with Synthetic Shift)
│   ├── perturbations.py         # Injection modules (heavy-tail, AR(1), heterogeneity)
│   ├── validators.py            # Bootstrap stability checks (CV of p-values)
│   └── utils.py                 # Logging, checksums, file I/O
├── tests/
│   ├── unit/
│   │   ├── test_perturbations.py
│   │   └── test_validators.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schemas.py
├── data/
│   ├── raw/                     # Downloaded datasets (checksummed)
│   ├── processed/               # Cleaned/transformed data
│   └── results/                 # JSON output of power estimates
├── docs/
└── requirements.txt
```

**Structure Decision**: Single project structure selected to minimize overhead for a computational research pipeline. All logic resides in `code/` with clear separation between loaders, simulators, and validators.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Synthetic Shift** | Essential to define H1 for continuous data without arbitrary splits. | Arbitrary splits create unknown effect sizes, invalidating the comparison to theoretical power. |
| **Conditional AR(1)** | Essential to test autocorrelation impact. | Applying AR(1) to cross-sectional data creates spurious structures not present in reality. |
| **Bootstrap Stability Check (CV of p-values)** | Required to ensure empirical estimates are reliable (FR-010). | Comparing variances of mean differences conflates data variance with estimator stability. |
| **Sensitivity Analysis (FR-006)** | Required to test robustness of bias classification (US-3). | Single threshold analysis is brittle and fails to address arbitrary cutoff artifacts. |