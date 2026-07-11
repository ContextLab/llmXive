# Feature Specification: Predicting Plant Stress Response from Publicly Available Transcriptomic Data

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "Predicting Plant Stress Response from Publicly Available Transcriptomic Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cross-Dataset Stress Signature Separability (Priority: P1)

The researcher needs to determine if distinct abiotic stress types (drought, salinity, heat, cold) induce separable transcriptional signatures that generalize across independent public datasets, rather than being dataset-specific artifacts. This is the core hypothesis of the project.

**Why this priority**: This addresses the primary research question and the identified literature gap. Without establishing whether signatures are separable and generalizable, the subsequent steps of biomarker identification or unified modeling have no foundation.

**Independent Test**: Can be fully tested by training a Random Forest classifier on a subset of datasets and evaluating its accuracy on a held-out, independent dataset. A measurable accuracy score (e.g., ≤ 0.25 vs ≥ 0.60) directly validates or refutes the separability hypothesis.

**Acceptance Scenarios**:

1. **Given** normalized RNA-seq count matrices from ≥5 distinct GEO datasets covering ≥2 stress types (drought, salinity, heat, cold), **When** a Random Forest classifier is trained on 4 datasets and tested on the 5th (Leave-One-Dataset-Out), **Then** the model achieves a classification accuracy that is **≤ 1/N** (where N is the number of classes in the held-out dataset, e.g., 0.25 for 4 classes) if signatures are dataset-specific or absent, OR **significantly greater than the baseline (p < 0.05 via permutation test) AND ≥ 0.60** if they generalize.
2. **Given** the same dataset split, **When** a confusion matrix is generated comparing predicted stress types against true metadata labels, **Then** the off-diagonal elements (misclassifications) reveal specific stress pairs that are transcriptionally indistinguishable across datasets (e.g., heat vs. cold).
3. **Given** the same dataset split, **When** the model accuracy is **> 1/N (dynamic baseline) AND < 0.60**, **Then** the system MUST flag the result as "Ambiguous - Further Investigation Required" and halt further biomarker analysis for that specific cross-dataset pair.
4. **Given** a null result (accuracy ≤ 1/N), **When** a post-hoc power analysis (Minimum Detectable Effect Size) is performed using the actual sample size of the held-out set, **Then** the system MUST report the calculated MDES value to distinguish between "No Biological Signal" and "Insufficient Sample Size to Detect Weak Signal".

---

### User Story 2 - Feature Importance and Biomarker Identification (Priority: P2)

The researcher needs to identify which specific genes (biomarkers) drive the classification performance in both within-dataset and cross-dataset scenarios to distinguish universal stress responders from context-specific ones.

**Why this priority**: Once separability is established (or refuted), understanding *which* genes are responsible provides the biological insight needed for breeding programs. This is a secondary but critical analytical step.

**Independent Test**: Can be tested by extracting feature importance scores from the trained Random Forest model and verifying that a subset of top-ranked genes shows consistent differential expression across the independent datasets used in the cross-validation. Specifically, the system calculates the Jaccard index of the top 50 genes between within-dataset and cross-dataset rankings, validated via bootstrapping.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model with accuracy significantly greater than baseline, **When** feature importance is calculated for the top 50 variable genes, **Then** the top 50 genes must show a statistically significant overlap (Jaccard index > 0.30 AND p < 0.05 via permutation test of gene sets) between the within-dataset and cross-dataset importance rankings.
2. **Given** the top-ranked genes, **When** their expression profiles are plotted across all datasets, **Then** the visualization must show consistent up/down-regulation patterns relative to control samples for at least one stress type across all datasets.
3. **Given** the top 1,500 genes, **When** a bootstrap resampling (100 iterations) of the training data is performed to calculate feature importance variance, **Then** only genes with a stability score (variance across iterations) < 0.30 are reported as robust biomarkers, distinguishing them from noise-driven importance in correlated gene modules.

---

### User Story 3 - Unsupervised Validation of Stress Clustering (Priority: P3)

