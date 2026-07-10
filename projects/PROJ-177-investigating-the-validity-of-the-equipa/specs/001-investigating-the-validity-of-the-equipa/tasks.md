# Tasks: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

**Input**: Design documents from `/specs/001-investigate-equipartition-granular-systems/`
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
  - Delivered as a MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` in `projects/PROJ-177-investigating-the-validity-of-the-equipa/` by executing: `mkdir -p code/data code/analysis code/utils data/raw data/processed data/results tests/unit tests/integration tests/contract`.
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` at `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/` containing `pandas`, `numpy`, `scipy`, `scikit-learn`, `pyyaml`, `tqdm`, `pytest`.
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `.pre-commit-config.yaml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/config.py` defining constants: `g=9.81`, `r_default=0.0025` (2.5mm), `chunk_size=100000`, `mass_density_map` (dict mapping material types to density), and `I_FORMULA_COEFF = 0.4` (for $I = \frac{2}{5}mr^2$).
- [ ] T005 [P] Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/utils/logging.py` with structured logging setup.
- [ ] T006 [P] Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/utils/validators.py` to validate input schema (x, y, z, theta, timestamp, mass optional) per FR-006.
- [ ] T008 Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/data/loader.py` with chunked CSV/Parquet ingestion (100k frames per chunk, float32 dtypes) to ensure ≤7GB RAM usage for 1M+ frames per SC-004.
- [ ] T009 Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/data/synchronizer.py` to align particle timestamps with driving signal logs, handling missing logs per AC-3.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Energy Component Extraction and Aggregation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw particle data and driving signals, compute $E_{trans}$ and $E_{rot}$ via finite differences, and aggregate by frequency bin.

**Independent Test**: Run pipeline on small synthetic CSV with known kinematics; verify output JSON/CSV matches exact calculated energy values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for energy calculation formulas in `projects/PROJ-177-investigating-the-validity-of-the-equipa/tests/unit/test_energy_calc.py` using hardcoded values.
- [ ] T011 [P] [US1] Integration test for missing driving signal error handling in `projects/PROJ-177-investigating-the-validity-of-the-equipa/tests/integration/test_synchronizer.py`.
- [ ] T007 [US1] Create `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/data/synthetic.py` generator to produce synthetic granular data with friction coupling for logic testing. **Deliverable**: Generate `projects/PROJ-177-investigating-the-validity-of-the-equipa/data/raw/synthetic_test.csv` with exactly 100 rows and verify friction coupling logic is present in the output.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/data/processor.py` function `calc_velocities(df)` to calculate finite-difference velocities ($v, \omega$) from positions/orientations per FR-001. **Output**: DataFrame with columns `vx, vy, vz, omega`.
- [ ] T013a [US1] Implement mass derivation logic in `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/data/processor.py` using material type and `r_default` (2.5mm) to calculate mass ($m = \frac{4}{3}\pi r^3 \rho$) if missing per FR-006. **Input**: Material type string. **Output**: Mass value.
- [ ] T013b [US1] Implement moment of inertia derivation in `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/data/processor.py` using $I = \frac{2}{5}mr^2$ (using `I_FORMULA_COEFF` from T004) for particles where $I$ is missing per Spec Assumptions. **Requires**: T004 (constants) and T013a (mass).
- [ ] T012b [US1] Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/data/processor.py` function `calc_energies(df)` to calculate $E_{trans} = 0.5 \cdot m \cdot v^2$ and $E_{rot} = 0.5 \cdot I \cdot \omega^2$ using velocities from T012 and mass/I from T013a/T013b. **Output**: DataFrame with columns `E_trans, E_rot, E_pot`.
- [ ] T014 [US1] Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/binning.py` to group energy data into fine-grained intervals and handle 0Hz exclusion per FR-002.
- [ ] T015 [US1] Ensure `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/data/processor.py` calculates $E_{pot}$ for diagnostics but excludes it from the ratio test per FR-001.
- [ ] T016 [US1] Add validation for missing frames and interpolation logic in `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/data/processor.py` per Edge Cases.
- [ ] T017 [US1] Create CLI entry point `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/main.py` to orchestrate ingestion (loader), synchronization, processing, and binning. **Args**: `--input`, `--output`, `--config`. **Exit**: 0 on success, 1 on error. **Note**: This task must call existing modules (loader.py, synchronizer.py, processor.py, binning.py) and NOT re-implement their logic.
- [ ] T018 [US1] Run end-to-end US1 pipeline on synthetic data (`projects/PROJ-177-investigating-the-validity-of-the-equipa/data/raw/synthetic_test.csv`) using the CLI (T017) and verify output `projects/PROJ-177-investigating-the-validity-of-the-equipa/data/processed/energies.csv` contains correct energy values.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Statistical Deviation Analysis (Priority: P2)

**Goal**: Compare observed mean energies against equipartition prediction (1:1 ratio) using Paired t-tests, KS tests, ANOVA, and Regression.

**Independent Test**: Feed dataset with perfect equipartition (p > 0.05) and biased dataset (p < 0.01); verify t-test results match expectations.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for Paired t-test logic in `projects/PROJ-177-investigating-the-validity-of-the-equipa/tests/unit/test_stats.py` using synthetic paired data.
- [ ] T020 [P] [US2] Integration test for Holm-Bonferroni correction in `projects/PROJ-177-investigating-the-validity-of-the-equipa/tests/integration/test_pipeline.py`.

### Implementation for User Story 2

**⚠️ CRITICAL DEPENDENCY**: Tasks T020, T021, T022, T023, T024, T024b, T025, T026 **MUST** wait for T014 (binning) completion. Do not start US2 implementation until US1 binning is verified.

- [ ] T020 [US2] Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/stats.py` function `paired_t_test(df)` to compare mean translational vs rotational energy (null hypothesis 1:1 ratio) per FR-003. **Return**: Dict with keys `statistic`, `pvalue`, `method`. **(Requires T014)**.
- [ ] T020a [US2] Add explicit comment/logic in `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/stats.py` stating that SC-001 is validated on synthetic data as a 'logic validation' (verifying the pipeline detects deviation) rather than a scientific measurement of real-world physics, per Plan Scope Note.
- [ ] T020b [US2] Implement documentation in `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/stats.py` explicitly noting the deviation from FR-003's "Two-Sample t-test" requirement to "Paired t-test" due to statistical validity of paired observations, referencing the plan's justification.
- [ ] T021 [US2] Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/stats.py` function `kolmogorov_smirnov_test(df)` to compare distributions per Constitution Principle VII. **(Requires T014)**.
- [ ] T021b [US2] Add explicit comment in `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/stats.py` linking KS test implementation to Constitution Principle VII, distinguishing it from FR-003's explicit list.
- [ ] T022 [US2] Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/stats.py` function `anova_test(df)` for multi-group comparisons across material types per FR-003. **(Depends on T014 binning output)**.
- [ ] T023 [US2] Implement Holm-Bonferroni correction logic in `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/stats.py` for multiple comparisons per FR-004.
- [ ] T024 [US2] Implement linear regression in `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/stats.py` relating energy deviation to driving frequency and material type per FR-007.
- [ ] T024b [US2] Implement linear regression in `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/stats.py` against a 'roughness' parameter (derived from material type proxy mapping) per Constitution Principle VII.
- [ ] T025 [US2] Implement significance testing for regression coefficients in `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/stats.py` per FR-007.
- [ ] T026 [US2] Aggregate all statistical results into `projects/PROJ-177-investigating-the-validity-of-the-equipa/data/results/statistical_output.json`. **Schema**: JSON object with keys `bins`, `tests`, `summary`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Sensitivity Analysis of Thresholds (Priority: P3)

