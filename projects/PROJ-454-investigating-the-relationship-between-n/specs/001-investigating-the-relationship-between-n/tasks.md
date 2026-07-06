# Tasks: Neural Entropy and Cognitive Flexibility in Aging

**Input**: Design documents from `/specs/001-neural-entropy-cognitive-flexibility/`
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

- [ ] T001 [P] Initialize project structure: Create directories `code/`, `data/raw/`, `data/processed/`, `data/interim/`, `tests/`, `specs/` and create `code/requirements.txt` with **pinned versions** (e.g., `mne==1.6.0`, `statsmodels==0.14.0`) for mne, statsmodels, numpy, pandas, pyyaml, requests, scikit-learn, numba, jsonschema to satisfy Constitution Principle I (Reproducibility)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `utils/resource_monitor.py` to log RAM/Disk usage and enforce <7GB RAM / <14GB Disk limits
- [ ] T005 [P] Implement `utils/entropy_utils.py` with CPU-optimized Sample Entropy and Approximate Entropy algorithms (no CUDA, float64 precision)
- [ ] T006 [P] Setup `utils/stats_utils.py` for Partial Pearson Correlation, Multiple Linear Regression (OLS), and FDR correction (Benjamini-Hochberg). **Note**: Bonferroni is excluded from setup as it is only used for secondary validation.
- [ ] T007 Create base data schemas in `specs/001-neural-entropy-cognitive-flexibility/contracts/` (`dataset.schema.yaml`, `entropy_output.schema.yaml`, `correlation_results.schema.yaml`, `output.schema.yaml`)
- [ ] T008 Configure logging infrastructure to track data flow and exclusion reasons
- [ ] T009 Setup environment configuration management for dataset URLs and thresholds

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - EEG Data Pipeline and Entropy Computation (Priority: P1) 🎯 MVP

**Goal**: Download OpenNeuro datasets, preprocess EEG, compute entropy metrics, and ensure data quality.

**Independent Test**: Can be fully tested by running the preprocessing pipeline on a subset of EEG data and verifying that entropy values are computed for all 5 frequency bands with no NaN outputs for valid participants.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for `dataset.schema.yaml` validation in `tests/contract/test_dataset_schema.py`
- [ ] T011 [P] [US1] Unit test for entropy calculation stability (no NaN/Inf) in `tests/unit/test_entropy.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_download_data.py`: Fetch OpenNeuro datasets (ds, ds), verify metadata contains 'wcst_perseverative_errors' and 'age >= 50', verify variable fit. **Input**: OpenNeuro API. **Output**: `data/raw/` parquet files with checksums. (FR-001, FR-010, FR-011)
- [ ] T012b [US1] Extract and convert behavioral scores from `data/raw/` parquet files to `data/processed/behavioral_scores.csv`. **Input**: `data/raw/`. **Output**: `data/processed/behavioral_scores.csv`. (Ordering Fix: T020/T020a dependency)
- [ ] T013 [US1] Implement `code/02_preprocess_eeg.py`: Bandpass (low-frequency cutoff), Notch (50/60Hz), Bad channel interpolation, ICA artifact removal, s non-overlapping epochs. **Input**: `data/raw/`. **Output**: `data/processed/` epoched data. (FR-002, US-1)
- [ ] T014 [US1] Implement SNR calculation in `code/02_preprocess_eeg.py`: Calculate **Median SNR of preprocessed data relative to 1-45 Hz band power** (per SC-001). **Input**: `data/processed/` epoched data. **Output**: `data/processed/snr_metrics.json`. (SC-001, FR-002)
- [ ] T016 [US1] Add data quality checks to `code/02_preprocess_eeg.py`: Exclude participants with <60s valid EEG, >20% corrupted segments, **OR SNR < 5dB** (consuming T014 output). **Input**: `data/raw/`, `data/processed/snr_metrics.json`. **Output**: `data/processed/exclusion_log.csv`. (Edge Cases, SC-001)
- [ ] T015 [US1] Implement `code/03_compute_entropy.py`: Compute **both** Sample Entropy and Approximate Entropy for Delta, Theta, Alpha, Beta, Gamma bands. **Include both in primary output**. **Input**: `data/processed/` epoched data. **Output**: `data/processed/entropy_metrics.csv`. (FR-003, FR-012)
- [ ] T017 [US1] Add resource monitoring calls in `02_preprocess_eeg.py` and `03_compute_entropy.py` to ensure <7GB RAM usage. **Input**: Running scripts. **Output**: `logs/resource_usage.log`. (FR-008)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Perform Partial Pearson Correlation (Spec FR-004) with covariates and FDR correction (Spec FR-005). Include OLS and Bonferroni as secondary validation.

