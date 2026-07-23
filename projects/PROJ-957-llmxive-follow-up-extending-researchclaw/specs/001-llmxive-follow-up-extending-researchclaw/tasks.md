# Tasks: llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

**Input**: Design documents from `/specs/001-llmxive-scaffold-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must complete before dependent tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `scipy`, `pytest`, `pyyaml`, `jsonschema`, `datasets`, `tqdm`, `numpy`, `statsmodels`
- [X] T003 [P] Create `pyproject.toml` with explicit configuration for linting and formatting. The file MUST contain a `[tool.ruff]` section with `line-length = 88` and `target-version = "py311"`, and a `[tool.black]` section with `line-length = 88` and `target-version = ["py311"]`. This task replaces the generic "Configure linting" instruction with a concrete file creation task.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/utils/checksum.py` for SHA256 verification of data artifacts
- [X] T005 [P] Implement `src/utils/logging.py` with structured JSON logging and error tracking
- [X] T006 [P] Implement `src/config.py` as a single source of truth for experiment parameters. The file MUST define a class `Config` with the following attributes and default values: `RESEARCHCLAWBENCH_DATASET_ID: str = "researchclawbench/v1"`, `SCIENTIFIC_CORE_MARGIN: int = 5`, `MAX_CONCURRENCY: int = 7`, `TIMEOUT_PER_RUN: int = 3600`, `TOTAL_WALL_CLOCK_BUDGET: int = 86400`. The class MUST have a `load()` method that reads from environment variables or falls back to these defaults. Export this class at the module level. **CRITICAL**: This class MUST be the single source of truth for the execution controller (T023a/T023) and must be explicitly imported by those modules to enforce the 24-hour budget.
- [ ] T007 [P] Create `src/data/loader.py` with ResearchClawBench fetch logic using `datasets.load_dataset` or canonical URL; use `RESEARCHCLAWBENCH_DATASET_ID` from `src/config.py`; include checksum verification against `data/raw/`. If the dataset ID is invalid or the checksum fails, the logic MUST trigger the "Verified Accuracy Gate" (T007b) to abort the process. **Output**: Write checksum to `data/raw/checksum.txt` in the format `sha256: <hex_string>` (plain text, no JSON wrapping).
- [ ] T007b [S] Implement "Verified Accuracy Gate" Logic: This task consolidates the gate sequence. It MUST: 1) Read the checksum file at `data/raw/checksum.txt` (produced by T007) and parse the `sha256: <hex_string>` format. 2) Verify the hash matches the expected value defined in `src/config.py`. 3) If mismatch, write "GATE: Verified Accuracy [FAIL]" to `results/verified_accuracy_gate.log`, create `results/verified_accuracy_gate.failed`, and exit the process with code 1. 4) If match, write "GATE: Verified Accuracy [PASS]" to `results/verified_accuracy_gate.log`, create `results/verified_accuracy_gate.done`, and proceed. **Dependency**: T007. <!-- FAILED: unspecified -->
- [ ] T008 [S] Create `src/data/filter.py` to implement the specific logic to SELECT tasks from the ResearchClawBench dataset where the metadata field `failure_mode` equals "experimental protocol mismatch". WRITE the resulting subset to `data/processed/protocol_mismatch_subset.json`. Include a verification step: if the `failure_mode` key is missing entirely, abort with error (FR-006). If the key exists but the count of tasks with value "experimental protocol mismatch" is < 10, OR if the dominant mode differs from "experimental protocol mismatch" (even if count >= 10), DO NOT abort; instead, write `results/failure_mode_audit.csv` with the schema `dominant_mode,count,total_tasks` (CSV header row, UTF-8, comma delimiter) containing the actual dominant mode and its count, and log a warning (Edge Case handling). **Dependency**: T007b must pass. **Output**: `data/processed/protocol_mismatch_subset.json` with SHA256 checksum.
- [ ] T009a [S] [P] Implement "Reference-Validator" step for Template URL: Verify the URL ` against the primary source using a simulated Reference-Validator check (or actual fetch to verify existence) and write the verified URL to `assets/templates/verified_template_url.txt`. If verification fails, abort. **Dependency**: T007b.
- [ ] T009b [S] [P] Fetch and Normalize Template: Fetch content from the verified URL in `assets/templates/verified_template_url.txt`. Extract ONLY the protocol content (e.g., text within `<div class="protocol">` or specific section headers) and save to `assets/templates/TEMPLATE-001-v1.0.md` with UTF-8 encoding. **Dependency**: T009a.
- [ ] T009c [S] [P] Create `assets/templates/template_map.json` with the explicit mapping of the 10 selected task IDs (from T008) to their specific template IDs (e.g., `{"task_001": "TEMPLATE-001-v1.0", "task_002": "TEMPLATE-001-v1.0"}`). This file MUST exist and be valid JSON before T015b runs. **Dependency**: T008.
- [ ] T009d [S] [P] Create `assets/templates/constraint_keywords.yaml` containing the explicit list of keywords used for "Scaffold Conflict" detection (FR-007); implement `src/scaffolding/validator.py` to load this file. **Dependency**: T009c.
- [ ] T010a [P] Create `contracts/rubric_schema.json` defining the JSON structure for "Protocol Alignment" (0-50) and "Scientific Core" scoring logic. The scoring algorithm MUST be a weighted sum of specific criteria: `{"criteria": [{"key": "step_1", "weight": 0.4}, {"key": "step_2", "weight": 0.6}]}`. Define these specific keys and weights in the task description or the file content; include `constraint_keywords` list reference for FR-007.
- [ ] T010b [P] Implement `src/scoring/rubric_engine.py` to load `contracts/rubric_schema.json` and implement the logic to calculate scores based on the schema definitions (weighted sum of criteria)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Scaffolded Protocol Injection (Priority: P1) 🎯 MVP

**Goal**: Load specific tasks, inject domain-specific procedural templates into agent prompts, and handle conflict detection.

**Independent Test**: Run a single agent on a single scaffolded task and verify the system prompt contains the injected template ID and the agent executes steps referencing it.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T011 [P] [US1] Unit test for `src/scaffolding/injector.py`: verify template ID insertion does not alter task description
- [ ] T012 [P] [US1] Unit test for `src/scaffolding/validator.py`: verify "Scaffold Conflict" detection against `assets/templates/constraint_keywords.yaml`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `src/scaffolding/injector.py`: Load task, retrieve template ID via `template_loader.py`, append template to system prompt (FR-001, FR-002)
- [ ] T014 [US1] Implement `src/scaffolding/validator.py`: Check task metadata vs `assets/templates/constraint_keywords.yaml` (loaded by T009d); log "Scaffold Conflict" and exclude run if mismatch (FR-007). **CRITICAL**: If a conflict is detected, the system MUST write the specific run ID to `results/audit_ids.csv` with the schema `run_id,task_id,conflict_reason,timestamp` (UTF-8 encoding, comma delimiter, timestamp format: ISO8601, e.g., `2026-07-12T10:00:00Z`) and flag the run for a mandatory human expert audit as required by FR-007. The file MUST be created if it doesn't exist. **Real-time Exclusion**: This logic MUST be invoked DURING the execution loop (T023) to immediately flag the run for exclusion.
- [ ] T014c [S] [US1] Implement `src/analysis/filter.py`: Load `results/audit_ids.csv` (from T014). Filter out any runs where the `run_id` exists in `audit_ids.csv` from the dataset used for aggregation. **Dependency**: T014. **Note**: This task MUST run BEFORE T024 (Aggregation) to ensure the statistical dataset is clean.
- [ ] T014b [S] [US1] Implement `src/analysis/audit_sampler.py`: Load `results/audit_ids.csv` (from T014), select a random sample of [deferred] of the conflict IDs (or all if < 10), and generate `results/human_audit_report.json` containing the selected IDs and a summary of conflict reasons. This task satisfies the "mandatory human expert audit" requirement of FR-007. **Dependency**: T014.
- [ ] T015c [US1] Implement logic to write the failure mode audit report to `results/failure_mode_audit.csv` if the dominant mode differs from the expected mode (`experimental protocol mismatch`) or if the count of expected mode is < 10 (FR-001). **Distinction**: This task handles "Failure Mode Audit" (edge case), distinct from T014 which handles "Scaffold Conflict" (FR-007).
- [ ] T016 [US1] Implement error handling in `src/cli/run_experiment.py`: Abort and exit code 1 if dataset lacks required metadata (FR-006)
- [ ] T017 [US1] Add logging for scaffold injection events and conflict warnings

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dual-Condition Execution & Scoring (Priority: P2)

**Goal**: Execute agents under Zero-Shot and Scaffolded conditions, apply rubrics, and store paired results.

**Independent Test**: Run evaluation script on a saved log and verify two distinct score objects (Zero-Shot and Scaffolded) are generated with correct sub-metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for scoring engine: verify `rubric_schema.json` loads and validates input structure
- [ ] T020 [P] [US2] Integration test: Run 1 agent on 1 task (Zero-Shot) and 1 task (Scaffolded) and verify paired output structure

### Implementation for User Story 2

- [ ] T020b [US2] Implement `src/scoring/dummy_generator.py` to generate Set A (scaffold text, no steps) and Set B (steps, no scaffold) dummy outputs; write to `results/dummy_outputs.json` for FR-008 validation (Note: T021 generates inline, this is for general use)
- [ ] T022a [S] [US2] Identify and list the specific autonomous agents from the original study. The task MUST explicitly define the list of agents by PARSING `docs/agent_list.md`. The `docs/agent_list.md` file MUST contain a Markdown table with columns: `Name`, `Model`, `Max_Tokens`, `Temperature`, `Description`. The list MUST be validated against the original study's documentation (citation required in the file). If the list cannot be validated or the count does not match the expected number, the system MUST abort with error. (FR-003). **Dependency**: None (but must run before T022b).
- [ ] T022b [S] [US2] Create `agents_config.yaml` defining the specific autonomous agents from the original study by PARSING `docs/agent_list.md` (generated by T022a) to extract agent names and flags. Ensure no GPU/CUDA dependencies are included. **Dependency**: T022a.
- [ ] T022 [US2] Implement `src/agents/loader.py`: Instantiate the specific autonomous agents defined in `agents_config.yaml` (created by T022b) using a factory pattern; ensure CPU-only execution via `agents/cpu_compat.py` (FR-003)
- [ ] T023a [S] [US2] Implement `src/agents/concurrency.py` with a semaphore-based concurrency controller (limit=7) and a wall-clock budget enforcement function (`run_with_budget`). This task MUST implement the logic to enforce a strict total wall-clock time budget by reading `TOTAL_WALL_CLOCK_BUDGET` from the `Config` class defined in T006. **Dependency**: T006.
- [ ] T023 [US2] Implement `src/cli/run_experiment.py` execution loop: Read 10 tasks from T008 (`data/processed/protocol_mismatch_subset.json`), load agents from T022, and execute a **comprehensive multi-agent loop** (multiple agents × 2 conditions [Zero-Shot, Scaffolded] × 10 tasks). Use `src/agents/concurrency.py` (T023a) to enforce concurrency limit of 7 and 24h budget. **CRITICAL**: This loop MUST import `Config` from `src/config.py` (T006) to enforce the budget. Do NOT use `sampling.py` or N=30 generations; strictly adhere to the 140-run experimental unit defined in FR-003. **CRITICAL**: This loop MUST check `results/audit_ids.csv` (from T014) in real-time; if a run_id is flagged as a conflict, the run MUST be immediately excluded from the results aggregation. **Dependency**: T023 MUST run after T023a, T021, T013, T014, and T006.
- [ ] T024 [US2] Implement result aggregation: Store Zero-Shot and Scaffolded scores as paired dataset entries linked by task ID in `results/paired_scores.json`. **CRITICAL**: This task MUST filter out any runs listed in `results/audit_ids.csv` (from T014) BEFORE writing the final JSON, ensuring the statistical dataset is clean. **Dependency**: T024 MUST run after T014c (Filter) and T023.
- [ ] T025 [US2] Add timeout handling: Record "Timeout" status and exclude from statistical calculation if run exceeds a predefined duration threshold
- [ ] T026 [US2] Implement logic to calculate the completion rate against the 140-run baseline. Report the pass/fail status for SC-004 (≥ 95% success rate) in `results/completion_rate_report.json`. **CRITICAL**: If the rate is < 95%, the system MUST **NOT** exit with code 1. Instead, it MUST update the project state file `state/projects/PROJ-957-llmxive-follow-up-extending-researchclaw.yaml` (set `current_stage` to `failed_sc004` or `status` to `failed`), log a critical warning, and flag the experiment as "Failed SC-004", allowing the partial data to remain for analysis. Allowed values for `current_stage`: `planned`, `tasked`, `analyzing`, `analyzed`, `failed_sc004`, `human_input_needed`.
- [ ] T021 [S] [US2] Implement `src/scoring/dummy_test.py` to validate the rubric logic (FR-008). This task MUST: 1) **Inline Generate** Set A (scaffold text, no steps) and Set B (steps, no scaffold) dummy outputs with the exact schema defined in `contracts/score_output.schema.yaml`. 2) Run the scoring engine on both. 3) Assert that Set B scores high (>= 40) and Set A scores low (< 10) as per FR-008. If assertion fails, write a report to `results/rubric_validation.json` with status "FAIL" and abort the experiment. This task is a prerequisite for T023 (Execution). **Dependency**: Must run after T010b. **Location**: Phase 4 (User Story 2) to ensure rubric is valid before execution.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Decoupling Analysis (Priority: P3)

**Goal**: Perform TOST equivalence test on "Scientific Core" and paired Wilcoxon test on "Protocol Alignment".

**Independent Test**: Feed synthetic CSV of paired scores into analysis module and verify output includes TOST p-values, effect sizes, and 95% CIs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for `src/analysis/tests.py`: Verify TOST logic with synthetic data (margin=5)
- [ ] T028 [P] [US3] Unit test for `src/analysis/tests.py`: Verify Wilcoxon test execution (pre-specified)

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `src/analysis/tests.py`: Read paired scores from `results/paired_scores.json`; perform a normality check (Shapiro-Wilk) and select either a paired t-test or Wilcoxon signed-rank test accordingly (FR-005); if power is low (<0.4), log warning but proceed with the selected test; perform TOST on "Scientific Core" scores with `MARGIN=5` from config (FR-005). **CRITICAL**: This task MUST include logic to interpret the TOST p-values (both < 0.05) and map them to the status string "safe" or "inconclusive" to be passed to the report generator.
- [ ] T030 [US3] Implement `src/analysis/report.py`: Generate JSON report at `results/statistical_report.json` with keys: `tost_p_value`, `wilcoxon_statistic`, `effect_size_cohen_d` (if t-test), `effect_size_rank_biserial` (if Wilcoxon), `mean_difference` (CALCULATED VALUE), `ci_95_lower` (mean difference), `ci_95_upper` (mean difference), `power_estimate` (SC-003), `tost_equivalence_margin` (value=5), AND `interpreted_status` (value: "safe" or "inconclusive") to verify the "safe" status defined in SC-003 and FR-005.
- [ ] T031 [US3] Add logic to report "inconclusive" status explicitly if statistical power is insufficient (N=10)
- [ ] T033 [US3] Integrate analysis module into `src/cli/run_experiment.py` to run after all executions complete

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` covering execution flow and statistical methodology
- [ ] T035 Code cleanup and refactoring of `src/agents/` and `src/scaffolding/`
- [ ] T036 [P] Additional unit tests for edge cases (timeout, conflict detection) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure end-to-end reproducibility on CPU runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for scaffold injection logic
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for paired score data

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T007b and T008 which are sequential.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for src/scaffolding/injector.py"
Task: "Unit test for src/scaffolding/validator.py"

