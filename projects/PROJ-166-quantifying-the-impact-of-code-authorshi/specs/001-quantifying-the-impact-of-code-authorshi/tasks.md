# Tasks: Quantifying the Impact of Code Authorship Diversity on Software Security

**Input**: Design documents from `/specs/001-quantify-authorship-diversity-security/`
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan. Create the following directories and files: `code/`, `code/__init__.py`, `code/config.py`, `code/data/`, `code/data/__init__.py`, `code/analysis/`, `code/analysis/__init__.py`, `data/`, `data/raw/`, `data/processed/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `requirements.txt`, `README.md`.
- [X] T002 Initialize A Python project with pinned dependencies. Create `requirements.txt` with exact versions: `pandas==2.1.0`, `statsmodels==0.14.0`, `scikit-learn==1.3.0`, `requests==2.31.0`, `gitpython==3.1.37`, `pyyaml==6.0.1`, `numpy==1.24.0`, `scipy==1.11.0`, `pytest==7.4.0`.
- [X] T003 [P] Configure linting and formatting tools. Create `pyproject.toml` with `[tool.black]` (line-length=88) and `.flake8` (max-line-length=88, exclude=venv) files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with paths, constants, random seeds, and NVD/GitHub API configuration. **Constants**: Define `TARGET_MIN_STARS = 1000` (static, no dynamic fallback).
- [X] T005 [P] Setup data directory structure (`data/raw/`, `data/processed/`) and generate schema definitions in `contracts/`. **Deliverables**: Create `contracts/repo_metrics.schema.yaml` (defining columns: `url`, `primary_language`, `unique_authors`, `kloc`, `cve_count`, `project_age`, `release_count`) and `contracts/model_results.schema.yaml` (defining output structure for coefficients, SE, p-values, CIs).
- [X] T006 [P] Implement `code/data/generate_target_list.py` to fetch a **target list of 600 repos** via GitHub API. **Endpoint**: `. **Query Logic**: Construct query string dynamically using the static variable `TARGET_MIN_STARS` from `code/config.py` (default 1000). **Constraint**: Do NOT implement dynamic fallback logic (e.g., decrementing `min_stars`). If the result count < 500, log a CRITICAL error and abort. **Max Retries**: 3 attempts per query before failing. **Output**: `data/raw/target_list.csv` with columns `url`, `primary_language`, `stars`, `age`. **Verification**: Assert file exists and contains >=500 rows. [UNRESOLVED-CLAIM: c_481673f1 — status=not_enough_info]
- [X] T007 [P] Implement `code/data/download_nvd.py` to download, merge, and deduplicate NVD/CVE JSON feeds (historical range) with checksum verification. **Logic**: Download all yearly JSON files from the official NVD feed, merge them in-memory to deduplicate by CVE ID. **Output**: `data/raw/nvd_cve_merged.json.gz` and `data/raw/nvd_cve_merged.json.gz.sha256`.
- [X] T008 [US1] Implement `code/data/extract_github.py` to clone, parse, and merge metrics for each repo in `target_list.csv`. **Clone Strategy**: Enforce `--shallow-since=2015-01-01` for ALL repositories in the target list to satisfy Constitution VI and capture the required history window. Do NOT perform full clones. **Parse**: Use `git log --format=%ae` on the shallow clone to extract unique author emails. **Filter**: Identify unique authors by distinct email fields. **Do NOT filter authors based on line count** (preserve Constitution VI definition). **cloc**: Run `cloc --by-file` to calculate `kloc`. **Merge**: Combine `unique_authors`, `kloc`, and `primary_language`. **Constraints**: If a clone fails (repo deleted/private), **SKIP** that repo, log `WARNING`, and continue. Do NOT fall back to synthetic data. **Output**: `data/processed/github_raw_metrics.csv` (columns: `url`, `primary_language`, `unique_authors`, `raw_line_count`, `kloc`) and `data/processed/tmp_clone_paths.txt` (list of successful clone paths). **Dependencies**: Requires T006 (target list) to be complete.
- [X] T009 [P] Implement `code/data/merge_datasets.py` (Part 1: Merge) to join GitHub metrics with NVD CVE counts using exact URL matching. Output `data/processed/repo_metrics.csv` (columns: `url`, `primary_language`, `unique_authors`, `kloc`, `cve_count`, `project_age`, `release_count`).
- [X] T009b Implement `code/data/merge_datasets.py` (Part 2: Validation) to enforce **exact URL matching** as per FR-002. If a URL in the target list has no exact match in NVD, set `cve_count` to 0. Flag ambiguous matches (e.g., substring matches) in logs but do not merge them. **Dependencies**: T009 must be complete before this task runs.
- [X] T010a [P] Create unit test `tests/unit/data/test_download_nvd.py::test_nvd_checksum_verification`: Assert SHA256 matches expected value.
- [X] T010b [P] Create unit test `tests/unit/data/test_extract_github.py::test_author_count_calculation`: Mock git log output with lines: "Author A", "Author B", "Author A". Assert unique author count is non-trivial.
- [X] T010c [P] Create unit test `tests/unit/data/test_merge_datasets.py::test_url_matching`: Mock NVD data, assert exact match logic works and ambiguous matches are ignored.
- [X] T013 [P] [US1] Add logging in `code/data/merge_datasets.py` for skipped repositories and ambiguous NVD matches. Use `logging.WARNING` for skips and `logging.ERROR` for ambiguous matches. Log format: `"[REPO_URL] Reason: <reason>"`. Write to `logs/merge_warnings.log`.
- [X] T014 [P] [US1] Implement a validation function in `code/data/merge_datasets.py` that checks `repo_metrics.csv` for null values in `kloc` and `cve_count`. **Behavior**: If nulls are found in `kloc` (cloc failure), **log a WARNING** and exclude the row from analysis (do not crash). If `cve_count` is missing, set it to **0** (do not crash). **Output**: A cleaned `data/processed/repo_metrics_clean.csv` with no nulls in critical columns.
- [X] T030 [P] Implement parallel processing in `code/data/extract_github.py` using `multiprocessing` with `max_workers=2` (to match CI CPU limit) and a memory limit check (abort if RAM > 6GB). Ensure pipeline processes ≥500 repos within 6 hours. [UNRESOLVED-CLAIM: c_5b7e9308 — status=refuted] **Dependencies**: Requires T006 (target list) to be complete.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Construction and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest a defined set of public GitHub repositories, extract commit metadata to calculate unique contributors, compute lines of code (KLOC), and retrieve associated vulnerability records from the NVD/CVE database to form the primary analysis dataset.

