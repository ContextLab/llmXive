---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Molecular Properties from Open Babel Fingerprints with Random Forests

**Input**: Design documents from `/specs/001-predicting-molecular-properties/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, linting, and performance configuration.

- [X] T001 Create `projects/PROJ-324-predicting-molecular-properties-from-ope/` directory structure including `code/`, `tests/`, `data/raw`, `data/processed`, `data/derived` subdirectories
- [X] T002 Initialize Python 3.10+ project with `requirements.txt` (rdkit, scikit-learn, shap, pandas, numpy, datasets, requests, obabel-wrapper)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T036 [S] **Performance Configuration**: Implement specific runtime constraints in `code/utils/config.py`. **Requirements**: 
  1. Set `MAX_DEPTH` = 15 for Random Forest (per Constitution VII).
  2. Configure `joblib` parallel backend for fingerprint generation with `n_jobs=-1` but `max_memory=6GB`.
  3. Implement a hard timeout check for `obabel` subprocess (max reasonable duration per molecule) to ensure the full pipeline completes within the **6-hour window** (Constitution VII) and targets the **4-hour goal** (Plan).
  *Dependency: Must be completed before T019 and T020 to ensure configuration is applied.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data download, preprocessing, and the critical train/test split.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create base `code/__init__.py` and utility modules for logging and seed management
- [ ] T008 [P] [US1] **Data Download**: Implement `code/data/download.py` using **PubChemPy** to fetch a diverse dataset of molecules with SMILES and experimental logP, solubility, boiling point. **CRITICAL**: This task supersedes any reference to `molecule-net` or GitHub URLs. Use `pubchempy.get_compounds()` or `pubchempy.get_cids()` to fetch data. Ensure real data only. Target: A large-scale dataset of molecules.
- [ ] T009 [P] [US1] Implement `code/data/preprocess.py` to filter for **high-confidence measurements**. **Logic**: 
  1. Exclude entries where `confidence_score < 0.8` (if available) or where target properties (logP, solubility, boiling point) are missing.
  2. **Explicitly check for physical covariates**: Detect missing pH, temperature, and pressure fields in the source data. If these fields are absent, log them as "Missing" in the report. Do NOT conflate missing metadata flags with missing physical covariates.
  3. Log the **experimental threshold** status (Plan Phase 0 Step 0.3) to `data/derived/data_quality_report.csv`.
  **Schema**: `data/derived/data_quality_report.csv` must include columns: `smiles`, `exclusion_reason`, `missing_covariate_list` (list of missing physical fields), `experimental_flag`.
- [X] T010 [P] [US1] Implement `code/data/preprocess.py` to define the **MaxMin sampling strategy** for calculating Tanimoto similarity. This task must define the algorithm to select a diverse subset (Tanimoto < 0.7) from the preprocessed data. **Constraint**: Target a final diverse set of **5000 molecules** (increased from 4000 to accommodate the 1000-molecule test set) to ensure O(N) feasibility on the 2-core runner within 6 hours, as authorized by Constitution VII (Computational Efficiency). The algorithm must select the maximum subset satisfying the diversity constraint or the full set if <5,000 exist.
- [X] T011 [US1] Implement `code/data/preprocess.py` to **execute** the diversity filtering using the strategy defined in T010, producing the final diverse dataset of **5000 molecules**. This task consumes the output of T009.
- [ ] T011.5 [US1/US2] Implement `code/data/preprocess.py` to **split** the diverse dataset into a training set and a strictly held-out test set. This task must ensure the split is random, stratified (if possible), and reproducible via random seed. Output `data/derived/train_set.csv` and `data/derived/test_set.csv`. *Status: Sequential after Phase 2 completion.*
- [X] T031 [P] [US1/US2] Enhance `code/data/download.py` (T008) to explicitly document the **experimental source**, **measurement conditions** (e.g., temperature, pH if available), and **source confidence** in the dataset metadata (`data/raw/dataset_metadata.json`). **CRITICAL**: Perform a runtime schema check for the presence of `measurement_uncertainty` and `quantity_of_substance` fields. If absent, the code MUST derive and record `"measurement_uncertainty_status": "Not Available in Source"` and `"quantity_of_substance_status": "Not Available in Source"` based on the actual fetched schema, not hard-coded strings. This validates data hygiene immediately upon ingestion.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. **Note**: T011.5 (Split) must be completed before T019 (Fingerprints) to ensure valid data separation.

---

## Phase 3: User Story 1 - Baseline Error Quantification (Priority: P1) 🎯 MVP

**Goal**: Generate a baseline prediction for logP, solubility, and boiling point using Crippen's additive fragment model and quantify the error against real experimental data on the **held-out test set**.

**Independent Test**: Can be fully tested by running the Crippen's additive fragment algorithm on the provided dataset and outputting a CSV of predicted vs. experimental values with a calculated Mean Absolute Error (MAE).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [X] T013 [P] [US1] Unit test for Crippen's atomic contribution calculation in `tests/unit/test_crippen.py`

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/models/baseline.py` to compute Crippen's atomic contributions for **ALL molecules in the full dataset** (both training and test sets). **Schema**: `smiles`, `property_name`, `experimental_value`, `predicted_value`, `residual`. **Algorithm**: Use standard Crippen atomic contributions (per Plan). **Fallback**: If an atom type is undefined in the Crippen set, log a warning, set `predicted_value` to the **mean of the training set** for that property, and flag `prediction_status` as 'Partial'. This task must handle undefined atoms deterministically.
- [ ] T014.5 [US1] Implement `code/models/baseline.py` to **extract** the test set predictions from the full dataset output of T014, saving specifically to `data/derived/baseline_test_predictions.csv` for use in the final statistical test (T021).
- [ ] T015 [US1] Implement `code/analysis/stats.py` to calculate MAE/RMSE for baseline predictions **on the held-out test set** (consuming `baseline_test_predictions.csv` from T014.5) and generate residual distribution plots (`data/derived/baseline_residuals.png`).
- [X] T016 [US1] Implement `code/analysis/stats.py` to log the "additive failure" magnitude. *Note: 3D conformational flagging is deferred to Phase 6 (T033).*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently, establishing the additive ground truth.

