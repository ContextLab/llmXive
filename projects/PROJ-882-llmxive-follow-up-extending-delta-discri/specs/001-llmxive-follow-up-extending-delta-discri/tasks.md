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
- [X] T002 Initialize a Python project with `requirements.txt` (pinned: `torch`, `transformers`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `spacy`, `sentence-transformers`, `pytest`). **REMOVED**: `delta` (non-existent package; algorithm implemented in code/).
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. These tasks create the validation contracts required for all data artifacts and document feasibility deviations.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T004, T005, T006 are hard prerequisites for T015, T018, T020 respectively. T036a and T037a MUST be completed to align spec.md with plan.md before T018 and T027 can proceed.

- [X] T002a **DEVIATION LOG**: Create `deviation_log.md` in `specs/001-delta-static-approximation/` documenting the N=500/Min=10 constraint and **Llama-3-8B** Oracle model choice. Explicitly reference **Constitution Principle VII** (Oracle Ground-Truth Generation) and document Llama-3-8B as the required model. **ACTION**: Write deviation details and link to Plan section.
- [X] T002b **CONFIG UPDATE**: Update `code/config.py` to reflect the Plan constraints: set `N_EXAMPLES_TARGET=500`, `N_EXAMPLES_MIN=10`, `ORACLE_MODEL="meta-llama/Meta-Llama-3-8B-Instruct"` (Llama‑3‑8B). **ACTION**: Implement configuration defaults matching the Deviation Log.
- [X] T004 Create `contracts/delta_oracle.schema.yaml` defining the JSON structure for DelTA coefficients (token_id, coefficient, variance check). **ACTION**: Write full YAML content.
- [X] T005 Create `contracts/static_features.schema.yaml` defining the JSON structure for feature vectors (n-grams, POS, semantic similarity). **ACTION**: Write full YAML content.
- [X] T006 Create `contracts/predictions.schema.yaml` defining the JSON structure for model outputs (predicted_coefficient, true_coefficient, example_id). **ACTION**: Write full YAML content.
- [X] T007 Implement `code/config.py` to manage paths, seeds (a representative sample), and hyperparameters (N=500 target, N=10 min, MLP config).
- [X] T008 Implement `code/main.py` pipeline orchestrator with error handling for numerical instability (edge case: catch RuntimeError/ValueError, log to error.log, skip to next example). **INCLUDES**: Logic to measure wall‑clock time for the **CPU‑only portion** (target ≤ 4 hours per SC‑003) and log it. The GPU offload step is timed separately.
- [X] T009 Setup logging infrastructure in `code/main.py` to track execution time against a predefined duration limit and memory usage. **ENHANCEMENT**: Ensure `data/processed/metrics.json` includes a `total_runtime_seconds` field for SC‑003 verification (CPU portion only) and a `peak_memory_mb` field for SC‑004 verification.
- [X] T036a [P] **SPEC AMENDMENT**: Update `spec.md` FR‑003 to replace "MathQA" with "OpenMathInstruct-1" as the reference dataset for semantic similarity. **DEPENDS ON**: None. **RATIONALE**: Plan.md explicitly identifies this as a critical spec amendment.
- [X] T037a [P] **SPEC AMENDMENT**: Update `spec.md` FR‑006 to replace "token-level shuffle" with "example-level shuffle" for the permutation test. **DEPENDS ON**: None. **RATIONALE**: Plan.md explicitly identifies this as a critical spec amendment.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Ground-Truth DelTA Coefficients (Priority: P1) 🎯 MVP

**Goal**: Generate ground‑truth DelTA Coefficients for a subset of GSM8K using Llama‑3‑8B as the Oracle.

