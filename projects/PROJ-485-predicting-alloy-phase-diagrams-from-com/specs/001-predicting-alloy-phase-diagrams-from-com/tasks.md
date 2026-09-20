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

- [ ] T001a1 [P] Create directory `code/`
- [ ] T001a2 [P] Create directory `code/ingest`
- [ ] T001a3 [P] Create directory `code/features`
- [ ] T001a4 [P] Create directory `code/models`
- [ ] T001a5 [P] Create directory `code/viz`
- [ ] T001a6 [P] Create directory `code/utils`
- [ ] T001b1 [P] Create directory `data/raw`
- [ ] T001b2 [P] Create directory `data/processed`
- [ ] T001b3 [P] Create directory `data/artifacts`
- [ ] T001c1 [P] Create directory `state/`
- [ ] T002a1 [P] Create `code/__init__.py` (empty file)
- [ ] T002a2 [P] Create `code/ingest/__init__.py` (empty file)
- [ ] T002a3 [P] Create `code/features/__init__.py` (empty file)
- [ ] T002a4 [P] Create `code/models/__init__.py` (empty file)
- [ ] T002a5 [P] Create `code/viz/__init__.py` (empty file)
- [ ] T002a6 [P] Create `code/utils/__init__.py` (empty file)
- [ ] T002a7 [P] Create `tests/__init__.py` (empty file)
- [ ] T002b [P] Create `.gitignore` excluding `data/raw/*`, `data/processed/*`, `data/artifacts/*`, `*.pyc`, `__pycache__`, `state/*.yaml` EXCEPT `state/PROJ-485/*.yaml` (Constitution Principle V)
- [ ] T003a1 [P] Define linting rules: max-line-length=88, target-version=py311
- [ ] T003a2 [P] Create `.ruff.toml` with content:
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
- [ ] T003b1 [P] Define formatting rules: line-length=88, target-version=py311
- [ ] T003b2 [P] Create `pyproject.toml` with black config:
```toml
[tool.black]
line-length = 88
target-version = ['py311']
```

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `code/utils/logging.py` for structured error logging (FR-007, FR-008)
- [X] T005 [P] Implement `code/utils/checksum.py` for SHA-256 data verification (Constitution Principle III)
- [X] T006 [P] Create `data/raw/elemental_properties.csv` with columns: `element`, `atomic_radius_angstrom`, `electronegativity_pauling`, `valence_electrons`. Seed with rows for Cu, Al, Zn, Fe, C (Constitution Principle III)
- [X] T007 [P] Create `code/main.py` pipeline orchestrator with state management (state/PROJ-485/...yaml)
- [X] T008 [P] Implement `code/utils/error_codes.py` as a Python Enum class with string values for: `DATA_SOURCE_MISSING`, `INVALID_DATA_SCHEMA`, `MISSING_TEMP_COORDS`, `LOW_DATA_DENSITY`, `API_RATE_LIMIT_EXCEEDED`, `INSUFFICIENT_POWER`
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
- [X] T009a [P] Implement 'Source Check' gating logic in `code/ingest/load_data.py` (or a pre-check utility) to verify if NIST-JANAF/SGTE URLs exist in the verified input block (from T009); halt with `DATA_SOURCE_MISSING` if absent (Plan Methodology 1). **Dependency**: T009

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw binary/ternary alloy phase data from NIST-JANAF/SGTE (or local CSV) and generate compositional descriptors.

