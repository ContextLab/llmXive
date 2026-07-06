# Feature Specification: Predicting Plant Stress Response from Publicly Available Proteomic Data

**Feature Branch**: `001-predict-plant-stress-response`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Can publicly available proteomic datasets from plants subjected to abiotic stresses (drought, salinity, heat) be used to train machine learning models that predict stress-responsive gene expression patterns in novel, unseen conditions?"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

As a researcher, I want to automatically download, normalize, and merge public proteomic and transcriptomic datasets for specific plant species under defined abiotic stresses, so that I can establish a clean, analysis-ready dataset without manual data wrangling.

**Why this priority**: Without a reliable, automated pipeline to fetch and harmonize disparate public datasets, no modeling or analysis can occur. This is the foundational step for the entire project.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script against a known subset of GEO/ProteomeXchange IDs and verifying that the output is a single, normalized CSV matrix containing protein abundances and matched gene expression values with no missing rows for the specified species/stress.

**Acceptance Scenarios**:

1. **Given** a list of valid GEO/ProteomeXchange accession numbers for Arabidopsis, rice, or wheat under drought, salinity, or heat, **When** the ingestion script is executed, **Then** it downloads the raw files, filters for low-abundance proteins (detected in < 50% of samples), imputes missing values using Left-Censored Missing (LCM) imputation, and outputs a unified matrix with protein and transcript counts.
2. **Given** a dataset with mismatched gene/protein identifiers between the proteomic and transcriptomic files, **When** the merge process runs, **Then** the system resolves identifiers using the biomaRt R package (version 2023-10) and drops only rows where no match is found, logging the drop count.
3. **Given** a dataset where the metadata does not explicitly label the stress condition, **When** the script encounters this ambiguity, **Then** it flags the record for manual review or excludes it from the training set, ensuring the final dataset contains only confirmed stress labels.

---

### User Story 2 - Baseline Model Training and Cross-Stress Validation (Priority: P2)

As a researcher, I want to train Random Forest and Support Vector Regression models on the preprocessed data using 5-fold cross-validation, so that I can evaluate the predictive accuracy of proteomic profiles for gene expression changes within and across stress types.

**Why this priority**: This addresses the core research question. The ability to train and validate models is the primary mechanism for generating scientific results.

**Independent Test**: The modeling module can be tested independently by feeding it a static, pre-saved CSV of the preprocessed data and verifying that it outputs a JSON report containing R² scores, RMSE values, and feature importance rankings for both within-stress and cross-stress validation splits.

**Acceptance Scenarios**:

1. **Given** a normalized dataset split into training ([deferred]) and held-out test ([deferred]) sets, **When** the training script runs with `RandomForestRegressor` and `SVR`, **Then** it performs 5-fold cross-validation on the training set and reports the mean R² score for each model.
2. **Given** a model trained exclusively on drought-stress data, **When** it is evaluated on a held-out salinity-stress test set, **Then** the system records the prediction performance metrics (R², RMSE) to quantify the "cross-stress" generalization gap. The ground truth is the actual measured gene expression levels in the salinity condition, not the stress label itself.
3. **Given** a trained model, **When** the feature importance extraction runs, **Then** it outputs a ranked list of top 20 proteins driving the predictions, sorted by absolute importance score, without requiring GPU acceleration.
4. **Given** a trained model, **When** a control test is run where the stress label is shuffled, **Then** the model's performance on the shuffled data must not significantly exceed the performance on the real data (p < 0.05), ensuring the model is not merely predicting the stress label.

---

### User Story 3 - Visualization and Reproducibility Reporting (Priority: P3)

As a researcher, I want the system to automatically generate publication-ready figures (scatter plots, confusion matrices, feature importance bars) and a summary report of runtime metrics, so that I can validate the results and ensure the analysis completed within the 6-hour compute limit.

**Why this priority**: While the model training is the core logic, the visualization and reporting are required to interpret the results and satisfy the project's feasibility constraints (time and reproducibility).

**Independent Test**: The reporting module can be tested by providing it with a dummy model object and a sample prediction array, verifying that it generates PNG files for all required plot types and a text summary of execution time and memory usage.

**Acceptance Scenarios**:

1. **Given** the final model predictions and ground truth values, **When** the plotting script executes, **Then** it generates a scatter plot of Predicted vs. Actual gene expression with a regression line and R² annotation, and saves it as `results/prediction_scatter.png`.
2. **Given** the cross-stress validation results, **When** the summary report is generated, **Then** it includes a confusion matrix or heat map showing performance degradation when training on one stress and testing on another.
3. **Given** the total runtime of the pipeline, **When** the system finishes, **Then** it logs the total CPU time and peak memory usage to a `runtime_metrics.json` file, confirming completion within the 6-hour GHA limit.

