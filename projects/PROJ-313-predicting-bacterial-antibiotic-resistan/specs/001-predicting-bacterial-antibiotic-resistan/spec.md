# Feature Specification: Predicting Bacterial Antibiotic Resistance from Public Genomic Databases

**Feature Branch**: `001-predicting-bacterial-antibiotic-resistance`  
**Created**: 2026-08-02  
**Status**: Draft  
**Input**: User description: "Which SNPs and mobile genetic element contexts provide additional predictive information for phenotypic antibiotic resistance beyond the presence of known resistance genes in bacterial genomes?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Baseline Gene-Presence Model Execution (Priority: P1)

The system must successfully download a subset of *E. coli* and *S. aureus* genomes with associated phenotypic AST data, extract known resistance gene presence/absence profiles, and train baseline classifiers (XGBoost and Random Forest) to predict resistance phenotypes.

**Why this priority**: This establishes the negative control. Without a functioning baseline that relies solely on known resistance genes (CARD database), we cannot quantify the incremental value of SNPs or MGE context. This is the "minimum viable" scientific step.

**Independent Test**: The pipeline can be fully tested by running the data ingestion and baseline training script, verifying that the AUC‑ROC metric is reported and compared against a deferred sanity threshold, and that the output metrics file is generated without GPU dependency.

**Acceptance Scenarios**:

1. **Given** the NCBI Pathogen Genome Browser and CARD API are accessible, **When** the ingestion script runs with a limit of [deferred] of isolates held out as an outer test set, **Then** a feature matrix containing only binary ARG presence is generated and fits within 7 GB RAM.
2. **Given** a prepared feature matrix of ARG presence, **When** the baseline models train using a nested evaluation protocol (outer 5‑fold cross‑validation with a A typical held‑out test split will be employed.; inner 5‑fold cross‑validation on the training folds for hyper‑parameter tuning), **Then** each model outputs AUC‑ROC, Precision, Recall, and F1‑score on the outer test split and writes a metrics file without exceeding the resource limits.

---

### User Story 2 - Integrated SNP and MGE Context Model (Priority: P2)

The system must extend the feature extraction to include SNP counts per gene/intergenic region and genomic distance metrics to mobile genetic elements (transposons/plasmids), then train integrated classifiers (XGBoost and Random Forest) to predict resistance.

**Why this priority**: This addresses the core research question. It tests whether the additional biological signals (SNPs, MGE proximity) provide predictive power beyond the baseline.

**Independent Test**: The pipeline can be fully tested by executing the extended feature extraction (using `snp-sites`, `snippy` for core alignment, MOB‑suite for plasmid detection, and ISfinder via the `isfinder` utility for transposon sites), training the integrated models with the same nested protocol as US‑1, and comparing their performance metrics directly against the baseline output from User Story 1.

**Acceptance Scenarios**:

1. **Given** the core genome reference and raw assemblies, **When** the feature extraction module runs, **Then** the resulting matrix includes binary ARG presence, SNP counts, and binned MGE distance metrics, all normalized via `StandardScaler`.
2. **Given** the integrated feature matrix, **When** the integrated models train with the nested protocol (inner 5‑fold CV on the training set, outer held‑out test evaluation), **Then** each model outputs performance metrics (AUC‑ROC, Precision, Recall, F1) and the comparative report quantifies the delta (which may be ≤ 0) relative to the baseline model’s metrics, together with a paired significance test on the outer test predictions.

---

### User Story 3 - Statistical Validation and Significance Testing (Priority: P3)

The system must perform permutation‑based feature importance assessment and phylogeny‑aware permutation testing to compare the distribution of identified SNPs and MGE distances between resistant and sensitive phenotypes, and generate a report quantifying the added predictive value.

**Why this priority**: This provides the statistical rigor required to claim "significance" rather than just correlation in the model weights. It validates the biological hypothesis that these specific variants are associated with the phenotype while accounting for population structure.

**Independent Test**: The pipeline can be fully tested by running the statistical validation script on the model's feature importance rankings and raw feature distributions, producing a p‑value report that identifies specific SNPs/MGE distances as statistically significant predictors after permutation‑based multiple‑testing correction and phylogeny‑aware adjustment.

**Acceptance Scenarios**:

1. **Given** the feature matrix and phenotype labels, **When** the statistical validation module executes permutation importance (10 000 permutations) and a mixed‑effects model that includes a kinship matrix (via `pyseer`), **Then** it outputs a list of SNPs and MGE distances with FDR‑adjusted p‑values < 0.05 that differ significantly between resistant and sensitive groups, and confirms that results are robust to phylogenetic structure.
2. **Given** the baseline and integrated model predictions on the outer held‑out test set, **When** the comparison report is generated, **Then** it performs a two‑sided Wilcoxon signed‑rank test on the paired predicted probabilities and explicitly states the p‑value, confirming whether the integrated model captures distinct biological signals.

---

### Edge Cases