The researcher needs to verify that stress types form distinct clusters in the feature space without relying on the supervised classifier's labels, ensuring the signal is inherent to the data structure.

**Why this priority**: This provides an orthogonal validation method. If the supervised model works but unsupervised clustering fails, the signal might be overfit or dependent on specific preprocessing artifacts.

**Independent Test**: Can be tested by running UMAP or t-SNE on the held-out test samples (processed strictly on TMM-normalized data without batch correction, or with batch correction parameters learned *only* from the training fold) and quantitatively assessing if samples of the same stress type cluster together, independent of the dataset source. The sole verifiable criterion is the Silhouette Score.

**Acceptance Scenarios**:

1. **Given** the reduced-dimensionality embedding (UMAP) of the held-out test set (processed on TMM-normalized data without batch correction), **When** samples are colored by stress type, **Then** distinct clusters must form for at least 3 out of N stress types (where N is the number of classes in the held-out set, or all N if N < 3) with an individual Silhouette Score > 0.4 for at least 3 clusters (or all if N < 3).
2. **Given** the same embedding, **When** samples are colored by dataset source, **Then** samples from different datasets but the same stress type must overlap significantly, confirming cross-dataset generalization of the transcriptional signature.
3. **Given** the same embedding, **When** a 'dataset-label' Silhouette Score is calculated, **Then** the score must be significantly lower than the 'stress-type' Silhouette Score to ensure clustering is not driven by batch effects.

---

### User Story 4 - Project State Management (Priority: P3)

The system MUST update the project state file upon completion of the analysis to reflect the final state, ensuring compliance with Constitution Principle V.

**Why this priority**: This is a mandatory constitutional requirement for versioning and reproducibility, ensuring the project state is persisted correctly.

**Independent Test**: Can be tested by verifying that the file `state/projects/<PROJ-ID>/projects.yaml` exists and contains the correct final state after the pipeline completes.

**Acceptance Scenarios**:

1. **Given** a completed analysis, **When** the system finishes, **Then** the file `state/projects/<PROJ-ID>/projects.yaml` MUST be updated with the final state and a timestamp.

---

### Edge Cases

