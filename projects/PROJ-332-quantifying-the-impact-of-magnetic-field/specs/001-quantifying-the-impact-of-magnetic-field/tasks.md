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

- [ ] T001a [P] Create project directory structure per `plan.md`. Explicitly create: `code/`, `data/raw/`, `data/intermediate/`, `data/processed/`, `outputs/`, `tests/`, `contracts/`, `.github/workflows/`.
- [ ] T001b [P] Create `.gitignore` for Python and data artifacts.
- [ ] T003a [P] Configure `flake8` linting rules. Create `.flake8` file with `max-line-length = 88` and `extend-ignore = E203, W503`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with `requirements.txt` (pinning `scipy`, `numpy`, `matplotlib`, `pandas`, `pytest`, `requests`, `pyyaml`; **NO** `mdsplus` library).
- [X] T003b [P] Configure `black` formatting rules. Create `pyproject.toml` with `[tool.black] line-length = 88`.
- [ ] T006b [P] [FR-007] Create `.github/workflows/ci.yml` with `timeout-minutes:` (6 hours) and `fail-on-error: true` to ensure immediate pipeline abort at the CI level. **Content**:
```yaml
name: CI Pipeline
on: [push, pull_request]
jobs:
 run-analysis:
 runs-on: ubuntu-latest
 timeout-minutes: a predetermined duration sufficient for the complete execution of the experimental protocol.
 steps:
 - uses: actions/checkout@v3
 - name: Set up Python
 uses: actions/setup-python@v4
 with:
 python-version: '3.11'
 - name: Install dependencies
 run: pip install -r code/requirements.txt
 - name: Run Pipeline
 run: python code/main.py
 env:
 DIII_D_DISCHARGES: "123456,123457,123458,123459,123460,123461,123462,123463,123464,123465"
```
**DEPENDS ON T001a**.
- [X] T004 Implement `code/data/__init__.py` and `code/analysis/__init__.py`.
- [X] T005 [P] Create `code/main.py` entry point with argument parsing for discharge list.
- [ ] T006a [P] [FR-007] Implement internal timeout wrapper in `code/utils/limits.py` using signal handling. **MUST** accept a `per_operation_threshold` parameter (default a moderate duration) to abort specific operations immediately if they exceed this limit, satisfying the "immediate abort" constraint for slow operations like network retries. **MUST** use a configurable constant `PER_OPERATION_TIMEOUT` (default 300s) defined in `code/config.py` to satisfy the 'predefined threshold' requirement. **CRITICAL**: The wrapper MUST raise `SystemExit(1)` or call `os._exit(1)` to trigger a **hard process termination of the entire `main.py` pipeline** immediately upon timeout, not just abort the specific function. This ensures the entire pipeline aborts as per FR-007. Wire to `code/main.py`. **DEPENDS ON T005**.
- [ ] T007a [P] [FR-009] Create `contracts/dataset.schema.yaml` defining columns: `discharge_id` (int), `island_width` (float), `tau_e` (float), `confinement_mode` (string), `h98y2` (float), `q_min` (float), `q_max` (float), `resonant_surface_density` (float), `te_profile` (array), `ne_profile` (array). **MUST** include `resonant_surface_density`, `confinement_mode`, and `h98y2` in required properties. **Content**:
```yaml
type: object
properties:
 discharge_id:
 type: integer
 island_width:
 type: number
 minimum: 0
 tau_e:
 type: number
 minimum: 0
 confinement_mode:
 type: string
 enum: ["L-mode", "H-mode"]
 h98y2:
 type: number
 q_min:
 type: number
 q_max:
 type: number
 resonant_surface_density:
 type: number
 minimum: 0
 te_profile:
 type: array
 items:
 type: number
 ne_profile:
 type: array
 items:
 type: number
required:
 - discharge_id
 - island_width
 - tau_e
 - confinement_mode
 - h98y2
 - q_min
 - q_max
 - resonant_surface_density
 - te_profile
 - ne_profile
```
**DEPENDS ON T001a**.
- [ ] T007b [P] [FR-009] Create `contracts/output.schema.yaml` defining fields: `r` (float), `p_value` (float), `ci_lower` (float), `ci_upper` (float), `power` (float), `hypothesis_status` (string), `warning_flags` (list). **Content**:
```yaml
type: object
properties:
 r:
 type: number
 p_value:
 type: number
 ci_lower:
 type: number
 ci_upper:
 type: number
 power:
 type: number
 hypothesis_status:
 type: string
 enum: ["Supported", "Not Supported", "Inconclusive due to low power"]
 warning_flags:
 type: array
 items:
 type: string
 stratification_warning:
 type: string
 nullable: true
 collinearity_flag:
 type: boolean
 default: false
required:
 - r
 - p_value
 - ci_lower
 - ci_upper
 - power
 - hypothesis_status
 - warning_flags
```
**DEPENDS ON T001a**.
- [X] T008 Implement logging infrastructure in `code/utils/logger.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Retrieval, Preprocessing & Metric Calculation (Priority: P1) 🎯 MVP

**Goal**: Automatically retrieve up to 10 specific DIII-D discharge datasets from the public MDSplus archive, parse them, and calculate topological metrics (`island_width`, `resonant_surface_density`) ensuring strict adherence to data provenance rules.

**Independent Test**: The pipeline can be tested by running the retrieval script against the public MDSplus archive and verifying that a single CSV file is produced containing a small number of rows (discharges) with columns for `discharge_id`, `island_width`, `resonant_surface_density`, `tau_e`, `te_profile`, and `ne_profile`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Unit test for MDSplus connection retry logic in `tests/unit/test_retrieval.py`.
- [X] T010 [P] [US1] Integration test for exclusion of discharges with missing data in `tests/integration/test_pipeline.py`.

### Implementation for User Story 1

- [X] T011 [US1] Implement MDSplus client connection with retry logic (multiple attempts, fixed time intervals) in `code/data/retrieval.py`.
- [X] T012 [US1] Implement logic to fetch EFIT, `islands`, `taue`, AND `h98y2` fields from the MDSplus `taue` or `h98y2` tree for a given discharge ID in `code/data/retrieval.py`. **MUST** include `h98y2` retrieval to support confinement mode classification. **MUST** explicitly calculate and store `confinement_mode` as 'H-mode' if `h98y2` >= 0.85, else 'L-mode', and include this string in the parsed dataset. **Output**: Store `confinement_mode` string in the intermediate parsed data structure. **DEPENDS ON T011**.
- [ ] T013 [US1] [FR-002] **COMPREHENSIVE (Retrieval & Intermediate Persistence)**: Implement logic to retrieve pre-calculated `island_width` from MDSplus. **IF** missing, check for availability of raw EFIT data (q-profile, Bt) in the archive. **IF** raw EFIT is present, mark the discharge as `needs_derivation` in the intermediate dataset. **IF** raw EFIT is missing, exclude the discharge and log warning. **CRITICAL**: Do NOT attempt to derive the island width in this task. **Additionally**, calculate `resonant_surface_density` is NOT performed here; this task only retrieves raw data. **CRITICAL**: **MUST persist raw EFIT data (q-profile, shear, Bt) to `data/intermediate/efit_intermediate.parquet`** for each discharge marked `needs_derivation`. This file is the sole source of raw data for T013b. **Output**: Write `island_width` (pre-calculated or None), `needs_derivation` flag, and raw EFIT data (if applicable) to `data/intermediate/efit_intermediate.parquet`. **DEPENDS ON T011, T012**.
- [ ] T013b [US1] [FR-002] **DERIVATION LOGIC**: Implement Rutherford equation derivation for `island_width` and `resonant_surface_density` calculation in `code/analysis/metrics.py`. **MUST** read raw EFIT data from `data/intermediate/efit_intermediate.parquet` if `needs_derivation` flag is True. **MUST** use `local_magnetic_shear`, `q_profile`, `Bt_field` from EFIT (extracted in T018a/b). **IF** inputs missing, exclude discharge. **Additionally**, calculate `resonant_surface_density` by counting rational surfaces (q=m/n) per unit normalized minor radius (rho_tor) using the EFIT q-profile (m,n ∈ ℕ⁺, tolerance |q - m/n| < 0.01). **IF** q-profile exists but has no integer crossings, assign density = 0. **Output**: Update `island_width` (derived) and `resonant_surface_density` in `data/processed/metrics.csv`. **DEPENDS ON T013, T018a, T018b**.
- [X] T014a [US1] Implement parsing logic to convert MDSplus EFIT, `islands`, and `taue` time-series data into a unified structured DataFrame in `code/data/preprocessing.py`. **MUST** include extraction of `te_profile` and `ne_profile`. **DEPENDS ON T013**.
- [ ] T014b [US1] [FR-009] Implement schema validation logic to validate input/output against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` **after** parsing (T014a) in `code/data/validator.py`. **MUST** validate the parsed DataFrame against T007a schema. **DEPENDS ON T007a, T014a**.
- [X] T015 [US1] Implement validation: ensure at least 5 valid discharges remain; fail pipeline if fewer [FR-001] in `code/main.py`. **This is a hard gate**.
- [ ] T016 [US1] Save unified dataset to `data/processed/unified_analysis.csv` with checksum generation. **Must include exact columns**: `discharge_id`, `island_width`, `resonant_surface_density`, `tau_e`, `confinement_mode`, `h98y2`, `q_min`, `q_max`, `te_profile`, `ne_profile`. **Logic**: `confinement_mode` is already calculated in T012; simply include the column. **CRITICAL**: If `needs_derivation` is True, merge the raw EFIT data from `data/intermediate/efit_intermediate.parquet` into this dataset or ensure T013b can access it. **Output** to `code/data/preprocessing.py`. **DEPENDS ON T015 success**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Topological Metric Validation & Pre-Analysis Checks (Priority: P2)

