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

- [X] T001 Create project structure per implementation plan by executing: `mkdir -p projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/{data/{raw,processed},code/{injectors,evaluation,analysis,synthetic},tests/{unit,integration},specs/001-gene-regulation}` <!-- FAILED: unspecified -->
- [ ] T002 {{claim:c_c938ab6b}}
- [X] T003a [P] Configure Black formatting by creating `pyproject.toml` with `tool.black` section (line-length=88, target-version=['py311']).
- [X] T003b [P] Configure Flake8 linting by creating `.flake8` with strict rules (max-line-length=88, exclude=venv).
- [X] T003c [P] Configure import sorting by adding `tool.isort` to `pyproject.toml` (profile=black).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create directory structure: `data/raw/`, `data/processed/`, `code/`, `tests/`, `specs/`
- [~] T005 [P] Implement `code/config.py` for path configuration, random seeds, and hyperparameters (200ms-2000ms bounds)
- [~] T006 [P] Setup logging infrastructure with file handlers and warning filters for edge cases
- [~] T007 [P] Implement `code/synthetic/tts_engine.py` (FR-011) as a fallback for missing EVA-Bench audio using Coqui TTS with known characteristics; simultaneously document 'known characteristics' (model version, prosody settings, seed) in `docs/tts_characteristics.md` to satisfy FR-011 reproducibility constraints; Output: `code/synthetic/tts_engine.py` and `docs/tts_characteristics.md`
- [~] T008 Create `data/checksums.json` schema and initialization script; schema must be `{"files": [{"path": "string", "sha256": "string"}]}`; script must initialize empty `{"files": []}`; Output: `data/checksums.json`
- [~] T009 Implement `code/main.py` orchestration skeleton with argument parsing for perturbation types [UNRESOLVED-CLAIM: c_6888dec5 — status=not_enough_info]

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Latency Injection & Baseline Execution (Priority: P1) 🎯 MVP

**Goal**: Implement the ability to inject variable network latency into EVA-Bench audio streams and re-run the evaluation pipeline.

**Independent Test**: The system can be tested by taking a single EVA-Bench scenario, injecting a fixed delay, re-running the pipeline, and verifying that the output log contains a modified inter-turn gap consistent with the injected delay while the original acoustic content remains unchanged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T010 [P] [US1] Define unit test for `LatencyInjector` gap insertion logic in `tests/unit/test_latency.py` (Write code that asserts failure if class missing)
- [~] T011 [P] [US1] Define unit test for chunked processing memory limits in `tests/unit/test_latency.py`
- [~] T012 [P] [US1] Define integration test for 800ms fixed delay scenario in `tests/integration/test_latency_pipeline.py`
- [~] T013 [P] [US1] Define integration test for ±50ms jitter variability in `tests/integration/test_latency_pipeline.py`

### Implementation for User Story 1

- [~] T014 [US1] Implement `code/injectors/latency.py`: `LatencyInjector` class with `librosa.stream` for chunked I/O
- [~] T015 [US1] Implement turn-boundary detection logic in `code/injectors/latency.py`; Input: `data/processed/turn_boundaries.csv`; Algorithm: If gap overlaps audio > 10ms, shift boundary to nearest silence > 50ms [UNRESOLVED-CLAIM: c_c51f6117 — status=not_enough_info]; Output: Updated turn boundaries <!-- FAILED: unspecified -->
- [~] T016 [US1] Implement duration validation and truncation logic in `code/injectors/latency.py`; MUST enforce a strict maximum duration limit as defined in Spec Edge Cases.; truncate audio if exceeded, log warning, and record score as `null`; Output: Updated audio files and logs
- [~] T017 [US1] Create `code/injectors/__init__.py` exports
- [ ] T018 [US1] Add deterministic jitter generation using seeded `numpy.random`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Threshold Detection & Non-Linear Analysis (Priority: P2)

**Goal**: Execute evaluation across latency increments and perform piecewise regression to identify non-linear failure thresholds.

**Independent Test**: The system can be tested by running the full sweep on a subset of 5 scenarios, extracting the "Conversation Progression" scores, and verifying that a piecewise regression model is fitted and an inflection point is reported.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for piecewise regression fitting in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/test_stats_models.py`
- [ ] T020 [P] [US2] Integration test for full latency sweep analysis in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/test_analysis.py`

### Implementation for User Story 2

