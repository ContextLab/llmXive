# Tasks: Predicting Avian Vocal Complexity from Environmental Noise Levels

**Input**: Design documents from `/specs/001-predicting-avian-vocal-complexity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `src/` directory
- [X] T001b [P] Create `src/data`, `src/analysis`, `src/utils` subdirectories
- [X] T001c [P] Create `data/raw`, `data/interim`, `data/processed`, `data/figures` directories
- [X] T002a [P] Create `requirements.txt` with pinned versions: `librosa==0.10.1`, `statsmodels==0.14.0`, `osmnx==1.8.0`, `geopy==2.4.0`, `pandas==2.1.0`, `scikit-learn==1.3.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `requests==2.31.0`, `datasets==2.14.0`, `pytest==7.4.0`, `pyyaml==6.0.1`. **Plan Kickback**: `osmnx` and `geopy` are required by Spec FR-009 (Interpolation) but missing from Plan.md. **Note**: This task creates the file and pins versions. The implementer must treat 'create file' and 'verify versions' as distinct logical steps if the file state is unknown.
- [X] T002b [P] Verify `requirements.txt` content matches the exact list in T002a and ensure `pip install -r requirements.txt` succeeds without errors. **Deliverable**: `requirements.txt` exists with correct content and `pip list` shows installed packages.
- [X] T002c [P] Setup virtual environment and install dependencies from `requirements.txt`. **Verification**: Run `pip check` to ensure no conflicts.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools. **Deliverable**: Create `.ruff.toml` and `pyproject.toml` with specific config sections for this project. **Verification**: Run `ruff check src/` and `black --check src/` successfully.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **T006 and T007 are blocking prerequisites for T020 and T022.**

- [X] T004 Create `src/utils/config.py` for paths, seeds, and constants. **Deliverable**: File must contain: `SEED = 42`, `RANDOM_SEED = 42`, `PATHS = {'RAW': 'data/raw', 'INTERIM': 'data/interim', 'PROCESSED': 'data/processed', 'FIGURES': 'data/figures'}`, `THRESHOLDS = {'SNR_DEFAULT': 10, 'INTERPOLATION_MAX_KM': 50, 'MISSING_THRESHOLD_PERCENT': 10}`.
- [ ] T005 Create `src/utils/logging.py` for error handling and filtered logs. **Deliverable**: Configure logger with INFO level, JSON format, and handlers for stdout and `data/logs/app.log`. Implement `log_error` and `log_warning` functions.
- [ ] T006 Create `contracts/dataset.schema.yaml` defining input/output schemas. **Deliverable**: YAML file with exact content:
 ```yaml
 type: object
 required:
 - recording_id
 - species_id
 - latitude
 - longitude
 - noise_level_db
 - syllable_count
 - duration_seconds
 - frequency_bandwidth_hz
 - spectral_entropy
 - snr_db
 properties:
 recording_id: { type: string }
 species_id: { type: string }
 latitude: { type: number }
 longitude: { type: number }
 noise_level_db: { type: number }
 syllable_count: { type: integer }
 duration_seconds: { type: number }
 frequency_bandwidth_hz: { type: number }
 spectral_entropy: { type: number }
 snr_db: { type: number }
 ```
- [ ] T007 Create `contracts/output.schema.yaml` defining model result schemas. **Deliverable**: YAML file with exact content:
 ```yaml
 type: object
 required:
 - metric_name
 - fixed_effect_coefficient
 - p_value
 - effect_size
 - random_effect_variance
 - ci_lower
 - ci_upper
 properties:
 metric_name: { type: string }
 fixed_effect_coefficient: { type: number }
 p_value: { type: number }
 effect_size: { type: number }
 random_effect_variance: { type: number }
 ci_lower: { type: number }
 ci_upper: { type: number }
 ```
- [X] T009 [D] Implement unit tests for config and logging utilities in `tests/unit/test_config_logging.py`. **Note**: Development can be parallel with T004/T005, but execution is serial and depends on T004/T005 completion. **Deliverable**: `tests/unit/test_config_logging.py` with passing tests.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve bird vocalization recordings, assign ambient noise levels (Global Soundscapes primary + Interpolation fallback), and extract standardized vocal complexity metrics.

**Independent Test**: Execute the data pipeline script on a subset of recordings and verify the output CSV contains valid `noise_level_db`, `species_id`, and calculated complexity metrics without errors.