- **What happens when** the NCBI download fails or the API returns fewer than the required isolates? The system must gracefully handle the reduced sample size, log a warning, and proceed with the available data, noting the power limitation in the final report.
- **How does the system handle** genomes with ambiguous assembly quality (e.g., high fragmentation) that prevent accurate SNP calling or MGE distance calculation? The system must filter out isolates where the core genome alignment covers < 90 % of the reference, ensuring only high‑quality data enters the model.
- **What happens when** a specific antibiotic phenotype has a highly imbalanced distribution (e.g., < 10 % resistant, > 90 % sensitive)? The system must apply stratified sampling during 5‑fold cross‑validation to ensure each fold contains a representative proportion of resistant cases.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download and preprocess a subset of at least 1,500 *E. coli* and *S. aureus* genomes with phenotypic AST data from the NCBI Pathogen Genome Browser and CARD, ensuring the dataset fits within 7 GB RAM and contains ≥100 resistant and ≥100 sensitive isolates for each antibiotic examined. (See US-1)
- **FR-002**: System MUST extract binary presence/absence of known resistance genes using CARD's API as the primary feature set for the baseline model. (See US-1)
- **FR-003**: System MUST call SNPs against a core genome reference using `snippy` followed by `snp-sites`, and calculate the genomic distance from each ARG to the nearest transposon insertion site (identified via the ISfinder database using the `isfinder` utility) or plasmid origin (identified via MOB‑suite). All pipelines must be run on the real assemblies obtained in FR‑001; synthetic generation of SNP counts or MGE distances is prohibited. (See US-2)
- **FR-004**: System MUST train XGBoost and Random Forest classifiers (baseline using ARG‑only features, integrated using full feature set) using a **nested evaluation protocol**: an outer cross‑validation (e.g., k‑fold) with a held‑out test split for final reporting, and a 5‑fold inner cross‑validation on the remaining training data for hyper‑parameter tuning. (See US-1, US-2)
- **FR-005**: System MUST assess the predictive contribution of SNP and MGE features using a **permutation‑based feature importance** procedure (10 000 permutations) combined with a mixed‑effects model that incorporates a kinship matrix (via `pyseer`) to correct for clonal population structure. Significant features are reported with Benjamini‑Hochberg FDR‑adjusted p‑values < 0.05. (See US-3)
- **FR-006**: System MUST generate a comparative report that explicitly quantifies the delta (which may be ≤ 0) in AUC‑ROC, Precision, Recall, and F1‑score of each integrated model over its corresponding baseline. (See US-3)
- **FR-007**: System MUST implement a sensitivity analysis that sweeps the classification probability threshold over a set of representative low, medium, and high values (e.g., 0.5 and 0.7) and reports the variation in false‑positive and false‑negative rates, justified as a robustness check for the predictive‑value claim. (See US-3)
- **FR-008**: System MUST handle download or API failures by logging a warning, proceeding with whatever isolates were successfully retrieved, and documenting the reduced sample size in the final report. (See US-1)
- **FR-009**: System MUST filter out isolates whose core‑genome alignment coverage is < 90 % of the reference before any downstream analysis. (See US-2)
- **FR-010**: System MUST apply stratified sampling during the 5‑fold inner cross‑validation to preserve the resistant‑vs‑sensitive class proportions in each fold. (See US-2)
- **FR-011**: System MUST conduct a phylogeny‑aware permutation test (e.g., using `pyseer` with a kinship matrix) to assess the significance of SNP and MGE features while accounting for clonal population structure. (See US-3)
- **FR-012**: System MUST evaluate whether the integrated model’s performance improvement over the baseline is statistically significant by applying a **two‑sided Wilcoxon signed‑rank test** to the paired predicted probabilities on the outer held‑out test set. (See US-3)
- **FR-013**: System MUST train separate models for each species (*E. coli*, *S. aureus*) and for each antibiotic phenotype that meets the 50/50 isolate threshold, preventing cross‑species or cross‑antibiotic pooling. (See US-1, US-2)
- **FR-014**: System MUST perform a **pre‑model power analysis** for each species‑antibiotic task, estimating the required isolate count to detect an effect size of *d* = 0.1 with statistical power ≥ 0.8 at α = 0.05 (≈ on the order of a thousand isolates). Modeling proceeds **only if** the observed isolate count meets or exceeds this requirement; otherwise the task is aborted and reported as under‑powered. (See US-3)
- **FR-015**: System MUST also train Random Forest classifiers (baseline and integrated) alongside XGBoost, using the same nested evaluation protocol, to enable algorithmic comparison. (See US-1, US-2)
- **FR-016**: System MUST ensure that **all feature‑selection, dimensionality‑reduction, and hyper‑parameter tuning steps are performed within each inner CV training fold**, thereby preventing data leakage. (See US-2)
- **FR-017**: System MUST assess potential confounding variables (geographic origin, collection date, sequencing platform) by encoding geography as a categorical region label, collection date as integer year, and platform as a categorical identifier; these encoded variables are included as fixed effects in the mixed‑effects model (FR‑005) and also supplied as covariates to the permutation‑importance routine. Results of the confounder assessment must be reported. (See US-3)
- **FR-018**: System MUST report computational feasibility against the GitHub Actions free‑tier constraints (≤ 6 h runtime, ≤ 7 GB RAM, CPU‑only) by verifying the job completes without OOM or timeout errors. (See US-1)
- **FR-019**: System MUST report the sensitivity of the decision threshold by providing false‑positive and false‑negative rates for each threshold in {0.3, 0.5, 0.7}. (See US-3)
- **FR-020**: System MUST report a power analysis for each antibiotic‑specific task, comparing the observed isolate count to the required sample size (≈ 1 400 isolates for *d* = 0.1, power) and note any insufficiencies in the final report. (See US-3)