**Goal**: Validate calculated metrics, perform power analysis, and check multicollinearity BEFORE running correlation.

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
- [X] T028 [US3] [FR-008] **NEW**: Implement Power Analysis calculation using `scipy.stats.zt_ind_solve_power` (or manual simulation) with `effect_size=0.5`, `alpha=0.05`, `n=current_N`. **MUST** calculate and report the exact power value in `outputs/summary_report.json` under key `power`. **MUST** run BEFORE correlation. If power < 20% to detect |r|=0.5, flag result as "Inconclusive due to low power" in the output. **DEPENDS ON T016**.
- [ ] T025b [US3] [FR-011] **NEW**: Implement Multicollinearity Check. Check correlation between `q_max - q_min` and `resonant_surface_density`. If correlation exceeds `MULTICOLLINEARITY_THRESHOLD` (configurable constant, default 0.95), flag as collinear, **exclude** `resonant_surface_density` from any multivariate analysis, and **report only the univariate correlation** for transparency. **Output**: Write `collinearity_flag` (boolean) and `excluded_variables` (list) to `outputs/summary_report.json`. **DEPENDS ON T016, T013b**.

**Checkpoint**: At this point, metrics are calculated, power is assessed, and multicollinearity is checked. Correlation can now proceed safely.

---

## Phase 5: User Story 3 - Statistical Correlation and Visualization (Priority: P3)

