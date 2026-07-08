# Research: Impact of Environmental Factors on Fungal Community Structure in Soil

## Problem Definition
The research aims to identify which abiotic soil variables (pH, nutrients, temperature, moisture) most strongly predict fungal community composition and diversity across different biomes. The core challenge is the integration of heterogeneous public datasets (ITS amplicon data + metadata) and the rigorous statistical testing of environmental drivers while adhering to strict computational limits (CPU-only, ≤7 GB RAM).

## Dataset Strategy

**Critical Constraint**: The project specification requires ingestion of ITS amplicon data from public repositories (SRA, IMG/M) with specific metadata (pH, nutrients, etc.). The **Verified datasets** block provided for this project contains **NO verified sources** for SRA, IMG/M, FASTQ, ASV, or CSVs containing the required fungal ITS metadata.

**Strategy**:
1. **Research Mode (Scientific Goal)**: The workflow is designed to fetch data from SRA/IMG/M using their programmatic APIs. The `validate_data_availability` phase will **abort with a FATAL error** if fewer than 3 valid datasets with real ITS sequences and matching metadata are found. This mode is required for any scientific claim.
2. **Pipeline Validation Mode (CI/CD)**: To allow code development and testing without real data, the workflow supports a `--mode=pipeline-validation` flag. In this mode:
 * Synthetic ASV tables and metadata are generated on-the-fly.
 * The "minimum 3 real datasets" abort condition is **skipped**.
 * All statistical tests run on synthetic data to verify code paths.
 * Results are explicitly labeled as "Synthetic Data - Not for Publication".

**Data Sourcing Protocol**:
If the automated search fails to find a sufficient number of valid datasets, the workflow will trigger a manual verification protocol. This involves:
1. Querying the SRA and IMG/M APIs for studies with "fungal", "ITS", and "soil" keywords.
2. Manually inspecting the metadata of a representative sample of top results for the required columns (pH, N, P, K, Temp, Moisture, Biome).
3. If valid datasets are found, they are added to the `data/` directory and the workflow proceeds.
4. If no valid datasets are found after this protocol, the project remains in a "Data Unavailable" state, and no scientific claims are made.

**Dataset Variables Fit**:
* **Required Variables**: pH, Nitrogen, Phosphorus, Potassium, Temperature, Moisture, Biome.
* **Current Status**: No verified dataset contains these variables for ITS fungal data in the provided block.
* **Action**: The `ingest` module will check for these columns. If a dataset lacks them, it is excluded (logging a warning). If < 3 datasets remain in **Research Mode**, the process aborts.

## Validation Strategy for Real Data

Before proceeding to full analysis on real data, a **Power & Confound Check** is mandatory:
1. **Power Calculation**: Calculate the Minimum Detectable Effect Size (MDES) for PERMANOVA given the combined sample size (N) and number of predictors. If MDES > 0.15 (or N < 100), the workflow aborts with "Insufficient Statistical Power".
2. **Confound Control**: Perform a "Leave-One-Study-Out" cross-validation. Run the PERMANOVA model excluding each dataset in turn. If the top driver changes significantly (e.g., from pH to moisture) when a single study is removed, the result is flagged as "Study-Dependent" and the conclusion is qualified accordingly.

## Statistical Methodology

### 1. Diversity Calculation (FR-002)
* **Alpha Diversity**: Shannon Index and Observed ASVs. Computed using `scipy.stats` and `skbio.diversity`.
* **Beta Diversity**: Bray-Curtis dissimilarity. Computed using `skbio.diversity.beta`.
* **Feasibility**: These are CPU-tractable. For large datasets, `dask` or chunked processing will be used to stay within 7 GB RAM.

### 2. PERMANOVA (FR-003) & Dispersion Check
* **Method**: `skbio.stats.distance.permanova` (equivalent to `adonis2`).
* **Permutations**: ≥999 (default), or ≥9999 if n < 20.
* **Correction**: Benjamini-Hochberg FDR applied to p-values across multiple predictors.
* **Multiple Comparisons**: Addressed via FDR correction as specified.
* **Homogeneity of Dispersion Check**: Before interpreting PERMANOVA results, the plan mandates a `betadisper` equivalent check (using `skbio.stats.distance.betadisper`) to ensure that significant p-values reflect differences in centroid location, not differences in multivariate dispersion (variance). If dispersion differs significantly, results will be flagged as "Dispersion-Driven".

### 3. Variance Partitioning (FR-004)
* **Method**: Hierarchical partitioning (using `skbio.stats.ordination.variance_partitioning` or equivalent) to quantify unique and shared variance.
* **Handling Collinearity**:
 * Calculate VIF for all predictors using `statsmodels.stats.outliers_influence.variance_inflation_factor`.
 * If VIF > 5: The plan WILL combine the collinear variables into a **Composite Index** via PCA, as mandated by the spec's Edge Cases.
 * **Reporting**: The output will report the "Variance Explained by the Composite Index" (representing the set of collinear variables). It will explicitly state: "The set of collinear variables (e.g., pH, Temp, Moisture) explains X% of variance. Individual contributions cannot be resolved due to high collinearity." This satisfies the spec's requirement to combine while maintaining construct validity by not making false independent claims.
 * The output will distinguish between "Unique Variance" and "Shared Variance" as required by FR-004.

