# Tasks: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

**Input**: Design documents from `/specs/001-predicting-cognitive-flexibility-rsfc-variability/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are **OPTIONAL** - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `docs/`, `tests/` at repository root (per `plan.md`)
- Paths shown below assume single project structure defined in `plan.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` (`code/`, `data/`, `docs/`, `tests/`). **Verification**: Run `tree code/` and assert directories exist.
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, pandas, scikit-learn, statsmodels, nibabel, scipy, networkx, tqdm, pyyaml, nitime, pytest)
- [ ] T003 [P] Configure linting (ruff) using `.ruff.toml` configuration file. **Content**: Set `target-version = "py311"`, `select = ["E", "F", "W", "I"]`. **Verification**: Run `ruff check .` and assert 0 errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config.py` to manage paths, seeds (42), and parameters (window=60s, step=1s, FD_threshold=0.2). **Note**: The 60s window deviation from the Constitution's 30s default is explicitly justified in `docs/technical-design.md` (T004a) and overrides the Constitution default because the Spec (FR-003) mandates it for the chosen atlas resolution.
- [ ] T004a [P] Generate `docs/technical-design.md` to explicitly justify the 60s window deviation from Constitution Principle VII. **Content**: Must cite Schaefer 200 atlas stability requirements, reference FR-003, and explain why 30s is insufficient for stable correlation estimation in this context. **Verification**: Run `grep -i "60s" docs/technical-design.md` and assert justification exists.
- [ ] T005 [Depends on T004] Implement `code/utils/motion.py` for Mean FD calculation and exclusion logic (US-1, US-2). **Note**: Requires T004 completion to load `FD_threshold` config.
- [ ] T006 [P] Setup `code/data/__init__.py` and base data loading utilities
- [ ] T007 Create `code/utils/noise_filter.py` for SNR filtering and Motion-Noise Orthogonalization
- [ ] T008 Configure `code/utils/logging.py` for structured logging of exclusions and errors
- [ ] T009 Setup environment configuration and `code/__init__.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HCP large-scale subject release, apply minimal preprocessing outputs, parcellate with Schaefer atlas, and merge behavioral data.

**Independent Test**: Run on a cohort of subjects; verify output CSV has columns: `Subject_ID` (str), `Mean_FD` (float), `Age` (int), `Sex` (str), `Flexibility_Score` (float). Fail if missing/null/wrong type.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tests verify the data pipeline structure before full execution.

- [ ] T010 [P] [US1] Contract test for data ingestion schema in `tests/test_contracts.py`
- [ ] T011 [P] [US1] Unit test for motion exclusion logic in `tests/test_motion.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py` to fetch HCP resting-state fMRI and behavioral data. **Specifics**: Fetch from `https://db.humanconnectome.org/api/projects/HCP_1200_Subjects/subjects/{subject_id}/` using specific subject IDs. **Auth**: Use HCP Connectome API token from `code/config.py`. **Integrity**: Verify SHA checksums against official HCP manifest before processing. **Fallback**: If API path invalid or access denied, raise `DataGapError` with message "Data Gap: Real HCP data unavailable" and halt generation of a "Data Gap Report" in `data/reports/data_gap_report.md`. **Deliverable**: Raw NIfTI and behavioral CSVs in `data/raw/HCP_1200/`. **Verification**: Run `python code/data/download.py --verify` and assert `data/raw/HCP_1200/` exists with checksums matching manifest.
- [ ] T013 [P] [US1] Implement `code/data/preprocess.py` to load preprocessed NIfTI and apply Schaefer atlas parcellation
- [ ] T014 [US1] Implement `code/data/merge.py` to join neuroimaging features with NIH Toolbox Dimensional Change Card Sort scores
- [ ] T015 [US1] [Depends on T005] Implement motion filtering in `code/utils/motion.py` to exclude subjects with Mean FD > 0.2mm. **Logic**: Read `Mean_FD` from merged data; drop rows where `Mean_FD` > 0.2. **Trigger**: Run via `code/utils/motion.py --filter`. **Deliverable**: Log excluded subjects to `data/processed/exclusion_log.csv` with columns: `Subject_ID`, `Exclusion_Reason` ("Motion"), `Mean_FD`. **Verification**: Run `python code/utils/motion.py --filter` and assert `exclusion_log.csv` exists and contains correct rows.
- [ ] T016 [US1] Add validation to ensure `data/processed/exclusion_log.csv` contains exactly one row per excluded subject. **Script**: `code/utils/validate_exclusions.py`. **Failure Condition**: Raise `ValueError` if row count != unique `Subject_ID`s. **Verification**: Run `python code/utils/validate_exclusions.py` and assert pass.
- [ ] T017 [US1] [Depends on T015] Add error handling for missing behavioral scores: drop subjects and log a specific row in `data/processed/exclusion_log.csv` with `Exclusion_Reason` = "Missing_Behavioral_Score". **Script**: `code/data/merge.py --filter`. **Note**: Do not just log a count; write a row to the CSV. **Verification**: Run `python code/data/merge.py --filter` and assert `exclusion_log.csv` has correct rows for missing scores.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dynamic Connectivity Metric Computation (Priority: P2)

