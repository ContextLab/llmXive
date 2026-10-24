# Specification: Molecular Property Prediction Pipeline

## User Stories & Testing

### User Story US-001 (Priority: P1)
**Title:** Acquire high‑quality experimental molecular dataset.  
**Why this priority:** Provides the essential ground truth for all downstream modeling and interpretability work.  
**Independent Test:** Run the data‑download script and verify that every record contains experimental logP, solubility, and boiling point values with source citations.  
**Acceptance Scenarios:**  
1. **Given** the script `code/data/download.py` is executed, **When** it completes, **Then** `data/raw/molecules.csv` contains ≥ 5 000 rows, each with non‑missing experimental properties and a DOI reference.  
2. **Given** the dataset is downloaded, **When** a validator checks source URLs, **Then** all URLs resolve (status 200) and are from peer‑reviewed publications.

### User Story US-002 (Priority: P1)
**Title:** Preprocess and quality‑control the dataset.  
**Why this priority:** Guarantees that the modeling pipeline works on clean, reliable data.  
**Independent Test:** Execute `code/data/preprocess.py` and inspect `data/processed/clean_molecules.csv`.  
**Acceptance Scenarios:**  
1. **Given** the raw dataset, **When** preprocessing finishes, **Then** ≤ 5 % of records have any missing covariate and every retained record has a confidence score ≥ 0.9.  
2. **Given** the cleaned dataset, **When** a data‑quality report is generated, **Then** `data_quality_report.csv` lists `missing_covariate_rate ≤ 0.05` and `low_confidence_rate ≤ 0.05`.

### User Story US-003 (Priority: P1)
**Title:** Train predictive models and compare against an additive baseline.  
**Why this priority:** Core scientific claim – Random Forest should outperform the classic additive fragment model.  
**Independent Test:** Run `code/model/train_rf.py` and `code/model/baseline_xlogp3.py`, then execute `code/evaluation/compare_models.py`.  
**Acceptance Scenarios:**  
1. **Given** the clean dataset, **When** the RF model is trained with nested 5‑fold CV, **Then** test MAE ≤ 0.5 and RMSE ≤ 0.7 (logP units).  
2. **Given** both RF and baseline predictions, **When** the paired Wilcoxon signed‑rank test is applied, **Then** the p‑value ≤ 0.05, indicating a statistically significant improvement.

### User Story US-004 (Priority: P2)
**Title:** Generate explainability artifacts and interaction‑zone summary.  
**Why this priority:** Provides interpretable insight into non‑additive structural effects, fulfilling the project’s scientific goal.  
**Independent Test:** Execute `code/analysis/shap_explain.py` and `code/analysis/interaction_zone_report.py`.  
**Acceptance Scenarios:**  
1. **Given** trained RF and baseline models, **When** SHAP interaction values are computed, **Then** `shap_interactions.csv` contains ≥ 10 000 rows and a permutation‑test significance p ≤ 0.05 for reported interactions.  
2. **Given** the top fingerprint bits by mean absolute SHAP, **When** LNAI is computed for all possible pairwise combos., **Then** at least one interaction passes Benjamini‑Hochberg FDR ≤ 0.05 and is listed in `interaction_zone_report.pdf` with precision ≥ 0.8 and recall ≥ 0.7 against a curated substructure reference set.  

### Edge Cases
- What happens when a molecule lacks any of the required experimental properties? → Record is excluded and counted toward `missing_covariate_rate`.  
- How does the system handle duplicate SMILES entries? → Duplicates are collapsed; the duplicate count is reported in the data‑quality report.

