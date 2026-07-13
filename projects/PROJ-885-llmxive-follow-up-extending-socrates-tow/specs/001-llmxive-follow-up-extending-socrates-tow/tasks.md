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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-885-llmxive-follow-up-extending-socrates-tow/`)
- [ ] T002 Initialize Python 3.11 project with `scikit-learn`, `pandas`, `transformers` (CPU-only), `datasets`, `pytest` dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config.py` with pinned random seeds, file paths (`data/raw`, `data/processed`, `data/results`), and hyperparameters
- [ ] T005 [P] Implement data validation utilities in `code/data/loader.py` to enforce schema compliance for generated trajectories
- [ ] T006 [P] Setup logging infrastructure in `code/config.py` to track experiment conditions (Adapter vs. Static) and skipped samples
- [ ] T007 Create base entities: `ConflictTrajectory` and `SocioCognitiveState` dataclasses in `code/models/entities.py`
- [ ] T008 [P] Implement retry mechanism with exponential backoff for API/local inference failures in `code/experiments/retry_utils.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Conflict Trajectories with Targeted Oversampling (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic conflict dialogue trajectories using the SoCRATES pipeline, specifically oversampling scenarios with "high emotional reactivity" and "diverse cultural identity" attributes.

**Independent Test**: Run the data generation script and verify the output JSON summary shows >40% of samples in the target categories, with memory <7GB and runtime <30m.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for trajectory schema in `tests/contract/test_trajectory_schema.py`
- [ ] T011 [P] [US1] Integration test for oversampling distribution in `tests/integration/test_oversampling.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/data/generator.py` to generate conflict trajectories with metadata tags (emotional reactivity, cultural identity)
- [ ] T013 [US1] Implement oversampling logic in `code/data/generator.py` to ensure ≥40% of trajectories fall into "high emotional reactivity" or "diverse cultural identity" categories
- [ ] T014 [US1] Implement `code/data/generator.py` output writer to save trajectories to `data/processed/trajectories.json` and a summary report to `data/processed/generation_stats.json`
- [ ] T015 [US1] Add validation in `code/data/generator.py` to verify generated data meets the 40% threshold before writing
- [ ] T016 [US1] Add logging for generation parameters and final distribution counts
- [ ] T019 [US1] Generate training dataset for classifier in `code/data/generator.py` using ONLY scenario metadata tags (emotional reactivity, cultural identity) distinct from consensus-gap evaluation metrics, saving to `data/processed/classifier_training_data.json` to ensure independence (FR-002)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Paired Mediation Experiments (Adapter vs. Static) (Priority: P2)

**Goal**: Run conflict trajectories through eight distinct LLMs under two conditions: (A) with dynamic socio-cognitive state adapter, (B) with static baseline prompt, ensuring CPU-only execution.

**Independent Test**: Run experiment script for one LLM and subset of trajectories, verifying "Adapter" logs contain injected state signals (e.g., "de-escalate") while "Static" logs do not.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for prompt injection in `tests/contract/test_prompt_injection.py`
- [ ] T022 [P] [US2] Integration test for paired experiment execution in `tests/integration/test_experiment_runner.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/models/classifier.py` with a lightweight logistic regression classifier trained on `data/processed/classifier_training_data.json` (metadata tags only) to infer socio-cognitive states, ensuring no overlap with evaluation metrics (FR-002)
- [ ] T023 [P] [US2] Implement `code/experiments/prompts.py` with templates for Static baseline and Dynamic Adapter (injecting state instructions like "validate cultural norms", "de-escalate")
- [ ] T024 [US2] Implement `code/experiments/runner.py` to load trajectories, run the classifier every N turns, and inject dynamic prompts for the Adapter condition
- [ ] T025 [US2] Implement `code/experiments/runner.py` to run the Static condition (no injection) for the same trajectories
- [ ] T026 [US2] Integrate retry logic from `code/experiments/retry_utils.py` to handle timeouts/crashes, logging skipped samples
- [ ] T027 [US2] Implement CPU-only inference loop in `code/experiments/runner.py` using `transformers` with `device="cpu"`, explicitly excluding bitsandbytes/quantization libraries, and implementing fallback logic to inject "neutral monitoring state" on low confidence (FR-002)
- [ ] T028 [US2] Save experiment logs to `data/processed/experiment_logs.json` containing trajectory ID, condition (Adapter/Static), injected state (if any), and LLM output
- [ ] T029 [US2] Add validation to ensure the classifier fails gracefully to a neutral "monitoring" state on low confidence (Edge Case FR-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compute Consensus Gap Closure and Statistical Significance (Priority: P3)

**Goal**: Calculate "consensus gap closure" metric using the topic-localized evaluator and perform statistical comparison (paired t-test or Wilcoxon) between Adapter and Static conditions.

**Independent Test**: Provide pre-computed CSV of gap scores and verify script outputs correct t-statistic, p-value, and Cohen's d.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for statistical report schema in `tests/contract/test_stats_report.py`
- [ ] T032 [P] [US3] Integration test for normality and significance testing in `tests/integration/test_statistical_analysis.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement `code/models/evaluator.py` (topic-localized evaluator) to calculate "consensus gap" scores for LLM outputs against ideal resolution (independent of state labels)
- [ ] T034 [US3] Implement `code/analysis/metrics.py` to compute consensus gap closure for every trajectory in `data/processed/experiment_logs.json`
- [ ] T038 [US3] Implement `code/analysis/stats.py` to perform conditional statistical workflow: (1) Shapiro-Wilk normality test on difference scores, (2) if normal (p>=0.05) run paired t-test, else run Wilcoxon signed-rank test, (3) apply Holm-Bonferroni correction for multiple comparisons across 8 LLMs, and (4) generate final report with t-statistic, p-value, Cohen's d, and `is_significant` flag
- [ ] T039 [US3] Implement sensitivity analysis script in `code/analysis/sensitivity.py` to sweep classifier confidence thresholds and report variation in injected directives (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `specs/001-dynamic-state-injection/quickstart.md`
- [ ] T041 Code cleanup and refactoring to ensure CPU memory usage stays <7GB
- [ ] T042 [P] Implement performance monitoring and batching logic in `code/experiments/runner.py` to ensure throughput ≥40 trajectories/hour and latency ≤45s per trajectory (SC-003)
- [ ] T043 [P] Additional unit tests in `tests/unit/` for classifier and evaluator logic
- [ ] T044 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for trajectory schema in tests/contract/test_trajectory_schema.py"
Task: "Integration test for oversampling distribution in tests/integration/test_oversampling.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/generator.py to generate conflict trajectories"
Task: "Implement code/data/generator.py output writer"
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
- **Critical Constraint**: All LLM inference MUST run on CPU only (no CUDA, no bitsandbytes, no aggressive quantization). If a model exceeds available system memory, exclude it.
- **Critical Constraint**: All data must be real/generated locally; no fake/synthetic input data for final results.