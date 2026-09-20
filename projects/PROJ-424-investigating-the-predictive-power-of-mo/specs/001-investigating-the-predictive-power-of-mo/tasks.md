# Tasks: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

**Input**: Design documents from `/specs/001-investigating-md-diffusion-predictive-power/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [X] T001a Create `code/` directory and subdirectories (`simulation/`, `analysis/`, `reporting/`, `utils/`) at `projects/PROJ-424-investigating-the-predictive-power-of-mo/`. **Verify**: `ls -R code/`.
- [X] T001b Create `data/` directory and subdirectories (`raw/`, `processed/`, `interim/`) at `projects/PROJ-424-investigating-the-predictive-power-of-mo/`. **Verify**: `ls -R data/`.
- [X] T001c Create `tests/` directory and subdirectories (`unit/`, `integration/`) at `projects/PROJ-424-investigating-the-predictive-power-of-mo/`. **Verify**: `ls -R tests/`.
- [X] T002 Initialize Python project with dependencies: `gromacs>=2023.0`, `mdanalysis>=2.0`, `numpy>=1.24`, `pandas>=2.0`, `scipy>=1.10`, `matplotlib>=3.7`, `seaborn>=0.12`, `scikit-learn>=1.2`, `pyyaml>=6.0`, `ruff>=0.1.0`, `black>=23.0` in `projects/PROJ-424-investigating-the-predictive-power-of-mo/code/requirements.txt`. **Verify**: File exists and contains pinned versions.
- [X] T003 Configure linting (ruff) and formatting (black) tools in `projects/PROJ-424-investigating-the-predictive-power-of-mo/code/`. **Deliverables**: `projects/PROJ-424-investigating-the-predictive-power-of-mo/code/.ruff.toml` with specific rules (e.g., `E4`, `E7`, `E9`, `F`) and `projects/PROJ-424-investigating-the-predictive-power-of-mo/code/pyproject.toml` with `[tool.black]` section.

---

## Phase 2.1: Foundational Implementation (Blocking Prerequisites for User Stories)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007a Implement `code/utils/logging.py` for structured logging. **Deliverable**: A `setup_logger` function that configures a standard Python logger with JSON formatting and file output to `logs/`.
- [X] T007b Implement `code/utils/checksums.py` for artifact verification. **Deliverable**: A `calculate_sha256(file_path)` function that returns the SHA256 hash of a file.
- [ ] T036 Update `spec.md` FR-008: Change the R² threshold requirement to 0.95 to align with **Plan** and **Constitution** Principle VI. **Action**: Edit `projects/PROJ-424-investigating-the-predictive-power-of-mo/specs/001-investigating-md-diffusion-predictive-power/spec.md` to reflect the kickback. **Dependency**: None.
- [ ] T037 Update `spec.md` Assumptions: Remove the claim that NIST provides an accessible API and replace with the 'manual curation' reality described in the **Plan**. **Action**: Edit `projects/PROJ-424-investigating-the-predictive-power-of-mo/specs/001-investigating-md-diffusion-predictive-power/spec.md` Assumptions section. **Dependency**: None.
- [ ] T038 Update `spec.md` SC-005: Remove the 'bootstrap difference-of-means test (p ≤ 0.05)' requirement and replace with 'descriptive trend analysis' and 'CI overlap check' to align with **Plan**. **Action**: Edit `projects/PROJ-424-investigating-the-predictive-power-of-mo/specs/001-investigating-md-diffusion-predictive-power/spec.md` Success Criteria section. **Dependency**: None.
- [ ] T005 Implement `code/config.py` to define parameters: solvents (water, ethanol, acetone), timescales (ns-scale intervals), force field (MARTINI), and **R² threshold = 0.95**. **Action**: Define `SCALING_FACTORS` as a dictionary with keys 'water', 'ethanol', 'acetone' and **hardcoded values**: `{'water': 1.23, 'ethanol': 0.85, 'acetone': 1.15 }` (derived from standard MARTINI literature). **Constraint**: **Verify**: `config.py` contains valid float values for all solvents and the R² threshold is 0.95. **Dependency**: T007a/b must be complete; **T036 must be complete**.
- [ ] T006a Generate `data/raw/nist_refs.json` with sample experimental diffusion coefficients for water, ethanol, and acetone. **Action**: Create a JSON file with the schema: `[{"solvent": "string", "temperature": number, "value": number, "source": "string"}]`. Populate with realistic values (e.g., Water: a diffusion coefficient on the order of 10⁻⁹ m²/s at 298K). **Verify**: File exists and is valid JSON. **Dependency**: None.
- [ ] T006c Implement `code/utils/data_validator.py` to validate the existence, schema, and checksum of `data/raw/nist_refs.json`. **Action**: Write a script that checks if the file exists, validates the JSON schema, and verifies the checksum. **Constraint**: The script MUST fail loudly (raise FileNotFoundError or ValidationError) if the file is missing or malformed. **Do NOT attempt network fetch**. **Verify**: Script raises an error if file is missing, checksum mismatch, or schema invalid. **Dependency**: T006a must be complete.
- [ ] T006b Load experimental diffusion coefficients from `data/raw/nist_refs.json` at `projects/PROJ-424-investigating-the-predictive-power-of-mo/data/raw/nist_refs.json`. **Action**: Write a script `code/utils/data_loader.py` that reads the JSON file, validates the schema (solvent, temperature, value), and loads it into memory. **Constraint**: The script MUST fail loudly (raise FileNotFoundError or ValidationError) if the file is missing or malformed. **Do NOT attempt network fetch**. **Output**: Validated data structure in memory. **Note**: This task implements the Plan's 'manual curation' strategy due to the absence of a programmatic NIST API. **Dependency**: T006c must be complete; **T037 must be complete**.

- [ ] T009a Create base schema for `diffusion_results` in `code/data_models/diffusion_results.yaml`.
- [ ] T009b Create base schema for `bootstrap_stats` in `code/data_models/bootstrap_stats.yaml`.
- [ ] T009c Create base schema for `sensitivity_report` in `code/data_models/sensitivity_report.yaml`.
- [ ] T010 Generate `contracts/*.schema.yaml` files for data validation. **Deliverables**: `contracts/diffusion_results.yaml`, `contracts/bootstrap_stats.yaml`, `contracts/sensitivity_report.yaml`. **Note**: Depends on T009.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Timescale-Accuracy Curves for Simple Liquids (Priority: P1) 🎯 MVP

**Goal**: Execute MD simulations for water, ethanol, acetone at varying time scales to assess convergence.; extract MSD; calculate diffusion coefficients; compare to NIST benchmarks; generate timescale-accuracy plot.

**Independent Test**: Run the pipeline for water at early, intermediate, and late time steps.; verify MAE calculation against `data/raw/nist_refs.json`; produce a plot of MAE vs. Simulation Duration.

### Tests for User Story 1 (TDD-First - Write BEFORE implementation) ⚠️

- [X] T011 [US1] Unit test for MSD extraction logic in `tests/unit/test_msd.py`. **Must fail before T016**.
- [X] T012 [US1] Unit test for diffusion coefficient calculation and scaling in `tests/unit/test_msd.py`. **Must fail before T016**.
- [X] T013 [US1] Unit test for MAE calculation against NIST refs in `tests/unit/test_analysis.py`. **Must fail before T018**.

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement `code/simulation/topology.py` to generate MARTINI topology files (.gro,.top) for water, ethanol, and acetone. **Deliverable**: Files saved to `data/raw/topologies/`.
- [X] T015 [US1] Implement `code/simulation/runner.py` to execute GROMACS/LAMMPS simulations with a timeout (time limit), density convergence check (±1% over 200ps), and non-equilibration flagging. **Must load specific.gro,.top, and.mdp files** from `data/raw/topologies/` generated by T014. **Depends on T014 completion** (must wait for topology files). **Uses R² threshold from `code/config.py` (0.95)** for validity checks. **Must flag non-linear MSD trajectories as invalid and exclude them from results**. **Density Check**: Extract density from `energy.edr` using `gmx energy -f energy.edr -o density.xvg` or `MDAnalysis.analysis.density` to verify stability. **Dependency**: T036 must be complete.
- [X] T016 [US1] Implement `code/analysis/msd.py` to:
 - Extract MSD trajectory from simulation output
 - Perform linear regression (MSD vs. time)
 - Validate linearity using **R² threshold from `code/config.py` (0.95)** (citing **Spec Kickback T036** as the authority for this update to Spec FR-008)
 - Calculate diffusion coefficient and apply solvent-specific scaling factors
 - **Raise an exception** if R² < 0.95 to prevent non-linear MSDs from contaminating results. **Dependency**: T036 must be complete.
- [X] T017 [US1] Implement `code/reporting/plots.py` to generate timescale-accuracy curves (MAE vs. Duration) with uncertainty bands
- [X] T018 [US1] Implement `code/main.py` pipeline entry point to orchestrate: topology gen → simulation → MSD extraction → diffusion calc → MAE calculation → plotting

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Methodological Rigor via Sensitivity Analysis (Priority: P2)

**Goal**: Verify robustness of diffusion coefficient estimation by sweeping regression start times (early fractions of trajectory length) and confirming variance < 5%.

**Independent Test**: Run sensitivity analysis on an ethanol trajectory; verify variance in calculated D values across start times; generate sensitivity report.

### Tests for User Story 2 (TDD-First - Write BEFORE implementation) ⚠️

- [X] T019 [US2] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`. **Must fail before T021**.
- [X] T020 [US2] Integration test for variance threshold check in `tests/integration/test_sensitivity.py`. **Must fail before T021**.

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/analysis/sensitivity.py` to:
 - Sweep regression start times at **0.1, 0.2, and 0.3** of total trajectory length. **Note**: These values resolve the '[deferred]' status in Spec SC-003 per the **Plan**'s approved kickback.
 - Calculate diffusion coefficient for each start time
 - Compute variance and flag if > 5%
 - Output `sensitivity_report` schema
- [X] T022 [US2] Integrate sensitivity analysis into `code/main.py` (runs after primary analysis for each solvent-timescale)
- [X] T023 [US2] Add logging for sensitivity results in `code/utils/logging.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Full Batch Analysis with Statistical Confidence Intervals (Priority: P3)

**Goal**: Run full batch (solvents × multiple timescales); perform bootstrap resampling (1000 iterations, with a fallback to 100); generate summary table with confidence intervals; perform descriptive trend analysis.

**Independent Test**: Execute full pipeline; verify `bootstrap_stats.csv` contains mean MAE and 95% CI for all solvent-timescale combinations; verify final report includes trend analysis.

### Tests for User Story 3 (TDD-First - Write BEFORE implementation) ⚠️

- [X] T024 [US3] Unit test for bootstrap resampling logic in `tests/unit/test_bootstrap.py`. **Must fail before T026**.
- [X] T025 [US3] Unit test for CI calculation and fallback logic in `tests/unit/test_bootstrap.py`. **Must fail before T026**.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis/bootstrap.py` to:
 - Perform **1000 iterations** of bootstrap resampling on MAE distribution.
 - **Fallback**: Reduce to **100 iterations** if wall-clock time > 5.5h. **Timer Logic**: Start timer at the beginning of the bootstrap loop. Check elapsed time before each iteration; if > 5.5h, set iterations to 100 and stop adding new iterations.
 - Calculate confidence intervals (percentile method)
 - Output `bootstrap_stats.csv`
- [X] T027 [US3] Implement `code/reporting/tables.py` to generate summary table with mean MAE, 95% CI, and **descriptive trend analysis** and **CI overlap check** for 1ns vs 10ns improvement. **Constraint**: **Do NOT** implement a bootstrap difference-of-means test (p-value) due to N=3 limitations per **Plan** (Critical Spec Kickbacks). **Output must include**: 'MAE_1ns', 'MAE_10ns', 'Reduction %', 'Trend Direction', 'CI Overlap Status'. **Cite Plan** as the authority for the fallback strategy. **Depends on T026.** **Dependency**: T038 must be complete.
- [X] T028 [US3] Integrate full batch execution into `code/main.py` (loop over solvents × timescales)
- [X] T029 [US3] Update `code/main.py` to handle NIST reference missing values: **skip** the specific solvent-timescale combination and **log a warning** (do not crash).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [P] Documentation updates in `projects/PROJ-424-investigating-the-predictive-power-of-mo/README.md` and `quickstart.md`
- [X] T031 Code cleanup and refactoring in `code/`
- [X] T032 Performance optimization for bootstrap resampling (vectorization)
- [X] T033 [P] Additional unit tests for edge cases (non-linear MSD, missing refs) in `tests/unit/`
- [X] T034 Run quickstart.md validation to ensure end-to-end execution. **Action**: Execute `python code/main.py` against the full pipeline and verify all outputs match expected formats.
- [X] T035 Generate final report artifact in `data/processed/final_report.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2.1)**: Depends on Setup completion - BLOCKS all user stories
 - **T007a/b** (Utils) must be completed before **T005** (Config) and **T006c** (Data Validation) and **T006b** (Data Load) as they provide logging and checksum functions.
 - **T006a** (Generate JSON) must be completed before **T006c** (Validation).
 - **T006c** (Validation) must be completed before **T006b** (Loading) to ensure the file exists and is valid before reading.
 - **T036, T037, T038** (Spec Updates) must be completed before **T005, T006b, T006c, T016, T027** respectively.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2.1) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2.1) - **Depends on T015 (US1) completion** for MSD extraction logic. T021 cannot run in parallel with T015.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2.1) - Depends on T015 (US1) results (diffusion coefficients)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (TDD-First)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2.1), **except**:
 - **T007a/b** must precede **T005**, **T006c**, **T006b**.
 - **T006a** must precede **T006c**.
 - **T006c** must precede **T006b**.
 - **T036, T037, T038** must precede their dependent tasks.
 - **T005** and **T006c** are **NOT** parallel-safe with T007a/b.
 - **T006c** is **NOT** parallel-safe with T006b.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (TDD-First)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **T014** and **T015** are **NOT** parallel-safe due to file dependency.
- **T026** and **T027** are **NOT** parallel-safe due to data dependency.
- **T010** is **NOT** parallel-safe with **T009**.

### Critical Intra-Phase Dependencies (Phase 5)

- **T026 (Bootstrap)** must complete before **T027 (Summary Table)** can start. T027 consumes the output of T026.
- **T027** is **NOT** parallel-safe with T026.
- **T010 (Generate Contracts)** must follow T009 (Schema Definition). **T010** is **NOT** parallel-safe with T009.
- **T015 (Simulation Runner)** must follow T014 (Topology Generation). **T015** is **NOT** parallel-safe with T014.
- **T036 (Spec Update)** must complete before **T005** and **T016**.
- **T037 (Spec Update)** must complete before **T006b** and **T006c**.
- **T038 (Spec Update)** must complete before **T027**.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (TDD-First):
Task: "Unit test for MSD extraction logic in tests/unit/test_msd.py"
Task: "Unit test for diffusion coefficient calculation and scaling in tests/unit/test_msd.py"

# Launch all models for User Story 1 together:
Task: "Implement code/simulation/topology.py"
Task: "Implement code/analysis/msd.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2.1: Foundational (CRITICAL - blocks all stories)
 - **Ensure T006a (Generate JSON) is completed** to provide ground truth with real data.
 - **Ensure T006c (Validation) is completed** before T006b (Loading).
 - **Ensure T036, T037, T038 are completed** to update the spec.
 - **Ensure T005 sets R²=0.95** to align with Plan and Constitution.
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
- **Critical**: All simulation tasks MUST use MARTINI force field or reduced system size to meet h runtime limit (FR-007).
- **Critical**: All data loading MUST use the curated `nist_refs.json` file; T006c validates existence, T006b loads it. NO synthetic fallbacks.
- **Critical**: Bootstrap iterations MUST fallback to 100 if wall-clock time > 5.5h (FR-004).
- **Critical**: T026 (Bootstrap) must strictly precede T027 (Summary Table) within Phase 5.
- **Critical**: T001 is split into T001a, T001b, T001c for executability.
- **Critical**: T021 uses concrete values 0.1, 0.2, 0.3 for sensitivity analysis (Plan authority).
- **Critical**: T027 explicitly defines output format for descriptive trend analysis (Plan authority).
- **Critical**: T016 uses R²=0.95 from config (Plan/Constitution authority).
- **Critical**: T006b loads curated JSON to ensure reproducibility.
- **Critical**: T014 (Topology) must precede T015 (Simulation) due to file dependency.
- **Critical**: T007a/b (Utils) must precede T005 (Config) and T006c (Validation) and T006b (Data Load) due to function dependency.
- **Critical**: T006a (Generate JSON) must precede T006c (Validation).
- **Critical**: T006c (Validation) must precede T006b (Loading).
- **Critical**: T036, T037, T038 (Spec Updates) must precede T005, T006b, T006c, T016, T027 respectively.
- **Critical**: T005 and T006c are NOT parallel-safe with T007a/b.
- **Critical**: T006c is NOT parallel-safe with T006b.
- **Critical**: T015 is NOT parallel-safe with T014.
- **Critical**: T027 is NOT parallel-safe with T026.
- **Critical**: T010 is NOT parallel-safe with T009.
- **Kickback Note**: Plan acknowledges contradiction between spec.md FR-001 (download) and manual curation strategy; Plan acknowledges contradiction between spec.md FR-008 (0.99) and Plan's 0.95; Plan acknowledges contradiction between spec.md SC-005 (p-value) and Plan's trend analysis. **Tasks T036, T037, T038 now MUST be completed** to update the spec. T005, T006b, T006c, T016, T027 depend on these spec updates. T006a generates the JSON file. T006c validates it. T006b loads it. T005 and T016 implement the 0.95 threshold per Plan. T027 implements descriptive trend analysis. T036, T037, T038 update the Spec to reflect these changes.