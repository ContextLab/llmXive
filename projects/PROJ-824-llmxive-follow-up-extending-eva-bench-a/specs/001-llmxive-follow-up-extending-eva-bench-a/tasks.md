# Tasks: llmXive follow-up: extending "EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents"

**Input**: Design documents from `/specs/001-llmxive-latency-study/`
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pydub, scipy, pandas, statsmodels, matplotlib, seaborn, requests)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/download.py` to fetch EVA-Bench dataset from HuggingFace/UCI with checksum validation
- [ ] T005 [P] Implement `data/checksums.json` generation and verification logic
- [ ] T006 [P] Setup `config.py` with paths, random seeds, and latency step constants (variable range)
- [~] T007 Create base schema validation for `contracts/dataset.schema.yaml` and `contracts/injection.schema.yaml`
- [~] T008 Configure error handling for data corruption and download failures (fail fast)
- [~] T009 [P] Setup environment configuration for CPU-only execution constraints, explicitly mandating the prohibition of model quantization and GPU acceleration in the pipeline logic (FR-006)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Latency Injection & Baseline Execution (Priority: P1) 🎯 MVP

**Goal**: Implement the ability to inject variable network latency into EVA-Bench audio streams and re-run the evaluation pipeline.

**Independent Test**: The system can be tested by taking a single EVA-Bench scenario, injecting a fixed delay, re-running the pipeline, and verifying that the output log contains a modified inter-turn gap consistent with the injected delay while the original acoustic content remains unchanged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Unit test for silence insertion logic in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/test_injection.py` <!-- FAILED: unspecified -->
- [~] T011 [P] [US1] Integration test for pipeline execution on modified audio in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/test_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `latency_injector.py` in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/processing/` using `pydub` to insert silence at turn boundaries
- [ ] T013 [US1] Implement `pipeline_runner.py` in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/processing/` to re-execute EVA-Bench scoring on modified audio
- [ ] T014 [US1] Add validation in `latency_injector.py` to ensure original speech content is bit-identical (hash check) (Part 1 of SC-001)
- [ ] T015 [US1] Add validation in `latency_injector.py` to measure the injected silence duration against the ±10ms tolerance threshold (Part 2 of SC-001)
- [ ] T016 [US1] Implement batch processing loop for a **smoke test** on a **10-scenario subset** with the full latency sweep (200ms-2000ms) and verify CPU tractability < 360s (US-1 Acceptance 3)
- [ ] T017 [US1] Implement batch processing loop for the **full dataset** (213 scenarios) with the full latency sweep (200ms-2000ms) and verify CPU tractability < 6 hours (FR-007, SC-004)
- [ ] T018 [US1] Add logging for injected delays and pipeline execution status

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Threshold Detection & Non-Linear Analysis (Priority: P2)

**Goal**: Execute evaluation across latency increments and perform piecewise regression to identify non-linear failure thresholds.

**Independent Test**: The system can be tested by running the full sweep on a subset of 5 scenarios, extracting the "Conversation Progression" scores, and verifying that a piecewise regression model is fitted and an inflection point is reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for piecewise regression fitting in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/test_stats_models.py`
- [ ] T020 [P] [US2] Integration test for full latency sweep analysis in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/test_analysis.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `stats_models.py` in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/analysis/` for repeated-measures ANOVA (FR-003)
- [ ] T022 [US2] Implement piecewise regression logic in `stats_models.py` to detect inflection points in "Conversation Progression" scores (FR-004)
- [ ] T023 [US2] Implement logic to flag score drops ≥ 15% between adjacent latency steps
- [ ] T024 [US2] Implement fallback to linear regression if piecewise model fails to converge; explicitly calculate and report the confidence interval for the "No distinct threshold detected" status (SC-002)
- [ ] T025 [US2] Implement sensitivity analysis: sweep decision cutoff ±50ms around identified threshold and generate `results/sensitivity_analysis.csv` and `results/sensitivity_plot.png` (SC-005)
- [ ] T026 [US2] Ensure full analysis completes within 45 minutes on CPU (optimize batch sizes if needed)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Robustness Reporting (Priority: P3)

**Goal**: Generate a comparative report contrasting latency degradation against acoustic noise baseline.

**Independent Test**: The system can be tested by generating a CSV or JSON report that includes columns for "Latency Condition," "Turn-Taking Score," and "Acoustic Baseline Score," verifying that the comparison logic correctly aligns the metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for comparative report format in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/contract/test_report.py`
- [ ] T028 [P] [US3] Integration test for AUC calculation and ANOVA interaction test in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/integration/test_comparison.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `comparison.py` in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/analysis/` to re-run the original EVA-Bench pipeline on the **identical scenario subset** used in the latency sweep (US1/US2) with acoustic perturbations to generate the acoustic baseline artifact (FR-005)
- [ ] T030 [US3] Implement normalized degradation curve generation (score vs. delay) and (score vs. SNR) using the generated baseline
- [ ] T031 [US3] Implement Area Under the Curve (AUC) calculation for both curves and difference reporting
- [ ] T032 [US3] Perform statistical comparison (interaction test or t-test) between the latency failure point and the acoustic noise failure point to validate distinctness (FR-008)
- [ ] T033 [US3] Generate final report with explicit "Distinct Failure Mode" conclusion based on the specific interaction test or t-test results (SC-003)
- [ ] T034 [US3] Visualize degradation curves using `matplotlib`/`seaborn` for final paper inclusion

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T036 Code cleanup and refactoring for CPU memory optimization (streaming audio)
- [ ] T037 Benchmark full pipeline execution time on a standard CPU runner to verify completion within 6 hours (SC-004, FR-007)
- [ ] T038 [P] Additional unit tests for edge cases (masked delays, corrupted files) in `tests/unit/`
- [ ] T039 Run quickstart.md validation and verify all acceptance criteria pass

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation (latency sweep results)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (latency results), US2 (thresholds), and the generation of the acoustic baseline (T029)

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
Task: "Unit test for silence insertion logic in tests/test_injection.py"
Task: "Integration test for pipeline execution on modified audio in tests/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement latency_injector.py in processing/latency_injector.py"
Task: "Implement pipeline_runner.py in processing/pipeline_runner.py"
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
- **Constraint**: All tasks must run on CPU-only CI (no CUDA/GPU, no 8-bit quantization)