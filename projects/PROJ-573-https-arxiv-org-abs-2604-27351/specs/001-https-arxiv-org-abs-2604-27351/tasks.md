# Tasks: Heterogeneous Scientific Foundation Model Collaboration Benchmark

**Input**: Design documents from `/specs/001-heterogeneous-collaboration/`
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

## Phase 0: Research & Dataset Verification (Week 1)

**Purpose**: Verify dataset availability, model weights, and statistical methodology BEFORE implementation begins

**⚠️ CRITICAL**: Implementation cannot proceed until Phase 0 tasks complete and research.md is finalized

- [ ] T001 [P] Verify time-series dataset availability (UCI_HAR) with explicit URL via `datasets.load_dataset('UCI_HAR')` and document variables in research.md (FR-001, Phase 0.1)
- [ ] T002 [P] Verify tabular dataset availability (selected UCI sets) with explicit URL and document variables in research.md (FR-001, Phase 0.1)
- [ ] T003 [P] Verify text dataset availability (DROP/MUST) via HuggingFace datasets and document variables in research.md (FR-001, Phase 0.1)
- [ ] T004 Validate statistical methodology (paired t-test, Wilcoxon signed-rank, bootstrap 1000 resamples) and document in research.md methodology section (FR-007, FR-014, Phase 0.3)
- [ ] T005 Document dataset-variable fit and flag any missing variables in research.md gap analysis (FR-001, Phase 0.4)
- [ ] T006 Validate model weights <1 GB for TimeSeries-Transformer, TabPFN, distilled LLM via HuggingFace model cards; document in research.md model verification report (FR-002, SC-002, Phase 0.5)

**Checkpoint**: Research gate complete - plan.md Constitution Check must show ✅ COMPLIANT before Phase 1 begins

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T007 Create project structure with exact directories: src/, tests/, data/, data/processed/, state/, contracts/, src/benchmark/, src/models/, src/tasks/, src/evaluation/, src/utils/, src/benchmark/config/, src/benchmark/config/modalities/ (per plan.md project structure)
- [ ] T008 Initialize Python 3.11 project with pinned dependencies in requirements.txt (scikit-learn>=1.3.0, pandas>=2.0.0, numpy>=1.24.0, pyyaml>=6.0, datasets>=2.14.0, scipy>=1.11.0, matplotlib>=3.7.0, reportlab>=4.0.0, requests>=2.31.0)
- [ ] T009 [P] Configure linting and formatting tools: ruff.toml (line-length=88, target-version=py311) and pyproject.toml (black config) in repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T010 [P] Create dataset schema contract in contracts/dataset.schema.yaml
- [ ] T011 [P] Create task schema contract in contracts/task.schema.yaml
- [ ] T012 [P] Create results schema contract in contracts/results.schema.yaml
- [ ] T013 [P] Create modality_model schema contract in contracts/modality_model.schema.yaml
- [ ] T014 Create data-model.md with entity relationships (Dataset, ModalityModel, Task)
- [ ] T015 Create quickstart.md with setup instructions
- [ ] T016 Implement checksum tracking infrastructure in state/projects/PROJ-573-https-arxiv-org-abs-2604-27351.yaml artifact_hashes map (Constitution III)
- [ ] T017 [P] Setup base logging module in src/utils/logging.py (foundation for seed/version/environment logging)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Run Full Benchmark (Priority: P1) 🎯 MVP

**Goal**: Execute the benchmark script on a fresh environment with default parameters and verify that a results report (CSV + summary PDF) is produced within the allotted compute budget.

**Independent Test**: Run `python run_benchmark.py --config default.yaml` and verify `results.csv` and `summary.pdf` are generated within 4 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T018 [P] [US1] Contract test for dataset schema validation in tests/contract/test_dataset_schema.py
- [ ] T019 [P] [US1] Contract test for results schema validation in tests/contract/test_results_schema.py
- [ ] T020 [P] [US1] Integration test for full benchmark execution in tests/integration/test_benchmark_run.py

### Implementation for User Story 1

- [ ] T021 [US1] Implement dataset download with 3-retry logic in src/data/download.py (FR-010); verify URLs: UCI_HAR via `datasets.load_dataset('UCI_HAR')`, DROP/MUST via HuggingFace datasets; depends on T007/T008 complete
- [ ] T022 [US1] Create task_runner.py in src/tasks/task_runner.py (FR-001, FR-006)
- [ ] T023 [US1] Implement timeout enforcement in src/utils/timeout.py (FR-006, FR-013)
- [ ] T024 [US1] Implement seed/version AND environment details logging in src/utils/logging.py (FR-005); log random seeds, model versions, AND environment details (Python version, OS, CPU info)
- [ ] T025 [US1] Implement metrics computation (F1, MAPE) in src/evaluation/metrics.py (FR-004)
- [ ] T026 [US1] Implement statistical tests in src/evaluation/statistical_tests.py (FR-007, FR-014, FR-011); MUST include: paired t-test, Wilcoxon signed-rank with effect sizes (r = Z/sqrt(N)) and 95% CI as PRIMARY outcome, bootstrap 1000 resamples, configurable α threshold (default 0.05) with logging
- [ ] T027 [US1] Implement report generator in src/evaluation/report_generator.py (FR-007); MUST verify report includes (a) t-statistic, (b) p-value, (c) bootstrap CI (1000 resamples)
- [ ] T028 [US1] Create run_benchmark.py main entry point in src/benchmark/run_benchmark.py (FR-001, FR-006, FR-010); depends on T024 logging complete
- [ ] T029 [US1] Create default.yaml config in src/benchmark/config/default.yaml
- [ ] T030 [US1] Create task_definitions.yaml with multiple multi-modal task definitions in src/tasks/task_definitions.yaml
- [ ] T031 [US1] Create StatisticalSummary persistence in data/statistical_summary.yaml (Constitution IV)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heterogeneous Modality-Specific Orchestration (Priority: P2)

