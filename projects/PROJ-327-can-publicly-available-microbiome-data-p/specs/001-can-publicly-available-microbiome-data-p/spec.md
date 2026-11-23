# Feature Specification: Can Publicly Available Microbiome Data Predict Host Plant Defense Responses?

**Feature Branch**: `001-predict-plant-defense`  
**Created**: 2023-10-27  
**Status**: Draft  
**Input**: User description: "Can Publicly Available Microbiome Data Predict Host Plant Defense Responses?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Curation and Integration (Priority: P1)

The system MUST ingest paired 16S rRNA amplicon data and metabolomics profiles for *Arabidopsis thaliana* and *Solanum lycopersicum* under herbivore stress, aligning them by species and experimental condition to create a unified analysis‑ready dataset.

**Why this priority**: Without a matched, clean dataset, no statistical modeling or hypothesis testing can occur. This is the foundational step that enables all subsequent analysis.

**Independent Test**: Can be fully tested by verifying that the pipeline successfully downloads, processes, and merges a sample subset of SRA and MetaboLights data into a single CSV/TSV file where every row contains both ASV counts and metabolite intensities for a single sample.

**Acceptance Scenarios**:

1. **Given** raw 16S reads and metabolite intensity files from NCBI SRA and MetaboLights, **When** the curation script runs, **Then** a merged table is generated where every sample ID in the microbiome table has a corresponding entry in the metabolite table.
2. **Given** samples with missing values in either modality, **When** the preprocessing step executes, **Then** those samples are filtered out, and a log reports the count of excluded samples.

---

### User Story 2 - Predictive Modeling and Validation (Priority: P2)

The system MUST train a Random Forest regressor to predict defense metabolite concentrations from microbiome principal components, using k‑fold cross‑validation to estimate predictive performance (R²).

**Why this priority**: This addresses the core research question by quantifying the relationship between microbiome composition and plant defense. It determines if the data contains sufficient signal.

**Independent Test**: Can be fully tested by running the training script on the curated dataset and verifying that it outputs a cross‑validated R² score, regression plots for each metabolite, and a feature‑importance ranking of the top 10 principal components, without requiring external GPU resources.

**Acceptance Scenarios**:

1. **Given** the integrated dataset with dimensionality reduced via PCA (fit within each CV training fold), **When** the Random Forest model trains using leave‑one‑study‑out cross‑validation, **Then** the system outputs a cross‑validated R² score, per‑metabolite regression plots, and a feature‑importance ranking of the top 10 principal components.
2. **Given** a trained model, **When** 1,000 permutation tests are executed (labels permuted within each CV fold and model retrained), **Then** the system reports a p‑value indicating whether the observed R² significantly exceeds chance levels (p < 0.05).

---

### User Story 3 - Sensitivity Analysis and Reporting (Priority: P3)

The system MUST perform a sensitivity analysis on the variance retention threshold (currently 90%) and report how model performance changes across a defined sweep of thresholds.

**Why this priority**: This ensures the results are robust to arbitrary parameter choices, addressing methodological soundness requirements regarding threshold justification.

**Independent Test**: Can be fully tested by re‑running the modeling pipeline with variance thresholds of 80 %, 90 %, and 95 %, and verifying that the output includes a comparison table showing the resulting R² scores for each threshold.

**Acceptance Scenarios**:

1. **Given** the standard pipeline configuration, **When** the sensitivity analysis flag is set, **Then** the system executes the model training three times with variance thresholds of 80 %, 90 %, and 95 %.
2. **Given** the results of the sensitivity sweep, **When** the report is generated, **Then** it explicitly lists the R² scores for each threshold and notes the variation magnitude.

---

### Edge Cases

