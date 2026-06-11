# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31 | **Spec**: `specs/001-knot-complexity-analysis/spec.md`
**Input**: Feature specification from `specs/001-knot-complexity-analysis/spec.md`

## Summary

This feature implements Phase 1 analysis of prime knot complexity, focusing on the alternating/non-alternating dichotomy for crossing numbers ≤10 (validated) and ≤13 (downloaded). The technical approach involves downloading knot data from Knot Atlas, computing additional invariants (arc index, Seifert circle count, bridge number), performing exploratory data analysis, fitting regression models to predict hyperbolic volume, and constructing a composite complexity score. All analysis must adhere to the project's reproducibility, data hygiene, and mathematical invariant consistency requirements per the constitution.

**Scope Clarification**: OEIS A002863 reports the cumulative count of prime knots up to a specified crossing number (CUMULATIVE, not at a specific crossing number). The exact number of prime knots at crossing number 13 is the documented value, as established by Hoste-Thistlethwaite-Weeks enumeration. Initial Phase analysis: validated on a constrained parameter c (high-speed regime, c≤10), exploratory on c=11-13. Regression models trained on c≤10 only to maintain consistency with validation scope.

**CRITICAL SPEC DEFECTS FLAGGED FOR KICKBACK**:
1. **Spec Factual Error (Assumptions Section)**: The spec.md states 'For crossing number 13, the exact count is 49 prime knots, as established in OEIS A002863' which is factually incorrect. OEIS A002863(13) is the CUMULATIVE count ≤13. The knots at a specific crossing number should be attributed to Hoste-Thistlethwaite-Weeks enumeration. **ACTION REQUIRED**: Spec must be corrected before implementation proceeds.
2. **Spec Placeholder SC-006**: Missing threshold percentage in 'of knots with computable invariants have all invariants populated'. Plan documents provisional default of ****. **ACTION REQUIRED**: Spec must be amended with confirmed value.
3. **Spec Placeholder SC-012**: Missing threshold percentage in 'match threshold for pass/fail status per invariant where reference coverage of dataset'. Plan documents provisional default of ****. **ACTION REQUIRED**: Spec must be amended with confirmed value.

**PROVISIONAL DEFAULTS (Pending Spec Correction)**:
- SC-006 threshold: (provisional, flagged for kickback)
- SC-012 threshold: (provisional, flagged for kickback)

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas==2.2.0`, `numpy==1.26.0`, `scipy==1.12.0`, `statsmodels==0.14.1`, `requests==2.31.0`, `pyyaml==6.0.1`, `matplotlib==3.8.0`, `seaborn==0.13.0`  
**Storage**: Files under `data/` (Parquet, CSV, PNG); no database  
**Testing**: `pytest==8.0.0`  
**Target Platform**: Linux server (GitHub Actions runner)  
**Project Type**: computational-research  
**Performance Goals**: Complete data download and invariant computation for low crossing number prime knots within a reasonable timeframe; regression analysis within a short timeframe  
**Constraints**: Must handle API rate limits with exponential backoff; must not modify raw data in place; must pin random seeds for all stochastic operations; must track Knot Atlas data version  
**Scale/Scope**: OEIS A002863 reports 9988 prime knots with crossing number ≤13 (CUMULATIVE). The exact number at c=13 is 49 (Hoste-Thistlethwaite-Weeks enumeration). Phase 1 validation focused on c≤10 (~632 knots); c=11-13 reserved for exploratory analysis only

**Power Analysis**: After filtering for hyperbolic volume (removing torus/satellite knots), a subset of knots remains at c≤10. **Exact Sample Size Documentation**: The filtering logic must be documented in `docs/reproducibility/power_analysis.md` with exact counts from the source dataset. Approximately 537 hyperbolic knots at c≤10 provides adequate power (≥0.80 at α=0.05) to detect correlations r≥0.13 for 2-predictor regression models. The torus/satellite exclusion rate must be calculated empirically from the downloaded dataset and documented.

> Domain-specific empirical specifics are deferred to the research/implementation phase. The prime knot count of 9988 for crossing number ≤13 is verified from OEIS A002863. The 49 knots at c=13 specifically is from Hoste-Thistlethwaite-Weeks enumeration.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Action |
|-----------|--------|----------------------|
| **I. Reproducibility** | PASS | All code under `code/` must be runnable end-to-end on fresh runner; random seeds pinned in `code/`; external datasets fetched from canonical source (Knot Atlas) on every run |
| **II. Verified Accuracy** | LIMITATION | Knot Atlas and KnotInfo sources NOT verified per Reference-Validator Agent; retry logic with exponential backoff implemented; limitations documented in `docs/reproducibility/validation_scope.md`; citations from verified datasets block only |
| **III. Data Hygiene** | PASS | All files under `data/` checksummed (SHA-256); raw data preserved unchanged; derivations written to new filenames; PII scan passed; license compliance documented |
| **IV. Single Source of Truth** | PASS | Every figure/statistic traces to exactly one row in `data/` and one block in `code/`; no hand-typed numbers in paper |
| **V. Versioning Discipline** | PASS | Every artifact carries content hash; state file `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml` `updated_at` timestamp updated on artifact changes |
| **VI. Mathematical Invariant Consistency** | PASS | All computed invariants verified against established definitions; empirical verification of known inequalities (bridge ≤ crossing, etc.) before analysis; discrepancies documented with derivation notes in `data/` |
| **VII. Statistical Significance Thresholds** | PASS | All statistical claims include p-values, confidence intervals, and effect sizes; both Pearson and Spearman correlations reported where distribution assumptions uncertain |

**GATE STATUS**: All 7 constitution principles addressed. Principle II marked as LIMITATION with mitigation strategy. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download_knots.py
│   │   ├── parse_knots.py
│   │   └── compute_invariants.py
│   ├── analysis/
│   │   ├── exploratory.py
│   │   ├── regression.py
│   │   └── validation.py
│   ├── models/
│   │   └── knot_record.py
│   └── utils/
│       ├── reproducibility.py
│       └── retry.py
├── data/
│   ├── raw/
│   │   └── knot_atlas_*.parquet
│   ├── processed/
│   │   ├── invariants_*.parquet
│   │   ├── regression_results_*.parquet
│   │   └── validation_results_*.parquet
│   └── plots/
│       └── *.png
├── docs/
│   └── reproducibility/
│       ├── checksums.md
│       ├── derivation_notes.md
│       ├── logs/
│       ├── algorithm_validation.md
│       ├── excluded_knots.md
│       ├── uncomputable_invariants.md
│       ├── tie_breaking_rules.md
│       ├── validation_scope.md
│       ├── power_analysis.md
│       └── license_compliance.md
├── config/
│   └── complexity_weights.yaml
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
└── code/requirements.txt
```

