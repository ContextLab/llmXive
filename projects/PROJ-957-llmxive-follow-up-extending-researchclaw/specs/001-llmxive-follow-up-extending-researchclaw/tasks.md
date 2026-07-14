# Tasks: llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

**Input**: Design documents from `/specs/001-llmxive-scaffold-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with dependencies: `pandas`, `scipy`, `pytest`, `pyyaml`, `jsonschema`, `datasets`, `tqdm`, `numpy`, `statsmodels`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `src/utils/checksum.py` for SHA256 verification of data artifacts
- [ ] T005 [P] Implement `src/utils/logging.py` with structured JSON logging and error tracking
- [ ] T006 [P] Implement `src/utils/config.py` for loading experiment parameters, timeout limits, and constants including `RESEARCHCLAWBENCH_DATASET_ID`, `SCIENTIFIC_CORE_MARGIN=5`, and `MAX_CONCURRENCY=7` (specifically for the TOST equivalence test on "Scientific Core" scores as required by FR-005)
- [ ] T007 [P] Create `src/data/loader.py` with ResearchClawBench fetch logic using `datasets.load_dataset` or canonical URL; use `RESEARCHCLAWBENCH_DATASET_ID` from config; include checksum verification against `data/raw/`; if ID is placeholder or checksum fails, ABORT with error (no mock data). **Output**: Write checksum to `data/raw/checksum.txt`.
- [ ] T007b [S] Implement "Verified Accuracy" Gate Logic: Read the checksum file at `data/raw/checksum.txt` (produced by T007). Verify the hash matches the expected value defined in `config.py`. If mismatch, trigger T007e (Exit). If match, trigger T007c (Log) and T007d (Write). This task is the entry point for the gate sequence. **Trigger**: Must run after T007 completes successfully.
- [ ] T007c [S] Implement Gate Logging: Write the specific message "GATE: Verified Accuracy [PASS]" or "GATE: Verified Accuracy [FAIL]" to `results/verified_accuracy_gate.log` (UTF-8). This task runs only after T007b passes.
- [ ] T007d [S] Implement Gate File Write: Create or update a marker file `results/verified_accuracy_gate.done` to signal successful gate passage. This task runs only after T007c.
- [ ] T007e [S] Implement Gate Exit Handler: Exit the process with code 1 if T007b detected a mismatch. This task runs only if T007b fails.
- [ ] T008 [S] Create `src/data/filter.py` to implement the specific logic to SELECT exactly 10 tasks from the ResearchClawBench dataset where the metadata field `failure_mode` equals "experimental protocol mismatch". WRITE the resulting subset to `data/processed/protocol_mismatch_subset.json`. Include a verification step to check if `failure_mode` key exists in the dataset schema before filtering; if missing, log an error and abort (FR-001, FR-006). **Dependency**: This task requires T007e to NOT have been triggered (i.e., gate passed). **Output**: `data/processed/protocol_mismatch_subset.json` with SHA256 checksum.
- [ ] T009 [P] Create `assets/templates/` directory; implement `src/scaffolding/template_loader.py` to load `template_map.json` (mapping multiple task IDs to template filenames); create `TEMPLATE-001-v1.0.md` by fetching content from the verified open-access manual URL: ` (Note: This URL is used as a placeholder for the specific template source; replace with the actual ResearchClawBench template URL if different, but for this task, use the provided URL as the canonical source) and save the content to `assets/templates/TEMPLATE-001-v1.0.md` with UTF-8 encoding; if URL is unavailable or fetch fails, ABORT with error (no placeholders).
- [ ] T009b [P] Implement logic to generate and populate `assets/templates/template_map.json` with the explicit mapping of the 10 selected task IDs (from T008) to their specific template IDs (e.g., `{"task_001": "TEMPLATE-001-v1.0", "task_002": "TEMPLATE-001-v1.0"}`). This file MUST exist and be valid JSON before T015b runs.
- [ ] T009c [P] Create `assets/templates/constraint_keywords.yaml` containing the explicit list of keywords used for "Scaffold Conflict" detection (FR-007); implement `src/scaffolding/validator.py` to load this file
- [ ] T010a [P] Create `contracts/rubric_schema.json` defining the JSON structure for "Protocol Alignment" (0-50) and "Scientific Core" scoring logic. The scoring algorithm MUST be a weighted sum of specific criteria: `{"criteria": [{"key": "step_1", "weight": 0.4}, {"key": "step_2", "weight": 0.6}]}`. Define these specific keys and weights in the task description or the file content; include `constraint_keywords` list reference for FR-007.
- [ ] T010b [P] Implement `src/scoring/rubric_engine.py` to load `contracts/rubric_schema.json` and implement the logic to calculate scores based on the schema definitions (weighted sum of criteria)
- [ ] T021 [S] [US2] Implement `src/scoring/dummy_test.py` to validate the rubric logic (FR-008). This task MUST: 1) Generate Set A (scaffold text, no steps) and Set B (steps, no scaffold) dummy outputs; 2) Run the scoring engine on both; 3) Assert that Set B scores high (>= 40) and Set A scores low (< 10) as per FR-008. If assertion fails, write a report to `results/rubric_validation.json` with status "FAIL" and abort the experiment. This task is a prerequisite for T023 (Execution). **Dependency**: Must run after T010b. **Location**: Phase 2 (Foundational) to ensure rubric is valid before execution.

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
- [ ] T014 [US1] Implement `src/scaffolding/validator.py`: Check task metadata vs `assets/templates/constraint_keywords.yaml` (loaded by T009c); log "Scaffold Conflict" and exclude run if mismatch (FR-007). **CRITICAL**: If a conflict is detected, the system MUST write the specific run ID to `results/audit_ids.csv` with the schema `run_id,task_id,conflict_reason,timestamp` (UTF-8 encoding, comma delimiter) and flag the run for a mandatory human expert audit as required by FR-007. The file MUST be created if it doesn't exist.
- [ ] T015b [US1] Implement `src/data/loader.py` extension to load the filtered set (T008 output), bind them to their corresponding templates via `template_map.json` (generated by T009b), write the resulting 10-task subset to `data/processed/protocol_mismatch_subset.json`, calculate and store the SHA256 checksum of this file (FR-001, Constitution Principle III). **Dependency**: This task MUST wait for T007e (Verified Accuracy gate) to pass successfully. The JSON structure MUST be `{"tasks": [{"task_id": "...", "template_id": "..."}]}`.
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