**Goal**: Compute Spearman rank correlation between topological metrics and energy confinement time, generate a scatter plot, and output the p-value.

**Independent Test**: The analysis module can be tested by running it on a small synthetic dataset with a known negative correlation and verifying that the system correctly reports the calculated p-value and flags the significance status.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for Spearman correlation and bootstrap resampling logic in `tests/unit/test_correlation.py`.
- [X] T024 [P] [US3] Integration test for "Hypothesis Not Supported" flag logic in `tests/integration/test_analysis.py`.

### Implementation for User Story 3

**DEPENDS ON**: T016 (unified_analysis.csv), T028 (Power), and T025b (Multicollinearity) must be complete before T025 starts.

- [ ] T025a [US3] [FR-010] **NEW**: Implement Stratification Logic. Check N per mode (L/H). **IF** N >= 3 for both, calculate separate correlations. **IF** N < 3 for either, **SKIP** stratification, **calculate the global correlation coefficient** (r, p-value, CI) using the same bootstrap parameters as T025, and **append warning flag: "Stratification skipped: insufficient samples per mode (N < 3)" to the `warning_flags` list in `outputs/summary_report.json`**. **MUST** perform the global calculation within this task to ensure the result is produced. **DEPENDS ON T016, T025b**.
- [ ] T025 [US3] [FR-004] Implement Global Spearman rank correlation calculation between `island_width` and `tau_e`. **MUST include**:
 1. **Bootstrap Resampling**: Perform bootstrap with `random_seed=42` and `bootstrap_iterations=1000` (minimum per Constitution Principle VII) to ensure reproducibility and calculate confidence intervals.
 2. **Output**: Return `r`, `p_value`, `ci_lower`, `ci_upper` and save to `outputs/summary_report.json`.
 3. **Constraint**: If T025a already calculated the global correlation (due to stratification skip), this task must **SKIP** redundant calculation and use the result from T025a. **DEPENDS ON T025a**.
