# Research: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Executive Summary
We evaluate how Box‑Cox, Yeo‑Johnson, and rank‑based inverse normal transformations influence **Type I error** and **statistical power** of parametric tests (t‑test, ANOVA) when applied to non‑normal real‑world data. Datasets are obtained via a programmatic OpenML query (classification tasks, ≥ 30 rows, ≥ 1 continuous feature, ≤ 10 % missing) and supplemented with the six verified HuggingFace URLs when they meet the same criteria. Missing values are imputed (mean/median) with a K‑NN sensitivity branch. Type I error is estimated through stratified label shuffling (5 000 permutations per dataset, fixed seed = 42). Power is estimated on simulated datasets that preserve each real dataset’s skewness/kurtosis and embed known Cohen’s *d* ∈ {0.2, 0.5, 0.8}. Empirical power is compared against analytical power from `statsmodels.stats.power.TTestIndPower` (or `FTestAnovaPower` for >2 groups) as a sanity check rather than a circular benchmark. Results are aggregated with a hierarchical bootstrap (target CI half‑width ≤ 0.07). A Friedman test with Bonferroni‑corrected Wilcoxon post‑hoc comparisons evaluates systematic effects, and an α‑sensitivity sweep (α = 0.01, 0.05, 0.10) explores threshold dependence. All steps run on the GitHub Actions free‑tier CPU runner, checkpoint after each dataset, and respect the 6‑hour limit.

## Dataset Strategy

### Acquisition via OpenML (programmatic)
We query the OpenML API (using the `openml` Python client) with these filters:

1. **Task type**: Classification (ensures a categorical target).  
2. **Instances**: N ≥ 30.  
3. **Numeric features**: ≥ 1.  
4. **Missingness**: ≤ 10 % per feature.  
5. **Public download URL**: `download_url` provided by OpenML.  

The query iterates over result pages until **≥ 50** datasets satisfying all criteria are collected. For each dataset we record:

- `dataset_id`, `source_url`, `filename`, `checksum_sha256`, `sample_size`, `num_continuous_vars`, `shapiro_wilk_p`, `skewness`, `kurtosis`, `missing_pct`, `status`, `filter_reason`, `exclusion_details`.

These records are stored in `data/datasets.csv`. The OpenML query is deterministic; the same datasets are retrieved on every run.

### Supplement with Verified HuggingFace URLs
The following six URLs were pre‑verified as directly downloadable (see “Verified datasets” block). They are inspected; any that contain at least one continuous variable **and** a categorical group label are added to the pool to ensure breadth across domains (health, finance, image, etc.). Those that fail the criteria are logged and excluded.

- https://huggingface.co/datasets/udayl/UCI_HAR/resolve/main/csv_files/test.csv  
- https://huggingface.co/datasets/jlh/uci-shopper/resolve/main/data/train-00000-of-00001-3316810f8df41d3a.parquet  
- https://huggingface.co/datasets/ucinlp/drop/resolve/main/data/train-00000-of-00001.parquet  
- https://huggingface.co/datasets/autoregression/unsplash-1m-urls/resolve/main/data/train-00000-of-00001.parquet  
- https://huggingface.co/datasets/marksverdhei/reddit-syac-urls/resolve/main/test.csv  
- https://huggingface.co/datasets/joshtobin/malicious_urls/resolve/main/data/train-00000-of-00001-0ac5e739002d814a.parquet  

Only those passing the continuous‑variable + group‑label test are retained; the rest are recorded in `data/exclusions.csv`.

### Filtering (post‑download)
1. **Continuous variables** – at least one numeric column.  
2. **Group label** – categorical target with ≥ 2 levels.  
3. **Non‑normality** – Shapiro‑Wilk *p* < 0.05 on every continuous variable.  
4. **Sample size** – N ≥ 30.  
5. **Missingness** – ≤ 10 % per variable.  

Datasets failing any criterion are excluded, with the reason logged. If fewer than 45 datasets survive, Phase 5 will note the limitation and report the actual bootstrap CI width (still satisfying SC‑004).

## Methodology

### Phase 1 – Acquisition & Checksum
- Stream each dataset from OpenML (or the verified URLs), compute SHA‑256, write to `data/checksums.csv`.  
- After each successful download, write a checkpoint file (`results/checkpoints/download_{dataset_id}.json`) to enable resumption.

### Phase 2 – Imputation & Filtering
- Compute per‑variable missingness.  
- **Primary imputation**: mean for variables with |skewness| < 0.5, median otherwise. Log each imputation in `data/imputation_log.csv`.  
- **Sensitivity branch**: repeat the entire pipeline using K‑Nearest‑Neighbors imputation (k = 5).  
- Apply Shapiro‑Wilk (`scipy.stats.shapiro`) to each continuous variable; retain datasets where the *minimum* *p* < 0.05.  
- Verify presence of a categorical target; exclude otherwise.  

