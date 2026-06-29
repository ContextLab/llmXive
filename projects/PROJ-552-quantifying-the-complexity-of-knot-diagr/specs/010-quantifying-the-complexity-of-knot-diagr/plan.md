# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-25 | **Spec**: specs/001-knot-complexity-analysis/spec.md
**Input**: Feature specification from specs/001-knot-complexity-analysis/spec.md

## Summary

This project quantifies the relationship between combinatorial invariants (crossing number, braid index) and geometric complexity (hyperbolic volume) for hyperbolic prime knots with crossing number ≤ 13. The technical approach involves downloading knot data from Knot Atlas, validating invariant precision, fitting multiple regression models, and documenting all transformations for reproducibility. Phase 1 validation focuses on crossing number ≤ 10, while knots with crossing numbers 11‑13 are included as exploratory data; results from this range will be reported separately with an explicit disclaimer.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas, numpy, scipy, scikit-learn, matplotlib, requests, pyyaml
**Storage**: Local files (CSV/JSON) under `data/` directory
**Testing**: pytest with contract validation against YAML schemas
**Target Platform**: Linux (GitHub Actions free‑tier runner)
**Performance Goals**: Complete analysis within 6 hours on 2 CPU cores, ~7 GB RAM, ~14 GB disk
**Constraints**: No GPU/CUDA; CPU‑only execution; data subset to fit available memory
**Scale/Scope**: ~9988 prime knots at crossing number ≤ 13 (source: OEIS A002863)

> Domain‑specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re‑check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| I. Reproducibility | PASS | Random seeds pinned; checksums recorded under `data/`; all transformations documented |
| II. Verified Accuracy | PASS | Citations validated against primary sources; Knot Atlas referenced by name (no URL fabricated per verified datasets block) |
| III. Data Hygiene | PASS | SHA‑256 checksums for all data files; no in‑place modifications; derivations produce new files |
| IV. Single Source of Truth | PASS | All figures/statistics trace to `data/` rows and `code/` blocks |
| V. Versioning Discipline | PASS | Content hashes for all artifacts; updated_at timestamps maintained |
| VI. Mathematical Invariant Consistency | PASS | Invariants verified against established definitions; discrepancies documented |
| VII. Statistical Significance | PASS | Census‑data exception applied; effect sizes reported instead of p‑values for complete enumeration |

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── knot_record.schema.yaml # Authoritative record schema
│ ├── dataset.schema.yaml # Dataset schema (references knot_record.schema.yaml)
│ ├── regression_model.schema.yaml # Canonical regression model schema
│ ├── regression_output.schema.yaml # Regression output schema
│ └── validation_scope.md # Completeness benchmark (≤ 10 vs ≤ 13)
│ └── tie_breaking_validator.py # Validation script (SC‑007)
│ └──... (other reproducibility docs)
└── docs/
 └── reproducibility/
 ├── validation_scope.md # Completeness benchmark (≤ 10 vs ≤ 13)
 ├── data_quality_report.md
 ├── invariant_coverage.md
 ├── excluded_knots.md
 ├── hyperbolic_volume_validation.md
 ├── core_precision_consistency.md
 ├── multicolinarity_assessment.md
 ├── residual_analysis.md
 ├── tie_breaking_rules.md
 ├── tie_breaking_validator.py # Validation script (SC‑007)
 ├── missing_invariants.md
 ├── random_seeds.md
 └── logs/
 └── *.log
```

### Source Code (repository root)

```text
code/
├── download/
│ └── knot_atlas_loader.py # Implements exponential back‑off (initial = 1 s, multiplier = 2, max = 32 s) and caches partial results after 3 failures (FR‑008)
├── data/
│ ├── parser.py
│ └── validator.py # Enforces null‑percentage ≤ 5 % (SC‑001) and aborts pipeline on violation
├── analysis/
│ ├── exploratory.py
│ ├── regression.py
│ └── residual_analysis.py
├── filter/
│ └── hyperbolic_filter.py
└── reproducibility/
 ├── checksum_generator.py
 └── tie_breaking_validator.py # Returns exit code 0 on success (SC‑007)
```

### Data

```text
data/
├── raw/
│ └── knot_atlas_raw.json
├── processed/
│ ├── knots_cleaned.csv
│ ├── knots_validated.csv
│ └── knots_hyperbolic.csv
└── plots/
 └── *.png
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | All requirements can be met with single‑project structure | N/A |

## Phase 1 Validation Staging

* **Validated Findings (Crossing ≤ 10)** – Full completeness benchmark documented in `docs/reproducibility/validation_scope.md`. All required invariants must have ≤ 5 % nulls, ≥ 99 % format pass rate, and zero duplicates (SC‑001, SC‑005).
* **Exploratory Findings (Crossing 11‑13)** – Data are downloaded and processed, but completeness is not formally validated. Findings from this range will be presented in a separate **Exploratory Findings** section of the manuscript, labelled as exploratory and interpreted with caution. They will not be used for validated conclusions.

## Data Acquisition & Robustness (FR‑001, FR‑008)

