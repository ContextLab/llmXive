# Feature Specification: Impact of Environmental Factors on Fungal Community Structure in Soil

**Feature Branch**: `001-impact-of-environmental-factors`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Which abiotic soil variables (pH, nutrient concentrations, temperature, moisture) most strongly predict the composition and diversity of fungal communities as revealed by ITS amplicon sequencing, and how does this ranking vary across biomes or soil types?"

## User Scenarios & Testing

### User Story 1 - Reproducible Environmental-Community Association Analysis (Priority: P1)

As a researcher, I want to run a standardized workflow that ingests public ITS amplicon data and abiotic metadata, processes sequences to ASVs, and calculates the statistical association (PERMANOVA, db-RDA) between environmental matrices and community beta-diversity, so that I can determine which abiotic factors (pH, nutrients, moisture, temperature) significantly predict fungal community composition.

**Why this priority**: This is the core scientific contribution. Without a valid, reproducible statistical link between the environment and the community, no further analysis of driver ranking or biome variation is possible. It delivers the primary hypothesis test.

**Independent Test**: The workflow can be executed on a subset of public datasets. Success is verified by the generation of a CSV report containing PERMANOVA R² values, p-values (< 0.05), and db-RDA variance explained for the combined dataset, confirming the analysis pipeline functions end-to-end.

**Acceptance Scenarios**:

1. **Given** a set of 3 valid public SRA/IMG/M projects with matching metadata, **When** the workflow is executed, **Then** the system outputs a `results/permanova_summary.csv` with significant correlations (p < 0.05) and a `results/db_rda_variance.csv` quantifying variance explained by each predictor.
2. **Given** a dataset where environmental metadata is missing for >20% of samples within a specific study, **When** the workflow is executed, **Then** the system imputes missing values using MICE (Multivariate Imputation by Chained Equations) or excludes the sample if MICE fails to converge within 50 iterations, and logs a warning, proceeding with the analysis on the remaining valid samples.
3. **Given** the analysis completes, **When** the user inspects the db-RDA triplot (PNG), **Then** the plot visually displays sample points clustered by the dominant environmental vector (e.g., pH) with a vector length proportional to its explanatory power.

---

### User Story 2 - Biome-Specific Driver Ranking (Priority: P2)

As an ecologist, I want the analysis to stratify the dataset by biome or soil type and re-run the PERMANOVA/db-RDA tests for each stratum, so that I can identify whether the ranking of dominant drivers (e.g., pH vs. moisture) shifts across different environmental contexts.

**Why this priority**: This addresses the "effect heterogeneity" aspect of the research question. It moves from a global average to context-specific insights, which is crucial for the novelty of the study.

**Independent Test**: The workflow can be run with a specific `--stratify-by=biome` flag. Success is verified by the generation of separate summary tables and plots for each biome, showing distinct rankings of variable importance (e.g., pH dominant in forests, moisture in grasslands).

**Acceptance Scenarios**:

1. **Given** a combined dataset with a valid `biome` column in metadata, **When** the stratified analysis is run, **Then** the system generates separate `results/db_rda_biome_<NAME>.csv` files for each unique biome, each containing the R² values for all predictors.
2. **Given** a biome with < 10 samples, **When** the analysis is run, **Then** the system skips the statistical test for that biome and logs an error indicating insufficient power (minimum practical stratum size for robust variance estimation is sufficient to ensure statistical power, based on power analysis for ecological PERMANOVA tests), rather than crashing or producing unreliable p-values.
3. **Given** the stratified results, **When** the user compares the top driver across biomes, **Then** the output clearly indicates if the top predictor changes (e.g., pH is the top driver in [actual count] biomes ([actual percentage]%), moisture is the top driver in [actual count] biomes).

---

### User Story 3 - Threshold Sensitivity and Robustness Reporting (Priority: P3)

As a reviewer, I want the system to perform a sensitivity analysis on the decision thresholds (e.g., p-value cutoff, variance explained minimum) and report how the "dominant driver" ranking changes, so that I can assess the robustness of the conclusions against arbitrary parameter choices.

**Why this priority**: This ensures methodological soundness by preventing "p-hacking" or over-interpretation of marginal results. It validates that the findings are not artifacts of a single arbitrary threshold.

**Independent Test**: The workflow can be run with a `--sweep-thresholds` flag. Success is verified by a `results/sensitivity_analysis.csv` showing the stability of the top-ranked driver across a range of p-values (0.01, 0.05, 0.1) and R² cutoffs.

**Acceptance Scenarios**:

