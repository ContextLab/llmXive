# Feature Specification: Predicting Plant Herbivore Resistance from Publicly Available Metabolomic Data

**Feature Branch**: `001-predict-herbivore-resistance`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Plant Herbivore Resistance from Publicly Available Metabolomic Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Resistance Score Extraction (Priority: P1)

The system must successfully locate, download, and parse publicly available plant metabolomic datasets (e.g., from NCBI GEO) to extract paired observations of metabolite abundance and quantified herbivore resistance scores for multiple genotypes.

**Why this priority**: Without a clean, paired dataset containing both predictors (metabolites) and outcomes (resistance scores), no analysis can proceed. This is the foundational step that determines feasibility.

**Independent Test**: The system can be tested by running the ingestion script against a known public dataset (e.g., GSE series) and verifying that a CSV file is produced with at least 10 rows of complete data (genotype ID, resistance score, and ≥5 metabolite columns) without manual intervention.

**Acceptance Scenarios**:
1. **Given** a valid NCBI GEO accession ID for a plant metabolomics study with herbivore treatment, **When** the ingestion script runs, **Then** the system downloads the raw data and metadata, parses the resistance metric (e.g., leaf area loss %), and outputs a structured CSV with no missing values in the target columns.
2. **Given** a dataset where resistance is reported as a categorical rating (e.g., "Low", "Medium", "High"), **When** the script processes the metadata, **Then** the system converts these to ordinal numeric values (1, 2, 3) for regression analysis and logs the mapping used.
3. **Given** a dataset with missing metabolite values for specific samples, **When** the pre-processing step runs, **Then** the system applies k-nearest neighbors (k=5) imputation to fill gaps and flags the imputed rows in a metadata column.

---

### User Story 2 - Predictive Modeling and Feature Importance (Priority: P2)

The system must train a CPU-tractable machine learning model (Random Forest Regressor) to predict resistance scores from metabolite profiles and extract a ranked list of the top 20 most predictive metabolites.

**Why this priority**: This delivers the core scientific value: identifying which metabolites are associated with resistance. It validates the "predictive potential" hypothesis mentioned in the research question.

**Independent Test**: The system can be tested by training the model on a subset of the data, evaluating the R² score on a held-out test set, and verifying that the output includes a sorted list of metabolite names with their corresponding importance scores.

**Acceptance Scenarios**:
1. **Given** a preprocessed dataset split into [deferred] training and [deferred] test sets by genotype, **When** the Random Forest Regressor (n_estimators=100, max_depth=10) is trained, **Then** the model produces a prediction file with resistance scores and a feature importance table where the top 5 metabolites sum to >30% of total importance.
2. **Given** a dataset with >100 metabolite features, **When** the model trains, **Then** the system automatically filters out features with near-zero variance (variance < 0.001) before training to prevent overfitting on noise.
3. **Given** a test set, **When** predictions are generated, **Then** the system calculates the Mean Squared Error (MSE) and R² score, ensuring the R² is reported in the summary logs even if negative (indicating a null result).

---

### User Story 3 - Statistical Validation and Multiplicity Correction (Priority: P3)

The system must perform permutation testing to validate that the model's performance exceeds random chance and apply multiple-testing corrections (e.g., Benjamini-Hochberg) to all correlation p-values.

**Why this priority**: This ensures methodological soundness. Without permutation testing, we cannot distinguish signal from noise. Without multiplicity correction, the "5-20 metabolites" claim risks being a statistical artifact.

**Independent Test**: The system can be tested by running the permutation test (1,000 iterations) and verifying that the p-value for the model's R² score is < 0.05, and that the final list of significant metabolites includes the adjusted p-values (q-values).

**Acceptance Scenarios**:
1. **Given** the trained model and test set, **When** the permutation test runs (shuffling resistance scores [deferred] times), **Then** the system generates a null distribution of R² scores and calculates a p-value; if p < 0.05, the result is flagged as "Statistically Significant."
2. **Given** a list of p-values from univariate correlations between each metabolite and resistance, **When** the correction step runs, **Then** the system applies the Benjamini-Hochberg procedure and outputs a new column of q-values, filtering the final report to only include metabolites with q < 0.10.
3. **Given** a scenario where the model performs no better than random (R² ≤ 0), **When** the validation runs, **Then** the system explicitly reports "Null Result: No predictive signal detected beyond random baseline" and halts further biomarker listing.

---

### Edge Cases

