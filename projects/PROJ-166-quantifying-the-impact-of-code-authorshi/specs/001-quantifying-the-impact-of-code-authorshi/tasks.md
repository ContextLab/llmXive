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
- [X] T002 [P] Initialize Python project with pinned dependencies compatible with Python 3.11. Create `requirements.txt` with version ranges: `pandas>=2.0.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `requests>=2.31.0`, `gitpython>=3.1.37`, `pyyaml>=6.0.1`, `numpy>=1.24.0`, `scipy>=1.11.0`, `pytest>=7.4.0`, `psutil>=5.9.0`.
- [ ] [S] T002a [S] Verify Python 3.11 compatibility of dependencies. **Action**: Run `pip install -r requirements.txt` in a Python 3.11 container and assert exit code 0. **Note**: Depends on T002 artifact (`requirements.txt`). **Dependencies**: T002.
- [X] T003 [P] Configure linting and formatting tools. Create `pyproject.toml` with `[tool.black]` (line-length=88) and `.flake8` (max-line-length=88, exclude=venv) files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with paths, constants, random seeds, and NVD/GitHub API configuration. **Constants**: Define `TARGET_MIN_STARS = 1000` (static threshold). **Execution Logic**: The pipeline MUST abort with exit code 1 if the final count of successfully processed repositories is < 500 (SC-001). **NVD Manifest**: Define `NVD_MANIFEST_SHA256 = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'` (Placeholder: MUST be replaced with the actual SHA256 hash of the current NVD manifest before execution). **Dependencies**: None.
- [ ] [P] T005 [P] Setup data directory structure (`data/raw/`, `data/processed/`) and generate schema definitions in `contracts/`. **Deliverables**: Create `contracts/repo_metrics.schema.yaml` (defining columns: `url`, `primary_language`, `unique_authors`, `kloc`, `cve_count`, `project_age`, `release_count`) and `contracts/model_results.schema.yaml` (defining output structure for coefficients, SE, p-values, CIs). **Note**: Downstream tasks (T006-T009) logically depend on these schemas for validation, but T005 can run in parallel with other setup tasks (T001-T004).
- [X] T006 [P] Implement `code/data/generate_target_list.py` to fetch a **target list of repos** via GitHub API. **Endpoint**: `https://api.github.com/search/repositories?q=stars:>1000`. **Query Logic**: Construct query string dynamically using the static variable `TARGET_MIN_STARS` from `code/config.py` (default 1000). **Authentication**: Requires `GITHUB_TOKEN` environment variable. **Rate Limit Handling**: Implement exponential backoff with jitter for HTTP rate-limiting errors; abort with CRITICAL error on HTTP 403. **Max Retries**: 3. **Output**: `data/raw/target_list.csv` with columns `url`, `primary_language`, `stars`, `age`. **Dependencies**: T005.
- [ ] [S] T007 [S] Implement `code/data/download_nvd.py` to download, merge, and deduplicate NVD/CVE JSON feeds (historical range early 21st century-present) with strict checksum verification. **Logic**: Download all yearly JSON files from the official NVD feed using the URL pattern ` for years from 2002 to present. Merge them in-memory to deduplicate by CVE ID. **Manifest Verification**: Download the official NVD manifest from ` (or the latest available manifest URL) and verify the SHA256 checksum of the merged file against the constant `NVD_MANIFEST_SHA256` defined in `code/config.py`. **Abort**: If checksum verification fails, the feed is corrupted, or the manifest is missing, the script MUST abort with a CRITICAL error. **Output**: `data/raw/nvd_cve_merged.json.gz` and `data/raw/nvd_cve_merged.json.gz.sha256`. **Dependencies**: T005, T004 (for checksum constant).
- [ ] [S] T008a [P] Setup environment for `cloc`. **Action**: Create a script `code/setup_cloc.sh` that installs `cloc` via `apt-get install cloc` if not present. **Verification**: The script MUST run `cloc --version` and assert exit code 0 to confirm the binary is functional before exiting. **Dependencies**: None.
- [ ] [S] T048 [S] [Draft] Draft Constitutional Amendment VI. **Action**: Create a proposal document `docs/amendments/VI_shallow_since.md` that proposes updating `constitution.md` Principle VI to replace `git clone --depth=1` with `git clone --shallow-since=2015-01-01`. **Rationale**: `--depth=1` prevents calculating `unique_authors` for historical repos. **Note**: This task produces a proposal; ratification occurs via the governance process (PR + Sync Impact Report) outside the pipeline. **Dependencies**: None.
- [ ] [S] T049 [S] [Draft] Draft Spec Amendment for FR-002. **Action**: Create a proposal document `docs/amendments/FR002_substring_matching.md` that proposes updating Spec FR-002 to allow "Substring Matching" as the primary strategy for NVD record matching, with "Exact URL Matching" as a fallback. **Rationale**: Exact matching results in massive false negatives, biasing the outcome variable. **Dependencies**: None.

