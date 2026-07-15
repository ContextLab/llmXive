# Tasks: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

**Input**: Design documents from `/specs/001-evaluating-code-summarization-bug-localization/`
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

- [X] T001 Create project structure per implementation plan: `mkdir -p code/data_prep code/analysis code/utils code/tests data/defects4j data/summaries data/interaction_logs data/analysis_results data/consent state/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure (`data/defects4j`, `data/summaries`, `data/interaction_logs`, `data/analysis_results`, `data/consent`)
- [X] T005 [P] Implement `code/utils/hash_artifacts.py` for versioning discipline (SHA-256 generation)
- [X] T006 [P] Setup environment configuration management (`.env` for paths, seeds)
- [X] T007 Create base data models (Participant, Task, Summary, AnalysisResult) in `code/utils/models.py`
- [X] T008 Configure error handling and logging infrastructure (`code/utils/logging_utils.py`)
- [ ] T009 [P] Setup CI resource monitor `code/utils/resource_monitor.py` to assert ≤7GB RAM and ≤6h runtime via in-script assertions as per FR-007's CI test procedure
- [ ] T018a [P] [US1] Define API contract for participant interaction data collection in `contracts/api_participant.md` (endpoints, request/response bodies, session management)
- [ ] T018b [US1] Implement `frontend/src/ParticipantForm.jsx` (or equivalent) based on the API contract defined in T018a (`contracts/api_participant.md`) to collect interaction data
- [ ] T018c [US1] Implement `backend/src/api/participant.py` (or equivalent) to handle submissions, manage session state, and apply Latin-square assignment logic. **Depends on T007 (Base data models)**. (Note: [P] tag removed as it depends on T007)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Human Subject Study Data Collection (Priority: P1) 🎯 MVP

**Goal**: Collect participant interaction data and prepare the dataset (Defects4J + Summaries) for the study.

**Independent Test**: Can be fully tested by simulating multiple tasks per participant for A small cohort of participants and verifying the CSV output contains valid timestamps, line selections, and participant IDs for all three conditions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [US1] Unit test for latency calibrator in `code/tests/test_latency_calibrator.py`. **Depends on T012** (Note: [P] tag removed as it depends on T012) <!-- FAILED: unspecified -->
- [ ] T011 [US1] Unit test for Defects4J download integrity in `code/tests/test_defects4j_download.py`. **Depends on T013** (Note: [P] tag removed as it depends on T013) <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/utils/latency_calibrator.py` to verify timestamp precision ≤100ms (FR-003)
- [~] T012a [US1] Integrate `code/utils/latency_calibrator.py` into the application startup flow (e.g., in `backend/src/main.py` or `frontend/src/App.jsx`) to ensure the test runs at startup as mandated by FR-003
- [X] T013 [US1] Implement `code/data_prep/download_defects4j.py` to fetch DefectsJ and extract 60 stratified buggy methods (FR-001)
- [X] T014 [US1] Implement `code/data_prep/generate_summaries.py` with:
 - Deterministic "LLM-Sim" generator (CPU-tractable, no GPU) mimicking LLM structure as a **staged implementation**; the real `codellama/CodeLlama-7b-hf` integration is deferred for GPU environments to satisfy CI constraints without violating FR-002's intent.
 - Rule-based `srcML` comment extractor fallback
 - Logic to handle LLM generation failure/timeout (FR-002)
 - **Deterministic Algorithm**: Use template "Method: <name>\nParams: <args>\nReturns: <type>\nComment: <first_comment_line>". **Edge Case Handling**: If no comments exist, use "No comment available"; if no parameters, use "No parameters".
 - Output: `data/summaries/llm_sim_summaries.csv` and `data/summaries/rule_summaries.csv`
 - **Depends on T013** (Note: [P] tag removed as it depends on T013)
