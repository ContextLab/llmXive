# Implementation Plan: Developing Novel Solutions to Address Energy Inequity in Low-Income Communities

**Branch**: `001-gene-regulation` | **Date**: 2026-08-27 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This feature implements a causal inference pipeline to estimate the impact of clean-energy adoption (treatment) on energy costs and socioeconomic outcomes for low-income US households. The approach relies on Propensity Score Matching (PSM) using EIA RECS and ACS data to construct a balanced control group, followed by OLS estimation of the Average Treatment Effect on the Treated (ATT) using `log(energy_cost)` as the primary outcome to avoid definitional circularity. A fallback Difference-in-Differences (DiD) strategy is included *only if* longitudinal data is available in the source dataset; otherwise, the pipeline halts the DiD attempt and reports the data constraint. The plan strictly adheres to the project constitution regarding reproducibility, data hygiene, and causal identification rigor. An exploratory scaling law module is included as a *descriptive* analysis at the tract level, explicitly excluded from causal claims.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `statsmodels`, `censusdata`, `matplotlib`, `seaborn`, `pyyaml`
**Storage**: Local file system (`data/`), CSV/Parquet formats
**Testing**: `pytest`
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: Data Analysis / Causal Inference Pipeline
**Performance Goals**: Process < 7 GB RAM, complete within 6 hours on 2 CPU cores.
**Constraints**: No local GPU; CPU-first execution; strict adherence to open-data availability (no gated datasets).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All code will be pinned in `requirements.txt`. Random seeds (numpy, pandas, sklearn) will be set globally. Data ingestion scripts will fetch from canonical URLs listed in `research.md` and record checksums. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` will be restricted to the "Verified datasets" block provided in the spec. The implementation will verify column headers against the EIA RECS schema and halt if mismatched. |
| **III. Data Hygiene** | **PASS** | Raw data will be stored in `data/raw/` with checksums. Transformed data will be stored in `data/processed/` with derivation logs. PII scanning will be run on all output artifacts. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report will be generated programmatically from `data/processed/` and `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes. The `state/` file will be updated upon successful completion of phases. |
| **VI. Causal Identification Rigor** | **PASS** | The plan explicitly implements PSM with SMD validation. The Scaling Law module is strictly *descriptive* and excluded from causal claims. The DiD fallback is conditional on data availability. |
| **VII. Socioeconomic Proxy Integrity** | **PASS** | Only variables explicitly present in the verified EIA RECS/ACS datasets will be used. No synthetic proxies will be constructed. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── ingest.py        # Fetches EIA RECS (official) and ACS (censusdata API)
│   ├── preprocess.py    # Cleaning, filtering, feature engineering
│   └── checksums.json   # Recorded hashes
├── analysis/
│   ├── psm.py           # Propensity Score Matching logic
│   ├── balance.py       # SMD calculation and balance plots
│   ├── causal.py        # OLS ATT (log-cost) and DiD fallback (conditional)
│   └── sensitivity.py   # Caliper sweep and robustness checks
├── scaling/
│   └── scaling.py       # Descriptive scaling law analysis (tract-level)
├── models/
│   ├── schemas.py       # Pydantic models for data validation
│   └── output.py        # Result serialization
├── utils/
│   └── logging.py
├── main.py              # Orchestration script
└── config.yaml          # Configuration (seeds, paths, thresholds)

tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_psm.py
    └── test_balance.py

data/
├── raw/                 # Downloaded raw files (checksummed)
└── processed/           # Cleaned, matched datasets
```

**Structure Decision**: Selected Option 1 (Single project) because the scope is a linear data analysis pipeline (Ingest -> Process -> Model -> Report) rather than a multi-service web application. This minimizes overhead for the CI runner and simplifies data sharing between steps.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Dual Strategy (PSM + Conditional DiD)** | The spec requires a fallback if PSM fails (FR-008). | A single PSM-only approach risks total analysis failure if balance cannot be achieved. DiD is included but gated by data availability to avoid methodological impossibility. |
| **Sensitivity Sweep** | Spec requires caliper sweep (FR-006). | A single-point estimate is insufficient to demonstrate robustness against arbitrary parameter choices, a key requirement for causal claims. |
| **Descriptive Scaling Module** | Reviewer feedback (Geoffrey West) requests investigation of scaling laws. | While not a causal requirement, ignoring the reviewer's specific mathematical critique would result in a rejected paper. A descriptive module is added to address this without compromising the causal core. |

## Pipeline Execution Flow

1.  **Step 1.0: Data Ingestion**: Fetch EIA RECS (official) and ACS (via `censusdata` API).
2.  **Step 1.1: Schema Validation**: **HALT** if `solar_installation`, `energy_cost`, or `income` are missing.
3.  **Step 1.2: Longitudinal Check**: If longitudinal fields (pre/post) are missing, set `did_available = False`.
4.  **Step 2.0: Preprocessing**: Filter low-income, winsorize, construct `treatment`.
5.  **Step 3.0: PSM**: Propensity score estimation, matching, balance check.
6.  **Step 4.0: Causal Estimation**: OLS on `log(energy_cost)`.
7.  **Step 5.0: DiD Fallback**: **Execute only if** `did_available == True` AND PSM balance failed.
8.  **Step 6.0: Scaling Analysis**: Descriptive tract-level analysis (excluded from causal claims).
9.  **Step 7.0: Reporting**: Generate results.

## Data Availability & Feasibility

- **CPU-First**: All operations (merge, PSM, OLS) are classical statistical methods executable on CPU. No GPU is required.
- **Memory**: The RECS dataset (typically ~50k-100k rows) fits comfortably within 7 GB RAM.
- **Data Mismatch**: If the verified EIA URL lacks required columns, the pipeline halts with a clear error message: "Required variables missing from verified EIA source. Cannot proceed with causal inference." The plan does not invent a substitute URL.
- **ACS Access**: Uses `censusdata` Python library to fetch tract-level median income programmatically, satisfying the spec's tract-level requirement without needing a static CSV.

## Statistical Rigor & Assumptions

- **Outcome Variable**: Primary causal outcome is `log(energy_cost)` to avoid mechanical correlation with income. `Energy Cost Burden` (Cost/Income) is calculated for descriptive reporting only.
- **Unconfoundedness**: Assumes that conditional on observed covariates, treatment assignment is independent of potential outcomes.
- **Common Support**: Observations with propensity scores near 0 or 1 will be excluded (FR-007).
- **Multiple Comparisons**: The sensitivity sweep (multiple calipers) will be reported descriptively.
- **Power**: A minimum of 50 adopters is required (SC-004).
- **Collinearity**: Income is used as a covariate in PSM but not in the final outcome regression (which uses `log(energy_cost)`), breaking the definitional link.