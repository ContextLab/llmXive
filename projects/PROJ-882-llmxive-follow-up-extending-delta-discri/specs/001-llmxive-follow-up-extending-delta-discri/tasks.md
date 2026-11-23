---
description: "Task list template for feature implementation"
---

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

**Purpose**: Core infrastructure and data artefacts that must exist before any user story can be executed.

- [X] T002a **DEVIATION LOG**: Create `deviation_log.md` in `specs/001-delta-static-approximation/` documenting the N=500/Min=10 constraint and **Llama-3-8B** Oracle model choice. Reference **Constitution Principle VII** and document Llama-3-8B as the required model.
- [X] T002b **CONFIG UPDATE**: Update `code/config.py` to reflect the Plan constraints: set `N_EXAMPLES_TARGET=500`, `N_EXAMPLES_MIN=10`, `ORACLE_MODEL="meta-llama/Meta-Llama-3-8B-Instruct"`. Implement configuration defaults matching the Deviation Log.
- [X] T004 Create `contracts/delta_oracle.schema.yaml` defining the JSON structure for DelTA coefficients (token_id, coefficient, variance check). **ACTION**: Write full YAML content.
- [X] T005 Create `contracts/static_features.schema.yaml` defining the JSON structure for feature vectors (n-grams, POS, semantic similarity). **ACTION**: Write full YAML content.
- [X] T006 Create `contracts/predictions.schema.yaml` defining the JSON structure for model outputs (predicted_coefficient, true_coefficient, example_id). **ACTION**: Write full YAML content.
- [X] T007 Implement `code/config.py` to manage paths, seeds (a representative sample), and hyperparameters (N=500 target, N=10 min, MLP config).
- [X] T008 Implement `code/main.py` pipeline orchestrator with error handling for numerical instability (edge case: catch RuntimeError/ValueError, log to error.log, skip to next example). Includes logic to measure wall‑clock time for the **CPU‑only portion** (target ≤ 4 hours per SC‑003) and log it.
- [X] T009 Setup logging infrastructure in `code/main.py` to track execution time against a predefined duration limit and memory usage. Ensure `data/processed/metrics.json` includes a `total_runtime_seconds` field for SC‑003 verification and a `peak_memory_mb` field for SC‑004 verification.
- [X] T010 [P] Implement `code/data/download_gsm8k.py` (FR‑001): Download GSM8K from HuggingFace, filter for verified correct solutions, and save to `data/raw/gsm8k_verified.parquet`. Target 500 examples; if <500 but ≥10, proceed with all available and log a warning. **VERIFICATION**: Assert source dataset contains ≥10 valid examples before proceeding.
- [X] T011 Verify that `data/raw/gsm8k_verified.parquet` exists and contains at least 10 rows after running the download script. **DEPENDS ON**: T010.
- [X] T012 Implement `code/data/generate_oracle.py` (FR‑002): Load **meta-llama/Meta-Llama-3-8B-Instruct**, run the DelTA algorithm on up to 500 stratified examples (seed=42). Handle numerical instability by catching exceptions, logging to `error.log`, and excluding failed examples. Abort if <10 valid examples remain. Compute global variance; raise `RuntimeError('ERR_TRIVIAL_TARGET')` if variance ≤ 1e‑9. Save results to `data/processed/delta_coefficients.json` conforming to `contracts/delta_oracle.schema.yaml`.
- [X] T013 Verify that `data/processed/delta_coefficients.json` is created, contains coefficients for all processed examples, and that the global variance of the coefficients > 1e‑9. **DEPENDS ON**: T012.
- [X] T014 Implement variance and integrity validation (FR‑005, SC‑005): After oracle generation, run a validation script that (a) computes global variance and aborts with `ERR_TRIVIAL_TARGET` if ≤1e‑9, (b) checks for NaN or Inf values and aborts with `ERR_DATA_CORRUPTION`. This task ensures SC‑005 and SC‑005b are enforced.
- [X] T015 Verify that `data/processed/delta_coefficients.json` passes the variance and NaN/Inf checks. **DEPENDS ON**: T014.
- [X] T016 Implement `code/data/download_reference.py`: Download the **OpenMathInstruct-1** dataset from HuggingFace (replacing the originally specified MathQA) and save a deterministic subset (seed=42, stratified by length) to `data/interim/openmath_reference.parquet`. This satisfies the amended FR‑003 requirement.
- [X] T017 Verify checksum of the downloaded OpenMathInstruct-1 file and validate against a dedicated reference‑set schema.
- [X] T018 Implement `code/data/extract_features.py` (FR‑003): Extract n‑gram statistics, POS tags (using `spacy`), and semantic similarity to the OpenMathInstruct-1 reference set using `sentence-transformers/all-MiniLM-L6-v2`. Process examples from `data/raw/gsm8k_verified.parquet`. Assign default vectors for OOV tokens. Output to `data/processed/static_features.parquet` conforming to `contracts/static_features.schema.yaml`.
- [X] T019 Verify that `data/processed/static_features.parquet` exists and matches the schema. **DEPENDS ON**: T018.
- [X] T020 Implement `code/models/mlp.py` (FR‑004): Define a **2‑layer MLP** with **128 hidden units per layer** and **ReLU activation**.
- [X] T021 Verify that `code/models/mlp.py` can be imported and that the model architecture matches the specification.

