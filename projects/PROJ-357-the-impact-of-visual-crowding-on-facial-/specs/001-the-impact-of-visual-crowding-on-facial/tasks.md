# Tasks: The Impact of Visual Crowding on Facial Emotion Recognition Accuracy

**Input**: Design documents from `/specs/001-visual-crowding-emotion-recognition/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must wait for previous task)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T002 [P] Create `projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/` root directory and subdirectories: `code/`, `data/`, `tests/`, `artifacts/`, `state/projects/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Implement `code/utils/hygiene.py` to compute SHA256 checksums for `data/` and `artifacts/` and update `state/projects/PROJ-357-...yaml`
- [X] T007 Create `code/config.py` to manage environment variables and random seeds

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stimuli Generation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Programmatically generate controlled visual crowding stimuli from the RAVDESS dataset with parametric control over flanker count, eccentricity, and emotion.

**Independent Test**: Run the stimulus generation script and verify that output images exist with a manifest file containing emotion category, flanker count, and eccentricity values.

### Implementation for User Story 1

- [X] T011 [P] [US1] **Verify RAVDESS Source**: Query the official HuggingFace API to validate the RAVDESS dataset URL. If `spec.md` FR-001 URL is empty, default to the verified canonical URL `parlance/RAVDESS` and update `code/config.py`.
- [X] T011b [S] [US1] **Document Resolution**: Update `code/config.py` documentation to reflect the resolved RAVDESS source URL and any validation logic used in T011.
- [X] T012 [P] [US1] Implement `code/utils/download.py` to fetch RAVDESS dataset from the verified URL (from T011) and cache in `data/raw`.
- [~] T013 [P] [US1] Implement `code/utils/frame_extractor.py` to extract frames from RAVDESS video files into `data/raw/frames`
- [~] T014 [US1] Implement `code/utils/stimulus_gen.py` to:
 - Load frames and filter by multiple emotion categories
 - **If any of the 8 RAVDESS emotion categories are missing, log a WARNING to `data/interim/generation_errors.log` and proceed with the available categories (do NOT halt execution).**
 - Generate stimuli with varying flanker counts (≥3 levels) and eccentricities
 - Detect and exclude overlapping flankers (Edge Case)
 - **Explicitly record exact flanker count and eccentricity for every generated image**
 - **Write exclusion reasons to `data/interim/generation_errors.log`**
 - Output generated images to `data/interim/stimuli`
- [~] T015 [US1] Generate `data/interim/stimuli_manifest.json` by:
 - **Reading `data/interim/generation_errors.log` (T014) to update 'status' fields for excluded items**
 - **Validating that every image in `data/interim/stimuli` has a corresponding entry with exact flanker count and eccentricity values**
 - Linking file paths to metadata (emotion, flanker count, eccentricity)
 - **If 'mismatch_count' > 0, the pipeline MUST halt. If 'status' indicates missing categories, proceed but log the warning.**
