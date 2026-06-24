# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-24 | **Spec**: [spec.md](../specs/001-knot-complexity-analysis/spec.md)  
**Input**: Feature specification from `/specs/001-knot-complexity-analysis/spec.md`

## Summary
The core deliverable is a reproducible analysis pipeline that (1) downloads the complete census of prime knots (≤ 13 crossings) from Knot Atlas, (2) cleans and validates the core invariants (crossing number, braid index, hyperbolic volume, alternating classification), (3) establishes precision thresholds for the core invariants, (4) **performs exploratory data analysis (FR‑004) with scatter plots of crossing number vs. braid index stratified by alternating status**, (5) filters to hyperbolic knots, (6) cross‑checks hyperbolic volume against KnotInfo, (7) **fits ridge‑regularized regression models (including alternating classification as a control variable) while respecting the mathematical constraint b ≤ c and monitoring multicollinearity**, (8) performs residual family analysis with cautious interpretation, (9) computes additional invariants (arc index, Seifert circle count, bridge number) and validates them against independent literature sources, (10) selects the final model using SC‑002 criteria (R², AIC, BIC, MAE), and (11) documents every step for full reproducibility.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `requests`, `pandas>=2.0`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `statsmodels`, `pyyaml`, `tqdm`, `jsonschema`  
- **Storage**: CSV files under `data/`; derived artefacts under `docs/reproducibility/`  
- **Testing**: `pytest` + `pytest-cov`; contract validation via `jsonschema` against the `contracts/` schemas.  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Performance Goal**: Entire pipeline ≤ 30 min on a standard runner (2 CPU, 7 GB RAM).  

## Constitution Check
| Constitution Principle | How the plan satisfies it |
|------------------------|---------------------------|
| **I. Reproducibility** | All scripts are deterministic (random seeds pinned in `code/reproducibility/seed_config.py`). External data is fetched from the canonical Knot Atlas URL on every run; no manual edits are required. |
| **II. Verified Accuracy** | All citations (e.g., Birman‑Menasco 1988, Ohyama 1993, OEIS A002863) will be validated by the Reference‑Validator Agent before any review point is awarded. |
| **III. Data Hygiene** | Raw downloads are stored unchanged (`data/raw/knot_atlas_raw.json`). Every transformation writes a new file (`*_cleaned.csv`, `*_validated.csv`). SHA‑256 checksums are recorded in `docs/reproducibility/checksums.sha256`. |
| **IV. Single Source of Truth** | Every figure, table, and statistic is generated from a single CSV row identified by the `knot_id` field; the pipeline logs the exact source row used for each derived value. |
| **V. Versioning Discipline** | All artefacts are content‑hashed; the hash map is stored in `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml`. |
| **VI. Mathematical Invariant Consistency** | Core invariants are taken directly from Knot Atlas. Additional invariants (Phase 9) are cross‑checked against independent literature (Wikipedia, OEIS) and KnotInfo where available. |
| **VII. Statistical Significance Thresholds** | Because the analysis covers a *complete census* of hyperbolic prime knots ≤ 13 crossings, the plan reports effect sizes (Spearman ρ, Pearson r, Cohen’s d, VIF) and descriptive goodness‑of‑fit metrics (R², AIC, BIC, MAE) without p‑values, respecting the census‑data exception. |

## Verified Datasets
- **Knot Atlas** – Primary source of knot invariants. URL: https://katlas.org (verified dataset).  

## Project Structure
```text
specs/001-knot-complexity-analysis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── knot_record.schema.yaml
    ├── dataset.schema.yaml
    ├── regression_model.schema.yaml
    └── knot_dataset.schema.yaml

code/
├── __init__.py
├── download/
│   └── knot_atlas_loader.py          # FR‑001, FR‑008
├── data/
│   ├── parser.py                     # FR‑001 parsing
│   ├── validator.py                  # FR‑002, FR‑009, FR‑010
│   └── tie_breaker.py                # FR‑011
├── analysis/
│   ├── precision.py                  # SC‑008 core‑invariant coverage
│   ├── correlations.py               # FR‑006 (new)
│   ├── exploratory.py                # FR‑004 (EDA)
│   ├── regression_with_alternating.py # FR‑005, SC‑005, SC‑013, SC‑014, SC‑002
│   ├── descriptive_metrics.py        # SC‑009
│   ├── residuals.py                  # FR‑011
│   ├── validation_phase2.py          # SC‑010
│   └── additional_invariants.py      # FR‑003 (arc index, Seifert, bridge)
├── reproducibility/
│   ├── seed_config.py                # random seed pinning
│   └── logger.py                     # FR‑007 log format
└── cli.py                            # entry‑point wrapper

data/
├── raw/
│   └── knot_atlas_raw.json
├── processed/
│   ├── knots_cleaned.csv
│   └── knots_validated.csv
└── checksums.sha256

docs/
├── reproducibility/
│   ├── data_quality_report.md        # SC‑013
│   ├── invariant_coverage.md         # SC‑008
│   ├── tie_breaking_rules.md         # SC‑007
│   ├── multicollinearity_assessment.md # SC‑005
│   ├── residual_analysis.md          # SC‑012
│   ├── validation_scope.md           # SC‑001
│   ├── hyperbolic_exclusions.md      # SC‑012
│   └── algorithm_validation.md       # SC‑010
└── figures/
    └── crossing_vs_braid.png
```

