# Feature Specification: Predicting Plant Root System Architecture from Genomic Data

**Feature Branch**: `001-predict-root-architecture`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Plant Root System Architecture from Publicly Available Genomic Data"

## User Scenarios & Testing

### User Story 1 - Data Harmonization and Preprocessing Pipeline (Priority: P1)

A researcher needs to download genomic variant data from the 1001 Genomes Project and phenotypic root architecture data from public repositories, then harmonize them into a single analysis-ready dataset by matching accessions, encoding genotypes, and performing stratified data splits.

**Why this priority**: Without a clean, matched, and properly split dataset, no modeling or analysis can occur. This is the foundational step that enables all subsequent research activities.

**Independent Test**: Can be fully tested by running the preprocessing script on a small subset of known accessions and verifying the output contains matched genotype-phenotype pairs, correct allele-count encoding (0, 1, 2), and stratified train/val/test splits by nutrient condition.

**Acceptance Scenarios**:

1. **Given** genomic data from 1001 Genomes and phenotypic data from public repositories, **When** the preprocessing pipeline runs, **Then** the output contains a unified dataset with matched accessions and properly encoded genotypes (0, 1, 2 for homozygous/heterozygous).
2. **Given** datasets with missing or mismatched accessions, **When** the pipeline runs, **Then** it logs the number of excluded accessions and proceeds with only the matched subset.
3. **Given** the unified dataset, **When** a researcher inspects the output, **Then** they can verify that each row contains both genotype markers and corresponding root trait measurements.
4. **Given** data with multiple nutrient conditions, **When** the split step runs, **Then** the system produces separate train/val/test splits for each nutrient condition with 80/10/10 ratios.

---

### User Story 2 - Baseline Model Training and Evaluation (Priority: P2)

A researcher needs to train multiple baseline machine learning models (linear regression with regularization, random forest, gradient boosting) on the harmonized dataset, trained separately for each nutrient condition, and evaluate their predictive performance using standard metrics against a null model.

**Why this priority**: Establishing baseline performance is essential to determine whether genomic markers have predictive value for root architecture traits across different soil conditions.

**Independent Test**: Can be fully tested by training models on the stratified dataset and verifying that performance metrics (R², MAE) are calculated and stored for each model and nutrient condition.

**Acceptance Scenarios**:

1. **Given** a trained model and test set for a specific nutrient condition, **When** evaluation runs, **Then** the system outputs R², mean absolute error, and cross-validation scores for the model.
2. **Given** multiple models trained across nutrient conditions, **When** comparison analysis runs, **Then** the system generates a summary table ranking models by predictive performance per condition.
3. **Given** a model trained on a specific nutrient condition, **When** results are reviewed, **Then** the system outputs the R² value and 95% confidence interval for that condition.

---

### User Story 3 - Feature Importance and Significance Testing (Priority: P3)

A researcher needs to identify which genomic markers are most predictive of root architecture traits and perform permutation tests to assess whether prediction accuracy exceeds random chance.

**Why this priority**: Understanding which specific markers drive predictions provides biological insight and enables marker-assisted selection, the ultimate goal of the research.

**Independent Test**: Can be fully tested by running feature importance analysis and permutation tests, then verifying that significant markers are identified and p-values are calculated.

**Acceptance Scenarios**:

1. **Given** a trained model, **When** feature importance analysis runs, **Then** the system outputs a ranked list of genomic markers with their importance scores.
2. **Given** 1000 permutation iterations, **When** significance testing runs, **Then** the system calculates and reports whether the observed R² exceeds the distribution of permuted R² values.
3. **Given** significant markers identified, **When** results are visualized, **Then** the system generates feature importance plots and prediction vs. actual scatter plots.

---

### User Story 4 - Computational Resource Management (Priority: P0)

A researcher needs the pipeline to operate within strict computational limits (GitHub Actions free-tier) to ensure reproducibility and accessibility without requiring paid infrastructure.

**Why this priority**: Without resource constraints, the pipeline may fail on standard CI/CD infrastructure, preventing automated validation and deployment. This is a cross-cutting constraint affecting all other stories.

**Independent Test**: Can be fully tested by running the full pipeline in a GitHub Actions environment with 2 CPU and 7GB RAM and verifying completion within 6 hours.

**Acceptance Scenarios**:

1. **Given** the full pipeline execution, **When** resource monitoring runs, **Then** peak memory usage does not exceed 7 GB and total runtime is ≤ 6 hours.
2. **Given** a model training step that exceeds memory limits, **When** the system detects this, **Then** it automatically triggers a dimensionality reduction (PCA) fallback to reduce feature space.

