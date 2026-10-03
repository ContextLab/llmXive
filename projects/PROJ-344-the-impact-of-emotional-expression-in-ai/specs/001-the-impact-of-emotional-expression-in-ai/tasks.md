# Tasks: The Impact of Emotional Expression in AI Avatars on User Trust

**Input**: Design documents from `/specs/001-emotional-synchrony-trust/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project structure per implementation plan in `projects/PROJ-344-the-impact-of-emotional-expression-in-ai/` by executing `mkdir -p data/raw data/processed data/features code tests/contract tests/unit tests/integration outputs state`
- [X] T002 Initialize Python project with pinned dependencies by generating `code/requirements.txt` containing pinned versions for openface, librosa, scikit-learn, statsmodels, pandas, matplotlib, seaborn, synthpop
- [X] T003 [P] Configure linting and formatting tools by creating `.black` and `.flake8` config files in root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create static schema definitions in `specs/001-emotional-synchrony-trust/contracts/dataset_schema.yaml` and `contracts/feature_extraction_schema.yaml` based on FR-001 schema requirements
- [X] T005 Implement data validation logic in `code/config.py` and `code/validators.py` to enforce FR-001 (schema check, metadata presence)
- [X] T006 Setup deterministic logging and state tracking by creating `state/` directory and `code/logging_config.py` with specific logging format
- [X] T007 Implement error handling framework by creating `code/utils.py` with a `handle_corrupted_file()` function that logs to logger and returns None for specific error conditions (corrupted media, missing metadata)
- [X] T012b [P] Create IRB Template by generating `data/irb_request_template.md` with consent forms and anonymization protocols per Constitution Principle VII. **Trigger**: This is a static setup artifact created in Phase 2 to ensure compliance before any data logic is triggered. **Dependency**: None.
- [X] T012c_doc [US1] Create Data Collection Protocol Documentation by generating `docs/data_collection_protocol.md` which outlines the steps for a controlled human data collection study. **Trigger**: This is a documentation artifact for manual execution, not part of the automated 6h pipeline. **Dependency**: T012b (IRB template must exist).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Intra-Modal Consistency Extraction and Correlation (Priority: P1) 🎯 MVP

**Goal**: Download/generate dataset, extract facial/vocal features, compute consistency metric, and calculate Spearman correlation.

**Independent Test**: Run extraction and correlation on a sample; verify output CSV contains interaction IDs, consistency scores, trust scores, and a correlation coefficient with a confidence interval.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` against `contracts/dataset_schema.yaml`
- [X] T011 [P] [US1] Unit test for cross-correlation logic with mocked time-series from `tests/fixtures/mock_timeseries.npy` in `tests/unit/test_compute_metrics.py`

### Implementation for User Story 1

- [ ] T012_fetch [US1] Implement dataset fetcher with conditional fallback logic in `code/data_loader.py`. **Critical Logic**:
 1. **Attempt Real Fetch**: If a verified real source is injected by the environment, fetch it. If `NetworkTimeout` (retryable), retry up to 3 times. If `SchemaMismatch` or `DataUnavailable` (non-retryable), proceed to step 2.
 2. **Synthetic Media Fallback (Path A)**: Invoke T012_media to generate **synthetic video/audio files** (MP4/WAV) matching the schema. **Output**: `data/raw/synthetic_*.mp4`, `data/raw/synthetic_*.wav`. This path MUST feed T013/T014.
 3. **Synthetic Feature Fallback (Path B)**: ONLY if T012_media fails or is explicitly skipped for rapid validation, invoke T012_gen to generate **synthetic feature time-series** (CSV) directly. **Output**: `data/processed/synthetic_features.csv`. **Condition**: If Path B is taken, T013, T014, T013_clean, T014_clean, and T015_merge are SKIPPED. T015 runs directly on T012_gen output. **Note**: Path B is for validation only and does not satisfy FR-002/FR-003 for the primary study.
 4. **Human Collection (Manual Only)**: If T012_media fails and T012_gen is not allowed for primary study, trigger T012_trigger_collection to initiate the controlled data collection study. **Output**: References `data/irb_request_template.md` and `docs/data_collection_protocol.md`. **Dependency**: T004, T005, T006, T007, T012b, T012c_doc.
 **Output**: `data/raw/` populated with media (Path A) OR `data/processed/synthetic_features.csv` (Path B).
 **Dependency**: T004, T005, T006, T007, T012b, T012c_doc.
