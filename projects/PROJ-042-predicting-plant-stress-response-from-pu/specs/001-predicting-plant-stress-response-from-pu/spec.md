# Feature Specification: Predicting Plant Stress Response from Publicly Available Transcriptomic Data

**Feature Branch**: `001-predicting-plant-stress-response-from-pu`  
**Created**: 2026-10-18  
**Status**: Draft  
**Input**: User description: "Predicting Plant Stress Response from Publicly Available Transcriptomic Data"

## User Scenarios & Testing *(mandatory)*

### User Story US-1 – Cross‑Dataset Stress‑Signature Separability (Priority: P1)

The researcher needs to know whether transcriptional signatures of the four abiotic stresses (drought, salinity, heat, cold) are biologically separable across independent public GEO datasets when only the top 50 most variable genes are used.

**Why this priority**: It directly tests the primary hypothesis that a minimal linear feature set can capture stress‑specific biology, informing whether low‑cost qPCR panels are feasible.

**Independent Test**: Train a **Logistic Regression** (L2‑regularized) classifier on four GEO datasets using only the top 50 variable genes selected *within* the training fold, then evaluate accuracy on the held‑out fifth dataset (Leave‑One‑Dataset‑Out, LODO). No batch‑correction is applied.

**Acceptance Scenarios**:

1. **Given** normalized count matrices from ≥ 5 verified plant GEO datasets, each containing at least two stress types, **When** a Logistic Regression model is trained on 4 datasets and tested on the 5th, **Then** the cross‑dataset accuracy is **≥ 0.70** *and* statistically greater than the permutation‑based null distribution (p < 0.05).  
2. **Given** the same LODO split, **When** the observed accuracy is **≤ random‑chance baseline** (1 / N, where N = number of stress classes in the held‑out set), **Then** the system flags “No separable signature” and proceeds to the post‑hoc power analysis (FR‑009).  
3. **Given** an accuracy that lies between the random baseline and 0.70, **Then** the result is labeled “Ambiguous” and a warning is logged; the pipeline continues to the biomarker stability analysis but does not claim a robust biomarker set.

### User Story US-2 – Minimal‑Feature Biomarker Stability (Priority: P2)

The researcher wants to identify which genes among the top 50 are robust contributors to any observed separability.

**Why this priority**: Robust biomarkers are required for downstream low‑cost assay design; unstable importance scores would mislead panel development.

**Independent Test**: Perform **bootstrap resampling** (100 iterations) of the training data, recompute feature‑importance (absolute logistic‑regression coefficients) for each iteration, and calculate the variance of each gene’s coefficient.

**Acceptance Scenarios**:

1. **Given** a trained Logistic Regression model with cross‑dataset accuracy ≥ 0.70, **When** bootstrap stability analysis is completed, **Then** genes with coefficient variance ≤ 0.30 are reported as **robust biomarkers**.  
2. **Given** the set of robust biomarkers, **When** their selection frequency across bootstrap iterations is ≥ 0.70, **Then** they are listed in the final results table.  
3. **Given** no gene meets the variance ≤ 0.30 criterion, **Then** the system reports “No stable minimal‑feature biomarkers detected” and recommends expanding the feature set.

### User Story US-3 – Unsupervised Validation of Stress Clustering (Priority: P3)

The researcher seeks an orthogonal, label‑free confirmation that stress types form distinct clusters in the minimal‑feature space.

**Why this priority**: Demonstrates that separability is intrinsic to the data rather than an artifact of the supervised model.

**Independent Test**: Compute a **UMAP** embedding (2‑D) of the held‑out test samples using the same top 50 genes (no batch correction). Calculate **Silhouette Scores** for (a) stress‑type labels and (b) dataset‑ID labels.

**Acceptance Scenarios**:

1. **Given** the UMAP embedding of the held‑out dataset, **When** the stress‑type Silhouette Score ≥ 0.40 for at least three stress classes, **Then** the result supports intrinsic clustering.  
2. **Given** the same embedding, **When** the dataset‑ID Silhouette Score is **significantly lower** than the stress‑type score (Δ ≥ 0.10, tested via permutation), **Then** batch effects are not driving the clustering.

### User Story US-4 – Project State Management (Priority: P4)

The system MUST persist the final analysis state for reproducibility and versioning.

**Why this priority**: Guarantees that downstream reviewers can reconstruct the exact pipeline execution.

**Independent Test**: After the pipeline finishes, check that the file `state/projects/PROJ-042-predicting-plant-stress-response-from-pu.yaml` exists, contains a `research_complete: true` flag, a timestamp, and a checksum of the results artifact.

**Acceptance Scenarios**:

1. **Given** a completed run, **When** the state file is inspected, **Then** it reflects the final status, timestamps, and result hashes exactly as specified in FR‑017.

### User Story US-5 – Reporting & Reproducibility (Priority: P5)

