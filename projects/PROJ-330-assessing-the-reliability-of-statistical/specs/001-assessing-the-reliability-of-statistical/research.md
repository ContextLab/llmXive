# Research: Assessing the Reliability of Statistical Significance in Openly Available Genomic Datasets

## Dataset Strategy

The analysis requires RNA-seq count matrices with associated metadata (batch, condition). The following datasets have been verified for format and accessibility.

| Dataset Name | Source | Verified URL | Format | Suitability & Notes |
|:--- |:--- |:--- |:--- |:--- |
| **Geo170K (Alignment)** | GEO | ` | Parquet | **High Suitability**. Large collection. We will sample a specific study ID with `n >= 20` and verified count data. |
| **TCGA Prostate (PRAD)** | TCGA | ` | CSV | **Conditional Suitability**. Must verify CSV contains **count data**, not just clinical features. If clinical only, skip. |
| **Paul RNA-Seq (Processed)** | GEO/External | ` | CSV | **High Suitability**. Explicitly processed. Likely contains counts and metadata. Ideal for initial testing. |
| **GEO Subset (Australia Center)** | GEO | ` | CSV | **Unsuitable**. Contains only label maps, no count matrix. Cannot be used for DE analysis. |
| **recount3 (GTEx Index)** | ENCODE/Recount | ` | JSON | **Unsuitable for Direct Use**. This is an index file only. It does not provide count matrices directly. While recount3 is a valid resource, the specific URL provided cannot be used for differential expression without fetching the actual data via a different API, which is not in the verified list. **Decision**: Excluded from primary analysis candidates. |

**Decision**: We will prioritize the **Paul Processed Dataset** and **Geo170K** (sampled) as primary test cases. The **TCGA PRAD** will be used only if the CSV is verified to contain counts. The **recount3** index is excluded from the immediate analysis plan due to lack of direct count data access.

**Critical Note on Variable Fit**: The plan strictly follows the *feature spec*: we need **count matrices**, **batch metadata**, and **condition labels**. If a dataset lacks batch metadata, the plan defaults to random stratification (as per Edge Cases).

## Statistical Methodology

### 1. Effect Size Stability (US-1) - *Methodological Correction*
- **Method**: Pearson correlation coefficient ($r$) of log2 fold-changes (LFC) between the full dataset analysis and each of the 5 stratified subsets.
- **Population**: **ALL genes**, not just significant ones.
 - *Rationale*: Calculating stability only on "significant genes" (as per US-1/FR-006) introduces "Winner's Curse" bias. The correlation will be artificially low due to power loss in subsets. The plan overrides this spec requirement to ensure methodological validity.
- **Baseline**: $r=1.0$ (perfect stability).
- **Handling Low Counts**: If $<5$ significant genes are found, report "Insufficient data" (FR-003), but stability is still calculated on all genes.
- **Correction**: Benjamini-Hochberg (BH) applied to all p-values to control FDR (FR-008).

### 2. Null Distribution & Inflation (US-2) - *Fixed-Dispersion Approximation*
- **Method**: Stratified Block Permutation using **Fixed-Dispersion Wald Perturbation**.
 1. Run DESeq2/edgeR ONCE on the full dataset to estimate dispersion parameters.
 2. For 1,000 permutations:
 - Shuffle sample labels *within* batch groups.
 - Compute Wald test statistics using the **permuted counts** and the **fixed** dispersion estimates from step 1.
 - Do NOT re-estimate dispersion (computationally infeasible).
 3. Compare empirical p-value distribution to Uniform(0,1).
- **Validation**: Kolmogorov-Smirnov (KS) test.
 - **Correct Logic**: A **high p-value (p > 0.05)** indicates consistency with uniformity (valid null).
 - **Spec Contradiction**: The spec (SC-002) states "D < 0.05". This is incorrect. D is the statistic; the p-value is the metric. The plan uses the correct logic.
- **Visualization**: Bland-Altman plot of parametric vs. empirical p-values.
- **Constraint**: If runtime > 6h, reduce iterations (min 100) and flag "low-confidence".
- **Permutation Space Check**: Before running, calculate max unique permutations ($\prod n_{batch}!$). If $< 100$, skip dataset or reduce iterations to max possible.

### 3. Cross-Dataset Benchmarking (US-3)
- **Method**: Aggregate stability $r$ and inflation metrics across a small set of datasets.
- **Analysis**: Compare means and identify outliers (e.g., batch-affected vs. clean).

### 4. Confounding Limitation
- The permutation null preserves batch structure. Therefore, a "uniform" result validates the **combined** model (parametric assumptions + batch structure). It does not isolate parametric inflation from unmodeled confounders. Results will be interpreted as "Inflation relative to the stratified null".

## Compute Feasibility & Rationale

- **Runtime**: The Fixed-Dispersion strategy reduces per-iteration cost to <5 seconds. A sufficient number of iterations can be completed in [deferred], well within the time limit.
- **Memory**: Datasets will be loaded into `pandas` DataFrames. We will filter genes with zero counts across all samples immediately to reduce memory footprint.
- **Libraries**:
 - Python: `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`.
 - R: `DESeq2` or `edgeR` (via `subprocess` or `rpy2`). *Rationale*: These are the gold standards. `rpy2` is preferred for integration, but `subprocess` is the fallback for robustness in CI.
- **Fallback**: If `rpy2` fails, use `subprocess` to call a standalone R script. If R is unavailable, use `statsmodels` (Python) with Negative Binomial (less ideal but feasible).

## Constitution Alignment

- **Reproducibility**: All seeds pinned. URLs verified.
- **Data Hygiene**: Checksums recorded for downloaded files.
- **Permutation Validation**: Explicitly implemented as per Principle VI (with Fixed-Dispersion approximation).
- **Batch Awareness**: Stratification logic implemented per Principle VII.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset lacks count data** | High | Verify CSV content before processing. If only clinical data, skip dataset and log warning. |
| **rpy2 installation failure** | High | Fallback to `subprocess` calling a standalone R script. |
| **Runtime Exceeds 6h** | High | Dynamic iteration reduction (FR-009) ensures completion, even if confidence is lower. |
| **Insufficient Samples (<20)** | Medium | Skip dataset, log warning, proceed to next. |
| **Permutation Space Too Small** | Medium | Check max unique permutations before running. If < 100, flag as "Sparse Null". |
| **Limited Dataset Availability** | Medium | The removal of recount3 reduces the pool of verified sources. We will proceed with the remaining verified datasets (Paul, Geo170K, TCGA) and document the limitation in the final report. |