1. **Given** the primary analysis results, **When** the sensitivity sweep is executed, **Then** the system outputs a table showing the top driver for each tested p-value threshold (0.01, 0.05, 0.10) and R² cutoff (0.05, 0.10, 0.15).
2. **Given** a scenario where the top driver changes across the sensitivity sweep, **When** the report is generated, **Then** the report flags this instability in a `results/robustness_summary.md` with a "Low Confidence" warning.
3. **Given** the sensitivity results, **When** the user reviews the summary, **Then** the report explicitly states the percentage of threshold combinations where the primary hypothesis (pH is the top driver) holds true.

---

### Edge Cases

- **Dataset-Variable Fit**: What happens if a selected public dataset lacks a critical variable (e.g., soil moisture) required for the global model? **Given** a dataset is missing a required column (pH, nitrogen, phosphorus, potassium, temperature, moisture, biome), **When** the harmonization phase runs, **Then** the system MUST exclude that specific dataset from the global analysis, log a structured warning: `{"level": "WARN", "msg": "Dataset excluded: missing variable <VAR>", "dataset_id": <ID>}`, and proceed with the remaining valid datasets. If an insufficient number of valid datasets remain after exclusion, the system MUST abort with a fatal error: `{"level": "FATAL", "msg": "Insufficient datasets for global analysis: <count> valid datasets found, minimum required a sufficient number"}`. No manual review is required for this exclusion logic. Proceeding with an insufficient number of datasets would invalidate global conclusions due to lack of statistical power and representativeness.
- **Collinearity**: How does the system handle highly correlated predictors (e.g., temperature and moisture often correlate)? **Given** a pair of predictors has VIF > 5, **When** the model is built, **Then** the system MUST remove the variable with the higher VIF. If the variables are to be combined, the system MUST combine them into a composite index via PCA and report the variance explained by the 'composite index' rather than the individual original variables. VIF > 5 is a standard threshold in ecological multivariate analysis for detecting problematic collinearity.
- **Computational Limits**: What happens if a specific dataset is too large for the available RAM limit? **Given** a dataset exceeds memory limits, **When** the workflow starts, **Then** the system MUST apply random subsampling of reads or samples BEFORE analysis to ensure the dataset fits within available memory constraints, logging the sampling ratio used.
- **Null Results**: How does the system handle a scenario where no abiotic variable explains >5% of variance? **Given** the PERMANOVA model yields no significant terms (p > 0.05), **When** the report is generated, **Then** the system MUST still generate the report, explicitly stating "No significant abiotic drivers detected" with the corresponding p-values, rather than failing.
- **Dataset Availability**: What happens if no verified ITS datasets are found after searching public repositories? **Given** the system searches all configured public repositories (SRA, IMG/M) and finds < 3 datasets with complete metadata, **When** the validation phase completes, **Then** the system MUST abort with a fatal error: `{"level": "FATAL", "msg": "No sufficient ITS datasets found: <count> valid datasets, minimum required"}`. The analysis cannot proceed without adequate data, as conclusions would be scientifically invalid.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest raw FASTQ files and associated metadata CSVs from at least 3 distinct public repositories (e.g., SRA, IMG/M) and harmonize them into a unified ASV table and metadata dataframe. The system MUST include an automated ontology mapping step to standardize biome labels (e.g., mapping 'Temperate Forest' to 'Forest') to ensure reproducibility. If a dataset is missing required columns (pH, nitrogen, phosphorus, potassium, temperature, moisture, biome), the system MUST exclude that dataset and log a warning. (See US-1)
- **FR-002**: System MUST compute beta-diversity (Bray-Curtis) and alpha-diversity (Shannon, Observed ASVs) from the processed ASV table using CPU-tractable methods. (See US-1)
- **FR-003**: System MUST perform a PERMANOVA (adonis2) test between the environmental distance matrix and the community beta-diversity matrix with ≥999 permutations to assess significance. If sample size < 20, the system MUST use exact permutation tests or ≥9999 permutations to ensure valid p-values. Mantel tests are permitted only as secondary descriptive metrics. The system MUST apply Benjamini-Hochberg FDR correction for multiple comparisons, as it is more appropriate than Bonferroni for ecological correlations between predictors. (See US-1)
- **FR-004**: System MUST execute variance partitioning analysis (varpart) to quantify the unique and shared proportion of community variance explained by each abiotic variable (pH, nutrients, temperature, moisture) and test axis significance via permutation ANOVA. If PCA-combination is used for collinear variables, the system MUST report variance explained by the 'composite index' rather than the original individual variables. (See US-1)
- **FR-005**: System MUST stratify the analysis by a categorical metadata field (e.g., biome) and re-run the PERMANOVA/varpart tests for each stratum to compare driver rankings. Strata with < 10 samples must be skipped, as this threshold is based on power analysis for robust variance estimation in ecological PERMANOVA tests. (See US-2)
- **FR-006**: System MUST perform a sensitivity analysis by sweeping the significance threshold (p-value across a range of conventional levels) and reporting the stability of the top-ranked driver. (See US-3)
- **FR-007**: System MUST calculate Variance Inflation Factors (VIF) for all predictor variables and flag any pair with VIF > 5 as collinear, triggering the removal or PCA-combination strategy defined in Edge Cases. VIF > 5 is a standard threshold in ecological multivariate analysis for detecting problematic collinearity. (See US-1)
- **FR-008**: System MUST impute missing environmental values using MICE (Multivariate Imputation by Chained Equations) per study. If MICE fails to converge within 50 iterations, the system MUST exclude samples with missing values rather than using global median imputation, to avoid introducing bias by ignoring study-specific covariance structures. (See US-1)
- **FR-009**: System MUST limit total runtime to ≤ 6 hours and memory usage to ≤ 7 GB on a standard CPU-only runner. If projected memory usage > 6 GB, the system MUST apply random subsampling of [deferred] of samples BEFORE analysis to ensure limits are never breached. (See US-1)

