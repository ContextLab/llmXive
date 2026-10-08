# Tasks: Assessing the Impact of Mindfulness Training on Default Mode Network Activity

**Input**: Design documents from `/specs/001-mindfulness-dmn-connectivity/`
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

- [X] T001 Create project structure with exact directory tree: src/, tests/, data/, docs/ directories each containing __init__.py files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Atlas Extraction (T021) to ensure data flow.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create data directory structure (data/raw/, data/processed/, data/results/)
- [X] T004 [P] Setup Docker configuration for fMRIPrep container at docker/fmriprep.Dockerfile with CPU-limited settings defining thread and memory constraints.
- [X] T006 [P] Setup logging infrastructure at src/utils/logging.py with JSON format logging and QC report template (HTML with motion summary, SNR, temporal SNR metrics)
- [X] T007 [P] Create base configuration management at src/config/settings.py with required config items: dataset_paths (dict with raw/processed/result keys as strings), preprocessing_params (dict with motion_correction=bool, slice_timing=bool, normalization=bool, smoothing_mm=int, bandpass_range=tuple[float, float]), atlas_choice (str: 'AAL' per Constitution Principle VI), motion_thresholds (dict with translation_mm=float, rotation_deg=float), statistical_thresholds (dict with nbs_t=float, nbs_alpha=float, power_target=float), all with Python type hints and JSON-serializable format
- [X] T008 [P] Implement random seed pinning for reproducibility at src/utils/seeding.py with a fixed seed value for numpy, random, and torch modules. **Verification**: Verify deterministic output on re-run with a fixed random seed.
- [X] T009 [P] Setup environment variable management for dataset API keys at src/config/env.py with env vars (OPENNEURO_API_KEY, DATA_DIR) and validation rules (required, non-empty)
- [X] T021 Implement AAL atlas DMN region extraction (PCC, mPFC, IPL, angular gyrus) per Constitution Principle VI and Plan.md at src/analysis/extract_dmn_rois.py. **Output**: AAL mask files in data/processed/atlas/ and a JSON manifest of ROI coordinates (MNI152). **Verification**: Verify all ROIs exist and match standard MNI coordinates. **Note**: This task implements the AAL atlas as mandated by the Constitution, overriding the conflicting FR-003 in the Spec text.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI datasets from OpenNeuro and run standardized preprocessing with fMRIPrep

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a single OpenNeuro dataset and verifying that fMRIPrep generates valid output files in expected MNI152 space

### Test Tasks for User Story 1

- [X] T043 [P] [US1] Write unit tests for preprocessing pipeline in tests/unit/test_preprocessing.py (FAIL before implementation)

### Implementation for User Story 1

