# Feature Specification: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

**Feature Branch**: `001-predict-plant-disease-resistance`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Predicting Plant Disease Resistance from Publicly Available Metabolomic Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a researcher, I want to download, normalize, and align public metabolomics datasets from Metabolomics Workbench that contain both pre-challenge metabolite profiles and disease-resistance metadata, so that I have a clean, analysis-ready dataset for model training.

**Why this priority**: This is the foundational step — without accessible, quality-controlled data, no downstream analysis is possible. This story can be independently tested by verifying data downloads, normalization outputs, and label construction.

**Independent Test**: Can be fully tested by executing the data acquisition script and verifying (1) ≥1 dataset downloads successfully, (2) metabolite intensity tables are normalized and log-transformed, (3) resistance labels are constructed from phenotype metadata, and (4) batch-effect correction is applied when ≥2 studies are combined.

**Acceptance Scenarios**:

1. **Given** Metabolomics Workbench study IDs with public access, **When** the acquisition script runs, **Then** raw intensity tables and phenotype metadata download successfully and are stored in the data directory
2. **Given** raw intensity tables with missing values, **When** preprocessing runs, **Then** features missing in >30% of samples are discarded and remaining values are log-transformed
3. **Given** ≥2 studies combined, **When** batch-effect correction runs, **Then** ComBat implementation is applied and batch-corrected values are stored separately from raw values

---

### User Story 2 - Model Training and Validation (Priority: P2)

As a researcher, I want to train a Random Forest classifier with stratified 5-fold cross-validation and evaluate it on an independent hold-out set, so that I can test whether constitutive metabolite profiles predict disease resistance without circular validation.

**Why this priority**: This directly addresses the research question — testing the predictive relationship. This story can be independently tested by verifying model performance metrics and validation methodology.

**Independent Test**: Can be fully tested by training the classifier on the preprocessed dataset, evaluating on the reserved hold-out set, and verifying (1) balanced accuracy ≥75% on test set, (2) feature selection uses only training folds, and (3) test set remains independent throughout training.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset with ≥50 samples and ≤50 metabolites, **When** Random Forest training runs with 5-fold CV, **Then** hyperparameters are optimized via GridSearchCV within the CV loop
2. **Given** a trained model, **When** evaluation runs on the [deferred] hold-out set, **Then** balanced accuracy, ROC-AUC, and precision-recall curves are computed and logged
3. **Given** the full evaluation pipeline, **When** permutation testing runs with 1,000 permutations, **Then** a null distribution is generated and model performance is compared against it

---

### User Story 3 - Biological Interpretation and Pathway Mapping (Priority: P3)

As a researcher, I want to extract feature importances from the trained model and map top metabolites to known pathways via KEGG/MetaCyc, so that I can assess biological plausibility of identified resistance signatures.

**Why this priority**: This provides biological insight but depends on P1 and P2 being complete. This story can be independently tested by verifying pathway mappings are generated and documented.

**Independent Test**: Can be fully tested by running the interpretation script on a trained model and verifying (1) top 10 metabolites by importance are extracted, (2) each is mapped to ≥1 pathway, and (3) results are documented with pathway names and literature references.

**Acceptance Scenarios**:

1. **Given** a trained Random Forest model, **When** feature importance extraction runs, **Then** top 10 metabolites ranked by mean decrease in impurity are identified
2. **Given** top metabolites with InChIKeys, **When** pathway mapping runs, **Then** each metabolite is matched to ≥1 KEGG or MetaCyc pathway
3. **Given** mapped pathways, **When** interpretation report generates, **Then** biological plausibility is discussed with reference to known defense compounds (e.g., phytoalexins, phenolics)

---

### Edge Cases

