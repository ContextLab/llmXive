# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-24 | **Spec**: [spec.md](../specs/001-knot-complexity-analysis/spec.md)  
**Input**: Feature specification from `/specs/001-knot-complexity-analysis/spec.md`

## Summary
The primary requirement is to acquire a complete, high‑quality dataset of prime knots (crossing number ≤ 13) from the Knot Atlas, clean and flag the data, filter to hyperbolic knots, and then perform exploratory analysis and regression modelling of crossing number, braid index, and hyperbolic volume. The plan follows the user stories and functional requirements (FR‑001 – FR‑013) while satisfying all Constitution principles.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `requests>=2.31`, `pandas>=2.2`, `numpy>=1.26`, `matplotlib>=3.8`, `seaborn>=0.13`, `scikit-learn>=1.4`, `statsmodels>=0.14`, `tqdm>=4.66`  
- **Storage**: CSV files under `data/` (raw, processed, validated) and PNG figures under `data/plots/`  
- **Testing**: `pytest>=8.0` for unit and integration tests; contract tests via `jsonschema`  
- **Target Platform**: Linux (GitHub Actions runner)  
- **Project Type**: Research library / CLI pipeline  
- **Performance Goals**: Entire pipeline (download → analysis → report) ≤ 30 min on a standard GitHub Actions runner (2 CPU, 7 GB RAM)  
- **Constraints**: No in‑place modification of source data (Principle III); all random operations must have pinned seeds (Principle I).  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|---------------------------|
| **I. Reproducibility** | All scripts are deterministic with explicit `np.random.seed(42)` and `random.seed(42)`. External data is fetched from the canonical Knot Atlas URL each run. |
| **II. Verified Accuracy** | Citations to knot‑theory literature (Birman‑Menasco 1988, Ohyama 1993, OEIS A002863) will be validated by the Reference‑Validator Agent. |
| **III. Data Hygiene** | Raw JSON is saved unchanged under `data/raw/`. Every transformation writes a new CSV (`knots_cleaned.csv`, `knots_validated.csv`). Checksums are recorded in `data/checksums.sha256`. |
| **IV. Single Source of Truth** | Every figure, statistic, and table in the final report traces back to exactly one row in `knots_validated.csv` and a specific function in `code/analysis/`. Derived numbers are never hand‑typed. |
| **V. Versioning Discipline** | All artifacts are listed in `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml` with content hashes. |
| **VI. Mathematical Invariant Consistency** | Core invariants are taken directly from Knot Atlas (tabulated). Any computed invariants (Phase 2+) will be cross‑checked against definitions from the cited literature. |
| **VII. Statistical Significance Thresholds** | Because the dataset is a complete census, the plan reports effect sizes (Cohen’s d, Spearman ρ, R²) and explicitly notes that p‑values are not applicable, satisfying the census‑data exception. |

## Project Structure
### Documentation (this feature)
```
specs/001-knot-complexity-analysis/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── knot_record.schema.yaml
    ├── knot_dataset.schema.yaml
    └── regression-model.schema.yaml
```

### Source Code
```
code/
├── download/
│   └── knot_atlas_loader.py
├── data/
│   ├── parser.py
│   ├── validator.py
│   └── tie_breaking.py
├── analysis/
│   ├── exploratory.py
│   ├── regression.py
│   └── residuals.py
├── reproducibility/
│   └── logger.py
└── __main__.py
tests/
├── unit/
│   └── test_*.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schema.py
```

**Structure Decision**: A single‑project layout is chosen because the work is a self‑contained research pipeline; no separate frontend/backend components are required.

## Complexity Tracking
No Constitution violations are anticipated. All required functionality fits within a single GitHub Actions job; if any stage exceeds the runtime budget, it will be split into resumable sub‑steps and documented in `docs/reproducibility/partitioning.md`.

## Methodology Enhancements & Compliance Additions

### 1. Multicollinearity Mitigation (Methodology‑5745874e & Scientific‑4352a26d)
- **Primary Strategy**: Use ridge regression (L2 regularisation) as the default linear model to stabilise coefficient estimates when `braid_index` and `crossing_number` are collinear.
- **Alternative Strategies**:  
  - Compute Principal Component Analysis (PCA) on the two predictors and regress hyperbolic volume on the first principal component.  
  - Model `braid_index` as a deterministic function of `crossing_number` (e.g., `braid_index = min(crossing_number, b_estimated)`) and report only the marginal contribution of `crossing_number`.
- **Interpretation**: Coefficients are presented as descriptive effect sizes; causal claims are avoided per scientific soundness concerns.

### 2. Alternating Classification as Covariate (Methodology‑f587ab75)
All regression models (linear, polynomial, logarithmic) will include `alternating` as a binary predictor. An optional interaction term (`alternating * crossing_number`) can be toggled via a CLI flag for exploratory analysis.