- [ ] T012_media [US1] Implement Controlled Synthetic Media Generation in `code/synthetic_media_gen.py` using `synthpop` and `ffmpeg` to generate **synthetic video (MP4) and audio (WAV) files** that mimic the temporal structure of real interactions. **Schema**: Video: 15fps, 320x240, 5s duration. Audio: Standard sampling rate, high-resolution mono, fixed short duration. **Output**: `data/raw/synthetic_*.mp4` and `data/raw/synthetic_*.wav`. **Logic**: This task MUST generate valid media files that can be processed by OpenFace and librosa. **Dependency**: T012_fetch (invoked by T012_fetch if real data fails).
- [ ] T012_gen [US1] Implement Controlled Synthetic Feature Generation in `code/synthetic_data_gen.py` using `synthpop` to generate **synthetic feature time-series** (CSV) that exactly mimic the schema of OpenFace/librosa output. **Schema**: Columns: `interaction_id` (str), `facial_landmarks_json` (str), `vocal_prosody_json` (str), `trust_score` (integers in [1, 5]). **Output**: `data/processed/synthetic_features.csv`. **Logic**: This task MUST generate CSV rows matching the `feature_extraction_schema.yaml`. **Note**: This path is for validation only and does not satisfy FR-002/FR-003 for the primary study. **Dependency**: T012_fetch (invoked by T012_fetch ONLY if T012_media fails or is skipped).
- [ ] T013 [P] [US1] Implement facial feature extraction in `code/extract_facial.py` using OpenFace (CPU binary) for video frames. **Output**: `data/processed/raw_facial_features.csv`. **Condition**: Run on ALL files in `data/raw/*.mp4`. **SKIP** if `data/processed/synthetic_features.csv` exists (T012_gen path). **Dependency**: T012_media (MUST complete and populate `data/raw` before this starts). **Failure Mode**: Raise FileNotFoundError if no valid media found. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T014 [P] [US1] Implement vocal prosody extraction in `code/extract_vocal.py` using librosa for pitch, energy, tempo from audio tracks. **Output**: `data/processed/raw_vocal_features.csv`. **Condition**: Run on ALL files in `data/raw/*.wav`. **SKIP** if `data/processed/synthetic_features.csv` exists (T012_gen path). **Dependency**: T012_media (MUST complete and populate `data/raw` before this starts). **Failure Mode**: Raise FileNotFoundError if no valid audio found.
- [X] T013_clean [US1] Implement filtering logic for facial features in `code/filter_features.py` to exclude interactions with time-series duration < 2.0 seconds or missing trust scores. **Input**: `data/processed/raw_facial_features.csv` (from T013). **Output**: `data/processed/clean_facial.csv`. **SKIP** if T012_gen path was taken. **Dependency**: T013.
- [X] T014_clean [US1] Implement filtering logic for vocal features in `code/filter_features.py` to exclude interactions with time-series duration < 2.0 seconds or missing trust scores. **Input**: `data/processed/raw_vocal_features.csv` (from T014). **Output**: `data/processed/clean_vocal.csv`. **SKIP** if T012_gen path was taken. **Dependency**: T014.
- [X] T015_merge [US1] Merge facial and vocal features into a single clean dataset in `code/merge_features.py`. **Input**: `data/processed/clean_facial.csv` (from T013_clean) AND `data/processed/clean_vocal.csv` (from T014_clean). **Output**: `data/processed/clean_features.csv`. **Schema**: Columns: `interaction_id`, `consistency_score` (computed later), `trust_score`, `avatar_type`, `duration`, `difficulty`. **SKIP** if T012_gen path was taken. **Dependency**: T013_clean AND T014_clean.
- [ ] T015 [US1] Implement intra-modal consistency metric calculation in `code/compute_metrics.py` (max abs cross-correlation within ±2s lag, normalized by product of standard deviations per FR-004). **Input**: `data/processed/clean_features.csv` (from T015_merge) OR `data/processed/synthetic_features.csv` (from T012_gen). **Logic**: If `data/processed/synthetic_features.csv` exists, use it and mark output as VALIDATION_ONLY. For PRIMARY study, T012_gen path is FORBIDDEN; pipeline MUST fail if T012_media fails and T012_trigger_collection is not triggered. **Output**: `data/processed/metrics.csv` with columns: `interaction_id` (str), `consistency_score` (float), `trust_score` (int). **Dependency**: T015_merge OR T012_gen (Conditional: if T012_gen runs, skip T013/T014/T013_clean/T014_clean/T015_merge).
- [X] T016 [US1] Implement Spearman correlation analysis in `code/analyze.py` to compute coefficient and 95% CI per FR-005, reading consistency scores from T015 output.
- [X] T016_report [US1] Generate `outputs/correlation_report.csv` and `outputs/unified_analysis_report.md` containing the correlation results. **Dependency**: T016.
- [X] T012_trigger_collection [US1] Implement executable task to initiate controlled data collection study if synthetic fallback fails. **Logic**: This task reads `data/irb_request_template.md` and `docs/data_collection_protocol.md` to launch the data collection workflow. **Output**: Generates `data/study_log.md` confirming the trigger event and protocol version, and updates `state/pipeline_status.yaml` to 'HUMAN_STUDIO_REQUIRED'. **Dependency**: T012_fetch (if T012_media fails). **Note**: This task is only executed if FR-001's fallback protocol is triggered.

