# Tasks: Single-Cell Trajectories of T-Cell Exhaustion

**Input**: Design documents from `/specs/001-single-cell-trajectories-of-t-cell-exhau/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are REQUIRED - include them to ensure independent implementation and testing of each story.

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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/`)
- [X] T002 Initialize Python project with `requirements.txt` (scvelo, scanpy, pandas, numpy, scipy, matplotlib, seaborn, requests, wget)
- [ ] T002b Setup system-level R environment: {{claim:c_bed10a97}}, install `r-seurat` v4 package, and `reticulate` via system package manager (apt-get/conda). **Verification**: Run `R --version` and `Rscript -e "packageVersion('Seurat')"` to confirm installation. **Checksum**: Record the checksum of the installed package list. **Note**: This task modifies the system environment and must NOT run in parallel with other system-modifying tasks. (Plan Technical Context, Constitution Principle I & III) <!-- FAILED: unspecified -->
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/` directory structure (`raw/`, `processed/`, `results/`) and `tests/` structure (`unit/`, `integration/`)
- [ ] T004a [P] Install and verify SRA Toolkit: Install `sratoolkit` via conda and configure `~/.ncbi/settings`. Verify installation by running `prefetch --help`. **Prerequisite**: None. **Depends on**: T001. (FR-001, Plan Phase 0) <!-- FAILED: unspecified -->
- [ ] T005 Implement `download_data.py` to fetch raw count matrices via SRA Toolkit. Fetch GSE136103, GSE127465, GSE111075, GSE138852 (FR-001). *Note: Corrects 'GSE' typo in FR-001 per Plan.* **Prerequisite**: T004a (SRA Toolkit installed). **Output**: Raw files in `data/raw/`. **Note**: This task writes to a shared directory and must NOT run in parallel. (FR-001)
- [ ] T006 [P] Implement `preprocess.R` for Seurat v4 QC (>20% mitochondrial reads) and normalization. **Prerequisite**: Ensure R 4.3 and Seurat v4 are installed (see T002b). **Output**: Normalized `.h5ad` files. **Depends on**: T002b. (FR-002)
- [ ] T007 Implement `preprocess.py` wrapper to call `preprocess.R` via subprocess and output `.h5ad` files. **Depends on**: T006 completion.
- [ ] T008 Create `contracts/fork_point.schema.yaml` defining the output schema for fork-point genes (gene symbols, branch ID, timing rank)
- [X] T009 Setup environment configuration for random seeds and dataset paths in `config.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Trajectory Reconstruction (Priority: P1) 🎯 MVP

**Goal**: Download four specific public scRNA-seq datasets, preprocess them to remove low-quality cells, and run scVelo to generate RNA velocity and pseudotime orderings independently for each dataset.

**Independent Test**: The pipeline executes end-to-end on GSE136103 within 45 minutes on CPU, producing a valid `.h5ad` file with velocity vectors and pseudotime values.

### Tests for User Story 1 (REQUIRED)

- [ ] T010 [P] [US1] Unit test for mitochondrial read filtering logic in `tests/unit/test_preprocess.py`. **Verification**: Assert that cells with >20% mitochondrial reads are removed. (Spec US-1 Acceptance Scenario 1)
- [ ] T011 [P] [US1] Integration test for end-to-end scVelo run on a subset of GSE136103 in `tests/integration/test_trajectory_reconstruction.py`. **Verification**: Assert that `velocity_graph.h5ad` is produced with required fields (velocity, pseudotime, unspliced, spliced). (Spec US-1 Acceptance Scenario 2)

### Implementation for User Story 1

- [ ] T014 [US1] Implement `velocity.py` to run scVelo on CPU with default precision. **Output**: `velocity_graph.h5ad` containing velocity vectors and pseudotime values. **Verification**: File exists, contains required fields (velocity, pseudotime, unspliced, spliced) as defined in `contracts/fork_point.schema.yaml` (T008). (FR-003)
- [ ] T014b [US1] Implement `aligner.py` to execute the **Markov-chain pseudotime aligner** on the velocity graph to produce a **unified trajectory graph** across cells. **Output**: `unified_trajectory.h5ad`. **Verification**: Graph contains continuous pseudotime axis and cell ordering. (Spec US-1 Acceptance Scenario 3, Plan Phase 2)
- [ ] T016 [US1] Implement logic to skip datasets with <1000 cells: log warning, mark dataset as skipped in `results/status.json`. (Edge Case)
- [ ] T017 [US1] Implement logic to **continue the pipeline loop** with remaining valid datasets after a skip (T016). **Verification**: Pipeline proceeds to next dataset without halting. (Edge Case)
- [ ] T018 [US1] Add retry logic for convergence failure in scVelo with a limited number of attempts and higher regularization.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Fork-Point Identification and Ranking (Priority: P2)

**Goal**: Analyze reconstructed trajectories to detect branch points where velocity vectors diverge, extract genes at these points, and rank them by timing relative to the branch.

