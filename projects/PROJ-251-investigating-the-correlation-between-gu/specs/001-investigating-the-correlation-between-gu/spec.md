# Feature Specification: Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination

**Feature Branch**: `001-gene-regulation`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Validation (Priority: P1)

The system must ingest pre-processed 16S rRNA OTU tables and corresponding serology metadata from NCBI SRA, filtering for subjects with complete baseline and post-vaccination records.

**Why this priority**: Without a clean, complete dataset, no statistical analysis or modeling can occur. This is the foundational step for the entire research pipeline.

**Independent Test**: The system can be tested by running the ingestion script against a known valid subset of the target dataset and verifying that the output CSV contains exactly N rows (where N is the count of subjects with complete data) and that all required columns (taxa abundances, antibody titers) are populated with no nulls.

**Acceptance Scenarios**:

1. **Given** a raw NCBI SRA archive containing 16S data and serology metadata, **When** the ingestion script filters for subjects with both baseline microbiome and post-vaccination antibody titer records, **Then** the output dataset contains exactly the subset of subjects with complete data (target N ≥ 50) and excludes any with missing values.
2. **Given** a dataset where some subjects lack post-vaccination titers, **When** the system processes the data, **Then** those subjects are excluded, and a log entry records the count of excluded subjects.
3. **Given** the ingested data, **When** the system validates the data types, **Then** microbiome abundance columns are numeric, and titer columns are numeric and log-transformed where applicable.

---

### User Story 2 - Correlation Analysis and Multiple Testing Correction (Priority: P2)

The system must calculate diversity metrics (Shannon index) and perform Spearman rank correlation tests between taxa abundance and log-transformed antibody titers, applying Benjamini-Hochberg correction for multiple comparisons. The system must first apply a Centered Log-Ratio (CLR) transformation to the microbiome data to address compositional constraints.

**Why this priority**: This is the core scientific inquiry. It directly addresses the research question regarding specific taxa correlations while ensuring statistical rigor against false positives and compositional bias.

**Independent Test**: The system can be tested by running the analysis on a synthetic dataset with known correlations and verifying that the output correctly identifies the expected significant taxa and reports the corrected p-values.

**Acceptance Scenarios**:

1. **Given** a dataset of normalized microbiome abundances and log-transformed antibody titers, **When** the system applies CLR transformation and then calculates Spearman rank correlations for each taxon, **Then** the output includes correlation coefficients and raw p-values for all tested taxa.
2. **Given** the raw p-values from correlation tests, **When** the system applies Benjamini-Hochberg correction, **Then** the output includes adjusted p-values (FDR) and flags taxa as significant only if adjusted p < 0.05.
3. **Given** the correlation results, **When** the system calculates the Shannon diversity index, **Then** the index is computed for each subject and included in the output dataset for potential secondary analysis.

---

### User Story 3 - Predictive Modeling and Nested Cross-Validation (Priority: P3)

The system must train a lightweight Random Forest classifier to predict high/low responder status based on top correlated taxa, using nested 5-fold cross-validation to prevent overfitting and data leakage. Feature selection (identifying top taxa) MUST occur inside the training loop of each outer fold.

**Why this priority**: This validates the predictive utility of the identified taxa, moving beyond simple correlation to a model-based assessment of biomarker potential, ensuring the validation is scientifically sound.

**Independent Test**: The system can be tested by running the training pipeline on the ingested dataset and verifying that the cross-validation accuracy is reported, that feature selection is performed within each fold, and that the model does not overfit (e.g., training accuracy is not significantly higher than validation accuracy).

**Acceptance Scenarios**:

1. **Given** the top correlated taxa identified via a process strictly contained within the training folds, **When** the system trains a Random Forest classifier to predict responder status (defined by seroconversion or absolute titer), **Then** the model reports mean accuracy and standard deviation across the 5 outer folds.
2. **Given** the trained model, **When** the system performs nested 5-fold cross-validation, **Then** the output includes the mean accuracy and standard deviation across the folds, and the feature selection step is logged as occurring within each training split.
3. **Given** the model predictions, **When** the system evaluates performance, **Then** the output includes a confusion matrix or classification report detailing precision, recall, and F1-score for high and low responders.

