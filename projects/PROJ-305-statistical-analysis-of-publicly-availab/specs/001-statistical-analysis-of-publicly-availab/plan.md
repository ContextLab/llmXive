# Implementation Plan: Statistical Analysis of Publicly Available COVID-19 Vaccine Adverse Event Reports

**Branch**: `001-statistical-analysis-covid-vaers` | **Date**: 2026-07-05 | **Spec**: `specs/001-statistical-analysis-covid-vaers/spec.md`
**Input**: Feature specification from `specs/001-statistical-analysis-covid-vaers/spec.md`

## Summary

This project implements a reproducible, CPU-only statistical pipeline to analyze VAERS (Vaccine Adverse Event Reporting System) data from 2020-2023. The primary requirement is to detect safety signals by calculating Reporting Odds Ratios (ROR), Proportional Reporting Ratios (PRR), and Information Components (IC) for System Organ Classes (SOCs), comparing COVID-19 vaccines against a **Non-COVID, Non-Flu** baseline to minimize confounding. The technical approach involves downloading verified datasets, cleaning and merging records by `VAX_TYPE`, mapping MedDRA codes to SOCs, and performing disproportionality analysis with Benjamini-Hochberg correction for multiple testing. All analysis is constrained to run on free-tier GitHub Actions runners with limited CPU and RAM resources without GPU dependencies. A critical **Schema Validation Gate** ensures the dataset contains required fields before proceeding, preventing fatal downstream failures.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `requests`, `pyarrow` (for parquet), `matplotlib`  
**Storage**: Local CSV/Parquet files in `data/` (raw) and `data/processed/` (cleaned); results in `output/`  
**Testing**: `pytest` with `pytest-cov` for coverage, including memory profiling tests.  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data analysis pipeline / CLI tool  
**Performance Goals**: Complete pipeline execution < 6 hours; memory usage < 7 GB RAM (enforced via chunked processing).  
**Constraints**: No GPU; no external API calls during analysis (data must be local); strict reproducibility via pinned seeds and checksums.  
**Scale/Scope**: ~-2023 VAERS data (estimated 500k-1M rows); ~30 SOCs.

> **Dataset Validation**: The pipeline halts immediately if the verified dataset lacks `VAX_TYPE` or MedDRA/SOC columns (Phase 1.2).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | Plan mandates pinned seeds, checksummed data, and isolated `requirements.txt`. |
| II. Verified Accuracy | PASS | Plan restricts dataset citations to the "Verified datasets" block only and includes a **Schema Validation Gate** to ensure data usability. |
| III. Data Hygiene | PASS | Plan requires raw data preservation, checksumming, and no in-place modification. |
| IV. Single Source of Truth | PASS | All figures/stats trace to `data/` rows and `code/` blocks; no hand-typed numbers. |
| V. Versioning Discipline | PASS | Content hashes for artifacts will be managed by the Advancement-Evaluator. |
| VI. Epidemiological Signal Disproportionality | PASS | Methodology explicitly uses ROR/PRR/IC comparing vaccine types vs. **Non-COVID, Non-Flu** baseline, and includes **Flu-only** sensitivity analysis. |
| VII. Null-Hypothesis Equivalence | PASS | Plan treats null results as valid contributions; no "failure" framing for non-significant signals. |

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-analysis-covid-vaers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── signal.schema.yaml
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Fetches and checksums raw data
│   ├── clean.py             # Filters, merges, maps MedDRA->SOC
│   └── validate.py          # Checks data integrity against dataset.schema.yaml
├── analysis/
│   ├── disproportionality.py # ROR, PRR, IC calculations
│   ├── temporal.py          # Weekly reporting profiles
│   └── sensitivity.py       # Flu-only baseline comparison
├── utils/
│   ├── config.py            # Paths, seeds, thresholds
│   └── plots.py             # Visualization helpers
├── main.py                  # Pipeline orchestrator
└── requirements.txt         # Pinned dependencies

