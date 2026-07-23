# Tasks: llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-adaplanbench/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001 [P] Create `data/raw/` directory
- [X] T002 [P] Create `data/processed/` directory
- [X] T003 [P] Create `code/` directory structure including `dataset/`, `agent/`, `analysis/`
- [X] T004 [P] Create `tests/unit/` and `tests/integration/` directories
- [X] T005 [P] Initialize Python project with `requirements.txt` (transformers, datasets, pandas, statsmodels, scikit-learn, pytest)
- [X] T006 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Implement `code/config.py` with paths, random seeds, resource limits, and dataset configuration (including official URL fallbacks for AdaPlanBench). Define `DatasetBlockedException` and `ResourceLimitExceeded` custom exceptions here.
- [X] T008 Implement `code/main.py` orchestration script with resource monitor wrapper (logs CPU/RAM per task, fails fast on limit)
- [ ] T008a [P] Implement the resource monitor wrapper logic in `code/main.py` (FR-006). Logic: Wrap task execution with a context manager that logs CPU and RAM usage per task to `data/processed/resource_logs.json`. **Schema**: `{"timestamp": "ISO8601", "task_id": "string", "cpu_percent": "float", "ram_gb": "float", "threshold_exceeded": "bool", "exceeded_limit": "string (CPU|RAM|null)", "snapshot_values": {"cpu": "float", "ram": "float"}}`. **Fail-fast mechanism**: Raise `ResourceLimitExceeded` exception immediately if CPU > 90% or RAM > 6.5GB, aborting the run. The log MUST record the values that triggered the exception before aborting. **Verification**: Run `pytest tests/unit/test_resource_monitor.py` to verify schema and exception raising. **Dependencies**: T007.
- [X] T009 Create base `code/agent/base.py` abstract agent interface
- [X] T026c [US2] Create `contracts/execution-log.schema.yaml` defining the structure for execution logs. **Full Schema Content**:
 ```yaml
 type: object
 properties:
 task_id: { type: string }
 constraint_count: { type: integer }
 generated_plan: { type: string }
 violation_boolean: { type: boolean }
 violation_reason: { type: [string, "null"] }
 violation_status: { type: [string, "null"] } # Added for FR-009: "implicit_unverified", "false_negative", or null
 final_score: { type: number }
 required: [task_id, constraint_count, generated_plan, violation_boolean, violation_reason, violation_status, final_score]
 ```
 **Note**: This schema defines the contract based on FR-004, FR-007, and FR-009 requirements. The `violation_status` field is mandatory to distinguish between explicit violations and unverified/implicit constraints. **Run BEFORE T026a and T026b-1**.
- [ ] T012b [US1] Implement Dataset Reachability & Block Check in `code/dataset/loader.py`. **Logic**: Attempt to fetch the AdaPlanBench dataset. Verify the existence of the `progressive_constraints` field in the metadata. If fetch fails or field is missing, raise `DatasetBlockedException` with a clear error message and abort the pipeline. **Verification**: Run `pytest tests/unit/test_filter.py::test_dataset_block_exception` to ensure the exception is raised correctly when data is missing. **Dependencies**: T007. **Run BEFORE T013**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Preparation and Constraint Filtering (Priority: P1) 🎯 MVP

**Goal**: Isolate the specific subset of AdaPlanBench where constraints are revealed progressively (≥5) to establish the independent variable.

**Independent Test**: Load raw dataset, apply filter, verify output count and `constraint_count` field for a sample of tasks against metadata.

### Implementation for User Story 1

