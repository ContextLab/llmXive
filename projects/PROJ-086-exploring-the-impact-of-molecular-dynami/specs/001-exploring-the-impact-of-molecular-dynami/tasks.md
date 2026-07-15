# Tasks: Exploring the Impact of Molecular Dynamics Simulation Parameters on Predicted Protein-Ligand Binding Affinity

**Input**: Design documents from `/specs/001-md-simulation-params/`
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

- [ ] T001 Create project structure per implementation plan (`code/simulation`, `code/analysis`, `data/raw`, `data/processed`, `results`)
- [ ] T002 Initialize Python project with `requirements.txt` containing `openmm`, `openmmtools`, `mdtraj`, `pandas`, `scipy`, `statsmodels`, `pyyaml`, `requests`, `pytest`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/io.py` for SHA256 checksumming, file I/O, and state updates (Principle V)
- [ ] T005 [P] Implement `code/utils/logger.py` for error handling, logging, and 300s timeout enforcement for 1.5ns runs
- [ ] T006 [P] Create `code/simulation/config.py` defining parameter sets (ffSB, CHARMM36m; 0.5ns, 1.0ns, 1.5ns; 300K) and random seeds
- [ ] T007 Create `code/analysis/load_data.py` to fetch PDBbind v2020 "refined" subset (≤2.0Å, ≤200 residues) from ` or a verified script <!-- ATOMIZE: requested -->
- [ ] T007a [P] Implement subsampling logic in `code/analysis/load_data.py` to select a representative subset of high-quality complexes from the fetched dataset. and save to `data/raw/subsampled_complexes.json`
- [ ] T008 Implement `code/simulation/setup.py` for system preparation: solvation (TIP3P), ion neutralization, and topology generation for a single PDB complex
- [X] T009 [P] Implement `code/analysis/stats.py` skeleton with Linear Mixed-Effects Model (LMM) structure (Complex as random intercept; ForceField, Duration as fixed effects) and variance decomposition utilities

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Parameter Sweep Execution (Priority: P1) 🎯 MVP

**Goal**: Execute controlled MD simulations on a subsampled dataset within CPU constraints to generate trajectory data.

**Independent Test**: Run a single simulation (complex 1J22, ff14SB, 1.5ns, 300K) on a 2-core CPU runner; verify `.nc` output exists and job completes < 7 mins.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. T011 depends on T012 execution but is written per TDD principles.

- [~] T010 [P] [US1] Unit test for `code/simulation/setup.py` solvation logic in `tests/unit/test_setup.py`
- [ ] T011 [US1] Integration test for full simulation pipeline (setup + run) on 1 complex in `tests/integration/test_simulation_run.py` (Depends on T012 execution; written per TDD principles) <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/simulation/run.py` using OpenMM for CPU-only MD execution with explicit solvent and a hard timeout for 1.5ns runs.
- [ ] T013 [US1] Implement batch orchestration logic in `code/main.py` to iterate over the subsampled list of complexes (from T007a) and parameter combinations (FF × 3 Dur × 1 Temp)
- [ ] T014 [US1] Add error handling in `code/main.py` to log failed runs (complex/params) and proceed to the next entry without halting
- [ ] T015 [US1] Implement `code/utils/io.py` logic to write trajectory files (`.nc` or `.xtc`) to `data/processed/` and record checksums in `state/`
- [ ] T016 [US1] Add validation to ensure trajectory files are valid and not truncated before marking the run as complete

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Affinity Estimation and Error Calculation (Priority: P2)

**Goal**: Calculate MM-PBSA/GBSA binding free energies from trajectories and compute RMSE/MAE against experimental values.

**Independent Test**: Provide a pre-generated trajectory and experimental value; verify the calculated MM-PBSA and RMSE match expected values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for `code/simulation/mm_pbsa.py` energy calculation logic with mock trajectory data in `tests/unit/test_mm_pbsa.py`
- [ ] T019 [P] [US2] Integration test for affinity estimation pipeline in `tests/integration/test_affinity_estimation.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/simulation/mm_pbsa.py` to perform MM-PBSA/GBSA post-processing on trajectory files from `data/processed/` (truncating to ≤20 frames to save RAM)
- [ ] T021 [US2] Implement `code/analysis/load_data.py` logic to map complex IDs to experimental binding constants (kcal/mol) from the PDBbind dataset
- [ ] T022 [US2] Implement `code/analysis/stats.py` logic to calculate Absolute Error (AE) for LMM input; compute RMSE and MAE as post-hoc summary metrics for each parameter combination
- [ ] T023 [US2] Add error handling in `code/simulation/mm_pbsa.py` to flag "failed analysis" for non-physical values or missing atoms without crashing
- [ ] T024 [US2] Implement data aggregation in `code/analysis/load_data.py` to write results (complex, params, energy, error) to `data/processed/analysis_results.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Sensitivity and Variance Analysis (Priority: P3)

