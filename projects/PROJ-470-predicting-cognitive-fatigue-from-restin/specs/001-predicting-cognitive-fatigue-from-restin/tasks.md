---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Input**: Design documents from `/specs/001-cognitive-fatigue-from-restin/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure: `projects/PROJ-470-predicting-cognitive-fatigue-from-restin/`, `data/raw/`, `data/processed/`, `code/`, `tests/unit/`, `tests/integration/`, `docs/`. **Verification**: Create `tests/unit/test_setup.py` that uses Python's `os.path.exists` to assert the existence of directories `data/raw`, `data/processed`, `code`, `tests/unit`, `tests/integration`, `docs`. Assert the test fails if any are missing.
- [X] T002 Create skeleton files: `code/config.yaml`, `code/download.py`, `code/preprocess.py`, `code/features.py`, `code/analysis.py`, `code/report.py`, `code/models/__init__.py`, `docs/README.md`. **Verification**: Run a Python script `tests/unit/test_skeleton.py` that uses `os.path.exists` to assert that all listed files in `code/` and `docs/` exist. Assert the test fails if any are missing.
- [X] T003 [P] Initialize Python 3.11 virtual environment and create `code/requirements.txt` with pinned dependencies: `mne`, `scikit-learn`, `numpy`, `pandas`, `lempel-ziv-complexity`, `scipy`, `pyyaml`, `pytest`, `nolds`. **Verification**: Run `pip list` in the venv and assert all dependencies are installed with pinned versions.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.yaml` with pipeline parameters. **Verification**: Parse `code/config.yaml` and assert it contains the following keys: `filter_low` (value 1), `filter_high` (value 40), `artifact_threshold` (value 100), `random_seed` (integer), `n_threshold` (value 30), `notch_frequency` (value 50), and `embedding_dim` (value 3).
- [X] T005 [P] Implement logging infrastructure in `code/utils/logging.py` to track participant exclusion and artifact rejection reasons. **Verification**: Create `tests/unit/test_logging.py` that triggers a log entry and asserts `logs/exclusion_log.csv` is created with the correct format.
- [X] T029 [P] Implement integration test for quickstart.md validation to ensure pipeline executes on CPU‑only CI. **Verification**: Create `tests/integration/test_quickstart_e2e.py` that executes the commands in `docs/quickstart.md` and asserts all steps complete successfully without errors. (Note: This task is moved here from Phase 6 to validate documentation early).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Retrieval and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Retrieve clean EEG data from public sources and preprocess to remove artifacts/line noise

**Independent Test**: Run preprocessing on a single sample file; verify 50Hz line noise peak is attenuated by >20dB in output spectrum.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] [US1] Unit test for bandpass filter attenuation in `tests/unit/test_preprocess.py`. **Verification**: Run `pytest tests/unit/test_preprocess.py::test_bandpass_attenuation` and assert it fails initially, then passes after implementation.
- [X] T008 [P] [US1] Integration test for data download and checksum verification in `tests/integration/test_download.py`. **Verification**: Run `pytest tests/integration/test_download.py` and assert it fails initially, then passes after implementation.
- [ ] T027a [P] [US1] Unit test for missing data edge case in `tests/unit/test_preprocess.py::test_missing_data`. **Verification**: Run `pytest tests/unit/test_preprocess.py::test_missing_data` and assert that the preprocessing script raises a clear error when a required EEG file is absent.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `code/download.py` to fetch a public EEG dataset. **CRITICAL**: Before proceeding, the script MUST validate the presence of both resting-state EEG and paired pre/post fatigue ratings per FR-001. The script MUST check for the presence of ANY of the following column name variations for pre/post fatigue ratings: `pre_fatigue`, `fatigue_pre`, `baseline_fatigue`, `post_fatigue`, `fatigue_post`, `end_fatigue`. **Implementation Detail**: The script MUST first inspect the metadata file (or API response) to count participants (`N`) and check for required variables BEFORE downloading full data. The script MUST read the `n_threshold` value from `code/config.yaml` (default). If the dataset lacks the required variables or yields an insufficient sample size, the script MUST halt with a non-zero exit code. and log `validation_report.json` with schema: `{ "status": "fail", "available_variables": [...], "participant_count": 0, "message": "Required variables missing or insufficient power" }`. Log specific error: "ERROR: No valid dataset found with required variables." **Verification**: The script MUST first inspect the metadata file (or API response) to count participants before downloading full data.
- [ ] T010 [US1] Implement `code/preprocess.py` to apply a bandpass filter (1-40 Hz) and remove line noise per FR-002 and Constitution Principle VI. **Justification**: Line noise removal is a mandatory step per Constitution Principle VI and FR-002. **CRITICAL**: The script MUST apply a notch filter to remove line noise. The notch frequency MUST be read from `code/config.yaml` (default value set to an appropriate line frequency). to allow adaptation to 60 Hz datasets. Output preprocessed data to `data/processed/cleaned_eeg.fif`. **Verification**: Create `tests/integration/test_preprocess.py::test_line_noise_attenuation` that computes PSD and asserts the peak at the configured notch frequency is attenuated by >20dB compared to the raw signal. Assert file exists and contains data for ≥30 participants.
- [ ] T011 [US1] Implement artifact rejection logic in `code/preprocess.py` to exclude epochs >±100µV and segments <120 seconds per FR-002 and Edge Cases. Log exclusion counts and reasons to `logs/exclusion_log.csv`. **Verification**: Assert `logs/exclusion_log.csv` exists and contains columns `[participant_id, reason, timestamp]`. Additionally, assert that the `reason` column contains valid rejection reasons (e.g., 'amplitude > 100uV', 'segment < 120s').
- [ ] T026 [P] [US1] Verify streaming data loading in `code/preprocess.py` ensures peak memory usage ≤ 7 GB (per DC‑001 and SC‑003) (targeting DC‑001). **Implementation Detail**: This task is a verification step that runs AFTER T010 implementation. It asserts that `preload=False` is used and generator-based iteration is implemented. **Verification**: Assert peak memory usage stays below 7GB during processing of the full dataset using a memory profiler.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Complexity Feature Extraction (Priority: P2)

