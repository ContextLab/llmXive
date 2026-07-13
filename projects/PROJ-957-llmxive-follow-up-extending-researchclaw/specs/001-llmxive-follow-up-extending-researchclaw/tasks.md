# Tasks: llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

**Input**: Design documents from `/specs/001-llmxive-scaffold-analysis/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with dependencies: `pandas`, `scipy`, `pytest`, `pyyaml`, `jsonschema`, `datasets`, `tqdm`, `numpy`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `src/utils/checksum.py` for SHA256 verification of data artifacts
- [ ] T005 [P] Implement `src/utils/logging.py` with structured JSON logging and error tracking
- [ ] T006 [P] Implement `src/utils/config.py` for loading experiment parameters, timeout limits (extended duration/run), and constants including `RESEARCHCLAWBENCH_DATASET_ID` and `SCIENTIFIC_CORE_MARGIN=5`
- [ ] T007 [P] Create `src/data/loader.py` with ResearchClawBench fetch logic using `datasets.load_dataset` or canonical URL; use `RESEARCHCLAWBENCH_DATASET_ID` from config; include checksum verification against `data/raw/`; if ID is placeholder or checksum fails, ABORT with error (no mock data)
- [ ] T007b [P] Implement logic in `src/data/loader.py` or a dedicated gate script to explicitly log the "Verified Accuracy" status as a blocking gate in the CI pipeline based on the checksum verification result
- [ ] T008 [P] Create `src/data/filter.py` to implement a generic filter function that accepts a dataset and a metadata key/value pair, returning a subset (no specific task selection logic here)
- [ ] T009 Create `assets/templates/` directory; implement `src/scaffolding/template_loader.py` to load `template_map.json` (mapping multiple task IDs to template filenames); create `TEMPLATE-001-v1.0.md` by fetching content from the specific open-access manual URL `https://www.openlabmanuals.org/protocols/standard_purification_v1.txt`; if URL is unavailable or fetch fails, ABORT with error (no placeholders)
- [ ] T009c [P] Create `assets/templates/constraint_keywords.yaml` containing the explicit list of keywords used for "Scaffold Conflict" detection (FR-007); implement `src/scaffolding/validator.py` to load this file
- [ ] T010a [P] Create `contracts/rubric_schema.json` defining the JSON structure for "Protocol Alignment" (0-50) and "Scientific Core" scoring logic; the scoring algorithm MUST be a weighted sum of specific criteria (e.g., `{"criteria": ["step_1", "step_2"], "weights": [0.5, 0.5]}`); define these specific keys and weights in the task description or the file content; include `constraint_keywords` list reference for FR-007
- [ ] T010b [P] Implement `src/scoring/rubric_engine.py` to load `contracts/rubric_schema.json` and implement the logic to calculate scores based on the schema definitions (weighted sum of criteria)
- [ ] T032 [P] [US3] Implement `src/analysis/sampling.py`: Logic for generating Multiple independent generations per task (N=30 defined as 3 generations × 10 tasks) and aggregation logic (average of scores) to mitigate low power (Plan: Statistical Rigor)

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
- [ ] T014 [US1] Implement `src/scaffolding/validator.py`: Check task metadata vs `assets/templates/constraint_keywords.yaml` (loaded by T009c); log "Scaffold Conflict" and exclude run if mismatch (FR-007)
- [ ] T015a [P] [US1] Implement `src/data/filter.py` extension to select tasks based on `failure_mode` metadata key with value `experimental protocol mismatch`; include a verification step to check if `failure_mode` key exists in the dataset schema before filtering, logging an error if missing
- [ ] T015b [US1] Implement `src/data/loader.py` extension to load the filtered set (T015a output), bind them to their corresponding templates via `template_map.json`, write the resulting 10-task subset to `data/processed/10_tasks_protocol_mismatch.json`, calculate and store the SHA256 checksum of this file (FR-001, Constitution Principle III)
- [ ] T015c [US1] Implement logic to write the failure mode audit report to `results/failure_mode_audit.csv` if the dominant mode differs from the expected mode (`experimental protocol mismatch`) or if the count of expected mode is < 10 (FR-001)
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
- [ ] T021 [US2] Implement `src/scoring/engine.py`: Load `rubric_schema.json` and validate against `results/dummy_outputs.json` (generated by T020b); then extract "Protocol Alignment" and "Scientific Core" scores for real runs (FR-004)
- [ ] T022 [US2] Implement `src/agents/loader.py`: Instantiate the specific autonomous agents defined in `agents_config.yaml` (created by T022b) using a factory pattern; ensure CPU-only execution via `agents/cpu_compat.py` (FR-003)
- [ ] T022b [P] [US2] Create `agents_config.yaml` defining the specific autonomous agents from the original study with their CPU-compatible configuration parameters (list of agent names, CPU-compatible flags)
- [ ] T023 [US2] Implement `src/cli/run_experiment.py` execution loop: Read 10 tasks from T015b (`data/processed/10_tasks_protocol_mismatch.json`), load agents from T022, run a multiple-agent setup across multiple conditions and tasks with a strict 24-hour wall-clock budget enforcement logic, a concurrency limit of 7, and utilize `src/analysis/sampling.py` (T032) for N=30 generation logic (FR-003)
- [ ] T024 [US2] Implement result aggregation: Store Zero-Shot and Scaffolded scores as paired dataset entries linked by task ID in `results/paired_scores.json`
- [ ] T025 [US2] Add timeout handling: Record "Timeout" status and exclude from statistical calculation if run exceeds 6h

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Decoupling Analysis (Priority: P3)

**Goal**: Perform TOST equivalence test on "Scientific Core" and paired Wilcoxon test on "Protocol Alignment".

**Independent Test**: Feed synthetic CSV of paired scores into analysis module and verify output includes TOST p-values, effect sizes, and 95% CIs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for `src/analysis/tests.py`: Verify TOST logic with synthetic data (margin=5)
- [ ] T028 [P] [US3] Unit test for `src/analysis/tests.py`: Verify Wilcoxon test execution (pre-specified)

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `src/analysis/tests.py`: Read paired scores from `results/paired_scores.json`; perform a normality check (Shapiro-Wilk) and select either a paired t-test or Wilcoxon signed-rank test accordingly (FR-005); if power is low (<0.4), log warning but proceed with the selected test; perform TOST on "Scientific Core" scores with `MARGIN=5` from config (FR-005)
- [ ] T030 [US3] Implement `src/analysis/report.py`: Generate JSON report with keys: `tost_p_value`, `wilcoxon_statistic`, `effect_size_cohen_d` (if t-test), `effect_size_rank_biserial` (if Wilcoxon), `ci_95_lower` (mean difference), `ci_95_upper` (mean difference), `power_estimate` (SC-003)
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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All agent execution must be CPU-only (no CUDA/GPU) to run on GitHub Actions free tier.
- **Data Integrity**: All dataset downloads must use real URLs or `datasets.load_dataset`; no synthetic/fake data generation for input.
- **Statistical Rigor**: T029 must perform normality check and select test accordingly; low power handling is a fallback note.
- **Verified Accuracy**: T007 and T009 must abort if data/templates cannot be verified; no placeholders allowed.