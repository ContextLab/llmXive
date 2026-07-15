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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create data directory structure (data/raw/, data/processed/, data/results/)
- [X] T004 [P] Setup Docker configuration for fMRIPrep container at docker/fmriprep.Dockerfile with CPU-limited settings defining thread and memory constraints.
- [X] T006 [P] Setup logging infrastructure at src/utils/logging.py with JSON format logging and QC report template (HTML with motion summary, SNR, temporal SNR metrics)
- [X] T007 [P] Create base configuration management at src/config/settings.py with required config items: dataset_paths (dict with raw/processed/result keys as strings), preprocessing_params (dict with motion_correction=bool, slice_timing=bool, normalization=bool, smoothing_mm=int, bandpass_range=tuple[float, float]), atlas_choice (str: 'AAL' per Constitution Principle VI), motion_thresholds (dict with translation_mm=float, rotation_deg=float), statistical_thresholds (dict with nbs_t=float, nbs_alpha=float, power_target=float), all with Python type hints and JSON-serializable format
- [ ] T008 [P] Implement random seed pinning for reproducibility at src/utils/seeding.py with seed value 42 for numpy, random, torch modules; verification criteria: deterministic output on re-run
- [ ] T009 [P] Setup environment variable management for dataset API keys at src/config/env.py with env vars (OPENNEURO_API_KEY, DATA_DIR) and validation rules (required, non-empty)
- [ ] T019 [P] Implement post-hoc power analysis script using statsmodels.stats.power.TTestPower at src/analysis/power_analysis.py with sample-size requirements documentation (power ≥80% target) for methods output <!-- SKIPPED: non-mapping output -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI datasets from OpenNeuro and run standardized preprocessing with fMRIPrep

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a single OpenNeuro dataset and verifying that fMRIPrep generates valid output files in expected MNI152 space

### Test Tasks for User Story 1

- [ ] T043 [P] [US1] Write unit tests for preprocessing pipeline in tests/unit/test_preprocessing.py (FAIL before implementation)

### Implementation for User Story 1

- [ ] T010 [US1] Implement OpenNeuro API client for dataset discovery at src/datasets/openneuro_client.py with API endpoints (/datasets, /datasets/{id}), methods (list_datasets, get_dataset_info), return types (dict)
- [ ] T011 [US1] Create dataset download script with URL validation at src/datasets/download_datasets.py with validation rules (URL format, checksum verification) and output format (downloaded files in data/raw/)
- [ ] T012 [US1] Implement dataset design verification to confirm pre/post resting-state scans with mindfulness metadata at src/datasets/verify_design.py with required metadata fields (pre_scan_count:int, post_scan_count:int, intervention_type:str, scan_type:str) and verification logic (pre_scan_count > 0 AND post_scan_count > 0 AND intervention_type matches regex 'mindfulness|MBSR|MBC' case-insensitive, scan_type equals 'rs-fMRI' or 'resting')
- [ ] T013 [US1] Create fMRIPrep Docker runner script at src/preprocessing/fmriprep_runner.py with appropriate thread and memory configuration settings
- [ ] T014 [US1] Implement motion parameter extraction from fMRIPrep output at src/preprocessing/extract_motion.py with output format (CSV with columns: subject_id, translation_x/y/z, rotation_x/y/z) and 6 rigid-body motion parameters
- [ ] T015 [US1] Create motion exclusion filter (>3mm translation or >3° rotation) at src/preprocessing/motion_filter.py
- [ ] T016 [US1] Implement Nilearn lightweight preprocessing fallback (motion correction, slice timing, MNI152 normalization, 6mm smoothing, bandpass) at src/preprocessing/nilearn_fallback.py as independent alternative to T013 (not dependent on T013 completion)
- [ ] T017 [US1] Create fMRIPrep HTML report parser for quality control at src/preprocessing/qc_parser.py with QC metrics (motion summary, SNR, temporal SNR) and output format (JSON summary + HTML report path)
- [ ] T018 [US1] Implement dataset-variable fit verification (pre/post scans, DMN node coordinates) and document results per FR-008 at src/datasets/verify_variables.py
- [ ] T020 [US1] Implement dataset gap logging and methods documentation for missing datasets at src/utils/gap_logging.py with log format (JSON with timestamp, dataset_id, gap_type) and documentation structure (markdown in docs/gaps.md)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - DMN Functional Connectivity Analysis (Priority: P2)

**Goal**: Extract DMN time series, compute connectivity matrices, apply statistical corrections, and calculate effect sizes

**Independent Test**: Can be fully tested by running the connectivity analysis on a single preprocessed dataset and verifying that correlation matrices, Fisher transformations, and NBS-corrected p-values are output

### Test Tasks for User Story 2