### Key Entities

- **Genomic Isolate**: Represents a bacterial sample, containing attributes: `isolate_id`, `species`, `assembly_quality`, `phenotype_label` (resistant/sensitive), `antibiotic_target`.
- **Resistance Feature Vector**: Represents the encoded data for an isolate, containing attributes: `arg_presence_vector` (binary), `snp_counts` (integer), `mge_distances` (float/binned), `normalized_features`.
- **Model Artifact**: Represents the trained classifier, containing attributes: `model_type` (XGBoost or Random Forest), `cross_validation_metrics` (AUC, Precision, Recall, F1), `feature_importance_ranking`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The increase (which may be ≤ 0) in AUC‑ROC, Precision, Recall, and F1‑score of each integrated model (SNPs + MGE) compared to its baseline (ARGs only) is measured against the baseline metrics to quantify added predictive value. (See US-3)
- **SC-002**: The statistical significance of specific SNPs and MGE distances is measured against the null hypothesis using permutation‑importance p‑values (adjusted for multiple comparisons) **and** phylogeny‑aware permutation test p‑values. (See US-3)
- **SC-003**: The computational feasibility is measured against the GitHub Actions free‑tier constraints (≤ 6 h runtime, ≤ 7 GB RAM, CPU‑only) by verifying the job completes without OOM or timeout errors. (See US-1)
- **SC-004**: The sensitivity of the decision threshold is measured by reporting the range of false‑positive rates across the swept thresholds {0.3, 0.5, 0.7}. (See US-3)
- **SC-005**: The sample size adequacy is measured against the pre‑model power requirement for the observed effect size, with a note on whether the collected isolate count provides sufficient power for the detected associations. (See US-3)

## Assumptions

- **Dataset Variable Fit**: It is assumed that the NCBI Pathogen Genome Browser and CARD database contain the necessary phenotypic AST data and that the genomic assemblies are of sufficient quality to call SNPs and identify MGEs. If the dataset lacks specific antibiotic classes, the study will be restricted to antibiotics with well‑populated AST fields in NCBI Pathogen Detection for the two target species — for *E. coli*: ampicillin, ciprofloxacin, and ceftriaxone; for *S. aureus*: oxacillin (methicillin), ciprofloxacin, and clindamycin. Any antibiotic with fewer than 50 resistant **and** 50 sensitive isolates after ingestion is excluded from modeling, and the exclusion is logged in the final report.
- **Inference Framing**: Since this is an observational study using public databases without random assignment, all findings regarding SNPs and MGEs will be framed as **associational** predictors, not causal mechanisms, unless a specific identification strategy is introduced in future work.
- **Compute Feasibility**: It is assumed that the required isolate dataset and the selected models (XGBoost, Random Forest) will fit within the 7 GB RAM and 6‑hour runtime limits of the GitHub Actions free‑tier runner without requiring GPU acceleration or 8‑bit quantization.
- **Threshold Justification**: The classification probability threshold of 0.5 is used as the default decision boundary, justified by community standards for binary classification, with a mandatory sensitivity analysis (FR‑007) to verify robustness.
- **Measurement Validity**: It is assumed that the phenotypic AST data in the source databases is reliable and that the CARD database provides a comprehensive and validated catalog of resistance genes for the target species.
- **Predictor Collinearity**: It is assumed that while SNPs and MGE distances may be correlated with ARG presence, the model will treat them as distinct features, and the statistical validation will account for collinearity by focusing on joint predictive performance rather than claiming independent causal effects for correlated predictors.
- **Robustness Justification**: The probability‑threshold sweep in FR‑007 is included to demonstrate that the claimed predictive value of SNPs/MGEs is not an artifact of a particular decision boundary, satisfying the robustness requirement of the research question.
- **Nested CV & Feature Selection**: All feature‑selection, dimensionality‑reduction, and hyper‑parameter tuning operations are performed inside each inner CV training fold to avoid data leakage (FR‑016).
- **Confounder Assessment**: Potential confounders such as geographic origin, collection date, and sequencing platform are examined and either included as covariates or used for stratified analysis (FR‑017).
- **Pre‑Model Power Check**: A priori power analysis (FR‑014) determines whether sufficient isolates are available before model training; tasks lacking power are flagged and not pursued further.