**Plan Compliance Note**: The Spec (FR-009) mandates interpolation for missing noise data. The Plan's previous "NO interpolation" stance is overridden. Tasks below implement the interpolation fallback (FR-009) and only drop records if interpolation fails.

### Tests for User Story 1

- [X] T010 [P] [US1] Write contract test for the `noise_mapped.csv` schema definition in `tests/contract/test_dataset_schema.py`
- [X] T011 [P] [US1] Write contract test for the `vocal_metrics.csv` schema definition in `tests/contract/test_dataset_schema.py`
- [X] T012 [P] [US1] Unit test for OSM land-use to noise mapping logic in `tests/unit/test_osm_mapping.py`
- [X] T013 [P] [US1] Unit test for SNR calculation and filtering logic in `tests/unit/test_snr_filter.py`

### Implementation for User Story 1

- [ ] T015d [US1] **Interpolation Fallback**: Implement `src/data/acquisition.py` function to perform nearest-neighbor search (using `geopy`) for missing Global Soundscapes coordinates within 50km. Interpolate noise levels from nearest valid neighbors. Output: `data/interim/interpolated_records.csv` with source coordinates and interpolated values. **Note**: This logic must be implemented first to support T015.
- [ ] T015 [US1] **Primary Source**: Implement `src/data/acquisition.py` to fetch noise levels from the **Global Soundscapes dataset** using `datasets.load_dataset('noise-map/global-soundscapes')`. **Fallback**: If the package fails, fetch from ` (verified mirror). **Constraint**: If BOTH fail, raise an error and FAIL LOUDLY. If a specific coordinate is missing, **read `data/interim/interpolated_records.csv` (from T015d)** and merge into the primary dataset. **Deliverable**: `data/interim/noise_mapped.csv` containing all successfully mapped records (primary + interpolated). **Prerequisites**: T015d (artifact dependency). <!-- FAILED: unspecified -->
- [ ] T015c [US1] **Validation**: Implement logic to validate the **combined** `noise_mapped.csv` against the Global Soundscapes dataset. **Constraint**: For records with primary source values, check deviation ≤2 dB(A). For records with interpolated values, **skip deviation check** and log status as 'INTERPOLATED'. **Deliverable**: Generate `data/interim/validation_log.csv` for ALL records, logging status as `PASS` (if deviation ≤2 dB(A)), `WARN` (if deviation >2 dB(A)), or `INTERPOLATED` (if no primary value). **Prerequisites**: Must run after T015 and T015d are complete.
- [ ] T015e [US1] **Interpolation Validation**: Verify that all missing noise values within 50km are successfully interpolated and logged. If >10% of records fail interpolation, log a warning but **DO NOT HALT** the pipeline. Satisfies SC-006.
- [X] T017a [US1] **Filtering Engine**: Implement the core parameterized filtering logic in `src/data/preprocessing.py` that accepts an SNR threshold argument and returns filtered records and exclusion logs. Output: `data/interim/filtered_snr.csv`. **Prerequisites**: T015 (artifact dependency). **Note**: This task depends on the merged dataset from T015.
- [X] T017b [US1] **Default Execution**: Execute the filtering engine from T017a with the default dB threshold to generate the primary `data/interim/filtered_snr.csv`.
- [ ] T018 [US1] Implement `src/data/preprocessing.py` to filter species with <5 valid recordings per location and log exclusions.
- [ ] T018b [US1] **Audit Trail**: Generate `data/interim/species_filtered.csv` containing all species excluded by T018. **Input**: `data/interim/filtered_snr.csv`. **Schema**: Columns `species_id` (string), `reason_for_exclusion` (string, e.g., "count < 5"), `count` (integer: count of valid recordings for this species at this location).
- [ ] T021a [US1] **SNR Filtering Log**: Generate `data/interim/filtered_records.csv` containing ONLY records excluded by SNR ≤ 10 dB (T017). **Input**: `data/interim/filtered_snr.csv`. **Schema**: Columns `recording_id` (string), `snr_db` (float), `threshold_applied` (float). Satisfies US-1 Acceptance Scenario 3.
- [ ] T021b [US1] **General Drop Log**: Generate `data/interim/dropped_records.csv` containing records excluded by T015 (missing Global Soundscapes + failed interpolation) and T015e (interpolation failure). **Constraint**: This file must EXCLUDE records filtered by T018 (species count). Filter out any records present in `species_filtered.csv` before writing. **Schema**: Columns `recording_id` (string), `drop_reason` (string, e.g., "missing_global_soundscapes", "interpolation_failed").
- [ ] T019 [US1] Implement `src/data/extraction.py` to extract vocal metrics (syllable count, duration, bandwidth, spectral entropy) using `librosa` (CPU-only).
- [ ] T020 [US1] Implement `src/data/preprocessing.py` to combine filtered data and extracted metrics to generate `data/processed/final_dataset.csv` and validate against `contracts/dataset.schema.yaml` (T006).

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Inference (Priority: P2)

**Goal**: Fit linear mixed-effects models, validate robustness via LOSO cross-validation, and perform sensitivity analysis.

**Independent Test**: Run the modeling script on the preprocessed dataset and verify the output includes model coefficients, p-values, effect sizes, and model fit statistics without crashing.

**Dependency Note**: The sensitivity analysis tasks (T030, T031) rely on the filtering engine implemented in T017a (Phase 3) and run on `data/interim/noise_mapped.csv` to avoid circular dependencies with T020.

### Tests for User Story 2

- [ ] T022 [P] [US2] Contract test for `data/processed/model_results.csv` in `tests/contract/test_output_schema.py`
- [ ] T023 [P] [US2] Unit test for LOSO cross-validation split logic in `tests/unit/test_loso_cv.py`

### Implementation for User Story 2

- [ ] T029b [US2] **Species Count Verification**: Count valid species in `data/processed/final_dataset.csv` and verify count ≥ 50 (SC-004). **Action**: If count < 50, **exit with code 1** and write `data/interim/species_count_block.txt` with the count and reason. **Output**: Log count to `data/interim/species_count_check.txt` with format: "Species Count: <N>". **Plan Compliance Note**: This is a hard pipeline gate per SC-004, which may contradict the 'research' nature of the Plan. Plan.md must be updated to reflect this hard constraint. **Prerequisites**: T020.
- [ ] T029 [US2] **Power Analysis**: Implement `src/analysis/modeling.py` to run Power Analysis for N=50 species and report minimum detectable effect size (References FR-005). **Input**: `data/interim/species_count_check.txt`. **Output**: `data/interim/power_analysis_report.md`. **Verification**: Ensure report contains N=50 and effect_size > 0.2.
- [ ] T024 [US2] Implement `src/analysis/modeling.py` to fit Linear Mixed-Effects model: `complexity ~ noise_level + (1|species) + (1|location)` using `statsmodels`. **Prerequisites**: T029b must pass.
- [ ] T025 [US2] Implement `src/analysis/modeling.py` to calculate Pearson correlation (r) and confidence interval for noise vs. complexity (SC-001).
- [ ] T026 [US2] Implement `src/analysis/modeling.py` to apply FDR correction to p-values for multiple metrics (FR-006, SC-002).
- [ ] T027 [US2] Implement `src/analysis/modeling.py` to perform Leave-One-Species-Out (LOSO) cross-validation (US-2, FR-004).
- [ ] T028 [US2] Implement `src/analysis/modeling.py` to generate residual diagnostics (Q-Q plot, residual vs. fitted) and save to `data/figures/`.
- [ ] T030a [US2] **Sensitivity Execution**: Execute the filtering engine (implementation from T017a) on `data/interim/noise_mapped.csv` with SNR thresholds (low, medium, high). **Iterate** through thresholds to generate distinct files `data/processed/sensitivity_5db.csv`, `data/processed/sensitivity_10db.csv`, `data/processed/sensitivity_15db.csv`. **MUST Log sample size counts for each threshold to `data/interim/sensitivity_counts.csv`** to satisfy FR-007. **MUST Generate distinct `filtered_records_<threshold>.csv` files** for each threshold with schema: `recording_id` (string), `threshold_applied` (float), `snr_db` (float), `reason` (string). **Prerequisites**: T017a (implementation dependency).
- [ ] T030b [US2] **Correlation Calculation**: Compute correlation (r) for each threshold dataset generated in T030a.
- [ ] T031 [US2] **Stability Metric & FPR**: Calculate variation in **correlation estimates (r-values)** and **sample size** across thresholds. **MUST ALSO estimate False Positive Rate (FPR) for EACH threshold** using a **Null-Data Simulation** (shuffle noise variable relative to vocal metric, 1000 permutations, seed=42) to satisfy SC-005. Output `data/processed/sensitivity_summary.csv` with columns: `threshold`, `sample_size`, `correlation_r`, `sample_size_variation_percent`, `correlation_variation_percent`, `fpr`, `fpr_variation_percent`. Verify variation ≤ 15% (FR-007) and FPR variation ≤ 10% (SC-005).
- [ ] T031c [US2] **Variation Verification**: Explicitly verify that the variation in correlation estimates (r-values) and FPR across thresholds is ≤ 15% and ≤ 10% respectively. If not, flag in report.

**Checkpoint**: User Story 2 should be fully functional and testable independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-quality visualizations and a summary report.

**Independent Test**: Execute the visualization script and verify the output directory contains at least three distinct image files and a text summary file.

### Tests for User Story 3

- [ ] T032 [P] [US3] Unit test for plot generation logic (file existence) in `tests/unit/test_viz_output.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `src/analysis/viz.py` to generate scatter plot with regression line and confidence interval (US-3, FR-008).
- [ ] T034 [US3] Implement `src/analysis/viz.py` to generate regional heatmap mapping noise levels to complexity metrics (US-3, FR-008).
- [ ] T035 [US3] Implement `src/analysis/viz.py` to generate residual plots from the LME model (US-3).
- [X] T036 [US3] Implement `src/analysis/report.py` to compile summary report with correlation direction, effect size, and corrected p-value (US-3, FR-009).
- [X] T037 [US3] Implement `src/analysis/report.py` to include power analysis results and sensitivity analysis summary (FR-002, FR-007).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Versioning

