# Feature Specification: Predicting Plant Disease Susceptibility from Publicly Available Genomic and Environmental Data

**Feature Branch**: `001-plant-disease-susceptibility`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Plant Disease Susceptibility from Publicly Available Genomic and Environmental Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Integration and Preprocessing Pipeline (Priority: P1)

The system must successfully ingest raw genomic sequencing data from NCBI SRA for 3–5 major crop species (wheat, rice, maize, tomato, soybean) and environmental metadata from public weather APIs, aligning reads, calling variants, and merging them into a single, normalized feature matrix with imputed missing values.

**Why this priority**: This is the foundational step; without a clean, merged dataset containing both genomic and environmental variables, no predictive modeling can occur. It delivers the primary data asset required for all downstream analysis.

**Independent Test**: The pipeline can be tested by running the ingestion script on a small, fixed subset of 10 samples and verifying that the output `feature_matrix.csv` exists, contains the expected columns (SNP frequencies, temperature, humidity, etc.), has zero missing values (due to imputation), and passes a schema validation check.

**Acceptance Scenarios**:

1. **Given** a list of 10 valid NCBI SRA accessions for wheat and a corresponding date/location for each, **When** the ingestion pipeline runs, **Then** a `feature_matrix.csv` is generated with exactly 10 rows, containing variant frequency vectors and matched environmental variables (temperature, precipitation, humidity) with no NaN values.
2. **Given** a sample with missing environmental data for a specific location, **When** the pipeline executes, **Then** the missing values are filled using missForest (random forest-based) imputation, and a log entry records the imputation action.
3. **Given** an invalid SRA accession ID in the input list, **When** the pipeline runs, **Then** the process halts gracefully, logs the specific error, and does not produce a partial output file.

---

### User Story 2 - Model Training and Performance Evaluation (Priority: P2)

The system must train Random Forest and Support Vector Machine models on the integrated dataset using a stratified split (70/15/15) by disease status, perform hyperparameter tuning via grid search (≤50 combinations), and generate performance metrics (AUC-ROC, Precision-Recall) and feature importance rankings.

**Why this priority**: This delivers the core analytical value—quantifying the predictive power of genomic and environmental factors. It allows the researcher to determine if the joint model outperforms a random baseline.

**Independent Test**: The training module can be tested by running it on a pre-processed, fixed dataset (e.g., 100 rows) and verifying that the output includes `model_performance.json` with AUC-ROC values > 0.5 (better than random) and a `feature_importance.csv` file listing the top 10 predictors.

**Acceptance Scenarios**:

1. **Given** a pre-processed feature matrix with 1000 samples and 500 features, **When** the training script executes with a grid search limit of 50, **Then** two models (Random Forest, SVM) are saved, and a performance report is generated showing AUC-ROC ≥ 0.55 for at least one model.
2. **Given** the trained models, **When** the feature importance analysis runs, **Then** the output lists the top 10 features, distinguishing between genomic (SNP) and environmental (temp, precip) contributors, with a clear ranking score for each.
3. **Given** a test set, **When** the model predicts, **Then** the precision-recall curve is plotted and saved as `pr_curve.png`, and the area under this curve is recorded in the performance report.

---

### User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

The system must perform permutation tests (1000 permutations, seed=42) to validate that model performance exceeds random chance and conduct a sensitivity analysis on any decision thresholds (if applicable) to ensure robustness.

**Why this priority**: This ensures scientific rigor. It confirms that the observed predictive power is not a statistical artifact and that the model is stable against minor variations in data or parameters, addressing the methodological soundness requirements.

**Independent Test**: The validation module can be tested by running the permutation test on the trained model and verifying that the p-value is calculated and reported, and that the sensitivity analysis output shows performance metrics across the tested threshold range.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model with an AUC-ROC of 0.65, **When** the permutation test runs with 1000 shuffles of the target labels, **Then** the output reports a p-value < 0.05, confirming the model's performance is statistically significant.
2. **Given** a classification threshold of 0.5 (default), **When** the sensitivity analysis runs, **Then** the system evaluates the model at thresholds {0.45, 0.50, 0.55} and reports the variation in False Positive Rate and False Negative Rate for each.
3. **Given** a scenario where the p-value from the permutation test is ≥ 0.05, **When** the analysis completes, **Then** the system flags the result as "Not Statistically Significant" and records this in the final report, rather than silently accepting the model.

---

### Edge Cases