**Goal**: Perform Linear Mixed-Effects Model (LMM) analysis to determine the impact of force field and duration on prediction error and generate variance plots.

**Independent Test**: Feed synthetic dataset with known variance contributions; verify LMM correctly identifies the dominant factor with confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for LMM model fitting in `tests/unit/test_lmm_model.py`
- [ ] T027 [P] [US3] Integration test for full statistical reporting in `tests/integration/test_statistical_analysis.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/analysis/stats.py` logic to fit a Linear Mixed-Effects Model (LMM) with `ForceField` and `Duration` as fixed effects and `Complex` as random intercept; read from `data/processed/analysis_results.csv` generated by T024
- [ ] T029 [US3] Implement `code/analysis/stats.py` logic to calculate variance components (percentage of total variance attributable to FF and Duration; note Temperature is constant and excluded)
- [ ] T030 [US3] Implement `code/analysis/viz.py` to generate variance component plots (showing FF and Duration contributions) and save them to `results/`
- [ ] T031 [US3] Implement final report generation in `code/main.py` to output a summary of fixed effect estimates, confidence intervals, and dominant uncertainty sources
- [ ] T032 [US3] Add validation to ensure statistical findings are framed as associational (observational study) with wide confidence intervals due to N=10 [UNRESOLVED-CLAIM: c_a1db0d28 — status=not_enough_info]

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `quickstart.md` with instructions for running the full pipeline on CI
- [ ] T034 Code cleanup and refactoring to ensure memory usage stays within acceptable system limits.
- [ ] T035 Performance optimization: Implement a timer wrapper in `code/main.py` that asserts total_time < 21600s (6 hours) for the full run and logs the result
- [ ] T036 [P] Additional unit tests for data validation and checksum verification in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure the pipeline executes successfully from scratch

---

## Phase 7: Review & Validation (Post-Analysis)

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical validity, and resource constraints.

- [ ] T038 [US1] Add explicit logic in `code/simulation/setup.py` to detect and skip complexes with steric clashes or missing heavy atoms that would cause solvation failure, logging them to `data/raw/skipped_complexes.log`
- [ ] T039 [US2] Implement a sanity check in `code/simulation/mm_pbsa.py` to reject binding energy estimates outside the physically plausible range, as established in prior literature (e.g., [Citation DOI/Author-Year]). and flag them as "failed analysis"
- [ ] T040 [US2] Add a fallback mechanism in `code/analysis/load_data.py` to verify the PDBbind subset contains at least 10 valid complexes [UNRESOLVED-CLAIM: c_49770151 — status=not_enough_info]; if fewer are found, raise a `DataInsufficientError` with a clear message and halt execution
- [ ] T041 [US3] Update `code/analysis/stats.py` to explicitly exclude Temperature as a factor in the LMM (since it is constant) and issue a warning in the final report that Temperature variance is zero by design
- [ ] T042 [US3] Enhance `code/analysis/viz.py` to include confidence intervals on the variance component plot, acknowledging the low statistical power (N=10) [UNRESOLVED-CLAIM: c_4e6574d6 — status=not_enough_info] and wide confidence intervals
- [ ] T043 [All] Add a resource monitoring wrapper in `code/main.py` that tracks peak RAM usage per simulation and automatically terminates the job if it exceeds 6GB to prevent CI runner crashes [UNRESOLVED-CLAIM: c_42c229c5 — status=not_enough_info]
- [ ] T044 [All] Implement a "dry-run" mode in `code/main.py` that validates the entire parameter sweep configuration and dataset availability without executing simulations, ensuring the pipeline is ready before committing CI resources

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review & Validation (Phase 7)**: Depends on completion of all User Stories and initial analysis runs

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (trajectories)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (error metrics)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Setup before services/run loops
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
Task: "Unit test for code/simulation/setup.py in tests/unit/test_setup.py"
Task: "Integration test for full simulation pipeline in tests/integration/test_simulation_run.py"

# Launch all models for User Story 1 together:
Task: "Implement code/simulation/run.py"
Task: "Implement batch orchestration in code/main.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (run 1 complex, verify output)
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
 - Developer A: User Story 1 (Simulation Engine)
 - Developer B: User Story 2 (Affinity Analysis)
 - Developer C: User Story 3 (Statistical Modeling)
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
- **Critical Constraint**: All simulation tasks must run on CPU-only CI (cores, 7GB RAM) with ≤6h total runtime. No GPU, no 8-bit models, no large LLMs.
- **Data Integrity**: All tasks must use real PDBbind data. No synthetic/fake data generation.
- **Design Note**: The design uses 1 Temperature (300K) per FR-001 and Plan Summary. The statistical analysis uses a Linear Mixed-Effects Model (LMM) instead of Three-Way ANOVA because Temperature is a constant factor.
- **Plan Deviation**: The Plan deviates from Constitution Principle VI (longer durations, variable temp) to meet CI constraints. This deviation is flagged for a future spec update.