# Tasks: Dynamic Socio-Cognitive State Injection

**Input**: Design documents from `/specs/001-dynamic-state-injection/`
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

- [ ] T001 Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`, `contracts/` as defined in plan.md
- [X] T002 Initialize Python 3.11 project with `scikit-learn`, `pandas`, `transformers` (CPU-only), `datasets`, `pytest` in `requirements.txt`. **Explicitly exclude** `bitsandbytes`, `flash-attn`, and any GPU-accelerated libraries. Add a comment in `requirements.txt` noting this exclusion to satisfy FR-004.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` with pinned random seeds, file paths (`data/raw`, `data/processed`, `data/results`), and hyperparameters. **Explicitly define `STATISTICAL_VARIANCE_TOLERANCE = 0.01` for reproducibility checks.**
- [X] T005 [P] Implement data validation utilities in `code/data/loader.py` to enforce schema compliance for generated trajectories
- [X] T006 [P] Setup logging infrastructure in `code/config.py` to track experiment conditions (Adapter vs. Static) and skipped samples
- [X] T007 Create base entities: `ConflictTrajectory` and `SocioCognitiveState` dataclasses in `code/models/entities.py`
- [X] T008 [P] Implement retry mechanism with exponential backoff for API/local inference failures in `code/experiments/retry_utils.py`
- [X] T009 [P] Create `code/experiments/model_loader.py` with a pre-flight memory check function that estimates model size. **Logic**: If a model's estimated RAM usage > 7GB, log a warning and skip loading it. Add a unit test in `tests/unit/test_model_loader.py` that verifies this exclusion logic works for a mock large model.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Conflict Trajectories with Targeted Oversampling (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic conflict dialogue trajectories using the SoCRATES pipeline, specifically oversampling scenarios with "high emotional reactivity" and "diverse cultural identity" attributes.

**Independent Test**: Run the data generation script and verify the output JSON summary shows >40% of samples in the target categories, with memory <7GB and runtime <30m.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for trajectory schema in `tests/contract/test_trajectory_schema.py`
- [X] T011 [P] [US1] Integration test for oversampling distribution in `tests/integration/test_oversampling.py`

### Implementation for User Story 1

