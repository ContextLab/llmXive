# Tasks: llmXive follow-up: extending "DelTA: Discriminative Token Credit Assignment for Reinforcement Learning"

**Input**: Design documents from `/specs/001-delta-static-approximation/`
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

- [ ] T001a Create directory structure: `code/data`, `code/models`, `code/eval`, `data/raw`, `data/processed`, `contracts`
- [ ] T001b Initialize `code/`, `data/`, `tests/` with `__init__.py` and `.gitkeep` files
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pinned: `torch`, `transformers`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `spacy`, `sentence-transformers`, `delta`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `contracts/delta_oracle.schema.yaml` defining the JSON structure for DelTA coefficients (token_id, coefficient, variance check)
- [ ] T005 Create `contracts/static_features.schema.yaml` defining the JSON structure for feature vectors (n-grams, POS, semantic similarity)
- [ ] T006 Create `contracts/predictions.schema.yaml` defining the JSON structure for model outputs (predicted_coefficient, true_coefficient, example_id)
- [X] T007 Implement `code/config.py` to manage paths, seeds (a set), and hyperparameters (N=200 examples per Plan Feasibility, 2-layer MLP config)
- [X] T008 Implement `code/main.py` pipeline orchestrator with error handling for numerical instability (edge case: catch RuntimeError/ValueError, log to error.log, skip to next example)
- [X] T009 Setup logging infrastructure in `code/main.py` to track execution time against 6-hour limit and memory usage
- [X] T009b Implement logic in `code/main.py` to measure wall-clock time of main.py execution, report it in final output, and fail explicitly if > 6 hours (SC-003). This is a global constraint check.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Ground-Truth DelTA Coefficients (Priority: P1) 🎯 MVP

**Goal**: Generate ground-truth DelTA Coefficients for a subset of GSM8K using Phi-3-mini as the Oracle.

**Independent Test**: Execute on a fixed subset of 200 GSM8K examples (seed=42) and verify the output file contains a valid DelTA Coefficient for every token, with variance > 1e-9 and no NaNs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for GSM8K filtering logic in `tests/unit/test_data_download.py` (verify verified correctness labels)
- [X] T011 [P] [US1] Unit test for DelTA coefficient variance check in `tests/unit/test_oracle.py` (assert variance > 1e-9)

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download_gsm8k.py` (FR-001): Download GSM8K from HuggingFace, filter for verified correct solutions, save to `data/raw/gsm8k_verified.parquet`. Ensure at least 200 examples are available.
- [X] T013 [US1] Implement `code/data/generate_oracle.py` (FR-002): Load Phi-3-mini (full precision, CPU-only) [Note: Plan overrides Spec's Llama-3-8B for feasibility], run DelTA algorithm (using `delta` library or explicit gradient logic) on N=200 stratified examples (seed=42). Handle numerical instability by catching exceptions, logging to error.log, and excluding failed examples. **FAIL** if fewer than 200 valid examples remain. <!-- ATOMIZE: requested -->
- [X] T014 [US1] Implement variance validation in `code/data/generate_oracle.py` (FR-002): Ensure output coefficients have variance > 1e-9; fail explicitly if not met.
- [ ] T015 [US1] Save output to `data/processed/delta_coefficients.json` conforming to `contracts/delta_oracle.schema.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Static Predictor Model (Priority: P2)

**Goal**: Train a lightweight 2-layer MLP on CPU using only static input features to predict DelTA Coefficients.

**Independent Test**: Train the model on the training split using only n-grams, POS, and semantic similarity (no hidden states) and verify convergence on CPU without GPU/CUDA.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for feature extraction independence in `tests/unit/test_features.py` (assert no hidden states from Oracle are used)
- [X] T017 [P] [US2] Integration test for MLP training loop in `tests/integration/test_training.py` (verify loss decreases on CPU)

### Implementation for User Story 2