## Phase 3: User Story 1 - Dataset Construction and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest a defined set of public GitHub repositories, extract commit metadata to calculate unique contributors, compute lines of code (KLOC), and retrieve associated vulnerability records from the NVD/CVE database to form the primary analysis dataset.

**Independent Test**: Execute the data pipeline script on a small, fixed seed of repositories (first alphabetically) and verify the output CSV contains non-null values for `unique_authors`, `kloc`, `cve_count`, and `primary_language` for all entries.

### Implementation for User Story 1

- [ ] [S] T008 [S] [US1] Implement `code/data/extract_github.py` to clone, parse, and merge metrics for each repo in `target_list.csv`. **Clone Strategy**: Enforce `git clone --shallow-since=2015-01-01` for ALL repositories. **Pre-requisite**: Requires `code/setup_cloc.sh` (T008a) to have successfully installed `cloc` and verified its functionality. **Constitution Check**: This task requires the amended Constitution (from T048) to be ratified before execution; if T048 is not complete, this task must be blocked. **Parse**: Use `git log --format=%ae` on the shallow clone to extract unique author emails. **Filter**: Identify unique authors by distinct email fields. **Metric Calculation**: Calculate `unique_authors` (count) as the primary metric. **Note**: The metric `authorship_diversity` is defined as `unique_authors` (count) only, NOT a ratio, to align with Constitution Principle VI (as amended). **cloc**: Run `cloc --by-file --quiet` to calculate `kloc`. **Execution**: Process repositories **sequentially** (one by one) to ensure memory safety. **Constraints**: If a clone fails OR if `--shallow-since=2015-01-01` does not contain sufficient history, **EXCLUDE** that repo, log `WARNING`, and continue. Do NOT fall back to synthetic data. **Output**: `data/processed/github_raw_metrics.csv` (columns: `url`, `primary_language`, `unique_authors`, `raw_line_count`, `kloc`) and `data/processed/tmp_clone_paths.txt`. **Dependencies**: T006, T048 (Draft), T008a, T005.
- [ ] [S] T009 [S] [US1] Implement `code/data/merge_datasets.py` to join GitHub metrics with NVD CVE counts using **Substring Matching** as the primary strategy (per T049 Draft), with exact URL matching as a fallback. **Matching Logic**: For each repo URL, perform **substring match** first. If a single unique candidate is found, use it. If multiple candidates are found (ambiguous) or no match, attempt **exact URL match** as a secondary verification step. **Validation**: If a URL matches multiple NVD entries, flag as ambiguous. **Ambiguous Handling**: Log ambiguous matches to `data/raw/ambiguous_matches.log` and mark them as `pending_verification` in the output dataset. **Cleaning**: If `kloc` is null, **log a WARNING** and exclude the row. If `cve_count` is missing, set it to **0**. **Output**: `data/processed/repo_metrics_clean.csv` (columns: `url`, `primary_language`, `unique_authors`, `kloc`, `cve_count`, `project_age`, `release_count`, `match_status`) and `data/raw/ambiguous_matches.csv`. **Dependencies**: T006, T007, T008, T005, T049 (Draft).
- [ ] [P] T010a Create unit test `tests/unit/data/test_download_nvd.py::test_nvd_checksum_verification`: Assert SHA256 matches expected value. **Action**: Read expected value from `code/config.py` constant `NVD_MANIFEST_SHA256`.
- [ ] [P] T010b Create unit test `tests/unit/data/test_extract_github.py::test_author_count_calculation`: Mock git log output with lines: "Author A", "Author B", "Author A". Assert unique author count is non-trivial.
- [ ] [P] T010c Create unit test `tests/unit/data/test_merge_datasets.py::test_url_matching`: Mock NVD data, assert substring match logic works and ambiguous matches are logged.
- [ ] [P] T013 Add logging in `code/data/merge_datasets.py` for skipped repositories and ambiguous NVD matches. Use `logging.WARNING` for skips and `logging.ERROR` for ambiguous matches. **Action**: For ambiguous matches, ensure the row is marked as `pending_verification`. Log format: `"[REPO_URL] Reason: <reason>"`. Write to `logs/merge_warnings.log`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 4: User Story 2 - Statistical Modeling and Inference (Priority: P2)

