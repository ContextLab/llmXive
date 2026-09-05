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

- [X] T001a Create directory structure: `code/data`, `code/models`, `code/eval`, `data/raw`, `data/processed`, `contracts`
- [X] T001b Initialize `code/`, `data/`, `tests/` with `__init__.py` and `.gitkeep` files
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pinned: `torch`, `transformers`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `spacy`, `sentence-transformers`, `pytest`). **REMOVED**: `delta` (non-existent package; algorithm implemented in code/).
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. These tasks create the validation contracts required for all data artifacts and document feasibility deviations.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T004, T005, T006 are hard prerequisites for T015, T018, T020 respectively.

- [X] T002a **DEVIATION LOG**: Create `deviation_log.md` in `specs/001-delta-static-approximation/` documenting the N=500/Min=10 constraint and **Llama-3-8B** Oracle model choice. Explicitly reference **Constitution Principle VII** (Oracle Ground-Truth Generation) and document Llama-3-8B as the required model. **ACTION**: Write deviation details and link to Plan section.
- [X] T002b **CONFIG UPDATE**: Update `code/config.py` to reflect the Plan constraints: set `N_EXAMPLES_TARGET=500`, `N_EXAMPLES_MIN=10`, `ORACLE_MODEL="meta-llama/Meta-Llama-8B"`. **ACTION**: Implement configuration defaults matching the Deviation Log.
- [X] T004 Create `contracts/delta_oracle.schema.yaml` defining the JSON structure for DelTA coefficients (token_id, coefficient, variance check). **ACTION**: Write full YAML content.
- [X] T005 Create `contracts/static_features.schema.yaml` defining the JSON structure for feature vectors (n-grams, POS, semantic similarity). **ACTION**: Write full YAML content.
- [X] T006 Create `contracts/predictions.schema.yaml` defining the JSON structure for model outputs (predicted_coefficient, true_coefficient, example_id). **ACTION**: Write full YAML content.
- [X] T007 Implement `code/config.py` to manage paths, seeds (a representative sample), and hyperparameters (N=500 target, N=10 min, MLP config).
- [X] T008 Implement `code/main.py` pipeline orchestrator with error handling for numerical instability (edge case: catch RuntimeError/ValueError, log to error.log, skip to next example). **INCLUDES**: Logic to measure wall-clock time for the **CPU-only portion** (target <= 4 hours per SC-003) and log it. The GPU offload step is timed separately.
- [X] T009 Setup logging infrastructure in `code/main.py` to track execution time against a predefined **4-hour** duration limit and memory usage. **ENHANCEMENT**: Ensure `data/processed/metrics.json` includes a `total_runtime_seconds` field for SC-003 verification (CPU portion only).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Ground-Truth DelTA Coefficients (Priority: P1) 🎯 MVP

**Goal**: Generate ground-truth DelTA Coefficients for a subset of GSM8K using Llama-3-8B as the Oracle.