**Goal**: Calculate Lempel-Ziv complexity and permutation entropy for resting-state segments, ensuring reproducibility and correct artifact generation.

**Independent Test**: Run complexity calculation on a synthetic signal with known properties; verify output values fall within expected ranges.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T012 [P] [US2] Unit test for LZC calculation on known signal in `tests/unit/test_features.py`.
- [ ] T013 [P] [US2] Unit test for permutation entropy on known signal in `tests/unit/test_features.py`.

### Implementation for User Story 2

- [ ] T014 [US2] Implement `code/features.py` to calculate Lempel‑Ziv complexity per channel per FR-003. Output to `data/processed/lzc_metrics.csv`. **Schema**: `participant_id` (str), `channel` (str), `lzc_value` (float64). **Verification**: Assert `data/processed/lzc_metrics.csv` exists, is non‑empty, and contains the three columns in the specified order. The output MUST contain data for N≥30 participants. Additionally, run the calculation on a synthetic signal (white noise, 256 Hz sampling rate, 120 seconds duration, seed=42, amplitude normalized to unity) and assert the output value is a numeric float within the theoretical range of [0, 1].
- [ ] T015 [US2] Implement `code/features.py` to calculate Permutation Entropy per channel per FR-003. Output to `data/processed/pe_metrics.csv`. **Schema**: `participant_id` (str), `channel` (str), `pe_value` (float64). **Verification**: Assert `data/processed/pe_metrics.csv` exists, is non‑empty, and contains the three columns in the specified order. The output MUST contain data for N≥30 participants. Additionally, run the calculation on a synthetic signal (white noise, 256 Hz sampling rate, 120 seconds duration, embedding dimension = 3, seed=42) and assert the output value is a numeric float within the theoretical range of [0, 1].

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Reporting (Priority: P3)

**Goal**: Correlate complexity metrics with fatigue scores, apply corrections, and generate report

**Independent Test**: Run analysis on mock dataset with known correlation values; verify reported p‑values and coefficients match mock truth.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US3] Unit test for Benjamini‑Hochberg correction implementation in `tests/unit/test_analysis.py`.
- [ ] T017 [P] [US3] Integration test for full analysis pipeline on mock data in `tests/integration/test_analysis.py`.
- [ ] T027b [P] [US3] Unit test for analysis mode failure in `tests/unit/test_analysis.py::test_analysis_mode_failure`. **Verification**: Run `pytest tests/unit/test_analysis.py::test_analysis_mode_failure` and assert that `code/analysis.py` exits with an informative error when neither paired nor baseline data are available.

### Implementation for User Story 3

