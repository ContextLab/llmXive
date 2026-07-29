---
description: "Task list template for feature implementation"
---

# Tasks: Exploring the Correlation Between Musical Preference and Personality Traits

**Input**: Design documents from `/specs/001-music-personality-correlation/`  
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only if explicitly requested in the feature specification.

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

## Phase 0: Research (Methodology & Power Analysis)

- [ ] T000a Conduct Power Analysis: Implement `code/power_analysis.py` to compute required sample size for detecting Pearson r = 0.10 with Bonferroni‑adjusted α = 0.001. Output `results/power_analysis.txt`. **Verification**: Script runs without error and file exists with a numeric sample size.
- [ ] T000b Document Dataset Strategy & Methodological Rationale: Write `research.md` describing the choice of OpenML BFI‑2 (ID 42473) and HuggingFace `lastfm/lastfm_1k`, include URLs, licensing, and rationale for using real data only. **Verification**: File contains the two dataset URLs and a “Real‑First” paragraph.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create directory structure: `data/raw/`, `data/processed/`, `code/`, `tests/`, `results/`, `logs/`. **Verification**: Assert each directory exists after creation.
- [ ] T001b Create empty `__init__.py` files in `code/` and `tests/`
- [ ] T001c Initialize `requirements.txt` with placeholder dependencies
- [ ] T002 Initialize Python project with dependencies in `requirements.txt`. **Content**: Pin exact versions for `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `numpy`, `datasets`, `requests`, `pytest`, `statsmodels`. **Verification**: Run `pip install -r requirements.txt` successfully; ensure all versions are pinned (e.g., `pandas==2.2.*`).
- [ ] T003a Create `.ruff.toml` configuration file for linting. **Content**: Set `line-length = 88`, `target-version = "py311"`, and enable specific rules (E, F, W). **Verification**: File exists and contains the specified settings.
- [ ] T003b Create `pyproject.toml` with `[tool.black]` configuration for formatting. **Content**: Set `line-length = 88`, `target-version = ['py311']`. **Verification**: File exists and contains the specified settings.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T005a Implement `setup_logging()` function in `code/utils.py` returning a logger configured with file rotation to `logs/app.log`. **Verification**: After calling the function, `logs/app.log` exists and contains at least one log entry.
- [ ] T006a Implement `load_config()` function in `code/utils.py` returning a dict of environment variables (depends on T006c). **Verification**: Function returns a dict containing keys `RANDOM_SEED` and `DATA_PATH`.
- [ ] T006b Create `.env.example` file listing expected environment variable names (e.g., `RANDOM_SEED`, `DATA_PATH`) with placeholder values. **Verification**: File exists and contains the two variable names.
- [ ] T006c Populate `.env` with default values: `RANDOM_SEED=42` and `DATA_PATH="data"`. **Verification**: File exists and contains the exact key‑value pairs.
- [ ] T007a Create `contracts/` directory. **Verification**: `ls contracts/` must succeed.
- [ ] T007b Define schema fields in `contracts/dataset.schema.yaml` (fields: `user_id`, `openness`, `conscientiousness`, `extraversion`, `agreeableness`, `neuroticism`, `age`, `gender`, `country`) and `contracts/analysis_output.schema.yaml` (fields: `trait`, `genre`, `rho`, `p_value`, `adjusted_p_value`, `is_significant`, `beta`, `std_error`, `effect_size_r`, `cohens_d`, `high_correlation_flag`). **Verification**: Use `pandera` to validate a sample CSV against the schema.
- [ ] T008 Generate deterministic synthetic dataset for fallback testing.  
  - Create `data/processed/synthetic_data.csv` containing realistic Big Five scores, log‑normal listening minutes, and demographic fields for **at least 100 users**.  
  - Validate the file against `contracts/dataset.schema.yaml` using `pandera`.  
  - **Verification**: File exists, row count ≥ 100, and passes schema validation. **Note**: This synthetic file is for unit‑test purposes only and must never be used in production pipelines.
- [ ] T009 Setup error handling wrappers in `code/utils.py` for HTTP timeouts and 404s. **Verification**: Simulated timeout raises `DataUnavailableError` as expected.
- [ ] T013b Create Genre Lookup Table: `contracts/genre_lookup.yaml` defining mapping from raw tags (e.g., 'alt', 'rock', 'classical') to standardized categories (Rock, Pop, Hip‑Hop, Classical, Electronic, Jazz, Folk, Country, Metal, Other). **Verification**: Verify file exists and contains all required categories.
- [ ] T035 Define `contracts/genre_preference.schema.yaml` for the GenrePreference entity (fields: `user_id`, `genre_name`, `listening_minutes`, `genre_score`). **Verification**: Validate a sample CSV with `pandera`.
- [ ] T018 Verify Checksums: Compute SHA‑256 checksums for all files in `data/raw/` and record them in `state/projects/PROJ-049-exploring-the-correlation-between-musica.yaml` under `artifact_hashes`. **Verification**: The state file contains a checksum entry for each raw data file.
- [ ] T038 Update Project State: After each phase, update `state/projects/PROJ-049-exploring-the-correlation-between-musica.yaml` with new artifact hashes and `updated_at` timestamps. **Verification**: State file shows timestamps newer than previous run for each updated artifact.

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest OpenML BFI‑2 and Last.fm 1k, clean, map genres, and prepare a unified dataframe.

- [ ] T058 Pre‑flight URL Verification: `code/check_data_sources.py` sends HEAD requests to OpenML and HuggingFace URLs; aborts with clear error if any response ≠ 200. **Verification**: Script exits non‑zero with descriptive message on a simulated 404.
- [ ] T012a [FR-001] Load OpenML BFI dataset: Implement `code/ingest.py` to download the relevant dataset ID 42473 using `openml.datasets.get_dataset`. **Logic**:  
  1. Start timer, attempt download with `timeout=300` and `retry_count=3`.  
  2. On HTTP 404/Timeout raise `DataUnavailableError` with clear message.  
  3. Record elapsed time; **assert** elapsed ≤ 300 seconds, log `"Download successful in X.YZ s"`.  
  4. Save raw data to `data/raw/bfi2_raw.csv`.  
  **Verification**: Log must show success message or raise `DataUnavailableError`.
- [ ] T012b [FR-001] Load Last.fm 1k: Implement `code/ingest.py` to stream dataset via `datasets.load_dataset("lastfm/lastfm_1k", split="train", streaming=True)`. **Logic** mirrors T012a, including timing assertion ≤ 300 s and saving to `data/raw/lastfm_raw.csv`. **Verification**: Same as T012a.
- [ ] T013 [US1] Merge Datasets: Merge `bfi2_raw.csv` and `lastfm_raw.csv` on `user_id` (inner join). **Logic**:  
  1. If result has 0 rows, raise `DataUnavailableError`.  
  2. Save merged CSV to `data/processed/merged_data.csv`.  
  **Verification**: Output file exists and has >0 rows.
- [ ] T036a Validate `merged_dataset.csv` against `contracts/dataset.schema.yaml`. **Verification**: Use `pandera` to validate; log any mismatches as errors.
- [ ] T014 [US1] Map Genres: Implement `code/mapping.py` that loads `contracts/genre_lookup.yaml` and maps raw genre tags in `merged_data.csv` to the 10 standardized categories plus 'Other'. **Verification**: Test mapping of `['alt', 'rock']` yields `['Rock', 'Rock']`.
- [ ] T015 [US1] Prepare Unified Data: From merged data, select personality traits, standardized genre, and demographics; exclude users with zero total listening minutes. Save to `data/processed/unified_data.csv`. **Verification**: File exists, row count >0, and contains required columns (`user_id`, trait scores, `genre`, `age`, `gender`, `country`).
- [ ] T019 Compute Listening Totals: From `unified_data.csv`, compute per‑user total listening minutes, add `listening_total` and `listening_proportion` columns (proportion = minutes / total). **Verification**: New columns exist; sum of `listening_proportion` per user ≈ 1.0.
- [ ] T020 Log‑Transform Proportion: Apply `log1p` to `listening_proportion` creating `log_listening_proportion`. **Verification**: Column exists, all values > 0.
- [ ] T055 Implement deterministic hashing of `user_id` in `code/ingest.py` (e.g., SHA‑256) to replace raw identifiers before any downstream processing. Store the hashed IDs in all derived files. **Verification**: Sample rows in `data/processed/unified_data.csv` contain fixed‑length hex strings and no original IDs.
- [ ] T056 Group rare countries (≤ 5 users) into an `"Other"` category during preprocessing. Update `code/preprocess.py` to perform this aggregation after the merge step. **Verification**: After preprocessing, the `country` column contains only categories with >5 users plus `"Other"`.
- [ ] T016 [FR-007] Handle Missing Data: Impute numeric demographics with median, categorical with mode, or exclude rows as per strategy. Log exact counts: `"INFO: Imputed X rows using {strategy} | Excluded Y rows"`. **Verification**: Log contains both counts and strategy used.
- [ ] T017 Verify schema integrity of `data/processed/unified_data.csv` (non‑empty, correct columns) and log checksum. **Verification**: Validation against `contracts/dataset.schema.yaml` passes; checksum logged in state file.
- [ ] T036 Verify that `data/processed/merged_data.csv` conforms to `contracts/dataset.schema.yaml`. **Verification**: Use `pandera` to validate; log any mismatches as errors.
- [ ] T057 Add overlap‑size check: after loading both source datasets, compute the number of users present in **both** datasets; log a warning if the count is < 200 and abort with `DataUnavailableError` if count is 0. **Verification**: Log contains the overlap count and appropriate warning/abort behavior.
- [ ] T058 [FR-001] Pre‑flight URL verification script (`code/check_data_sources.py`) that sends a HEAD request to each dataset URL (OpenML and HuggingFace) before the main pipeline runs; abort with clear error if any returns non‑200. **Verification**: Script exits with non‑zero status and descriptive message on a 404.

## Phase 4: User Story 2 - Statistical Correlation and Regression Analysis (Priority: P2)

**Goal**: Compute Pearson correlations, multiple linear regressions with demographics, apply Bonferroni correction.

- [ ] T020a [TEST] Generate Synthetic Merged Dataset for Independent Testing: Create `data/processed/synthetic_merged.csv` with ≥ 5 users, full trait, genre, and demographic fields. Validate against both `contracts/dataset.schema.yaml` and `contracts/genre_preference.schema.yaml`. **Verification**: File exists and passes both schema checks.
- [ ] T020 [FR-003] Compute **Pearson** Correlations: In `code/analysis.py`,  
  1. Log‑transform `listening_minutes`.  
  2. Compute Pearson **r** and two‑tailed p‑value for every trait‑genre pair.  
  3. Output `data/processed/correlation_results.csv` with columns `trait`, `genre`, `rho`, `p_value`.  
  4. Add boolean `high_correlation_flag` where `abs(rho) > 0.3`.  
  **Verification**: File exists, columns correct, values match synthetic ground truth within tolerance when run on `synthetic_merged.csv`.
- [ ] T021 Run Multiple Linear Regression: For each trait, fit OLS `trait ~ age + gender + C(country)` using `statsmodels`. Output beta coefficients, standard errors to `data/processed/regression_results.csv`. **Verification**: File exists, contains expected columns.
- [ ] T022 Detect Collinearity: Compute VIF for covariates; if any VIF > 5, drop that predictor, log warning, and re‑fit. Add `model_definition` JSON column listing actual covariates used. **Verification**: Log contains any VIF warnings; output file reflects dropped predictors.
- [ ] T023 Apply **Bonferroni** Correction: Using the total number of tests (N = 5 × N_genres), compute `adjusted_p_value = p_value * N` (capped at 1.0). Flag `is_significant` when `adjusted_p_value < 0.001`. Append these columns to `correlation_results.csv`. **Verification**: Adjusted p‑values present and significance flag follows the 0.001 threshold.
- [ ] T034 Measure Validity of Demographic Controls:  
  1. Fit a baseline model without covariates (`trait ~ 1`).  
  2. Compute percent change in each beta coefficient between baseline and full model.  
  3. Create `data/processed/coefficient_deltas.csv` containing `trait`, `genre`, `beta_full`, `beta_baseline`, `percent_change`, `validity_status` (e.g., "Stable" if |percent_change| < 10%).  
  **Verification**: File exists, columns correct, reasonable values for synthetic data.
- [ ] T024 Save Final Analysis Results: Merge correlation, regression, and coefficient delta tables into `data/processed/analysis_results.csv` (includes FR‑004 fields, FR‑006 placeholders, and flags). **Verification**: File exists and matches `contracts/analysis_output.schema.yaml`.
- [ ] T037 Verify that `data/processed/analysis_results.csv` conforms to `contracts/analysis_output.schema.yaml`. **Verification**: Use `pandera` to validate; log any mismatches.
- [ ] T038 Run Analysis on Synthetic Dataset: Execute the full pipeline (T020‑T024) using `synthetic_merged.csv` and verify that `analysis_results.csv` matches pre‑computed synthetic expectations within tolerance. **Verification**: Automated test passes.

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate heatmap, compute effect sizes, and produce a summary CSV.

- [ ] T026 [FR-006] Generate Correlation Heatmap: Read `analysis_results.csv` and produce `results/correlation_heatmap.png` (800×600, 150 dpi) using `seaborn.heatmap` with diverging colormap ('coolwarm'), labeled axes, and title. **Verification**: File exists, dimensions 800×600, and image loads without error.
- [ ] T027a Generate Regression Coefficient Bar Plot: Plot beta coefficients per trait from `analysis_results.csv`, save `results/regression_coefficients.png`. **Verification**: File exists, image dimensions > 0, and contains a bar for each trait.
- [ ] T027 [FR-006] Calculate Effect Sizes: For each **significant** trait‑genre pair, compute Cohen’s d from Pearson r and derive 95 % CI via Fisher’s z transformation. Append `cohens_d`, `ci_lower`, `ci_upper` to `analysis_results.csv`. **Verification**: Columns present, numeric, and CI values are finite.
- [ ] T028 [FR-006] Export Summary Report: Create `results/results_report.csv` containing `trait`, `genre`, `cohens_d`, `ci_lower`, `ci_upper`, `significance_status`. For non‑significant rows, leave effect‑size fields empty and set `significance_status` to `"Non‑significant (adjusted p ≥ 0.001)"`. **Verification**: Schema matches `contracts/analysis_output.schema.yaml` and all trait‑genre combinations are present.
- [ ] T029 Verify Report Completeness: Test `tests/test_report.py::test_report_completeness` asserts that `results_report.csv` contains rows for all traits across all standardized genres. **Verification**: Test passes.
- [ ] T054 Deterministic Report Validation (single definition):  
  1. Load `results/correlation_heatmap.png` with Pillow; assert image width > 0 and presence of a gradient column (simple pixel‑range check).  
  2. Load `results/results_report.csv` and validate header against `contracts/analysis_output.schema.yaml` using `pandera`.  
  **Verification**: Both checks must pass; task fails otherwise.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T030 Documentation updates in `README.md` with execution instructions and real‑data source explanation. **Verification**: `README.md` contains a section titled “Execution Instructions” and includes URLs for OpenML BFI‑2 and Last.fm archive.
- [ ] T031 Refactor Codebase:  
  - T031a Apply `ruff` linting fixes across `code/`. **Verification**: `ruff check` succeeds without errors.  
  - T031b Apply `black` formatting across `code/`. **Verification**: `black --check` passes without modifications.  
  - T031c Ensure all modules have type hints and docstrings per `pyproject.toml` settings. **Verification**: Running `mypy` (or custom script) reports no missing type hints or docstrings.
- [ ] T032a Add `tests/test_edge_cases.py::test_empty_dataset` for empty dataset handling. **Verification**: File `tests/test_edge_cases.py` exists and contains the function `test_empty_dataset`.
- [ ] T032b Add `tests/test_edge_cases.py::test_all_missing_demographics` for missing demographic handling. **Verification**: Same as above for the second test function.
- [ ] T033 End‑to‑End Pipeline Orchestration: Implement `code/pipeline.py` that sequentially runs ingestion, analysis, and reporting, records total runtime in `logs/timing.log`, and raises `TimeoutError` if execution exceeds 6 hours. **Verification**: `logs/timing.log` exists, contains total seconds, and script aborts on timeout.
- [ ] T042 Documentation: Update `README.md` and `data/README.md` to explicitly state the “Real‑First” strategy, list OpenML 42473 and `lastfm/lastfm_1k` as the exclusive data sources, and remove any mention of synthetic data for production. **Verification**: Both README files contain the “Real‑First” paragraph and the two data‑source URLs.
- [ ] T053 (optional) Add Sensitivity Analysis: In `code/analysis.py`, sweep α from 0.01 to 0.10, record count of significant findings per α in `data/processed/sensitivity_analysis.csv`. **Verification**: File exists with columns `alpha`, `significant_count`.
- [ ] T059 Set global random seed (`code/utils.py::set_global_seed`) that seeds `numpy`, `random`, and any other libraries; invoke it at the start of `code/pipeline.py`. **Verification**: Running the pipeline twice on the same data yields identical outputs (hashes/checksums match).
- [ ] T060 Add production guard: in `code/pipeline.py`, after successful real‑data download, assert that the path used for downstream steps is not the synthetic fallback (`data/processed/synthetic_*`). Raise `RuntimeError` if a synthetic path is mistakenly used. **Verification**: Unit test confirms the guard triggers when `synthetic_merged.csv` is passed as the main input.
- [ ] T061 Unit test for privacy hashing: `tests/unit/test_hashing.py::test_user_id_hashed` loads `data/processed/unified_data.csv` and asserts all `user_id` values match the SHA‑256 pattern and are unique. **Verification**: Test passes.
- [ ] T062 Unit test for country grouping: `tests/unit/test_country_grouping.py::test_rare_countries_grouped` validates that no country appears with a count ≤ 5 except `"Other"`. **Verification**: Test passes.
- [ ] T063 Unit test for overlap size: `tests/unit/test_overlap.py::test_minimum_overlap` asserts that the overlap count ≥ 200 for the real dataset (or skips if real data unavailable). **Verification**: Test passes when real data is present.
- [ ] T064 Unit test for pipeline abort on missing data: `tests/unit/test_pipeline_error.py::test_abort_on_missing_dataset` simulates a 404 during download and checks that `DataUnavailableError` is raised and the pipeline exits cleanly. **Verification**: Test passes.
- [ ] T065 Update contracts to reflect hashed `user_id` type: modify `contracts/dataset.schema.yaml` to specify `user_id` as a string of length 64 (hex). **Verification**: Schema validation succeeds on the processed files.
- [ ] T066 Documentation of privacy & compliance: Add a section in `README.md` titled “Privacy & Data Handling” describing the hashing approach, the exclusion of personally identifying information, and the licensing compliance for OpenML and Last.fm data. **Verification**: Section present and contains the required keywords (e.g., "hashing", "PII", "licensing").