- What happens when the NCBI SRA API returns an error or rate-limit during download? (System retries up to 3 times with exponential backoff, then logs failure and skips that specific sample).
- How does the system handle a crop species with insufficient samples (< 50) for stratified splitting? (The system aggregates data across species or excludes that species with a warning log).
- What if the environmental data source (ERA5-Land) lacks data for a specific sample location? (The system uses missForest imputation; if no neighbors exist within 50km for environmental variables, the sample is excluded and logged).
- How does the system handle highly collinear genomic features (e.g., SNPs in linkage disequilibrium)? (The system performs LD pruning with r² > 0.8 or PCA-based dimensionality reduction to prevent spurious independent effect claims).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download genomic sequencing data for 5 major crop species (wheat, rice, maize, tomato, soybean) from NCBI SRA using E-utilities or wget, handling rate limits with exponential backoff (max 3 retries). (See US-1)
- **FR-002**: System MUST align raw reads to reference genomes (Wheat: RefSeq GCA_000003205.5; Rice: Ensembl GCA_001433935.2; Maize: RefSeq GCA_000005005.4; Tomato: Sol Genomics Network SL4.0; Soybean: Phytozome Wm82.a2.v1) using minimap2, call SNPs with bcftools, and summarize them as variant frequency vectors for each sample. (See US-1)
- **FR-003**: System MUST retrieve environmental variables (temperature, precipitation, humidity) for sample collection locations from ERA5-Land API as primary source using curl, matching by date and geographic coordinates; if ERA5-Land fails, fall back to NOAA API. (See US-1)
- **FR-004**: System MUST normalize, merge, and impute missing values in the combined genomic-environmental feature matrix using missForest (random forest-based) or MICE imputation to ensure a complete dataset for modeling; if environmental neighbors are unavailable within 50km, the system MUST exclude the sample and log the action. (See US-1)
- **FR-005**: System MUST train Random Forest and SVM models on the prepared data using a 70/15/15 stratified split by disease status, with hyperparameter tuning via grid search limited to ≤50 combinations to ensure CPU feasibility. (See US-2)
- **FR-006**: System MUST evaluate model performance using AUC-ROC and Precision-Recall curves, generating visualizations and saving metrics to a JSON report. (See US-2)
- **FR-007**: System MUST perform permutation tests with 1000 permutations and a fixed random seed (seed=42) to validate model performance; the system MUST report the p-value and explicitly flag results where p ≥ 0.05 as "Not Statistically Significant". (See US-3)
- **FR-008**: System MUST conduct a sensitivity analysis on the classification threshold (sweeping {0.45, 0.50, 0.55}) and report the variation in False Positive and False Negative rates. (See US-3)
- **FR-009**: System MUST check for predictor collinearity using LD pruning (r² > 0.8) or PCA-based dimensionality reduction and report diagnostic metrics to prevent spurious independent effect claims for related genomic features. (See US-2)
- **FR-010**: System MUST validate that the 'disease susceptibility' target label is derived from an independent phenotypic source (e.g., field trial records, distinct pathology databases) linked by accession, not from the genomic sequencing data itself, and document the linkage method. (See US-1, US-2)

### Key Entities

- **Sample**: Represents a single plant specimen, containing attributes for species, location, date, genomic variant frequencies, environmental context, and disease status label source.
- **Model**: Represents a trained predictor (Random Forest or SVM), containing hyperparameters, feature weights, and performance metrics.
- **Feature**: Represents a single predictor variable, either a genomic SNP frequency or an environmental metric (e.g., mean temperature), with attributes for source, type (continuous/categorical), value, and collinearity_status (e.g., pruned, retained).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model performance (AUC-ROC) is measured against the random baseline (AUC = 0.5) to determine if the joint genomic-environmental signal is statistically significant. (See US-2)
- **SC-002**: Statistical significance (p-value from permutation test) is measured against the alpha threshold of 0.05 to validate that observed performance is not due to chance. (See US-3)
- **SC-003**: Feature importance rankings are measured against the total variance explained to quantify the relative contribution of genomic vs. environmental predictors. (See US-2)
- **SC-004**: Sensitivity analysis results (variation in FPR/FNR) are measured across the threshold sweep {0.45, 0.50, 0.55} to assess model robustness. (See US-3)
- **SC-005**: Data completeness (percentage of missing values after imputation) is measured against [deferred] missing values to ensure the dataset is fully prepared for modeling. (See US-1)

## Assumptions

- Public genomic data (NCBI SRA) for the selected crop species contains sufficient metadata (location, date) to link with environmental data, and the 'disease susceptibility' label can be derived from an independent phenotypic source (e.g., field trial records) linked by accession, not from the SRA data itself.
- The free-tier GitHub Actions runner (2 CPU, 7 GB RAM) is sufficient to process the sampled dataset (≤ 1000 samples) and run the specified machine learning models (Random Forest, SVM) without GPU acceleration.
- The environmental data from ERA5-Land is available at the spatial and temporal resolution required to match the sample collection metadata.
- The genomic data is of sufficient quality (read depth, coverage) to call SNPs reliably using standard tools (minimap2, bcftools) on a CPU-only environment.
- The dataset size will be sampled or subsetted to fit within the 7 GB RAM constraint; the full population of SRA records is not required for the initial proof of concept.