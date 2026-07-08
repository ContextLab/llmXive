# Feature Specification: Predicting Plant Stress Response from Publicly Available Transcriptomic Data

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-06-28  
**Status**: Draft  
**Input**: User description: "Predicting Plant Stress Response from Publicly Available Transcriptomic Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cross-Dataset Stress Signature Separability (Priority: P1)

The researcher needs to determine if distinct abiotic stress types (drought, salinity, heat, cold) induce separable transcriptional signatures that generalize across independent public datasets, rather than being dataset-specific artifacts. This is the core hypothesis of the project.

**Why this priority**: This addresses the primary research question and the identified literature gap. Without establishing whether signatures are separable and generalizable, the subsequent steps of biomarker identification or unified modeling have no foundation.

**Independent Test**: Can be fully tested by training a Random Forest classifier on a subset of datasets and evaluating its accuracy on a held-out, independent dataset. A measurable accuracy score (e.g., <25% vs >65%) directly validates or refutes the separability hypothesis.

**Acceptance Scenarios**:

1. **Given** normalized RNA-seq count matrices from 5 distinct GEO datasets covering 4 stress types, **When** a Random Forest classifier is trained on 4 datasets and tested on the 5th, **Then** the model achieves a classification accuracy strictly below [deferred] (random chance baseline) if signatures are dataset-specific, or above [deferred] if they generalize.
2. **Given** the same dataset split, **When** a confusion matrix is generated comparing predicted stress types against true metadata labels, **Then** the off-diagonal elements (misclassifications) reveal specific stress pairs that are transcriptionally indistinguishable across datasets (e.g., heat vs. cold).
3. **Given** the same dataset split, **When** the model accuracy falls between [deferred] and [deferred] (inclusive), **Then** the system MUST flag the result as "Ambiguous - Further Investigation Required" and halt further biomarker analysis for that specific cross-dataset pair.

---

### User Story 2 - Feature Importance and Biomarker Identification (Priority: P2)

The researcher needs to identify which specific genes (biomarkers) drive the classification performance in both within-dataset and cross-dataset scenarios to distinguish universal stress responders from context-specific ones.

**Why this priority**: Once separability is established (or refuted), understanding *which* genes are responsible provides the biological insight needed for breeding programs. This is a secondary but critical analytical step.

**Independent Test**: Can be tested by extracting feature importance scores from the trained Random Forest model and verifying that a subset of top-ranked genes shows consistent differential expression across the independent datasets used in the cross-validation.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model with >65% accuracy, **When** feature importance is calculated for the top 1500 variable genes, **Then** the top 50 genes must show a statistically significant overlap (e.g., >30% overlap) between the within-dataset and cross-dataset importance rankings.
2. **Given** the top-ranked genes, **When** their expression profiles are plotted across all datasets, **Then** the visualization must show consistent up/down-regulation patterns relative to control samples for at least one stress type across all datasets.

---

### User Story 3 - Unsupervised Validation of Stress Clustering (Priority: P3)

The researcher needs to verify that stress types form distinct clusters in the feature space without relying on the supervised classifier's labels, ensuring the signal is inherent to the data structure.

**Why this priority**: This provides an orthogonal validation method. If the supervised model works but unsupervised clustering fails, the signal might be overfit or dependent on specific preprocessing artifacts.

**Independent Test**: Can be tested by running UMAP or t-SNE on the held-out test samples (after batch correction) and visually/quantitatively assessing if samples of the same stress type cluster together, independent of the dataset source.

**Acceptance Scenarios**:

1. **Given** the reduced-dimensionality embedding (UMAP) of the held-out test set (after batch correction), **When** samples are colored by stress type, **Then** distinct clusters must form for at least 3 out of 4 stress types with a Silhouette Score > 0.4.
2. **Given** the same embedding, **When** samples are colored by dataset source, **Then** samples from different datasets but the same stress type must overlap significantly, confirming cross-dataset generalization of the transcriptional signature.

---

### Edge Cases