**Independent Test**: Execute on a fixed subset of 500 GSM8K examples (seed=42) and verify the output file contains a valid DelTA Coefficient for every token, with variance > 1e-9 and no NaNs. If <500 found, proceed with min=10 and log warning.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for GSM8K filtering logic in `tests/unit/test_data_download.py` (verify verified correctness labels)
- [X] T011 [P] [US1] Unit test for DelTA coefficient variance check in `tests/unit/test_oracle.py` (assert variance > 1e-9)

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download_gsm8k.py` (FR-001): Download GSM8K from HuggingFace, filter for verified correct solutions, save to `data/raw/gsm8k_verified.parquet`. Target examples; if <500 available, proceed with all available (min 10) and log warning. **VERIFICATION**: Assert source dataset contains > 10 valid examples before proceeding.
- [ ] T013 [US1] Implement `code/data/generate_oracle.py` (FR-002): Load **meta-llama/Meta-Llama-3-8B** (full precision), run DelTA algorithm using explicit `torch.autograd.grad` logic with `retain_graph=True` on up to 500 stratified examples (seed=42). Handle numerical instability by catching exceptions, logging to error.log, and excluding failed examples. **FALLBACK**: If <500 valid examples remain but >=10, proceed with warning. **FAIL** if <10 valid examples remain. **ASSERT GLOBAL VARIANCE > 1e-9**; fail explicitly if not met. **VERIFICATION**: Assert output file contains coefficients for all examples in the dataset.
- [ ] T015a [US1] Save output to `data/processed/delta_coefficients.json` conforming to `contracts/delta_oracle.schema.yaml`. **BUILD-TIME DEPENDENCY**: T004 (schema file must exist). **DATA DEPENDENCY**: T012, T013 (data must be generated). **VALIDATION**: At runtime, validate the generated JSON content against the schema to ensure data integrity.
- [ ] T015b [US1] Validate `data/processed/delta_coefficients.json` against `contracts/delta_oracle.schema.yaml` using `jsonschema`. **BLOCKED BY**: T015a.
- [ ] T015c [US1] Verify global variance of coefficients > 1e-9. **BLOCKED BY**: T015a. **FAIL**: If variance <= 1e-9, raise `ERR_TRIVIAL_TARGET`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Static Predictor Model (Priority: P2)

**Goal**: Train a lightweight multi-layer perceptron on CPU using only static input features to predict DelTA Coefficients.

**Independent Test**: Train the model on the training split using only n-grams, POS, and semantic similarity (no hidden states) and verify convergence on CPU without GPU/CUDA.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for feature extraction independence in `tests/unit/test_features.py` (assert no hidden states from Oracle are used)
- [X] T017 [P] [US2] Integration test for MLP training loop in `tests/integration/test_training.py` (verify loss decreases on CPU)

### Implementation for User Story 2

- [ ] T018a [US2] **REFERENCE SET**: Implement `code/data/download_reference.py`: Download the **OpenMathInstruct-1** dataset from HuggingFace (verified source). Select a representative sample of examples (seed=42, stratified by length) and save to `data/processed/openmath_reference.parquet`. **ACTION**: Create deterministic subset file for semantic similarity calculations. **DEPENDS ON**: None (external data). **NOTE**: This is an EXTERNAL reference set, distinct from GSM8K, to ensure Static-Input Independence.
- [ ] T018 [US2] Implement `code/data/extract_features.py` (FR-003): Extract n-gram stats, POS tags (using `spacy`), and semantic similarity to the reference set (`data/processed/openmath_reference.parquet` from T018a) using `sentence-transformers/all-MiniLM-L6-v2`. **DEPENDS ON**: T012, T018a, T005. Process a representative set of examples from T012. Filter OOV tokens or assign default vectors. Output to `data/processed/static_features.parquet` with columns [token_id, feature_vector]. **NO CIRCULARITY**: Do NOT use GSM8K as the reference set.
- [X] T019 [US2] Implement feature vector handling in `code/data/extract_features.py` (Edge Case): Filter OOV tokens or assign default vectors to prevent training errors.
- [ ] T020 [US2] Save extracted features to `data/processed/static_features.parquet` conforming to `contracts/static_features.schema.yaml`. **BLOCKED BY**: T018, T005. **FORMAT NOTE**: Use parquet to match T018 output. **VALIDATION**: Validate output against schema before saving.
- [ ] T021a [US2] Implement `code/models/mlp.py` (FR-004): Define a **2-layer MLP** with **128 hidden units per layer** and **ReLU activation**. **DEPENDS ON**: T005 (schema for input/output dimensions).
- [ ] T022 [US2] Implement `code/models/train.py` (FR-004): Training loop using only extracted static features (T020), ground truth coefficients (T015a), and using the model defined in T021a on CPU; ensure no CUDA/GPU calls; save model to `data/processed/mlp_model_static.pt`. **DEPENDS ON**: T020, T015a, T021a.
- [ ] T023 [US2] Generate predictions for the held-out test set using the Static Model and save to `data/processed/predictions_static.json`. **DEPENDS ON**: T022.

---

## Phase 4b: Upper Bound Oracle Implementation (Plan Phase 2.2)

**Goal**: Implement the Upper Bound Oracle to distinguish 'Emergent Signal' from 'Poor Proxies'.

- [ ] T021d-Gen [US2/Control] Implement `code/oracle/generate_upper_bound.py`: Load **meta-llama/Meta-Llama-3-8B** (matching Oracle model), extract hidden states for the same tokens used in T013, and save to `data/processed/hidden_states.parquet`. **DEPENDS ON**: T013, T012. **NOTE**: This is the control experiment generation step.
- [ ] T021d [US2/Control] Extract hidden states from **meta-llama/Meta-Llama-3-8B** for the same tokens used in T013. Save to `data/processed/hidden_states.parquet`. **DEPENDS ON**: T013, T012. **NOTE**: This is the control experiment.
- [ ] T021b [US2/Control] Implement `code/models/train_upper.py` (Plan Phase 2.2): Training loop using hidden states (T021d-Gen/T021d) and ground truth coefficients (T015a) to train a 2-layer MLP (same architecture as T021a). Save to `data/processed/mlp_model_upper.pt`. **DEPENDS ON**: T021d-Gen, T015a, T021a.
- [ ] T021c [US2/Control] Generate predictions for the held-out test set using the Upper Bound Model and save to `data/processed/predictions_upper.json`. **DEPENDS ON**: T021b.

**Checkpoint**: At this point, User Stories 1 AND 2 (Static + Upper Bound) should both work independently

---

## Phase 5: User Story 3 - Evaluate Rank Correlation and Significance (Priority: P3)

**Goal**: Compute Spearman rank correlation, Kendall's Tau, Bootstrap CI, and perform permutation tests to distinguish signal emergence from poor proxies.

**Independent Test**: Run evaluation on test set to output Spearman, Kendall, CI, p-value (permutation test), and classification result.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for Spearman calculation against random baseline in `tests/unit/test_metrics.py`
- [X] T025 [P] [US3] Unit test for permutation test logic (a sufficient number of shuffles) in `tests/unit/test_metrics.py`

### Implementation for User Story 3

- [ ] T026b-Gen [US3] **UNIFORM BASELINE**: Implement `code/eval/baseline_uniform.py`: Generate a **uniform weight vector** (constant 1/N) as the primary uniform baseline (SC-001 compliant). **VERIFY**: Normalize the vector to match the scale of the DelTA coefficients (mean=0, std=1 or equivalent scaling). Save to `data/processed/uniform_baseline.json`. **DEPENDS ON**: T015a, T023, T021c (to access split logic/indices). **NOTE**: This baseline is mathematically independent of the training data distribution to ensure fairness. **NO SCALING** to match variance.
- [ ] T026b-Rand [US3] **RANDOM BASELINE**: Implement `code/eval/baseline_random.py`: Generate a **random baseline** vector from N(0,1) with seed=42. Save to `data/processed/random_baseline.json`. **DEPENDS ON**: T015a, T023, T021c.
- [ ] T026 [US3] Implement `code/eval/metrics.py` (FR-005, FR-006): Compute Spearman rank correlation between predicted (T023, T021c) and true (T015a) coefficients. Compare against random baseline (from T026b-Rand) and **uniform baseline** (from T026b-Gen). **DEPENDS ON**: T023, T021c, T015a, T026b-Gen, T026b-Rand.
- [ ] T026c [US3] Implement Kendall's Tau correlation in `code/eval/metrics.py` (Plan Phase 3.2). **DEPENDS ON**: T023, T021c, T015a.
- [ ] T026d [US3] Implement Confidence Intervals via Bootstrap using a sufficient number of iterations. in `code/eval/metrics.py` (Plan Phase 3.2). **DEPENDS ON**: T023, T021c, T015a.
- [ ] T027 [US3] Implement permutation test in `code/eval/metrics.py` (FR-006): **SHUFFLE TOKEN-LEVEL COEFFICIENTS WITHIN EACH EXAMPLE ID** repeatedly to generate null distribution; calculate p-value (FR-006). This preserves the example structure while breaking token-level signal. **DEPENDS ON**: T026.
- [ ] T028a [US3] **THRESHOLD DERIVATION**: Implement `code/eval/threshold_derivation.py`: Select a deterministic subset (seed=42) of T022 predictions. Compute Permutation Importance scores. Calculate a high percentile of absolute Permutation Importance values. Write this value to `data/processed/permutation_threshold.json` as `PERM_IMPORTANCE_THRESHOLD`. **DEPENDS ON**: T022. **FAIL**: If T022 artifacts are missing, fail explicitly with error code 1.
- [ ] T028 [US3] Implement `code/eval/interpret.py` (FR-008, Plan Phase 3.3): Compute Permutation Importance. **Decision Logic**: Use **Permutation Importance** and correlation thresholds as primary (FR-008).
    - **Emergent Signal**: Static Correlation (Low/Not Significant) AND Permutation Importance (Mean >= 0.01).
    - **Poor Proxies**: Static Correlation (Low/Not Significant) AND Permutation Importance (Mean < 0.01).
    - **Significant**: Static Correlation (High/Significant).
    - **Note**: The comparison against the Upper Bound Oracle (T021c) is **OPTIONAL** and for diagnostic purposes only; the primary classification must rely on the Permutation Importance logic defined in FR-008.
    **DEPENDS ON**: T023, T026, T028a. (T021c is optional).
- [ ] T029 [US3] Generate final report in `data/processed/evaluation_results.json` including correlation (Spearman, Kendall), CI, p-value, and classification result (Emergent/Poor Proxies/Significant). **DEPENDS ON**: T026, T026b-Gen, T026b-Rand, T026c, T026d, T027, T028.
- [ ] T030 [US3] Add logic to frame findings as associational (FR-007) and write `causal_disclaimer` field to `data/processed/metrics.json`. **DEPENDS ON**: T029, T008. **ACTION**: Ensure `metrics.json` exists (from T008) before writing `causal_disclaimer`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` and `README.md`
- [ ] T032 Code cleanup and refactoring to ensure memory footprint < 7 GB
- [ ] T033 **SC-003 VERIFICATION**: Read `data/processed/metrics.json` (from T008/T009) and explicitly verify `total_runtime_seconds` for the **CPU-only pipeline** is less than the **4-hour** limit (SC-003). If exceeded, log a critical failure. **DEPENDS ON**: T009, T008. **NOTE**: This limit excludes the GPU offload time.
- [ ] T034 [P] Additional unit tests in `tests/unit/` covering edge cases (numerical instability, OOV tokens)
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**. T004, T005, T006 must be marked complete before T015, T018, T020 can proceed.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)**: Generates ground truth data required for US2 and US3
 - **US2 (P2)**: Requires ground truth from US1 and static features (independent of US3 logic)
 - **US2/Control (Upper Bound)**: Requires ground truth from US1 and hidden states
 - **US3 (P3)**: Requires predictions from US2 (Static & Upper Bound) and ground truth from US1
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2). No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). Requires US1 output (coefficients) for training.
- **Upper Bound Oracle**: Can start after Foundational (Phase 2). Requires US1 output (coefficients) and hidden states.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2). Requires US1 (ground truth), US2 (Static predictions), and Upper Bound predictions.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data download/filtering before Oracle generation
- Feature extraction before Model training
- Training before Evaluation
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 (Static) and Upper Bound can start in parallel *if* US1 is complete (US1 is the critical path)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

