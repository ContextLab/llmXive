# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-02 | **Spec**: `specs/001-knot-complexity-analysis/spec.md`
**Input**: Feature specification from `/specs/001-knot-complexity-analysis/spec.md`

## Summary

**Primary Requirement**: Quantify the relationship between crossing number, braid index, and hyperbolic volume for prime knots with crossing number ≤13, with Phase 1 validation focused on crossing numbers ≤10.

**Technical Approach**:
- Download knot data from Knot Atlas (`https://katlas.org`) with verified fallback to Hoste-Thistlethwaite-Weeks tables via arXiv supplement (https://arxiv.org/abs/2402.02717) when primary source is unavailable.
- Primary invariants (crossing number, braid index, hyperbolic volume, alternating classification) are taken from tabulated values in Knot Atlas tables when present.
- Compute additional invariants (arc index, Seifert circle count, bridge number) **only** for records lacking tabulated values, using well-established algorithms (Birman-Menasco, Seifert's algorithm, Schubert's decomposition). This limits computational load while satisfying completeness requirements.
- Perform exploratory analysis stratified by alternating/non-alternating classification, fitting **separate** regression models for each class and an optional combined model that includes classification as a categorical predictor with interaction terms.
- Primary regression predictors are **crossing number** and **braid index**; additional invariants are used solely for descriptive exploratory plots and are **not** included in the main predictive models (addressing multicollinearity concerns).
- Create a Composite Complexity Score (default equal weights) as an **exploratory descriptive metric**; its correlation with hyperbolic volume is reported for insight but **not** used to validate regression models.
- Apply tie-breaking rules (braid word > DT code; lexicographically first DT code) consistently; validation performed via `code/validation/tie_breaking_validator.py`.

**Mathematical Bounds Acknowledgment**: Correlations between invariants are bounded by known mathematical relationships (MFW inequality relates braid index to crossing number; volume ≤ c × crossing number for hyperbolic knots). Observed correlations reflect these bounds rather than free empirical discovery.

**Generalizability Limitation**: Filtering to knots with valid hyperbolic volume (excluding torus/satellite knots) creates selection bias. Conclusions about "knot complexity" are explicitly restricted to the hyperbolic subclass only.

All work must comply with the project's 7 Constitutional Principles.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas, numpy, scipy, statsmodels, matplotlib, seaborn, requests, pyyaml, datasets (HuggingFace for any verified dataset sources)
**Storage**: Local file system (`data/`, `docs/`) with SHA-256 checksums per Constitution Principle III
**Testing**: pytest with contract tests against schema validation
**Target Platform**: Linux server (GitHub Actions compatible)
**Project Type**: research-analysis (CLI-driven data pipeline with Jupyter notebook outputs)
**Performance Goals**:
- Data download and invariant computation for **≤13** crossing number dataset (≈10,000 prime knots) within 2 h on a standard CI runner.
- **Only** the ≤10 subset must achieve **≥99%** completeness on required fields (SC-006).
- All other invariants may have lower completeness but must be flagged.
**Constraints**:
- Exponential backoff retry logic for API failures (initial 1 s, max 60 s, multiplier 2).
- Records with missing invariants are **flagged** (FR-011) not excluded.
- Tie-breaking validation script required (FR-013, SC-008).
- All transformations produce new files with documented derivations (Principle III).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| **I. Reproducibility** | ✅ Compliant | Random seeds pinned; external datasets fetched from canonical sources; `requirements.txt` at `code/`. |
| **II. Verified Accuracy** | ⚠️ Pending – BLOCKING GATE | Primary citations (Knot Atlas, KnotInfo) require runtime verification. Phase 0 research blocked until Reference-Validator confirms reachability. |
| **III. Data Hygiene** | ✅ Compliant | Checksums recorded; no in-place modifications. |
| **IV. Single Source of Truth** | ✅ Compliant | Figures/statistics trace to single data rows and code blocks. |
| **V. Versioning Discipline** | ✅ Compliant | Content hashes tracked; timestamps updated by Advancement-Evaluator. |
| **VI. Mathematical Invariant Consistency** | ✅ Compliant | Invariants verified against primary literature; discrepancies documented. |
| **VII. Statistical Significance Thresholds** | ✅ Compliant | All statistical claims include p-values, confidence intervals, and effect sizes; Pearson & Spearman reported. |

**GATE STATUS**: ⚠️ BLOCKED – Principle II requires runtime verification before Phase 0 research may proceed.

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│ ├── knot_record.schema.yaml
│ ├── invariants_dataset.schema.yaml
│ ├── regression_result.schema.yaml
│ └── composite_complexity_score.schema.yaml
└── tasks.md
```

### Source Code (repository root)

```text
code/
├── requirements.txt
├── download/
│ ├── __init__.py
│ ├── knot_atlas_downloader.py
│ └── retry_logic.py
├── compute/
│ ├── __init__.py
│ ├── invariant_calculator.py
│ └── validation.py
├── analysis/
│ ├── __init__.py
│ ├── exploratory.py
│ ├── regression.py
│ └── composite_score.py
├── validation/
│ └── tie_breaking_validator.py # validates tie-breaking rule consistency
├── docs/
│ └── reproducibility/
│ ├── checksums.md
│ ├── derivation_notes.md
│ ├── algorithm_validation.md
│ ├── validation_scope.md
│ ├── excluded_knots.md
│ ├── uncomputable_invariants.md
│ ├── tie_breaking_rules.md
│ └── validation_status.md
├── data/
│ ├── raw/
│ ├── processed/
│ └── plots/
└── tests/
 ├── contract/
 ├── integration/
 └── unit/
```

**Structure Decision**: Single project structure selected for research pipeline. All code under `code/` with clear separation of concerns (download, compute, analysis, validation). Documentation under `docs/reproducibility/` per Constitution Principle III. Data under `data/` with `raw/processed/plots/`.

## Phase 1 Implementation Tasks

| Task | Description | Output | Success Criterion |
|------|-------------|--------|-------------------|
| 1 | Download knot data from Knot Atlas with fallback | `data/raw/knot_atlas_full.parquet` | ≥99% records for ≤10 subset |
| 2 | Compute additional invariants for missing entries | `data/processed/knots_with_invariants.parquet` | ≥99% completeness on required fields |
| 3 | Run exploratory analysis (scatter plots) | `data/plots/crossing_vs_braid_*.png` | All plots generated at 1200×900 resolution |
| 4 | Fit regression models (linear, polynomial, logarithmic) | `data/processed/regression_result.json` | VIF scores computed; multicollinearity flagged |
| 5 | Compute composite complexity score | `data/processed/composite_score_results.json` | Pearson/Spearman correlations reported |
| 6 | **Validate tie-breaking rules** | `docs/reproducibility/validation_status.md` | **Validation report confirms consistent hierarchy application** |
| 7 | Generate reproducibility documentation | `docs/reproducibility/checksums.md`, etc. | All checksums recorded; derivation notes complete |

**Task 6 Detail**: The tie-breaking validator script (`code/validation/tie_breaking_validator.py`) must:
- Extract all knot records where multiple diagram representations exist
- Verify chosen representation follows hierarchy: braid word > DT code; lexicographically first DT code
- Write status report to `docs/reproducibility/validation_status.md` with pass/fail determination

## Phase 1 Scope Clarifications

- **Data Collection**: All prime knots with crossing number ≤13 are downloaded and stored (`data/raw/`).
- **Validated Subset**: Only knots with crossing number ≤10 are required to meet the **≥99%** completeness threshold (SC-006). Analyses reported in Phase 1 are limited to this validated subset. Data for 11-13 is retained for exploratory use only and will not be included in final Phase 1 conclusions.

## Statistical Modeling Notes

- **Primary Regression**: Uses crossing number and braid index as predictors; models are fit **separately** for alternating and non-alternating knots, and an optional combined model includes a categorical `alternating_classification` predictor with interaction terms.
- **Multicollinearity**: VIF scores are computed; predictors with VIF > 5 are flagged, but no additional invariants are added to the primary model to avoid multicollinearity.
- **Composite Complexity Score**: Calculated as a weighted sum (default 0.5 × crossing + 0.5 × braid). Its correlation with hyperbolic volume is reported **descriptively**; it is **not** used to validate the regression models.

## Data Quality Requirements

- **Required Fields**: `crossing_number`, `braid_index`, `hyperbolic_volume`, `alternating_classification`.
- **Completeness Threshold**: **≥99%** of records in the ≤10 subset must have all required fields populated (SC-006). Missing invariants are flagged via `missing_invariant_flags` (FR-011) and documented.
- **Classification Ambiguity**: Records with ambiguous classification are marked `unclassifiable` and excluded from stratified regression analyses (FR-012).

## Tie-Breaking Validation

- Validation script `code/validation/tie_breaking_validator.py` checks that for any knot with multiple diagram representations the chosen representation follows the documented hierarchy (braid word > DT code; lexicographically first DT code). The script is executed after invariant computation and before analysis.
- Output: `docs/reproducibility/validation_status.md` with detailed pass/fail determination and any violations logged.

## Performance & Resource Planning

- The exponential backoff logic ensures robust downloading even under intermittent network conditions.
- Invariant computation is limited to missing entries; for the full ≤13 dataset this keeps total runtime under the 2-hour target on standard CI hardware.
- Tabulated values are prioritized over algorithmic computation to address NP-hard feasibility concerns for arc index and bridge number algorithms.

## Mathematical Bounds Acknowledgment

All correlation analyses must acknowledge known mathematical constraints:
- **MFW Inequality**: Relates braid index to crossing number for most knots
- **Volume Bounds**: Hyperbolic volume ≤ c × crossing number for hyperbolic knots (c ≈ constant)
- **Bridge Number**: Bridge number ≤ crossing number for most knots
- **Implication**: Observed correlations reflect these mathematical bounds rather than free empirical discovery; this limitation must be explicitly stated in all results reporting.

## Generalizability Limitation

The analysis explicitly filters to hyperbolic knots only (torus and satellite knots excluded due to zero/undefined hyperbolic volume). All conclusions about "knot complexity" are restricted to the hyperbolic subclass. Generalizability to all prime knots is explicitly **not** claimed.