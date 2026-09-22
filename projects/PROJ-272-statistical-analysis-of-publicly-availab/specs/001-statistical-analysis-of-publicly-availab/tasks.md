---
description: "Task list template for feature implementation"
---

# Tasks: Statistical Analysis of Publicly Available Textual Data for Detecting Cognitive Decline

**Input**: Design documents from `/specs/001-statistical-cognitive-decline/`
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

## Phase 0: Spec Amendment (Blocking Prerequisite)

**Purpose**: Resolve the contradiction between FR-001 (Dual-Source) and the Plan (ADReSS-only). This task MUST complete before any ingestion.

- [ ] T000a [FR-001] [US1] **SPEC AMENDMENT (EDIT)**: Edit `spec.md` FR-001 and US1 to reflect the "ADReSS-only" scope. Replace "Primary Source: ADReSS Challenge Dataset (2019/2020 editions)" with "Primary Source: ADReSS Challenge Dataset (2019/2020 editions). DementiaBank is explicitly excluded." Remove "DementiaBank" from Edge Cases. This task blocks all downstream tasks. (Depends on: None)
- [ ] T000b [FR-001] [US1] **PLAN UPDATE**: Update `plan.md` to remove "DementiaBank" from the "Scope Constraint" section and confirm "ADReSS-only" scope. (Depends on T000a)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create data directories: `mkdir -p data/raw data/processed data/interim data/results`
- [ ] T001b [P] Create test directories: `mkdir -p tests/unit tests/contract tests/integration`
- [ ] T001c [P] Create spec directories: `mkdir -p specs/001-statistical-cognitive-decline/contracts`
- [ ] T001d [P] Create code directories: `mkdir -p code`
- [X] T002 Initialize Python 3.11 project with dependencies: Create `requirements.txt` with pinned versions: `pandas>=2.0.0`, `scikit-learn>=1.3.0`, `nltk>=3.8`, `spacy>=3.7`, `sentence-transformers>=2.2.0`, `numpy>=1.24.0`, `scipy>=1.10.0`, `pyyaml>=6.0`, `tqdm>=4.65.0`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration management in `code/config.py` (paths, random seeds, CPU-only constraints)
- [X] T005 [P] Implement logging infrastructure in `code/utils.py` with file and console handlers
- [X] T006 [P] Create data validation utilities in `code/utils.py` (UTF-8 normalization, length checks)
- [ ] T007 [P] Setup pre-commit hooks for PII scanning and dependency checks: Create `.pre-commit-config.yaml` with `detect-secrets` and `black` hooks
- [ ] T008 [P] Create base schema definitions in `specs/001-statistical-cognitive-decline/contracts/`: Create `dataset.schema.yaml` and `feature.schema.yaml` using JSON Schema format in YAML, defining fields: `participant_id`, `label`, `text`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Acquire ADReSS Challenge dataset, clean transcripts, and structure into a labeled analysis-ready dataset. (Scope reduced to ADReSS only per Plan, contingent on T000a).

**Independent Test**: Run ingestion on a sample subset (e.g., a representative number of transcripts) and verify output contains a matching number of records with non-null cognitive status labels and cleaned text fields.

### Implementation for User Story 1

