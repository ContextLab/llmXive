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
 IMPORTANT: The tasks below have been revised to address all panel concerns.

 Key Changes:
 1. Split T014 into T014 (CI Simulation of FR-002) and T014-real (Offline GPU Runner) to resolve FR-002 contradiction.
 2. Consolidated T019, T019-exec, T031c into T019-consent to fix circular dependencies and ensure implementation.
 3. Replaced T030/T030a-exec with T030-workflow to create the missing CI YAML artifact.
 4. Replaced vague T042 with T042-logging (PII scrubber implementation).
 5. Fixed dependency graph: T045 -> T048 -> T024 -> T044/T049.
 6. Removed erroneous T045 -> T025 dependency.
 7. Updated T024, T031, T030-workflow with explicit schemas and file lists.
 ============================================================================
-->

## Phase 0: Offline Generation (Pre-requisite)

**Purpose**: Generate LLM summaries offline (requires GPU) to be loaded by CI. This phase is NOT part of the CI runner; it is a one-time pre-processing step.

- [X] T014 [P] [US1] **Offline (Simulation)**: Implement `code/generation/generate_summaries_offline.py` to **simulate** LLM summary generation for CI testing.
 - **Behavior**: When run in CI (CPU), it must **mock** the HuggingFace generation call to raise a `TimeoutError` or return `None` to trigger the **fallback logic** in T015b, verifying FR-002's resilience.
 - **Output**: `data/summaries/llm_summaries.csv` (empty or partial) and `data/summaries/rule_summaries.csv`.
 - **Note**: This task tests the *fallback path* of FR-002. The *real generation* is handled by T014-real.
 - **Depends on**: T013.

- [ ] T014-real [P] [US1] **Offline (Real)**: Implement `code/generation/run_gpu_summaries.py` to perform **actual** LLM summary generation via HuggingFace `codellama/CodeLlama-7b-hf` with 8-bit quantization (`device="cuda"`, `load_in_8bit`).
 - **Behavior**: This script is **NOT** run in CI. It is executed manually on a GPU machine (e.g., Kaggle) to generate the full `data/summaries/llm_summaries.csv` for the final reproducibility package.
 - **Output**: `data/summaries/llm_summaries.csv` (full dataset).
 - **Fallback**: If LLM fails (timeout >30s, empty output), use rule-based `srcML` extractor.
 - **Note**: This task satisfies the "Real Generation" requirement of FR-002 for the final study.
 - **Depends on**: T013.

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

- [X] T012 [US1] Implement `code/simulation/latency_calibrator.py` to verify timestamp precision ≤100ms (FR-003). **Output**: A JSON report of latency measurements. **Must return a strict pass/fail status** suitable for the startup gate.
- [X] T012a [US1] **Startup Gate**: Integrate `code/simulation/latency_calibrator.py` into `code/main.py` startup flow. **Implementation**: Modify `code/main.py` to import `LatencyCalibrator` and call `.run()` before any data loading. **Must raise `SystemExit` with non-zero exit code if latency >100ms**, preventing any data download or simulation. **Depends on T012 and T012b**.
- [X] T013 [US1] Implement `code/download/download_defects4j.py` to fetch DefectsJ v2.0 and extract a stratified sample of buggy methods (FR-001).
 - **Output**: `data/raw/defects4j/ground_truth.csv` containing `task_id`, `method_id`, `ground_truth_line`, `project_name`.
 - **Verification**: Include a schema validation step to ensure all required columns exist.
 - **Streaming**: Use `datasets.load_dataset(..., streaming=True)` to handle large datasets within RAM constraints.
 - **Fail Loud**: Raise explicit error if download fails; no synthetic fallback.
 - **Depends on T011**.
- [X] T013b [US1] **Missing Ground Truth**: Implement logic in `code/download/download_defects4j.py` and `code/analysis/run_statistics.py` to detect tasks with missing `ground_truth_line`. Flag these tasks in a `data/interaction_logs/missing_ground_truth.json` and exclude them from accuracy calculations. **Depends on T013**.
- [X] T020 [US1] Implement Latin-square design assignment logic in `code/simulation/assignment_generator.py` to generate balanced task conditions for a cohort of participants (US-1, Assumptions).
- [X] T015 [US1] Implement `code/simulation/participant_sim.py` to simulate participant interaction logs (Latin-square design) and record CSV logs (participant_id, task_id, condition, timestamp_ms, selected_line, ground_truth_line) to `data/interaction_logs/raw_logs.csv` (FR-003).
 - **Parameters**: Sample `time-to-decision` from a Normal distribution with injected effect size for LLM condition.
 - **Scope**: Explicitly acknowledge this is a 'simulation-only' scope reduction required by the Plan's CI constraints. **This task generates synthetic data, not real participant logs.**
 - **Depends on T013 and T020**.
