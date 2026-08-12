# Tasks: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

**Input**: Design documents from `/specs/001-predict-plant-disease-resistance/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Data Acquisition & Verification (FR-001, FR-014)

**Purpose**: Identify and verify public datasets with specific Study IDs before implementation begins.

- [ ] T012 [US1] **Execute** `code/research/verify_studies.py` to query the Metabolomics Workbench API for public studies containing 'plant disease' and 'metabolomics'. **Output**: Generate `data/raw/study_manifest.json` containing at least 2 valid Study IDs (e.g., `C-STUDY-XXXX`) and their metadata. **Hard Fail**: If no valid studies are found or `data/raw/study_manifest.json` is not created, raise `DataUnavailableError` and halt. **Do NOT use hardcoded placeholder IDs or synthetic data.** **Verification**: Confirm `data/raw/study_manifest.json` exists and contains valid JSON with Study IDs.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project directory structure (`code/`, `data/raw`, `data/processed`, `data/intermediate`, `tests/`, `state/`, `results/`, `results/plots`, `contracts/`).
- [ ] T001b [P] **Execute** verification that all directories created in T001a exist and are writable. Run `ls -R` and capture output to verify structure.
- [ ] T002 [P] Initialize a Python project with pinned dependencies in `requirements.txt` (pandas, numpy, scikit-learn, statsmodels, requests, pytest, pyyaml, joblib, pydantic).
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `.pre-commit-config.yaml`. **Create the file with valid YAML syntax including hooks for black, flake8, and isort, and verify pre-commit hooks install successfully.**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/constants.py` with random seeds (`random_state=42`), file paths, and hypothesis thresholds (Balanced Acc > 0.75). **Define `HOLD_OUT_FRACTION = 0.20` for T020.**
- [ ] T005 [P] Implement `code/utils/io.py` for checksumming (MD5/SHA256) and logging artifacts to `state/artifact_hashes.yaml`
- [ ] T006a [P] Create `contracts/metadata.schema.yaml` defining `MetaboliteProfile` and `ResistanceLabel` schemas (Mandatory for Constitution Principle III). **Write the file with the following content:**
 ```yaml
 $schema: http://json-schema.org/draft-07/schema#
 type: object
 properties:
   MetaboliteProfile:
     type: object
     properties:
       sample_id: {type: string}
       InChIKey: {type: string}
       normalized_intensity: {type: number}
       study_id: {type: string}
     required: [sample_id, InChIKey, normalized_intensity]
   ResistanceLabel:
     type: object
     properties:
       germplasm_id: {type: string}
       assay_score: {type: number}
       measurement_method: {type: string}
       harmonized_score: {type: number}
     required: [germplasm_id, assay_score, harmonized_score]
 ```
- [ ] T006b [P] **Execute** validation of `contracts/metadata.schema.yaml` using `jsonschema` or `yamllint` to ensure schema validity.
- [ ] T007a [P] Create `contracts/output.schema.yaml` defining `metrics.json` and `shap_analysis.json` structures (Mandatory for Constitution Principle III). **Write the file with the following content:**
 ```yaml
 $schema: http://json-schema.org/draft-07/schema#
 type: object
 properties:
   metrics:
     type: object
     properties:
       balanced_accuracy: {type: number}
       roc_auc: {type: number}
       permutation_p_value: {type: number}
     required: [balanced_accuracy, roc_auc, permutation_p_value]
   shap_analysis:
     type: object
     properties:
       top_features:
         type: array
         items:
           type: object
           properties:
             feature_name: {type: string}
             shap_value: {type: number}
           required: [feature_name, shap_value]
       collinearity_vif:
         type: array
         items:
           type: object
           properties:
             feature_name: {type: string}
             vif_value: {type: number}
           required: [feature_name, vif_value]
       framing: {type: string}
     required: [top_features, framing]
 ```
- [ ] T007b [P] **Execute** validation of `contracts/output.schema.yaml` using `jsonschema` or `yamllint` to ensure schema validity.
- [ ] T008 [P] Setup `tests/unit/` structure and `pytest.ini` configuration

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, normalize, align, and harmonize public metabolomics datasets from Metabolomics Workbench containing pre-challenge profiles and resistance metadata.

