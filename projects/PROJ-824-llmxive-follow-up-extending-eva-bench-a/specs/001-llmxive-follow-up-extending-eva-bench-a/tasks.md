# Tasks: llmXive follow-up: extending EVA-Bench with Latency & Acoustic Perturbations

**Input**: Design documents from `/specs/001-gene-regulation/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan by executing: `mkdir -p projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/{data/{raw,processed},code/{injectors,evaluation,analysis,synthetic},tests/{unit,integration},specs/001-gene-regulation}`
- [ ] T002 Initialize Python 3.11 project by creating `projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a/requirements.txt` with pinned versions: `librosa==0.10.1`, `pandas==2.0.3`, `statsmodels==0.14.0`, `scipy==1.11.0`, `numpy==1.24.0`, `pyyaml==6.0.1`, `coqui-tts==0.23.0`
- [ ] T003a [P] Configure Black formatting by creating `pyproject.toml` with `tool.black` section (line-length=88, target-version=['py311']).
- [ ] T003b [P] Configure Flake8 linting by creating `.flake8` with strict rules (max-line-length=88, exclude=venv).
- [ ] T003c [P] Configure import sorting by adding `tool.isort` to `pyproject.toml` (profile=black).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create directory structure: `data/raw/`, `data/processed/`, `code/`, `tests/`, `specs/`
- [ ] T005 [P] Implement `code/config.py` for path configuration, random seeds, and hyperparameters (200ms-2000ms bounds)
- [ ] T006 [P] Setup logging infrastructure with file handlers and warning filters for edge cases
- [ ] T007 [P] Implement `code/synthetic/tts_engine.py` (FR-011) as a fallback for missing EVA-Bench audio using Coqui TTS with known characteristics; simultaneously document 'known characteristics' (model version, prosody settings, seed) in `docs/tts_characteristics.md` to satisfy FR-011 reproducibility constraints; Output: `code/synthetic/tts_engine.py` and `docs/tts_characteristics.md`
- [ ] T008 Create `data/checksums.json` schema and initialization script; schema must be `{"files": [{"path": "string", "sha256": "string"}]}`; script must initialize empty `{"files": []}`; Output: `data/checksums.json`
- [ ] T009 Implement `code/main.py` orchestration skeleton with argument parsing for perturbation types

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Latency Injection Pipeline (Priority: P1) 🎯 MVP

**Goal**: Implement a reliable mechanism to inject variable network latency into EVA-Bench audio streams without modifying models.

**Independent Test**: Run `LatencyInjector` on a single scenario with 500ms delay; verify output duration > input duration by target amount while preserving content.

### Test Definition for User Story 1 (Write First)

- [ ] T010 [P] [US1] Define unit test for `LatencyInjector` gap insertion logic in `tests/unit/test_latency.py` (Write code that asserts failure if class missing)
- [ ] T011 [P] [US1] Define unit test for chunked processing memory limits in `tests/unit/test_latency.py`
- [ ] T012 [P] [US1] Define integration test for 800ms fixed delay scenario in `tests/integration/test_latency_pipeline.py`
- [ ] T013 [P] [US1] Define integration test for ±50ms jitter variability in `tests/integration/test_latency_pipeline.py`

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/injectors/latency.py`: `LatencyInjector` class with `librosa.stream` for chunked I/O
- [ ] T015 [US1] Implement turn-boundary detection logic in `code/injectors/latency.py`; Input: `data/processed/turn_boundaries.csv`; Algorithm: If gap overlaps audio > 10ms, shift boundary to nearest silence > 50ms; Output: Updated turn boundaries
- [ ] T016 [US1] Implement duration validation and truncation logic in `code/injectors/latency.py`; MUST enforce a strict maximum duration limit as defined in Spec Edge Cases.; truncate audio if exceeded, log warning, and record score as `null`; Output: Updated audio files and logs
- [ ] T017 [US1] Create `code/injectors/__init__.py` exports
- [ ] T018 [US1] Add deterministic jitter generation using seeded `numpy.random`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 4 - Static Acoustic Perturbation Arm (Priority: P4)

**Goal**: Apply static acoustic perturbations (noise, reverb) to establish a control condition for comparison.

**Independent Test**: Apply noise at a signal-to-noise ratio; verify turn boundaries remain unchanged while audio content is altered.

### Test Definition for User Story 4

