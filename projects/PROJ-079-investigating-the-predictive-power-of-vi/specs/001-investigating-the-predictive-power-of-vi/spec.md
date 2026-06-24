# Feature Specification: Predictive Modeling of Host Immune Response from Viral Sequence Features

**Feature Branch**: `001-predict-immune-response`  
**Created**: 2026-06-24  
**Status**: Draft  
**Input**: User description: "Investigating the Predictive Power of Viral Sequence Features for Host Immune Response"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - End‑to‑End Data Acquisition & preprocessing (Priority: P1)

A researcher wants to obtain a clean dataset that pairs viral genomic features with a quantitative host immune‑response score, ready for modelling.

**Why this priority**: Without reliable input data the entire scientific question cannot be addressed; this is the foundational step.

**Independent Test**: Run the pipeline on a representative subset of viruses and verify that a merged CSV containing all required columns is produced without manual intervention.

**Acceptance Scenarios**:

1. **Given** a list of virus identifiers present in the selected GEO studies, **When** the pipeline is executed, **Then** it downloads the corresponding complete genomes from NCBI Virus and stores them locally.  
2. **Given** the downloaded transcriptomic GEO series, **When** the preprocessing module runs, **Then** it outputs a normalized expression matrix and an interferon‑response score (first PC of a predefined ISG set) for each infected sample.

---

### User Story 2 - Model training & performance reporting (Priority: P2)

A researcher wants to train a predictive model and obtain clear performance metrics to evaluate the hypothesis.

**Why this priority**: Demonstrates whether viral sequence features have measurable predictive power, directly addressing the research question.

**Independent Test**: Execute the modelling step on the full dataset and verify that the reported R², RMSE, and permutation‑test p‑value are logged.

**Acceptance Scenarios**:

1. **Given** the pre‑processed feature/response matrix, **When** the elastic‑net training routine finishes, **Then** it outputs a model file, R² ≥ 0.30 on the held‑out test set, and an RMSE value.  

---

### User Story 3 - Interpretation & visualization of predictive features (Priority: P3)

A researcher wants to understand which viral features drive the predictions and to inspect their effect sizes.

**Why this priority**: Enables biological interpretation and hypothesis generation for downstream experimental work.

**Independent Test**: After model training, request the feature‑importance plot and verify that the top predictors are displayed with partial dependence curves.

**Acceptance Scenarios**:

1. **Given** a trained model, **When** the visualization module is invoked, **Then** it generates and saves (a) a bar plot of standardized coefficients for all retained features and (b) partial‑dependence plots for the five most influential predictors.

---

### Edge Cases

- What happens when a virus in the GEO dataset has no complete genome entry in NCBI Virus?  
- How does the system handle transcriptomic samples that lack clear infection metadata linking them to a specific virus strain?  
- What if the combined dataset contains fewer than 30 paired observations after filtering?  

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download viral genome sequences from NCBI Virus for every virus identifier referenced in the selected GEO transcriptomic studies.  
- **FR-002**: System MUST retrieve host transcriptomic count data from GEO, perform library‑size normalization (e.g., TMM or DESeq2 median‑ratio), and compute an interferon‑response score using a predefined interferon‑stimulated gene (ISG) set.  
- **FR-003**: System MUST extract the following viral sequence features for each genome:  
  - Codon Adaptation Index (CAI)  
  - Global and region‑specific GC‑content  
  - k‑mer frequencies for k = 3, 4, 5, 6  
  - Repeat density (percentage of genome covered by repeats)  
  - Predicted protein stability scores (using a lightweight predictor such as I‑TASSER‑lite).  
- **FR-004**: System MUST merge viral features with host response scores into a single tabular dataset, ensuring one‑to‑one mapping between virus strain and sample.  
- **FR-005**: System MUST split the merged dataset into training ([deferred]) and test ([deferred]) subsets stratified by virus family, guaranteeing no family appears in both splits.
- **FR-006**: System MUST train an elastic‑net regression model on the training set, tuning α (mixing) and λ (regularization strength) via 5‑fold cross‑validation *inside* the training data only.  
- **FR-007**: System MUST evaluate the final model on the held‑out test set, reporting R², RMSE, and conducting a permutation test with **≥ 1 000** random label shuffles to obtain an empirical p‑value for the overall model fit.  
- **FR-008**: System MUST compute variance‑inflation factors (VIF) for all candidate predictors and flag any predictor with VIF > 5 as collinear.  
- **FR-009**: System MUST apply Benjamini‑Hochberg false discovery rate (FDR) correction to the set of p‑values obtained from testing each individual feature’s coefficient against zero.  
- **FR-010**: System MUST generate and save (a) a bar plot of standardized feature importances and (b) partial‑dependence plots for the top 5 predictors, with axes labeled and legends included.  
- **FR-011**: System MUST log total execution time and abort with an informative error if runtime exceeds **4 hours** on a standard 8‑core CPU environment.  

### Key Entities

- **ViralGenome**: Represents a complete viral nucleotide sequence; key attributes include accession ID, virus family, and raw FASTA string.  
- **HostExpressionSample**: Represents a GEO transcriptomic sample; key attributes include sample ID, raw counts matrix, infection metadata, and computed ISG‑PC1 score.  
- **FeatureMatrix**: Tabular entity linking each ViralGenome to its extracted numerical features and the corresponding HostExpressionSample’s immune‑response score.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The elastic‑net model achieves **R² ≥ 0.30** on the held‑out test set (reference: Expected results).  
- **SC-002**: At least one viral feature shows an FDR‑adjusted permutation‑test p‑value **≤ 0.05** (reference: Expected results).  
- **SC-003**: All predictors retained in the final model have **VIF ≤ 5**, indicating acceptable collinearity (reference: Methodological soundness).  
- **SC-004**: The entire pipeline completes within **4 hours** on the prescribed compute environment (reference: Runtime constraint).  

## Assumptions

- **[NEEDS CLARIFICATION: does NCBI Virus contain complete genomes for every virus present in the selected GEO studies?]**  
- **[NEEDS CLARIFICATION: do the chosen GEO datasets provide explicit, machine‑readable metadata linking each infected sample to a specific virus strain accession?]**  
- **[NEEDS CLARIFICATION: is the predefined ISG gene set (e.g., 50 canonical interferon‑stimulated genes) validated for the host species represented in each GEO dataset?]**  
- Researchers have access to a Linux‑based compute node with at least 8 CPU cores, 32 GB RAM, and internet connectivity for data download.  
- All third‑party tools (Biopython, scikit‑learn, I‑TASSER‑lite) are available in the provided conda environment with pinned versions.  
- No additional experimental validation (e.g., wet‑lab assays) is required for this computational study; conclusions are limited to associational inference.
