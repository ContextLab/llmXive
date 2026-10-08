# Tasks: Gut Microbiome and Cognitive Decline Analysis

**Input**: Design documents from `/specs/001-investigating-the-correlation-between-gu/`
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

- [X] T001a Create root project directory structure using the exact command: `mkdir -p projects/PROJ-189-investigating-the-correlation-between-gu/{data/raw,data/processed,data/models,code,code/utils,tests,tests/contract,tests/integration,tests/unit,docs}`.
- [X] T001b Create `.gitignore` file at root with EXACT patterns: `data/raw/*`, `data/processed/*.parquet`, `__pycache__/`, `venv/`, `.env`, `*.pyc`, `.pytest_cache/`
- [X] T001c Initialize `README.md` with EXACT content: Title "Gut Microbiome and Cognitive Decline Analysis", Description "Investigating the Correlation Between Gut Microbiome Composition and Cognitive Decline in Aging Populations", Setup Instructions "python -m venv venv && source venv/bin/activate && pip install -r code/requirements.txt".
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (Must include: `pandas`, `scikit-learn`, `scipy`, `statsmodels`, `scikit-bio`, `numpy`, `seaborn`, `pytest`, `ruff`, `black`)
- [X] T003 Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections
- [X] T009 Setup environment configuration management for dataset paths and random seeds by creating `code/.env.example` with keys `AGP_URL`, `HRS_URL`, `RANDOM_SEED`, `MAX_RAM_GB`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement deterministic data fetching utilities with checksum validation in `code/utils/data_fetchers.py` (Must raise on checksum mismatch)
- [X] T006 Implement `setup_logger()` function in `code/utils/logging.py` that returns a logger configured to write to `data/processed/run.log` with format `[timestamp] [level] [module] [message]` and explicitly captures mismatch counts and validation results as required by US-1.
- [X] T007 Create base data models/entities (Sample, Taxon) in `code/utils/data_models.py` (Must define Pydantic models for Sample and Taxon)
- [X] T008 Implement CPU-only execution guard and resource limit checks (≤7GB RAM, ≤6h) in `code/utils/resource_guard.py` (Must raise `ResourceLimitExceeded` if limits exceeded)
- [X] T019 Write contract test code for correlation output schema (rho, p-value, adj-p-value) in `tests/contract/test_correlation.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw AGP 16S data and HRS cognitive metadata, merge by participant ID, filter for age ≥ 60, and produce a clean analysis-ready dataset using Rarefaction (per Spec FR-002) and document the process.

**Independent Test**: Can be fully tested by executing `code/01_data_ingestion.py` and `code/02_preprocessing.py` and verifying the output dataframe contains ≥ 500 rows where every row has non-null values for at least 5 microbial genera and cognitive score column.

### Implementation for User Story 1

- [X] T012 [US-1] Implement `fetch_and_stream_agp_data()` in `code/01_data_ingestion.py` to **stream the full AGP dataset** using `datasets.load_dataset("american_gut_project", streaming=True, chunksize=10000)` and implement strict real-data loading that raises `DataFetchError` immediately if the real AGP/HRS fetch fails. **Must explicitly log the chunking strategy, total rows processed, and the exact dataset version used (e.g., "american_gut_project")**. (Addresses "Large real datasets: STREAM" and "Loader must FAIL LOUDLY" rules). **Note**: The HuggingFace `american_gut_project` dataset is the programmatic interface to the Qiita/EBI data referenced in the Plan.
- [X] T013 [US-1] Implement HRS cognitive metadata fetcher from official HRS portal in `code/01_data_ingestion.py`
- [X] T014a [US-1] Implement `fetch_participant_ids()` in `code/01_data_ingestion.py` to extract unique IDs from raw AGP and HRS sources and return two sets.
- [X] T014b [US-1] Implement `merge_participant_ids()` in `code/01_data_ingestion.py` to intersect ID sets, return the merged DataFrame, and log the mismatch count.
- [X] T014c [US-1] Implement `validate_merge()` in `code/01_data_ingestion.py` to check overlap ≥ 500 samples, **validate that all required columns (age, sex, BMI, cognitive score) are present**, write mismatch counts and validation status to `data/processed/merge_log.json`, and raise `ValueError` if validation fails.
- [X] T015 [US-1] Implement `filter_and_impute()` function in `code/02_preprocessing.py` to filter for age ≥ 60, impute covariates (BMI, education), **validate that critical columns (age, sex, BMI, cognitive score) contain zero null values after imputation**, and raise `ValueError` if validation fails.
- [X] T016a [US-1] Implement `rarefy_counts()` in `code/02_preprocessing.py` to rarefy taxonomic tables to the **global minimum non-zero read depth** (enforcing a floor of 5000 if the global minimum is < 5000) and output `data/processed/rarefied_counts_temp.parquet`.
- [X] T016b [US-1] Implement `collapse_to_genus()` in `code/02_preprocessing.py` to aggregate rarefied counts to genus-level integer counts.
- [X] T016c [US-1] Implement `convert_to_relative_abundance()` in `code/02_preprocessing.py` to **convert the genus-level integer counts from T016b to relative abundances (floats)** and save the result as `data/processed/rarefied_relative_abundance.parquet`. (**Depends on T016b**).
- [X] T016d [US-1] Implement `verify_artifact_checksum()` in `code/02_preprocessing.py` to verify the integrity of `data/processed/rarefied_relative_abundance.parquet` by computing and storing its SHA256 hash in `data/processed/checksums.json`.
- [X] T017 [US-1] Implement `validate_sample_size_and_power()` in `code/02_preprocessing.py` to **calculate statistical power for the regression model** based on the effective N after filtering. **If effective N < 100**, the script MUST log a critical warning and optionally halt execution (configurable via env var), rather than proceeding with underpowered analysis. (Addresses "Insufficient sample size" edge case).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are "Write Test Code" tasks. They must be written AFTER implementation tasks but EXECUTED AFTER implementation tasks.

- [X] T010 Write contract test code for merged dataframe schema in `tests/contract/test_data_merge.py`
- [X] T011 Write integration test code for age filtering and missing value imputation in `tests/integration/test_preprocessing.py`

### Phase 3b: Test Execution (Run after Implementation)

- [X] T045 Execute contract tests for merged dataframe schema: **Run `pytest tests/contract/test_data_merge.py -v` and save results to `data/processed/test_report_merge.json`**. (**BLOCKED** until T010, T011, and T012-T017 complete)
- [ ] T046 Execute integration tests for age filtering and missing value imputation: **Run `pytest tests/integration/test_preprocessing.py -v` and save results to `data/processed/test_report_preprocessing.json`**. (**BLOCKED** until T010, T011, and T012-T017 complete; **REQUIRES** T011 to have been successfully executed to ensure file existence).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Associational Correlation Analysis (Priority: P2)

**Goal**: Compute Spearman rank correlations between genus-level microbial abundances and cognitive test scores with FDR correction and CLR transformation on rarefied data.

**Independent Test**: Can be fully tested by running `code/03_correlation_analysis.py` and verifying the output table contains p-values adjusted via FDR, with no unadjusted p-values used for significance claims, and confirming the input data was CLR-transformed (on relative abundances derived from rarefied data).

### Implementation for User Story 2

- [X] T020a [US-2] **Document Methodological Override**: Add a comment block in the header of `code/03_correlation_analysis.py` explicitly stating that **Spec FR-002 (Rarefaction) and FR-003 (Spearman) override the Plan Summary's mention of CSS/SparCC/SPIEC-EASI**. This task ensures the implementation adheres to the Spec, while acknowledging the Plan's status as an input artifact that requires correction. **Note**: The Plan must be updated to reflect that Rarefaction and Spearman correlation are the primary methods, not CSS/SparCC. (Addresses "Plan vs Spec" conflict).
- [X] T021 [US-2] Implement `apply_clr_transformation()` function in `code/03_correlation_analysis.py` that explicitly loads `data/processed/rarefied_relative_abundance.parquet` (floats derived from rarefied counts), applies Centered Log-Ratio (CLR) transformation, and saves the result to `data/processed/corpus_clr.parquet`. (**Depends on T016c**).
- [X] T022 [US-2] Implement `compute_spearman_correlation()` function in `code/03_correlation_analysis.py` to calculate Spearman rank correlations (ONLY method per Spec FR-003) between **the CLR-transformed data from T021** (loaded from `data/processed/corpus_clr.parquet`) and cognitive scores. (**Depends on T021**).
- [X] T023 [US-2] Implement `apply_fdr_correction()` function in `code/03_correlation_analysis.py` to apply Benjamini-Hochberg FDR correction (α = 0.05) on raw p-values.
- [X] T024a [US-2] Implement `filter_significant_pairs()` in `code/03_correlation_analysis.py` to filter results for adj-p < 0.05.
- [X] T024b [US-2] Implement `flag_associational()` in `code/03_correlation_analysis.py` to add column `interpretation` with value "associational" to significant pairs.
- [X] T024c [US-2] Implement `save_correlation_results()` in `code/03_correlation_analysis.py` to write the final table to `data/processed/correlation_results.csv` and log the "associational" framing to `data/processed/run.log`.
- [X] T025 [US-2] Generate summary report of significant genus-score pairs in `data/processed/correlation_results.csv`

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 Write contract test code for correlation output schema (rho, p-value, adj-p-value) in `tests/contract/test_correlation.py`
- [X] T020 Write integration test code for FDR correction logic in `tests/integration/test_correlation.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Robustness Validation (Priority: P3)