---

### Edge Cases

- What happens when the dataset contains taxa with zero variance (all subjects have 0 abundance)? The system must exclude these taxa from correlation testing to avoid division by zero or undefined statistics.
- How does the system handle subjects with antibody titers below the limit of detection? The system must treat these as a specific value (e.g., half the detection limit) or exclude them, with the choice documented in the assumptions.
- What happens if the number of subjects with complete data is less than 50? The system must halt execution and report a "Insufficient Sample Size" error, preventing invalid statistical inference.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest 16S rRNA OTU tables and serology metadata from NCBI SRA and filter for subjects with complete baseline and post-vaccination records (See US-1).
- **FR-002**: System MUST normalize microbiome data to relative abundance, apply a Centered Log-Ratio (CLR) transformation, and log-transform antibody titers prior to analysis (See US-2).
- **FR-003**: System MUST calculate Shannon diversity index for each subject (See US-2).
- **FR-004**: System MUST perform Spearman rank correlation tests between each CLR-transformed taxon abundance and log-transformed antibody titers (See US-2).
- **FR-005**: System MUST apply Benjamini-Hochberg correction to all correlation p-values to control false discovery rate (See US-2).
- **FR-006**: System MUST train a Random Forest classifier using top correlated taxa to predict responder status, where feature selection is performed strictly within the training fold (See US-3).
- **FR-007**: System MUST perform nested 5-fold cross-validation on the Random Forest model, ensuring feature selection occurs inside the training loop of each fold, to estimate generalization performance (See US-3).
- **FR-008**: System MUST output all intermediate artifacts (filtered data, correlation results, model metrics) in JSON/CSV format (See US-1, US-2, US-3).

### Key Entities

- **Subject**: Represents an individual participant in the cohort, containing attributes for baseline microbiome composition, post-vaccination antibody titers, and derived diversity metrics.
- **Taxon**: Represents a specific microbial taxon (e.g., genus or species) with attributes for relative abundance across subjects and correlation statistics.
- **CorrelationResult**: Represents the statistical output of the correlation test between a taxon and antibody titers, including coefficient, raw p-value, and adjusted p-value.
- **ModelPerformance**: Represents the cross-validation results of the Random Forest classifier, including accuracy, precision, recall, and F1-score.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The number of subjects with complete data is measured against the target minimum of 50 (See US-1).
- **SC-002**: The false discovery rate (FDR) of significant correlations is measured against a corrected p-value threshold. (See US-2).
- **SC-003**: The predictive accuracy of the Random Forest model is measured against the target of >60% on nested cross-validation (See US-3).
- **SC-004**: The number of taxa significantly correlated with antibody titers (after correction) is measured against the expected range of a low single-digit count to a higher single-digit count. (See US-2).
- **SC-005**: The computational runtime of the entire pipeline is measured against the time limit for a GitHub Actions free-tier runner. (See Assumptions).

## Assumptions

- The pre-processed 16S rRNA OTU tables and serology metadata from NCBI SRA contain all necessary variables (baseline taxa abundances, post-vaccination antibody titers) for the analysis.
- The dataset is observational; therefore, findings will be framed as associational, not causal.
- The number of subjects with complete data (N ≥ 50) is sufficient to achieve statistical power for the planned correlation and classification analyses; if N < 50, the analysis will be halted.
- The Random Forest model will be trained on a CPU-only environment with default precision, avoiding GPU-specific optimizations or 8-bit quantization.
- The Benjamini-Hochberg correction will be applied to control the false discovery rate at a standard community threshold for microbiome studies.
- The analysis will be performed on a sampled subset of the data if the full dataset exceeds RAM or disk limits, with the sampling strategy documented.
- The threshold for defining "high" vs. "low" responders is based on seroconversion (≥4-fold rise in titer) or an absolute titer threshold (e.g., HAI ≥ 40), aligning with influenza vaccine standards. A sensitivity analysis will be performed by sweeping the threshold at ±10% of the defined cutoff to assess stability of the model's accuracy.