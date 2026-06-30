# Tasks: Reproduce & validate: WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation

**Input**: Design documents from `/specs/PROJ-630/001-reproduce-validate-wbench/`
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

- [X] T001 Create project structure: `mkdir -p src/metrics/{consistency,physical,quality} src/evaluation src/utils src/cli tests/{unit,integration,contract} tools docs`
- [X] T002 Initialize Python + project: Create `pyproject.toml` with `build-system`, `project` (name, version, dependencies: `torch==2.1.0+cpu`, `opencv-python`, `pandas`, `numpy`, `requests`, `huggingface-hub`, `scikit-learn`) and `requirements.txt` with `--index-url for torch
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup dataset loader utility: Implement `src/utils/dataset_loader.py` with function `load_wbench_parquet(path: str) -> pd.DataFrame` that validates columns `['case_id', 'prompt', 'interaction_sequence', 'video_path', 'ground_truth']`. **Constraint**: Must use real assets; if `video_path` is invalid or missing, the function must log a warning and return a filtered dataframe excluding that row. **Do not generate mock data.**
- [X] T005 [P] Implement retry logic utility: Create `src/utils/retry.py` with a generic `retry_on_exception(max_attempts: int)` decorator for network calls.
- [X] T005a [P] Implement API retry wrapper: Create `src/utils/api_retry.py` specifically for FR-004. Implement `fetch_model_with_retry(url: str, max_attempts: int = 3)` that wraps API calls, handles timeouts, and returns `None` on final failure. Tag: FR-004, US-2.
- [X] T006 [P] Setup logging infrastructure in `src/utils/logger.py` with structured output (JSON format) and log levels (INFO, WARNING, ERROR).
- [X] T008 Configure environment variable management for API keys (if needed) and paths.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Validate Environment & Dependency Installation (Priority: P1) 🎯 MVP

**Goal**: Ensure the vendored WBench codebase installs and runs on a CPU-only GitHub Actions runner without GPU errors.

**Independent Test**: Execute `tools/install.sh` and `tools/verify_install.py`; exit code 0 and "Ready" status for all tools.

### Implementation for User Story 1

- [X] T010 [US1] Create `tools/install.sh` to install system deps (ffmpeg, git-lfs) and Python deps with CPU-only torch flag (`pip install -r requirements.txt --index-url)
- [X] T011 [US1] Implement `tools/verify_install.py` to check imports of `torch`, `opencv-python`, `pandas`, `huggingface-hub` and print "Ready" for each
- [X] T012 [US1] Add schema check in `tools/verify_install.py` to load WBench parquet using `src/utils/dataset_loader.py` (T004 artifact) and validate required columns (`case_id`, `prompt`, `video_path`, `ground_truth`). If columns missing, exit 1.
- [X] T013 [US1] Handle missing video paths in `tools/verify_install.py`: If a row has an invalid `video_path`, skip the case and log a warning. **Strictly do not generate dummy frames.**
- [X] T014 [US1] Ensure `src/` modules import cleanly in `tools/verify_install.py` without CUDA errors (using `torch.device('cpu')` forced).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Core Evaluation Pipeline on Sample Data (Priority: P1)

**Goal**: Run the evaluation pipeline on a minimal subset of cases using real video data to verify end-to-end flow.

**Independent Test**: Run `python src/cli/main.py --subset 2`; output valid JSON/CSV with non-null metrics; no CUDA errors.

### Implementation for User Story 2

- [X] T015 [US2] Implement dataset filtering in `src/evaluation/runner.py` to select valid test cases with existing video files (using `src/utils/dataset_loader.py` from T004).
- [X] T016a [US2] Implement `src/metrics/quality/motion_smoothness.py`: Function `calculate_motion_smoothness(video_path: str, sample_rate: int = 1)` using optical flow on sampled frames (frame/sec). **Constraint**: Must use CPU-only OpenCV.
- [X] T016b [US2] Implement `src/metrics/consistency/consistency_checker.py`: Function `calculate_consistency(video_path: str, interaction_sequence: list)` using lightweight VLM on sampled frames (frame/sec). **Constraint**: Must use CPU-only inference.
- [X] T016c [US2] Implement `src/metrics/physical/physics_compliance.py`: Function `calculate_physics(video_path: str)` using statistical motion analysis on sampled frames (frame/sec). **Constraint**: Must use CPU-only numpy/scipy.
- [X] T016d [US2] Verify Integration: Create `src/evaluation/aggregator.py` that explicitly imports and calls `src/metrics/consistency/consistency_checker.py` and `src/metrics/physical/physics_compliance.py`. Assert these modules are used in the pipeline. Tag: FR-006.
- [X] T018 [US2] Implement error handling in `src/evaluation/runner.py` to mark cases as "failed" on timeout/missing data. **Must use** `src/utils/api_retry.py` (T005a) for network calls and `src/utils/retry.py` (T005) for local retries.
- [X] T019a [US2] Create sample result aggregation: Implement logic in `src/evaluation/aggregator.py` to output `data/results/sample_results.json` for the subset run. Schema: `{"case_id": str, "metrics": {"quality": float, "consistency": float, "physics": float,...}}`.
- [X] T019b [US2] Implement sample run CLI: Add `--subset` flag parsing in `src/cli/main.py` to trigger T019a logic and output `data/results/sample_results.json`.
- [X] T021 [US2] Verify no CUDA/GPU errors in logs during sample run.