### Explicit Task Dependencies

- **T015a** depends on **T004** (schema), **T012**, **T013**. **BLOCKED BY T004 and T012**.
- **T018a** depends on **T012** (for context) but downloads external data.
- **T018** depends on **T012** (raw GSM8K examples), **T018a** (reference set), and **T005** (schema). **BLOCKED BY T018a**.
- **T020** depends on **T018** and **T005**. **BLOCKED BY T005**.
- **T022** depends on **T021a**, **T020**, **T015a**. **BLOCKED BY T020 and T015a**.
- **T023** depends on **T022**.
- **T021d-Gen** depends on **T013**, **T012**.
- **T021b** depends on **T021d-Gen**, **T015a**, **T021a**.
- **T021c** depends on **T021b**.
- **T026b-Gen** depends on **T015a**, **T023**, **T021c**.
- **T026b-Rand** depends on **T015a**, **T023**, **T021c**.
- **T026** depends on **T023**, **T021c**, **T015a**, **T026b-Gen**, **T026b-Rand**.
- **T026c** depends on **T023**, **T021c**, **T015a**.
- **T026d** depends on **T023**, **T021c**, **T015a**.
- **T027** depends on **T026**.
- **T028a** depends on **T022**.
- **T028** depends on **T023**, **T026**, **T028a**.
- **T029** depends on **T026**, **T026b-Gen**, **T026b-Rand**, **T026c**, **T026d**, **T027**, **T028**.
- **T030** depends on **T029**, **T008**.

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
4. Add Upper Bound Oracle → Test independently (control experiment) → Deploy/Demo
5. Add User Story 3 → Test independently (correlation, permutation, importance, classification) → Deploy/Demo
6. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Critical Path)
 - Developer B: User Story 2 (Prepares feature extraction logic in parallel, waits for US1 data)
 - Developer C: Upper Bound Oracle (Prepares hidden state extraction in parallel, waits for US1 data)
 - Developer D: User Story 3 (Prepares evaluation logic in parallel, waits for US1/US2/Upper Bound data)
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
- **Compute Constraint**: All tasks must run on CPU-only GitHub Actions with limited core and memory resources. Do not use 8-bit/4-bit quantization or CUDA-specific libraries (except for Oracle step if auto-offloaded to Kaggle GPU).
- **Data Constraint**: Use real GSM8K data from HuggingFace; do not fabricate synthetic data.
- **Independence Constraint**: Feature extraction (US2) must NOT use hidden states from the Oracle model (US1).
- **Constraint**: N=500 target, min=10 examples per Spec FR-002. Pipeline must warn and proceed if <500 found, fail if <10.
- **Model Constraint**: Oracle must use **Llama-3-8B** per Spec FR-002 and Plan.
- **Feature Constraint**: Semantic similarity uses sentence-transformers models per Spec FR-003.
- **Baseline Clarification**: T026b-Gen implements the SC-001 compliant uniform baseline (constant 1/N). Tb-Rand implements the random baseline (N(0,1)).
- **Threshold Clarification**: T028 uses Permutation Importance and correlation thresholds as primary logic.
- **Time Verification**: T033 explicitly verifies the **4-hour** limit for the CPU pipeline per SC-003.
- **Causal Disclaimer**: T030 ensures `causal_disclaimer` is written to metrics.json.
- **Spec Amendment FR-003**: The implementation uses **OpenMathInstruct-1** (verified HuggingFace) as the reference set for semantic similarity, replacing the spec's "MathQA" to ensure data availability and independence.
- **Spec Amendment FR-006**: The implementation uses **token-level permutation** (shuffling coefficients within each example ID) as required by the spec to preserve non-i.i.d. structure while breaking token-level signals.