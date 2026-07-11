# Feature Specification: Predicting Antibiotic Resistance Evolution from Genomic Sequences

**Feature Branch**: `001-predict-antibiotic-resistance`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Predicting Antibiotic Resistance Evolution from Genomic Sequences"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Feature Extraction (Priority: P1)

As a computational biologist, I need to download *E. coli* genomic sequences and susceptibility metadata from public databases (NCBI Pathogen Detection, CARD), preprocess them to identify SNPs and resistance genes, and generate a structured feature matrix so that I can have a clean dataset ready for modeling.

**Why this priority**: Without a validated, processed feature matrix linking genotypes to phenotypes, no downstream analysis or model training is possible. This is the foundational data pipeline.

**Independent Test**: The pipeline can be tested by running the preprocessing script on a small subset of isolates (e.g., 50) and verifying the output CSV contains the expected columns: `isolate_id`, `gene_presence_matrix` (binary), `snp_counts` (numeric), and `resistance_phenotype` (binary), matching the schema defined in Key Entities.

**Acceptance Scenarios**:

1. **Given** a list of valid isolate IDs from NCBI Pathogen Detection, **When** the ingestion script runs, **Then** the system downloads the FASTA sequences and associated metadata without errors.
2. **Given** downloaded FASTA files and a reference genome, **When** the Snippy and ARIBA tools are executed, **Then** a feature matrix is generated with binary columns for gene presence and numeric columns for SNP counts per gene.
3. **Given** the generated feature matrix, **When** a validation check is performed, **Then** the number of rows in the matrix exactly matches the number of isolates in the input metadata, and no rows contain missing values for the primary outcome variable.

---

### User Story 2 - Model Training and Validation (Priority: P2)

As a data scientist, I need to train logistic regression and random forest models on the processed feature matrix using stratified splits and 5-fold cross-validation, ensuring mechanism-blind validation for known resistance genes, to determine which genomic features best predict resistance phenotypes for each antibiotic class.

**Why this priority**: This is the core analytical engine. It transforms raw data into predictive insights and provides the primary metrics (AUC-ROC) to answer the research question while avoiding circular validation.

**Independent Test**: The training module can be tested by running it on a fixed, small training set and verifying that it outputs model weights, a confusion matrix, and an AUC-ROC score that is reproducible across runs (given a fixed random seed) and that the mechanism-blind check excludes known resistance markers from the feature set for the target class.

**Acceptance Scenarios**:

1. **Given** a pre-processed feature matrix with a binary resistance label, **When** the training script executes with a fixed random seed, **Then** it produces separate trained models (Logistic Regression and Random Forest) for each antibiotic class and saves their weights to disk.
2. **Given** the trained models, **When** they are evaluated on the held-out test set, **Then** the system outputs AUC-ROC scores and precision-recall curves for each antibiotic class, excluding the canonical resistance gene for that class from the input features.
3. **Given** the cross-validation results, **When** the feature importance is calculated, **Then** the top 10 genomic features contributing to the prediction (excluding the target resistance gene) are ranked and exported to a summary table.

---

### User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

As a researcher, I need to perform phylogenetically-aware permutation testing and sensitivity analysis on classification thresholds to ensure the model's predictive power is not due to chance or population structure and that the results are robust to parameter variations.

**Why this priority**: This ensures the scientific validity of the findings. Without phylogenetically-aware permutation, a high AUC could be a false positive due to clonal structure; without sensitivity analysis, the results might be fragile to minor parameter changes.

**Independent Test**: The analysis script can be tested by running the permutation test on a known random dataset (where no signal exists) and verifying the p-value is > 0.05, and by running the sensitivity sweep to confirm the output shows variance in performance metrics across thresholds.

**Acceptance Scenarios**:

1. **Given** the trained model and the test set, **When** 1000 phylogenetically-aware permutation iterations are executed (respecting clonal lineages), **Then** the system calculates a null distribution and reports a p-value indicating whether the observed AUC-ROC is statistically significant (p < 0.05).
2. **Given** a decision threshold (e.g., 0.5), **When** the sensitivity analysis sweeps the threshold across {0.4, 0.45, 0.5, 0.55, 0.6}, **Then** the system reports how the false-positive and false-negative rates vary across these values.
3. **Given** the final results, **When** the reproducibility script is executed, **Then** it regenerates all figures (ROC curves, feature importance) and tables from the saved model weights and data.

---

### Edge Cases

