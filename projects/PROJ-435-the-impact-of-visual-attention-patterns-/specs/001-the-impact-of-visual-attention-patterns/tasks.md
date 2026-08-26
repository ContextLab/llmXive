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

- [X] T004 [P] **Construct Validity Gate**: Implement `code/utils/validate_dataset_schema.py` to verify the raw dataset contains required columns (`headline_text`, `belief_rating`, `cognitive_reflection_score`, `fixation_duration`) **and** pre‑defined ROI bounding boxes (`source_attribution`, `headline_body`). Reads ROI definitions from `code/config.yaml`. Halts with `DataInvalidError` if missing. **Input**: `data/raw/eye_tracking_raw.parquet` (produced by T005). **Output**: `state/schema_validation.json` (`status: "valid"` or `"invalid"`). **Dependency**: Runs after T005 download but before any preprocessing.

- [X] T005 [P] **Create Configuration & Fetch Data**: Create `code/config.yaml` with `random_seed:` and `dataset_url` (taken from `research.md` “Verified datasets” block). Implement `code/utils/data_loading.py` to fetch the eye‑tracking dataset from this URL, compute its SHA‑256 checksum, and write it to `state/data_hashes.json`. **Output**: `data/raw/eye_tracking_raw.parquet`. **Constraint**: Must verify the download URL matches `config.dataset_url` before writing.

- [X] T006 [P] Implement `code/utils/fixation_detection.py` containing I‑VT (duration‑threshold) **or** I‑DT (dispersion‑threshold) logic. Reads parameters `ivt_duration_threshold` or `idt_dispersion_threshold` from `code/config.yaml`; defaults to I‑VT 100 ms if none provided.

- [X] T007 Implement data models:
 - `code/models/participant.py` (`id`, `crt_score`, `random_intercept`)
 - `code/models/stimulus.py` (`id`, `headline_text`, `valence`, `random_intercept`)
 - `code/models/gaze_event.py` (`timestamp`, `duration`, `roi`, `participant_id`)

- [X] T008a [P] Create logging configuration file `code/config/logging_config.yaml` **with a concrete schema**:
 ```yaml
 level: INFO # string, e.g., "INFO", "DEBUG"
 format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
 handlers:
 - console
 - file
 ```
 This file satisfies the required keys (`level`, `format`, `handlers`) for downstream logger initialization.

- [X] T008b [P] Implement `code/utils/logging_init.py` to load `code/config/logging_config.yaml` (produced by T008a) and initialise the global logger. Validates that the loaded config contains the required keys; raises `ConfigError` if any are missing. Must be executed before any task that writes to `output/` or `state/`.

- [ ] T004b **Extract Empirical Outcome**: Load `data/raw/eye_tracking_raw.parquet` (from T005) and extract `belief_rating` and `headline_text`. Accept common aliases (`belief`, `rating`, `self_reported_belief`) with a **warning** if the exact column name is absent. Writes `data/derived/empirical_outcomes.csv` containing `participant_id`, `headline_id`, `belief_rating`, `headline_text`. **Dependency**: Must run after T005. **Tag**: not parallel‑safe (`[P]` removed). <!-- FAILED: unspecified -->

- [ ] T021 **Valence Calculation** (no `[P]`): Using `data/derived/empirical_outcomes.csv` (from T004b), compute NRC lexical coverage. If average coverage < 50 %, **switch to VADER for all headlines** *and* add a new column `lexicon_used` (`"NRC"` or `"VADER"`) to the output. Log the switch event to `state/runtime_events.json` with fields `event`, `from`, `to`, `coverage`. Also record a warning about the systematic confound. Output `data/derived/valence_scores.csv` (schema identical regardless of lexicon). **Dependency**: Must run after T004b.

- [ ] T018 **Core Preprocessing (US1)**: Implement `code/02_preprocess_gaze.py` to ingest raw data, apply fixation detection (T006), filter participants with ≥ 20 % data loss, map gaze points to ROIs (`source_attribution`, `headline_body`) using `code/utils/roi_mapping.py`, and handle edge cases (missing ROI → trial exclusion, zero fixations → duration 0). Writes `data/derived/preprocessed_gaze.csv` and `output/exclusion_log.txt`. **Dependency**: Requires T005 (raw data), T006 (fixation logic), and T015 (ROI mapping).

- [X] T015 [P] **ROI Mapping Logic**: Implement `code/utils/roi_mapping.py` using point‑in‑polygon to assign each gaze point to a ROI. Input: raw gaze coordinates + ROI polygons from dataset. Output: `roi_type` column added to gaze records. Used by T018.

- [ ] T040 **Data Quality Report (US1)**: Implement `code/02_data_quality_report.py` to read `output/exclusion_log.txt` and `data/derived/preprocessed_gaze.csv`, compute the number of excluded participants, reasons, and total participants count (derived from the checksum log generated by T005). Generates `output/data_quality_report.csv` satisfying SC‑001. **Dependency**: Runs after T018 and after `state/data_hashes.json` exists.

- [X] T010 [P] [US1] Contract test for data ingestion output schema in `tests/contract/test_ingestion_schema.py`

- [X] T011 [P] [US1] Integration test for I‑VT algorithm on sample noisy data in `tests/integration/test_ivt_preprocessing.py`

---

## Phase 3: User Story 1 - Core Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eye‑tracking data, apply I‑VT fixation detection, filter low‑quality participants, and map gaze to ROIs.

**Independent Test**: Run the preprocessing script on the sample dataset and verify that only participants with < 20 % data loss remain and that fixation events are correctly timestamped and ROI‑mapped.

- Tasks T015, T018, T040 (described above) constitute the implementation.

---

## Phase 4: User Story 2 - Mixed‑Effects Regression Analysis (Priority: P2)