**Checkpoint**: At this point, User Story 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate Full Dataset Results & Generate Diagnostics (Priority: P2)

**Goal**: Process a representative subset or full dataset to reproduce paper's aggregate statistics and generate leaderboards.

**Independent Test**: Run full evaluation; produce `final_results.csv` matching paper schema; execution time ≤ 6 hours (or labeled Proxy).

### Implementation for User Story 3

- [X] T022 [US3] Extend `src/evaluation/runner.py` to iterate through full dataset with progress tracking.
- [X] T023 [US3] Implement full result aggregation in `src/evaluation/aggregator.py` to compute mean scores for 5 dimensions (quality, setting, interaction, consistency, physics) across all processed cases.
- [X] T024a [US3] Generate `final_results.csv`: Implement writer in `src/evaluation/aggregator.py` to output `data/results/final_results.csv` with columns: `case_id, video_quality_score, setting_adherence_score, interaction_adherence_score, consistency_score, physics_compliance_score, overall_score`.
- [X] T024b [US3] Validate Schema: Implement `tools/validate_schema.py` to compare `data/results/final_results.csv` columns against `assets/leaderboard_9models_full.csv` columns. Fail if mismatch. Tag: SC-003.
- [X] T025 [US3] Implement variance analysis logic to compare aggregated scores against paper values. **Constraint**: No fixed tolerance; focus on understanding and documenting deviation (e.g., "CPU precision variance", "Frame sampling").
- [X] T025a [US3] Fetch Reference Data: Create `tools/fetch_paper_data.py` to download/verify `assets/leaderboard_9models_full.csv` from the repo or paper supplementary. Tag: SC-003.
- [X] T026 [US3] Add timeout handling for full dataset run to label as "Proxy Evaluation" if > 6 hours.
- [X] T027a [US3] Create diagnostic report: Implement `tools/generate_diagnostics.py` to write `data/results/diagnostics.md` summarizing success rates and skipped cases.
- [X] T027b [US3] Implement Success Rate Calculation: Create `tools/calculate_success_rate.py` to compute percentage of cases with non-null metrics. Assert ≥90% success rate for SC-005.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T028 [P] Documentation updates in `docs/` including quickstart and usage examples
- [X] T029 Code cleanup and refactoring for memory efficiency (chunked processing)
- [X] T030 Performance optimization: ensure frame sampling is set to 1 frame per second (as per Plan Phase 2) to meet -core CPU limit.
- [X] T031 [P] Unit tests: Create `tests/unit/test_metrics.py` with `test_motion_smoothness()`, `test_consistency()`, `test_physics()`. Create `tests/unit/test_api_retry.py` with `test_retry_on_timeout()`.
- [X] T032 Security hardening: sanitize input paths and API responses
- [X] T033 Run `tools/verify_install.py` and full sample pipeline as final validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 environment being valid
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 pipeline logic being stable

### Within Each User Story

- Models/Utilities before services/runner
- Services/Runner before CLI
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
# Launch all tasks for User Story 1 together (if team capacity allows):
Task: "Create tools/install.sh to install system deps and Python deps with CPU-only torch flag"
Task: "Implement tools/verify_install.py to check imports of torch, opencv-python, pandas, huggingface-hub"
Task: "Add schema check in tools/verify_install.py to load WBench parquet and validate required columns"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (install and verify)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Sample run)
4. Add User Story 3 → Test independently → Deploy/Demo (Full aggregation)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Environment)
 - Developer B: User Story 2 (Sample Pipeline)
 - Developer C: User Story 3 (Aggregation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (if tests included)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All metric calculations must be CPU-optimized (frame sampling: reduced frequency, chunked processing) to fit -core/GB limits.
- **Critical**: Do not mock video data; use real assets from the dataset or skip the case.
- **Critical**: FR-004 requires explicit retry wrapper for API calls (T005a).
- **Critical**: FR-006 requires explicit integration of `src/metrics/consistency/` and `src/metrics/physical/` (T016d).
- **Critical**: SC-003 requires schema validation against reference file (T024b).
- **Critical**: SC-005 requires success rate calculation (T027b).