- [~] T016 [S] [US1] **Versioning Checkpoint**: Run `code/utils/hygiene.py` to update state hashes after Phase 3 (Stimuli) completion.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T008 [P] [US1] Unit test for frame extraction logic in `tests/unit/test_frame_extractor.py`
- [~] T009 [P] [US1] Unit test for stimulus composition and overlap detection in `tests/unit/test_stimulus_gen.py`
- [~] T010 [P] [US1] Integration test for full pipeline in `tests/integration/test_pipeline.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Clutter Metric Computation (Priority: P2)

**Goal**: Compute visual clutter metrics (local contrast variance, spatial frequency energy) for each generated stimulus.

**Independent Test**: Run the metric computation script on a subset of stimuli and verify numeric values are produced for all entries with no missing data.

### Implementation for User Story 2

- [~] T019 [US2] Implement `code/utils/clutter_metrics.py` to compute local contrast variance and spatial frequency energy for the flanker region of each stimulus **consuming `stimuli_manifest.json` (T015) and generated images from `data/interim/stimuli` (T014)**
- [~] T020 [US2] **Implement Streaming Data Loader**: Refactor `code/utils/clutter_metrics.py` to process the full manifest via streaming/chunking to keep memory < 7 GB. Use `datasets.load_dataset` with `streaming=True` or manual chunked iteration.
- [~] T021 [US2] **Implement Fallback Logic**: If chunked processing exceeds available memory, fall back to a statistically valid random sample (e.g., a fixed-size random sample or fixed seed random sample) and explicitly log the sample size and limitation in `data/processed/metrics_sampling_log.txt`. Do NOT silently drop data or use a synthetic stand-in.
- [ ] T022 [US2] **Generate Clutter Metrics CSV**: Execute the metric computation (T019-T021) to generate `data/processed/clutter_metrics.csv` by joining metrics to `stimuli_manifest.json` via file path. **Verification: Verify row count matches stimuli_manifest.json (or the sampled count if fallback triggered) and no null values in metric columns.**
- [ ] T023 [US2] **Generate Validation Report**: Generate `data/processed/validation_report.json` confirming that clutter metrics (spatial frequency energy) correlate with flanker count (p < 0.05). **Schema: {'correlation_p_value': float, 'threshold_met': bool, 'status': 'pass'|'fail', 'sample_size': int}. This is a blocking gate for Phase 4 completion.**
- [~] T024 [S] [US2] **Versioning Checkpoint**: Run `code/utils/hygiene.py` to update state hashes after Phase 4 (Metrics) completion.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 4 - Human Emotion-Judgment Data Collection (Priority: P2)

**Goal**: Collect human observer recognition accuracy data for the generated stimuli to serve as the outcome variable. **This phase implements a local web interface for a pilot study with ≥5 real participants.**

**Independent Test**: Run the pilot study with ≥5 participants and verify that recognition accuracy is recorded for each stimulus with participant IDs and response labels.

### Implementation for User Story 4

- [ ] T045 [P] [US4] Implement `code/analysis/web_interface.py` to create a local, headless web interface for presenting stimuli and collecting emotion-judgment responses (-category classification).
- [~] T046a [US4] Implement `code/analysis/pilot_protocol.py` to define the experimental protocol (randomization, timing, instructions) and ensure IRB-compliant consent forms are displayed before data collection.
- [~] T046b [US4] **Generate Consent Template**: Create a template consent form `data/interim/consent_template.md` by copying the template from `specs/001-visual-crowding-emotion-recognition/consent_template.md` or generating from `spec.md` assumptions.
- [ ] T047 [MANUAL] [US4] **Execute Human Pilot**: Run `pilot_protocol.py` (T046a) with `web_interface.py` (T045) to collect raw responses from ≥5 unique participants.
 - **Output: `data/interim/raw_pilot_responses.csv` with columns: participant_id, stimulus_id, true_label, response_label, timestamp.**
 - **Verification: Verify file exists and contains ≥5 unique participant IDs. The pipeline will pause here until the CSV is manually uploaded or generated.**
- [~] T049a [US4] **Validate Real Human Data**: Verify that `data/interim/raw_pilot_responses.csv` exists, contains ≥5 unique participant IDs, and is not a synthetic placeholder. **If validation fails, halt the pipeline. This task must remain [ ] until T047 is completed and the file is uploaded.** <!-- FAILED: unspecified -->
- [~] T049b [S] [US4] **Versioning Checkpoint**: Run `code/utils/hygiene.py` to update state hashes after Phase 5 (Human Data) validation.
- [~] T048 [US4] Implement `code/analysis/data_loader.py` to load and validate raw pilot CSVs, compute `accuracy` (correct/incorrect), and aggregate by stimulus ID, emotion, and flanker count.
 - **Output: `data/processed/human_judgments_aggregates.csv` with columns: stimulus_id, accuracy, n_trials, emotion_label, flanker_count.**
 - **Note: For unit testing, this script must also support loading a mock CSV with the same schema if `--test-mode` flag is provided.**

**Checkpoint**: At this point, User Stories 1, 2, and 4 should be functional with real human data ready for analysis

---

## Phase 6: User Story 3 - Associational Analysis & Reporting (Priority: P3)

**Goal**: Perform a Generalized Linear Mixed Model (GLMM) to correlate clutter metrics with human recognition accuracy.

**Independent Test**: Run the analysis script on sample data and verify that regression coefficients, p-values, and model diagnostics are produced.

### Implementation for User Story 3

- [~] T033 [US3] Implement `code/analysis/glmm_model.py` to fit a binomial GLMM with clutter metrics as fixed effects and participant/stimulus as random effects
- [ ] T034 [US3] Implement fallback logic: if GLMM fails to converge, fit a fixed-effects only model and log the warning.
 - **Output: `data/processed/fixed_effects_results.json` with schema: {'convergence_status': 'fail', 'fallback_reason': str, 'coefficients': dict}.**
 - **Log a warning to `data/interim/model_warnings.log`.**
- [ ] T038 [US3] **Generate Regression Results JSON**: Generate `data/processed/regression_results.json` containing coefficients, confidence intervals, and p-values. **Schema: Each coefficient entry must have 'beta', 'se', 'ci_lower', 'ci_upper', 'p_value', 'fdr_p_value'. This task depends on T033/T034.**
- [ ] T035 [US3] Implement multiple-comparison correction (Benjamini-Hochberg FDR ≤ 0.05) for hypothesis tests (FR-005).
 - **Output: Update `data/processed/regression_results.json` with 'fdr_corrected_p_values' array.**
- [~] T036 [US3] Implement `code/analysis/reporting.py` to generate a final report framing findings as associational (FR-006).
 - **Requirement: Report must explicitly state 'model_type' (GLMM or Fixed-Effects) and discuss fallback status if applicable.**
- [~] T040 [US3] **Execute Reporting with Fallback**: **Depends on T034 and T038**. If T034 triggers a fallback, execute `code/analysis/reporting.py` with the fixed-effects results from T034 to generate the final report. Ensure the report reflects the model type and any fallbacks.
- [~] T037 [US3] Generate `artifacts/model_config.yaml` with hyperparameters, seeds, and model diagnostics.
 - **Schema: Include keys: 'seed', 'model_type', 'convergence_status', 'fdr_threshold', 'fallback_status', 'fallback_reason'.**

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T032 [P] [US3] Unit test for GLMM convergence and fallback logic in `tests/unit/test_glmm_fallback.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T039 [P] Run `code/utils/hygiene.py` to update state hashes for all final artifacts
- [~] T041 [P] Documentation updates in `specs/001-visual-crowding-emotion-recognition/quickstart.md`.
 - **Update: Add section 'Running the Human Pilot' with CLI arguments and IRB protocol instructions.**
