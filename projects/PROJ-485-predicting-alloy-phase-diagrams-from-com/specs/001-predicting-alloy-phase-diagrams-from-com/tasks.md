# Tasks: Predicting Alloy Phase Diagrams from Compositional Data

**Input**: Design documents from `/specs/001-predict-alloy-phase-diagrams/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY where spec acceptance criteria require verification (e.g., US-1 Independent Test).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] **Initialize Project Structure**: Create all required directories (`code/`, `code/ingest`, `code/features`, `code/models`, `code/viz`, `code/utils`, `data/raw`, `data/processed`, `data/artifacts`, `state/`) and all necessary `__init__.py` files for the `code/` package structure. Create `.gitignore` excluding `data/raw/*`, `data/processed/*`, `data/artifacts/*`, `*.pyc`, `__pycache__`, `state/*.yaml` EXCEPT `state/PROJ-485/*.yaml` (Constitution Principle V). **Verify**: Run `find code -type d | wc -l` and assert count > 10.
- [X] T003 [P] **Configure Linting and Formatting**:
 1. Create `.ruff.toml` with content:
```toml
[lint]
select = ["E", "F", "W", "I"]
ignore = []
max-line-length = 88

[lint.isort]
known-first-party = ["code"]

[lint.pydocstyle]
convention = "google"

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```
 2. Create `pyproject.toml` with black config:
```toml
[tool.black]
line-length = 88
target-version = ['py311']
```
**Verify**: Run `ruff check .` and assert exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `code/utils/logging.py` for structured error logging (FR-007, FR-008)
- [X] T005 [P] Implement `code/utils/checksum.py` for SHA-256 data verification (Constitution Principle III)
- [X] T006 [P] Create `data/raw/elemental_properties.csv` with columns: `element`, `atomic_radius_angstrom`, `electronegativity_pauling`, `valence_electrons`. Seed with rows for Cu, Al, Zn, Fe, C (Constitution Principle III)
- [X] T007 [P] Create `code/main.py` pipeline orchestrator with state management (state/PROJ-485/...yaml)
- [X] T008 [P] Implement `code/utils/error_codes.py` as a Python Enum class with string values for: `DATA_SOURCE_MISSING`, `INVALID_DATA_SCHEMA`, `MISSING_TEMP_COORDS`, `LOW_DATA_DENSITY`, `API_RATE_LIMIT_EXCEEDED`, `INSUFFICIENT_POWER`, `INVALID_SCOPE`, `RESOURCE_LIMIT_EXCEEDED`
- [X] T009a [P] Define configuration schema for `code/config.yaml`. **Requirement**: Must include keys `nist_janaf_url`, `sgte_url`, `local_fallback_path`. **Validation**: Schema must explicitly require phase boundary coordinates (temperature, composition) as part of the data validation rules (FR-001).
- [X] T009b [P] Create `code/config.yaml` with the defined schema. **Content**:
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
```
**Validation**: Script must fail if these keys are missing or empty. (Constitution Principle II, Plan Methodology 1)
- [X] T009c [P] Implement 'Source Check' gating logic in `code/ingest/load_data.py` (or a pre-check utility) to verify if NIST-JANAF/SGTE URLs exist in the verified input block (from T009); halt with `DATA_SOURCE_MISSING` if absent (Plan Methodology 1). **Dependency**: T009

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw binary/ternary alloy phase data from NIST-JANAF/SGTE (or local CSV) and generate compositional descriptors.

**Independent Test**: Run `code/ingest/load_data.py` against a small hardcoded subset; verify output CSV has correct rows and derived columns with valid numeric ranges.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/ingest/load_data.py` with exponential backoff (limited retries) for API access (FR-001, FR-007)
- [X] T013 [US1] Implement fallback logic in `code/ingest/load_data.py` to load local CSVs ONLY if `local_fallback_path` in `code/config.yaml` points to an existing, verified real file. **Requirement**: If the path is empty or the file does not exist, the system MUST raise `DATA_SOURCE_MISSING`. Do NOT generate synthetic data. The fallback path is validated at runtime and supports loading from a verified input block (FR-001, FR-012).
- [X] T014 [US1] Implement filtering logic:
 1. Skip entries with missing temperature values in binary systems (handled by FR-001).
 2. Skip entries for ternary systems lacking temperature-composition coordinates. **Requirement**: Log `MISSING_TEMP_COORDS` ONLY for the ternary case to `data/logs/pipeline.log` (JSON line format: `{"timestamp": "...", "level": "ERROR", "code": "MISSING_TEMP_COORDS", "message": "Row <id> excluded: ternary system missing temperature-composition coordinates"}`). **Depends on T008**. (FR-001, FR-008)
 **Verify**: Assert `data/logs/pipeline.log` exists and contains a line with code `MISSING_TEMP_COORDS`.
- [X] T015 [US1] Implement `code/features/generate_descriptors.py` to calculate: mean atomic radius, electronegativity variance, valence electron count, Hume-Rothery concentration using constants from `data/raw/elemental_properties.csv` (created by T006) (FR-002, FR-015)
- [X] T016 [US1] Add validation in `code/features/generate_descriptors.py` to verify derived values against `data/raw/elemental_properties.csv` (SC-005, SC-007)
- [X] T017 [US1] Implement data checksumming and state update in `code/ingest/load_data.py` after raw data load (Constitution Principle III, V)
- [X] T018 [US1] Write processed data to `data/processed/descriptors.csv` with schema compliance (FR-001). **Verify**: Run `code/utils/validate_schema.py data/processed/descriptors.csv` and assert exit code 0.

### Tests for User Story 1 (MANDATORY)
*Note: These tasks are listed after implementation to reflect 'Producer before Consumer' artifact flow. They depend on T008 and T012-T018. Test tasks must be executed ONLY after their corresponding implementation tasks are complete.*

- [X] T010 [P] [US1] Write `tests/test_ingest.py` with function `test_invalid_schema_raises_error` asserting `INVALID_DATA_SCHEMA` is raised when phase boundary coordinates (temperature, composition) are missing. **Depends on T008 completion.**
- [X] T011 [P] [US1] Write `tests/test_features.py` with function `test_descriptor_deviation` asserting derived values deviate ≤1% from `data/raw/elemental_properties.csv` (Mandatory per US-1 Independent Test)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest Regressor with LOSO cross-validation, perform power analysis, and compare against null baseline.

**Independent Test**: Execute `code/models/train.py` on fixed seed; verify LOSO report (MAE, R²), power analysis report, and model file saved to disk.

### Implementation for User Story 2

- [X] T022 [US2] **Pre-step to T021**. Implement 'Property Range Extrapolation' and 'New Element' checks.
 1. **New Element Check (FR-010)**: Verify if any element in test fold is NOT present in training fold. If yes, skip fold and log `INVALID_SCOPE` (not `DATA_SOURCE_MISSING`).
 2. **Extrapolation Check (Plan)**: Calculate convex hull of elemental properties (radius, EN) in training set using data from `data/raw/elemental_properties.csv` for the specific elements in the training fold. Log warning if test elements fall outside hull, but do NOT skip based on this alone unless new elements are found.
 **Deliverables**: Generate `data/artifacts/convex_hull.json` (schema: `{"vertices": [{"element": "Cu", "radius": <float>, "electronegativity": <float>},...]}`) and `data/logs/skipped_fold.log` (JSON lines: `{"fold_id": "Cu-Zn", "reason": "invalid_scope"}`). **Requirement**: The generation of `data/artifacts/convex_hull.json` is a mandatory artifact that must be written to disk before T021 executes. **Primary Deliverable**: The skip logic for FR-010. The JSON is secondary for traceability. (FR-010, Plan Methodology 3)
 **Verify**: Assert `data/artifacts/convex_hull.json` exists and is valid JSON; assert `data/logs/skipped_fold.log` exists if any folds were skipped.
- [X] T021 [US2] **Depends on T018, T022**. Implement `code/models/train.py` with Random Forest Regressor (scikit-learn) and LOSO strategy (FR-003). **Algorithm**: Use `sklearn.model_selection.LeaveOneGroupOut` on the `system_id` column. **Dependency**: T022 must be complete before T021 runs.
- [X] T023 [US2] Implement statistical power analysis (target ≥0.8) in `code/models/train.py` using `statsmodels`; halt with `INSUFFICIENT_POWER` if failed (FR-011, FR-014)
- [X] T024 [US2] Implement null model baseline (global mean) and comparison logic.
 1. **Global Mean Calculation**: Calculate the mean experimental temperature of the **ENTIRE** dataset (not per fold) to establish a constant baseline as required by FR-009.
 2. **Prediction**: For each LOSO fold, generate predictions for the *test fold* using this constant global mean.
 3. **Deliverable**: Generate `data/artifacts/baseline_comparison.json` (schema: `{"null_model_mae": <float>, "rf_model_mae": <float>, "percentage_improvement": <float>}`). **Constraint**: Baseline must be derived from experimental data distinct from any computational assessment. (FR-009)
 **Verify**: Assert `data/artifacts/baseline_comparison.json` exists and contains keys `null_model_mae`, `rf_model_mae`, `percentage_improvement`.
- [X] T025 [US2] Verify SC-008: Implement Permutation Test on fold-level MAE differences between Random Forest and Null Model baseline.
 1. **Algorithm**: Shuffle the fold-level MAE differences (RF vs Null) [deferred] times. Calculate the p-value as the fraction of permuted statistics (absolute mean difference) that are >= the observed statistic.
 2. **Deliverable**: Write `data/artifacts/permutation_pvalue.txt` containing raw float with a standard level of precision. **Verification**: Assert p < 0.05 AND report percentage improvement. (US-2, SC-008, Plan Methodology 4)
 **Verify**: Assert `data/artifacts/permutation_pvalue.txt` exists and contains a float < 0.05.
- [X] T026 [US2] Calculate and log MAE and R² per fold and aggregate in `code/models/evaluate.py` (FR-004)
- [X] T027 [US2] Implement data density check in `code/models/evaluate.py`: aggregate errors by `system_id`; compute standard deviation of errors per system; flag `LOW_DATA_DENSITY` if N (count of unique compositions per system_id) < 5 OR SD > 50K. **Requirement**: Log to structured log file using T008 Enum. (FR-008, FR-013, SC-009)
- [X] T028 [US2] Implement resource monitoring wrapper in `code/utils/resource_monitor.py`. **Deliverable**: Log execution time (seconds, int) and peak memory usage (GB, float) to `data/artifacts/resource_log.json` (schema: `{"execution_time_seconds": <int>, "peak_memory_gb": <float>}`). **Enforcement**: If `execution_time_seconds > 14400` OR `peak_memory_gb > 7.0`, HALT the pipeline immediately with error code `RESOURCE_LIMIT_EXCEEDED`. **Dependency**: This wrapper must wrap T021 and T023 execution. (FR-006, SC-003)
 **Verify**: Assert `data/artifacts/resource_log.json` exists and contains `execution_time_seconds` and `peak_memory_gb`.
- [X] T029 [US2] Save trained model artifact to `data/artifacts/model.pkl` with version hash. **Verification**: Assert file exists and hash is recorded in state. (Constitution Principle V)
 **Verify**: Assert `data/artifacts/model.pkl` exists and `state/PROJ-485/...yaml` contains its SHA-256 hash.

### Tests for User Story 2 (MANDATORY)
*Note: These tasks are listed after implementation to reflect 'Producer before Consumer' artifact flow.*

- [X] T019 [P] [US2] Write `tests/test_model.py` with function `test_loso_no_new_elements` asserting fold split logic correctly skips folds with new elements but allows interpolation. **Depends on T022 completion.**
- [X] T020 [P] [US2] Write `tests/test_model.py` with function `test_power_analysis_insufficient` asserting `INSUFFICIENT_POWER` is raised when power < 0.8 (Mandatory per FR-014). **Depends on T023 completion.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Fidelity Assessment (Priority: P3)

**Goal**: Visualize predicted vs. ground-truth phase diagrams for simple binary systems (e.g., Cu-Zn, Al-Cu).

**Independent Test**: Run `code/viz/plot_phase_diagrams.py` on Cu-Zn; verify PNG/SVG generated with distinct experimental (solid) and predicted (dashed) lines.

### Implementation for User Story 3

- [X] T032 [US3] **Depends on T029**. Implement `code/viz/plot_phase_diagrams.py` to load model artifact from `data/artifacts/model.pkl` (produced by T029) and ground truth for specific systems. **Verification**: Assert model file exists before loading. (FR-005)
 **Verify**: Assert `data/artifacts/model.pkl` exists.
- [X] T033 [US3] Implement logic to generate plots with X-axis (composition 0-100%) and Y-axis (temperature). **Verification**: Assert plot object has correct axis labels and ranges. Use `matplotlib.pyplot`. (US-3)
 **Verify**: Assert plot object has X-axis label 'Composition (%)' and Y-axis label 'Temperature (K)'.
- [X] T034 [US3] Implement visual distinction (solid vs. dashed lines) for experimental vs. predicted boundaries. **Verification**: Assert line styles are distinct in saved plot. (US-3)
 **Verify**: Assert experimental lines are solid and predicted lines are dashed in the generated plot.
- [X] T035 [US3] Calculate Topological Consistency Score (TCS):
 1. **Algorithm**: For each system, select fixed composition slices (e.g., 0.1, 0.2,... 0.9). At each slice, sort the predicted temperatures and experimental temperatures.
 2. **Metric**: TCS = (Number of slices where `sorted(predicted) == sorted(experimental)`) / (Total slices). Result is a normalized float value.
 3. **Deliverable**: Generate `data/artifacts/tcs_report.json` (schema: `{"system": "Cu-Zn", "tcs_score": <float>, "slices_evaluated": <int>}`). **Verification**: Log warning if TCS < 0.8 but DO NOT halt. TCS is an auxiliary metric for topology; the primary gate is MAE (SC-004). (Methodology Section 4, SC-004)
 **Verify**: Assert `data/artifacts/tcs_report.json` exists and contains `tcs_score`.
- [X] T036 [US3] Implement MAE check for visual fidelity.
 1. **Logic**: Calculate MAE between predicted and experimental phase boundary lines.
 2. **Action**: If MAE > 50K, log a warning with error code `LOW_DATA_FIDELITY` to `data/artifacts/fidelity_check.log` (JSON lines: `{"system": "Cu-Zn", "mae": <float>, "status": "FAILED"}`). **Requirement**: Mark the *system-specific* result as 'FAILED' in the final report to explicitly record that SC-004 is unmet for this system. Do NOT halt the pipeline execution for other systems, but the success criterion (SC-004) is considered unmet for this specific system. (US-3, SC-004)
 **Verify**: Assert `data/artifacts/fidelity_check.log` exists and contains the failure record if MAE > 50K.
- [X] T037 [US3] Save generated plots to `data/artifacts/plots/` with system ID naming convention. **Verification**: Assert PNG/SVG files exist. (FR-005)
 **Verify**: Assert `data/artifacts/plots/Cu-Zn.png` exists.
- [X] T038 [US3] Exclude complex/metastable systems (e.g., Fe-C) from visualization. **Verification**: Assert Fe-C is not in the generated plots list. **Constraint**: Visualization must be limited to 'simple binary systems' (e.g., Cu-Zn, Al-Cu). (US-3, Assumptions)
 **Verify**: Assert `data/artifacts/plots/Fe-C.png` does NOT exist.

### Tests for User Story 3 (MANDATORY)
*Note: These tasks are listed after implementation to reflect 'Producer before Consumer' artifact flow.*

- [X] T030 [P] [US3] Write `tests/test_viz.py` with function `test_tcs_calculation` verifying partial match ratio formula logic (Mandatory per SC-004 auxiliary check). **Depends on T035 completion.**
 **Verify**: Run `pytest tests/test_viz.py::test_tcs_calculation` and assert exit code 0.
- [X] T031 [P] [US3] Write `tests/integration/test_viz.py` with function `test_plot_generation` verifying PNG/SVG output exists (Mandatory per US-3). **Depends on T032, T037 completion.**
 **Verify**: Run `pytest tests/integration/test_viz.py::test_plot_generation` and assert exit code 0.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Documentation updates in `docs/` (README, API docs)
- [X] T040 Code cleanup and refactoring (remove debug prints, optimize loops)
- [X] T041 Performance optimization: ensure data subsampling if memory > 6 GB
- [X] T042 [P] Additional unit tests for edge cases (ternary systems, empty datasets)
- [X] T043 Run `quickstart.md` validation script
- [X] T044 Update `state/PROJ-485/...yaml` with final artifact hashes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**:
 - **Strict Sequential Flow**: Phase 3 (US1) MUST complete (specifically T018) before Phase 4 (US2) begins (specifically T021).
 - Phase 5 (US3) depends on Phase 4 (US2) completion (specifically T029).
 - User stories can then proceed in parallel (if staffed) only after their respective upstream phases are complete.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 data output (T018). Cannot start until T018 completes.
- **User Story 3 (P3)**: Depends on US2 model output (T029). Cannot start until T029 completes.

### Within Each User Story

- **Implementation First**: Implementation tasks (e.g., T012-T018) MUST be completed before their corresponding Test tasks (e.g., T010-T011) can be written or executed. This reflects the 'Producer before Consumer' artifact flow.
- Tests are written *after* code exists to verify functionality (TDD cycle: Red -> Green -> Refactor, but task list order reflects execution dependency).
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows) ONLY IF upstream dependencies are met.
- All tests for a user story marked [P] can run in parallel AFTER implementation is complete.
- Different user stories can be worked on in parallel by different team members ONLY if dependencies are satisfied.

---

## Parallel Example: User Story 1

```bash
# Launch all implementation for User Story 1 together:
Task: "Implement code/ingest/load_data.py"
Task: "Implement code/features/generate_descriptors.py"

# Launch all tests for User Story 1 together (AFTER code is written):
Task: "Unit test for schema validation in tests/test_ingest.py"
Task: "Unit test for descriptor calculation in tests/test_features.py"
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
 - Developer B: User Story 2 (waits for A to finish T018)
 - Developer C: User Story 3 (waits for B to finish T029)
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
- **Critical Constraint**: All tasks must run on free CPU-only CI (cores, limited RAM, no GPU). No 8-bit/4-bit quantization or CUDA dependencies.
- **Data Integrity**: No synthetic/fake data generation. All tasks must use real data from NIST-JANAF/SGTE or verified local CSVs.
- **Data Streaming Requirement**: For datasets exceeding substantial RAM capacity, tasks MUST implement streaming (e.g., `datasets.load_dataset(..., streaming=True)`) or explicit chunking. Do not load entire datasets into memory.
- **Loader Failure Policy**: Data loaders MUST fail loudly (raise exception) if real data fetch fails. Do NOT implement synthetic fallbacks.
- **Real Data Only**: All analysis tasks must consume real datasets. Synthetic or toy stand-ins are prohibited.

---

## Phase N+1: Review Resolution & Robustness (Revision Pass)

**Goal**: Address specific reviewer concerns regarding data source verification, streaming logic, and error handling robustness identified in prior research-stage reviews.

### Implementation for Review Resolution

- [X] T045 [P] [US1] **Data Source Verification**: Confirm `code/ingest/load_data.py` strictly enforces the "Fail Loudly" policy. Ensure the script raises a specific `ValueError` with code `DATA_SOURCE_MISSING` if the verified URL block is empty or the fetch fails after retries. No synthetic fallbacks exist. (Constitution Principle II, Rule: Loader must fail loudly)
 **Verify**: Run pipeline with empty URL block and assert `DATA_SOURCE_MISSING` is raised.
- [X] T046 [P] [US1] **Streaming Implementation**: Implement streaming logic for large dataset ingestion in `code/ingest/load_data.py`. For external sources (NIST-JANAF/SGTE) that are not standard HuggingFace datasets, use `requests` with `stream=True` and manual chunked parsing, or `pandas.read_csv(..., chunksize=...)` for local/HTTP CSVs. Ensure the code accumulates statistics online and writes to `data/processed/descriptors.csv` incrementally. (Rule: Large real datasets: STREAM the real data)
 **Verify**: Run pipeline on large dataset and assert `data/processed/descriptors.csv` is populated without OOM error.
- [X] T047 [P] [US1] **Verified Source Injection**: Add a pre-check in `code/ingest/load_data.py` to detect if a "VERIFIED REAL DATA SOURCE" block is injected by the execution stage. If present, override `code/config.yaml` defaults and use the injected package/recipe as the sole source. (Rule: If a verified real data source is injected, USE it)
 **Verify**: Inject a verified source and assert it is used instead of config defaults.
- [X] T048 [P] [US2] **Convex Hull Validation**: Refine `code/models/train.py` (T022 logic) to strictly enforce FR-010. Ensure the "New Element" check explicitly halts or skips the fold with a clear log entry (`INVALID_SCOPE`) if the test set contains elements not present in the training set's convex hull of properties. (FR-010, Plan Methodology 3)
 **Verify**: Run with a fold containing a new element and assert `INVALID_SCOPE` is logged and fold skipped.
- [X] T049 [P] [US2] **Power Analysis Rigor**: Enhance `code/models/train.py` (T023) to perform a more rigorous power analysis using the actual variance observed in the pilot run, not just a theoretical estimate. Ensure the `INSUFFICIENT_POWER` error is raised with a detailed report of the calculated power, effect size, and sample size. (FR-011, FR-014)
 **Verify**: Run with a small dataset and assert `INSUFFICIENT_POWER` is raised with detailed report.
- [X] T050 [P] [US3] **Fidelity Threshold Enforcement**: Update `code/viz/plot_phase_diagrams.py` (T036) to strictly enforce the 50K MAE threshold. If the MAE exceeds this limit, the system must log the specific error code `LOW_DATA_FIDELITY` and flag the system in the final report as 'FAILED', ensuring the success criterion is met or explicitly failed. (US-3, SC-004)
 **Verify**: Run with a system having MAE > 50K and assert `LOW_DATA_FIDELITY` is logged and system marked 'FAILED'.