## Functional Requirements
- **FR-001**: System MUST download **experimental** molecular data **(experimental logP, solubility, boiling point only)** from verified peer‑reviewed sources. (See US-001) **Task T001** runs `code/data/download.py`.  
- **FR-002**: System MUST preprocess data to handle missing values, ensure ≤ 5 % missing covariates, retain only records with confidence ≥ 0.9, and discard any computed property entries. (See US-002) **Task T002** runs `code/data/preprocess.py`.  
- **FR-003**: System MUST generate Open Babel **MACCS** and **FP2** fingerprints via CLI subprocess. (See US-002)  
- **FR-004**: System MUST train Random Forest models with nested 5‑fold cross‑validation and fixed random seed = 42. (See US-003)  
- **FR-005**: System MUST perform a paired Wilcoxon signed‑rank test (α = 0.05) between the additive‑fragment baseline and the Random Forest on absolute errors. (See US-003)  
- **FR-006**: System MUST generate SHAP interaction values for the Random Forest and assess their significance with a 1 000‑permutation test (p ≤ 0.05). (See US-004)  
- **FR-007**: System MUST map SHAP bits back to chemical substructures and achieve precision ≥ 0.8 and recall ≥ 0.7 against a curated reference set. (See US-004)  
- **FR-008**: System MUST log data quality metrics (missing_covariate_rate, low_confidence_rate) in `data_quality_report.csv` with thresholds ≤ 0.05 each. (See US-002) **Task T003** creates the report.  
- **FR-009**: System MUST compute an additive‑fragment baseline (e.g., XlogP3) for each molecule and output residuals in `baseline_residuals.csv`. (See US-003)  
- **FR-010**: System MUST produce an Interaction‑Zone Report (`interaction_zone_report.pdf`) summarizing statistically significant fingerprint‑bit‑pair interactions after pre‑selecting the top‑100 bits by mean absolute SHAP value (≈ 4 950 tested pairs). (See US-004)  
- **FR-011**: System MUST obtain expert review of the Interaction‑Zone Report and record acceptance (≥ 2 independent chemists) in `validation_report.pdf`. (See US-004)  
- **FR-012**: System MUST compute the Local Non‑Additivity Index (LNAI) **only for fingerprint bit‑pairs where each bit has marginal prevalence ≥ 5 % and the joint prevalence ≥ 5 %**, using **rank‑biserial correlation** between `(RF_error − Baseline_error)` and the joint‑presence indicator; significance is assessed via a 10 000‑permutation test and corrected with Benjamini‑Hochberg (FDR ≤ 0.05). (See US-004)  
- **FR-013**: System MUST pre‑select the top‑100 fingerprint bits by mean absolute SHAP importance **before** any LNAI pairwise testing to limit the number of tested pairs to ≈ 4 950. (See US-004)  
- **FR-014**: System MUST generate visual artifact `shap_interactions.png` summarizing the distribution of significant SHAP interaction values. (See US-004)  
- **FR-015**: System MUST generate visual artifact `rf_residuals.png` showing residuals of the Random Forest predictions versus the baseline. (See US-003)  

## Non-Functional Requirements
- **NFR-001**: All code MUST be Python 3.10+.  
- **NFR-002**: Data artifacts MUST be stored in the `data/` directory hierarchy.  
- **NFR-003**: Scripts MUST fail loudly if real data sources are unreachable.  
- **NFR-004**: Analysis MUST be reproducible via explicit random seed management (seed = 42).  

## Data Model
- **Input**: SMILES strings, **experimental** logP, solubility, boiling point.  
- **Intermediate**: Fingerprint arrays (MACCS, FP2).  
- **Output**:  
  - `predictions.csv` (RF predictions with confidence scores)  
  - `baseline_residuals.csv` (baseline prediction errors)  
  - `rf_residuals.png` (visual residual plot)  
  - `shap_interactions.csv` (SHAP interaction values)  
  - `shap_interactions.png` (visual summary of SHAP interactions)  
  - `interaction_zone_report.pdf` (summary of significant bit‑pair interactions)  
  - `data_quality_report.csv` (missing covariate rate, low‑confidence rate, duplicate count, etc.)  
  - `lna_index.csv` (rank‑biserial correlation values for selected bit‑pairs)  
  - `validation_report.pdf` (expert review outcomes)  
  - `validation_audit.pdf` (comprehensive audit of all generated artifacts)  

