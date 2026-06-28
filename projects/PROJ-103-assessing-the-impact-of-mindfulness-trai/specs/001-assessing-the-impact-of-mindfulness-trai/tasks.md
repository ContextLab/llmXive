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

- [ ] T001 Create project structure with exact directory tree: src/, tests/, data/, docs/ directories each containing __init__.py files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup Docker configuration for fMRIPrep container with CPU-limited settings
- [ ] T005 [P] Create data directory structure (data/raw/, data/processed/, data/results/)
- [ ] T006 [P] Setup logging infrastructure and QC report template in src/utils/logging.py
- [ ] T007 Create base configuration management in src/config/settings.py
- [ ] T008 Implement random seed pinning for reproducibility in src/utils/seeding.py
- [ ] T009 Setup environment variable management for dataset API keys in src/config/env.py
- [ ] T019 Implement post-hoc power analysis script using statsmodels.stats.power.TTestPower in src/analysis/power_analysis.py with sample-size requirements documentation (power ≥80% target) for methods output

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI datasets from OpenNeuro and run standardized preprocessing with fMRIPrep

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a single OpenNeuro dataset and verifying that fMRIPrep generates valid output files in expected MNI152 space

### Test Tasks for User Story 1

- [ ] T043 [P] [US1] Write unit tests for preprocessing pipeline in tests/unit/test_preprocessing.py (FAIL before implementation)

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement OpenNeuro API client for dataset discovery in src/datasets/openneuro_client.py
- [ ] T011 [US1] Create dataset download script with URL validation in src/datasets/download_datasets.py
- [ ] T012 [US1] Implement dataset design verification to confirm pre/post resting-state scans with mindfulness metadata in src/datasets/verify_design.py
- [ ] T013 [US1] Create fMRIPrep Docker runner script with --nthreads 2 --omp-nthreads 2 --mem-mb 6000 in src/preprocessing/fmriprep_runner.py
- [ ] T014 [US1] Implement motion parameter extraction from fMRIPrep output in src/preprocessing/extract_motion.py
- [ ] T015 [US1] Create motion exclusion filter (>3mm translation or >3° rotation) in src/preprocessing/motion_filter.py
- [ ] T016 [US1] Implement Nilearn lightweight preprocessing fallback (motion correction, slice timing, MNI152 normalization, 6mm smoothing, bandpass) in src/preprocessing/nilearn_fallback.py
- [ ] T017 [US1] Create fMRIPrep HTML report parser for quality control in src/preprocessing/qc_parser.py
- [ ] T018 [US1] Implement dataset-variable fit verification (pre/post scans, DMN node coordinates) and document results per FR-008 in src/datasets/verify_variables.py
- [ ] T020 [US1] Implement dataset gap logging and methods documentation for missing datasets in src/utils/gap_logging.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - DMN Functional Connectivity Analysis (Priority: P2)

**Goal**: Extract DMN time series, compute connectivity matrices, apply statistical corrections, and calculate effect sizes

**Independent Test**: Can be fully tested by running the connectivity analysis on a single preprocessed dataset and verifying that correlation matrices, Fisher transformations, and NBS-corrected p-values are output

### Test Tasks for User Story 2

- [ ] T044 [P] [US2] Write unit tests for connectivity analysis in tests/unit/test_connectivity.py (FAIL before implementation)

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement Yeo 7-network atlas DMN region extraction (PCC, mPFC, IPL, angular gyrus) per spec FR-003 in src/analysis/extract_dmn_rois.py
- [ ] T022 [US2] Create time series extraction from MNI152 normalized BOLD images in src/analysis/extract_timeseries.py
- [ ] T023 [US2] Implement Pearson correlation matrix computation between all DMN node pairs in src/analysis/correlation_matrix.py
- [ ] T024 [US2] Create Fisher z-transformation with AR(1) prewhitening in src/analysis/fisher_z_transform.py
- [ ] T025 [US2] Implement permutation testing (10,000 iterations) as alternative to AR(1) in src/analysis/permutation_test.py
- [ ] T026 [US2] Create paired t-test for pre vs. post connectivity across subjects in src/analysis/paired_tests.py
- [ ] T027 [US2] Implement bootstrapped 95% CI calculation (10,000 iterations) for Cohen's d in src/analysis/effect_sizes.py
- [ ] T028 [US2] Implement Network-Based Statistic (NBS) correction with primary threshold t≥3.1 and component-wise family-wise error correction at α=0.05 in src/analysis/nbs_correction.py
- [ ] T030 [US2] Create associational framing validator to prevent causal claims in output reports per FR-009 in src/utils/associational_framing.py
- [ ] T031 [US2] Implement sensitivity analysis for motion thresholds (2mm, 3mm, 4mm) in src/analysis/motion_sensitivity.py
- [ ] T032 [US2] Create results summary table generator with effect sizes and p-values in src/analysis/results_summary.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Dataset Meta-Analysis (Priority: P3)