- [ ] T020b [US2] Implement `src/scoring/dummy_generator.py` to generate Set A (scaffold text, no steps) and Set B (steps, no scaffold) dummy outputs; write to `results/dummy_outputs.json` for FR-008 validation
- [ ] T022a [P] [US2] Identify and list the specific autonomous agents from the original study (e.g., "Agent-Alpha", "Agent-Beta", etc.) and their CPU-compatible configuration parameters. Document this list in `docs/agent_list.md` as a Markdown table with columns: `Agent Name`, `CPU Config`, `Memory Limit`.
- [ ] T022b [P] [US2] Create `agents_config.yaml` defining the specific autonomous agents from the original study by PARSING `docs/agent_list.md` (generated by T022a) to extract agent names and flags. Ensure no GPU/CUDA dependencies are included.
- [ ] T022 [US2] Implement `src/agents/loader.py`: Instantiate the specific autonomous agents defined in `agents_config.yaml` (created by T022b) using a factory pattern; ensure CPU-only execution via `agents/cpu_compat.py` (FR-003)
- [ ] T023a [S] [US2] Implement `src/agents/concurrency.py` with a semaphore-based concurrency controller (limit=7) and a wall-clock budget enforcement function (`run_with_budget`). This task MUST implement the logic to enforce a strict total wall-clock time budget and a timeout per run.
- [ ] T023 [US2] Implement `src/cli/run_experiment.py` execution loop: Read 10 tasks from T015b (`data/processed/protocol_mismatch_subset.json`), load agents from T022, and execute a **comprehensive multi-agent loop** (multiple agents × 2 conditions [Zero-Shot, Scaffolded] × 10 tasks). Use `src/agents/concurrency.py` (Ta) to enforce concurrency limit of 7 and 24h budget. Do NOT use `sampling.py` or N=30 generations; strictly adhere to the 140-run experimental unit defined in FR-003. **Dependency**: T023 MUST run after T023a and T021.
- [ ] T024 [US2] Implement result aggregation: Store Zero-Shot and Scaffolded scores as paired dataset entries linked by task ID in `results/paired_scores.json`
- [ ] T025 [US2] Add timeout handling: Record "Timeout" status and exclude from statistical calculation if run exceeds a predefined duration threshold
- [ ] T026 [US2] Implement logic to calculate the completion rate against the 140-run baseline. Report the pass/fail status for SC-004 (≥ 95% success rate) in `results/completion_rate_report.json`. **CRITICAL**: If the rate is < 95%, the system MUST exit with code 1 and update the project state file `state/projects/PROJ-957-llmxive-follow-up-extending-researchclaw.yaml` (set `current_stage` to `failed_sc004` or `status` to `failed`). Log a critical warning and flag the experiment as "Failed SC-004".

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
- [ ] T030 [US3] Implement `src/analysis/report.py`: Generate JSON report with keys: `tost_p_value`, `wilcoxon_statistic`, `effect_size_cohen_d` (if t-test), `effect_size_rank_biserial` (if Wilcoxon), `ci_95_lower` (mean difference), `ci_95_upper` (mean difference), `power_estimate` (SC-003), `tost_equivalence_margin` (value=5), AND `interpreted_status` (value: "safe" or "inconclusive") to verify the "safe" status defined in SC-003 and FR-005.
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T007b-T007e which are sequential.
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
- **Verified Accuracy**: T007-T007e must abort if data/templates cannot be verified; no placeholders allowed.
- **Scope**: Strictly 140 runs (7 agents × 2 conditions × 10 tasks). No N=30 generations.
- **Execution Order**: T023 (Execution) MUST run after T015b (Data Prep), T022 (Agent Loading), and T023a (Concurrency Controller). T029 (Analysis) MUST run after T024 (Aggregation).
- **Gate Logic**: T007b-T007e form a sequential chain that blocks T008 and all subsequent tasks.
- **Audit Trails**: T014 handles "Scaffold Conflict" (FR-007); T015c handles "Failure Mode Audit" (edge case).