---

## Phase 4: User Story 2 - Non-Linear Model Training and Validation (Priority: P2)

**Goal**: Train Random Forest regressors using Open Babel fingerprints and evaluate performance via k-fold cross-validation on the **training set**, then evaluate on the **held-out test set** to quantify improvement over the additive baseline.

**Independent Test**: Can be fully tested by training the Random Forest model, performing k-fold cross-validation, and reporting the RMSE and MAE, comparing them numerically to the P1 baseline metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for fingerprint generation in `tests/contract/test_fingerprint_schema.py`
- [X] T018 [P] [US2] Integration test for full training pipeline in `tests/integration/test_rf_pipeline.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/data/fingerprints.py` to generate Open Babel fingerprints (MACCS, ECFP4, FP2) by **invoking the `obabel` command-line tool via subprocess** (per FR-003). **Execution Logic**: 
  1. Generate ECFP4, MACCS, and FP2 for **all molecules** in the training set.
  2. **Do NOT skip** any fingerprint type based on runtime. If `obabel` fails to complete within the 6-hour window, the script must **fail loudly** (raise an exception) to prevent partial feature sets.
  3. This task must consume the **training set** from T011.5. *Dependency: Must wait for T011.5 completion.* It must produce the `fingerprints.parquet` artifact.
- [X] T019.5 [US2] Implement `code/models/random_forest.py` to set up **Nested Cross-Validation** (outer loop for test set, inner loop for hyperparameter tuning) to generate valid error pairs for statistical testing, as required by the Plan's Complexity Tracking section.
- [X] T020 [US2] Implement `code/models/random_forest.py` to train RF regressors using the Nested CV structure (T019.5) with hyperparameter tuning via -fold cross-validation **on the training set**, ensuring `max_depth` limits (≤15) and dataset sampling to fit CPU constraints (FR-004). This task must produce a `final_model.pkl` artifact trained on the full training set for downstream SHAP analysis.
- [ ] T020.1 [US2] Implement `code/models/random_forest.py` to perform the **final model evaluation** on the **held-out test set** using the trained model (`final_model.pkl`) and generate `data/derived/rf_test_predictions.csv`. This step is critical for the paired Wilcoxon test (FR-005) to ensure valid error pairs are available.
- [ ] T021 [US2] Implement `code/analysis/stats.py` to perform paired Wilcoxon signed-rank test on absolute errors (Baseline vs. RF) using the valid error pairs from the **held-out test set** (consuming `baseline_test_predictions.csv` from T014.5 and `rf_test_predictions.csv` from T020.1). **Critical Logic**: Before running the test, **check the experimental threshold status** (from T009). If <50% of the test set has experimental values, **skip the statistical test**, log a "Model Consistency" report, and output a placeholder report indicating the limitation. Do not crash or produce invalid p-values.
- [ ] T022 [US2] Implement `code/analysis/stats.py` to generate comparison plots (Baseline vs. RF MAE/RMSE) **using the held-out test set** and save to `data/derived/model_comparison.png`.
- [X] T023 [US2] Implement `code/models/random_forest.py` to include a runtime monitor that automatically reduces dataset size or skips lower-priority fingerprints if the 6-hour limit is approached (per Edge Cases). *Note: This monitor must NOT override the hard fail in T019, but can adjust parameters for future runs.*

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, providing a statistically significant comparison.

