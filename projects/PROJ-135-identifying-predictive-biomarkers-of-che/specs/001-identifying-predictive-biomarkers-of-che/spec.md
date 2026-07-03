# Feature Specification: Identifying Predictive Biomarkers of Chemotherapy Response in Public Cancer Datasets

**Feature Branch**: `001-chemo-biomarker-discovery`  
**Created**: 2024-01-15  
**Status**: Draft  
**Input**: User description: "Which gene‑expression signatures derived from publicly available cancer transcriptomic datasets can reliably predict patient response to standard chemotherapeutic agents across multiple tumor types?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1)

A researcher downloads transcriptomic data from TCGA and GEO repositories, harmonizes gene identifiers, filters low-expression genes, and normalizes counts to prepare a unified analysis-ready dataset.

**Why this priority**: This is the foundational step without which no downstream analysis can occur. The entire project depends on successful data retrieval and preprocessing.

**Independent Test**: Can be fully tested by running the data acquisition and pre-processing pipeline end-to-end on a subset of 2 cancer types and verifying that output files contain ≥100 samples per cancer type with harmonized gene symbols and variance-stabilized expression values.

**Acceptance Scenarios**:

1. **Given** valid TCGA project identifiers and GEO accession numbers, **When** the data acquisition script executes, **Then** RNA-seq count matrices and clinical metadata are downloaded to `data/raw/` and the system logs a warning if total size > 5 GB, but proceeds with execution.
2. **Given** raw count matrices with mixed identifier types (Ensembl, Entrez, HGNC), **When** the harmonization script runs, **Then** all genes are converted to HGNC symbols with ≥95% gene coverage retained.
3. **Given** a count matrix, **When** filtering and normalization execute, **Then** low-expression genes (CPM < 1 in >80% of samples) are removed and variance-stabilized values are output to `data/processed/`.

---

### User Story 2 - Cross-Cancer Biomarker Identification (Priority: P2)

A researcher performs differential expression analysis within each tumor type, identifies genes significant in ≥2 cancer types, and computes a meta-analyzed gene panel for cross-tumor validation.

**Why this priority**: This implements the core research question of finding generalizable biomarkers. Without cross-cancer integration, the project cannot answer whether signatures generalize.

**Independent Test**: Can be fully tested by running the DE analysis on 3 tumor types, computing the intersection of significant genes, and verifying that the meta-analysis produces a ranked gene panel with Stouffer's method p-values.

**Acceptance Scenarios**:

1. **Given** normalized expression data and response labels for a tumor type (discovery set), **When** DESeq2 Wald test executes, **Then** genes with FDR < 0.05 and |log2FC| > 1.0 are identified as significant.
2. **Given** significant gene lists from ≥2 tumor types (discovery sets), **When** the cross-cancer integration runs, **Then** the intersection produces a gene panel with ≤50 genes for downstream modeling; if the intersection yields 0 genes, the system MUST fallback to the union of top-ranked genes (≤50) and flag this in `results/summary.md`.
3. **Given** p-values for each gene across tumor types, **When** Stouffer's meta-analysis executes, **Then** combined p-values are computed and ranked genes are output to `results/meta_analysis/`.

---

### User Story 3 - Predictive Model Training and Validation (Priority: P3)

A researcher builds elastic-net logistic regression models using the identified gene panel, performs nested cross-validation, and evaluates external validation on independent GEO datasets to measure generalizability.

**Why this priority**: This validates the predictive utility of discovered biomarkers. It confirms whether the gene panel achieves the target AUC ≥0.75 and generalizes beyond training data.

**Independent Test**: Can be fully tested by training the elastic-net model on one cancer type's data (training set), performing nested cross-validation, and computing ROC-AUC on held-out GEO validation data.

**Acceptance Scenarios**:

1. **Given** the meta-analyzed gene panel and training data (training set), **When** elastic-net logistic regression executes with 5-fold nested CV, **Then** optimal alpha and lambda parameters are selected and AUC is computed.
2. **Given** a trained model, **When** external validation runs on ≥2 independent GEO datasets (after cross-platform normalization), **Then** the system MUST compute and report AUC for each cohort.
3. **Given** model predictions and clinical response labels, **When** calibration curves are generated, **Then** for all deciles with a sample size ≥20, predicted probabilities MUST align with observed response rates within ±10% (95% CI of calibration error); for deciles with <20 samples, the system MUST report the CI and flag the result as 'underpowered'.

---

### Edge Cases

