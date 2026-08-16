# Tasks: The Influence of Emotional Contagion on Collective Decision-Making in Online Forums

**Input**: Design documents from `/specs/001-emotional-contagion-decisions/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (code/, data/raw, data/processed, state/, docs/)
- [X] T002 Initialize Python project with requirements.txt (pandas, nltk, scikit-learn, statsmodels, pyyaml, requests, scipy)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup initial data contracts in code/contracts/ (thread.schema.yaml, sentiment.schema.yaml, result.schema.yaml) based on Plan.md initial draft.
- [X] T005 [P] Implement logging infrastructure and artifact hashing in state/
- [X] T006 Create base configuration management for API keys and dataset paths
- [X] T007 [P] Setup pytest environment with CPU-only constraints: Create `code/tests/conftest.py` and `pytest.ini` to enforce random seed pinning (e.g., `addopts = --random-seed=42`) and CPU-only execution flags.

---

## Phase 2.5: Data Acquisition (Split for Sequential Execution)

**Purpose**: Implement the data download fallback chain in atomic steps.

- [X] T008a [S] [US1] **Fetch Data**: Implement `code/data/download.py` to fetch data:
 **Primary**: Pushshift API (verified endpoint as per Spec Assumption 1).
 **Fallback 1**: Reddit Official API (OAuth).
 **Fallback 2**: Verified HuggingFace archives (generic reference per Spec Assumption 1).
 **Fallback 3**: Internet Archive/Common Crawl (generic reference per Spec Assumption 1).
 **Constraint**: If all sources fail, raise a `RuntimeError` with a clear message indicating the data source failure. Do NOT generate synthetic data.
 **Output**: Write raw data to `data/raw/reddit_threads.jsonl`.

- [X] T008b [S] [US1] **Validate Fallbacks**: Implement `code/data/download.py` to log the `origin_type` (API vs. archive) for every thread and verify the fallback chain logic.
 **Input**: Read `data/raw/reddit_threads.jsonl`.
 **Logic**: Verify that the `origin_type` logging implemented in T008a is present and accurate for all records.
 **Output**: Write `data/processed/download_attempts.log` with `{"timestamp": "...", "endpoint": "...", "status_code":..., "success": true/false}` for each attempt.

- [X] T008c [S] [US1] **Record Checksums**: Compute a cryptographic checksum of `data/raw/reddit_threads.jsonl` and record it in `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml` under `artifact_hashes`.

---

## Phase 2.5: Sentiment Tool Validation (Independent of Data Download)

**Purpose**: Validate VADER sentiment tool against human annotations (Constitution Principle VII). Runs independently of data download to ensure tool readiness.
 **Note**: T007a-0 (dependent on data download) was removed due to dependency conflict. T007a-1 is the canonical independent validation path.

- [X] T007a-1 [S] [US2] **Verify VADER Tool against Human-Annotated Corpus**.
 **Dependency**: None (runs independently of T008).
 **Logic**:
 1. **Standard Test**: Run VADER against the built-in NLTK VADER test suite (bundled with the library) to ensure scores fall within the standard normalized range.
 2. **Human-Annotated Corpus**: Attempt to download a verified, small human-annotated sentiment corpus from HuggingFace (generic reference per Spec Assumption 1).
 3. **Verification**: Compute Cohen's Kappa between VADER scores and human annotations on the sample. [UNRESOLVED-CLAIM: c_e36176cb — status=not_enough_info]
 4. **Fallback (Manual)**: If the external dataset is unavailable, use a pre-defined list of 5 specific sentences hardcoded in `code/data/sentiment.py` annotated by at least 2 human raters (simulated or pre-annotated) to calculate inter-rater reliability. **Risk**: If the external dataset cannot be found, the hardcoded fallback is used with a logged warning about potential bias.
 **Hardcoded Sentences for Fallback**:
 - "I love this product!" (Positive)
 - "This is terrible." (Negative)
 - "It is okay." (Neutral)
 - "I am so angry right now!" (Negative)
 - "What a wonderful day!" (Positive)
 **Constraint**: Do NOT use only the project's own data without human annotation. If no external human-annotated corpus is found, manual annotation is MANDATORY.
 **Data Hygiene**: Compute SHA-256 checksum of the sample used for verification and record it in `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml` under `artifact_hashes`.
 **Output**: `data/processed/vader_verification_log.json` containing `status` (pass/fail), `sample_size`, `min_score`, `max_score`, `cohen_kappa`, `annotation_source` (external/manual).

- [X] T007b [S] [US2] **Depends on T007a-1**: Implement Sentiment Validation Pipeline.
 **Dependency**: T007a-1.
 **Logic**:
 1. **Validation Execution**: Confirm VADER is installed and functional on the test corpus.
 2. **Storage**: Generate `data/processed/vader_validation_report.json` containing the verification status and sample details.
 3. **Audit**: Ensure the raw annotations file (if any) is checksummed and recorded in `state/`.
 **Output**: `data/processed/vader_validation_report.json`.
 **Constraint**: **Log warning** if VADER fails to run, but do NOT halt the pipeline if the tool is installed; proceed to generate the report.

---

## Phase 3: User Story 1 - Data Collection, Ground Truth, and Extraction (Priority: P1) 🎯 MVP

**Goal**: Download data, classify ground truth availability, and extract threads.

**Independent Test**: Can be fully tested by running the data extraction script against a sample of threads from r/AskScience and verifying that each thread has a sufficient number of seed posts extracted with valid timestamps and author IDs, and that the total dataset spans ≥2 subreddits and ≥1 site.

### Implementation for User Story 1

- [X] T010 [S] [US1] **Generate Exclusion Log**: Implement `code/data/extract.py` to identify threads with <3 top-level posts and write them to `data/processed/exclusions_seed.log`.
 **Input**: Read RAW data from `data/raw/reddit_threads.jsonl` (output of T008a).
 **Logic**: Filter threads with <3 top-level posts. Log `thread_id` and reason code `SEED_INSUFFICIENT`.
 **Output**: Write `data/processed/exclusions_seed.log`.

- [X] T009 [S] [US1] **Depends on T008a, T010**: Implement `code/data/extract.py` to identify threads with decision points and extract the first N=3 top-level posts as seed posts from the *filtered* dataset (threads that passed the seed count filter).
 **Input**: Read RAW data from `data/raw/reddit_threads.jsonl`. Apply the exclusion filter defined by T010 by reading `data/processed/exclusions_seed.log` to identify threads to skip.
 **Output**: Write `data/processed/threads_with_seeds.csv`.

- [X] T019 [S] [US1] **Depends on T009, T010**: Implement `code/data/validation.py` to validate ground-truth availability (FR-009).
 **Logic**:
 1. For Stack Exchange threads: Classify as 'valid' if an 'accepted_answer_id' exists.
 2. For Reddit threads: Classify as 'valid_no_gt' (valid for dataset inclusion, but no ground truth for external validation) as per Assumption 2.
 **Constraint**: Do NOT exclude Reddit threads from the dataset; include them with the 'valid_no_gt' flag to satisfy FR-001 (≥2 subreddits).
 **Action**: Log the count and percentage of 'valid' and 'valid_no_gt' threads relative to the total filtered dataset.
 **Output**: Write `data/processed/valid_threads.csv` (only 'valid' threads) and `data/processed/all_threads_classified.csv` (all threads with classification).

- [X] T019a [S] [US1] **Depends on T009, T019**: Implement `code/data/validation.py` to **compute the external validation score** (accuracy of consensus vs. ground truth) for valid threads.
 **Logic**: Calculate accuracy of consensus (majority vote) against ground truth for valid threads.
 **Consensus Definition**: For Stack Exchange, consensus is the 'accepted_answer_id'. For Reddit, consensus is 'upvotes > downvotes'. If upvote/downvote data is missing, set `external_validation_score` to `null` and log the reason as 'Missing Data'. If upvotes == downvotes for a Reddit thread, set `external_validation_score` to `null` and log the reason as 'Inconclusive'.
 **Input**: Merge data from T009 (seed posts) and T019 (ground truth classification). Iterate over ALL threads in `data/processed/all_threads_classified.csv` (which includes T010 filtering logic).
 **Output**: Append `external_validation_score` to `data/processed/valid_threads.csv` (for valid threads) and `data/processed/all_threads_classified.csv` (for all threads, setting null for 'valid_no_gt').
 **Constraint**: This task runs on the full classified dataset, explicitly handling 'valid_no_gt' threads by setting their score to null.

- [X] T019b [S] [US1] **Depends on T009, T019, T010**: Implement logic in `code/data/validation.py` to check if valid threads < 30% of the *FILTERED* dataset.
 **Source**: Read `total_thread_count` DIRECTLY from `data/processed/all_threads_classified.csv` (output of T019, which includes T010 filtering logic) to ensure the denominator represents the *filtered* dataset (threads that passed the seed post filter). Read `valid_thread_count` from `data/processed/all_threads_classified.csv` (T019 output).
 **Action**: Calculate `valid_thread_percentage = (count(valid) / count(all_filtered_threads)) * `.
 **Constraint**: **Generate `data/processed/ground_truth_stats.json` first** containing `total_dataset_count`, `valid_dataset_count`, and `valid_thread_percentage`. **THEN** check if `valid_thread_percentage < 30`. If <30, **raise a RuntimeError** with a clear message indicating that the study validity threshold (SC-006) is not met and the pipeline cannot proceed. If >=30, set `status: pass`.
 **Output**: Generate `state/sc_006_compliance_report.json` (conditional on threshold) and `data/processed/ground_truth_stats.json` (always).
 **Note**: This task produces the SC-006 compliance report and the mandatory ground truth metrics log.

- [X] T019c [S] [US1] **New Task**: Update data contracts to reflect Spec FR-006 (Thread ID random intercepts) and validate.
 **Dependency**: T019 (Ground Truth Classification).
 **Logic**:
 1. Read the initial contract definitions from `code/contracts/thread.schema.yaml` (created in T004).
 2. Update the schema to explicitly define `random_intercept: thread_id` to align with Spec FR-006, overriding the Plan.md suggestion of 'Subreddit'.
 3. Document the override in the schema file comments.
 4. **Validation**: Regenerate the schema and validate that it matches the Spec FR-006 requirements.
 **Output**: Updated `code/contracts/thread.schema.yaml` and `state/schema_validation_log.json`.
 **Constraint**: This task MUST run before T020 (GLMM Fitting) to ensure the correct schema is used.

- [X] T011 [S] [US1] Implement validation logic in `code/data/extract.py` to ensure metadata (timestamp, author, comment ID) is complete for ≥95% of extracted threads.

- [X] T012 [S] [US1] **Depends on T009, T010, T011**: Create unit tests in `code/tests/test_extract.py`: Implement specific functions `test_extract_seed_posts`, `test_flag_insufficient_seeds`, and `test_metadata_completeness`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Ground truth and seed extraction are complete.

---

## Phase 4: User Story 2 - Sentiment Analysis and Contagion Index Computation (Priority: P2)

**Goal**: Apply VADER sentiment analysis and compute the emotional contagion index.

**Independent Test**: Can be fully tested by running sentiment analysis on a fixed test corpus of Reddit comments and verifying that VADER scores fall within the standard normalized range. and the contagion index computation returns a valid correlation coefficient for threads with ≥20 replies.

### Implementation for User Story 2

- [X] T013 [S] [US2] **Depends on T008, T019, T007b**: Implement `code/data/sentiment.py` to apply VADER (NLTK) and compute compound sentiment scores on a bounded scale for each post in the *full* dataset (valid + valid_no_gt).
 **Constraint**: This task runs on the FULL dataset. **Dependency on T007b ensures validation ran (and passed or logged a warning).**

- [X] T015a [S] [US2] **Depends on T013, T019**: Implement `code/data/metrics.py` to compute the emotional contagion index (Part 1: Filtering).
 **Input**: Use the *filtered* dataset (valid + valid_no_gt threads, seed posts extracted). Read valid thread list from `data/processed/threads_with_seeds.csv` (output of T009). **Filter**: Select threads where `reply_count >= 20`.
 **Logic**:
 1. **Primary Set**: Select threads with `reply_count >= 20` for the fixed-window contagion index calculation (as per Plan and Spec).
 2. **Exclusion**: Log the count of threads excluded due to `reply_count < 20` with reason code `REPLY_COUNT_INSUFFICIENT`.
 **Constraint**: **Strictly exclude** threads with <20 replies from all contagion analysis to adhere to Spec FR-004.

- [X] T015b [S] [US2] **Depends on T015a**: Implement `code/data/metrics.py` to compute the emotional contagion index (Part 2: Calculation) **AND Confidence Intervals**.
 **Logic**:
 1. **Fixed Window (Primary)**: For threads with `reply_count >= 20`, calculate the **change in sentiment (delta)** of subsequent replies over the **first 20 comments**. **Delta is defined as the slope of the linear regression of sentiment score vs. reply position (1 to 20)**. Compute the Pearson correlation between the seed-post sentiment and this **delta**.
 2. **Confidence Intervals**: For each thread, compute confidence intervals for the Pearson correlation using bootstrapping (1000 resamples).
 **Constraint**: Threads with <20 replies are excluded (handled by T015a). **Do NOT use a variable window**.
 **Output**: Append results to `data/processed/thread_metrics.csv` with columns [thread_id, contagion_index, reply_count_used, window_type, confidence_interval_low, confidence_interval_high].

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Decision Quality Metrics and Statistical Modeling (Priority: P3)

**Goal**: Compute decision quality metrics, fit GLMMs, and perform sensitivity analysis.

**Independent Test**: Can be tested by running the statistical modeling pipeline on a sample dataset of threads and verifying that GLMMs converge, p-values are computed, and multiple-comparison correction is applied when ≥3 tests are run.

### Implementation for User Story 3

- [X] T018 [S] [US3] Implement `code/data/metrics.py` to compute decision quality metrics: (a) agreement proportion, (b) Shannon entropy for diversity, (c) external validation score (read from T019a output), and (d) efficiency metrics (time-to-decision, thread length).
 **Input**: Read external validation score from `data/processed/valid_threads.csv` generated by T019a.

- [X] T020 [S] [US3] **Depends on T019a, T015b, T019c**: Implement `code/data/modeling.py` to fit Generalized Linear Mixed Models (GLMM) with **thread-level random intercepts**. Use **beta regression** for bounded outcomes (agreement proportion). For time-to-decision (continuous duration), **select an appropriate distribution (e.g., Gamma or Log-Normal) based on residual diagnostics (AIC/BIC)** and use the corresponding link function. **Include the external validation score as a predictor** in the model where applicable.
 **Constraint**: **Override Plan.md**: Use **Random intercept: Thread ID** (not Subreddit) to match Spec FR-006 and account for intra-thread correlation. Document this override in code comments. **Input**: Join `valid_threads.csv` (T019a) and `thread_metrics.csv` (T015b) on `thread_id`. **Dependency on T019c ensures the model uses the corrected schema.**
 **Note**: The Plan's initial suggestion of "Subreddit" as the random effect contradicted Spec FR-006 ("thread-level random intercepts"). This task resolves the contradiction by adhering to the Spec and using the updated schema from T019c.

- [X] T021 [S] [US3] Implement significance testing in `code/data/modeling.py`: Wald tests (α=0.05) for contagion coefficients.

- [X] T022 [S] [US3] Implement multiple-comparison correction in `code/data/modeling.py`: Apply Bonferroni or Benjamini-Hochberg FDR when ≥3 hypothesis tests are run (FR-007).

- [X] T023a [S] [US3] **Split Task 1**: Implement FP/FN Calculation in `code/data/modeling.py`.
 **Input**: Read valid thread list from `data/processed/valid_threads.csv`. **Filter**: Use threads where `is_valid=True`.
 **Logic**:
 1. **FP/FN Calculation**: For valid threads, compute and report False Positive and False Negative rates of Consensus vs. Ground Truth for *each* threshold sweep.
 **Consensus Logic**:
 - Stack Exchange: Consensus=1 if 'accepted_answer_id' exists, 0 otherwise.
 - Reddit: Consensus=1 if upvotes > downvotes, 0 if downvotes > upvotes, Inconclusive if equal.
 **Constraint**: If T019b reports `sc_006_compliance: false`, FP/FN columns must be filled with `null` and a warning logged. Inconclusive cases are excluded from FP/FN calculation.
 **Output**: Intermediate FP/FN data.

- [X] T023b [S] [US3] **Split Task 2**: Implement Correlation Analysis in `code/data/modeling.py`.
 **Input**: Read valid thread list from `data/processed/valid_threads.csv` and contagion index from `data/processed/thread_metrics.csv`. **Dependency on T023a ensures FP/FN columns exist.**
 **Logic**:
 1. **Correlation Analysis**: Compute the **Pearson correlation between contagion_index and (1) agreement_proportion, (2) Shannon entropy, and (3) external validation score** for each sweep (agreement cutoff **{0.5, 0.6, 0.7}** and entropy threshold **{0.2, 0.4, 0.6}**).
 2. **Null Handling**: If a grid cell has <2 data points or correlation cannot be computed, set the correlation coefficient to `null` and log the reason. Set `false_positive_rate` and `false_negative_rate` to `null` in these cells.
 3. **Grid Enforcement**: **Raise a RuntimeError** if the grid is incomplete (i.e., if any cell in the full {0.5, 0.6, 0.7} x {0.2, 0.4, 0.6} grid has null values due to insufficient data). The sensitivity analysis is only valid if the full grid is populated.
 4. **Output**: Write `data/processed/sensitivity_analysis.csv` with columns: `agreement_cutoff` (float), `entropy_threshold` (float), `correlation_agreement` (float/null), `correlation_entropy` (float/null), `correlation_validation` (float/null), `false_positive_rate` (float/null), `false_negative_rate` (float/null), `grid_coverage` (boolean).
 **Requirement**: Report valid sensitivity analysis only for the full grid. If data is sparse, raise a RuntimeError.

- [X] T023c [S] [US3] **Split Task 3**: Generate Trend Summary in `code/data/modeling.py`.
 **Input**: Read `data/processed/sensitivity_analysis.csv` from T023b.
 **Logic**:
 1. **Trend Summary**: Generate a deterministic `trend_summary` text description for the primary metric (contagion vs. agreement).
 - If correlation coefficient decreases as agreement cutoff increases (0.5 -> 0.6 -> 0.7), set `trend_summary = "decreasing trend"`.
 - If correlation coefficient increases as agreement cutoff increases, set `trend_summary = "increasing trend"`.
 - Otherwise, set `trend_summary = "stable trend"`.
 2. **Output**: Append `trend_summary` to `data/processed/sensitivity_analysis.csv`.
 **Constraint**: This task runs after T023b.

- [X] T024 [S] [US3] **Depends on T019a, T015b**: Implement correlation analysis in `code/data/modeling.py`: Compute the correlation between the **external validation score** and the contagion index/decision quality metrics.
 **Input**: Read external validation score from `data/processed/valid_threads.csv` (T019a) and contagion index from `data/processed/thread_metrics.csv` (T015b).
 **Output**: Output results to `data/processed/external_validation_correlation.csv`.
 **Note**: This is a secondary analysis as defined in T051.

- [X] T024a [P] [US3] Create integration tests in `code/tests/test_modeling.py` to verify GLMM convergence and correction application.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [S] [US3] **Review Fix**: Implement collinearity diagnostics (Variance Inflation Factor) for predictors **(sentiment, thread length, time-to-decision, external_validation_score)** in `code/data/modeling.py` as required by **Assumption 7**. Output VIF scores to `data/processed/collinearity_diagnostics.json`.
 **JSON Schema**: `{"vif_scores": {"sentiment": float, "thread_length": float, "time-to-decision": float, "external_validation_score": float}, "threshold": 5, "flagged": boolean}`.
 **Threshold Logic**: **Conditional Trigger**: Compute pairwise correlations for the 4 predictors. If ≥2 predictors are correlated (correlation coefficient > 0.0), proceed to compute VIF. If no predictors are correlated, log a skip message and set `flagged: false`. If any predictor has VIF > 5, set `flagged: true` and frame joint relationships descriptively in the final report.

- [X] T031 [S] **Review Fix**: Ensure `code/data/download.py` implements a strict "fail-loud" policy for data fetching: **Remove** any `try/except` blocks that fall back to `generate_synthetic_*()` or mock data. If the primary Pushshift API, Reddit API, and HuggingFace archives all fail, the script MUST raise a `RuntimeError` with a clear message indicating the data source failure, ensuring the execution stage can re-try with a verified real source rather than proceeding with fabricated data.
 **Implementation**: Modify `download.py` to catch all API exceptions, attempt fallbacks, and if all fail, `raise RuntimeError("All data sources failed. No synthetic data generated.")`.

- [X] T032 [S] **Review Fix**: Update `code/data/metrics.py` to explicitly state the **streaming/sampling rule** in comments and logs: specify the exact split used, chunking strategy (if any), and the number of rows processed. If a sample is taken due to dataset size, the code MUST log the sample size and a statement of its representativeness limitation, ensuring no "toy" or "synthetic" data is used as a silent fallback.

- [X] T041 [S] **Review Fix**: Generate Sampling Strategy Log.
 **Action**: Create `data/processed/sampling_strategy_log.json` documenting the exact sampling rules (if any) used for dataset subsets, including the random seed, sample size, and representativeness limitations. This task is a **generation** task, not a verification task.
 **Constraint**: This task must run after T025 to ensure the pipeline has executed and generated the necessary data.

- [X] T042 [S] **Review Fix**: Generate Fail-Loud Verification Log.
 **Action**: Create `data/processed/fail_loud_verification_log.json` documenting the results of **simulated** failure condition triggers (e.g., using `unittest.mock` to simulate API 500 errors) to confirm that `RuntimeError` is raised and the pipeline halts as expected. This task is a **generation** task, not a verification task.
 **Constraint**: This task must run after T031 to ensure the fail-loud logic is in place.

- [X] T025 [S] [US3] **Review Fix**: Run full pipeline on **up to N=500** threads and verify completion within 6 hours on CPU-only runner (SC-005).
 **Requirement**: Implement a runtime check that **raises an error** or flags a `status: failure` if the total runtime exceeds a **predefined maximum duration threshold**. **Automated Mechanism**: If the runtime exceeds a predefined threshold, the task must trigger a retry with a reduced dataset size (e.g., a fraction of the original sample) and log the reduction. If the retry also fails, raise a RuntimeError. The check MUST measure the **entire pipeline execution** (including data download, extraction, sentiment, and modeling).
 **Input**: Depends on the *implementation* of tasks T008 through T024.
 **Output**: Generate `state/performance_log.json` containing `total_runtime_seconds` (int), `thread_count` (int), `status` (string: "success" or "failure"), and `resource_check` (object: {cpu: bool, ram_gb: float, disk_gb: float}).
 **Constraint**: This task runs AFTER T023 (Sensitivity Analysis) to verify the full pipeline performance.

- [X] T026 [S] [US3] **Review Fix**: Generate final report in `docs/paper.md` including SC-006 pass/fail status, ground truth percentage, model results, **and the correlation analysis between external validation score and decision quality (from T024)**.
 **Dependency**: T025, T024.

- [X] T029 [S] [US3] **Review Fix**: Create/Overwrite `docs/quickstart.md` with execution instructions for the full pipeline.
 **Dependency**: T030, T031, T032.
 **Deliverable**: `docs/quickstart.md` MUST contain:
 1. **Prerequisites**: Python 3.11, dependencies.
 2. **Install Command**: `pip install -r code/requirements.txt`.
 3. **Run Command**: `python code/analysis/run_pipeline.py --threads`.
 4. **Output Description**: List expected artifacts in `data/processed/` and `state/`.
 **Verification**: Ensure the file exists and contains all listed sections.

- [X] T027 [S] Record all artifact checksums: Update `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml` with a map of file paths to SHA-256 hashes.

- [X] T028 [S] **Review Fix**: Verify reproducibility by re-running pipeline and matching checksums.
 **Dependency**: T027, T030, T031, T032.
 **Implementation**: Execute `code/analysis/verify_reproducibility.py`.
 **Logic**:
 1. **Verify Checksum**: Verify that the checksum of `data/raw/reddit_threads.jsonl` matches the hash recorded in `state/...yaml` before running.
 2. **Re-run Pipeline**: Re-run the full pipeline (`python code/analysis/run_pipeline.py --threads`) using the **same downloaded raw data** (do not re-download) and **fixed random seeds**.
 3. **Compute Hashes**: Compute SHA-256 hashes of all output artifacts in `data/processed/` and `state/`.
 4. **Compare**: Compare new hashes against the hashes recorded in `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml` (from T027).
 5. **Assertion**: Assert that `hash(new) == hash(old)` for all artifacts.
 **Output**: Generate `state/reproducibility_report.json` containing `status` (string: "pass" or "fail"), `artifacts_checked` (int), `mismatches` (list of paths).
 **Constraint**: If any hash mismatch is found, **raise a RuntimeError** and mark the project as failed.

- [X] T033 [S] **Review Fix**: Generate `docs/analysis_summary.md` that explicitly addresses **Assumption 5** (Power Limitation).
 **Logic**: Read `thread_count` from `state/performance_log.json`. If `thread_count < 100`, generate a warning block in the summary stating: "Power limitation detected: n < 100 threads. Results should be interpreted with caution due to limited statistical power."
 **Constraint**: This task must run after T025.
 **Output**: Append the power limitation statement to `docs/analysis_summary.md` if triggered; otherwise, state "Power sufficient (n ≥ 100)".

- [X] T034 [S] **Review Fix**: Ensure `docs/paper.md` explicitly frames all findings as **associational** (not causal) as required by **Assumption 4**.
 **Logic**:
 1. **Insert Limitations**: Insert a "Limitations" section in `docs/paper.md` that states: "This study is observational with no random assignment. All reported relationships between emotional contagion and decision quality are correlational and should not be interpreted as causal."
 2. **Content Framing Check**: Verify that the "Limitations" section explicitly contains the associational framing statement. If missing, raise a RuntimeError.
 3. **Full Document Scan**: Scan the **entire** `docs/paper.md` (Abstract, Introduction, Methods, Results, Discussion, Conclusion) for causal language.
 4. **Forbidden Phrases**: Check for the following phrases: "causes", "leads to", "proves", "determines", "results in", "influences" (when used causally), "impact" (when used causally), "effect" (when used causally).
 5. **Regex Logic**: Use regex `r'\b(causes|leads to|proves|determines|results in|influences|impact|effect)\b'` (case-insensitive) to find matches.
 6. **Action**: If any causal language is found in any section, **raise a RuntimeError** with a message listing the detected phrases and their locations.
 **Constraint**: This task must run **after T026** (Report Generation) and verify `docs/paper.md` exists before scanning.

- [X] T035 [S] **Review Fix**: Verify **SC-004** (Threshold Sensitivity) compliance.
 **Logic**: Read `data/processed/sensitivity_analysis.csv`. (Wikidata Q47604, https://www.wikidata.org/wiki/Q47604) Verify that `agreement_cutoff` and `entropy_threshold` values are from the specified sets {, 0.6, 0.7} and {0.2, 0.4, 0.6}.
 **Action**: If no valid rows are found, **log an error** to `state/validation_errors.log` and set `sc_004_compliance: false` in `state/validation_summary.json`. If at least one valid row is present, log `sc_004_compliance: true`.
 **Output**: `state/validation_summary.json` with `sc_004_compliance` (boolean).

---

## Phase 7: Execution & Verification (Post-Implementation)

**Purpose**: Final verification steps to ensure the pipeline runs correctly on the target infrastructure and produces valid results.

- [X] T036 [S] **Execution Gate**: Run the full pipeline end-to-end on the GitHub Actions free-tier runner (limited CPU, limited RAM, 14 GB disk).
 **Input**: Trigger `code/analysis/run_pipeline.py` via CI/CD.
 **Verification**: Confirm that all artifacts are generated, no synthetic data fallbacks are triggered, and the runtime remains within acceptable operational limits.
 **Output**: CI build status (Pass/Fail). If Fail, the project is blocked until resolved.

- [X] T037 [S] **Data Integrity Check**: Verify that all output files in `data/processed/` have valid checksums and match the schema definitions in `code/contracts/`.
 **Logic**: Run `code/analysis/verify_schemas.py` against all generated CSV/JSON files.
 **Output**: `state/schema_validation_report.json` with `status` (pass/fail) and `errors` (list).

- [X] T038 [S] **Final Report Generation**: Compile the final `docs/paper.md` and `docs/analysis_summary.md` with all computed metrics, model coefficients, and sensitivity analysis results.
 **Dependency**: T026, T033, T034.
 **Output**: Final `docs/paper.md` and `docs/analysis_summary.md` ready for review.

- [X] T039 [S] **Final Validation**: Run `code/analysis/final_validation.py` to ensure all Success Criteria (SC-001 to SC-006) are met.
 **Logic**: Check SC-001 (variable fit), SC-002 (associational framing), SC-003 (multiple comparison), SC-004 (sensitivity), SC-005 (performance), SC-006 (ground truth).
 **Output**: `state/final_validation.json` with `all_criteria_met` (boolean) and `details` (object).

---

## Phase 8: Final Review & Revision (Pending)

**Purpose**: Address any remaining concerns from the analysis phase or manual review.

- [X] T043 [S] **Review Fix**: Ensure `docs/paper.md` includes a "Data Availability" section with a direct link to the `data/raw/reddit_threads.jsonl` checksum and the `state/artifact_hashes` map, ensuring full reproducibility.
 **Action**: Update `docs/paper.md` to include a "Data Availability" subsection with the exact file path, checksum, and instructions for accessing the raw data.
 **Constraint**: This task must run after T027.

- [X] T044 [S] **Review Fix**: Ensure `docs/quickstart.md` includes a specific section on **Data Source Verification** detailing the exact Pushshift API endpoints and generic HuggingFace/Archive references used, and the fallback order.
 **Action**: Update `docs/quickstart.md` to include a "Data Sources" subsection listing:
 1. Primary: Pushshift API URL/Endpoint.
 2. Fallback 1: Reddit Official API (OAuth flow description).
 3. Fallback 2: Generic HuggingFace dataset reference (per Spec Assumption 1).
 4. Fallback 3: Generic Internet Archive/Common Crawl archive reference (per Spec Assumption 1).
 **Constraint**: This task must run after T031.

- [X] T045 [S] **Review Fix**: Validate that the sensitivity analysis grid (T023b) explicitly handles the case where `agreement_cutoff` or `entropy_threshold` values result in zero threads, logging a specific warning and setting correlation to `null` rather than crashing.
 **Action**: Add a check in `code/data/modeling.py` within T023b logic: if `len(threads_in_cell) == 0`, log "Warning: Empty grid cell for cutoff X and threshold Y" and set correlation values to `null`.
 **Constraint**: This task must run after T023b.

- [X] T046 [S] **Review Fix**: Ensure the `state/reproducibility_report.json` (T028) includes a `random_seed` field confirming the seed used during the re-run matches the one pinned in `pytest.ini`.
 **Action**: Modify `code/analysis/verify_reproducibility.py` to read the seed from `pytest.ini` and include it in the report: `{"random_seed": 42,...}`.
 **Constraint**: This task must run after T027.

- [X] T047 [S] **Review Fix**: Add a task to verify that the `external_validation_score` calculation (T019a) correctly handles the case where `upvotes` or `downvotes` are missing from the raw data for Reddit threads, setting the score to `null` and logging the specific thread ID.
 **Action**: Update `code/data/validation.py` to check for missing `upvotes`/`downvotes` keys in the raw JSON for Reddit threads, log `thread_id` to `data/processed/missing_vote_data.log`, and set `external_validation_score` to `null`.
 **Constraint**: This task must run after T019a.

- [X] T048 [S] **Review Fix**: Ensure the `docs/analysis_summary.md` (T033) includes a section on **Data Coverage** reporting the percentage of threads from each subreddit/site and the distribution of thread lengths.
 **Action**: Update `code/analysis/analysis_summary.py` to read `data/processed/all_threads_classified.csv` and calculate distribution statistics, appending them to the summary.
 **Constraint**: This task must run after T033.

- [X] T049 [S] **Review Fix**: Verify that the `code/data/download.py` (T008a) logs the **exact timestamp** and **HTTP status code** for every API attempt (success or failure) to `data/processed/download_attempts.log`.
 **Action**: Modify `code/data/download.py` to log `{"timestamp": "...", "endpoint": "...", "status_code":..., "success": true/false}` for each attempt.
 **Constraint**: This task must run after T008a.

- [X] T050 [S] **Review Fix**: Ensure the `state/final_validation.json` (T039) includes a `validation_details` map that lists the specific pass/fail status and reason for each SC (SC-001 to SC-006).
 **Action**: Update `code/analysis/final_validation.py` to populate `validation_details` with objects like `{"SC-001": {"status": "pass", "reason": "All variables present"}}`.
 **Constraint**: This task must run after T035.

- [X] T052 [S] **Review Fix**: Ensure that the `code/data/sentiment.py` (T013) handles non-ASCII characters and emoji correctly by explicitly loading the NLTK VADER lexicon with `use_lexicon=True` and ensuring the tokenizer does not strip valid sentiment-bearing tokens.
 **Action**: Add a unit test in `code/tests/test_sentiment.py` that verifies emoji sequences (e.g., "😡", "❤️") are correctly tokenized and assigned non-zero sentiment scores.
 **Constraint**: This task must run after T013.

---

## Phase 9: Execution Gate & Data Integrity (Pending)

**Purpose**: Ensure the pipeline executes correctly on the target infrastructure and that all data sources are real and verified.

- [X] T051 [S] **New Task**: Implement `code/analysis/verify_data_sources.py` to validate that all data files in `data/raw/` are derived from the verified real sources (Pushshift, Reddit API, HuggingFace, Internet Archive, or Common Crawl) and contain no synthetic artifacts.
 **Logic**:
 1. Scan `data/raw/reddit_threads.jsonl` for synthetic markers (e.g., "synthetic", "mock", "generated_fallback").
 2. Verify that the `origin_type` logged in `data/processed/download_attempts.log` matches the source of the data.
 3. **Provenance Check**: For data from Internet Archive or Common Crawl, verify the provenance by checking for specific archive markers or checksums associated with these sources.
 4. Cross-reference the file checksums in `state/projects/PROJ-139-the-influence-of-emotional-contagion-on-.yaml` with the actual files on disk.
 5. If any synthetic markers are found or checksums mismatch, **raise a RuntimeError** with a detailed report.
 **Output**: Generate `state/data_source_verification.json` with `status` (pass/fail), `sources_verified` (list), and `anomalies` (list).
 **Constraint**: This task MUST run after T008a and before T036 (Execution Gate). If it fails, the pipeline cannot proceed.

- [X] T056 [S] **New Task**: Implement `code/analysis/validate_streaming_rules.py` to enforce the streaming/sampling rules defined in T032.
 **Logic**:
 1. Read `code/data/metrics.py` and `code/data/download.py` to extract the documented streaming/sampling rules.
 2. Verify that the rules are consistent with the actual implementation (e.g., if the rule says "stream 500 threads", ensure the code does not load the entire dataset into memory).
 3. Run a memory profiling test on the pipeline to ensure RAM usage stays within acceptable operational limits.
 4. Log the memory usage profile to `data/processed/memory_profile.json`.
 **Output**: Generate `state/streaming_validation.json` with `status` (pass/fail), `max_ram_gb` (float), and `rule_compliance` (boolean).
 **Constraint**: This task MUST run after T032 and before T025 (Performance Check).

- [X] T053 [S] **New Task**: Implement `code/analysis/validate_ground_truth_coverage.py` to verify that the ground truth coverage meets SC-006 requirements.
 **Logic**:
 1. Read `data/processed/ground_truth_stats.json` generated by T019b.
 2. Verify that `valid_thread_percentage` is ≥ 30%.
 3. If the percentage is < 30%, generate a detailed report explaining which subreddits/sites contributed to the low coverage and why.
 4. If the percentage is ≥ 30%, confirm compliance and log the exact percentage.
 **Output**: Generate `state/ground_truth_coverage_report.json` with `status` (pass/fail), `valid_thread_percentage` (float), and `recommendations` (list).
 **Constraint**: This task MUST run after T019b and before T039 (Final Validation).

- [X] T057 [S] **New Task**: Implement `code/analysis/validate_sensitivity_grid.py` to ensure the sensitivity analysis grid (T023b) is complete and valid.
 **Logic**:
 1. Read `data/processed/sensitivity_analysis.csv` generated by T023b.
 2. **Check Completeness**: If >50% of cells are empty, **raise a RuntimeError** indicating insufficient data for sensitivity analysis.
 3. Verify that no correlation values are `null` unless explicitly logged as due to insufficient data points.
 4. If no valid rows are found, **raise a RuntimeError** with a detailed report.
 **Output**: Generate `state/sensitivity_grid_validation.json` with `status` (pass/fail), `grid_coverage` (boolean), and `missing_cells` (list).
 **Constraint**: This task MUST run after T023b and before T035 (SC-004 Compliance).

- [X] T055 [S] **New Task**: Implement `code/analysis/validate_model_specification.py` to ensure the GLMM model specification (T020) matches the Spec FR-006 requirements.
 **Logic**:
 1. Read `code/data/modeling.py` to extract the model specification (random intercepts, link functions, distributions).
 2. Verify that the random intercept is `thread_id` (not `subreddit`).
 3. Verify that the link functions and distributions match the Spec requirements (beta regression for bounded outcomes, appropriate link for time-to-decision).
 4. If any mismatch is found, **raise a RuntimeError** with a detailed report.
 **Output**: Generate `state/model_specification_validation.json` with `status` (pass/fail), `random_intercept` (string), and `link_functions` (dict).
 **Constraint**: This task MUST run after T020 and before T039 (Final Validation).

- [X] T058 [S] **New Task**: Verify Confidence Intervals in `thread_metrics.csv`.
 **Logic**:
 1. Read `data/processed/thread_metrics.csv` generated by T015b.
 2. Verify that the columns `confidence_interval_low` and `confidence_interval_high` exist and contain valid numeric values.
 3. Verify that the confidence intervals are non-empty and within the valid range [-1.0, 1.0].
 4. If any values are missing or invalid, **raise a RuntimeError** with a detailed report.
 **Output**: Generate `state/confidence_interval_validation.json` with `status` (pass/fail), `missing_columns` (list), and `invalid_rows` (list).
 **Constraint**: This task MUST run after T015b and before T039 (Final Validation).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Phase 3 (US1)**: Runs after Foundational (Phase 2)
- **Phase 2.5 (Validation)**: Runs independently of Data Download (T008), but must complete before US2 (T013).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Execution & Verification (Phase 7)**: Depends on all previous phases being complete
- **Final Review (Phase 8)**: Depends on successful completion of Phase 7
- **Execution Gate & Data Integrity (Phase 9)**: Depends on all previous phases being complete and must run before final validation

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data extraction (T019, T010, T009)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 metrics

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, Phase 3 (US1) can start
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to fetch data from Pushshift API"
Task: "Implement code/data/validation.py to classify ground truth"
Task: "Create unit tests in code/tests/test_extract.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data + Ground Truth)
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
 - Developer A: User Story 1 (Data + Ground Truth)
 - Developer B: Phase 2.5 (Sentiment Validation)
 - Developer C: User Story 2 (Sentiment + Contagion)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential, depend for previous task completion
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

- **Plan.md Note**: The Plan.md initially suggested "Subreddit" as the random intercept for GLMMs. This was overridden by Spec FR-006 which requires "Thread ID". Tasks T019c and T020 implement this override, and T020 depends on the updated schema to ensure the model specification matches the Spec.

- **New Phase 9**: Added to ensure all data sources are real, verified, and that the pipeline adheres to the strict "no synthetic data" policy. These tasks are critical for passing the execution gate and ensuring the integrity of the final results.

- **Review Fix T053**: Added task to compute confidence intervals for the contagion index correlation using bootstrapping to provide a measure of uncertainty, as required by the analysis depth of the study. (Note: CI calculation logic was merged into T015b; T053 in Phase 9 now verifies the output).

- **Task ID Renaming**: T052 (Phase 9) renamed to T056; T054 (Phase 9) renamed to T057; T040 (Phase 6) renamed to T041; T040 (Phase 8) renamed to T042 to resolve collisions.

- **Merged Logic**: T053 (Confidence Intervals) logic merged into T015b to ensure `thread_metrics.csv` is generated with the required columns.

- **Conditional Logic**: T019b modified to generate report before checking threshold and set `status: fail` instead of raising `RuntimeError`, allowing T053 (Phase 9) to execute.

- **Specific Values**: T023b updated with exact numerical sets for sensitivity analysis grid.

- **Fallback Sources**: T008a updated with specific dataset IDs and verification steps for all fallback sources.

- **Sentiment Validation**: T007a-0 removed; T007a-1 is the canonical independent path with hardcoded fallback sentences.

- **Task Splitting**: T008a split into T008a, T008b, T008c. T023b split into T023a, T023b, T023c.

---

## Phase 10: Analysis Review & Revision (Pending)

**Purpose**: Address specific concerns raised by `/speckit.analyze` regarding data flow, statistical rigor, and documentation completeness.

- [ ] T059 [S] **Review Fix**: Correct the data flow dependency in T015a to ensure it reads from the *filtered* dataset (threads with ≥3 seed posts) rather than the raw dataset, preventing the inclusion of threads that should have been excluded by T010. <!-- ATOMIZE: requested -->
 **Action**: Update `code/data/metrics.py` in T015a to explicitly load `data/processed/threads_with_seeds.csv` (output of T009) as the primary input, rather than `data/raw/reddit_threads.jsonl`.
 **Constraint**: This task must run after T009 and before T015b.

- [ ] T060 [S] **Review Fix**: Enhance the statistical power analysis in T033 to include a post-hoc power calculation (using `statsmodels.stats.power`) rather than just a simple threshold check, providing a more rigorous assessment of the study's ability to detect the expected effect size.
 **Action**: Update `docs/analysis_summary.md` generation to include a "Post-Hoc Power Analysis" section with calculated power values for the observed effect sizes.
 **Constraint**: This task must run after T025 and before T033.

- [ ] T061 [S] **Review Fix**: Ensure the sensitivity analysis in T023b explicitly reports the number of threads contributing to each grid cell, as the current output only reports correlation values and nulls, making it difficult to assess the reliability of the sensitivity results.
 **Action**: Modify `data/processed/sensitivity_analysis.csv` to include a `thread_count` column for each grid cell.
 **Constraint**: This task must run after T023b.

- [ ] T062 [S] **Review Fix**: Add a task to validate that the VADER sentiment analysis in T013 correctly handles multi-lingual content, as the dataset may contain non-English threads, and VADER is primarily optimized for English. <!-- FAILED: unspecified -->
 **Action**: Implement a language detection step (using `langdetect` or similar) in `code/data/sentiment.py` to flag non-English threads and exclude them from the primary analysis or handle them separately.
 **Constraint**: This task must run after T013 and before T015b.

- [ ] T063 [S] **Review Fix**: Update the final report (T026) to include a "Limitations" subsection specifically addressing the potential bias introduced by the exclusion of threads with <5 replies, as this may systematically exclude certain types of discussions (e.g., controversial topics that die out quickly).
 **Action**: Append a "Exclusion Bias" paragraph to `docs/paper.md` discussing the implications of the reply count filter.
 **Constraint**: This task must run after T015a and before T026.

- [ ] T064 [S] **Review Fix**: Ensure the collinearity diagnostics in T030 include a visualization (e.g., a correlation heatmap) in the final report to make the VIF results more interpretable.
 **Action**: Generate a PNG heatmap of predictor correlations in `docs/` and reference it in `docs/paper.md`.
 **Constraint**: This task must run after T030.

- [ ] T065 [S] **Review Fix**: Validate that the "fail-loud" policy in T031 is correctly triggered during the execution gate (T036) by simulating a complete data source failure and confirming the pipeline halts with a clear error message.
 **Action**: Add a specific test case in `code/tests/test_fail_loud.py` that mocks all data sources to return errors and verifies the `RuntimeError` is raised.
 **Constraint**: This task must run after T031 and before T036.

- [X] T066 [S] **Review Fix**: Ensure the streaming rules in T032 are explicitly documented in the `docs/quickstart.md` to inform users of the memory constraints and the streaming strategy used.
 **Action**: Add a "Memory and Streaming" section to `docs/quickstart.md` detailing the chunking strategy and memory limits.
 **Constraint**: This task must run after T032 and before T029.

- [ ] T067 [S] **Review Fix**: Add a task to verify that the ground truth classification in T019 correctly handles threads with multiple accepted answers (if any exist in the dataset) and logs them as ambiguous.
 **Action**: Update `code/data/validation.py` to check for multiple `accepted_answer_id` values and log them to `data/processed/ambiguous_ground_truth.log`.
 **Constraint**: This task must run after T019.

- [ ] T068 [S] **Review Fix**: Ensure the GLMM model in T020 includes a check for model convergence and logs any non-convergent models with diagnostic information (e.g., number of iterations, Hessian status).
 **Action**: Add convergence checks in `code/data/modeling.py` and log warnings to `data/processed/model_convergence.log`.
 **Constraint**: This task must run after T020.

- [ ] T069 [S] **Review Fix**: Validate that the confidence intervals in T015b are correctly calculated using the bootstrapping method and that the number of resamples (1000) is sufficient for the desired precision.
 **Action**: Add a sensitivity test in `code/tests/test_sentiment.py` to verify the stability of the confidence intervals with different numbers of resamples.
 **Constraint**: This task must run after T015b.

- [ ] T070 [S] **Review Fix**: Ensure the final validation (T039) includes a check for the presence of all required artifacts in `data/processed/` and `state/` as defined in the data contracts.
 **Action**: Update `code/analysis/final_validation.py` to verify the existence and schema compliance of all expected files.
 **Constraint**: This task must run after T039.