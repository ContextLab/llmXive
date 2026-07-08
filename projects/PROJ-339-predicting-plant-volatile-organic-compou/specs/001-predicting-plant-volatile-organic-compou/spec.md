# Feature Specification: Predicting Plant VOC Emission Profiles from Genomic and Environmental Data

**Feature Branch**: `001-predict-voc-profiles`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Predicting Plant Volatile Organic Compound Emission Profiles from Publicly Available Genomic and Environmental Data"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

The system must successfully ingest paired RNA-seq and VOC metabolomics data from public repositories (NCBI GEO, Metabolomics Workbench) for *Arabidopsis thaliana*, normalize transcript counts to TPM, handle missing values via imputation, and merge datasets based on shared experimental metadata (treatment, time, tissue) ensuring exact sample pairing.

**Why this priority**: Without a clean, merged dataset with exact sample pairing, no analysis can occur. This is the foundational step that enables all subsequent modeling and validation.

**Independent Test**: The pipeline can be executed on a sample subset of public data, producing a single merged CSV file with normalized genomic and environmental features alongside VOC targets, which can be inspected for completeness and data type correctness.

**Acceptance Scenarios**:

1. **Given** a list of valid GEO and Metabolomics Workbench accession numbers for *Arabidopsis thaliana* stress studies, **When** the ingestion script runs, **Then** the output is a merged dataset containing at least 50 rows with normalized transcript counts (TPM), environmental variables, and VOC concentrations. If the dataset contains fewer than 50 rows, the system MUST exclude these samples from the modeling pipeline and emit a warning.
2. **Given** input files with missing values in transcript or VOC columns, **When** the preprocessing step runs, **Then** missing values are imputed (e.g., using median or KNN) without dropping a substantial portion of the original rows.
3. **Given** a merged dataset, **When** the data validation check runs, **Then** all numeric columns have no non-numeric entries and all categorical columns have consistent encoding.

---

### User Story 2 - Predictive Model Training and Evaluation (Priority: P2)

The system must train a Random Forest Regressor using scikit-learn on the prepared dataset to predict VOC emission levels, perform 5-fold cross-validation, and report R² and RMSE metrics.

**Why this priority**: This delivers the core predictive capability. It validates whether the integrated data can explain VOC variability, addressing the primary research question.

**Independent Test**: The model training script can be run on a CPU-only environment, completing within 1 hour for a sample subset (≤50 samples) or 6 hours for the full dataset, and outputting a JSON file with cross-validation metrics (R², RMSE) and a trained model artifact.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset with ≥50 samples, **When** the Random Forest model is trained with 5-fold cross-validation, **Then** the output includes an R² score and RMSE value.
2. **Given** the trained model, **When** evaluated on a held-out test set ([deferred] of the dataset), **Then** the system calculates and reports the R² score and RMSE value.
3. **Given** a dataset with missing environmental or genomic features, **When** the model training runs, **Then** the process does not crash and handles missing data gracefully (via imputation or exclusion) as defined in the preprocessing step.

---

### User Story 3 - Feature Importance and Biological Interpretation (Priority: P3)

The system must calculate permutation feature importance and generate SHAP value visualizations to identify top genomic and environmental predictors, and validate these against known biological pathways (e.g., jasmonic acid signaling) by reporting overlap statistics.

**Why this priority**: This provides the scientific insight—identifying *which* genes and environmental factors drive VOC emissions—fulfilling the "gap" in understanding predictive determinants.

**Independent Test**: The analysis script can be run on the trained model, producing a ranked list of top 10 features (genes and environmental variables) and a SHAP summary plot, which can be cross-referenced with existing literature.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** permutation feature importance is calculated, **Then** the output lists the top features with their importance scores.
2. **Given** the top genomic features, **When** compared against known terpene synthase gene families, **Then** the system outputs a ranked list and a calculated overlap proportion for manual validation.
3. **Given** the SHAP analysis results, **When** visualized, **Then** the plot clearly shows the direction and magnitude of feature contributions for specific VOC classes.

---

### Edge Cases