**Goal**: Fit a multivariate Negative Binomial GLM predicting vulnerability counts from author counts and control variables, using `log(kloc)` as a **free predictor** (per Plan guidance to avoid bias) and output coefficient estimates, p-values, and confidence intervals.

**Independent Test**: Run the analysis script on a static, pre-generated CSV of a representative sample size and verify the output JSON includes an `author_count_coefficient` with a non-null standard error and a confidence interval.

### Implementation for User Story 2

- [ ] [S] T017a [S] [US2] Implement `code/analysis/fit_nb_model.py` to fit the primary Negative Binomial GLM. **Response**: `cve_count`. **Predictors**: `author_count` + controls (`project_age`, `C(primary_language)`, `release_count`). **Size Adjustment**: Use `log(kloc)` as a **free predictor** (covariate). **Formula**: `cve_count ~ author_count + project_age + C(primary_language) + release_count + np.log(kloc)`. **Implementation**: Use `smf.glm(formula=..., data=df, family=sm.families.NegativeBinomial())`. **Exclusions**: Exclude rows where `kloc` <= 0. **Output**: `data/processed/nb_model_results.json` containing: `author_count_coefficient`, `std_err`, `p_value`, `ci_95_lower`, `ci_95_upper`, `convergence_status`, `model_type` ("NegativeBinomial"). **Dependencies**: T009.
- [ ] [S] T017b [S] [US2] Implement `code/analysis/fit_zinb_model.py` to fit the Zero-Inflated Negative Binomial (ZINB) model for robustness. **Response**: `cve_count`. **Predictors**: Same as T017a. **Implementation**: Use `statsmodels.discrete.discrete_model.ZeroInflatedNegativeBinomialP`. **Output**: `data/processed/zinb_model_results.json` containing: `author_count_coefficient`, `std_err`, `p_value`, `model_type` ("ZeroInflatedNegativeBinomial"), `zib_aic`, `nb_aic`. **Dependencies**: T017a.
- [ ] [S] T017c [S] [US2] Implement `code/analysis/model_selection.py` to compare NB and ZINB models and check collinearity. **Logic**: Compare AIC/BIC of NB and ZINB. If ZINB AIC/BIC is significantly lower, log a `WARNING` and record ZINB as the preferred robustness model, but **DO NOT overwrite** the primary NB coefficients in `model_results_raw.json` unless Spec FR-004 is amended (see T050). **Collinearity**: Calculate VIF for all predictors. If VIF > 5.0, log a `WARNING` and record the VIF values, but **DO NOT** automatically switch to Ridge regression in the primary output. **Output**: Update `data/processed/model_results_raw.json` with `vif` dict, `zinb_aic`, `nb_aic`, `preferred_model` (for robustness), and `high_collinearity_warning`. **Dependencies**: T017a, T017b.
- [ ] [S] T050 [S] [Draft] Draft Spec Amendment for Model Selection. **Action**: Create a proposal document `docs/amendments/FR004_model_selection.md` that proposes updating Spec FR-004 to allow automatic model selection (NB vs ZINB) and Ridge regression fallback based on statistical criteria (AIC/BIC, VIF). **Dependencies**: T017c.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Checks and Sensitivity Analysis (Priority: P3)