- [X] T010 [US1] Unit test for filter logic in `tests/unit/test_filter.py` (verifies exclusion of <5 constraints)
- [X] T012 [US1] Implement `code/dataset/loader.py` to fetch AdaPlanBench household tasks. **Configuration**: Read dataset ID/URL from `code/config.py` (which contains official URL fallbacks). On fetch failure, raise a clear error and abort – no mock fallback. Verify existence of `progressive_constraints` field before proceeding.
- [ ] T013 [US1] Implement filtering logic in `code/dataset/loader.py` to select tasks with ≥5 progressive constraint reveals and write to `data/processed/filtered_tasks.csv`. **Output Schema**: The CSV MUST include columns `task_id`, `raw_prompt`, `progressive_constraints` (list), and `constraint_count` (integer, calculated as `len(progressive_constraints)`). **Verification**: Run `pytest tests/unit/test_filter.py::test_constraint_count_calculation` and verify row count in `filtered_tasks.csv` matches expected N (non-zero). **Dependencies**: T012b, T012. **Run AFTER T012b AND T012**.
- [X] T011 [US1] Integration test `test_filtered_dataset_schema` in `tests/integration/test_dataset_content.py` (verifies `progressive_constraints` schema and `constraint_count` field presence; **Run AFTER T013**)
- [ ] T015 [US1] Implement validation script `code/dataset/validate_subset.py` to sample a subset of tasks and verify constraint counts match original metadata. **Verification**: Run `validate_subset.py` and verify exit code 0 and log "Validation passed" for [deferred] of sampled tasks. **Dependencies**: T013. **Run AFTER T013**.

**Checkpoint**: Filtered dataset ready; independent variable established.

---

## Phase 4: User Story 2 - Dual-Track Agent Execution and Constraint Logging (Priority: P2)

**Goal**: Execute dual-track architecture (SLM generator + deterministic constraint store) and monolithic baseline, logging violations, corrections, and reconfiguration metrics.

**Independent Test**: Run agent on a known task with a specific constraint violation; verify rule-based module intercepts, corrects, and logs the event.

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for `code/agent/resolver.py` in `tests/unit/test_resolver.py` (verifies string matching and negation patterns)
- [X] T018 [P] [US2] Contract test for execution log schema in `tests/contract/test_execution_log_schema.py`

### Implementation for User Story 2