**Independent Test**: The system identifies at least one statistically significant branch point in the GSE dataset and outputs a ranked CSV of fork-point genes. [UNRESOLVED-CLAIM: c_aaad57d9 — status=not_enough_info]

### Tests for User Story 2 (REQUIRED)

- [ ] T019 [P] [US2] Unit test for velocity vector field divergence calculation against null distribution in `tests/unit/test_forkpoint.py`.
- [ ] T020 [P] [US2] Integration test for fork-point detection on a single dataset in `tests/integration/test_forkpoint_detection.py`.

### Implementation for User Story 2

- [ ] T020a [US2] Implement `null_distribution.py` to generate null distribution via **rotation-based null model** (rotating velocity vectors in reduced dimension space while preserving splicing kinetics) as per Plan Phase 3. **Output**: Null distribution data. (FR-004, Plan Phase 3)
- [ ] T020b [US2] Implement `forkpoint.py` divergence calculation: Compare velocity vectors against the null distribution (T020a) to identify branch points where divergence > 2.0 SD above null mean (FR-004).
- [ ] T021 [US2] Implement branch point identification logic: Flag points where divergence > 2.0 SD above null mean (FR-004).
- [ ] T022 [US2] Implement gene extraction and ranking in `forkpoint.py`: Output CSV with gene symbols, branch ID, and timing rank (1=earliest) (FR-005).
- [ ] T023 [US2] Add filtering logic to exclude branch points with divergence < 1.5 SD (flag as 'low_confidence') (Edge Case)
- [ ] T024 [US2] Implement filtering logic to ensure the output list contains genes with differential timing > 0.1 pseudotime units. **Output**: CSV with filtered genes. **Note**: Do not force a minimum of 5 genes; report the actual count found. (US-2 Acceptance Scenario 3, Edge Case)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Dataset Validation and Significance Testing (Priority: P3)

**Goal**: Validate fork-point genes across all four datasets using bootstrap resampling and verify enrichment against therapy response signatures in GSE138852.

**Independent Test**: The system performs 1000 bootstrap iterations, calculates enrichment p-values < 0.01, and generates a final report with a heatmap. [UNRESOLVED-CLAIM: c_cebb771c — status=not_enough_info]

### Tests for User Story 3 (REQUIRED)

- [ ] T025 [P] [US3] Unit test for block bootstrapping logic (patient-level) in `tests/unit/test_validate.py`.
- [ ] T026 [P] [US3] Integration test for enrichment analysis and heatmap generation in `tests/integration/test_cross_dataset_validation.py`.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `validate.py` to split data: Discovery (GSE136103, GSE127465, GSE111075) vs Validation (GSE138852) (FR-006)
- [ ] T028 [US3] Implement patient-level block bootstrapping: map patient labels to single-cell trajectories, resample patients repeatedly (FR-006)
- [ ] T029 [US3] Implement enrichment analysis against therapy response signatures from **GSE138852 responder vs. non-responder labels**; calculate p-values (FR-008, SC-006)
- [ ] T030 [US3] Generate final validation report with p-values and statistical metrics.
- [ ] T031 [US3] Implement `report.py` to generate final heatmap with bootstrap confidence intervals (FR-007)
- [ ] T032 [US3] Add associational disclaimer to the final report, explicitly **labeling all findings as associational** and including a **disclaimer section** as required by **SC-004** and **FR-005**. **Verification**: Implement a regex check (e.g., `re.search(r'associational', report_text)`) to verify the disclaimer is present in the generated report header. (SC-004, FR-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` including quickstart guide
- [ ] T034 Code cleanup and refactoring of `forkpoint.py` and `validate.py`
- [ ] T035 Performance optimization for streaming large datasets if memory > 7GB
- [ ] T036 [P] Additional unit tests for edge cases (convergence failure, low cell counts)
- [ ] T037 Run `quickstart.md` validation to ensure reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 trajectory outputs
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 fork-point outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Scripts before logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T002b, T005 which are sequential)
- T005 (Download) and T006 (Preprocess) are sequential (T006 depends on T005 output). T007 depends on T006.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for mitochondrial read filtering logic in tests/unit/test_preprocess.py"
Task: "Integration test for end-to-end scVelo run on a subset of GSE136103 in tests/integration/test_trajectory_reconstruction.py"

# Launch all models/scripts for User Story 1 together (after Foundation):
Task: "Implement velocity.py to run scVelo on CPU..."
Task: "Implement aligner.py for Markov-chain pseudotime alignment..."
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
- **Data Integrity**: Never use synthetic data; if download fails, the pipeline must fail loudly.
- **Compute Constraints**: All scVelo runs must be CPU-only; if convergence fails, retry with regularization before aborting.
- **Statistical Rigor**: Fork-point identification must use **rotation-based null model** (Plan Phase 3), not permutation shuffles.
- **Spec Correction**: T005 uses corrected dataset IDs (GSE136103...) to address the typo in FR-001.
- **Verification**: T032 includes a regex check to verify the associational disclaimer.
- **Edge Cases**: T024 does not force a minimum of 5 genes; it reports the actual count.