- [X] T015b [US1] **Runtime Fallback**: Implement logic in `code/simulation/participant_sim.py` to handle missing LLM summaries (simulating timeout/failure). If an LLM summary is missing for a task (e.g., file not found or `None`), automatically substitute the rule-based summary for that task. **Satisfies FR-002 runtime fallback requirement**. **Depends on T015**.
- [X] T016 [US1] Implement data anonymization script `code/utils/anonymize_logs.py` to generate `data/interaction_logs/anonymized_logs.csv` (VI) - creates new file, does not overwrite raw logs. **Depends on T015**.
- [X] T017 [US1] Implement dropout handling logic in `code/simulation/participant_sim.py` to flag partial data (Edge Case).
- [X] T017b [US2] **Dropout Exclusion**: Implement logic in `code/analysis/run_statistics.py` to exclude participants with partial data (flagged by T017) from paired analyses requiring complete data. **Depends on T017**.
- [X] T019-consent [US1] **Consent & Security**: Implement `code/utils/secure_storage.py` to:
 1. Create `data/consent/` directory.
 2. Add `data/consent/` to `.gitignore`.
 3. Set permissions to `chmod 600` on `data/consent/`.
 4. **Verify** that `data/consent/` is not present in the repository history (via `git log` check).
 **Output**: Ensures Constitution Principle VI is met. **Depends on T019-impl (merged)**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2)

**Goal**: Run McNemar's tests for accuracy and LME models for speed, computing effect sizes and confidence intervals.

