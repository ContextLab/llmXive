# Tasks: Exploring the Impact of Cosmic Microwave Background Anomalies on Early Universe Simulations

**Input**: Design documents from `/specs/001-cmb-anomaly-lss-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY - they correspond to the Independent Test scenarios defined in the User Stories.

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

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `state/`, `contracts/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, scipy, astropy, healpy, camb, nbodykit, fitsio, requests, pytest)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Create versioning utility (`code/utils/versioning.py`) to calculate SHA256 hashes for all artifacts and update `state/projects/PROJ-036-exploring-the-impact-of-cosmic-microwave/artifact_hashes.yaml` (extract project ID from config)
- [X] T005 [P] Implement citation validation utility (`code/utils/validate_citations.py`) to check `research.md` URLs against verified datasets <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T006 [P] Setup environment configuration management (load `config/lambdacdm.yaml` and `config/anomaly.yaml`)
- [X] T007 Create base cosmology constants module (`code/utils/cosmology.py`)
- [ ] T008 Configure error handling and logging infrastructure (ensure memory/disk limits are monitored)
- [ ] T009 Create schema validation contract (`contracts/cmb_lss_schema.schema.yaml`) for statistical outputs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Validate Planck CMB Maps (Priority: P1) 🎯 MVP

**Goal**: Download Planck CMB temperature maps (Commander/SMICA) from the Planck Legacy Archive, validate checksums, and confirm anomaly regions exist.

**Independent Test**: Verify files exist, checksums match official hashes, Nside ≥ 256 in FITS headers, and galactic mask application works.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data download integrity in `code/tests/test_data_validation.py` (function: `test_download_checksums_match` asserts that the calculated SHA256 hash of the downloaded file matches the value in config/planck_checksums.yaml) <!-- FAILED: unspecified -->
- [ ] T011 [P] [US1] Integration test for Planck map loading and masking in `code/tests/test_data_validation.py` (function: `test_chunked_map_loading_and_mask` asserts Nside ≥ 256 and galactic mask application without OOM)

### Implementation for User Story 1

- [X] T012 [US1] Implement data downloader in `code/01_data_download.py` (handles retries, backoff, and checksum validation using values from config/planck_checksums.yaml)
- [X] T012b [US1] Pre-populate `config/planck_checksums.yaml` with official SHA256 hashes for Planck PR3 Commander/SMICA maps (manual step or script to fetch from verified source)
- [X] T013b [US1] Implement chunked FITS streaming loader in `code/utils/io.py` to process full-sky map data without OOM on constrained memory resources

