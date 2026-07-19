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
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create `projects/PROJ-324-predicting-molecular-properties-from-ope/` directory structure
- [ ] T001b Create `code/`, `data/`, `tests/` subdirectories
- [ ] T001c Create `data/raw`, `data/processed`, `data/derived` subdirectories
- [X] T002 Initialize Python 3.10+ project with `requirements.txt` (rdkit, scikit-learn, shap, pandas, numpy, datasets, requests, obabel-wrapper)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data download, preprocessing, and the critical train/test split.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create base `code/__init__.py` and utility modules for logging and seed management
- [X] T008 [P] [US1] Implement `code/data/download.py` to fetch a diverse dataset from `molecule-net/thermodynamics` (exact ID) with SMILES and experimental logP, solubility, boiling point, ensuring real data only. Target: A substantial collection of molecules.
- [ ] T009 [P] [US1] Implement `code/data/preprocess.py` to filter for high-confidence measurements, handle missing values, detect missing covariates (e.g., temperature, pH), and log excluded entries to `data/derived/data_quality_report.csv` with a `missing_covariate` column (addressing FR-008). The report schema must strictly include columns: `smiles`, `exclusion_reason`, `missing_covariate_list`.
- [X] T010 [P] [US1] Implement `code/data/preprocess.py` to define the **MaxMin sampling strategy** for calculating Tanimoto similarity. This task must define the algorithm to select a diverse subset (Tanimoto < 0.7) from the preprocessed data. **Constraint**: Target a final diverse set of **[deferred] molecules** (reduced from the initial fetch) to ensure O(N) feasibility on the 2-core runner within 6 hours. The algorithm must select the maximum subset satisfying the diversity constraint or the full set if <5,000 exist.
- [ ] T011 [US1] Implement `code/data/preprocess.py` to **execute** the diversity filtering using the strategy defined in T010, producing the final diverse dataset of **[deferred] molecules**. This task consumes the output of T009.
- [ ] T011.5 [US1/US2] Implement `code/data/preprocess.py` to **split** the diverse dataset into a training set (**[deferred] molecules**) and a strictly held-out test set (**[deferred] molecules**). This task must ensure the split is random, stratified (if possible), and reproducible via random seed. Output `data/derived/train_set.csv` and `data/derived/test_set.csv`. *This task is critical for the Validation Protocol (FR-005) and must be completed after T009 and T010. (Note: Not [P] due to dependency on T009/T010).*
- [X] T031 [P] [US1/US2] Enhance `code/data/download.py` (T008) to explicitly document the **experimental source**, **measurement conditions** (e.g., temperature, pH if available), and **source confidence** in the dataset metadata (`data/raw/dataset_metadata.json`). **CRITICAL**: Perform a runtime schema check for the presence of `measurement_uncertainty` and `quantity_of_substance` fields. If absent, the code MUST derive and record `"measurement_uncertainty_status": "Not Available in Source"` and `"quantity_of_substance_status": "Not Available in Source"` based on the actual fetched schema, not hard-coded strings. This validates data hygiene immediately upon ingestion.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Error Quantification (Priority: P1) 🎯 MVP

**Goal**: Generate a baseline prediction for logP, solubility, and boiling point using Crippen's additive fragment model and quantify the error against real experimental data on the **held-out test set**.

