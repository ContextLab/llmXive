# Feature Specification: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

**Feature Branch**: `001-predict-plant-disease-resistance`  
**Created**: 2026-06-26  
**Status**: Draft  
**Input**: User description: "Predicting Plant Disease Resistance from Publicly Available Metabolomic Data"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

As a researcher, I want to download, normalize, align, and harmonize public metabolomics datasets from Metabolomics Workbench that contain both pre-challenge metabolite profiles and disease-resistance metadata, so that I have a clean, analysis-ready dataset for model training.

**Why this priority**: This is the foundational step — without accessible, quality-controlled, and harmonized data, no downstream analysis is possible. This story can be independently tested by verifying data downloads, normalization outputs, label harmonization, and batch-effect correction.

**Independent Test**: Can be fully tested by executing the data acquisition script and verifying (1) ≥2 datasets download successfully, (2) metabolite intensity tables are normalized, log-transformed, and harmonized across studies, (3) resistance labels are constructed and harmonized from phenotype metadata, and (4) batch-effect correction is applied when ≥2 studies are combined.

**Acceptance Scenarios**:

1. **Given** Metabolomics Workbench study IDs with public access, **When** the acquisition script runs, **Then** raw intensity tables and phenotype metadata download successfully and are stored in the data directory
2. **Given** raw intensity tables with missing values, **When** preprocessing runs, **Then** features missing in >30% of samples are discarded and remaining values are log-transformed
3. **Given** ≥2 studies combined, **When** batch-effect correction runs, **Then** ComBat implementation is applied and batch-corrected values are stored separately from raw values
4. **Given** heterogeneous resistance labels across studies, **When** label harmonization runs, **Then** labels are standardized via z-scoring within study or stratified by assay method before model training

---

### User Story 2 - Model Training and Validation (Priority: P2)

As a researcher, I want to train a Random Forest classifier with constrained depth, stratified 5-fold cross-validation, and evaluate it on an independent hold-out set, including correlation testing, sensitivity analysis, and collinearity diagnostics, so that I can test whether constitutive metabolite profiles predict disease resistance without circular validation or overfitting.

**Why this priority**: This directly addresses the research question — testing the predictive relationship with methodological rigor. This story can be independently tested by verifying model performance metrics, validation methodology, and all supplementary analyses.

**Independent Test**: Can be fully tested by training the classifier on the preprocessed dataset, evaluating on the reserved [deferred] hold-out set, and verifying (1) balanced accuracy is evaluated against a 75% hypothesis threshold on test set, (2) feature selection uses only training folds, (3) test set remains independent throughout training, (4) correlation tests with FDR correction are performed, (5) sensitivity analysis sweeps cutoffs, and (6) collinearity diagnostics (VIF) are computed.

**Acceptance Scenarios**:

1. **Given** a preprocessed dataset with ≥50 samples and ≤50 metabolites, **When** Random Forest training runs with 5-fold CV, **Then** hyperparameters are optimized via GridSearchCV within the CV loop with max_depth constrained to 10 (tunable up to 20)
2. **Given** a trained model, **When** evaluation runs on the independent [deferred] hold-out set, **Then** balanced accuracy, ROC-AUC, and precision-recall curves are computed and logged
3. **Given** the full evaluation pipeline, **When** permutation testing runs with 1,000 permutations, **Then** a null distribution is generated and model performance is compared against it
4. **Given** metabolite and resistance data, **When** correlation analysis runs, **Then** pairwise correlations are computed and multiple-comparison correction (Benjamini-Hochberg FDR ≤0.05) is applied
5. **Given** a classification model, **When** sensitivity analysis runs, **Then** decision cutoffs are swept over absolute diff ∈ {0.01, 0.05, 0.1} and false-positive/false-negative rates are reported
6. **Given** selected metabolites, **When** collinearity diagnostics run, **Then** VIF is calculated for each predictor and values >5 are flagged

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

