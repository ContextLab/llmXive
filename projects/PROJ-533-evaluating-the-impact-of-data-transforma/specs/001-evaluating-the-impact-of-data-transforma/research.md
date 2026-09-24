# Research: Evaluating the Impact of Data Transformation on Statistical Test Sensitivity

## Executive Summary

This research investigates the robustness of parametric tests (t-test, ANOVA) to violations of normality under three common transformation strategies: Box-Cox, Yeo-Johnson, and rank-based inverse normal transformation (INT).

**Methodological Correction**: Type I error estimation is performed **exclusively on simulated data** where the null hypothesis (independence of X and Y) is guaranteed by construction. Real-world data is used **only** to characterize distribution shapes (skew, kurtosis) which inform the simulation parameters. This avoids the methodological flaw of shuffling labels on real-world data which may contain latent confounds.

Using real-world datasets from UCI and OpenML, we filter for non-normal continuous variables, measure their skewness/kurtosis, and then generate **distribution-matched simulated data** to estimate Type I error and power. The study adheres to strict reproducibility standards, using fixed seeds and public, verifiable data sources.

## Dataset Strategy

### Verified Datasets

The following datasets are the **only** sources used for this research. All URLs are verified and publicly accessible via HuggingFace datasets or direct links as provided in the project inputs. These datasets are selected specifically for containing **continuous numerical variables** and **categorical group labels** suitable for Shapiro-Wilk testing and t-test/ANOVA.

| Dataset Name | Source | URL | Format | Continuous Variables | Group Label | Notes |
|:--- |:--- |:--- |:--- |:--- |:--- |:--- |
| UCI Wine | UCI | ` | CSV | `alcohol`, `malic_acid`, `ash`, `alcalinity_of_potash`, `magnesium`, `phenols`, `flavanoids`, `nonflavanoid_phenols`, `proanthocyanins`, `color_intensity`, `hue`, `od280/od315_of_diluted_wines`, `proline` | `class` (3 cultivars) | Classic numeric dataset. |
| UCI Wine Quality Red | UCI | ` | CSV | `fixed acidity`, `volatile acidity`, `citric acid`, `residual sugar`, `chlorides`, `free sulfur dioxide`, `total sulfur dioxide`, `density`, `pH`, `sulphates`, `alcohol` | `quality` (binned) | Continuous chemical measures. |
| UCI Wine Quality White | UCI | ` | CSV | Same as Red | `quality` (binned) | Continuous chemical measures. |
| OpenML Adult | OpenML | ` | CSV | `age`, `fnlwgt`, `education-num`, `capital-gain`, `capital-loss`, `hours-per-week` | `class` (income) | Large numeric dataset. |
| OpenML Covertype | OpenML | ` | CSV | `elevation`, `aspect`, `slope`, `horizontal_dist_to_hydrology`, `vertical_dist_to_hydrology`, `horizontal_dist_to_roadways`, `horizontal_dist_to_fire_points` | `Cover_Type` (7 classes) | Numeric terrain data. |
| UCI Bank Marketing | UCI | ` | CSV | `age`, `duration`, `campaign`, `pdays`, `previous`, `emp.var.rate`, `cons.price.idx`, `cons.conf.idx`, `euribor3m`, `nr.employed` | `y` (subscription) | Economic indicators. |
| UCI Concrete | UCI | ` | XLS | `Cement`, `Blast Furnace Slag`, `Fly Ash`, `Water`, `Superplasticizer`, `Coarse Aggregate`, `Fine Aggregate`, `Age` | (Continuous target, binned for ANOVA) | Physical properties. |
| UCI Abalone | UCI | ` | CSV | `Length`, `Diameter`, `Height`, `Whole weight`, `Shucked weight`, `Viscera weight`, `Shell weight` | `Sex` (M, F, I) | Biological measurements. |
| OpenML Car Evaluation | OpenML | ` | CSV | (Ordinal numeric) | `class` | Discrete numeric. |
| OpenML Seeds | OpenML | ` | CSV | `area`, `perimeter`, `compactness`, `length`, `width`, `asymmetry`, `groove` | `variety` (3 types) | Seed measurements. |

**Selection Criteria**:
1. **Continuous Variables**: Must contain at least one continuous numerical variable suitable for Shapiro-Wilk testing.
2. **Group Labels**: Must contain at least one categorical variable with ≥2 levels for t-test/ANOVA applicability.
3. **Non-Normality**: Must pass Shapiro-Wilk test (p < 0.05) on at least one continuous variable.
4. **Sample Size**: N ≥ 30.
5. **Missing Data**: < 10% missing values (imputed otherwise).
6. **Non-Normality Stratification**: Datasets will be analyzed for skewness and kurtosis to ensure the simulation pool covers a representative range (mild to extreme).

**Data Acquisition Plan**:
- Use `datasets.load_dataset()` or direct `requests` for CSV/Parquet files.
- Stream data where necessary to fit memory constraints (`pandas.read_csv(chunksize=...)`).
- Compute SHA-256 checksums immediately upon download and store in `data/checksums.csv`.
- Log all download failures and exclusions in `data/exclusions.csv`.
- **Programmatic Discovery**: If the static list is insufficient for 50 datasets, query OpenML for datasets with `numeric` features and `categorical` targets.

### Dataset Variable Fit

**Confirmation**: The selected datasets contain continuous variables (e.g., `alcohol`, `residual sugar`, `age`, `elevation`) and categorical labels (e.g., `class`, `Sex`, `Cover_Type`).
- **Predictors**: Continuous variables (e.g., `alcohol`, `age`).
- **Outcome**: Group labels (e.g., `class`, `Sex`).
- **Covariates**: None explicitly required for the core analysis, but demographic variables (if present) will be noted.

