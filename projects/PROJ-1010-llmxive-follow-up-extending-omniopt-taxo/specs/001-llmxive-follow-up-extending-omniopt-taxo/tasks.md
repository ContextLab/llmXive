# Tasks: llmXive follow-up: extending "OmniOpt: Taxonomy, Geometry, and Benchmarking of Modern Optimizers"

**Input**: Design documents from `/specs/001-spectral-optimizer-prediction/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project directory structure: `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/`, `code/`, `data/`, `tests/`, `state/`
- [ ] T001b [P] Create code subdirectories: `code/utils/`, `code/data/`, `code/analysis/`
- [ ] T001c [P] Create test subdirectories: `tests/unit/`, `tests/integration/`
- [ ] T002a [P] Create `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/requirements.txt` with pinned dependencies: `torch`, `transformers`, `scikit-learn`, `datasets`, `numpy`, `scipy`, `pandas`, `pyyaml`, `pytest`
- [ ] T002b [P] Verify Python 3.11+ availability in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement seed pinning utility in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/utils/seeds.py`
- [X] T005 [P] Implement structured logging utility in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/utils/logging.py`
- [X] T006 [P] Implement memory monitoring utility in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/utils/memory_monitor.py`
- [ ] T007 Create base data directory structure (`data/raw/`, `data/processed/`, `data/omniopt_lookup.json`) and state tracking in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/`
- [X] T008 Setup environment configuration management for dataset paths and OmniOpt lookup source in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/.env.example`
- [X] T009 [P] Implement data streaming loader for TinyImageNet/C4 using `datasets.load_dataset(..., streaming=True)` in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/utils/data_loader.py` (FAIL LOUDLY on missing real source)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Proxy Data Preparation and Gradient Spectral Extraction (Priority: P1) 🎯 MVP

**Goal**: Generate a dataset of spectral signatures from initial gradient covariance matrices for diverse small-scale models.

**Independent Test**: The system can be tested by running the extraction pipeline on a single architecture (e.g., ResNet) on a subset of TinyImageNet and verifying that a valid JSON/CSV file containing the spectral feature vector and the model identifier is produced within a reasonable time limit on a CPU-only runner.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for numerical stability of eigenvalue decomposition (handling singular matrices) in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/tests/unit/test_spectral_extractor.py` (Depends on T001-T006 structure)
- [~] T011 [P] [US1] Unit test for streaming data loader failure behavior (must raise, not fallback) in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/tests/unit/test_data_loader.py` (Depends on T001-T006 structure)

### Implementation for User Story 1

- [~] T012 [US1] Implement `spectral_extractor.py` in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/` to compute gradient covariance from first 100 steps of proxy training. **Model Selection**: Select a representative sample of models from HuggingFace model hub matching: parameter_count M-50M, architecture type in [ResNet, MobileNet, EfficientNet, ViT-Base]. Use TinyImageNet (a subset of samples).
- [X] T013 [US1] Implement spectral feature extraction in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/spectral_extractor.py`: Calculate **Spectral Radius**, **Condition Number**, and **Tail Decay Exponent** (via power-law fitting via MLE on top-50 eigenvalues) per **FR-002** requirement. Handle numerical stability (regularization) for singular matrices.
- [X] T013b [US1] Implement **Spectral Entropy** calculation in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/spectral_extractor.py`: Compute Shannon entropy of the normalized eigenvalue distribution (Formula: `-sum(p * log2(p))`) as the robust research metric per plan.md Complexity Tracking.
- [ ] T013c [US1] Write extracted `SpectralFeatureVector` records (including both Tail Decay and Entropy) to `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/data/processed/spectral_features.csv`
- [X] T014 [US1] Implement robust error handling in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/spectral_extractor.py` to log and exclude samples that fail to converge or produce NaN/Inf values
- [X] T015 [US1] Implement memory-efficient gradient accumulation and covariance computation to ensure < 7GB peak RAM usage in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/spectral_extractor.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Ground Truth Labeling and Dataset Construction (Priority: P2)

**Goal**: Map the extracted spectral signatures to the "optimal mechanism family" ground truth labels derived from the OmniOpt benchmark results.

**Independent Test**: The system can be tested by loading the OmniOpt benchmark results (or the pre-computed lookup table) and merging them with the spectral feature dataset. The test passes if every spectral feature vector is successfully paired with a categorical label.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for label mapping logic and handling of missing/unlabeled entries in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/tests/unit/test_label_mapper.py` (Depends on T019 implementation)
- [ ] T018 [P] [US2] Integration test for the two-tier ground truth protocol (Paper Tables primary, Re-run secondary) in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/tests/integration/test_label_mapping.py` (Depends on T019 and T020 implementation)

### Implementation for User Story 2

- [ ] T019 [US2] Implement `label_mapper.py` in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/` to load static OmniOpt lookup table from `data/omniopt_lookup.json`
- [ ] T020b [US2] Create `data/omniopt_config.yaml` with configuration parameters for benchmark re-runs (model list, hyperparameters, timeout limits)
- [ ] T020 [US2] Implement fallback mechanism in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/re_run_omniopt_subexperiment.py`: **Trigger**: If lookup returns null for a model in the 20 selected. **Config**: Use `data/omniopt_config.yaml`. **Timeout**: 45 mins per re-run.
- [ ] T021 [US2] Implement logic to map `OptimalMechanismLabel` (e.g., "Adam", "SGD", "Lion") to spectral features, flagging and excluding samples with ambiguous ties or missing data
- [ ] T022 [US2] Perform dataset sanity check in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/label_mapper.py`:
 1. **Global Shannon Entropy**: Must be > 1.5 bits (Calculation: `-sum(p * log2(p))` on label distribution).
 2. **Class Balance**: Minimum 3 samples per class.
 3. Write final `labeled_dataset.json` to `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/data/processed/`