**Goal**: Perform robustness checks including subsampling by programming language, a sensitivity analysis using an alternative diversity metric (Shannon entropy), a lagged variable analysis to mitigate reverse causality, an interaction terms analysis, and a top-tier exclusion sensitivity analysis.

**Independent Test**: Run the robustness script and verify it produces separate regression results for at least two distinct language subsamples (e.g., Python and JavaScript), one alternative diversity metric, one lagged variable model, interaction terms, and a top-tier exclusion analysis.

### Implementation for User Story 3

- [ ] [S] T021a [S] [US3] Implement `code/analysis/robustness.py` (Part 1a: Generate Subsamples) to prepare language subsamples. **Logic**: Iterate over **all unique languages** in `data/processed/repo_metrics_clean.csv`. Filter by sample size `n >= 30`. Log exclusions for `n < 30`. **Output**: `data/processed/language_subsamples.csv` with columns `language`, `n_rows`, `subset_path`. **Dependencies**: T009.
- [ ] [S] T021b [S] [US3] Implement `code/analysis/robustness.py` (Part 1b: Fit GLMs per Subsample) to fit GLMs for each qualifying language. **Logic**: Re-fit NB GLM for each language subsample (using same formula as T017a). **Output**: `data/processed/robustness_subsample_pvalues.csv` with columns `language`, `coefficient`, `std_err`, `p_value_raw`. **Dependencies**: T021a.
- [ ] [S] T021c [S] [US3] Implement `code/analysis/robustness.py` (Part 1c: Aggregate Subsample Results) to combine subsample results. **Output**: Final `robustness_subsample_results.json`. **Dependencies**: T021b.
- [ ] [S] T022 [S] [US3] Implement `code/analysis/robustness.py` (Part 2: Shannon Entropy) to calculate Shannon entropy and re-fit GLM. **Logic**: Calculate `H = -sum(p_i * ln(p_i))`. Re-fit GLM using entropy as predictor. **Output**: `data/processed/robustness_entropy_pvalues.csv` with columns `model_type`, `coefficient`, `std_err`, `p_value_raw`, `coefficient_diff`. **Dependencies**: T017a.
- [ ] [S] T034a [S] [US3] Implement `code/analysis/robustness.py` (Part 3a: Calculate Lagged Variables) to compute lagged metrics. **Logic**: Calculate `author_count_lag_year` and `cve_count_lag_1year`. **Data Handling**: `project_end_date` is the latest commit timestamp from `--shallow-since` clone. Exclude repos where the lag window falls outside available data. **Output**: `data/processed/lagged_variables.csv`. **Dependencies**: T008.
- [ ] [S] T034b [S] [US3] Implement `code/analysis/robustness.py` (Part 3b: Filter Data for Lagged Analysis) to apply exclusions. **Logic**: Filter out repos with insufficient history. **Output**: `data/processed/lagged_filtered_data.csv`. **Dependencies**: T034a.
- [ ] [S] T034c [S] [US3] Implement `code/analysis/robustness.py` (Part 3c: Fit Lagged GLM) to fit the lagged model. **Logic**: Fit NB GLM with lagged variables. **Output**: `data/processed/robustness_lagged_results.json`. **Dependencies**: T034b.
- [ ] [S] T042 [S] [US3] Implement `code/analysis/robustness.py` (Part 4: Interaction Terms) to calculate interaction effects. **Logic**: Fit GLM with `author_count * C(primary_language)`. **Output**: `data/processed/robustness_interaction_pvalues.csv`. **Dependencies**: T017a.
- [ ] [S] T049 [S] [US3] Implement `code/analysis/robustness.py` (Part 7: Top-Tier Exclusion) to perform sensitivity analysis. **Logic**: Exclude top decile of projects by `cve_count`. Re-fit GLM. **Output**: `data/processed/robustness_top_tier_exclusion.json`. **Dependencies**: T017a.
- [ ] [S] T023a [S] [US3] Implement `code/analysis/robustness.py` (Part 5a: Aggregate P-Values) to collect all raw p-values. **Logic**: Aggregate p-values from `model_results_raw.json` (T017c), `robustness_subsample_pvalues.csv` (T021c), `robustness_entropy_pvalues.csv` (T022), `robustness_lagged_results.json` (T034c), `robustness_interaction_pvalues.csv` (T042), and `robustness_top_tier_exclusion.json` (T049). **Output**: `data/processed/all_raw_pvalues.csv`. **Dependencies**: T017c, T021c, T022, T034c, T042, T049.
- [ ] [S] T023b [S] [US3] Implement `code/analysis/robustness.py` (Part 5b: Apply BH Correction) to apply Benjamini-Hochberg. **Logic**: Apply BH correction to `all_raw_pvalues.csv`. **Output**: `data/processed/bh_corrected_pvalues.csv`. **Dependencies**: T023a.
- [ ] [S] T023c [S] [US3] Implement `code/analysis/robustness.py` (Part 5c: Generate BH Report) to create the final report. **Output**: `data/processed/robustness_results.json` and `bh_correction_report.md`. **Dependencies**: T023b.
- [ ] [S] T047 [S] [US3] Implement `code/analysis/manual_verification.py` (Part 6: Generate Candidates). **Purpose**: Generate a list of ambiguous matches for human review. **Logic**: Read `data/raw/ambiguous_matches.csv`. Stratify by language and CVE count. Select a random sample. **Output**: `data/raw/manual_verification_candidates.csv`. **Note**: This task stops at candidate generation; it does not ingest results. **Dependencies**: T009.
- [ ] [S] T047b [S] [US3] Implement `code/analysis/manual_verification.py` (Part 6b: Ingest Results). **Purpose**: Consume the human-verified results and update the dataset. **Logic**: Read `manual_verification_results.csv` (provided by human). Update `data/processed/repo_metrics_clean.csv` by resolving `pending_verification` rows. **Output**: `data/processed/repo_metrics_final.csv`. **Dependencies**: T047, `manual_verification_results.csv` (external input).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] [P] T025a Update `README.md`: Add a CLI usage section with example commands.
- [ ] [P] T025b Update `README.md`: Add a "Methods" section explaining the GLM free predictor approach.
- [ ] [P] T025c Update `README.md`: Add a "Data" section describing the pipeline.
- [X] T026 Code cleanup and refactoring: Extract `parse_git_log` and `run_cloc` into separate modules in `code/data/utils.py` to ensure modularity.
- [ ] [S] T027a [P] Create benchmark harness `code/validate_target_list.py`. **Purpose**: Create the infrastructure to measure time and success rate. **Action**: Implement a script that validates `data/raw/target_list.csv` contains >= 550 repos and exits with code 0 or 1. **Dependencies**: None.
- [ ] [S] T027c [S] Create full pipeline benchmark `code/run_pipeline_benchmark.py`. **Purpose**: Execute the full pipeline (T006-T009) and measure elapsed time to verify SC-001. **Logic**: Run the full pipeline on the target list. Record `total_time_seconds`, `total_repos`, `successful_repos`. **Output**: `benchmark_results.json`. **Dependencies**: T006-T009.
- [ ] [CI] T027b [CI] Execute benchmark on full dataset in CI environment. **Purpose**: Verify SC-001 (≥500 repositories within 6 hours). **Input**: `benchmark_results.json` from T027c. **Criteria**: 1) Total execution time must be <= 6 hours. 2) **Absolute Count**: The number of successfully processed repositories MUST be >= 500. 3) Success rate >= 95%. **Output**: JSON with `total_time_seconds`, `total_repos`, `successful_repos`, `success_rate`. **Pass/Fail**: Fail if time > 6h OR if `successful_repos` < 500. **Dependencies**: T027a, T027c.
- [ ] [P] T028a Create unit test `tests/unit/analysis/test_zero_kloc_exclusion`: Verify rows with kloc=0 are excluded.
- [ ] [P] T028b Create unit test `tests/unit/analysis/test_empty_nvd_match`: Verify cve_count=0 when no match found.
- [ ] [P] T029 Update `code/config.py` to use `os.getenv` for API keys.
- [ ] [P] T037 [P] [Revision] Update `code/config.py` to enforce a **hard timeout** for the entire pipeline execution. **Logic**: Use `signal.alarm` (Linux) or a `threading.Timer` watchdog (non-Linux) to abort the process if `time.time() - start_time > 19800` seconds. **Output**: If timeout occurs, write a `pipeline_timeout.json` file and exit with code 1. **Dependencies**: None.
- [ ] [P] T044 [P] [Revision] Implement `code/data/extract_github.py` **memory-aware chunking** to prevent CI OOM. **Logic**: Process repositories sequentially. If a single repo clone exceeds Significant memory usage (detected via `psutil`), skip that repo, log `CRITICAL`, and continue. **Constraint**: Do NOT use synthetic data as a fallback. **Output**: Update `data/processed/github_raw_metrics.csv` with a `processing_status` column (`success`, `oom_skip`, `error_skip`). **Dependencies**: T008.