- [X] T010a [P] [US1] Create OpenNeuro API client class at src/datasets/openneuro_client.py with `list_datasets` method returning list of dataset IDs and basic metadata. **Verification**: Unit test confirms API call succeeds and returns list.
- [X] T010b [P] [US1] Implement `get_dataset_info` method at src/datasets/openneuro_client.py with error handling for missing datasets. **Verification**: Unit test confirms error handling on invalid ID.
- [X] T011 [US1] Create dataset download script with URL validation at src/datasets/download_datasets.py with validation rules (URL format, checksum verification) and output format (downloaded files in data/raw/)
- [X] T012a [P] [US1] Define dataset metadata schema at src/datasets/metadata_schema.py including required fields: pre_scan_count, post_scan_count, intervention_type, scan_type. **Verification**: Schema validates against sample JSON.
- [X] T012b [P] [US1] Implement design verification logic at src/datasets/verify_design.py to check for 'mindfulness intervention metadata' by searching for keywords ('mindfulness', 'MBSR', 'meditation', 'mindfulness-based stress reduction') in metadata fields. If keywords are missing, log a gap in docs/gaps.md and proceed if real resting-state data is available; if no real data is available, raise `DataFetchError`. **Verification**: Unit test confirms correct filtering and gap logging.
- [X] T013 [US1] Create fMRIPrep Docker runner script at src/preprocessing/fmriprep_runner.py with appropriate thread and memory configuration settings (--nthreads <NUM_THREADS> --omp-nthreads <NUM_THREADS> --mem-mb <MEMORY_MB>).
- [X] T014 [US1] Implement motion parameter extraction from fMRIPrep output at src/preprocessing/extract_motion.py with output format (CSV with columns: subject_id, translation_x/y/z, rotation_x/y/z) and standard rigid-body motion parameters
- [X] T015 [US1] Create motion exclusion filter (>3mm translation or >3° rotation) at src/preprocessing/motion_filter.py. **Output**: data/processed/excluded_subjects.csv listing excluded IDs. **Verification**: Verify CSV contains subjects with motion >3mm/3° and excludes them from analysis.
- [X] T016 [US1] Implement Nilearn lightweight preprocessing fallback (motion correction, slice timing, MNI standard normalization, 6mm smoothing, bandpass 0.01-0.1 Hz) at src/preprocessing/nilearn_fallback.py using `clean_img` and `resample_to_img`. **Note**: Conditional alternative to T013 (OR logic), not parallel.
- [X] T017 [US1] Create fMRIPrep HTML report parser for quality control at src/preprocessing/qc_parser.py with QC metrics (motion summary, SNR, temporal SNR) and output format (JSON summary + HTML report path)
- [X] T018 [US1] Implement dataset-variable fit verification (pre/post scans, DMN node coordinates) and document results per FR-008 at src/datasets/verify_variables.py
- [X] T020 [US1] Implement dataset gap logging and methods documentation for missing datasets at src/utils/gap_logging.py with log format (JSON with timestamp, dataset_id, gap_type) and documentation structure (markdown in docs/gaps.md)
- [X] T050 [US1] Implement strict real-data loader with NO synthetic fallback at src/datasets/real_data_loader.py. **Requirement**: Must raise `DataFetchError` if OpenNeuro API fails completely; if API succeeds but mindfulness metadata is missing, log a gap and proceed with available real resting-state data (per Plan's Dataset Scarcity Contingency). Must NOT contain `try/except` blocks that fall back to `generate_synthetic_*()` or mock data. **Verification**: Unit test confirms exception is raised on simulated network failure and gap logging occurs on missing metadata.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - DMN Functional Connectivity Analysis (Priority: P2)

**Goal**: Extract DMN time series, compute connectivity matrices, apply statistical corrections, and calculate effect sizes

**Independent Test**: Can be fully tested by running the connectivity analysis on a single preprocessed dataset and verifying that correlation matrices, Fisher transformations, and NBS-corrected p-values are output

### Test Tasks for User Story 2

- [X] T044 [P] [US2] Write unit tests for connectivity analysis in tests/unit/test_connectivity.py (FAIL before implementation)

### Implementation for User Story 2

- [X] T022 [US2] Create time series extraction from MNI152 normalized BOLD images at src/analysis/extract_timeseries.py with extraction method (mean time series from ROI mask). **Dependency**: Requires T015 (Motion Filter) to be complete to ensure only valid subjects are processed. **Output**: Numpy array per subject.
- [X] T023 [US2] Implement Pearson correlation matrix computation between all DMN node pairs at src/analysis/correlation_matrix.py
- [X] T024 [US2] Create Fisher z-transformation with AR(1) prewhitening at src/analysis/fisher_z_transform.py
- [X] T025 [US2] Implement Permutation testing at src/analysis/permutation_test.py using a sufficient number of iterations for robust statistical inference. **Output**: p-values and effect sizes. **Verification**: Unit test confirms p-value distribution on synthetic data.
- [X] T026 [US2] Create paired t-test for pre vs. post connectivity across subjects at src/analysis/paired_tests.py
- [X] T027 [US2] Implement bootstrapped 95% CI calculation for Cohen's d at src/analysis/effect_sizes.py. **Output**: Function calculate_ci(data, n=10000) returning dict. **Verification**: Unit test confirms CI bounds on synthetic data.
- [X] T028 [US2] Implement Network-Based Statistic (NBS) correction with primary threshold t≥3.1 and component-wise family-wise error correction at α=0.05 at src/analysis/nbs_correction.py. **Output**: significant_components. **Verification**: Verify NBS output matches reference on small dataset.
- [X] T030 [US2] Create associational framing validator to prevent causal claims in output reports per FR-009 at src/utils/associational_framing.py. **Verification**: Scan output text for causal language and raise error if found.
- [X] T031 [US2] Implement sensitivity analysis for motion thresholds across varying magnitudes at src/analysis/motion_sensitivity.py
- [X] T032 [US2] Create results summary table generator with effect sizes and p-values at src/analysis/results_summary.py with table format (CSV with columns: connection, effect_size, ci_lower, ci_upper, p_value)
- [X] T051 [US2] Implement streaming data processor for large datasets at src/analysis/streaming_processor.py. **Requirement**: Use `datasets.load_dataset(..., streaming=True)` or chunked iteration to process fMRI data without loading full dataset into RAM. **Verification**: Unit test confirms memory usage stays <7GB on simulated large input (50 subjects, 200 timepoints, 3mm resolution).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Dataset Meta-Analysis (Priority: P3)

**Goal**: Perform random-effects meta-analysis across ≥3 datasets with heterogeneity assessment

**Independent Test**: Can be fully tested by running the meta-analysis script on ≥3 datasets with computed effect sizes and verifying that pooled effect size, confidence interval, and heterogeneity metrics are output in forest plot format

### Test Tasks for User Story 3

- [X] T058 [P] [US3] Write unit tests for meta-analysis script in tests/unit/test_meta_analysis.py (FAIL before implementation)

### Implementation for User Story 3

- [X] T038 [US3] Implement dataset scarcity contingency (single-dataset reporting if <3 datasets) gating logic at src/analysis/dataset_contingency.py to determine whether meta-analysis should proceed. **Deliverable**: If <3 datasets, generate single-dataset results report with effect sizes and 95% CIs.
- [X] T033 [US3] Create R metafor package integration wrapper at src/analysis/metafor_wrapper.R
- [X] T034 [US3] Implement random-effects meta-analysis across datasets at src/analysis/meta_analysis.py. **Dependency**: Requires effect sizes from T027/T032 (US2) to be complete.
- [X] T035 [US3] Create I² heterogeneity statistic calculation at src/analysis/heterogeneity.py
- [X] T036 [US3] Implement leave-one-out sensitivity analysis for I² > 50% at src/analysis/sensitivity_analysis.py. **Output**: sensitivity_analysis.py. **Verification**: Verify I2 reduction when removing outlier dataset.
- [X] T037 [US3] Create forest plot generator for pooled effect sizes at src/analysis/forest_plots.py with plot library (matplotlib/seaborn) and output format (PNG at publication-quality resolution, PDF for publication)
- [X] T039 [US3] Create Q-test for heterogeneity significance at src/analysis/q_test.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T019 [P] Implement post-hoc power analysis script using statsmodels.stats.power.TTestPower at src/analysis/power_analysis.py. **Dependency**: Requires effect sizes from US2. **Output**: docs/power_analysis_report.md. **Verification**: Verify report contains power >= 80% calculation.
- [X] T019a [P] Implement a priori power analysis script using statsmodels.stats.power.TTestPower at src/analysis/power_analysis.py. **Input**: Assumed effect size d=0.5. **Output**: docs/power_analysis_report.md (appended section). **Verification**: Verify report contains required sample size calculation for [deferred] power.
- [X] T040 [P] Documentation updates at docs/methods.md with specific content sections (power analysis methodology, motion exclusion rates, dataset counts, preprocessing params)
- [X] T041 [P] Code cleanup and refactoring across src/analysis/*.py files to remove duplicate imports and add type hints (function signatures, return types)
- [X] T042 Performance optimization for NBS permutation testing on 2 cores with success criteria: runtime <2h on 2 cores for 10 subjects. **Output**: optimized nbs_runner.py. **Verification**: Run benchmark on 10 subjects and log time <2h.
- [X] T045 Security hardening for API key handling at src/config/env.py with.env file validation and key rotation
- [X] T047 Create final report template with associational framing and dataset gap documentation at docs/final_report.md
- [X] T046 Run plan.md and spec.md validation to ensure all FRs are addressed and generate docs/fr_traceability.md mapping each FR to implementation location
- [X] T048 Implement reproducibility checklist verification (random seeds, Docker hashes, data checksums) at src/utils/reproducibility_check.py
- [X] T052 [P] Implement execution gate validation script at src/utils/fabrication_guard.py. **Requirement**: Scan all result files for synthetic data markers (e.g., `random.*`, `mock_`, `synthetic_`) and raise error if found. **Verification**: Unit test confirms detection of synthetic data patterns.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Strictly requires** T015 (Motion Filter) from US1 to be complete before T022 (Time Series Extraction) can begin.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Strictly requires** T027/T032 (Effect Sizes) from US2 to be complete before T034 (Meta-analysis) can begin.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
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
# Launch all preprocessing tasks for User Story 1 together:
Task: "Implement OpenNeuro API client for dataset discovery at src/datasets/openneuro_client.py"
Task: "Create data directory structure (data/raw/, data/processed/, data/results/)"
Task: "Setup logging infrastructure at src/utils/logging.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test preprocessing pipeline on single OpenNeuro dataset
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
 - Developer A: User Story 1 (Data Acquisition/Preprocessing)
 - Developer B: User Story 2 (Connectivity Analysis)
 - Developer C: User Story 3 (Meta-Analysis)
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
- **Compute Feasibility**: All tasks must run on GitHub Actions free tier (limited CPU resources, limited RAM, within a maximum time limit)
- **Dataset URLs**: OpenNeuro datasets at https://openneuro.org/datasets must be verified before download
- **Atlas Choice**: AAL atlas per Constitution Principle VI and Plan.md (overrides Spec FR-003 which contains an error)
- **Motion Thresholds**: >3mm translation or >3° rotation for exclusion (sensitivity analysis 3/4mm)
- **Statistical Methods**: Fisher-z with AR(1) or permutation (10k), NBS (t≥3.1, α=0.05), bootstrapped CIs (10k)
- **Framing**: All findings must be associational, not causal (FR-009)
- **Power Analysis**: A priori and post-hoc per spec FR-010 (moved to Phase 6 to respect data dependencies)
- **Data Integrity**: T050 and T052 enforce strict real-data loading and forbid synthetic fallbacks to prevent fabrication. T051 ensures large datasets are streamed.
- **Dataset Scarcity**: T012b and T050 implement the Plan's contingency to log gaps and proceed with available real data if mindfulness metadata is missing.