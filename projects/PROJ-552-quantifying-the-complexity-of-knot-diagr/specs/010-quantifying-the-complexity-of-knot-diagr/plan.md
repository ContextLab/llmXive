# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-07-02 | **Spec**: `specs/010-quantifying-the-complexity-of-knot-diagr/spec.md`
**Input**: Feature specification from `/specs/010-quantifying-the-complexity-of-knot-diagr/spec.md`

## Summary

This project implements a computational analysis pipeline to quantify the relationship between combinatorial invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) for the complete census of prime knots with crossing number ≤ 13. The approach prioritizes data integrity by using the `database-knotinfo` Python library as the verified, programmatic source for all knot data, ensuring reproducibility and avoiding fabrication. The pipeline filters for hyperbolic knots, performs descriptive statistical analysis (Spearman/Pearson correlations, regression models with orthogonalization), and rigorously documents edge cases, data quality, and reproducibility artifacts in compliance with the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `database-knotinfo`, `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `pyyaml`, `requests`  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `docs/reproducibility/`)  
**Testing**: `pytest` (unit tests for data parsing, invariant validation; integration tests for full pipeline)  
**Target Platform**: Linux (GitHub Actions runner: multi‑CPU configuration, 7GB RAM, 14GB disk)  
**Project Type**: CLI/Analysis Pipeline  
**Performance Goals**: Complete pipeline execution < 2 hours on standard CPU; data download < 10 minutes.  
**Constraints**: No local GPU required; all analysis is CPU-tractable (statistical regression, correlation).  
**Scale/Scope**: Total census count: a comprehensive set of prime knots (source: OEIS). Expected hyperbolic subset: [deferred] knots (excluding <100 torus/satellite knots).

> **Sample Size & Power Justification**: The analysis relies on a complete census of hyperbolic knots. This sample size is vastly sufficient for the proposed regression models (linear, polynomial, logarithmic) to detect non-trivial effect sizes, even in the presence of high multicollinearity. The primary risk is not statistical power (which is effectively infinite for a census) but the interpretability of individual coefficients. Therefore, the analysis focuses on the *joint* predictive power (R²) and *residual* patterns, rather than the statistical significance of individual coefficients.

**Dataset Breakdown**:
- **Total Prime Knots (≤13 crossings)**: [deferred] (Source: OEIS A002863).
- **Expected Hyperbolic Knots**: [deferred]. Torus and satellite knots are known to be a small minority (<100) for this crossing range.
- **Expected Excluded Count**: <100 (documented in `docs/reproducibility/excluded_knots.md`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ PASS | Pipeline uses `database-knotinfo` for deterministic data fetch; random seeds pinned in `code/`; checksums recorded in `data/`. |
| **II. Verified Accuracy** | ✅ PASS | All citations (KnotInfo, OEIS A002863) verified against primary sources; `database-knotinfo` acts as verified source for knot invariants. |
| **III. Data Hygiene** | ✅ PASS | Raw data preserved; derivations produce new files; SHA-256 checksums recorded for all data files. |
| **IV. Single Source of Truth** | ✅ PASS | All figures/statistics trace to `data/processed/knots_validated.csv`; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | ✅ PASS | Artifacts carry content hashes; `state/` updated on change. |
| **VI. Mathematical Invariant Consistency** | ✅ PASS | Added Phase 2.5 to explicitly verify computed invariants against definitions before inclusion, resolving the previous conflict. |
| **VII. Statistical Significance** | ✅ PASS | Census data exception applied: effect sizes (Cohen's d, r) reported; p-values excluded per Constitution Principle VII amendment. |

## Project Structure

### Documentation (this feature)

```text
specs/010-quantifying-the-complexity-of-knot-diagr/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── knot_record.schema.yaml       # SSoT for individual records
│   ├── invariants_dataset.schema.yaml # SSoT for aggregate dataset
│   └── regression_output.schema.yaml  # SSoT for model results
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── download/
│   └── knot_info_loader.py       # Fetches data via database-knotinfo
├── data/
│   ├── parser.py                 # Parses raw records to DataFrame
│   ├── validator.py              # Validates against contracts/knot_record.schema.yaml
│   └── filter.py                 # Filters for hyperbolic volume > 0
├── analysis/
│   ├── exploratory.py            # Scatter plots, stratified stats
│   ├── regression.py             # Model fitting (linear, poly, log) with orthogonalization
│   └── residual.py               # Residual analysis & family identification
├── reproducibility/
│   ├── checksums.py              # Generates SHA-256 for data files
│   ├── logs.py                   # Timestamped operation logs
│   ├── tie_breaking_validator.py # Validates tie-breaking consistency (SC-007)
│   └── plot_validator.py         # Validates plot resolution (SC-016)
└── main.py                       # Orchestrates pipeline

tests/
├── unit/
│   ├── test_parser.py
│   └── test_validator.py
└── integration/
    └── test_pipeline.py

