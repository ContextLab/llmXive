# Tasks: llmXive follow-up: extending "OmniDirector: General Multi-Shot Camera Cloning without Cross-Paired D"

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

- [ ] T001 Create project structure per 'Project Structure' section in plan.md: create `code/`, `code/data/`, `code/geometry/`, `code/analysis/`, `code/tests/`, `code/tests/unit/`, `code/tests/integration/`, `data/raw/`, `data/processed/`. <!-- FAILED: unspecified -->
- [X] T002 Initialize Python 3.11 project with `opencv-python`, `numpy`, `pandas`, `scipy`, `pytest`, `pyyaml` in `code/requirements.txt`.
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup basic logging infrastructure in `code/__init__.py`.
- [ ] T005 [P] Implement configuration loader in `code/config.py` to manage paths and constants.
- [ ] T006 [P] Create base data models for `GridFrame`, `CameraPose`, and `ReconstructedBox` in `code/data/models.py`.
- [ ] T006b [P] Design memory-efficient processing strategy: Define chunked data loading and streaming logic in `code/config.py` to ensure <6GB memory footprint before implementation begins.
- [ ] T007 Attempt to fetch the real OmniDirector dataset from the canonical source (e.g., HuggingFace or GitHub release). If fetch fails, generate a deterministic synthetic dataset locally that mimics the real schema. **Output Schema**: `data/processed/filtered_sequences.csv` must contain columns: `sequence_id`, `frame_id`, `radial_motion_deg`, `z_velocity`, `grid_points_2d` (list of pixel coords), `R_matrix`, `t_vector`, `randomized_depth` (boolean). For synthetic data, set `randomized_depth=True` for [deferred] of sequences. Output to `data/raw/omnidirector.zip` (real) or `data/raw/synthetic_omnidirector.zip` (fallback).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Ingestion and Geometric Filtering (Priority: P1) 🎯 MVP

**Goal**: Ingest OmniDirector dataset (real or fallback synthetic), filter sequences with defined spatial volumes, and output curated grid frames with ground-truth parameters.

**Independent Test**: Run ingestion on a small subset of sequences and verify output contains valid grid frames, correct $R_i, t_i$ pairing, and excludes static/translational-only sequences.

### Implementation for User Story 1

- [~] T008 Implement dataset loader in `code/data/ingestion.py` to load the dataset from `data/raw/omnidirector.zip` (real) or `data/raw/synthetic_omnidirector.zip` (fallback) and extract grid-video pairs. **Input Schema**: Matches T007 output.
- [~] T009 [US1] Implement geometric filtering logic in `code/data/ingestion.py` to classify sequences as 'retained' or 'excluded' based on FR-001 heuristics: **radial motion > 15° OR Z-axis velocity > 0.1 units/frame**. **Input**: `radial_motion_deg`, `z_velocity` columns from T008.
- [~] T010 [US1] Implement grid frame extraction and ground-truth pairing in `code/data/preprocessing.py`. **Output**: Ensure `grid_points_2d` are extracted for each frame.
- [~] T011 [US1] Write filtered dataset to `data/processed/filtered_sequences.csv` with checksums. **Schema**: `sequence_id`, `frame_id`, `radial_motion_deg`, `z_velocity`, `grid_points_2d`, `R_matrix`, `t_vector`, `randomized_depth`.
- [~] T012 [US1] Implement linear interpolation for missing/occluded grid lines in `code/data/ingestion.py` to handle edge cases without crashing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests AFTER implementation tasks T008-T012 are complete

- [~] T013 [P] [US1] Unit test for filtering heuristics (radial > 15°, Z-vel > 0.1) in `code/tests/unit/test_ingestion.py`.
- [~] T014 [P] [US1] Integration test for pipeline on subset in `code/tests/integration/test_ingestion_pipeline.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Based Perspective Inversion Solver (Priority: P2)

**Goal**: Implement a CPU-tractable geometric solver to detect grid lines, track perspective distortion, and estimate relative 3D camera motion/bounding box dimensions.

**Independent Test**: Run solver on a single video sequence and compare reconstructed bounding box dimensions against ground-truth metadata.

### Implementation for User Story 2

- [~] T015 [P] [US2] Define `WorldGridModel` (canonical unit grid at Z=0) in `code/geometry/utils.py`.
- [~] T016 [US2] Implement orthogonal grid line detection and intersection logic in `code/geometry/utils.py`.
- [~] T017 Implement CPU-based `solvePnP` solver in `code/geometry/solver.py` to estimate relative motion vectors, consuming `data/processed/filtered_sequences.csv` from T011. **Input**: `grid_points_2d` (2D image points) and `R_matrix`, `t_vector` (3D object points derived from WorldGridModel).
- [~] T018 [US2] Implement bounding box dimension reconstruction (height, width, depth) from motion vectors in `code/geometry/reconstruction.py`.
- [~] T019 [US2] Write pose estimates and reconstructed boxes to `data/processed/poses_estimated.json`.
- [~] T020 [US2] Implement logic to handle missing data (interpolation/skipping) and flag high-complexity sequences in `code/geometry/solver.py`.
- [~] T021 [US2] Implement detection and logging of sequences where 'perspective distortion exceeds solvable thresholds' as defined in FR-007 in `code/geometry/solver.py`.
- [~] T022 [US2] Enforce CPU-only implementation: Use `cv2.solvePnP` with `SOLVEPNP_ITERATIVE` and ensure no GPU flags or CUDA dependencies are used in `code/geometry/solver.py`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T023 [P] [US2] Unit test for line intersection detection in `code/tests/unit/test_solver.py`.
- [~] T024 [P] [US2] Unit test for solvePnP scale ambiguity handling in `code/tests/unit/test_solver.py`.
- [~] T025 [P] [US2] Integration test for full sequence reconstruction in `code/tests/integration/test_geometry_pipeline.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Correlation Analysis (Priority: P3)