- What happens when the public datasets contain inconsistent sample metadata (e.g., "herbivore stress" labeled differently across studies)? The system MUST normalize these labels or exclude ambiguous samples (see FR-007).
- How does the system handle a dataset where the number of samples is too small (<30) to perform meaningful cross‑validation? The system MUST halt execution and log the error “Error: insufficient samples (<30) for 5‑fold cross‑validation” (see FR-008). Verification of this guard is performed via a unit‑test fixture (see SC-005).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess 16S rRNA amplicon data from NCBI SRA using DADA2 to generate ASV tables, explicitly filtering for samples from *A. thaliana* and *S. lycopersicum* under herbivore stress (See US-1).
- **FR-002**: System MUST normalize metabolite intensities using median scaling, merge them with ASV tables, ensure a strict one-to-one sample match, filter out any samples with missing values in either modality, and log the count of excluded samples (See US-1).
- **FR-003**: System MUST reduce ASV dimensionality using Principal Component Analysis (PCA) to retain a specified variance threshold, ensuring the data fits within 7 GB RAM limits (See US-2).
- **FR-004**: System MUST train a Random Forest regressor (multi‑output) using scikit‑learn to predict metabolite concentrations from PCA scores, utilizing 5‑fold cross‑validation (See US-2).
- **FR-005**: System MUST perform 1,000 permutation iterations to generate a null distribution and calculate a p‑value for the model's R² score (See US-2).
- **FR-006**: System MUST execute a sensitivity analysis sweeping the PCA variance threshold across {0.80, 0.90, 0.95} and report the resulting R² variation (See US-3).
- **FR-007**: System MUST normalize heterogeneous metadata labels (e.g., different spellings of “herbivore stress”) to a canonical ontology; samples with irreconcilable or ambiguous labels MUST be excluded, and the exclusion count logged (See US-1).
- **FR-008**: System MUST verify that the total number of usable samples is ≥ 30 before initiating 5‑fold cross‑validation; if not, execution aborts with the error message “Error: insufficient samples (<30) for 5‑fold cross‑validation” (See US-2).
- **FR-009**: System MUST fit the PCA transformation **within each training fold** of the cross‑validation to avoid information leakage (See US-2).
- **FR-010**: System MUST report the feature‑importance ranking of the top 10 principal components after model training (See US-2).
- **FR-011**: System MUST conduct the permutation test by permuting metabolite response labels **within each CV fold**, retraining the model for each permutation, and recomputing R² to build the null distribution (See US-2).
- **FR-012**: System MUST control for study‑level batch effects by employing leave‑one‑study‑out cross‑validation (or by including study identifier as a covariate) so that predictive performance is not driven by study provenance (See US-2).
- **FR-013**: System MUST implement a multi‑output Random Forest regressor that predicts each defense metabolite individually; per‑metabolite R² scores and an aggregated mean R² must be reported (See US-2).

### Key Entities

- **Sample**: Represents a single biological specimen, containing attributes for species, treatment condition, ASV abundance counts, and metabolite concentrations.
- **ASV Table**: A matrix representing the abundance of Amplicon Sequence Variants across all samples.
- **Metabolite Profile**: A vector or matrix representing the normalized intensity of defense‑related secondary metabolites for each sample.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The cross‑validated R² score is measured against the null distribution generated by 1,000 permutation tests to determine statistical significance (See US-2).
- **SC-002**: The model's predictive performance (R²) is measured against the variance retention threshold to assess sensitivity (See US-3).
- **SC-003**: The total runtime of the analysis pipeline is measured against the 6‑hour CI job limit to ensure compute feasibility (See US-2).
- **SC-004**: The memory footprint of the PCA‑reduced dataset is measured against the 7 GB RAM limit to verify resource constraints (See US-2).
- **SC-005**: A unit‑test fixture verifies that FR‑008 aborts execution with the correct error message when the sample count is < 30.
- **SC-006**: Cross‑validation results are validated to ensure that study identifiers are not predictive (i.e., performance does not drop dramatically under leave‑one‑study‑out CV) (See FR‑012).
- **SC-007**: The permutation test procedure (FR‑011) is validated by confirming that each permutation permutes only the metabolite labels within CV folds and that the resulting p‑value distribution is uniform under the null.
- **SC-008**: Per‑metabolite R² scores and the aggregated mean R² (from FR‑013) are reported and compared against a baseline random‑guess model.

## Assumptions

- **Assumption about data availability**: Publicly available datasets in NCBI SRA and MetaboLights contain sufficient paired samples (n ≥ 30) for *A. thaliana* and *S. lycopersicum* under herbivore stress to support 5‑fold cross‑validation.
- **Assumption about methodological framing**: Since the data is observational (no random assignment), all findings regarding microbiome‑metabolite relationships will be framed as associational, not causal.
- **Assumption about computational constraints**: The Random Forest model and PCA dimensionality reduction on a subset of < 500 samples will complete within 6 hours on a 2‑core, 7 GB RAM runner without GPU acceleration.
- **Assumption about variable fit**: The selected public datasets contain the specific defense metabolites (e.g., glucosinolates, alkaloids) required to test the hypothesis; if a dataset lacks these specific variables, it will be excluded during the curation phase (See FR-002).
- **Assumption about threshold justification**: The 90 % variance retention threshold for PCA is based on common community standards for dimensionality reduction in omics data, and the sensitivity analysis will validate its robustness.