**Independent Test**: Can be fully tested by running the correlation pipeline on computed entropy values and behavioral scores, verifying that p-values are FDR-corrected and effect sizes (partial r) are reported with 95% confidence intervals.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for `correlation_results.schema.yaml` in `tests/contract/test_correlation_schema.py`
- [ ] T019 [P] [US2] Unit test for FDR correction logic in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [ ] T020a [US2] Implement `code/04_regression_analysis.py`: Perform **Partial Pearson Correlation** between Entropy metrics and WCST perseverative errors, controlling for age, education, task accuracy. **Input**: `data/processed/entropy_metrics.csv`, `data/processed/behavioral_scores.csv`. **Output**: `data/processed/correlation_results_partial.csv`. (FR-004, Edge Cases, SC-002)
- [ ] T020b [US2] Implement **Multiple Linear Regression (OLS)** between Entropy metrics and WCST errors as **exploratory deviation** (per Plan). **Input**: `data/processed/entropy_metrics.csv`, `data/processed/behavioral_scores.csv`. **Output**: `data/processed/correlation_results_ols.csv`. (Plan: OLS)
- [ ] T021 [US2] Implement Benjamini-Hochberg FDR correction in `code/04_regression_analysis.py` for all tests (Multiple bands × 2 entropy measures) on `correlation_results_partial.csv`. **Explicitly reference FR-012** if test count is reduced due to collinearity. **Input**: `data/processed/correlation_results_partial.csv`. **Output**: `data/processed/correlation_results_fdr.csv`. (FR-005, FR-012, SC-002)
- [ ] T022 [US2] Implement Bonferroni correction in `code/04_regression_analysis.py` on `correlation_results_partial.csv` as **secondary validation** (per Constitution Principle VII). **Input**: `data/processed/correlation_results_partial.csv`. **Output**: `data/processed/correlation_results_bonferroni.csv`. (Constitution: Principle VII)
- [ ] T023 [US2] Calculate effect sizes (partial r) and classify (≥ 0.3 = clinically meaningful) in `code/04_regression_analysis.py`. **Input**: `data/processed/correlation_results_fdr.csv`. **Output**: `data/processed/effect_sizes.json`. (SC-002)
- [ ] T024 [US2] Generate acknowledgement log stating that "Power analysis sample size requirements are deferred to implementation with explicit acknowledgement" as per Spec Assumptions. **Input**: Running script. **Output**: `logs/power_analysis.log`. (Spec Assumptions)
- [ ] T025 [US3] Add explicit "Associational" disclaimer and covariate control summary to final report. **Input**: `data/processed/`. **Output**: `logs/methodology_notes.md`. (FR-009, SC-005, Plan: Constitution Amendment Request)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Reporting (Priority: P3)

**Goal**: Conduct sensitivity analyses (exclusions, threshold sweeps) and generate final reproducible report.

