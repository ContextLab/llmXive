# Tasks: llmXive follow-up: extending Representation Forcing for Structured Text Generation

**Input**: Design documents from `/specs/001-llmxive-rf-structured-text/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [ ] T001a [P] Create project directory structure per implementation plan: `projects/PROJ-867-llmxive-follow-up-extending-representati/` including `code/`, `data/`, `tests/`, `docs/` subdirectories
- [X] T001b [P] Initialize `code/requirements.txt` with CPU-only dependencies: `torch`, `transformers`, `datasets`, `scikit-learn`, `jsonschema`, `pyyaml`, `psutil`
- [X] T002 [P] Create `code/config.py` skeleton with placeholders for hyperparameters, paths, and seeds
- [ ] T003 [P] Create `tests/unit/`, `tests/contract/`, `tests/integration/` directory skeletons

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/resource_monitor.py` as a context manager/decorator to enforce a configurable memory limit (default 4GB) derived from the 7GB runner constraint (FR-007), with active monitoring, logging of resource trends, and process kill on overflow; include mock test for verification
- [ ] T005 [P] Implement `code/data/loaders.py` to fetch PubLayNet dataset from HuggingFace (`facebook/publaynet`) with SHA-256 checksum verification
- [X] T006a [P] Implement `code/data/verify_schema.py` to perform semantic verification of PubLayNet annotations (confirming presence of structural boxes and text content) as required by Plan Phase 0 Step 1, before processing begins
- [X] T007 [P] Create `docs/contracts/rf_token_sequence.yaml` schema definition
- [X] T008 [P] Create `docs/contracts/structured_text_output.yaml` schema definition
- [X] T009 [P] Create `docs/contracts/evaluation_metrics.yaml` schema definition
- [X] T010 [P] Implement `code/utils/stats.py` with placeholders for McNemar's test and Wilcoxon signed-rank test using `scipy.stats`
- [X] T011 [P] Implement `code/utils/validators.py` for JSON/Markdown syntax parsing and AST edit distance calculation
- [ ] T012 [P] Implement `code/data/preprocessing.py` logic for general image loading, resizing to 224x224, and basic normalization (shared across all US)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract Structural Priors via Frozen Representation Forcing (Priority: P1) 🎯 MVP

**Goal**: Extract intermediate representation tokens from a frozen RF encoder without invoking pixel-decoding layers.

**Independent Test**: The system loads a frozen encoder, processes a single image, and outputs a tensor of correct dimensionality without CUDA or pixel-decoding layers.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T013 [P] [US1] Unit test for RF token shape validation in `tests/unit/test_rf_encoder.py`
- [ ] T014 [P] [US1] Integration test for single-image extraction in `tests/integration/test_extraction.py`

### Implementation for User Story 1

