---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Alloy Phase Diagrams from Compositional Data

**Input**: Design documents from `/specs/001-predict-alloy-phase-diagrams/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY where spec acceptance criteria require verification (e.g., US-1 Independent Test).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.,g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] **Initialize Project Structure (Directories)**: Create all required directories (`code/`, `code/ingest`, `code/features`, `code/models`, `code/viz`, `code/utils`, `data/raw`, `data/processed`, `data/artifacts`, `data/logs`, `state/`). **Verify**: Run `find code -type d | wc -l` and assert count > 10.
- [X] T002 [P] **Initialize Project Structure (__init__.py)**: Create all necessary `__init__.py` files for the `code/` package structure. **Verify**: Assert all `__init__.py` files exist in `code/` and subdirectories.
- [X] T003 [P] **Initialize Project Structure (.gitignore)**: Create `.gitignore` excluding `data/raw/*`, `data/processed/*`, `data/artifacts/*`, `data/logs/*`, `*.pyc`, `__pycache__`, `state/*.yaml` EXCEPT `state/PROJ-485/*.yaml` (Constitution Principle V). **Verify**: Assert `.gitignore` exists and contains the specified exclusions.
- [X] T004 [P] **Configure Linting and Formatting**:
 1. Create `code/__init__.py` with a docstring to ensure files exist for linters.
 2. Create `pyproject.toml` with content:
```toml
[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
select = ["E", "F", "W", "I"]
ignore = []
max-line-length = 88

[tool.ruff.isort]
known-first-party = ["code"]

[tool.ruff.pydocstyle]
convention = "google"
```
 3. **Verify**: Run `ruff check.` and `black --check.` and assert exit code 0 for both.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Setup `code/utils/logging.py` for structured error logging (FR-007, FR-008)
- [X] T006 [P] Implement `code/utils/checksum.py` for SHA-256 data verification (Constitution Principle III) **Verify**: Assert file exists. **Content Accuracy Check**: Compute SHA-256 of a test artifact and assert the value in `state/...yaml` matches the computed value (not just file existence).
- [X] T007 [P] Create `data/raw/elemental_properties.csv` with columns: `element`, `atomic_radius_angstrom`, `electronegativity_pauling`, `valence_electrons`. Seed with rows for Cu, Al, Zn, Fe, C (Constitution Principle III)
- [X] T008 [P] Create `code/main.py` pipeline orchestrator with state management (state/PROJ-485/...yaml)
- [X] T009a [P] **Define Error Codes**: Implement `code/utils/error_codes.py` as a Python Enum class with string values for: `DATA_SOURCE_MISSING`, `INVALID_DATA_SCHEMA`, `MISSING_TEMP_COORDS`, `LOW_DATA_DENSITY`, `API_RATE_LIMIT_EXCEEDED`, `INSUFFICIENT_POWER`, `INVALID_SCOPE`, `RESOURCE_LIMIT_EXCEEDED`, `NO_SIGNIFICANT_IMPROVEMENT`, `LOW_DATA_FIDELITY`, `DATA_SCHEMA_MISMATCH`, `TEMPERATURE_RANGE_VIOLATION`, `COMPOSITION_SUM_ERROR`, `POTENTIAL_MEMORY_LEAK`, `MISSING_GROUND_TRUTH`, `LOW_RESOLUTION_PLOT`, `DATA_INTEGRITY_VIOLATION`. **Verify**: Assert file exists and contains all specified codes.
- [X] T009b [P] **Define Configuration Schema**: Define configuration schema for `code/config.yaml`. **Requirement**: Must include keys `nist_janaf_url`, `sgte_url`, `local_fallback_path`. **Validation**: Schema must explicitly require phase boundary coordinates (temperature, composition) as part of the data validation rules (FR-001). **Schema Definition**: Use JSON Schema format. **Implementation**: Write the schema to `code/config_schema.json` and use the `jsonschema` library to validate `code/config.yaml` against this file at runtime.
- [X] T009c [P] **Create Configuration File**: Create `code/config.yaml` with the defined schema. **Content**:
```yaml
nist_janaf_url: ""
sgte_url: ""
local_fallback_path: ""
data_schema:
 required_columns:
 - temperature
 - composition
 - element_a
 - element_b
required_systems:
 - Cu-Zn
 - Al-Cu
```
**Validation**: Script `code/utils/validate_config.py` must fail if these keys are missing or empty. (Constitution Principle II, Plan Methodology 1)
- [X] T009d [P] **Implement Source Check Gating**: Implement 'Source Check' gating logic in `code/ingest/load_data.py` (or a pre-check utility) to verify if NIST-JANAF/SGTE URLs exist in the verified input block (from T009); halt with `DATA_SOURCE_MISSING` if absent (FR-001, FR-012). **Dependency**: T009

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw binary/ternary alloy phase data from NIST-JANAF/SGTE (or local CSV) and generate compositional descriptors.

**Independent Test**: Run `code/ingest/load_data.py` against a small hardcoded subset; verify output CSV has correct rows and derived columns with valid numeric ranges.

### Implementation for User Story 1

- [X] T012 [US1] **Implement HTTP Access & Backoff**: Implement `code/ingest/load_data.py` with exponential backoff (limited retries) for HTTP access (FR-001, FR-007). **Logic**: If URL is HTTP, use `requests.get(..., stream=True)` with exponential backoff on 429/503. **Error Handling**: If 429/503 occurs after retries, raise `API_RATE_LIMIT_EXCEEDED`. If other fetch failure occurs, raise `DATA_SOURCE_MISSING`.
- [X] T013 [US1] **Implement Streaming Logic**: Implement streaming logic for large datasets in `code/ingest/load_data.py`. **Logic**: Use `pandas.read_csv(..., chunksize=10000)` for local/HTTP CSVs. Accumulate statistics online. **Constraint**: Do NOT load full dataset into memory.
- [X] T014 [US1] **Implement Error Handling**: Implement error handling in `code/ingest/load_data.py`. **Logic**: If fetch fails after retries, raise specific error codes (`API_RATE_LIMIT_EXCEEDED` or `DATA_SOURCE_MISSING`). **Dependency**: T012.
- [X] T015 [US1] Implement fallback logic in `code/ingest/load_data.py` to load local CSVs ONLY if `local_fallback_path` in `code/config.yaml` points to an existing, verified real file. **Requirement**: "Verified real file" means the file exists and passes checksum validation (T006). If the path is empty or the file does not exist or fails checksum, the system MUST raise `DATA_SOURCE_MISSING`. Do NOT generate synthetic data. The fallback path is validated at runtime and supports loading from a verified input block (FR-001, FR-012).
- [X] T016 [US1] Implement filtering logic:
 1. Skip entries with missing temperature values in binary systems (handled by FR-001).
 2. Skip entries for ternary systems lacking temperature-composition coordinates. **Requirement**: Log `MISSING_TEMP_COORDS` for ANY system (binary or ternary) lacking temperature coordinates to `data/logs/pipeline.log` (JSON line format: `{"timestamp": "...", "level": "ERROR", "code": "MISSING_TEMP_COORDS", "message": "Row <id> excluded: missing temperature-composition coordinates"}`). **Depends on T008**. (FR-001, FR-008)
 **Verify**: Assert `data/logs/pipeline.log` exists and contains a line with code `MISSING_TEMP_COORDS`.
- [X] T017 [US1] Implement `code/features/generate_descriptors.py` to calculate: mean atomic radius, electronegativity variance, valence electron count, Hume-Rothery concentration using constants from `data/raw/elemental_properties.csv` (created by T007) (FR-002, FR-015)
- [X] T018 [US1] Add validation in `code/features/generate_descriptors.py` to verify derived values against `data/raw/elemental_properties.csv` (SC-005, SC-007)
- [X] T019 [US1] Implement data checksumming and state update in `code/ingest/load_data.py` after raw data load AND processed data load (Constitution Principle III, V)
 **Verify**: Assert `state/PROJ-485/...yaml` is updated with the correct hash. **Content Accuracy Check**: Compute SHA-256 of the raw artifact file and assert it matches the value recorded in `state/...yaml`.
- [X] T020 [US1] Write processed data to `data/processed/descriptors.csv` with schema compliance (FR-001). **Verify**: Run `code/utils/validate_schema.py data/processed/descriptors.csv` and assert exit code 0.

### Tests for User Story 1 (MANDATORY)
*Note: These tasks are listed after implementation to reflect 'Producer before Consumer' artifact flow. They depend on T008, T012, and T015.*

- [X] T010 [P] [US1] Write `tests/test_ingest.py` with function `test_invalid_schema_raises_error` asserting `INVALID_DATA_SCHEMA` is raised when phase boundary coordinates (temperature, composition) are missing. **Depends on T012 completion.**
- [X] T011 [P] [US1] Write `tests/test_features.py` with function `test_descriptor_deviation` asserting derived values deviate ≤1% from `data/raw/elemental_properties.csv` (Mandatory per US-1 Independent Test). **Depends on T015 completion.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest Regressor with LOSO cross-validation, perform power analysis, and compare against null baseline.

**Independent Test**: Execute `code/models/train.py` on fixed seed; verify LOSO report (MAE, R²), power analysis report, and model file saved to disk.

### Implementation for User Story 2

- [X] T022 [US2] **New Element Check**: Implement 'New Element' check in `code/models/train.py`.
 1. **Logic**: Verify if any element in test fold is NOT present in the training fold.
 2. **Action**: If a new element is detected, **HALT the pipeline** and log `INVALID_SCOPE`. **Do NOT skip the fold**. (FR-010)
 **Deliverables**: Generate `data/logs/skipped_fold.log` (JSON lines: `{"fold_id": "<id>", "reason": "invalid_scope", "action": "halted"}`) if halted.
 **Verify**: Assert `data/logs/skipped_fold.log` exists if halted and contains valid JSON lines with "halted" action.
- [X] T023 [US2] **Property Range Extrapolation**: Implement 'Property Range Extrapolation' check in `code/models/train.py` (Plan Methodology 3).
 1. **Logic**: Calculate the convex hull of elemental properties (radius, EN) in the training set.
 2. **Action**: If a test set element falls outside this hull (extrapolation), skip the fold and log `INVALID_SCOPE`. **This is distinct from the 'New Element' check (T022)** and implements the plan's refinement for interpolation.
 **Deliverables**: Generate `data/artifacts/filtered_dataset.csv` (mandatory) and `data/logs/skipped_fold.log` (JSON lines: `{"fold_id": "<id>", "reason": "invalid_scope"}`).
 **Verify**: Assert `data/artifacts/filtered_dataset.csv` exists, contains columns `system_id`, `element_a`, `element_b`, `temperature`, `composition`, and is valid CSV; assert `data/logs/skipped_fold.log` exists if any folds were skipped and contains valid JSON lines.
- [X] T024 [US2] **Pilot Baseline Run**: Implement a pilot baseline run in `code/models/train.py` to estimate variance for power analysis.
 1. **Logic**: Run a minimal Random Forest on a subset of the training data. to estimate variance.
 2. **Deliverable**: Generate `data/artifacts/pilot_variance.json` (schema: `{"variance": <float>}`).
 **Dependency**: T022, T023.
 **Verify**: Assert `data/artifacts/pilot_variance.json` exists.
- [X] T025 [US2] **Power Analysis**: Implement statistical power analysis (target ≥0.8) in `code/models/train.py` using `statsmodels`.
 1. **Logic**: Use variance from `data/artifacts/pilot_variance.json` to calculate power.
 2. **Action**: If power < 0.8, **HALT** with `INSUFFICIENT_POWER` and report detailed metrics (effect size, sample size, power). (FR-011, FR-014)
 **Dependency**: T024.
 **Verify**: Assert `state/...yaml` is updated with power analysis details if halted.
- [X] T026 [US2] **Model Training & Baseline Comparison**: Implement `code/models/train.py` with Random Forest Regressor (scikit-learn) and LOSO strategy (FR-003).
 1. **Algorithm**: Use `sklearn.model_selection.LeaveOneGroupOut` on the `system_id` column.
 2. **Baseline**: Calculate the null model baseline using the **GLOBAL MEAN EXPERIMENTAL TEMPERATURE** (calculated from the entire dataset before CV split). (FR-009)
 3. **Deliverable**: Generate `data/artifacts/baseline_comparison.json` (schema: `{"null_model_mae": <float>, "rf_model_mae": <float>, "percentage_improvement": <float>}`). **Constraint**: Baseline must be global mean. (FR-009)
 **Dependency**: T022, T023, T025 (must pass).
 **Verify**: Assert `data/artifacts/baseline_comparison.json` exists and contains keys `null_model_mae`, `rf_model_mae`, `percentage_improvement`.
- [X] T027 [US2] Verify SC-008: Implement Permutation Test on fold-level MAE differences between Random RF and Null Model baseline.
 1. **Algorithm**: Shuffle the fold-level MAE differences (RF vs Null) multiple times for robust resampling. Calculate the p-value as the fraction of permuted statistics (absolute mean difference) that are >= the observed statistic.
 2. **Deliverable**: Generate `data/artifacts/permutation_pvalue.txt` (schema: `{"p_value": <float>}`). **Verification**: If p < 0.05, report percentage improvement. If p >= 0.05, raise `NO_SIGNIFICANT_IMPROVEMENT` and log to `data/logs/pipeline.log`. (US-2, SC-008, Plan Methodology 4)
 **Verify**: Assert `data/artifacts/permutation_pvalue.txt` exists.
- [X] T028 [US2] Calculate and log MAE and R² per fold and aggregate in `code/models/evaluate.py` (FR-004)
- [X] T029 [US2] Implement data density check in `code/models/evaluate.py`: aggregate errors by `system_id`; compute standard deviation of errors per system; flag `LOW_DATA_DENSITY` if N (count of unique compositions per system_id) < 5 OR SD > 50K. **Requirement**: If N < 2, treat as `LOW_DATA_DENSITY` (SD undefined). Log to `data/logs/pipeline.log` using `code/utils/logging.py` (T005). (FR-008, FR-013, SC-009)
- [X] T030 [US2] Implement resource monitoring wrapper in `code/utils/resource_monitor.py`. **Deliverable**: Log execution time (seconds, int) and peak memory usage (GB, float) to `data/artifacts/resource_log.json` (schema: `{"execution_time_seconds": <int>, "peak_memory_gb": <float>}`). **Enforcement**: If `execution_time_seconds > 14400` OR `peak_memory_gb > 7.0`, HALT the pipeline immediately with error code `RESOURCE_LIMIT_EXCEEDED`. **Dependency**: This wrapper must wrap T026 execution. Use `psutil` for monitoring. (FR-006, SC-003)
 **Verify**: Assert `data/artifacts/resource_log.json` exists and contains `execution_time_seconds` and `peak_memory_gb`.
- [X] T031 [US2] Save trained model artifact to `data/artifacts/model.pkl` with version hash. **Verification**: Assert file exists and hash is recorded in state. (Constitution Principle V)
 **Verify**: Assert `data/artifacts/model.pkl` exists and `state/PROJ-485/...yaml` contains its SHA-256 hash. **Content Accuracy Check**: Compute SHA-256 of `model.pkl` and assert it matches the value recorded in `state/...yaml`.

### Tests for User Story 2 (MANDATORY)
*Note: These tasks are listed after implementation to reflect 'Producer before Consumer' artifact flow.*

- [X] T065 [P] [US2] Write `tests/test_model.py` with function `test_loso_no_new_elements` asserting fold split logic correctly skips folds with new elements but allows interpolation. **Depends on T022 completion.**
- [X] T066 [P] [US2] Write `tests/test_model.py` with function `test_power_analysis_insufficient` asserting `INSUFFICIENT_POWER` is raised when power < 0.8 (Mandatory per FR-014). **Depends on T025 completion.**
- [X] T067 [P] [US2] Write `tests/test_model.py` with function `test_permutation_fail_path` asserting `NO_SIGNIFICANT_IMPROVEMENT` is raised when p >= 0.05. **Depends on T027 completion.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Fidelity Assessment (Priority: P3)

**Goal**: Visualize predicted vs. ground-truth phase diagrams for simple binary systems (e.g., Cu-Zn, Al-Cu).

**Independent Test**: Run `code/viz/plot_phase_diagrams.py` on Cu-Zn; verify PNG/SVG generated with distinct experimental (solid) and predicted (dashed) lines.

### Implementation for User Story 3

- [X] T032 [US3] **Pre-step to T033**: Verify upstream artifacts exist and are valid.
 1. Check `data/artifacts/model.pkl` exists and is not empty.
 2. Check `data/processed/descriptors.csv` exists and is not empty.
 3. If either is missing/invalid, raise `INVALID_DATA_SCHEMA` and halt.
 **Verify**: Assert both files exist. (Constitution Principle II, FR-005)
- [X] T033 [US3] **Implement Plotting**: Implement `code/viz/plot_phase_diagrams.py` to load model artifact from `data/artifacts/model.pkl` (produced by T031) and ground truth for specific systems from `data/processed/descriptors.csv`. **Verification**: Assert model file exists before loading. (FR-005)
 **Verify**: Assert `data/artifacts/model.pkl` exists.
- [X] T034 [US3] Implement logic to generate plots with X-axis (composition 0-100%) and Y-axis (temperature). **Verification**: Assert plot object has correct axis labels and ranges. Use `matplotlib.pyplot`. (US-3)
 **Verify**: Assert plot object has X-axis label 'Composition (%)' and Y-axis label 'Temperature (K)'.
- [X] T035 [US3] Implement visual distinction (solid vs. dashed lines) for experimental vs. predicted boundaries. **Verification**: Assert line styles are distinct in saved plot. (US-3)
 **Verify**: Assert experimental lines are solid and predicted lines are dashed in the generated plot.
- [X] T036 [US3] **Calculate MAE & Enforce Fidelity**: Implement MAE check for visual fidelity.
 1. **Logic**: Calculate MAE between predicted and experimental phase boundary lines.
 2. **Action**: If MAE > 50K, **LOG** the specific error code `LOW_DATA_FIDELITY` and mark the system as 'FAILED' in the report. **Do NOT halt the entire pipeline**. Log to `data/artifacts/fidelity_check.log` (JSON lines: `{"system_id": "<id>", "mae": <float>, "status": "FAILED"}`). **Requirement**: Continue processing other systems. (US-3, SC-004)
 **Verify**: Assert `data/artifacts/fidelity_check.log` exists and contains the failure record if MAE > 50K.
- [X] T037 [US3] **Calculate TCS (Auxiliary Metric)**: Calculate Topological Consistency Score (TCS) for auxiliary reporting ONLY.
 1. **Algorithm**: For each system, select a fixed number of composition slices across the composition range. At each slice, sort the predicted temperatures and experimental temperatures.
 2. **Metric**: TCS = (Number of slices where `sorted(predicted) == sorted(experimental)`) / (Total slices). Result is a normalized float value.
 3. **Deliverable**: Generate `data/artifacts/tcs_report.json` (schema: `{"system": "Cu-Zn", "tcs_score": <float>, "slices_evaluated": <int>}`). **Verification**: Log warning if TCS < 0.8 but DO NOT halt. TCS is an auxiliary metric for topology; the primary gate is MAE (SC-004).
- [X] T038 [US3] Save generated plots to `data/artifacts/plots/` with system ID naming convention. **Verification**: Assert PNG/SVG files exist for ALL systems in `code/config.yaml` -> `required_systems`. (FR-005)
 **Verify**: Assert `data/artifacts/plots/<system_id>.png` exists for every system in the `required_systems` list (e.g., Cu-Zn.png, Al-Cu.png).
- [X] T039 [US3] Exclude complex/metastable systems (e.g., Fe-C) from visualization. **Verification**: Assert Fe-C is not in the generated plots list. **Constraint**: Visualization must be limited to 'simple binary systems' (e.g., Cu-Zn, Al-Cu). (US-3, Assumptions)
 **Verify**: Assert `data/artifacts/plots/Fe-C.png` does NOT exist.
- [X] T040 [US3] Generate comprehensive fidelity report.
 1. Read `data/artifacts/fidelity_check.log`.
 2. Generate `data/artifacts/fidelity_report.json` with schema: `{"systems": [{"system_id": "<id>", "mae": <float>, "tcs": <float>, "status": "PASSED" | "FAILED"}], "overall_status": "PASSED" | "FAILED"}`.
 3. Mark status as 'FAILED' if MAE > 50K.
 **Verify**: Assert `data/artifacts/fidelity_report.json` exists and contains all systems with correct status.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates in `docs/` (README, API docs)
- [X] T042 [P] Code cleanup and refactoring (remove debug prints, optimize loops)
- [X] T043 [P] Additional unit tests for edge cases (ternary systems, empty datasets)
- [X] T044 [P] Run `quickstart.md` validation script
- [X] T045 [P] Update `state/PROJ-485/...yaml` with final artifact hashes
 **Verify**: Assert `state/PROJ-485/...yaml` contains hashes for all final artifacts. **Content Accuracy Check**: Compute SHA-256 of each final artifact and assert it matches the value recorded in `state/...yaml`.

---

## Phase N+1: Review Resolution & Robustness (Revision Pass)

**Goal**: Address specific reviewer concerns regarding data source verification, streaming logic, and error handling robustness identified in prior research-stage reviews.

### Implementation for Review Resolution

- [X] T046 [P] [US1] **Data Source Verification**: Confirm `code/ingest/load_data.py` strictly enforces the "Fail Loudly" policy. Ensure the script raises a specific `ValueError` with code `DATA_SOURCE_MISSING` if the verified URL block is empty or the fetch fails after retries. No synthetic fallbacks exist. (Constitution Principle II, Rule: Loader must fail loudly)
 **Verify**: Run pipeline with empty URL block and assert `DATA_SOURCE_MISSING` is raised.
- [X] T047 [P] [US1] **Verified Source Injection**: Add a pre-check in `code/ingest/load_data.py` to detect if a "VERIFIED REAL DATA SOURCE" block is injected by the execution stage. If present, override `code/config.yaml` defaults and use the injected package/recipe as the sole source. (Rule: If a verified real data source is injected, USE it)
 **Verify**: Inject a verified source and assert it is used instead of config defaults.
- [X] T048 [P] [US2] **Convex Hull Validation**: Refine `code/models/train.py` (T022 logic) to strictly enforce FR-010. Ensure the "New Element" check explicitly halts or skips the fold with a clear log entry (`INVALID_SCOPE`) if the test set contains elements not present in the training set's convex hull of properties. (FR-010, Plan Methodology 3)
 **Verify**: Run a test case with an extrapolated element and assert `INVALID_SCOPE` is logged and the fold is skipped.
- [X] T049 [P] [US2] **Statistical Power Analysis Rigor**: Enhance `code/models/train.py` (T025) to perform a more rigorous power analysis using the actual variance observed in the pilot run, not just a theoretical estimate. Ensure the `INSUFFICIENT_POWER` error is raised with a detailed report of the calculated power, effect size, and sample size. (FR-011, FR-014)
 **Verify**: Run with a small dataset and assert the error log contains the detailed power analysis report.
- [X] T050 [P] [US3] **Fidelity Threshold Enforcement**: Update `code/viz/plot_phase_diagrams.py` to strictly enforce the 50K MAE threshold. If the MAE exceeds this limit, the system must log the specific error code `LOW_DATA_FIDELITY` and flag the system in the final report as 'FAILED', ensuring the success criterion is met or explicitly failed. (US-3, SC-004)
 **Verify**: Run with a system having MAE > 50K and assert `LOW_DATA_FIDELITY` is logged and system marked 'FAILED'.
- [X] T052 [P] [US1] **Memory Monitoring**: Implement periodic memory check in `code/utils/resource_monitor.py` that runs at regular intervals during training. If memory usage increases by > 10% in a -minute window (relative to start of task), log `POTENTIAL_MEMORY_LEAK` to `data/logs/pipeline.log` and halt the pipeline with `RESOURCE_LIMIT_EXCEEDED`. **Verify**: Simulate a memory leak and assert the pipeline halts with the specific error code.
- [X] T053 [P] [US1] **Test Case Definition**: Implement a test case in `tests/test_ingest.py` to verify streaming logic. **Test Case**: Run on a simulated large file generated by `code/tests/generate_large_dataset.py` and assert peak memory < 7 GB while processing. **Dependency**: T013. **Verify**: Run on a simulated large file (1M rows) and assert peak memory < 7 GB while processing.
- [X] T054 [P] [US2] **Extrapolation Check Refinement**: Enhance `code/models/train.py` (T023) to calculate the convex hull of elemental properties (radius, EN) for the training set elements using `scipy.spatial.ConvexHull`. If a test set element falls outside this hull (extrapolation), the fold must be skipped and logged as `INVALID_SCOPE`. Ensure this logic is distinct from the "new element" check but follows the same strict skip policy. **Verify**: Run a test case with an extrapolated element and assert `INVALID_SCOPE` is logged and the fold is skipped.
- [X] T055 [P] [US3] **Visual Fidelity Reporting**: Update `code/viz/plot_phase_diagrams.py` to generate a comprehensive fidelity report (`data/artifacts/fidelity_report.json`) that lists each system, its MAE, TCS, and a 'status' field ('PASSED' or 'FAILED') based on the 50K MAE threshold. **Dependency**: T036, T037. **Verify**: Assert the report contains all systems and correctly flags those with MAE > 50K as 'FAILED'.
- [X] T056 [P] [US1] **Resource Limit Enforcement**: Implement strict HALT logic in `code/ingest/load_data.py`. If the real NIST-JANAF/SGTE dataset exceeds the 7GB RAM limit even with streaming, **HALT** the pipeline immediately with `RESOURCE_LIMIT_EXCEEDED`. **Do NOT implement a sampling strategy**. (Constitution Principle II, Rule: Large real datasets: STREAM the real data)
 **Verify**: Run on a large-scale dataset and assert the pipeline halts with `RESOURCE_LIMIT_EXCEEDED`.
- [X] T057 [P] [US1] **Error Code Granularity Expansion**: Expand `code/utils/error_codes.py` to include specific codes for `DATA_SCHEMA_MISMATCH` (when column names differ but types match), `TEMPERATURE_RANGE_VIOLATION` (when T < 0K or T > 5000K), and `COMPOSITION_SUM_ERROR` (when composition fractions do not sum to 1.0 ± 0.01). Update `code/ingest/load_data.py` to detect and log these specific conditions to `data/logs/pipeline.log`. **Verify**: Run with malformed data and assert the correct specific error code is logged in `data/logs/pipeline.log`.
- [X] T061 [P] [US1] **Data Integrity Checksum Verification**: Add a final verification step in `code/ingest/load_data.py` that re-computes the SHA-256 checksum of the processed `data/processed/descriptors.csv` and compares it against the expected hash stored in `state/PROJ-485/...yaml`. If they do not match, raise `DATA_INTEGRITY_VIOLATION` and halt. **Verify**: Corrupt the processed file and assert the pipeline halts with the integrity error.
- [X] T062 [P] [US3] **Plot Resolution and Quality Check**: Ensure all generated plots in `code/viz/plot_phase_diagrams.py` have a minimum resolution of high DPI for publication quality. Add a check that verifies the saved PNG/SVG files meet this resolution requirement. If not, log `LOW_RESOLUTION_PLOT` and regenerate with higher DPI. **Dependency**: T038. **Verify**: Generate a plot and assert the file metadata shows >= 300 DPI.
- [X] T063 [P] [US2] **Random Seed Reproducibility Audit**: Add a test task in `tests/test_model.py` named `test_reproducibility_audit` to run the entire training pipeline twice with the same seed and assert that the resulting `model.pkl` checksums and all metric JSON files are identical. This ensures deterministic behavior. **Dependency**: T026, T031. **Verify**: Run the audit test and assert checksums match.
- [X] T064 [P] [US1] **Streamed Data Aggregation Validation**: Verify that the streamed data aggregation logic in `code/ingest/load_data.py` correctly accumulates statistics (mean, variance) across all chunks without overflow or precision loss. **Implementation**: First, create `code/tests/generate_large_dataset.py` to generate a multi-million row file with known statistics. Then, run the test that processes this file in chunks and compares the final stats against a single-pass calculation of the same file. **Dependency**: T013. **Verify**: Run the test and assert the aggregated stats match the single-pass stats within 1e-6 tolerance.
- [X] T058 [P] [US2] **LOSO Fold Robustness Check**: Implement a check in `code/models/train.py` to skip folds with fewer than a sufficient number of data points in the test set. **Logic**: If test set size < 3, log `LOW_DATA_DENSITY` (reusing existing code) with a specific message "Test set size < 3" and skip the fold. **Dependency**: T022. **Verify**: Run a test case with a small test set and assert the fold is skipped and logged correctly.

---

## Phase N+2: Final Integration & Validation

**Goal**: Ensure end-to-end pipeline integrity and resolve any remaining edge cases identified during final integration testing.

### Implementation for Final Integration

- [ ] T068 [P] [US1] **End-to-End Pipeline Dry Run**: Execute the full pipeline from raw data ingestion to final visualization report on a small, controlled subset of data (e.g., only Cu-Zn system) to verify all components integrate correctly. **Requirement**: The pipeline must complete without raising unhandled exceptions and produce all expected artifacts in `data/artifacts/`. **Verify**: Assert `data/artifacts/model.pkl`, `data/artifacts/fidelity_report.json`, and `data/artifacts/plots/Cu-Zn.png` exist and are valid.
- [ ] T069 [P] [US2] **Cross-Validation Consistency Check**: Verify that the LOSO cross-validation results are consistent across multiple runs with the same random seed. **Requirement**: Run the training script three times with the same seed and compare the resulting MAE and R² values in `data/artifacts/baseline_comparison.json`. **Verify**: Assert that the metric values are identical (within floating point tolerance) across all three runs.
- [X] T070 [P] [US3] **Visualization Quality Assurance**: Run a script `code/viz/validate_plot_quality.py` to verify all generated plots meet the resolution requirements (>= 300 DPI) and contain correct axis labels. **Requirement**: The script must fail if any plot does not meet criteria. **Verify**: Assert the validation script passes.
- [ ] T071 [P] [General] **Documentation Finalization**: Update the `README.md` and `docs/` to reflect the final state of the project, including instructions for running the pipeline, interpreting results, and known limitations. **Requirement**: Documentation must be clear, concise, and accurate. **Verify**: Run the documentation build process (if applicable) and ensure no warnings or errors are generated.
- [ ] T072 [P] [General] **Performance Optimization Review**: Review the codebase for potential performance bottlenecks and implement optimizations where feasible without compromising correctness. **Requirement**: Focus on areas identified during resource monitoring (T030, T052) and streaming logic (T013). **Verify**: Run the pipeline with the optimized code and confirm that execution time and memory usage are within acceptable limits.
- [ ] T073 [P] [General] **Security Audit**: Conduct a security audit of the codebase to identify and remediate any potential vulnerabilities (e.g., insecure file handling, hardcoded credentials). **Requirement**: Use automated tools (e.g., `bandit`, `safety`) and manual review. **Verify**: Generate a security audit report with "No Critical Issues" status.
- [ ] T074 [P] [General] **Compliance Verification**: Verify that the project adheres to all constitutional principles and specification requirements. **Requirement**: Create a compliance checklist mapping each principle/requirement to the corresponding implementation task. **Verify**: Submit a completed compliance checklist with "Compliant" status for all items.
- [ ] T075 [P] [General] **Final Release Preparation**: Prepare the project for release by tagging the repository, generating release notes, and ensuring all artifacts are properly versioned and documented. **Requirement**: Follow the project's release process. **Verify**: Confirm that the release is tagged and all artifacts are accessible.