---

## Phase 5: User Story 3 - Interaction Zone Mapping (Priority: P3)

**Goal**: Identify specific fingerprint bit pairs contributing to error reduction using SHAP values, map them to chemical substructures, and validate against known chemical rules (using RDKit built-ins).

**Independent Test**: Can be fully tested by generating SHAP summary plots, interaction strength heatmaps, and mapping the top interacting fingerprint bits back to chemical substructures using RDKit.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for interaction context schema in `tests/contract/test_interaction_schema.py`
- [X] T025 [P] [US3] Unit test for SHAP bit-to-substructure mapping in `tests/unit/test_shap_mapping.py`

### Implementation for User Story 3

- [ ] T030.1 [US3] **Create Rules File**: Implement `code/data/rules.py` to define and export the required SMARTS patterns (hydroxyl, carbonyl, aromatic, etc.) as a list of dictionaries or a constant. This file is a **prerequisite** for T030.
- [X] T026 [US3] Implement `code/analysis/explainability.py` to calculate SHAP interaction values for the trained RF model (T020) using the `final_model.pkl` artifact (FR-006). *Dependency: Requires T020 completion.*
- [ ] T027 [US3] Implement `code/analysis/explainability.py` to generate heatmaps of top interacting fingerprint bit pairs and save to `data/derived/shap_interactions.png`.
- [ ] T029 [US3] Implement `code/analysis/explainability.py` to map top interacting bits back to chemical substructures using RDKit, outputting `data/derived/deviation_contexts.csv` (FR-007).
- [X] T030 [US3] Implement `code/analysis/explainability.py` to cross-reference identified substructures with **RDKit's built-in functional group detection** (`rdkit.Chem.Fragments`) and **steric descriptors** (`rdkit.Chem.rdMolDescriptors` - e.g., Molecular Weight, TPSA, NumRotatableBonds) to correlate **topological proxies** for steric effects with model deviations (FR-010). **Requirement**: Explicitly compute and output the **Local Non-Additivity Index** (LNAI) as the correlation between RF residuals and Crippen baseline deviations, identifying specific **interaction zones** where RF outperforms the additive baseline, per Constitution Principle VI. **Dependency**: Load SMARTS patterns from `code/data/rules.py` (T030.1). *Note: Steric descriptors are used as **topological proxies** for steric effects, consistent with the Plan's disclaimer that 2D fingerprints cannot capture true 3D steric hindrance. Do NOT claim to distinguish physical phenomena.*
- [X] T039 [US3] Implement `code/analysis/explainability.py` to explicitly frame findings as **associational** correlations, not causal mechanisms, in the output report (per Assumptions).

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Reviewer Concerns & Data Integrity (Revision Tasks)

**Purpose**: Address specific feedback from Marie Curie (simulated) and Rosalind Franklin (simulated) regarding experimental validation, measurement uncertainty, and conformational limitations.