- [ ] T018 [US2] Implement `code/data/extract_features.py` (FR-003): Extract n-gram stats, POS tags (using `spacy`), and semantic similarity to an initial subset of GSM8K traces (using sentence-transformers/all-MiniLM-L6-v2) [Plan override: avoids circularity vs Spec's Llama-3-8B embeddings] for every token. **DEPENDS ON T012 (raw GSM8K examples) and T005 (schema). Explicitly DO NOT depend on T015**. Filter OOV tokens or assign default vectors. Output to `data/processed/static_features.parquet` with columns [token_id, feature_vector].
- [X] T019 [US2] Implement feature vector handling in `code/data/extract_features.py` (Edge Case): Filter OOV tokens or assign default vectors to prevent training errors.
- [ ] T020 [US2] Save extracted features to `data/processed/static_features.json` conforming to `contracts/static_features.schema.yaml`
- [X] T021 [US2] Implement `code/models/mlp.py` (FR-004): Define a multi-layer perceptron (MLP) with ReLU activation and a hidden layer of moderate capacity.
- [ ] T022 [US2] Implement `code/models/train.py` (FR-004): Training loop using only extracted static features (T020), ground truth coefficients (T015), and using the model defined in T021 on CPU; ensure no CUDA/GPU calls; save model to `data/processed/mlp_model.pt`
- [ ] T023 [US2] Generate predictions for the held-out test set and save to `data/processed/predictions.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluate Rank Correlation and Significance (Priority: P3)

**Goal**: Compute Spearman rank correlation, perform permutation tests, and analyze feature importance to distinguish signal emergence from poor proxies.

**Independent Test**: Run evaluation on test set to output Spearman correlation, p-value (permutation test), and feature importance scores.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for Spearman calculation against random baseline in `tests/unit/test_metrics.py`
- [ ] T025 [P] [US3] Unit test for permutation test logic (a sufficient number of shuffles) in `tests/unit/test_metrics.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/eval/metrics.py` (FR-005, FR-006): Compute Spearman rank correlation between predicted (T023) and true (T015) coefficients. Compare against random baseline (N(0,1), seed=42) and **uniform baseline** (defined as mean of the true coefficients distribution).
- [ ] T026b [US3] Implement uniform baseline generation and comparison in `code/eval/metrics.py` (FR-005): Explicitly generate uniform weights as the mean of the true coefficients distribution (derived from T015) and compute Spearman correlation against true coefficients for comparison.
- [ ] T027 [US3] Implement permutation test in `code/eval/metrics.py` (FR-006): Shuffle targets repeatedly to generate null distribution; calculate p-value (FR-006)
- [ ] T028 [US3] Implement `code/eval/interpret.py` (FR-008): Compute SHAP values or permutation importance. **Decision Logic**: If mean SHAP < 0.05 OR feature importance is uniformly low across all types, classify result as 'features are poor proxies'. Otherwise, if features are strong but correlation low, classify as 'signal is emergent'.
- [ ] T029 [US3] Generate final report in `data/processed/evaluation_results.json` including correlation, p-value, and feature importance
- [ ] T030 [US3] Add logic to frame findings as associational (FR-007) in the report generation

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` and `README.md`
- [ ] T032 Code cleanup and refactoring to ensure memory footprint < 7 GB
- [ ] T033 Performance optimization to ensure total pipeline < 6 hours
- [ ] T034 [P] Additional unit tests in `tests/unit/` covering edge cases (numerical instability, OOV tokens)
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)**: Generates ground truth data required for US2 and US3
 - **US2 (P2)**: Requires ground truth from US1 and static features (independent of US3 logic)
 - **US3 (P3)**: Requires predictions from US2 and ground truth from US1
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2). No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). Requires US1 output (coefficients) for training.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2). Requires US1 (ground truth) and US2 (predictions) outputs.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data download/filtering before Oracle generation
- Feature extraction before Model training
- Training before Evaluation
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 can start in parallel *if* US1 is complete (US1 is the critical path)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

### Explicit Task Dependencies

- **T015** depends on **T004** (schema), **T012**, **T013**, **T014**
- **T018** depends on **T012** (raw GSM8K examples) and **T005** (schema). **DO NOT** depend on T015.
- **T020** depends on **T018**
- **T022** depends on **T021**, **T020**, **T015**
- **T023** depends on **T022**
- **T026** depends on **T023**, **T015**
- **T026b** depends on **T015**
- **T027** depends on **T026**
- **T029** depends on **T026**, **T026b**, **T027**, **T028**

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for GSM8K filtering logic in tests/unit/test_data_download.py"
Task: "Unit test for DelTA coefficient variance check in tests/unit/test_oracle.py"

# Launch implementation steps sequentially due to data flow:
Task: "Implement code/data/download_gsm8k.py" -> Must complete before
Task: "Implement code/data/generate_oracle.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Generate Ground Truth)
4. **STOP and VALIDATE**: Verify coefficients are generated, variance > 1e-9, no NaNs, and file conforms to schema.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (training on CPU, no hidden states) → Deploy/Demo
4. Add User Story 3 → Test independently (correlation, permutation, importance) → Deploy/Demo
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Critical Path)
 - Developer B: User Story 2 (Prepares feature extraction logic in parallel, waits for US1 data)
 - Developer C: User Story 3 (Prepares evaluation logic in parallel, waits for US1/US2 data)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Compute Constraint**: All tasks must run on CPU-only GitHub Actions with limited core and memory resources. Do not use 8-bit/4-bit quantization or CUDA-specific libraries.
- **Data Constraint**: Use real GSM8K data from HuggingFace; do not fabricate synthetic data.
- **Independence Constraint**: Feature extraction (US2) must NOT use hidden states from the Oracle model (US1).
- **Constraint**: N=200 examples is mandatory per Plan Feasibility. Pipeline must fail if fewer than 200 valid examples are found.
- **Model Constraint**: Oracle must use Phi-3-mini per Plan (overrides Spec's Llama-3-8B).
- **Feature Constraint**: Semantic similarity uses sentence-transformers/all-MiniLM-L6-v2 per Plan (overrides Spec's Llama-3-8B embeddings to avoid circularity).