- **What happens when** the public dataset contains no numeric resistance metric? **Then** the system must fail gracefully with a clear error message: "No quantifiable resistance metric found in metadata. Aborting."
- **How does the system handle** datasets where the number of samples (genotypes) is less than the number of metabolites (p >> n)? **Then** the system must apply dimensionality reduction (PCA) to the top 50 variance metabolites before training to avoid singular matrices, and log a warning about low sample size.
- **What happens when** the NCBI GEO download fails due to network timeout? **Then** the system retries up to 3 times with exponential backoff (1s, 2s, 4s) before failing the job.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download plant metabolomic datasets from NCBI GEO using `wget` or `curl` without requiring authentication, and parse associated metadata to extract resistance scores. (See US-1)
- **FR-002**: System MUST preprocess metabolomic data by normalizing abundances, filtering low-coverage metabolites, and imputing missing values using k-nearest neighbors (k=5). (See US-1)
- **FR-003**: System MUST train a Random Forest Regressor (n_estimators=100, max_depth=10) on the training set and evaluate performance on a genotype-held-out test set. (See US-2)
- **FR-004**: System MUST extract and rank the top 20 metabolites by feature importance and output a CSV containing metabolite names, importance scores, and univariate correlation coefficients. (See US-2)
- **FR-005**: System MUST perform 1,000 iterations of permutation testing to generate a null distribution and calculate the p-value for the model's R² score. (See US-3)
- **FR-006**: System MUST apply Benjamini-Hochberg correction to all metabolite-resistance correlation p-values and report q-values, filtering results to q < 0.10. (See US-3)

### Key Entities

- **MetaboliteProfile**: Represents the chemical composition of a plant sample; attributes include sample_id, genotype_id, metabolite_abundances (map), and normalized_status.
- **ResistanceMetric**: Represents the herbivore damage score; attributes include sample_id, score_value (numeric), score_unit (e.g., "% leaf area loss"), and source_metadata_field.
- **PredictionModel**: Represents the trained Random Forest instance; attributes include model_id, training_params, feature_importance_ranking, and performance_metrics (R², MSE).
- **ValidationResult**: Represents the outcome of statistical tests; attributes include permutation_p_value, adjusted_q_values, and significance_flag.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The prediction performance (R² score) is measured against the null distribution generated by 1,000 permutations to determine statistical significance. (See US-3)
- **SC-002**: The false discovery rate is measured against the Benjamini-Hochberg adjusted p-values (q-values) to ensure the reported biomarker list is not due to multiple testing artifacts. (See US-3)
- **SC-003**: The predictive signal strength is measured against the baseline of random guessing (R² = 0) to confirm that metabolite profiles contain non-random information about resistance. (See US-3)
- **SC-004**: The dataset-variable fit is measured against the requirement that every predictor (metabolite) and outcome (resistance) must be present in the source data; any missing variable triggers a `[NEEDS CLARIFICATION]` flag. (See US-1)
- **SC-005**: The computational feasibility is measured against the constraint of completing the entire pipeline (download, train, validate) within 6 hours on a CPU-only runner with ≤7 GB RAM. (See US-2)

## Assumptions

- **Dataset Availability**: Publicly available NCBI GEO datasets contain both raw metabolomic intensity files and explicit, quantifiable resistance metrics (e.g., % leaf area loss, damage rating) in the associated metadata for the same samples.
- **Inference Framing**: The study design is observational; therefore, all findings will be framed as **associational** correlations between metabolite abundance and resistance, not causal claims of defense mechanisms, as no randomization of metabolites is possible.
- **Measurement Validity**: The resistance metrics extracted from metadata (e.g., "leaf area loss") are considered valid proxies for herbivore resistance, consistent with standard ecological literature, without requiring re-validation of the specific scoring rubrics used in the source studies.
- **Compute Constraints**: The total number of samples across the selected public datasets will be ≤ 500, allowing the entire dataset to fit within 7 GB RAM and the Random Forest training to complete within the 6-hour GitHub Actions limit without GPU acceleration.
- **Threshold Justification**: The significance threshold for metabolite selection (q < 0.10) is chosen based on common exploratory genomics/metabolomics standards; a sensitivity analysis sweeping this threshold over {0.05, 0.10, 0.15} will be performed to report how the number of identified biomarkers varies.
- **Imputation Method**: The k-nearest neighbors (k=5) imputation method is assumed to be sufficient for handling missing metabolite values in this specific dataset size and sparsity profile, without introducing significant bias.