- [X] T012 [FR-001] [US1] Implement data download utility in `code/ingestion.py` to fetch ADReSS raw files from canonical GitHub URL; Compute SHA-256 hash upon download and log it; **If canonical URL fails, raise `ConnectionError` with message "ADReSS download failed. No synthetic fallback."** (Depends on T004)
- [X] T012b [FR-001] [US1] **Raw Record Count**: Implement a function in `code/ingestion.py` to count the total number of raw records in the downloaded dataset BEFORE any filtering. Save this count to `data/results/raw_record_count.json`. (Depends on T012)
- [X] T012c [FR-001] [US1] **Scope Validation**: Validate that `code/config.py` explicitly excludes DementiaBank (per T000a). If DementiaBank is detected, raise `ValueError`. (Depends on T000a, T004)
- [X] T012e [US1] Validate dataset size in `code/ingestion.py`: Log the total number of participants per group. If any group has < 10 participants, log a `WARNING` and flag dataset as "low_power" in `data/results/metadata.json`, but DO NOT fail the pipeline (Depends on T012b)
- [X] T012f [US1] Record computed SHA-256 checksum in `data/raw/checksums.json` with filename and hash (Depends on T012)
- [X] T013 [US1] Implement text cleaning pipeline in `code/ingestion.py`: remove non-verbal annotations, normalize to UTF-8 (Depends on T012)
- [X] T014 [US1] Implement record filtering in `code/ingestion.py`: Filter records where label is null OR text length < 50 words. Log excluded records with reason codes to `data/interim/exclusions.log`. (Depends on T013)
- [X] T015 [US1] Implement metadata extraction in `code/ingestion.py` to parse cognitive status (Control, MCI, AD) from ADReSS headers and generate specific reason codes for excluded records (Depends on T013)
- [X] T016 [US1] Create intermediate cleaned dataset in `data/interim/cleaned_adress.csv` with derivation log (Depends on T014, T015)
- [ ] T012g [SPEC-GAP] [US1] Document Spec Gap in `data/ingestion_amendment.log`: Record that FR-001 required dual-source but Plan excludes DementiaBank (post-T000a). Task: "Formally amend FR-001 to ADReSS-only or provide verified DementiaBank source URL before proceeding." (Depends on T000a)
- [X] T012h [US1] **Success Criterion SC-001**: Calculate the proportion of participants with valid cognitive status labels vs total raw records (using count from T012b). Write this value to `data/results/metadata.json` under key `valid_label_proportion`. (Depends on T012b, T014)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation to ensure code exists to test**

- [X] T009 [P] [US1] Unit test for text cleaning (remove `<laughter>`, `<pause>`) in `tests/unit/test_ingestion.py` (Depends on T013)
- [X] T010 [P] [US1] Unit test for UTF-8 normalization and exclusion logic in `tests/unit/test_ingestion.py` (Depends on T013, T014)
- [X] T011 [P] [US1] Contract test for dataset schema validation and **SC-001 verification**: In `tests/contract/test_schemas.py`, validate `data/interim/cleaned_adress.csv` AND assert that `data/results/metadata.json` contains key `valid_label_proportion` with a value between 0 and 1. (Depends on T008, T016, T012h)
- [X] T047 [US1] Integration test: Run full ingestion pipeline on a sample subset of transcripts and verify output contains a corresponding number of records with valid labels and cleaned text in `tests/integration/test_us1_sample.py` (Depends on T016). Assertions: `assert len(df) == expected_count`, `assert df["label"].notnull().all()`, `assert df["text"].str.len() >= 50`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Linguistic Feature Extraction and Statistical Testing (Priority: P2)

**Goal**: Compute lexical, syntactic, and semantic features for each participant and perform statistical hypothesis testing (Mann-Whitney U) between groups.

**Independent Test**: Run feature extraction on a small, fixed dataset (a limited number of participants) and verify output includes multiple feature categories with calculated p-values and effect sizes.

### Implementation for User Story 2

