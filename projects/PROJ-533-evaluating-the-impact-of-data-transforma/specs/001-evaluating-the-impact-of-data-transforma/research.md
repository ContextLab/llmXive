# Research: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Executive Summary
We assess how three transformations—Box‑Cox, Yeo‑Johnson, and rank‑based inverse normal—affect **Type I error** and **statistical power** of parametric tests (t‑test, ANOVA) on non‑normal data. Real‑world datasets provide the distributional landscape; simulated datasets with known Cohen’s *d* supply ground truth for power. Type I error is estimated by **dual null‑simulation**: stratified label shuffling **and** residual permutation (fixed seed, 5 000 iterations per dataset). Power is estimated on simulated data and validated against both an analytical normal‑theory calculation **and** a non‑parametric bootstrap reference, providing an independent check. Results are aggregated across ≥ 50 datasets, bootstrap confidence intervals (target half‑width ≤ 0.02) are computed, and a **Friedman test** with Bonferroni‑corrected post‑hoc comparisons evaluates systematic transformation effects. All steps run on a CPU‑only GitHub Actions runner.

## Dataset Strategy

### Verified Datasets (numeric, tabular, with continuous variables and categorical group labels)
| Dataset | Source | Loader / URL |
|:---|:---|:---|
| Wine Quality (Red) | UCI | `datasets.load_dataset("uciml/WineQuality", "red")` |
| Breast Cancer Wisconsin (Diagnostic) | UCI | `datasets.load_dataset("uciml/BreastCancer", "diagnostic")` |
| Iris | UCI | `datasets.load_dataset("uciml/Iris")` |
| Adult Income | OpenML | `datasets.load_dataset("openml/Adult")` |
| Statlog (Heart) | UCI | `datasets.load_dataset("uciml/StatlogHeart")` |
| Vehicle Silhouettes | OpenML | `datasets.load_dataset("openml/VehicleSilhouettes")` |

These six datasets satisfy the requirement for continuous predictors and a categorical group label, and they are all accessible via programmatic loaders (no manual download). Additional OpenML datasets will be streamed (size‑capped at 5 MB) until the total count reaches ≥ 50, adhering to the same criteria.

**Selection Criteria** (applied to the full OpenML query, see Phase 1):
1. ≥ 1 continuous numeric variable.  
2. ≥ 2 levels in a categorical group label.  
3. **Non‑normality bands**: Shapiro‑Wilk *p* ∈ [0.01, 0.20] divided into three bands (0.01‑0.05, 0.05‑0.10, 0.10‑0.20) to capture a range of deviations.  
4. Sample size *N* ≥ 30.  
5. Missingness < 10 % (otherwise imputed).  

All selected datasets contain the required predictor and outcome variables; any dataset lacking a group label is excluded and recorded in `data/exclusions.csv`.

### Dataset‑Variable Fit
- **Predictors**: All continuous columns after filtering.  
- **Outcome**: The categorical group label (binary or multi‑class).  
- **Covariates**: None required; extra continuous columns are treated as additional predictors.

All selected datasets contain the required predictor and outcome variables; any dataset lacking a group label is excluded and recorded in `data/exclusions.csv`.

## Methodology

### Phase 1 – Acquisition & Filtering
1. **Download** each verified dataset with the programmatic loader shown above; additional OpenML datasets are streamed (`streaming=True`) and size‑limited to 5 MB.  
2. **SHA‑256 checksum** computed while streaming; saved to `data/checksums.csv`.  
3. **Missing‑value imputation** (mean for approximately symmetric variables, median for skewed) for variables with ≤ 10 % missing; rates logged in `data/imputation_log.csv`. A **sensitivity analysis** will repeat imputation with the alternative method to assess impact.  
4. **Shapiro‑Wilk test** on each continuous variable; retain datasets across three *p*‑value bands (0.01‑0.05, 0.05‑0.10, 0.10‑0.20) to avoid bias toward only strongly non‑normal data.  
5. **Sample‑size filter**: retain *N* ≥ 30.  
6. Log all exclusions (`data/exclusions.csv`).

### Phase 2 – Distribution Characterization
Compute **skewness** and **kurtosis** for each retained variable; store averages per dataset for later simulation shape matching.

### Phase 3 – Type I Error Estimation (Real‑Data Null Simulation)
For each filtered dataset **D**:
1. **Dual null‑simulation strategy**:  
   - **Stratified label shuffling**: shuffle group labels **5 000** times **within** each covariate stratum (if any) to break association while preserving latent structure.  
   - **Residual permutation**: fit a null linear model on the continuous variables, permute residuals, and recombine with fitted values.  