---

## Phase 4: User Story 2 - Robustness Check with Control Variables (Priority: P2)

**Goal**: Run ordinal regression with control variables (avatar type, duration, difficulty) to verify robustness.

**Independent Test**: Run regression script on extracted features; verify output includes coefficients, p-values, and pseudo R-squared.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for ordinal regression model fitting with synthetic metadata in `tests/unit/test_analyze.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement ordinal regression (proportional odds model) in `code/analyze.py` including control variables per FR-006. **Logic**: Include control variables: 'avatar_type' (categorical encoding), 'interaction_duration' (numeric), 'task_difficulty' (ordinal). **Output**: Regression coefficients, p-values, and pseudo R-squared. **Dependency**: T015.
- [X] T022 [US2] Add logic to extract and report p-values and model fit statistics (pseudo R-squared) for consistency and controls, ensuring these values are explicitly written to the final report per SC-002. **Dependency**: T021.
- [X] T023_report [US2] Integrate regression results with US1 consistency scores to produce a unified analysis report containing all statistical outputs. **Output**: `outputs/unified_analysis_report.md`. **Requirement**: Must include the "associational only" disclaimer in the report header (see T017). **Dependency**: T021 AND T016_report.

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatter plot with regression line and confidence interval, ensuring WCAG AA contrast.

**Independent Test**: Run plotting script; verify output is a valid PNG with labeled axes, legend, title, and readable font sizes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Visual regression test to check file generation and basic structure in `tests/integration/test_visualize.py`

### Implementation for User Story 3

- [ ] T025_impl [US3] Implement scatter plot generation logic in `code/visualize.py` with consistency on X, trust on Y, regression line, and 95% CI bands per FR-007. **Requirement**: Implement `verify_wcag_contrast()` function that calculates relative luminance for ALL text elements (title, labels, legend) against the background and asserts >= 4.5:1 ratio. If check fails, auto-adjust colors by increasing lightness iteratively until threshold is met. Font sizes must be at least 12pt. The plot title MUST include the "associational only" disclaimer (see T017). **Output**: `outputs/consistency_trust_scatter.png` (generated by T025_exec). **Dependency**: T016_report AND T023_report.
- [X] T017 [US3] [Critical] Modify `code/visualize.py` (the implementation of T025_impl) to inject the "associational only" disclaimer into the plot title and report headers. **Dependency**: T025_impl. **Note**: This task must run BEFORE T025_exec.
- [ ] T025_exec [US3] Execute the visualization script to generate the final plot. **Input**: `code/visualize.py` (modified by T017). **Command**: `python code/visualize.py --mode scatter`. **Output**: `outputs/consistency_trust_scatter.png`. **Dependency**: T017.
- [X] T026 [US3] Export final figure to `outputs/` with proper labeling (title indicating correlation coefficient)

---

## Phase 6: Integration & End-to-End Verification

**Purpose**: Verify the full pipeline runs within constraints and produces valid results.

- [X] T027 [US1] Execute Full Pipeline and Validate Constraints by running `code/run_pipeline.py` with N=500 sample and verifying outputs exist in `outputs/`. **Assertion**: Must raise `SystemExit` if peak RAM > 7GB or runtime > 6h, explicitly confirming SC-005 compliance. **Dependency**: T012_fetch, T012_media, T013, T014, T015, T016, T025_impl, T017, T025_exec. (Note: T021/T023 are optional for MVP integration; T027 depends on T025_exec which depends on T017, which depends on T025_impl).

---

## Phase 7: Data Integrity & Reproducibility Hardening

**Purpose**: Ensure strict adherence to data hygiene and reproducibility principles (Constitution I, II, III, V).

- [X] T029_gen [US1] Implement checksum generation logic in `code/checksums.py` to generate SHA-256 hashes. **Dependency**: T012_fetch (must have populated data).
- [X] T029_store [US1] Implement checksum storage logic to write hashes to `state/raw_data_hashes.json` and `state/feature_hashes.json`. **Dependency**: T029_gen.
- [X] T029_int [US1] Integrate checksum generation into the pipeline execution flow to ensure hashes are generated after data creation and before usage. **Dependency**: T029_store AND T012_fetch/T012_media.
- [X] T030_gen [US1] Implement checksum verification logic for derived files in `code/checksums.py`. **Dependency**: T029_gen.
- [X] T030_store [US1] Implement checksum storage logic for derived files in `state/feature_hashes.json`. **Dependency**: T030_gen.
- [X] T030_int [US1] Integrate checksum verification into the pipeline execution flow to ensure verification happens before analysis. **Dependency**: T030_store AND T013/T014.
- [X] T031 [US1] Add deterministic seeding logic to `code/config.py` ensuring all random operations (synthetic generation, sampling) use a fixed seed logged in `state/random_seed.txt`.
- [X] T032 [US1] Create `code/audit_trail.py` to automatically log all pipeline execution parameters, input file hashes, and output file hashes into `state/audit_log.md` for full reproducibility per Constitution Principle I and V.

---

## Phase 8: Execution Feedback Resolution

**Purpose**: Resolve specific execution feedback and run-book mismatches identified during previous cycles.

- [X] T033 Reconcile run-book vs implementation for `code/extract_features.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/extract_features.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for cross-correlation logic with mocked time-series in tests/unit/test_compute_metrics.py"