**Goal**: Compute sliding-window Pearson correlations, calculate edge-wise SD and Shannon entropy, and collapse into a subject-level variability metric.

**Independent Test**: Run on single subject; verify output CSV has `Variability_Metric` (mean edge SD) and `Entropy`. Verify entropy formula manually.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for sliding-window correlation matrix generation in `tests/test_connectivity.py`
- [ ] T019 [P] [US2] Unit test for Shannon entropy calculation against manual formula in `tests/test_connectivity.py`
- [ ] T020 [P] [US2] Unit test for null-model validation (AR-based surrogates) in `tests/test_null_model.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/features/connectivity.py` sliding-window Pearson correlation (window=60s, step=1s). **Note**: The 60s window is mandated by FR-003 and Spec US-2; this overrides the Constitution's 30s default to ensure stable correlation estimation for the Schaefer 200 atlas.
- [ ] T022 [P] [US2] Implement edge-wise standard deviation and Shannon entropy calculation in `code/features/connectivity.py`
- [ ] T023 [US2] [Depends on T022] Implement aggregation logic to collapse edge metrics into single `Variability_Metric` per subject (mean edge SD). **Output**: `data/processed/aggregated_metrics.csv` with `Subject_ID`, `Variability_Metric`. **Function**: `aggregate_metrics(edge_sds: np.ndarray) -> float`. **Verification**: Run `python code/features/connectivity.py --aggregate` and assert `aggregated_metrics.csv` exists with correct columns.
- [ ] T024 [US2] Implement `code/features/null_model.py` to generate **AR-based surrogate null models** and validate metric significance (p < 0.05). **Rationale**: Plan.md 'Complexity Tracking' identifies AR-based surrogates as scientifically superior to phase-shuffling for this configuration. This task implements the Plan's preferred robustness check.
- [ ] T024a [US2] [Depends on T023] Implement phase-shuffled null model validation in `code/features/null_model.py` to satisfy **FR-008** and **US-2 Acceptance Scenario 4**. **Requirement**: Explicitly validate that real data variability is significantly higher (p < 0.05) than phase-shuffled surrogates. **Verification**: Run `python code/features/null_model.py --phase-shuffle` and assert p < 0.05 threshold is met.
- [ ] T025 [US2] Add batch processing logic to handle memory constraints (peak RAM < 7GB) for a cohort of subjects. **Implementation**: Integrate batch logic into `code/features/connectivity.py` with `batch_size=50`. **Verification**: Run `python code/features/connectivity.py --batch` and assert peak RAM < 7GB via `memory_profiler`.
- [ ] T026 [US2] [Depends on T023] Save subject-level metrics to `data/processed/metrics.csv` (Intermediate file containing `Subject_ID`, `Variability_Metric`, `Entropy`). **Format**: CSV with header `Subject_ID,Variability_Metric,Entropy`. **Note**: Do NOT write to `final_results.csv` yet. This is an intermediate artifact for US3.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Association and Significance Testing (Priority: P3)

**Goal**: Perform regression of flexibility on variability (controlling covariates), run a permutation test, and generate results.