- [ ] T025c [US3] [FR-004] **NEW**: Implement Spearman rank correlation calculation between `resonant_surface_density` and `tau_e`. **MUST** check `collinearity_flag` from T025b; **IF** flag is True, **SKIP** this calculation entirely, **update `summary_report.json` to include the univariate `island_width` correlation result and set `collinearity_exclusion_flag=True`**, and log exclusion to prevent tautological inflation. **ELSE**, calculate correlation using the same bootstrap parameters as T025 (`random_seed=42`, `iterations=1000`). **MUST** output `r_density`, `p_density`, `ci_lower_density`, `ci_upper_density` to `outputs/summary_report.json` only if not skipped. **MUST** apply stratification logic (T025a) to density correlation as well. **DEPENDS ON T025a, T025b**.
- [X] T027 [US3] Implement hypothesis logic: `directional_effect` (r < -0.5) and `statistical_significance` (p < 0.05) in `code/analysis/correlation.py`.
- [ ] T029 [US3] Generate diagnostic scatter plot (`topology_vs_confinement.png`) with: Title 'Topology vs Confinement', x-axis 'Island Width (m)', y-axis 'Tau_E (s)', regression line style 'linear' with % CI band. **Save plot to `outputs/topology_vs_confinement.png`**. **MUST** use `matplotlib.pyplot` and include error bars for CI. **DEPENDS ON T025**.
- [X] T030 [US3] Generate final summary report artifact consuming outputs from T025, T025a, T025b, T025c, T027, T028, T029. **Must unconditionally report** the effect size magnitude (|r|) for ALL valid datasets regardless of statistical significance. **JSON Schema**: `{r, p_value, ci_lower, ci_upper, power, hypothesis_status, warning_flags}`. Output to `code/main.py`. **DEPENDS ON T029**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031a [P] Update `quickstart.md` with execution commands and environment setup.
- [ ] T031b [P] Update `README.md` with project overview and architecture.
- [ ] T032a [P] Run data retrieval integration test with a known set of DIII-D discharge IDs. **Test Data**: Use discharge IDs `123456, 123457, 123458` (if available) or **FAIL** if DIII-D data is unavailable. **DO NOT use synthetic mock data as a fallback**. **Expected Output**: A CSV file with a small number of rows matching the schema.
- [ ] T032b [P] Run analysis integration test with synthetic data. **Test Data**: Create a synthetic dataset with N=20, r=-0.7, Gaussian noise. **Expected Output**: `summary_report.json` with `r` approx -0.7, `p_value` < 0.05, and `hypothesis_status` "Supported". **NOTE**: This synthetic data is ONLY for unit/integration testing of the correlation logic (T023-T024) and NOT for the live pipeline (T032a).
- [ ] T033a [P] Verify memory footprint < 7 GB in CI environment. **Command**: Run `python -m memory_profiler code/main.py` and capture output. Log max memory usage.
- [ ] T033b [P] Verify execution time < 6 hours in CI environment. **Command**: Run `time python code/main.py` and capture output. Log total time.
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
- **User Story 3 (P3)**: Depends on US2 completion (requires calculated metrics) - **Cannot run until T016 is done**

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
- **CRITICAL**: If pre-calculated island width is missing, the Rutherford equation derivation MUST be attempted ONLY if specific archival metadata (shear, q, Bt) is present; otherwise exclude (FR-002).
- **CRITICAL**: Stratification by mode is mandatory if N>=3 per mode; otherwise, global correlation with warning (FR-010).
- **CRITICAL**: Fixed random seed is mandatory for all stochastic processes (FR-005, Constitution I).
- **CRITICAL**: Power analysis is mandatory and must flag "Inconclusive" if power < 20% (FR-008).
- **CRITICAL**: T006a must implement internal Python timeout handling with a configurable `PER_OPERATION_TIMEOUT` (default 300s) and MUST trigger a hard process exit (`os._exit(1)`) of the entire pipeline.
- **CRITICAL**: T013 must use m, n ∈ positive integers and tolerance |q - m/n| < 0.01.
- **CRITICAL**: T013 MUST persist raw EFIT data to `data/intermediate/efit_intermediate.parquet` for derivation.
- **CRITICAL**: T013b MUST perform the derivation logic using the persisted data.
- **CRITICAL**: T016 output columns must match spec.md:US-1 Independent Test exactly, including `confinement_mode` and `h98y2`.
- **CRITICAL**: T025 must use `random_seed=42` and `bootstrap_iterations=1000`.
- **CRITICAL**: T028 must report exact power value in `outputs/summary_report.json` under key `power`.
- **CRITICAL**: T025c must calculate correlation for `resonant_surface_density` ONLY if `collinearity_flag` is False; IF True, it MUST update `summary_report.json` with univariate results and exclusion flag.
- **CRITICAL**: T025b must use a configurable `MULTICOLLINEARITY_THRESHOLD` (default 0.95) and exclude `resonant_surface_density` from analysis if collinear.
- **CRITICAL**: Order: Power (T028) and Multicollinearity (T025b) MUST precede Correlation (T025/T025c).
- **CRITICAL**: Order: Stratification Logic (T025a) MUST precede Correlation (T025) and MUST perform global calculation if stratification is skipped.
- **CRITICAL**: Order: Schema Validation (T014b) MUST follow Parsing (T014a) to validate the parsed data.
- **CRITICAL**: T013 must include q-profile and shear extraction logic to avoid cross-phase dependencies.
- **CRITICAL**: T016 output columns must match spec.md:US-1 Independent Test exactly, including `confinement_mode` and `h98y2`.
- **NOTE**: T020b has been removed to eliminate duplication. All density calculation logic is now in T013b.
- **NOTE**: T013 is now retrieval-only; derivation and density calculation moved to T013b.
- **NOTE**: T032a MUST NOT use synthetic data; T032b synthetic data is ONLY for unit tests.