---

## Phase 3: User Story 1 - Generate Ground‑Truth DelTA Coefficients (Priority: P1) 🎯 MVP

**Goal**: Validate that the oracle generation pipeline produces correct artefacts.

- [X] T022 [P] Unit test for GSM8K filtering logic in `tests/unit/test_data_download.py` (verify verified correctness labels). **DEPENDS ON**: T010.
- [X] T023 [P] Unit test for DelTA coefficient variance check in `tests/unit/test_oracle.py` (assert variance > 1e‑9). **DEPENDS ON**: T012.
- [X] T024 [P] Integration test that runs the full oracle pipeline on a small sample (e.g., 20 examples) and asserts that `data/processed/delta_coefficients.json` contains a coefficient for every token, with no NaNs or Infs. **DEPENDS ON**: T010, T012, T014.

---

## Phase 4: User Story 2 - Train Static Predictor Model (Priority: P2)

**Goal**: Train and validate the lightweight MLP using the static features.

- [X] T025 [P] Unit test for feature extraction independence in `tests/unit/test_features.py` (assert no hidden states from Oracle are used). **DEPENDS ON**: T018.
- [X] T026 [P] Integration test for MLP training loop in `tests/integration/test_training.py` (verify loss decreases on CPU). **DEPENDS ON**: T020, T012, T018.
- [X] T027 Implement `code/models/train.py` (FR‑004): Training loop using static features (`static_features.parquet`) and ground‑truth coefficients (`delta_coefficients.json`). Ensure CPU‑only execution, save model to `data/processed/mlp_model.pt`. **DEPENDS ON**: T020, T012, T018.
- [X] T028 Verify that `data/processed/mlp_model.pt` exists, can be loaded with `torch.load`, and its architecture matches the defined MLP. **DEPENDS ON**: T027.
- [X] T029 Implement prediction script `code/models/predict.py`: Load the trained MLP and static features for the held‑out test split, generate predictions, and save to `data/processed/predictions_static.json` conforming to `contracts/predictions.schema.yaml`. **DEPENDS ON**: T027, T018.
- [X] T030 Verify that `data/processed/predictions_static.json` exists and passes schema validation. **DEPENDS ON**: T029.

### Dummy‑data path for isolated US2 testing

- [X] T051 Create a tiny synthetic reference set (`data/interim/dummy_reference.parquet`) with 5 examples for unit‑test feature extraction.
- [X] T052 Run `code/data/extract_features.py` on the synthetic reference set to produce `data/processed/dummy_static_features.parquet`.
- [X] T053 Train the MLP on the dummy static features and a tiny synthetic DelTA target (`data/processed/dummy_delta_coefficients.json`) to produce `data/processed/dummy_mlp_model.pt`.
- [X] T054 Generate predictions from the dummy model and validate schema (`data/processed/dummy_predictions.json`).

---

## Phase 5: User Story 3 - Evaluate Rank Correlation and Significance (Priority: P3)

**Goal**: Compute Spearman correlation, perform permutation testing, and interpret results.

