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
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

## Phase 0: Spec Verification (Blocking Prerequisite)

**Purpose**: Verify alignment between Spec (FR-001) and Plan regarding DementiaBank exclusion. The Spec explicitly excludes DementiaBank; the Plan must reflect this without contradiction. This phase MUST run before any setup tasks to prevent wasted effort on out-of-scope code.

- [ ] T000 [Plan] [US1] **SPEC & PLAN VERIFICATION (AUTOMATED)**: Create and execute `scripts/verify_scope.py`. This script MUST parse `spec.md` and `plan.md` for the keyword "DementiaBank". If found, it MUST exit with code 1 and print "ERROR: DementiaBank found in scope. Aborting." If not found, it MUST exit 0. **Gate Logic**: This task is a blocking gate. It MUST run FIRST. It has NO dependencies on setup tasks. If it fails, the pipeline halts. (Depends on: None)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure. Consolidated from fragmented tasks to ensure atomic setup.

- [ ] T001a [P] **Directory Structure**: Create project directory structure (`mkdir -p data/raw data/interim data/results data/processed code tests/unit tests/contract tests/integration specs/001-statistical-cognitive-decline/contracts`). (Depends on: None)
- [ ] T001b [P] **Dependencies & Pinning**: Create `requirements.txt` with pinned versions (`pandas>=2.0.0`, `scikit-learn>=1.3.0`, `nltk>=3.8`, `spacy>=3.7`, `sentence-transformers>=2.2.0`, `numpy>=1.24.0`, `scipy>=1.10.0`, `pyyaml>=6.0`, `tqdm>=4.65.0`, `pytest>=7.0.0`, `huggingface_hub>=0.10.0`). This task covers both file creation and the explicit pinning of all versions to ensure reproducibility. (Depends on: T001a)
- [ ] T001c [P] **Linting/Formatting**: Configure linting (ruff/flake8) and formatting (black) in `pyproject.toml` or `.flake8`. (Depends on: T001a)
- [ ] T001d1 [P] **Configure Black**: Configure Black formatting in `pyproject.toml` (line length 88, target version python3.9). (Depends on: T001a)
- [ ] T001d2 [P] **Configure Ruff**: Configure Ruff linting in `pyproject.toml` (exclude patterns, specific rules). (Depends on: T001a)
- [ ] T001d3 [P] **Pre-commit Hooks**: Setup `.pre-commit-config.yaml` with `detect-secrets`, `black`, `ruff` and install hooks. (Depends on: T001d1, T001d2)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003a [P] **Path/Seed Config**: Setup configuration management in `code/config.py` for paths and random seeds. (Depends on T001a)
- [ ] T003b [P] **Dataset Source Config**: Setup configuration in `code/config.py` for `DATASET_SOURCE="ADReSS"`, `CANONICAL_URL`, `MIRROR_URL`. (Depends on T001a)
- [ ] T004 [P] **Logging Infrastructure**: Implement logging infrastructure in `code/utils.py` with file and console handlers. (Depends on T001a)
- [ ] T005 [P] **Data Validation Utilities**: Create data validation utilities in `code/utils.py` (UTF-8 normalization, length checks). (Depends on T001a)
- [ ] T006 [P] **Schema Definitions**: Create base schema definitions in `specs/001-statistical-cognitive-decline/contracts/`: Create `dataset.schema.yaml` and `feature.schema.yaml` using JSON Schema format in YAML, defining fields: `participant_id`, `label`, `text`. (Depends on T001a)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Acquire ADReSS Challenge dataset, clean transcripts, and structure into a labeled analysis-ready dataset. (Scope reduced to ADReSS only per Plan).

**Independent Test**: Run ingestion on a sample subset and verify output contains a matching number of records with non-null cognitive status labels and cleaned text fields.

### Implementation for User Story 1