- [X] T033 [P] [US3] Implement `code/analysis/explainability.py` to generate a "Conformational Limitation Report" that identifies molecules where 2D topology (fingerprints) likely fails to capture solution-phase conformational ensembles. **Method**: Use a topological proxy heuristic (specifically `NumRotatableBonds > 10` via RDKit) to flag potential 3D failures, addressing Rosalind Franklin's concern on static vs. dynamic structures.
- [X] T043 [P] [US1/US2/US3] **Marie Curie Review Response**: Implement `code/analysis/stats.py` to generate a **Validation Protocol Summary** in the final report. This task must **explicitly state the absence** of `measurement_uncertainty` and `quantity_of_substance` data if T031 detected these fields as missing. It must NOT attempt to extract non-existent data, but rather report the source limitation as a derived fact. This task aggregates the metadata findings from T031 to ensure the final report reflects the actual state of the data.
- [X] T044 [P] [US1/US2/US3] **Marie Curie Review Response**: Enhance `code/analysis/stats.py` to include a **Validation Protocol Summary** section in the final report. This section must explicitly state the **held-out test set size**, the **source of experimental values** for the test set, and the **measurement uncertainty** (or "Not Available" if missing) for the target properties, ensuring the model's output is framed as a comparison against verified experimental data, not just cross-validation scores.
- [X] T045 [P] [US3] **Rosalind Franklin Review Response**: Implement `code/analysis/explainability.py` to generate a **Conformational Sensitivity Analysis**. This task must compare the RF predictions against a set of molecules identified by the `NumRotatableBonds > 10` heuristic and report the **deviation magnitude** for these specific cases. The report must explicitly state that the model's "substructure" findings are **topological proxies** and may not reflect solution-phase conformational ensembles, addressing the concern that fingerprints are topological abstractions.
- [X] T046 [P] [US1/US2/US3] **Marie Curie Review Response**: Implement `code/analysis/stats.py` to generate a **Data Provenance & Uncertainty Ledger**. This task must iterate through the final dataset and create a structured log (JSON/CSV) that explicitly maps each molecule's property values to their specific source record (e.g., "PubChem CID 12345, Experimental LogP, Uncertainty: N/A"). If uncertainty data is missing, the ledger must explicitly record "Uncertainty: Not Reported in Source" for that entry, ensuring no silent assumption of zero error. This addresses the requirement for "measurement standards against which predictions will be tested."
- [X] T047 [P] [US3] **Rosalind Franklin Review Response**: Implement `code/analysis/explainability.py` to generate a **Conformational Variance Proxy Plot**. This task must visualize the distribution of `NumRotatableBonds` for molecules where the RF model deviates significantly (>2σ) from the Crippen baseline, explicitly labeling these regions as "Potential Conformational Artifacts." The plot must include a disclaimer that D fingerprints cannot resolve solution-phase ensembles, directly addressing the concern that "fingerprint weights correspond to physical interactions rather than statistical artifacts."
- [ ] T037 [P] **Code Quality**: Add docstrings to all public functions in `code/` (including `models/`, `analysis/`, and `data/`). **Verification**: Run `ruff --select D code/` to ensure compliance.
- [ ] T048 [P] **Marie Curie Review Response**: Implement `code/analysis/stats.py` to generate a **Measurement Standards Audit**. This task must explicitly list the **uncertainty bounds** (if available) or **explicitly state "Not Reported"** for every data point in the held-out test set used for validation. It must produce `data/derived/measurement_standards_audit.csv` with columns: `smiles`, `property`, `experimental_value`, `reported_uncertainty`, `uncertainty_source_status`. This ensures the validation protocol meets the requirement for "measurement standards against which predictions will be tested."
- [ ] T049 [P] **Rosalind Franklin Review Response**: Implement `code/analysis/explainability.py` to generate a **Conformational Ensemble Proxy Report**. This task must explicitly identify molecules where the **NumRotatableBonds > 10** heuristic suggests significant conformational flexibility and report the **RF prediction error** for these molecules compared to rigid molecules. The report must include a **qualitative assessment** of whether the 2D fingerprint method captures the "conformational ensemble" limitations, explicitly stating that the model cannot resolve solution-phase dynamics. This addresses the concern that "fingerprint weights correspond to physical interactions rather than statistical artifacts."

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T038 [P] Documentation updates in `docs/` including `quickstart.md` and `research.md`
- [ ] T040 Additional unit tests (if requested) in `tests/unit/`
- [ ] T041 Security hardening
- [ ] T042 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately. **T036 must complete before T019/T020**.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes T011.5 (Train/Test Split)**.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review Concerns (Phase 6)**: Can be parallelized with US1/US2/US3 implementation but must be integrated before final validation
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **Review Concerns (Phase 6)**: Must be implemented alongside US1/US2/US3 to ensure data integrity and validation protocols are in place before final analysis

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T036 which is [S])
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Reviewer concern tasks (Phase 6) can be parallelized with their respective user story implementations