The research question remains: Can full-sky map data be processed without out-of-memory errors on constrained memory resources?
The method remains: Optimization of memory allocation and streaming algorithms for large-scale sky surveys.
References: [DOI/arXiv/author-year]
- [X] T013 [US1] Implement FITS header validation in `code/utils/io.py` (assert Nside ≥ 256, validate that downloaded maps contain known Cold Spot and low-quadrupole regions using coordinates from config/anomaly.yaml) <!-- SKIPPED: YAML+regex parse failed (while scanning a simple key
 in "<unicode string>", line 8, column 1:
 The implementation uses `astropy...
 ^
could not find expected ':'
 in "<unicode string>", line 8, column 243:
... hs and real configuration files.
 ^) -->
- [X] T014 [US1] Implement galactic mask application (|b| > 5°) in `code/01_data_download.py`
- [X] T014b [US1] Validate galactic mask application in `code/tests/test_data_validation.py` (function: `test_mask_application` asserts that the mask correctly removes pixels with |b| ≤ 5°)
- [~] T015 [US1] Integrate with versioning utility to hash raw data in `data/raw/`
- [~] T016 [US1] Add error handling for network failures and corrupted files

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Generate Modified Initial Conditions (Priority: P2)

**Goal**: Generate anomaly-modified power spectra using CAMB with Phase-Injected Mode strategy and create initial condition files.

**Independent Test**: Verify power spectrum deviation at ℓ ≤ 30 is logged, and IC files conform to GADGET-2/nbodykit format and size limits.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T018 [P] [US2] Contract test for power spectrum modification in `code/tests/test_power_spectrum.py` (function: `test_phase_injected_mode` asserts deviation at ℓ ≤ 30 is logged)
- [ ] T019 [P] [US2] Integration test for IC file generation in `code/tests/test_power_spectrum.py` (function: `test_ic_file_format` asserts GADGET-2/nbodykit format compliance and file size < 50 MB for ³ configuration)

### Implementation for User Story 2

- [ ] T020 [US2] Implement CAMB configuration loader in `code/utils/cosmology.py` (loads `config/lambdacdm.yaml` and `config/anomaly.yaml` to define standard and anomaly-modified parameters)
- [ ] T021 [US2] Implement Phase-Injected Mode strategy in `code/02_power_spectrum.py` (injects the Cold Spot phase mode into the standard power spectrum using the mode-coupling approximation defined in Planck 2018 Results Paper VII)
- [ ] T021b [US2] Implement mode-coupling approximation logic in `code/02_power_spectrum.py` (calculate and validate low-ℓ coupling coefficients to ensure the approximation error is within bounds)
- [ ] T022 [US2] Log deviation from standard ΛCDM at ℓ ≤ 30 in `code/02_power_spectrum.py`
- [ ] T023a [US2] Generate anomaly-modified ICs in `code/03_initial_conditions.py` (output GADGET-2/nbodykit format for the anomaly simulation)
- [ ] T023b [US2] Generate standard ΛCDM control ICs in `code/03_initial_conditions.py` (output GADGET-2/nbodykit format for the control simulation)
- [ ] T024 [US2] Enforce disk space check (≤ 50 MB) and abort if exceeded
- [ ] T025 [US2] Validate IC files for unphysical values (negative power) before simulation launch

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Run Simulations and Extract Statistics (Priority: P3)

**Goal**: Run paired N-body simulations (anomaly + control) on CPU, extract LSS statistics, and perform diagnostic statistical comparisons.

**Independent Test**: Verify simulation completes within 12h/7GB RAM, extracts power spectrum/void stats, and outputs KS/Chi-squared diagnostic metrics.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T037 [P] [US3] Contract test for simulation runner in `code/tests/test_simulation_runner.py` (function: `test_simulation_runtime_limit` asserts ≤ 12h limit by mocking simulation duration)
- [ ] T038 [P] [US3] Integration test for statistical extraction in `code/tests/test_statistics.py` (function: `test_statistical_extraction` asserts KS/Chi-squared outputs and delta values)

### Implementation for User Story 3

- [ ] T026 [US3] Implement simulation orchestrator in `code/04_simulation_runner.py` (runs paired grid-based simulations using ICs from T023a and T023b)
- [ ] T027 [US3] Enforce CPU-only execution and memory monitoring (abort if > 7GB RAM)
- [ ] T027b [US3] Measure and log simulation runtime/RAM to `data/results/metrics.yaml` in `code/04_simulation_runner.py` (records actual wall-clock time and peak RAM usage)
- [ ] T028 [US3] Implement LSS statistics extractor in `code/05_statistics.py` (matter power spectrum, void size distributions)
- [ ] T029 [US3] Implement diagnostic statistical tests (Kolmogorov-Smirnov, Chi-squared) in `code/05_statistics.py`
- [ ] T030 [US3] Implement Benjamini-Hochberg multiple-comparison correction in `code/05_statistics.py` (applied to generate diagnostic metrics, not inferential p-values, due to N=1 limitation)
- [ ] T031 [US3] Output delta values (anomaly minus control) and diagnostic p-values to `data/results/`
- [ ] T031b [US3] Output corrected p-values to `data/results/metrics.yaml` (explicitly logs the Benjamini-Hochberg corrected values required by SC-002)
- [ ] T032 [US3] Tag all output metadata with classification: associational (diagnostic) (explicitly frames results as diagnostic metrics to resolve N=1 contradiction)
- [ ] T033 [US3] Implement sensitivity analysis sweep for p-value thresholds across a range of conventional significance levels and output results to `data/results/sensitivity_analysis.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Visualization & Reporting (Polish)

**Purpose**: Generate plots and finalize research artifacts

- [ ] T034 [P] [Polish] Implement visualization module in `code/06_visualization.py` (power spectrum plots, void distributions)
- [ ] T035 [Polish] Generate final research report in `specs/001-cmb-anomaly-lss-impact/research.md` citing only `data/results/` artifacts and verified datasets from `# Verified datasets` block (validated by Reference-Validator Agent)
- [ ] T036 [Polish] Run quickstart.md validation and update documentation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data availability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 IC files

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
Task: "Contract test for data download integrity in code/tests/test_data_validation.py"
Task: "Integration test for Planck map loading and masking in code/tests/test_data_validation.py"

# Launch all models for User Story 1 together:
Task: "Implement data downloader in code/01_data_download.py"
Task: "Implement FITS header validation in code/utils/io.py"
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
- **Feasibility Constraint**: All tasks must run on GitHub Actions free-tier (Multiple CPU, 7GB RAM, 14GB Disk). No GPU, no 8-bit models, no large LLMs.
- **Data Integrity**: No fake data. All inputs must come from real Planck Legacy Archive or verified sources.
- **Statistical Framing**: All p-values are diagnostic metrics due to N=1, not inferential significance tests.
- **Spec Contradiction Note**: The spec's Success Criteria (SC-003/SC-004) reference a ³/500 Mpc/h configuration, but the plan downsizes to 128³/250 Mpc/h for feasibility. Tasks reflect the plan's downsized reality. This contradiction requires a spec update (kickback).