**Independent Test**: Can be fully tested by running the Crippen's additive fragment algorithm on the provided dataset and outputting a CSV of predicted vs. experimental values with a calculated Mean Absolute Error (MAE).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [X] T013 [P] [US1] Unit test for Crippen's atomic contribution calculation in `tests/unit/test_crippen.py`

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/models/baseline.py` to compute Crippen's atomic contributions for all molecules in the **held-out test set**, outputting `data/derived/baseline_predictions.csv`.
- [ ] T015 [US1] Implement `code/analysis/stats.py` to calculate MAE/RMSE for baseline predictions **on the held-out test set** and generate residual distribution plots (`data/derived/baseline_residuals.png`).
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

- [X] T019 [US2] Implement `code/data/fingerprints.py` to generate Open Babel fingerprints (MACCS, ECFP4, FP2) by **invoking the `obabel` command-line tool via subprocess** (per FR-003). This task must prioritize ECFP4 > MACCS > FP2 to manage runtime (FR-009) and consume the **training set** from T011.5. *Dependency: Must wait for T011.5 completion. [P] indicates parallel execution with other Phase 4 tasks once Phase 2 is done.* It must produce the `fingerprints.parquet` artifact.
- [X] T019.5 [US2] Implement `code/models/random_forest.py` to set up **Nested Cross-Validation** (outer loop for test set, inner loop for hyperparameter tuning) to generate valid error pairs for statistical testing, as required by the Plan's Complexity Tracking section.
- [X] T020 [US2] Implement `code/models/random_forest.py` to train RF regressors using the Nested CV structure (T019.5) with hyperparameter tuning via 3-fold cross-validation **on the training set**, ensuring `max_depth` limits (≤15) and dataset sampling to fit CPU constraints (FR-004). This task must produce a `final_model.pkl` artifact trained on the full training set for downstream SHAP analysis.
- [X] T021 [US2] Implement `code/analysis/stats.py` to perform paired Wilcoxon signed-rank test on absolute errors (Baseline vs. RF) using the valid error pairs from the **held-out test set** and report p-values (FR-005).
- [ ] T022 [US2] Implement `code/analysis/stats.py` to generate comparison plots (Baseline vs. RF MAE/RMSE) **using the held-out test set** and save to `data/derived/model_comparison.png`.
- [X] T023 [US2] Implement `code/models/random_forest.py` to include a runtime monitor that automatically reduces dataset size or skips lower-priority fingerprints if the 6-hour limit is approached (per Edge Cases).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, providing a statistically significant comparison.

---

## Phase 5: User Story 3 - Interaction Zone Mapping (Priority: P3)

**Goal**: Identify specific fingerprint bit pairs contributing to error reduction using SHAP values, map them to chemical substructures, and validate against known chemical rules (using RDKit built-ins).

**Independent Test**: Can be fully tested by generating SHAP summary plots, interaction strength heatmaps, and mapping the top interacting fingerprint bits back to chemical substructures using RDKit.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for interaction context schema in `tests/contract/test_interaction_schema.py`
- [X] T025 [P] [US3] Unit test for SHAP bit-to-substructure mapping in `tests/unit/test_shap_mapping.py`

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis/explainability.py` to calculate SHAP interaction values for the trained RF model (T020) using the `final_model.pkl` artifact (FR-006). *Dependency: Requires T020 completion. [P] indicates parallel execution with other Phase 5 tasks once Phase 4 is done.*
- [ ] T027 [US3] Implement `code/analysis/explainability.py` to generate heatmaps of top interacting fingerprint bit pairs and save to `data/derived/shap_interactions.png`.
- [ ] T028 [US3] Implement `code/analysis/explainability.py` to calculate the Jaccard similarity of identified sets across thresholds **using exactly 100 bootstrap resamples** of the test set and report results to `data/derived/stability_analysis.csv` to assess the stability of top interacting bits. *Note: This is a diagnostic validation step to ensure the robustness of the SHAP findings, not a new primary success criterion.*
- [ ] T029 [US3] Implement `code/analysis/explainability.py` to map top interacting bits back to chemical substructures using RDKit, outputting `data/derived/deviation_contexts.csv` (FR-007).
- [ ] T030 [US3] Implement `code/analysis/explainability.py` to cross-reference identified substructures with **RDKit's built-in functional group detection** (`rdkit.Chem.Fragments`) and **steric descriptors** (`rdkit.Chem.rdMolDescriptors` - e.g., Molecular Weight, TPSA, NumRotatableBonds) to distinguish physical phenomena from statistical artifacts (FR-010). *Note: Steric descriptors are used as **topological proxies** for steric effects, consistent with the Plan's disclaimer that 2D fingerprints cannot capture true 3D steric hindrance.*
- [ ] T039 [US3] Implement `code/analysis/explainability.py` to explicitly frame findings as **associational** correlations, not causal mechanisms, in the output report (per Assumptions).

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Reviewer Concerns & Data Integrity (Revision Tasks)

**Purpose**: Address specific feedback from Marie Curie (simulated) and Rosalind Franklin (simulated) regarding experimental validation, measurement uncertainty, and conformational limitations.

