# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31 | **Spec**: `specs/001-knot-complexity-analysis/spec.md`
**Input**: Feature specification from `specs/001-knot-complexity-analysis/spec.md`

## Summary

This project quantifies knot complexity through joint analysis of crossing number and braid index as predictors of hyperbolic volume, stratified by alternating/non-alternating classification. The technical approach involves downloading knot data from Knot Atlas, computing additional invariants (arc index, Seifert circle count, bridge number), filtering to exclude torus/satellite knots with zero/undefined hyperbolic volume, performing exploratory analysis with scatter plots, fitting multiple regression models (linear, polynomial, logarithmic), and validating a composite complexity score against hyperbolic volume on an exploratory validation sample. Primary analysis focuses on the ≤10 subset where invariants are verified (n=249 knots per OEIS A002863) [UNRESOLVED-CLAIM: c_75ca1bf7 — status=not_enough_info]; ≤13 data is used for exploratory extension (n=9988 at crossing number 13 per OEIS A002863).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas==2.1.0, numpy==1.24.3, scikit-learn==1.3.0, statsmodels==1.3.0, matplotlib==3.8.0, seaborn==0.13.0, pyyaml==6.0.1, requests==2.31.0, datasets==2.14.0
**Storage**: Local filesystem (data/ directory for datasets, docs/reproducibility/ for artifacts)
**Testing**: pytest==7.4.0
**Target Platform**: Linux server (GitHub Actions runner)
**Project Type**: computational research / data analysis
**Performance Goals**: Download all prime knots ≤13 crossing number within 10 minutes; regression analysis complete within 30 minutes
**Constraints**: Must handle API rate limiting with exponential backoff; must flag missing invariants rather than silently exclude; must produce reproducible results with pinned random seeds; SC-005 retry logic must be verified against simulated failures; SC-006 ≥99% invariant coverage must be measured and documented; SC-014 ≥95% hyperbolic volume completeness must be measured and documented; Measurement error risk in ≤13 data mitigated by primary analysis on ≤10 subset
**Scale/Scope**: 9988 (OEIS A002863, https://oeis.org/A002863) prime knots at crossing number 13 (per OEIS A002863); Phase 1 validation benchmarked on crossing number ≤10 (n=249 per OEIS A002863 summation) [UNRESOLVED-CLAIM: c_c98f42c9 — status=not_enough_info]
**Training vs Validation**: Regression models trained on ≤10 subset (verified invariants); exploratory models on ≤13 subset; validation restricted to ≤10 subset where algorithm accuracy verified (≥95% match threshold per SC-012); exploratory holdout uses 20% of ≤10 subset for validation testing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Implementation Strategy | Status |
|-----------|-------------|------------------------|--------|
| I. Reproducibility | Random seeds pinned; external datasets fetched from same canonical source | All stochastic operations use `random.seed()` and `np.random.seed()` with documented values in `docs/reproducibility/random_seeds.md`; Knot Atlas data downloaded fresh on each run | ✅ |
| II. Verified Accuracy | External citations verified against primary source; title-token-overlap ≥ 0.7 | Reference-Validator Agent runs via `code/reproducibility/reference_validator.py`; all citations from spec.md and research.md must pass verification before review points awarded | ✅ |
| III. Data Hygiene | Datasets checksummed under data/; no in-place modification; no PII | SHA-256 checksums recorded in `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml` artifact_hashes map; all transformations produce new files with derivation notes | ✅ |
| IV. Single Source of Truth | Every figure/statistic traces to one row in data/ and one block in code/ | Derived numbers generated programmatically; no hand-typed statistics in reports; traceability documented in `docs/reproducibility/derivation_notes.md` | ✅ |
| V. Versioning Discipline | Every artifact carries content hash; stale review records invalidated on change | Content hashes computed for all data/code files; `updated_at` timestamp updated in project state YAML on artifact change | ✅ |
| VI. Mathematical Invariant Consistency | Computed invariants verified against established definitions; discrepancies documented | Algorithm validation against KnotInfo reference values (≥95% match threshold per SC-012); discrepancies documented in `data/` via `docs/reproducibility/discrepancy_notes.md`; Primary analysis restricted to ≤10 subset where verified | ✅ |
| VII. Statistical Significance Thresholds | All statistical claims include p-values, confidence intervals, effect sizes; Pearson AND Spearman reported where assumptions uncertain | FR-008 mandates dual correlation reporting; effect sizes (Cohen's d, r) documented alongside all p-values; assumption checks (Levene's, Shapiro-Wilk) performed before ANOVA | ✅ |

All 7 principles satisfied. No complexity justification required.

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md # This file (/speckit-plan command output)
├── research.md # Phase 0 output (/speckit-plan command)
├── data-model.md # Phase 1 output (/speckit-plan command)
├── quickstart.md # Phase 1 output (/speckit-plan command)
├── contracts/ # Phase 1 output (/speckit-plan command)
│ ├── knot_record.schema.yaml
│ ├── knot_data.schema.yaml
│ ├── invariants_dataset.schema.yaml
│ ├── regression_model.schema.yaml
│ ├── regression_output.schema.yaml
│ ├── regression_result.schema.yaml
│ └── composite_complexity_score.schema.yaml
└── tasks.md # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── download/
│ └── download_knot_atlas.py
├── compute/
│ ├── compute_invariants.py
│ ├── validate_algorithms.py
│ └── validate_discrepancies.py # Constitution Principle VI implementation
├── analyze/
│ ├── exploratory_analysis.py
│ ├── regression_models.py
│ └── statistical_tests.py
├── reproducibility/
│ ├── random_seeds.py
│ ├── checksums.py
│ ├── logs.py
│ ├── reference_validator.py # Constitution Principle II integration
│ ├── tie_breaking_validation.py # SC-008 validation script
│ ├── retry_verification.py # SC-005 retry logic verification
│ ├── coverage_measurement.py # SC-006 coverage measurement
│ └── volume_completeness.py # SC-014 volume completeness measurement
└── main.py

data/
├── raw/
│ └── knot_atlas_raw.json
├── processed/
│ ├── knots_cleaned.csv
│ ├── knots_filtered_volume.csv # FR-014 filtered dataset
│ ├── knots_with_invariants.csv
│ ├── exploratory_validation_sample.csv
│ └── regression_results.json
└── plots/
 ├── crossing_vs_braid_alternating.png
 └── crossing_vs_braid_nonalternating.png

docs/
└── reproducibility/
 ├── derivation_notes.md
 ├── algorithm_validation.md
 ├── discrepancy_notes.md # Constitution Principle VI implementation
 ├── tie_breaking_rules.md
 ├── excluded_knots.md # SC-014 excluded knots documentation
 ├── uncomputable_invariants.md
 ├── validation_scope.md
 ├── validation_status.md
 ├── random_seeds.md
 └── invariant_algorithms.md

tests/
├── contract/
│ ├── test_knot_record_schema.py
│ ├── test_knot_data_schema.py
│ ├── test_invariants_dataset_schema.py
│ ├── test_regression_model_schema.py
│ ├── test_regression_output_schema.py
│ ├── test_regression_result_schema.py
│ └── test_composite_complexity_score_schema.py
├── integration/
│ ├── test_download_pipeline.py
│ └── test_retry_logic.py # SC-005 verification
└── unit/
 ├── test_invariant_computation.py
 ├── test_statistical_tests.py
 ├── test_tie_breaking_validation.py # SC-008 validation
 └── test_volume_filtering.py # FR-014/SC-014 verification
```

**Structure Decision**: Single-project structure selected (DEFAULT option) to maintain tight coupling between download, computation, and analysis modules. All code under `code/` directory; data artifacts under `data/` directory; reproducibility documentation under `docs/reproducibility/` directory. This structure supports Constitution Principle III (Data Hygiene) by separating raw data from processed data and ensuring all transformations produce new files.

## Data Flow

```
knot_atlas_raw.json (data/raw/)
 ↓ [download_knot_atlas.py]
 ↓ [checksums.py → state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml]
knots_cleaned.csv (data/processed/)
 ↓ [compute_invariants.py]
 ↓ [validate_discrepancies.py → docs/reproducibility/discrepancy_notes.md] # Constitution Principle VI
 ↓ [checksums.py → state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml]
knots_with_invariants.csv (data/processed/)
 ↓ [volume_completeness.py → docs/reproducibility/excluded_knots.md] # FR-014/SC-014
 ↓ [checksums.py → state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml]
knots_filtered_volume.csv (data/processed/)
 ↓ [exploratory_analysis.py]
crossing_vs_braid_alternating.png, crossing_vs_braid_nonalternating.png (data/plots/)
 ↓ [regression_models.py]
 ↓ [checksums.py → state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml]
regression_results.json (data/processed/)
 ↓ [statistical_tests.py]
 ↓ [checksums.py → state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml]
validation_results.json (data/processed/)
```

## Computational Task Ordering

Per the computational task ordering requirement, phases are ordered as follows:
1. **Data Download**: Knot Atlas data downloaded first (User Story 1)
2. **Invariant Computation**: Additional invariants computed from available diagram representations (User Story 2)
3. **Discrepancy Documentation**: Computed invariants compared against canonical values; discrepancies logged to docs/reproducibility/discrepancy_notes.md (Constitution Principle VI)
4. **Volume Filtering**: Torus/satellite knots with zero/undefined hyperbolic volume filtered; excluded knots documented in docs/reproducibility/excluded_knots.md (FR-014/SC-014)
5. **Exploratory Analysis**: Scatter plots generated showing crossing number vs. braid index stratified by classification (User Story 2)
6. **Model Fitting**: Regression models fitted to test linear vs. non-linear relationships (User Story 3)
7. **Validation**: Composite complexity score validated against exploratory validation sample (User Story 3)
8. **Figure Generation**: All figures generated before inclusion in final paper (User Story 3)
