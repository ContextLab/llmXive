# Feature Specification: Predicting Bacterial Antibiotic Resistance from Public Genomic Databases

**Feature Branch**: `001-predicting-bacterial-antibiotic-resistance`  
**Created**: 2026-08-02  
**Status**: Draft  
**Input**: User description: "Which SNPs and mobile genetic element contexts provide additional predictive information for phenotypic antibiotic resistance beyond the presence of known resistance genes in bacterial genomes?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Gene-Presence Model Execution (Priority: P1)

The system must successfully download a subset of *E. coli* and *S. aureus* genomes with associated phenotypic AST data, extract known resistance gene presence/absence profiles, and train a baseline Random Forest classifier to predict resistance phenotypes.

**Why this priority**: This establishes the negative control. Without a functioning baseline that relies solely on known resistance genes (CARD database), we cannot quantify the incremental value of SNPs or MGE context. This is the "minimum viable" scientific step.

**Independent Test**: The pipeline can be fully tested by running the data ingestion and baseline training script, verifying that the model achieves a non-trivial AUC-ROC (e.g., >0.6) on a held-out test set, and that the output metrics file is generated without GPU dependency.

**Acceptance Scenarios**:

1. **Given** the NCBI Pathogen Genome Browser and CARD API are accessible, **When** the ingestion script runs with a limit of [deferred] isolates, **Then** a feature matrix containing only binary ARG presence is generated and fits within 7 GB RAM.
2. **Given** a prepared feature matrix of ARG presence, **When** the baseline Random Forest model trains using 5-fold cross-validation on a CPU-only runner, **Then** the model outputs a valid AUC-ROC and F1-score for the baseline phenotype prediction.

---

### User Story 2 - Integrated SNP and MGE Context Model (Priority: P2)

The system must extend the feature extraction to include SNP counts per gene/intergenic region and genomic distance metrics to mobile genetic elements (transposons/plasmids), then train an integrated XGBoost model to predict resistance.

**Why this priority**: This addresses the core research question. It tests whether the additional biological signals (SNPs, MGE proximity) provide predictive power beyond the baseline.

**Independent Test**: The pipeline can be fully tested by executing the extended feature extraction (using `snp-sites` and distance calculations), training the integrated model, and comparing its performance metrics directly against the baseline output from User Story 1.

**Acceptance Scenarios**:

1. **Given** the core genome reference and raw assemblies, **When** the feature extraction module runs, **Then** the resulting matrix includes binary ARG presence, SNP counts, and binned MGE distance metrics, all normalized via `StandardScaler`.
2. **Given** the integrated feature matrix, **When** the XGBoost model trains with 5-fold cross-validation, **Then** the model outputs performance metrics (AUC-ROC, F1) that are strictly greater than or equal to the baseline model's metrics (demonstrating non-degradation).

---

### User Story 3 - Statistical Validation and Significance Testing (Priority: P3)

The system must perform Mann-Whitney U tests to compare the distribution of identified SNPs and MGE distances between resistant and sensitive phenotypes, and generate a report quantifying the added predictive value.

**Why this priority**: This provides the statistical rigor required to claim "significance" rather than just correlation in the model weights. It validates the biological hypothesis that these specific variants are associated with the phenotype.

**Independent Test**: The pipeline can be fully tested by running the statistical validation script on the model's feature importance rankings or raw feature distributions, producing a p-value report that identifies specific SNPs/MGE distances as statistically significant predictors.

**Acceptance Scenarios**:

1. **Given** the feature matrix and phenotype labels, **When** the statistical validation module executes Mann-Whitney U tests, **Then** it outputs a list of SNPs and MGE distances with p-values < 0.05 (after correction) that differ significantly between resistant and sensitive groups.
2. **Given** the baseline and integrated model metrics, **When** the comparison report is generated, **Then** it explicitly states the delta in AUC-ROC and F1-score, confirming if the integrated model captures distinct biological signals.

---

### Edge Cases

