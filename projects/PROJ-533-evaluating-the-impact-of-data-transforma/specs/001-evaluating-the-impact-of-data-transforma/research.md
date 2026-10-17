# Research: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Executive Summary
We assess how three common transformations—Box‑Cox, Yeo‑Johnson, and rank‑based inverse normal—affect the **Type I error rate** and **statistical power** of parametric tests (t‑test, ANOVA) when applied to non‑normal data. Real‑world datasets are used to **characterize distribution shapes** (skewness, kurtosis). **Type I error** is estimated **by shuffling group labels on the filtered real datasets** (multiple iterations, fixed seed), per FR‑004 and US‑2. **Power** is estimated on simulated datasets with known Cohen’s d (small, medium, large) that share the same marginal shapes. Results are aggregated across ≥ 50 datasets, bootstrap confidence intervals (target half‑width ± 0.02) are computed, and a **Friedman test** (non‑parametric repeated‑measures ANOVA) with Bonferroni‑corrected post‑hoc comparisons evaluates whether transformation choice systematically influences error rates. The pipeline runs entirely on a CPU‑only GitHub Actions runner.

## Dataset Strategy

### Verified Datasets
Only the URLs listed below are used directly; additional OpenML datasets are discovered via the public API (no hard‑coded URLs).

| Dataset | Source | URL | Format | Continuous Variables | Group Label |
|:---|:---|:---|:---|:---|:---|
| UCI HAR Test | UCI | ` | CSV | 561 sensor features | `activity` (6 classes) |
| UCI Shopper Train | UCI | ` | Parquet | 13 numeric attributes | `store_id` (categorical) |
| UCI NLP Drop | UCI | ` | Parquet | 30 numeric embeddings | `label` (binary) |
| Reddit URLs Test | URLs | ` | CSV | 5 numeric URL‑derived features | `spam` (binary) |
| Malicious URLs Train | URLs | ` | Parquet | 12 numeric features | `malicious` (binary) |
| Nowiki Abstract URLs | URLs | ` | Parquet | 8 numeric text metrics | `has_abstract` (binary) |
| Bounded Null Parquet (SHA‑256 example) | SHA‑256 | ` | Parquet | – (used only for checksum demonstration) | – |

**Selection Criteria** (applied to the full OpenML query):
1. Contains ≥ 1 continuous numeric variable.  
2. Contains a categorical group label with ≥ 2 levels.  
3. Shapiro‑Wilk on at least one continuous variable yields **p < 0.05**.  
4. Sample size **N ≥ 30**.  
5. Missingness **< 10 %** (otherwise imputed).  

If the static list above does not reach 50 datasets, the pipeline queries OpenML for additional datasets meeting the same criteria; each discovered URL is verified at download time.

### Dataset Variable Fit
- **Predictors**: All continuous variables listed per dataset.  
- **Outcome**: The categorical group label (e.g., `activity`, `spam`).  
- **Covariates**: None required for core analysis; additional numeric columns are treated as extra predictors.  

All selected datasets satisfy the predictor/outcome requirements; any dataset lacking a group label is excluded and logged (`data/exclusions.csv`).

## Methodology

### Phase 1 – Acquisition & Filtering
1. **Download** each verified URL, compute SHA‑256, record in `data/checksums.csv`.  
2. **Impute** missing values ≤ 10 % using mean (numeric) or median (skewed) per variable; log rates in `data/imputation_log.csv`.  
3. **Filter**: Apply Shapiro‑Wilk to each continuous variable; retain datasets where any variable has **p < 0.05**. Exclude datasets failing N ≥ 30 or missingness thresholds; log in `data/exclusions.csv`.  

### Phase 2 – Distribution Characterization
Compute **skewness** and **kurtosis** for each retained continuous variable; aggregate per‑dataset averages. Stratify datasets into **mild**, **moderate**, and **extreme** non‑normality bins to guide simulation parameter selection.

### Phase 3 – Type I Error Estimation (Real‑Data Label Shuffling — primary FR‑004 method)
For each filtered real dataset **D**:
1. **Shuffle** the group labels **N = 5000** times using a **fixed random seed** recorded in `results/simulation_seeds.txt` (per Constitution Principle VII).  
2. **Apply** the three transformations (Box‑Cox, Yeo‑Johnson, rank‑based inverse normal) to the continuous variables, with λ optimized per dataset.  
3. **Run** the appropriate parametric test (t‑test for binary groups, one‑way ANOVA for ≥ 2 groups) on each transformed version of the data under each shuffled labeling.  
4. **Record** the proportion of p < 0.05 as the Type I error estimate for that transformation‑test pair (FR‑004, US‑2 acceptance scenario 2).  
5. **Sanity check** (optional, diagnostic only): compare against simulated null datasets preserving marginal shapes (Phase 3a); these results are logged but never used for the primary FR‑004 estimate.

### Phase 3a – Simulated Null (Optional Diagnostic Only)
Generate marginal‑shape‑preserving null datasets (independent predictor and label) and compute error rates; used solely to verify that real‑data label‑shuffling estimates are consistent with shape‑matched simulation. Not used for the primary FR‑004 metric.

### Phase 4 – Simulated Alternative Data (Power)
For each effect size **d ∈ {0.2 (small), 0.5 (medium), 0.8 (large)}**:
1. **Generate** predictor **X** with the same marginal shape as in Phase 2.  
2. **Generate** group label **Y** such that the difference in means yields the target **Cohen’s d**.  
3. **Apply** the three transformations.  
4. **Run** the same tests; repeat **1000** times per effect size, transformation, and test.  
5. **Compute** **power** as the proportion of significant results.

### Phase 5 – Aggregation & Inference
1. **Bootstrap** (10 000 resamples) the per‑dataset error/power rates to obtain 95 % CIs; enforce half‑width ≤ 0.02 (SC‑004).  
2. **Friedman Test (FR‑008)**: For each test type and metric, perform a Friedman test (non‑parametric repeated‑measures ANOVA, `scipy.stats.friedmanchisquare`) on the per‑dataset error (or power) values across the three transformations, treating datasets as repeated measures.  
3. **Post‑hoc**: Conduct **Bonferroni‑corrected** pairwise Wilcoxon signed‑rank comparisons among transformations to identify specific differences.  
4. **Sensitivity Sweep**: Repeat Type I error estimation for α ∈ {0.01, 0.05, 0.10} and record in `results/sensitivity_results.csv`.  

### Phase 6 – Reporting
- **Tables**: `results/aggregated_results.csv` (mean error/power, CI, n_datasets, n_iterations).  
- **Inference**: `results/friedman_summary.txt` (Friedman statistics, p‑values, Bonferroni‑corrected post‑hoc results), modeled by the `FriedmanResult` entity in `data-model.md`.  
- **Figures**: Bar plots of error rates and power by transformation/test, plus α‑sweep curves (`results/figures/`).  
- All outputs are traceable to a single row in `data/datasets.csv` (Principle IV).  

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: Bonferroni correction applied to all post‑hoc pairwise tests (FR‑008).  
- **Power Justification**: 5000 shuffles for Type I error and 1000 simulations per effect size give SE ≈ 0.01, satisfying the ±0.02 CI half‑width requirement (SC‑004).  
- **Causal Framing**: Findings are **associational**; no causal claims (Assumption section).  
- **Measurement Validity**: All variables are defined in the original public datasets; no questionnaire instruments are used.  
- **Collinearity**: Transformations are applied separately; no multicollinearity concerns.  
- **Friedman Choice**: The Friedman test (non‑parametric repeated‑measures ANOVA) is the FR‑008‑mandated method; it handles the repeated‑measures structure (same datasets observed under all three transformations) without normality assumptions on the error rates.

## Compute Feasibility
All steps are CPU‑only and use streaming/chunked I/O to stay well within the ~7 GB runner RAM limit. Total wall‑clock time is estimated ≤ 5 h on the free‑tier GitHub Actions runner. No GPU resources are required.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Insufficient open datasets | Programmatic OpenML search expands the pool; each discovered dataset is validated before inclusion. |
| Transformation on negative values | Automatic log‑shift; intervention logged (`data/imputation_log.csv`). |
| Long runtime | Checkpoint after each dataset (T004) and resume (`--resume` flag). |
| Friedman test degenerate cases | Fall back to pairwise Wilcoxon signed‑rank tests with Bonferroni correction; fallback logged in `results/friedman_summary.txt`. |
| Missing group label | Exclude and record in `data/exclusions.csv`. |