**Purpose**: Final validation, hashing, and reporting

- [ ] T038 [P] [Polish] Implement `src/main.py` to orchestrate the full pipeline end-to-end
- [ ] T039 [Polish] Implement `src/utils/versioning.py` to generate SHA-256 hashes for `data/raw`, `data/interim`, `data/processed`, `data/figures`, `data/processed/sensitivity_*.csv`, `data/processed/sensitivity_summary.csv`, `data/processed/false_positive_analysis.json`, and `data/processed/report.md` (FR-005, SC-006). **Deliverable**: `data/processed/artifact_hashes.json` with keys as file paths and values as SHA-256 hashes.
- [ ] T040 [Polish] Update `state/projects/PROJ-255...yaml` with artifact hashes (FR-005).
- [ ] T041 [Polish] Run integration test on a representative recording subset to verify end-to-end flow (US-1).
- [ ] T042 [Polish] **Data Completeness Verification**: Verify that all retained records have valid Global Soundscapes noise proxies OR valid interpolated values. Confirm SC-006: all missing noise values within 50km are EITHER successfully interpolated AND logged in `interpolated_records.csv`, OR dropped and logged in `dropped_records.csv`. If >10% of missing values are dropped without interpolation, flag error.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T006 and T007 are blocking prerequisites for T020 and T022**. Do not start T020/T022 until T006/T007 are complete.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Acquisition/Preprocessing before Extraction
- Modeling before Visualization
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Write contract test for noise_mapped.csv schema"
Task: "Write contract test for vocal_metrics.csv schema"
Task: "Unit test for OSM land-use mapping"
Task: "Unit test for SNR filtering"

