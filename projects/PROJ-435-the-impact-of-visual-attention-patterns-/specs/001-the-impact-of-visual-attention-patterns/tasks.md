# Tasks: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

**Input**: Design documents from `/specs/001-impact-of-visual-attention-patterns/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project structure per implementation plan: `code/`, `data/raw/`, `data/derived/`, `data/processed/`, `tests/`, `state/` (Reference: `scripts/init_project.py` template)
- [X] T002 Initialize Python 3.11 project with requirements.txt dependencies (pandas, numpy, scikit-learn, statsmodels, nltk, scipy)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Real Data Ingestion to ensure downstream tasks have valid inputs.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008a [P] Create logging configuration file `code/config/logging_config.yaml` **with a concrete schema**:
 ```yaml
 level: INFO # string, e.g., "INFO", "DEBUG" - Default to INFO to capture audit trails
 format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
 handlers:
 - console
 - file
 ```
 This file satisfies the required keys (`level`, `format`, `handlers`) for downstream logger initialization.

- [X] T008b [P] Implement `code/utils/logging_init.py` to load `code/config/logging_config.yaml` (produced by T008a) and initialise the global logger. Validates that the loaded config contains the required keys; raises `ConfigError` if any are missing. Must be executed before any task that writes to `output/` or `state/`. **Dependency**: T008a (Config must exist before Load).

- [X] T005 [P] **Create Configuration & Fetch Data**: Create `code/config.yaml` with `random_seed:` and `dataset_id` (taken from `research.md` "Verified datasets" block). Implement `code/utils/data_loading.py` to fetch the eye‑tracking dataset using `datasets.load_dataset(dataset_id, split=...)` with explicit versioning (e.g., `revision="v1.0"`), compute its SHA‑256 checksum, and write it to `state/data_hashes.json`. **Output**: `data/raw/eye_tracking_raw.parquet`. **Constraint**: Must verify the dataset ID matches `config.dataset_id` before writing. Log the resolved dataset ID to `state/runtime_events.json`. **Dependency**: T008b.

- [X] T004 [FR-001] [FR-002] **Construct Validity Gate**: Implement `code/utils/validate_dataset_schema.py` to verify the raw dataset contains required columns (`headline_text`, `belief_rating`, `cognitive_reflection_score`, `fixation_duration`) **and** pre‑defined ROI bounding boxes (`source_attribution`, `headline_body`). Reads ROI definitions from `code/config.yaml`. Halts with `DataInvalidError` if missing. **Input**: `data/raw/eye_tracking_raw.parquet` (produced by T005). **Output**: `state/schema_validation.json` (`status: "valid"` or `"invalid"`). **Dependency**: Runs after T005 (T004 is NOT parallel-safe with T005).

- [X] T004b [FR-004] [SC-002] **Extract Empirical Outcome**: Load `data/raw/eye_tracking_raw.parquet` (from T005). **Strict Schema Enforcement**:
 1. Attempt to locate a column named exactly `belief_rating`.
 2. If missing, raise `DataInvalidError` immediately with message: "Numeric 'belief_rating' column not found. The Spec requires a numeric self-reported belief rating. Categorical mapping is not authorized by the Spec."
 3. If the column is categorical (e.g., 'High', 'Low', 'True', 'False'), raise `DataInvalidError` immediately.
 4. If the column is missing entirely, raise `DataInvalidError` immediately.
 **Output**: `data/derived/empirical_outcomes.csv` containing `participant_id`, `headline_id`, `belief_rating`, `headline_text`. **Dependency**: T005, T008b. **Constraint**: If `data/raw/eye_tracking_raw.parquet` is missing, raise `FileNotFoundError` immediately; do not attempt to proceed.

- [X] T006 [P] **Implement I-VT Fixation Detection**: Implement `code/utils/fixation_detection.py` containing I‑VT (duration‑threshold) logic as the **default** algorithm. Reads parameters `ivt_duration_threshold` (default configurable) or `idt_dispersion_threshold` from `code/config.yaml`. If I-DT is configured, it must be explicitly enabled; otherwise, I-VT is used. **Constraint**: Must enforce a minimum duration threshold for I-VT to distinguish fixations from saccades (Holmqvist et al., 2011). as per FR-001.

- [X] T007 Implement data models:
 - `code/models/participant.py` (`id`, `crt_score`, `random_intercept`)
 - `code/models/stimulus.py` (`id`, `headline_text`, `valence`, `random_intercept`)
 - `code/models/gaze_event.py` (`timestamp`, `duration`, `roi`, `participant_id`)

- [X] T015 [P] **ROI Mapping Logic**: Implement `code/utils/roi_mapping.py` using point‑in‑polygon to assign each gaze point to a ROI. Input: raw gaze coordinates + ROI polygons from dataset. Output: `roi_type` column added to gaze records. Used by T018.

- [X] T018 **Core Preprocessing (US1)**: Implement `code/02_preprocess_gaze.py` to ingest raw data, apply fixation detection (T006), filter participants with ≥ 20% data loss, map gaze points to ROIs (`source_attribution`, `headline_body`) using `code/utils/roi_mapping.py` (produced by T015), and handle edge cases (missing ROI → trial exclusion, zero fixations → duration 0). **Parameterization**: Must accept a CLI argument `--threshold` (default) to allow dynamic threshold sweeping for robustness analysis. Writes `data/derived/preprocessed_gaze.csv` and `output/exclusion_log.txt`. **Dependency**: Requires T005 (raw data), T006 (fixation logic), T015 (ROI mapping), T008b.

- [X] T040 **Data Quality Report (US1)**: Implement `code/02_data_quality_report.py` to read `output/exclusion_log.txt` (produced by T018) and `data/derived/preprocessed_gaze.csv`, compute the number of excluded participants, reasons, and total participants count (derived from the checksum log generated by T005). Generates `output/data_quality_report.csv` satisfying SC‑001. **Output Schema**: `participant_id` (int), `data_loss_pct` (float), `excluded_flag` (bool). **Calculation**: `excluded_flag` = `True` if `data_loss_pct` > 20. **Dependency**: Runs after T018 and after `state/data_hashes.json` exists.

- [X] T021 **Valence Calculation** (no `[P]`): Using `data/derived/empirical_outcomes.csv` (from T004b), compute NRC lexical coverage. If average coverage < 50%, **switch to VADER for all headlines** *and* add a new column `lexicon_used` (`"NRC"` or `"VADER"`) to the output. Log the switch event to `state/runtime_events.json` with fields `event`, `from`, `to`, `coverage`. **Compliance Note**: This switch is a compliant feature per FR-003, not a defect; log as "Automatic Lexicon Fallback". Output `data/derived/valence_scores.csv` (schema identical regardless of lexicon). **Dependency**: Must run after T004b.

- [X] T010 [P] [US1] Contract test for data ingestion output schema in `tests/contract/test_ingestion_schema.py`

- [X] T011 [P] [US1] Integration test for I‑VT algorithm on sample noisy data in `tests/integration/test_ivt_preprocessing.py`

---

## Phase 3: User Story 1 - Core Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eye‑tracking data, apply I‑VT fixation detection, filter low‑quality participants, and map gaze to ROIs.

**Independent Test**: Run the preprocessing script on the sample dataset and verify that only participants with < 20% data loss remain and that fixation events are correctly timestamped and ROI‑mapped.

- Tasks T015, T018, T040 (described above) constitute the implementation.

---

## Phase 4: User Story 2 - Mixed‑Effects Regression Analysis (Priority: P2)

**Goal**: Execute a mixed-effects regression testing the three-way interaction between source fixation duration, headline valence, and cognitive reflection scores.

- [X] T020a **Synthetic Data Generator**: Implement `code/utils/synthetic_data_generator.py` to generate a synthetic dataset for coefficient recovery testing. **Parameters**: Generate `n` participants and `m` headlines. True three-way interaction coefficient = 0.5. [UNRESOLVED-CLAIM: c_af46442d — status=not_enough_info] Random intercepts ~ N(μ, σ²). Noise sigma = 1.0. [UNRESOLVED-CLAIM: c_7b50d654 — status=not_enough_info] Outcome = linear combination of predictors + interaction + noise. **Output**: `data/synthetic/ground_truth.csv` containing all columns and the known true coefficients for validation. **Dependency**: None (can run in parallel).

- [X] T023 **Data Merge & Outlier Capping**: Merge `data/derived/preprocessed_gaze.csv` (T018), `data/derived/empirical_outcomes.csv` (T004b), and `data/derived/valence_scores.csv` (T021) on `participant_id` and `headline_id`.
 1. Validate schemas; raise `DataMissingError` if required columns are absent.
 2. Cap `cognitive_reflection_score` at extreme percentiles (1st and 99th) **globally across the entire dataset** to handle outliers as per Spec Edge Cases.
 3. Preserve the `lexicon_used` flag from T021 as a covariate.
 4. Compute `headline_length` (word count) and `total_fixation_duration` (sum of fixation durations) as controls.
 Output: `data/derived/merged_dataset_full.csv`. **Dependency**: After T018, T004b, T021.

- [X] T024 [FR-007] [SC-004] **Mixed‑Effects Regression & Correction**: Using `statsmodels`, fit
 `belief_rating ~ fixation_duration * valence * crt + headline_length + total_fixation_duration + (1|participant_id) + (1|headline_id)` on `data/derived/merged_dataset_full.csv`.
 Steps:
 1. Load merged data, ensure outlier‑capped CRT and `lexicon_used` are present.
 2. Fit the model with random intercepts for participants and headlines.
 3. Apply **Holm‑Bonferroni correction** to **ALL** fixed effects tested in the model (including primary effects: `fixation_duration`, `valence`, `crt`, and their interactions; AND control variables: `headline_length`, `total_fixation_duration`) to strictly satisfy FR-007's requirement to control family-wise error rate for all tested hypotheses.
 4. Output `data/derived/regression_results.csv` containing coefficients, raw p‑values, corrected p‑values (`p_adj`), confidence intervals, and interaction terms.
 **Dependency**: After T023.

- [X] T017 **Measure Runtime**: Implement `code/06_measure_runtime.py` to record wall‑clock time of the entire pipeline, compare to the time limit, and write `state/runtime_metrics.json` (`total_runtime_minutes`, `limit_minutes`, `status`). **Dependency**: Runs after T024.

- [X] T019 [P] [US2] Contract test for regression output schema in `tests/contract/test_regression_schema.py`

- [X] T020 [P] [US2] Integration test for coefficient recovery on synthetic data in `tests/integration/test_mixed_effects_recovery.py`:
 1. Load `data/synthetic/ground_truth.csv` (produced by T020a).
 2. Run the regression model (T024 logic) on this synthetic data.
 3. Verify that the estimated coefficient for the three-way interaction matches the known theoretical value within a reasonable margin of error.
 4. Verify that the model correctly identifies random intercepts for participants and headlines.
 **Dependency**: Requires T020a, T024 (or T032 logic).

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Verify that findings are robust to methodological variations (fixation thresholds, headline length controls, etc.).

- [X] T032 [P] **Robustness Runner**: Refactor regression logic from T024 into a reusable function/class that accepts a `fixation_duration_threshold` argument. Exposes the same modeling pipeline (including Holm-Bonferroni on ALL fixed effects) and returns regression statistics.

- [X] T034 **Headline Length Control Verification**: Implement `code/05_regression_analysis.py` (now encapsulated in T032) to verify that `headline_length` is included as a control variable. Output `output/verification_log.txt` confirming the model specification includes `headline_length`. **Dependency**: After T023, T024.

- [X] T033 [FR-005] [SC-003] **Robustness Sweep**: Execute a sweep over a range of thresholds as required by FR-005. For each threshold:
 1. Reset the random seed to `config.random_seed` **before** any data shuffling or model fitting to ensure determinism.
 2. Load **raw gaze data** (from T005) and apply I-VT fixation detection with the specific threshold `X` (bypassing the full T018 pipeline).
 3. Map gaze points to ROIs (using T015 logic) and **re-apply participant filtering (T018 logic) dynamically for this specific threshold** to ensure the participant pool is consistent relative to the new threshold.
 4. Merge with valence and outcomes (T023 logic) and run the regression via the robustness runner (T032).
 5. Compute `mean_belief_rating`, `std_dev_belief`, and `range_belief` for the current threshold and **report the resulting variation in the mean belief rating** across thresholds.
 6. Append results to `data/derived/robustness_report.csv`.
 **Dependency**: Requires T005 (raw data), T006 (fixation logic), T015 (ROI mapping), T021, T023 (schema), and T032. Note: T033 processes raw data per iteration, avoiding full pipeline re-execution.

- [X] T039 **Stability Check**: Read `data/derived/robustness_report.csv` and verify that the sign and significance of the three‑way interaction term remain consistent across thresholds. Output `output/stability_check.json` with fields `consistent_direction`, `consistent_significance`, `ci_overlap_summary`.

- [X] T029 [P] [US3] Contract test for robustness report schema in `tests/contract/test_robustness_schema.py`

- [X] T030 [P] [US3] Integration test for threshold sweep stability in `tests/integration/test_sensitivity_analysis.py`

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Final refinements affecting multiple stories.

- [X] T045 [P] **Documentation Updates**: Update `docs/README.md` to reflect the final pipeline steps, and update `paper/abstract.md` with the final study scope (fixed effects: source fixation, valence, cognitive reflection). The update to `paper/abstract.md` must be driven by the content of `output/causal_framing_statement.txt` (produced by T028). **Output**: Updated `docs/README.md` and `paper/abstract.md`. **Dependency**: T024, T039.

- [X] T046 **Code Cleanup and Refactoring**: Refactor `code/utils/fixation_detection.py` and `code/utils/roi_mapping.py` to reduce cyclomatic complexity to < 10. Run `ruff --max-complexity=10` to verify. **Output**: Refactored files and `output/refactoring_report.txt` confirming complexity metrics. **Dependency**: T018, T015.

- [ ] T047 **Performance Optimization**: Vectorize data merge in T023 and cache intermediate results in T018. Verify runtime < 300 minutes and memory < 7 GB on the reference dataset. [UNRESOLVED-CLAIM: c_6e895ce9 — status=not_enough_info] **Output**: Optimized scripts and `output/performance_metrics.json`. **Dependency**: T023, T018.

- [X] T048 [P] **Additional Unit Tests**: Implement unit tests for `code/utils/fixation_detection.py` (edge cases: a defined time threshold, 0ms duration) and `code/utils/valence_calculation.py` (lexicon switch logic). **Output**: `tests/unit/test_fixation_detection.py` and `tests/unit/test_valence_calculation.py`. **Dependency**: T006, T021.

- [ ] T049 Run `quickstart.md` validation
- [ ] T050 Verify all artifacts are checksummed in `state/`
- [X] T028 [P] **Final Report Generation**: Implement `code/07_generate_causal_framing.py` to produce `output/causal_framing_statement.txt`. Reads `data/derived/regression_results.csv` (output of T024), extracts the three‑way interaction coefficients and their (corrected) p‑values, and dynamically composes a causal framing statement respecting FR‑006. **Dependency**: T024.

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Stories (Phases 3‑5)** → **Polish (Phase N)**
- All tasks in Phase 2 must succeed before any user‑story tasks start.
- **New Dependency**: Logging (T008b) must complete before T005, T004b, T018, and all other Phase 2 tasks.
- **New Dependency**: T008b depends on T008a.
- **New Dependency**: Phase N (T045, T028) depends on T024 (regression), T039 (robustness).
- **New Dependency**: T033 (Robustness Sweep) depends on T005 (raw data), T006 (fixation logic), T015 (ROI mapping), T021, T023 (schema), and T032.

### Within User Stories
- **US1**: T005 → T004b → T015 → T018 → T040 (plus contract tests T010/T011)
- **US2**: T020a → T023 → T024 → T017 (plus contract tests T019/T020)
- **US3**: T032 → T033 → T039 (plus contract tests T029/T030)

### Parallel Opportunities
- All `[P]`‑tagged tasks within a phase may run concurrently once their hard dependencies are satisfied.
- Logging setup (T008a/T008b) must complete before any task that writes logs.
- T032, T034, T048, T055, T056 are parallel-safe once their respective upstream dependencies are complete.

---

## Notes
- All random seeds are pinned in `code/config.yaml` (seed = 42) and reset before each robustness iteration.
- Every artifact written is recorded in `state/` with a SHA‑256 hash for data‑hygiene compliance.
- The `lexicon_used` flag ensures that the VADER fallback does not introduce an uncontrolled confound; it is treated as a covariate in the regression.
- No synthetic belief data or WYSIATI metrics are introduced; the outcome remains strictly empirical (`belief_rating`) per FR‑004 and Constitution Principle VI.
- **Revision Note**: Phase 5.5 (WYSIATI & Confidence Metrics) has been **removed** as it represents scope creep and violates the Spec and Constitution Principle VI.
- **Revision Note**: Task T004b now strictly enforces numeric `belief_rating` and fails loudly if missing, removing unverified mapping logic.
- **Revision Note**: Task T024 now applies Holm-Bonferroni correction to ALL fixed effects (primary + controls) to satisfy FR-007.
- **Revision Note**: Task T033 now explicitly re-applies participant filtering for each threshold iteration to ensure sample consistency.
- **Revision Note**: Task T023 now specifies global capping for outliers.
- **Revision Note**: Phase N tasks (T045-T050) are marked as incomplete pending implementation.