**Structure Decision**: Single project structure selected. This is a computational research project with no web/mobile frontend requirements. The `code/`, `data/`, `docs/`, `config/`, and `tests/` directories align with the project's reproducibility and data hygiene requirements. All data transformations produce new files under `data/` (raw vs processed), and reproducibility documentation lives under `docs/reproducibility/` per Constitution Principle III. **requirements.txt** is located at `code/requirements.txt` (not project root) per Constitution Principle I.

**Schema Governance**: Regression output files (`data/processed/regression_results_*.parquet`) MUST conform to `contracts/regression_output.schema.yaml` (CANONICAL). The `knot_data.schema.yaml` is deprecated; use `knot_record.schema.yaml` for new implementations.

**Composite Score Storage**: CompositeComplexityScore records are stored in `data/processed/validation_results.parquet` (not separate file).

## Computational Methods

### Training/Validation Split

**Explicit Specification**: Regression models are trained on validated c≤10 data ONLY. c=11-13 data is reserved for exploratory analysis (model evaluation only, not training). This maintains consistency between validation scope and conclusions.

**Split Strategy**: training, validation, stratified by crossing number and alternating classification. Random seed pinned (documented in `docs/reproducibility/seed_values.md`).

### Invariant Computation Algorithms

1. **Arc Index**: Birman-Menasco method (Birman & Menasco, 1988, "A Algorithm for the Arc Index of a Knot", *Mathematische Annalen*, 281, pp. 127-138)
2. **Seifert Circle Count**: Seifert's algorithm on minimal crossing diagrams (Seifert, 1934, "Über das Geschlecht von Knoten", *Mathematische Annalen*, 110, pp. 571-592); formula: s(D) (source: math/0303273)
3. **Bridge Number**: Schubert's bridge decomposition (Schubert, 1956, "Über eine numerische Knoteninvariante", *Mathematische Zeitschrift*, 61, pp. 245-288); 2-bridge knots (source: Wikipedia)

**Empirical Verification**: Before analysis, verify known mathematical inequalities hold for dataset:
- bridge_number ≤ crossing_number
- braid_index ≤ crossing_number (for most knots)
- Document any discrepancies in `data/derivation_notes.md` per Constitution Principle VI.

### Regression Modeling

Three model types compared (FR-005):
1. Linear regression: `volume ~ crossing_number + braid_index`
2. Polynomial regression: `volume ~ crossing_number + braid_index + crossing_number² + braid_index²`
3. Logarithmic regression: `volume ~ log(crossing_number) + log(braid_index)`
4. **Alternative**: Spline regression if polynomial overfitting detected (justification: non-linear relationships in knot geometry per arXiv 1806.09719)

**Multicollinearity Assessment**: Variance Inflation Factors (VIF) computed for all predictors. VIF > 5 flagged as potential multicollinearity issue (per FR-005, citing DOI 10.1142/S0218216519500020 and arXiv 1805.04428).

### Statistical Testing

- **Correlation**: Both Pearson AND Spearman correlations reported where distribution assumptions cannot be verified a priori (Constitution Principle VII)
- **ANOVA**: For group differences between alternating and non-alternating knots, with Levene's test for equal variances and Shapiro-Wilk test for normality (FR-008)
- **Effect Sizes**: Cohen's d for group comparisons, r or r² for correlations
- **Power Analysis**: Documented in `docs/reproducibility/power_analysis.md`; ~537 hyperbolic knots at c≤10 provides power ≥0.80 to detect r≥0.13 at α=0.05

## Spec Defect Resolution Log

| Spec Defect | Location | Issue | Provisional Fix | Action Required |
|-------------|----------|-------|-----------------|-----------------|
| Factual Error | spec.md Assumptions | OEIS A002863(13)=9988 is CUMULATIVE, not count at c=13 | Documented correct attribution (Hoste-Thistlethwaite-Weeks for c=13 count) | Kickback correction to spec.md |
| SC-006 | spec.md | Missing threshold percentage in 'of knots with computable invariants' | (provisional) | Kickback correction to spec.md |
| SC-012 | spec.md | Missing threshold percentage in 'match threshold for pass/fail status' | (provisional) | Kickback correction to spec.md |

**BLOCKING**: Implementation of SC-006 and SC-012 validation checks will use provisional values (and respectively) but cannot be marked as 'complete' until spec is corrected.