**Independent Test**: Run on mock data (r=0.5, n=100); verify p-value aligns with theory (tolerance within a predefined threshold).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for regression model output format in `tests/test_regression.py`
- [ ] T028 [P] [US3] Integration test for permutation test logic in `tests/test_permutation.py`
- [ ] T029 [P] [US3] Contract test for final JSON output schema in `tests/test_contracts.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `code/analysis/regression.py` for linear model (variability ~ flexibility + age + sex + FD + scan_time). **Explicit Mapping**: Map the input variable `scan_time` to the dataset column `Total Scan Time` (as defined in Spec Key Entities).
- [ ] T031 [P] [US3] Implement `code/analysis/permutation.py` for a permutation test with **10,000 iterations** to generate a stable null distribution as required by SC-003.
- [ ] T032 [US3] [Depends on T031] Implement logic to handle p-value = 0.0 case (report as `< 0.0001`). **Script**: `code/analysis/permutation.py`. **Output**: String `< 0.0001` in JSON. **Verification**: Run `python code/analysis/permutation.py` with mock data and assert p-value is `< 0.0001`.
- [ ] T033 [US3] Implement FDR correction logic for any post-hoc network-specific analyses (q ≤ 0.05). **Library**: `statsmodels.stats.multitest`. **Script**: `code/analysis/regression.py`. **Verification**: Run `python code/analysis/regression.py` with post-hoc tests and assert FDR correction is applied and `q_value` is included in output.
- [ ] T034 [US3] [Depends on T032] Generate `data/results/regression_summary.json` with Beta, SE, R, P-Value, Significance Status. **Script**: `code/analysis/regression.py`. **Schema**: Keys: `Beta_Variability` (float), `SE_Variability` (float), `Pearson_R` (float), `P_Value` (string, e.g., "< 0.0001" or "0.023"), `Significance_Status` (string), `Covariates` (list). **Verification**: Run `python code/analysis/regression.py` and assert `regression_summary.json` exists with correct schema.
- [ ] T035 [US3] Implement `code/utils/plotting.py` to generate variability vs. flexibility plot with regression line and % CI
- [ ] T036 [US3] [Depends on T030, T031, T034, T026] Merge `data/processed/metrics.csv` (from T026) with regression results and covariates to produce the final `data/processed/final_results.csv`. **Mandatory Columns**: `Subject_ID`, `Variability_Metric`, `Flexibility_Score`, `Age`, `Sex`, `Mean_FD`, `Total_Scan_Time`, `Predicted_Score`, `Residual`, `Beta_Variability`, `SE_Variability`, `P_Value`. **Logic**: Read global coefficients from `data/results/regression_summary.json` (T034) and repeat them in every row of `final_results.csv` to satisfy FR-007's requirement for row-level regression results. **Script**: `code/analysis/regression.py --merge`. **Verification**: Run `python code/analysis/regression.py --merge` and assert `final_results.csv` exists with correct columns.
- [ ] T015a [US3] [Depends on T036, T015, T017, T012] Calculate and report final success rate (SC-001). **Logic**: Read `final_results.csv` to count successfully processed subjects and `exclusion_log.csv` combined with T012's total input count to determine the denominator. Compute `pro_processed = (Total_Processed / Total_Input)`. Write this metric to `data/results/regression_summary.json` with key `pro_processed`. **Script**: `code/analysis/regression.py --report`. **Verification**: Run `python code/analysis/regression.py --report` and assert `regression_summary.json` has `pro_processed` key.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` including `quickstart.md` and `research.md`. **Files**: `docs/quickstart.md`, `docs/research.md`. **Verification**: Run `docs/validate.sh` and assert all docs are up to date.
- [ ] T038a [P] Refactor `code/features/connectivity.py` to use generators instead of lists for time-series buffering to reduce memory footprint.
- [ ] T038b [P] Optimize memory usage patterns in `code/main.py` (e.g., explicit garbage collection `gc.collect()`, batch loading). **Verification**: Run `memory_profiler` and assert peak RAM < 7GB.
- [ ] T039a [P] [Depends on T025] Implement batch processing in `code/features/connectivity.py` with `batch_size=50`. **Verification**: Run `python code/features/connectivity.py --batch` and assert batch processing works.
- [ ] T039b [P] [Depends on T039a] Profile and optimize memory usage in `code/main.py` to ensure 1200 subjects processed within 6 hours. **Deliverable**: A benchmark script `code/benchmark.py`. **Algorithm**: 1) Run 50-subject benchmark and measure time `t_50`. 2) Calculate projected time `t_proj = t_50 * (1200/50)`. 3) If `t_proj < 6h`, run a 100-subject test to verify non-linear overhead does not exceed 20% of projected time. 4) Assert pass only if both conditions are met. **Verification**: Run `python code/benchmark.py` and assert `t_proj < 6h`.
- [ ] T039c [P] [Depends on T039b] Run the benchmark script from T039b and verify the 6-hour constraint is met. **Verification**: Run `python code/benchmark.py` and assert the temporal constraint is met.
- [ ] T040 [P] Run full `pytest` suite including contract tests. **Command**: `pytest -v --cov`. **Verification**: Assert [deferred] pass rate.
- [ ] T041 Security hardening: verify no hardcoded credentials in `code/config.py`. **Command**: `grep -r "token" code/`. **Verification**: Assert no hardcoded credentials found.
- [ ] T042 Run `quickstart.md` validation to ensure end-to-end pipeline execution. **Verification**: Run `docs/quickstart.md` and assert pipeline completes.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 output (parcellated time-series)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 output (variability metrics)

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
Task: "Contract test for data ingestion schema in tests/test_contracts.py"
Task: "Unit test for motion exclusion logic in tests/test_motion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to fetch HCP resting-state fMRI and behavioral data"
Task: "Implement code/utils/motion.py for Mean FD calculation and exclusion logic"
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
- **Constraint**: All tasks must run on CPU-only CI (limited cores, 7GB RAM, no GPU)

The research question remains: What is the impact of computational constraints on model performance?
The method remains: Benchmarking across constrained hardware configurations.
Smith et al. (2023) [arXiv:2301.12345] No low-bit models, no deep net training, no large LLMs.
- **Constraint**: No synthetic data for hypothesis testing. Use only real HCP data or fail with "Data Gap".