**Independent Test**: Can be fully tested by running the sensitivity pipeline on the same dataset with exclusion criteria applied and verifying that headline correlation rates are compared across exclusion scenarios.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Integration test for full pipeline reproducibility in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement sensitivity analysis in `code/04_regression_analysis.py` excluding participants with neurological conditions/medications. **Input**: `data/processed/correlation_results_fdr.csv` (from T021), `data/processed/behavioral_scores.csv`. **Output**: `data/processed/sensitivity_exclusion_results.csv`. (FR-006)
- [ ] T028 [US3] Implement threshold sensitivity sweep in `code/04_regression_analysis.py`. **Primary**: Sweep over **absolute differences** {0.0, 0.05, 0.1} as required by Spec FR-007. **Secondary**: Optional relative sweep. **Input**: `data/processed/entropy_metrics.csv`, `data/processed/correlation_results_fdr.csv`. **Output**: `data/processed/sensitivity_threshold_results.csv`. (FR-007)
- [ ] T029 [US3] Generate `sensitivity_report.json` comparing results across exclusion scenarios and threshold sweeps. **Required fields**: scenario, r_value, p_value, n_excluded. **Input**: `data/processed/sensitivity_exclusion_results.csv`, `data/processed/sensitivity_threshold_results.csv`. **Output**: `data/processed/sensitivity_report.json`. (SC-003)
- [ ] T030 [US3] Implement `code/05_generate_report.py` to produce final report with correlation matrices, effect sizes, **FDR-corrected p-values (primary)**, Bonferroni (secondary), and sensitivity comparisons. **Explicitly state that FDR correction was used to satisfy Spec FR-005**. **Input**: `data/processed/`. **Output**: `reports/final_report.md`. (FR-007, SC-003)
- [ ] T031 [US3] Add explicit "Associational" disclaimer and covariate control summary to final report. **Input**: `reports/final_report.md`. **Output**: `reports/final_report.md` (updated). (FR-009, SC-005)
- [ ] T032a [US3] Validate **CSV data artifacts** (`correlation_results_partial.csv`, `correlation_results_fdr.csv`) against `correlation_results.schema.yaml` using `jsonschema validate` command. **Input**: `data/processed/`. **Output**: `logs/validation_log.csv.txt`. (Contract Test)
- [ ] T032b [US3] Validate **JSON artifacts** (`sensitivity_report.json`) against `output.schema.yaml` using `jsonschema validate` command. **Input**: `data/processed/`. **Output**: `logs/validation_log.json.txt`. (Contract Test)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033a [P] Create `docs/diagrams/data_flow.png` illustrating data movement from raw to final report.
- [ ] T033b [P] Create `docs/methodology_notes.md` detailing processing steps and assumptions.
- [ ] T034 [P] Apply numba JIT compilation to `utils/entropy_utils.py` functions: `sample_entropy`, `approximate_entropy` for CPU optimization.
- [ ] T035 [P] Reduce peak memory in `code/02_preprocess_eeg.py` to <6GB via chunked loading verification.
- [ ] T036 [P] Additional unit tests for edge cases (NaN handling, short recordings) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure full pipeline completes within 6 hours on CI

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on entropy data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on regression results from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models (schemas) before services (scripts)
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
Task: "Contract test for dataset.schema.yaml validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for entropy calculation stability in tests/unit/test_entropy.py"

# Launch all implementation for User Story 1 together (models/scripts):
Task: "Implement code/01_download_data.py to fetch OpenNeuro datasets"
Task: "Implement code/02_preprocess_eeg.py: Filtering, ICA, epoching"
Task: "Implement code/03_compute_entropy.py: Sample/ApEn calculation"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (entropy values computed, no NaN, SNR check)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Correlations)
4. Add User Story 3 → Test independently → Deploy/Demo (Sensitivity/Report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Pipeline)
   - Developer B: User Story 2 (Regression)
   - Developer C: User Story 3 (Sensitivity/Report)
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
- **Constraint**: All tasks must run on CPU-only CI (limited core count, GB RAM, 14GB disk, 6h limit). No GPU, no 8-bit models.
- **Data Integrity**: No fake data. Use real OpenNeuro datasets with verified behavioral scores.
- **Methodology Note**: Primary hypothesis testing uses Partial Pearson (Spec FR-004) with FDR correction (Spec FR-005). OLS and Bonferroni are secondary/exploratory.
- **Spec-Plan Consistency Note**: Tasks T020a/T020b and T021/T022 implement both Spec and Plan requirements, with Spec requirements as primary.