- What happens when a specific stress type (e.g., "cold") has significantly fewer samples in one dataset compared to others? The system must handle class imbalance via stratified sampling or weighting to prevent bias.
- How does the system handle datasets where gene identifiers do not fully overlap? The system must filter to the union of genes present in ≥80% of datasets and report the percentage of genes lost, ensuring the feature space is consistent.
- What happens if the Random Forest model converges to random chance (accuracy <25%)? The system must flag this as "No Separable Signature" and halt further biomarker analysis for that specific cross-dataset pair.
- What happens if the feature space after filtering yields <1500 genes? The system MUST halt execution with a "Feature Space Insufficient" error and report the exact gene count.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST download and parse raw count matrices and metadata for several public RNA-seq datasets from NCBI GEO (including GSE, GSE40677, GSE51148, GSE59991, GSE66904) using `wget` or `curl` (See US-1).
- **FR-002**: The system MUST filter raw counts to retain only genes with ≥1 CPM (Counts Per Million) in at least 3 samples, AND THEN normalize the remaining raw counts via TPM transformation to ensure data quality and correct library size bias (See US-1).
- **FR-003**: The system MUST harmonize gene identifiers across all datasets using `biopython` and retain only genes present in the union of ≥80% of the selected datasets to ensure a consistent feature space while preserving stress-specific signals (See US-1).
- **FR-004**: The system MUST perform feature selection to retain the top most variable genes across all samples. (as defined in the FeatureSpace entity) to ensure the data fits within the 7GB RAM limit of the free-tier CI runner (See US-2).
- **FR-005**: The system MUST train a Random Forest classifier using `scikit-learn` with hyperparameters tuned via 5-fold cross-validation on the training fold only, strictly avoiding any GPU/CUDA dependencies (See US-1).
- **FR-006**: The system MUST evaluate model performance on both within-dataset (train/test split) and cross-dataset (train on 4, test on 1) partitions using stratified metrics (accuracy, F1-score, macro-averaged precision/recall) (See US-1).
- **FR-007**: The system MUST generate confusion matrices comparing within-dataset vs. cross-dataset performance to quantify the generalization gap (See US-1).
- **FR-008**: The system MUST perform unsupervised clustering (UMAP or t-SNE) on held-out test samples to verify stress-class separation independently of the classifier's predictions (See US-3).
- **FR-009**: The system MUST output feature importance rankings for the top genes to identify stress-responsive genes that drive classification (See US-2).
- **FR-010**: The system MUST include a multiple-comparison correction step (e.g., Bonferroni or FDR) for any hypothesis tests performed on feature importance to control family-wise error rate (See US-2).
- **FR-011**: The system MUST apply a batch-effect correction algorithm (e.g., ComBat or Harmony) to the normalized data before performing unsupervised clustering (FR-008) to ensure clusters reflect biology, not dataset source (See US-3).
- **FR-012**: The system MUST validate stress labels against metadata fields for duration or severity (if available) and flag samples with inconsistent or missing severity data for exclusion or separate analysis (See US-1).

### Key Entities

- **StressDataset**: Represents a single GEO accession, containing raw counts, metadata (stress type, species, control), and processed normalized values.
- **FeatureSpace**: The union of gene identifiers present in ≥80% of datasets, filtered to the top 1500 most variable genes (See FR-003, FR-004).
- **ClassificationModel**: The trained Random Forest instance, storing hyperparameters, feature importances, and performance metrics.
- **Embedding**: The reduced-dimensional representation (2D/3D) of samples for visualization and unsupervised validation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Within-dataset classification accuracy is measured against the baseline random chance (equal probability for the number of classes) to confirm signal presence (See US-1).
- **SC-002**: Cross-dataset classification accuracy is measured against the within-dataset baseline to quantify the generalization gap (See US-1).
- **SC-003**: Feature importance overlap between within-dataset and cross-dataset models is measured against a random permutation baseline to identify robust biomarkers (See US-2).
- **SC-004**: Clustering silhouette score is measured against the stress-type labels to verify unsupervised separation validity (See US-3).
- **SC-005**: Computation time is measured against the standard time limit of the GitHub Actions free-tier runner to ensure feasibility (See US-1).

## Assumptions

- **Assumption about data availability**: It is assumed that the target GEO datasets (GSE30047, GSE40677, GSE51148, GSE59991, GSE66904) contain raw count matrices and sufficient metadata to unambiguously label samples with stress types (drought, salinity, heat, cold).
- **Assumption about gene identifier consistency**: It is assumed that `biopython` can successfully map gene identifiers across the different species or platforms present in the selected datasets, and that the union of genes present in ≥80% of datasets will yield ≥1,500 features for analysis. **If this assumption fails (<1,500 genes), the pipeline halts.**
- **Assumption about computational constraints**: It is assumed that a top subset of the most variable genes, when stored as a floating-point matrix for the available samples, will fit within the 7GB RAM limit of the free-tier CI runner..
- **Assumption about inference framing**: It is assumed that the study design is observational (no random assignment of stress conditions by the researchers), and therefore all findings regarding stress signatures will be framed as ASSOCIATIONAL, not causal.
- **Assumption about threshold justification**: The decision to retain a subset of the most variable genes is justified by the memory constraints of the free-tier CI runner.; a sensitivity analysis will sweep the top-k value over a range of magnitudes to report how accuracy and generalization gap vary.
- **Assumption about power**: The sample size is determined by the available public datasets; a formal power analysis for sample size is deferred due to data availability constraints. However, a sensitivity analysis on feature selection (top-k genes) serves as the proxy for assessing the stability of the model against feature space variations.
- **Assumption about measurement validity**: It is assumed that the stress labels provided in the GEO metadata are accurate and consistent across datasets, serving as the ground truth for classification. **Note: FR-012 addresses potential inconsistencies.**
- **Assumption about collinearity**: It is assumed that the top most variable genes may contain correlated predictors; the Random Forest model's inherent ability to handle multicollinearity will be relied upon, and no explicit collinearity diagnostic (e.g., VIF) will be performed unless feature importance is ambiguous.