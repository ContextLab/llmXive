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

- [X] T001 Create `scripts/init_repo.py` to generate the directory structure defined in plan.md: `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`, `contracts/`.
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
- [X] T009 [P] Create `code/experiments/model_loader.py` with a pre-flight memory check function that estimates model size. **Logic**: If a model's estimated RAM usage > 7GB, log a warning, skip loading it, and **record this exclusion in `data/results/scope_adjustments.json`**. **Schema Requirement**: The `scope_adjustments.json` file MUST be a valid JSON list of objects with keys `model_name`, `reason`, and `estimated_ram_gb` to ensure machine-readability for downstream statistical tasks (T038A). Add a unit test in `tests/unit/test_model_loader.py` that verifies this exclusion and logging logic works for a mock large model.
- [X] T027 [US2] Implement CPU-only inference loop in `code/experiments/runner.py` using `transformers` with `device="cpu"`. **Verification**: Explicitly map the model to CPU. **Constraint**: If `torch.cuda.is_available()` returns True, the script MUST **FAIL THE BUILD** with a clear error message stating "GPU detected; reproducibility requires CPU-only execution." DO NOT warn and continue. Explicitly exclude bitsandbytes/quantization libraries. Implement fallback logic to inject "neutral monitoring state" on low confidence (FR-002).

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

