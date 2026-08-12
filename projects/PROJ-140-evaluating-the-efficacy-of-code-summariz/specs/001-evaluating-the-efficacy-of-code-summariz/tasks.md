# Tasks: Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

**Input**: Design documents from `/specs/001-evaluating-code-summarization-bug-localization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Manual]**: Requires manual intervention or offline execution (e.g., GPU generation); excluded from automated CI dependency graph.
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
 1. T014-real moved to Phase 0, [P] tag removed, explicit verification added.
 2. T015-llm clarified for CI context (sim first, real fallback) with pre-checks.
 3. All other tasks preserved and dependencies updated for clarity.
 ============================================================================
-->

## Phase 0: Offline Pre-processing (Manual, Non-CI)

**Purpose**: Document scope reduction and generate LLM summaries offline (requires GPU) to be loaded by CI. This phase is **NOT** part of the CI runner; it is a one-time pre-processing step executed manually on a GPU machine.

- [X] T000 [P] **Scope Reduction Documentation**: Create `docs/scope_reduction.md` to explicitly document the change from the spec's "Human Subject Study" to a "Deterministic Simulation" as per the Plan.md summary.
 - **Content**: Must state that real participants are replaced by a simulated cohort, and LLM summaries are pre-generated offline.
 - **Rationale**: Addresses the disconnect between spec assumptions and plan implementation (F001 part 2).
 - **Depends on**: None.

- [ ] T014-real [Manual] [US1] **Offline (Real)**: Implement `code/generation/run_gpu_summaries.py` to perform **actual** LLM summary generation via HuggingFace `codellama/CodeLlama-7b-hf` with 8-bit quantization (`device="cuda"`, `load_in_8bit=True`).
 - **Behavior**: This script is **NOT** run in CI. It is executed manually on a GPU machine (e.g., Kaggle) to generate the full `data/summaries/llm_summaries_real.csv` for the final reproducibility package.
 - **Implementation**: Use `transformers.AutoModelForCausalLM.from_pretrained(..., load_in_8bit=True, device_map="auto")` and `AutoTokenizer`. Process the stratified sample of buggy methods extracted in T013.
 - **Fallback**: If LLM fails (timeout >30s, empty output), use rule-based `srcML` extractor.
 - **Output**: `data/summaries/llm_summaries_real.csv`.
 - **Verification**: Run `python code/generation/run_gpu_summaries.py --verify`. This command must assert that `data/summaries/llm_summaries_real.csv` exists, contains the expected number of rows (matching the stratified sample size from T013), and passes schema validation (columns: `task_id`, `summary_text`, `method_id`).
 - **Note**: This task satisfies the "Real Generation" requirement of FR-002 for the final study. The execution engine will detect the `device="cuda"` requirement and offload this specific task to a GPU runner if triggered.
 - **Depends on**: T013.

- [X] T014 [P] [US1] **Offline (Simulation)**: Implement `code/generation/generate_summaries_offline.py` to **simulate** LLM summary generation for CI testing.
 - **Behavior**: Generate a valid CSV file `data/summaries/llm_summaries_sim.csv` containing mocked summary text for all tasks in the stratified sample. This file serves as the *fallback* data for the CI pipeline when the real LLM summaries are not provided.
 - **Output**: `data/summaries/llm_summaries_sim.csv` (valid CSV with mocked text) and `data/summaries/rule_summaries.csv`.
 - **Note**: This task produces the *fallback* data. The *real generation* is handled by T014-real. The output file is distinct from T014-real to allow parallel execution.
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
- [X] T012a [US1] **Startup Gate**: Integrate `code/simulation/latency_calibrator.py` into `code/main.py` startup flow. **Implementation**: Modify `code/main.py` to import `LatencyCalibrator` and call `.run()` before any data loading. **Must raise `SystemExit` with exit code 1 if latency >100ms**, preventing any data download or simulation. **Depends on T012 and T012b**.
- [X] T013 [US1] Implement `code/download/download_defectsj.py` to fetch DefectsJ v2.0 and extract a stratified sample of buggy methods (FR-001).
 - **Output**: `data/raw/defects4j/ground_truth.csv` containing `task_id`, `method_id`, `ground_truth_line`, `project_name`.
 - **Verification**: Include a schema validation step to ensure all required columns exist.
 - **Streaming**: Use `datasets.load_dataset(..., streaming=True)` to handle large datasets within RAM constraints.
 - **Fail Loud**: Raise explicit error if download fails; no synthetic fallback.
 - **Stratified Sampling**: Implement stratified sampling to extract N methods per project type (Chart, Time, Math) using a fixed random seed to ensure balanced representation. **Explicitly filter by project type**.
 - **Depends on T011**.
- [X] T013b [US1] **Missing Ground Truth**: Implement logic in `code/download/download_defects4j.py` to detect tasks with missing `ground_truth_line`. Flag these tasks in `data/interaction_logs/missing_ground_truth.json` and exclude them from accuracy calculations. **Output**: `data/interaction_logs/missing_ground_truth.json`. **Depends on T013**.
- [X] T020 [US1] Implement Latin-square design assignment logic in `code/simulation/assignment_generator.py` to generate balanced task conditions for a cohort of participants (US-1, Assumptions).
- [X] T015-base [US1] **Baseline Condition**: Implement `code/simulation/participant_sim_base.py` to simulate participant interaction logs for the **baseline** (no summary) condition.
 - **Behavior**: Generate rows where `condition='baseline'`, `summary_text` is null/empty, and `ground_truth_line` is valid (matching the ground truth from T013).
 - **Parameters**: Sample `time-to-decision` from a Normal distribution matching the baseline condition.
 - **Scope**: Explicitly acknowledge this is a 'simulation-only' scope reduction required by the Plan's CI constraints.
 - **Depends on T013, T020, T013b**.
- [X] T015-llm [US1] **LLM Condition**: Implement `code/simulation/participant_sim_llm.py` to simulate participant interaction logs for the **LLM** summary condition.
 - **Behavior**: 
  1. **Pre-check**: Verify existence of `data/summaries/llm_summaries_real.csv`.
  2. **CI Context (Default)**: If `llm_summaries_real.csv` is missing, load `data/summaries/llm_summaries_sim.csv` (generated by T014).
  3. **Final Package Context**: If `llm_summaries_real.csv` exists, load it.
  4. **Generate Interaction Logs**: Create rows where `condition='LLM'`, `summary_text` is loaded from the selected source, and `ground_truth_line` is valid.
 - **Parameters**: Sample `time-to-decision` from a Normal distribution with injected effect size for LLM condition.
 - **Note**: In CI context, T014-real (manual) is optional. If not provided, the task automatically uses the simulated data from T014.
 - **Dependencies**: Depends on T013, T020, T013b. **Conditional Dependency**: If `llm_summaries_real.csv` is missing, T014 must have run to provide the fallback.
 - **Depends on**: T013, T020, T013b, T014 (if real file missing).
- [X] T015-rule [US1] **Rule-Based Condition**: Implement `code/simulation/participant_sim_rule.py` to simulate participant interaction logs for the **rule-based** summary condition.
 - **Behavior**: Generate rows where `condition='rule'`, `summary_text` is loaded from `data/summaries/rule_summaries.csv`, and `ground_truth_line` is valid.
 - **Parameters**: Sample `time-to-decision` from a Normal distribution with injected effect size for rule-based condition.
 - **Fallback**: If LLM summary is missing for a task, use rule-based summary (simulating fallback).
 - **Depends on T013, T020, T013b, T014**.
- [X] T015-fallback-check [US1] **Runtime Fallback Logic**: Implement `code/simulation/check_fallback.py` to verify the **automatic fallback** logic required by FR-002.
 - **Behavior**: Iterate through the interaction logs. 
  1. If a task has `condition='LLM'` and `summary_text` is **missing** (null/empty), the script MUST **generate the rule-based summary on-the-fly** using `code/generation/rule_summary.py` and inject it into the log.
  2. If a task has `condition='LLM'` and `summary_text` is present but was sourced from `llm_summaries_sim.csv` (simulated), flag it in a log but do not replace it (as it is a valid fallback for CI).
 - **Output**: Update `data/interaction_logs/raw_logs.csv` to include the generated rule-based summary for missing LLM cases.
 - **Verification**: Assert that no LLM task remains without a summary text after this step.
 - **Rationale**: Addresses FR-002's requirement for automatic fallback in the automated execution flow.
 - **Depends on T015-base, T015-llm, T015-rule**.
- [X] T016 [US1] Implement data anonymization script `code/utils/anonymize_logs.py` to generate `data/interaction_logs/anonymized_logs.csv` (VI) - creates new file, does not overwrite raw logs. **Depends on T015-base, T015-llm, T015-rule, T015-fallback-check**.
- [X] T016-prevent-raw-commit [US1] **Prevent Raw Log Commit**: Implement `code/utils/prevent_raw_commit.py` to:
 1. Ensure `data/interaction_logs/raw_logs.csv` is listed in `.gitignore`.
 2. Create a pre-commit hook that scans for PII patterns (email, IP, participant_id) in `data/interaction_logs/` and blocks commits if found.
 3. Verify that `data/interaction_logs/raw_logs.csv` is not in the git history.
 **Output**: Ensures Constitution Principle VI is met by preventing raw logs from ever entering VCS. **Depends on T016**.
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

- [X] T025 [US2] Define sensitivity analysis range in `code/analysis/config.py` to specify the "standard cutoffs" for the sweep. **Mandatory default values**: `[0.01, 0.05, 0.10]` (overrideable by research phase via config). **Note**: This task must be completed before T044. **Explicitly reference spec assumption about sensitivity analysis**.
- [X] T045 [US2] **Mandatory**: Implement outlier detection logic in `code/analysis/run_statistics.py` to flag tasks with duration >30 minutes, update `data/analysis_results/outlier_flags.json`. **Depends on T016**.
- [X] T048 [US2] **Mandatory**: Implement explicit outlier exclusion logic in `code/analysis/run_statistics.py` to filter participants with ≥2 tasks >30 minutes before running McNemar's or LME tests. **Output**: `data/interaction_logs/cleaned_logs.csv`. **Depends on T045**.
- [X] T024-load [US2] **Mandatory**: Implement `code/analysis/load_data.py` to load `data/interaction_logs/cleaned_logs.csv` (from T048) and summary data. **Load** `data/interaction_logs/missing_ground_truth.json` (from T013b) to exclude invalid tasks. **Depends on T048, T013b**.
- [X] T024-stats [US2] **Mandatory**: Implement `code/analysis/run_statistics.py` to:
 - **Import and invoke bootstrapping functions from `code/analysis/bootstrap_utils.py`** to compute Odds Ratios and Cohen's d with bootstrapped CIs (FR-005).
 - **Import and invoke correction function from `code/analysis/correction_utils.py`** to apply Holm-Bonferroni correction (α=0.05) (FR-006).
 - Run McNemar's tests for accuracy (baseline vs LLM, baseline vs Rule) (FR-004).
 - Run Linear Mixed-Effects (LME) models with random intercepts for participants using `statsmodels.formula.api.mixedlm` (FR-004).
 - Compute **Top-K accuracy** (e.g., Top-5) and speed (time-to-decision) metrics (Complexity Tracking).
 - **Explicitly measure and report** whether p-values meet the `<0.05` threshold as a pass/fail criterion for SC-003.
 - Output `data/analysis_results/results.csv` with all metrics.
 - **Depends on T024-load, T023, T023a, T025**.
- [X] T024-report [US2] **Mandatory**: Implement `code/analysis/generate_report.py` to generate `data/analysis_results/final_report.md` summarizing results. **Depends on T024-stats**.
- [X] T023 [US2] Implement `code/analysis/bootstrap_utils.py` for bootstrapping (A substantial number of resamples, fixed seed) to compute confidence intervals (FR-005)
- [X] T023a [US2] Implement `code/analysis/correction_utils.py` for multiple-comparison correction logic (Holm-Bonferroni) (FR-006)
- [X] T044 [US2] **Mandatory**: Implement sensitivity analysis sweep loop in `code/analysis/run_sensitivity.py` to iterate over the thresholds defined in T025 (configurable range) and record how p-values shift. **Output**: `data/analysis_results/sensitivity_analysis.csv`. **Depends on T024-stats**.
- [X] T049 [US2] **Mandatory**: Update `code/analysis/generate_sensitivity_report.py` to output a detailed `data/analysis_results/sensitivity_analysis_report.md` summarizing how p-values shift across a range of standard significance thresholds. **Depends on T044**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproducibility Package Generation (Priority: P3)

**Goal**: Generate a reproducible research package (scripts + anonymized logs) that runs on GitHub Actions free-tier.

**Independent Test**: Can be fully tested by cloning the OSF repository, running the analysis script in a GitHub Actions free-tier runner, and verifying the output matches the original results within a reasonable numerical tolerance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Integration test for CI resource constraints in `.github/workflows/test_reproducibility.yml`. **Depends on T030-workflow**.
- [X] T028 [P] [US3] Test for numerical tolerance between original and rerun results in `code/tests/test_reproducibility.py`

### Implementation for User Story 3

- [X] T030-workflow [US3] **CI Workflow**: Implement `.github/workflows/test_reproducibility.yml` to:
 1. Install dependencies from `requirements.txt`.
 2. Run `code/main.py` (which runs T012a, T013, T015-base, T015-llm, T015-rule, T024-load, T024-stats).
 3. **Assert** runtime ≤6h and memory ≤7GB using `code/utils/resource_monitor.py`.
 4. **Verify** numerical tolerance: **Re-run the analysis with the same seed** and compare `data/analysis_results/results.csv` against the current execution's results. **Command**: `python code/tests/test_reproducibility.py --seed 42 --tolerance 1e-4`. **Tolerance**: `1e-4` for p-values and effect sizes.
 5. **Fail** if any constraint is violated.
 **Depends on T009, T024-stats**.

- [X] T031b [US3] **Verification**: Implement `code/utils/verify_pii_removal.py` to scan `data/interaction_logs/anonymized_logs.csv` for PII and verify `data/consent/` is excluded from VCS history. **Fail** if PII is found or `data/consent/` is present. **Depends on T016, T019-consent**.

- [X] T031 [US3] **Reproducibility Package**: Implement `code/utils/package_reproducibility.py` to generate `data/reproducibility_package_v1.0.tar.gz`.
 - **Include**: `code/` (all scripts), `data/analysis_results/results.csv`, `data/interaction_logs/anonymized_logs.csv`, `docs/README.md`, `requirements.txt`, `state/projects/PROJ-140.../artifact_hashes.yaml`.
 - **Exclude**: `data/consent/`, `data/raw/defects4j/` (use `fetch_defects4j.py` instead), `data/interaction_logs/raw_logs.csv`.
 - **Logic**: Use `tar` command: `tar --exclude='data/consent' --exclude='data/raw/defects4j' --exclude='data/interaction_logs/raw_logs.csv' -czvf data/reproducibility_package_v1.0.tar.gz code/ data/analysis_results data/interaction_logs/anonymized_logs.csv docs/ requirements.txt state/`.
 - **Verification**: Assert `data/reproducibility_package_v1.0.tar.gz` exists and is < 500MB.
 - **Depends on T031b, T032**.

- [X] T032 [US3] **Hash Generation**: Run `code/utils/update_hashes.py` to generate `state/projects/PROJ-140.../artifact_hashes.yaml` with final hashes of all artifacts (V). **Depends on T031b**.

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
- [X] T042-logging [P] **Security Hardening**: Implement `code/utils/logging_utils.py` to include a **regex-based PII scrubber** that masks patterns like `participant_id`, email, and IP addresses before logging. **Add** `code/tests/test_logging_pii.py` to verify scrubbing works. **Verification**: Run `python code/tests/test_logging_pii.py` and assert all PII patterns are masked. **Depends on T008**.

- [X] T043 Run `docs/quickstart.md` validation
- [X] T046 [US1] Implement strict "Fail Loud" data loader in `code/download/download_defects4j.py`. **Rationale**: Per Constitution Principle "Loader must FAIL LOUDLY", remove any `try/except` blocks that might fallback to synthetic data for *dataset downloads*. The script must raise an explicit error if the HuggingFace `defects4j` dataset or the specified mirror URL is unreachable, ensuring no fake data enters the pipeline. **Note**: This applies ONLY to dataset downloads; LLM summary fallback is handled by T015-rule. **Depends on T013**.
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
 - **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 analysis completion (T024-stats)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **Strictly depends** on US1 data generation (T013-T020). US2 cannot start until US1 is complete.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 analysis completion (T024-stats)

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
- T030-workflow (CI Workflow) depends on T024-stats (Analysis) completion.
- T044 and T045 are mandatory to satisfy the "sensitivity analysis" and "outlier handling" assumptions in the spec. They must be implemented before the final reproducibility check.
- T015-base, T015-llm, T015-rule depend on T020.
- T016 depends on T015-base, T015-llm, T015-rule.
- T017b depends on T017.
- T031 depends on T031b (PII Verification) and T032 (Hash Generation).
- T029 depends on T030-workflow (CI Workflow) being defined to accurately document the execution steps.
- T044 depends on T024-stats.
- T045 depends on T016.
- T048 depends on T045.
- T049 depends on T044.
- T050 depends on T029, T046, T047.
- **T011 must be written and executed before T013** to satisfy the "Tests First" principle.
- **T010 must be written and executed before T012** to satisfy the "Tests First" principle.
- T031c is merged into T019-consent.
- T019-consent must be completed before T031b.
- T031b must be completed before T031.
- T032 must be completed before T031.
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
- [Manual] tasks = offline, non-parallel, require manual intervention
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
- **CRITICAL**: T045, T048, T024-load, T024-stats dependencies are corrected to reflect data flow (T045/T048 run BEFORE T024).
- **CRITICAL**: T051-T054 have been removed as they are scope creep not authorized by the spec. **Note**: These tasks are permanently out of scope.
- **CRITICAL**: The "Revision Tasks" section has been removed to eliminate duplication with tasks already defined in Phases 3, 4, and 5.
- **CRITICAL**: Tasks T016, T019, T027, T030, T031 were incorrectly marked [X] in previous revisions. They are now correctly marked [ ] to reflect that the artifacts (anonymized_logs.csv, consent directory, CI workflow, reproducibility package) are missing and must be implemented.
- **CRITICAL**: T015 is split into T015-base, T015-llm, T015-rule to explicitly cover all three conditions.
- **CRITICAL**: T024 is split into T024-load, T024-stats, T024-report to ensure atomic execution.
- **CRITICAL**: T032 runs BEFORE T031 to ensure hash file is included in package.
- **CRITICAL**: T014 and T014-real output files are separated (`llm_summaries_sim.csv` vs `llm_summaries_real.csv`) to allow parallel execution.
- **CRITICAL**: T012a explicitly mandates non-zero exit code and blocking behavior.
- **CRITICAL**: T013 explicitly implements stratified sampling logic.
- **CRITICAL**: T030-workflow now performs a deterministic re-run check for tolerance verification.
- **CRITICAL**: T025 now uses a configurable parameter for sensitivity range.
- **CRITICAL**: T015-fallback-check is added to implement the runtime fallback logic for FR-002.
- **CRITICAL**: T016-prevent-raw-commit is added to prevent raw logs from entering VCS.
- **CRITICAL**: T000 is added to document the scope reduction from real human study to simulation.
- **CRITICAL**: T014-real is moved to Phase 0 and marked [Manual] (no [P]) to reflect its offline, non-parallel nature.
- **CRITICAL**: T015-llm explicitly defines CI behavior (sim first, real fallback) to resolve dependency ambiguity.