# Launch all extraction tasks for User Story 1 together:
# Note: T013 and T014 are now in separate files (extract_facial.py, extract_vocal.py) producing data artifacts.
# They depend on T012_media to populate data/raw first.
Task: "Implement facial feature extraction in code/extract_facial.py using OpenFace (CPU binary)"
Task: "Implement vocal prosody extraction in code/extract_vocal.py using librosa"

# T015_merge consumes the data artifacts (clean_facial.csv, clean_vocal.csv) produced by T013_clean/T014_clean.
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
 - Developer A: User Story 1 (Extraction & Correlation)
 - Developer B: User Story 2 (Regression)
 - Developer C: User Story 3 (Visualization)
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
- **Critical Constraint**: All data processing must use CPU-only models (OpenFace CPU binary, librosa). No GPU, no 8-bit/4-bit quantization, no deep learning training.
- **Data Integrity**: Do not fabricate input data. Use real datasets (NAB/UCI) or deterministic synthetic generation via `synthpop` only as a fallback per FR-001. If synthetic is insufficient, trigger controlled data collection (T012_trigger_collection) using the protocol defined in T012c_doc.
- **Constitution Compliance**: T012c_doc implements the documentation for the Data Collection Protocol (consent forms, anonymization) as version-controlled artifacts. T012b is the explicit IRB template created in Phase 2.
- **Revision Note**: T012 updated to clarify the "fail loud" -> "synthetic fallback" flow with explicit steps. T012b moved to Phase 2. T012_gen extracted as the explicit synthetic feature generation task. T012_media added to generate synthetic media for extraction. T013/T014 split into Extraction and Cleaning (T013_clean, T014_clean) to handle edge cases and avoid race conditions. T015_merge added to combine clean features. T025 split into T025_impl (code) and T025_exec (run) to ensure T017 (disclaimer injection) runs before plot generation. T029/T030 split into Gen/Store/Int tasks. T012c removed from automated pipeline and replaced with T012c_doc.
- **New**: Phase 6 split into T026 (Implement Optimization) and T027 (Execute & Validate) to separate implementation from execution. T017 expanded to cover all final outputs including the unified report and plot title.
- **New**: T018 and T019 removed/merged. T018 logic merged into T012. T019 logic integrated into T012/T013/T014 with conditional triggers.
- **Critical Update**: T012 now explicitly defines two mutually exclusive paths (Media -> Extraction vs. Direct CSV) to resolve pipeline continuity. T012_media includes explicit schema (15fps, 44100Hz) to ensure compatibility with OpenFace/librosa. T015_merge includes explicit output schema. T025_impl mandates unconditional WCAG verification. T012c is removed from automated execution to satisfy SC-005.
- **Critical Update**: T012_trigger_collection added to execute the data collection protocol if synthetic fallback fails, addressing FR-001's requirement.