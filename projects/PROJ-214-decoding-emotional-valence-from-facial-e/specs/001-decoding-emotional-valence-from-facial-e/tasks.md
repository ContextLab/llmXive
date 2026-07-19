# Tasks: Decoding Emotional Valence from Facial EMG Patterns with Machine Learning

**Input**: Design documents from `/specs/001-decoding-emotional-valence-from-facial-emg/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

## Plan Deviation Log

**Purpose**: Explicitly document deviations from the Spec to satisfy scientific validity and plan constraints.

1. **FR-005 Cross-Validation**: Spec requires "nested 5-fold cross-validation". Plan implements **Nested Leave-One-Subject-Out (LOSO)**.
 * *Justification*: N=32 subjects yields insufficient test subjects (~6) in 5-fold CV for robust generalization error estimation. [UNRESOLVED-CLAIM: c_3d297a89 — status=not_enough_info] LOSO is the standard for N=32 to maximize test set representation.
2. **FR-005/FR-007 Model Strategy**: Spec mandates Random Forest for all variance analysis. Plan implements **Dual Model Strategy (Random Forest + Logistic Regression)**.
 * *Justification*: Nagelkerke's R² is mathematically undefined for Random Forests. [UNRESOLVED-CLAIM: c_ae54984d — status=not_enough_info] Logistic Regression is required to calculate this metric scientifically.
3. **FR-001 Dataset URL**: Spec URL contained SSL error artifacts. Plan uses verified HuggingFace source (`emre-ozgür/DEAP-EMG`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create `code/` and `tests/` directories at repository root
- [ ] T001b [P] Create `data/raw`, `data/processed`, `data/models` directories at repository root

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, scipy, scikit-learn, pandas, joblib, shap, requests, scikit-learn-extra, pytest, pytest-cov)
- [ ] T003a [P] Create `.ruff.toml` configuration file for linting
- [ ] T003b [P] Create `.black.toml` configuration file for formatting

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with paths, hyperparameters, random seeds, and DEAP dataset metadata
- [ ] T005a [P] Create `code/download.py` to fetch the official DEAP dataset from the verified HuggingFace source (`emre-ozgür/DEAP-EMG`), extract specific EMG channels (corrugator, zygomaticus, orbicularis), and save to `data/raw/` (FR-001 part 1)
- [X] T005c [P] **Implement the `state` file update logic**: Create a utility function in `code/config.py` or a dedicated `code/state_manager.py` to initialize, read, and update the file at `state/projects/PROJ-214-decoding-emotional-valence-from-facial-e.yaml`. This function MUST create the file if missing, ensure the `artifact_hashes` map structure exists (as mandated by Constitution Principle V), and provide a method to record new checksums. (Constitution Principle V)
- [ ] T005b [P] Implement checksum generation for downloaded DEAP dataset files and record the checksums in the project's `state` file at `state/projects/PROJ-214-decoding-emotional-valence-from-facial-e.yaml` under the key `artifact_hashes` to satisfy FR-001 integrity validation (FR-001 part 2). **Depends on T005c**. (Constitution Principle III)
- [X] T006 [P] Create `code/preprocessing.py` stubs for filtering, windowing, and feature extraction logic (FR-002, FR-003, FR-004)
- [X] T007 Create `code/train.py` stub for nested LOSO pipeline and model bundling (FR-005)
- [X] T008 Create `code/importance.py` stub for permutation importance and SHAP analysis (FR-006)
- [X] T009 Create `code/validate.py` stub for permutation tests and sensitivity analysis (FR-008, FR-009)
- [X] T010 Create `code/report.py` stub for final report generation (FR-009, SC-001..005)
- [ ] T011a [P] Create `tests/unit/__init__.py`
- [ ] T011b [P] Create `tests/integration/__init__.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Valence Classification Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest DEAP dataset, preprocess EMG signals, extract features, and train a binary classifier to distinguish positive vs. negative valence with subject-level cross-validation.