**Independent Test**: Run `code/ingest/load_data.py` against a small hardcoded subset; verify output CSV has correct rows and derived columns with valid numeric ranges.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/ingest/load_data.py` with exponential backoff (limited retries) for API access (FR-001, FR-007)
- [X] T013 [US1] Implement fallback logic in `code/ingest/load_data.py` to load local CSVs if primary source fails (FR-012)
- [X] T013b [US1] **Fallback Data Generation**: Create `data/raw/fallback_phase_data.csv` containing a small, verified subset of experimental binary phase data (e.g., Cu-Al, Al-Cu) with columns `temperature`, `composition`, `element_a`, `element_b`. **Requirement**: Data must be sourced from public literature or verified local files to ensure the pipeline has a viable path to execution if primary sources are missing. (FR-001, FR-012)
- [X] T014 [US1] Implement filtering logic: 
  1. Skip entries with missing temperature values in binary systems (handled by FR-001).
  2. Skip entries for ternary systems lacking temperature-composition coordinates. **Requirement**: Log `MISSING_TEMP_COORDS` ONLY for the ternary case to `data/logs/pipeline.log` (JSON line format: `{"timestamp": "...", "level": "ERROR", "code": "MISSING_TEMP_COORDS", "message": "Row <id> excluded: ternary system missing temperature-composition coordinates"}`). **Depends on T008**. (FR-001, FR-008)
- [X] T015 [US1] Implement `code/features/generate_descriptors.py` to calculate: mean atomic radius, electronegativity variance, valence electron count, Hume-Rothery concentration using constants from `data/raw/elemental_properties.csv` (created by T006) (FR-002, FR-015)
- [X] T016 [US1] Add validation in `code/features/generate_descriptors.py` to verify derived values against `data/raw/elemental_properties.csv` (SC-005, SC-007)
- [X] T017 [US1] Implement data checksumming and state update in `code/ingest/load_data.py` after raw data load (Constitution Principle III, V)
- [X] T018 [US1] Write processed data to `data/processed/descriptors.csv` with schema compliance (FR-001)

### Tests for User Story 1 (MANDATORY)
*Note: These tasks are listed after implementation to reflect 'Producer before Consumer' artifact flow. They depend on T008 and T012-T018.*

- [X] T010 [P] [US1] Write `tests/test_ingest.py` with function `test_invalid_schema_raises_error` asserting `INVALID_DATA_SCHEMA` is raised when phase boundary coordinates (temperature, composition) are missing. **Depends on T008 completion.**
- [X] T011 [P] [US1] Write `tests/test_features.py` with function `test_descriptor_deviation` asserting derived values deviate ≤1% from `data/raw/elemental_properties.csv` (Mandatory per US-1 Independent Test)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest Regressor with LOSO cross-validation, perform power analysis, and compare against null baseline.

**Independent Test**: Execute `code/models/train.py` on fixed seed; verify LOSO report (MAE, R²), power analysis report, and model file saved to disk.

### Implementation for User Story 2

- [X] T022 [US2] **Pre-step to T021**. Implement 'Property Range Extrapolation' and 'New Element' checks.
 1. **New Element Check (FR-010)**: Verify if any element in test fold is NOT present in training fold. If yes, skip fold and log `DATA_SOURCE_MISSING` (or `INVALID_DATA_SCHEMA` if interpreted as data quality issue, but spec says skip/halt). **Decision**: Skip fold.
 2. **Extrapolation Check (Plan)**: Calculate convex hull of elemental properties (radius, EN) in training set. Log warning if test elements fall outside hull, but do NOT skip based on this alone unless new elements are found.
 **Deliverables**: Generate `data/artifacts/convex_hull.json` (schema: `{"vertices": [{"element": "Cu", "radius": 1.28,...},...]}`) and `data/logs/skipped_fold.log` (JSON lines: `{"fold_id": "Cu-Zn", "reason": "new_element"}`). **Requirement**: The generation of `data/artifacts/convex_hull.json` is a mandatory artifact that must be written to disk before T021 executes. (FR-010, Plan Methodology 3)
- [X] T021 [US2] **Depends on T018, T022**. Implement `code/models/train.py` with Random Forest Regressor (scikit-learn) and LOSO strategy (FR-003)
- [X] T023 [US2] Implement statistical power analysis (target ≥0.8) in `code/models/train.py` using `statsmodels`; halt with `INSUFFICIENT_POWER` if failed (FR-011, FR-014)
- [X] T024 [US2] Implement null model baseline (global mean) and comparison logic. 
 1. **Per-Fold Baseline**: For each LOSO fold, calculate the mean experimental temperature of the *training fold* only.
 2. **Prediction**: Generate predictions for the *test fold* using this training-fold mean.
 3. **Deliverable**: Generate `data/artifacts/baseline_comparison.json` (schema: `{"null_model_mae": "<null_mae_value>", "rf_model_mae": "<rf_mae_value>", "percentage_improvement": "<improvement_percentage>"}`). **Constraint**: Baseline must be derived from experimental data distinct from any computational assessment. (FR-009)
- [X] T025 [US2] Verify SC-008: Implement Permutation Test on fold-level MAE differences between Random Forest and Null Model baseline. 
 1. **Algorithm**: Shuffle the fold-level MAE differences (RF vs Null) a sufficient number of times. Calculate the p-value as the fraction of permuted statistics (absolute mean difference) that are >= the observed statistic.
 2. **Deliverable**: Write `data/artifacts/permutation_pvalue.txt` containing raw float with a standard level of precision. **Verification**: Assert p < 0.05 AND report percentage improvement. (US-2, SC-008, Plan Methodology 4)
- [X] T026 [US2] Calculate and log MAE and R² per fold and aggregate in `code/models/evaluate.py` (FR-004)
- [X] T027 [US2] Implement data density check in `code/models/evaluate.py`: aggregate errors by `system_id`; compute standard deviation of errors per system; flag `LOW_DATA_DENSITY` if N (count of unique compositions per system_id) < 5 OR SD > 50K. **Requirement**: Log to structured log file using T008 Enum. (FR-008, FR-013, SC-009)
- [X] T028 [US2] Implement resource monitoring wrapper in `code/utils/resource_monitor.py`. **Deliverable**: Log execution time and peak memory usage to `data/artifacts/resource_log.json` (schema: `{The execution time will be measured and recorded., peak_memory_gb: moderate}`). **Verification**: If time > 4h or memory > 7GB, log a warning/error to the log file indicating the constraint violation, but do NOT enforce a hard halt (aligning with SC-003 success criteria). (FR-006, SC-003)
- [X] T029 [US2] Save trained model artifact to `data/artifacts/model.pkl` with version hash. **Verification**: Assert file exists and hash is recorded in state. (Constitution Principle V)

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
- [X] T033 [US3] Implement logic to generate plots with X-axis (composition 0-100%) and Y-axis (temperature). **Verification**: Assert plot object has correct axis labels and ranges. (US-3)
- [X] T034 [US3] Implement visual distinction (solid vs. dashed lines) for experimental vs. predicted boundaries. **Verification**: Assert line styles are distinct in saved plot. (US-3)
- [X] T035 [US3] Calculate Topological Consistency Score (TCS): 
 1. **Algorithm**: For each system, select fixed composition slices (e.g., 0.1, 0.2, ... 0.9). At each slice, sort the predicted temperatures and experimental temperatures. 
 2. **Metric**: TCS = (Number of slices where `sorted(predicted) == sorted(experimental)`) / (Total slices).
 3. **Deliverable**: Generate `data/artifacts/tcs_report.json` (schema: `{"system": "Cu-Zn", tcs_score: high, "slices_evaluated": a representative subset}`). **Verification**: Log warning if TCS < 0.8 but DO NOT halt. TCS is an auxiliary metric; primary gate is MAE. (Methodology Section 4, SC-004)
- [X] T036 [US3] Implement MAE check for visual fidelity. 
 1. **Logic**: Calculate MAE between predicted and experimental phase boundary lines.
 2. **Action**: If MAE > 50K, log a warning with error code `LOW_DATA_FIDELITY` to `data/artifacts/fidelity_check.log` (JSON lines: `{"system": "Cu-Zn", mae: moderate magnitude, "status": "PASS"}`). **Requirement**: Do NOT halt the pipeline; this is a qualitative flag per US-3 Acceptance Scenario 3. (US-3, SC-004)
- [X] T037 [US3] Save generated plots to `data/artifacts/plots/` with system ID naming convention. **Verification**: Assert PNG/SVG files exist. (FR-005)
- [X] T038 [US3] Exclude complex/metastable systems (e.g., Fe-C) from visualization. **Verification**: Assert Fe-C is not in the generated plots list. **Constraint**: Visualization must be limited to 'simple binary systems' (e.g., Cu-Zn, Al-Cu). (US-3, Assumptions)

### Tests for User Story 3 (MANDATORY)
*Note: These tasks are listed after implementation to reflect 'Producer before Consumer' artifact flow.*

- [X] T030 [P] [US3] Write `tests/test_viz.py` with function `test_tcs_calculation` verifying partial match ratio formula logic (Mandatory per SC-004 auxiliary check). **Depends on T035 completion.**
- [X] T031 [P] [US3] Write `tests/integration/test_viz.py` with function `test_plot_generation` verifying PNG/SVG output exists (Mandatory per US-3). **Depends on T032, T037 completion.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` (README, API docs)
- [ ] T040 Code cleanup and refactoring (remove debug prints, optimize loops)
- [ ] T041 Performance optimization: ensure data subsampling if memory > 6 GB
- [ ] T042 [P] Additional unit tests for edge cases (ternary systems, empty datasets)
- [ ] T043 Run `quickstart.md` validation script
- [ ] T044 Update `state/PROJ-485/...yaml` with final artifact hashes

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