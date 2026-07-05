# Implementation Plan: Evaluating the Impact of Outlier Removal Methods on Variance Estimation

**Branch**: `001-evaluating-outlier-removal-impact` | **Date**: 2026-06-26 | **Spec**: `specs/001-evaluating-the-impact-of-outlier-removal/spec.md`
**Input**: Feature specification from `specs/001-evaluating-the-impact-of-outlier-removal/spec.md`

## Summary

This feature implements a statistical simulation study to evaluate how three outlier removal methods (IQR filtering, Winsorization, Trimming) affect variance estimation accuracy. The system will generate synthetic data with known ground truth parameters, inject outliers at varying rates, apply removal strategies, and compute bias and Mean Squared Error (MSE) against the theoretical distribution parameters. Statistical significance will be tested via Linear Mixed-Effects Models (LMM) with Holm-Bonferroni correction.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scipy, statsmodels, matplotlib, seaborn, pyyaml, linearmodels  
**Storage**: Local filesystem (CSV/Parquet) under `data/`  
**Testing**: pytest (contract tests against YAML schemas)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: CLI / Data Science Simulation  
**Performance Goals**: Complete 100 Monte Carlo replicates across 5 distributions and 4 contamination levels within 6 hours on 2 CPU cores, 7GB RAM.  
**Constraints**: No GPU; CPU-only execution; memory usage < 6GB to allow OS overhead; no external API calls during runtime (datasets fetched once).  
**Scale/Scope**: 
- **5 UCI Datasets**: Downloaded and processed to extract distributional parameters (skewness, kurtosis) for seeding synthetic generation. 
- **5 Distribution Types**: Normal, LogNormal, Exponential, Beta, Gamma (used for synthetic generation).
- **3 Removal Methods**: IQR, Winsorization, Trimming.
- **4 Contamination Levels**: [deferred], [deferred], [deferred], [deferred].
- **100 Replicates/Condition**: Strictly enforced (no fallback).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `projects/PROJ-428-evaluating-the-impact-of-outlier-removal/.specify/memory/constitution.md`*

| Principle | Status | Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | `random.seed(42)` set globally; `requirements.txt` pins versions; scripts run end-to-end. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` restricted to verified URLs. The Reference-Validator Agent enforces the `research_review` → `research_accepted` gate before acceptance. |
| **III. Data Hygiene** | PASS | Raw synthetic data generation is deterministic; checksums recorded in `state/` manifest. |
| **IV. Single Source of Truth** | PASS | All results stored in `data/results/`; figures generated programmatically from this data. |
| **V. Versioning Discipline** | PASS | Artifacts hashed; `updated_at` logic handled by agent workflow. |
| **VI. Monte Carlo Replication** | PASS | Plan strictly enforces 100 replicates per condition. No fallback to 50 is permitted; exceeding 6 hours is a feasibility failure. |
| **VII. Distribution-Type Stratification** | PASS | Analysis loops over 5 distinct distribution types; results stored with `distribution_type` column. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-outlier-removal-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── contamination_profile.schema.yaml
    ├── removal_method.schema.yaml
    └── estimation_result.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-428-evaluating-the-impact-of-outlier-removal/
├── code/
│   ├── requirements.txt
│   ├── src/
│   │   ├── __init__.py
│   │   ├── data_generator.py       # Synthetic data + UCI loading logic
│   │   ├── outlier_removal.py      # IQR, Winsorization, Trimming logic
│   │   ├── metrics.py              # Bias, MSE calculation
│   │   └── analysis.py             # LMM, plotting
│   ├── tests/
│   │   ├── test_data_generator.py
│   │   └── test_contracts.py       # Validates output against YAML schemas
│   └── run_simulation.py           # Entry point
├── data/
│   ├── raw/                        # Downloaded/Generated raw data
│   └── processed/                  # Cleaned/Analyzed data
└── state/
    └── projects/PROJ-428-.../state.yaml
```

**Structure Decision**: Single project structure (Option 1) selected to minimize overhead. The `src/` directory contains modular scripts for data generation, processing, and analysis, aligned with the linear workflow of the simulation. Tests are colocated in `tests/` with a specific module for contract validation.

## Complexity Tracking

No violations detected in Constitution Check. The complexity of 100 replicates across 5 distributions and 4 contamination levels is managed by the linear, batch-oriented nature of the simulation, which is optimized for CPU execution. If the 6-hour limit is exceeded, the project will be flagged for resource review rather than degrading statistical power.