- [X] T014a [US1] Implement `code/data_prep/generate_summaries_real_llm.py` for Real LLM generation path (HuggingFace `codellama/CodeLlama-7b-hf` with 8-bit quantization) for non-CI environments. **Requires GPU/CUDA**. If generation fails (timeout, empty output), fall back to rule-based summary (FR-002).
- [~] T015 [US1] Implement `code/utils/interaction_logger.py` to record CSV logs (participant_id, task_id, condition, timestamp_ms, selected_line, ground_truth_line) to `data/interaction_logs/raw_logs.csv` (FR-003)
- [~] T016 [US1] Implement data anonymization script `code/utils/anonymize_logs.py` to generate `data/interaction_logs/anonymized_logs.csv` (VI) - creates new file, does not overwrite raw logs
- [X] T017 [US1] Implement dropout handling logic in `code/utils/interaction_logger.py` to flag partial data (Edge Case)
- [~] T019 [US1] Implement secure storage logic for raw consent forms in non-public `data/consent/` directory with `.gitignore` exclusion and access control (Constitution Principle VI). **Implementation**: Set file permissions to `chmod 600` for all files in `data/consent/` and add explicit `.gitignore` rule.
- [X] T020 [US1] Implement Latin-square design assignment logic in `code/utils/assignment_generator.py` to generate balanced task conditions for a cohort of participants (US-1, Assumptions)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2)

**Goal**: Run McNemar's tests for accuracy and LME models for speed, computing effect sizes and confidence intervals.

