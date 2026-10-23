# Research: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Executive Summary
We assess how three transformations—Box‑Cox, Yeo‑Johnson, and rank‑based inverse normal—affect **Type I error** and **statistical power** of parametric tests (t‑test, ANOVA) on non‑normal data. Real‑world datasets are sourced exclusively via a **programmatic OpenML query** that selects public datasets containing at least one continuous numeric variable and a categorical group label. The seven URLs listed in the project constitution are unsuitable (they lack continuous variables or group labels), so we supplement with additional OpenML datasets that satisfy the criteria. Missing values are imputed (primary mean/median strategy, with a K‑NN sensitivity branch). Type I error is estimated using **stratified label shuffling** (5 000 permutations each) – residual permutation is **not** employed because it is inappropriate for simple t‑tests/ANOVA. Power is estimated on simulated datasets that preserve the empirical skewness/kurtosis of the real datasets and embed known Cohen’s *d* values. Results are aggregated, bootstrap confidence intervals are computed with a **target half‑width ≤ 0.02** (actual width reported if the target is unattainable), and a Friedman test with Bonferroni‑corrected post‑hoc comparisons evaluates systematic transformation effects. All steps run on the GitHub Actions free‑tier CPU runner.

## Dataset Strategy

### Acquisition via OpenML (programmatic)
We query the OpenML API with the following criteria:
1. **Task type**: Classification (to obtain a categorical target).  
2. **Number of instances**: N ≥ 30.  
3. **At least one numeric feature** (continuous).  
4. **Missingness**: ≤ 10 % per feature (checked after download).  
5. **Publicly accessible download URL** (OpenML provides a direct `download_url`).  

The query iterates over result pages until **≥ 50** datasets satisfying all criteria are collected. Each dataset’s metadata (source URL, SHA‑256 checksum, sample size, number of continuous variables, Shapiro‑Wilk p‑value, missingness) is recorded in `data/datasets.csv`. This strategy guarantees that every dataset used is a **public open‑source resource**, satisfying FR‑001.

**Note on Verified URLs:** The seven URLs listed in the constitution (e.g., `unsplash_urls`, `reddit_syac_test`) are URL‑list or hash datasets that lack the required continuous variables and categorical group labels. They are therefore excluded from analysis. Their presence is recorded for provenance, but they do not count toward the 50‑dataset requirement.

### Selection & Filtering Criteria (applied post‑download)
1. **Continuous Variables** – At least one numeric column.  
2. **Group Label** – The target column provided by OpenML (categorical with ≥ 2 levels).  
3. **Non‑Normality** – Shapiro‑Wilk *p* ∈ [0.01, 0.20] on each continuous variable; datasets where the minimum *p* falls outside this band are excluded.  
4. **Sample Size** – N ≥ 30.  
5. **Missingness** – ≤ 10 % per variable; imputed as described in Phase 2.  

All datasets that satisfy the above are recorded in `data/datasets.csv`. If after filtering fewer than 45 datasets remain, Phase 5 will note that the bootstrap CI half‑width target may be unattainable and will report the achieved precision.

## Methodology

### Phase 1 – Acquisition & Checksum
- Stream each file from OpenML, compute SHA‑256, store in `data/checksums.csv`.  
- Write a checkpoint after each download (`results/checkpoints/download_{dataset_id}.json`) for resumability.

### Phase 2 – Imputation & Filtering
- For each variable, compute missingness rate.  
- **Primary imputation**: mean for near‑symmetric variables (|skewness| < 0.5) and median for skewed.  
- **Sensitivity branch**: repeat the full analysis using K‑Nearest‑Neighbors imputation (k=5). Log rates in `data/imputation_log.csv`.  
- Perform Shapiro‑Wilk test on each continuous variable; retain datasets whose **minimum** *p* across variables falls in the target bands.  
- Verify presence of a categorical column; if absent, the dataset is excluded and recorded in `data/exclusions.csv`.