- [X] T031 [P] Unit test for Spearman calculation against random baseline in `tests/unit/test_metrics.py`.
- [X] T032 [P] Unit test for permutation test logic (sufficient number of shuffles) in `tests/unit/test_metrics.py`.
- [X] T033 Implement `code/eval/baseline_uniform.py`: Generate a uniform weight vector, normalize to match DelTA coefficient scale, and save to `data/processed/uniform_baseline.json`. **DEPENDS ON**: T012, T029.
- [X] T034 Verify that `data/processed/uniform_baseline.json` exists, is valid JSON, and contains a list of floats of appropriate length.
- [X] T035 Implement `code/eval/baseline_random.py`: Generate a random baseline vector from N(0,1) with seed=42, save to `data/processed/random_baseline.json`. **DEPENDS ON**: T012, T029.
- [X] T036 Verify that `data/processed/random_baseline.json` exists, is valid JSON, and contains a list of floats of appropriate length.
- [X] T037 Implement `code/eval/metrics.py` (FR‑005, FR‑006): Compute Spearman rank correlation between predictions (`predictions_static.json`) and true coefficients (`delta_coefficients.json`). Compare against both random and uniform baselines. Also compute the p‑value via a **example‑level permutation test** (shuffling entire example IDs while preserving token order) as required by the amended spec. **DEPENDS ON**: T029, T033, T035.
- [X] T038 Verify that the permutation routine respects example boundaries and produces a p‑value field in the output.
- [X] T039 Implement `code/eval/interpret.py` (FR‑008): Compute Permutation Importance for each static feature, then apply the decision logic:
    - If Spearman < 0.05 **AND** mean Permutation Importance < 0.01 → classification = "features are poor proxies".
    - Else if Spearman < 0.05 → classification = "signal is emergent".
    - Else → classification = "significant".
  Save results to `data/processed/evaluation_results.json` with fields `spearman`, `p_value`, `classification`.
- [X] T040 Verify that `data/processed/evaluation_results.json` contains the required top‑level fields and that `classification` is one of the allowed strings.
- [X] T041 Add a `causal_disclaimer` field to `data/processed/metrics.json` stating that findings are associational only (FR‑007). **DEPENDS ON**: T037.
- [X] T042 Verify that `data/processed/metrics.json` now includes the `causal_disclaimer` field with appropriate text.

### Dummy‑data evaluation path

- [X] T055 Create tiny synthetic predictions and ground‑truth files (`data/processed/dummy_predictions.json`, `data/processed/dummy_delta_coefficients.json`) for unit testing of metric calculations.
- [X] T056 Run `code/eval/metrics.py` on dummy data to verify Spearman and baseline calculations work without the full pipeline.
- [X] T057 Execute the example‑level permutation test on dummy data to ensure shuffling operates correctly.
- [X] T058 Run `code/eval/interpret.py` on dummy results and verify classification logic produces one of the allowed strings.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031a Update `README.md` with installation, usage, and quickstart sections.
- [ ] T031b Update `docs/architecture.md` with a pipeline diagram.
- [ ] T031c Update `docs/usage.md` with command‑line examples.
- [ ] T031d Verify each documentation file contains the expected headings and that the repository builds without missing docs.
- [ ] T032a Refactor `code/data/` to use streaming where possible.
- [ ] T032b Refactor `code/models/` to separate CPU‑only utilities.
- [ ] T032c Refactor `code/eval/` to isolate metric calculations.
- [ ] T032d Generate a memory‑profile report (`memory_profile.txt`) and ensure peak RAM ≤ 16 GB.
- [ ] T033 **SC‑003 VERIFICATION**: Read `data/processed/metrics.json` (from T008/T009) and explicitly verify `total_runtime_seconds` for the **CPU‑only pipeline** is within the acceptable temporal limit. Log a critical failure if exceeded. **DEPENDS ON**: T009, T008.
- [ ] T045 **SC‑004 VERIFICATION**: Read `data/processed/metrics.json` and assert `peak_memory_mb` ≤ 16384 (16 GB). Log a failure if the limit is exceeded. **DEPENDS ON**: T009, T008.
- [ ] T034 Additional unit tests covering edge cases:
   - `tests/unit/test_numerical_instability.py` (oracle gradient failures)
   - `tests/unit/test_oov_handling.py` (feature extraction OOV tokens)
   - `tests/unit/test_missing_features.py` (feature vector defaults)
   - Ensure all new tests pass.
- [ ] T035a **Quickstart End‑to‑End Validation**: Run `python -m code.main --quickstart` and assert that `data/processed/evaluation_results.json` exists and contains keys `spearman`, `p_value`, `classification`.
- [ ] T048 **Delta Oracle Schema Validation**: Validate `data/processed/delta_coefficients.json` against `contracts/delta_oracle.schema.yaml`.
- [ ] T049 **Static Features Schema Validation**: Validate `data/processed/static_features.parquet` against `contracts/static_features.schema.yaml`.
- [ ] T050 **Predictions Schema Validation**: Validate `data/processed/predictions_static.json` against `contracts/predictions.schema.yaml`.

---

## Documentation Tasks for Spec Amendments (Plan‑Root Cause)

- [ ] T036a **Spec Amendment**: Update `specs/001-delta-static-approximation/spec.md` to replace “MathQA” with “OpenMathInstruct-1” in FR‑003 and related sections.
- [ ] T037a **Spec Amendment**: Update `specs/001-delta-static-approximation/spec.md` to change the permutation test description from “token‑level shuffle” to “example‑level shuffle” as required by FR‑006.
