# Research: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

## 1. Dataset Strategy

The project relies on the **American Gut Project (AGP)** for 16S rRNA OTU count tables and associated metadata. The spec requires variables for `antibiotic_use_last_3mo`, `sleep_efficiency`, `sleep_duration`, and covariates (age, BMI, diet).

### Verified Datasets
Per the project constraints, only the following verified sources are available for citation. **Critical Note**: The provided "Verified datasets" block lists `turkishloyd` and `otus` datasets which appear to be generic or unrelated to the specific American Gut Project sleep/antibiotic variables required by the spec.

| Dataset Name | Verified URL | Relevance to Spec | Action Plan |
|:--- |:--- |:--- |:--- |
| OTU (parquet) | ` | **Unknown/Low**. This URL points to a dataset named "turkishloyd" which does not match the "American Gut Project" description in the spec. It likely lacks the specific sleep/antibiotic metadata required. | **HALT STRATEGY**: The plan will NOT simulate data. If this dataset lacks required columns, the pipeline will halt with a critical error: "Dataset missing required sleep/antibiotic metadata. No verified source available." |
| OTU (json) | ` | **Unknown/Low**. Similar to above, "otus" is a generic name. | **HALT STRATEGY**: Same as above. Used only for structural testing if the real AGP data is unavailable. |

**Dataset Fit Assessment**:
The spec explicitly assumes the American Gut Project contains `antibiotic_use_last_3mo` and sleep metrics. However, the **Verified datasets** block provided for this planning phase does **not** contain a verified URL for the American Gut Project.
* **Risk**: The dataset in the verified block does not match the spec's variable requirements.
* **Mitigation**: The `ingestion.py` script will include a rigorous column validation step. If the loaded dataset lacks `sleep_efficiency`, `sleep_duration`, or `antibiotic_use_last_3mo`, the script will:
 1. Check for proxy variables (e.g., `sleep_quality`, `hours_slept`).
 2. If proxies exist, proceed with a "Scope Narrowed" status (measuring self-reported quality).
 3. If *no* sleep variable (primary or proxy) exists, **HALT** with a fatal error: "Fatal: No sleep data available in verified sources. Pipeline cannot proceed."
 4. This ensures we do not proceed with a dataset that cannot answer the research question or simulate data.

## 2. Statistical Methodology

### 2.1 Alpha-Diversity Calculation (FR-002)
* **Method**: Shannon and Simpson indices.
* **Library**: `scikit-bio` (`skbio.diversity.alpha`).
* **Rationale**: These are standard, non-parametric measures of diversity robust to uneven sequencing depth. `scikit-bio` is CPU-tractable.
* **Handling Zero Counts**: Samples with zero OTU counts will be excluded prior to calculation to avoid `NaN` (Edge Case 2).

### 2.2 Correlation Analysis (FR-004, FR-007)
* **Method**: Spearman Rank Correlation.
* **Rationale**: Microbiome data is non-normal and compositional. Spearman is robust to outliers and monotonic (not necessarily linear) relationships.
* **Multiple Comparison Correction**: Benjamini-Hochberg (BH) procedure.
 * **Application**: Applied separately to:
 1. Diversity metric vs. Sleep metric tests (2-4 tests).
 2. Taxon-level tests (thousands of tests).
 * **Implementation**: `statsmodels.stats.multitest.multipletests` with method `'fdr_bh'`.
* **Compositional Data Handling**: Taxon-level analysis will use **Centered Log-Ratio (CLR)** transformation before correlation.
 * **Risk Acknowledgment**: While CLR reduces compositionality effects, spurious correlations may still persist. Results will be interpreted with caution, and this limitation will be explicitly stated in the final report.

### 2.3 Confounder Adjustment (FR-008)
* **Method**: **Permutation-based Partial Correlation**.
* **Library**: `pingouin` (`pingouin.partial_corr`).
* **Implementation**: `pingouin.partial_corr(data, x='diversity', y='sleep', covar=['age', 'bmi', 'diet'], method='spearman', permutation=1000)`.
* **Fallback for Sparsity**: If global N < 20, the pipeline will attempt **Stratified Partial Correlation** (calculating partial correlations within strata of BMI or Diet and aggregating results).
* **Fail-Stop**: If `pingouin` is unavailable or the permutation test fails, the pipeline **HALTS** with a fatal error. **No custom implementation** (e.g., rank-based residuals) will be used as a fallback, as this method is statistically non-standard and invalid.

### 2.4 Power and Sample Size
* **Requirement**: `n >= 30` or Power >= 0.8 for expected effect size (r=0.3).
* **Action**: The pipeline will calculate the effective sample size after filtering and compute the Minimum Detectable Effect Size (MDES).
* **Decision**: If MDES > 0.3 or N < 30, the pipeline **HALTS** with a warning: "Insufficient Power: MDES > 0.3. Study may be underpowered to detect biologically relevant correlations."

### 2.5 Causal Inference & Assumptions
* **Observational Nature**: The dataset is observational. All claims will be framed as **associational**.
* **Collinearity**: If predictors (e.g., specific taxa) are definitionally related (e.g., one is a subset of another), independent effects will not be claimed. Descriptive reporting of correlations will be used with explicit acknowledgment of collinearity.

## 3. Compute Feasibility

* **Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
* **Strategy**:
 * **Data Loading**: Use `pandas` with `dtype` optimization. If the OTU table is too large for RAM, implement chunked processing or filter to the top 1000 most abundant taxa before correlation (a common practice in microbiome analysis to reduce noise and computational load).
 * **Library Selection**: `scikit-bio`, `scipy`, `pandas`, `seaborn`, `pingouin` are all CPU-native and have small footprints.
 * **No GPU**: No CUDA or mixed-precision libraries used.
 * **Runtime**: Correlation of ~1000 taxa against 2 sleep metrics is trivial (< 1 min). Diversity calculation on a large sample size is also fast. Permutation tests (1000 iterations) may take longer but should complete within 6 hours for N < 1000. Total runtime expected < 4 hours.

## 4. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Spearman over Pearson** | Microbiome data is non-normal; Spearman is robust. |
| **Benjamini-Hochberg** | Essential for controlling False Discovery Rate in high-dimensional taxon-level tests (Constitution Principle VI). |
| **Exclusion over Imputation** | Per Constitution Principle VII, missing sleep metadata leads to exclusion to maintain integrity. |
| **Scope Narrowing** | If primary `sleep_efficiency` is missing, the study proceeds with `sleep_quality` (proxy) rather than halting, provided a proxy exists. |
| **Permutation-based Partial Correlation** | Required for valid non-parametric adjustment. `pingouin` is the standard, validated library for this. No custom fallback allowed to preserve statistical rigor. |
| **CLR Transformation** | Standard approach to handle compositionality in 16S data, though acknowledged as not a complete fix for spurious correlations. |