### 4. Missing Data Imputation (FR-008) & Sensitivity
* **Method**: MICE (Multivariate Imputation by Chained Equations) using `miceforest`.
* **Constraint**: Max 50 iterations. If convergence fails, exclude the sample.
* **Feasibility**: `miceforest` is CPU-tractable for moderate sample sizes (<5000 samples). Subsampling will be applied if the dataset is too large.
* **Sensitivity Analysis for Imputation**: To address the MAR assumption risk, the plan mandates a comparison of results between:
 * MICE-imputed dataset.
 * Complete-case analysis (samples with any missing values excluded).
 * **Pattern-Mixture Simulation**: Impute missing values by shifting them by a sensitivity parameter (e.g., ±1 SD) to simulate MNAR.
 * If results diverge significantly (e.g., top driver changes), the report will flag "Imputation Sensitivity Detected" and default to the complete-case results for the primary conclusion.
* **PERMANOVA Sensitivity Check**: Specifically compare the PERMANOVA p-value distribution between the MICE-imputed dataset and the Complete-Case dataset. If p-values shift significantly (e.g., from >0.05 to <0.05), the result is flagged as "Imputation-Sensitive".

### 5. Stratification (FR-005)
* **Method**: Group by `biome`. Run PERMANOVA/varpart per group.
* **Power Check**: Skip groups with < 10 samples (logs error).
* **Ranking Metric**: Calculate the **standard deviation of the rank index** of the top driver across biomes (SC-003). Target ≤ 0.5.
 * **Calculation**: For each biome, rank the predictors by R². Compute the standard deviation of the rank of the top predictor across all biomes.

### 6. Sensitivity Analysis (FR-006) & Robustness
* **Method**: Sweep p-value thresholds (0.01, 0.05, 0.10) and R² cutoffs (0.05, 0.10, 0.15).
* **Output**: Stability of top driver ranking.
* **Robustness Metric**: Calculate the percentage of threshold combinations where the top driver remains unchanged. **Pass criteria**: ≥ 80% stability (SC-004).
 * **Calculation**: Count the number of (p-value, R²) combinations where the top driver is the same. Divide by total combinations. If ≥ 80%, pass.

### 7. Power Analysis (New Requirement)
* **Minimum Total N**: The plan mandates a minimum total sample size of **N >= 100** across all datasets combined to ensure sufficient power for PERMANOVA with multiple predictors.
* **Minimum Stratum N**: As per FR-005, strata with < 10 samples are skipped.
* **Abort Condition**: If the combined dataset (after filtering for valid variables) has N < 100, the workflow aborts with a `FATAL` error: "Insufficient statistical power: Total N < 100".

## Ontology Mapping (FR-001)
* **Strategy**: Use the Environment Ontology (ENVO) to standardize biome labels.
* **Mapping**: Implement a dictionary-based mapping (e.g., 'Temperate Forest' -> 'Forest') and a fuzzy matching step for ambiguous terms.
* **Validation**: All mapped labels must correspond to valid ENVO URIs (e.g., `).

## Computational Feasibility & Constraints

* **Hardware**: GitHub Actions Free Tier (multiple CPU cores, 7 GB RAM, 14 GB Disk).
* **Memory Management**:
 * ASV tables are sparse; use `scipy.sparse` matrices.
 * If memory > 6 GB projected: Apply random subsampling of samples (log ratio).
 * **Sampling Report**: The system MUST generate `results/sampling_report.csv` documenting the subsampling ratio and original/sample counts (FR-009).
 * No GPU usage; all libraries selected have CPU wheels.
* **Runtime**:
 * Target < 6 hours.
 * Heavy steps (PERMANOVA with a standard number of permutations) are limited to small subsets or reduced permutations if time-critical, with a warning.
* **Libraries**:
 * `pandas`, `numpy`, `scipy`, `skbio`, `miceforest`, `scikit-learn`, `matplotlib`, `seaborn`, `statsmodels`.
 * **Pure Python**: The stack is strictly Python-based (`skbio`) to avoid heavy conda/R overhead and ensure CPU-only execution. `q2cli` is **not** used.

## Decision Rationale

* **Why `skbio` over `vegan` (R)**: Python-only stack is preferred for CI integration and avoiding R dependency overhead on GitHub Actions, unless R is strictly required for a specific algorithm not available in `skbio`. `skbio` provides robust PERMANOVA and diversity metrics.
* **Why MICE over Median**: MICE preserves the covariance structure of environmental variables, which is critical for accurate variance partitioning. Median imputation would artificially reduce variance and bias the results.
* **Why VIF > 5**: This is the standard threshold in ecological multivariate analysis to detect problematic collinearity.
* **Why Abort on < 3 Datasets**: Statistical power and representativeness are insufficient for global conclusions with fewer than 3 independent studies.
* **Why Abort on N < 100**: To ensure the PERMANOVA test has sufficient power to detect moderate effect sizes in a multivariate setting.

## Risks & Mitigations

* **Risk**: No verified ITS datasets found.
 * **Mitigation**: Plan includes a hard abort with a clear error message in **Research Mode**. In **Pipeline Validation Mode**, synthetic data is used. The 'Data Sourcing Protocol' is initiated if the automated search fails.
* **Risk**: Dataset too large for 7 GB RAM.
 * **Mitigation**: Subsampling strategy implemented in `ingest.py` with logging. `results/sampling_report.csv` generated.
* **Risk**: MICE fails to converge.
 * **Mitigation**: Fallback to sample exclusion as per FR-008. Sensitivity analysis compares results.
* **Risk**: Collinearity prevents independent variable claims.
 * **Mitigation**: VIF check and hierarchical partitioning to report "set" variance.
* **Risk**: PERMANOVA driven by dispersion, not location.
 * **Mitigation**: `betadisper` check performed before interpretation.
