# Tasks: llmXive follow-up: extending "Edit-Compass & EditReward-Compass: A Unified Benchmark for Image Editing"

**Input**: Design documents from `/specs/001-llmxive-followup-correlation-study/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

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

- [X] T002 Initialize project with `requirements.txt` (pinning `transformers==4.41.0`, `sentence-transformers==2.7.0`, `torch==2.2.2+cpu`, `llama-cpp-python==0.2.80`, `scikit-image`, `lpips==0.1.4`, `statsmodels`, `numpy`, `scipy`, `pandas`, `tqdm`).
- [X] T003 [P] Create `pyproject.toml` with `[tool.black]` (line-length=88) and `[tool.ruff]` (select=['E', 'F', 'W']) sections to configure linting and formatting. This single file replaces separate `.ruff.toml` and `.black` files to avoid redundancy.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement basic logging utility in `src/utils/logging.py` (JSON format, file + stdout)
- [X] T006 [P] Create `src/data_models.py` defining `EditInstance` Pydantic model (must include fields: `source_image_path`, `edited_image_path`, `instruction`, `category`, `human_judgment_score`) and `ScoreRecord` Pydantic model (must include fields: `instance_id`, `logic_score`, `fidelity_score`, `ssim`, `lpips`, `vllm_description`). This file serves as the primary data model definition.
- [X] T006b [P] Define the `RegressionResult` Pydantic model class in `src/data_models.py` with `Optional[float]` fields for `fdr_corrected_p_logic` and `fdr_corrected_p_fidelity` to allow instantiation before T026 runs. Verification: `grep -q "fdr_corrected_p_logic" src/data_models.py` and `grep -q "Optional\[float\]" src/data_models.py`.
- [X] T007 [P] Create `contracts/score-record.schema.yaml` for JSON schema validation of `ScoreRecord` (Depends on T006). Verification: `test -f contracts/score-record.schema.yaml` and validate YAML syntax.
- [X] T007a [P] Create `contracts/regression-result.schema.yaml` for JSON schema validation of `RegressionResult` (Depends on T006b). Verification: `test -f contracts/regression-result.schema.yaml` and validate YAML syntax.
- [X] T008 [P] Implement `src/cli/main.py` entry point with argument parsing for pipeline stages
- [X] T008a [P] Implement `src/services/reference_validator.py` to perform local citation verification (checking title overlap >= 0.7 and URL reachability). This local implementation explicitly satisfies the Constitution's Principle II (Verified Accuracy) for offline execution by emulating the Reference-Validator Agent's flow, replacing the external agent dependency.
- [X] T009 [P] Create directory structure: `data/raw`, `data/filtered`, `data/scores`, `outputs`, `contracts`. Ensure `.gitkeep` files exist in all directories to preserve them in git.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Filtering (Priority: P1) 🎯 MVP

**Goal**: Download the Edit-Compass dataset and filter for "World Knowledge Reasoning" and "Visual Reasoning" categories.

**Independent Test**: Verify `data/filtered/` contains only valid JSON/CSV entries with the required category labels and that raw data is untouched in `data/raw/`.

### Implementation for User Story 1

- [X] T011 [US1] Implement `src/services/download.py` to fetch Edit-Compass dataset via `wget`/`curl` from official repo: `https://huggingface.co/datasets/HuggingFaceH4/edit-compass`. Save raw data to `data/raw/edit-compass.json`. Validate the presence of the 'category' key using `jq` (e.g., `jq '.[0].category' data/raw/edit-compass.json`) and verify at least one record contains "World Knowledge Reasoning" or "Visual Reasoning".
 - **Error Handling**:
 1. If download fails, exit with code 1 and log "FATAL: Download failed. Aborting."
 2. If file structure is invalid (missing 'category' key), exit with code 1 and log "FATAL: File structure mismatch. Missing 'category' key."
 3. If zero records match target categories, exit with code 1 and log "FATAL: Filter returned zero records for target categories."
 Verification: `test -f data/raw/edit-compass.json` and `jq '.[0].category' data/raw/edit-compass.json | grep -q "World Knowledge Reasoning\|Visual Reasoning"`.
