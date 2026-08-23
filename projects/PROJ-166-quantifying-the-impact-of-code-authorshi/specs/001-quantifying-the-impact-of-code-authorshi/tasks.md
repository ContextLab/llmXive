---
description: "Task list template for feature implementation"
---

# Tasks: Quantifying the Impact of Code Authorship Diversity on Software Security

**Input**: Design documents from `/specs/001-quantify-authorship-diversity-security/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must wait for dependencies)
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

- [X] T001 [P] Create project structure at repository root. Create the following directories and files: `code/`, `code/__init__.py`, `code/config.py`, `code/data/`, `code/data/__init__.py`, `code/analysis/`, `code/analysis/__init__.py`, `data/`, `data/raw/`, `data/processed/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `requirements.txt`, `README.md`.
- [X] T002 [P] Initialize Python project with pinned dependencies compatible with Python 3.x. Create `requirements.txt` with version ranges: `pandas>=2.0.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `requests>=2.31.0`, `gitpython>=3.1.37`, `pyyaml>=6.0.1`, `numpy>=1.24.0`, `scipy>=1.11.0`, `pytest>=7.4.0`, `psutil>=5.9.0`.
- [X] T002a [P] Verify Python 3.11 compatibility of dependencies. Create a script `tests/unit/test_dependency_compatibility.py` that attempts to import all dependencies in `requirements.txt` and asserts no version conflicts or missing wheels for Python 3.11.
- [X] T003 [P] Configure linting and formatting tools. Create `pyproject.toml` with `[tool.black]` (line-length=88) and `.flake8` (max-line-length=88, exclude=venv) files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with paths, constants, random seeds, and NVD/GitHub API configuration. **Constants**: Define `TARGET_MIN_STARS = 1000` (static threshold). **Execution Logic**: While the query threshold is static, the execution allows proceeding with 500-599 repos (with warning) or abort if <500. **Clarification**: Repos with 500-599 stars are counted towards the SC-001 threshold only if successfully processed.
- [ ] T005 [P] Setup data directory structure (`data/raw/`, `data/processed/`) and generate schema definitions in `contracts/`. **Deliverables**: Create `contracts/repo_metrics.schema.yaml` (defining columns: `url`, `primary_language`, `unique_authors`, `kloc`, `authorship_diversity`, `cve_count`, `project_age`, `release_count`) and `contracts/model_results.schema.yaml` (defining output structure for coefficients, SE, p-values, CIs).
- [X] T006 [P] Implement `code/data/generate_target_list.py` to fetch a **target list of repos** via GitHub API. **Endpoint**: `. **Query Logic**: Construct query string dynamically using the static variable `TARGET_MIN_STARS` from `code/config.py` (default 1000). **Authentication**: Requires `GITHUB_TOKEN` environment variable. **Rate Limit Handling**: Implement exponential backoff with jitter for HTTP 429 errors; abort with CRITICAL error on HTTP 403. **Max Retries**: 3 attempts per query before failing. **Output**: `data/raw/target_list.csv` with columns `url`, `primary_language`, `stars`, `age`. **Dependencies**: None.
- [ ] T007 [P] Implement `code/data/download_nvd.py` to download, merge, and deduplicate NVD/CVE JSON feeds (historical range) with checksum verification. **Logic**: Download all yearly JSON files from the official NVD feed, merge them in-memory to deduplicate by CVE ID. **Output**: `data/raw/nvd_cve_merged.json.gz` and `data/raw/nvd_cve_merged.json.gz.sha256`.
- [ ] [S] T008 [US1] Implement `code/data/extract_github.py` to clone, parse, and merge metrics for each repo in `target_list.csv`. **Clone Strategy**: Enforce `git clone --depth=1` for ALL repositories to satisfy Constitution Principle VI. **Parse**: Use `git log --format=%ae` on the shallow clone to extract unique author emails. **Filter**: Identify unique authors by distinct email fields. **Do NOT filter authors based on line count** (preserve Constitution VI definition: all unique emails). **cloc**: Run `cloc --by-file --quiet` to calculate `kloc`. **Pre-requisite**: Ensure `cloc` is installed in the execution environment (e.g., via Dockerfile or CI setup script) before running this task. **Metric Calculation**: Calculate `authorship_diversity = unique_authors / kloc` (handle division by zero by setting to 0). **Merge**: Combine `unique_authors`, `kloc`, `authorship_diversity`, and `primary_language`. **Execution**: Process repositories **sequentially** (one by one) to ensure memory safety and avoid hidden shared state. **Constraints**: If a clone fails (repo deleted/private) OR if `--depth=1` does not contain sufficient history to calculate unique_authors (e.g., repo created > 1 year ago but shallow clone only has recent commits), **EXCLUDE** that repo, log `WARNING`, and continue. Do NOT fall back to synthetic data. **Output**: `data/processed/github_raw_metrics.csv` (columns: `url`, `primary_language`, `unique_authors`, `raw_line_count`, `kloc`, `authorship_diversity`) and `data/processed/tmp_clone_paths.txt` (list of successful clone paths). **Dependencies**: Requires T006 (target list) to be complete.
- [ ] [S] T009 [US1] Implement `code/data/merge_datasets.py` to join GitHub metrics with NVD CVE counts using exact URL matching, including validation and cleaning. **Validation**: Enforce **exact URL matching** as per FR-002. If a URL in the target list has no exact match in NVD, set `cve_count` to 0. **Ambiguous Handling**: If a URL matches multiple NVD entries or matches via substring (ambiguous), **EXCLUDE** the row from the final output and log an ERROR. Do NOT merge ambiguous matches. **Cleaning**: If `kloc` is null (cloc failure), **log a WARNING** and exclude the row from analysis. If `cve_count` is missing, set it to **0**. **Output**: `data/processed/repo_metrics_clean.csv` (columns: `url`, `primary_language`, `unique_authors`, `kloc`, `authorship_diversity`, `cve_count`, `project_age`, `release_count`). **Dependencies**: Requires T006, T007, T008.