## Phased Implementation Timeline

| Phase | Tasks | FR/SC IDs |
|-------|-------|-----------|
| **Phase 0 – Setup** | Create virtualenv, pin dependencies, add `requirements.txt`. Record dataset completeness benchmark (SC‑001). | – |
| **Phase 1 – Data Acquisition** | `code/download/knot_atlas_loader.py` fetches JSON from **https://katlas.org** (verified dataset). | FR‑001, FR‑008 |
| **Phase 2 – Parsing & Cleaning** | `code/data/parser.py` extracts required fields; `code/data/validator.py` generates `data_quality_flags`, `missing_invariant_flags`, handles ambiguous alternating status (SC‑006). | FR‑002, FR‑009, FR‑010 |
| **Phase 3 – Core Invariant Coverage (SC‑008)** | `analysis/precision.py` computes coverage & match rates for crossing number and braid index against independent literature (bridge‑number ≤ crossing‑number, OEIS counts) **instead of a circular KnotInfo check**; aborts if braid‑index match < 95 % (per SC‑008). Also reports SC‑013 data‑quality metrics (null % ≤ 5, format ≥ 99, duplicates = 0). | SC‑008, SC‑013 |
| **Phase 4 – Exploratory Data Analysis (FR‑004)** | `analysis/exploratory.py` creates scatter plots of crossing number vs. braid index, colored by alternating classification; produces `docs/figures/crossing_vs_braid.png` and accompanying descriptive summary. | FR‑004 |
| **Phase 5 – Hyperbolic Filter (FR‑012)** | Filter `knots_validated.csv` to `hyperbolic_knots.csv` where `hyperbolic_volume > 0`. Document excluded non‑hyperbolic knots (SC‑012). | FR‑012 |
| **Phase 6 – Hyperbolic Volume Cross‑Check (FR‑013, SC‑014)** | `analysis/validation_phase2.py` cross‑checks hyperbolic volumes against KnotInfo; requires ≥ 90 % match (SC‑014). | FR‑013, SC‑014 |
| **Phase 7 – Correlation & Effect Sizes (FR‑006, SC‑009)** | `analysis/correlations.py` computes Spearman ρ, Pearson r, and Cohen’s d for all invariant pairs; `analysis/descriptive_metrics.py` adds mean differences and variance ratios. | FR‑006, SC‑009 |
| **Phase 8 – Regression & Multicollinearity (FR‑005, SC‑005, SC‑013, SC‑002)** | `analysis/regression_with_alternating.py` fits **ridge‑regularized** linear, polynomial (degree 2), and logarithmic models **including alternating classification as a covariate**. Because of the mathematical constraint `braid_index ≤ crossing_number`, VIF is monitored; if VIF > 5 for braid index, a reduced model using only crossing number is also saved. Model selection uses **SC‑002** (combined R², AIC, BIC, MAE) to choose the final model. | FR‑005, SC‑005, SC‑013, SC‑002 |
| **Phase 9 – Residual Family Analysis (FR‑011, SC‑012)** | `analysis/residuals.py` flags families with |residual| ≥ 2σ; generates `docs/reproducibility/residual_analysis.md` with exploratory caveats (no causal claims). | FR‑011, SC‑012 |
| **Phase 10 – Additional Invariants (FR‑003, SC‑010)** | `analysis/additional_invariants.py` computes arc index, Seifert circle count, bridge number; `validation_phase2.py` validates against independent literature sources (Wikipedia bridge number, OEIS A002863) and KnotInfo where available (≥ 90 % match). | FR‑003, SC‑010 |
| **Phase 11 – Documentation & Reproducibility (SC‑001, SC‑006, SC‑007)** | Generate `data_quality_report.md`, `invariant_coverage.md`, `tie_breaking_rules.md`, `hyperbolic_exclusions.md`, `algorithm_validation.md`. All artefacts are checksum‑tracked. | SC‑001, SC‑006, SC‑007 |
| **Phase 12 – Final Packaging** | Export CSVs, model artefacts, figures; update `state/projects/...yaml` with content hashes. | – |

## Complexity Tracking
All functional requirements are now directly traceable to user stories and FR/SC identifiers. No constitution violations remain. The regression methodology respects predictor dependence via regularization and VIF monitoring, and all statistical reporting follows the census‑data exception.

## Contract Validation
Each analysis module validates its outputs against the appropriate JSON/YAML schema under `contracts/` using `jsonschema`. Failures abort the pipeline, ensuring strict conformance.