- **Confounded Batch and Condition**: What happens if a dataset contains only one stress type (e.g., only drought)? The system MUST perform a Fisher's Exact Test (or Chi-squared with Yates' correction for >2x2 tables) (p < 0.05) on the contingency table of (Dataset ID × Stress Type) prior to analysis. If significant confounding is detected, the system MUST **exclude that dataset** from the cross-dataset analysis and log a warning, then continue with the remaining datasets.
- **Insufficient Feature Intersection**: What happens if the intersection of genes present in **ALL** of the selected datasets yields <1,500 features? The system MUST halt execution with a "Feature Space Insufficient" error and report the exact gene count, as per Constitution Principle VII.
- **Class Imbalance**: What happens when a specific stress type has significantly fewer samples in one dataset? The system MUST handle class imbalance via stratified sampling (for CV) and class weighting in the Random Forest to prevent bias.
- **Ambiguous Accuracy**: What happens if the Random Forest model converges to random chance (accuracy ≤ 1/N)? The system MUST flag this as "No Separable Signature" and halt further biomarker analysis for that specific cross-dataset pair, triggering the post-hoc power analysis.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST query NCBI GEO metadata to discover and verify at least 5 distinct plant transcriptomic datasets (Organism MUST be *Arabidopsis thaliana*, *Oryza sativa*, *Solanum lycopersicum*, or *Zea mays*) that contain samples for at least 2 stress types (drought, salinity, heat, cold) before inclusion in the analysis. The system MUST explicitly exclude any dataset identified as human, animal, or non-stress related. (See US-1)
- **FR-002**: The system MUST filter raw counts to retain only genes with ≥1 CPM (Counts Per Million) in at least 3 samples, AND THEN normalize the remaining raw counts via **TMM (Trimmed Mean of M-values)** transformation to ensure data quality and correct library size bias. (See US-1)
- **FR-003**: The system MUST harmonize gene identifiers across all datasets using `mygene` or `biomart` (not `biopython` alone) and retain **only genes present in the intersection of ALL selected datasets** to ensure a consistent feature space in strict adherence to Constitution Principle VII. (See US-1)
- **FR-004**: The system MUST perform feature selection to retain the top **K** most variable genes across all samples (where K is determined by sensitivity analysis over {1000, 1500, 2000} as defined in Assumptions) to ensure the data fits within the 7GB RAM limit of the free-tier CI runner; if the intersection from FR-003 yields <1,500 genes, the system MUST halt execution and report the exact count. (See US-2)
- **FR-005**: The system MUST train a Random Forest classifier using `scikit-learn` with hyperparameters tuned via 5-fold cross-validation on the training fold only, strictly avoiding any GPU/CUDA dependencies. (See US-1)
- **FR-006**: The system MUST evaluate model performance on both within-dataset (train/test split) and cross-dataset (train on 4, test on 1) partitions using stratified metrics (accuracy, F1-score, macro-averaged precision/recall). (See US-1)
- **FR-007**: The system MUST generate confusion matrices comparing within-dataset vs. cross-dataset performance to quantify the generalization gap. (See US-1)
- **FR-008**: The system MUST perform unsupervised clustering (UMAP or t-SNE) on held-out test samples using **TMM-normalized data without batch correction** (or batch correction parameters fitted strictly on the training fold) to verify stress-class separation independently of the classifier's predictions. (See US-3)
- **FR-009**: The system MUST output feature importance rankings for the top genes to identify stress-responsive genes that drive classification. (See US-2)
- **FR-010**: The system MUST include a multiple-comparison correction step (e.g., Benjamini-Hochberg FDR) for any hypothesis tests performed on feature importance to control family-wise error rate. (See US-2)
- **FR-011**: The system MUST perform a **label-permutation test (1,000 iterations)** where stress labels are shuffled **strictly within each dataset** in the held-out test set relative to the training set's learned decision boundary to establish a null distribution for cross-dataset accuracy, requiring a p-value < 0.05 to claim statistical significance over chance. (See US-1)
- **FR-012**: The system MUST validate stress labels against metadata fields for duration or severity (if available) and flag samples with inconsistent or missing severity data by writing a CSV row with status 'INVALID_LABEL' and logging an error message to stderr for exclusion. (See US-1)
- **FR-013**: The system MUST perform a bootstrapping stability analysis (100 iterations) on the feature importance rankings to ensure biomarker stability, requiring a stability score (variance < 0.30) for a gene to be classified as robust. (See US-2)
- **FR-014**: The system MUST perform a post-hoc power analysis (Minimum Detectable Effect Size calculation) to interpret null results and distinguish between 'no signal' and 'insufficient sample size'. (See US-1)
- **FR-015**: The system MUST perform a Fisher's Exact Test (or Chi-squared with Yates' correction for >2x2 tables) for 'confounded batch and condition' before applying any batch correction. The test uses a contingency table with Rows=Batch (Dataset ID) and Columns=Stress Type. The system MUST **exclude any dataset** where the p-value < 0.05 indicates significant confounding and log a warning. If the table is sparse (zero-count cells), the system MUST use Fisher's Exact Test with continuity correction. (See US-1)
- **FR-016**: The system MUST explicitly verify that every cited GEO accession in the input data contains plant samples and the required stress types before processing; any dataset failing this verification (e.g., human datasets) MUST be excluded with a logged error. (See US-1)
- **FR-017**: The system MUST update the project state file `state/projects/<PROJ-ID>/projects.yaml` upon completion of the analysis to reflect the final state, ensuring compliance with Constitution Principle V. (See US-4)
- **FR-018**: The system MUST frame all findings regarding stress signatures as **ASSOCIATIONAL** (not causal) in all generated reports, as the study design is observational without random assignment (Constitution Principle I). (See Constitution Principle I)
- **FR-019**: The system MUST report the number of known stress pathways (e.g., ABA signaling, ROS scavenging) represented in the gene intersection, and MUST halt execution if the coverage of conserved stress genes is < 50%, as this indicates a biologically impoverished feature space. (See US-1)

