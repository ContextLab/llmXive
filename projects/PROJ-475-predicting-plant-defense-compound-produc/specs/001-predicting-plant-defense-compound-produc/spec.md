# Feature Specification: Predicting Plant Defense Compound Production from Public Genomic and Environmental Data

**Feature Branch**: `001-predict-plant-defense-compounds`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Plant Defense Compound Production from Public Genomic and Environmental Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Validation Pipeline (Priority: P1)

**Journey**: A researcher needs to assemble a unified dataset by downloading genomic variants (NCBI SRA), environmental metadata (WorldClim/GBIF), and defense compound profiles (ChemBank/PhenolExplorer) for a specific target species (e.g., *Arabidopsis thaliana*), then validates that every population has complete data across all three modalities before analysis begins.

**Why this priority**: Without a validated, multi-modal dataset, no predictive modeling can occur. This is the foundational step; if data cannot be matched or is incomplete, the entire research question is unanswerable.

**Independent Test**: The pipeline can be tested by running the ingestion script against a small, known subset of public IDs and verifying that the output CSV contains only rows where `population_id`, `env_id`, and `compound_id` are non-null and match the expected schema.

**Acceptance Scenarios**:

1. **Given** a list of valid population IDs from the 1001 Genomes Project, **When** the ingestion script runs, **Then** it downloads the corresponding VCF files and extracts environmental data for the recorded coordinates.
2. **Given** a population with genomic and environmental data but missing compound measurements, **When** the validation step runs, **Then** that population is excluded from the final dataset with a logged warning count.
3. **Given** the final merged dataset, **When** the user inspects the summary statistics, **Then** the report confirms the retention percentage of populations with non-null values for all predictor and outcome variables.

---

### User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Journey**: A data scientist needs to transform raw genomic variants into diversity metrics (heterozygosity, nucleotide diversity) and aggregate environmental variables, then train a regularized regression model (LASSO/Ridge) to predict defense compound abundance using 5-fold cross-validation (or LOOCV if N < 30).

**Why this priority**: This implements the core analytical logic of the project. It translates raw data into the predictive framework required to answer the research question regarding G x E interactions.

**Independent Test**: The training module can be tested by running it on a synthetic dataset with known coefficients and verifying that the model recovers the signal within a reasonable error margin (R² > 0.5 on synthetic data) and that the cross-validation scores are consistent across folds.

**Acceptance Scenarios**:

1. **Given** a clean, merged dataset, **When** the feature engineering step runs, **Then** it outputs a feature matrix including calculated genomic diversity metrics and normalized environmental variables.
2. **Given** the feature matrix, **When** the LASSO regression model is trained with 5-fold cross-validation (or LOOCV), **Then** the system outputs the best hyperparameter (alpha) and the mean R² and MAE across folds.
3. **Given** the trained model, **When** the feature importance is extracted, **Then** the output lists the top 10 predictors (genomic and environmental) ranked by absolute coefficient magnitude.

---

### User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Journey**: A researcher needs to verify that the model's predictive power is not due to chance by running permutation tests, and needs to confirm that any decision thresholds (e.g., variable selection cutoffs) are robust by sweeping them across a defined range.

**Why this priority**: This ensures methodological soundness. It addresses the "multiplicity & power" and "threshold justification" requirements, preventing the publication of spurious correlations or arbitrary cutoffs.

**Independent Test**: The analysis script can be tested by running a permutation test on a dataset where the outcome is randomized; the resulting p-value should be > 0.05 (indicating no signal), and the sensitivity sweep should produce a report showing how model performance varies with different alpha values.

**Acceptance Scenarios**:

1. **Given** the trained model, **When** a permutation test (n=1000 shuffles) is executed, **Then** the observed R² is compared against the null distribution to generate a p-value.
2. **Given** a specific predictor threshold (e.g., coefficient > 0.05), **When** the sensitivity analysis sweeps the threshold over {0.01, 0.05, 0.1}, **Then** a report is generated showing the variation in false-positive rates and feature selection stability.
3. **Given** multiple hypothesis tests (one per predictor), **When** the results are compiled, **Then** a multiple-comparison correction (e.g., Benjamini-Hochberg) is applied and the adjusted p-values are reported.

---

### Edge Cases

