# Implementation Plan: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

**Branch**: `001-data-transformation-sensitivity` | **Date**: 2024-10-21 | **Spec**: `specs/001-data-transformation-sensitivity/spec.md`  
**Input**: Feature specification from `/specs/001-data-transformation-sensitivity/spec.md`

## Summary
The pipeline will:

1. **Download** a minimum of 50 open, numeric, tabular datasets (e.g., Wine Quality, Breast Cancer Wisconsin, Iris, Adult, Statlog Heart, Vehicle Silhouettes) via HuggingFace or OpenML programmatic loaders.  
   - Files are streamed (`streaming=True`) and size‑capped at 5 MB to keep RAM low.  
   - **Deterministic verification**: Immediately after each download a SHA‑256 checksum is computed (stream‑wise) and recorded in `data/checksums.csv`.  
   - After each dataset a **checkpoint** is written (`results/checkpoints/`) so the run can resume if the CI job times out.  
2. **Verify** each file with SHA‑256 while streaming; record checksums in `data/checksums.csv`.  
3. **Impute** missing values (mean for approximately symmetric variables, median for skewed) and **log** the imputation rate; a **sensitivity analysis** will also run median‑vs‑mean imputation and compare downstream Type I error and power to assess confounding.  
4. **Filter** datasets using a **stratified non‑normality criterion**: retain datasets across three Shapiro‑Wilk p‑value bands (0.01‑0.05, 0.05‑0.10, 0.10‑0.20) and ensure *N* ≥ 30. This avoids bias toward only strongly non‑normal data and improves generalisability.  
5. **Characterize** distribution shape (skewness, kurtosis) for each retained dataset; store averages per dataset for later simulation shape matching.  

### Phase 3 – Type I Error Estimation (Real‑Data Null Simulation)
For each filtered dataset **D**:
1. **Dual null‑simulation strategy**:  
   - **Stratified label shuffling**: shuffle group labels **5 000** times **within** each covariate stratum (if any) to break association while preserving latent structure.  
   - **Residual permutation**: fit a null linear model on the continuous variables, permute residuals, and recombine with fitted values. This addresses the concern that simple shuffling may leave latent structure intact.  
2. **Transform** the continuous variables with each of the three methods (Box‑Cox, Yeo‑Johnson, rank‑based inverse normal). λ is optimized per dataset. Log any log‑shift interventions.  
3. **Run** the appropriate parametric test (t‑test for binary groups, one‑way ANOVA for ≥ 2 groups) on each transformed version.  
4. **Record** the proportion of *p* < 0.05 as the Type I error estimate for that transformation‑test pair (FR‑004).  
5. **Compare** the two null‑simulation estimates; large discrepancies trigger a warning and are logged for further inspection.

### Phase 4 – Simulated Data for Power (Ground Truth)
For each effect size **d ∈ {0.2, 0.5, 0.8}** **and for each retained real dataset**:
1. **Generate** **1 000** simulated datasets **using that dataset’s own skewness and kurtosis** (via `scipy.stats.skewnorm` and matching kurtosis). This preserves per‑dataset shape variability rather than collapsing to an average.  
2. **Create** group labels such that the mean difference yields the target Cohen’s *d*.  
3. **Apply** the three transformations (as in Phase 3) and a baseline untransformed condition.  
4. **Run** the same parametric tests; compute the proportion of significant results → **empirical power** estimate (FR‑006).  
5. **Independent validation**:  
   - **Primary benchmark** – non‑parametric bootstrap power computed by resampling the simulated datasets 10 000 times (no normality assumptions).  
   - **Secondary benchmark** – analytical power with `statsmodels.stats.power.TTestIndPower` (normal‑theory) retained only for reference.  
   - Report divergence between bootstrap and analytical estimates to quantify how well transformations restore normality.

### Phase 5 – Aggregation & Inference
1. **Bootstrap** (10 000 resamples) the per‑dataset error and power values to obtain 95 % confidence intervals; target half‑width ≤ 0.02 (SC‑004).  
2. **Sample‑size justification**: Power analysis for the Friedman test (small effect *f* = 0.25) indicates that **≥ 45** datasets give > 80 % power at α = 0.05 (computed with `statsmodels.stats.power.FTestAnovaPower`). Our ≥ 50‑dataset target satisfies this, justifying the CI precision goal.  
3. **Friedman test** (`scipy.stats.friedmanchisquare`) on the per‑dataset error (and separately on power) across the three transformations.  
4. **Post‑hoc**: Bonferroni‑corrected pairwise Wilcoxon signed‑rank tests to locate specific differences; fallback to Wilcoxon if ties prevent Friedman. Results saved in `results/friedman_summary.txt`.  
5. **α‑sensitivity sweep**: repeat Type I error estimation for α ∈ {0.01, 0.05, 0.10}; store in `results/sensitivity_results.csv`.

### Phase 6 – Reporting
- **Tables**: `results/aggregated_results.csv` (mean error/power, CI, n datasets, n iterations).  
- **Figures**: Bar plots of error rates and power by transformation/test (`results/figures/error_rates.png`, `power_curves.png`, `alpha_sweep.png`).  
- **Traceability**: Every figure/table references a single row in `data/datasets.csv`.  

All steps are CPU‑only, stream‑oriented, and checkpointed after each dataset to guarantee determinism on the GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `seaborn`, `matplotlib`, `datasets` (HuggingFace), `pyyaml`, `portalocker` (for atomic checkpoints)  
- **Storage**: Filesystem under `data/`, `results/`, `state/` (CSV/Parquet)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM, ≤ 6 h) – **CPU‑first**; no GPU required.  
- **Constraints**: Open‑source numeric datasets only, SHA‑256 checksums, fixed random seeds, checkpointing, streaming I/O for large files.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Download timeout (T001/T002) | Use HuggingFace loaders for the six verified numeric datasets (fast, cached); stream OpenML files with a 5 MB size cap; checkpoint after each dataset. |
| Transformation failure on negative values | Automatic log‑shift; logged in `imputation_log.csv`. |
| Bootstrap CI target not met | Target is a goal; we will report the achieved half‑width. |
| Power validation circularity | Provide both analytical normal‑theory power **and** a bootstrap‑derived empirical power as independent references. |
| Friedman test ties | Fall back to Wilcoxon signed‑rank; log fallback in `results/friedman_summary.txt`. |
| Missing group label | Exclude dataset, log in `exclusions.csv`. |
| Imputation impact confound | Run a sensitivity analysis comparing mean vs median imputation and report any systematic differences. |
| Dataset selection bias | Include a stratified range of Shapiro‑Wilk p‑values to capture mild to strong non‑normality. |
| Simulation shape collapse | Generate simulations per dataset using its own skewness/kurtosis rather than an average. |
| Null‑simulation latent structure | Use stratified shuffling and residual permutation to better approximate a true null. |

---