**Goal**: Compute reconstruction error, perform Pearson's r correlation analysis, validate aspect ratios, and run Synthetic Control validation.

**Independent Test**: Run analysis on full curated dataset and generate report with Pearson's r, error distribution, and aspect ratio validation.

### Implementation for User Story 3

- [~] T026 Implement reconstruction error calculation (absolute difference) in `code/analysis/metrics.py`, consuming `data/processed/poses_estimated.json` from T019.
- [~] T027 [US3] Implement camera motion complexity metric calculation in `code/analysis/metrics.py`.
- [ ] T028 [US3] Implement Pearson's r correlation analysis between complexity and accuracy in `code/analysis/metrics.py`.
- [ ] T029 [US3] Implement aspect ratio validation (±5% tolerance) against known synthetic volumes in `code/analysis/validation.py`.
- [ ] T030 Implement Synthetic Control Validation: Read `data/processed/filtered_sequences.csv` from T011. Identify rows where `randomized_depth` is `True`. Attempt to recover metric depth for these rows. Flag error >50% in `code/analysis/validation.py`.
- [ ] T031 [US3] Calculate Dataset Filtering Success Rate (retained/total) and record in `data/processed/reconstruction_results.csv` (SC-004).
- [ ] T032 [US3] Instrument pipeline for timing (start/stop) and record total execution time in `data/processed/reconstruction_results.csv` (SC-005).
- [ ] T033 [US3] Generate final `data/processed/reconstruction_results.csv` (Single Source of Truth).
- [ ] T034 [US3] Generate final statistical report `report.md` with specific sections: SC-001 (Error), SC-002 (Correlation), SC-003 (Aspect Ratio), SC-004 (Filter Rate), SC-005 (Time), and visualizations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T035 [P] [US3] Unit test for Pearson correlation calculation in `code/tests/unit/test_metrics.py`.
- [ ] T036 [P] [US3] Unit test for aspect ratio validation logic in `code/tests/unit/test_validation.py`.
- [ ] T037 [P] [US3] Integration test for full statistical report generation in `code/tests/integration/test_analysis_pipeline.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `code/docs/` and `code/README.md`.
- [ ] T039 Implement chunked processing in `code/geometry/solver.py` and add memory profiling to ensure <6GB usage on full dataset.
- [ ] T040 Optimize line detection to run in <100ms per frame: Replace Canny edge detection with Sobel and implement parallel frame processing using `multiprocessing` in `code/geometry/utils.py`.
- [ ] T041 Run `quickstart.md` validation to ensure full pipeline execution within 6h on free-tier CI.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`data/processed/filtered_sequences.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (`data/processed/poses_estimated.json`)

### Within Each User Story

- Implementation tasks MUST be completed before Test tasks
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (among tests, not with implementation)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement dataset loader in code/data/ingestion.py"
Task: "Implement grid frame extraction in code/data/preprocessing.py"

# Launch tests ONLY after implementation is complete:
Task: "Unit test for filtering heuristics in code/tests/unit/test_ingestion.py"
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

## Data Strategy

- **Primary Source**: The system MUST attempt to fetch the real OmniDirector dataset from the canonical source (HuggingFace/GitHub) as defined in T007.
- **Fallback**: If the real dataset is unavailable or the fetch fails, T007 generates a deterministic synthetic dataset locally. This synthetic dataset strictly adheres to the schema required by T008-T030 (including `randomized_depth` flags) to ensure the pipeline remains executable and testable.
- **Validation**: FR-008 (Synthetic Control) is validated by identifying rows with `randomized_depth=True` in the filtered CSV, whether from real or synthetic data.
- **Reproducibility**: All random seeds are pinned. If real data is used, the fetch URL is logged. If synthetic data is used, the seed is logged.