# Launch all models for User Story 1 together:
Task: "Implement src/scaffolding/injector.py"
Task: "Implement src/scaffolding/validator.py"
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
- [S] tasks = sequential dependencies (must complete before next)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All agent execution must be CPU-only (no CUDA/GPU) to run on GitHub Actions free tier.
- **Data Integrity**: All dataset downloads must use real URLs or `datasets.load_dataset`; no synthetic/fake data generation for input.
- **Statistical Rigor**: T029 must perform normality check and select test accordingly; low power handling is a fallback note.
- **Verified Accuracy**: T007b forms a sequential chain that blocks T008 and all subsequent tasks. T009a must also pass T007b.
- **Scope**: Strictly 140 runs (7 agents × 2 conditions × 10 tasks). No N=30 generations.
- **Execution Order**: T023 (Execution) MUST run after T008 (Data Prep), T022 (Agent Loading), T023a (Concurrency Controller), T013 (Scaffold Injection), T014 (Conflict Logic), and T006 (Config). T029 (Analysis) MUST run after T024 (Aggregation).
- **Gate Logic**: T007b forms a sequential chain that blocks T008 and all subsequent tasks. T009a must also pass T007b.
- **Audit Trails**: T014 handles "Scaffold Conflict" (FR-007); T014c handles "Real-time Exclusion" (runs BEFORE T024); T014b handles "Human Audit Sampling"; T015c handles "Failure Mode Audit" (edge case).
- **Agent List**: T022a explicitly defines the 7 agents to ensure CPU tractability.
- **Completion Rate**: T026 reports failure but does not abort the experiment, preserving data for analysis.
- **Filtering**: T014c MUST run before T024 to ensure T024 aggregates only clean data.