**Independent Test**: Execute the data pipeline script on a small, fixed seed of repositories (first alphabetically) and verify the output CSV contains non-null values for `unique_authors`, `kloc`, `cve_count`, and `primary_language` for all entries.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py`. Validate columns and types.
- [X] T012 [US1] Integration test for full pipeline on 5-repo seed in `tests/integration/test_data_pipeline.py`. Run T006->T007->T008->T009 and assert output file exists with correct data.

### Implementation for User Story 1

- [X] T015 [Removed: Placeholder not needed]

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Inference (Priority: P2)

**Goal**: Fit a multivariate Poisson or Negative-Binomial GLM predicting vulnerability counts from author counts and control variables, using `log(kloc)` as a **free predictor** (per Plan guidance to avoid bias) and output coefficient estimates, p-values, and confidence intervals.

**Independent Test**: Run the analysis script on a static, pre-generated CSV of a representative sample size. and verify the output JSON includes an `author_count_coefficient` with a non-null standard error and a 95% confidence interval.

### Tests for User Story 2

- [X] T016 [P] [US2] Contract test for model results schema in `tests/contract/test_model_results.py`.
- [X] T017 [US2] Implement `code/analysis/fit_models.py` to fit a Negative-Binomial GLM. **Response**: `cve_count`. **Predictors**: `author_count` + controls (`project_age`, `C(primary_language)`, `release_count`). **Size Adjustment**: Use `log(kloc)` as a **free predictor** (covariate), NOT an offset, per Spec Amendment and Plan.md. **Formula**: `cve_count ~ author_count + project_age + C(primary_language) + release_count + np.log(kloc)`. **Model Selection**: Before fitting the final model, perform a Likelihood Ratio Test (LRT) comparing a Poisson GLM to a Negative Binomial GLM. **LRT Implementation**: Use `statsmodels.stats.diagnostic.likelihood_ratio_test` or manual calculation of `2 * (logLik_NB - logLik_Poisson)` with `scipy.stats.chi2` (df=1). Verify the dispersion parameter is significantly > 1. If not, log a warning but proceed with Negative Binomial as per spec. **Exclusions**: Exclude rows where `kloc` <= 0. **Diagnostics**: Calculate VIF for all predictors. **Output**: `data/processed/model_results_raw.json` containing: `author_count_coefficient`, `std_err`, `p_value` (raw, uncorrected), `ci_95_lower`, `ci_95_upper`, `vif` (dict), `convergence_status` (boolean). **Parameters**: Use `family=sm.families.NegativeBinomial()` and `link=sm.families.links.log()`. **Flagging**: If model fails to converge, log `ERROR` and set `convergence_status` to false. **Dependencies**: T009 (repo_metrics.csv) and T014 (repo_metrics_clean.csv) must be complete.
- [X] T018 [US2] (Merged into T017)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Checks and Sensitivity Analysis (Priority: P3)

**Goal**: Perform robustness checks including subsampling by programming language and a sensitivity analysis using an alternative diversity metric (Shannon entropy) to ensure findings are not artifacts of a single metric choice.

**Independent Test**: Run the robustness script and verify it produces separate regression results for at least two distinct language subsamples (e.g., Python and JavaScript) and one alternative diversity metric.

### Tests for User Story 3

- [X] T019 [P] [US3] Contract test for robustness results schema in `tests/contract/test_robustness_results.py`.
- [X] T020 [P] [US3] Integration test for subsample and entropy analysis in `tests/integration/test_robustness.py`.

### Implementation for User Story 3

- [X] T021 [US3] Implement `code/analysis/robustness.py` (Part 1: Subsampling) to perform subsampling by language: filter `primary_language == 'Python'` and `primary_language == 'JavaScript'`. **Verification**: Assert at least 2 languages have >10 rows. [UNRESOLVED-CLAIM: c_aac33303 — status=refuted] **Re-fit GLM** using the same predictors as T017 (including `log(kloc)` as a free predictor). **Fallback**: If fewer than 2 languages have >10 rows, log a WARNING and proceed with only the qualifying languages. **Output**: Save raw p-values to `data/processed/robustness_subsample_pvalues.csv` with columns `language`, `coefficient`, `std_err`, `p_value_raw`, `n_rows`. **Note**: Do NOT apply BH correction here; raw p-values will be aggregated in T023. **Dependencies**: T017 must be complete.
- [X] T022 [US3] Implement `code/analysis/robustness.py` (Part 2: Shannon Entropy) to calculate Shannon entropy: `H = -sum(p_i * ln(p_i))` where `p_i = author_commits / total_commits` (handle log(0) by adding epsilon=1e-9). **Re-fit GLM** using entropy as the primary predictor instead of `author_count`. **Report the difference** as `abs(coefficient_entropy - coefficient_author_count)`. **Output**: Save raw p-values to `data/processed/robustness_entropy_pvalues.csv` with columns `model_type`, `coefficient`, `std_err`, `p_value_raw`, `coefficient_diff`. **Note**: Do NOT apply BH correction here; raw p-values will be aggregated in T023. **Dependencies**: T017 must be complete.
- [X] T023 [US3] Implement `code/analysis/robustness.py` (Part 3: Global BH Correction) to aggregate **ALL** raw p-values: from `model_results_raw.json` (T017), `robustness_subsample_pvalues.csv` (T021), and `robustness_entropy_pvalues.csv` (T022). Apply a **single** Benjamini-Hochberg correction to this combined set as mandated by FR-006. **Field Mapping**: Extract `p_value` from `model_results_raw.json`; extract `p_value_raw` from the CSV files. Update `data/processed/robustness_results.json` with adjusted p-values for all tests. **Output**: Final JSON containing all coefficients, raw p-values, and adjusted p-values. **Dependencies**: T017, T021, T022 must be complete. **Note**: This task is NOT parallel-safe.
- [X] T024 [US3] Generate `data/processed/robustness_results.json` containing subsample coefficients, entropy model results, and adjusted p-values.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T025a [P] Update `README.md`: Add a CLI usage section with example commands.
- [X] T025b [P] Update `README.md`: Add a "Methods" section explaining the GLM free predictor approach.
- [X] T025c [P] Update `README.md`: Add a "Data" section describing the pipeline.
- [X] T026 Code cleanup and refactoring: Extract `parse_git_log` and `run_cloc` into separate modules in `code/data/utils.py` to ensure modularity.
- [X] T027a [P] Create benchmark harness `tests/unit/test_performance_harness.py`. **Purpose**: Create the infrastructure to measure time and success rate. **Output**: A script that can be invoked by CI to run the full pipeline. **Dependencies**: None (harness creation).
- [X] T027b [CI] Execute benchmark on full dataset in CI environment. **Purpose**: Verify SC-001 (≥500 repos within 6 hours). **Input**: Must use `data/raw/target_list.csv`. **Precondition**: Assert `target_list.csv` contains >= 500 rows. **Criteria**: 1) Total execution time must be <= 6 hours. [UNRESOLVED-CLAIM: c_b178d2e2 — status=not_enough_info] 2) Success rate >= 95% (i.e., <= 5% of repos skipped due to errors) **on the full 500+ repo dataset** to verify SC-001. **Output**: JSON with `total_time_seconds`, `total_repos`, `successful_repos`,`success_rate`. **Pass/Fail**: Fail if either time or success rate thresholds are not met. **Note**: This is a CI integration task, not a unit test.
- [X] T028a [P] Create unit test `tests/unit/analysis/test_zero_kloc_exclusion`: Verify rows with kloc=0 are excluded.
- [X] T028b [P] Create unit test `tests/unit/analysis/test_empty_nvd_match`: Verify cve_count=0 when no match found.
- [X] T029 [P] Update `code/config.py` to use `os.getenv` for API keys.
- [X] T030 [P] Add test `tests/unit/test_config_no_leak.py` to verify no API keys are logged.
- [X] T031 [P] Create CI script `scripts/validate_quickstart.sh` that executes the pipeline on the seed dataset and exits 0 on success.
- [X] T032 [Removed: Scope Optimization] Task T032 (lagged variable analysis) has been removed. While the Plan mentions it as a recommended robustness check, it is not mandated by the Spec's Functional Requirements. It is deprioritized to focus on core FRs for this iteration.
- [X] T033 [Removed: Scope Creep] Task T033 (interaction term analysis) has been removed. The Spec (FR-001 to FR-007) does not explicitly mandate interaction terms. This task was an unverified plan addition and is removed to prevent scope creep.

---

## Phase 7: Revision & Compliance Fixes (Addressing Analysis Findings)

**Purpose**: Address specific concerns raised by the `/speckit.analyze` review regarding data integrity, model robustness, and CI constraints.

### Implementation for Revision

- [ ] T034 [P] [Revision] Implement `code/analysis/robustness.py` (Part 4: Lagged Variable Analysis). **Purpose**: Address Plan.md requirement for mitigating reverse causality. **Logic**: Calculate `author_count_lag_1year` (authors from 2015-2019) and `cve_count_lag_1year` (CVEs from 2015-2019). **Model**: Fit a full Negative Binomial GLM using these lagged variables as predictors (same formula structure as T017 but with lagged inputs). **Output**: Save results to `data/processed/robustness_lagged_results.json` with coefficients, p-values, and a note on the lagged period. **Dependencies**: Requires T008 (extract_github.py) and T017 (fit_models.py) base scripts to exist. **Constraint**: Do NOT reduce this to a simple correlation check; a full GLM is required.
- [X] T035 [P] [Revision] Implement `code/analysis/fit_models.py` collinearity check: Add a VIF (Variance Inflation Factor) calculation step **before** model fitting. **Logic**: Calculate VIF for `author_count` and `kloc`. If VIF > 5.0 for any predictor, **log a WARNING** and proceed with the model but flag the result in `model_results_raw.json` with `high_collinearity_warning: true`. Do NOT remove variables or alter the model formula to force a pass; the analysis must report the actual statistical state.
- [X] T036 [P] [Revision] Implement `code/analysis/robustness.py` subsampling guard: Add a check in T021 to verify that each language subsample has sufficient statistical power (n >= 30). If a language group has < 30 rows, **log a WARNING** and exclude that specific subsample from the final `robustness_results.json` with a reason `insufficient_sample_size`. Do NOT run the GLM on undersampled groups.
- [X] T037 [P] [Revision] Update `code/config.py` to enforce a **hard timeout** of 5.5 hours for the entire pipeline execution (leaving 30 mins buffer for CI overhead). **Logic**: Use `signal.alarm` (Linux) or a `threading.Timer` watchdog (non-Linux) to abort the process if `time.time() - start_time > 19800` seconds. **Output**: If timeout occurs, write a `pipeline_timeout.json` file and exit with code 1. This ensures compliance with SC-001 (6h limit) without partial/corrupted results.
- [ ] T038 [Removed: Replaced by T034] Task T038 (minimal lagged variable check) has been removed and replaced by T034 (full Lagged GLM) to meet Plan requirements.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on completion of Phase 2 and initial failure analysis (T034-T038 address specific analysis findings)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on `repo_metrics.csv` from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on `model_results.json` from US2
- **Revision Tasks (T034-T038)**: Can be implemented in parallel with each other, but depend on the existence of the base scripts in T008, T017, T021.

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
- All Revision tasks (Phase 7) marked [P] can run in parallel as they affect different files/modules
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for full pipeline on 5-repo seed in tests/integration/test_data_pipeline.py"

# Launch all data extraction tasks for User Story 1 together:
Task: "Implement code/data/extract_github.py logic to calculate author_count and kloc"
Task: "Implement code/data/download_nvd.py logic to map CVEs to repos via exact URL matching"
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
 - Developer D: Revision tasks (T034-T038)
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
- **Hardware Constraint**: All tasks must run on CPU-only CI with limited cores and RAM. No GPU models or heavy quantization.
- **Data Integrity**: All tasks must use real data sources (NVD, GitHub API). No synthetic data fabrication. **Critical**: T034 ensures that if data fetch fails, the pipeline aborts or skips, never fabricates.
- **Causality Warning**: All tasks involving model interpretation must explicitly state that results are observational associations, not causal claims.
- **Plan Override**: Task T017 implements `log(kloc)` as a free predictor per Plan.md and Spec Amendment, overriding Spec FR-004's original offset requirement to avoid bias.
- **Revision Context**: Tasks T034-T038 address specific findings from the `/speckit.analyze` review regarding data robustness, collinearity, sample size, and CI timeout constraints. T034 specifically implements the Lagged Variable GLM to address Plan requirements.