**Independent Test**: Can be fully tested by running the preprocessing and training script on a subset of subjects and verifying that the cross-validated accuracy is statistically significantly above the majority class baseline (p < 0.05) using a label-shuffled control.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for Butterworth filter and 50Hz/60Hz notch filter in `tests/unit/test_preprocessing.py`
- [X] T013 [P] [US1] Unit test for RMS, ZCR, WAMP, MAV feature extraction in `tests/unit/test_features.py`
- [X] T014 [P] [US1] Integration test for end-to-end subject processing (download -> preprocess -> train) in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement signal filtering in `code/preprocessing.py` (FR-002, FR-003): Apply a band-pass Butterworth filter and a **50 Hz/60 Hz notch filter** (detecting the specific frequency from the dataset metadata or defaulting to 50 Hz if unspecified) to raw EMG signals, followed by baseline correction using the pre-stimulus interval.
- [X] T016 [US1] Implement non-overlapping short-duration windowing and feature extraction (RMS, ZCR, WAMP, MAV) for 3 muscles in `code/preprocessing.py` (FR-004)
- [ ] T017a [US1] Implement global data check for 'Skewed Valence Scores' (Edge Case: Skewed Valence) to detect subjects with all scores > 5 or < 5 and **exclude them from the TRAINING folds only** (retaining them for testing if valid) in `code/preprocessing.py`. **Do not exclude from the entire pipeline**; only omit from training data. Log the exclusion reason and subject ID.
- [ ] T018 [US1] Implement missing channel imputation (median filter) and explicitly **create and write to `data/processed/exclusions.log`** the exclusion of any subject with missing channels, and log this to the final report in `code/preprocessing.py` (Edge Case: Missing Channels)
- [ ] T019 [US1] **Implement and execute** Nested Leave-One-Subject-Out (LOSO) cross-validation loop with `joblib` parallelization (**n_jobs=2** to match the 2-CPU runner constraint, with sequential fallback if overhead is detected) in `code/train.py` (FR-005) [Deviation: FR-005 '5-fold' -> LOSO per Plan Complexity Tracking]. **Includes global exclusion logic**: Subjects flagged by T017a (skewed valence) are excluded from the **training folds**; subjects with missing channels (T018) are excluded from the current fold. **Includes model training**: Train both Random Forest (with a configured number of trees), Linear SVM (linear kernel), AND Logistic Regression within the loop with strict subject-level isolation.
- [ ] T021 [US1] Implement window-level prediction aggregation via majority voting to produce subject-level labels in `code/train.py`
- [ ] T022 [US1] Save `model_bundle.pkl` containing **BOTH the trained Random Forest, Linear SVM, AND Logistic Regression models** to `data/models/` and implement memory flushing (delete intermediate features per subject) to stay <7GB RAM (FR-010). **Ensure the bundle is loadable by subsequent scripts (`importance.py`, `validate.py`) without re-training.** [Deviation: Plan Dual Model Strategy for FR-007].
- [ ] T023 [US1] Calculate and log cross-validated accuracy against majority class baseline and perform a **permutation test (1000 shuffles)** and **paired t-test (paired on fold-level accuracies)** against the label-shuffled baseline (p < 0.05) in `code/validate.py` (SC-001) (Constitution Principle VII)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Muscle-Specific Feature Importance Analysis (Priority: P2)

**Goal**: Quantify the contribution of each muscle group (corrugator, zygomaticus, orbicularis) to classification performance using permutation importance and hierarchical feature addition.