- [ ] T033 [P] [US3] Implement `code/analysis/explainability.py` to generate a "Conformational Limitation Report" that identifies molecules where 2D topology (fingerprints) likely fails to capture solution-phase conformational ensembles. **Method**: Use a spatial proxy heuristic (e.g., detecting specific steric clash patterns in the SMILES graph or high ring strain indicators) to flag potential 3D failures, addressing Rosalind Franklin's concern on static vs. dynamic structures.
- [ ] T043 [P] [US1/US2/US3] **Marie Curie Review Response**: Implement `code/analysis/stats.py` to generate a **Validation Protocol Summary** in the final report. This task must **explicitly state the absence** of `measurement_uncertainty` and `quantity_of_substance` data if T031 detected these fields as missing. It must NOT attempt to extract non-existent data, but rather report the source limitation as a derived fact. This task aggregates the metadata findings from T031 to ensure the final report reflects the actual state of the data.
- [ ] T044 [P] [US1/US2/US3] **Marie Curie Review Response**: Enhance `code/analysis/stats.py` to include a **Validation Protocol Summary** section in the final report. This section must explicitly state the **held-out test set size**, the **source of experimental values** for the test set, and the **measurement uncertainty** (or lack thereof) for the target properties, ensuring the model's output is framed as a comparison against verified experimental data, not just cross-validation scores.
- [ ] T045 [P] [US3] **Rosalind Franklin Review Response**: Implement `code/analysis/explainability.py` to generate a **Conformational Sensitivity Analysis**. This task must compare the RF predictions against a set of molecules known to have high conformational flexibility (e.g., long aliphatic chains) and report the **deviation magnitude** for these specific cases. The report must explicitly state that the model's "substructure" findings are **topological proxies** and may not reflect solution-phase conformational ensembles, addressing the concern that fingerprints are topological abstractions.
- [ ] T036 [P] Implement specific performance optimizations: limit Random Forest `max_depth` to 15, use `joblib` for parallel fingerprint generation, and implement a 5-minute timeout check for the `obabel` subprocess to ensure ≤6h runtime.
- [ ] T037 [P] Code cleanup: ensure type hints in all modules, remove unused imports, and add docstrings to all public functions.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` including `quickstart.md` and `research.md`
- [ ] T040 Additional unit tests (if requested) in `tests/unit/`
- [ ] T041 Security hardening
- [ ] T042 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
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

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Reviewer concern tasks (Phase 6) can be parallelized with their respective user story implementations

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

1. Complete Phase 1: Setup
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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All data must be REAL from verified sources; NO fabrication or synthetic data allowed.
- **Critical**: All models must run on CPU-only free-tier runners; NO GPU or quantization.
- **Critical**: Address reviewer concerns explicitly in Phase 6 tasks (T033, T043-T045).
- **Critical**: Fingerprint generation MUST use `obabel` command-line tool (FR-003) via subprocess.
- **Critical**: Stability analysis MUST calculate and report Jaccard similarity using exactly 100 bootstrap resamples (T028). *Note: This is a diagnostic, not a primary success criterion.*
- **Critical**: Findings MUST be framed as associational correlations, not causal mechanisms (Assumptions).
- **Critical**: Diversity filtering MUST use a defined sampling strategy (MaxMin) to ensure feasibility (T010/T011). Target: [deferred] molecules.
- **Critical**: Nested Cross-Validation MUST be implemented to ensure valid statistical testing (T019.5).
- **Critical**: Validation protocol (T011.5) must strictly separate training and test sets to prevent data leakage. Split: A substantial training set and a smaller test set.
- **Critical**: Conformational limitations (T033, T045) must be explicitly reported as a constraint of the 2D fingerprint method.
- **Critical**: Dataset size is fixed at a scale sufficient to ensure runtime feasibility and statistical power.
- **Critical**: Optional metadata fields (uncertainty, quantity) are logged as "Not Available" in metadata JSON based on **runtime schema validation** of the fetched data (T031), not hard-coded.
- **Critical**: Chemical rule validation uses valid RDKit features (Lipinski, steric descriptors via `rdMolDescriptors`), used as **topological proxies** for steric effects (T030).
- **Critical**: Measurement uncertainty and quantity of substance must be explicitly documented or noted as absent in the final report (T043, T044) to satisfy the requirement for experimental validation standards.
- **Critical**: Conformational sensitivity analysis (T045) must explicitly compare predictions for flexible molecules to highlight the limitations of 2D topological proxies.