- [ ] T015 [P] [US1] Implement `code/models/rf_encoder.py` wrapping `microsoft/layoutlmv3-base` with weights frozen and pixel-decoder layers disabled
- [ ] T016 [US1] Implement `code/data/preprocessing.py` logic to load images (using T005 loader), resize to 224x224, and extract RF token sequences via T015
- [ ] T017 [US1] Implement NaN detection and clamping logic in `code/data/preprocessing.py` to handle floating-point instability on CPU
- [ ] T018 [US1] Implement logic to pad/truncate token sequences to a fixed context window in `code/data/preprocessing.py`
- [ ] T019 [US1] Add error handling for corrupted/blank images to return minimal valid structure in `code/data/preprocessing.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Lightweight Autoregressive Model on RF Tokens (Priority: P2)

**Goal**: Train a small autoregressive model to map RF tokens to structured text (JSON/Markdown).

**Independent Test**: The system trains the model for a limited number of epochs (Constitution VII) and produces syntactically valid JSON/Markdown strings for a subset of validation samples.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for model output parsing in `tests/contract/test_ar_model.py`
- [ ] T021 [P] [US2] Integration test for training loop convergence in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/models/autoregressive.py` defining a lightweight transformer (~30M params) accepting RF tokens as embeddings [UNRESOLVED-CLAIM: c_69cb81b7 — status=not_enough_info]
- [ ] T023 [P] [US2] Implement `code/data/preprocessing.py` logic to create a `DataLoader` for RF token pairs (depends on T005 and T016)
- [ ] T024 [US2] Implement `code/train.py` training loop (depends on T023) with configuration for max 2 epochs (Constitution VII)
- [ ] T025 [US2] Implement `code/train.py` stopping logic (depends on T024) to enforce a hard limit of 2 epochs (Plan override of FR-003/Constitution VII) and log convergence diagnostics
- [ ] T026 [US2] Integrate `code/utils/resource_monitor.py` into training loop (depends on T004)
- [ ] T027 [US2] Implement logic to generate structured text from RF tokens and validate syntax using `jsonschema` or `markdown` parsers (depends on T011)
- [ ] T028 [US2] Implement `code/models/baseline.py` defining a simple CNN encoder for raw downsampled pixel inputs
- [ ] T029 [US2] Implement `code/train.py` logic to train the Pixel-Baseline Model under identical constraints (max 2 epochs, 4GB limit)
- [ ] T030 [US2] Implement logging of training loss and syntactic validity rate to `data/results/training_log.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently; Baseline model ready for comparison

---

## Phase 5: User Story 3 - Benchmark Against Pixel Baseline and Statistical Significance (Priority: P3)

**Goal**: Compare RF model performance against a pixel-based baseline and perform statistical significance testing.

**Independent Test**: {{claim:c_af3b40e4}}

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for statistical significance output in `tests/contract/test_stats.py`
- [ ] T032 [P] [US3] Integration test for end-to-end benchmark pipeline in `tests/integration/test_benchmark.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/evaluate.py` to compute syntactic validity rates and AST edit distance for both RF and Baseline models
- [ ] T036 [US3] Implement `code/utils/stats.py` logic to perform Wilcoxon signed-rank test on `data/results/aggregated_scores.json` (seed-level metrics) to determine statistical significance (FR-006)
- [ ] T034 [US3] Implement `code/main.py` orchestration to run RF and Baseline training, evaluation, and statistical comparison sequentially across multiple random seeds (depends on T033, T036)
- [ ] T035 [US3] Implement logic to aggregate per-seed results from `data/results/` into `data/results/aggregated_scores.json` (seed-level metrics)
- [ ] T037 [US3] Log total runtime and memory peak usage to `data/results/metrics.json` (SC-005, FR-007)
- [ ] T038 [US3] Implement verification logic to compare logged runtime against the 6-hour CI job threshold and raise `SystemExit(1)` if exceeded (SC-005)

**Checkpoint**: All user stories should now be independently functional; Statistical significance computed

---

## Phase 6: User Story 4 - Validate Structural Prior Independence (Priority: P4)

**Goal**: Validate that RF tokens capture structural information distinct from pixel features on a "structure-only" subset.

**Independent Test**: The system evaluates both models on low-contrast/high-complexity images and reports superior RF validity rates.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T039 [P] [US4] Unit test for structure-only subset filtering logic in `tests/unit/test_subset_filter.py`
- [ ] T040 [P] [US4] Integration test for structural independence validation in `tests/integration/test_structure_independence.py`

### Implementation for User Story 4

- [ ] T041 [US4] Implement `code/data/preprocessing.py` logic to filter for "structure-only" subset (low visual contrast, high structural complexity) and `code/evaluate.py` logic to run specific evaluation on this subset (depends on T012, T033)
- [ ] T042 [US4] Implement `code/main.py` logic to report comparative validity rates on the structure-only subset
- [ ] T043 [US4] Log "complexity overflow" metrics for images exceeding token capacity in `data/results/complexity_metrics.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in `docs/quickstart.md` and `docs/contracts/`
- [ ] T045 Code cleanup and refactoring of `code/` directory
- [ ] T046 Performance optimization for data loading (batching) to stay within 6h runtime
- [ ] T047 [P] Additional unit tests for edge cases (blank pages, NaNs) in `tests/unit/`
- [ ] T048 Run `quickstart.md` validation to ensure full pipeline reproducibility on CPU-only runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for token extraction
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 for comparison
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US1 and US3 for subset evaluation

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for RF token shape validation in tests/unit/test_rf_encoder.py"
Task: "Integration test for single-image extraction in tests/integration/test_extraction.py"

# Launch all models for User Story 1 together:
Task: "Implement code/models/rf_encoder.py wrapping microsoft/layoutlmv3-base"
Task: "Implement code/data/preprocessing.py to load images and extract RF token sequences"
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
- **CRITICAL**: All tasks must run on CPU-only free-tier runners (≤4GB RAM, ≤6h) [UNRESOLVED-CLAIM: c_90ed94a4 — status=not_enough_info]. No GPU/CUDA tasks allowed. 