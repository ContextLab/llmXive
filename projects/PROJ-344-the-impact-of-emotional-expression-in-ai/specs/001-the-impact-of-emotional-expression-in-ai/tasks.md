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
- [X] T012a [US1] Verify Registry Status by creating `code/verify_registry.py` to scan the dataset registry for valid NAB/UCI sources. **Output**: `state/registry_status.json` (true if valid data found, false if empty).
- [X] T012b [US1] Create IRB Template by generating `data/irb_request_template.md` with consent forms and anonymization protocols per Constitution Principle VII.
- [X] T012c [US1] Create Data Collection Protocol Script by generating `code/data_collection_protocol.py` which contains the logic to trigger a controlled data collection study (e.g., generating a request for human-in-the-loop data). **Dependency**: T012a (must exist) and T012b (template must exist).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Intra-Modal Consistency Extraction and Correlation (Priority: P1) 🎯 MVP

**Goal**: Download/generate dataset, extract facial/vocal features, compute consistency metric, and calculate Spearman correlation.

**Independent Test**: Run extraction and correlation on a sample; verify output CSV contains interaction IDs, consistency scores, trust scores, and a correlation coefficient with a confidence interval.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` against `contracts/dataset_schema.yaml`
- [X] T011 [P] [US1] Unit test for cross-correlation logic with mocked time-series from `tests/fixtures/mock_timeseries.npy` in `tests/unit/test_compute_metrics.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement dataset fetcher with deterministic fallback logic in `code/data_loader.py`. **Critical Logic**: <!-- FAILED: unspecified -->
 1. Attempt to download real NAB/UCI data.
 2. If fetch fails (raises `DataFetchError`), check `state/registry_status.json` (from T012a).
 3. If registry is NOT empty, retry fetch.
 4. If registry IS empty, invoke `code/synthetic_data_gen.py` (T012_gen) to generate synthetic data.
 5. If synthetic generation fails, invoke `code/data_collection_protocol.py` (T012c) to trigger human data collection.
 6. **Never** halt execution with an error; always proceed to the next fallback step.
 **Output**: `data/processed/features.csv` (from real or synthetic data) or `state/collection_triggered.log` (if protocol triggered).
- [ ] T012_gen [US1] Implement Controlled Synthetic Data Generation in `code/synthetic_data_gen.py` using `synthpop` to generate **synthetic raw media files** (dummy video/audio) OR **synthetic feature time-series** that exactly mimic the schema and format of OpenFace/librosa output. **Output**: `data/processed/synthetic_features.csv` (or `data/raw/synthetic_video.mp4` etc). **Logic**: This task MUST NOT bypass the extraction logic (FR-002/FR-003). If synthetic media is generated, T013/T014 MUST run on it. If synthetic features are generated, they must match the `features.csv` schema exactly. **Dependency**: T012 (invoked by T012 if real data fails and registry is empty).
- [ ] T013 [P] [US1] Implement facial feature extraction in `code/extract_facial.py` using OpenFace (CPU binary) for video frames. **Output**: `data/processed/features.csv`. **Condition**: Run on ALL files in `data/raw` (real or synthetic). **Dependency**: T012 (must have populated `data/raw`).
- [ ] T014 [P] [US1] Implement vocal prosody extraction in `code/extract_vocal.py` using librosa for pitch, energy, tempo from audio tracks. **Output**: `data/processed/features.csv`. **Condition**: Run on ALL files in `data/raw` (real or synthetic). **Dependency**: T012 (must have populated `data/raw`).
- [ ] T015 [US1] Implement intra-modal consistency metric calculation in `code/compute_metrics.py` (max abs cross-correlation within ±2s lag, normalized) per FR-004. **Input**: `data/processed/features.csv` (produced by T013/T014). **Dependency**: T013 AND T014 (must have completed). <!-- FAILED: unspecified -->
- [X] T016 [US1] Implement Spearman correlation analysis in `code/analyze.py` to compute coefficient and 95% CI per FR-005, reading consistency scores from T015 output.
- [ ] T017 [US1] [Critical] Add logic to frame results as associational only (non-causal) in **ALL** outputs. **Specific Artifacts**: Modify `outputs/correlation_report.csv`, `outputs/regression_results.md`, `outputs/unified_analysis_report.md`, and the plot title in `outputs/consistency_trust_scatter.png`. Ensure every output artifact explicitly states the associational nature of the findings.
- [ ] T018 [US1] Implement "Fail Loud" Data Fetcher in `code/data_loader.py` by replacing all `try/except` fallbacks to synthetic data with a strict `raise DataFetchError` when real data is unavailable. **Requirement**: The loader MUST NOT generate or return synthetic data if the real fetch fails; it must terminate the pipeline unless a verified real source is explicitly injected by the execution environment. **Dependency**: T012 (refactor the existing logic).
- [ ] T019 [US1] Implement Real Data Streaming Logic in `code/data_loader.py` to handle datasets larger than 7GB RAM by using `datasets.load_dataset(..., streaming=True)` and chunked processing. **Requirement**: If a real dataset is selected, the code MUST stream it in chunks to compute statistics online, never loading the full dataset into memory. **Dependency**: T018.