**Independent Test**: Execute on a fixed subset of 500 GSM8K examples (seed=42) and verify the output file contains a valid DelTA Coefficient for every token, with variance > 1e‑9 and no NaNs. If <500 found, proceed with min=10 and log a warning.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for GSM8K filtering logic in `tests/unit/test_data_download.py` (verify verified correctness labels)
- [X] T011 [P] [US1] Unit test for DelTA coefficient variance check in `tests/unit/test_oracle.py` (assert variance > 1e‑9)

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download_gsm8k.py` (FR‑001): Download GSM8K from HuggingFace, filter for verified correct solutions, save to `data/raw/gsm8k_verified.parquet`. Target 500 examples; if <500 available but >=10, proceed with all available and log warning. **VERIFICATION**: Assert source dataset contains >= 10 valid examples before proceeding.
- [X] T013 [US1] Implement `code/data/generate_oracle.py` (FR‑002): Load **meta-llama/Meta-Llama-3-8B-Instruct**, run DelTA algorithm using explicit `torch.autograd.grad` on up to 500 stratified examples (seed=42). Handle numerical instability by catching exceptions, logging to `error.log`, and excluding failed examples. **FALLBACK**: If <500 valid examples remain but ≥10, proceed with warning. **FAIL** if <10 valid examples remain. **INTEGRATED CHECK**: Compute global variance of DelTA coefficients within this script; raise `RuntimeError('ERR_TRIVIAL_TARGET')` if variance <= 1e‑9. **VERIFICATION**: Assert output file contains coefficients for all examples in the dataset.
- [ ] T015a [US1] Save output to `data/processed/delta_coefficients.json` conforming to `contracts/delta_oracle.schema.yaml`. **BUILD‑TIME DEPENDENCY**: T004 (schema file must exist). **DATA DEPENDENCY**: T012, T013 (data must be generated). **VALIDATION**: At runtime, validate the generated JSON content against the schema to ensure data integrity.
- [ ] T015b [US1] Validate `data/processed/delta_coefficients.json` against `contracts/delta_oracle.schema.yaml` using `jsonschema`. **DEPENDS ON**: T015a.
- [ ] T015c [US1] Verify global variance of coefficients > 1e‑9 using the logic in T013; on failure raise `RuntimeError('ERR_TRIVIAL_TARGET')`. **DEPENDS ON**: T015a.
- [ ] T015d [US1] Verify that `data/processed/delta_coefficients.json` contains no NaN or Inf values. **DEPENDS ON**: T015a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train Static Predictor Model (Priority: P2)

**Goal**: Train a lightweight multi‑layer perceptron on CPU using only static input features to predict DelTA Coefficients.

**Independent Test**: Train the model on the training split using only n‑grams, POS, and semantic similarity (no hidden states) and verify convergence on CPU without GPU/CUDA.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for feature extraction independence in `tests/unit/test_features.py` (assert no hidden states from Oracle are used)
- [X] T017 [P] [US2] Integration test for MLP training loop in `tests/integration/test_training.py` (verify loss decreases on CPU)

### Implementation for User Story 2

- [ ] T018a [US2] **REFERENCE SET**: Implement `code/data/download_reference.py`: Download the **OpenMathInstruct-1** dataset from HuggingFace (verified source per Plan). Select a deterministic subset of examples (seed=42, stratified by length) and save to `data/interim/openmath_reference.parquet`. **ACTION**: Replace MathQA with OpenMathInstruct-1 as per Plan amendment. **DEPENDS ON**: None (external data).
- [ ] T038 [US2] Verify checksum of downloaded OpenMathInstruct-1 file and validate against `contracts/static_features.schema.yaml` (or a dedicated reference‑set schema). **DEPENDS ON**: T018a.
- [ ] T018 [US2] Implement `code/data/extract_features.py` (FR‑003): Extract n‑gram stats, POS tags (using `spacy`), and semantic similarity to the **OpenMathInstruct-1** reference set (`data/interim/openmath_reference.parquet`) using `sentence-transformers/all‑MiniLM‑L6‑v2`. Process a representative set of examples from T012. Filter OOV tokens or assign default vectors. Output to `data/processed/static_features.parquet` with columns `[token_id, feature_vector]`. **NO CIRCULARITY**: Do NOT use GSM8K as the reference set. **DEPENDS ON**: T012, T018a, T005, T036a (spec amendment).
- [ ] T019 [US2] Implement feature vector handling in `code/data/extract_features.py` (Edge Case): Filter OOV tokens or assign default vectors to prevent training errors.
- [ ] T020 [US2] Save extracted features to `data/processed/static_features.parquet` conforming to `contracts/static_features.schema.yaml`. **DEPENDS ON**: T018, T005. **VALIDATION**: Validate output against schema before saving.
- [ ] T021a [US2] Implement `code/models/mlp.py` (FR‑004): Define a **2‑layer MLP** with **128 hidden units per layer** and **ReLU activation**. **DEPENDS ON**: T005 (schema for input/output dimensions).
- [ ] T022 [US2] Implement `code/models/train.py` (FR‑004): Training loop using only extracted static features (T020), ground‑truth coefficients (T015a), and the model defined in T021a on CPU; ensure no CUDA/GPU calls; save model to `data/processed/mlp_model.pt`. **DEPENDS ON**: T020, T015a, T021a.
- [ ] T046 [US2] Verify that `data/processed/mlp_model.pt` exists, can be loaded with `torch.load`, and its architecture matches the defined MLP. **DEPENDS ON**: T022.
- [ ] T023 [US2] Generate predictions for the held‑out test set using the Static Model and save to `data/processed/predictions_static.json`. **DEPENDS ON**: T022.
- [ ] T048 [US2] Validate `data/processed/predictions_static.json` against `contracts/predictions.schema.yaml`. **DEPENDS ON**: T023.

---

## Phase 5: User Story 3 - Evaluate Rank Correlation and Significance (Priority: P3)

**Goal**: Compute Spearman rank correlation and perform permutation tests to distinguish signal emergence from poor proxies.

**Independent Test**: Run evaluation on test set to output Spearman, p‑value (permutation test), and classification result.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for Spearman calculation against random baseline in `tests/unit/test_metrics.py`
- [X] T025 [P] [US3] Unit test for permutation test logic (a sufficient number of shuffles) in `tests/unit/test_metrics.py`

### Implementation for User Story 3

- [ ] T026b-Gen [US3] **UNIFORM BASELINE**: Implement `code/eval/baseline_uniform.py`: Generate a **uniform weight vector** (constant /N) as the primary uniform baseline (SC‑001 compliant). **VERIFY**: Normalize the vector to match the scale of the DelTA coefficients (mean=0, std=1 or equivalent scaling). Save to `data/processed/uniform_baseline.json`. **DEPENDS ON**: T015a, T023.
- [ ] T040 [US3] Verify that `data/processed/uniform_baseline.json` exists, is valid JSON, and contains a list of floats of appropriate length. **DEPENDS ON**: T026b-Gen.
- [ ] T026b-Rand [US3] **RANDOM BASELINE**: Implement `code/eval/baseline_random.py`: Generate a **random baseline** vector from N(0,1) with seed=42. Save to `data/processed/random_baseline.json`. **DEPENDS ON**: T015a, T023.
- [ ] T041 [US3] Verify that `data/processed/random_baseline.json` exists, is valid JSON, and contains a list of floats of appropriate length. **DEPENDS ON**: T026b-Rand.
- [ ] T026 [US3] Implement `code/eval/metrics.py` (FR‑005, FR‑006): Compute Spearman rank correlation between predicted (T023) and true (T015a) coefficients. Compare against random baseline (from T026b‑Rand) and **uniform baseline** (from T026b‑Gen). **DEPENDS ON**: T023, T015a, T026b‑Gen, T026b‑Rand.
- [ ] T027 [US3] Implement permutation test in `code/eval/metrics.py` (FR‑006): **SHUFFLE EXAMPLE-LEVEL COEFFICIENTS** (shuffling entire example IDs while preserving token structure within examples) repeatedly to generate null distribution; calculate p‑value. This respects the non-i.i.d. structure as per Plan amendment. **DEPENDS ON**: T026, T037a (spec amendment).
- [ ] T027b [US3] Verify that the permutation routine respects example boundaries by checking that shuffled indices never cross example boundaries. **DEPENDS ON**: T027.
- [ ] T028 [US3] Implement `code/eval/interpret.py` (FR‑008, Plan Phase 3.3): Compute Permutation Importance. **Decision Logic**:
 - **Emergent Signal**: Spearman correlation low/non‑significant **AND** mean Permutation Importance ≥ 0.01.
 - **Poor Proxies**: Spearman correlation low/non‑significant **AND** mean Permutation Importance < 0.01.
 - **Significant**: Spearman correlation high/significant.
 - **Note**: The comparison against the Upper Bound Oracle is **OPTIONAL** and for diagnostic purposes only; the primary classification must rely on the Permutation Importance logic defined in FR‑008.
 **DEPENDS ON**: T023, T026.
- [ ] T028b [US3] Verify that `data/processed/evaluation_results.json` contains a top‑level field `classification` with one of the allowed strings. **DEPENDS ON**: T028.
- [ ] T029 [US3] Generate final report in `data/processed/evaluation_results.json` including correlation (Spearman), CI, p‑value, and classification result (Emergent/Poor Proxies/Significant). **DEPENDS ON**: T026, T026b‑Gen, T026b‑Rand, T027, T028.
- [ ] T030 [US3] Add logic to frame findings as associational (FR‑007) and write `causal_disclaimer` field to `data/processed/metrics.json`. **DEPENDS ON**: T029, T008. **ACTION**: Ensure `metrics.json` exists (from T008) before writing `causal_disclaimer`.
- [ ] T030b [US3] Verify that `data/processed/metrics.json` now includes the `causal_disclaimer` field with appropriate text. **DEPENDS ON**: T030.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates:
 - Update `README.md` with installation, usage, and quickstart sections.
 - Update `docs/architecture.md` with pipeline diagram.
 - Update `docs/usage.md` with command‑line examples.
 - Verify each file contains the expected headings.
- [ ] T032 [P] Code cleanup and refactoring:
 - Refactor `code/data/` to use streaming where possible.
 - Refactor `code/models/` to separate CPU‑only utilities.
 - Refactor `code/eval/` to isolate metric calculations.
 - Generate a memory‑profile report (`memory_profile.txt`) and ensure peak RAM ≤ 16 GB.
- [ ] T033 [P] **SC‑003 VERIFICATION**: Read `data/processed/metrics.json` (from T008/T009) and explicitly verify `total_runtime_seconds` for the **CPU‑only pipeline** is within the acceptable temporal limit. (SC‑003). If exceeded, log a critical failure. **DEPENDS ON**: T009, T008.
- [ ] T045 [P] **SC‑004 VERIFICATION**: Read `data/processed/metrics.json` and assert `peak_memory_mb` ≤ 16384 (16 GB). Log a failure if the limit is exceeded. **DEPENDS ON**: T009, T008.
- [ ] T034 [P] Additional unit tests covering edge cases:
 - `tests/unit/test_numerical_instability.py` (oracle gradient failures)
 - `tests/unit/test_oov_handling.py` (feature extraction OOV tokens)
 - `tests/unit/test_missing_features.py` (feature vector defaults)
 - Ensure all new tests pass.
- [ ] T035a [P] **Quickstart End‑to‑End Validation**: Run `python -m code.main --quickstart` and assert that `data/processed/evaluation_results.json` exists and contains keys `spearman`, `p_value`, `classification`. **DEPENDS ON**: All prior phases.
- [ ] T048 [P] **Delta Oracle Schema Validation**: Validate `data/processed/delta_coefficients.json` against `contracts/delta_oracle.schema.yaml`. **DEPENDS ON**: T015a.
- [ ] T049 [P] **Static Features Schema Validation**: Validate `data/processed/static_features.parquet` against `contracts/static_features.schema.yaml`. **DEPENDS ON**: T020.
- [ ] T050 [P] **Predictions Schema Validation**: Validate `data/processed/predictions_static.json` against `contracts/predictions.schema.yaml`. **DEPENDS ON**: T023.

**Dependencies & Execution Order**

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies - can start immediately
- **Foundational (Phase 2)**: depends on Setup completion - **BLOCKS all user stories**. T004, T005, T006 must be marked complete before T015, T018, T020 can proceed. T036a and T037a must be complete before T018 and T027.
- **User Stories (Phase 3+)**: all depend on Foundational phase completion
 - **User Story 1 (P1)**: generates ground‑truth data required for US2 and US3
 - **User Story 2 (P2)**: requires ground‑truth from User Story 1. The dependency is expressed via ordering only; no explicit BLOCKED BY annotation remains.
 - **User Story 3 (P3)**: requires predictions from User Story 2 (Static) and ground‑truth from User Story 1.
- **Polish (Final Phase)**: depends on all desired user stories being complete

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 (Static) can start in parallel *if* US1 is complete (US1 is the critical path)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

### Explicit Task Dependencies

- **T015a** depends on **T004** (schema), **T012**, **T013**. **BLOCKED BY T004 and T012**.
- **T018a** depends on **none** (external data).
- **T018** depends on **T012** (raw GSM8K examples), **T018a** (reference set), **T005** (schema), and **T036a** (spec amendment). **BLOCKED BY T018a and T036a**.
- **T020** depends on **T018** and **T005**. **BLOCKED BY T005**.
- **T022** depends on **T021a**, **T020**, **T015a**. **BLOCKED BY T020 and T015a**.
- **T023** depends on **T022**.
- **T026b-Gen** depends on **T015a**, **T023**.
- **T026b-Rand** depends on **T015a**, **T023**.
- **T026** depends on **T023**, **T015a**, **T026b-Gen**, **T026b-Rand**.
- **T027** depends on **T026** and **T037a** (spec amendment). **BLOCKED BY T037a**.
- **T028** depends on **T023**, **T026**.
- **T029** depends on **T026**, **T026b-Gen**, **T026b-Rand**, **T027**, **T028**.
- **T030** depends on **T029**, **T008**.
- **T031** depends on none.
- **T032** depends on none.
- **T033** depends on **T009**, **T008**.
- **T045** depends on **T009**, **T008**.
- **T034** depends on none.
- **T035a** depends on all prior phases.
- **T048-T050** depend on their respective artifact generation tasks.