**Goal**: Add a new modality to the heterogeneous pipeline without breaking existing tasks.

**Independent Test**: Add a dummy "image" modality configuration file and run a single task that includes the new modality; verify that the pipeline processes it using the specified model and includes its output in the final prediction.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US2] Contract test for modality_model schema in tests/contract/test_modality_model_schema.py
- [ ] T033 [P] [US2] Integration test for modality addition in tests/integration/test_modality_addition.py

### Implementation for User Story 2

- [ ] T034 [P] [US2] Implement modality-specific model wrapper for time-series in src/models/timeseries_model.py (FR-002); use CPU-tractable TimeSeries-Transformer (< 1 GB)
- [ ] T035 [P] [US2] Implement modality-specific model wrapper for tabular in src/models/tabular_model.py (FR-002); use TabPFN (< 1 GB)
- [ ] T036 [P] [US2] Implement modality-specific model wrapper for text in src/models/text_model.py (FR-002); use distilled LLM (< 1 GB)
- [ ] T037 [US2] Implement heterogeneous routing layer in src/models/routing.py (FR-002); depends on T034-T036 complete
- [ ] T038 [US2] Implement missing modality handler in src/utils/missing_handler.py (FR-009, FR-012)
- [ ] T039 [US2] Create timeseries.yaml modality config in src/benchmark/config/modalities/timeseries.yaml (FR-008); update state/artifact_hashes after config changes
- [ ] T040 [US2] Create tabular.yaml modality config in src/benchmark/config/modalities/tabular.yaml (FR-008); update state/artifact_hashes after config changes
- [ ] T041 [US2] Create text.yaml modality config in src/benchmark/config/modalities/text.yaml (FR-008); update state/artifact_hashes after config changes
- [ ] T042 [US2] Implement run_task.py single task execution in src/benchmark/run_task.py (FR-008, FR-009)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Unified Text-Only Translation (Priority: P3)

**Goal**: Run the benchmark with the `--mode unified` flag and confirm that all inputs are translated to text before feeding to a single LLM.

**Independent Test**: Run the benchmark with `--mode unified` and confirm that time-series and tabular data are converted to text representations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T043 [P] [US3] Contract test for unified translation schema in tests/contract/test_translation_schema.py
- [ ] T044 [P] [US3] Integration test for unified mode execution in tests/integration/test_unified_mode.py

### Implementation for User Story 3

- [ ] T045 [US3] Implement unified translation layer in src/models/translation.py (FR-003)
- [ ] T046 [US3] Implement time-series to text conversion logic in src/models/translation.py (US-3 Scenario 1); deterministic schema: "Mean heart rate = X bpm, max = Y bpm..."
- [ ] T047 [US3] Implement tabular to text conversion logic in src/models/translation.py (US-3 Scenario 1); deterministic schema: CSV-style text representation
- [ ] T048 [US3] Add fidelity validation for translation quality in src/models/translation.py (FR-003)
- [ ] T049 [US3] Update run_benchmark.py to support --mode unified flag (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Documentation updates: quickstart.md (setup/dependencies sections) and data-model.md (entity relationships and schema references)
- [ ] T051 Code cleanup and refactoring across src/: remove unused imports, consolidate duplicate code, resolve TODO comments, remove dead code
- [ ] T052 [P] Additional unit tests in tests/unit/ (model wrappers, metrics, statistical tests)
- [ ] T053 Run quickstart.md validation to ensure reproducible setup
- [ ] T054 Verify total runtime ≤4 hours on reference hardware (SC-003)
- [ ] T055 Verify per-task inference ≤5 minutes (SC-002)
- [ ] T056 Verify reproducibility across 5 seeds (SC-004); mean accuracy differences within 95% CI with CI width ≤15%
- [ ] T057 Archive artifacts with content hashes in state/artifact_hashes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately
- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Contract test for results schema validation in tests/contract/test_results_schema.py"

# Launch model implementations for User Story 1 together (after T024 logging complete):
Task: "Implement dataset download with 3-retry logic in src/data/download.py"
Task: "Create task_runner.py in src/tasks/task_runner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research & Dataset Verification
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
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

## Compute Feasibility Notes

- All models must be CPU-tractable (< 1 GB weights) - validated in T006
- No GPU/CUDA dependencies
- Total dataset size ≤ 5 GB
- Per-task inference ≤ 5 minutes on 2 CPU cores
- Full benchmark ≤ 4 hours wall-clock time
- Use UCI_HAR for time-series, DROP/MUST for text (per plan.md substitution strategy)
- No 8-bit/4-bit quantization (bitsandbytes requires CUDA)
- Dataset downloads MUST use verified URLs or HuggingFace datasets.load_dataset()