- [ ] T019 [P] [US4] Define unit test for `AcousticPerturber` SNR calculation in `tests/unit/test_acoustic.py`
- [ ] T020 [P] [US4] Define integration test for reverberation without timing shift in `tests/integration/test_acoustic_pipeline.py`

### Implementation for User Story 4

- [ ] T021 [US4] Implement `code/injectors/acoustic.py`: `AcousticPerturber` class (white noise, reverberation)
- [ ] T022 [US4] Implement signal-to-noise ratio (SNR) calculation and application logic
- [ ] T023 [US4] Verify and log that turn boundaries are preserved after acoustic perturbation
- [ ] T024 [US4] Integrate `AcousticPerturber` into `code/main.py` orchestration

**Checkpoint**: At this point, User Story 1 AND User Story 4 should both work independently

---

## Phase 5: User Story 2 - EVA-Bench Re-evaluation (Priority: P2)

**Goal**: Re-run original EVA-Bench scoring logic on perturbed streams to generate new EVA-A and EVA-X scores.

**Independent Test**: Compare baseline (0ms) vs. 0ms injected; delta must be zero within floating-point tolerance.

**Requires**: T014-T018 (US1), T021-T024 (US4) must be complete to provide perturbed audio files.

### Tests for User Story 2

- [ ] T025 [P] [US2] Unit test for EVA-Bench wrapper stability in `tests/unit/test_metric_check.py`
- [ ] T026 [P] [US2] Integration test for baseline consistency (0ms vs 0ms) in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [ ] T027 [US2] Implement `code/evaluation/runner.py`: Wrapper to execute original EVA-Bench scoring on perturbed files; Requires: T014-T018, T021-T024
- [ ] T028 [US2] Implement metric extraction logic for "Turn-Taking" and "Conversation Progression" sub-metrics
- [ ] T029 [US2] Implement floor-effect handling (skip delta if baseline is 0) with logging
- [ ] T029b [US2] Calculate delta (Δ) between baseline and perturbed scores for each scenario; Input: `data/processed/results.csv` containing `scenario_id` and `system_id` columns; Output: Append rows to `data/processed/results.csv` with columns `scenario_id`, `system_id`, `metric`, `baseline`, `perturbed`, `delta`; Ensures hierarchical structure for LMM; Requires: T027, T028
- [ ] T029c [US2] Calculate and aggregate system-level deltas to ensure hierarchical structure for LMM as required by FR-003; Input: `data/processed/results.csv` (output of T029b); Output: Ensure `results.csv` includes `system_id` grouping for LMM; Requires: T029b
- [ ] T030 [US2] Implement `code/analysis/metric_check.py`: Validate "Turn-Taking" definition for tautology risk (FR-010); Output: Write boolean flag `is_tautology` to `data/processed/metric_validation.json`
- [ ] T030b [US2] Implement logic to adjust the analysis based on the tautology flag from T030; If `is_tautology` is true, switch to a non-tautological proxy metric or flag the result as invalid per FR-010; Output: Update `data/processed/metric_validation.json` with adjustment details; Requires: T030
- [ ] T031 [US2] Create `data/processed/results.csv` schema and writer for aggregated scores
- [ ] T032 [US2] Implement parallel execution logic in `code/main.py` to process 213 scenarios within 6h limit; Requires: T014-T018, T021-T024

**Checkpoint**: At this point, User Stories 1, 2, and 4 should be functional; data generation pipeline is ready.

---

## Phase 6: User Story 3 - Threshold Detection & Statistical Analysis (Priority: P3)

**Goal**: Perform LMM and Isotonic Regression to identify latency "knee points" and verify statistical significance.

**Independent Test**: Feed synthetic dataset with known 800ms break point; system must identify it with p < 0.05.

**Requires**: T031 (results.csv) and T029c (system-level deltas) must be complete.

### Tests for User Story 3

