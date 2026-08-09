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

- **Single project**: `code/` at repository root (as per Plan.md)
- **Data**: `data/` at repository root
- **Tests**: `code/tests/`
- **Docs**: `docs/` at repository root

<!--
 ============================================================================
 IMPORTANT: The tasks below have been revised to match the Plan.md structure.
 
 Key Changes:
 1. Removed all FastAPI/React web stack tasks (T012b, T018a-d) as they contradicted the "Simulated Human Study" scope.
 2. Replaced with CLI-based simulation tasks in `code/simulation/`.
 3. Moved LLM generation to an "Offline Generation" phase (T014) to satisfy CI constraints.
 4. Updated all paths to use `code/` structure only.
 5. Moved mandatory Sensitivity Analysis (T044) and Outlier Detection (T045) to Phase 4.
 6. Added explicit PII verification (T031b) for Constitution Principle VI.
 ============================================================================
-->

## Phase 0: Offline Generation (Pre-requisite)

**Purpose**: Generate LLM summaries offline (requires GPU) to be loaded by CI. This phase is NOT part of the CI runner; it is a one-time pre-processing step.

- [X] T014 [P] [US1] **Offline**: Implement `code/generation/generate_summaries_offline.py` to generate LLM summaries via HuggingFace `codellama/CodeLlama-7b-hf` with 8-bit quantization (`device="cuda"`, `load_in_8bit`). 
 - **Output**: `data/summaries/llm_summaries.csv` and `data/summaries/rule_summaries.csv`
 - **Fallback**: If LLM fails, use rule-based `srcML` extractor.
 - **Note**: This task runs ONCE on a GPU machine. The resulting CSVs are committed and loaded by the CI pipeline. **Depends on T013**.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: `mkdir -p code/download code/generation code/simulation code/analysis code/utils code/tests data/raw/defects4j data/summaries data/interaction_logs data/analysis_results data/consent docs state/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure (`data/raw/defects4j`, `data/summaries`, `data/interaction_logs`, `data/analysis_results`, `data/consent`)
- [X] T005 [P] Implement `code/utils/hash_artifacts.py` for versioning discipline (SHA-256 generation)
- [X] T006 [P] Setup environment configuration management (`.env` for paths, seeds)
- [X] T007 Create base data models (Participant, Task, Summary, AnalysisResult) in `code/utils/models.py`
- [X] T008 Configure error handling and logging infrastructure (`code/utils/logging_utils.py`)
- [X] T009 [P] Setup CI resource monitor `code/utils/resource_monitor.py` to assert ≤7GB RAM and ≤6h runtime via in-script assertions as per FR-007's CI test procedure
- [X] T012b [P] [US1] Create `code/main.py` as the CLI entry point for the pipeline. **Required for T012a integration**.

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Human Subject Study Data Collection (Priority: P1) 🎯 MVP

**Goal**: Collect participant interaction data (via simulation) and prepare the dataset (Defects4J + Summaries) for the study.

**Independent Test**: Can be fully tested by simulating multiple tasks per participant for a small cohort of participants and verifying the CSV output contains valid timestamps, line selections, and participant IDs for all three conditions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [US1] Unit test for latency calibrator in `code/tests/test_latency_calibrator.py`. **Must be written before T012**.
- [X] T011 [US1] Unit test for Defects4J download integrity in `code/tests/test_defects4j_download.py`. **Must be written before T013**.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/simulation/latency_calibrator.py` to verify timestamp precision ≤100ms (FR-003). **Output**: A JSON report of latency measurements.
- [X] T012a [US1] **Startup Gate**: Integrate `code/simulation/latency_calibrator.py` into `code/main.py` startup flow. **Implementation**: Add a pre-flight check in `code/main.py` that runs `LatencyCalibrator().run()`. Asserts precision ≤100ms and raises `SystemExit` if failed, preventing any data download or simulation. **Depends on T012 and T012b**.
- [X] T013 [US1] Implement `code/download/download_defects4j.py` to fetch Defects4J v2.0 and extract a stratified sample of buggy methods (FR-001). 
 - **Output**: `data/raw/defects4j/ground_truth.csv` containing `task_id`, `method_id`, `ground_truth_line`, `project_name`.
 - **Verification**: Include a schema validation step to ensure all required columns exist.
 - **Streaming**: Use `datasets.load_dataset(..., streaming=True)` to handle large datasets within RAM constraints.
 - **Fail Loud**: Raise explicit error if download fails; no synthetic fallback.
 - **Depends on T011**.