- What happens when no public dataset contains both pre-challenge metabolite data AND resistance labels? [NEEDS CLARIFICATION: does Metabolomics Workbench contain studies with both required variables?]
- How does system handle sample sizes <50 (insufficient for reliable ML)?
- What happens when batch-effect correction fails (e.g., ComBat convergence issues)?
- How does system handle metabolites that cannot be aligned across studies via InChIKey?
- What happens when the hold-out set contains no positive (resistant) samples (class imbalance)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download raw intensity tables and phenotype metadata from Metabolomics Workbench for ≥1 study with public access (See US-1)
- **FR-002**: System MUST normalize metabolite intensity values using log-transformation and discard features missing in >30% of samples (See US-1)
- **FR-003**: System MUST encode disease resistance as binary (resistant/susceptible) or ordinal (0–3 scale) based on published assay thresholds (See US-1)
- **FR-004**: System MUST apply ComBat batch-effect correction when ≥2 studies are combined (See US-1)
- **FR-005**: System MUST train Random Forest classifier with n_estimators=500, max_depth=None, and stratified 5-fold cross-validation (See US-2)
- **FR-006**: System MUST reserve [deferred] of samples as independent hold-out set before any feature selection (See US-2)
- **FR-007**: System MUST perform permutation testing with ≥1,000 permutations to assess significance against null distribution (See US-2)
- **FR-008**: System MUST apply multiple-comparison correction (e.g., Benjamini-Hochberg FDR) for correlation tests between metabolites and resistance (See US-2)
- **FR-009**: System MUST perform sensitivity analysis sweeping any decision cutoff over absolute diff ∈ {0.01, 0.05, 0.1} and report how false-positive/false-negative rates vary (See US-2)
- **FR-010**: System MUST extract feature importances and map top 10 metabolites to KEGG/MetaCyc pathways (See US-3)
- **FR-011**: System MUST frame all findings as ASSOCIATIONAL (not causal) in output documentation since no randomization is used (See US-2)
- **FR-012**: System MUST run collinearity diagnostics (e.g., VIF ≤5) when multiple predictors are definitionally related (See US-2)

### Key Entities

- **MetaboliteProfile**: Represents pre-challenge metabolite abundances; key attributes include InChIKey, normalized intensity, sample ID
- **ResistanceLabel**: Represents disease-resistance phenotype; key attributes include germplasm ID, assay score (binary/ordinal), measurement method
- **Model**: Represents trained Random Forest classifier; key attributes include feature_importances_, balanced_accuracy, ROC-AUC

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model balanced accuracy is measured against the ≥75% target threshold on the independent hold-out set (See US-2)
- **SC-002**: Metabolite-resistance correlations are measured against |r| > 0.4, p < 0.01 criteria with Benjamini-Hochberg FDR correction (See US-2)
- **SC-003**: Permutation test significance is measured against p < 0.05 threshold comparing model performance to null distribution (See US-2)
- **SC-004**: Sample size sufficiency is measured against learning curve analysis per DOME recommendations (See US-2)
- **SC-005**: Threshold sensitivity is measured by sweeping absolute diff ∈ {0.01, 0.05, 0.1} and reporting variation in inconsistency rates (See US-2)

## Assumptions

- Public metabolomics repositories (Metabolomics Workbench) contain studies with both pre-challenge metabolite profiles AND documented disease-resistance scores for the same germplasm
- Sample sizes in available datasets are ≥50 to support stratified 5-fold cross-validation with meaningful hold-out set (if <50, learning curve analysis will flag power limitation)
- Metabolite identifiers can be aligned across studies using InChIKey (some studies may use different naming conventions requiring manual mapping)
- Batch-effect correction via ComBat is applicable when combining ≥2 studies (assumes sufficient overlap in metabolites across studies)
- Resistance labels are independent from metabolite measurements (different instruments, different timepoints — no shared signal)
- All analysis runs within GitHub Actions free-tier constraints (2 CPU cores, ≤7 GB RAM, ≤6 h total runtime)
- Random Forest hyperparameter tuning completes within 4 hours (GridSearchCV with ≤50 metabolites, n_estimators=500)
- Permutation testing with 1,000 iterations completes within 6 hours on CPU-only runner
- KEGG/MetaCyc pathway databases are accessible via public APIs for metabolite mapping
- No GPU or CUDA acceleration is required (all methods use scikit-learn on CPU in default precision)