docs/
├── reproducibility/
│   ├── data_quality_report.md
│   ├── validation_scope.md       # Required by SC-012
│   ├── excluded_knots.md
│   ├── random_seeds.md
│   ├── hyperbolic_volume_validation.md # Required by FR-013
│   ├── core_precision_consistency.md   # Required by SC-015
│   ├── tie_breaking_rules.md
│   ├── validation_status.md      # Required by SC-007
│   ├── plot_validation_report.md # Required by SC-016
│   ├── residual_analysis.md
│   └── multicollinearity_assessment.md
└── plots/                        # Generated PNGs (variable resolution)
```

**Schema SSoT Clarification**:
- `data-model.md` defines the logical entities (KnotRecord, InvariantsDataset).
- `contracts/knot_record.schema.yaml` is the physical validation artifact for individual records (used by `validator.py`).
- `contracts/invariants_dataset.schema.yaml` is the physical validation artifact for the aggregate dataset.
- `contracts/regression_output.schema.yaml` is the physical validation artifact for model results.
- This plan explicitly references `contracts/knot_record.schema.yaml` in Phase 0 to ensure the validation logic in `code/data/validator.py` maps to the correct schema file.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | N/A | Constitution Check passed without violations. |

## Phase Execution Order

1.  **Phase 0: Data Acquisition & Validation**
    *   Download data via `database-knotinfo` (verified source).
    *   Parse to `KnotRecord` objects; validate against `contracts/knot_record.schema.yaml` (explicitly referenced).
    *   Flag missing invariants (`missing_invariant_flags`) and data quality issues (`data_quality_flags`).
    *   Generate `data/raw/knot_atlas_raw.json` and `data/processed/knots_cleaned.csv`.

2.  **Phase 1: Filtering & Preprocessing**
    *   Filter for hyperbolic volume > 0 (exclude torus/satellite).
    *   Apply tie-breaking rules for diagram representations.
    *   **Step 1.3**: Generate `docs/reproducibility/validation_scope.md` (Required by SC-012: must contain crossing number ≤10 vs ≤13 distinction, justification, and counts table).
    *   Generate `docs/reproducibility/excluded_knots.md`.

3.  **Phase 2: Exploratory Analysis**
    *   **Step 2.1**: Generate scatter plots of **Crossing Number vs. Hyperbolic Volume** and **Braid Index vs. Hyperbolic Volume**, stratified by alternating/non-alternating (Primary focus per scientific soundness concern).
    *   **Step 2.2**: Compute descriptive statistics (mean diff, variance ratio, Cohen's d).
    *   **Step 2.4**: Run `code/reproducibility/tie_breaking_validator.py` to verify tie-breaking consistency; generate `docs/reproducibility/validation_status.md` (Required by SC-007).
    *   **Step 2.5**: Run `code/reproducibility/plot_validator.py` to verify plot resolution (high definition) and metadata; generate `docs/reproducibility/plot_validation_report.md` (Required by SC-016).
    *   Generate `docs/reproducibility/data_quality_report.md`.

4.  **Phase 2.5: Computed Invariant Verification** (NEW: Addresses Constitution Principle VI)
    *   Compute additional invariants (arc index, Seifert circle count, bridge number) for the subset where diagram representations allow.
    *   Verify computed values against established mathematical definitions and KnotInfo (where available).
    *   Document discrepancies and derivation notes in `data/`.
    *   Generate `docs/reproducibility/computed_invariant_verification.md`.

5.  **Phase 3: Regression & Modeling**
    *   **Step 3.1**: Orthogonalize the braid index predictor with respect to crossing number to address multicollinearity (Methodology concern).
    *   Fit linear, polynomial, and logarithmic models using the orthogonalized predictors.
    *   Compute VIF to assess multicollinearity (expected to be high; reported as diagnostic only).
    *   **Step 3.2**: Perform residual analysis using **Median Absolute Deviation (MAD)** scaled to standard deviation (approximately 1.5 times the Median Absolute Deviation (MAD)) for outlier detection (≥ 2 sigma threshold) to ensure robustness (Methodology concern).
    *   Identify specific hyperbolic knot families that deviate significantly.
    *   **Mathematical Constraint Acknowledgment**: Explicitly state that individual coefficients are descriptive of the braid index ≤ crossing number constraint, not independent effects. Focus on R² and residual patterns.
    *   **Mathematical Fact vs. Statistical Inference**: Clarify that the analysis confirms known bounds and quantifies deviations, rather than testing for the existence of the relationship.
    *   Generate `docs/reproducibility/multicollinearity_assessment.md` and `residual_analysis.md`.

6.  **Phase 4: Reproducibility & Reporting**
    *   **Step 4.3**: Perform Core Invariant Precision Consistency Check (Crossing Number/Braid Index) against KnotInfo for the ≤10 crossing subset; generate `docs/reproducibility/core_precision_consistency.md` (Required by SC-015).
    *   **Step 4.4**: Perform Hyperbolic Volume Consistency Check against KnotInfo; generate `docs/reproducibility/hyperbolic_volume_validation.md` (Required by FR-013).
    *   Generate checksums, logs, and derivation notes.
    *   Finalize `docs/reproducibility/` artifacts.