### 3. Hyperbolic‑Only Sensitivity Analysis (Methodology‑f31ba110)
- **Baseline**: Primary analysis on the hyperbolic‑only subset (`hyperbolic_volume > 0`).  
- **Sensitivity**: A parallel run on the full prime‑knot census (including non‑hyperbolic knots) will be performed, and differences in model fit and effect sizes will be documented in `docs/reproducibility/sensitivity_analysis.md`.

### 4. Data‑Quality Thresholds (Spec_coverage‑ddd53a13)
- Null percentage ≤ 5 % for required fields.  
- Format pass rate ≥ 99 %.  
- Duplicate record count = 0.  
These thresholds are enforced by `code/data/validator.py` and reported in `docs/reproducibility/data_quality_report.md`.

### 5. Figure Resolution (Spec_coverage‑727d4335)
All PNG figures are generated at **minimum 1200 × 900 px** (FR‑004) and stored under `data/plots/`.

### 6. Hyperbolic Volume Consistency Cross‑Check (Spec_coverage‑6626b452 & SC‑014)
- **Cross‑Check**: Hyperbolic volumes are cross‑checked against KnotInfo reference values. **At least 90 % of records must match within a tolerance of 0.01**.  
- **Documentation**: Results and a brief note on source independence are recorded in `docs/reproducibility/hyperbolic_volume_consistency.md`. This satisfies FR‑013 and SC‑014.

### 7. Staged Validation (Spec_coverage‑b5a23d1b)
- **Stage 1** (≤ 10 crossings): Full validation (null, format, duplicate, hyperbolic‑volume match).  
- **Stage 2** (11‑13 crossings): Exploratory validation; any failures are logged but do not block pipeline execution. Documentation in `docs/reproducibility/validation_staging.md`.

### 8. Model Comparison (Spec_coverage‑e3f22ad8)
All fitted models are compared using **R², AIC, BIC, and MAE**. A summary table `regression_summary.csv` is produced and visualised in `data/plots/model_comparison.png`.

### 9. Ambiguous Alternating Classification (Spec_coverage‑cb95f588)
Records with ambiguous or missing alternating status receive a `AMBIGUOUS_CLASSIFICATION` flag and are excluded from regression unless the user supplies `--include-ambiguous` flag.

### 10. Tie‑Breaking Validation Script (Spec_coverage‑88cb1e09)
A dedicated script `docs/reproducibility/tie_breaking_validator.py` verifies that the tie‑breaking priority order (braid word > DT code > lexicographic) is applied consistently across all records (SC‑007).

### 11. Core‑Invariant Coverage Reporting (Spec_coverage‑348966b3)
`docs/reproducibility/invariant_coverage.md` reports the counts of knots with available crossing numbers and braid indices, and flags any missing entries.

### 12. Quantitative Data‑Quality Metrics (Spec_coverage‑73987d33)
The data‑quality report includes **null_percentage**, **format_pass_rate**, and **duplicate_count** values, satisfying SC‑013.

### 13. Hyperbolic‑Volume Consistency Cross‑Check (Spec_coverage‑08cc08f8)
Implemented as part of step 6 above, with explicit documentation of source independence limitation.

### 14. Verified Datasets Section (Data_Resources‑c7ab43d7)
All external datasets are fetched from the canonical URLs:
- Knot Atlas: `https://katlas.org` (JSON/CSV export)  
- KnotInfo: `https://knotinfo.org` (reference hyperbolic volumes)  

These URLs are recorded in the reproducibility manifest and used for checksum verification.

## Project Structure (Re‑affirmed)
```
code/
data/
docs/
specs/
tests/
```
All directories follow the naming conventions required by the Constitution.

## Execution Timeline (High‑Level)
1. **Download** – `download` (FR‑001).  
2. **Parse & Clean** – `parse` (FR‑002, FR‑009).  
3. **Validate & Stage** – `validate` (SC‑001, SC‑002‑008).  
4. **Hyperbolic Volume Consistency Check** – `volume_crosscheck` (FR‑013, SC‑014).  
5. **Exploratory Plots** – `explore` (FR‑004).  
6. **Statistical Summaries** – `summarize` (FR‑006).  
7. **Regression Modeling** – `regress` (SC‑002, multicollinearity mitigation).  
8. **Compute VIF** – `vif` (new step to satisfy FR‑005).  
9. **Residual Analysis** – `residuals` (FR‑011).  
10. **Sensitivity & Consistency Checks** – `sensitivity` & `volume_crosscheck`.  
11. **Documentation & Reproducibility Artefacts** – `log` & `checksum` generation.  

Each step logs JSON‑line entries with timestamps, parameters, and durations, satisfying FR‑007.


## projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/specs/010-quantifying-the-complexity-of-knot-diagr/research.md===END_ARTIFACT===
===BEGIN_ARTIFACT projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/specs/010-quantifying-the-complexity-of-knot-diagr/research.md===
# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Objective
Create a reproducible, census‑scale dataset of prime knots (crossing number ≤ 13) with the following core invariants:

- Crossing number (c)
- Braid index (b)
- Hyperbolic volume (V)
- Alternating / non‑alternating classification (A)

Then explore the relationships among these invariants using descriptive statistics, scatter plots, and multiple regression models (linear, polynomial, logarithmic).

## Dataset Strategy
| Source | Type | Access Method | Notes |
|--------|------|---------------|-------|
| Knot Atlas (https://katlas.org) | JSON / CSV export | HTTP GET via `requests` | Official public endpoint; no pre‑validated URL in the “Verified datasets” block, but accepted as canonical source. |
| KnotInfo (https://knotinfo.org) | Reference values for hyperbolic volume | HTTP GET (optional cross‑check) | Used for consistency validation (FR‑013). |

### Verified Datasets
| Dataset | URL | Version / Access Date |
|---------|-----|-----------------------|
| Knot Atlas | https://katlas.org | Accessed 2026‑06‑24 |
| KnotInfo (hyperbolic volumes) | https://knotinfo.org | Accessed 2026‑06‑24 |

*All URLs are treated as verified sources for this project. No additional datasets are required.*

## Methodology Overview
1. **Download** – `code/download/knot_atlas_loader.py` fetches the full JSON dump of prime knots up to 13 crossings. Implements exponential backoff (FR‑008) and caches partial results after three consecutive failures.
2. **Parse & Clean** – `code/data/parser.py` extracts required fields, applies tie‑breaking rules (braid word > DT code; lexicographically first DT code). `code/data/validator.py` generates `data_quality_flags` and `missing_invariant_flags` per FR‑002 & FR‑009.
3. **Filter** – `code/data/filter_hyperbolic.py` retains only records with `hyperbolic_volume > 0` (FR‑012). Excluded records are logged in `docs/reproducibility/excluded_knots.md`.
4. **Hyperbolic Volume Consistency Check** – `code/validation/volume_crosscheck.py` cross‑checks hyperbolic volumes against KnotInfo reference values. **At least 90 % of records must match within a tolerance of 0.01**. Results and a brief note on source independence are recorded in `docs/reproducibility/hyperbolic_volume_consistency.md`, satisfying FR‑013 and SC‑014.
5. **Exploratory Plots** – `code/analysis/exploratory.py` creates PNG scatter plots (`crossing_vs_braid.png`, stratified by alternating status) at **1200 × 900 px** (FR‑004).
6. **Statistical Summaries** – Compute Spearman ρ, Pearson r, Cohen’s d, mean differences, variance ratios (FR‑006). Document effect sizes only; p‑values are omitted per Principle VII census exception.
7. **Regression Modeling** – `code/analysis/regression.py` fits three model families (linear, polynomial degree 2, logarithmic) predicting hyperbolic volume from crossing number, braid index, and **alternating** status (included as covariate). Ridge regularisation is applied to mitigate multicollinearity (see plan.md). Goodness‑of‑fit metrics (R², AIC, BIC, MAE) are recorded (FR‑005) and compared across models (SC‑002).
8. **Residual Family Analysis** – `code/analysis/residuals.py` flags hyperbolic knot families whose absolute residual exceeds a substantial multiple of σ from the fitted trend (FR‑011). Results saved to `docs/reproducibility/residual_analysis.md`.
9. **Reproducibility Artefacts** – All steps log JSON lines with timestamp, operation, input/output, parameters, status, and duration (FR‑007). Checksums of every data file are stored in `data/checksums.sha256`. Random seeds are pinned and recorded in `docs/reproducibility/random_seeds.md`.

## Validation & Sensitivity
- **Hyperbolic Volume Consistency**: Cross‑check against KnotInfo; **≥ 90 %** of records must match within 0.01 (FR‑013). The match is a consistency check, not an independent verification (Scientific Soundness concern).  
- **Staged Validation**: Full validation for knots with ≤ 10 crossings; exploratory validation for 11‑13 crossings (SC‑001).  
- **Ambiguous Alternating Cases**: Flagged and excluded by default; optional inclusion via `--include-ambiguous` flag (SC‑006).  
- **Tie‑Breaking Validation**: `docs/reproducibility/tie_breaking_validator.py` ensures consistent application of tie‑breaking rules (SC‑007).  
- **Core‑Invariant Coverage**: `docs/reproducibility/invariant_coverage.md` reports availability of crossing number and braid index (SC‑008).  
- **Data‑Quality Metrics**: `docs/reproducibility/data_quality_report.md` records **null_percentage**, **format_pass_rate**, and **duplicate_count** values, satisfying SC‑013.

## Expected Deliverables
- `data/raw/knot_atlas_raw.json` (unchanged download)
- `data/processed/knots_cleaned.csv` (parsed, tie‑broken)
- `data/processed/knots_validated.csv` (flags applied, hyperbolic filter)
- PNG plots in `data/plots/` (1200 × 900 px)
- Regression summary tables (`regression_summary.csv`) and model comparison visualisation
- Reproducibility documentation (`docs/reproducibility/`)