- **What happens when** a specific antibiotic class has fewer than 50 isolates in the dataset? The system must exclude that class from training to prevent model collapse and log a warning.
- **What happens when** all classes in the dataset have fewer than 50 isolates? The system must abort execution with error code E004 ("Insufficient data for any class") and produce no model output.
- **How does the system handle** missing metadata for a subset of isolates (e.g., susceptibility data is present but the specific antibiotic tested is unknown)? The system must drop these rows from the training set and report the exclusion count in the preprocessing summary.
- **What happens when** the genomic feature extraction fails for a specific isolate (e.g., Snippy cannot align the sequence)? The system must skip that isolate, log the error with the isolate ID, and proceed with the remaining data without crashing the entire pipeline.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download *E. coli* FASTA sequences and susceptibility metadata from NCBI Pathogen Detection and CARD, limiting the dataset to ≤ 5000 isolates to fit within 7 GB RAM (See US-1).
- **FR-002**: System MUST preprocess sequences to call SNPs using Snippy, identify resistance genes via ARIBA, and extract copy number variations, outputting a structured feature matrix (See US-1).
- **FR-003**: System MUST split the feature matrix into training, validation, and test sets using a stratified approach (specific ratios are implementation details) to ensure balanced representation (See US-1).
- **FR-004**: System MUST train Logistic Regression and Random Forest models using scikit-learn with 5-fold cross-validation, ensuring no GPU/CUDA dependencies (See US-2).
- **FR-005**: System MUST perform 1000 iterations of phylogenetically-aware permutation testing to establish a null distribution for significance assessment (p < 0.05), respecting clonal lineages to avoid false positives (See US-3).
- **FR-006**: System MUST execute a sensitivity analysis sweeping the classification threshold over {0.4, 0.45, 0.5, 0.55, 0.6} and report the variation in false-positive/false-negative rates (See US-3).
- **FR-007**: System MUST generate and save ROC curves, precision-recall curves, and feature importance bar plots using matplotlib/seaborn (See US-2).
- **FR-008**: System MUST perform mechanism-blind validation by excluding known resistance genes for the target antibiotic class from the feature set during training and testing to prevent circular validation (See US-2).
- **FR-009**: System MUST train separate, mechanism-specific models for each antibiotic class rather than a single multi-class model to avoid spurious correlations (See US-2).

### Key Entities

- **Isolate**: Represents a single *E. coli* sample, containing attributes for sequence data, metadata (antibiotic susceptibility), and derived genomic features.
- **GenomicFeature**: Represents a specific biological marker (e.g., a specific SNP, a resistance gene presence flag, or a copy number count) used as a predictor in the model.
- **ResistancePhenotype**: The binary outcome variable (Resistant/Susceptible) for a specific antibiotic class associated with an Isolate.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: Model predictive performance (AUC-ROC) is measured against the held-out test set to determine if cross-validated accuracy exceeds a baseline (specific value determined in implementation phase) (See US-2).
- **SC-002**: Statistical significance of the model is measured against the null distribution generated by 1000 phylogenetically-aware permutation iterations, requiring p < 0.05 to claim signal (See US-3).
- **SC-003**: Model robustness is measured against the sensitivity analysis sweep, reporting the range of variation in false-positive rates across the threshold set {0.4, 0.45, 0.5, 0.55, 0.6} (See US-3).
- **SC-004**: Computational feasibility is measured against the 7 GB RAM and 6-hour time limit of the free-tier CI runner, ensuring the full pipeline completes without OOM or timeout errors (See US-1, US-2).

## Assumptions

- The NCBI Pathogen Detection and CARD databases contain sufficient *E. coli* isolates with paired genomic sequences and antibiotic susceptibility data to form a dataset of ≥ 1000 samples after filtering.
- The critical variables for the model are defined as chromosomal SNPs and canonical resistance gene presence. If plasmid copy number data is missing from the source metadata, the system MUST proceed with chromosomal features only and log warning W003 ("Plasmid data missing; proceeding with chromosomal features only").
- The analysis is observational; therefore, all findings will be framed as associational rather than causal, as no random assignment of mutations is performed.
- The free-tier GitHub Actions runner (2 CPU, 7 GB RAM) is sufficient to process ≤ 5000 isolates using scikit-learn and standard statistical tools without GPU acceleration.
- The `Snippy` and `ARIBA` tools are available in the environment or can be installed via standard package managers without requiring proprietary licenses or heavy dependencies.
- The dataset contains no severe class imbalance (e.g., >95% susceptible) that would render the random forest model ineffective; if imbalance is detected, stratified sampling will be used, but no synthetic oversampling (SMOTE) is assumed unless specified.
- The threshold justification for the primary classification boundary (0.5) is based on the community standard for binary classification unless the sensitivity analysis indicates a significantly different optimal cutoff.