### Edge Cases

- What happens when a public dataset contains no matched transcriptomic data for a specific proteomic sample? (System excludes the sample and logs the exclusion reason).
- How does the system handle datasets where the plant species is mislabeled or ambiguous in the metadata? (System skips the dataset and raises a warning in the log).
- How does the system behave if the LCM imputation fails due to a column containing all missing values? (System drops the column and logs the column name).
- What happens if the 6-hour time limit is approached during model training? (System implements a checkpoint or early-stopping mechanism to ensure graceful termination and partial result saving).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download proteomic and transcriptomic data from NCBI GEO and ProteomeXchange using `wget`/`curl` for Arabidopsis, rice, and wheat under drought, salinity, and heat conditions. If multiple datasets exist for a species/stress pair, the system MUST select the one with the largest sample size (n), breaking ties by earliest publication date (See US-1).
- **FR-002**: System MUST normalize protein expression matrices, filter low-abundance proteins (defined as detected in < 50% of samples within a stress condition), and handle missing values using Left-Censored Missing (LCM) imputation (See US-1).
- **FR-003**: System MUST merge proteomic and transcriptomic datasets using the biomaRt R package (version 2023-10) for identifier mapping, excluding unmatched rows (See US-1).
- **FR-004**: System MUST train Random Forest and Support Vector Regression models using scikit-learn on CPU-only hardware (See US-2).
- **FR-005**: System MUST perform 5-fold cross-validation for within-stress generalization and evaluate performance on held-out cross-stress test sets. The ground truth for cross-stress evaluation must be the actual measured gene expression levels, not the stress label. The system MUST include a control test to verify the model is not merely predicting the stress label (See US-2).
- **FR-006**: System MUST generate feature importance plots identifying the top proteins driving stress predictions (See US-2).
- **FR-007**: System MUST produce summary figures including prediction scatter plots and cross-stress performance matrices (See US-3).
- **FR-008**: System MUST record and report total runtime metrics (CPU time, memory usage) to verify completion within the 6-hour limit (See US-3).

### Key Entities

- **ProteomicSample**: Represents a mass spectrometry measurement from a specific plant tissue under a specific stress condition, containing protein abundance values.
- **TranscriptomicSample**: Represents an RNA-seq measurement from a matched tissue/stress condition, containing gene expression counts.
- **StressCondition**: An enumerated category (Drought, Salinity, Heat) associated with a sample.
- **ModelArtifact**: The trained machine learning model object (Random Forest or SVR) along with its hyperparameters and performance metrics.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Predictive accuracy (R²) of the model mapping proteomic profiles to gene expression is measured against the performance of a null model (predicting the mean) to quantify the improvement in predictive power (See US-2).
- **SC-002**: Cross-stress generalization capability is measured by the drop in R² score when training on one stress type and testing on a different stress type (See US-2).
- **SC-003**: Computational feasibility is measured by the total runtime and peak memory usage against the GitHub Actions free-tier limits (≤6 hours, ~7 GB RAM) (See US-3).
- **SC-004**: Data completeness is measured by the percentage of initial public datasets (all datasets in GEO/ProteomeXchange matching the query keywords [species] AND [stress]) successfully merged and retained after preprocessing and identifier matching (defined as containing both matched proteomic and transcriptomic raw files with valid metadata headers) (See US-1).
- **SC-005**: Methodological validity is measured by the successful execution of 5-fold cross-validation and the absence of circular data dependencies between predictors and outcomes (See US-2).

## Assumptions

- Publicly available datasets in NCBI GEO and ProteomeXchange contain sufficient paired proteomic and transcriptomic data for Arabidopsis, rice, and wheat under drought, salinity, and heat stresses to train a meaningful model.
- The relationship between protein abundance and gene expression is sufficiently stable within stress categories to allow for supervised learning, even if cross-stress generalization is limited. The model aims to capture stress-specific signatures in protein abundance that correlate with expression patterns rather than absolute levels.
- The GitHub Actions free-tier runner (2 CPU, 7 GB RAM) is sufficient to process the preprocessed datasets and train Random Forest/SVR models within 6 hours, provided the dataset is sampled or subsetted if necessary.
- Standard identifier mapping (e.g., UniProt to Ensembl via biomaRt) exists and is reliable for the plant species and datasets selected, minimizing data loss during the merge step.
- The analysis includes a sensitivity check for post-translational regulation effects, acknowledging the biological decoupling of transcription and translation under stress.
- No GPU acceleration is required for Random Forest or SVR models on the expected dataset size, and all libraries (scikit-learn, matplotlib) are available in the standard CPU environment.