---

### Edge Cases

- What happens when accession matching fails due to naming inconsistencies between datasets? (System should log mismatches and proceed with matched subset)
- How does the system handle missing phenotypic data for specific accessions? (System should exclude incomplete records and report exclusion count)
- What occurs when genomic data contains missing variant calls? (System should exclude markers with >5% missingness; imputation is reserved for sensitivity analysis only)
- How does the system respond if no markers show predictive power beyond random chance? (System should report null result and flag potential environmental dominance)

## Requirements

### Functional Requirements

- **FR-001**: System MUST download genomic variant data from the 1001 Genomes Project and phenotypic root architecture data from the Arabidopsis thaliana Root Phenotyping Database (ATRDB) and PhenomicsDB (See US-1)
- **FR-002**: System MUST harmonize datasets by matching accessions and encoding genotypes as allele-count matrices (0, 1, 2) ONLY. NO imputation is allowed unless explicitly documented as a sensitivity analysis (See US-1)
- **FR-003**: System MUST split data into training ([deferred]), validation ([deferred]), and test ([deferred]) sets by accession, stratified by nutrient condition, creating separate splits for each distinct soil nutrient condition (See US-1)
- **FR-004**: System MUST train baseline models including linear regression (with L1/L2 regularization), random forest, and gradient boosting using scikit-learn, trained separately for each nutrient condition (See US-2)
- **FR-005**: System MUST evaluate models using R², mean absolute error, and cross-validation on held-out test set, comparing performance against a null model (intercept-only) (See US-2)
- **FR-006**: System MUST perform feature importance analysis using SHAP values or permutation importance (See US-3)
- **FR-007**: System MUST conduct permutation tests with 1000 iterations to assess statistical significance and report whether the p-value is < 0.05 (See US-3)
- **FR-008**: System MUST generate visualization outputs including feature importance plots and prediction vs. actual scatter plots (See US-3)
- **FR-009**: System MUST append a standardized disclaimer text block to all generated reports stating: "Findings are associational and do not imply causation." (See US-3)
- **FR-010**: System MUST apply L1/L2 regularization or Principal Component Analysis (PCA) dimensionality reduction for linear models to address the 'p >> n' problem inherent in genomic data (See US-2)

### Key Entities

- **GenomicDataset**: Contains SNP/sequence data with accessions, variant positions, and allele counts
- **PhenotypicDataset**: Contains root architecture measurements (length, branching density, angle) with associated accessions and nutrient conditions
- **UnifiedDataset**: Merged dataset with matched accessions containing both genomic and phenotypic variables
- **Model**: Trained machine learning model with performance metrics and feature importance data

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Prediction accuracy (R²) is measured against the null model baseline, and the system MUST output the R² value with a 95% confidence interval (See US-2)
- **SC-002**: Statistical significance is measured against permutation test distribution with 1000 iterations (See US-3)
- **SC-003**: Model performance comparison is measured against the null model (intercept-only) using cross-validation (See US-2)
- **SC-004**: Feature importance rankings are measured against stability across 10 bootstrap samples to identify robust predictive markers (See US-3)
- **SC-005**: Computational feasibility is measured against GitHub Actions free-tier constraints (2 CPU, ~7 GB RAM, ≤6 hours) (See US-4)
- **SC-006**: Dataset-variable fit is measured against the requirement that all predictor and outcome variables exist in the source datasets (See US-1)

## Assumptions

- The 1001 Genomes Project provides sufficient genomic variant data for the required accessions with complete genotype information
- Public repositories contain phenotypic root architecture data with matching accession identifiers and nutrient condition metadata
- Genomic data can be encoded as allele-count matrices (0, 1, 2) without requiring complex haplotype reconstruction
- The relationship between genetic variation and root architecture is polygenic and potentially non-linear (involving epistasis and GxE interactions); therefore, the methodology MUST include tree-based methods (Random Forest, Gradient Boosting) and SHAP analysis to capture these complex interactions rather than assuming linearity
- Nutrient condition effects can be modeled as categorical variables or interaction terms
- Public datasets contain no more than 5% missing values for critical variables, allowing for simple exclusion only; imputation is reserved for sensitivity analysis only
- The analysis can be completed within 6 hours on GitHub Actions free-tier without GPU acceleration
- No new citations beyond those provided in the idea Markdown will be added to the spec
- The study design is observational, so all findings will be framed as associational rather than causal
- Multiple comparison correction will be applied when testing multiple hypotheses to control family-wise error rate
- Thresholds for feature importance significance will be set at p < 0.05 with sensitivity analysis across {0.01, 0.05, 0.1}