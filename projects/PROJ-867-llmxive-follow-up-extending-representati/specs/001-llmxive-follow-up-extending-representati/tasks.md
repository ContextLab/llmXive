# Tasks: llmXive follow-up: extending Representation Forcing for Structured Text Generation

**Input**: Design documents from `/specs/001-llmxive-rf-structured-text/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Must run sequentially (same file or data dependency)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Initialize project structure: Create `code/`, `data/`, `tests/`, `docs/` directories and their sub-skeletons (`tests/unit`, `tests/contract`, `tests/integration`) in `projects/PROJ-867-llmxive-follow-up-extending-representati/`
- [X] T001d [P] Initialize `code/requirements.txt` with CPU-only dependencies: `torch`, `transformers`, `datasets`, `scikit-learn`, `jsonschema`, `pyyaml`, `psutil`
- [X] T002 [P] Create `code/config.py` skeleton with placeholders for hyperparameters, paths, and seeds

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/resource_monitor.py` as a context manager/decorator to enforce configurable memory limit (4GB) and significant disk usage limit (12GB, checked every 10s via `os.disk_usage`) derived from FR-007, with active monitoring, logging of resource trends, and process kill on overflow; include mock test for verification
- [X] T005 [P] Implement `code/data/loaders.py` to fetch PubLayNet dataset from HuggingFace (`facebook/publaynet`) with SHA-256 checksum verification
- [X] T006 [P] Implement `code/data/verify_schema.py` to perform semantic verification of PubLayNet annotations: parse JSONL, assert presence of 'bbox' and 'text' fields per image, and raise a descriptive error if missing (Plan Phase 0 Step 1, FR-003)
- [X] T007 [P] Create `docs/contracts/rf_token_sequence.yaml` schema definition
- [X] T008 [P] Create `docs/contracts/structured_text_output.yaml` schema definition
- [X] T009 [P] Create `docs/contracts/evaluation_metrics.yaml` schema definition
- [X] T010 [P] Implement `code/utils/stats.py` with placeholders for McNemar's test and Wilcoxon signed-rank test using `scipy.stats`
- [X] T011 [P] Implement `code/utils/validators.py` for JSON/Markdown syntax parsing and AST edit distance calculation
- [X] T012 [P] Implement `code/data/preprocessing.py` logic for general image loading, resizing to 224x224, and basic normalization (shared across all US)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract Structural Priors via Frozen Representation Forcing (Priority: P1) 🎯 MVP

**Goal**: Extract intermediate representation tokens from a frozen RF encoder without invoking pixel-decoding layers.

**Independent Test**: The system loads a frozen encoder, processes a single image, and outputs a tensor of correct dimensionality without CUDA or pixel-decoding layers.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T013 [P] [US1] Unit test for RF token shape validation in `tests/unit/test_rf_encoder.py`
- [X] T014 [P] [US1] Integration test for single-image extraction in `tests/integration/test_extraction.py`

### Implementation for User Story 1

- [X] T015 [S] [US1] Implement `code/models/rf_encoder.py` wrapping `microsoft/layoutlmv3-base` with weights frozen. **Critical**: Verify pixel-decoder weights are NOT loaded into memory; ensure decoder layers are explicitly excluded during model initialization. Add a unit test in `tests/unit/test_rf_encoder.py` that asserts `model.decoder` is None or not instantiated. Verify via graph inspection that the forward pass does not invoke pixel-decoding layers (FR-001, US-1).
- [ ] T016 [S] [US1] Implement `code/data/preprocessing.py` logic to: 1) `load_image` (using T005 loader), 2) `extract_tokens` (via T015), 3) `clamp_nans` (handle CPU floating-point instability), 4) `pad_sequences` (fixed context window), and 5) `handle_corruption` (return minimal valid structure for blank/corrupted images). **Must run after T015**. Output: Must produce `data/processed/tokens.parquet`.
- [X] T017 [S] [US1] Implement logic to pad/truncate token sequences to a fixed context window in `code/data/preprocessing.py`. **Must run after T016** to process the cleaned tokens. (Note: Merged into T016, kept for dependency tracking if split later).
- [X] T018 [S] [US1] Implement error handling for corrupted/blank images to return minimal valid structure in `code/data/preprocessing.py`. **Must run after T017**. (Note: Merged into T016).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Lightweight Autoregressive Model on RF Tokens (Priority: P2)

**Goal**: Train a small autoregressive model to map RF tokens to structured text (JSON/Markdown).