---

## Phase 7: Revision & Compliance Fixes (Addressing Analysis Findings)

**Purpose**: Address specific concerns raised by the `/speckit.analyze` review regarding data integrity, model robustness, and CI constraints.

- [ ] [S] T045 [S] [Revision] Implement `code/analysis/fit_models.py` **convergence handling**. **Logic**: If the Negative Binomial GLM fails to converge after max iterations, **log a CRITICAL ERROR**, set `convergence_status` to false, and output `null` for coefficients. **DO NOT** attempt to fit a Poisson GLM as a fallback. **Output**: Update `model_results_raw.json` with `convergence_status` and `fallback_model_used: false`. **Dependencies**: T017a.
- [ ] [S] T046 [S] [Revision] Implement `code/data/download_nvd.py` **streaming download** for large NVD files. **Logic**: Use `requests` with `stream=True` and write to disk in chunks to avoid RAM spikes. **Verification**: Ensure the final file size matches the `Content-Length` header (or log warning if mismatch). **Dependencies**: T007.

---

## Phase 8: Final Validation and Reporting

**Purpose**: Ensure all components work together and produce a final, reproducible report.

- [ ] [S] T039 [P] [Revision] Implement `code/analysis/generate_final_report.py` to synthesize all results into a single human-readable Markdown report. **Pre-check**: Assert existence of `data/processed/repo_metrics_final.csv` (from T047b), `data/processed/model_results_raw.json`, and `data/processed/robustness_results.json`. If any are missing, fail immediately with error. **Logic**: Aggregate coefficients, p-values (raw and adjusted), VIF warnings, and sample size notes. **Output**: `docs/final_analysis_report.md` containing:
 1. Executive Summary of the primary association.
 2. Table of main model coefficients with significance stars.
 3. Section on Robustness Checks (Subsamples, Entropy, Lagged, Interaction, Top-Tier Exclusion) with a summary table.
 4. Explicit "Limitations" section citing the observational nature, potential reverse causality, any excluded subsamples (per T021c), lagged data exclusions (per T034c), and **repos excluded due to `--shallow-since=2015-01-01` insufficient history** (per T008).
 5. Appendix with the exact command-line invocation used to reproduce the results.
 **Dependencies**: T017c, T021c, T022, T023c, T034c, T042, T047b, T049.