- [ ] T027 [US2] Implement `code/evaluation/runner.py`: Wrapper to execute original EVA-Bench scoring on perturbed files; Requires: T014-T018, T021-T024
- [ ] T028 [US2] Implement metric extraction logic for "Turn-Taking" and "Conversation Progression" sub-metrics
- [ ] T029 [US2] Implement floor-effect handling (skip delta if baseline is 0) with logging
- [ ] T029b [US2] Calculate delta (Δ) between baseline and perturbed scores for each scenario; Input: `data/processed/results.csv` containing `scenario_id` and `system_id` columns; Output: Append rows to `data/processed/results.csv` with columns `scenario_id`, `system_id`, `metric`, `baseline`, `perturbed`, `delta`; Ensures hierarchical structure for LMM; Requires: T027, T028
- [ ] T029c [US2] Calculate and aggregate system-level deltas to ensure hierarchical structure for LMM as required by FR-003; Input: `data/processed/results.csv` (output of T029b); Output: Ensure `results.csv` includes `system_id` grouping for LMM; Requires: T029b
- [ ] T030 [US2] Implement `code/analysis/metric_check.py`: Validate "Turn-Taking" definition for tautology risk (FR-010); Output: Write boolean flag `is_tautology` to `data/processed/metric_validation.json`
- [ ] T030b [US2] Implement logic to adjust the analysis based on the tautology flag from T030; If `is_tautology` is true, switch to a non-tautological proxy metric or flag the result as invalid per FR-010; Output: Update `data/processed/metric_validation.json` with adjustment details; Requires: T030
- [ ] T031 [US2] Create `data/processed/results.csv` schema and writer for aggregated scores
- [ ] T032 [US2] Implement parallel execution logic in `code/main.py` to process 213 scenarios within 6h limit [UNRESOLVED-CLAIM: c_f42c7bc6 — status=not_enough_info]; Requires: T014-T018, T021-T024

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Robustness Reporting (Priority: P3)

**Goal**: Generate a comparative report contrasting latency degradation against acoustic noise baseline.

**Independent Test**: The system can be tested by generating a CSV or JSON report that includes columns for "Latency Condition," "Turn-Taking Score," and "Acoustic Baseline Score," verifying that the comparison logic correctly aligns the metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for comparative report format in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/contract/test_report.py`
- [ ] T028 [P] [US3] Integration test for AUC calculation and ANOVA interaction test in `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/code/tests/integration/test_comparison.py`

### Implementation for User Story 3

- [ ] T036a [US3] Document deviation from Spec FR-005 (Segmented Regression) to Isotonic Regression; Cite Plan's Complexity Tracking rationale (sparse data); Output: `docs/method_deviation_report.md`; Requires: T036
- [ ] T036 [US3] Implement `code/analysis/isotonic.py`: Primary threshold detection using Isotonic Regression; **Note**: This task implements Isotonic Regression *instead* of the Segmented Regression mandated by Spec FR-005, as justified in the Plan's Complexity Tracking due to sparse data; Output: `data/processed/statistical_report.json` with knee point; Requires: T038
- [ ] T036b [US3] Derive and report 'slope ratio' equivalent from Isotonic model to satisfy SC-003; Output: Add 'slope_ratio' field to `data/processed/statistical_report.json`; Requires: T036
- [ ] T037 [US3] Implement `code/analysis/lmm.py`: Piecewise Linear Mixed-Effects Model (PLMM) for secondary check [UNRESOLVED-CLAIM: c_dd0cb010 — status=not_enough_info]; Requires: T038
- [ ] T038 [US3] Implement delta calculation logic ($\Delta$) between baseline and perturbed scores; Aggregate per-system deltas from `data/processed/results.csv` (output of T029c) for regression input; Requires: T029c (output file)
- [ ] T039 [US3] Implement multiple-comparison correction (Bonferroni/Holm) for p-values
- [ ] T040 [US3] Implement sensitivity analysis for knee point stability: Sweep the **decision cutoff** parameter of the threshold model over [750, 800, 850]ms (±50ms sweep) to verify stability as required by SC-005; Output: `data/processed/sensitivity.json`; Requires: T036
- [ ] T041 [US3] Implement comparative analysis logic (Latency vs. Acoustic interaction effects)
- [ ] T041b [US3] Generate final comparative report artifact (`data/processed/comparative_report.json`) satisfying FR-009 and SC-006; Requires: T029c, T041
- [ ] T042 [US3] Generate final `data/processed/statistical_report.json` with knee points, slopes, and p-values

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
- **User Stories (Phase 3, 4, 5, 6)**: All depend on Foundational phase completion
 - US1 (P1) and US4 (P4) can run in parallel as they are independent data generation steps
 - US2 (P2) depends on US1/US4 completion (needs perturbed files)
 - US3 (P3) depends on US2 completion (needs scores)
- **Polish (Phase 7)**: Depends on all user stories being complete

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
 - Developer A: User Story 1 (Latency)
 - Developer B: User Story 4 (Acoustic)
3. Once US1/US4 done:
 - Developer C: User Story 2 (Evaluation)
4. Once US2 done:
 - Developer D: User Story 3 (Analysis)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All audio processing must use `librosa.stream` to stay within 7GB RAM limits [UNRESOLVED-CLAIM: c_7d83bbdf — status=not_enough_info].
- **Critical Constraint**: {{claim:c_52ef3759}} (Wikidata Q5099853, https://www.wikidata.org/wiki/Q5099853).
- **Critical Constraint**: Synthetic audio (FR-011) is a fallback only; real EVA-Bench data is preferred.