- [ ] T033 [P] [US3] Unit test for Isotonic Regression breakpoint detection in `tests/unit/test_isotonic.py`
- [ ] T034 [P] [US3] Unit test for LMM p-value calculation in `tests/unit/test_lmm.py`
- [ ] T035 [P] [US3] Integration test for multiple-comparison correction (Bonferroni) in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T036a [US3] Document deviation from Spec FR-005 (Segmented Regression) to Isotonic Regression; Cite Plan's Complexity Tracking rationale (sparse data); Output: `docs/method_deviation_report.md`; Requires: T036
- [ ] T036 [US3] Implement `code/analysis/isotonic.py`: Primary threshold detection using Isotonic Regression; **Note**: This task implements Isotonic Regression *instead* of the Segmented Regression mandated by Spec FR-005, as justified in the Plan's Complexity Tracking due to sparse data; Output: `data/processed/statistical_report.json` with knee point; Requires: T038
- [ ] T036b [US3] Derive and report 'slope ratio' equivalent from Isotonic model to satisfy SC-003; Output: Add 'slope_ratio' field to `data/processed/statistical_report.json`; Requires: T036
- [ ] T037 [US3] Implement `code/analysis/lmm.py`: Piecewise Linear Mixed-Effects Model (PLMM) for secondary check; Requires: T038
- [ ] T038 [US3] Implement delta calculation logic ($\Delta$) between baseline and perturbed scores; Aggregate per-system deltas from `data/processed/results.csv` (output of T029c) for regression input; Requires: T029c (output file)
- [ ] T039 [US3] Implement multiple-comparison correction (Bonferroni/Holm) for p-values
- [ ] T040 [US3] Implement sensitivity analysis for knee point stability: Sweep the **decision cutoff** parameter of the threshold model over [750, 800, 850]ms (±50ms sweep) to verify stability as required by SC-005; Output: `data/processed/sensitivity.json`; Requires: T036
- [ ] T041 [US3] Implement comparative analysis logic (Latency vs. Acoustic interaction effects)
- [ ] T041b [US3] Generate final comparative report artifact (`data/processed/comparative_report.json`) satisfying FR-009 and SC-006; Requires: T029c, T041
- [ ] T042 [US3] Generate final `data/processed/statistical_report.json` with knee points, slopes, and p-values

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T043 [P] Create `scripts/hash_artifacts.py` to compute SHA-256 for all outputs and update `state/projects/PROJ-824-llmxive-follow-up-extending-eva-bench-a.yaml` with new `artifact_hashes` map; Output: Updated YAML file
- [ ] T044 [P] Run full integration test suite on the multi-core CI runner to verify 6h timeout compliance
- [ ] T044b [P] Validate 6-hour runtime limit including computational cost of Tobit Regression and Isotonic/PLMM analysis; Output: Runtime log in `data/processed/runtime_validation.log`; Requires: T032, T036, T037
- [ ] T045 [P] Update `README.md` with execution instructions for Latency and Acoustic arms
- [ ] T046 [P] Verify `quickstart.md` validation passes
- [ ] T047 [P] Document edge case handling (audio truncation, floor effects, parsing errors) in `docs/edge_cases.md`

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

- **User Story 1 (P1)**: Can start after Foundational - No dependencies
- **User Story 4 (P4)**: Can start after Foundational - No dependencies
- **User Story 2 (P2)**: Depends on US1 and US4 (requires perturbed audio files)
- **User Story 3 (P3)**: Depends on US2 (requires evaluation results)

### Within Each User Story

- Test Definition (T010-T013, T019-T020) MUST be written before Implementation
- Implementation tasks MUST exist before Test Execution (to avoid import errors)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003a, T003b, T003c, T004, T005, T006, T007, T008, T009 can run in parallel during Setup/Foundational
- T010-T013 (US1 Tests) and T019-T020 (US4 Tests) can run in parallel
- T014-T018 (US1 Impl) and T021-T024 (US4 Impl) can run in parallel
- T025-T032 (US2) must wait for US1/US4 data
- T038, T036, T036a, T036b, T037, T039, T040, T041, T041b, T042 (US3) must wait for US2 data

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Latency Injection)
4. **STOP and VALIDATE**: Verify latency injection works and duration increases correctly.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Latency) → Test independently → Data generation ready for Latency arm
3. Add User Story 4 (Acoustic) → Test independently → Control arm ready
4. Add User Story 2 (Re-eval) → Test independently → Scores generated for both arms
5. Add User Story 3 (Analysis) → Test independently → Final statistical report
6. Add Polish → Final validation

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
- **Critical Constraint**: All audio processing must use `librosa.stream` to stay within 7GB RAM limits.
- **Critical Constraint**: No GPU; use CPU-optimized libraries (scipy, statsmodels) only.
- **Critical Constraint**: Synthetic audio (FR-011) is a fallback only; real EVA-Bench data is preferred.