- [ ] [S] T043 [P] [Revision] Implement `code/analysis/generate_final_json.py` to aggregate all results into a single machine-readable artifact. **Logic**: Aggregate coefficients, p-values (raw and adjusted), VIF warnings, sample size notes, and model selection details from `model_results_raw.json`, `robustness_results.json`, and `data/processed/repo_metrics_final.csv`. **Output**: `data/processed/final_results.json` containing all metrics in a single, structured JSON object as required by FR-007. **Dependencies**: T017c, T021c, T022, T023c, T034c, T042, T047b, T049.
- [ ] [S] T040 [P] [Revision] Add a "Reproducibility Check" task in `tests/integration/test_reproducibility.py`. **Pre-check**: Assert existence of all required input artifacts. **Logic**: Run the full pipeline twice on the same seed dataset (using a fixed seed in `config.py` and `numpy.random.seed`). Assert that the resulting `data/processed/model_results_raw.json` and `data/processed/robustness_results.json` files are byte-for-byte identical (or within floating-point tolerance). **Purpose**: Verify SC-003 (Reproducibility). **Dependencies**: T027a (harness), T039 (report generation), T043 (final JSON).
- [ ] [S] T041 [CI] Execute the full pipeline on the seed dataset in CI to generate the final report artifact. **Purpose**: Verify the pipeline runs end-to-end in the CI environment and produces the `docs/final_analysis_report.md`. **Precondition**: All previous tasks (T001-T040) must be complete. **Output**: The generated `docs/final_analysis_report.md` artifact. **Pass/Fail**: Fail if the report is missing or contains error messages in the output.

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
- **Revision Tasks (T035-T037, T044-T046)**: Can be implemented in parallel with each other, but depend on the existence of the base scripts in T008, T017, T021.
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
- T021a, T021b, T022, T034a, T042, T049 (US3) are marked [P] (relative to each other) and can run in parallel as they read from the same clean dataset, but T023a must wait for all of them.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for full pipeline on 5-repo seed in tests/integration/test_data_pipeline.py"