**Constraint Check**:
- **Missing Variables**: If a dataset lacks a categorical group label with ≥2 levels, it is excluded.
- **Non-Normality**: If a dataset is normally distributed (p ≥ 0.05), it is excluded from the Type I error analysis (as the premise is non-normal data).
- **Skewness/Kurtosis**: Datasets will be stratified by skewness/kurtosis to ensure the simulation covers a representative range of non-normality.

## Methodology

### Phase 1: Data Acquisition and Filtering
1. **Download**: Fetch datasets from verified URLs.
2. **Checksum**: Compute SHA-256 and record.
3. **Filter**:
 - Identify continuous variables.
 - Identify categorical group labels.
 - Apply Shapiro-Wilk test to continuous variables.
 - **Stratify**: Measure skewness and kurtosis. Exclude if N < 30 or missing > 10%.
 - Exclude if p ≥ 0.05 (for all continuous variables) OR if skewness/kurtosis is trivial (to ensure non-normality).
 - Impute missing values (mean/median) if ≤ 10%.

### Phase 2: Distribution Characterization
1. **Analyze**: For each filtered dataset, calculate skewness and kurtosis for all continuous variables.
2. **Stratify**: Group datasets by skewness/kurtosis magnitude (mild, moderate, extreme).
3. **Sample**: Select a representative subset of datasets from each stratum to inform the simulation parameters.

### Phase 3: Type I Error Estimation (Simulated Null)
1. **Generate Null Data**: Create simulated datasets where X and Y are **guaranteed independent**. Use the distribution shapes (skew/kurtosis) measured in Phase 2 to generate the marginal distributions of X. Y is generated as random noise independent of X.
2. **Transform**: Apply Box-Cox, Yeo-Johnson, and Rank-based INT.
3. **Test**: Run t-test/ANOVA.
4. **Estimate**: Proportion of p < 0.05 is the Type I error estimate.
5. **Iterations**: N = 2400 iterations per condition to meet SC-004 CI target (±0.02).

### Phase 4: Power Analysis (Simulated Alternative)
1. **Generate Alt Data**: Create simulated datasets with known effect sizes (Cohen's d: small, medium, large). **Crucially**, the data is generated to match the **distribution shapes (skew/kurtosis)** observed in the filtered real-world datasets.
2. **Transform & Test**: Apply transformations and run t-test/ANOVA.
3. **Re-calculate Effect Size**: After transformation, re-calculate the effective Cohen's d in the transformed space to ensure the ground truth is valid.
4. **Power Estimate**: Proportion of significant results (p < 0.05).
5. **Confidence Intervals**: Bootstrap CIs (target half-width ±0.02).

### Phase 5: Aggregation and Reporting
1. **Aggregate**: Compute mean Type I error and power per transformation-test combination.
2. **Statistical Test**: Use **Generalized Linear Mixed Model (GLMM)** with binomial distribution to assess transformation effect, accounting for correlation within datasets. (Friedman test is inappropriate for correlated proportions).
3. **Post-hoc**: Pairwise comparisons with Bonferroni correction.
4. **Sensitivity**: Sweep α (0.01, 0.05, 0.10) and report how false-positive rates vary (FR-008).
5. **Validation**: Calculate bootstrap CI half-width and verify against ±0.02 target (SC-004).
6. **Visualization**: Bar plots (matplotlib/seaborn) with error bars.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Bonferroni correction applied for post-hoc pairwise comparisons (FR-008).
- **Sample Size/Power**: **Justification**: For a worst-case power of 0.5, N=1000 yields SE ~0.0158 (CI half-width ~0.031). To meet SC-004 target of ±0.02, N=2400 is required (SE ~0.01, half-width ~0.02).
- **Causal Inference**: Findings are **associational**. No causal claims are made about transformation effects (Assumption: Inference Framing).
- **Measurement Validity**: No questionnaires used; data from public repositories with documented definitions.
- **Collinearity**: Transformations are mutually exclusive per variable; no collinearity diagnostics required.
- **Threshold**: α = 0.05 (standard); sensitivity analysis performed.
- **Shapiro-Wilk Sensitivity**: Acknowledged bias towards large datasets; mitigated by using skewness/kurtosis stratification.
- **GLMM**: Used instead of Friedman test to correctly handle correlated error rates within datasets.

## Compute Feasibility

- **CPU-First**: All statistical tests (t-test, ANOVA, Shapiro-Wilk, GLMM) and transformations are computationally lightweight and run efficiently on CPU.
- **Memory**: Streaming and chunked processing ensure datasets fit within a moderate amount of RAM.
- **Time**: Pipeline designed to complete within 6 hours on GitHub Actions. Checkpointing ensures resumption.
- **GPU**: Not required. No deep learning models or large matrix operations are used.

## Risks and Mitigations

- **Risk**: Dataset lacks group labels.
 - *Mitigation*: Filter out during Phase 1; log to `data/exclusions.csv`.
- **Risk**: Transformation fails (e.g., Box-Cox on negative data).
 - *Mitigation*: Apply log-shift; log intervention; skip if still fails.
- **Risk**: Type I error estimate is 0 (all non-significant).
 - *Mitigation*: Record 0; compute bootstrap CI (which may be [0, 0] or small upper bound).
- **Risk**: Runtime exceeds 6 hours.
 - *Mitigation*: Checkpoint after each dataset; resume from last checkpoint.
- **Risk**: Insufficient numeric datasets.
 - *Mitigation*: Use programmatic OpenML query to discover additional numeric datasets.
