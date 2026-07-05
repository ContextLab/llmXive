# Tasks: Predicting Avian Vocal Complexity from Environmental Noise Levels

**Input**: Design documents from `/specs/001-predict-avian-vocal-complexity/`
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
- [X] T002a [P] Create `requirements.txt` with pinned versions: `librosa==0.10.1`, `statsmodels==0.14.0`, `osmnx==1.8.0`, `pandas==2.1.0`, `scikit-learn==1.3.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `requests==2.31.0`, `geopy==2.4.0`, `pytest==7.4.0`
- [X] T002b [P] Setup virtual environment and install dependencies
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `src/utils/config.py` for paths, seeds, and constants <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 6, column 5:
 * **Seeds**: `SEED` and `RANDO...
 ^
expected alphabetic or numeric character, but found ' '
 in "<unicode string>", line 6, column 6:
 * **Seeds**: `SEED` and `RANDOM...
 ^) -->
- [ ] T005 Create `src/utils/logging.py` for error handling and filtered logs
- [ ] T006 Create `contracts/dataset.schema.yaml` defining input/output schemas
- [ ] T007 Create `contracts/output.schema.yaml` defining model result schemas
- [ ] T009 [P] Implement unit tests for config and logging utilities

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve bird vocalization recordings, assign ambient noise levels (OSM primary), and extract standardized vocal complexity metrics.

**Independent Test**: Execute the data pipeline script on a subset of recordings and verify the output CSV contains valid `noise_level_db`, `species_id`, and calculated complexity metrics without errors.

**Plan Deviation Note**: The Plan explicitly states "NO interpolation for missing noise data" and "drop missing" for records without OSM proxies. While Spec FR-009 requests interpolation, the Plan's execution constraint takes precedence for the current runner environment. Tasks below reflect the Plan's "drop missing" strategy.

### Tests for User Story 1

- [ ] T010 [P] [US1] Write contract test for the `noise_mapped.csv` schema definition in `tests/contract/test_dataset_schema.py`
- [~] T011 [P] [US1] Write contract test for the `vocal_metrics.csv` schema definition in `tests/contract/test_dataset_schema.py`
- [~] T012 [P] [US1] Unit test for OSM land-use to noise mapping logic in `tests/unit/test_osm_mapping.py`
- [~] T013 [P] [US1] Unit test for SNR calculation and filtering logic in `tests/unit/test_snr_filter.py`

### Implementation for User Story 1

- [~] T014 [US1] Implement `src/data/acquisition.py` to fetch metadata/audio from Xeno-canto API and save to `data/raw/`
- [~] T015 [US1] **Primary Source**: Implement `src/data/acquisition.py` to query OpenStreetMap via `osmnx` for land-use at coordinates and map to noise levels (Urban=60, Rural=40, Wild=30). **Constraint**: If OSM data is missing, **drop the record** (Plan Summary). Output: `data/interim/noise_mapped.csv`. Log dropped records to `data/interim/dropped_missing_osm.csv`.
- [~] T015c [US1] **Validation**: Implement logic to validate OSM noise proxies against the Global Soundscapes dataset (if available) with ≤2 dB(A) deviation. If Global Soundscapes is unavailable, log the deviation and the justification for using OSM-only data in `data/interim/validation_log.csv` to satisfy FR-002.
- [~] T017a [US1] **Filtering Engine**: Implement the core parameterized filtering logic in `src/data/preprocessing.py` that accepts an SNR threshold argument and returns filtered records and exclusion logs. Output: `data/interim/filtered_snr.csv`.
- [~] T017b [US1] **Default Execution**: Execute the filtering engine from T017a with the default dB threshold to generate the primary `data/interim/filtered_snr.csv`.
- [~] T018 [US1] Implement `src/data/preprocessing.py` to filter species with <5 valid recordings per location and log exclusions.
- [~] T018b [US1] **Audit Trail**: Generate `data/interim/species_filtered.csv` containing all species excluded by T018.
- [~] T021 [US1] **Logging**: Generate `data/interim/dropped_records.csv` containing all records excluded by T015 (missing OSM), T017 (SNR ≤ 10 dB), and T018 (species count) to satisfy US-1 Acceptance Scenario 3.
- [~] T019 [US1] Implement `src/data/extraction.py` to extract vocal metrics (syllable count, duration, bandwidth, spectral entropy) using `librosa` (CPU-only).
- [~] T020 [US1] Implement `src/data/preprocessing.py` to combine filtered data and extracted metrics to generate `data/processed/final_dataset.csv` and validate against `contracts/dataset.schema.yaml`.

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Inference (Priority: P2)

**Goal**: Fit linear mixed-effects models, validate robustness via LOSO cross-validation, and perform sensitivity analysis.

**Independent Test**: Run the modeling script on the preprocessed dataset and verify the output includes model coefficients, p-values, effect sizes, and model fit statistics without crashing.

**Dependency Note**: The sensitivity analysis tasks (T030, T031) rely on the filtering engine implemented in T017a (Phase 3).

### Tests for User Story 2

- [~] T022 [P] [US2] Contract test for `data/processed/model_results.csv` in `tests/contract/test_output_schema.py`
- [~] T023 [P] [US2] Unit test for LOSO cross-validation split logic in `tests/unit/test_loso_cv.py`

### Implementation for User Story 2

- [~] T029b [US2] **Species Count Verification**: Count valid species in `data/processed/final_dataset.csv` and verify count ≥ 50 (SC-004). Block modeling if count < 50.
- [~] T029 [US2] **Power Analysis**: Implement `src/analysis/modeling.py` to run Power Analysis for N=50 species and report minimum detectable effect size (References FR-005). Output: `data/interim/power_analysis_report.md`.
- [~] T024 [US2] Implement `src/analysis/modeling.py` to fit Linear Mixed-Effects model: `complexity ~ noise_level + (1|species) + (1|location)` using `statsmodels`.
- [~] T025 [US2] Implement `src/analysis/modeling.py` to calculate Pearson correlation (r) and confidence interval for noise vs. complexity (SC-001).
- [~] T026 [US2] Implement `src/analysis/modeling.py` to apply FDR correction to p-values for multiple metrics (FR-006, SC-002).
- [~] T027 [US2] Implement `src/analysis/modeling.py` to perform Leave-One-Species-Out (LOSO) cross-validation (US-2, FR-004).
- [~] T028 [US2] Implement `src/analysis/modeling.py` to generate residual diagnostics (Q-Q plot, residual vs. fitted) and save to `data/figures/`.
- [~] T030a [US2] **Sensitivity Execution**: Execute the filtering engine (Ta) with SNR thresholds ranging from low to high values, including 10 and 15 dB.. Generate `data/processed/sensitivity_5db.csv`, `data/processed/sensitivity_10db.csv`, `data/processed/sensitivity_15db.csv`. **MUST Log sample size counts for each threshold to `data/interim/sensitivity_counts.csv`** to satisfy FR-007. **MUST Generate `filtered_records.csv` outputs for each threshold.**
- [~] T030b [US2] **Correlation Calculation**: Compute correlation (r) for each threshold dataset generated in T030a.
- [~] T031 [US2] **Stability Metric**: Calculate variation in effect size/power and sample size across thresholds. Output `data/processed/sensitivity_summary.csv` with columns: `threshold`, `sample_size`, `correlation_r`, `variation_percent`. Verify variation ≤ 10% (SC-005).
- [~] T031b [US2] **False Positive Analysis**: Implement logic to estimate and log false-positive rate variation across the SNR sweep against the 10 dB baseline to satisfy SC-005. Output: `data/processed/false_positive_analysis.json`.

**Checkpoint**: User Story 2 should be fully functional and testable independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-quality visualizations and a summary report.

**Independent Test**: Execute the visualization script and verify the output directory contains at least three distinct image files and a text summary file.

### Tests for User Story 3

- [~] T032 [P] [US3] Unit test for plot generation logic (file existence) in `tests/unit/test_viz_output.py`

### Implementation for User Story 3

- [~] T033 [US3] Implement `src/analysis/viz.py` to generate scatter plot with regression line and confidence interval (US-3, FR-008).
- [~] T034 [US3] Implement `src/analysis/viz.py` to generate regional heatmap mapping noise levels to complexity metrics (US-3, FR-008).
- [~] T035 [US3] Implement `src/analysis/viz.py` to generate residual plots from the LME model (US-3).
- [~] T036 [US3] Implement `src/analysis/report.py` to compile summary report with correlation direction, effect size, and corrected p-value (US-3, FR-009).
- [~] T037 [US3] Implement `src/analysis/report.py` to include power analysis results and sensitivity analysis summary (FR-002, FR-007).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Versioning

**Purpose**: Final validation, hashing, and reporting

- [~] T038 [P] [Polish] Implement `src/main.py` to orchestrate the full pipeline end-to-end
- [~] T039 [Polish] Implement `src/utils/versioning.py` to generate SHA hashes for `data/raw`, `data/interim`, `data/processed`, `data/figures`, `data/processed/sensitivity_*.csv`, `data/processed/sensitivity_summary.csv`, `data/processed/false_positive_analysis.json`, and `data/processed/report.md` (FR-005, SC-006).
- [~] T040 [Polish] Update `state/projects/PROJ-255...yaml` with artifact hashes (FR-005).
- [~] T041 [Polish] Run integration test on a representative recording subset to verify end-to-end flow (US-1).
- [ ] T042 [Polish] Verify data completeness: ensure all retained records have valid OSM noise proxies (SC-006).

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
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
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
Task: "Implement acquisition.py for Xeno-canto and OSM"
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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All audio processing must be CPU-only (no GPU, no deep learning).
- **Plan Compliance**: The Plan's "NO interpolation" constraint is strictly followed. Spec FR-009 (Interpolation) is flagged as a plan deviation for human review.
- **Sensitivity Analysis**: Tasks T030/T031 explicitly mandate logging sample size counts and `filtered_records.csv` outputs for each threshold to satisfy FR-007.