# Tasks: Investigating the Relationship Between Stellar Flare Frequency and Exoplanet Atmospheric Retention

**Input**: Design documents from `/specs/001-stellar-flare-atmospheric-retention/`
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

- [ ] T001 Create project directory structure: `code/`, `tests/`
- [ ] T002 Create project directory structure: `data/raw/`, `data/processed/`, `data/results/`, `data/logs/`, `contracts/`
- [X] T003 [P] Create `code/__init__.py` to ensure all modules import correctly without circular dependencies
- [ ] T004 [P] Create `requirements.txt` with pinned versions: `requests`, `pandas`, `numpy`, `scipy`, `astropy`, `matplotlib`, `pyyaml`, `astroquery`, `pytest`, `pingouin`
- [ ] T005 [P] Create virtual environment and install dependencies from `requirements.txt`
- [ ] T006 [P] Create `contracts/dataset.schema.yaml` defining the input/output schema specifically for `data/processed/merged_filtered.csv` (star_id, flare_count, radius, mass, semi_major_axis, density, age)
- [~] T007 [P] Create `contracts/results.schema.yaml` defining the output schema for correlation results (ρ_partial, p-value, sensitivity data structure)
- [~] T008 [P] Configure linting (flake8/pylint) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T009 Create `code/config.py` defining physical constants (G, solar units), API base URLs, retry parameters (configurable maximum, backoff 1s), and default thresholds (efficiency η=0.15, K_tide=1.0, f_XUV=0.1, M_ATM_INITIAL_BASELINE=0.01)
- [~] T010 [P] Create `code/utils.py` with retry logic (exponential backoff), checksumming functions, and structured logging for API provenance (writing to `data/logs/api_log.jsonl`)
- [~] T010a [P] Define `DEFAULT_M_DWARF_AGE` in `code/config.py` as a representative median age for M-dwarfs based on literature. and add a comment citing the source, ensuring compliance with SC-006

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Filter Multi-Source Astrophysical Data (Priority: P1) 🎯 MVP

**Goal**: Automatically retrieve stellar flare catalogs from MAST (TESS) and exoplanet parameters from NASA Exoplanet Archive, merge by host ID, and filter for M-dwarfs with ≥10 flares.

**Independent Test**: Execute `code/data_ingestion.py` and verify `data/processed/merged_filtered.csv` contains the expected columns and excludes records with missing mass/radius or <10 flares, without running physics models.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T011 [P] [US1] Unit test for API retry logic in `tests/test_utils.py` (mock rate limit responses)
- [~] T012 [P] [US1] Unit test for data filtering logic in `tests/test_data_ingestion.py` (mock API responses with known M-dwarfs and non-M-dwarfs)

### Implementation for User Story 1

- [~] T013 [US1] Implement `code/data_ingestion.py` function `fetch_flare_catalog`: Fetch flare events from MAST TESS Stellar Flare Catalog using `astroquery` or `requests` (FR-001)
- [~] T014 [US1] Implement `code/data_ingestion.py` function `fetch_exoplanet_params`: Fetch exoplanet parameters from NASA Exoplanet Archive (FR-001)
- [~] T015 [US1] Implement `code/data_ingestion.py` function `merge_datasets`: Join flare counts with planet parameters by `host_star_id`
- [~] T015a [US1] Implement `code/data_ingestion.py` function `validate_rotation_period`: Explicitly check for the presence of the `Rotation Period` column in the exoplanet dataset; if missing, log a warning and flag records for fallback handling in the physics phase (FR-003 dependency)
- [~] T016 [US1] Implement `code/data_ingestion.py` function `filter_and_impute`:
 - Exclude non-M-dwarf hosts
 - Exclude systems with <10 flare events
 - Exclude records with missing mass, radius, or semi-major axis (FR-002, SC-006)
 - Assign `config.DEFAULT_M_DWARF_AGE` (a representative age for M dwarfs) if `system_age` is missing and log a warning (SC-006)
- [~] T017 [US1] Save the final filtered dataset to `data/processed/merged_filtered.csv` with checksum generation
- [~] T018 [US1] Add comprehensive logging of API queries and filtering decisions to `data/logs/api_log.jsonl` (FR-008, VI)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Cumulative XUV Flux and Model Mass Loss (Priority: P2)

**Goal**: Calculate cumulative XUV flux (flare + quiescent) and model atmospheric mass loss/retention using the energy-limited escape model.

**Independent Test**: Run `code/physics.py` on a small hardcoded synthetic dataset and verify the output matches manual calculations of the energy-limited formula within 1% tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Unit test for `code/physics.py` flux calculation using synthetic inputs (FR-003)
- [~] T020 [P] [US2] Unit test for `code/physics.py` mass loss calculation against the energy-limited formula (FR-004)

### Implementation for User Story 2

- [~] T021 [US2] Implement `code/physics.py` function `calculate_quiescent_xuv`:
 - PRIMARY: Calculate $L_X$ using the Wright et al. (2018) relation $L_X/L_{bol} = 10^{-3.5} (P_{rot}/10 \text{ days})^{-2.7}$ (or specific coefficients from the paper) if `Rotation Period` is available.
 - FALLBACK: If `Rotation Period` is missing, use the fixed proxy $L_X = 10^{-4} L_{bol}$ and log a warning.
 - Output must be in erg/s (FR-003).