- [ ] T018 [US3] Implement `code/analysis.py` validation: Check for columns representing paired pre/post fatigue ratings in the metadata dataframe. **CRITICAL**: If paired data exists, proceed to paired analysis. The primary statistical output MUST be Pearson/Spearman correlation between complexity changes (delta) and fatigue delta scores per FR-004. An ANCOVA model (`Post ~ Pre + Fatigue`) may be run as an optional exploratory robustness check, but the primary reported results must be the correlation coefficients. If paired data is missing but baseline fatigue exists, pivot to cross‑sectional analysis (Baseline Complexity vs. Baseline Fatigue). If neither condition is met, write `validation_report.json` with error details and exit with code 1. **Verification**: Create `tests/unit/test_analysis.py::test_correlation_implementation` that verifies the correlation analysis is correctly applied for paired data and that correlation coefficients are reported as the primary output.
- [ ] T019 [US3] Implement `code/analysis.py` for Pearson/Spearman correlation between complexity changes (delta) and fatigue delta scores (paired mode) OR baseline complexity vs baseline fatigue (cross‑sectional mode) per FR-004. **CRITICAL**: The implementation MUST explicitly exclude participants with missing fatigue ratings and log the exclusion count per Edge Cases. **Verification**: Create `tests/unit/test_analysis.py::test_correlation_calculation` that runs on mock data with known correlation values and asserts the output matches.
- [ ] T020 [P] [US3] Implement Benjamini‑Hochberg correction for multiple comparisons across electrodes per FR-005. **Verification**: Create `tests/unit/test_analysis.py::test_bh_correction` that runs the correction on a known set of p-values (e.g., a range of representative values) and asserts the adjusted p-values match the theoretical calculation.
- [ ] T021 [US3] Implement sensitivity analysis at p≤0.05 and p≤0.01 thresholds with result table per FR-006. Output table to `data/analysis/sensitivity_table.csv`. **Schema Requirement**: The CSV MUST contain columns: `threshold` (float), `count_significant` (int). **Verification**: Assert `data/analysis/sensitivity_table.csv` exists and contains the two specified columns with correct counts of significant electrodes at each threshold.
- [ ] T022 [US3] Generate final report with statistical significance, Pearson/Spearman coefficients, p-values, confidence intervals, and the sensitivity analysis table per US‑3 and FR-004. The report must strictly discuss correlation coefficients, p‑values, and confidence intervals. Output to `docs/final_report.md`. **Verification**: Assert `docs/final_report.md` exists and contains sections for "Correlation Analysis", "Statistical Significance", "Confidence Intervals", and "Sensitivity Analysis". Additionally, verify the content includes specific data points (e.g., "r =...", "p =...") and matches the schema validation using a mock data truth table provided in the test (e.g., expected r=0.45, p=0.02 for a specific mock dataset).
- [ ] T023 [US3] Add collinearity diagnostics (VIF < 5) check if metrics are combined per SC‑004. **Verification**: Create `tests/unit/test_analysis.py::test_vif_check` that verifies the VIF calculation and logs a warning if any VIF >= 5. Output the VIF values to `data/analysis/vif_report.csv`. Assert `data/analysis/vif_report.csv` exists and contains the VIF values.
- [ ] T024 [P] [US3] Documentation updates in `docs/` covering pipeline parameters, data sources, and statistical interpretation guidelines. **Verification**: Assert `docs/README.md` contains a section "Pipeline Parameters" with a table of values from `code/config.yaml`. The verification MUST parse `code/config.yaml` and assert that the values in `docs/README.md` match the parsed YAML values exactly.
- [ ] T025 [P] [US3] Performance profiling of `code/preprocess.py` and `code/features.py` to identify memory bottlenecks. **Verification**: Create `tests/unit/test_profile.py` that runs the pipeline and outputs a `profile_report.json` containing peak memory usage and wall time for each step. The JSON MUST contain keys `peak_memory_mb` (float) and `wall_time_s` (float).
- [ ] T028 [P] [US3] Security hardening for data handling (PII scan implementation). **Verification**: Create `tests/unit/test_pii_scan.py` that runs a PII scan on `data/raw` and `data/processed` using Python's `re` module to search for common PII patterns (e.g., email, SSN patterns) and asserts `pii_scan_report.txt` is generated with no findings.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

(No tasks in this phase; T029 moved to Phase 2)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed) or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on cleaned data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on features from US2

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
- **Critical**: All tasks must run on CPU‑only CI (limited cores, constrained RAM, no GPU)
- **Critical**: No synthetic/fake data allowed; must use real datasets from verified sources
- **Critical**: T009 implements the mandatory validation logic for paired pre/post fatigue ratings as defined in FR-001.
- **Critical**: T010 specifies the 1–40 Hz bandpass filter and configurable notch filter as required by FR-002 and Constitution Principle VI.
- **Critical**: T018 implements the conditional fallback logic (correlation for paired, cross‑sectional for single-timepoint) as defined in the plan, using Pearson/Spearman correlation as mandated by FR-004.
- **Critical**: T022, T023, T024, etc. respect the spec‑defined deliverables.
- **Critical**: T021 now explicitly defines the schema for the sensitivity analysis table to meet FR-006 (count of significant electrodes).
- **Critical**: T026 specifies the use of `preload=False` and generator iteration for streaming, with memory target aligned to DC-001 (≤ 7 GB).
- **Critical**: T029 has been moved to Phase 2 to resolve the circular dependency with `quickstart.md`.
- **Critical**: Tasks T030, T031, T032, T033 have been removed to align with FR-003 and eliminate scope creep.
- **Critical**: T006 (ComplexityMetric model class) has been removed to avoid over-engineering.
- **Critical (Revision)**: Task T026 has been moved to Phase 3 to ensure memory constraints are met during preprocessing implementation.
- **Critical (Revision)**: Task T010 now includes a configurable notch filter frequency.
- **Critical (Revision)**: Task T018 now explicitly prioritizes correlation analysis over ANCOVA.
- **Critical (Revision)**: Task T021 now correctly defines the schema for the count of significant electrodes.
- **Critical (Revision)**: Task T006 (ComplexityMetric model class) has been removed to avoid over-engineering.
- **Critical (Revision)**: Task T009 now reads `n_threshold` from `code/config.yaml` to accommodate deferred power analysis.
- **Critical (Revision)**: Task T009 now checks for multiple column name variations for fatigue ratings.
- **Critical (Revision)**: Task T014 and T015 verification steps now use precise synthetic signal parameters and remove unverified numeric thresholds.