### Key Entities

- **StressDataset**: Represents a single GEO accession, containing raw counts, metadata (stress type, species, control), and processed normalized values.
- **FeatureSpace**: The intersection of gene identifiers present in **ALL** selected datasets, filtered to the top K most variable genes. (See FR-003, FR-004)
- **ClassificationModel**: The trained Random Forest instance, storing hyperparameters, feature importances, and performance metrics.
- **Embedding**: The reduced-dimensional representation (2D/3D) of samples for visualization and unsupervised validation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Within-dataset classification accuracy is measured against the theoretical random baseline of 1/N (1/number of classes) to determine if the signal is statistically distinguishable from chance (p < 0.05 via permutation test). (See US-1)
- **SC-002**: Cross-dataset classification accuracy is measured against the within-dataset baseline to quantify the generalization gap. (See US-1)
- **SC-003**: Feature importance overlap (Jaccard index) is measured against a null distribution generated by permuting gene labels [deferred] times to calculate a p-value < 0.05. (See US-2)
- **SC-004**: Clustering silhouette score is measured against the stress-type labels to verify unsupervised separation validity. (See US-3)
- **SC-005**: Computation time is measured against the standard time limit of the GitHub Actions free-tier runner (6 hours) to ensure feasibility. (See US-1)
- **SC-006**: The Minimum Detectable Effect Size (MDES) is measured against the observed effect size in null results to determine if the sample size was sufficient to detect a biologically relevant signal. (See US-1)
- **SC-007**: The stability score (variance) of feature importance is measured against the threshold of 0.30 to distinguish robust biomarkers from noise. (See US-2)

## Assumptions

- **Assumption about data availability**: It is assumed that the system can successfully discover and verify at least 5 distinct plant transcriptomic datasets from NCBI GEO containing at least 2 stress types via metadata parsing; if fewer than 5 valid datasets are found, the pipeline halts with an error.
- **Assumption about gene identifier consistency**: It is assumed that `mygene` or `biomart` can successfully map gene identifiers across the different species or platforms present in the selected datasets, and that the intersection of genes present in **ALL** of datasets will yield ≥1,500 features for analysis. **If this assumption fails (<1,500 genes), the pipeline halts with an error as per FR-004.**
- **Assumption about computational constraints**: It is assumed that a top subset of the most variable genes, when stored as a floating-point matrix for the available samples, will fit within the 7GB RAM limit of the free-tier CI runner.
- **Assumption about inference framing**: It is assumed that the study design is observational (no random assignment of stress conditions by the researchers), and therefore all findings regarding stress signatures will be framed as ASSOCIATIONAL, not causal.
- **Assumption about threshold justification**: The decision to retain the top K most variable genes is justified by the memory constraints of the free-tier CI runner; a sensitivity analysis will sweep the top-k value over a range of magnitudes (e.g., 1000, 1500, 2000) to report how accuracy and generalization gap vary.
- **Assumption about power**: The sample size is determined by the available public datasets; a post-hoc power analysis (Minimum Detectable Effect Size) is required to interpret null results, as specified in FR-014.
- **Assumption about measurement validity**: It is assumed that the stress labels provided in the GEO metadata are accurate and consistent across datasets, serving as the ground truth for classification. **Note: FR-012 addresses potential inconsistencies.**
- **Assumption about collinearity**: It is assumed that the top most variable genes may contain correlated predictors; the Random Forest model's inherent ability to handle multicollinearity is supplemented by the bootstrapped stability analysis (FR-013) to distinguish robust biomarkers from noise among correlated genes.
- **Assumption about batch correction**: It is assumed that batch correction (if used for sensitivity analysis) will be fitted **strictly on the training fold** and applied to the test fold to prevent data leakage, and that the primary validation will be performed on **TMM-normalized data without batch correction** to test biological signal vs. technical noise.
- **Assumption about dataset quality**: It is assumed that the selected GEO datasets will not have confounded batch and condition (e.g., one dataset containing only drought samples); FR-015 enforces a check for this, excluding such datasets if detected.