* HTTP fetch from Knot Atlas (` Name or service not known)"))]) with exponential back‑off (initial = 1 s, multiplier = 2, max = 32 s).
* After three consecutive failures, partial results are cached to `data/raw/` enabling resumable downloads.
* Retry logic satisfies SC‑004 and ensures the full census of prime knots with crossing number ≤ 13 (OEIS A002863 count = 9988) is downloaded. Completeness is verified by comparing record count against this enumeration.

## Data Validation (FR‑002, SC‑001, SC‑005)

* Null‑percentage threshold: any required field > 5 % nulls aborts the pipeline with a clear error (enforced by `code/data/validator.py`).
* Format validation pass rate must be ≥ 99 %; duplicate count must be 0.
* All checks are logged in `docs/reproducibility/data_quality_report.md`.

## Core Invariant Precision (FR‑013, SC‑015)

* Cross‑check crossing number, braid index, and hyperbolic volume against KnotInfo.
* Requirement: ≥ 90 % of records must match within a tolerance of **1e‑6**.
* **Action if coverage < 90 %**: a warning is recorded in `core_precision_consistency.md`; the affected records remain in the dataset but the results are flagged as exploratory and not treated as validated evidence.

## Tie‑Breaking Rules (FR‑011, SC‑007)

* Preference order: braid word > Dowker‑Thistlethwaite (DT) code; if multiple DT codes, choose lexicographically first.
* Validation script `docs/reproducibility/tie_breaking_validator.py` enforces these rules (must exit 0).

## Statistical Methodology (FR‑006, FR‑005, SC‑006, SC‑011)

### Correlation Analysis (FR‑006, SC‑006)

| Metric | Method | Notes |
|--------|--------|-------|
| Primary | Spearman correlation | Discrete invariants |
| Supplementary | Pearson correlation | Reported for completeness |
| Effect Size | r or r² | Reported; no p‑values for census data |

### Regression Models (FR‑005, SC‑002)

| Model Type | Form | Selection Criterion |
|------------|------|---------------------|
| Linear | y = β₀ + β₁x₁ + β₂x₂ + ε | R², AIC/BIC, MAE |
| Polynomial (degree 2) | y = β₀ + β₁x₁ + β₂x₂ + β₃x₁² + β₄x₂² + β₅x₁x₂ + ε | R², AIC/BIC, MAE |
| Logarithmic | y = β₀ + β₁log(x₁) + β₂log(x₂) + ε | R², AIC/BIC, MAE |

*Model selection is based solely on goodness‑of‑fit metrics; no statistical power or significance testing is performed (census‑data exception).*

### Multicollinearity (FR‑005)

* VIF is computed for all joint models. High VIF values are **expected** because braid index ≤ crossing number by definition. **Importantly, high VIF does not invalidate the descriptive analysis**; it merely reflects the definitional relationship.

### Residual Analysis (FR‑005, SC‑011)

* Families with residuals ≥ 2 SD are identified and reported **descriptively** as illustrations of finite‑population structure (e.g., pretzel, hyperbolic non‑alternating families). These deviations characterize the population and are **not** treated as outliers in a predictive sense.

### Group Comparison (FR‑004, SC‑009)

| Metric | Calculation | Notes |
|--------|-------------|-------|
| Mean Difference | μ_alternating − μ_non‑alternating | Descriptive |
| Variance Ratio | σ²_alternating / σ²_non‑alternating | Descriptive |
| Cohen’s d | (μ₁ − μ₂) / σ_pooled | Primary effect‑size measure |

*No inferential tests are performed; results are purely descriptive.*

## Negative Result Definition

A *negative result* is defined as observing **R² ≤ 0.05** for **all** fitted models, indicating that neither crossing number nor braid index explains a non‑trivial proportion of variance in hyperbolic volume.

## Reproducibility Documentation (FR‑007, SC‑003)

All required artifacts will be generated:

| Artifact | Location | Contents |
|----------|----------|----------|
| SHA‑256 Checksums | `data/` | `checksums.sha256` |
| Derivation Notes | `docs/reproducibility/` | Formula citations, step‑by‑step transformation logic |
| Timestamped Logs | `docs/reproducibility/logs/` | `*.log` with operation details |
| Random Seeds | `docs/reproducibility/random_seeds.md` | Seed values |
| Data Quality Report | `docs/reproducibility/data_quality_report.md` | Null percentages, format pass rate, duplicate count |
| Validation Scope | `docs/reproducibility/validation_scope.md` | Completeness benchmark (≤ 10 vs ≤ 13) |
| Invariant Coverage | `docs/reproducibility/invariant_coverage.md` | Per‑invariant coverage stats |
| Excluded Knots | `docs/reproducibility/excluded_knots.md` | Torus/satellite knots filtered per FR‑012 |
| Hyperbolic Volume Validation | `docs/reproducibility/hyperbolic_volume_validation.md` | Consistency check against KnotInfo |
| Core Precision Consistency | `docs/reproducibility/core_precision_consistency.md` | Braid‑index precision validation |
| Multicollinearity Assessment | `docs/reproducibility/multicolinarity_assessment.md` | VIF values |
| Residual Analysis | `docs/reproducibility/residual_analysis.md` | Families deviating ≥ 2 SD |
| Tie‑Breaking Rules | `docs/reproducibility/tie_breaking_rules.md` | Documented rules |
| Tie‑Breaking Validator | `docs/reproducibility/tie_breaking_validator.py` | Validation script (SC‑007) |
| Missing Invariants | `docs/reproducibility/missing_invariants.md` | Counts and documentation of records excluded due to missing invariants |
| Random Seeds | `docs/reproducibility/random_seeds.md` | Seed values |
| Logs | `docs/reproducibility/logs/*.log` | Detailed operation logs |

## Compute Feasibility (CPU‑Only CI)

* **Memory**: Data subset ≤ 7 GB RAM; processing done in chunks if needed.
* **Disk**: Raw + processed files are on the order of a few hundred megabytes.; well within 14 GB limit.
* **No GPU**: All libraries are CPU‑only (scikit‑learn, pandas, etc.).
* **No Deep Learning**: Classical regression models only.