**Goal**: Train a Random Forest regressor with 5-fold Cross-Validation, validate against permutation null distribution, perform sensitivity analysis on rarefaction depth, and calculate VIF for collinearity on top predictive taxa.

**Independent Test**: Can be fully tested by executing `code/04_predictive_modeling.py` and `code/05_sensitivity_analysis.py` and verifying the hold-out R² score exceeds a high percentile threshold of the permutation null distribution (A sufficient number of shuffles will be performed to ensure robust statistical estimation, as determined by convergence criteria outlined in the literature (DOI:10.1038/nmeth.1226).) and memory usage remains within acceptable system limits.

### Implementation for User Story 3

- [X] T030 [US-3] Implement `train_random_forest()` function in `code/04_predictive_modeling.py` to train Random Forest regressor with **-fold cross-validation** (inner loop: hyperparameter tuning; outer loop: k-fold cross-validation removed) on **the CLR-transformed data from T021**. **Must log random seed and final hyperparameters to `data/processed/run.log` and `data/models/hyperparams.json`**. (FR-004, Plan Summary) (**Depends on T021**).
- [X] T031a [US-3] Implement `shuffle_labels()` in `code/04_predictive_modeling.py` to perform the label shuffles for the null distribution.
- [X] T031b [US-3] Implement `score_permutations()` in `code/04_predictive_modeling.py` to calculate R² for each shuffled dataset.
- [X] T031c [US-3] Implement `calculate_null_threshold()` in `code/04_predictive_modeling.py` to determine the **95th percentile** of the permutation null distribution, save to `data/processed/null_threshold.json`, and log seeds/params.
- [X] T032a [US-3] Implement `select_top_taxa()` function in `code/04_predictive_modeling.py` to identify **top N taxa (highest mean decrease in impurity, capped at a predefined limit or until cumulative importance > 80%)** and save list to `data/processed/top_taxa_initial.json`. **CRITICAL**: Must include an assertion that the artifact is written and valid before completion.
- [X] T033 [US-3] Implement `calculate_vif_and_filter()` function in `code/04_predictive_modeling.py` to **select top taxa (from T032a), calculate Variance Inflation Factors (VIF) for these taxa using the CLR-transformed data from T021 (data/processed/corpus_clr.parquet)**, filter out taxa with VIF > 5, and save the final filtered feature list to `data/processed/top_taxa_final.json`. (**Depends on T021, T032a**).
- [X] T034a [US-3] Implement `sweep_rarefaction_depths()` in `code/05_sensitivity_analysis.py` to **iterate over a discrete set of large integer values and min_depth**. For **each depth**, **re-execute the full pipeline (rarefaction -> relative abundance conversion -> CLR -> model training) from scratch** using the functions defined in T016a, T016b, T016c, T021, T030. **If RAM usage exceeds a predefined threshold during the sweep, fail gracefully (exit with code 1) to ensure the variance analysis is not computed on incomplete data; DO NOT skip the depth or reduce permutations.** (**Depends on T016a, T016b, T016c, T021, T030**).
- [X] T034b [US-3] Implement `re_evaluate_model()` in `code/05_sensitivity_analysis.py` to re-train and evaluate the model at each depth.
- [X] T034c [US-3] Implement `generate_variance_report()` in `code/05_sensitivity_analysis.py` to compile variance in R² and save to `data/processed/sensitivity_variance_report.json`.
- [X] T035 [US-3] Implement `monitor_ram_usage()` in `code/04_predictive_modeling.py` to **check available RAM before starting the permutation loop; if RAM < 7GB, log a warning and exit with code 1 immediately** to ensure a graceful CI failure (FR-007).
- [X] T036 [US-3] Implement `save_model_artifacts()` in `code/04_predictive_modeling.py` to save `model.pkl`, `shap_values.npy`, and `hyperparams.json` to `data/models/`.
- [X] T037 [US-3] Implement `verify_model_significance()` in `code/04_predictive_modeling.py` to **calculate the high percentile of the permutation null distribution (generated via multiple shuffles in the same run), compare the hold-out R² of the PRIMARY model (default depth) against this threshold, and write `data/processed/significance_verification.json` containing the threshold, R², and pass/fail status**. (**Depends on T031c**).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 Write contract test code for model metrics schema (R², RMSE, VIF) in `tests/contract/test_model_metrics.py`
- [X] T029 Write integration test code for permutation null distribution generation in `tests/integration/test_permutation.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042 Update `docs/paper_draft.md` Methods section with Rarefaction and 5-fold CV details
- [ ] T043 [US-3] Implement `extract_and_write_results()` to **read `data/processed/correlation_results.csv` and `data/processed/significance_verification.json`, then update the Results section of `docs/paper_draft.md`** with the extracted data. (**Depends on T037, T025**).
- [ ] T044 [US-3] Implement `extract_and_write_discussion()` to **read `data/processed/correlation_results.csv`, `data/processed/memory_log.txt`, and `data/processed/sensitivity_variance_report.json`, then update the Discussion section of `docs/paper_draft.md`** with implications and limitations. (**Depends on T034c, T025**).
- [ ] T038a [Polish] Refactor `code/utils/`: Extract `validate_sample_size_and_power()` into a standalone function in `code/utils/stats_helpers.py`.
- [ ] T038b [Polish] Refactor `code/utils/`: Rename `strict_real_data_loader` to `fetch_real_data_ensuring_failure` for clarity.
- [ ] T039a [Polish] Profile RAM usage in `code/04_predictive_modeling.py` during permutation loops and identify the top 2 memory-intensive lines.
- [ ] T039b [Polish] Optimize `code/04_predictive_modeling.py`: Reduce memory footprint of permutation loop by processing in batches of permutations.
- [ ] T040a [Polish] Write unit tests for `code/utils/data_fetchers.py` (checksum validation).
- [ ] T040b [Polish] Write unit tests for `code/utils/resource_guard.py` (RAM limit checks).
- [ ] T041 [Polish] Run quickstart validation: Execute `./code/quickstart.sh` and verify exit code 0.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output; US2 results inform feature selection

### Within Each User Story

- Tests (if included) MUST be written (T010/T011) AFTER implementation tasks, but EXECUTED AFTER implementation tasks (T045/T046).
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks can run in parallel
- All Foundational tasks can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all write-tests for User Story 1 together:
Task: "Write contract test code for merged dataframe schema in tests/contract/test_data_merge.py"
Task: "Write integration test code for age filtering and missing value imputation in tests/integration/test_preprocessing.py"
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
- **Blocked Tasks**: Tasks marked as BLOCKED (e.g., T045, T046) must not be executed until their dependencies are verified complete.
- [ ] T047 [US-1] **Verify Real Data Source**: Explicitly locate and document the exact URL or package ID for the AGP 16S data and HRS cognitive data in `code/.env.example` and `code/01_data_ingestion.py` (replacing any generic "official portal" references). **This task ensures the loader has a concrete, reachable source before execution**.
- [ ] T048 [US-1] **Implement Chunked Streaming**: Ensure `stream_agp_taxonomic_data` uses `datasets.load_dataset(..., streaming=True)` with explicit `chunksize` or `batch_size` parameters to guarantee memory safety on the free-tier runner, logging the chunk count and total rows processed.
- [ ] T049 [US-2] **Confirm CLR Input Source**: Add a validation step in `code/03_correlation_analysis.py` that asserts `data/processed/rarefied_relative_abundance.parquet` exists and contains float values before applying CLR, failing loudly if the upstream rarefaction task (T016c) was skipped or produced integers.
- [ ] T050 [US-3] **Guard Permutation Memory**: Implement a hard limit on the number of permutations and a check for available RAM before starting the permutation loop in `code/04_predictive_modeling.py`, reducing permutations or raising an error if RAM < 6GB to prevent OOM crashes.