# Launch all models for User Story 1 together:
Task: "Implement acquisition.py for Xeno-canto and Global Soundscapes"
Task: "Implement preprocessing.py for filtering and extraction"
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Viz/Report)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [D] tasks = develop-parallel, execute-serial (e.g., T009)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All audio processing must be CPU-only (no GPU, no deep learning).
- **Plan Compliance**: The Spec's FR-009 (Interpolation) is now implemented via T015d/T015e. The Plan's "NO interpolation" stance is overridden by the Spec requirement. **Note**: The Plan document itself still contains contradictory text regarding "NO interpolation" and requires a separate update to align with the Spec and these tasks.
- **Sensitivity Analysis**: Tasks T030/T031 explicitly mandate logging sample size counts and distinct `filtered_records_<threshold>.csv` outputs for each threshold to satisfy FR-007. T031 also includes FPR estimation via Null-Data Simulation to satisfy SC-005.
- **Schema Definitions**: T006 and T007 now include full YAML schema content to ensure executability.
- **Interpolation Logic**: T015d implements nearest-neighbor search; T015e validates success. T042 confirms all missing values are either interpolated or dropped.
- **Primary Source Enforcement**: T015 and T015c enforce Global Soundscapes as the primary source, failing loudly if unavailable.
- **Dependencies**: `osmnx` and `geopy` are now explicitly listed in requirements.txt (T002a). This is flagged for kickback to align tasks and plan.
- **Hard Gate**: T029b enforces a hard pipeline gate (exit 1) if species count < 50, per SC-004.