- [ ] T022b [US2] Implement **SC-005 Verification** in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/label_mapper.py`:
 1. Count total diverse architectures (Must be >= 20).
 2. Verify distinct optimizer families (Must be >= 5).
 3. Verify max class percentage (No single family > 50%).
 4. **Action**: Raise `ValueError` if any constraint fails; Log pass/fail status.
- [ ] T023 [US2] Log all exclusion reasons and exclusion counts to `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/data/processed/exclusion_log.txt`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Model Training and Validation (Priority: P3)

**Goal**: Perform a Spearman Rank Correlation analysis AND train a Classification model to predict the optimal optimizer family from spectral features and validate its performance.

**Independent Test**: The system can be tested by computing the Spearman correlation coefficient on the labeled dataset and evaluating it using a permutation test. The test passes if the model produces a correlation coefficient and a p-value without exceeding memory limits.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for permutation test implementation (null distribution construction) in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/tests/unit/test_correlation_analyzer.py`
- [ ] T025 [P] [US3] Integration test for full pipeline correlation analysis and significance testing in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `correlation_analyzer.py` in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/` to perform **Spearman Rank Correlation** analysis (Research Primary Metric) on the labeled dataset. **Validation**: Use **Leave-One-Out Cross-Validation (LOOCV)** to handle N<20. Output mean correlation coefficient (rho) and standard deviation.
- [ ] T026b [US3] Implement **Classification Model** in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/correlation_analyzer.py`: Train a **Logistic Regression** model to map spectral features to optimal mechanism family per **FR-004** (Spec Mandate). **Validation**: Use 5-fold cross-validation. Output prediction accuracy and macro-F1 score.
- [ ] T027 [US3] Implement statistical significance testing in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/correlation_analyzer.py`: Perform permutation test with **10,000 permutations**. **Null Hypothesis**: There is no monotonic relationship between spectral features and mechanism performance (rho = 0). Calculate p-value (Threshold: p < 0.05).
- [ ] T027b [US3] Implement statistical significance testing for classification in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/correlation_analyzer.py`: Perform permutation test on classification accuracy (sufficient permutations) to assess significance of the classification model (FR-004).
- [ ] T028 [US3] Implement generalization correlation reporting on a hold-out set of unseen architectures in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/correlation_analyzer.py`
- [ ] T029 [US3] Generate `results.json` containing mean Spearman correlation coefficient (rho), standard deviation, and p-values in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/data/processed/results.json`
- [ ] T029b [US3] Append **Classification Metrics** to `results.json`: Report **Prediction Accuracy** (vs baseline + 5% threshold per **SC-001**), Macro-F1 score, and classification p-value.
- [ ] T030 [US3] Implement hard runtime limit enforcement using `signal.alarm`, establishing a maximum execution duration to ensure timely completion of the analysis. in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/main_pipeline.py`; behavior on timeout: save partial state to `data/processed/partial_results.json` then raise `RuntimeError`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/specs/001-spectral-optimizer-prediction/quickstart.md` (update with spectral entropy, tail decay, Spearman, and Classification methods)
- [ ] T032 [P] Audit dependencies and update `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/requirements.txt` to remove unused dependencies based on audit
- [ ] T033 [P] Implement sparse eigenvalue decomposition using `scipy.sparse.linalg.eigsh` in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/spectral_extractor.py` to target <15 mins per decomposition. **Note**: This is a refactor of T012/T013 and must be performed AFTER T013 is verified.
- [ ] T034 [P] Additional unit tests for edge cases (singular matrices, empty datasets) in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/tests/unit/`
- [ ] T035a [P] Implement path validation (prevent `..` traversal) in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/utils/data_loader.py`
- [ ] T035b [P] Implement input sanitization for all data paths in `projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/code/utils/data_loader.py`
- [ ] T036 Run quickstart.md validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs spectral features as input)
- **User Story 3 (P3)**: Depends on US2 completion (needs labeled dataset as input)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Utilities/Foundational code before implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories cannot run in parallel due to data flow dependencies (US1 -> US2 -> US3)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for numerical stability of eigenvalue decomposition"
Task: "Unit test for streaming data loader failure behavior"

# Launch all models for User Story 1 together:
Task: "Implement spectral_extractor.py"
Task: "Implement memory-efficient gradient accumulation"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify spectral features are extracted and saved)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Labeled dataset ready)
4. Add User Story 3 → Test independently → Deploy/Demo (Correlation analysis + Classification ready)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Extraction)
 - Developer B: User Story 2 (Labeling) - *Must wait for US1 output*
 - Developer C: User Story 3 (Analysis) - *Must wait for US2 output*
3. Stories complete and integrate sequentially due to data flow

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Do NOT fabricate data; use `datasets.load_dataset(..., streaming=True)` for real data.
- **Critical**: **Dual Metric Implementation**: T013 implements "Tail Decay" (Spec FR-002); T013b implements "Spectral Entropy" (Plan). T026 implements Spearman (Plan); T026b implements Classification (Spec FR-004). Both paths are delivered.
- **Critical**: **SC-005 Verification**: T022b performs the final diversity check (min 20, 5 families, <50% max) on the labeled dataset.
- **Critical**: **LOOCV**: T026 uses Leave-One-Out Cross-Validation for robustness on N<20.
- **Critical**: **OmniOpt Labels**: Must come from static table or re-run; no heuristics.