## Validation Protocol
- **Data split**: Perform a **stratified [deferred] / [deferred] train‑test split** on the experimental dataset, stratifying on the target property (logP) and fixing random seed = 42 for reproducibility.
- **Metrics**: MAE ≤ 0.5 logP units, RMSE ≤ 0.7 logP units on the held‑out test set.  
- **Statistical Test**: Paired Wilcoxon signed‑rank test on absolute errors (α = 0.05).  
- **Baseline generation**: Compute additive‑fragment XlogP3 values for all molecules; store residuals.  
- **SHAP interaction significance**: Compute SHAP interaction values; assess via 1 000‑permutation test, retain interactions with p ≤ 0.05.  
- **LNAI computation**:  
  1. Rank fingerprint bits by mean absolute SHAP value; select top 100 bits (≈ 4 950 pairs).  
  2. For each pair, require **marginal prevalence ≥ 5 %** for each bit and **joint prevalence ≥ 5 %** of molecules; compute **rank‑biserial correlation** between `(RF_error − Baseline_error)` and the joint presence indicator.  
  3. Assess significance with a 10 000‑permutation test; apply Benjamini‑Hochberg FDR correction; retain pairs with FDR ≤ 0.05.  
- **Expert validation**: Two independent chemists must review `interaction_zone_report.pdf`; acceptance recorded in `validation_report.pdf`.  

## Success Criteria
- **SC-001**: Experimental dataset contains ≥ 5 000 molecules with complete experimental logP, solubility, and boiling point entries (see US-001).  
- **SC-002**: After preprocessing, missing_covariate_rate ≤ 0.05 and low_confidence_rate ≤ 0.05 (see US-002).  
- **SC-003**: Random Forest test MAE ≤ 0.5 and RMSE ≤ 0.7 logP units (see US-003).  
- **SC-004**: Paired Wilcoxon test yields p ≤ 0.05, demonstrating RF superiority over baseline (see US-003).  
- **SC-005**: Interaction‑Zone Report contains ≥ 1 statistically significant bit‑pair with precision ≥ 0.8 and recall ≥ 0.7, and receives positive expert review (see US-004).  

## Assumptions
- All target property values are experimentally measured; computed estimates are excluded.  
- The Open Babel CLI provides accurate MACCS and FP2 fingerprints for all input SMILES.  
- The curated substructure reference set used for evaluating mapping precision/recall is pre‑validated and stored in `reference/substructures.yaml`.  
- Computational resources are limited to 2 CPU cores, 7 GB RAM, and ≤ 4 h runtime per pipeline execution.  
- Pre‑selection of the top‑100 SHAP‑important bits ensures the LNAI step (≈ 5 k pairwise tests) completes well within the runtime budget.  

## Tasks
- **T001**: Run `code/data/download.py` to retrieve experimental molecular data.  
- **T002**: Run `code/data/preprocess.py` to clean data, filter by confidence, and enforce missing‑value limits.  
- **T003**: Generate `data_quality_report.csv` summarizing missing covariate rate, low‑confidence rate, and duplicate count.  
- **T004**: Compute MACCS and FP2 fingerprints via Open Babel CLI.  
- **T005**: Train Random Forest with nested 5‑fold CV (seed = 42).  
- **T006**: Compute additive‑fragment baseline (XlogP3) and residuals.  
- **T007**: Perform paired Wilcoxon signed‑rank test on absolute errors.  
- **T008**: Compute SHAP interaction values and assess significance with 1 000‑permutation test.  
- **T009**: Generate `shap_interactions.png`.  
- **T010**: Pre‑select top‑100 fingerprint bits by mean absolute SHAP importance.  
- **T011**: Compute LNAI for qualifying bit‑pairs using rank‑biserial correlation and 10 000‑permutation test with BH FDR correction.  
- **T012**: Produce `interaction_zone_report.pdf` and `validation_report.pdf` (expert review).  
- **T013**: Generate visual artifact `rf_residuals.png`.  
- **T014**: Assemble `validation_audit.pdf` compiling all generated artifacts and compliance checks.  
