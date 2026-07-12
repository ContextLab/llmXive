# Tasks: llmXive follow-up: extending "Edit-Compass & EditReward-Compass: A Unified Benchmark for Image Editing"

**Input**: Design documents from `/specs/001-llmxive-followup-correlation-study/`
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

- [ ] T001a [P] Create directory `src/services`
- [ ] T001c [P] Create directory `src/models`
- [ ] T001d [P] Create directory `src/utils`
- [ ] T001e [P] Create directory `src/data-models`
- [ ] T001f [P] Create directory `tests/unit`
- [ ] T001g [P] Create directory `tests/contract`
- [~] T001h [P] Create directory `data/raw`
- [~] T001i [P] Create directory `data/filtered`
- [~] T001j [P] Create directory `data/scores`
- [~] T001k [P] Create directory `outputs`
- [~] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `transformers`, `sentence-transformers`, `torch==2.2.2+cpu`, `llama-cpp-python`, `scikit-image`, `lpips`, `statsmodels`, `numpy`, `scipy`)
- [~] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T004 Setup data directory structure: `data/raw/`, `data/filtered/`, `data/scores/`, `outputs/`
- [~] T005 [P] Implement basic logging utility in `src/utils/logging.py` (JSON format, file + stdout)
- [~] T006 [P] Create `src/data-models.py` defining `EditInstance` Pydantic model (must include fields: `source_image_path`, `edited_image_path`, `instruction`, `category`, `human_judgment_score`) and `ScoreRecord` Pydantic model (must include fields: `instance_id`, `logic_score`, `fidelity_score`, `ssim`, `lpips`, `vllm_description`, `p_value_logic`, `p_value_fidelity`, `beta_logic`, `beta_fidelity`)
- [~] T007 [P] Create `contracts/score-record.schema.yaml` for JSON schema validation
- [~] T008 [P] Implement `src/cli/main.py` entry point with argument parsing for pipeline stages

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Filtering (Priority: P1) 🎯 MVP

**Goal**: Download the Edit-Compass dataset and filter for "World Knowledge Reasoning" and "Visual Reasoning" categories.

**Independent Test**: Verify `data/filtered/` contains only valid JSON/CSV entries with the required category labels and that raw data is untouched in `data/raw/`.

### Tests for User Story 1 (TDD - Write FIRST) ⚠️

- [ ] T009a-1 [P] [US1] Write `tests/unit/test_download.py::test_url_validity`: Assert that the download URL returns HTTP 200 and content type is valid.
- [ ] T009a-2 [P] [US1] Write `tests/unit/test_download.py::test_checksum_verification`: Assert that the downloaded file SHA256 matches the expected checksum.
- [~] T010 [P] [US1] Write `tests/unit/test_filter.py::test_category_filter_logic`: Assert that filtering by ["World Knowledge Reasoning", "Visual Reasoning"] returns only matching records. <!-- ATOMIZE: requested -->
- [~] T010b [P] [US1] Write `tests/unit/test_filter.py::test_empty_result_handling`: Assert that if no matches are found, the script exits with a clear error message. <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [~] T011 [US1] Implement `src/services/download.py` to fetch Edit-Compass dataset via `wget`/`curl` from official repo, handling errors and saving to `data/raw/`
- [~] T012 [US1] Implement `src/services/filter.py` to load raw data, filter by `category` in ["World Knowledge Reasoning", "Visual Reasoning"], and save to `data/filtered/`
- [~] T013 [US1] Add error handling for missing files or malformed JSON in download/filter scripts
- [~] T014 [US1] Integrate download and filter into `src/cli/main.py` (Stage: `download-filter`)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Scoring Generation (Priority: P2)

**Goal**: Compute Logic Consistency Score (VLM) and Fidelity Score (SSIM/LPIPS) for each filtered instance.

**Independent Test**: Run on a small batch; verify `data/scores/` contains JSON with numeric Logic/Fidelity scores (0-1 range) and no nulls.

### Tests for User Story 2 (TDD - Write FIRST) ⚠️

- [ ] T015a-1 [P] [US2] Write `tests/unit/test_scoring.py::test_ssim_calculation`: Assert SSIM calculation on dummy images returns value in [0, 1].
- [ ] T015a-2 [P] [US2] Write `tests/unit/test_scoring.py::test_lpips_calculation`: Assert LPIPS calculation on dummy images returns value in [0, 1].
- [~] T016 [P] [US2] Write `tests/unit/test_scoring.py::test_vlm_description_generation`: Assert VLM wrapper returns a non-empty string description for a valid image prompt.
- [~] T016b [P] [US2] Write `tests/unit/test_scoring.py::test_logic_score_range`: Assert Logic Score (cosine similarity) is in [-1, 1].

### Implementation for User Story 2