---

## Phase 4: User Story 2 - Robustness Check with Control Variables (Priority: P2)

**Goal**: Run ordinal regression with control variables (avatar type, duration, difficulty) to verify robustness.

**Independent Test**: Run regression script on extracted features; verify output includes coefficients, p-values, and pseudo R-squared.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for ordinal regression model fitting with synthetic metadata in `tests/unit/test_analyze.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement ordinal regression (proportional odds model) in `code/analyze.py` including control variables per FR-006
- [ ] T022 [US2] Add logic to extract and report p-values and model fit statistics (pseudo R-squared) for consistency and controls, ensuring these values are explicitly written to the final report per SC-002.
- [ ] T023 [US2] Integrate regression results with US1 consistency scores to produce a unified analysis report containing all statistical outputs. **Output**: `outputs/unified_analysis_report.md`. **Requirement**: Must include the "associational only" disclaimer in the report header (see T017).

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatter plot with regression line and confidence interval, ensuring WCAG AA contrast.

**Independent Test**: Run plotting script; verify output is a valid PNG with labeled axes, legend, title, and readable font sizes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Visual regression test to check file generation and basic structure in `tests/integration/test_visualize.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement scatter plot generation in `code/visualize.py` with consistency on X, trust on Y, regression line, and 95% CI bands per FR-007. **Requirement**: Implement a custom `verify_wcag_contrast()` function using `Pillow` to programmatically measure pixel contrast ratios (≥4.5:1) AND verify that axis-label font sizes meet a minimum readable magnitude (e.g., >= 12pt equivalent) before export per SC-003. The script must raise an error if these checks fail. **Requirement**: The plot title MUST include the "associational only" disclaimer (see T017). **Output**: `outputs/consistency_trust_scatter.png`.
- [ ] T026 [US3] Export final figure to `outputs/` with proper labeling (title indicating correlation coefficient)

---

## Phase 6: Integration & End-to-End Verification

**Purpose**: Verify the full pipeline runs within constraints and produces valid results.

- [ ] T027 [US1] Implement Proactive Optimization in `code/run_pipeline.py` by adding batch processing logic using `pandas.read_csv(chunksize=...)` and streaming data structures to ensure the pipeline fits memory constraints (<7GB) BEFORE execution. **Output**: `code/run_pipeline.py` (updated).
- [ ] T028 [US1] Execute Full Pipeline and Validate Constraints by running `code/run_pipeline.py` with N=500 sample and verifying outputs exist in `outputs/`. **Assertion**: Must raise `SystemExit` if peak RAM > 7GB or runtime > 6h, explicitly confirming SC-005 compliance. **Dependency**: T027 (optimization must be implemented first).

---

## Phase 7: Data Integrity & Reproducibility Hardening

**Purpose**: Ensure strict adherence to data hygiene and reproducibility principles (Constitution I, II, III, V).

- [ ] T029 [US1] Implement checksum verification for raw data ingestion in `code/checksums.py` to generate and store SHA-256 hashes in `state/raw_data_hashes.json` per Constitution Principle III.
- [ ] T030 [US1] Implement checksum verification for derived feature files in `code/checksums.py` to generate and store hashes in `state/feature_hashes.json` per Constitution Principle III.
- [ ] T031 [US1] Add deterministic seeding logic to `code/config.py` ensuring all random operations (synthetic generation, sampling) use a fixed seed logged in `state/random_seed.txt`.
- [ ] T032 [US1] Create `code/audit_trail.py` to automatically log all pipeline execution parameters, input file hashes, and output file hashes into `state/audit_log.md` for full reproducibility per Constitution Principle I and V.

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
Task: "Implement facial feature extraction in code/extract_facial.py using OpenFace (CPU binary)"
Task: "Implement vocal prosody extraction in code/extract_vocal.py using librosa"

# T015 consumes the data artifacts (data/processed/features.csv) produced by T013/T014 (or T012_gen).
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
- **Data Integrity**: Do not fabricate input data. Use real datasets (NAB/UCI) or deterministic synthetic generation via `synthpop` only as a fallback per FR-001. If synthetic is insufficient, trigger controlled data collection (T012b/c) using the protocol defined in T012a.
- **Constitution Compliance**: T012b/c implements the actual Data Collection Protocol (consent forms, anonymization) as version-controlled artifacts. T012a is the explicit trigger script generating the IRB template.
- **Revision Note**: T012 updated to clarify the "fail loud" -> "synthetic fallback" flow with explicit steps. T012b moved to Phase 2 to ensure trigger availability. T012_gen extracted as the explicit synthetic generation task. T023 updated with specific WCAG verification mechanism. T029-T032 added to enforce strict data hygiene and reproducibility checksums. **New**: Phase 6 split into T026 (Implement Optimization) and T027 (Execute & Validate) to separate implementation from execution. T017 expanded to cover all final outputs including the unified report and plot title.
- **New**: T018 and T019 added to enforce "Fail Loud" data fetching and real data streaming to prevent fabrication and handle large datasets correctly.