### Critical Execution Blocks

- **T014 (Baseline)** and **T019 (Fingerprints)**: **MUST WAIT** for **T011.5 (Train/Test Split)** to complete. This is a hard dependency to prevent data leakage.
- **T021 (Wilcoxon Test)**: **MUST WAIT** for **T020.5 (OOF Persistence)** to complete.
- **T029 (Substructure Mapping)**: **MUST WAIT** for **T026 (SHAP Interaction Values)** to complete.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Unit test for Crippen's atomic contribution calculation in tests/unit/test_crippen.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to fetch a diverse dataset..."
Task: "Implement code/data/preprocess.py to filter for high-confidence measurements..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (including T036 configuration)
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 + Reviewer Concerns (Data Quality)
 - Developer B: User Story 2 + Reviewer Concerns (Validation Protocol)
 - Developer C: User Story 3 + Reviewer Concerns (Conformational Limitations)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential, must complete before dependent tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All data must be REAL from verified sources; NO fabrication or synthetic data allowed.
- **Critical**: All models must run on CPU-only free-tier runners; NO GPU or quantization.
- **Critical**: Address reviewer concerns explicitly in Phase 6 tasks (T033, T043-T045, T046, T047, T048, T049).
- **Critical**: Fingerprint generation MUST use `obabel` command-line tool (FR-003) via subprocess.
- **Critical**: Findings MUST be framed as associational correlations, not causal mechanisms (Assumptions).
- **Critical**: Diversity filtering MUST use a defined sampling strategy (MaxMin) to ensure feasibility (T010/T011). Target: **5000 molecules** (to allow 4000 train + 1000 test).
- **Critical**: Nested Cross-Validation MUST be implemented to ensure valid statistical testing (T019.5).
- **Critical**: Validation protocol (T011.5) must strictly separate training and test sets to prevent data leakage. Split: molecules training, 1000 molecules test.
- **Critical**: Conformational limitations (T033, T045, T047, T049) must be explicitly reported as a constraint of the 2D fingerprint method.
- **Critical**: Dataset size is fixed at a scale sufficient to ensure runtime feasibility and statistical power (a train/test split).
- **Critical**: Optional metadata fields (uncertainty, quantity) are logged as "Not Available" in metadata JSON based on **runtime schema validation** of the fetched data (T031), not hard-coded.
- **Critical**: Chemical rule validation uses valid RDKit features (Lipinski, steric descriptors via `rdMolDescriptors`), used as **topological proxies** for steric effects (T030).
- **Critical**: Measurement uncertainty and quantity of substance must be explicitly documented or noted as absent in the final report (T043, T044, T046, T048) to satisfy the requirement for experimental validation standards.
- **Critical**: Conformational sensitivity analysis (T045, T047, T049) must explicitly compare predictions for flexible molecules (NumRotatableBonds > 10) to highlight the limitations of 2D topological proxies.
- **Critical**: T036 (Performance Config) must be completed before T019 and T020 to ensure runtime constraints are applied.
- **Critical**: T030.1 must be completed before T030 to provide the required SMARTS patterns.
- **Critical**: T014 must process the full dataset to support T030; T014.5 extracts test set predictions for T021.
- **Critical**: T019 must NOT skip fingerprint generation; it must fail loudly if time constraints are exceeded.
- **Critical**: T021 must include conditional logic to handle the 50% experimental threshold.
- **Critical**: T008 must use PubChemPy as the data source.
- **Critical**: T009 must explicitly check for physical covariates (pH, temperature) and log them as missing if absent.
- **Critical**: T037 merges docstring tasks to reduce fragmentation.
- **Critical**: T048 and T049 explicitly address the "Measurement Standards" and "Conformational Ensemble" concerns raised by Marie Curie and Rosalind Franklin respectively, ensuring the validation protocol is robust and the limitations of 2D fingerprints are clearly communicated.