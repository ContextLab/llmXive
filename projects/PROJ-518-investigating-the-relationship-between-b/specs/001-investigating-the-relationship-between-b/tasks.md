# Tasks: Investigating the Relationship Between Brain Network Dynamics and Creative Problem Solving

**Input**: Design documents from `/specs/518-brain-dynamics-creativity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY where defined by spec acceptance criteria.

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

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create project structure per implementation plan (`mkdir -p projects/PROJ-518-investigating-the-relationship-between-b/code projects/PROJ-518-investigating-the-relationship-between-b/tests projects/PROJ-518-investigating-the-relationship-between-b/data/raw projects/PROJ-518-investigating-the-relationship-between-b/data/processed projects/PROJ-518-investigating-the-relationship-between-b/data/interim projects/PROJ-518-investigating-the-relationship-between-b/docs/outputs`). <!-- FAILED: unspecified -->
- [X] T002 Initialize Python 3.10 project with pinned `requirements.txt` containing `nilearn==0.10.0`, `networkx==3.2.1`, `scikit-learn==1.4.2`, `numpy==1.26.4`, `pandas==2.2.2`, `matplotlib==3.8.4`, `scipy==1.12.0`, `brainconn==0.1.0`.
- [X] T003 [P] Configure linting (flake8/black) by creating `.flake8` and `pyproject.toml` with appropriate sections.

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T004 Setup data directory structure (`mkdir -p data/raw data/processed data/interim docs/outputs`).
- [X] T005 [P] Implement `code/config.py` with a `Config` dataclass containing `WINDOW_SIZES = [20,30,40]`, `STEP = 5`, `ATLAS_PATH`, `DATA_PATH`, and load from `.env` if present.
- [X] T006 [P] Setup `code/utils/logging.py` with function `log_exclusion(reason: str, subject_id: str)` that appends CSV rows to `data_exclusion_log.txt`.
- [X] T007 Create `code/utils/versioning.py` with `hash_file(path: str) -> str` and `update_state_file()` that writes SHA‑256 hashes to `state/projects/PROJ-518...yaml`.
- [X] T008 Configure error handling: define `class DataMissingCreativityError(Exception)` in `code/errors.py`.
- [X] T009 Setup environment configuration management (`code/config.py` as above).

## Phase 2.5: Critical Pre‑Conditions (User Story 4 – Priority: P1) 🚨 BLOCKER

- [X] T033 Implement `validate_caq_availability(manifest_path: str, behavioral_path: str) -> bool` in `code/data/loader.py` that checks for the CAQ field and raises `DataMissingCreativityError` with the missing field name if absent.
- [X] T036 Ensure validation runs as a pre‑condition by calling `validate_caq_availability` at the start of `code/main.py` before any data loading.
- (T034 merged into T033 – the exception raised halts execution with error code `DATA_MISSING_CREATIVITY`.)

## Phase 3: User Story 1 – Compute Network Flexibility and Test Association (Priority: P1) 🎯 MVP

### Tests (MANDATORY)

- [ ] T010 [P] [US1] Contract test `tests/contract/test_loader.py::test_loader_raises_on_missing_caq` asserting `DataMissingCreativityError` is raised when CAQ is missing.
- [ ] T011 [P] [US1] Integration test `tests/integration/test_pipeline_flow.py::test_end_to_end_correlation` runs the full pipeline on a mock subset and asserts numeric `r` and `p` values.

### Implementation

- [ ] T012 [P] [US1] Implement `code/data/loader.py` function `fetch_hcp_data(subject_id: str)` that downloads raw fMRI and behavioral JSON **after** validation succeeds.
- [X] T013 [P] [US1] Implement `code/data/preprocess.py` function `preprocess_fmri(input_path: str, output_path: str)` performing motion correction, spatial normalization, and **band‑pass filtering within a low-frequency range** using Nilearn.
- [X] T014 [US1] Implement `code/analysis/connectivity.py` function `compute_sliding_window_connectivity(fmri_data: np.ndarray, window_size: int, step: int)` reading `WINDOW_SIZES` and `STEP` from `config.py`.
- [ ] T014.1 [US1] Implement `code/analysis/connectivity.py` function `compute_static_connectivity_strength(fmri_data: np.ndarray) -> float` that calculates the mean of absolute pairwise correlations **from the full‑window static matrix** per participant.
- [X] T015 [US1] Implement `code/analysis/dynamics.py` function `detect_communities(connectivity_matrix: np.ndarray, gamma: float = 1.0) -> List[int]` using Louvain with **γ = 1.0**.
- [X] T016 [US1] Implement `code/analysis/dynamics.py` function `calculate_flexibility(community_labels: List[List[int]]) -> float` that counts ROI community changes **and averages across ROIs** to produce the whole‑brain metric.
- [X] T051 [US1] Implement `code/analysis/statistics.py` function `fit_regression(flexibility: np.ndarray, creativity: np.ndarray, covariates: dict) -> RegressionResult` using `statsmodels` OLS to fit the full model `creativity ~ network_flexibility + age + sex + education + static_connectivity_strength`.
- [~] T017 [US1] Within `fit_regression`, compute and **report Pearson correlation coefficient** between flexibility and creativity.
- [ ] T017.1 [US1] Implement baseline model `creativity ~ static_connectivity_strength + covariates`, compute ΔR², and **format ΔR² to an appropriate level of precision** via `format_delta_r2(delta_r2: float) -> str`.
- [~] T018 [US1] Add `validate_and_filter_subjects(subjects: List[Participant]) -> List[Participant]` in `loader.py` to skip missing scans (log warning) and missing behavioral scores (exclude + log) **after** validation.
- [~] T019 [US1] Add `filter_by_motion(subjects: List[Participant], fd_thresh: float = 0.5, vol_thresh: float = 0.2) -> List[Participant]` to exclude participants exceeding motion criteria and log the exclusion.
- [~] T020 [US1] Ensure `log_exclusion` is called with standardized reason codes (`MISSING_SCAN`, `MISSING_SCORE`, `HIGH_MOTION`) for every exclusion decision.

## Phase 4: User Story 2 – Generate Diagnostic Visualisations (Priority: P2)

### Tests

- [X] T021 [P] [US2] Contract test `tests/contract/test_plots.py::test_plot_functions_exist`.

### Implementation

- [~] T022 [P] [US2] Implement `code/viz/plots.py` function `plot_flexibility_vs_creativity(flexibility, creativity, output_path='docs/outputs/flexibility_vs_creativity.png')` that creates a scatter plot with regression line and a confidence band, saves as **`flexibility_vs_creativity.png`**.
- [~] T023 [US2] Implement `code/viz/plots.py` function `plot_residuals(model: RegressionResult, residuals_path='docs/outputs/model_residuals.png', qq_path='docs/outputs/model_qq.png')` that generates residuals‑vs‑fitted and QQ plots, saving as **`model_residuals.png`** and **`model_qq.png`**.
- [~] T057 [US2] After each plot is saved, call `compress_image(path, max_mb=5.0)` to enforce **≤ 5 MB** file size (SC‑004).
- [~] T058 [US2] Add error handling in plot functions to skip NaN data points, log warnings, and continue (robustness for missing data).

## Phase 5: User Story 3 – Perform Permutation‑Based Significance Testing & Sensitivity Sweep (Priority: P3)

### Tests

- [~] T026 [P] [US3] Contract test `tests/contract/test_permutation.py::test_permutation_counts`.

### Implementation

- [~] T027 [P] [US3] Implement `run_permutation_test(flexibility, creativity, n_permutations=10000) -> float` that shuffles **creativity scores only** (preserving the flexibility vector) and returns an empirical two‑tailed p‑value.
- [~] T045 [US3] Implement `apply_fwe_correction(p_values: List[float], method='max-t') -> List[float]` using the **max‑T permutation method**.
- [~] T046 [US3] Implement `run_sensitivity_analysis(flexibility, creativity, window_lengths=[20,30,40]) -> pd.DataFrame` that returns a table with columns `window_length`, `correlation`, `p_value`.
- [ ] T030 [US3] Save permutation results to `data/interim/permutation_results.csv` and sensitivity summary to `data/interim/sensitivity_summary.csv` with explicit column headers.
- [~] T031 [US3] Verify the sensitivity DataFrame includes `correlation` and `p_value` for each window length (SC‑005).
- [~] T060 [US3] Profile and optimise `run_permutation_test` (vectorised NumPy) to complete **≤ 6 hours** on 2 CPU cores and < 7 GB RAM.

## Phase N: Polish & Cross‑Cutting Concerns

- [~] T037 [P] Documentation updates in `README.md` and `docs/outputs/` describing each generated artifact and their filenames.
- [~] T038 Code cleanup and refactoring using `black` and `flake8`.
- [~] T039 Performance optimisation across all stories (profiling, memory usage < 7 GB).
- [~] T040 [P] Additional unit tests for `calculate_flexibility`, `fit_regression`, and `run_permutation_test`.
- [ ] T041 Security hardening: run `safety check` on `requirements.txt` and update vulnerable packages.
- [ ] T042 Run `quickstart.md` commands in a fresh virtualenv and verify successful completion.
- [ ] T043 Implement `format_delta_r2(delta_r2: float) -> str` returning a string with **four decimal places**; integrate into regression output.
- [ ] T044 Verify SC‑003: ΔR² is reported with precision of at least 4 decimal places (uses T043).
- [ ] T045 (already defined) Family‑wise error correction using max‑T method.
- [ ] T046 (already defined) Sensitivity analysis table generation.
- [ ] T047 Ensure all plots saved with exact filenames per spec (flexibility_vs_creativity.png, model_residuals.png, model_qq.png).
- [ ] T048 Ensure image compression enforces ≤ 5 MB limit (calls `compress_image`).

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **Critical Pre‑Conditions (Phase 2.5)** → **User Stories (Phase 3‑5)** → **Polish (Phase N)**
- Tasks T018/T019 now explicitly depend on successful completion of Phase 2.5 (validation) and are listed under Phase 2.5 for correct ordering.
- T012 runs **after** T033 validation succeeds (ordering clarified).
- All [P] tasks can run in parallel within their phase.