The final report must frame all findings as associational and include all statistical summaries required for peer review.

**Why this priority**: Aligns with Constitution Principle I and ensures transparent communication of observational results.

**Independent Test**: Verify that the generated PDF/HTML report contains sections for (a) associational framing, (b) cross‑dataset accuracy with confidence intervals, (c) power analysis results, (d) biomarker stability tables, and (e) reproducibility metadata (state file hash, software versions).

**Acceptance Scenarios**:

1. **Given** a completed analysis, **When** the report is generated, **Then** it includes all sections listed above and each statistical claim is accompanied by a p‑value or confidence interval.

## Edge Cases

- **Dataset with a single stress type**: If a GEO accession contains only one stress condition, the system runs **Fisher’s Exact Test** on the (Dataset × Stress) contingency table. A significant association (p < 0.05) triggers exclusion of that dataset and logs a warning.  
- **Insufficient gene intersection**: If the intersection of gene identifiers across all selected datasets yields **< 1,500 genes**, the pipeline aborts with error code E‑GENE‑INTERSECTION and reports the exact count.  
- **Severe class imbalance**: When any stress class contributes < 5 % of samples in a dataset, the training step applies **class‑weighting** (inverse frequency) in the Logistic Regression loss.  
- **Missing or inconsistent stress metadata**: Samples with absent or contradictory stress labels are written to `invalid_samples.csv` with status `INVALID_LABEL` and excluded from all analyses.  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST query NCBI GEO (via Entrez/E-utilities) to discover **≥ 5 distinct plant transcriptomic datasets** (organism = *Arabidopsis thaliana*, *Oryza sativa*, *Solanum lycopersicum*, or *Zea mays*) that each contain **≥ 2 abiotic stress types** (drought, salinity, heat, cold). Datasets failing this check are excluded. (See US‑1)  
- **FR-002**: The system MUST verify that **all four stress types** appear in the combined pool of selected datasets, with each stress represented in **≥ 2 different datasets**. If not, the pipeline aborts with a clear message. (See US‑1)  
- **FR-003**: Raw count matrices are filtered to retain genes with **≥ 1 CPM** in at least **3 samples** per dataset, then normalized using **TMM** (edgeR) to correct library size bias. (See US‑1)  
- **FR-004**: Gene identifiers are harmonized across datasets using **mygene** or **biomart**; only genes present in the **intersection of ALL selected datasets** are kept. The pipeline aborts if the intersection yields **< 1,500 genes**. (See US‑1)  
- **FR-005**: Feature selection selects the **top K most variable genes** (variance across all samples) where **K ∈ {50, 100, 150}**. A **sensitivity analysis** sweeps K over this set and records accuracy and generalization gap for each value. (See US‑2)  
- **FR-006**: For each LODO iteration, a **Logistic Regression** classifier (L2 regularization, liblinear solver) is trained **only on the training datasets**. No batch‑correction is applied to either training or test data in the primary evaluation. (See US‑1)  
- **FR-007**: Model performance is evaluated on the held‑out dataset using **stratified accuracy, macro‑averaged F1, precision, and recall**. (See US‑1)  
- **FR-008**: The system performs **two permutation tests** (1,000 iterations each): (a) a label‑permutation within the held‑out dataset (preserving batch structure) and (b) an across‑dataset label permutation that shuffles stress labels across all datasets while preserving dataset boundaries. The observed accuracy must be **significantly greater** than both null distributions (p < 0.05). (See US‑1)  
- **FR-009**: The system MUST perform a **post‑hoc power analysis** for any null result (accuracy ≤ random baseline). It computes the **Minimum Detectable Effect Size (MDES)** using observed sample size, class balance, and a two‑sided α = 0.05 test of proportions. (See US‑1)  
- **FR-010**: The system MUST compute **bootstrap stability** of logistic‑regression coefficients (100 resamples). Genes with coefficient variance ≤ 0.30 and selection frequency ≥ 0.70 are reported as robust biomarkers. (See US‑2)  
- **FR-011**: The system MUST generate **UMAP embeddings** (2‑D, n_neighbors = 15, min_dist = 0.1) of the held‑out test samples using the selected top K genes (no batch correction). It must calculate **Silhouette Scores** for stress‑type and dataset‑ID labels and report the difference. (See US‑3)  
- **FR-012**: The system MUST apply **Benjamini‑Hochberg FDR correction** to any p‑values derived from permutation tests or stability analyses, controlling the false discovery rate at **0.05**. (See US‑2)  
- **FR-013**: The system MUST log and export a CSV file `invalid_samples.csv` for any sample with missing or contradictory stress metadata (status `INVALID_LABEL`). (See US‑1)  
- **FR-014**: The system MUST update the project state file `state/projects/PROJ-042-predicting-plant-stress-response-from-pu.yaml` with a `research_complete: true` flag, a UTC timestamp, and SHA‑256 hashes of all result artefacts. (See US‑4)  
- **FR-015**: All findings are explicitly framed as **associational** (not causal) in generated reports, reflecting the observational nature of the public datasets. (See US‑5)  
- **FR-016**: The system MUST ensure total RAM usage ≤ 7 GB and total runtime ≤ 6 hours on a GitHub Actions free‑tier runner; if projected resource usage exceeds these limits (e.g., K = 150 on > 10 000 samples), the pipeline aborts with an informative error. (See US‑5)  
- **FR-017**: The system MUST require **≥ 7** distinct GEO datasets meeting the stress‑type criteria; if fewer are found, the pipeline aborts with a clear message. Additionally, it must compute a **95 % bootstrap confidence interval** for the LODO cross‑dataset accuracy by resampling the LODO folds (1,000 bootstrap replicates). (See US‑1)  
- **FR-018**: The system MUST verify that each selected GEO accession is a **plant transcriptomic study** and contains at least **two of the four target stress types**; any accession failing this check is excluded, logged, and does not contribute to downstream analysis. (See US‑1)  
- **FR-019**: The system MUST report a **sensitivity analysis** for the number of selected features K (50, 100, 150) including accuracy, macro‑F1, and the 95 % CI from FR‑017, enabling assessment of robustness to feature‑set size. (See US‑2)

