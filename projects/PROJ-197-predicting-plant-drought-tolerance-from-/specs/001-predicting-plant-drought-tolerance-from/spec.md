# Feature Specification: Predicting Plant Drought Tolerance from Publicly Available Physiological and Genomic Data

**Feature Branch**: `001-drought-tolerance-prediction`  
**Created**: 2026-06-25  
**Status**: Draft  
**Input**: User description: "Predicting Plant Drought Tolerance from Publicly Available Physiological and Genomic Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Construction (Priority: P1)

The system must successfully download, parse, and merge physiological trait data from the TRY database with genomic feature data (ABA-signaling and osmoprotectant genes) from NCBI RefSeq for a defined set of plant species, producing a single, clean dataset ready for modeling.

**Why this priority**: This is the foundational step; without a unified, high-quality dataset, no predictive modeling or scientific insight is possible. It validates the feasibility of the data acquisition strategy.

**Independent Test**: Can be fully tested by executing the data pipeline script and verifying the output CSV contains the expected number of rows (species) and columns (merged traits + gene presence/absence), with no missing values for the target label.

**Acceptance Scenarios**:

1. **Given** the TRY database CSV export and NCBI RefSeq FTP links for a list of 50 species, **When** the ingestion script runs, **Then** a merged dataframe is generated where every row represents a unique species with combined physiological and genomic columns.
2. **Given** missing continuous trait values in the source TRY data, **When** the script applies phylogenetic MICE imputation, **Then** the output dataframe contains no NaN values for continuous predictors, or the column is dropped and logged if [deferred] missing, and the imputation method is logged.
3. **Given** a species list where some species lack genomic annotations in RefSeq, **When** the script processes the list, **Then** those species are either excluded with a warning log or flagged with a specific "no_genomic_data" indicator, ensuring the final dataset integrity is maintained.

---

### User Story 2 - Model Training and Validation (Priority: P2)

The system must train two supervised classifiers (Random Forest and XGBoost) on the constructed dataset using a stratified 80/20 split and 5-fold cross-validation, ensuring the models are trained without GPU acceleration and complete within the CI limit. Additionally, the system must validate that the combined features provide statistically significant improvement over a phylogeny-only baseline.

**Why this priority**: This validates the core scientific hypothesis that genomic and physiological markers can predict drought tolerance beyond phylogenetic relatedness. It also confirms the computational feasibility of the approach on free-tier CI resources.