- **What happens when** the genomic data contains high levels of missingness (>20% missing genotypes) for a specific population? The system must either impute using a defined method (e.g., mean imputation for SNPs) or exclude the population entirely, logging the decision.
- **How does the system handle** environmental metadata that is missing for a population's coordinates (e.g., coordinates outside WorldClim coverage)? The system must flag the population as "incomplete" and exclude it from the final analysis, rather than failing the entire run.
- **What happens when** the target defense compound data is unavailable for a specific population in the source database? The system must perform listwise deletion for that row and report the count of excluded populations in the final summary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download genomic variant data (VCF format) for the target species from NCBI SRA using explicit DOIs or accession numbers. Before download, the system MUST check available disk space and ensure it is at least 1.5x the estimated dataset size. After ingestion, the system MUST report total disk usage and halt if usage exceeds a critical threshold of available space. (See US-1)
- **FR-002**: System MUST extract environmental metadata (temperature, precipitation, soil pH) from WorldClim or GBIF APIs based on the latitude/longitude coordinates associated with each population. (See US-1)
- **FR-003**: System MUST merge genomic, environmental, and defense compound datasets, performing listwise deletion for any population lacking data in any of the three modalities. (See US-1)
- **FR-004**: System MUST calculate genomic diversity metrics (heterozygosity, nucleotide diversity) and aggregate environmental variables per population to serve as predictors. (See US-2)
- **FR-005**: System MUST train a regularized regression model (LASSO or Ridge) using scikit-learn. If the number of populations (N) is ≥ 30, the system MUST use 5-fold cross-validation. If N < 30, the system MUST use Leave-One-Out Cross-Validation (LOOCV). (See US-2)
- **FR-006**: System MUST execute a permutation test with at least 1,000 shuffles to generate a null distribution and calculate a p-value for the model's R². (See US-3)
- **FR-007**: System MUST perform a sensitivity analysis on the model's regularization parameter (alpha) by sweeping values {, 0.05, 0.1} and reporting the impact on feature selection stability. (See US-3)
- **FR-008**: System MUST apply a multiple-comparison correction (e.g., Benjamini-Hochberg) to the p-values of all predictor coefficients before reporting significance. (See US-3)
- **FR-009**: System MUST enforce population as the exclusive unit of analysis. All predictors and outcomes MUST be aggregated to the population level before model training. Individual-level data MUST NOT be used as a direct input to the regression model. (See US-2)
- **FR-010**: System MUST verify the number of populations (N) before training. If N < 30, the system MUST switch to LOOCV (as per FR-005) and MUST NOT include 'source study' as a covariate if the number of unique studies ≥ N-1. In such cases, the system MUST fall back to global Z-score normalization. (See US-2)
- **FR-011**: System MUST normalize defense compound values (Z-score) within each source study and include 'source study' as a fixed effect covariate in the model to control for methodological variance, unless prevented by FR-010. (See US-2)

### Key Entities

- **Population**: Represents a single plant population, containing a unique identifier, genomic coordinates, and links to compound data.
- **GenomicVariant**: Represents a specific genetic marker (SNP) or derived metric (heterozygosity) associated with a population.
- **EnvironmentalContext**: Represents the climatic and soil conditions (temperature, precipitation, etc.) at the population's collection site.
- **DefenseCompound**: Represents the measured concentration of a specific secondary metabolite (alkaloid, terpene) for a population.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The percentage of populations retained after merging genomic, environmental, and compound data must be ≥ 80% of the initial input count. If < 80%, the pipeline MUST fail with error code E-DATA-INSUFFICIENT. (See US-1)
- **SC-002**: The model's predictive performance (R² and MAE) is measured against a null model (intercept-only) to verify that genomic and environmental predictors add explanatory power. The observed R² must be significantly greater than the null model's R² (p < 0.05 via permutation test). (See US-2)
- **SC-003**: The statistical significance of the model is measured against the null distribution generated by the permutation test (p-value < 0.05) to confirm findings are not random. (See US-3)
- **SC-004**: The stability of feature selection is measured across the sensitivity sweep of regularization parameters (alpha). The median Jaccard index of the top 10 selected features across the sweep must be ≥ 0.6. (See US-3)
- **SC-005**: The total execution time of the analysis pipeline is measured against the free-tier CI runner's time limit to ensure compute feasibility. (See US-2, US-3)

## Assumptions

- **Assumption about data availability**: The 1001 Genomes Project for *Arabidopsis thaliana* (or equivalent for *Solanum*) contains sufficient variant data, and corresponding environmental/compound data exists in public repositories (ChemBank, PhenolExplorer) with matching identifiers. If a required variable (e.g., specific soil nutrient) is missing from the environmental source, it will be excluded, and the model will rely on available proxies.
- **Assumption about computational constraints**: The analysis will be performed on a standard GitHub Actions runner environment (multiple cores, sufficient RAM, and adequate disk storage). The genomic dataset will be pre-filtered to a manageable subset (e.g., top [deferred] SNPs by variance) or aggregated into diversity metrics before model training to prevent memory overflow.
- **Assumption about methodological framing**: Since the data is observational (no random assignment of genotypes or environments), all findings regarding the relationship between predictors and defense compounds will be framed as **associational**, not causal.
- **Assumption about threshold justification**: The sensitivity analysis for the regularization parameter (alpha) uses the specific set {0.01, 0.05, 0.1} as a defensible community-standard range for initial exploration; if the optimal alpha lies outside this range, the sensitivity report will flag this, but the core analysis will proceed with the best fit within the tested range.
- **Assumption about measurement validity**: The defense compound measurements in the source databases (ChemBank, PhenolExplorer) are treated as accurate *after* normalization (Z-score per study) and covariate adjustment for source study, as mandated by FR-011.
- **Assumption about collinearity**: Genomic diversity metrics (e.g., heterozygosity) and specific SNP counts may be collinear; the model will report the joint relationship descriptively, and a Variance Inflation Factor (VIF) diagnostic will be run to flag any predictors with VIF > 5, but these will not be removed unless they cause model instability.
- **Assumption about biological hypothesis**: Population-level genomic diversity (heterozygosity) is hypothesized to correlate with mean defense compound abundance due to the 'Heterozygote Advantage' hypothesis in plant defense evolution, providing a theoretical basis for the predictor-outcome link.