# Launch all data extraction tasks for User Story 1 together:
Task: "Implement code/data/extract_github.py logic to calculate author_count and kloc"
Task: "Implement code/data/download_nvd.py logic to map CVEs to repos via substring matching"
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
 - Developer D: Revision tasks (T035-T037, T044-T046)
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
- **Revision Context**: Tasks T035-T037, T044-T046 address specific findings from the `/speckit.analyze` review regarding data robustness, collinearity, sample size, CI timeout constraints, and memory management. T034 specifically implements the Lagged Variable GLM to address Plan requirements while adhering to Constitution VI.
- **Final Validation**: Tasks T039-T043 ensure the final output is a coherent, reproducible report and that the pipeline is deterministic. T043 specifically generates the machine-readable JSON output required by FR-007.
- **Constitutional Amendment**: Task T048 updates the Constitution to allow `--shallow-since` clones, resolving the blocker identified in Plan.md. T008 depends on T048.
- **Matching Strategy**: Task T009 implements Substring Matching as the primary strategy, with Exact URL matching as a fallback, to address construct validity threats identified in Plan.md. T049 proposes the Spec amendment to formalize this.
- **Model Selection**: Tasks T017a, T017b, T017c explicitly mandate using ZINB or Ridge coefficients as a robustness finding, but do not overwrite the primary NB results unless Spec FR-004 is amended (T050).
- **Sensitivity Analysis**: Task T049 implements the required top-tier exclusion sensitivity analysis.