# Implementation Plan: Assessing the Validity of Statistical Power in Publicly Available Pre-Registered Studies

**Branch**: `001-assessing-statistical-power-validity` | **Date**: 2024-05-22 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-assessing-the-validity-of-statistical-po/spec.md`

## Summary

This feature implements a pipeline to assess the validity of statistical power in pre-registered studies by comparing "planned" power estimates against "sensitivity" power calculated from actual sample sizes. The system extracts data from the Open Science Framework (OSF), calculates power gaps using `statsmodels`, and performs a multiple linear regression to identify predictors of planning inaccuracy. The implementation adheres to strict CPU-only constraints (GitHub Actions free tier) and the project's Constitution regarding reproducibility and data hygiene.

**Key Methodological Correction**: The "Power Gap" metric is redefined to measure **Execution Fidelity** (adherence to planned sample sizes) rather than "Planning Accuracy" (realism of effect size assumptions). The regression model excludes "sample_size_category" to prevent mathematical coupling.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `requests` (OSF API), `pandas`, `statsmodels` (power/regression), `numpy`, `scipy`, `pyyaml`
**Storage**: Local JSON/CSV files in `data/` (raw and derived), checksummed per Constitution Principle III.
**Testing**: `pytest` with unit tests for extraction logic and regression diagnostics.
**Target Platform**: Linux (GitHub Actions free-tier runner: multi-core CPU, several GB RAM).
**Project Type**: Data analysis pipeline / CLI tool.
**Performance Goals**: Complete analysis of a sample cohort (target ≥30 studies) within 6 hours; memory usage < 5 GB.
**Constraints**: No GPU; no large LLM inference; OSF API rate limiting handling; strict adherence to `statsmodels` CPU-tractable methods.
**Scale/Scope**: Batch processing of pre-registered studies; regression on derived metrics.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | All random seeds pinned in `code/`. `requirements.txt` pins versions. Data fetched from canonical OSF API. |
| **II. Verified Accuracy** | **Pass** | **Phase 1.5** explicitly invokes the Reference-Validator Agent to check all citations against primary sources before finalizing research artifacts. |
| **III. Data Hygiene** | **Pass** | Raw data preserved in `data/raw/`; derived data in `data/derived/`. Checksums recorded in state file. No PII allowed. |
| **IV. Single Source of Truth** | **Pass** | All statistics in the final report will trace to specific rows in `data/derived/power_analysis.csv`. |
| **V. Versioning Discipline** | **Pass** | Artifacts will carry content hashes. **The state file (`state/projects/...yaml`) will be explicitly updated with these hashes upon completion of each phase.** |
| **VI. Power Analysis Transparency** | **Pass** | `power_gap`, `test_type`, `effect_size_assumption`, `sample_size`, and `alpha` will be explicitly recorded per study in the dataset. |
| **VII. Statistical Method Specification** | **Pass** | `statsmodels` used for all tests. Alpha fixed at 0.05. VIF diagnostics required before regression interpretation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assessing-the-validity-of-statistical-po/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (Hand-crafted design artifacts)
    ├── study_record.schema.yaml
    └── regression_result.schema.yaml
```

**Note on Contracts**: The `contracts/` directory contains **hand-crafted design artifacts** (Phase 1 output) that define the schema for the data and code. They are not auto-generated from code but serve as the specification for the implementation.

### Source Code (repository root)

```text
projects/PROJ-350-assessing-the-validity-of-statistical-po/
├── data/
│   ├── raw/                 # Raw JSON from OSF API
│   └── derived/             # Cleaned CSVs, power calculations
├── code/
│   ├── __init__.py
│   ├── extraction.py        # OSF API connection, NLP/Regex parsing (FR-001)
│   ├── power_calc.py        # Sensitivity power logic (FR-003)
│   ├── regression.py        # Modeling & VIF diagnostics (FR-005, FR-006)
│   └── main.py              # Pipeline orchestration
├── tests/
│   ├── test_extraction.py
│   ├── test_power_calc.py
│   └── test_regression.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected. The workflow is linear (Extract -> Calculate -> Model), making a monolithic `code/` directory with modular scripts appropriate. This minimizes overhead and fits the CPU-only, low-latency constraints of the GitHub Actions runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **NLP + Regex Hybrid Parsing** | OSF pre-registrations are unstructured text; pure regex fails on varied formats. | Pure regex is brittle and cannot handle semantic variations in "planned power" phrasing. |
| **Sensitivity Power vs. Observed Power** | Required to avoid "Winner's Curse" bias (circularity). | Using observed effect sizes to validate planned power would invalidate the study's core hypothesis. |
| **VIF Diagnostics** | Required by FR-006 to prevent spurious causal claims. | Running regression without collinearity checks risks misinterpreting correlated predictors (e.g., field vs. sample size). |
| **Exclusion of Sample Size Category** | Required to avoid mathematical coupling with Power Gap. | Including sample size as a predictor for a metric derived from sample size creates a tautological regression. |

