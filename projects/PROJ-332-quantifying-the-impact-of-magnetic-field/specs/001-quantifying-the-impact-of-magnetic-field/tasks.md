# Tasks: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

**Input**: Design documents from `/specs/001-quantify-topology-confinement/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per `plan.md`)
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

- [ ] T001a [P] Create project directory structure per `plan.md`. Explicitly create: `code/`, `data/raw/`, `data/processed/`, `outputs/`, `tests/`, `contracts/`, `.github/workflows/`.
- [ ] T001b [P] Create `.gitignore` for Python and data artifacts.
- [X] T002 Initialize Python project with `requirements.txt` (pinning `scipy`, `numpy`, `matplotlib`, `pandas`, `pytest`, `requests`, `pyyaml`; **NO** `mdsplus` library).
- [ ] T003a [P] Configure `flake8` linting rules. Create `.flake8` file with `max-line-length = 88` and `extend-ignore = E203, W503`.
- [ ] T003b [P] Configure `black` formatting rules. Create `pyproject.toml` with `[tool.black] line-length = 88`.
- [ ] T006b [P] [FR-007] Create `.github/workflows/ci.yml` with `timeout-minutes: 360` (6 hours) and `fail-on-error: true` to ensure immediate pipeline abort at the CI level. **DEPENDS ON T001a**.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/data/__init__.py` and `code/analysis/__init__.py`.
- [X] T005 [P] Create `code/main.py` entry point with argument parsing for discharge list.
- [X] T006a [P] [FR-007] Implement internal timeout wrapper in `code/utils/limits.py` using signal handling to abort the Python process if execution exceeds the threshold, and wire to `code/main.py`. **DEPENDS ON T005**.
- [ ] T007a [P] Create `contracts/dataset.schema.yaml` defining columns: `discharge_id` (int), `island_width` (float), `tau_e` (float), `confinement_mode` (string), `h98y2` (float), `q_min` (float), `q_max` (float), `resonant_surface_density` (float). **DEPENDS ON T001a**.
- [ ] T007b [P] Create `contracts/output.schema.yaml` defining fields: `r` (float), `p_value` (float), `ci_lower` (float), `ci_upper` (float), `power` (float), `hypothesis_status` (string), `warning_flags` (list). **DEPENDS ON T001a**.
- [X] T008 Implement logging infrastructure in `code/utils/logger.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Retrieval and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically retrieve up to 10 specific DIII-D discharge datasets from the public MDSplus archive and parse them into a unified analysis-ready format containing `island_width` (pre-calculated or derived) and `tau_e`.

**Independent Test**: The pipeline can be tested by running the retrieval script against the public MDSplus archive and verifying that a single CSV file is produced containing a small number of rows (discharges) with columns for `discharge_id`, `island_width`, `tau_e`, `te_profile`, `ne_profile`, and `confinement_mode`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for MDSplus connection retry logic in `tests/unit/test_retrieval.py`.
- [X] T010 [P] [US1] Integration test for exclusion of discharges with missing data in `tests/integration/test_pipeline.py`.

### Implementation for User Story 1

- [X] T011 [US1] Implement MDSplus client connection with retry logic (multiple attempts, fixed time intervals) in `code/data/retrieval.py`.
- [X] T012 [US1] Implement logic to fetch EFIT, `islands`, `taue`, AND `h98y2` fields from the MDSplus `taue` or `h98y2` tree for a given discharge ID in `code/data/retrieval.py`. **MUST** include `h98y2` retrieval to support confinement mode classification as per `spec.md:FR-003`.
- [ ] T013 [US1] [FR-002] Implement logic to retrieve pre-calculated `island_width` from MDSplus. **IF** missing, attempt derivation using Rutherford equation in `code/analysis/metrics.py` (function `derive_island_width`). **MUST** first retrieve derivation inputs: `local_magnetic_shear`, `q_profile`, `Bt_field` from EFIT. **CRITICAL**: If derivation inputs are ALSO missing, THEN exclude the discharge and log warning. **Do not** exclude if only pre-calculated is missing; use derivation as the primary fallback. **Output**: Write `island_width` to `data/processed/metrics.csv`.
- [ ] T014b [US1] [FR-009] Implement schema validation logic to validate input/output against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` **before** any parsing or analysis begins in `code/data/validator.py`. **DEPENDS ON T007a AND T007b**.
- [ ] T014a [US1] Implement parsing logic to convert MDSplus EFIT, `islands`, and `taue` time-series data into a unified structured DataFrame in `code/data/preprocessing.py`. **DEPENDS ON T014b**.
- [X] T015 [US1] Implement validation: ensure at least 5 valid discharges remain; fail pipeline if fewer [FR-001] in `code/main.py`. **This is a hard gate**.
- [X] T016 [US1] Save unified dataset to `data/processed/unified_analysis.csv` with checksum generation. **Must include** exact columns: `discharge_id`, `island_width`, `tau_e`, `confinement_mode` (L-mode/H-mode), `h98y2`. Logic: `confinement_mode` = 'H-mode' if `h98y2` >= 0.85, else 'L-mode'. Output to `code/data/preprocessing.py`. **DEPENDS ON T015 success**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Topological Metric Calculation & Pre-Analysis Checks (Priority: P2)