### Phase 3 – Null‑Simulation (Type I Error)
For every retained dataset **D** and each transformation (baseline, Box‑Cox, Yeo‑Johnson, rank‑inverse‑normal):

1. **Stratified label shuffling** – 5 000 permutations, respecting any observed covariate strata, using seed = 42.  
2. Optimise λ for Box‑Cox/Yeo‑Johnson via maximum‑likelihood (`scipy.stats.boxcox_normmax`).  
3. Run the appropriate parametric test (two‑sample t‑test or one‑way ANOVA).  
4. Record the proportion of *p* < 0.05 as the Type I error estimate.  

Residual permutation is **not** employed (per FR‑017).

### Phase 4 – Simulated Power Datasets
For each retained real dataset **R** and each effect size **d** ∈ {0.2, 0.5, 0.8}:

1. Generate 1 000 synthetic datasets preserving **R**’s empirical skewness and kurtosis via a moment‑matching algorithm.  
2. Assign binary group labels to achieve the target Cohen’s *d*.  
3. Apply the four transformations.  
4. Run the same parametric test; empirical power = proportion of *p* < 0.05.  
5. **Analytical benchmark**: compute theoretical power using `statsmodels.stats.power.TTestIndPower` (or `FTestAnovaPower` for >2 groups). Report the difference as a validation metric; no requirement that the empirical CI contain the analytical value, only that the comparison is reported (addresses reviewer comment on circularity).  

### Phase 5 – Hierarchical Aggregation & Inference
1. **Hierarchical bootstrap**: outer resample draws datasets with replacement (10 000 draws). For each sampled dataset, inner resample draws from its permutation‑based error‑rate or power estimates (1 000 draws). Compute the mean across the hierarchical sample; derive 95 % CI. Target half‑width ≤ 0.07 (SC‑004). If usable datasets < 45, report the actual half‑width and note the limitation.  
2. **Sample‑size justification**: power analysis for Friedman test (small effect *f* = 0.25) shows ≥ 45 datasets give > 80 % power at α = 0.05 (`statsmodels.stats.power.FTestAnovaPower`). Our ≥ 50‑dataset target satisfies this.  
3. **Friedman test** on Type I error and separately on power across the three transformations (`scipy.stats.friedmanchisquare`).  
4. **Post‑hoc**: Bonferroni‑corrected Wilcoxon signed‑rank pairwise tests; if ties prevent Friedman, fallback to Wilcoxon and log the decision.  
5. **α‑sensitivity sweep** – repeat null simulation for α ∈ {0.01, 0.05, 0.10}; store results in `results/sensitivity_results.csv`.  

### Phase 6 – Reporting
- **Tables**: `results/aggregated_results.csv` (mean, CI, half‑width, *n* datasets, *n* iterations).  
- **Figures**: Bar plots (`error_rates.png`, `power_curves.png`, `alpha_sweep.png`) generated with seaborn/matplotlib.  
- **Traceability**: Each figure/table footnote cites the exact row(s) in `data/datasets.csv` or `data/simulated_datasets.csv`.  

## Statistical Rigor & Assumptions
- **Multiple comparisons** – Bonferroni correction applied to all post‑hoc pairwise tests (FR‑009).  
- **Power validation** – Empirical power compared to analytical calculations; no circular expectation.  
- **Associational framing** – Findings are observational; no causal claims (Constitution Principle VII).  
- **Measurement validity** – Variables are taken directly from public repositories; no questionnaire instruments.  
- **Collinearity** – Transformations are mutually exclusive; no multicollinearity diagnostics required.  

## Compute Feasibility
All operations are NumPy/Pandas vectorised; peak memory < 4 GB. Estimated wall‑clock time on the free runner ≈ 1 hour. No GPU required.

## Risks & Mitigations (re‑stated)
| Risk | Mitigation |
|------|------------|
| Insufficient qualifying public datasets | Continue paging OpenML; supplement with the six verified HuggingFace URLs; record provenance. |
| Bootstrap CI precision unattainable | Target set to ≤ 0.07; if not met, report actual width (SC‑004 satisfied). |
| Transformation failure on negative values | Automatic log‑shift; log the intervention in `data/imputation_log.csv`. |
| Checkpoint race conditions | Use `portalocker` for atomic checkpoint writes; sequential ordering for all write‑heavy tasks. |
| Runtime limit breach | Check elapsed time after each dataset; abort gracefully with a checkpoint if approaching 6 h. |

---