- [~] T042 Run full pipeline integration test in `tests/integration/test_pipeline.py`
- [ ] T043 Verify all tasks complete within 6 hours on CPU-only runner (Constraint).
 - **Output: Generate `state/timing_report.json` with keys: 'phase', 'start_timestamp', 'end_timestamp', 'duration_hours'.**
 - **Pass condition: duration_hours < 6.0 for the full pipeline.**

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (stimuli)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (stimuli)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 (metrics) and US4 (human data)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US4 can start in parallel (US3 must wait for US2/US4 data)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for frame extraction logic in tests/unit/test_frame_extractor.py"
Task: "Unit test for stimulus composition and overlap detection in tests/unit/test_stimulus_gen.py"

# Launch all models for User Story 1 together:
Task: "Implement code/utils/download.py to fetch RAVDESS dataset"
Task: "Implement code/utils/frame_extractor.py to extract frames"
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
4. Add User Story 4 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Stimuli)
 - Developer B: User Story 2 (Metrics)
 - Developer C: User Story 4 (Human Data - Web Interface)
3. Once data is ready:
 - Developer A/B/C or D: User Story 3 (Analysis)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential (must wait for previous task)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint Reminder**: All tasks must run on free CPU-only CI with limited CPU resources and GB RAM (no GPU). No 8-bit quantization or large model training.