- [ ] T012c [FR-001] [US1] **Scope Validation**: Validate that `code/config.py` explicitly excludes DementiaBank (per T000). Check `DATASET_SOURCE == "ADReSS"`. If DementiaBank is detected or `DATASET_SOURCE` is missing, raise `ValueError`. (Depends on T003b)
- [ ] T012 [FR-001] [US1] Implement data download utility in `code/ingestion.py` to fetch ADReSS raw files from canonical GitHub URL. **Retry Logic**: Attempt primary URL; if failed, attempt `MIRROR_URL` (versioned Zenodo/Commit). **Failure**: If both fail, raise `ConnectionError` with message "ADReSS download failed. No synthetic fallback." (Depends on T012c)
- [ ] T012d [FR-001] [US1] **Checksum Verification**: Implement SHA-256 checksum verification in `code/ingestion.py`. Compute the hash of downloaded files and compare against a known hash (or log the computed hash for manual verification if unknown). Fail loudly if mismatch. (Depends on T012)
- [ ] T012b [FR-001] [US1] **Raw Record Count**: Implement function `count_raw_records()` in `code/ingestion.py` to count the total number of raw records in the downloaded dataset BEFORE any filtering. Save this count to `data/results/raw_record_count.json` with exact schema `{"raw_count": <int>}`. Log group counts (Control, MCI, AD) as informational messages. (Depends on T012d)
- [ ] T013a [US1] **Remove Annotations**: Implement text cleaning in `code/ingestion.py` to remove non-verbal annotations (e.g., `<laughter>`, `<pause>`). (Depends on T012d)
- [ ] T013b [US1] **UTF-8 Normalization**: Implement text cleaning in `code/ingestion.py` to normalize text to UTF-8. (Depends on T013a)
- [ ] T014 [US1] **Filter Records**: Implement function `filter_records()` in `code/ingestion.py`: Filter records where label is null OR text length < 50 words (as per FR-001 Edge Case). **Verification**: Explicitly verify the filter logic by checking for `None` labels and counting words. Log excluded records with reason codes (`MISSING_LABEL`, `TOO_SHORT`) to `data/interim/exclusions.log`. (Depends on T013b)
- [ ] T015 [US1] **Metadata Extraction**: Implement metadata extraction in `code/ingestion.py` to parse cognitive status (Control, MCI, AD) from ADReSS headers and generate specific reason codes for excluded records. (Depends on T013b)
- [ ] T016 [US1] **Create Cleaned Dataset**: Implement function `create_cleaned_dataset()` in `code/ingestion.py` to save the filtered dataset to `data/interim/cleaned_adress.csv` with derivation log. (Depends on T014, T015)
- [ ] T012g [US1] **Metadata Aggregation**: Implement function `aggregate_metadata()` in `code/ingestion.py` to merge `data/results/raw_record_count.json`, `data/interim/exclusions.log`, and `data/results/group_counts.json` (from T012b) to calculate `valid_label_proportion`. Write to `data/results/metadata.json` with schema `{"raw_count": <int>, "filtered_count": <int>, "valid_label_proportion": <float>, "group_counts": {"Control": <int>, "MCI": <int>, "AD": <int>}}. (Depends on T012b, T014)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation to ensure code exists to test**

- [ ] T009 [P] [US1] Unit test for text cleaning (remove `<laughter>`, `<pause>`) in `tests/unit/test_ingestion.py`. (Depends on T013a)
- [ ] T010 [P] [US1] Unit test for UTF-8 normalization and exclusion logic in `tests/unit/test_ingestion.py`. (Depends on T013b, T014)
- [ ] T011 [P] [US1] Contract test for dataset schema validation: In `tests/contract/test_schemas.py`, validate `data/interim/cleaned_adress.csv` AND assert that `data/results/metadata.json` contains keys `raw_count`, `filtered_count`, `valid_label_proportion`, and `group_counts` against `dataset.schema.yaml`. (Depends on T006, T016, T012g)
- [ ] T047 [US1] Integration test: Run full ingestion pipeline on a sample subset of transcripts and verify output contains a corresponding number of records with valid labels and cleaned text in `tests/integration/test_us1_sample.py`. (Depends on T016). Assertions: `assert len(df) == expected_count`, `assert df["label"].notnull().all()`, `assert df["text"].str.len() >= 50`. (Depends on T016)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Linguistic Feature Extraction and Statistical Testing (Priority: P2)

**Goal**: Compute lexical, syntactic, and semantic features for each participant and perform statistical hypothesis testing (Mann-Whitney U) between groups.

**Independent Test**: Run feature extraction on a small, fixed dataset and verify output includes multiple feature categories with calculated p-values and effect sizes.

### Implementation for User Story 2

- [ ] T022a [US2] **TTR**: Implement Type-Token Ratio extraction in `code/features.py`. (Depends on T016)
- [ ] T022b [US2] **MTLD**: Implement Mean Length of Textual Discourse (MTLD) extraction in `code/features.py`. (Depends on T016)
- [ ] T022c [US2] **Noun/Verb Ratio**: Implement Noun/Verb ratio extraction in `code/features.py`. (Depends on T016)
- [ ] T023 [US2] **Syntactic Features**: Implement syntactic feature extraction (Mean Clause Length, T-unit Count) using spaCy in `code/features.py`. (Depends on T016)
- [ ] T024 [US2] **Semantic Embeddings**: Implement semantic feature extraction (Sentence Embeddings) using the CPU-efficient model `sentence-transformers/all-MiniLM-L6-v2` in `code/features.py`. **Commit Hash**: Use `huggingface_hub.model_info` to fetch the exact model revision hash from the HuggingFace Hub config (parse `commit_hash` from `config.json`) and log it. Process in batches using `torch.no_grad` with `batch_size=32` to prevent OOM. **Atomic Write**: Save embeddings to a temp file `data/processed/embeddings.tmp.npy` then `os.replace` to `data/processed/embeddings.npy`. **Reproducibility Check**: Re-run generation on a [deferred] subset and verify checksum matches. (Depends on T001b, T016)
- [ ] T024c [US2] **Data Hygiene**: Compute SHA-256 checksum for `data/processed/embeddings.npy` and record it in `data/processed/checksums.json` with schema `{"embeddings.npy": "<hash>"}`. (Depends on T024)
- [ ] T024b [US2] **Cosine Similarity**: Calculate 'Sentence Embedding Cosine Similarity' (Average Intra-Document Sentence Similarity) from embeddings in `code/features.py` and append as a new column to the feature matrix. **Definition**: Compute pairwise cosine similarity between all sentence embeddings within a single transcript, then take the mean of these values to produce a single scalar per participant. This metric captures semantic coherence within the transcript. (Depends on T024)
- [ ] T029 [US2] **Collinearity Check**: Handle edge case: Flag and exclude records with effectively identical feature vectors **before saving the final matrix**. **Definition**: Use `numpy.allclose` with `rtol=1e-5` to detect floating-point collinearity, NOT `array_equal`. Log excluded IDs to `data/interim/exclusions.log`. (Depends on T024b)
- [ ] T025 [US2] **Save Feature Matrix**: Save processed feature matrix to `data/processed/features.csv` with metadata. This task consumes the feature matrix artifact generated by T024b (with the appended similarity column) and T029 (after collinearity filtering). **Input**: `data/processed/features.csv` (pre-collinearity) -> **Output**: `data/processed/features.csv` (final). (Depends on T024b, T029)
- [ ] T026 [US2] **Statistical Testing**: Implement statistical testing module in `code/stats.py`: Mann-Whitney U for Control vs AD and Control vs MCI. (Depends on T025)
- [ ] T027 [US2] **Bonferroni Correction**: Implement Bonferroni correction logic in `code/stats.py` to report raw and adjusted p-values; persist raw/adjusted p-values to `data/results/stats_p_values.json`. (Depends on T026)
- [ ] T028 [US2] **Cohen's d**: Calculate Cohen's d effect sizes for all significant features and save to `data/results/stats_cohens_d.json`. (Depends on T026)
- [ ] T028b [US2] [Plan] **Rank-Biserial**: Calculate Rank-Biserial effect sizes for all significant features as required by the Plan's Summary section and save to `data/results/stats_rank_biserial.json`. (Depends on T026)
- [ ] T028c [US2] **Stats Aggregation & Reporting**: Implement function `aggregate_stats()` in `code/stats.py` to merge `data/results/stats_p_values.json`, `data/results/stats_cohens_d.json`, and `data/results/stats_rank_biserial.json` into a unified `data/results/statistical_metrics.json`. **Reporting Requirement**: Ensure the final JSON explicitly reports Bonferroni-corrected p-values and effect sizes (Cohen's d, Rank-Biserial) in a single structure as per US2 Acceptance Criteria #5. (Depends on T027, T028, T028b)

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for Type-Token Ratio and MTLD calculation in `tests/unit/test_features.py`. (Depends on T022a, T022b)
- [ ] T019 [P] [US2] Unit test for spaCy syntactic complexity metrics (Clause Length, T-unit) in `tests/unit/test_features.py`. (Depends on T023)
- [ ] T020 [P] [US2] Unit test for semantic coherence (Sentence Embedding Cosine Similarity) in `tests/unit/test_features.py`. (Depends on T024b)
- [ ] T021 [P] [US2] Unit test for Mann-Whitney U and Bonferroni correction in `tests/unit/test_stats.py`. (Depends on T026, T027)
- [ ] T025a [P] [US2] **Contract Test**: Verify feature matrix contains exactly the 6 required columns: `[TTR, MTLD, Noun_Verb_Ratio, Mean_Clause_Length, T_Unit_Count, Sentence_Embedding_Cosine_Similarity]`. Fail if any are missing. (Depends on T025)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Validation (Priority: P3)

**Goal**: Train Logistic Regression and Random Forest classifiers for preliminary sanity checks and perform nested k-fold cross-validation for primary validation.

**Independent Test**: Train model on split data, verify AUC >= 0.70 on test set (preliminary) and mean AUC > 0.5 (p<0.05) on nested CV.

### Implementation for User Story 3

- [ ] T033 [US3] **Adaptive Data Splitting & CV Config**: Implement data splitting and **Adaptive CV** in `code/modeling.py`:
 1. **Split Logic**: Use `sklearn.model_selection.train_test_split` with `stratify=y`. First split the dataset into a training set and a temporary set. Then split the temporary set into equal halves to achieve a train/validation/test distribution. IF dataset size permits.
 2. **Adaptive Logic**: Implement a configurable adaptive strategy where the number of outer folds or the validation method is adjusted based on `min(group_counts)`. **Threshold**: If `min(group_counts) < 5`, use `LeaveOneOut()`. Else, use `KFold(n=5)`.
 3. **Ratio Validation**: If the dataset is large enough for 70/15/15, enforce the ratio. If the dataset is too small, the adaptive logic applies, and the ratio check is skipped.
 4. **Output Schema**: Save `data/results/cv_config.json` with schema `{"outer_folds": <int>, "method": "k-fold"|"LOOCV", "sample_size_warning": <bool>}`.
 5. **Blocking Gate**: This task is a blocking gate. If split fails (e.g., N=0), raise `ValueError`. The pipeline runner (GitHub Actions) will halt if this task exits with non-zero code. **Input**: `data/processed/features.csv` (from T025). (Depends on T025)
- [ ] T033b [US3] **Adaptive Logic Validation**: Implement function `validate_adaptive_logic()` in `code/modeling.py` to explicitly test the threshold logic (min_count < 5) and verify the correct CV method (LOOCV vs KFold) is selected and logged. (Depends on T033)
- [ ] T034a [US3] **LogReg Definition**: Define Logistic Regression model hyperparameters in `code/modeling.py`. (Depends on T033)
- [ ] T034b [US3] **LogReg Training**: Implement Logistic Regression training loop in `code/modeling.py`. (Depends on T034a)
- [ ] T034c [US3] **LogReg Evaluation**: Implement Logistic Regression evaluation metrics calculation in `code/modeling.py`. (Depends on T034b)
- [ ] T035 [US3] **Random Forest**: Implement Random Forest training and evaluation in `code/modeling.py`. (Depends on T033)
- [ ] T037 [US3] **Nested CV**: Implement a nested k-fold cross-validation loop (adaptive per T033) in `code/modeling.py`. (Depends on T033)
- [ ] T036 [US3] **Aggregate Metrics**: Aggregate model metrics (AUC, F1, accuracy) from preliminary and nested CV runs into a unified summary object in `code/modeling.py`. (Depends on T034c, T035, T037)
- [ ] T038 [US3] **CPU Constraint**: Ensure nested CV uses CPU-only models and respects memory constraints (< 7 GB). Explicitly enforce "no low-bit quantization" as per Plan constraints. (Depends on T037)
- [ ] T039 [US3] **CV Metrics**: Calculate mean AUC and standard deviation across outer folds; save results to `data/results/cv_metrics.json`. (Depends on T037)
- [ ] T040 [US3] **Final Report**: Generate final results report in `data/results/model_performance.json`. (Depends on T036, T039)

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for stratified split logic in `tests/unit/test_modeling.py`. (Depends on T033)
- [ ] T031 [P] [US3] Unit test for nested cross-validation loop in `tests/unit/test_modeling.py`. (Depends on T037)
- [ ] T032 [P] [US3] Integration test for full pipeline (ingest -> features -> model) in `tests/integration/test_pipeline.py`. (Depends on T033, T037)
- [ ] T054 [US3] [REVISE] Unit test for adaptive cross-validation: In `tests/unit/test_modeling.py`, create a tiny dataset (N < 15 per class) and assert that the nested CV logic reduces folds or switches to LOOCV instead of raising ValueError. (Depends on T033)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041a [P] Documentation updates: Write feature definitions section in `research.md`.
- [ ] T041b [P] Documentation updates: Write statistical rationale section in `research.md`.
- [ ] T042 [P] Code cleanup and refactoring for readability.
- [ ] T043 [P] Performance optimization: Ensure semantic embedding batch processing fits within RAM limits.
- [ ] T044 [P] Additional unit tests for edge cases (empty transcripts, collinear data) in `tests/unit/`.
- [ ] T045 [P] Run quickstart.md validation to ensure reproducibility on fresh environment.
- [ ] T046 [US3] Measure total pipeline runtime and peak RAM: Wrap `code/main.py` execution with `tracemalloc` (for peak RSS) and `time` (for total seconds). Generate `data/results/runtime_log.json` with schema `{"total_seconds": <float>}` and `data/results/memory_profile.json` with schema `{"peak_rss_gb": <float>}`. Verify against SC-005 (≤ 6 hours, ≤ 7 GB). (Depends on T040)

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

1. Complete Phase 0: Spec Verification (T000) - **CRITICAL**
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
- **Constraint Reminder**: All models must run on CPU only (no CUDA, no 8-bit quantization). Use a CPU-efficient model (e.g., `sentence-transformers/all-MiniLM-L6-v2`) for embeddings.
- **Data Source**: Only ADReSS dataset is used per Plan (post-T000); DementiaBank is excluded.
- **Robustness**: T012 ensures retry logic with mirror fallback; T014/T015 ensure short transcripts are excluded; T033 enforces adaptive logic for small datasets.
- **Data Hygiene**: T024c ensures embeddings are checksummed. T012d ensures raw data is checksummed.
- **Reproducibility**: T012 includes versioned mirror fallback; T024 logs exact model version and commit hash; T029 uses `np.allclose` for collinearity.
- **Atomic Writes**: T012g, T028c, T024 use atomic write patterns to prevent race conditions.
- **Scope Note**: Tasks T055-T058 (Verified Data Source Injection, Storage Constraint Simulation, Streaming Implementation, Feature Robustness) have been removed as they represented unapproved scope creep and lacked mapping to Spec/Plan requirements.