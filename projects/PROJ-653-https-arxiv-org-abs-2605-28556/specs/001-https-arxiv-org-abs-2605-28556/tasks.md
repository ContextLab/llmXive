# Tasks: A Matter of TASTE: Improving Coverage and Difficulty of Agent Benchmarks

**Input**: Design documents from `/specs/653-taste-benchmark-reproduction/`
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

- [X] T001 Create project structure: `mkdir -p src/taste_pipeline src/cli src/utils tests/contract tests/integration tests/unit artifacts/domains/airline artifacts/baselines artifacts/task_sets artifacts/reports contracts`
- [X] T002 Initialize Python 3.10 project with `pyproject.toml` dependencies: `numpy>=1.24,<2.0`, `scikit-learn>=1.3`, `pydantic>=2.0`, `pandas>=2.0`, `transformers[torch]>=4.30` (CPU only), `pytest>=7.0`, `ruff>=0.1.0`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/utils/config.py` to load `tool_spec.json` and verify tool existence in validators (FR-006)
- [X] T005 Implement `src/utils/entropy.py` for Shannon entropy calculation and mode collapse detection (SC-003)
- [X] T006 [P] Generate synthetic baseline (Fallback Strategy): Create `contracts/baseline.schema.yaml` and implement `src/utils/baseline.py` to generate randomized tool sequences preserving length distribution from `pre_seed.json` if `artifacts/baselines/t2_bench_airline.json` is missing
- [X] T007 Create `contracts/task.schema.yaml`, `contracts/domain_config.schema.yaml`, and `contracts/validation_report.schema.yaml` (FR-004, FR-005)
- [X] T008 Implement `src/cli/main.py` entry point with graceful exit on missing env vars (FR-006)
- [X] T009 Setup `artifacts/domains/airline/` with `tool_spec.json`, `pre_seed.json`, `post_seed.json` placeholders

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute TASTE Pipeline End-to-End (Priority: P1) 🎯 MVP

**Goal**: Successfully execute the vendored TASTE pipeline (Stage 1: N-gram, Stage 2: Clustering, Stage 3: Synthesis) on the `airline` domain.

**Independent Test**: Run `python -m src.cli.main --domain airline`; verify `artifacts/task_sets/tasks.json` exists with ≥10 valid tasks.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for `tasks.json` schema: `tests/contract/test_task_schema.py` (Cases: `test_missing_scenario_field`, `test_invalid_tool_sequence`, `test_valid_task_structure`)
- [X] T011 [P] [US1] Integration test for pipeline execution: `tests/integration/test_pipeline_airline.py` (Cases: `test_end_to_end_airline`, `test_checkpoint_creation`)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `src/taste_pipeline/stage1_ngram.py`: Load seeds, compute n-gram probabilities, sample sequences (FR-001)
- [X] T013 [US1] Add entropy check in `stage1_ngram.py` to detect mode collapse: If entropy < 0.5, increase temperature by 0.1 and re-sample (Edge Case 1)
- [X] T014 [P] [US1] Implement `src/taste_pipeline/stage2_clustering.py`: Cluster sequences, select ≥5 medoids (FR-002)
- [X] T015 [US1] Implement `src/taste_pipeline/stage3_synthesis.py`: Generate natural language scenarios for medoids (FR-004)
- [X] T016 [US1] Integrate `stage1` → `stage2` → `stage3` in `src/cli/main.py` with checkpoint saving
- [X] T017 [US1] Add logging for pipeline stages and entropy metrics (SC-003)
- [X] T021 [US1] Implement retry logic (with a configurable maximum number of attempts) in `stage3_synthesis.py` for validation failures: If validation fails, re-sample with increased temperature

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Task Coherence and Tool Usage (Priority: P2)

**Goal**: Validate that synthesized tasks are coherent and tool sequences are valid per domain validators.

**Independent Test**: Run `src/taste_pipeline/validators/airline.py` against generated tasks; validation rate ≥ 80% (SC-001).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for validation report schema: `tests/contract/test_validation_report_schema.py` (Cases: `test_missing_validation_rate`, `test_invalid_report_structure`)
- [X] T019 [P] [US2] Integration test for validator coherence: `tests/integration/test_validator_coherence.py` (Cases: `test_airline_validator_valid`, `test_airline_validator_invalid`)

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `src/taste_pipeline/validators/airline.py`: Logic to verify scenario vs. action_sequence coherence (FR-003)
- [X] T022 [US2] Implement `src/taste_pipeline/evaluation/validator_wrapper.py` to batch validate tasks and generate report (FR-005)
- [X] T023 [US2] Update `tasks.json` generation to include `validation_status` and `validation_reason` fields (FR-004)
- [X] T024 [US2] Add logic to filter out invalid tasks and re-sample until ≥80% validity or max retries (5) (SC-001)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Difficulty Drop Claim (Priority: P3)

**Goal**: Execute Multi-Heuristic Ensemble evaluation to demonstrate difficulty drop vs. baseline.

**Independent Test**: Run `src/taste_pipeline/evaluation/ensemble_agent.py`; verify success rate drop ≥ 30pp, p < 0.05, and Cohen's d > 0.5 (SC-005).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for evaluation results: `tests/contract/test_evaluation_results.py` (Cases: `test_missing_difficulty_metric`, `test_invalid_p_value`)
- [X] T026 [P] [US3] Integration test for difficulty comparison: `tests/integration/test_difficulty_comparison.py` (Cases: `test_baseline_vs_taste_diff`, `test_statistical_significance`)

### Implementation for User Story 3

- [X] T028 [US3] Implement `src/taste_pipeline/evaluation/proxy_calibration.py`: Load `artifacts/baselines/failure_cases.json` (a set of hand-crafted LLM failure examples), calibrate ensemble scores against known labels, verify Pearson correlation > 0.6
- [X] T027 [P] [US3] Implement `src/taste_pipeline/evaluation/ensemble_agent.py`: Regex, Exact Match, CPU-only DistilBERT (transformers with torch CPU) heuristics
- [X] T029 [US3] Implement `src/taste_pipeline/evaluation/statistical_analysis.py`: Calculate success rate drop (must be ≥ 30 percentage points), Permutation Test (p < 0.05), and Cohen's d (effect size > 0.5)
- [X] T030 [US3] Implement `src/taste_pipeline/evaluation/baseline_runner.py`: Check for `artifacts/baselines/t2_bench_airline.json`; if missing, trigger fallback from T006; run ensemble on both baseline and TASTE tasks (consumes `artifacts/task_sets/tasks.json` from T016)
- [X] T031 [US3] Generate `artifacts/reports/difficulty_report.json` comparing TASTE vs. Baseline success rates (SC-002, SC-005)
- [X] T032 [US3] Add tool coverage analysis to report (≥2.0x unique combinations) (SC-002)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `research.md`, `quickstart.md` with reproduction steps
- [X] T034 Code cleanup and refactoring of pipeline stages
- [X] T035 [P] Performance optimization: Implement caching for N-gram lookups and parallelize clustering using joblib; verify runtime ≤ 6h via benchmark script
- [X] T036 [P] Additional unit tests for N-gram and clustering in `tests/unit/`
- [X] T037 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T015 (Synthesis) output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T022 (Validation) and T016 (Synthesis) output

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
Task: "Contract test for tasks.json schema in tests/contract/test_task_schema.py"
Task: "Integration test for pipeline execution in tests/integration/test_pipeline_airline.py"

# Launch all models for User Story 1 together:
Task: "Implement stage1_ngram.py in src/taste_pipeline/stage1_ngram.py"
Task: "Implement stage2_clustering.py in src/taste_pipeline/stage2_clustering.py"
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
- **Feasibility Check**: All tasks use CPU-only libraries (scikit-learn, DistilBERT CPU); no GPU or 8-bit quantization used.
- **Data Integrity**: No fake data generation; `baseline.py` generates synthetic baselines only if real `τ²-Bench` is missing, but TASTE tasks use real seed data.