**Goal**: Perform random-effects meta-analysis across ≥3 datasets with heterogeneity assessment

**Independent Test**: Can be fully tested by running the meta-analysis script on ≥3 datasets with computed effect sizes and verifying that pooled effect size, confidence interval, and heterogeneity metrics are output in forest plot format

### Test Tasks for User Story 3

- [ ] T058 [P] [US3] Write unit tests for meta-analysis script in tests/unit/test_meta_analysis.py (FAIL before implementation)

### Implementation for User Story 3

- [ ] T033 [US3] Create R metafor package integration wrapper in src/analysis/metafor_wrapper.R
- [ ] T034 [US3] Implement random-effects meta-analysis across datasets in src/analysis/meta_analysis.py
- [ ] T035 [US3] Create I² heterogeneity statistic calculation in src/analysis/heterogeneity.py
- [ ] T036 [US3] Implement leave-one-out sensitivity analysis for I² > 50% in src/analysis/sensitivity_analysis.py
- [ ] T037 [US3] Create forest plot generator for pooled effect sizes in src/analysis/forest_plots.py
- [ ] T038 [US3] Implement dataset scarcity contingency (single-dataset reporting if <3 datasets) gating logic in src/analysis/dataset_contingency.py
- [ ] T039 [US3] Create Q-test for heterogeneity significance in src/analysis/q_test.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in docs/methods.md with power analysis methodology and motion exclusion rates
- [ ] T041 Code cleanup and refactoring across src/analysis/*.py to remove duplicate imports and add type hints
- [ ] T042 Performance optimization for NBS permutation testing on 2 cores with success criteria: runtime <2h on 2 cores for 10 subjects
- [ ] T045 Security hardening for API key handling in src/config/env.py with .env file validation and key rotation
- [ ] T046 Run quickstart.md validation to ensure all FRs are addressed and generate docs/fr_traceability.md mapping each FR to implementation location
- [ ] T047 Create final report template with associational framing and dataset gap documentation in docs/final_report.md
- [ ] T048 Implement reproducibility checklist verification (random seeds, Docker hashes, data checksums) in src/utils/reproducibility_check.py

**⚠️ NOTE**: Plan-spec-task misalignment flagged for kickback:
- Plan.md and Constitution Principle VI mandate AAL atlas, but spec.md FR-003 and tasks require Yeo 7-network atlas. Spec is source of truth; plan requires amendment.
- Plan.md specifies a priori power analysis (d=0.5), but spec.md FR-010 requires post-hoc power analysis. Spec is source of truth; plan requires amendment.

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
Task: "Implement OpenNeuro API client for dataset discovery in src/datasets/openneuro_client.py"
Task: "Create data directory structure (data/raw/, data/processed/, data/results/)"
Task: "Setup logging infrastructure and QC report template in src/utils/logging.py"
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
- **Compute Feasibility**: All tasks must run on GitHub Actions free tier (limited CPU resources, 7GB RAM, 6h max)
- **Dataset URLs**: OpenNeuro datasets at https://openneuro.org/datasets must be verified before download
- **Atlas Choice**: Yeo 7-network atlas per spec FR-003 (plan-spec misalignment flagged - plan requires amendment)
- **Motion Thresholds**: >3mm translation or >3° rotation for exclusion (sensitivity analysis 2/3/4mm)
- **Statistical Methods**: Fisher-z with AR(1) or permutation (10k), NBS (t≥3.1, α=0.05), bootstrapped CIs (10k)
- **Framing**: All findings must be associational, not causal (FR-009)
- **Power Analysis**: Post-hoc per spec FR-010 (plan-spec misalignment flagged - plan requires amendment)