- [~] T017 [US2] Implement `src/models/vlm.py` wrapper for `Phi-3-mini-4k-instruct-GGUF` (4-bit, CPU-only) using `llama-cpp-python` with initial batch size 8
- [~] T018 [US2] Implement `src/services/scoring.py` Logic Score logic: Embed instruction & VLM description via `all-MiniLM-L-v2`, compute cosine similarity
- [~] T019 [US2] Implement `src/services/scoring.py` Fidelity Score logic: Compute SSIM and LPIPS, calculate a weighted combination of SSIM and (1-LPIPS)
- [ ] T020 [US2] Implement batch processing loop in `src/services/scoring.py` with **pre-flight memory estimation** and **dynamic batch-size adjustment**. Formula: `RAM_est = model_size_gb * 1.2 + batch_size * image_size_mb` where `image_size_mb` is the memory of a single resized 512x512 RGB float32 tensor. Reduce batch size if `RAM_est > 6.5GB` (7GB limit minus 0.5GB safety buffer) to guarantee 7GB limit is never exceeded; skip failures with logs.
- [ ] T021 [US2] Integrate scoring into `src/cli/main.py` (Stage: `score`) and write results to `data/scores/`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation Analysis (Priority: P3)

**Goal**: Perform independence check, multiple linear regression, and Benjamini-Hochberg correction to determine the stronger predictor.

**Independent Test**: Verify regression output includes standardized betas, p-values, and FDR-corrected significance; check independence check halts if |r| ≥ 0.5.

### Tests for User Story 3 (TDD - Write FIRST) ⚠️

- [ ] T022 [P] [US3] Write `tests/unit/test_analysis.py::test_pearson_threshold_halt`: Assert that if correlation >= 0.5, the function raises `CircularValidationRiskError`.
- [ ] T023 [P] [US3] Write `tests/unit/test_analysis.py::test_fisher_z_test`: Assert Fisher's r-to-z transformation calculates the correct z-score and p-value for two independent correlations.
- [ ] T023b [P] [US3] Write `tests/unit/test_analysis.py::test_fdr_correction`: Assert Benjamini-Hochberg correction correctly adjusts p-values.

### Implementation for User Story 3

- [ ] T024a [US3] Implement `src/services/analysis.py` to generate and archive `outputs/circular_validation_risk_report.json` containing the correlation value `r`, the threshold, and the halt decision. This task MUST complete the file write and close the file handle before T024 proceeds.
- [ ] T024 [US3] Implement `src/services/analysis.py` independence check: Calculate Pearson correlation between Human Score and Logic Score; if |r| ≥ 0.5, log the risk flag, ensure T024a has completed, then raise `CircularValidationRiskError` exception with message "CIRCULAR_VALIDATION_RISK: |r|={value:.4f} >= 0.5" and exit process with code 1 to halt pipeline.
- [ ] T025 [US3] Implement `src/services/analysis.py` multiple linear regression: Dependent=Human Score, Independent=Logic & Fidelity Scores
- [ ] T025a [US3] Implement `src/services/analysis.py` to invoke the **Reference-Validator Agent** as a blocking gate before regression begins to verify external citations (Constitution Principle II).
- [ ] T026 [US3] Implement `src/services/analysis.py` Benjamini-Hochberg correction on regression p-values (FDR ≤ 0.05)
- [ ] T028a [US3] Implement `src/services/analysis.py` to perform a **statistical test for the difference in correlation strength** (Fisher's r-to-z transformation) between Logic and Fidelity predictors. The task must verify if Logic correlation exceeds Fidelity correlation by **at least 0.1** AND the **p-value of the difference is < 0.05**. Output results to `outputs/correlation_diff_test.json` with fields: `z_score`, `p_value`, `effect_size`, `conclusion`.
- [ ] T029 [US3] Generate final report in `outputs/regression_report.md`. Decision Logic: If (diff >= 0.1 AND p_diff < 0.05) -> State "Logic is stronger predictor". Else if (beta_fidelity > beta_logic AND p_diff < 0.05) -> State "Fidelity is stronger predictor". Else -> State "Inconclusive". The report must state the result of the difference test (T028a).
- [ ] T030 [US3] Integrate analysis into `src/cli/main.py` (Stage: `analyze`)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Add contract tests validating `data/scores/*.json` against `contracts/score-record.schema.yaml`
- [ ] T032 [P] Performance optimization: Ensure VLM batch size and image resizing are tuned for a constrained runtime limit.
- [ ] T033 [P] Execute the Advancement-Evaluator Agent to update `state/projects/PROJ-814-...yaml` with requirements.txt hash and dataset checksums.
- [ ] T034 [P] Run `quickstart.md` validation and update documentation with execution instructions

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

- Tests (if included) MUST be written and FAIL before implementation
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
- **Critical Constraint**: All VLM inference must use CPU-only 4-bit quantization (`llama-cpp-python`) to fit within 7GB RAM.
- **Critical Constraint**: No GPU/CUDA usage allowed; `torch` must be CPU version.
- **Critical Constraint**: Dataset download must use real URLs; no synthetic data generation.
- **Critical Constraint**: T024 must raise an exception and exit if correlation threshold is breached; T020 must use pre-flight memory estimation with a 6.5GB safety buffer.