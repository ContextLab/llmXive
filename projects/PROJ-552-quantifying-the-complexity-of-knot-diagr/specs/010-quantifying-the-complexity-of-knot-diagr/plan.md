# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-12 | **Spec**: `specs/001-knot-complexity-analysis/spec.md`
**Input**: Feature specification from `specs/001-knot-complexity-analysis/spec.md`

## Summary

This project quantifies the relationship between combinatorial invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) across the complete census of hyperbolic prime knots with crossing number ≤ 13. The approach involves downloading the Knot Atlas dataset, validating data quality against KnotInfo reference values, filtering for hyperbolic knots (volume > 0), and performing descriptive statistical analysis. 

**Critical Methodological Revision**: To address scientific soundness concerns regarding the definitional constraint `braid_index ≤ crossing_number`, the analysis will NOT treat them as independent predictors in a joint regression. Instead, the study will:
1. Establish a baseline model using **Crossing Number (c)** alone to predict Volume.
2. Analyze **Braid Efficiency (b/c)** as a derived metric to explain residuals and geometric deviations.
3. Perform residual analysis against the c-only baseline to identify genuine geometric anomalies.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `requests`, `pyyaml`, `seaborn`  
**Storage**: Local file system (`data/raw`, `data/processed`, `docs/reproducibility`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM)  
**Project Type**: Computational research / Data analysis  
**Performance Goals**: Complete pipeline execution ≤ 6 hours on CPU-only runner  
**Constraints**: No GPU, no deep learning, memory usage < 7GB, disk usage < 14GB  
**Scale/Scope**: ~9,988 prime knots (source: OEIS A002863, https://oeis.org/A002863), filtered to hyperbolic subset

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Satisfied via pinned random seeds in code, checksums for all data files, and version-controlled dependencies in `requirements.txt`. All results reproducible by re-running `code/` against `data/` on fresh runner.
- **Principle II (Verified Accuracy)**: Satisfied via Reference-Validator Agent checking all citations against primary sources (Knot Atlas, KnotInfo, OEIS) before contributing review points.
- **Principle III (Data Hygiene)**: Satisfied via SHA-256 checksums recorded under `data/`, no in-place modifications, new files for all transformations, and PII scan passing.
- **Principle IV (Single Source of Truth)**: Satisfied via traceability of all figures/statistics to exactly one row in `data/` and one block in `code/`.
- **Principle V (Versioning Discipline)**: Satisfied via content hashes for all artifacts and `updated_at` timestamp updates in state file.
- **Principle VI (Mathematical Invariant Consistency)**: Satisfied via verification of computed invariants against primary literature definitions and documentation of discrepancies in `data/`.
- **Principle VII (Statistical Significance)**: Satisfied via effect size reporting (Cohen's d, r, r²) for all statistical claims. Census-data exception applied: p-values not reported for complete enumeration; descriptive statistics used instead.

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── download/
│   └── knot_atlas_loader.py      # Data download with retry logic (FR-008)
├── data/
│   ├── parser.py                 # Data parsing and cleaning (FR-002)
│   ├── validator.py              # Data validation against schemas (FR-002, SC-013)
│   └── quality_checker.py        # Data quality metrics calculation (SC-013)
├── analysis/
│   ├── exploratory.py            # EDA, scatter plots (FR-004)
│   ├── regression.py             # Model fitting (c-only baseline, b/c efficiency) (FR-005)
│   └── residual_analysis.py      # Residual deviation detection (FR-005, SC-011)
├── reproducibility/
│   ├── checksums.py              # SHA-256 generation (FR-007)
│   └── logs.py                   # Timestamped logging (FR-007)
└── main.py                       # Pipeline orchestration

data/
├── raw/
│   └── knot_atlas_raw.json       # Raw downloaded data
├── processed/
│   ├── knots_cleaned.csv         # Cleaned dataset
│   ├── knots_validated.csv       # Validated dataset with flags
│   └── plots/                    # Generated PNG plots
└── checksums/
    └── manifest.json             # SHA-256 checksums

docs/reproducibility/
├── data_quality_report.md        # Data quality metrics (SC-013)
├── data_fabrication_audit.md     # Audit of first 100 rows (Task T091 deliverable)
├── validation_scope.md           # Phase 1 vs. exploratory scope (Assumptions)
├── excluded_knots.md             # Filtered knots (FR-012)
├── hyperbolic_volume_validation.md # Consistency check vs. KnotInfo (FR-013)
├── core_precision_consistency.md # Core invariant validation (SC-015)
├── residual_analysis.md          # Deviation families (SC-011)
├── tie_breaking_rules.md         # Tie-breaking documentation (FR-011)
├── multicolinearity_assessment.md # VIF analysis (FR-005)
├── random_seeds.md               # Seed values (FR-007)
├── invariant_coverage.md         # Invariant availability counts (SC-008)
├── plot_validation_report.md     # Plot quality checks (SC-016)
└── validation_status.md          # Overall validation status (SC-007)
```

**Structure Decision**: Single-project structure chosen for simplicity and alignment with computational research workflow. All code modules are organized by function (download, data, analysis, reproducibility) to ensure clear separation of concerns and maintainability.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | All requirements are met within single-project structure. | N/A |

## Data Quality & Validation (Task T091 Resolution)

**Task T091: Investigate and Fix Data Ingestion**

To ensure data integrity and provide a concrete deliverable for the implementation step:

1.  **Deliverable**: Generate `docs/reproducibility/data_fabrication_audit.md`.
2.  **Content Requirements**:
    -   Display the first 100 rows of the `knots_validated.csv` dataset.
    -   Explicitly verify that core fields (`crossing_number`, `braid_index`, `hyperbolic_volume`) contain **zero nulls**.
    -   Verify that `hyperbolic_volume` > 0 for all included records (post-filter).
    -   Verify that `braid_index` ≤ `crossing_number` for all records (mathematical constraint check).
3.  **Pass/Fail Criteria**:
 - **Pass**: 0 nulls in core fields for the first 100 rows AND [deferred] format compliance AND [deferred] constraint compliance (b ≤ c).
    -   **Fail**: Any nulls found, any format failure, or any violation of `b ≤ c`.
4.  **Action on Failure**: If criteria are not met, the pipeline must halt, and the error must be logged in `docs/reproducibility/logs.py` with a detailed report of the specific rows and fields failing validation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Satisfied via pinned random seeds in code, checksums for all data files, and version-controlled dependencies in `requirements.txt`. All results reproducible by re-running `code/` against `data/` on fresh runner.
- **Principle II (Verified Accuracy)**: Satisfied via Reference-Validator Agent checking all citations against primary sources (Knot Atlas, KnotInfo, OEIS) before contributing review points.
- **Principle III (Data Hygiene)**: Satisfied via SHA-256 checksums recorded under `data/`, no in-place modifications, new files for all transformations, and PII scan passing.
- **Principle IV (Single Source of Truth)**: Satisfied via traceability of all figures/statistics to exactly one row in `data/` and one block in `code/`.
- **Principle V (Versioning Discipline)**: Satisfied via content hashes for all artifacts and `updated_at` timestamp updates in state file.
- **Principle VI (Mathematical Invariant Consistency)**: Satisfied via verification of computed invariants against primary literature definitions and documentation of discrepancies in `data/`.
- **Principle VII (Statistical Significance)**: Satisfied via effect size reporting (Cohen's d, r, r²) for all statistical claims. Census-data exception applied: p-values not reported for complete enumeration; descriptive statistics used instead.