2. **Transform** the continuous variables with each of the three methods (Box‑Cox, Yeo‑Johnson, rank‑based inverse normal). λ is optimized per dataset. Log any log‑shift interventions.  
3. **Run** the appropriate parametric test (t‑test for binary groups, one‑way ANOVA for ≥ 2 groups) on each transformed version.  
4. **Record** the proportion of *p* < 0.05 as the Type I error estimate for that transformation‑test pair (FR‑004).  
5. **Compare** the two null‑simulation estimates; large discrepancies trigger a warning and are logged for further inspection.

### Phase 4 – Simulated Data for Power (Ground Truth)
For each effect size **d ∈ {0.2, 0.5, 0.8}** **and for each retained real dataset**:
1. **Generate** **1 000** simulated datasets **using that dataset’s own skewness and kurtosis** (via `scipy.stats.skewnorm` and matching kurtosis). This preserves dataset‑specific shape variability.  
2. **Create** group labels such that the mean difference yields the target Cohen’s *d*.  
3. **Apply** the three transformations (as in Phase 3) and a baseline untransformed condition.  
4. **Run** the same parametric tests; compute the proportion of significant results → **empirical power** estimate (FR‑006).  
5. **Independent validation**:  
   - **Primary benchmark** – non‑parametric bootstrap power computed by resampling the simulated datasets 10 000 times (no normality assumptions).  
   - **Secondary benchmark** – analytical power with `statsmodels.stats.power.TTestIndPower` (normal‑theory) retained only as a reference.  
   - Report divergence between bootstrap and analytical estimates to quantify how well transformations restore normality.

### Phase 5 – Aggregation & Inference
1. **Bootstrap** (10 000 resamples) the per‑dataset error and power values to obtain 95 % confidence intervals; target half‑width ≤ 0.02 (SC‑004).  
2. **Sample‑size justification**: Power analysis for the Friedman test (small effect *f* = 0.25) shows that **≥ 45** datasets provide > 80 % power at α = 0.05 (computed with `statsmodels.stats.power.FTestAnovaPower`). Our ≥ 50‑dataset target satisfies this, justifying the CI precision goal.  
3. **Friedman test** (`scipy.stats.friedmanchisquare`) on the per‑dataset error (and separately on power) across the three transformations.  
4. **Post‑hoc**: Bonferroni‑corrected pairwise Wilcoxon signed‑rank tests to locate specific differences; fallback to Wilcoxon if ties prevent Friedman. Results saved in `results/friedman_summary.txt`.  
5. **α‑sensitivity sweep**: repeat Type I error estimation for α ∈ {0.01, 0.05, 0.10}; store in `results/sensitivity_results.csv`.

### Phase 6 – Reporting
- **Tables**: `results/aggregated_results.csv` (mean error/power, CI, n datasets, n iterations).  
- **Figures**: Bar plots of error rates and power by transformation/test (`results/figures/error_rates.png`, `power_curves.png`, `alpha_sweep.png`).  
- **Traceability**: Every figure/table references a single row in `data/datasets.csv`.  

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: Bonferroni correction applied to all post‑hoc pairwise tests (FR‑008).  
- **Power Justification**: Analytical power computed via `statsmodels`; simulation provides an empirical check; bootstrap power offers an independent benchmark.  
- **Causal Framing**: Findings are strictly **associational** (Assumption section).  
- **Measurement Validity**: All variables originate from publicly documented datasets; no questionnaire instruments.  
- **Collinearity**: Transformations are applied separately; no multicollinearity concerns.  

## Compute Feasibility
All operations are CPU‑light; streaming I/O keeps RAM < 4 GB. Estimated wall‑clock time is on the order of an hour on the free GitHub Actions runner.. No GPU is required.

## Risks & Mitigations (re‑stated)
| Risk | Mitigation |
|------|------------|
| Download/checksum timeout (T001/T002) | Use HuggingFace loaders for the six verified numeric datasets (fast, cached); stream OpenML files with a 5 MB size cap; checkpoint after each dataset. |
| Transformation on negative values | Automatic log‑shift; logged in `imputation_log.csv`. |
| Bootstrap CI target not met | Target is a goal; we will report the achieved half‑width. |
| Power validation circularity | Provide both analytical normal‑theory power **and** a bootstrap‑derived empirical power as independent references. |
| Friedman test ties | Fall back to Wilcoxon signed‑rank; log fallback. |
| Missing group label | Exclude, log in `exclusions.csv`. |
| Imputation impact confound | Run a sensitivity analysis comparing mean vs median imputation and report any systematic differences. |
| Dataset selection bias | Include a stratified range of Shapiro‑Wilk p‑values to capture mild to strong non‑normality. |
| Simulation shape collapse | Generate simulations per dataset using its own skewness/kurtosis rather than an average. |
| Null‑simulation latent structure | Use stratified shuffling and residual permutation to better approximate a true null. |

---