- [ ] T044 [P] [US2] Write unit tests for connectivity analysis in tests/unit/test_connectivity.py (FAIL before implementation)

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement AAL atlas DMN region extraction (PCC, mPFC, IPL, angular gyrus) per Constitution Principle VI at src/analysis/extract_dmn_rois.py
- [ ] T022 [US2] Create time series extraction from MNI152 normalized BOLD images at src/analysis/extract_timeseries.py with extraction method (mean time series from ROI mask) and output format (numpy array per subject)
- [ ] T023 [US2] Implement Pearson correlation matrix computation between all DMN node pairs at src/analysis/correlation_matrix.py
- [ ] T024 [US2] Create Fisher z-transformation with AR(1) prewhitening at src/analysis/fisher_z_transform.py
- [ ] T025 [US2] Implement permutation testing (10,000 iterations) as alternative to AR(1) at src/analysis/permutation_test.py
- [ ] T026 [US2] Create paired t-test for pre vs. post connectivity across subjects at src/analysis/paired_tests.py
- [ ] T027 [US2] Implement bootstrapped 95% CI calculation (10,000 iterations) for Cohen's d at src/analysis/effect_sizes.py
- [ ] T028 [US2] Implement Network-Based Statistic (NBS) correction with primary threshold t≥3.1 and component-wise family-wise error correction at α=0.05 at src/analysis/nbs_correction.py
- [ ] T030 [US2] Create associational framing validator to prevent causal claims in output reports per FR-009 at src/utils/associational_framing.py
- [ ] T031 [US2] Implement sensitivity analysis for motion thresholds across varying magnitudes at src/analysis/motion_sensitivity.py
- [ ] T032 [US2] Create results summary table generator with effect sizes and p-values at src/analysis/results_summary.py with table format (CSV with columns: connection, effect_size, ci_lower, ci_upper, p_value)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Dataset Meta-Analysis (Priority: P3)

**Goal**: Perform random-effects meta-analysis across ≥3 datasets with heterogeneity assessment

**Independent Test**: Can be fully tested by running the meta-analysis script on ≥3 datasets with computed effect sizes and verifying that pooled effect size, confidence interval, and heterogeneity metrics are output in forest plot format

### Test Tasks for User Story 3

- [ ] T058 [P] [US3] Write unit tests for meta-analysis script in tests/unit/test_meta_analysis.py (FAIL before implementation)

### Implementation for User Story 3

- [ ] T038 [US3] Implement dataset scarcity contingency (single-dataset reporting if <3 datasets) gating logic at src/analysis/dataset_contingency.py to determine whether meta-analysis should proceed
- [ ] T033 [US3] Create R metafor package integration wrapper at src/analysis/metafor_wrapper.R
- [ ] T034 [US3] Implement random-effects meta-analysis across datasets at src/analysis/meta_analysis.py
- [ ] T035 [US3] Create I² heterogeneity statistic calculation at src/analysis/heterogeneity.py
- [ ] T036 [US3] Implement leave-one-out sensitivity analysis for I² > 50% at src/analysis/sensitivity_analysis.py
- [ ] T037 [US3] Create forest plot generator for pooled effect sizes at src/analysis/forest_plots.py with plot library (matplotlib/seaborn) and output format (PNG at publication-quality resolution, PDF for publication)
- [ ] T039 [US3] Create Q-test for heterogeneity significance at src/analysis/q_test.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates at docs/methods.md with specific content sections (power analysis methodology, motion exclusion rates, dataset counts, preprocessing params)
- [ ] T041 [P] Code cleanup and refactoring across src/analysis/*.py files to remove duplicate imports and add type hints (function signatures, return types)
- [ ] T042 Performance optimization for NBS permutation testing on 2 cores with success criteria: runtime <2h on 2 cores for 10 subjects
- [ ] T045 Security hardening for API key handling at src/config/env.py with.env file validation and key rotation
- [ ] T047 Create final report template with associational framing and dataset gap documentation at docs/final_report.md
- [ ] T046 Run quickstart.md validation to ensure all FRs are addressed and generate docs/fr_traceability.md mapping each FR to implementation location
- [ ] T048 Implement reproducibility checklist verification (random seeds, Docker hashes, data checksums) at src/utils/reproducibility_check.py
- [ ] T059 [P] Flag spec/plan misalignment for kickback: Document that spec.md:FR-003 (Yeo atlas) conflicts with Constitution Principle VI (AAL atlas) and plan.md:Power analysis (a priori) conflicts with spec.md:FR-010 (post-hoc) at docs/kickback_notes.md with severity=HIGH and required amendments listed

**⚠️ KICKBACK REQUIRED**: The following plan-spec misalignments require amendment before implementation:
- spec.md:FR-003 mandates Yeo 7-network atlas, but Constitution Principle VI requires AAL atlas. Spec requires amendment.
- plan.md specifies a priori power analysis, but spec.md FR-010 requires post-hoc power analysis. Plan requires amendment.
- T059 (document alignment meta-task) removed from tasks.md and flagged for kickback to plan stage.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 preprocessing output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 effect size output

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
- **Atlas Choice**: AAL atlas per Constitution Principle VI (spec.md:FR-003 flagged for amendment - currently mandates Yeo)
- **Motion Thresholds**: >3mm translation or >3° rotation for exclusion (sensitivity analysis 2/3/4mm)
- **Statistical Methods**: Fisher-z with AR(1) or permutation (10k), NBS (t≥3.1, α=0.05), bootstrapped CIs (10k)
- **Framing**: All findings must be associational, not causal (FR-009)
- **Power Analysis**: Post-hoc per spec FR-010 (plan.md specifies a priori - requires amendment)