- [X] T015 [US1] Implement `code/simulation/participant_sim.py` to simulate participant interaction logs (Latin-square design) and record CSV logs (participant_id, task_id, condition, timestamp_ms, selected_line, ground_truth_line) to `data/interaction_logs/raw_logs.csv` (FR-003). **Depends on T013 and T020**.
- [X] T016 [US1] Implement data anonymization script `code/utils/anonymize_logs.py` to generate `data/interaction_logs/anonymized_logs.csv` (VI) - creates new file, does not overwrite raw logs.
- [X] T017 [US1] Implement dropout handling logic in `code/simulation/participant_sim.py` to flag partial data (Edge Case).
- [X] T019-impl [US1] Implement `code/utils/secure_storage.py` to set file permissions (`chmod 600`) for all files in `data/consent/` and manage `.gitignore` exclusions (VI).
- [X] T019-exec [US1] Execute `code/utils/secure_storage.py` to apply permissions and exclusions. **Depends on T019-impl**.
- [X] T020 [US1] Implement Latin-square design assignment logic in `code/simulation/assignment_generator.py` to generate balanced task conditions for a cohort of participants (US-1, Assumptions).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2)

**Goal**: Run McNemar's tests for accuracy and LME models for speed, computing effect sizes and confidence intervals.

**Independent Test**: Can be fully tested by feeding a synthetic CSV dataset and verifying the analysis outputs p-values, effect sizes (Odds Ratio, Cohen's d), and 95% confidence intervals for all four comparisons.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for McNemar's test implementation in `code/tests/test_statistics.py`
- [X] T022 [P] [US2] Unit test for LME model and bootstrapping in `code/tests/test_bootstrap_utils.py`

### Implementation for User Story 2

- [X] T025 [US2] Define sensitivity analysis range in `code/analysis/config.py` to specify the "standard cutoffs" for the sweep. **Mandatory values**: a set of representative significance thresholds. **Note**: This task must be completed before T044.
- [X] T044 [US2] **Mandatory**: Implement sensitivity analysis sweep loop in `code/analysis/run_statistics.py` to iterate over the thresholds defined in T025 (`[0.01, 0.05, 0.10]`) and record how p-values shift. **Output**: `data/analysis_results/sensitivity_analysis.csv`. **Depends on T025**.
- [X] T045 [US2] **Mandatory**: Implement outlier detection logic in `code/analysis/run_statistics.py` to flag tasks with duration >30 minutes, update `data/analysis_results/outlier_flags.json`, and ensure the sensitivity analysis (T044) optionally excludes these flagged participants. **Depends on T044**.
- [X] T023 [US2] Implement `code/analysis/bootstrap_utils.py` for bootstrapping (A substantial number of resamples, fixed seed) to compute confidence intervals (FR-005)
- [X] T023a [US2] Implement `code/analysis/correction_utils.py` for multiple-comparison correction logic (Holm-Bonferroni) (FR-006)
- [X] T024 [US2] Implement `code/analysis/run_statistics.py` to:
 - Load `data/interaction_logs/anonymized_logs.csv` and summary data
 - Compute **Top-K accuracy** (e.g., Top-5) and speed (time-to-decision) metrics (Complexity Tracking)
 - Run McNemar's tests for accuracy (baseline vs LLM, baseline vs Rule) (FR-004)
 - Run Linear Mixed-Effects (LME) models with random intercepts for participants (FR-004)
 - **Import and invoke bootstrapping functions from `code/analysis/bootstrap_utils.py`** to compute Odds Ratios and Cohen's d with bootstrapped CIs (FR-005)
 - **Import and invoke correction function from `code/analysis/correction_utils.py`** to apply Holm-Bonferroni correction (α=0.05) (FR-006)
 - **Invoke T044** to generate sensitivity analysis results.
 - **Invoke T045** to generate outlier flags.
 - Output `data/analysis_results/results.csv` with all metrics.
 - **Explicitly measure and report** whether p-values meet the `<0.05` threshold as a pass/fail criterion for SC-003.
 - **Depends on T023, T023a, T025, T044, T045**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproducibility Package Generation (Priority: P3)

**Goal**: Generate a reproducible research package (scripts + anonymized logs) that runs on GitHub Actions free-tier.

**Independent Test**: Can be fully tested by cloning the OSF repository, running the analysis script in a GitHub Actions free-tier runner, and verifying the output matches the original results within a 5% numerical tolerance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Integration test for CI resource constraints in `.github/workflows/test_reproducibility.yml`
- [X] T028 [P] [US3] Test for numerical tolerance between original and rerun results in `code/tests/test_reproducibility.py`

### Implementation for User Story 3

- [X] T030a [US3] Implement `code/utils/generate_baseline_results.py` to run the analysis script and save results to `data/analysis_results/baseline_results.json`.
- [X] T030a-exec [US3] Execute `code/utils/generate_baseline_results.py` to generate `baseline_results.json` and commit it. **Depends on T030a**.
- [X] T031b [US3] **Verification**: Implement `code/utils/verify_pii_removal.py` to scan `data/interaction_logs/anonymized_logs.csv` for PII and verify `data/consent/` is excluded from VCS history. **Fail** if PII is found or `data/consent/` is present. **Depends on T016, T019**.
- [X] T031c [US3] **CI History Check**: Implement a CI step in `.github/workflows/test_reproducibility.yml` to verify that `data/consent/` is not present in the repository history. **Depends on T019**.
- [X] T030 [US3] Implement `.github/workflows/test_reproducibility.yml` to:
 - Install dependencies
 - Run `code/analysis/run_statistics.py`
 - Assert runtime ≤6h and memory ≤7GB
 - Verify numerical tolerance against `data/analysis_results/baseline_results.json` (generated by T030a-exec) (SC-004, SC-005)
 - **Note**: T030 depends on T030a-exec completion.
- [X] T029 [US3] Create `docs/README.md` documenting how to rerun analysis on GitHub Actions free-tier (≤6h, ≤7GB RAM, NO GPU) (FR-007) - **Depends on T030**.
- [X] T031 [US3] Implement `code/utils/package_reproducibility.py` to generate the final reproducibility package bundle `data/reproducibility_package_v1.0.tar.gz` containing scripts, `data/analysis_results/results.csv`, `data/interaction_logs/anonymized_logs.csv`, `docs/README.md` for OSF publication (FR-007). **Exclusion**: Explicitly exclude `data/consent/` from the bundle to satisfy Constitution Principle VI. **Depends on T031b**.
- [X] T031-exec [US3] Execute `code/utils/package_reproducibility.py` to generate the bundle. **Depends on T031**.
- [X] T032 [US3] Update `state/projects/PROJ-140.../artifact_hashes.yaml` with final hashes of all artifacts (V)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Update `docs/README.md` with installation steps and dependencies
- [ ] T034 [P] Update `docs/README.md` with analysis execution steps and expected outputs
- [X] T035 [P] Add API documentation to `docs/api.md` (if applicable) or remove if not needed.
- [X] T036 Code cleanup: Refactor `code/utils/logging_utils.py` to remove unused imports
- [X] T037 Code cleanup: Refactor `code/utils/models.py` to simplify data structures
- [X] T038 Performance optimization: Reduce memory usage to <6GB in `code/analysis/run_statistics.py`
- [X] T039 Performance optimization: Reduce runtime to <5h in `code/analysis/run_statistics.py`
- [X] T040 [P] Add unit tests for edge cases in `code/tests/test_statistics.py`
- [X] T041 [P] Add unit tests for data integrity in `code/tests/test_data_integrity.py`
- [ ] T042 Security hardening (ensure no sensitive data leaks in logs)
- [ ] T043 Run `docs/quickstart.md` validation
- [X] T046 [US1] Implement strict "Fail Loud" data loader in `code/download/download_defects4j.py`. **Rationale**: Per Constitution Principle "Loader must FAIL LOUDLY", remove any `try/except` blocks that might fallback to synthetic data. The script must raise an explicit error if the HuggingFace `defects4j` dataset or the specified mirror URL is unreachable, ensuring no fake data enters the pipeline. **Depends on T013**.
- [X] T047 [US1] Implement streaming dataset processing in `code/download/download_defects4j.py` using `datasets.load_dataset(..., streaming=True)`. **Rationale**: Per Constitution Principle "Large real datasets: STREAM the real data", ensure the full Defects4J dataset is processed in chunks to fit within the ~GB RAM constraint, rather than loading it entirely into memory. **Depends on T046**.
- [X] T048 [US2] Implement explicit outlier exclusion logic in `code/analysis/run_statistics.py` to filter participants with ≥2 tasks >30 minutes before running McNemar's or LME tests. **Rationale**: Per Spec Edge Case "What happens when participants complete tasks outside the expected time window", this ensures the sensitivity analysis (T044) correctly verifies robustness by excluding these flagged participants. **Depends on T045**.
- [X] T049 [US2] Update `code/analysis/run_statistics.py` to output a detailed `data/analysis_results/sensitivity_analysis_report.md` summarizing how p-values shift across a range of standard significance thresholds. **Rationale**: Per Spec Assumption "Sensitivity analysis sweeps the statistical significance threshold", this provides a human-readable summary of the robustness checks required by SC-003. **Depends on T044**.
- [X] T050 [US3] Update `docs/README.md` to explicitly document the "Fail Loud" behavior and the streaming processing strategy for Defects4J. **Rationale**: Per Constitution Principle I (Reproducibility), ensure third-party runners understand that the pipeline will fail on missing data rather than substituting synthetic values, and how to handle large datasets. **Depends on T029, T046, T047**.

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
 - T012a (Startup Gate) depends on T012 (Calibrator) and T012b (CLI Entry).
- **Once Foundational phase completes:**
 - User Story 1 (Data Collection) can start immediately.
 - User Story 2 (Analysis) **MUST WAIT** for US1 to finish data generation.
 - User Story 3 (Reproducibility) can start once US2 is complete.
- All tests for a user story marked [P] can run in parallel **EXCEPT**:
 - T010 must be written before T012.
 - T011 must be written before T013.
- Models within a story marked [P] can run in parallel
- Different user stories **CANNOT** be worked on in parallel if they have producer-consumer dependencies (e.g., US2 depends on US1).
- T030 (CI Workflow) depends on T030a-exec (Baseline Generation) completion.

### Specific Task Dependencies

- T013 depends on T011.
- T012a depends on T012 (Calibrator implementation) and T012b (CLI entry point).
- T024 depends on T025 (Sensitivity Analysis Config), T044, and T045.
- T030 depends on T030a-exec (Baseline Generation).
- T044 depends on T025 (Sensitivity Config).
- T045 depends on T044.
- T046 depends on T013.
- T047 depends on T046.
- T048 depends on T045.
- T049 depends on T044.
- T050 depends on T029, T046, T047.
- **T011 must be written and executed before T013** to satisfy the "Tests First" principle.
- **T010 must be written and executed before T012** to satisfy the "Tests First" principle.
- T031 depends on T031b (PII Verification).
- T029 depends on T030 (CI Workflow) being defined to accurately document the execution steps.
- T030 depends on T030a-exec (Baseline Generation) completion.
- T044 and T045 are mandatory to satisfy the "sensitivity analysis" and "outlier handling" assumptions in the spec. They must be implemented before the final reproducibility check.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for latency calibrator in code/tests/test_latency_calibrator.py"
Task: "Unit test for Defects4J download integrity in code/tests/test_defects4j_download.py"

# Launch all models for User Story 1 together:
Task: "Implement code/simulation/latency_calibrator.py"
Task: "Implement code/download/download_defects4j.py"
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
- **CRITICAL**: All LLM-related tasks in CI must use the **pre-computed** static artifacts (T014 Offline). The execution engine will NOT run GPU code in CI.
- **CRITICAL**: T024 (Analysis) MUST be executed AFTER T013-T020 (Data Generation) are complete to ensure the input CSV exists.
- **CRITICAL**: T029 (README) depends on T030 (CI Workflow) being defined to accurately document the execution steps.
- **CRITICAL**: T025 (Sensitivity Config) MUST be completed before T044 (Sensitivity Analysis) to ensure config exists.
- **CRITICAL**: T044 and T045 are mandatory to satisfy the "sensitivity analysis" and "outlier handling" assumptions in the spec. They must be implemented before the final reproducibility check.
- **CRITICAL**: T010 and T011 must be written BEFORE T012 and T013 respectively to satisfy the "Tests First" principle. T013 explicitly depends on T011 completion. T012a explicitly integrates the calibrator into the startup flow.
- **CRITICAL**: T012a is now marked as [X] (implemented) in Phase 3, as it depends on T012b (CLI entry point) which has been moved to Phase 2 (Foundational). This resolves the missing artifact dependency and ensures the latency test is integrated at startup.
- **CRITICAL**: T031b is added to verify PII removal before packaging, satisfying Constitution Principle VI.
- **CRITICAL**: T031c is added to verify `data/consent/` is not in repo history, satisfying Constitution Principle VI.

## Revision Tasks: Addressing Review Concerns

The following tasks are added to address specific reviewer concerns regarding data integrity, execution flow, and statistical rigor.

- [X] T046 [US1] Implement strict "Fail Loud" data loader in `code/download/download_defects4j.py`. **Rationale**: Per Constitution Principle "Loader must FAIL LOUDLY", remove any `try/except` blocks that might fallback to synthetic data. The script must raise an explicit error if the HuggingFace `defects4j` dataset or the specified mirror URL is unreachable, ensuring no fake data enters the pipeline. **Depends on T013**.
- [X] T047 [US1] Implement streaming dataset processing in `code/download/download_defects4j.py` using `datasets.load_dataset(..., streaming=True)`. **Rationale**: Per Constitution Principle "Large real datasets: STREAM the real data", ensure the full Defects4J dataset is processed in chunks to fit within the ~7GB RAM constraint, rather than loading it entirely into memory. **Depends on T046**.
- [X] T048 [US2] Implement explicit outlier exclusion logic in `code/analysis/run_statistics.py` to filter participants with ≥2 tasks >30 minutes before running McNemar's or LME tests. **Rationale**: Per Spec Edge Case "What happens when participants complete tasks outside the expected time window", this ensures the sensitivity analysis (T044) correctly verifies robustness by excluding these flagged participants. **Depends on T045**.
- [X] T049 [US2] Update `code/analysis/run_statistics.py` to output a detailed `data/analysis_results/sensitivity_analysis_report.md` summarizing how p-values shift across standard significance thresholds. **Rationale**: Per Spec Assumption "Sensitivity analysis sweeps the statistical significance threshold", this provides a human-readable summary of the robustness checks required by SC-003. **Depends on T044**.
- [X] T050 [US3] Update `docs/README.md` to explicitly document the "Fail Loud" behavior and the streaming processing strategy for Defects4J. **Rationale**: Per Constitution Principle I (Reproducibility), ensure third-party runners understand that the pipeline will fail on missing data rather than substituting synthetic values, and how to handle large datasets. **Depends on T029, T046, T047**.