### Key Entities

- **StressDataset** – Represents a GEO accession with raw counts, sample metadata (stress type, species, severity), and processed normalized values.  
- **FeatureSpace** – The intersection of gene identifiers across all selected StressDatasets after filtering; size ≥ 1,500 genes.  
- **ClassificationModel** – Logistic Regression instance storing coefficients, intercept, hyperparameters, and performance metrics for each LODO fold.  
- **Embedding** – 2‑D UMAP representation of test samples used for unsupervised validation.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cross‑dataset classification accuracy ≥ 0.70 **and** p < 0.05 versus the permutation null distribution (FR‑008). (See US‑1)  
- **SC-002**: Within‑dataset accuracy is reported and compared to the random baseline (1 / N) to confirm that a signal exists before cross‑dataset evaluation. (See US‑1)  
- **SC-003**: At least one gene meets the robustness criteria (variance ≤ 0.30, selection frequency ≥ 0.70) **or** the system explicitly reports “No robust minimal‑feature biomarkers” and provides the full variance table. (See US‑2)  
- **SC-004**: Stress‑type Silhouette Score ≥ 0.40 for ≥ 3 stress classes **and** dataset‑ID Silhouette Score at least 0.10 lower than the stress‑type score, confirming that clustering is not driven by batch. (See US‑3)  
- **SC-005**: Post‑hoc power analysis yields an MDES estimate; the report must state whether the observed sample size was sufficient to detect an effect size of 0.15 (Cohen’s h) with **≥ 0.80 power** (standard convention for adequate statistical power). (See US‑1)  
- **SC-006**: Total wall‑clock runtime ≤ 6 hours and peak RAM ≤ 7 GB on the free‑tier CI runner; resource logs are attached to the final artefact package. (See US‑5)  
- **SC-007**: The project state file is correctly updated (FR‑014) and passes schema validation. (See US‑4)  
- **SC-008**: The sensitivity analysis over K (FR‑019) shows that accuracy does not drop > 0.05 when moving from K = 50 to K = 150, demonstrating stability of the minimal‑feature model. (See US‑2)

## Assumptions

- **Data availability**: It is assumed that ≥ 7 plant GEO datasets meeting the stress‑type and sample‑size criteria exist. If fewer are found, the pipeline aborts (FR‑017).  
- **Gene‑identifier mapping**: It is assumed that `mygene`/`biomart` can map all gene IDs across the selected species to a common identifier space, yielding ≥ 1,500 intersecting genes. Failure triggers abort (FR‑004).  
- **Computational resources**: It is assumed that the chosen K values (50, 100, 150) keep the data matrix within the 7 GB RAM limit; the pipeline checks memory usage before training.  
- **Observational design**: All conclusions are reported as associational; no causal inference is attempted (FR‑015).  
- **Threshold justification**: The K values for feature selection are justified by memory constraints and by a predefined sensitivity analysis (see FR‑005).  
- **Power analysis method**: MDES is calculated using the normal approximation for difference in proportions (two‑sided α = 0.05), which is standard in classification power studies.  
- **Batch‑effect handling**: No batch correction is applied in the primary analysis; an optional sensitivity analysis (not required for primary acceptance) may apply ComBat within the training fold only.  
- **Class‑weighting**: Logistic Regression uses inverse‑frequency class weights when any stress class contributes < 5 % of samples in a dataset.  
- **Reproducibility**: All random seeds (data split, bootstrap, permutation) are fixed (seed = 42) to ensure deterministic results across CI runs.  