- [X] T022 [US2] Implement lexical feature extraction (TTR, MTLD, Noun/Verb ratio) in `code/features.py` (Depends on T016)
- [X] T023 [US2] Implement syntactic feature extraction (Mean Clause Length, T-unit Count) using spaCy in `code/features.py` (Depends on T016)
- [ ] T024 [US2] Implement semantic feature extraction (Sentence Embeddings) using `all-MiniLM-L6-v2` in `code/features.py` (CPU-only); Process in batches using `torch.no_grad()` with `batch_size=32` to prevent OOM; Save embeddings to `data/processed/embeddings.npy` (shape [N, 384], dtype float32), where D=384. AND generate `data/processed/embeddings.derivation.log` documenting the transformation (Depends on T016)
- [ ] T024c [US2] **Data Hygiene**: Compute SHA-256 checksum for `data/processed/embeddings.npy` and record it in `data/processed/checksums.json` and update `state/projects/...yaml`. (Depends on T024)
- [X] T024b [US2] Calculate 'Sentence Embedding Cosine Similarity' (self-similarity) from embeddings in `code/features.py` and append as a new column to the feature matrix (Depends on T024)
- [X] T029 [US2] Handle edge case: Flag and exclude records with identical feature vectors (collinearity) **before saving the final matrix**. Log excluded IDs to `data/interim/exclusions.log`. (Depends on T024b)
- [ ] T025 [US2] Save processed feature matrix to `data/processed/features.csv` with metadata (Depends on T024b, T029)
- [X] T026 [US2] Implement statistical testing module in `code/stats.py`: Mann-Whitney U for Control vs AD and Control vs MCI (Depends on T025)
- [ ] T027 [US2] Implement Bonferroni correction logic in `code/stats.py` to report raw and adjusted p-values; Persist results to `data/results/statistical_metrics.json` (Depends on T026)
- [ ] T028 [US2] Calculate Cohen's d effect sizes for all significant features and persist to `data/results/statistical_metrics.json` (Depends on T026)
- [X] T049 [US2] [REVISE] Implement explicit sample size reporting in `code/ingestion.py` (or `stats.py`): If any group has < 10 participants, log a `WARNING` and flag the dataset as "low_power" in `data/results/metadata.json` (Depends on T016)

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Type-Token Ratio and MTLD calculation in `tests/unit/test_features.py` (Depends on T022)
- [X] T019 [P] [US2] Unit test for spaCy syntactic complexity metrics (Clause Length, T-unit) in `tests/unit/test_features.py` (Depends on T023)
- [X] T020 [P] [US2] Unit test for semantic coherence (Sentence Embedding Cosine Similarity) in `tests/unit/test_features.py` (Depends on T024b)
- [X] T021 [P] [US2] Unit test for Mann-Whitney U and Bonferroni correction in `tests/unit/test_stats.py` (Depends on T026, T027)
- [ ] T025a [P] [US2] **Contract Test**: Verify feature matrix contains exactly the 6 required columns: `[TTR, MTLD, Noun_Verb_Ratio, Mean_Clause_Length, T_Unit_Count, Sentence_Embedding_Cosine_Similarity]`. Fail if any are missing. (Depends on T025)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Validation (Priority: P3)

**Goal**: Train Logistic Regression and Random Forest classifiers for preliminary sanity checks and perform nested k-fold cross-validation for primary validation.

**Independent Test**: Train model on split data, verify AUC >= 0.70 on test set (preliminary) and mean AUC > 0.5 (p<0.05) on nested CV.

### Implementation for User Story 3

- [X] T033 [US3] Implement data splitting and **Adaptive CV** in `code/modeling.py`:
 1. **Enforce 70/15/15 split**: Validate that the stratified split matches the 70/15/15 ratio. If it deviates, raise an error unless the dataset is too small (see below).
 2. **Adaptive Logic**: If `min(group_counts) < 15`, reduce folds to 3 and log the change in `data/results/cv_config.json`.
 3. **SC-004 Conflict Resolution**: If fold count is reduced, explicitly flag SC-004 ("5-fold stability") as **UNTESTABLE** in the final report, record the actual fold count used, AND report the exact fold count and 95% confidence interval as a fallback verification step.
 4. **Unit Test Assertion**: For N < 10 samples per class, verify folds are reduced and logged.
 (Depends on T025)