tests/
├── contract/
│   ├── test_dataset_schema.py
│   └── test_signal_schema.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_disproportionality.py
    ├── test_temporal.py
    └── test_memory_profile.py  # Validates SC-004
```

**Structure Decision**: Single project structure selected for simplicity and alignment with the data-analysis nature of the project. All code resides under `src/` with clear separation of concerns (data, analysis, utils). Tests mirror this structure.

## Implementation Phases

### Phase 0: Data Acquisition & Schema Validation (Critical Gate)
1. **Download**: Fetch `chrisvoncsefalvay/vaers-outcomes` (or specified verified source) to `data/raw/`.
2. **Checksum**: Verify SHA256 hash against recorded value.
3. **Schema Validation (Blocking)**: Run `src/data/validate.py` against `contracts/dataset.schema.yaml`.
   - **Check**: Verify presence of `VAX_TYPE`, `SOC_CODE` (or `LLT`), `REPT_DATE`.
   - **Action**: If missing, **HALT** with error code `E_SCHEMA_MISSING`. Do not proceed to Phase 1.
   - **Action**: If present, proceed.

### Phase 1: Data Cleaning & Baseline Construction
1. **Filter**: Separate data into `COVID-19`, `Non-COVID, Non-Flu` (Baseline), and `Flu-only` (Sensitivity).
   - **Baseline Definition**: `VAX_TYPE` != "COVID-19" AND `VAX_TYPE` does NOT contain "Influenza".
2. **Map MedDRA**: Map available codes to SOC using the embedded mapping table.
3. **Handle Missing**: Exclude records with missing `SOC` or `REPT_DATE`.
4. **Memory Check**: Log RAM usage; if > 5 GB, enable chunked processing for subsequent steps.

### Phase 2: Disproportionality Analysis
1. **Contingency Tables**: Generate 2x2 tables for each SOC (Event/No Event vs. COVID/Non-COVID).
2. **Continuity Correction**: Apply a small constant additive smoothing factor to cells with zero counts to prevent undefined statistical measures..
3. **Calculate Metrics**: Compute ROR, PRR, IC with confidence intervals.
4. **Multiple Testing**: Apply Benjamini-Hochberg correction to p-values.
5. **Signal Validation**: Flag signals meeting a majority of metric thresholds

The research question, method, and references remain unchanged as per the planning document requirements. (FR-005).

### Phase 3: Temporal & Sensitivity Analysis
1. **Temporal Profile**: Generate weekly counts for top 5 signals relative to median `REPT_DATE`.
   - **Label**: Explicitly label as "Reporting Time" (not "Post-Vaccination Time").
   - **Limitation**: Include note that `REPT_DATE` is a biased proxy for event onset.
2. **Sensitivity**: Compare "Non-COVID, Non-Flu" baseline vs. "Flu-only" baseline for top 5 signals.
3. **Reporting Propensity**: Add disclaimer that metrics reflect reporting intensity, not absolute risk.

### Phase 4: Memory Profiling & Constraint Enforcement (SC-004)
1. **Profile**: Measure peak RAM usage during Phase 2 and 3.
2. **Validate**: Ensure usage < 7 GB. If exceeded, log failure and halt.
3. **Report**: Include memory profile in `output/report.md`.

### Phase 5: Output & Validation (SC-005)
1. **Generate**: Create `signals.csv`, `temporal_profiles/`, `sensitivity_analysis.csv`.
2. **Validate SC-005**: Calculate proportion of signals meeting 2/3 rule.
3. **Final Report**: Compile `output/report.md` with all metrics, limitations, and validation results.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations identified. | N/A |

## Risk Management

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Missing Schema** | **Fatal** | **Phase 0 Schema Validation Gate** halts execution immediately. |
| **Memory Exceeded** | High | **Phase 4** enforces < 7 GB limit; chunked processing enabled if needed. |
| **Reporting Bias** | Medium | Explicitly framed as "Reporting Time" and "Reporting Propensity" in output. |
| **Confounding Baseline** | High | Baseline redefined to "Non-COVID, Non-Flu" to ensure independence. |