**Goal**: Calculate topological metrics (resonant surface density), perform power analysis, and check multicollinearity BEFORE running correlation.

**Independent Test**: The calculation module can be tested by feeding it a provided reference CSV file containing known values for a set of test discharges and verifying that the output matches the expected values within a reasonable tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for resonant surface density calculation against reference values in `tests/unit/test_metrics.py`.
- [X] T017b [P] [US3] Unit test for Power Analysis logic in `tests/unit/test_statistics.py`.

### Implementation for User Story 2 & Pre-Analysis

**DEPENDS ON**: T016 (unified_analysis.csv) must be complete before T020b starts.

- [X] T018a [US2] Implement q-profile extraction from EFIT data in `code/analysis/metrics.py`.
- [X] T018b [US2] Implement local magnetic shear calculation from q-profile in `code/analysis/metrics.py`.
- [X] T019 [US2] Implement outlier detection: flag and exclude discharges where `island_width` > minor radius in `code/analysis/metrics.py`.
- [X] T020a [US2] Handle edge case: if no integer q-values cross minor radius, assign default "zero" density in `code/analysis/metrics.py`.
- [ ] T020b [US2] [FR-002] **NEW**: Calculate `resonant_surface_density` by counting rational surfaces (q=m/n) per unit normalized minor radius (rho_tor) using the EFIT q-profile. **MUST** use a loop where m,n ∈ [, 10] and tolerance |q - m/n| < 0.01. If q-profile exists but has no integer crossings, density is 0. **Output**: Write column `resonant_surface_density` to `data/processed/metrics.csv`. **DEPENDS ON T016**.
- [ ] T028 [US3] [FR-008] **NEW**: Implement Power Analysis calculation using `scipy.stats.power` or manual simulation with `effect_size=0.5`, `alpha=0.05`, `n=current_N`. **MUST** calculate and report the exact power value in `outputs/summary_report.json` under key `power`. **MUST** run BEFORE correlation. If power < 20% to detect |r|=0.5, flag result as "Inconclusive due to low power" in the output. **DEPENDS ON T020b**.
- [ ] T025b [US3] [FR-011] **NEW**: Implement Multicollinearity Check. Check correlation between `q_max - q_min` and `resonant_surface_density`. If > 0.95, flag as collinear, **exclude** `resonant_surface_density` from any multivariate analysis, and **report only the univariate correlation** for transparency. **Output**: Write `collinearity_flag` (boolean) and `excluded_variables` (list) to `outputs/summary_report.json`. **DEPENDS ON T020b**.

**Checkpoint**: At this point, metrics are calculated, power is assessed, and multicollinearity is checked. Correlation can now proceed safely.

---

## Phase 5: User Story 3 - Statistical Correlation and Visualization (Priority: P3)

**Goal**: Compute Spearman rank correlation between topological metrics and energy confinement time, generate a scatter plot, and output the p-value.

**Independent Test**: The analysis module can be tested by running it on a small synthetic dataset with a known negative correlation and verifying that the system correctly reports the calculated p-value and flags the significance status.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for Spearman correlation and bootstrap resampling logic in `tests/unit/test_correlation.py`.
- [ ] T024 [P] [US3] Integration test for "Hypothesis Not Supported" flag logic in `tests/integration/test_analysis.py`.

### Implementation for User Story 3

**DEPENDS ON**: T020b (metrics.csv), T028 (Power), and T025b (Multicollinearity) must be complete before T025 starts.

- [ ] T025a [US3] [FR-010] **NEW**: Implement Stratification Logic. Check N per mode (L/H). If N >= 3 for both, calculate separate correlations. If N < 3 for either, skip stratification, calculate global correlation, and **append warning flag: "Stratification skipped: insufficient samples per mode (N < 3)"** to the output artifact. **MUST** precede T025.
- [ ] T025 [US3] [FR-004] Implement Global Spearman rank correlation calculation between `island_width` and `tau_e`. **MUST include**:
 1. **Bootstrap Resampling**: Perform bootstrap with `random_seed=42` and `bootstrap_iterations=1000` (minimum per Constitution Principle VII) to ensure reproducibility and calculate confidence intervals.
 2. **Output**: Return `r`, `p_value`, `ci_lower`, `ci_upper` and save to `outputs/summary_report.json`.
 3. **Constraint**: If T025b flagged collinearity, this task runs ONLY on `island_width`. **DEPENDS ON T025a**.
