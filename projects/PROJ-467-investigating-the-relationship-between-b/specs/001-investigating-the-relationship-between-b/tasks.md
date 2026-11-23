# Tasks: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Tactile Discrimination

**Input**: Design documents from `/specs/001-investigating-the-relationship-between-b/`
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

- [ ] T001 Create project structure: `mkdir -p src/brainnet tests/unit tests/contract data/processed data/raw results/figures metadata contracts`
- [ ] T002 Initialize Python 3.11 project with dependencies: `numpy`, `pandas`, `nilearn`, `networkx`, `scikit-learn`, `statsmodels`, `pingouin`, `datasets`, `pytest`, `jsonschema`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black/isort) tools
- [X] T004 [P] Create `requirements.txt` with pinned versions (e.g., `nilearn==0.10.*`)
- [ ] T005 [P] Setup `.gitignore` for data artifacts and Python cache

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Implement `src/brainnet/utils.py`: Seed handling (`np.random.seed(42)`), logging setup, and memory profiling decorators
- [ ] T007 [P] Create `contracts/raw_dataset.schema.yaml` and `contracts/network_metric.schema.yaml` per `data-model.md`
- [ ] T008 [P] Implement `src/brainnet/preprocessing.py`: Motion correction, band-pass filtering (0.01–0.1 Hz) using `nilearn`
- [ ] T009 [P] Implement `src/brainnet/preprocessing.py`: ROI extraction using Schaefer-200 atlas (scale=200)
- [ ] T010 [P] Create `src/brainnet/__init__.py` exposing `run_all`, `validate`, and `analyze` entry points

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Data Pipeline and Variable Validation (Priority: P1) 🎯 MVP

**Goal**: Load HCP dataset, validate tactile score presence, and ensure data completeness (≥95% subjects).

**Independent Test**: Run `python -m brainnet.data_loader` with `--max-subjects 100` and verify it exits with a success code (if tactile found) or an error code with a specific error message (if tactile missing).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: While TDD requires writing tests first, these tasks are listed here to execute after the implementation code exists.

