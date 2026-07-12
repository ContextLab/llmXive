# Tasks: LLMXive Follow-up: Extending "A Survey of Large Audio Language Models"

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY to satisfy the Independent Test criteria defined in the User Stories.

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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `models/`, `results/`, `state/`)
- [ ] T002 Initialize Python 3.11 project with pinned `requirements.txt` (torch-cpu, transformers, scikit-learn, pandas, soundfile, datasets)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `src/utils/config.py` for random seeds, path management, and state file I/O
- [ ] T005 [P] Setup `tests/contract/` directory and schema validation utilities for YAML/JSON artifacts
- [ ] T006 [P] Create `state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml` with initial `artifact_hashes` map
- [ ] T007a [P] Implement `src/utils/stats.py` Mahalanobis distance calculation logic using `LedoitWolf` covariance estimator (FR-006)
- [ ] T007b [P] Save the implemented Mahalanobis utility to `src/utils/stats.py` with proper documentation
- [ ] T008 Configure error handling and logging infrastructure (global logger with file and console handlers)
- [ ] T009 Setup environment configuration to enforce CPU-only execution (`os.environ["CUDA_VISIBLE_DEVICES"]=""`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2.5: Data Verification & Label Independence Gate

**Purpose**: Explicitly validate dataset labeling methodology before embedding extraction (FR-007)

- [ ] T011b [US1] Implement `src/data/verify_labels.py` to perform an automated check for the *absence* of latent-space correlation in dataset metadata; fail the pipeline if such correlation is detected (FR-007)

**Checkpoint**: Label independence verified - safe to proceed with embedding extraction

---

## Phase 3: User Story 1 - CPU-Only Latent Embedding Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract fixed-dimensional latent embeddings from audio-text pairs using a frozen, lightweight encoder on CPU.

**Independent Test**: Run extraction on 100 benign files on a 2-core CPU runner; verify JSON output of fixed-size vectors without CUDA errors within 15 mins.

### Tests for User Story 1 (MANDATORY) ⚠️

- [ ] T010 [P] [US1] Contract test for embedding output schema in `tests/contract/test_embedding_schema.py`
- [ ] T011 [P] [US1] Integration test for error handling (corrupted files) in `tests/integration/test_error_handling.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/data/download.py` to fetch verified datasets (LALM subsets); if unavailable, implement fallback logic to generate 'verified benign TTS + random noise' data (FR-007, FR-005)
- [ ] T013 [P] [US1] Implement `src/data/preprocess.py` to load audio, skip corrupted files gracefully, and validate label independence (FR-005)
- [ ] T014 [US1] Implement `src/data/embed.py` to load `distil-whisper-base` (CPU-only), extract embeddings in batches (size=32), and save to `data/embeddings.parquet` (Parquet format) (FR-001)
- [ ] T015 [US1] Add dimensionality validation logic to ensure encoder output matches expected `AudioEmbedding` shape before saving
- [ ] T016 [US1] Implement resource logging for embedding extraction phase (time per batch, peak RAM)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight Binary Classifier Training (Priority: P2)

**Goal**: Train a Logistic Regression classifier on extracted embeddings to distinguish jailbreak vs. benign samples.

**Independent Test**: Train on [deferred] of data; verify model convergence, non-zero weights, and probability output for test set within 5 mins on CPU.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T018 [P] [US2] Contract test for model artifact schema in `tests/contract/test_model_schema.py`
- [ ] T019 [P] [US2] Integration test for train/test split integrity in `tests/integration/test_data_split.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `src/models/train.py` to perform a stratified split of embeddings and labels into training and testing subsets. (FR-002)
- [ ] T021 [US2] Implement `src/models/train.py` to train `LogisticRegression` (CPU, no GPU) on the training split (FR-002)
- [ ] T022 [US2] Implement `src/models/train.py` to calculate benign centroid ($\mu_{benign}$) and covariance ($\Sigma$) **only** from the Training Set's benign samples
- [ ] T022b [US2] Implement `src/models/train.py` to calculate Mahalanobis distance for **ALL samples** (train and test) using the benign centroid/covariance and save the unified AnomalyScore report to `data/anomaly_scores.parquet` (FR-006)
- [ ] T023 [US2] Generate synthetic random noise baseline (Gaussian, same dim) and calculate its distance to $\mu_{benign}$ for comparison
- [ ] T024 [US2] Save trained model artifact and prediction probabilities to `results/predictions.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance Evaluation and Resource Profiling (Priority: P3)

**Goal**: Evaluate classifier metrics, compare against baseline, and verify pipeline fits 6h/7GB constraints.

**Independent Test**: Run evaluation script; verify report contains Precision/Recall/F1, baseline comparison, and resource logs confirming <6h/<7GB.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T025 [P] [US3] Contract test for evaluation report schema in `tests/contract/test_report_schema.py` (Written BEFORE T027/T029; depends on spec.md/contracts schema definition, not implementation tasks)
- [ ] T026 [P] [US3] Integration test for full pipeline resource constraints in `tests/integration/test_resource_limits.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `src/models/eval.py` to calculate Precision, Recall, F1-score and compare against stratified random baseline (FR-003)
- [ ] T027b [US3] Implement `src/models/eval.py` to read `data/anomaly_scores.parquet` (from T022b), calculate Pearson correlation (r) between Mahalanobis distance and jailbreak labels, **perform hypothesis test**, and verify threshold (p < 0.05 or r > 0.3) as required by SC-005; save results to `results/correlation.json`
- [ ] T028 [US3] Implement `src/models/eval.py` to profile RAM usage (`tracemalloc`/`psutil`) and total wall-clock time (FR-004)
- [ ] T029 [US3] Generate `results/report.md` containing all metrics and `results/resource_log.json`
- [ ] T030 [US3] Implement state update logic to compute SHA-256 hashes for all artifacts and update `state/projects/PROJ-835-llmxive-follow-up-extending-a-survey-of.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Orchestration & CLI

**Purpose**: Connect all phases into a single executable pipeline

- [ ] T031 [P] Implement `src/cli/run_pipeline.py` to orchestrate download -> embed -> train -> eval -> state-update
- [ ] T032 [P] Add CLI argument parsing for dataset sampling size and batch size configuration
- [ ] T033 [P] Create `quickstart.md` with instructions to run the full pipeline on a free-tier runner

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Data Verification (Phase 2.5)**: Depends on Foundational; BLOCKS Phase 3
- **User Stories (Phase 3+)**: All depend on Foundational and Data Verification phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational + Data Verification - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational + Data Verification - Depends on T012/T013/T014 (Data/Embeddings)
- **User Story 3 (P3)**: Can start after Foundational + Data Verification - Depends on T020/T021/T022 (Model/Predictions)

### Within Each User Story

- Tests (Mandatory) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational + Data Verification phases complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Specific Task Dependencies

- **T020** (Split) MUST complete before **T021** (Train) and **T022** (Centroid)
- **T022** (Centroid) MUST complete before **T022b** (Unified AnomalyScore)
- **T022b** (Unified AnomalyScore) MUST complete before **T027b** (Correlation/Validation)
- **T025** (Contract Test) depends on the **specification** of the schema (from spec.md/contracts), NOT on implementation tasks T027/T029.
- **T027b** (Correlation) is NOT parallel-safe ([P] removed) as it consumes T022b outputs.
- **T025** (Contract Test) is written before T027/T029 to define the schema, but logically depends on the spec, not the implementation.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (MANDATORY):
Task: "Contract test for embedding output schema in tests/contract/test_embedding_schema.py"
Task: "Integration test for error handling in tests/integration/test_error_handling.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/download.py"
Task: "Implement src/data/preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: Data Verification (CRITICAL - blocks US1)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational + Data Verification → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Data Verification together
2. Once Foundational + Data Verification is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
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
- **Critical**: T020 must complete before T021/T022; T022 must complete before T022b; T022b must complete before T027b.
- **Critical**: T025 depends on the *specification* of the schema (from spec.md/contracts), not on the implementation tasks T027/T029.
- **Critical**: T014 must output to `data/embeddings.parquet` as per plan.md.
- **Critical**: T022b must calculate Mahalanobis distance for *all* samples to generate the unified AnomalyScore report.