**Independent Test**: Can be tested by running the importance analysis module on the trained Random Forest model and verifying that the output includes a ranked list of muscle groups with associated importance scores and that the hierarchical Nagelkerke's R² change is calculated for each addition.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US2] Unit test for permutation importance calculation logic in `tests/unit/test_importance.py`
- [ ] T025 [P] [US2] Unit test for Nagelkerke's R² calculation for Logistic Regression in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement permutation importance calculation grouped by muscle origin in `code/importance.py` (FR-006) [Depends: T022]
- [ ] T027 [US2] Implement SHAP value calculation for Random Forest model and generate summary plots in `code/importance.py` (FR-006) [Depends: T022]
- [ ] T028 [US2] Implement hierarchical model fitting sequence (Corrugator → +Zygomaticus → +Orbicularis) in `code/importance.py` (FR-007)
- [ ] T029 [US2] Train Logistic Regression models on hierarchical feature subsets (from T019/T022) in `code/importance.py` (FR-007) [Depends: T019, T022] [Deviation: FR-007 'RF only' -> Dual Model Strategy per Plan]. **Deliverable**: Calculate and log Nagelkerke's R² change for each step (Corrugator vs Baseline, +Zygomaticus vs Corrugator, etc.) and **calculate confidence intervals via bootstrap (sufficient iterations for stability)** for each R² change.
- [ ] T031 [US2] Generate report output listing top 10 features, muscle group contributions, and R² changes with CIs in `code/report.py` (SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Sensitivity Reporting (Priority: P3)

**Goal**: Generate a final report comparing observed accuracy to the label-shuffled baseline with effect sizes, and include a sensitivity analysis for the valence binarization threshold.

**Independent Test**: Can be tested by executing the reporting script and verifying the presence of a p-value, Cohen's d, and a table showing accuracy variation across three different valence cutoffs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test for Permutation Test (1000 shuffles) logic in `tests/unit/test_validation.py`
- [ ] T033 [P] [US3] Unit test for Cohen's d calculation in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement Permutation Test (sufficient shuffles) comparing observed accuracy vs. label-shuffled baseline in `code/validate.py` (FR-008)
- [ ] T035 [US3] Implement Paired T-Test against label-shuffled baseline in `code/validate.py` (FR-008)
- [ ] T036 [US3] Calculate and report Cohen's d effect size in `code/report.py` (SC-005)
- [ ] T037 [US3] Implement sensitivity analysis sweeping the valence binarization threshold over the **specific values {4.9, 5.0, 5.1}** required by FR-009 and SC-003 in `code/validate.py` (FR-009)
- [ ] T038 [US3] Generate sensitivity report showing accuracy variation (<3% threshold) in `code/report.py` (SC-003)
- [ ] T039 [US3] Generate final `paper.md`/report explicitly stating findings are associational (no causal claims), listing all metrics (p-values, d, R², sensitivity), and **explicitly logging all exclusions (missing channels, skewed subjects)** in the final report (SC-004, Edge Cases)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] Update `README.md` with project overview, setup instructions, and execution guide
- [ ] T040b [P] Update `quickstart.md` with detailed execution guide and troubleshooting
- [ ] T040c [P] Update `paper.md` template with report placeholders and citation structure
- [ ] T041a [P] Code cleanup: enforce black formatting in `code/`
- [ ] T041b [P] Code cleanup: remove unused imports in `code/`
- [ ] T042 [P] Additional unit tests for edge cases (missing data, skewed subjects) in `tests/unit/`
- [ ] T043 Run `quickstart.md` validation to ensure full pipeline execution <6 hours and <7GB RAM
- [ ] T044 Verify all artifacts (model_bundle.pkl, reports, exclusions.log) are hashable and versioned per Constitution Principle V

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on trained Random Forest model from US1 (T022)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on cross-validation results from US1

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Signal processing (filtering/windowing) before feature extraction
- Feature extraction before model training
- Model training before importance analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Butterworth filter in tests/unit/test_preprocessing.py"
Task: "Unit test for feature extraction in tests/unit/test_features.py"

# Launch all models for User Story 1 together:
Task: "Implement signal filtering in code/preprocessing.py"
Task: "Implement feature extraction in code/preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Preprocessing, Training, Basic Validation)
4. **STOP and VALIDATE**: Test User Story 1 independently on a single subject subset
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Feature Importance)
4. Add User Story 3 → Test independently → Deploy/Demo (Statistical Rigor)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Core Pipeline)
 - Developer B: User Story 2 (Importance Analysis)
 - Developer C: User Story 3 (Validation & Reporting)
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
- **Critical Constraint**: All tasks must run on CPU-only GitHub Actions (limited CPU resources, 7GB RAM, 6h limit). No GPU, no 8-bit quantization, no large models.
- **Data Integrity**: Never fabricate data. Use real DEAP dataset via `download.py` from HuggingFace.
- **Memory Management**: Process subjects sequentially in training loop; delete intermediate features immediately.
- **Deviation Markers**: Tasks with [Deviation: FR-XX] explicitly override spec requirements per Plan justification.
- **State File**: `state/projects/PROJ-214-decoding-emotional-valence-from-facial-e.yaml` is the single source of truth for artifact hashes.