### Phase 3 – Null‑Simulation (Type I Error)
For every retained dataset **D**:
1. **Stratified label shuffling** – 5 000 permutations respecting any observed covariate strata.  
2. Apply each transformation (Box‑Cox, Yeo‑Johnson, rank‑inverse‑normal, baseline). λ for Box‑Cox/Yeo‑Johnson is optimized per variable via maximum likelihood.  
3. Run the appropriate parametric test (t‑test for two groups, one‑way ANOVA for >2 groups).  
4. Record the proportion of *p* < α (α = 0.05) as the Type I error estimate for each transformation‑test pair.  

**Residual permutation** is **not** used for inference because it assumes exchangeability of residuals, which is inappropriate for simple t‑tests/ANOVA. The residual‑permutation script remains in the repository for documentation only.

### Phase 4 – Simulated Power Datasets
For each retained real dataset **R** and each effect size **d** ∈ {0.2, 0.5, 0.8}:
1. Generate **1 000** synthetic datasets preserving **R**’s empirical skewness and kurtosis (via a moment‑matching procedure).  
2. Assign group labels achieving the target Cohen’s *d* (binary groups).  
3. Apply the three transformations + baseline.  
4. Run the same parametric test; compute empirical power as the proportion of significant results (α = 0.05).  
5. **Validation** – Compute a non‑parametric bootstrap power estimate (10 000 resamples) and an analytical normal‑theory power estimate (`statsmodels.stats.power.TTestIndPower`). Report both for transparency.

### Phase 5 – Aggregation & Inference
1. **Bootstrap** 10 000 resamples of per‑dataset error and power values to obtain 95 % CIs with **target half‑width ≤ 0.02**. **Feasibility check**: if usable datasets < 45, we will report the actual half‑width and note the limitation (still compliant with SC‑004).  
2. **Sample‑size justification** – Power analysis for the Friedman test (small effect *f* = 0.25) indicates ≥ 45 datasets give > 80 % power at α = 0.05 (`statsmodels.stats.power.FTestAnovaPower`). Our ≥ 50‑dataset goal satisfies this.  
3. **Friedman test** (`scipy.stats.friedmanchisquare`) on error rates and separately on power across the three transformations.  
4. **Post‑hoc** – Bonferroni‑corrected pairwise Wilcoxon signed‑rank tests; if ties prevent Friedman, fallback to Wilcoxon and log the decision.  
5. **α‑sensitivity sweep** – Repeat Type I error estimation for α ∈ {0.01, 0.05, 0.10}; store results in `results/sensitivity_results.csv`.  

### Phase 6 – Reporting
- **Tables**: `results/aggregated_results.csv` (mean, CI, half‑width, n_datasets, n_iterations).  
- **Figures**: Bar plots (`error_rates.png`, `power_curves.png`, `alpha_sweep.png`) generated with seaborn/matplotlib.  
- **Traceability**: Every figure/table includes a footnote referencing the exact row in `data/datasets.csv` (or synthetic source ID).  

## Statistical Rigor & Assumptions
- **Multiple Comparisons** – Bonferroni correction applied to all post‑hoc pairwise tests (FR‑008).  
- **Power Justification** – Analytical power calculations provide a reference; bootstrap power offers an independent, assumption‑free benchmark.  
- **Causal Framing** – Findings are strictly associational; no causal claims are made (Constitution Principle VII).  
- **Measurement Validity** – All variables are taken directly from the open datasets; no questionnaire instruments are involved.  
- **Collinearity** – Transformations are applied separately; no multicollinearity diagnostics are required (Assumption section).  

## Compute Feasibility
All components are vectorized NumPy/Pandas operations; peak RAM stays < 4 GB. Estimated wall‑clock time on the free runner is on the order of an hour. No GPU resources are required.

## Risks & Mitigations (re‑stated)
| Risk | Mitigation |
|------|------------|
| Insufficient verified datasets with group labels | Supplement with OpenML‑queried datasets; record provenance of all sources. |
| Dual null‑simulation overhead | Only label shuffling is used; residual permutation omitted, eliminating ambiguity. |
| Bootstrap CI precision unattainable | Target is documented; if the half‑width target cannot be met, the actual CI width is reported and the limitation is noted, satisfying SC‑004. |
| Checkpoint race conditions | Use `portalocker` for atomic writes; sequential ordering for file‑writing tasks. |
| Transformation failure on negative values | Automatic log‑shift applied; interventions logged in `data/imputation_log.csv`. |

---


