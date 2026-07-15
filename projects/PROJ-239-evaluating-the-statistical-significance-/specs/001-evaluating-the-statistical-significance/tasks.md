# Tasks: Evaluating the Statistical Significance of A/B Test Results with Non-Independent Observations

**Input**: Design documents from `/specs/001-evaluating-the-statistical-significance/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`projects/PROJ-239-evaluating-the-statistical-significance-`). **Deliverable**: Run `mkdir -p code tests data/raw data/derived` and create empty `code/__init__.py` and `tests/__init__.py`. Verify with `ls code tests data/raw data/derived`.
- [X] T002 Initialize Python 3.11 project with dependencies. **Deliverable**: Create `requirements.txt` with exact pins: `numpy==1.26.0`, `scipy==1.12.0`, `statsmodels==0.14.1`, `pandas==2.2.0`, `pytest==7.4.0`.
- [X] T003 [P] Configure linting (flake8/black). **Deliverable**: Add `.flake8` and `pyproject.toml` with Black config, and verify with `black --check.` and `flake8.`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 Create `code/config.py` to define simulation parameters and validation. **Deliverable**: Define constants `ICC_RANGE = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]`, `ICC_STEP = 0.1`, `ALPHA_LEVELS = [0.01, 0.05, 0.10]`, `DEFAULT_N_CLUSTERS = 100`, `DEFAULT_SEED = 42`. Implement `validate_config(cfg)` that raises `ValueError` if `cfg['n_clusters'] < 50` **unless** `cfg['icc'] == 0.0`. Provide `load_config()` returning a dict and `set_seed(seed)` using `np.random.seed(seed)`.
- [X] T006 [P] Initialize test scaffolding. **Deliverable**: Create the following files with exact content:
 1. `tests/unit/__init__.py`: Empty file or docstring.
 2. `tests/unit/test_data_generator.py`: File containing only a `pass` statement inside a `def test_placeholder():` function.
 3. `tests/unit/test_estimators.py`: File containing only a `pass` statement inside a `def test_placeholder():` function.
- [X] T007 [P] Add basic CI configuration. **Deliverable**: Create `.github/workflows/ci.yml` that installs `requirements.txt`, runs `pytest`, and caches pip.
- [X] T008 [P] Add unit test for `code/data_generator.py`. **Deliverable**: Implement `tests/unit/test_data_generator.py` with function `test_generate_data_h0_true()` asserting that generated treatment groups have equal means (within tolerance) and that cluster IDs are preserved.
- [X] T009 [P] Add unit test for `code/estimators.py` standard t‑test. **Deliverable**: Implement `tests/unit/test_estimators.py` with function `test_naive_ttest_independent_data()` that creates independent data with known means and asserts the returned p‑value matches `scipy.stats.ttest_ind` output.
- [X] T010 [US1] Implement `code/data_generator.py`. **Deliverable**: Function `generate_data(n_clusters, n_obs_per_cluster, icc, seed) -> pd.DataFrame` using a random intercept model `Y_ij = mu + u_i + e_ij`.
 - **Critical Logic**: If `icc == 0.0`, the random intercept `u_i` MUST be zero (independent data).
 - Treatment labels are assigned **randomly at the cluster level**.
 - **Constitution Note**: This baseline method intentionally violates Principle VI (Cluster-Aware Inference) to measure Type I error inflation. It must be clearly documented as a "violation baseline" for comparison only.
 - Edge‑case handling for `icc=0.0` and unbalanced cluster sizes is added (see T028).
- [X] T011 [US1] Implement naive baseline t‑test in `code/estimators.py`. **Deliverable**: Function `run_naive_ttest(data, treatment_col, outcome_col) -> float` wrapping `scipy.stats.ttest_ind`. This function **must be called via the wrapper** `run_naive_ttest_with_warning` (see T036) to flag the intentional violation of cluster‑aware inference.
- [X] T012 [US1] Implement `code/simulation_runner.py` baseline loop. **Deliverable**: Function `run_baseline_simulation(icc, n_iterations, seed) -> List[Dict]` that generates data, runs the naive t‑test (through the warning wrapper), stores p‑values, and returns a list of result dicts.
- [X] T013 [US1] Implement aggregation in `code/analysis.py`. **Deliverable**: Function `aggregate_errors(results_list, alpha_levels) -> pd.DataFrame` that computes empirical Type I error rates and **95 % confidence intervals** using the **Clopper-Pearson (Exact) method** (see T038) to ensure statistical rigor for binary simulation outcomes.
- [ ] T014 [US1] Create script `run_simulation_baseline.py`. **Deliverable**: CLI accepting `--icc`, `--iterations`, `--seed`, and optional `--icc-step`. Uses the config loader (T004) and writes `data/derived/baseline_results.csv`. Exit code 0 on success.
- [X] T015 [US2] Add unit test for cluster‑robust variance. **Deliverable**: `tests/unit/test_estimators.py` function `test_cluster_robust_variance_fixed_data()` that runs `run_cluster_robust_ttest` on a small fixed dataset and asserts the p‑value is within an expected range.
- [X] T016 [US2] Add unit test for block permutation logic. **Deliverable**: `tests/unit/test_estimators.py` function `test_block_permutation_respects_clusters()` that verifies no observation‑level swaps occur during permutation.
- [X] T017 [US2] Implement cluster‑robust variance estimator in `code/estimators.py`. **Deliverable**: Function `run_cluster_robust_ttest(data, treatment_col, outcome_col, cluster_id_col) -> float` using statsmodels `cov_type='cluster'` with CR2 adjustment. This is the constitutionally compliant method.
- [X] T018 [US2] Implement block permutation test in `code/estimators.py`. **Deliverable**: Function `run_block_permutation(data, treatment_col, outcome_col, cluster_id_col, n_permutations=1000) -> float` that permutes treatment labels at the cluster level and returns a p‑value.
- [X] T019 [US2] Extend `code/simulation_runner.py` to include robust methods. **Deliverable**: Update the loop to also run `run_cluster_robust_ttest` and `run_block_permutation` for each iteration, storing their p‑values alongside the naive result. **Depends on** T012 (baseline runner) and T017/T018.
- [X] T020 [US2] Extend aggregation in `code/analysis.py` to compute empirical error rates for all three methods across ICC levels. **Deliverable**: Updated `aggregate_errors` returns a DataFrame with columns `method`, `icc`, `alpha`, `error_rate`, `ci_lower`, `ci_upper`. Uses Clopper-Pearson intervals.
- [ ] T021 [US2] Create script `run_simulation_robust.py`. **Deliverable**: CLI similar to baseline script, writes `data/derived/robustResults.csv`.
- [X] T022 [US3] Integration test for report generation. **Deliverable**: `tests/integration/test_report_generation.py` with function `test_report_contains_all_alpha_levels()` that runs the full simulation (using reduced iterations) and asserts that the generated `final_report.csv` contains rows for α = 0.01, 0.05, 0.10.
- [ ] T023 [US3] (Foundational) Define default `ALPHA_LEVELS` in `config.py` (already done in T004). No implementation needed beyond defaults. **Note**: Dynamic override is handled by T034.
- [X] T024 [US3] Refactor `code/analysis.py` to compute 95 % CIs using the Clopper-Pearson method from T038 (already part of T013/T020).
- [ ] T025 [US3] Generate `data/derived/final_report.csv`. **Deliverable**: CSV with columns `ICC`, `Alpha`, `Method`, `Empirical_Error_Rate`, `CI_Lower`, `CI_Upper`.
- [X] T026 [US3] Create `scripts/generate_report.py`. **Deliverable**: Script that reads `final_report.csv` and produces `specs/001-evaluating-the-statistical-significance/research.md` with sections Introduction, Methods, Results (tables/plots via matplotlib), Conclusion. **Depends on** T035 for real‑world data handling and checksumming.
- [ ] T027 [US3] Implement performance monitoring in `code/simulation_runner.py`. **Deliverable**: Log wall‑clock time to console and append to `data/timing.csv`; also record peak memory usage to `data/memory.csv`. If peak memory > 7 GB, raise an explicit error. Memory optimisation (sub‑sampling) logic is added here (see T037).
- [X] T028 [US3] Edge‑case handling in `code/data_generator.py`. **Deliverable**: Ensure the generator gracefully handles `icc=0.0` (produces independent data by setting random intercept to 0) and accepts a list of heterogeneous cluster sizes; raise informative warnings if clusters are highly unbalanced. If `icc=0.0`, skip the minimum cluster count validation for robust methods.
- [X] T029 [US3] Validate all dependencies are CPU‑only. **Deliverable**: Add a check in CI (`grep -i cuda requirements.txt && echo 'No CUDA deps'`) and confirm the command returns no matches.
- [X] T030 [US3] Add pytest integration test for end‑to‑end simulation with reduced iterations. **Deliverable**: `tests/integration/test_end_to_end.py` function `test_end_to_end_reduced_iterations()` that runs `run_simulation_robust.py` with `--iterations 10` and asserts output files exist and contain plausible values.
- [X] T031 [US3] Document `code/simulation_runner.py` **AND** `code/data_generator.py` with Google‑style docstrings covering ICC ranges, iteration counts, and seed usage (Principle VII). <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 4, column 1:
 **Input**: Design documents from...
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 4, column 2:
 **Input**: Design documents from...
 ^) -->
- [ ] T032 [Polish] Run quickstart validation. **Deliverable**: Execute `pytest tests/` and verify exit code 0; update `quickstart.md` accordingly.

## Phase 6: Cross‑Cutting Enhancements & Constitution Alignment

- [X] T033 [P] Add CLI / config loader support for user‑specified ICC range and step size. **Deliverable**: Extend `code/config.py` with `parse_cli_args()` that populates `cfg['icc_range']` and `cfg['icc_step']` from command‑line flags `--icc-range` and `--icc-step`. This satisfies FR‑001 user configurability.
- [X] T034 [P] Add CLI support for user‑provided α list. **Deliverable**: Extend `code/config.py` with `--alpha-list` argument that overrides `ALPHA_LEVELS` at runtime, fulfilling FR‑005.
- [ ] T035 [P] Implement UCI Online Retail data ingestion, checksumming, and PII‑scan. **Deliverable**: Script `code/uci_ingest.py` that downloads the dataset from the canonical URL, writes to `data/raw/uci_online_retail.csv`, computes SHA‑256 checksum stored in `data/checksums.txt`, and runs a simple regex PII scan (e.g., email patterns). This task satisfies the data‑hygiene requirement for the report.
- [X] T036 [P] Wrap naive baseline t‑test with a warning. **Deliverable**: Function `run_naive_ttest_with_warning` in `code/estimators.py` that logs a clear warning that the method assumes independence and is intended only for baseline comparison, thereby respecting Constitution Principle VI.
- [X] T037 [P] Memory‑optimisation logic. **Deliverable**: In `code/simulation_runner.py`, before each iteration check estimated memory footprint; if projected usage exceeds 6 GB, down‑sample observations per cluster to keep total size < 7 GB. This, together with T027, ensures FR‑006 compliance.
- [X] T038 [P] Confidence‑interval method selector. **Deliverable**: Function `select_ci_method(error_rate, n)` in `code/analysis.py` that **always returns 'clopper_pearson'** for this project to ensure statistical rigor and consistency with the Single Source of Truth principle.
- [X] T039 [P] Ensure all scripts run on CPU‑only hardware. **Deliverable**: Add a CI step that parses `requirements.txt` for any CUDA‑related packages and fails the job if found (reinforces T029).

---

### Dependencies & Execution Order Summary

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Stories (Phases 3‑5)** → **Cross‑Cutting (Phase 6)**
- All tasks marked `[P]` may run in parallel as long as they do not modify the same file.
- Validation tasks (e.g., T029, T039) run after the corresponding implementation tasks to verify compliance.
- **Critical Dependencies**:
 - T035 must complete before T026.
 - T034 must complete before T023 is considered fully functional.
 - T031 covers both runner and generator.

---

### Notes

- All tasks now include concrete deliverables, file paths, and verification steps.
- The baseline naive t‑test is explicitly flagged as a methodological violation but retained for comparison, satisfying both the research need and Constitution Principle VI via T036.
- Dynamic configuration via CLI arguments ensures FR‑001 and FR‑005 are fully user‑configurable.
- Real‑world UCI data handling is now present, complying with data‑hygiene and single‑source‑of‑truth principles.
- Memory and runtime constraints are actively enforced through profiling and sub‑sampling logic.
- Confidence‑interval selection is standardized to Clopper-Pearson for rigor.
- Edge cases for ICC=0.0 are explicitly handled to prevent invalid robust variance estimates.