- [ ] [P] T010a Create unit test `tests/unit/data/test_download_nvd.py::test_nvd_checksum_verification`: Assert SHA256 matches expected value.
- [ ] [P] T010b Create unit test `tests/unit/data/test_extract_github.py::test_author_count_calculation`: Mock git log output with lines: "Author A", "Author B", "Author A". Assert unique author count is non-trivial.
- [ ] [P] T010c Create unit test `tests/unit/data/test_merge_datasets.py::test_url_matching`: Mock NVD data, assert exact match logic works and ambiguous matches are ignored.
- [ ] [P] T013 Add logging in `code/data/merge_datasets.py` for skipped repositories and ambiguous NVD matches. Use `logging.WARNING` for skips and `logging.ERROR` for ambiguous matches. **Action**: For ambiguous matches, ensure the row is **excluded** from the output dataset. Log format: `"[REPO_URL] Reason: <reason>"`. Write to `logs/merge_warnings.log`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Construction and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest a defined set of public GitHub repositories, extract commit metadata to calculate unique contributors, compute lines of code (KLOC), and retrieve associated vulnerability records from the NVD/CVE database to form the primary analysis dataset.

**Independent Test**: Execute the data pipeline script on a small, fixed seed of repositories (first alphabetically) and verify the output CSV contains non-null values for `unique_authors`, `kloc`, `authorship_diversity`, `cve_count`, and `primary_language` for all entries.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py`. Validate columns and types.
- [X] T012 [US1] Integration test for full pipeline on 5-repo seed in `tests/integration/test_data_pipeline.py`. Run T006->T007->T008->T009 and assert output file exists with correct data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Inference (Priority: P2)

**Goal**: Fit a multivariate Negative Binomial GLM predicting vulnerability counts from author counts and control variables, using `log(kloc)` as a **free predictor** (per Plan guidance to avoid bias) and output coefficient estimates, p-values, and confidence intervals.

**Independent Test**: Run the analysis script on a static, pre-generated CSV of a representative sample size. and verify the output JSON includes an `author_count_coefficient` with a non-null standard error and a confidence interval

The research question, method, and references remain unchanged as required for the planning phase, with the specific confidence level now expressed qualitatively to avoid premature empirical specification..

### Tests for User Story 2

- [X] T016 [P] [US2] Contract test for model results schema in `tests/contract/test_model_results.py`.
- [ ] [S] T017 [US2] Implement `code/analysis/fit_models.py` to fit a Negative Binomial GLM. **Response**: `cve_count`. **Predictors**: `author_count` + controls (`project_age`, `C(primary_language)`, `release_count`). **Size Adjustment**: Use `log(kloc)` as a **free predictor** (covariate), NOT an offset, per FR-004 (which explicitly requires it as a free predictor). **Formula**: `cve_count ~ author_count + project_age + C(primary_language) + release_count + np.log(kloc)`. **Model Mandate**: **Fit ONLY a Negative Binomial GLM** as required by FR-004. Do NOT perform a Likelihood Ratio Test (LRT) to select between Poisson and Negative Binomial. **Implementation**: Use `smf.glm(formula=..., data=df, family=sm.families.NegativeBinomial())`. **Exclusions**: Exclude rows where `kloc` <= 0. **Diagnostics**: Calculate VIF for all predictors. **Input**: Explicitly use `data/processed/repo_metrics_clean.csv` (from T009) as the primary input. **Output**: `data/processed/model_results_raw.json` containing: `author_count_coefficient`, `std_err`, `p_value` (raw, uncorrected), `ci_95_lower`, `ci_95_upper`, `vif` (dict), `convergence_status` (boolean), `model_type` ("NegativeBinomial"). **Parameters**: Use `family=sm.families.NegativeBinomial()`. **Flagging**: If model fails to converge, log `ERROR`, set `convergence_status` to false, and **DO NOT** attempt a Poisson fallback. **Dependencies**: T009 (repo_metrics_clean.csv) must be complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Checks and Sensitivity Analysis (Priority: P3)

**Goal**: Perform robustness checks including subsampling by programming language, a sensitivity analysis using an alternative diversity metric (Shannon entropy), a lagged variable analysis to mitigate reverse causality, and interaction terms analysis.

**Independent Test**: Run the robustness script and verify it produces separate regression results for at least two distinct language subsamples (e.g., Python and JavaScript), one alternative diversity metric, one lagged variable model, and interaction terms.

### Tests for User Story 3

- [X] T019 [P] [US3] Contract test for robustness results schema in `tests/contract/test_robustness_results.py`.
- [X] T020 [P] [US3] Integration test for subsample, entropy, lagged, and interaction analysis in `tests/integration/test_robustness.py`.

### Implementation for User Story 3

- [ ] [S] T021 [US3] Implement `code/analysis/robustness.py` (Part 1: Subsampling) to perform subsampling by language. **Logic**: Dynamically iterate over **all unique languages** present in `data/processed/repo_metrics_clean.csv`. **Filter**: For each language, if the sample size `n < 30`, **log a WARNING** and exclude that language from the GLM fitting (as statistical power is insufficient for reliable GLM estimation), but record the exclusion. **Re-fit GLM** using the same predictors as T017 (including `log(kloc)` as a free predictor) for each qualifying language (n >= 30). **Output**: Save raw p-values to `data/processed/robustness_subsample_pvalues.csv` with columns `language`, `coefficient`, `std_err`, `p_value_raw`, `n_rows`. If model fails to converge for a subsample, set `coefficient` to `null` and log WARNING. **Note**: Do NOT apply BH correction here; raw p-values will be aggregated in T023. **Dependencies**: T017 must be complete.
- [ ] [S] T022 [US3] Implement `code/analysis/robustness.py` (Part 2: Shannon Entropy) to calculate Shannon entropy: `H = -sum(p_i * ln(p_i))` where `p_i = author_commits / total_commits` (handle log(0) by adding epsilon=1e-9). **Re-fit GLM** using entropy as the primary predictor instead of `author_count`. **Report the difference** as `abs(coefficient_entropy - coefficient_author_count)`. **Output**: Save raw p-values to `data/processed/robustness_entropy_pvalues.csv` with columns `model_type`, `coefficient`, `std_err`, `p_value_raw`, `coefficient_diff`. **Note**: Do NOT apply BH correction here; raw p-values will be aggregated in T023. **Dependencies**: T017 must be complete.
- [ ] [S] T034 [US3] Implement `code/analysis/robustness.py` (Part 3: Lagged Variable Analysis). **Purpose**: Address Plan.md requirement for mitigating reverse causality. **Logic**: Calculate `author_count_lag_1year` (authors from 12 months prior to project end date) and `cve_count_lag_1year` (CVEs from 12 months prior). **Data Handling**: **CRITICAL**: `project_end_date` is defined as the timestamp of the latest commit in the `--depth=1` clone. For repos where the 12-month window falls outside the available data (e.g., repo created < 1 year ago, or `--depth=1` prevents seeing 12 months back), **EXCLUDE** that repository from the **lagged analysis** specifically (set result to null) and log a WARNING. **Model**: Fit a full Negative Binomial GLM using these lagged variables as predictors (same formula structure as T017 but with lagged inputs). **Output**: Save results to `data/processed/robustness_lagged_results.json` with coefficients, p-values, and a note on the lagged period (including which repos were excluded due to data window constraints). **Dependencies**: Requires T008 (extract_github.py) and T017 (fit_models.py) base scripts to exist. **Constraint**: Do NOT reduce this to a simple correlation check; a full GLM is required. **Sample Size Check**: If the resulting sample size is < 30, log a CRITICAL warning and exclude the result from the final robustness set.
- [ ] [S] T042 [US3] Implement `code/analysis/robustness.py` (Part 4: Interaction Terms) to calculate interaction effects. **Logic**: Fit a GLM with interaction terms: `cve_count ~ author_count * C(primary_language) + controls + log(kloc)`. **Verification**: Ensure at least two languages have sufficient data to estimate interactions. **Output**: Save raw p-values to `data/processed/robustness_interaction_pvalues.csv` with columns `interaction_term`, `coefficient`, `std_err`, `p_value_raw`. **Dependencies**: T017 must be complete.
- [ ] [S] T023 [US3] Implement `code/analysis/robustness.py` (Part 5: Global BH Correction) to aggregate **ALL** raw p-values: from `model_results_raw.json` (T017), `robustness_subsample_pvalues.csv` (T021), `robustness_entropy_pvalues.csv` (T022), `robustness_lagged_results.json` (T034), and `robustness_interaction_pvalues.csv` (T042). Apply a **single** Benjamini-Hochberg correction to this combined set as mandated by FR-006. **Field Mapping**: Extract `p_value` from `model_results_raw.json`; extract `p_value_raw` from the CSV files; extract `p_value` from `robustness_lagged_results.json`. Handle missing/null values by excluding them from the correction set. **Execution**: Wait for the **completion** of all parallel branches (T017, T021, T022, T034, T042) before aggregation. Update `data/processed/robustness_results.json` with adjusted p-values for all tests. **Output**: Final JSON containing all coefficients, raw p-values, and adjusted p-values. **Dependencies**: T017, T021, T022, T034, T042 must be complete. **Note**: This task is NOT parallel-safe.
- [ ] [S] T024 [US3] Generate `data/processed/robustness_results.json` containing subsample coefficients, entropy model results, lagged model results, interaction results, and adjusted p-values.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] [P] T025a Update `README.md`: Add a CLI usage section with example commands.
- [ ] [P] T025b Update `README.md`: Add a "Methods" section explaining the GLM free predictor approach.
- [ ] [P] T025c Update `README.md`: Add a "Data" section describing the pipeline.
- [X] T026 Code cleanup and refactoring: Extract `parse_git_log` and `run_cloc` into separate modules in `code/data/utils.py` to ensure modularity.
- [ ] [S] T027a [P] Create benchmark harness `tests/unit/test_performance_harness.py`. **Purpose**: Create the infrastructure to measure time and success rate. **Output**: A script that can be invoked by CI to run the full pipeline. **Dependencies**: None (harness creation).
- [ ] [S] T027b [CI] Execute benchmark on full dataset in CI environment. **Purpose**: Verify SC-001 (≥500 repositories within 6 hours). **Input**: Must use `data/raw/target_list.csv`. **Pre-check**: Validate that `data/raw/target_list.csv` contains >= 550 repos; if not, fail immediately. **Criteria**: 1) Total execution time must be <= 6 hours. 2) **Absolute Count**: The number of successfully processed repositories MUST be >= 500. 3) Success rate >= 95% (calculated as successful / total input). **Output**: JSON with `total_time_seconds`, `total_repos`, `successful_repos`, `success_rate`. **Pass/Fail**: Fail if time > 6h OR if `successful_repos` < 500. **Note**: This is a CI integration task, not a unit test.
- [ ] [P] T028a Create unit test `tests/unit/analysis/test_zero_kloc_exclusion`: Verify rows with kloc=0 are excluded.
- [ ] [P] T028b Create unit test `tests/unit/analysis/test_empty_nvd_match`: Verify cve_count=0 when no match found.
- [ ] [P] T029 Update `code/config.py` to use `os.getenv` for API keys.
- [ ] [S] T035 [P] [Revision] Implement `code/analysis/fit_models.py` collinearity check: Add a VIF (Variance Inflation Factor) calculation step **before** model fitting. **Logic**: Calculate VIF for `author_count` and `kloc`. If VIF > 5.0 for any predictor, **log a WARNING** and proceed with the model but flag the result in `model_results_raw.json` with `high_collinearity_warning: true`. Do NOT remove variables or alter the model formula to force a pass; the analysis must report the actual statistical state.
- [ ] [S] T036 [P] [Revision] Implement `code/analysis/robustness.py` subsampling guard: Add a check in T021 to verify that each language subsample has sufficient statistical power (n >= 30). If a language group has < 30 rows, **log a WARNING** and exclude that specific subsample from the final `robustness_results.json` with a reason `insufficient_sample_size`. Do NOT run the GLM on undersampled groups.
- [ ] [P] T037 [Revision] Update `code/config.py` to enforce a **hard timeout** for the entire pipeline execution (leaving a buffer for CI overhead). **Logic**: Use `signal.alarm` (Linux) or a `threading.Timer` watchdog (non-Linux) to abort the process if `time.time() - start_time > 19800` seconds. **Output**: If timeout occurs, write a `pipeline_timeout.json` file and exit with code 1. This ensures compliance with SC-001 (6h limit) without partial/corrupted results.

---

## Phase 7: Revision & Compliance Fixes (Addressing Analysis Findings)

**Purpose**: Address specific concerns raised by the `/speckit.analyze` review regarding data integrity, model robustness, and CI constraints.

- [ ] [S] T044 [Revision] Implement `code/data/extract_github.py` **memory-aware chunking** to prevent CI OOM. **Logic**: Process repositories sequentially (as per T008). If a single repo clone exceeds 1GB of memory usage (detected via `psutil`), skip that repo, log `CRITICAL`, and continue. **Constraint**: Do NOT use synthetic data as a fallback. **Output**: Update `data/processed/github_raw_metrics.csv` with a `processing_status` column (`success`, `oom_skip`, `error_skip`). **Dependencies**: T008.
- [ ] [S] T045 [Revision] Implement `code/analysis/fit_models.py` **convergence handling**. **Logic**: If the Negative Binomial GLM fails to converge after max iterations, **log a CRITICAL ERROR**, set `convergence_status` to false, and output `null` for coefficients. **DO NOT** attempt to fit a Poisson GLM as a fallback. This ensures strict adherence to FR-004 (Negative Binomial only). **Output**: Update `model_results_raw.json` with `convergence_status` and `fallback_model_used: false`. **Dependencies**: T017.
- [ ] [S] T046 [Revision] Implement `code/data/download_nvd.py` **streaming download** for large NVD files. **Logic**: Use `requests` with `stream=True` and write to disk in chunks to avoid RAM spikes. **Verification**: Ensure the final file size matches the `Content-Length` header (or log warning if mismatch). **Dependencies**: T007.
- [ ] [S] T048 [Revision] Implement `code/analysis/generate_final_report.py` to explicitly document the exclusion of pre-2015 repos from the lagged variable analysis (T034) due to `--depth=1` constraints, ensuring transparency in the limitations section.

---

## Phase 8: Final Validation and Reporting

**Purpose**: Ensure all components work together and produce a final, reproducible report.

- [ ] [S] T039 [P] [Revision] Implement `code/analysis/generate_final_report.py` to synthesize all results into a single human-readable Markdown report. **Pre-check**: Assert existence of `data/processed/repo_metrics_clean.csv`, `data/processed/model_results_raw.json`, and `data/processed/robustness_results.json`. If any are missing, fail immediately with error. **Logic**: Aggregate coefficients, p-values (raw and adjusted), VIF warnings, and sample size notes from `model_results_raw.json`, `robustness_results.json`, and `data/processed/repo_metrics_clean.csv`. **Output**: `docs/final_analysis_report.md` containing:
 1. Executive Summary of the primary association.
 2. Table of main model coefficients with significance stars.
 3. Section on Robustness Checks (Subsamples, Entropy, Lagged, Interaction) with a summary table.
 4. Explicit "Limitations" section citing the observational nature, potential reverse causality, any excluded subsamples (per T036), lagged data exclusions (per T034, T048), and **repos excluded due to `--depth=1` insufficient history** (per T008).
 5. Appendix with the exact command-line invocation used to reproduce the results.
 **Dependencies**: T017, T021, T022, T023, T034, T035, T036, T042, T048 must be complete.
- [ ] [S] T040 [P] [Revision] Add a "Reproducibility Check" task in `tests/integration/test_reproducibility.py`. **Pre-check**: Assert existence of all required input artifacts. **Logic**: Run the full pipeline twice on the same seed dataset (using a fixed seed in `config.py` and `numpy.random.seed`). Assert that the resulting `data/processed/model_results_raw.json` and `data/processed/robustness_results.json` files are byte-for-byte identical (or within floating-point tolerance). **Purpose**: Verify SC-003 (Reproducibility). **Dependencies**: T027a (harness), T039 (report generation), T043 (final JSON).
- [ ] [S] T041 [CI] Execute the full pipeline on the seed dataset in CI to generate the final report artifact. **Purpose**: Verify the pipeline runs end-to-end in the CI environment and produces the `docs/final_analysis_report.md`. **Precondition**: All previous tasks (T001-T040) must be complete. **Output**: The generated `docs/final_analysis_report.md` artifact. **Pass/Fail**: Fail if the report is missing or contains error messages in the output.
- [ ] [S] T043 [P] [Revision] Implement `code/analysis/generate_final_json.py` to aggregate all results into a single machine-readable artifact. **Logic**: Aggregate coefficients, p-values (raw and adjusted), VIF warnings, sample size notes, and model selection details from `model_results_raw.json`, `robustness_results.json`, and `data/processed/repo_metrics_clean.csv`. **Output**: `data/processed/final_results.json` containing all metrics in a single, structured JSON object as required by FR-007. **Dependencies**: T017, T021, T022, T023, T034, T035, T036, T042 must be complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on completion of Phase 2 and initial failure analysis (T035-T037 address specific analysis findings)
- **Final Validation (Phase 8)**: Depends on completion of all previous phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on `repo_metrics.csv` from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on `model_results.json` from US2
- **Revision Tasks (T035-T037, T044-T048)**: Can be implemented in parallel with each other, but depend on the existence of the base scripts in T008, T017, T021.
- **Final Validation Tasks (T039-T043)**: Depend on all analysis and robustness tasks being complete.

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
- Final Validation tasks (Phase 8) marked [P] can run in parallel (Report generation and Reproducibility check)
- Different user stories can be worked on in parallel by different team members
- T021, T022, T034, T042 (US3) are marked [P] (relative to each other) and can run in parallel as they read from the same clean dataset, but T023 must wait for all of them.

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
 - Developer D: Revision tasks (T035-T037, T044-T048)
 - Developer E: Final Validation tasks (T039-T043)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential (must wait for dependencies)
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
- **Revision Context**: Tasks T035-T037, T044-T048 address specific findings from the `/speckit.analyze` review regarding data robustness, collinearity, sample size, CI timeout constraints, and memory management. T034 specifically implements the Lagged Variable GLM to address Plan requirements while adhering to Constitution VI.
- **Final Validation**: Tasks T039-T043 ensure the final output is a coherent, reproducible report and that the pipeline is deterministic. T043 specifically generates the machine-readable JSON output required by FR-007.