- [X] T049 [US1] Implement `code/analysis/power_analysis.py` to calculate the required sample size. **Requirement**: Using `statsmodels.stats.power.tt_solve_power`, compute the minimum N required to detect a medium effect size (Cohen's d = 0.5) with power=0.80 and alpha=0.05 for a paired t-test. **Gating**: If the calculated N exceeds the intended generation count, the script MUST HALT execution, set a `power_insufficient` flag in `data/results/power_analysis_report.json`, and log a critical error. **Do NOT proceed to data generation (T014) if power is insufficient.**
- [X] T014 [US1] Implement `code/data/generator.py` output writer to save trajectories to `data/processed/trajectories.json` and a summary report to `data/processed/generation_stats.json`. **Requirement**: The summary report MUST explicitly list the count and percentage of trajectories in each target category to satisfy T015 validation. **Dependency**: Must only run if T049 confirms sufficient power.
- [X] T015 [US1] Add validation in `code/data/generator.py` to verify generated data meets the 40% threshold before writing
- [X] T016 [US1] Add logging for generation parameters and final distribution counts
- [X] T048 [US1] Implement `code/analysis/data_separation_check.py` to verify that `turn_text` derivation does not contain tokens unique to the "ideal resolution" used in the evaluator. **Requirement**: Run this check on the derived training data before saving. If contamination is detected, HALT and raise an error. **Dependency**: Must run before T019 saves data.
- [X] T019 [US1] Implement `code/data/generator.py` to **derive turn-level training pairs** from generated `ConflictTrajectory` objects. **Requirement**: Implement logic to split the full trajectory history into sliding windows of N=3 turns (use `config.TURN_WINDOW_SIZE = 3` as the explicit default value) to create `turn_text` (dialogue snippet) and `label` (socio-cognitive state from trajectory metadata) pairs. Save this derived dataset to `data/processed/classifier_training_data.json`. **Independence Check**: Explicitly verify that the `label` derivation logic uses ONLY trajectory metadata tags (e.g., emotional reactivity, cultural identity) and does NOT incorporate any logic or data from the `ConsensusGapScore` evaluator (FR-005). **Data Separation**: Dependency: Requires T048 to confirm data independence before saving.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Paired Mediation Experiments (Priority: P2)

**Goal**: Run conflict trajectories through eight distinct LLMs under two conditions: (A) with dynamic socio-cognitive state adapter, (B) with static baseline prompt, ensuring CPU-only execution.

**Independent Test**: Run experiment script for one LLM and subset of trajectories, verifying "Adapter" logs contain injected state signals (e.g., "de-escalate") while "Static" logs do not.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for prompt injection in `tests/contract/test_prompt_injection.py`
- [X] T022 [P] [US2] Integration test for paired experiment execution in `tests/integration/test_experiment_runner.py`

### Implementation for User Story 2

- [X] T020 [P] [US1/US2] Implement `code/models/classifier.py` with a lightweight logistic regression classifier. **Input Schema**: Must accept `classifier_training_data.json` containing a list of dicts with keys `turn_text`, `label`, `trajectory_id`. **Training**: Train on `turn_text` features (e.g., TF-IDF) to predict `label`. Ensure no overlap with evaluation metrics (FR-002). **Dependency**: Requires T019 to have generated `classifier_training_data.json`.
- [X] T045 [US2] Implement `code/data/generator.py` to export a shared utility function `split_trajectory_into_turns` that implements the sliding window logic (N=3) used in T019. **Requirement**: This function must be the single source of truth for turn slicing. Add a unit test in `tests/unit/test_data_flow.py` that verifies this function produces identical windows to the T019 derivation logic for a fixed seed.
- [X] T024b [US2] Implement **turn-by-turn streaming slicing logic** in `code/experiments/runner.py` by importing and calling the shared `split_trajectory_into_turns` function from `code/data/generator.py`. **Dependency**: Requires T045 to be complete.
- [X] T024a [US2] Implement the main experiment runner in `code/experiments/runner.py`. **Dependency**: Requires T024b (slicing logic) to be complete. This task orchestrates the loop: load trajectory -> slice turns -> classify -> inject prompt -> run LLM.
- [X] T023 [P] [US2] Implement `code/experiments/prompts.py` with templates for Static baseline and Dynamic Adapter (injecting state instructions like "validate cultural norms", "de-escalate")
- [X] T025 [US2] Implement `code/experiments/runner.py` to run the Static condition (no injection) for the same trajectories
- [X] T026 [US2] Integrate retry logic from `code/experiments/retry_utils.py` to handle timeouts/crashes, logging skipped samples
- [X] T027 [US2] Implement CPU-only inference loop in `code/experiments/runner.py` using `transformers` with `device="cpu"`. **Verification**: Explicitly map the model to CPU. **Constraint**: If `torch.cuda.is_available()` returns True, log a warning that a GPU is detected but the run is forced to CPU for reproducibility; DO NOT fail the build. Explicitly exclude bitsandbytes/quantization libraries. Implement fallback logic to inject "neutral monitoring state" on low confidence (FR-002).
- [X] T028 [US2] Save experiment logs to `data/processed/experiment_logs.json` containing trajectory ID, condition (Adapter/Static), injected state (if any), and LLM output. **Mandatory**: For the **Adapter** condition, the log entry for each turn MUST include `confidence_score` (float) and `injected_state` (string or null). **Requirement**: For the **Static** condition entries, explicitly set `confidence_score` to `null` and `injected_state` to `null` to maintain schema consistency without generating unnecessary data artifacts.
- [X] T029 [US2] Add validation to ensure the classifier fails gracefully to a neutral "monitoring" state on low confidence (Edge Case FR-002)
- [X] T042 [US2] Implement `code/analysis/perf_monitor.py` to calculate throughput (trajectories/hour) and latency (s/trajectory) from `experiment_logs.json`. **Verification**: Add a step that logs a warning if throughput < 40 or latency > 45, but **MUST NOT fail the build**. The script must generate `data/results/perf_report.json` with these metrics to satisfy SC-003 reporting requirements.
- [X] T042b [US2] Create a CI orchestration script (e.g., `scripts/check_perf.sh`) that reads `data/results/perf_report.json`. **Logic**: If throughput < 40 or latency > 45, log a warning to the console and exit with code 0. **Do NOT fail the CI build**. This is a post-execution check only.

**Checkpoint**: At this point, User Story 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compute Consensus Gap Closure and Statistical Significance (Priority: P3)

**Goal**: Calculate "consensus gap closure" metric using the topic-localized evaluator and perform statistical comparison (paired t-test or Wilcoxon) between Adapter and Static conditions.

**Independent Test**: Provide pre-computed CSV of gap scores and verify script outputs correct t-statistic, p-value, and Cohen's d.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [P] [US3] Contract test for statistical report schema in `tests/contract/test_stats_report.py`
- [X] T032 [P] [US3] Integration test for normality and significance testing in `tests/integration/test_statistical_analysis.py`

### Implementation for User Story 3

- [X] T033 [P] [US3] Implement `code/models/evaluator.py` (topic-localized evaluator) to calculate "consensus gap" scores for LLM outputs against ideal resolution (independent of state labels)
- [X] T034 [US3] Implement `code/analysis/metrics.py` to compute consensus gap closure for every trajectory in `data/processed/experiment_logs.json`
- [X] T038 [US3] Implement `code/analysis/stats.py` to perform conditional statistical workflow: (1) Shapiro-Wilk normality test on difference scores, (2) if normal (p>=0.05) run paired t-test, else run Wilcoxon signed-rank test, (3) apply Holm-Bonferroni correction for multiple comparisons across multiple LLMs, and (4) generate final report with t-statistic, p-value, Cohen's d, and `is_significant` flag. **Stratified Analysis**: Additionally, generate a descriptive list of metrics (mean gap, std dev) for the subset of trajectories where `emotional_reactivity` > `config.HIGH_REACTIVITY_THRESHOLD` OR `cultural_identity` diversity is high.
- [X] T039 [US3] Implement sensitivity analysis script in `code/analysis/sensitivity.py` to sweep classifier confidence thresholds (e.g., a range of values). **Input**: `data/processed/experiment_logs.json`. **Filter**: Filter out rows where `confidence_score` is null (Static condition) before processing, as these do not represent a classifier threshold sweep. **Output**: Generate `data/results/sensitivity_analysis_report.json` containing a table of confidence thresholds vs. count of injected directives.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `specs/001-dynamic-state-injection/quickstart.md`
- [X] T041 [P] Implement `code/analysis/memory_profiler.py` to instrument memory usage during the full experiment suite. **Execution**: Run the profiler against the full experiment set and generate `data/results/memory_profile_report.json`. **Constraint**: If any model exceeds a predefined RAM usage threshold, log a warning, exclude that model from the experiment, and **fail the build**.
- [ ] T043 [P] Additional unit tests in `tests/unit/` for classifier and evaluator logic
- [ ] T044 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Phase 7: Review Resolution & Verification

**Purpose**: Address specific reviewer concerns regarding data flow, statistical validity, and reproducibility.

### Review Concern: Statistical Robustness & Multiple Comparisons
> **Concern**: The plan mentions Holm-Bonferroni correction but does not explicitly detail the handling of the "high-difficulty" subset vs. the full dataset in the final report.

- [X] T046 [US3] Refactor `code/analysis/stats.py` to perform stratified statistical analysis, applying Holm-Bonferroni correction across both the full dataset and the high-difficulty subset. **Requirement**: For the high-difficulty subset, run the same statistical tests (t-test/Wilcoxon) and report **both** the corrected p-values (Holm-Bonferroni) and the uncorrected p-values for transparency. Do not skip correction for the subset.

### Review Concern: Statistical Reproducibility
> **Concern**: T047 requires verifying statistical reproducibility by asserting mean consensus gap variance < `config.STATISTICAL_VARIANCE_TOLERANCE`, but this configuration constant is not defined in the tasks or spec.

- [X] T047 [US3] Implement `code/analysis/reproducibility_check.py` to verify that repeated runs (with same seed) produce mean consensus gap scores with variance < `config.STATISTICAL_VARIANCE_TOLERANCE` (defined in T004 as 0.01). **Requirement**: Assert this condition and fail the build if the variance exceeds the threshold, ensuring strict reproducibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Phase 3 (US1)**: No dependencies on other stories
 - **Phase 4 (US2)**: Explicitly depends on the completion of Phase 3 (US1). Specifically, T019 must generate `classifier_training_data.json` before T020 can run.
 - **Phase 5 (US3)**: Explicitly depends on the completion of Phase 4 (US2). Specifically, T028 must generate `experiment_logs.json` before T034 can run.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation for input
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 experiment logs for input

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

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
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All LLM inference MUST run on CPU only (no CUDA, no bitsandbytes, no aggressive quantization). If a model exceeds available system memory, exclude it (see T009, T041).
- **Critical Constraint**: All data must be real/generated locally; no fake/synthetic input data for final results.
- **Critical Constraint**: The classifier MUST be trained on turn-level dialogue text (T019) to satisfy FR-002.
- **Critical Constraint**: T024a and T024b implement the runtime streaming logic to extract turn level features from trajectories during experiments for dynamic prompt injection, using the same sliding window algorithm as training data derivation (T045).
- **Critical Constraint**:  T038 applies Holm-Bonferroni correction across all statistical tests including those performed on the high-difficulty dataset subset.
- **Critical Constraint**: T041 fails builds if memory limits are exceeded.
- **Critical Constraint**: T049 must halt generation if power analysis fails.