- What happens when a GEO dataset lacks explicit response annotations (only survival data available)? → The pipeline must skip that dataset and log a warning; at least 2 datasets with response labels must be available for the feature to proceed.
- How does the system handle datasets with different normalization methods (e.g., RPKM vs. TPM vs. counts)? → The pipeline must re-normalize all expression data using DESeq2 VST to ensure comparability; datasets that cannot be re-normalized are excluded with a logged warning.
- What if the intersection of significant genes across tumor types yields 0 genes? → The pipeline must fall back to the union of top-ranked genes (≤50) and flag this in `results/summary.md` for manual review.
- How does the system handle class imbalance in response labels? → The system MUST use stratified k-fold cross-validation and, if the responder ratio is <20%, apply cost-sensitive learning with class weights inversely proportional to class frequency. The system MUST report class-weighted performance metrics (e.g., balanced accuracy) alongside AUC.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download TCGA RNA-seq HTSeq-Counts and clinical metadata via TCGAbiolinks R package for ≥3 tumor types (See US-1)
- **FR-002**: System MUST download ≥2 GEO microarray datasets with chemotherapy response annotations (e.g., GSE25055, GSE42752) via GEOquery (See US-1)
- **FR-003**: System MUST harmonize gene identifiers from Ensembl/Entrez to HGNC symbols with ≥95% gene coverage retained (See US-1)
- **FR-004**: System MUST filter low-expression genes (CPM < 1 in >80% of samples) and apply DESeq2 variance-stabilizing transformation (See US-1)
- **FR-005**: System MUST perform tumor-type-specific differential expression using DESeq2 Wald test with FDR < 0.05 and |log2FC| > 1.0 on the discovery set (See US-2)
- **FR-006**: System MUST compute intersection of significant genes across ≥2 tumor types (discovery sets) and apply Stouffer's meta-analysis for combined p-values; if intersection yields 0 genes, fallback to union of top-ranked genes (≤50) (See US-2)
- **FR-007**: System MUST build elastic-net logistic regression models with nested cross-validation within each cancer type using the training set (See US-3)
- **FR-008**: System MUST perform leave-one-cancer-type-out validation to assess cross-tumor generalizability; if LOO leaves <2 tumor types, the system MUST halt and report an error (See US-3)
- **FR-009**: System MUST compute ROC-AUC, precision-recall, and calibration curves for performance evaluation (See US-3)
- **FR-010**: System MUST apply Bonferroni correction for multiple hypothesis testing where m = number of genes in the final meta-analyzed panel (for meta-analysis significance) or m = number of model comparisons (for DeLong's test), with adjusted p-value threshold < 0.01 (See US-3)
- **FR-011**: System MUST report DeLong's test comparing model against clinical covariates-only baseline (See US-3)
- **FR-012**: System MUST execute entire pipeline on CPU-only GitHub Actions runner within ≤6 hours and ≤7 GB RAM (See US-1)
- **FR-013**: System MUST split each tumor type's data into a discovery set (for gene selection) and a training set (for model fitting) with a substantial majority/minority split (See US-2, US-3)
- **FR-014**: System MUST apply ComBat-seq or quantile matching to align GEO microarray data with TCGA RNA-seq data before model application (See US-3)

### Key Entities *(include if feature involves data)*

- **Sample**: Represents a patient tumor specimen with attributes: sample_id, tumor_type, response_label (responder/non-responder), expression_vector (gene × 1), set_type (discovery/training)
- **GenePanel**: Represents the meta-analyzed biomarker set with attributes: gene_symbol, meta_p_value, log2FC_mean, selected (boolean)
- **Model**: Represents the trained elastic-net predictor with attributes: cancer_type, alpha, lambda, coefficients, cross_val_auc

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: ROC-AUC on held-out validation cohorts is measured against the target threshold of ≥0.75 (See US-3)
- **SC-002**: Statistical significance of model improvement over random baseline is measured against Bonferroni-adjusted p < 0.01 (See US-3)
- **SC-003**: Gene panel generalizability is measured against performance drop between training and external validation cohorts (See US-3)
- **SC-004**: Pipeline runtime is measured against the GitHub Actions free-tier constraint of ≤6 hours (See US-1)
- **SC-005**: Memory usage is measured against the GitHub Actions free-tier constraint of ≤7 GB RAM (See US-1)
- **SC-006**: Cross-tumor biomarker discovery is measured against the requirement that ≥2 tumor types contribute significant genes to the panel (See US-2)

## Assumptions

- TCGA clinical metadata contains sufficient chemotherapy response annotations (RECIST or equivalent) for ≥3 tumor types; if annotations are sparse for a tumor type, that tumor type is excluded from analysis.
- GEO datasets GSE25055 and GSE42752 contain complete response annotations and expression data compatible with TCGA RNA-seq normalization methods.
- Elastic-net logistic regression on ≤50 genes with ≤1000 samples per tumor type will complete within 6 hours on 2 CPU cores with 7 GB RAM.
- The gene panel size of ≤30 genes is sufficient for clinical interpretability while maintaining predictive power; if the intersection yields >30 genes, the top 30 ranked by meta p-value are selected.
- All expression data can be re-normalized to DESeq2 VST scale regardless of original platform (RNA-seq or microarray); platform-specific batch effects are addressed via ComBat-seq or quantile matching (FR-014).
- The analysis is observational (no random assignment to treatment); findings are framed as associational relationships between gene expression and response, not causal effects.
- Sample size per tumor type is ≥50 responders and ≥50 non-responders to achieve adequate statistical power for differential expression; if power is insufficient, the analysis reports this limitation explicitly.
- Sensitivity analysis will sweep FDR thresholds {, 0.05, 0.1} for the initial screening (FR-005) and panel size, but the final model significance will use the fixed Bonferroni-adjusted threshold (FR-010) for the specific hypothesis tested.
- Gene expression predictors are not definitionally related (no collinearity by construction); if collinearity diagnostics (VIF > 5) identify related predictors, joint relationships are framed descriptively rather than as independent effects.
- If only 3 tumor types are available, LOO is valid (leaving 2 for training); if the dataset drops to 2 total types, LOO is invalid and the system MUST halt (FR-008).