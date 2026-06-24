# Research: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

## Objective
To determine how the combinatorial invariants *crossing number* (c) and *braid index* (b) relate to the geometric invariant *hyperbolic volume* (V) across the complete census of hyperbolic prime knots with ≤ 13 crossings.

## Dataset Strategy
| Dataset | Source | Access Method | Notes |
|---------|--------|---------------|-------|
| Knot Atlas core table | Knot Atlas (**verified URL:** https://katlas.org) | HTTP GET → JSON → `code/download/knot_atlas_loader.py` | The URL is a verified dataset per the project’s “Verified datasets” block. |
| KnotInfo reference values (hyperbolic volume) | KnotInfo (https://knotinfo.org) | HTTP GET → JSON (via `requests`) | Used for cross‑check of hyperbolic volume (FR‑013). |
| OEIS A002863 (prime‑knot counts) | OEIS (https://oeis.org/A002863) | Manual lookup (static constant) | Provides the expected total count (9 988) for ≤ 13 crossings. |
| Bridge number / alternating constraints | Wikipedia (https://en.wikipedia.org/wiki/Bridge_number) & Wikipedia (https://en.wikipedia.org/wiki/2-bridge_knot) | Static reference | Used for inequality‑based validation of braid index and bridge number (alternative to circular KnotInfo check). |

## Methodology Overview
1. **Download & Parse** – `knot_atlas_loader.py` retrieves the full JSON dump, applies exponential‑backoff retry logic (FR‑008), and writes the raw file unchanged.  
2. **Cleaning & Flagging** – `parser.py` extracts the required fields; `validator.py` generates `data_quality_flags` and `missing_invariant_flags` (FR‑002, FR‑009) and writes a checksum manifest.  
3. **Core Invariant Coverage (SC‑008)** – `precision.py` compares crossing numbers against the canonical definition and validates braid indices using **independent literature constraints** (e.g., braid_index ≤ crossing_number, bridge number ≤ crossing number) rather than a circular KnotInfo comparison. It reports coverage and match rates; execution aborts if braid‑index match < 95 % (per SC‑008).  
4. **Exploratory Data Analysis (FR‑004)** – `exploratory.py` generates scatter plots of crossing number vs. braid index, colored by alternating classification, and saves `docs/figures/crossing_vs_braid.png`. A brief descriptive summary is added to the reproducibility report.  
5. **Hyperbolic Filter (FR‑012)** – Records with `hyperbolic_volume = 0` are excluded, yielding `hyperbolic_knots.csv`. Documentation of excluded knots is generated (SC‑012).  
6. **Cross‑Check Hyperbolic Volume (FR‑013, SC‑014)** – `validation_phase2.py` cross‑checks hyperbolic volumes against KnotInfo; requires ≥ 90 % match.  
7. **Correlation & Effect‑Size (FR‑006, SC‑009)** – `correlations.py` computes Spearman ρ, Pearson r, and Cohen’s d for each pair of invariants; `descriptive_metrics.py` adds mean differences and variance ratios.  
8. **Regression & Multicollinearity (FR‑005, SC‑005, SC‑013, SC‑002)** – `regression_with_alternating.py` fits **ridge‑regularized** linear, polynomial degree 2, and logarithmic models **including alternating classification as a control variable**. Because of the mathematical constraint `braid_index ≤ crossing_number`, VIF is monitored; if VIF > 5 for braid index, a reduced model using only crossing number is also saved. Model selection follows **SC‑002** (combined R², AIC, BIC, MAE) to pick the best model.  
9. **Residual Family Analysis (FR‑011, SC‑012)** – `residuals.py` identifies hyperbolic families whose absolute residual exceeds a chosen significance threshold (e.g., multiple σ), documents them in `docs/reproducibility/residual_analysis.md` with explicit caution that findings are exploratory, not causal.  
10. **Additional Invariants (FR‑003, SC‑010)** – In Phase 10 we compute arc index, Seifert circle count, bridge number; validate against independent literature sources (Wikipedia, OEIS) and KnotInfo where available (≥ 90 % match).  
11. **Documentation & Reproducibility (SC‑001, SC‑006, SC‑007)** – Generate `data_quality_report.md`, `invariant_coverage.md`, `tie_breaking_rules.md`, `hyperbolic_exclusions.md`, `algorithm_validation.md`. All artefacts are version‑controlled and checksummed.

## Expected Deliverables
- Cleaned dataset `data/processed/knots_validated.csv` (passes SC‑013 & SC‑014).  
- Figure `docs/figures/crossing_vs_braid.png`.  
- Regression summary tables (CSV + markdown).  
- Residual analysis report.  
- Full reproducibility artefacts (checksums, seed list, logs).  

## Statistical Reporting Note
Since the dataset represents a *complete census* of prime knots ≤ 13 crossings, all statistical analysis is descriptive rather than inferential. Effect sizes are the primary metrics of interest; p‑values are NOT reported for census data (complete enumeration; effect sizes are the primary metrics, per research.md). Train/test splits, ANOVA assumption checks, and inferential statistics are not applicable for complete census data. **Constitution Principle VII Exception** is honored throughout.