**Independent Test**: The system trains the model for a limited number of epochs (Constitution VII) and produces syntactically valid JSON/Markdown strings for a subset of validation samples.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output parsing in `tests/contract/test_ar_model.py`
- [X] T021 [P] [US2] Integration test for training loop convergence in `tests/integration/test_training.py`

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement `code/models/autoregressive.py` defining a lightweight transformer accepting RF tokens as embeddings
- [ ] T023 [S] [US2] Implement `code/data/preprocessing.py` logic to create a `DataLoader` for RF token pairs. **Must consume extracted token artifacts (data/processed/tokens.parquet) produced by T016**. Depends on T005 and T016 completion.
- [X] T024 [S] [US2] Implement `code/models/baseline.py` defining a simple CNN encoder (limited depth) for raw downsampled (224x224) image pixels, strictly adhering to the constraints defined in T028a (FR-004, Plan Phase 0 Step 3).
- [X] T025 [S] [US2] Implement `code/train.py` training loop (depends on T022, T023, T024). **Critical**: Implement validation loss plateau detection logic *only* for logging/diagnostics. **Formal waiver of FR-003 convergence stop condition**: The training loop must NOT stop on plateau; the hard epoch limit (Constitution VII) is the ONLY stopping criterion. Explicitly document this override in code comments referencing Constitution VII. Integrate `code/utils/resource_monitor.py` (T004) for both RF and Baseline training paths.
- [X] T026 [S] [US2] Implement `code/train.py` logic to train the Pixel-Baseline Model under identical constraints (max 2 epochs, 4GB RAM/12GB disk limit).
- [ ] T027 [S] [US2] Implement logic to generate structured text from RF tokens and validate syntax using `jsonschema` or `markdown` parsers (depends on T011).
- [ ] T028 [S] [US2] Log training loss and syntactic validity rate to `data/results/training_log.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently; Baseline model ready for comparison

---

## Phase 5: User Story 3 - Benchmark Against Pixel Baseline and Statistical Significance (Priority: P3)

**Goal**: Compare RF model performance against a pixel-based baseline and perform statistical significance testing.

**Independent Test**:

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for statistical significance output in `tests/contract/test_stats.py`
- [ ] T032 [P] [US3] Integration test for end-to-end benchmark pipeline in `tests/integration/test_benchmark.py`

### Implementation for User Story 3

- [ ] T033 [S] [US3] Implement `code/evaluate.py` to compute syntactic validity rates and AST edit distance for both RF and Baseline models.
- [ ] T034 [S] [US3] Implement `code/main.py` orchestration to run RF and Baseline training, evaluation, and statistical comparison sequentially across multiple random seeds. **Critical**: Must generate and structure `data/results/aggregated_scores.json` with per-image scores for *each random seed* (raw data). Verify input structure before aggregation. Perform McNemar's test on binary validity rates (FR-006).
- [ ] T035 [S] [US3] Implement `code/utils/stats.py` logic to perform Wilcoxon signed-rank test on `data/results/aggregated_scores.json` (depends on T034). **Critical**: Perform test on the per-image distribution to determine statistical significance (FR-006).
- [ ] T036 [S] [US3] Log total runtime and memory peak usage to `data/results/metrics.json` (SC-005, FR-007).
- [ ] T037 [S] [US3] Implement verification logic to compare logged runtime against the CI job threshold and raise `SystemExit(1)` if exceeded (SC-005).

**Checkpoint**: All user stories should now be independently functional; Statistical significance computed

---

## Phase 6: User Story 4 - Validate Structural Prior Independence (Priority: P4)

**Goal**: Validate that RF tokens capture structural information distinct from pixel features on a "structure-only" subset.

**Independent Test**: The system evaluates both models on low-contrast/high-complexity images and reports superior RF validity rates.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T038 [P] [US4] Unit test for structure-only subset filtering logic in `tests/unit/test_subset_filter.py`
- [ ] T039 [P] [US4] Integration test for structural independence validation in `tests/integration/test_structure_independence.py`

### Implementation for User Story 4

- [ ] T040 [S] [US4] Implement `code/data/preprocessing.py` logic to filter for "structure-only" subset (low visual contrast, high structural complexity). Depends on T012, T033.
- [ ] T041 [S] [US4] Implement `code/main.py` logic to run evaluation on the structure-only subset and report comparative validity rates. Depends on T040.
- [ ] T042 [S] [US4] Log "complexity overflow" metrics for images exceeding token capacity in `data/results/complexity_metrics.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Update `docs/quickstart.md` with specific sections: "Environment Setup", "Running the Pipeline", "Interpreting Results". Update `docs/contracts/` with final schema versions.
- [ ] T044 [P] Code cleanup: Remove unused imports, simplify `config.py` defaults, and refactor `code/utils/` for modularity.
- [ ] T045 [P] Performance optimization: Implement batching strategy (batch size 4) in data loaders to stay within 6h runtime.
- [ ] T046 [P] Add specific unit tests for edge cases: blank pages, NaNs, and complexity overflow in `tests/unit/`.
- [ ] T047 [P] Run `quickstart.md` validation to ensure full pipeline reproducibility on CPU-only runner.

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
- [S] tasks = sequential dependencies (same file or data flow)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: No GPU/CUDA tasks allowed.