- [~] T022 [US2] Implement `code/physics.py` function `calculate_cumulative_flux`: Compute $F_{XUV} = F_{quiescent} + \sum (E_{flare} \times f_{XUV} / (4 \pi a^2))$, where $f_{XUV}$ is a fixed conversion factor. (FR-003)
- [ ] T023 [US2] Implement `code/physics.py` function `calculate_retention_fraction`:
 - Calculate instantaneous mass loss rate $\dot{M}$ using energy-limited model $\dot{M} = \frac{\epsilon \pi R_p^3 F_{XUV}}{G M_p K_{tide}}$ (FR-004).
 - Integrate $\dot{M}$ over system age (scalar) using the trapezoidal rule (or simple multiplication if rate is assumed constant over age).
 - Compute $Retention = 1 - (\int \dot{M} dt / M_{atm, initial})$ where $M_{atm, initial} = 0.01 \times M_p$.
 - **CRITICAL**: Do NOT implement the 'Atmospheric Erosion Index (AEI)' mentioned in the plan summary; strictly use the FR-005 formula (FR-005).
- [ ] T024a [US2] Implement `code/physics.py` function `calculate_unphysical_flag`: Calculate a boolean flag for each row where mass loss rate > 10% $M_p$ / Gyr (FR-009).
- [ ] T024b [US2] Implement `code/physics.py` function `apply_unphysical_filter`: Filter the DataFrame to remove rows where the flag from T024a is true, ensuring these are excluded from subsequent statistical analysis (FR-009).
- [ ] T025 [US2] Read `data/processed/merged_filtered.csv`, apply physics models (T021-T023), apply unphysical filters (T024a-T024b), and write the clean result to `data/processed/derived_physics.csv` with columns: `cumulative_flux`, `mass_loss_rate`, `retention_fraction`, `is_valid` (do NOT overwrite the original file).
- [ ] T026 [US2] Add validation logic to ensure no NaN values in derived columns for valid inputs (US-2 Acceptance 3)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Correlation and Visualization (Priority: P3)

**Goal**: Perform partial Spearman rank correlation (controlling for mass and semi-major axis) and generate visualizations.

**Independent Test**: Run `code/analysis.py` and `code/visualization.py` on the derived dataset and verify the output JSON contains ρ_partial and p-value, and a PNG plot is generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for partial correlation logic in `tests/test_analysis.py` (mock data with known correlation)

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/analysis.py` function `run_partial_correlation`:
 - Read the filtered `data/processed/derived_physics.csv` (post-T024b).
 - Perform a **partial Spearman rank correlation** between `cumulative_flux` and `retention_fraction` controlling for `mass` and `semi_major_axis`.
 - **Mandatory**: Explicitly rank-transform all variables using `scipy.stats.rankdata` before computing partial correlation (to ensure true rank-based method, as `pingouin.partial_corr` may default to Pearson).
 - Fallback: If rank-based partial correlation is not supported by the library version, implement manually using residuals of rank-transformed variables (FR-006, SC-001).
- [ ] T029 [US3] Implement `code/analysis.py` function `run_sensitivity_analysis`: Re-run correlation with $M_{atm, initial}$ baselines across a range of low to moderate magnitudes., calculate the variation in correlation coefficients, and append the calculated variation to `correlation_results.json` (FR-010)
- [ ] T030 [US3] Save results to `data/results/correlation_results.json` including ρ_partial, p-value, and a structured summary of sensitivity results with keys: `baselines` (list of values), `correlations` (list of ρ values), and `variation` (range or std dev) (FR-006, FR-010)
- [ ] T031 [US3] Implement `code/visualization.py` to generate scatter plot: X-axis = Cumulative XUV Flux, Y-axis = Retention Fraction, with regression line and labels (FR-007)
- [ ] T032 [US3] Save plot to `data/results/flux_vs_retention.png`
- [ ] T033 [US3] Add console output logic to print significance statement based on p-value < 0.05 and sign of ρ (US-3 Acceptance 3)
- [ ] T034 [US3] Ensure all analysis outputs explicitly frame findings as "associational" only (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Update `README.md` with execution instructions and dependency installation
- [ ] T036 Run full pipeline integration test: Ingest -> Physics -> Analysis -> Visualization
- [ ] T037 Verify performance: Ensure processing completes in ≤ 60 seconds on target hardware (SC-004)
- [ ] T038 Run `pytest` suite and ensure [deferred] pass rate
- [ ] T039 Validate all JSON/CSV outputs against `contracts/` schemas
- [ ] T040 Final cleanup: Remove debug prints, ensure all logging is structured, verify checksums

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
- **User Story 2 (P2)**: Depends on User Story 1 completion (requires `merged_filtered.csv` as input)
- **User Story 3 (P3)**: Depends on User Story 2 completion (requires `derived_physics.csv` as input)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services/logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- US2 and US3 must be sequential due to data dependencies

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: (Wait for US1 data) → User Story 2 (Physics)
 - Developer C: (Wait for US2 data) → User Story 3 (Analysis)
3. Stories complete and integrate sequentially due to data dependencies

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Data Flow**: US1 (Ingest) → US2 (Physics) → US3 (Analysis). Do not attempt US2 until US1 CSV exists.
- **Compute Constraint**: All physics and analysis must run on CPU only (scipy, numpy, astropy, pingouin). No GPU or large models.
- **Data Integrity**: Do not fabricate data. Use real API sources (MAST, NASA Exoplanet Archive) as defined in FR-001.
- **Eccentricity Handling**: Task T016 includes logic to flag/exclude planets with extreme eccentricity to maintain model validity (Edge Case 2).
- **Unphysical Mass Loss**: Task T024a/T024b explicitly handle the 10% mass loss per Gyr threshold to prevent skewing correlations (Edge Case 3, FR-009).
- **Rotation Period Dependency**: Task T015a ensures the Rotation Period column is validated before physics calculations (FR-003).
- **Methodology**: Task T028 ensures true rank-based partial correlation is performed (FR-006).