- [ ] T011 [P] [US1] Contract test for `raw_dataset.schema.yaml` validation in `tests/contract/test_data_loader.py`
- [ ] T012 [P] [US1] Unit test for tactile score absence detection in `tests/unit/test_data_loader.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `src/brainnet/data_loader.py`: Function to download HCP via `datasets.load_dataset` from verified HF URL. **Constraint**: Must fail loudly if the `tactile_score` column is missing; do NOT fall back to synthetic data or alternative datasets. **Specifics**: Use dataset ID `7eu7d7/HCP-Diffusion-datas` and file `HCP_RestingState.parquet`. **Exit Behavior**: If `tactile_score` is missing, raise `ValueError` with exact message: `Dataset validation failed: Standard HCP Young Adult dataset does NOT include tactile discrimination measures. Resolution required: Manually provide a custom dataset containing both fMRI and tactile measures. The pipeline cannot automatically switch datasets.` and exit with code 1.
- [ ] T014 [US1] Implement `src/brainnet/data_loader.py`: Function `validate_tactile_presence()` that checks for `tactile_score` column. **If missing**: Raise `ValueError` with exact message: `Dataset validation failed: Standard HCP Young Adult dataset does NOT include tactile discrimination measures. Resolution required: Manually provide a custom dataset containing both fMRI and tactile measures. The pipeline cannot automatically switch datasets.`
- [ ] T015 [US1] Implement `src/brainnet/data_loader.py`: Function `validate_completeness()` to compute missing value rates. Validates subject count matches the selected dataset documentation (expected N≈1200±50 for HCP or N≈1000±100 for alternative/custom). Generates `data/processed/subject_count_validation.json` or halts with specific error if mismatch.
- [ ] T016 [US1] Implement `src/brainnet/data_loader.py`: Function to load tactile instrument metadata from the loaded dataset. **Constraint**: Read the DOI from the dataset's metadata. If the DOI is missing or invalid, fallback to the standard Weinstein DOI (`10.1016/j.neuropsychologia.2011.04.012`) and log a warning. Do NOT raise an error if the metadata is missing, as long as the dataset passed T014 validation.
- [ ] T018 [US1] Generate `data/processed/completeness_report.json` with subject counts, missing rates, and validation status

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Network Dynamics Computation (Priority: P2)

**Goal**: Compute static and dynamic network metrics (modularity, segregation, flexibility) within ≤3 hours for ≤100 subjects and ≤6.5GB RAM.

**Independent Test**: Run `python -m brainnet.static_metrics` and `dynamic_metrics` on a sample of 50 subjects; verify runtime <2h, memory <6GB, and output files conform to schemas.

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `src/brainnet/static_metrics.py`: Compute Pearson correlation matrix (200x200) from ROI time series
- [ ] T022 [US2] Implement `src/brainnet/static_metrics.py`: Graph construction with absolute correlation threshold ≥0.2; compute Modularity Q (Louvain) and Segregation Index
- [ ] T023 [P] [US2] Implement `src/brainnet/dynamic_metrics.py`: Sliding-window logic (length=60s, step=30s) using Numba or efficient NumPy loops
- [ ] T024 [US2] Implement `src/brainnet/dynamic_metrics.py`: Compute dynamic modularity time-series (Louvain per window)
- [ ] T025 [US2] Implement `src/brainnet/dynamic_metrics.py`: Compute Flexibility metric (count of community changes per node across windows) per research.md
- [ ] T026 [US2] Implement memory profiling in `src/brainnet/dynamic_metrics.py` to ensure peak RAM <6.5GB; log scaling behavior (O(n²))
- [ ] T026b [US2] Implement runtime validation in `src/brainnet/dynamic_metrics.py`: Measure wall-clock time for the full pipeline on ≤100 subjects. If time exceeds 3 hours, log a critical warning and flag the run as "timeout risk".
- [ ] T027 [US2] Save static metrics to `data/processed/static_metrics.parquet` and dynamic series to `data/processed/dynamic_metrics.npz`
- [ ] T028 [US2] Generate `metadata/static_metrics.json` and `metadata/dynamic_metrics.json` with parameters (window length, threshold, atlas)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4b: Diagnostics (Blocking Prerequisite for US3)

**Purpose**: Compute collinearity diagnostics and prepare data for analysis. Must run before Phase 5.

- [ ] T029 [Diag] Implement `src/brainnet/analysis.py`: Compute VIF for all predictors; flag if VIF > 5.0. **Logic**: If VIF > 5.0, identify the predictor with the highest VIF, remove it, and recompute VIFs. Repeat until VIF ≤ 5.0 or no predictors remain. **Output**: If VIF > 5.0 persists, flag the result for "descriptive framing" in the final report and record the change in correlation coefficient when high-VIF predictors are removed.
- [ ] T029b [Diag] Implement `src/brainnet/analysis.py`: **Conditional**: If VIF > 5.0 persists after removal loop in T029, identify the predictor set for PCA.
- [ ] T029c [Diag] Implement `src/brainnet/analysis.py`: **Conditional**: Perform PCA on the remaining predictor set, retain components explaining ≥90% variance, save `data/processed/pca_components.parquet`.
- [ ] T029d [Diag] Implement `src/brainnet/analysis.py`: **Conditional**: If PCA was performed in T029c, flag the analysis in the report and log the variance explained.
- [ ] T029e [Diag] Implement `src/brainnet/analysis.py`: **Benchmark Validation**: Compute Modularity Q and Segregation Index on a small subset of the *actual loaded real data* (e.g., first 10 subjects from the HCP or alternative dataset). Expected physiological range for HCP Modularity Q is 0.3-0.7. Log any deviations from expected ranges. **Constraint**: Use ONLY the actual dataset loaded by T013; do NOT use synthetic or generated data. **Guard**: Skip if T014 validation failed (tactile data missing).
- [ ] T029f [Diag] Implement `src/brainnet/analysis.py`: **Scaling Validation**: Verify O(n^2) memory scaling by running the metric computation on three specific subsets of the *actual loaded real data*: n=10, n=50, and n=100 subjects. Log peak RAM for each run and verify the ratio of memory usage matches the theoretical square of the subject count ratio within a 10% tolerance. **Constraint**: Use ONLY the actual dataset loaded by T013; do NOT use synthetic or generated data. **Guard**: Skip if T014 validation failed (tactile data missing).

**Checkpoint**: Diagnostics complete; ready for Phase 5.

---

## Phase 5: User Story 3 - Associational Correlation Analysis (Priority: P3)

**Goal**: Run correlational analyses (raw and adjusted) with FDR correction, power analysis, sensitivity sweeps, and PCA fallback.

**Independent Test**: Run `python -m brainnet.analysis` on the CI subset; verify output includes FDR-corrected p-values, power estimates, and sensitivity stability metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for FDR correction logic in `tests/unit/test_analysis.py`
- [ ] T031 [P] [US3] Unit test for power analysis calculation in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement `src/brainnet/analysis.py`: A priori power analysis (Pingouin) for r=0.20, α=0.05, power=0.80 (Wikipedia: Power (statistics), https://en.wikipedia.org/wiki/Power_(statistics)); flag if N < required
- [ ] T033 [US3] Implement `src/brainnet/analysis.py`: Compute raw Pearson correlations between each predictor and `tactile_score`
- [ ] T034 [US3] Implement `src/brainnet/analysis.py`: Compute partial correlations adjusting for age, sex, mean FD, scanner ID
- [ ] T035 [US3] Implement `src/brainnet/analysis.py`: Apply Benjamini-Hochberg FDR (q≤0.05) to all ≥5 hypothesis tests
- [ ] T036 [US3] Implement `src/brainnet/analysis.py`: Sensitivity sweep across thresholds {, 0.05, 0.1}; compute correlation coefficient stability (CV) for each threshold.
- [ ] T037 [US3] Implement `src/brainnet/analysis.py`: **Conditional**: If `data/processed/pca_components.parquet` exists, compute partial correlations (controlling for age/sex) between tactile scores and retained component scores. Save results to `results/pca_correlations.csv`.
- [ ] T038 [US3] Implement `src/brainnet/analysis.py`: Enforce associational language (FR-004); scan output strings for causal terms ('causes', 'determines', 'effect', 'leads to') and raise error if found.
- [ ] T039 [US3] Generate `results/correlation_results.csv` with raw/adjusted r, p, q-values, power estimates, and CI status
- [ ] T040 [US3] Generate `results/sensitivity_report.json` with threshold sweep results and stability metrics
- [ ] T041 [US3] Generate `results/vif_report.json` with VIF values, removal steps, and PCA variance explained (if applicable)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Artifacts (Polish)

**Purpose**: Assemble final reports, validate contracts, and ensure reproducibility.

- [ ] T042 [P] Implement `src/brainnet/report.py`: Assemble `results/report.md` with sections for data completeness, runtime, power, VIF, and correlations
- [ ] T043 [P] Implement `src/brainnet/report.py`: Generate LaTeX tables for manuscript export
- [ ] T044 [P] Implement `tests/contract/test_network_schema.py`: Validate all output files against `contracts/*.schema.yaml`
- [ ] T045 [P] Generate `results/figures/` (scatter plots, modularity time-series) as SVG/PNG
- [ ] T046 [P] Update `quickstart.md`: Add section detailing `--max-subjects` flag usage and expected runtime for CI runs.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048a [P] Documentation: Create `docs/api.md` with function signatures for `data_loader`, `static_metrics`, `dynamic_metrics`, `analysis`.
- [ ] T048b [P] Documentation: Create `docs/analysis_guide.md` explaining statistical methods (VIF, PCA, FDR).
- [ ] T048c [P] Documentation: Update `README.md` with project overview and quickstart links.
- [ ] T049b [P] Refactoring: Standardize error handling in `src/brainnet/analysis.py` using custom exceptions.
- [ ] T050a [P] Performance: Implement Numba optimization for sliding-window loop in `src/brainnet/dynamic_metrics.py`.
- [ ] T050b [P] Performance: Run benchmark on CI subset (100 subjects) and verify runtime reduction of at least 50% compared to the unoptimized version in T023.
- [ ] T051a [P] Testing: Add unit tests for VIF logic in `tests/unit/test_analysis.py`.
- [ ] T051b [P] Testing: Add unit tests for PCA logic in `tests/unit/test_analysis.py`.
- [ ] T052a [P] Security: Add input sanitization to `src/brainnet/data_loader.py` to prevent path traversal.
- [ ] T052b [P] Security: Validate file paths in `src/brainnet/report.py` to ensure they stay within `results/`.
- [ ] T053a [P] Validation: Run `python -m brainnet.run_all --max-subjects 100 --seed 42` and verify exit code 0.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T007 (Contracts) MUST complete before T008/T009 (Preprocessing)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Diagnostics (Phase 4b)**: Must complete before Phase 5 (Analysis)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data loading
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for metrics AND Diagnostics (Phase 4b) for VIF/PCA

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T006, T010) can run in parallel (T007 must finish before T008/T009)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for raw_dataset.schema.yaml validation in tests/contract/test_data_loader.py"
Task: "Unit test for tactile score absence detection in tests/unit/test_data_loader.py"

# Launch all models for User Story 1 together:
Task: "Implement src/brainnet/data_loader.py: Function to download HCP"
Task: "Implement src/brainnet/data_loader.py: Function validate_tactile_presence()"
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
4. Add Diagnostics (Phase 4b) → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: Diagnostics (Phase 4b)
 - Developer D: User Story 3
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