**Independent Test**: Can be fully tested by feeding a synthetic CSV dataset and verifying the analysis outputs p-values, effect sizes (Odds Ratio, Cohen's d), and 95% confidence intervals for all four comparisons.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for McNemar's test implementation in `code/tests/test_statistics.py`
- [X] T022 [P] [US2] Unit test for LME model and bootstrapping in `code/tests/test_bootstrap_utils.py`

### Implementation for User Story 2

- [X] T025 [US2] Define sensitivity analysis range in `code/analysis/config.py` to specify the "standard cutoffs" for the sweep. **Mandatory default values**: `[0.01, 0.05, 0.10]` (overrideable by research phase). **Note**: This task must be completed before T044.
- [X] T045 [US2] **Mandatory**: Implement outlier detection logic in `code/analysis/run_statistics.py` to flag tasks with duration >30 minutes, update `data/analysis_results/outlier_flags.json`. **Depends on T024 (data flow correction)**.
- [X] T048 [US2] **Mandatory**: Implement explicit outlier exclusion logic in `code/analysis/run_statistics.py` to filter participants with ≥2 tasks >30 minutes before running McNemar's or LME tests. **Depends on T045**.
- [X] T044 [US2] **Mandatory**: Implement sensitivity analysis sweep loop in `code/analysis/run_statistics.py` to iterate over the thresholds defined in T025 (`[0.01, 0.05, 0.10]`) and record how p-values shift. **Output**: `data/analysis_results/sensitivity_analysis.csv`. **Depends on T024**.
- [X] T049 [US2] **Mandatory**: Update `code/analysis/run_statistics.py` to output a detailed `data/analysis_results/sensitivity_analysis_report.md` summarizing how p-values shift across a range of standard significance thresholds. **Depends on T044**.
- [X] T023 [US2] Implement `code/analysis/bootstrap_utils.py` for bootstrapping (A substantial number of resamples, fixed seed) to compute confidence intervals (FR-005)
- [X] T023a [US2] Implement `code/analysis/correction_utils.py` for multiple-comparison correction logic (Holm-Bonferroni) (FR-006)
- [X] T024 [US2] Implement `code/analysis/run_statistics.py` to:
 - Load `data/interaction_logs/anonymized_logs.csv` and summary data.
 - **Load** `data/interaction_logs/missing_ground_truth.json` (from T013b) to exclude invalid tasks.
 - **Load** `data/analysis_results/outlier_flags.json` (from T045) to apply exclusion via T048.
 - Compute **Top-K accuracy** (e.g., Top-5) and speed (time-to-decision) metrics (Complexity Tracking).
 - Run McNemar's tests for accuracy (baseline vs LLM, baseline vs Rule) (FR-004).
 - Run Linear Mixed-Effects (LME) models with random intercepts for participants using `statsmodels.formula.api.mixedlm` (FR-004).
 - **Import and invoke bootstrapping functions from `code/analysis/bootstrap_utils.py`** to compute Odds Ratios and Cohen's d with bootstrapped CIs (FR-005).
 - **Import and invoke correction function from `code/analysis/correction_utils.py`** to apply Holm-Bonferroni correction (α=0.05) (FR-006).
 - **Invoke T044** to generate sensitivity analysis results (post-processing).
 - Output `data/analysis_results/results.csv` with all metrics.
 - **Explicitly measure and report** whether p-values meet the `<0.05` threshold as a pass/fail criterion for SC-003.
 - **Depends on T023, T023a, T025, T045, T048, T013b, T017b**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproducibility Package Generation (Priority: P3)

**Goal**: Generate a reproducible research package (scripts + anonymized logs) that runs on GitHub Actions free-tier.

**Independent Test**: Can be fully tested by cloning the OSF repository, running the analysis script in a GitHub Actions free-tier runner, and verifying the output matches the original results within a reasonable numerical tolerance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Integration test for CI resource constraints in `.github/workflows/test_reproducibility.yml`. **Depends on T030-workflow**.
- [X] T028 [P] [US3] Test for numerical tolerance between original and rerun results in `code/tests/test_reproducibility.py`

### Implementation for User Story 3

- [ ] T030-workflow [US3] **CI Workflow**: Implement `.github/workflows/test_reproducibility.yml` to:
 1. Install dependencies from `requirements.txt`.
 2. Run `code/main.py` (which runs T012a, T013, T015, T024).
 3. **Assert** runtime ≤6h and memory ≤7GB using `code/utils/resource_monitor.py`.
 4. **Verify** numerical tolerance: Compare `data/analysis_results/results.csv` against `data/analysis_results/baseline_results.json` (generated by T030a-exec or a static baseline). **Tolerance**: `1e-4` for p-values and effect sizes.
 5. **Fail** if any constraint is violated.
 **Depends on T009, T024**.

- [ ] T031b [US3] **Verification**: Implement `code/utils/verify_pii_removal.py` to scan `data/interaction_logs/anonymized_logs.csv` for PII and verify `data/consent/` is excluded from VCS history. **Fail** if PII is found or `data/consent/` is present. **Depends on T016, T019-consent**.

- [ ] T031 [US3] **Reproducibility Package**: Implement `code/utils/package_reproducibility.py` to generate `data/reproducibility_package_v1.0.tar.gz`.
 - **Include**: `code/` (all scripts), `data/analysis_results/results.csv`, `data/interaction_logs/anonymized_logs.csv`, `docs/README.md`, `requirements.txt`, `state/projects/PROJ-140.../artifact_hashes.yaml`.
 - **Exclude**: `data/consent/`, `data/raw/defects4j/` (use `fetch_defects4j.py` instead), `data/interaction_logs/raw_logs.csv`.
 - **Depends on T031b**.

- [ ] T031-exec [US3] Execute `code/utils/package_reproducibility.py` to generate the bundle. **Depends on T031**.

- [ ] T032 [US3] Update `state/projects/PROJ-140.../artifact_hashes.yaml` with final hashes of all artifacts (V)

- [X] T029 [US3] Create `docs/README.md` documenting how to rerun analysis on GitHub Actions free-tier (≤6h, ≤7GB RAM, NO GPU) (FR-007) - **Depends on T030-workflow**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Update `docs/README.md` with installation steps and dependencies
- [X] T034 [P] Update `docs/README.md` with analysis execution steps and expected outputs
- [X] T035 [P] Add API documentation to `docs/api.md` (if applicable) or remove if not needed.
- [X] T036 Code cleanup: Refactor `code/utils/logging_utils.py` to remove unused imports
- [X] T037 Code cleanup: Refactor `code/utils/models.py` to simplify data structures
- [X] T038 Performance optimization: Reduce memory usage to <6GB in `code/analysis/run_statistics.py`
- [X] T039 Performance optimization: Reduce runtime to <5h in `code/analysis/run_statistics.py`
- [X] T040 [P] Add unit tests for edge cases in `code/tests/test_statistics.py`
- [X] T041 [P] Add unit tests for data integrity in `code/tests/test_data_integrity.py`
- [ ] T042-logging [P] **Security Hardening**: Implement `code/utils/logging_utils.py` to include a **regex-based PII scrubber** that masks patterns like `participant_id`, email, and IP addresses before logging. **Add** `code/tests/test_logging_pii.py` to verify scrubbing works. **Depends on T008**.

- [X] T043 Run `docs/quickstart.md` validation
- [X] T046 [US1] Implement strict "Fail Loud" data loader in `code/download/download_defects4j.py`. **Rationale**: Per Constitution Principle "Loader must FAIL LOUDLY", remove any `try/except` blocks that might fallback to synthetic data for *dataset downloads*. The script must raise an explicit error if the HuggingFace `defects4j` dataset or the specified mirror URL is unreachable, ensuring no fake data enters the pipeline. **Note**: This applies ONLY to dataset downloads; LLM summary fallback is handled by T015b. **Depends on T013**.
- [X] T047 [US1] Implement streaming dataset processing in `code/download/download_defects4j.py` using `datasets.load_dataset(..., streaming=True)`. **Rationale**: Per Constitution Principle "Large real datasets: STREAM the real data", ensure the full DefectsJ dataset is processed in chunks to fit within available memory constraints, rather than loading it entirely into memory. **Depends on T046**.
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
- T030-workflow (CI Workflow) depends on T024 (Analysis) completion.
- T044 and T045 are mandatory to satisfy the "sensitivity analysis" and "outlier handling" assumptions in the spec. They must be implemented before the final reproducibility check.
- T015 depends on T020.
- T015b depends on T015.
- T016 depends on T015.
- T017b depends on T017.
- T031 depends on T031b (PII Verification).
- T029 depends on T030-workflow (CI Workflow) being defined to accurately document the execution steps.
- T044 depends on T024.
- T045 depends on T024 (data flow correction).
- T048 depends on T045.
- T049 depends on T044.
- T050 depends on T029, T046, T047.
- **T011 must be written and executed before T013** to satisfy the "Tests First" principle.
- **T010 must be written and executed before T012** to satisfy the "Tests First" principle.
- T031c is merged into T019-consent.
- T019-consent must be completed before T031b.
- T031b must be completed before T031.
- T042-logging is a standalone task for security hardening.

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
- **CRITICAL**: All LLM-related tasks in CI must use the **pre-computed** static artifacts (T014-real) or the **simulation** (T014) that triggers fallback. The execution engine will NOT run GPU code in CI.
- **CRITICAL**: T024 (Analysis) MUST be executed AFTER T013-T020 (Data Generation) are complete to ensure the input CSV exists.
- **CRITICAL**: T029 (README) depends on T030-workflow (CI Workflow) being defined to accurately document the execution steps.
- **CRITICAL**: T025 (Sensitivity Config) MUST be completed before T044 (Sensitivity Analysis) to ensure config exists.
- **CRITICAL**: T044 and T045 are mandatory to satisfy the "sensitivity analysis" and "outlier handling" assumptions in the spec. They must be implemented before the final reproducibility check.
- **CRITICAL**: T010 and T011 must be written BEFORE T012 and T013 respectively to satisfy the "Tests First" principle. T013 explicitly depends on T011 completion. T012a explicitly integrates the calibrator into the startup flow.
- **CRITICAL**: T019-consent is added to consolidate consent directory creation and verification.
- **CRITICAL**: T030-workflow is added to create the missing CI artifact.
- **CRITICAL**: T042-logging is added to replace vague T042 with concrete PII scrubbing.
- **CRITICAL**: T014 is split into T014 (Simulation) and T014-real (Real Generation) to satisfy FR-002.
- **CRITICAL**: T045, T048, T044, T049 dependencies are corrected to reflect data flow.
- **CRITICAL**: T051-T054 have been removed as they are scope creep not authorized by the spec. **Note**: These tasks are permanently out of scope.
- **CRITICAL**: The "Revision Tasks" section has been removed to eliminate duplication with tasks already defined in Phases 3, 4, and 5.
- **CRITICAL**: Tasks T016, T019, T027, T030, T031 were incorrectly marked [X] in previous revisions. They are now correctly marked [ ] to reflect that the artifacts (anonymized_logs.csv, consent directory, CI workflow, reproducibility package) are missing and must be implemented.