- [ ] T025c [US3] [FR-004] **NEW**: Implement Spearman rank correlation calculation between `resonant_surface_density` and `tau_e`. **MUST** use the same bootstrap parameters as T025 (`random_seed=42`, `iterations=1000`). **MUST** output `r`, `p_value`, `ci_lower`, `ci_upper` to `outputs/summary_report.json`. **MUST** be skipped if T025b flagged collinearity. **DEPENDS ON T025a**.
- [X] T027 [US3] Implement hypothesis logic: `directional_effect` (r < -0.5) and `statistical_significance` (p < 0.05) in `code/analysis/correlation.py`.
- [ ] T029 [US3] Generate diagnostic scatter plot (`topology_vs_confinement.png`) with: Title 'Topology vs Confinement', x-axis 'Island Width (m)', y-axis 'Tau_E (s)', regression line style 'linear' with % CI band. **Save plot to `outputs/topology_vs_confinement.png`**. **DEPENDS ON T025**.
- [ ] T030 [US3] Generate final summary report artifact consuming outputs from T025, T025a, T025b, T025c, T027, T028, T029. **Must unconditionally report** the effect size magnitude (|r|) for ALL valid datasets regardless of statistical significance. **JSON Schema**: `{r, p_value, ci_lower, ci_upper, power, hypothesis_status, warning_flags}`. Output to `code/main.py`. **DEPENDS ON T029**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031a [P] Update `quickstart.md` with execution commands and environment setup.
- [ ] T031b [P] Update `README.md` with project overview and architecture.
- [ ] T032a [P] Run data retrieval integration test with a known set of DIII-D discharge IDs.
- [ ] T032b [P] Run analysis integration test with synthetic data.
- [ ] T033a [P] Verify memory footprint < 7 GB in CI environment.
- [ ] T033b [P] Verify execution time < 6 hours in CI environment.
- [ ] T034a [P] Add docstrings to all modules in `code/data/` and `code/analysis/`.
- [ ] T034b [P] Add docstrings to all modules in `code/viz/` and `code/utils/`.

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
- **User Story 2 (P2)**: Depends on US1 completion (requires parsed data) - **Cannot run until T016 is done**
- **User Story 3 (P3)**: Depends on US2 completion (requires calculated metrics) - **Cannot run until T020b is done**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed) - **Note: In this specific pipeline, data flow (US1->US2->US3) enforces sequential execution, but code structure can be developed in parallel.**
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for MDSplus connection retry logic in tests/unit/test_retrieval.py"
Task: "Integration test for exclusion of discharges with missing data in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement MDSplus client connection with retry logic in code/data/retrieval.py"
Task: "Implement parsing logic to convert MDSplus time-series data in code/data/preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify 5-10 valid rows in CSV)
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
 - Developer A: User Story 1 (Data Retrieval)
 - Developer B: User Story 2 (Metrics - can start coding logic, but needs US1 data for full integration)
 - Developer C: User Story 3 (Analysis - can start coding logic, but needs US2 data for full integration)
3. Stories complete and integrate sequentially due to data flow dependencies.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Do NOT use synthetic data fallbacks. If MDSplus fetch fails, the job MUST fail (FR-001, Constitution VI).
- **CRITICAL**: If pre-calculated island width is missing, the Rutherford equation derivation MUST be attempted before exclusion (FR-002).
- **CRITICAL**: Stratification by mode is mandatory if N>=3 per mode; otherwise, global correlation with warning (FR-010).
- **CRITICAL**: Fixed random seed is mandatory for all stochastic processes (FR-005, Constitution I).
- **CRITICAL**: Power analysis is mandatory and must flag "Inconclusive" if power < 20% (FR-008).
- **CRITICAL**: T006a must implement internal Python timeout handling; T006b must configure CI timeout.
- **CRITICAL**: T020b must use m,n ∈ [1, 10] and tolerance |q - m/n| < 0.01.
- **CRITICAL**: T025 must use `random_seed=42` and `bootstrap_iterations=1000`.
- **CRITICAL**: T028 must report exact power value in `outputs/summary_report.json` under key `power`.
- **CRITICAL**: T025c must calculate correlation for `resonant_surface_density` as per FR-004.
- **CRITICAL**: T025b must exclude `resonant_surface_density` from analysis if collinear.
- **CRITICAL**: Order: Power (T028) and Multicollinearity (T025b) MUST precede Correlation (T025/T025c).
- **CRITICAL**: Order: Stratification Logic (T025a) MUST precede Correlation (T025).
- **CRITICAL**: Order: Schema Validation (T014b) MUST precede Parsing (T014a).