- [ ] T033a [US3] **Split Validation**: Explicitly validate the 70/15/15 ratio in `code/modeling.py`. If the ratio is not met and the dataset is not too small, raise `ValueError`. (Depends on T033)
- [ ] T034 [US3] Implement Logistic Regression training and evaluation in `code/modeling.py` (Preliminary Sanity Check) (Depends on T033)
- [ ] T035 [US3] Implement Random Forest training and evaluation in `code/modeling.py` (Preliminary Sanity Check) (Depends on T033)
- [ ] T037 [US3] Implement a nested k-fold cross-validation loop in `code/modeling.py` for primary validation (Depends on T033)
- [ ] T036 [US3] Aggregate model metrics (AUC, F1, accuracy) from preliminary and nested CV runs into a unified summary object in `code/modeling.py` (Depends on T034, T035, T037)
- [ ] T038 [US3] Ensure nested CV uses CPU-only models and respects memory constraints (< 7 GB) (Depends on T037)
- [ ] T039 [US3] Calculate mean AUC and standard deviation across outer folds; save results to `data/results/cv_metrics.json` (Depends on T037)
- [ ] T040 [US3] Generate final results report in `data/results/model_performance.json` (Depends on T036, T039)

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for stratified split logic in `tests/unit/test_modeling.py` (Depends on T033)
- [ ] T031 [P] [US3] Unit test for nested cross-validation loop in `tests/unit/test_modeling.py` (Depends on T037)
- [ ] T032 [P] [US3] Integration test for full pipeline (ingest -> features -> model) in `tests/integration/test_pipeline.py` (Depends on T033, T037)
- [ ] T054 [US3] [REVISE] Unit test for adaptive cross-validation: In `tests/unit/test_modeling.py`, create a tiny dataset (a small number of samples per class) and assert that the nested CV logic automatically reduces the number of folds and logs the change (Depends on T033)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041a [P] Documentation updates: Write feature definitions section in `research.md`
- [ ] T041b [P] Documentation updates: Write statistical rationale section in `research.md`
- [ ] T042 Code cleanup and refactoring for readability
- [ ] T043 Performance optimization: Ensure semantic embedding batch processing fits within RAM limits
- [ ] T044 [P] Additional unit tests for edge cases (empty transcripts, collinear data) in `tests/unit/`
- [ ] T045 Run quickstart.md validation to ensure reproducibility on fresh environment
- [ ] T046 [US3] Measure total pipeline runtime and peak RAM: Wrap `code/main.py` execution with `tracemalloc` and `time` to measure total runtime and peak RSS; Generate `data/results/runtime_log.json` with `total_seconds` and `data/results/memory_profile.json` with `peak_rss_gb`; Verify against SC-005 (≤ 6 hours, ≤ 7 GB) (Depends on T040)

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
- **User Story 2 (P2)**: Depends on T016 (cleaned dataset) from US1
- **User Story 3 (P3)**: Depends on T025 (feature matrix) from US2

### Within Each User Story

- Implementation tasks MUST be written before Test tasks
- Tests depend on the existence of the implementation code
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation tasks for US1 that are independent:
Task: "Implement data download utility in code/ingestion.py"
Task: "Implement text cleaning pipeline in code/ingestion.py"

# After implementation, launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for text cleaning in tests/unit/test_ingestion.py"
Task: "Unit test for UTF-8 normalization in tests/unit/test_ingestion.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Spec Amendment (T000a, T000b) - **CRITICAL**
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (clean data exists)
6. Deploy/demo if ready

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
 - Developer A: User Story 1 (Ingestion)
 - Developer B: User Story 2 (Features/Stats) - *Must wait for US1 data*
 - Developer C: User Story 3 (Modeling) - *Must wait for US2 features*
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
- **Constraint Reminder**: All models must run on CPU only (no CUDA, no 8-bit quantization). Use `all-MiniLM-L6-v2` for embeddings.
- **Data Source**: Only ADReSS dataset is used per Plan (post-T000a); DementiaBank is excluded unless T000a provides a verified URL.
- **Spec Gap**: FR-001 requires dual-source. T000a and T000b address this gap by amending the spec or documenting the exclusion.
- **Robustness**: T012 ensures no synthetic fallbacks; T014/T015 ensure short transcripts are excluded; T033 handles adaptive CV and flags SC-004 conflicts with a fallback.
- **Data Hygiene**: T024c ensures embeddings are checksummed. T012f ensures raw data is checksummed.
- **Success Criteria**: T012h calculates SC-001 proportion. T025a verifies SC-002 features. T033 flags SC-004/SC-003 conflicts and provides a fallback.