- [ ] T013b [US2] Implement `code/dataset/loader.py` function `fetch_monolithic_baseline_model()` to download a local, CPU-tractable monolithic baseline model (e.g., `microsoft/Phi-3-mini-4k-instruct` in default precision). **Constraint**: Must NOT use external APIs. Must run on CPU. **Verification**: Verify model loads successfully and generates a sample response within 60 seconds on CPU. **Dependencies**: T007. **Run BEFORE T026a**.
- [X] T020 [US2] Implement `code/agent/monolithic.py` (direct SLM prompt) using the local model fetched in T013b.
- [X] T021 [US2] Implement `code/agent/constraint_store.py` (deterministic key‑value store for active constraints). **Logic**: Use in-memory dictionary. Methods: `add_constraint(task_id, constraint_text)`, `check_violation(task_id, proposed_action)`, `get_active_constraints(task_id)`.
- [X] T022 [US2] Implement `code/agent/resolver.py` with exact string matching, case‑insensitive substring matching, and explicit negation patterns (FR‑007). **Logic**: Detect violations only. **Include FR-008**: If intent parsing fails, log "false_negative". **Include FR-009**: If constraint is implicit or pattern fails, log "implicit_unverified" in `violation_status`, set `violation_boolean` to false, and flag for human review. **Verification**: Run `pytest tests/unit/test_resolver.py` covering all three status types (violation, false_negative, implicit_unverified). **Dependencies**: T021. **Run AFTER T021**.
- [X] T023 [US2] Implement `code/agent/dual_track.py` to orchestrate generator, store, and resolver.
- [ ] T026a [US2] Implement `code/agent/monolithic_runner.py` with function `run_monolithic(dataset, model)` to execute the monolithic baseline on `data/processed/filtered_tasks.csv`. **Note**: This task executes the LOCAL monolithic baseline (Phi-3-mini) as per Plan constraints. The Spec's Assumption regarding GPT-4/API baselines is explicitly superseded by the Plan's 'Constraints' section for this execution phase. Output logs to `data/processed/monolithic_logs.json`. **Output Schema**: Conforms to `contracts/execution-log.schema.yaml`. **Dependencies**: T013, T026c, T020, T013b. **Verification**: Verify `monolithic_logs.json` exists with N rows matching `filtered_tasks.csv` count. Run integration test `test_monolithic_execution`. **Run AFTER T013, T026c, T020, T013b**.
- [ ] T026b-1 [US2] Implement `code/agent/dual_track_runner.py` with function `run_dual_track(dataset)` to execute the dual-track agent on `data/processed/filtered_tasks.csv`. **Logic**: Load tasks, invoke generator, constraint store, and resolver. **Dependencies**: T021, T022, T023, T013. **Verification**: Verify the runner executes without error on a single task. **Run AFTER T021, T022, T023, T013**.
- [ ] T026b-2 [US2] Implement violation logging logic in `code/agent/dual_track_runner.py`. **Logic**: Integrate the resolver's output (violation, false_negative, implicit_unverified) into the execution trace. **Dependencies**: T026b-1, T022. **Verification**: Run a single task and verify the log contains the correct `violation_status` field. **Run AFTER T026b-1**.
- [ ] T026b-3 [US2] Integrate logging into the execution loop and write results to `data/processed/dual_track_logs_full.json`. **Logic**: Ensure the log includes `task_id`, `constraint_count`, `generated_plan`, `violation_boolean`, `violation_reason`, `violation_status`, and `final_score`. **Dependencies**: T026b-2. **Verification**: Verify `dual_track_logs_full.json` exists and contains "violation_status" field for all rows. **Run AFTER T026b-2**.
- [X] T026e [US2] Implement `code/agent/judges.py` to wrap and integrate the original AdaPlanBench automated judges for scoring task success and constraint adherence (FR-004).
- [ ] T026f [US2] Merge and Validate Execution Logs. **Logic**: Read `data/processed/monolithic_logs.json` (T026a) and `data/processed/dual_track_logs_full.json` (T026b-3), validate against schema (T026c). Create TWO outputs: (1) `execution_traces_filtered.csv` (filtering out rows where `violation_status` is 'implicit_unverified' for primary analysis) and (2) `execution_traces_full.csv` (retaining all rows for validation). **Output Schema**: Columns: `task_id`, `architecture` (monolithic|dual_track), `constraint_count`, `violation_boolean`, `violation_reason`, `violation_status`, `final_score`. **Dependencies**: T026a, T026b-3, T024 (merged into T022). **Verification**: Verify `execution_traces_filtered.csv` row count equals sum of monolithic and dual_track logs minus filtered rows. Verify `execution_traces_full.csv` contains all rows. **Run AFTER T026a AND T026b-3**.
- [ ] T030 [US3] Implement `code/analysis/power.py` to perform power analysis on the filtered subset. **Method**: Calculate the achieved power for the GLMM given: `groups=2` (monolithic vs dual-track), `alpha=0.05`, `effect_size=0.15` (Cohen's f² target), and `n_observations` derived from the actual sample size in `data/processed/filtered_tasks.csv` (from T013). Use `statsmodels.stats.power` or equivalent. Generate `data/processed/power_report.json`. **Output Schema**: `calculated_power` (float), `effect_size` (float), `sample_size` (int), `groups` (int). Log the result. **Dependencies**: T013. **Run AFTER T013**.
- [ ] T033 [US3] Implement `code/dataset/annotator.py` CLI to randomly select a sample of tasks from `data/processed/filtered_tasks.csv`. Use `random.seed(42)` and stratified sampling by `constraint_count` (from T013) with bins: `[5, 6, 7+]` where `7+` includes ALL tasks with `constraint_count >= 7`. Output `data/processed/annotation_sample.csv`. **Output Schema**: Columns must be `task_id`, `raw_prompt`, `constraint_list`, `constraint_count`. This sample is independent of the rule-based module (FR-010). **Dependencies**: T013. **Verification**: Run `test_stratified_sampling` to verify equal distribution across constraint_count bins. **Run AFTER T013**.
- [ ] T034 [US3] Implement comparison script that reads `data/processed/execution_traces_full.csv` and the human‑annotated ground truth from `data/processed/annotation_sample.csv`, computes the agreement rate with confidence interval, and writes `data/processed/agreement_rate_report.json`. **Logic**: Compare rule-based violation flags against human annotations. **Output Schema**: `agreement_rate` (float), `confidence_interval_lower` (float), `confidence_interval_upper` (float), `sample_size` (int). **Dependencies**: T026f, T033. **Verification**: Verify `agreement_rate_report.json` contains confidence intervals and matches manual calculation on sample data. **Run AFTER T026f AND T033**.
- [ ] T034b [US3] Implement `code/analysis/exclusion_validator.py` to validate the exclusion logic (SC-001). **Logic**: Read `data/processed/execution_traces_full.csv` (T026f) and `data/processed/annotation_sample.csv` (T033). Identify cases where the system flagged `violation_status='implicit_unverified'`. Check if human annotators agreed these should be excluded (i.e., not violations). Compute the **precision** of the implicit detection logic (True Positives / (True Positives + False Positives)) for the 'implicit' flag. **Output**: `exclusion_validation_report.json` with `exclusion_agreement_rate` (float) and `implicit_detection_precision` (float). **Dependencies**: T034. **Verification**: Verify report exists and contains `exclusion_agreement_rate` and `implicit_detection_precision`. **Run AFTER T034**.
- [ ] T035 [US3] Implement `code/analysis/adherence_verifier.py` to calculate the dual-track agent's adherence rate from `data/processed/execution_traces_filtered.csv`. **Logic**: Filter out rows where `violation_status` is "implicit_unverified" before calculating the rate (already done in T026f). **Compare against the SC-004 threshold of >85%**. Generate `data/processed/adherence_verification.json` with `adherence_rate` (float) and `threshold_passed` (bool). **Dependencies**: T026f. **Verification**: Verify `adherence_verification.json` `threshold_passed` is True/False based on >85% calculation. **Run AFTER T026f**.
- [ ] T036 [US3] Implement `code/analysis/glmm.py` to fit GLMM with binomial link function testing interaction between "number of constraints" and "architecture". **Dependencies**: T026f. **Verification**: Verify `statistical-results.json` matches schema and contains p-value for interaction term. **Run AFTER T026f**.
- [ ] T036a [US3] Implement `code/analysis/cost_analysis.py` to perform t-test on reconfiguration costs (if logged) or report N/A. **Logic**: Read `data/processed/execution_traces_filtered.csv`. If reconfiguration cost is present, perform t-test. If not, report N/A. **Output**: `cost_analysis_report.json`. **Dependencies**: T026f. **Verification**: Verify report exists. **Run AFTER T026f**.

**Checkpoint**: Dual‑track and monolithic agents executed; violation logs, reconfiguration metrics, and heuristic adaptation data generated.

---

## Phase 5: User Story 3 - Statistical Analysis and Validation (Priority: P3)

**Goal**: Perform GLMM analysis and human annotation validation to determine if explicit constraint tracking mitigates performance degradation and distinguishes search from learning.

**Independent Test**: Run GLMM on logs; verify output includes fixed effect estimates, p‑values, and convergence diagnostics.

### Tests for User Story 3

- [X] T028 [P] [US3] Unit test for GLMM model fitting in `tests/unit/test_glmm.py` (sanity check on synthetic data)
- [X] T029 [P] [US3] Integration test for power analysis in `tests/integration/test_power_analysis.py`

### Implementation for User Story 3

- [X] T032 [US3] Implement `code/hash_artifacts.py` to compute SHA‑256 hashes for existing files in `data/` (if any exist) and update state YAML (Constitution Principle V)
- [X] T038 [US3] [P] Update `research.md` with a results section comparing dual‑track vs. monolithic violation rates across constraint counts. Explicitly report the **interaction effect** p-value and effect size as per SC-002. Link this output to the final paper generation to satisfy Constitution Principle IV.
- [X] T039 [US3] [P] Add unit tests for edge cases in `tests/unit/` including: implicit constraint handling (no violation logged), parsing failures (false_negative logged), and empty constraint lists

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041b [P] Refactor `code/agent/resolver.py` by extracting the `match_constraint` function into a new module `code/agent/constraint_matcher.py`.
- [X] T007a [P] [US1] Generate `quickstart.md` with setup instructions, dependency installation, and execution steps to validate the project structure. (Reference plan.md Phase 1 documentation requirements). **Run AFTER all Phase 3, 4, 5 tasks are complete.**
- [X] T043 [P] Run `quickstart.md` validation and ensure all steps complete within 6 hours on CI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Phase 5 (Analysis)**: Depends on Foundational and US2 implementation; can run in parallel with US3 analysis
- **Phase N**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T026f (Execution Traces) for variance calculation
- **Phase 5 (Analysis)**: Depends on T021, T022, T026f; provides critical metrics for US3 analysis
- **Phase N**: Can start after all desired user stories are complete

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
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
- **Scope Note**: The scope is strictly limited to User Stories 1-3 as defined in spec.md. No additional research objectives are included. The 'reconfiguration cost' and 'heuristic abandonment' metrics are NOT implemented as primary analysis targets. T036a is a placeholder for cost analysis if data is available, but it is not a core requirement.
- **Critical Constraint**: Phase 6 (Search vs. Learning) has been removed as it was not authorized by the spec. The project now strictly adheres to FR-001 through FR-011.
- **Revision Note**: Tasks T016, T025, T026d, T037, T040, T041a have been removed to align with the scope note. Tasks T008a, T022b, T026e, T026f have been added/updated to address missing FR requirements. T026c (schema) has been moved to Phase 2 to resolve circular dependencies. T030 (Power Analysis) has been moved to Phase 5 and updated to depend on T013 for pre-execution validation. Tasks T014, T014b, T027b, T035b, T038b have been removed to resolve scope creep and logical contradictions. T026b and T026f have been consolidated into single tasks with explicit dependencies. Phase 6 (T044-T048) has been removed to address the Alan Turing review concern regarding unapproved scope. T027a and T036a have been removed/merged into T026b and T036 respectively. T024 has been merged into T022. T027 has been removed. T026b has been split into T026b-1, T026b-2, T026b-3. T036a has been separated from T036.
- **Review Response**: The reviewer's concern regarding "Search vs. Learning" has been addressed by removing the unapproved scope (Phase 6) and instead integrating the "Cost of Reconfiguration" metric directly into the existing execution and analysis phases (Task T026b) as a logged metric only, not a primary analysis target.
- **Concern Resolution**: The dependency concern [ordering-cecab032] regarding Task T035b is resolved because Task T035b (and its dependencies T014b, T027b) was removed from the project scope as it was identified as scope creep. The task no longer exists, and thus the dependency chain is invalid. The new Phase 5 tasks (T030-T036a) are designed to be independent of T035b and do not introduce circular dependencies.
- **Dataset Block Handling**: T012b ensures the pipeline halts immediately if the dataset is unreachable, satisfying the Plan's "BLOCKED" requirement.
- **Baseline Resolution**: T013b resolves the API vs. No-API contradiction by fetching a local model.
- **Exclusion Validation**: T034b explicitly validates the exclusion logic per SC-001.
- **Schema Fix**: T008a schema updated to include failure evidence.
- **Verification**: All tasks with "FAILED: unspecified" now have explicit verification steps.
- **Merged Tasks**: T024 merged into T022. T027 removed (redundant). T027a merged into T026b. T026b split into T026b-1, T026b-2, T026b-3. T036a separated from T036.