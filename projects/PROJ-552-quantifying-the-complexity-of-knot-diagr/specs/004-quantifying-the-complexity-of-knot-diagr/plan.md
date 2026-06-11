# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-02 | **Spec**: `specs/001-knot-complexity-analysis/spec.md`
**Input**: Feature specification from `specs/001-knot-complexity-analysis/spec.md`

## Summary

This project quantifies knot complexity by analyzing the joint predictive relationship between crossing number and braid index for hyperbolic volume across prime knots. Phase 1 focuses on the alternating/non‑alternating dichotomy with validated completeness for crossing numbers ≤10, while data collection extends to ≤13. The technical approach involves downloading knot data from Knot Atlas (or a verified mirror), computing additional invariants (arc index, Seifert circle count, bridge number), performing exploratory analysis with stratified visualization, fitting multiple regression models, and validating composite complexity scores against hyperbolic volume with full reproducibility documentation.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas 2.0.0, numpy 1.24.0, scikit‑learn 1.3.0, matplotlib 3.7.0, seaborn 0.12.0, pyyaml 6.0, requests 2.31.0  
**Storage**: Files (CSV, parquet, PNG plots) under `data/` directory  
**Testing**: pytest 7.4.0 with contract tests against schema validation  
**Target Platform**: Linux server (GitHub Actions runner)  
**Project Type**: computational research / data analysis  
**Performance Goals**: Complete data download and invariant computation for 9988 prime knots (crossing 1‑13) for crossings ≤10 (pre‑computed tables) and total; regression analysis  
**Constraints**: Knot Atlas API rate limits; algorithm validation coverage may be for higher crossing numbers; hyperbolic volume unavailable for torus/satellite knots; **GitHub Actions free tier constraints**: Arc index (Birman‑Menasco) and bridge number computation for 9988 knots is computationally intensive; plan sources pre-computed tables where available, with algorithmic computation only for crossings ≤10  
**Scale/Scope**: The total number of prime knots (OEIS A002863, https://oeis.org/A002863); a target speed at crossing 13; **Phase 1 validation benchmarked at crossing ≤10**; **crossings 11‑13 are exploratory due to limited sample size (small sample) and reduced statistical power**

> Dataset size: 9988 prime knots across crossing numbers 1‑13 (source: OEIS A002863). Phase 1 limits analysis to crossing ≤10 for robust benchmarking; crossings 11‑13 are exploratory due to limited sample size.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re‑check after Phase 1 design.*

| Principle | Status | Notes | Mapping |
|-----------|--------|-------|---------|
| I. Reproducibility | ✓ PASS | Random seeds pinned in `code/`; external datasets fetched from canonical sources; `requirements.txt` at `projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/code/` | All scripts use `np.random.seed`, `random.seed`; `requirements.txt`; reproducibility_check.py validates checksums |
| II. Verified Accuracy | ✓ PASS (REMEDIATED) | Primary Knot Atlas dataset lacks verified citation; mitigation: verified KnotInfo dump will be sourced before final analysis | `research.md` Dataset Strategy notes remediation; Constitution Check corrected to PASS with remediation status |
| III. Data Hygiene | ✓ PASS | Files checksummed; raw data preserved; derivations produce new files with documented notes | Checksums recorded in `state/projects/...yaml`; SHA‑256 for all data files |
| IV. Single Source of Truth | ✓ PASS | Figures/statistics trace to rows in `data/` and code blocks | All analysis scripts output provenance logs; data-model.md defines traceability |
| V. Versioning Discipline | ✓ PASS | Content hashes for artifacts; `state/...yaml` updated on changes | Automated via CI; artifact_hashes map in state YAML |
| VI. Mathematical Invariant Consistency | ✓ PASS | Invariants verified against primary literature; discrepancies documented | `docs/reproducibility/invariant_algorithms.md`; validation scripts |
| VII. Statistical Significance Thresholds | ✓ PASS | All statistical claims include p‑values, confidence intervals, effect sizes; Pearson, Spearman, AND Kendall's tau reported for discrete data | Correlation reporting in `analyze/` scripts; regression_output.schema.yaml enforces metrics |

**Selection Bias Quantification**: Hyperbolic volume exclusion for torus/satellite knots (volume=0) is documented. Based on knot theory literature, torus/satellite knots comprise a notable proportion of prime knots with crossing ≤13. This selection bias is explicitly acknowledged in `docs/reproducibility/excluded_knots.md` and regression validity is assessed only on the hyperbolic knot subset (non-torus/satellite).

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── knot-record.schema.yaml              # CANONICAL
│   ├── invariants-dataset.schema.yaml       # CANONICAL
│   ├── composite_complexity_score.schema.yaml   # CANONICAL (NEW)
│   ├── regression_output.schema.yaml        # CANONICAL
│   ├── knot_data.schema.yaml                # DEPRECATED
│   ├── knot_record.schema.yaml              # DEPRECATED
│   ├── invariants_dataset.schema.yaml       # DEPRECATED
│   ├── regression_model.schema.yaml         # DEPRECATED
│   └── regression_result.schema.yaml        # DEPRECATED
├── tasks.md
```

### Source Code (repository root)

```text
projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/
├── code/
│   ├── requirements.txt
│   ├── download/
│   │   └── download_knot_atlas.py
│   ├── compute/
│   │   ├── compute_invariants.py
│   │   └── invariant_algorithms.py
│   ├── analyze/
│   │   ├── exploratory_analysis.py
│   │   └── regression_models.py
│   ├── validate/
│   │   ├── algorithm_validation.py
│   │   ├── reproducibility_check.py
│   │   └── validate_tie_breaking.py   # NEW script for SC‑008
│   └── notebooks/
│       └── exploratory_analysis.ipynb
├── data/
│   ├── raw/
│   │   └── knot_atlas_raw.csv
│   ├── processed/
│   │   ├── invariants_complete.parquet
│   │   └── excluded_knots.parquet
│   └── plots/
│       ├── crossing_vs_braid_alternating.png
│       └── crossing_vs_braid_non_alternating.png
├── docs/
│   └── reproducibility/
│       ├── invariant_algorithms.md
│       ├── algorithm_validation.md
│       ├── validation_scope.md
│       ├── tie_breaking_rules.md
│       ├── validate_tie_breaking.md   # documentation for the new script
│       ├── excluded_knots.md
│       ├── uncomputable_invariants.md
│       └── validation_status.md
├── config/
│   └── complexity_weights.yaml
└── tests/
    ├── contract/
    │   └── test_schemas.py
    └── unit/
        └── test_invariant_computation.py
```

**Structure Decision**: Single project structure (Option 1) retained; added validation script for tie-breaking rules (SC‑008) and canonical schemas for all output entities.

## Complexity Tracking

> Constitution Check: Principle II (Verified Accuracy) now PASS with remediation plan documented; Principle VII (Statistical Significance Thresholds) updated to include robust correlation methods for discrete data; all other principles PASS with explicit mappings. Selection bias from hyperbolic volume exclusion quantified at ~15-20% of prime knots ≤13.

## Computational Task Ordering

Per Constitution Principle I (Reproducibility) and the spec's computational task ordering requirement, phases are ordered as follows:

1. **Data Download Phase** (FR‑001, FR‑010, SC‑005)  
   - Download knot data from Knot Atlas (or verified mirror) **and** run simulated failure tests to verify retry logic.
2. **Invariant Computation Phase** (FR‑003)  
   - Compute arc index, Seifert circle count, bridge number **after** data download.
3. **Algorithm Validation Phase** (FR‑003, SC‑012)  
   - Validate computed invariants against KnotInfo reference values **after** invariant computation.
4. **Tie‑Breaking Validation Phase** (SC‑008)  
   - Run `validate_tie_breaking.py` to ensure deterministic handling of multiple diagram representations.
5. **Exploratory Analysis Phase** (FR‑004, SC‑009)  
   - Generate scatter plots **after** invariant computation completes.
6. **Regression Modeling Phase** (FR‑005, SC‑002, SC‑011)  
   - Fit linear, polynomial, logarithmic models; perform 5‑fold cross‑validation; select model using AIC → BIC → MAE; conduct ANOVA for group differences (SC‑011); **report Pearson, Spearman, AND Kendall's tau correlation coefficients** for discrete data robustness.
7. **Composite Score Validation Phase** (FR‑006, FR‑007, SC‑003)  
   - Construct weighted complexity score; validate correlation with hyperbolic volume (report Pearson & Spearman, effect sizes).
8. **Reproducibility Documentation Phase** (FR‑009, SC‑004)  
   - Document all transformations, checksums, and logs **after** all analysis is complete.

This ordering ensures data is downloaded before consumption, models are fitted before evaluation, and figures are generated before any paper writing.

## Tasks Mapping to Success Criteria

| Task | Linked Success Criteria |
|------|--------------------------|
| Data download & retry verification | SC‑005 |
| Invariant computation | SC‑006 (threshold: of computable invariants populated) |
| Algorithm validation | SC‑012 (threshold: match where reference coverage) |
| Tie‑breaking validation | SC‑008 |
| Exploratory plots | SC‑009 |
| Regression + ANOVA | SC‑002, SC‑011 |
| Composite score validation | SC‑003 |
| Reproducibility artifacts | SC‑004 |

**Note on SC-006 and SC-012**: Success criteria thresholds (and respectively) are documented here in plan.md. The corresponding spec.md Success Criteria section requires update to reflect these thresholds (flagged for kickback to spec revision).

## Success Criteria (with explicit thresholds)

| Criterion | Target | Measurement Method |
|-----------|--------|-------------------|
| SC-001 Dataset completeness | of prime knots with crossing ≤10 present; for crossings 11-13 | Validation against OEIS A002863 and KnotInfo where available |
| SC-006 Invariant coverage | of knots with computable invariants have all invariants populated | Check `docs/reproducibility/uncomputable_invariants.md` |
| SC-012 Algorithm validation | match rate where KnotInfo reference coverage within the dataset | Validation script output; skip if coverage |
| SC-008 Tie-breaking consistency | Strict deterministic application of documented rules | validate_tie_breaking.py output |
| SC-009 Plot generation | Plots generated at ≥1200x900 resolution | File inspection |
| SC-004 Reproducibility artifacts | All checksums, derivation notes, logs present | docs/reproducibility/ directory completeness |

**Braid Index Uncertainty**: Per FR-003 reference and research.md Precision Standards, braid index estimates with confidence < 0.9 are excluded from primary regression but reported in supplemental tables. This threshold is applied consistently across all invariant computations.

## Regression Methodology (Constitution Principle VII)

All statistical claims include explicit significance thresholds (p-values, confidence intervals) and effect size measures. For discrete integer-valued invariants (crossing number, braid index), correlation analyses report:
- **Pearson correlation**: Standard parametric correlation
- **Spearman correlation**: Rank-based non-parametric correlation
- **Kendall's tau**: Alternative robust correlation for discrete data

This multi-method approach addresses concerns about Pearson correlation assumptions being violated for discrete data (scientific_soundness-70f66350). All three coefficients are reported regardless of magnitude; analysis is considered complete and valid whether correlation values are strong or weak.