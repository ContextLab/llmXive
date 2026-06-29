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

1. **Given** the pre‑processed feature/response matrix, **When** the elastic‑net training routine finishes, **Then** it outputs a model file, the R² value, and the RMSE value.  

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
- **FR-002**: System MUST retrieve host transcriptomic count data from GEO, perform library‑size normalization using TMM normalization (edgeR), and compute an interferon‑response score using the Interferome v2.0 Human ISG set (n=50) as the first principal component.  
- **FR-003**: System MUST extract the following viral sequence features for each genome:  
  - Codon Adaptation Index (CAI)  
  - Global and region‑specific GC‑content  
  - k‑mer frequencies for k = 3, 4, 5, 6  
  - Repeat density (percentage of genome covered by repeats)  
  - Predicted protein stability scores (using ESM-1b v1.1 for viruses with well-annotated ORFs of length > 100aa).  
- **FR-004**: System MUST merge viral features with host response scores into a single tabular dataset, ensuring one‑to‑one mapping between virus strain and sample.  
- **FR-005**: System MUST split the merged dataset into training and test subsets at the **virus strain level** (not family level), ensuring no strain appears in both splits. The test set MUST contain **≥ 5 distinct virus strains** to ensure statistical power for generalization. (See US-2)
- **FR-006**: System MUST train an elastic‑net regression model on the training set, tuning α (mixing) and λ (regularization strength) via 5‑fold cross‑validation *inside* the training data only.  
- **FR-007**: System MUST evaluate the final model on the held‑out test set, reporting R², RMSE, and conducting a global permutation test with **≥ 1 000** random label shuffles to obtain an empirical p‑value for the overall model fit.  
- **FR-008**: System MUST compute variance‑inflation factors (VIF) for all candidate predictors and flag any predictor with VIF > 5 as collinear. (See US-3)
- **FR-009**: System MUST apply Benjamini‑Hochberg false discovery rate (FDR) correction to the set of p‑values obtained from the Debiased Lasso feature significance test (FR-012). (See US-3)
- **FR-010**: System MUST generate and save (a) a bar plot of standardized feature importances and (b) partial‑dependence plots for the top 5 predictors, with axes labeled and legends included.  
- **FR-011**: System MUST log total execution time and abort with an informative error if runtime exceeds **4 hours** on a standard 8‑core CPU environment. (See US-1, US-2)
- **FR-012**: System MUST compute feature-level p-values for all retained predictors using the **Debiased Lasso** method (standard for Elastic Net inference) to generate a p-value for each coefficient against zero.  
- **FR-013**: System MUST implement a fallback strategy for missing genomes: if a complete genome is missing for a specific virus accession, the system MUST log a warning, exclude that specific virus from the training set, and proceed with the remaining data. The study is valid only if the final merged dataset contains **≥ 30** paired observations after this exclusion. (See US-1)
- **FR-014**: System MUST validate the presence of the `virus_strain_accession` or equivalent metadata field in the GEO series matrix. If this link is missing or ambiguous for a sample, the system MUST exclude that sample and log the reason. The pipeline MUST abort with a fatal error if **> 10%** of the initial candidate samples lack a valid strain link. (See US-1)
- **FR-015**: System MUST verify the host species of each GEO sample. For human (Homo sapiens) or mouse (Mus musculus), apply the standard canonical ISG set. For other species, the system MUST map orthologs using **Ensembl Compara v109** and apply the orthologous ISG set. If a sample is excluded from the ISG calculation, it is marked as 'response_unknown' and **excluded** from the regression training set. The final model MUST be trained on **≥ 30** samples with valid ISG scores. (See US-1)
- **FR-016**: System MUST perform **Strain-Level Aggregation** before modeling: if multiple host samples exist for the same virus strain, the system MUST average the host response scores (ISG-PC1) for that strain to create a single representative Y value, ensuring the unit of analysis is the strain, not the sample. (See US-2)
- **FR-017**: System MUST abort with a fatal error if the dataset contains fewer than **5 distinct virus strains** in the test set after splitting, as this violates the statistical power requirement for generalization. (See US-2)

### Key Entities

- **ViralGenome**: Represents a complete viral nucleotide sequence; key attributes include accession ID, virus family, and raw FASTA string.  
- **HostExpressionSample**: Represents a GEO transcriptomic sample; key attributes include sample ID, raw counts matrix, infection metadata, and computed ISG‑PC1 score.  
- **FeatureMatrix**: Tabular entity linking each ViralGenome to its extracted numerical features and the corresponding HostExpressionSample’s immune‑response score.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The system reports the R² value on the held-out test set; the hypothesis is supported if R² ≥ 0.30 (reference: Expected results).  
- **SC-002**: The system reports the minimum FDR-adjusted p-value from the Debiased Lasso test; the hypothesis is supported if min(p) ≤ 0.05 (reference: Expected results).  
- **SC-003**: All predictors retained in the final model have **VIF ≤ 5**, indicating acceptable collinearity (reference: Methodological soundness).  
- **SC-004**: The entire pipeline completes within **4 hours** on the prescribed compute environment (reference: Runtime constraint).  

## Assumptions

- The pipeline assumes complete genomes exist in NCBI Virus for all targeted viruses.  
- The pipeline requires explicit, machine-readable metadata linking samples to virus strains.  
- The predefined ISG gene set is validated for the host species.  
- Researchers have access to a Linux‑based compute node with at least 8 CPU cores, 32 GB RAM, and internet connectivity for data download.  
- All third‑party tools (Biopython, scikit-learn, ESM-1b, edgeR) are available in the provided conda environment with pinned versions.  
- No additional experimental validation (e.g., wet‑lab assays) is required for this computational study; conclusions are limited to associational inference.