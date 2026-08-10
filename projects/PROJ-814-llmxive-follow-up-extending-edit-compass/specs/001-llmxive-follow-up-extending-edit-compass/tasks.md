# Tasks: llmXive follow-up: extending "Edit-Compass & EditReward-Compass: A Unified Benchmark for Image Editing"

**Input**: Design documents from `/specs/001-llmxive-followup-correlation-study/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Execution Order**: Write Code -> Run Test. All "Implementation" tasks must be completed before their corresponding "Test" tasks can be executed. (TDD methodology applies: write test code *after* implementation code exists to run it, or write test *definitions* first but execute them after).

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

- [ ] T001a [P] Create directory `src/services` and add empty `.gitkeep` file
- [ ] T001b [P] Create directory `src/models` and add empty `.gitkeep` file
- [ ] T001c [P] Create directory `src/utils` and add empty `.gitkeep` file
- [ ] T001d [P] Create directory `src/data-models` and add empty `.gitkeep` file
- [ ] T001e [P] Create directory `tests/unit` and add empty `.gitkeep` file
- [ ] T001f [P] Create directory `tests/contract` and add empty `.gitkeep` file
- [ ] T001g [P] Create directory `data/raw` and add empty `.gitkeep` file
- [ ] T001h [P] Create directory `data/filtered` and add empty `.gitkeep` file
- [ ] T001i [P] Create directory `data/scores` and add empty `.gitkeep` file
- [ ] T001j [P] Create directory `outputs` and add empty `.gitkeep` file
- [X] T002 Initialize {{claim:c_c23a1a02}} (Wikipedia: History of Python, https://en.wikipedia.org/wiki/History_of_Python) project with `requirements.txt` (pinning `transformers`, `sentence-transformers`, `torch==2.2.2+cpu [UNRESOLVED-CLAIM: c_6b25f0c5 — status=not_enough_info]`, `llama-cpp-python`, `scikit-image`, `lpips`, `statsmodels`, `numpy`, `scipy`)
- [X] T003 [P] Create `pyproject.toml` with `[tool.black]` (line-length=88 [UNRESOLVED-CLAIM: c_473685d6 — status=not_enough_info]) and `[tool.ruff]` (select=['E', 'F', 'W']) sections to configure linting and formatting. This single file replaces separate `.ruff.toml` and `.black` files to avoid redundancy.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement basic logging utility in `src/utils/logging.py` (JSON format, file + stdout)
- [X] T006 [P] Create `src/data_models.py` defining `EditInstance` Pydantic model (must include fields: `source_image_path`, `edited_image_path`, `instruction`, `category`, `human_judgment_score`) and `ScoreRecord` Pydantic model (must include fields: `instance_id`, `logic_score`, `fidelity_score`, `ssim`, `lpips`, `vllm_description`). This file serves as the primary data model definition.
- [X] T006b [P] Append `RegressionResult` Pydantic model to `src/data_models.py` (must include fields: `model_r_squared`, `beta_logic`, `beta_fidelity`, `p_value_logic`, `p_value_fidelity`, `fdr_corrected_p_logic`, `fdr_corrected_p_fidelity`). Note: The `fdr_corrected_p` fields are populated *after* the regression and correction steps (T026), not at model instantiation.
- [ ] T007 [P] Create `contracts/score-record.schema.yaml` for JSON schema validation of `ScoreRecord` (Depends on T006)
- [ ] T007a [P] Create `contracts/regression-result.schema.yaml` for JSON schema validation of `RegressionResult` (Depends on T006b)
- [X] T008 [P] Implement `src/cli/main.py` entry point with argument parsing for pipeline stages
- [X] T008a [P] Implement `src/services/reference_validator.py` to perform local citation verification (checking title overlap >= 0.7 [UNRESOLVED-CLAIM: c_3ac7a73b — status=not_enough_info] and URL reachability). This local implementation satisfies the Constitution's Principle II (Verified Accuracy) for offline execution, replacing the external agent dependency.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Filtering (Priority: P1) 🎯 MVP

**Goal**: Download the Edit-Compass dataset and filter for "World Knowledge Reasoning" and "Visual Reasoning" categories.

**Independent Test**: Verify `data/filtered/` contains only valid JSON/CSV entries with the required category labels and that raw data is untouched in `data/raw/`.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `src/services/download.py` to fetch Edit-Compass dataset via `wget`/`curl` from official repo. This task includes validating the presence of the 'category' key in the raw dataset metadata and verifying that at least one record contains "World Knowledge Reasoning" or "Visual Reasoning". If keys are missing or labels are absent, exit with code 1 and log "ERROR: Missing category labels or data structure mismatch". If zero records match, exit with code 1 and log "ERROR: No records found for target categories". Save raw data to `data/raw/`.
- [X] T012 [US1] Implement `src/services/filter.py` to load raw data, filter by `category` in ["World Knowledge Reasoning", "Visual Reasoning"], and save to `data/filtered/`. If zero records match, exit with code 1 and log "ERROR: Filter returned zero records".
- [ ] T013 [US1] Update `src/services/download.py` to raise `FileNotFoundError` on missing files and `src/services/filter.py` to raise `ValueError` on malformed JSON.
- [X] T014 [US1] Integrate download and filter into `src/cli/main.py` (Stage: `download-filter`)

### Tests for User Story 1 (TDD - Write AFTER Implementation) ⚠️

- [ ] T009a-1 [P] [US1] Write `tests/unit/test_download.py::test_url_validity`: Assert that the download URL returns HTTP 200 and content type is valid. (Depends on T011)
- [ ] T009a-2 [P] [US1] Write `tests/unit/test_download.py::test_checksum_verification`: Assert that the downloaded file SHA256 matches the expected checksum. (Depends on T011)
- [X] T010a [P] [US1] Write `tests/unit/test_filter.py::test_valid_category_match`: Assert that filtering by ["World Knowledge Reasoning", "Visual Reasoning"] returns only records where the category field EXACTLY matches one of these values. (Depends on T012)
- [X] T010b [P] [US1] Write `tests/unit/test_filter.py::test_empty_result_handling`: Assert that if no matches are found, the script exits with exit code 1 and logs the message "ERROR: No records found for categories: [World Knowledge Reasoning, Visual Reasoning]". (Depends on T012)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Scoring Generation (Priority: P2)

**Goal**: Compute Logic Consistency Score (VLM) and Fidelity Score (SSIM/LPIPS) for each filtered instance.

**Independent Test**: Run on a small batch; verify `data/scores/` contains JSON with numeric Logic/Fidelity scores (0-1 range) and no nulls.

### Implementation for User Story 2

- [ ] T017 [US2] Implement `src/models/vlm.py` wrapper for `Phi-3-mini-4k-instruct-GGUF` (4-bit, CPU-only) using `llama-cpp-python` with initial batch size 8
- [ ] T018 [US2] Implement `src/services/scoring.py` Logic Score logic: Embed instruction & VLM description via `{{claim:c_697bedb4}} (2607.07974, https://arxiv.org/abs/2607.07974)`, compute cosine similarity
- [ ] T019 [US2] Implement `src/services/scoring.py` Fidelity Score logic: Compute SSIM and LPIPS between the **original** source and edited images (NO resizing), calculate a weighted combination of SSIM and (1-LPIPS). This ensures compliance with FR-004 and Constitution IV (Single Source of Truth).
- [ ] T020 [US2] Implement batch processing loop in `src/services/scoring.py` with **pre-flight memory estimation** and **dynamic batch-size adjustment**. Formula: `RAM_est = model_size_gb * scaling_factor + batch_size * image_size_mb`. `image_size_mb` is the memory of a single image tensor (using dimensions defined in T019, i.e., original size). **MUST NOT resize images**. Reduce batch size if `RAM_est > 6.5GB [UNRESOLVED-CLAIM: c_0b494cc3 — status=not_enough_info]` (GB limit minus A safety buffer of sufficient capacity to accommodate system overhead and unexpected load variations.) to guarantee the storage limit is never exceeded; skip failures with logs. (Depends on T019).
- [X] T021 [US2] Integrate scoring into `src/cli/main.py` (Stage: `score`) and write results to `data/scores/`

### Tests for User Story 2 (TDD - Write AFTER Implementation) ⚠️

- [ ] T015a-1 [P] [US2] Write `tests/unit/test_scoring.py::test_ssim_calculation`: Assert SSIM calculation on dummy images returns value in [0, 1]. (Depends on T019)
- [ ] T015a-2 [P] [US2] Write `tests/unit/test_scoring.py::test_lpips_calculation`: Assert LPIPS calculation on dummy images returns value in [0, 1]. (Depends on T019)
- [X] T016 [P] [US2] Write `tests/unit/test_scoring.py::test_vlm_description_generation`: Assert VLM wrapper returns a non-empty string description for a valid image prompt. (Depends on T017)
- [X] T016b [P] [US2] Write `tests/unit/test_scoring.py::test_logic_score_range`: Assert Logic Score (cosine similarity) is in [-1, 1]. (Depends on T018)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation Analysis (Priority: P3)

**Goal**: Perform independence check, multiple linear regression, and Benjamini-Hochberg correction to determine the stronger predictor.

**Independent Test**: Verify regression output includes standardized betas, p-values, and FDR-corrected significance; check independence check halts if |r| ≥ 0.5.

### Implementation for User Story 3

- [X] T024a [US3] Implement `src/services/analysis.py` to extract and validate the 'Human Judgment Score' field from the filtered dataset (`data/filtered/`). Ensure the field exists and is numeric for all records. If missing, raise `ValueError` with message "ERROR: Human Judgment Score missing". (Prerequisite for T024).
- [ ] T024b [US3] Implement `src/services/analysis.py` to perform an **atomic write** of `outputs/circular_validation_risk_report.json`. The write MUST use a temporary file (e.g., `report.json.tmp`) followed by `os.rename()` to ensure atomicity. The JSON structure MUST include fields: `r` (correlation coefficient), `threshold` (0.5), `decision` (string), and `timestamp`. (Dependency for T024).
- [ ] T024 [US3] Implement `src/services/analysis.py` independence check: Calculate Pearson correlation between Human Score (from T024a) and Logic Score. If |r| ≥ 0.5, **atomically** write `outputs/circular_validation_risk_report.json` (using T024b logic) AND immediately raise `CircularValidationRiskError` with message "CIRCULAR_VALIDATION_RISK: |r|={value:.4f} >= 0.5" and exit process with code 1. (Depends on T024a, T024b).
- [X] T025 [US3] Implement `src/services/analysis.py` multiple linear regression: Dependent=Human Score, Independent=Logic & Fidelity Scores (Depends on T024a).
- [ ] T026 [US3] Implement `src/services/analysis.py` Benjamini-Hochberg correction on regression p-values (FDR ≤ 0.05 [UNRESOLVED-CLAIM: c_33e2a091 — status=not_enough_info])
- [ ] T028a [US3] Implement `src/services/analysis.py` to perform a **statistical test for the difference in correlation strength** (Fisher's r-to-z transformation) between Logic and Fidelity predictors. The task must verify if Logic correlation exceeds Fidelity correlation by **at least 0.1** AND the **p-value of the difference is < 0.05 [UNRESOLVED-CLAIM: c_cfa37bc2 — status=not_enough_info]**. Output results to `outputs/correlation_diff_test.json` with fields: `z_score`, `p_value`, `effect_size`, `conclusion`. (Depends on T025, T026)
- [ ] T028b [US3] Implement `src/services/analysis.py` to explicitly output the "threshold_met" (boolean) and "threshold_value" (0.1) in the final report, ensuring SC-001 is verifiable. (Depends on T028a)
- [ ] T029 [US3] Generate final report in `outputs/regression_report.md`. Decision Logic: If (diff >= 0.1 AND p_diff < 0.05) -> State "Logic is stronger predictor". Else if (beta_fidelity > beta_logic AND p_diff < 0.05) -> State "Fidelity is stronger predictor". **Else -> State "Inconclusive: Neither predictor significantly exceeds the 0.1 threshold with p < 0.05."** The report MUST explicitly output `threshold_met` (boolean) and `threshold_value` (0.1) to verify SC-001. (Depends on T025, T026, T028a, T028b)
- [ ] T030 [US3] Integrate analysis into `src/cli/main.py` (Stage: `analyze`)

### Tests for User Story 3 (TDD - Write AFTER Implementation) ⚠️

- [ ] T022 [P] [US3] Write `tests/unit/test_analysis.py::test_pearson_threshold_halt`: Assert that if correlation >= 0.5, the function raises `CircularValidationRiskError`. (Depends on T024)
- [ ] T023 [P] [US3] Write `tests/unit/test_analysis.py::test_fisher_z_test`: Assert Fisher's r-to-z transformation calculates the correct z-score and p-value for two independent correlations. (Depends on T028a)
- [ ] T023b [P] [US3] Write `tests/unit/test_analysis.py::test_fdr_correction`: Assert Benjamini-Hochberg correction correctly adjusts p-values. (Depends on T026)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Add contract tests validating `data/scores/*.json` against `contracts/score-record.schema.yaml` and `outputs/regression_report.json` against `contracts/regression-result.schema.yaml`
- [ ] T032a [P] Run a full pass of the scoring pipeline and verify peak RAM usage is < 6.5GB [UNRESOLVED-CLAIM: c_0e292ac6 — status=not_enough_info] in the logs, confirming the **dynamic batch-size adjustment** logic in T020 functions correctly. (Replaces T032a which incorrectly hardcoded batch size).
- [ ] T032b [P] Run a full pass of the scoring pipeline and verify peak RAM usage is < 6.5GB [UNRESOLVED-CLAIM: c_0e292ac6 — status=not_enough_info] in the logs.
- [ ] T033 [P] Execute the Advancement-Evaluator Agent to update `state/projects/PROJ-814-...yaml` with requirements.txt hash and dataset checksums.
- [ ] T034 [P] Run `python -m src.cli.main --validate-docs` and update `quickstart.md` with the new CLI flags and execution instructions.

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
- **User Story 2 (P2)**: Depends on US1 completion (needs filtered data in `data/filtered/`)
- **User Story 3 (P3)**: Depends on US2 completion (needs scores in `data/scores/`)

### Within Each User Story

- Implementation tasks MUST be completed before Test tasks can be executed.
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Unit tests for different services can run in parallel
- Different user stories cannot run in parallel due to data dependencies (US1 → US2 → US3)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 download/filter independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Sequential Pipeline Strategy

Given data dependencies (Raw → Filtered → Scores → Analysis):

1. Team completes Setup + Foundational together
2. Developer A: User Story 1 (Download/Filter)
3. Once US1 data is ready: Developer B: User Story 2 (Scoring)
4. Once US2 scores are ready: Developer C: User Story 3 (Analysis)
5. Final Polish: Tests, docs, performance tuning

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All VLM inference must use CPU-only quantization. (`llama-cpp-python`) to fit within 7GB RAM.
- **Critical Constraint**: No GPU/CUDA usage allowed; `torch` must be CPU version.
- **Critical Constraint**: Dataset download must use real URLs; no synthetic data generation.
- **Critical Constraint**: T024 must atomically write the risk report (using T024b) and raise the exception to prevent state loss. T020 must use pre-flight memory estimation with a 6.5GB safety buffer. **NO image resizing** is permitted; SSIM/LPIPS must be calculated on original images.
- **Critical Constraint**: T008a must implement the local reference validator to replace the external agent dependency, satisfying Constitution Principle II.
- **Critical Constraint**: T032a (Phase 6) verifies the dynamic batch logic; do not hardcode batch sizes.