- What happens when the public dataset contains fewer than 50 samples (insufficient for robust cross-validation)?
- How does the system handle VOC measurements below the detection limit (censored data)?
- What if the merged dataset has no overlap in metadata between genomic and VOC studies?
- How does the system behave if a specific gene family (e.g., terpene synthases) is completely absent from the dataset?

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest and parse RNA-seq and VOC metabolomics data from NCBI GEO and Metabolomics Workbench for *Arabidopsis thaliana* (See US-1).
- **FR-002**: System MUST normalize transcript counts to TPM and impute missing values using a defined strategy (See US-1).
- **FR-003**: System MUST merge genomic and environmental features with VOC targets ONLY if they originate from the SAME biological replicate (sample ID match). If exact pairing is impossible, the system MUST exclude the unpaired samples (See US-1).
- **FR-004**: System MUST train a Random Forest Regressor using scikit-learn on CPU-only hardware (See US-2).
- **FR-005**: System MUST perform 5-fold cross-validation and report R² and RMSE metrics (See US-2).
- **FR-006**: System MUST calculate permutation feature importance to rank predictors (See US-3).
- **FR-007**: System MUST generate SHAP value visualizations for feature interpretation (See US-3).
- **FR-008**: System MUST report the proportion of top genomic features overlapping with known VOC-related gene families (e.g., terpene synthases) as a descriptive statistic, not a pass/fail criterion (See US-3).
- **FR-009**: System MUST frame findings as associational, not causal, by generating a disclaimer in all reports and JSON outputs stating: "Findings are associational due to observational data" (See US-2).
- **FR-010**: System MUST include a multiple-comparison correction procedure for feature importance testing, as required by Constitution Principle VII (Interpretable Modeling) (See US-3).
- **FR-011**: System MUST validate that each experimental condition has at least 3 biological replicates. If fewer than 3 replicates exist for a condition, the system MUST exclude that condition from the cross-validation folds (See US-1).
- **FR-012**: System MUST exclude samples from the training set if continuous environmental metadata (temperature, light intensity) are missing, rather than inferring them from categorical labels (See US-1).

### Key Entities

- **Sample**: Represents a single experimental condition (e.g., specific treatment, time point, tissue) with associated genomic and environmental features and VOC targets.
- **GenomicFeature**: Represents a gene expression level (TPM) or pathway-specific aggregate.
- **EnvironmentalFeature**: Represents temperature, light intensity, treatment type, or other metadata.
- **VOCProfile**: Represents the measured concentration of specific volatile organic compounds.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The proportion of variance in VOC profiles explained by the model (R²) is measured against the baseline of a mean-predictor model (See US-2).
- **SC-002**: The predictive accuracy (RMSE) is measured against the observed variability in the test set (See US-2).
- **SC-003**: The proportion of top genomic features overlapping with known VOC-related gene families (e.g., terpene synthases) is measured as a descriptive statistic against existing literature (See US-3).
- **SC-004**: The stability of feature importance rankings is measured across 5-fold cross-validation splits (See US-3).
- **SC-005**: The false discovery rate for feature importance is measured against a corrected significance threshold (See US-3).

## Assumptions

- Publicly available datasets (NCBI GEO, Metabolomics Workbench) contain sufficient paired RNA-seq and VOC data for *Arabidopsis thaliana* under stress conditions to support a sample size of ≥50.
- The Random Forest Regressor, when trained on the full dataset, is expected to complete within a reasonable timeframe (e.g., 6 hours) on standard CPU hardware, though specific hardware constraints are deferred.
- Missing values in the dataset can be adequately handled via median imputation without introducing significant bias.
- The relationship between genomic/environmental features and VOC emissions is primarily linear or monotonic, suitable for Random Forest modeling.
- The dataset contains at least one known VOC-related gene family (e.g., terpene synthases) for validation purposes.
- Environmental metadata (temperature, light intensity, CO2 levels) are required for the analysis. If specific continuous values are missing in the public dataset, the sample is excluded rather than inferred.
- VOC measurements are expected to be quantitative concentration values (e.g., ng g⁻¹ FW, ng h⁻¹ m⁻²). Qualitative (presence/absence) data is insufficient for regression modeling and will be excluded.
- The dataset is expected to include at least 3 biological replicates per experimental condition to enable robust statistical testing and variance estimation.