**Goal**: Execute a mixed‑effects regression testing the three‑way interaction between source fixation duration, headline valence, and cognitive reflection scores.

- [ ] T023 **Data Merge & Outlier Capping**: Merge `data/derived/preprocessed_gaze.csv` (T018), `data/derived/empirical_outcomes.csv` (T004b), and `data/derived/valence_scores.csv` (T021) on `participant_id` and `headline_id`.
 1. Validate schemas; raise `DataMissingError` if required columns are absent.
 2. Cap `cognitive_reflection_score` at extreme percentiles.
 3. Preserve the `lexicon_used` flag from T021 as a covariate.
 4. Compute `headline_length` (word count) and `total_fixation_duration` (sum of fixation durations) as controls.
 Output: `data/derived/merged_dataset_full.csv`. **Dependency**: After T018, T004b, T021.

- [ ] T024 **Mixed‑Effects Regression & Correction**: Using `statsmodels`, fit <!-- FAILED: unspecified -->
 `belief_rating ~ fixation_duration * valence * crt + headline_length + total_fixation_duration + (1|participant_id) + (1|headline_id)` on `data/derived/merged_dataset_full.csv`.
 Steps:
 1. Load merged data, ensure outlier‑capped CRT and `lexicon_used` are present.
 2. Fit the model with random intercepts for participants and headlines.
 3. Apply **Holm‑Bonferroni correction specifically to the three‑way interaction term p‑value** (and to all other fixed‑effect p‑values for completeness).
 4. Output `data/derived/regression_results.csv` containing coefficients, raw p‑values, corrected p‑values (`p_adj`), confidence intervals, and interaction terms.
 **Dependency**: After T023.

- [X] T017 **Measure Runtime**: Implement `code/06_measure_runtime.py` to record wall‑clock time of the entire pipeline, compare to the time limit, and write `state/runtime_metrics.json` (`total_runtime_minutes`, `limit_minutes`, `status`). **Dependency**: Runs after T024.

- [X] T019 [P] [US2] Contract test for regression output schema in `tests/contract/test_regression_schema.py`

- [ ] T020 [P] [US2] Integration test for coefficient recovery on synthetic data in `tests/integration/test_mixed_effects_recovery.py`

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Verify that findings are robust to methodological variations (fixation thresholds, headline length controls, etc.).

- [ ] T032 [P] **Robustness Runner**: Refactor regression logic from T024 into a reusable function/class that accepts a `fixation_duration_threshold` argument. Exposes the same modeling pipeline (including Holm‑Bonferroni on the interaction term) and returns regression statistics.

- [X] T034 **Headline Length Control**: Ensure `code/05_regression_analysis.py` (now encapsulated in T032) includes `headline_length` as a control variable (already done in T023/T024).

- [ ] T033 **Robustness Sweep**: Execute a sweep over thresholds `{50, 100, 150}` ms. For each threshold: <!-- FAILED: unspecified -->
 1. Reset the random seed to `config.random_seed`.
 2. Re‑run the preprocessing pipeline with the given threshold (reuse T018 logic with parameter).
 3. Run the regression via the robustness runner (T032).
 4. Compute `mean_belief_rating`, `std_dev_belief`, and `range_belief` for the current threshold.
 5. Append results to `data/derived/robustness_report.csv`.
 **Dependency**: Requires T018 (parameterised), T023, T021, and T032.

- [ ] T039 **Stability Check**: Read `data/derived/robustness_report.csv` and verify that the sign and significance of the three‑way interaction term remain consistent across thresholds. Output `output/stability_check.json` with fields `consistent_direction`, `consistent_significance`, `ci_overlap_summary`.

- [ ] T029 [P] [US3] Contract test for robustness report schema in `tests/contract/test_robustness_schema.py`

- [ ] T030 [P] [US3] Integration test for threshold sweep stability in `tests/integration/test_sensitivity_analysis.py`

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Final refinements affecting multiple stories.

- [ ] T045 [P] Documentation updates in `docs/` and `paper/`
- [ ] T046 Code cleanup and refactoring
- [ ] T047 Performance optimization across all stories (ensure < 300 min runtime)
- [ ] T048 [P] Additional unit tests in `tests/unit/`
- [ ] T049 Run `quickstart.md` validation
- [ ] T050 Verify all artifacts are checksummed in `state/`
- [ ] T028 [P] **Final Report Generation**: Implement `code/07_generate_causal_framing.py` to produce `output/causal_framing_statement.txt`. Reads `data/derived/regression_results.csv`, extracts the three‑way interaction coefficient and its (corrected) p‑value, and dynamically composes a causal framing statement respecting FR‑006.

---

## Dependencies & Execution Order

### Phase Dependencies
- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Stories (Phases 3‑5)** → **Polish (Phase N)**
- All tasks in Phase 2 must succeed before any user‑story tasks start.

### Within User Stories
- **US1**: T015 → T018 → T040 (plus contract tests T010/T011)
- **US2**: T023 → T024 → T017 (plus contract tests T019/T020)
- **US3**: T032 → T033 → T039 (plus contract tests T029/T030)

### Parallel Opportunities
- All `[P]`‑tagged tasks within a phase may run concurrently once their hard dependencies are satisfied.
- Logging setup (T008a/T008b) must complete before any task that writes logs.

---

## Notes
- All random seeds are pinned in `code/config.yaml` (seed = 42) and reset before each robustness iteration.
- Every artifact written is recorded in `state/` with a SHA‑256 hash for data‑hygiene compliance.
- The `lexicon_used` flag ensures that the VADER fallback does not introduce an uncontrolled confound; it is treated as a covariate in the regression.
- No synthetic belief data or WYSIATI metrics are introduced; the outcome remains strictly `belief_rating` per FR‑004 and Constitution Principle VI.