- What happens when no public dataset contains both pre-challenge metabolite data AND resistance labels? Metabolomics Workbench contains studies with both required variables. Verified via `fetch_url` on Metabolomics Workbench study catalog: multiple public datasets include pre-challenge metabolite profiles linked to disease-resistance metadata (phenotype scores) for the same germplasm. This satisfies the data availability assumption.
- How does system handle sample sizes <50 (insufficient for reliable ML)?
- What happens when batch-effect correction fails (e.g., ComBat convergence issues)?
- How does system handle metabolites that cannot be aligned across studies via InChIKey?
- What happens when the hold-out set contains no positive (resistant) samples (class imbalance)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download raw intensity tables and phenotype metadata from Metabolomics Workbench for ≥1 study with public access (See US-1)
- **FR-002**: System MUST normalize metabolite intensity values using log-transformation and discard features missing in >30% of samples (See US-1)
- **FR-003**: System MUST encode disease resistance as binary (resistant/susceptible) or ordinal (0–3 scale) based on published assay thresholds, with harmonization via z-scoring within study or stratification by assay method (See US-1)
- **FR-004**: System MUST apply ComBat batch-effect correction when ≥2 studies are combined (See US-1)
- **FR-005**: System MUST train Random Forest classifier with n_estimators=500, max_depth=10 (tunable up to 20), and stratified 5-fold cross-validation (See US-2)
- **FR-006**: System MUST reserve [deferred] of samples as independent hold-out set before any feature selection (See US-2)
- **FR-007**: System MUST perform permutation testing with ≥1,000 permutations to assess significance against null distribution (See US-2)
- **FR-008**: System MUST apply multiple-comparison correction (Benjamini-Hochberg FDR ≤0.05) for correlation tests between metabolites and resistance to control false discoveries in exploratory analysis (See US-2)
- **FR-009**: System MUST perform sensitivity analysis sweeping decision cutoffs over absolute diff ∈ {0.01, 0.05, 0.1} and report how false-positive/false-negative rates vary to ensure robustness against arbitrary threshold choices (See US-2)
- **FR-010**: System MUST extract feature importances and map top 10 metabolites to KEGG/MetaCyc pathways (See US-3)
- **FR-011**: System MUST frame all findings as ASSOCIATIONAL (not causal) in output documentation since no randomization is used (See US-2)
- **FR-012**: System MUST run collinearity diagnostics (VIF ≤5) for biological interpretation of feature importances, even though Random Forest handles collinearity internally (See US-2)
- **FR-013**: System MUST harmonize disease resistance labels across studies via z-scoring within study or stratification by assay method to address heterogeneity in assay protocols (See US-1)
- **FR-014**: System MUST verify that 'pre-challenge' samples are temporally and biologically distinct from the challenge outcome by checking sample metadata timestamps and experimental design (See US-1)

### Key Entities

- **MetaboliteProfile**: Represents pre-challenge metabolite abundances; key attributes include InChIKey, normalized intensity, sample ID
- **ResistanceLabel**: Represents disease-resistance phenotype; key attributes include germplasm ID, assay score (binary/ordinal), measurement method, harmonized score
- **Model**: Represents trained Random Forest classifier; key attributes include feature_importances_, balanced_accuracy, ROC-AUC

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Model balanced accuracy is measured against a 75% hypothesis threshold on the independent hold-out set to test the research question (See US-2)
- **SC-002**: Metabolite-resistance correlations are measured against |r| > 0.4, p < 0.01 criteria with Benjamini-Hochberg FDR correction (See US-2)
- **SC-003**: Permutation test significance is measured against p < 0.05 threshold comparing model performance to null distribution (See US-2)
- **SC-004**: Sample size sufficiency is measured against learning curve analysis per DOME recommendations (See US-2)
- **SC-005**: Threshold sensitivity is measured by sweeping absolute diff ∈ {0.01, 0.05, 0.1} and reporting variation in inconsistency rates (See US-2)

## Assumptions

- Public metabolomics repositories (Metabolomics Workbench) contain studies with both pre-challenge metabolite profiles AND documented disease-resistance scores for the same germplasm
- Sample sizes in available datasets are ≥50 to support stratified 5-fold cross-validation with meaningful hold-out set (if <50, learning curve analysis will flag power limitation)
- Metabolite identifiers can be aligned across studies using InChIKey (some studies may use different naming conventions requiring manual mapping)
- Batch-effect correction via ComBat is applicable when combining ≥2 studies (assumes sufficient overlap in metabolites across studies)
- Resistance labels are independent from metabolite measurements in terms of instrumental measurement (different instruments, different timepoints), but the model predicts a biological trait from its chemical manifestation; temporal and biological separation of 'pre-challenge' samples from challenge outcomes is verified via metadata
- All analysis runs within GitHub Actions free-tier constraints (2 CPU cores, ≤7 GB RAM, ≤6 h total runtime)
- Random Forest hyperparameter tuning completes within 4 hours (GridSearchCV with ≤50 metabolites, n_estimators=500, max_depth=10)
- Permutation testing with 1,000 iterations completes within 6 hours on CPU-only runner
- KEGG/MetaCyc pathway databases are accessible via public APIs for metabolite mapping
- No GPU or CUDA acceleration is required (all methods use scikit-learn on CPU in default precision)