### Key Entities

- **ASV Table**: A matrix of Amplicon Sequence Variant counts per sample, derived from DADA2 denoising.
- **Environmental Matrix**: A dataframe of scaled abiotic variables (pH, nitrogen, phosphorus, potassium, Temp, Moisture) per sample.
- **Distance Matrices**: Euclidean distance matrix of environmental variables and Bray-Curtis distance matrix of community composition.
- **RDA Model**: A statistical model object quantifying the linear relationship between the Environmental Matrix and the Community Matrix.
- **Stratum**: A subset of data defined by a categorical variable (e.g., Biome, Soil Type) used for comparative analysis.
- **Sampling Report**: A CSV file (`results/sampling_report.csv`) documenting subsampling ratios and sample counts when memory limits are exceeded.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of variance in fungal beta-diversity explained by the top abiotic driver is measured against the R² value from the global variance partitioning model. (See US-1)
- **SC-002**: The statistical significance of the environmental-community association is measured against the PERMANOVA p-value (target < 0.05) with 999 permutations. (See US-1)
- **SC-003**: The consistency of the dominant driver ranking across different biomes is measured by the standard deviation of the rank index of the top driver across biomes. The standard deviation must be ≤ 0.5 to pass. (See US-2)
- **SC-004**: The robustness of the primary conclusion is measured against a range of sensitivity thresholds where the top driver remains unchanged. The top driver must remain unchanged in ≥ 80% of threshold combinations to pass. (See US-3)
- **SC-005**: The computational feasibility is measured against the total wall-clock time (target < 6h) and peak memory usage (target < 7 GB) on the GitHub Actions free-tier runner. (See US-1)
- **SC-006**: The collinearity risk is measured against the maximum VIF value calculated for the predictor set (target < 5 for independent claims). (See US-1)

## Assumptions

- Publicly available datasets from SRA/IMG/M contain the required metadata columns (pH, moisture, temperature, nitrogen, phosphorus, potassium) for at least 3 studies; if not, those studies are excluded from the global analysis, and the system aborts if fewer than 3 valid datasets remain.
- The "biome" or "soil type" metadata is consistently labeled across the selected datasets, allowing for valid stratification; if labels are inconsistent, the automated ontology mapping strategy defined in FR-001 is used.
- The QIIME 2 and DADA2 pipelines can run on the GitHub Actions free-tier runner without GPU acceleration, relying on optimized CPU implementations.
- The fungal ITS region is the sole marker used for community profiling; other markers (e.g., 16S for bacteria) are out of scope.
- The MICE imputation strategy for missing environmental data preserves covariance structure better than median imputation and introduces negligible bias compared to the natural variation in the dataset. If MICE fails, samples are excluded to avoid bias.
- The assumption that pH is a dominant driver (based on literature) is a hypothesis to be tested, not a guaranteed outcome; the analysis must be able to report null or alternative findings.
- Example datasets (e.g., HuggingFace) are used for testing purposes only and do not address the core ITS data availability issue; the workflow requires verified ITS datasets from public repositories.
- **Constitutional Compliance**: Principle I (Data Integrity) is verified by checksums of all data files. Principle II (No Fabrication) is verified by logging all data exclusions. Principle III (Reproducibility) is verified by version-controlled pipeline and parameter logging. Principle IV (Transparency) is verified by open-source code and public data sources.