**Goal**: Sweep significance threshold $\alpha$ over $\{0.01, 0.05, 0.10\}$ and report stability of "significant deviation" classification.

**Independent Test**: Run analysis on fixed dataset with three thresholds; verify output table correctly reflects changing counts of significant bins.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for threshold classification logic in `projects/PROJ-177-investigating-the-validity-of-the-equipa/tests/unit/test_sensitivity.py`.

### Implementation for User Story 3

- [ ] T028 [US3] Implement `projects/PROJ-177-investigating-the-validity-of-the-equipa/code/analysis/sensitivity.py` to sweep $\alpha \in \{0.01, 0.05, 0.10\}$ per FR-005.
- [ ] T029 [US3] Implement logic to count "significant deviation" bins for each threshold per FR-005.
- [ ] T030 [US3] Generate summary table in `projects/PROJ-177-investigating-the-validity-of-the-equipa/data/results/sensitivity_report.csv` showing stability of conclusions per AC-3. **Headers**: `threshold`, `significant_bins`, `total_bins`.
- [ ] T031 [US3] Add explicit "stability" statement in report if conclusions change across thresholds per AC-3.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T032 [P] Documentation updates in `README.md` and `quickstart.md`.
- [ ] T033 Code cleanup and refactoring for memory efficiency.
- [ ] T034 Profile memory usage with 1M frames in `projects/PROJ-177-investigating-the-validity-of-the-equipa/data/raw/` and validate 100k chunk size sufficiency per SC-004. **Action**: If memory > 6GB, refactor `loader.py` to reduce `chunk_size` to 50k.
- [ ] T034b [P] Validate that the full pipeline (ingestion, processing, analysis) processes 1M frames within 6 hours on CPU-only runner per SC-004, explicitly verifying the chunked processing logic (100k frames/chunk) is active.
- [ ] T035 [P] Additional unit tests for edge cases (missing frames, 0Hz) in `projects/PROJ-177-investigating-the-validity-of-the-equipa/tests/unit/`.
- [ ] T036 Run `quickstart.md` validation to ensure full pipeline reproducibility.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **MUST WAIT** for US1 binning output (T014)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (p-values)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services
- Services before endpoints/CLI
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- **US2 cannot start until T014 (binning) is complete**, even if other US1 tasks are done.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only after their specific dependencies are met**.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for energy calculation formulas in tests/unit/test_energy_calc.py"
Task: "Integration test for missing driving signal error handling in tests/integration/test_synchronizer.py"

# Launch all models for User Story 1 together:
Task: "Create config.py in code/config.py"
Task: "Create validators.py in code/utils/validators.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (T018)
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
   - Developer A: User Story 1 (T007, T012-T018)
   - Developer B: User Story 2 (T020-T026) **MUST WAIT** for T014 completion
   - Developer C: User Story 3 (T028-T031)
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