**Independent Test**: Verify data downloads (≥2 studies), normalization outputs (log-transformed, missing >30% discarded), label harmonization (z-scoring), and batch-effect correction (ComBat) via script execution.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for `code/data/download.py` verifying Metabolomics Workbench HTTP fetch and file storage in `tests/unit/test_download.py`
- [ ] T010 [P] [US1] Unit test for `code/data/validate_temporal.py` verifying timestamp checks in `tests/unit/test_temporal.py`
- [ ] T011 [P] [US1] Integration test for full preprocessing pipeline (download → validate → preprocess → harmonize) in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/data/validate_temporal.py` to verify FR-014: **Explicitly check metadata for 'pre-challenge', 'baseline', or timestamps prior to pathogen inoculation. If metadata lacks these, raise `TemporalVerificationError` and halt the pipeline for that study. Do NOT skip.**
- [ ] T014 [US1] Implement `code/data/harmonize_labels.py` to encode resistance as binary/ordinal and apply z-scoring or stratification (FR-003, FR-013). **Ensure `binary_label` is passed to the trainer and `harmonized_score` is used ONLY for exploratory correlation.**
- [ ] T015 [US1] Implement `code/data/preprocess.py` to:
 - Log-transform intensities and discard features missing >30% (FR-002)
 - Align metabolites via InChIKey across studies
 - Perform covariate residualization for biological confounders
 - Apply ComBat batch-effect correction when ≥2 studies are combined (FR-004)
 - **Handle InChIKey alignment failures**: Log missing metabolites to `results/alignment_missing.json` and proceed with the intersection of aligned metabolites.
- [ ] T016 [US1] Add logging for data acquisition and preprocessing steps to `code/utils/io.py`
- [ ] T017 [US1] **Execute** `code/data/preprocess.py` to generate `data/processed/batch_corrected_matrix.csv` and `data/processed/labels.csv` (Mandatory for Data Hygiene; T020 depends on this completion). **Verify file existence, non-empty content, and record SHA256 checksums in `state/artifact_hashes.yaml`. If files are missing or empty, raise an error and halt.** <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train a constrained Random Forest classifier with rigorous stratified cross-validation, permutation testing, and sensitivity analysis to test the predictive relationship without circular validation.

**Independent Test**: Verify balanced accuracy on hold-out set, feature selection within CV folds, permutation testing (≥1000), FDR correction, and sensitivity analysis sweeps.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for `code/modeling/train.py` verifying stratified split and hold-out reservation (FR-006) in `tests/unit/test_modeling.py`
- [ ] T019 [P] [US2] Unit test for `code/modeling/evaluate.py` verifying permutation distribution generation in `tests/unit/test_modeling.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/modeling/train.py` to:
 - **Split data into train/hold-out using stratified sampling on binary_label BEFORE any feature selection or scaling. This split MUST occur BEFORE the GridSearchCV loop begins to satisfy FR-006.**
 - Output `train_indices` and `holdout_indices` lists to `data/processed/split_indices.json`.
 - Train Random Forest (n_estimators=500, max_depth=10) with Stratified k-fold CV (FR-005)
 - Perform GridSearchCV within the CV loop with `param_grid={'max_depth': [low, medium, high]}` (tunable up to 20)
 - **Dependency**: Requires T017 completion.
- [ ] T021a [US2] Implement `code/modeling/evaluate.py` (Correlation Analysis):
 - **Filter input data to ONLY the training subset (using `train_indices` from T020).**
 - Compute pairwise correlations (metabolite vs. resistance) on the **training data only**.
 - Apply Benjamini-Hochberg FDR correction (≤0.05) to p-values (FR-008, SC-002).
 - Filter for |r| > 0.4, p < 0.01.
 - Output to `results/shap_analysis.json` (partial).
 - **Dependency**: Requires T020 completion.
- [ ] T021b [US2] Implement `code/modeling/evaluate.py` (Model Validation):
 - **Execute Learning Curve Analysis unconditionally for ALL runs.**
 - If the resulting curve indicates insufficient power (N < 50), flag power limitation in the report.
 - Compute Balanced Accuracy, ROC-AUC, Precision-Recall on the independent hold-out set (SC-001) using `holdout_indices` from T020.
 - **Execute permutation testing on the trained model from T020 with exactly n_permutations=1000 to generate the null distribution and assess significance (FR-007, SC-003).**
 - Perform Sensitivity Analysis sweeping decision cutoffs over a range of absolute diff values. and report FP/FN rates (FR-009, SC-005).
 - **Dependency**: Requires T020 and T021a completion.
- [ ] T022 [US2] **Execute** collinearity diagnostics (VIF calculation) for selected metabolites using `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Must run after T020. Flag VIF > 5 and save results to `data/intermediate/vif_scores.json` (Mandatory per FR-012). Verify file existence and non-empty content.**
- [ ] T024 [US2] **Execute** generation of `results/metrics.json` and `results/shap_analysis.json` by aggregating results from T021a, T021b, and T022. **Read VIF scores from `data/intermediate/vif_scores.json`. Include the mandatory "framing" field set to "associational" with the exact string: "These results represent associations, not causation" (FR-011). Verify JSON validity and presence of required keys (balanced_accuracy, permutation_p_value, framing).**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Biological Interpretation and Pathway Mapping (Priority: P3)