- **What happens when** the NCBI download fails or the API returns fewer than 1,000 isolates? The system must gracefully handle the reduced sample size, log a warning, and proceed with the available data, noting the power limitation in the final report.
- **How does the system handle** genomes with ambiguous assembly quality (e.g., high fragmentation) that prevent accurate SNP calling or MGE distance calculation? The system must filter out isolates where the core genome alignment covers <90% of the reference, ensuring only high-quality data enters the model.
- **What happens when** a specific antibiotic phenotype has a highly imbalanced distribution (e.g., [deferred] sensitive, [deferred] resistant)? The system must apply stratified sampling during 5-fold cross-validation to ensure each fold contains a representative proportion of resistant cases.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess a subset of [deferred] *E. coli* and *S. aureus* genomes with phenotypic AST data from NCBI and CARD, ensuring the dataset fits within 7 GB RAM. (See US-1)
- **FR-002**: System MUST extract binary presence/absence of known resistance genes using CARD's API as the primary feature set for the baseline model. (See US-1)
- **FR-003**: System MUST call SNPs against a core genome reference using `snp-sites` and calculate the genomic distance from each ARG to the nearest transposon insertion site or plasmid origin. (See US-2)
- **FR-004**: System MUST train a Random Forest classifier (baseline) and an XGBoost model (integrated) using 5-fold cross-validation on CPU-only hardware, ensuring no GPU/CUDA dependencies. (See US-2)
- **FR-005**: System MUST perform Mann-Whitney U tests to compare the distribution of SNPs and MGE distances between resistant and sensitive phenotypes, applying a multiple-comparison correction (e.g., Bonferroni or FDR). (See US-3)
- **FR-006**: System MUST generate a comparative report that explicitly quantifies the increase in AUC-ROC and F1-score of the integrated model over the baseline. (See US-3)
- **FR-007**: System MUST implement a sensitivity analysis that sweeps the classification probability threshold over {0.3, 0.5, 0.7} and reports the variation in false-positive and false-negative rates. (See US-3)

### Key Entities

- **Genomic Isolate**: Represents a bacterial sample, containing attributes: `isolate_id`, `species`, `assembly_quality`, `phenotype_label` (resistant/sensitive), `antibiotic_target`.
- **Resistance Feature Vector**: Represents the encoded data for an isolate, containing attributes: `arg_presence_vector` (binary), `snp_counts` (integer), `mge_distances` (float/binned), `normalized_features`.
- **Model Artifact**: Represents the trained classifier, containing attributes: `model_type` (Random Forest/XGBoost), `cross_validation_metrics` (AUC, F1), `feature_importance_ranking`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The increase in AUC-ROC of the integrated model (SNPs + MGE) compared to the baseline (ARGs only) is measured against the baseline AUC-ROC to quantify added predictive value. (See US-3)
- **SC-002**: The statistical significance of specific SNPs and MGE distances is measured against the null hypothesis using Mann-Whitney U test p-values (adjusted for multiple comparisons). (See US-3)
- **SC-003**: The computational feasibility is measured against the GitHub Actions free-tier constraints (≤6h runtime, ≤7 GB RAM, CPU-only) by verifying the job completes without OOM or timeout errors. (See US-1)
- **SC-004**: The sensitivity of the decision threshold is measured by reporting the range of false-positive rates across the swept thresholds {0.3, 0.5, 0.7}. (See US-3)
- **SC-005**: The sample size adequacy is measured against the power requirement for the observed effect size, with a note on whether the [deferred]-isolate limit provides sufficient power for the detected associations. (See US-3)

## Assumptions

- **Dataset Variable Fit**: It is assumed that the NCBI Pathogen Genome Browser and CARD database contain the necessary phenotypic AST data and that the genomic assemblies are of sufficient quality to call SNPs and identify MGEs. If the dataset lacks specific variables (e.g., specific antibiotic classes), a `[NEEDS CLARIFICATION: does dataset contain AST for antibiotic X?]` marker will be inserted.
- **Inference Framing**: Since this is an observational study using public databases without random assignment, all findings regarding SNPs and MGEs will be framed as **associational** predictors, not causal mechanisms, unless a specific identification strategy is introduced in future work.
- **Compute Feasibility**: It is assumed that the [deferred] isolate dataset and the selected models (Random Forest, XGBoost) will fit within the 7 GB RAM and 6-hour runtime limits of the GitHub Actions free-tier runner without requiring GPU acceleration or 8-bit quantization.
- **Threshold Justification**: The classification probability threshold of 0.5 is used as the default decision boundary, justified by community standards for binary classification, with a mandatory sensitivity analysis (FR-007) to verify robustness.
- **Measurement Validity**: It is assumed that the phenotypic AST data in the source databases is reliable and that the CARD database provides a comprehensive and validated catalog of resistance genes for the target species.
- **Predictor Collinearity**: It is assumed that while SNPs and MGE distances may be correlated with ARG presence, the model will treat them as distinct features, and the statistical validation will account for collinearity by focusing on joint predictive performance rather than claiming independent causal effects for correlated predictors.