- **Data Integrity**: Do not fabricate data. Use real RAVDESS dataset and real human pilot data (T047-T049) as specified in US-4.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [~] T050 Reconcile run-book vs implementation for `code/run_full_pipeline.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/run_full_pipeline.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.

<!-- REVISION CONCERNS: Addressing /speckit.analyze findings -->
- [~] T051 [US2] **Implement Streaming Data Loader for Metrics**: Refactor `code/utils/clutter_metrics.py` to use `datasets.load_dataset` with `streaming=True` or manual chunked iteration over `stimuli_manifest.json` to ensure memory usage stays under 7 GB even with large stimulus sets. **Do NOT load the entire manifest into RAM at once.**
- [~] T052 [US3] **Implement Robust Convergence Fallback**: Enhance `code/analysis/glmm_model.py` to catch specific convergence errors from `statsmodels` (e.g., `ConvergenceWarning`) and automatically switch to a fixed-effects logistic regression model with detailed logging of the switch and the reason (e.g., "Singularity", "Maximum iterations reached").
- [~] T053 [US4] **Add Data Integrity Check for Human Responses**: Create a validation task in `code/analysis/pilot_protocol.py` to ensure `data/interim/raw_pilot_responses.csv` contains no duplicate `stimulus_id` + `participant_id` pairs and that all `response_label` values are within the valid 8-category range before aggregation.
- [~] T054 [US3] **Generate Final Associational Report**: Implement `code/analysis/reporting.py` to explicitly generate a markdown report that frames all findings as associational (per FR-006), includes the model type (GLMM vs Fixed-Effects), and details any fallbacks or convergence warnings encountered.
- [~] T055 [Polish] **Create Unified Pipeline Orchestrator**: Implement `code/run_full_pipeline.py` to sequentially execute T013 (Stimuli), T019 (Metrics), T047 (Human Data - Manual Trigger), T033 (GLMM), and T054 (Reporting), ensuring strict dependency ordering and error propagation.

- [~] T056 [Polish] **Finalize Execution Gate Validation**: Update `code/utils/hygiene.py` to include a specific validation step that checks for the presence of `data/processed/clutter_metrics.csv` and `data/processed/human_judgments_aggregates.csv` before allowing the pipeline to proceed to the GLMM stage, ensuring data flow integrity.
- [~] T057 [US2] **Document Streaming Strategy**: Update `code/utils/clutter_metrics.py` docstrings and `specs/001-visual-crowding-emotion-recognition/quickstart.md` to explicitly describe the chunking/streaming logic used to handle large datasets within the 7 GB RAM constraint, including the fallback sampling criteria.
- [~] T058 [US3] **Verify FDR Implementation**: Add a unit test in `tests/unit/test_glmm_fallback.py` (or a new `tests/unit/test_reporting.py`) to verify that the Benjamini-Hochberg correction is correctly applied to the p-values in `regression_results.json` and that the FDR threshold (0.05) is respected.
- [~] T059 [US4] **Validate Consent Compliance**: Ensure `code/analysis/pilot_protocol.py` includes a checksum or hash verification step to confirm that the consent form displayed to participants matches the version stored in `data/interim/consent_template.md` at the time of data collection.
- [ ] T060 [Polish] **Run End-to-End Timing Verification**: Execute the full pipeline (including manual data upload simulation) on the free-tier runner to generate `state/timing_report.json` and confirm the total duration is [deferred] as required by the performance constraints. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