**Independent Test**: Can be fully tested by running the training script and verifying that both models are trained, cross-validation scores are recorded, the baseline is trained, and the statistical comparison (DeLong's test) confirms the best model significantly outperforms the baseline.

**Acceptance Scenarios**:

1. **Given** the merged dataset with a binary drought-tolerance label, **When** the training script executes, **Then** both RandomForest and XGBoost models are trained using default hyperparameters for all parameters except tree count, which is grid-searched across values {100, 200, 500}.
2. **Given** the stratified train/test split, **When** the models are evaluated on the held-out test set, **Then** the ROC-AUC score is calculated and logged for both models, and the best performing model (highest mean AUC) is identified.
3. **Given** the 2-core CPU environment constraint, **When** the training job runs, **Then** the process completes without OOM (Out Of Memory) errors or GPU-related exceptions within 30 minutes.
4. **Given** the best performing model and the phylogeny-only baseline, **When** the comparison test is executed, **Then** DeLong's test is used to verify the best model's AUC is statistically significantly higher than the baseline (p < 0.05).

---

### User Story 3 - Statistical Comparison and Interpretation (Priority: P3)

The system must perform a statistical comparison of the two classifiers' performance using a paired t-test on cross-validated AUC scores and generate feature importance rankings (via permutation or SHAP) to identify the most predictive biological markers.

**Why this priority**: This provides the scientific insight (biological determinants) and statistical rigor required to validate the findings beyond simple accuracy metrics.

**Independent Test**: Can be fully tested by running the analysis script and verifying that a p-value is generated from the paired t-test and a ranked list of top features (genes or traits) is output.

**Acceptance Scenarios**:

1. **Given** the ROC-AUC scores from 5-fold cross-validation for both models, **When** the paired t-test is executed, **Then** a p-value is generated to determine if the performance difference is statistically significant at α = 0.05.
2. **Given** the trained Random Forest model, **When** permutation feature importance is calculated, **Then** the top-ranked features are ranked, explicitly distinguishing between genomic markers (genes) and physiological traits.
3. **Given** the final model results, **When** the report is generated, **Then** it includes a summary of the feature importance and the statistical significance of the model comparison.

### Edge Cases

- What happens when the TRY database or NCBI RefSeq is temporarily unavailable or returns a 404 error? (System should retry a limited number of times with exponential backoff, then fail gracefully with a clear error message).
- How does the system handle species present in the trait database but missing entirely from the genomic database? (They are excluded from the training set, and a log entry records the exclusion count).
- What if the dataset is too small to support stratified splitting (e.g., a small number of samples)? (The system should detect this and switch to a leave-one-out cross-validation strategy or raise a critical error).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download physiological trait data from the TRY database and genomic annotation files from NCBI RefSeq for the specified species list (See US-1).
- **FR-002**: System MUST merge the physiological and genomic data by species identifier, applying phylogenetic MICE (Multiple Imputation by Chained Equations) for missing continuous traits (See US-1).
- **FR-003**: System MUST split the dataset into an [deferred] training set and a [deferred] testing set, stratified by the drought-tolerance label (See US-2).
- **FR-004**: System MUST train RandomForest and XGBoost classifiers using scikit-learn and xgboost libraries on CPU-only resources (See US-2).
- **FR-005**: System MUST perform a stratified 5-fold cross-validation and a paired t-test on the AUC scores to compare the performance of the two classifiers (See US-3).
- **FR-006**: System MUST generate and output feature importance rankings identifying the top predictive genomic markers and root traits (See US-3).
- **FR-007**: System MUST log all data processing steps, including imputation counts and excluded species, for reproducibility (See US-1).
- **FR-008**: System MUST ensure the entire pipeline (download to report) completes within 6 hours on a 2-core CPU runner (See US-2).
- **FR-009**: System MUST train a K-Nearest Neighbors (K=5) classifier using the phylogenetic distance matrix as the sole input to serve as a baseline model (See US-2).
- **FR-010**: System MUST compare the ROC-AUC of the best performing model (Random Forest or XGBoost) against the baseline model (FR-009) using DeLong's test for paired AUCs to determine statistical significance (See US-2).

### Key Entities

- **SpeciesRecord**: Represents a single plant species, containing attributes for physiological traits (e.g., root depth), genomic markers (binary presence/absence of specific genes), and the drought-tolerance phenotype label.
- **ModelResult**: Represents the outcome of a trained classifier, containing metrics (ROC-AUC, accuracy), hyperparameters, and feature importance scores.
- **DataPipelineLog**: A structured record of the data ingestion process, including source URLs, download status, imputation details, and merge statistics.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The ROC-AUC of the best performing model (Random Forest or XGBoost) on the held-out test set is measured against the phylogeny-only baseline model (FR-009) using DeLong's test to ensure the combined features outperform the baseline by at least 0.05 AUC with p < 0.05 (See US-2).
- **SC-002**: The total execution time of the data pipeline and model training is measured against the 6-hour GitHub Actions job limit to ensure CPU feasibility (See US-2).
- **SC-003**: The p-value from the paired t-test on cross-validated AUC scores is measured against the significance threshold of α = 0.05 to determine if one model significantly outperforms the other (See US-3).
- **SC-004**: The number of successfully merged species in the final dataset is measured against the input species list to verify data completeness (See US-1).
- **SC-005**: The top 10 feature importance scores are measured against a list of 15 independent ABA-signaling genes (distinct from the training features) to verify that at least 3 of these 15 genes appear in the top 10 ranks (See US-3).

## Assumptions

- The TRY database CSV export and NCBI RefSeq FTP links provided in the idea are accessible and stable during the CI job execution.
- The dataset size (after merging) will fit within the available RAM limit of the GitHub Actions runner; if not, the pipeline will automatically sample a subset of the data.
- The drought-tolerance phenotype labels from the published supplemental tables are binary (tolerant/sensitive) and compatible with the species identifiers in the other datasets.
- The "ABA-signaling" and "osmoprotectant biosynthesis" gene lists are explicitly defined in the codebase or a separate configuration file. The training feature set consists of 20 specific genes, while the validation set for SC-005 consists of a distinct list of 15 genes sourced from an independent literature review to avoid circularity.
- The phylogenetic MICE strategy is sufficient for the continuous trait data, assuming missingness is Not Missing At Random (NMAR) and accounting for phylogenetic signal.
- The computational cost of SHAP values or permutation importance for the chosen model size is acceptable within the training window.
- The phylogeny-only baseline model (FR-009) uses a K-Nearest Neighbors algorithm (K=5) on the phylogenetic distance matrix.
- DeLong's test is the appropriate statistical method for comparing the AUC of two models on the same test set.