**Goal**: Extract feature importances and map top metabolites to known pathways via KEGG/MetaCyc to assess biological plausibility.

**Independent Test**: Verify top metabolites are extracted, mapped to ≥1 pathway each, and documented with literature references.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for `code/modeling/interpret.py` verifying pathway mapping logic in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/modeling/interpret.py` to:
 - Extract top-ranked metabolites ranked by **mean decrease in impurity (feature_importances_)** from the trained Random Forest model (FR-010).
 - Map metabolites to KEGG/MetaCyc pathways using the KEGG REST API (no auth) or InChIKey lookups. **Fallback**: If KEGG fails, use MetaCyc.
 - Generate interpretation report discussing biological plausibility (e.g., phytoalexins, phenolics).
 - **Dependency**: Requires trained model from T020 and T024.
- [ ] T027 [US3] Save pathway mapping results to `results/pathway_analysis.json`. **Include fields: metabolite_id, pathway_name, database_source (KEGG/MetaCyc). Ensure the "framing" field is set to "associational" with the exact string: "These results represent associations, not causation" (FR-011).**
- [ ] T028 [US3] **Execute** generation of visualization `results/plots/pathway_barplot.png` using `matplotlib` (via `seaborn`) based on data from `results/pathway_analysis.json`. **Plot the most prominent pathways by frequency/importance. Save as PNG with high resolution. Verify file existence and non-empty content.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Update `README.md` with execution instructions and `quickstart.md` validation
- [ ] T030 [P] Run full pipeline integration test on GitHub Actions free-tier (verify ≤6h runtime, ≤7GB RAM) <!-- ATOMIZE: requested -->
- [ ] T031 [P] Code cleanup and refactoring based on linting feedback
- [ ] T033 [P] Verify `state/artifact_hashes.yaml` tracks all data and model artifacts correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data IDs)**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Phase 0 completion (requires study IDs)
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires processed data from T017)
- **User Story 3 (P3)**: Depends on US2 completion (requires trained model and metrics)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (or data loaders before processing scripts)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (if dependencies allow)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for download.py in tests/unit/test_download.py"
Task: "Unit test for temporal validation in tests/unit/test_temporal.py"

# Launch all data scripts for User Story 1 together (if independent):
Task: "Implement download.py"
Task: "Implement harmonize_labels.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data IDs
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (data pipeline works)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Modeling added)
4. Add User Story 3 → Test independently → Deploy/Demo (Interpretation added)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling - can start once data schema is defined)
 - Developer C: User Story 3 (Interpretation - can start once model schema is defined)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (limited cores, constrained RAM). No GPU/CUDA, no 8-bit/4-bit quantization, no deep learning. Use `scikit-learn` Random Forest only.
- **Data Integrity**: Do not fabricate data. Use real Metabolomics Workbench datasets. If data is unavailable, halt with "Data Unavailable" error.
- **Execution Order**: Ensure T012 (Verify IDs) completes before T013/T014/T015. Ensure T017 (Generate processed data) completes before T020. Ensure T021a (Training Correlations) runs before T021b (Hold-out Evaluation). Ensure T022 (VIF), T024 (Logging), and T026 (Interpret) are executed in sequence to produce final artifacts.