- [X] T012 [US1] Implement `src/services/filter.py` to load raw data, filter by `category` in ["World Knowledge Reasoning", "Visual Reasoning"], and save to `data/filtered/`. If zero records match, exit with code 1 and log "ERROR: Filter returned zero records."
- [X] T012b [P] [US1] Implement validation in `src/services/filter.py` to check that `human_judgment_score` is present and numeric for **every** record in the filtered set.
 - **Error Handling**: If ANY record is missing `human_judgment_score` or is non-numeric, exit with code 1 and log "FATAL: Required variable 'human_judgment_score' missing or invalid in filtered dataset. Halting."
 - **Output**: Write a report `outputs/exclusion_report.json` with `total_records`, `valid_records`, `excluded_records` (should be 0 if halting, or count if not halting - but logic requires halting). This task **HALTS** the pipeline on missing data, satisfying SC-005.
 Verification: `test -f outputs/exclusion_report.json` and `grep -q "FATAL" outputs/exclusion_report.json` (if halted).
- [X] T014 [US1] Integrate download and filter into `src/cli/main.py` (Stage: `download-filter`)

### Tests for User Story 1 (TDD - Write AFTER Implementation) ⚠️

- [X] T009a-1 [P] [US1] Write `tests/unit/test_download.py::test_url_validity`: Assert that the download URL (https://huggingface.co/datasets/HuggingFaceH4/edit-compass) returns HTTP 200 and content type is valid. Run: `pytest tests/unit/test_download.py::test_url_validity`. (Depends on T011).
- [X] T009a-2 [P] [US1] Write `tests/unit/test_download.py::test_checksum_verification`: Assert that the downloaded file SHA256 matches the expected checksum. Run: `pytest tests/unit/test_download.py::test_checksum_verification`. (Depends on T011).
- [X] T010a [P] [US1] Write `tests/unit/test_filter.py::test_valid_category_match`: Assert that filtering by ["World Knowledge Reasoning", "Visual Reasoning"] returns only records where the category field EXACTLY matches one of these values. (Depends on T012).
- [X] T010b [P] [US1] Write `tests/unit/test_filter.py::test_empty_result_handling`: Assert that if no matches are found, the script exits with exit code 1 and logs the message "FATAL: Filter returned zero records for target categories." (Depends on T012).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Scoring Generation (Priority: P2)

**Goal**: Compute Logic Consistency Score (VLM) and Fidelity Score (SSIM/LPIPS) for each filtered instance.

**Independent Test**: Run on a small batch; verify `data/scores/` contains JSON with numeric Logic/Fidelity scores (0-1 range) and no nulls.

### Implementation for User Story 2

- [X] T017 [US2] Implement `src/models/vlm.py` wrapper for `Phi-3-mini-4k-instruct-GGUF` (Low-bit, CPU-only) using `llama-cpp-python` and `src/services/scoring.py` for Logic Score (cosine similarity via `sentence-transformers/all-MiniLM-L6-v2` with L2-normalized vectors) and Fidelity Score (SSIM + (-LPIPS)). The model artifact MUST be downloaded from `https://huggingface.co/TheBloke/Phi-mini-4k-instruct-GGUF` with the exact filename `phi-3-mini-4k-instruct.Q4_K_M.gguf`.
 - **Memory Estimation**: Implement pre-flight memory estimation: `RAM_est = 2.0 + (batch_size * 0.05)`, where 2.0 is the base model overhead in GB and 0.05 is the estimated per-image batch overhead. Set `RAM_limit = 7 * 0.95` GB. Dynamically adjust batch size (start at) to ensure `RAM_est < RAM_limit`.
 - **Logging**: Log the final batch size used: "Final batch size: X".
 - **Verification**: `grep -q "all-MiniLM-L6-v2" src/services/scoring.py` and `grep -q "L2-normalized" src/services/scoring.py` and `grep -q "Final batch size" src/services/scoring.py`.
- [X] T021 [US2] Integrate scoring into `src/cli/main.py` (Stage: `score`) and write results to `data/scores/`

### Tests for User Story 2 (TDD - Write AFTER Implementation) ⚠️

- [X] T015a-1 [P] [US2] Write `tests/unit/test_scoring.py::test_ssim_calculation`: Assert SSIM calculation on dummy images returns a value within the valid normalized range.. Run: `pytest tests/unit/test_scoring.py::test_ssim_calculation`. (Depends on T017).
- [X] T015a-2 [P] [US2] Write `tests/unit/test_scoring.py::test_lpips_calculation`: Assert LPIPS calculation on dummy images returns a normalized value within a bounded range.. Run: `pytest tests/unit/test_scoring.py::test_lpips_calculation`. (Depends on T017).
- [X] T016 [P] [US2] Write `tests/unit/test_scoring.py::test_vlm_description_generation`: Assert VLM wrapper returns a non-empty string description for a valid image prompt. (Depends on T017).
- [X] T016b [P] [US2] Write `tests/unit/test_scoring.py::test_logic_score_range`: Assert Logic Score (cosine similarity) is within a bounded range.. (Depends on T017).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation Analysis (Priority: P3)

**Goal**: Perform independence check, multiple linear regression, and Benjamini-Hochberg correction to determine the stronger predictor.

**Independent Test**: Verify regression output includes standardized betas, p-values, and FDR-corrected significance; check independence check halts if |r| ≥ 0.5.

### Implementation for User Story 3

- [X] T024a [US3] Implement `src/services/analysis.py` to extract and validate the 'Human Judgment Score' field from the filtered dataset (`data/filtered/`). Ensure the field exists and is numeric for all records. If missing, raise `ValueError` with message "ERROR: Human Judgment Score missing". (Prerequisite for T024). **Note**: This is a safety net; T012b should have already halted on missing data. Depends on T012.
- [X] T024 [US3] Implement `src/services/analysis.py` independence check: Calculate Pearson correlation between Human Score (from T024a) and Logic Score. If |r| ≥ 0.5, atomically write `outputs/circular_validation_risk_report.json` (using temp file `outputs/.risk_report.tmp` and `os.rename`) with fields `r` (float), `threshold` (0.5), `decision` ("HALT"), `timestamp` (ISO 8601) BEFORE raising `CircularValidationRiskError` and exiting with code 1. The CLI entry point (`src/cli/main.py`) MUST catch this exception and exit with code 1 to halt the pipeline. Verification: `test -f outputs/circular_validation_risk_report.json` and `jq. outputs/circular_validation_risk_report.json`. (Depends on T024a, T017).
- [X] T025 [US3] **Conditional Execution**: Implement `src/services/analysis.py` multiple linear regression: Dependent=Human Score, Independent=Logic & Fidelity Scores. **SKIPPED** if T024 raised an error or the risk report exists. This task is only executed if T024 completes successfully (no error raised). (Depends on T024 success).
- [X] T026 [US3] Implement `src/services/analysis.py` Benjamini-Hochberg correction on regression p-values (FDR ≤ 0.05). Verification: `grep -q "benjamini_hochberg" src/services/analysis.py`.
- [X] T028a [US3] Implement `src/services/analysis.py` to perform a Fisher's r-to-z transformation to test the difference in correlation strength between Human Preference vs Logic Score and Human Preference vs Fidelity Score. Output results to `outputs/correlation_diff_test.json` with fields: `z_score`, `p_value_diff` (the p-value for the difference test), `correlation_difference`, `effect_size`, `conclusion`, `threshold_value` (0.1), `threshold_met` (boolean). This test is required by Success Criteria SC-001. (Depends on T025, T026).
- [X] T028b [US3] Implement `src/services/analysis.py` to calculate the difference in standardized beta coefficients (`beta_logic - beta_fidelity`) as a secondary metric. (Depends on T025).
- [X] T029 [US3] Generate final report in `outputs/regression_report.md`. **Decision Logic**:
 1. **Primary**: Read `outputs/correlation_diff_test.json`. If (`correlation_difference` >= 0.1 AND `p_value_diff` < 0.05) -> State "Logic is stronger predictor".
 2. **Secondary**: If Primary condition fails, report beta difference as a secondary metric ONLY. **DO NOT** conclude "Logic is the stronger predictor" based solely on beta weight.
 The report MUST explicitly output `threshold_met` (boolean) and `threshold_value` (0.1) for the correlation difference. (Reference: arXiv:1706.08250 for statistical context on correlation differences). (Depends on T025, T026, T028a, T028b).
- [X] T029b [US3] Implement validation in `src/services/analysis.py` to ensure FDR-corrected p-values are present and non-null in the final `RegressionResult` before report generation (T029). If null, raise `ValueError`. (Depends on T026).
- [X] T030 [US3] Integrate analysis into `src/cli/main.py` (Stage: `analyze`)

### Tests for User Story 3 (TDD - Write AFTER Implementation) ⚠️

- [X] T022 [P] [US3] Write `tests/unit/test_analysis.py::test_pearson_threshold_halt`: Assert that if correlation >= 0.5, the function raises `CircularValidationRiskError`. Run: `pytest tests/unit/test_analysis.py::test_pearson_threshold_halt`. (Depends on T024).
- [X] T023 [P] [US3] Write `tests/unit/test_analysis.py::test_fisher_z_test`: Assert Fisher's r-to-z transformation calculates the correct z-score and p-value for two independent correlations. Run: `pytest tests/unit/test_analysis.py::test_fisher_z_test`. (Depends on T028a).
- [X] T023b [P] [US3] Write `tests/unit/test_analysis.py::test_fdr_correction`: Assert Benjamini-Hochberg correction correctly adjusts p-values. Run: `pytest tests/unit/test_analysis.py::test_fdr_correction`. (Depends on T026).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Add contract tests validating `data/scores/*.json` against `contracts/score-record.schema.yaml` and `outputs/regression_report.json` against `contracts/regression-result.schema.yaml`.
- [X] T032 [P] Run a full pass of the scoring pipeline and verify peak RAM usage is < 7GB in the logs, confirming the dynamic batch-size adjustment logic in T017 functions correctly. Generate `outputs/memory_profile.log` with peak RAM stats.
- [X] T033 [P] Execute the Advancement-Evaluator Agent to update `state/projects/PROJ-814-...yaml` with requirements.txt hash and dataset checksums.
- [X] T034 [P] Run `python -m src.cli.main --validate-docs` and update `quickstart.md` with the new CLI flags and execution instructions.

---

## Phase 7: Review Resolution & Robustness (New Tasks)

**Goal**: Address specific concerns regarding data integrity, error handling, and VLM stability identified in prior analysis.

### Implementation for Review Resolution

- [X] T035 [P] [US1] Implement strict "Fail-Loud" logic in `src/services/download.py`. Remove any `try/except` blocks that fall back to synthetic data. If `wget`/`curl` fails or the file structure is invalid, raise a `DataFetchError` with a specific error code and log "FATAL: Real data fetch failed. Aborting. Do not substitute synthetic data." (Ref: Constitution Principle I (Reproducibility) and Principle III (Data Hygiene)).
- [X] T036 [X] [US2] Implement robust timeout handling in `src/models/vlm.py`. If the VLM generation exceeds a defined timeout (e.g., a predefined interval) or runs out of memory, catch the specific exception, log the `instance_id` to `outputs/skipped_instances.log`, and skip the instance gracefully without crashing the entire batch. Do not return a default score. **Verification**: `test -f outputs/skipped_instances.log` and `grep -q "timeout\|oom" outputs/skipped_instances.log` (if any instances were skipped).
- [X] T037 [X] [US2] Add a pre-flight check in `src/services/scoring.py` to verify that `source_image_path` and `edited_image_path` actually exist on disk before attempting SSIM/LPIPS calculation. If missing, log a warning and skip the instance, ensuring the pipeline does not crash on corrupted file paths. **Verification**: `test -f outputs/skipped_instances.log` and `grep -q "missing_path" outputs/skipped_instances.log` (if any instances were skipped).
- [X] T038 [P] [US3] Implement a Variance Inflation Factor (VIF) calculation in `src/services/analysis.py` (Depends on T025). If VIF for either predictor > 5.0, append a "Collinearity Warning" section to `outputs/regression_report.md` explaining that independent effects may be confounded.

---

## Phase 8: Final Validation & Reporting (Revision Round 1)

**Goal**: Ensure all critical constraints are met and the pipeline produces a scientifically valid, reproducible result before final submission.

### Implementation for Final Validation

- [X] T039 [P] [US3] Implement a final "Sanity Check" script in `src/cli/main.py` (Stage: `validate-final`) that re-runs the Fisher's r-to-z test (T028a) logic (importing the function from T028a) and verifies the `threshold_met` boolean matches the `correlation_difference` and `p_value_diff` logic defined in T029. If the logic is inconsistent, raise an error and halt.
- [ ] T040 [P] [US1] Add a "Data Integrity" verification task in `src/services/download.py` that computes the SHA256 checksum of the final `data/filtered/` dataset and compares it against a known-good checksum stored in `state/projects/PROJ-814-checksums.yaml` under the key `filtered_dataset_sha256`. If mismatched, log a critical error.
- [ ] T041 [P] [US2] Implement a "Batch Size Stress Test" in `src/services/scoring.py` that attempts to run the scoring pipeline with `batch_size=1` (minimum) and `batch_size=16` (maximum theoretical) to verify the dynamic adjustment logic (T017) correctly identifies the optimal batch size under memory pressure. Log the results to `outputs/batch_stress_test.log`.
- [ ] T042 [P] [US3] Generate a "Methodology Transparency" report in `outputs/methodology_report.md` that explicitly lists: (1) The exact version of `Phi-3-mini` used, (2) The exact prompt template used for VLM description generation (sourced from `src/config/prompts.yaml`), (3) The exact formula for the Logic Score (including normalization), (4) The exact parameters for SSIM and LPIPS. This report is required for reproducibility (Constitution Principle I).
- [ ] T043 [P] [US3] Implement a "Sensitivity Analysis" in `src/services/analysis.py` that re-runs the regression with a random subsample of the data (multiple iterations) to verify the stability of the `beta_logic` and `beta_fidelity` coefficients. Report the standard deviation of these coefficients in `outputs/sensitivity_analysis.json`.
- [ ] T044 [P] [Global] Run the full pipeline end-to-end on a small subset of instances to verify that all stages (Download -> Filter -> Score -> Analyze) complete without error and produce the expected output files. This is a "Smoke Test" for the entire pipeline. **Constraint**: This task MUST depend on T046 to measure and enforce the 6-hour runtime limit.
- [ ] T045 [P] [Global] Update `README.md` with a "Running the Study" section that includes: (1) Prerequisites, (2) Installation steps, (3) How to run the full pipeline, (4) How to interpret the results (specifically the `threshold_met` field), and (5) A link to the `methodology_report.md`.
- [ ] T046 [P] [Global] Implement a "Runtime Monitor" wrapper in `src/cli/main.py` that measures total pipeline elapsed time. If runtime exceeds 6 hours, log "FATAL: Pipeline exceeded 6-hour time limit" and exit with code 1. This task satisfies SC-003 and is a dependency for T044.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review Resolution (Phase 7)**: Can run in parallel with Phase 6, but must be completed before final validation.
- **Final Validation (Phase 8)**: Depends on all previous phases being complete.

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
- Review Resolution tasks (Phase 7) and Final Validation tasks (Phase 8) can run in parallel with Phase 6 tasks.

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
4. Once US2 scores is ready: Developer C: User Story 3 (Analysis)
5. Final Polish: Tests, docs, performance tuning
6. Review Resolution: Implement robustness checks (Phase 7) concurrently or immediately after.
7. Final Validation: Run full pipeline and generate reports (Phase 8).

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
- **Critical Constraint**: T024 must atomically write the risk report (using temp file + rename) and raise the exception to prevent state loss. T017 must use pre-flight memory estimation with a safety buffer of 0.1 applied to the dataset size. **NO image resizing** is permitted; SSIM/LPIPS must be calculated on original images.
- **Critical Constraint**: T008a must implement the local reference validator to replace the external agent dependency, satisfying Constitution Principle II.
- **Critical Constraint**: T032 verifies the dynamic batch logic; do not hardcode batch sizes.
- **Critical Constraint**: T009 ensures all necessary directories exist with.gitkeep files to prevent git from ignoring them.
- **Critical Constraint (New)**: T035 enforces the "Fail-Loud" principle. Synthetic fallbacks are strictly forbidden.
- **Critical Constraint (New)**: T036 ensures VLM timeouts do not crash the pipeline; skipped instances are logged, not imputed.
- **Critical Constraint (New)**: T038 adds VIF analysis to detect collinearity, ensuring the regression interpretation is statistically sound.
- **Critical Constraint (New)**: T028a is required by SC-001 to test the difference in correlation coefficients, not just beta weights.
- **Critical Constraint (New)**: T029 strictly enforces SC-001 as the sole condition for the primary conclusion; beta weight alone cannot trigger the "Logic is stronger predictor" conclusion.
- **Critical Constraint (New)**: T036 and T037 must be marked as [X] upon completion to satisfy Edge Case requirements.
- **Critical Constraint (New)**: Phase 8 tasks (T039-T045) are mandatory for final validation and must be completed before the project is considered "analyzed".
- **Critical Constraint (New)**: T046 is the dedicated mechanism for enforcing the 6-hour runtime limit (SC-003) and is a dependency for T044.