**Independent Test**: Can be fully tested by feeding a synthetic CSV dataset and verifying the analysis outputs p-values, effect sizes (Odds Ratio, Cohen's d), and 95% confidence intervals for all four comparisons.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for McNemar's test implementation in `code/tests/test_statistics.py`
- [X] T022 [P] [US2] Unit test for LME model and bootstrapping in `code/tests/test_bootstrap_utils.py`

### Implementation for User Story 2

- [X] T025 [US2] Define sensitivity analysis range in `code/analysis/config.py` to specify the "standard cutoffs" for the sweep. **Mandatory values**: `[0.01, 0.05, 0.10]`. **Note**: This task must be completed before T024 to ensure config exists.
- [X] T023 [US2] Implement `code/analysis/bootstrap_utils.py` for bootstrapping (A substantial number of resamples, fixed seed) to compute confidence intervals (FR-005)
- [X] T023a [US2] Implement `code/analysis/correction_utils.py` for multiple-comparison correction logic (Holm-Bonferroni) (FR-006)
- [X] T024a [US2] Implement `code/analysis/run_statistics.py` to:
 - Load `data/interaction_logs/anonymized_logs.csv` and summary data
 - Compute **Top-K accuracy** (e.g., Top-5) and speed (time-to-decision) metrics (Complexity Tracking)
 - Run McNemar's tests for accuracy (baseline vs LLM, baseline vs Rule) (FR-004)
 - Run Linear Mixed-Effects (LME) models with random intercepts for participants (FR-004)
 - Output `data/analysis_results/results.csv` with all metrics
 - Output `data/analysis_results/sensitivity_analysis.csv` with threshold sweep results
 - Output `data/analysis_results/outlier_flags.json` with outlier detection flags
- [X] T024b [US2] Implement `code/analysis/run_statistics.py` (continued) to:
 - **Import and invoke bootstrapping functions from `code/analysis/bootstrap_utils.py`**
 - Compute Odds Ratios and Cohen's d with bootstrapped CIs (FR-005)
 - **Import and invoke correction function from `code/analysis/correction_utils.py`**
 - Apply Holm-Bonferroni correction (α=0.05) (FR-006)
 - Finalize output files

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproducibility Package Generation (Priority: P3)

**Goal**: Generate a reproducible research package (scripts + anonymized logs) that runs on GitHub Actions free-tier.

**Independent Test**: Can be fully tested by cloning the OSF repository, running the analysis script in a GitHub Actions free-tier runner, and verifying the output matches the original results within a 5% numerical tolerance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T027 [P] [US3] Integration test for CI resource constraints in `.github/workflows/test_reproducibility.yml`
- [X] T028 [P] [US3] Test for numerical tolerance (5%) between original and rerun results in `code/tests/test_reproducibility.py`

### Implementation for User Story 3

- [~] T030a [US3] Implement `code/utils/generate_baseline_results.py` to run the analysis script once, capture the output, and commit `data/analysis_results/baseline_results.json` as the ground truth for the 5% tolerance check.
- [ ] T030 [US3] Implement `.github/workflows/test_reproducibility.yml` to:
 - Install dependencies
 - Run `code/analysis/run_statistics.py`
 - Assert runtime ≤6h and memory ≤7GB
 - Verify numerical tolerance against `data/analysis_results/baseline_results.json` (generated by T030a) (SC-004, SC-005)
 - **Note**: T030 depends on T030a completion.
- [~] T029 [US3] Create `README.md` documenting how to rerun analysis on GitHub Actions free-tier (≤6h, ≤7GB RAM, NO GPU) (FR-007) - **Depends on T030**
- [ ] T031 [US3] Generate final reproducibility package bundle `data/reproducibility_package_v1.0.tar.gz` containing scripts, `data/analysis_results/results.csv`, `data/interaction_logs/anonymized_logs.csv`, `README.md` for OSF publication (FR-007). **Exclusion**: Explicitly exclude `data/consent/` from the bundle to satisfy Constitution Principle VI.
- [~] T032 [US3] Update `state/projects/PROJ-140.../artifact_hashes.yaml` with final hashes of all artifacts (V)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T033 [P] Update `README.md` with installation steps and dependencies
- [~] T034 [P] Update `README.md` with analysis execution steps and expected outputs
- [X] T035 [P] Add API documentation to `docs/api.md`
- [X] T036 Code cleanup: Refactor `code/utils/logging_utils.py` to remove unused imports
- [X] T037 Code cleanup: Refactor `code/utils/models.py` to simplify data structures
- [X] T038 Performance optimization: Reduce memory usage to <6GB in `code/analysis/run_statistics.py`
- [ ] T039 Performance optimization: Reduce runtime to <5h in `code/analysis/run_statistics.py`
- [ ] T040 [P] Add unit tests for edge cases in `code/tests/test_statistics.py`
- [ ] T041 [P] Add unit tests for data integrity in `code/tests/test_data_integrity.py`
- [ ] T042 Security hardening (ensure no sensitive data leaks in logs)
- [ ] T043 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (P2)**: **Must wait** for User Story 1 data generation (T013-T020) to complete. Cannot run in parallel with US1.
 - **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 analysis completion (T024)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **Strictly depends** on US1 data generation (T013-T020). US2 cannot start until US1 is complete.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 analysis completion (T024)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT**:
 - T018c (Backend API) depends on T007 (Base data models) and cannot run in parallel.
- **Once Foundational phase completes:**
 - User Story 1 (Data Collection) can start immediately.
 - User Story 2 (Analysis) **MUST WAIT** for US1 to finish data generation.
 - User Story 3 (Reproducibility) can start once US2 is complete.
- All tests for a user story marked [P] can run in parallel **EXCEPT**:
 - T010 depends on T012.
 - T011 depends on T013.
- Models within a story marked [P] can run in parallel
- Different user stories **CANNOT** be worked on in parallel if they have producer-consumer dependencies (e.g., US2 depends on US1).
- T030 (CI Workflow) depends on T030a (Baseline Generation) completion.

### Specific Task Dependencies

- T018b depends on T018a (API Contract).
- T018c depends on T018a (API Contract) and T007 (Base data models).
- T014 depends on T013 (Download Defects4J).
- T024 depends on T025 (Sensitivity Analysis Config).
- T030 depends on T030a (Baseline Generation).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for latency calibrator in code/tests/test_latency_calibrator.py"
Task: "Unit test for Defects4J download integrity in code/tests/test_defects4j_download.py"

# Launch all models for User Story 1 together:
Task: "Implement code/utils/latency_calibrator.py"
Task: "Implement code/data_prep/download_defects4j.py"
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
3. Add User Story 2 → Test independently → Deploy/Demo (Requires US1 data)
4. Add User Story 3 → Test independently → Deploy/Demo (Requires US2 results)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Collection)
 - Developer B: User Story 2 (Analysis Pipeline) - **Must wait for US1 to complete**
 - Developer C: User Story 3 (Reproducibility) - **Must wait for US2 to complete**
3. Stories complete and integrate sequentially based on dependencies.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All LLM-related tasks in CI must use the deterministic `LLM-Sim` generator (T014) to satisfy CPU-only constraints. No 8-bit quantization or GPU usage is permitted in the CI pipeline. The real LLM integration (T014a) is for non-CI environments only.
- **CRITICAL**: T024 (Analysis) MUST be executed AFTER T013-T020 (Data Generation) are complete to ensure the input CSV exists.
- **CRITICAL**: T029 (README) depends on T030 (CI Workflow) being defined to accurately document the execution steps.
- **CRITICAL**: T025 (Sensitivity Config) MUST be completed before T024 (Analysis) to ensure config exists.
- **CRITICAL**: T030 (CI Workflow) MUST be completed after T030a (Baseline Generation) to ensure ground truth exists.