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
4. **Exploratory Plots** – `code/analysis/exploratory.py` creates PNG scatter plots (`crossing_vs_braid.png`, stratified by alternating status) at **1200 × 900 px** (FR‑004).
5. **Statistical Summaries** – Compute Spearman ρ, Pearson r, Cohen’s d, mean differences, variance ratios (FR‑006). Document effect sizes only; p‑values are omitted per Principle VII census exception.
6. **Regression Modeling** – `code/analysis/regression.py` fits three model families (linear, polynomial degree 2, logarithmic) predicting hyperbolic volume from crossing number, braid index, and **alternating** status (included as covariate). Ridge regularisation is applied to mitigate multicollinearity (see plan.md). Goodness‑of‑fit metrics (R², AIC, BIC, MAE) are recorded (FR‑005) and compared across models (SC‑002).
7. **Residual Family Analysis** – `code/analysis/residuals.py` flags hyperbolic knot families whose absolute residual exceeds 2 σ from the fitted trend (FR‑011). Results saved to `docs/reproducibility/residual_analysis.md`.
8. **Reproducibility Artefacts** – All steps log JSON lines with timestamp, operation, input/output, parameters, status, and duration (FR‑007). Checksums of every data file are stored in `data/checksums.sha256`. Random seeds are pinned and recorded in `docs/reproducibility/random_seeds.md`.

## Validation & Sensitivity
- **Hyperbolic Volume Consistency**: Cross‑check against KnotInfo; ≥ 90 % of records must match within 0.01 (FR‑013). The match is a consistency check, not an independent verification (Scientific Soundness concern).  
- **Staged Validation**: Full validation for knots with ≤ 10 crossings; exploratory validation for 11‑13 crossings (SC‑001).  
- **Ambiguous Alternating Cases**: Flagged and excluded by default; optional inclusion via `--include-ambiguous` flag (SC‑006).  
- **Tie‑Breaking Validation**: `docs/reproducibility/tie_breaking_validator.py` ensures consistent application of tie‑breaking rules (SC‑007).  
- **Core‑Invariant Coverage**: `docs/reproducibility/invariant_coverage.md` reports availability of crossing number and braid index (SC‑008).  
- **Data‑Quality Metrics**: `docs/reproducibility/data_quality_report.md` records null percentage, format pass rate, and duplicate count (SC‑013).  

## Expected Deliverables
- `data/raw/knot_atlas_raw.json` (unchanged download)
- `data/processed/knots_cleaned.csv` (parsed, tie‑broken)
- `data/processed/knots_validated.csv` (flags applied, hyperbolic filter)
- PNG plots in `data/plots/` (1200 × 900 px)
- Regression summary tables (`regression_summary.csv`) and model comparison visualisation
- Reproducibility documentation (`docs/reproducibility/`)