- [X] T012 [P] [US1] Implement `code/data/generator.py` to generate conflict trajectories with metadata tags (emotional reactivity, cultural identity)
- [X] T013 [US1] Implement oversampling logic in `code/data/generator.py` to ensure ≥40% of trajectories fall into "high emotional reactivity" or "diverse cultural identity" categories
- [X] T014 [US1] Implement `code/data/generator.py` output writer to save trajectories to `data/processed/trajectories.json` and a summary report to `data/processed/generation_stats.json`. **Requirement**: The summary report MUST explicitly list the count and percentage of trajectories in each target category to satisfy T049 validation.
- [X] T015 [US1] Add validation in `code/data/generator.py` to verify generated data meets the 40% threshold before writing
- [X] T016 [US1] Add logging for generation parameters and final distribution counts
- [X] T019 [US1] Implement `code/data/generator.py` to **derive turn-level training pairs** from generated `ConflictTrajectory` objects. **Requirement**: Implement logic to split the full trajectory history into sliding windows of N=3 turns (use `config.TURN_WINDOW_SIZE`) to create `turn_text` (dialogue snippet) and `label` (socio-cognitive state from trajectory metadata) pairs. **Schema Requirement**: The output `data/processed/classifier_training_data.json` MUST include `confidence_score` (float) and `threshold_used` (float) fields in every record to support downstream sensitivity analysis (T039). Save this derived dataset. **Independence Check**: Explicitly verify that the `label` derivation logic uses ONLY trajectory metadata tags (e.g., emotional reactivity, cultural identity) and does NOT incorporate any logic or data from the `ConsensusGapScore` evaluator (FR-005). This ensures the classifier trains on independent metadata without circular validation.
- [X] T049 [US1] Implement `code/analysis/power_analysis.py` to calculate the required sample size. **Requirement**: Using `statsmodels.stats.power.tt_solve_power`, compute the minimum N required to detect a medium effect size (Cohen's d = 0.5) with power=0.80 and alpha=0.05 for a paired t-test. **Output**: Generate `data/results/power_analysis_report.json` containing the calculated N and a boolean `is_sufficient` flag comparing it against the actual generated trajectory count (T014). **Constraint**: If `is_sufficient` is false, the script MUST generate a `data/results/HALT` file containing a JSON object with `reason`, `required_n`, `actual_n`, and `timestamp`, **log a warning** to proceed, and **NOT exit with code 1**, allowing the pipeline to continue to Phase 4 to report the underpowered result. **Action**: The script MUST generate the report (stating the study is underpowered) and **NOT exit with code 1**, satisfying Spec Assumption 4. **Dependency**: This task depends on T014 completion.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. **Phase 4 is blocked until T049 generates the power report (even if underpowered).**

---

## Phase 4: User Story 2 - Execute Paired Mediation Experiments (Priority: P2)

**Goal**: Run conflict trajectories through eight distinct LLMs under two conditions: (A) with dynamic socio-cognitive state adapter, (B) with static baseline prompt, ensuring CPU-only execution.

**Independent Test**: Run experiment script for one LLM and subset of trajectories, verifying "Adapter" logs contain injected state signals (e.g., "de-escalate") while "Static" logs do not.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for prompt injection in `tests/contract/test_prompt_injection.py`
- [X] T022 [P] [US2] Integration test for paired experiment execution in `tests/integration/test_experiment_runner.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/models/classifier.py` with a lightweight logistic regression classifier. **Input Schema**: Must accept `classifier_training_data.json` containing a list of dicts with keys `turn_text`, `label`, `trajectory_id`, `confidence_score`, `threshold_used`. **Training**: Train on `turn_text` features (e.g., TF-IDF) to predict `label`. Ensure no overlap with evaluation metrics (FR-002). **Dependency**: This task requires T019 to complete first; it is NOT parallel-safe with T019.
- [X] T023 [P] [US2] Implement `code/experiments/prompts.py` with templates for Static baseline and Dynamic Adapter (injecting state instructions like "validate cultural norms", "de-escalate")
- [X] T045A [US2] Refactor `code/experiments/runner.py` to explicitly import and reuse the `split_trajectory_into_turns` function from `code/data/generator.py` (defined in T019). **Dependency**: T024 depends on this refactoring to ensure shared logic.
- [X] T045B [US2] Implement `tests/unit/test_data_flow.py` to verify the runtime streaming logic produces identical turn windows to the training data derivation logic for a fixed seed trajectory. **Requirement**: This test explicitly verifies the "train on real data" constraint (FR-002) is strictly maintained without circularity. **Dependency**: Depends on T045A.
- [X] T024 [US2] Implement `code/experiments/runner.py` to load trajectories, run the classifier every N turns, and inject dynamic prompts for the Adapter condition. **Requirement**: Implement a stateful accumulator that appends dialogue turns and triggers the classifier every N=3 turns (using `config.TURN_WINDOW_SIZE`) using the logic defined in T019 and T045A. This explicitly resolves the gap between static trajectory generation and dynamic inference requirements (FR-002). **Dependency**: Depends on T020 (classifier), T045A (shared split logic), and T045B (test).
- [X] T025 [US2] Implement `code/experiments/runner.py` to run the Static condition (no injection) for the same trajectories
- [X] T026 [US2] Integrate retry logic from `code/experiments/retry_utils.py` to handle timeouts/crashes, **aggregating skipped samples and logging the count in `data/processed/experiment_logs.json`** per trajectory and condition.
- [X] T028 [US2] Save experiment logs to `data/processed/experiment_logs.json` containing trajectory ID, condition (Adapter/Static), injected state (if any), and LLM output. **Mandatory**: For the **Adapter** condition, the log entry for each turn MUST include `confidence_score` (float) and `injected_state` (string or null). **Requirement**: For the **Static** condition entries, explicitly set `confidence_score` to `null` and `injected_state` to `null` to maintain schema consistency. **Edge Case Handling**: If the Adapter condition triggers but the classifier confidence is below threshold, `injected_state` MUST be set to the string `"neutral-monitoring"` (not null) to distinguish this fallback from the Static baseline. **Traceability**: Explicitly reference the Spec's "Edge Case" for low confidence handling and link to T050 for the neutral monitoring prompt logic. **Statistical Note**: Downstream analysis (T034/T038) MUST treat `injected_state` = "neutral-monitoring" as "no injection" to preserve the validity of the Static baseline comparison.
- [X] T029 [US2] Add validation to ensure the classifier fails gracefully to a neutral "monitoring" state on low confidence (Edge Case FR-002)
- [X] T042 [US2] Implement `code/analysis/perf_monitor.py` to calculate throughput (trajectories/hour) and latency (s/trajectory) from `experiment_logs.json`. **Verification**: Add a step that logs a warning if throughput < 40 or latency > 45. **Constraint**: The script must generate `data/results/perf_report.json` with these metrics to satisfy SC-003 reporting requirements. **Explicitly DO NOT fail the build** if thresholds are missed; this is a measurement of feasibility, not a gate.
- [X] T050 [US2] Refactor `code/experiments/prompts.py` to explicitly define the "neutral monitoring" system prompt template. **Requirement**: This template must be distinct from the "Static" baseline (which has no injection) and the "Dynamic" injection (which has specific directives). It should explicitly state the LLM to "maintain neutrality and monitor for escalation" without taking a side. Update `code/experiments/runner.py` to inject this specific template when `confidence_score` < `config.CONFIDENCE_THRESHOLD`. **Dependency**: Depends on T023.
- [X] T047A [US2] Implement a deterministic experiment runner wrapper in `code/experiments/runner.py`. **Requirement**: The script must accept a `--seed` argument that seeds `numpy`, `random`, and `torch` (CPU) at the start of execution. Set `torch.use_deterministic_algorithms(True)` and `torch.backends.cudnn.deterministic = True`. **Verification**: Run the experiment twice with the same seed and trajectory subset, and assert that the resulting `experiment_logs.json` files show statistical reproducibility: specifically, the mean consensus gap variance between the two runs must be < `config.STATISTICAL_VARIANCE_TOLERANCE`. Do NOT assert byte-for-byte identity, as CPU inference may exhibit minor floating-point variations.
- [X] T047B [US2] Implement `tests/unit/test_reproducibility.py` to execute the deterministic runner wrapper (T047A) twice with the same seed and assert that the mean consensus gap variance is within tolerance. **Dependency**: Depends on T047A.

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
- [X] T034 [US3] Implement `code/analysis/metrics.py` to compute consensus gap closure for every trajectory in `data/processed/experiment_logs.json`. **Dependency**: This task depends on T028 (Phase 4) completion; it is NOT parallel-safe with any Phase 4 tasks. **Note**: T034 is blocked until Phase 4 (specifically T028) completes. **Statistical Note**: Explicitly filter out or treat `injected_state` = "neutral-monitoring" as "no injection" to preserve baseline validity.
- [X] T038A [US3] Implement `code/analysis/stats.py` Part 1: Data ingestion. Read `scope_adjustments.json` and `memory_profile_report.json` to determine the **actual** number of LLMs executed (N_actual).
- [X] T038B [US3] Implement `code/analysis/stats.py` Part 2: Normality testing. Perform Shapiro-Wilk normality test on difference scores.
- [X] T038C [US3] Implement `code/analysis/stats.py` Part 3: Statistical testing and correction. If normal (p>=0.05) run paired t-test, else run Wilcoxon signed-rank test. Apply Holm-Bonferroni correction for multiple comparisons across the **actual** N_actual LLMs (defining the "family" as the set of per-LLM p-values). **Stratified Analysis**: Generate descriptive metrics for the high-difficulty subset, but **DO NOT** apply Holm-Bonferroni correction to this subset (FR-007 applies only to aggregation across LLMs). Report the high-difficulty results as descriptive statistics with a note on potential underpowering.
- [X] T038D [US3] Implement `code/analysis/stats.py` Part 4: Report generation. Generate final report with t-statistic, p-value, Cohen's d, and `is_significant` flag.
- [X] T039 [US3] Implement sensitivity analysis script in `code/analysis/sensitivity.py` to sweep classifier confidence thresholds (e.g., a range of values). **Input**: `data/processed/experiment_logs.json` (must contain `confidence_score`). **Filtering Requirement**: Explicitly filter the input data WHERE `condition == 'Adapter'` before applying threshold logic to avoid skewing the "count of injected directives" metric with null values from the Static condition. **Output**: Generate `data/results/sensitivity_analysis_report.json` containing a table of confidence thresholds vs. count of injected directives, and verify the file exists with the correct schema (satisfying SC-005).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040A [P] Update `README.md` with installation instructions, dependencies, and quick start guide.
- [X] T040B [P] Update `specs/001-dynamic-state-injection/quickstart.md` with step-by-step execution instructions for the full pipeline.
- [X] T041 [P] Implement `code/analysis/memory_profiler.py` to instrument memory usage during the full experiment suite. **Execution**: Run the profiler against the full experiment set and generate `data/results/memory_profile_report.json`. **Constraint**: The script MUST log a warning if any model exceeds a predefined RAM usage threshold, **exclude that model from the experiment run**, and ensure the excluded model is **removed from `data/processed/experiment_logs.json`** before statistical aggregation (T038A). **MUST NOT fail the build**, but must ensure the final report only reflects valid scope.
- [X] T043A [P] [US2] Implement unit tests for the logistic regression classifier in `tests/unit/test_classifier.py`. **Requirement**: Must include `test_classifier_predicts_correct_label`, `test_classifier_handles_low_confidence`, and `test_classifier_independence_from_evaluator`.
- [X] T043B [P] [US3] Implement unit tests for the topic-localized evaluator in `tests/unit/test_evaluator.py`. **Requirement**: Must include `test_evaluator_calculates_gap_score`, `test_evaluator_independence_from_state_labels`, and `test_evaluator_handles_missing_ideal_resolution`.
- [X] T044A [P] Implement `scripts/validate_quickstart.py` to run the full pipeline as described in `quickstart.md`. **Requirement**: The script must generate `data/results/quickstart_validation_report.json` containing: `timestamp`, `exit_code`, `log_file_path`, `success_flag` (boolean), and `error_message` (if any). **Dependency**: Depends on T040A, T040B, T041, T043A, T043B, T051.
- [X] T051 [US3] Implement `code/analysis/report_generator.py` to synthesize the final research paper draft. **Requirement**: The script must ingest `data/results/stats_report.json`, `data/results/sensitivity_analysis_report.json`, and `data/results/power_analysis_report.json`. It must generate a Markdown document `docs/research_draft.md` that includes: (1) A Methods section explicitly stating the sample size, power calculation, and exclusion criteria (T009, T041); (2) A Results section with tables for the primary hypothesis (all LLMs) and the stratified high-difficulty analysis; (3) A Discussion section that interprets the Holm-Bonferroni corrected p-values and the sensitivity analysis findings. **Constraint**: The script must fail if any required input file is missing or malformed.

---

## Phase 7: Review Resolution & Verification

**Purpose**: Address specific reviewer concerns regarding data flow, statistical validity, and reproducibility.

### Review Concern: Data Flow & Turn-Level Inference
> **Concern**: The original plan implied static trajectory generation but required dynamic turn-level inference. The dependency between T019 (training data derivation) and T024 (runtime streaming) must be explicit to ensure the classifier uses the same logic at runtime as it did during training.

- [X] T045A [US2] (Moved to Phase 4) Refactor `code/experiments/runner.py` to explicitly import and reuse the `split_trajectory_into_turns` function from `code/data/generator.py` (defined in T019). **Requirement**: Add a unit test in `tests/unit/test_data_flow.py` (T045B) that verifies the runtime streaming logic produces identical turn windows to the training data derivation logic for a fixed seed trajectory. This ensures the "train on real data" constraint (FR-002) is strictly maintained without circularity.

### Review Concern: Statistical Robustness & Multiple Comparisons
> **Concern**: The plan mentions Holm-Bonferroni correction but does not explicitly detail the handling of the "high-difficulty" subset vs. the full dataset in the final report.

- [X] T038C [US3] (Updated) Logic moved to T038C. The stratified analysis (now descriptive only) is now part of the core Phase 5 workflow.

### Review Concern: Statistical Reproducibility
> **Concern**: T047 requires verifying statistical reproducibility by asserting mean consensus gap variance < `config.STATISTICAL_VARIANCE_TOLERANCE`, but this configuration constant is not defined in the tasks or spec.

- [X] T047A [US2] (Moved to Phase 4) Implement a deterministic experiment runner wrapper in `code/experiments/runner.py`. **Requirement**: The script must accept a `--seed` argument that seeds `numpy`, `random`, and `torch` (CPU) at the start of execution. Set `torch.use_deterministic_algorithms(True)` and `torch.backends.cudnn.deterministic = True`. **Verification**: Run the experiment twice with the same seed and trajectory subset, and assert that the resulting `experiment_logs.json` files show statistical reproducibility: specifically, the mean consensus gap variance between the two runs must be < `config.STATISTICAL_VARIANCE_TOLERANCE`. Do NOT assert byte-for-byte identity, as CPU inference may exhibit minor floating-point variations.
- [X] T047B [US2] (Moved to Phase 4) Implement `tests/unit/test_reproducibility.py` to execute the deterministic runner wrapper (T047A) twice with the same seed and assert that the mean consensus gap variance is within tolerance.

### Review Concern: Data Independence & Leakage Prevention
> **Concern**: Ensure the classifier training data (T019) and the evaluation ground truth (T033) are rigorously decoupled to prevent the "circular validation" risk where the model might learn to predict the evaluation score rather than the socio-cognitive state.

- [X] T048 [US1] Implement a strict data separation check in `code/data/generator.py`. **Requirement**: Before saving `classifier_training_data.json`, the script must verify that the `label` field is derived *solely* from the trajectory's metadata tags (e.g., `emotional_reactivity`, `cultural_identity`) and that the `turn_text` content does not contain any tokens or phrases that are unique to the "ideal resolution" text used in the evaluator. Add a unit test in `tests/unit/test_data_independence.py` that asserts zero overlap between the vocabulary of the classifier labels and the "ideal resolution" templates.

### Review Concern: Statistical Power & Sample Size Justification
> **Concern**: The plan assumes a sample size is sufficient for power (≥0.80) but does not task the generation of a formal power analysis report to validate this assumption before running the full experiment.

- [X] T049 [US1] (Moved to Phase 3) Implement `code/analysis/power_analysis.py` to calculate the required sample size. **Requirement**: Using `statsmodels.stats.power.tt_solve_power`, compute the minimum N required to detect a medium effect size (Cohen's d = 0.5) with power=0.80 and alpha=0.05 for a paired t-test. **Output**: Generate `data/results/power_analysis_report.json` containing the calculated N and a boolean `is_sufficient` flag comparing it against the actual generated trajectory count (T014). **Constraint**: If `is_sufficient` is false, the script MUST generate a `data/results/HALT` file containing a JSON object with `reason`, `required_n`, `actual_n`, and `timestamp`, and **log a warning** to proceed but allow the pipeline to continue to Phase 4 to report the underpowered result. **Action**: The script MUST generate the report (stating the study is underpowered) and **NOT exit with code 1**, satisfying Spec Assumption 4.

### Review Concern: Execution Feasibility & GPU Fallback Logic
> **Concern**: The spec mandates CPU-only execution, but the execution gate rule states that if a task genuinely requires GPU (e.g., specific model inference that fails on CPU), it must be scaled down for a single free GPU (Kaggle) rather than fabricated. We must explicitly task the system to detect CPU failure and trigger the GPU offload path if necessary, ensuring no "fake" CPU simulation occurs.

- [X] T027 [US2] (Updated) Implement CPU-only inference loop in `code/experiments/runner.py` using `transformers` with `device="cpu"`. **Verification**: Explicitly map the model to CPU. **Constraint**: If `torch.cuda.is_available()` returns True, the script MUST **FAIL THE BUILD** with a clear error message stating "GPU detected; reproducibility requires CPU-only execution." DO NOT warn and continue. Explicitly exclude bitsandbytes/quantization libraries. **Note**: GPU fallback is strictly forbidden per Constitution Principle VI and FR-004. If a model cannot run on CPU, it must be excluded (see T009, T041).

### Review Concern: Dataset Integrity & Streaming Validation
> **Concern**: The plan assumes local generation, but if the SoCRATES dataset were to be replaced by a large external source in a future iteration, the system must not shrink to a toy dataset. We must explicitly task the system to validate that any dataset (generated or loaded) respects the streaming/chunking constraints if it exceeds memory.

- [X] T005 [US1] (Updated) Implement data validation utilities in `code/data/loader.py` to enforce schema compliance for generated trajectories. **Note**: Since the plan specifies local generation, streaming logic for external large datasets is out of scope.

### Review Concern: Edge Case Handling for Low Confidence States
> **Concern**: The spec requires a "neutral monitoring" state for low confidence, but the implementation must ensure this state is distinct from the "Static" baseline to avoid confounding variables in the statistical analysis.

- [X] T028 [US2] (Updated) Save experiment logs to `data/processed/experiment_logs.json`. **Edge Case Handling**: If the Adapter condition triggers but the classifier confidence is below threshold, `injected_state` MUST be set to the string `"neutral-monitoring"` (not null) to distinguish this fallback from the Static baseline. **Statistical Note**: Downstream analysis (T034/T038) MUST treat `injected_state` = "neutral-monitoring" as "no injection" to preserve the validity of the Static baseline comparison.

### Review Concern: Multiple Comparison Correction Scope
> **Concern**: The Holm-Bonferroni correction must be applied only to the set of LLMs that were *actually* executed and passed memory checks, not the theoretical set of 8 LLMs.

- [X] T038A [US3] (Updated) The Holm-Bonferroni correction factor must be calculated as `1 / len(active_llms)` (or equivalent logic for the specific method chosen), NOT a fixed constant based on 8. The `active_llms` list is derived from `scope_adjustments.json` and `memory_profile_report.json`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Phase 3 (US1)**: No dependencies on other stories. **T049 (Power Analysis) must run after T014 completes.**
 - **Phase 4 (US2)**: Explicitly depends on the completion of Phase 3 (US1). Specifically, T019 must generate `classifier_training_data.json` before T020 can run. T049 must generate the power report (even if underpowered) before Phase 4 begins.
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
4. **STOP and VALIDATE**: Test User Story 1 independently and run Power Analysis (T049). **T049 will generate a report; if underpowered, it logs a warning but allows continuation.**
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Run Power Analysis → Deploy/Demo (MVP!)
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
- **Critical Constraint**: All LLM inference MUST run on CPU only (no CUDA, no bitsandbytes, no aggressive quantization). If a model exceeds available system memory, exclude it (see T009, T041). **GPU fallback is strictly forbidden.**
- **Critical Constraint**: All data must be real/generated locally; no fake/synthetic input data for final results.
- **Critical Constraint**: The classifier MUST be trained on turn-level dialogue text (T019) to satisfy FR-002.
- **Critical Constraint**: T028 must log per-turn confidence scores ONLY for Adapter condition to enable T039 sensitivity analysis; Static condition logs must have null values. **Exception**: Low-confidence Adapter cases must log `injected_state` as `"neutral-monitoring"`.
- **Critical Constraint**: T041 must generate a verifiable memory report and exclude models exceeding limits, but MUST NOT fail the build.
- **Critical Constraint**: T045A/B ensures the training data derivation logic matches the runtime inference logic exactly to prevent data leakage or logic drift.
- **Critical Constraint**: T038C ensures statistical validity by explicitly analyzing the high-difficulty subset as descriptive statistics (no Holm-Bonferroni correction applied to subset), while applying correction to the full LLM aggregation.
- **Critical Constraint**: T048 ensures strict decoupling between classifier labels and evaluation ground truth to prevent circular validation.
- **Critical Constraint**: T049 provides a formal power analysis to validate the study's statistical assumptions, and **logs a warning but allows continuation** if power is insufficient, satisfying Spec Assumption 4.
- **Critical Constraint**: T050 must define a distinct "neutral monitoring" prompt to handle low-confidence states, ensuring the fallback is not confused with the static baseline.
- **Critical Constraint**: T042 must report metrics for analysis but MUST NOT fail the build if thresholds are missed.
- **Critical Constraint**: T027 must fail the build if a GPU is detected to ensure strict reproducibility.
- **Critical Constraint**: T009 and T038A must use a defined schema for exclusion logs to dynamically adjust the Holm-Bonferroni correction factor.
- **Critical Constraint**: T047A/B ensures reproducibility by explicitly testing variance tolerance.
- **Critical Constraint**: T043A/B explicitly names test files for classifier and evaluator logic.
- **Critical Constraint**: T044A explicitly names the validation report artifact.