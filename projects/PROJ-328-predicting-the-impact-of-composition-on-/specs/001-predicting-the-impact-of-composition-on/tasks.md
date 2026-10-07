# Tasks: Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

**Input**: Design documents from `/specs/001-predict-solder-hardness/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a-Create [P] **Initialize Project Directories**: Create the following directory structure: `data/raw`, `data/processed`, `data/outputs`, `code/ingestion`, `code/features`, `code/models`, `code/evaluation`, `code/visualization`, `code/utils`, `tests/contract`, `tests/integration`. **CRITICAL**: Ensure all directories exist. **Deliverable**: Verified directory structure.
- [ ] T001b-Script [P] **Create Init Script**: Create a shell script `scripts/init_dirs.sh` that performs the directory creation and verification logic. **CRITICAL**: The script must use `mkdir -p` and `test -d` to verify. **Deliverable**: `scripts/init_dirs.sh`.
- [ ] T001c-Verify [P] **Execute and Verify Init Script**: Run `scripts/init_dirs.sh` and verify the output log. **CRITICAL**: If verification fails, halt. **Deliverable**: Verification log.
- [X] T002 [P] Create `requirements.txt` at repository root with dependencies (PIN MINIMUM VERSIONS): `pandas`, `scikit-learn`, `xgboost`, `shap`, `numpy`, `matplotlib`, `pyyaml`, `requests`, `compositional>=0.2.0`, `pdfplumber`, `pytest`, `flake8`, `black`, `mendeleev`.
- [X] T003 [P] Create `.flake8` and `pyproject.toml` at repository root with specific linting rules (e.g., `max-line-length = 88`, `ignore = E203, W503`). **CRITICAL**: Verify file creation and content. Create a minimal Python file `code/utils/sample.py` and run `flake8` on it to verify configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005b [P] Create scaffolding for `code/features/` directory structure. **CRITICAL**: Verify existence of `code/features/__init__.py`, `code/features/transformer.py`, `code/features/descriptor_engine.py`, `code/features/collinearity.py`.
- [X] T006 [P] Create `code/config.py` with configuration constants: `MAX_ELEMENTS` (set to 5), `ROOM_TEMP_THRESHOLD_C` (25.0), `ROOM_TEMP_TOLERANCE_C` (5.0), `COMPOSITION_SUM_THRESHOLD` (95.0), `MIN_N_FOR_POWER` (50), `TARGET_N` (100). **CRITICAL**: Verify file creation and content. Ensure all values are explicitly defined as numeric types. **Do NOT** include `SENSITIVITY_EXTEND_STEP` in this file.
- [X] T007 [P] Create base data models/entities in `code/models/entities.py`. **CRITICAL**: Define `SolderComposition` class with attributes: `elemental_breakdown` (dict), `hardness_hv` (float), `alloy_family` (str), `source_citation` (str). Define `CompositionalDescriptor` class with attributes: `weighted_mean_atomic_mass`, `electronegativity_variance`, `atomic_radius_variance`, `weighted_avg_melting_point`, `valence_electron_concentration`. **Verify file creation.** **Depends on T001a-Create**.
- [ ] T008a-Query [P] **Query Research Sources**: Implement `code/ingestion/source_query.py` to query the spec's source list and known repositories. **CRITICAL**: Output a raw list of candidate URLs to `data/config/candidate_sources.txt` as a JSON list of objects: `[{"url": "...", "source_type": "api|pdf", "citation": "..."}]`. **CRITICAL**: Use the specific URLs from the spec (Materials Project API, NIST UCI, OpenAlloy) and known literature sources. **CRITICAL**: Reference Constitution Principle II defaults (CITATION_TITLE_OVERLAP_THRESHOLD=0.7) for validation logic. **CRITICAL**: **Specific API Details**:
 1. **Materials Project**: Endpoint `https://materialsproject.org/rest/v2/materials/`, Header `X-Api-Key: <TOKEN>`. Query for `solder` or `Sn` based alloys.
 2. **NIST**: Endpoint ` (scrape specific solder hardness tables) or ` (search for solder data).
 3. **OpenAlloy**: Endpoint ` (scrape alloy database).
 4. **Literature**: Use `https://arxiv.org/search/?query=solder+hardness&searchtype=all`. **CRITICAL**: **Fallback Logic**: If the API query for NIST or OpenAlloy fails (e.g., 404, timeout, or invalid endpoint), the script MUST log a `SOURCE_UNAVAILABLE` warning and proceed to rely on the Literature Scraping pipeline (T012d) as the primary fallback to meet FR-001. **CRITICAL**: **Output Artifact**: Generate `data/config/source_dependency_graph.json` containing a DAG of source availability and fallback paths. **Depends on T001a-Create**.
- [ ] T008a-Format [P] **Format Source List**: Implement `code/ingestion/format_sources.py` to read `candidate_sources.txt` and format it into `data/config/candidate_sources_formatted.json`. **CRITICAL**: Ensure valid JSON structure. **Depends on T008a-Query**.
- [ ] T008b [P] **Verify Research Sources**: Run the Reference-Validator Agent on the draft content from T008a-Format. Generate `specs/001-predict-solder-hardness/research_verified.md` containing only verified citations and URLs. **CRITICAL**: If verification fails for ANY source, the pipeline MUST HALT with `SourceVerificationError`. If verification succeeds, proceed. **CRITICAL**: If T008a-Query returns no sources, halt. **CRITICAL**: Use Constitution Principle II defaults (CITATION_TITLE_OVERLAP_THRESHOLD=0.7) for validation. **Depends on T008a-Format**.
- [X] T009a [P] **Create Utils Scaffolding**: Create `code/utils/` directory structure. **CRITICAL**: Create exact files: `code/utils/__init__.py`, `code/utils/helpers.py`. **Deliverable**: `code/utils/__init__.py`, `code/utils/helpers.py`. **Depends on T001a-Create**.
- [X] T009b [P] Create `code/utils/logger.py` with a `get_logger()` function that writes to `logs/pipeline.log` in JSON format. **CRITICAL**: This step depends on T009a. **Depends on T009a**.
- [X] T009c [P] **Populate `sources.yaml`**: Read the **verified** `research_verified.md` from T008b and populate `data/config/sources.yaml` with the specific, verified URLs and API endpoints. **CRITICAL**: This task MUST run after T008b. **CRITICAL**: If T008b failed (halted), this task is skipped. **CRITICAL**: **Artifact Path**: Read `research_verified.md`. **Depends on T008b**.

- [ ] T058 [P] **Verify Task Ordering**: Audit the dependency chain between T013 (Data Cleaning), T014 (Validation), T023b/T023c (Descriptor Engineering), and T025/T026 (Model Training). **CRITICAL**: Confirm that T023b/T023c explicitly depend on the output of T013 (`solder_hardness_cleaned.csv`) and that T025/T026 depend on T023b/T023c. Ensure no task attempts to verify FR-X using results from a file that is produced by a later task. **CRITICAL**: This task depends ONLY on task definitions (T006, T012d-Protocol-Doc, T023a, T024b), not their outputs. **CRITICAL**: **Output Artifact**: Generate `data/outputs/task_ordering_audit.json` containing a JSON representation of the dependency graph and a boolean `is_valid` flag. **CRITICAL**: **Schema**: `{"graph": {...}, "is_valid": bool, "issues": [...]}`. **Depends on T006, T012d-Protocol-Doc, T023a, T024b, T013, T014, T023b, T023c, T025, T026**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Aggregate and validate solder hardness dataset (Priority: P1) 🎯 MVP

**Goal**: Aggregate ≥100 unique solder alloy compositions with Vickers hardness from open sources into a unified dataset with validation.

**Independent Test**: Execute ingestion pipeline on GitHub Actions free-tier runner and verify output dataset contains ≥100 unique compositions with non-null hardness values and complete elemental breakdowns. If 50 ≤ N < 100, verify warning is emitted.

### Implementation for User Story 1

- [ ] T012a [P] [US1] **Fetch Data from API Sources**: Implement `code/ingestion/api_fetcher.py` to fetch data from verified/provisional API sources: 1) Materials Project API (v1, endpoint `/materials/...`, Header `X-Api-Key`), 2) NIST/UCI repositories (specific URL patterns), 3) OpenAlloy. **CRITICAL**: Pre-check: Verify `sources.yaml` exists. If missing, raise `ConfigError`. **CRITICAL**: Consolidate all API fetching logic into this single file. **CRITICAL**: Explicitly handle API authentication (if required) and rate limiting (e.g., `time.sleep(1)` between requests). **CRITICAL**: Read specific API endpoints, headers, and query parameters from `data/config/sources.yaml` before execution. **CRITICAL**: Do NOT fallback to synthetic data on failure; raise `DataFetchError` and skip source. **CRITICAL**: **Data Hygiene**: Save all fetched data to `data/raw/api_fetched.json` immediately upon successful fetch. **CRITICAL**: **Checksum**: Generate SHA256 checksum for `api_fetched.json` and append to `data/checksums.txt`. **CRITICAL**: **Output File**: `data/raw/api_fetched.json`. **Depends on T009c**.
- [ ] T012d-Protocol-Doc [P] [US1] **Define Systematic Literature Review Protocol (Document)**: Define the PRISMA protocol in `code/ingestion/slit_review_protocol.md` based on the **verified/provisional** sources from T008a-Query. **CRITICAL**: This task defines the search and extraction logic but does not execute it. **CRITICAL**: Use the source list from T008a-Query to define the protocol. **CRITICAL**: **Specific Search Strings**: `"solder alloy" AND "Vickers hardness" AND "composition"`. **CRITICAL**: **Inclusion Criteria**: Room temp, <5 elements, HV units. **CRITICAL**: **Exclusion Criteria**: >5 elements, non-room temp, non-HV units. **CRITICAL**: **Extraction Schema**: `alloy_id` (str), `elements` (dict of element:percent), `hardness_hv` (float), `citation` (str). **CRITICAL**: **Validation Logic**: Ensure `elements` sum to ≥95%, `hardness_hv` > 0. **CRITICAL**: **Output Format**: The document must explicitly list the sections: 'Search Strings', 'Inclusion Criteria', 'Exclusion Criteria', 'Extraction Schema', 'Validation Logic'. **Depends on T008a-Query**.
- [ ] T012d-Protocol-Schema [P] [US1] **Define Systematic Literature Review Protocol (Schema)**: Define the JSON schema for extracted data in `data/config/slr_schema.json` based on T012d-Protocol-Doc. **CRITICAL**: This task produces the schema file used by T012d-SLR-Exec. **CRITICAL**: Schema must include `alloy_id`, `elements`, `hardness_hv`, `citation`. **Depends on T012d-Protocol-Doc**.
- [ ] T012d-SLR-Exec [US1] **Execute Systematic Literature Review**: Implement the actual search, screening, and extraction logic in `code/ingestion/literature_scraper.py` to scrape tables from the specific PDFs listed in `data/config/sources.yaml`. **CRITICAL**: Logic: 1) Load source list from `sources.yaml`. If `sources.yaml` is missing or empty, raise `DataFetchError` with message "No verified sources available. Halting." 2) Load `COMPOSITION_SUM_THRESHOLD` and `MAX_ELEMENTS` from `code/config.py`. **CRITICAL**: **PDF Extraction Algorithm**: 1) Identify if a source is a PDF by checking the file extension or MIME type. 2) If it is a PDF, use `pdfplumber` to extract tables. 3) If it is not a PDF, skip and log `NON_PDF_SOURCE`. 4) Handle PDFs that require login or have dynamic content by logging `UNACCESSIBLE_PDF` and skipping. 5) Detect tables by finding rows with >3 numeric columns. 6) Merge multi-page tables by matching headers. 7) Parse columns: `element`, `percentage`, `hardness_hv`. 8) Handle missing headers by inferring from context. **CRITICAL**: During table extraction, validate each row: if `sum(elemental_percentages) < COMPOSITION_SUM_THRESHOLD` OR `len(elements) > MAX_ELEMENTS`, **FLAG** the record as 'excluded_pre_filter' and log to `data/raw/extraction_log.txt` with reason code, but do NOT write it to the raw CSV. 9) Extract tables from specified PDFs using `pdfplumber`. 10) Parse columns: `element`, `percentage`, `hardness_hv`. 11) Handle multi-page tables by merging. 12) **Handle N < 50**: If total N < 50 after scraping, **emit a severe warning `N_TOO_LOW` and proceed with a `reduced_n_flag` set to True**, explicitly marking status as 'Exploratory' in the output log. 13) **Handle 50 <= N < 100**: If 50 <= N < 100, proceed with a `reduced_n_flag` set to True and emit a warning `N_IN_REDUCED_RANGE`. 14) Handle partial data: Log failures to `ingestion_log.txt` but proceed if N >= 50. **CRITICAL**: This task depends on T008b (Verified Sources) to populate sources.yaml, allowing provisional state if verification fails. **CRITICAL**: **CRITICAL**: **Dependency**: This task MUST depend on T009c (Populate sources.yaml) to ensure the source list is ready. **CRITICAL**: **Depends on T008b, T012d-Protocol-Doc, T012d-Protocol-Schema, T006, T009c**. **CRITICAL**: **Output File**: `data/raw/literature_scraped.csv`.
- [ ] T012d-Filter [US1] **Filter Scraped Data**: Implement logic in `code/ingestion/filter_scraper.py` to apply strict exclusion criteria (e.g., >5 elements) to the raw scraped data from T012d-SLR-Exec. **CRITICAL**: This task runs AFTER scraping to ensure raw data is preserved. **CRITICAL**: Read `MAX_ELEMENTS` from `code/config.py`. **CRITICAL**: Output filtered data to `data/raw/filtered_raw.csv`. **CRITICAL**: **Depends on T012d-SLR-Exec**.
- [ ] T012g [US1] **Write Raw Data to Immutable Store**: Implement logic in `code/ingestion/aggregator.py` to write ALL fetched/scraped data (from T012a, T012d-SLR-Exec) to `data/raw/` as immutable files (e.g., `api_fetched.json`, `literature_scraped.csv`, `filtered_raw.csv`) BEFORE any cleaning. **CRITICAL**: Generate SHA256 checksums for all successfully fetched files and append to `data/checksums.txt`. **CRITICAL**: If any source fails, write checksums for only the successful files and set `partial_success: true` in `data/raw/.ingestion_status.json`. **CRITICAL**: **File Inventory**: `api_fetched.json`, `literature_scraped.csv`, `filtered_raw.csv`. **CRITICAL**: **Checksum Logic**: If T012a or T012d-SLR-Exec fails, do not halt; proceed with available data and log the failure. **CRITICAL**: **Data Hygiene**: Ensure all raw files are checksummed and recorded in `data/checksums.txt` before proceeding. **Depends on T012a, T012d-SLR-Exec, T012d-Filter**.
- [X] T013 [US1] Implement data cleaning and filtering logic in `code/ingestion/cleaner.py` to:
 - Exclude alloys with >5 elements (read threshold from `code/config.py` `MAX_ELEMENTS`)
 - Standardize hardness to HV units: **CRITICAL**: Read conversion factors from `code/config.py` (e.g., `HV_PER_GPA`). Do NOT hardcode.
 - Filter for room-temperature measurements only: verify column `measurement_temp_c` exists; filter where `abs(measurement_temp_c - config.ROOM_TEMP_THRESHOLD_C) <= config.ROOM_TEMP_TOLERANCE_C`.
 - **Manual Review Flagging**: Identify records where `abs(measurement_temp_c - config.ROOM_TEMP_THRESHOLD_C) > config.ROOM_TEMP_TOLERANCE_C` but `<= 2 * config.ROOM_TEMP_TOLERANCE_C` and write them to `data/processed/manual_review_queue.csv`.
 - **Validate Elemental Composition**: Iterate every record, sum elemental composition values. Read `COMPOSITION_SUM_THRESHOLD` from `code/config.py`. **CRITICAL**: If sum < `COMPOSITION_SUM_THRESHOLD`, **EXCLUDE** the record from the final output, log it to `data/processed/excluded_records.csv` with reason code `COMPOSITION_SUM_LOW`, and **DO NOT** include it in `solder_hardness_cleaned.csv`.
 - **Output**: **MUST** save cleaned data to `data/processed/solder_hardness_cleaned.csv`. **CRITICAL**: This file is the ONLY input for T014 and T023b/T023c. **CRITICAL**: If the file is empty or N < 50, **STILL** create the file (with headers) and write `power_limitation_warning: 'N < 50'` to `data/processed/.ingestion_status.json`. **CRITICAL**: Write `pass_rate` (passed/total_raw) to `data/processed/.ingestion_status.json`. **CRITICAL**: If N < 50, set `reduced_n_flag: true` in `data/processed/.ingestion_status.json`. **CRITICAL**: **Blocking**: If N < 50 and `reduced_n_flag` is false, halt US2. **Depends on T012g**.
- [X] T014 [US1] Implement validation reporting logic in `code/ingestion/validator.py` to check for non-null hardness and complete composition. **CRITICAL**: <!-- FAILED: unspecified -->
 1. **Input**: Read `data/processed/.ingestion_status.json` (output of T013) and `data/processed/solder_hardness_cleaned.csv`.
 2. **Calculate Composition Sums**: Explicitly calculate the sum of elemental columns for every record in the cleaned file to confirm no invalid records remain.
 3. **Enforce Threshold**: Confirm no records in `cleaned.csv` have composition sum < `COMPOSITION_SUM_THRESHOLD` (read from `code/config.py`).
 4. **Count Non-Null Hardness**: Count records where `hardness_hv` is not null in `cleaned.csv`.
 5. **Count Excluded Records**: Read `data/processed/excluded_records.csv` (produced by T013) and count total excluded records due to composition sum < 95%.
 6. **Threshold Check**: If total N < 50, log a severe warning and proceed with a reduced N flag (do NOT halt). If 50 <= N < 100, proceed but flag for power limitation.
 7. **Write Status**: Explicitly write `threshold_status` ('N>=100', '50<=N<100', 'N<50'), `exact_N`, `excluded_count`, `power_limitation_warning` (if applicable), and `reduced_n_flag` (bool) to `data/processed/.ingestion_status.json`. **This file is the single source of truth for SC-004 metrics.** **CRITICAL**: If N < 50, ensure `power_limitation_warning` is set to 'N < 50' and `reduced_n_flag` is true. **CRITICAL**: **Schema**: `{"threshold_status": str, "exact_N": int, "excluded_count": int, "power_limitation_warning": str|null, "reduced_n_flag": bool}`. **Depends on T013**.
- [ ] T014a [US1] **Calculate Composition Validation Metrics**: Read `data/raw/` files, `data/processed/excluded_records.csv` (from T013), and `data/processed/solder_hardness_cleaned.csv` (from T013) to calculate the *proportion* of records that met the composition sum threshold (≥95%) relative to the **original raw dataset**. **CRITICAL**: Output `data/processed/validation_metrics.yaml` with keys: `total_raw_records` (int), `passed_threshold_count` (int), `failed_threshold_count` (int), `pass_rate_percentage` (float). **CRITICAL**: This task explicitly addresses SC-004 by providing the measurable validation metric. **CRITICAL**: Schema: `total_raw_records` (int), `passed_threshold_count` (int), `failed_threshold_count` (int), `pass_rate_percentage` (float). **CRITICAL**: Formula: `pass_rate_percentage = (passed_threshold_count / total_raw_records) * 100`. **Depends on T012g, T013**.
- [ ] T014b [US1] **Aggregate Final Report**: Implement `code/ingestion/aggregate_final_report.py` to read `data/processed/.ingestion_status.json` (from T014) and `data/processed/report.yaml` (from T031c) and produce the final `data/processed/final_aggregated_report.yaml`. **CRITICAL**: This task aggregates the power limitation status and the model results into a single artifact for the paper draft. **Depends on T014, T031c**. <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [X] T016b [US1] **Generate Validation Report Script**: Write a Python script `code/ingestion/generate_validation_report.py` that reads `data/processed/.ingestion_status.json` and `data/processed/validation_metrics.yaml` and generates `data/processed/validation_report.yaml`. **CRITICAL**:
 - **Input Schema**: `threshold_status` (str), `exact_N` (int), `excluded_count` (int), `power_limitation_warning` (str), `pass_rate_percentage` (float).
 - **Output Schema**: `status` (str), `count` (int), `excluded_count` (int), `power_limitation_warning` (str), `pass_rate_percentage` (float).
 - **Logic**: Read JSON/YAML, map to YAML, write file.
 - **CRITICAL**: Ensure no undefined variables. **Depends on T014, T014a**.
- [ ] T016c [US1] **Verify Validation Report Generation (Integration Test)**: Run `code/ingestion/generate_validation_report.py` using the **actual** output files `data/processed/.ingestion_status.json` and `validation_metrics.yaml` produced by T014 and T014a. **CRITICAL**: Do NOT use mock data. If the script fails or produces invalid YAML, halt. **Depends on T016b, T014, T014a**. <!-- FAILED: unspecified -->
- [ ] T019 [US1] **Execute Validation Report Generation**: Run the script from T016b (verified by T016c) to produce `data/processed/validation_report.yaml`. **Depends on T016c**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---
## Phase 4: User Story 2 - Train and compare composition-to-hardness regression models (Priority: P2)

**Goal**: Train XGBoost and linear regression models with cross-validation, bootstrap comparison, SHAP analysis, and VIF diagnostics.

### Test-First: User Story 2 (OPTIONAL - only if tests requested) ⚠️
*Note: These tasks define contracts for T020-T021 and must be written before implementation code exists.*

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T021 [P] [US2] Integration test for model training pipeline in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [X] T023a [US2] Implement CLR transform utility in `code/features/transformer.py` using `compositional` library to handle closure problem. **Output**: A function to apply CLR to a vector of values.
- [ ] T023b [US2] **Apply CLR Transform**: Implement logic in `code/features/transformer.py` to apply the CLR transform (from T023a) to the raw elemental composition percentages from `data/processed/solder_hardness_cleaned.csv`. **Output**: Save the CLR-transformed composition matrix to `data/processed/clr_features.csv`. **CRITICAL**: This matrix is used for the model input, NOT for calculating physical descriptors. **CRITICAL**: Read-only input from `solder_hardness_cleaned.csv`. **CRITICAL**: Write to distinct output file `clr_features.csv`. **Depends on T023a, T013**.
- [ ] T023c [US2] **Compute Physical Descriptors**: Implement logic in `code/features/descriptor_engine.py` to calculate weighted mean atomic mass, electronegativity variance, atomic radius variance, weighted average melting point, and valence electron concentration **using the RAW elemental composition percentages from `data/processed/solder_hardness_cleaned.csv` and elemental property constants from `mendeleev`**. **CRITICAL**: **MUST use RAW elemental composition percentages** for physical descriptors. Physical descriptors must be computed from the raw data to satisfy FR-003 and FR-014 (the CLR transform is only for the model input). **CRITICAL**: Use `mendeleev` library for elemental properties. **CRITICAL**: **Specific Property Keys**: Use `element.electronegativity.pauling` for electronegativity. **CRITICAL**: Save the physical descriptors to `data/processed/descriptors.csv`. **CRITICAL**: This satisfies FR-003 (physical descriptors) and ensures mathematical correctness. **CRITICAL**: Read-only input from `solder_hardness_cleaned.csv`. **CRITICAL**: Write to distinct output file `descriptors.csv`. **CRITICAL**: **Dependency**: This task MUST depend on T013 to ensure `solder_hardness_cleaned.csv` exists. **CRITICAL**: **Output Schema**: `alloy_id` (str), `weighted_mean_atomic_mass` (float), `electronegativity_variance` (float), `atomic_radius_variance` (float), `weighted_avg_melting_point` (float), `valence_electron_concentration` (float). **Depends on T013, T023a**.
- [ ] T024 [US2] Implement VIF calculation in `code/features/collinearity.py` to flag predictors with VIF ≥ 5 (requires output from T023c).
- [ ] T054 [US2] **Enhance VIF Reporting**: Extend `code/features/collinearity.py` to output a detailed report `data/processed/vif_report.yaml` listing all predictors, their VIF scores, and a boolean `is_collinear` flag for VIF ≥ 5. **CRITICAL**: Ensures compliance with FR-013 and SC-006 by providing explicit collinearity diagnostics. **Depends on T024**.
- [ ] T024b [US2] **Configure CPU-Only Execution**: Create `code/models/config_cpu.py` to explicitly set all XGBoost and Linear Regression parameters to enforce CPU-only execution (e.g., `n_jobs=1`, `device='cpu'`, disable GPU acceleration flags).
- [ ] T024c [US2] **Verify CPU Execution**: Implement `code/models/verify_cpu.py` to run a small dummy training loop and assert that no GPU/CUDA devices are detected or used (e.g., check `torch.cuda.is_available()` or XGBoost device logs). **CRITICAL**: This task ensures FR-010 is verifiable. **Depends on T024b**.
- [ ] T025 [US2] Implement XGBoost training with grid search (≤10 combinations) in `code/models/xgboost_trainer.py`. **CRITICAL**: This script MUST import and use the configuration from `code/models/config_cpu.py` to enforce CPU-only execution. **CRITICAL**: Define the grid search parameters explicitly: `max_depth=[low, medium, high]`, `learning_rate=[low, moderate, high]`, `n_estimators=[low, moderate, high]`. **CRITICAL**: Ensure total combinations ≤ 10. **Depends on T024c, T023b, T023c**.
- [ ] T026 [US2] Implement Linear Regression baseline training in `code/models/linear_trainer.py`. **CRITICAL**: This script MUST import and use the configuration from `code/models/config_cpu.py` to enforce CPU-only execution. **Depends on T024c, T023b, T023c**.
- [ ] T027 [US2] Implement k-fold cross-validation for both models in `code/evaluation/cv.py` (requires T025/T026). **CRITICAL**: This task MUST generate cross-validation fold scores for both models. **Depends on T025, T026**.
- [ ] T027a [US2] **Implement Paired T-Test on CV Folds**: Implement a script `code/evaluation/paired_ttest.py` to perform a paired t-test on the cross-validation fold scores of XGBoost vs. Linear Regression. **CRITICAL**: This task explicitly addresses FR-004 and SC-002. Output metrics to `data/processed/paired_ttest_results.yaml` with keys: `t_statistic` (float), `p_value` (float), `significant` (bool). **CRITICAL**: Grid search parameters must be defined in `code/evaluation/grid_search_config.py` and used in T025/T026. **Depends on T027**.
- [ ] T028 [US2] Implement bootstrap resampling for confidence intervals on held-out test set in `code/evaluation/bootstrap.py`.
- [ ] T029b [US2] **Compute Bootstrap Test-Set CIs**: Implement Bootstrap Confidence Interval generation in `code/evaluation/bootstrap.py` to calculate confidence intervals for R² and RMSE on the **held-out test set**. **CRITICAL**: This task produces `data/processed/test_set_ci.yaml` with keys: `r2_mean` (float), `r2_ci_lower` (float), `r2_ci_upper` (float), `rmse_mean` (float), `rmse_ci_lower` (float), `rmse_ci_ci_upper` (float). **CRITICAL**: This task explicitly addresses FR-005 and SC-005. **Depends on T028, T025, T026**.
- [ ] T029d [US2] **Compute Bootstrap Model Comparison**: Implement Bootstrap Model Comparison in `code/evaluation/bootstrap.py` to compare XGBoost vs Linear Regression using a resampling approach on CV folds. Output metrics to `data/processed/bootstrap_comparison.yaml`. **CRITICAL**: This task is independent of the threshold sweep. **Depends on T029b**.
- [ ] T029a-Define [US2] **Define Sensitivity Thresholds Logic**: Create `code/evaluation/thresholds.py` to define the specific set of R² thresholds for the sensitivity analysis. **CRITICAL**: **DYNAMIC SWEEP RANGE**: Generate a threshold range based on the null baseline (R²=0.0) and the best observed cross-validated R² score from T027. The range should be defined as a sequence of values spanning from a lower bound to the optimal cross-validated $R^2$ ($best\_cv\_r2$), divided into 11 intervals. **CRITICAL**: **Do NOT** use a fixed 0-1 range. This satisfies FR-009's requirement to 'sweep the R² performance threshold over a range of values' relevant to the model's performance. **CRITICAL**: **Output**: Define the range logic (e.g., `numpy.linspace(0.0, best_cv_r2, 11)`). **CRITICAL**: **Dependency**: Depends on T027 to get the best CV score. **Depends on T027**.
- [ ] T029a-Generate [US2] **Generate Sensitivity Thresholds File**: Implement `code/evaluation/generate_thresholds.py` to read the logic from T029a-Define and output `data/config/sensitivity_thresholds.yaml`. **CRITICAL**: Output to `data/config/sensitivity_thresholds.yaml`. **Depends on T029a-Define**.
- [ ] T029c [US2] **Compute Sensitivity Metrics**: Implement Sensitivity Analysis in `code/evaluation/sensitivity.py`. **CRITICAL**: 1) Load thresholds from `data/config/sensitivity_thresholds.yaml` (dynamic range). 2) For each threshold T, calculate `fraction = (count of bootstrap R² > T) / total_bootstrap_samples`. 3) Generate output to `data/processed/sensitivity_analysis.yaml` and `data/outputs/sensitivity_plot.png`. **CRITICAL**: Output schema: `threshold` (float), `fraction_exceeding` (float). **CRITICAL**: **Validation**: Ensure the generated threshold range has a minimum width of 0.5 and at least 5 points. If not, raise an error. **Depends on T029a-Generate, T029b**.
- [ ] T030 [US2] Implement SHAP value calculation and top-k feature ranking in `code/evaluation/shap_analysis.py`. **CRITICAL**: Save ranked features to `data/processed/shap_ranking.yaml` with keys: `feature_name` (str), `mean_abs_shap_value` (float), `rank` (int). **Depends on T025, T026**.
- [ ] T031 [US2] Save model artifacts, metrics, and diagnostics to `models/` and `data/processed/`
- [ ] T031b [US2] **Generate Predictions and Bootstrap CIs**: Implement inference script in `code/evaluation/predict.py` to run the trained models (from T025/T026) on the test set. **CRITICAL**: Combine held-out test predictions with the bootstrap resampling logic (from T029b) to calculate R² and RMSE with confidence intervals. Save predictions to `data/processed/predictions.csv` and the calculated metrics (including CIs) to `data/processed/test_metrics.yaml`. **CRITICAL**: This task produces the `test_metrics.yaml` artifact required by T035. **Depends on T025, T026, T029b**.
- [ ] T031c [US2] **Generate Report YAML**: Create `code/evaluation/generate_report.py` to produce `data/processed/report.yaml` containing summary metrics and **inherent associational framing**. **CRITICAL**: This task MUST include the "Associational Analysis Only" warning in the metadata of the report. **CRITICAL**: This task MUST include the "Power Limitation" warning if N < 100 (read from `data/processed/.ingestion_status.json`). **CRITICAL**: This task is the sole producer of the framing metadata; no post-hoc injection tasks are allowed. **CRITICAL**: **Schema**: `associational_framing_warning` (str: "Findings are associational, not causal."), `power_limitation_warning` (str: "Statistical power limited due to N < 100." if applicable), `r2_mean` (float), `rmse_mean` (float), `r2_ci_lower` (float), `r2_ci_upper` (float), `rmse_ci_lower` (float), `rmse_ci_upper` (float). **CRITICAL**: This task does NOT scan the paper draft (which does not exist yet). **CRITICAL**: **Dependency**: Depends on T027a (Paired T-Test) which is now [X]. **Depends on T025, T026, T030, T027a, T014**.
- [ ] T035b [US2] **Aggregate Sensitivity Metrics**: Create `code/evaluation/aggregate_sensitivity.py` to read `data/processed/sensitivity_analysis.yaml` and generate a synthesized summary table `data/processed/sensitivity_summary.yaml` with columns: `threshold`, `fraction_exceeding`, `interpretation`. **CRITICAL**: This task ensures the paper draft receives interpretable data, not raw YAML. **Depends on T029c**.
- [ ] T042b [US2] **Verify Compute Feasibility**: Implement `code/evaluation/verify_runtime.py` to run the full pipeline on a subset of data and verify that total runtime is <6 hours, peak RAM <7GB, and disk usage <14GB. **CRITICAL**: This task explicitly addresses SC-007. **Depends on T012d-SLR-Exec, T013, T023b, T023c, T025, T026, T027, T028, T029c, T030, T031b, T031c, T036, T037, T038**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate interpretable visualizations and partial dependence plots (Priority: P3)

**Goal**: Generate scatter plot of predicted vs. measured hardness with error bars and partial dependence plots for top features.

- [ ] T036 [US3] Implement scatter plot generation in `code/visualization/scatter.py` with % CI error bars (requires T031b predictions).
- [ ] T037 [US3] Implement partial dependence plot generation in `code/visualization/pdp.py` for top-ranked SHAP features (requires T030 output).
- [ ] T038 [US3] Save all plots to `data/outputs/` with correct labels and units.
- [ ] T035 [US3] **Generate Paper Draft**: Create `specs/001-predict-solder-hardness/paper_draft.md` containing the methodology, results, and discussion sections. **CRITICAL**: **CRITICAL**: Use the template `specs/001-predict-solder-hardness/ppaper_template.md`. **Include sections**: Abstract, Methods, Results (with T031b metrics), Discussion, Limitations. **CRITICAL**: The "Limitations" section MUST explicitly state that findings are associational, not causal, and report any power limitations. **CRITICAL**: Dependencies: T031b, T036, T037, T038, T054, T035b, T014b, T031c. **Depends on T014b, T031c, T031b, T036, T037, T038, T054, T035b**. (Added dependencies on Sensitivity Summary, VIF, and Final Aggregated Report).
- [ ] T056 [US3] **Standardize Associational Framing**: Update `specs/001-predict-solder-hardness/paper_draft.md` (from T035) and `data/processed/final_aggregated_report.yaml` (produced by T014b) to include a prominent "Limitations" section explicitly stating that findings are associational, not causal, due to the observational nature of the data. **CRITICAL**: Ensures compliance with FR-007 and prevents causal over-interpretation. **CRITICAL**: This task acts as a refinement step after T035. **Depends on T014b, T035**.
- [ ] T057 [US3] **Associational Framing Audit**: Implement `code/evaluation/framing_audit.py` to scan the `paper_draft.md` (from T056) for causal language (e.g., "causes", "drives", "effect") in the Discussion section. **CRITICAL**: If causal language is detected, raise a `FramingViolationError` and halt. **CRITICAL**: This task ensures the final paper complies with FR-007. **CRITICAL**: **Depends on T056**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `docs/`
- [ ] T041 Code cleanup and refactoring
- [ ] T043 [P] Additional unit tests in `tests/unit/`
- [ ] T044 Run quickstart.md validation
- [ ] T058 [P] **Verify Task Ordering**: Audit the dependency chain between T013 (Data Cleaning), T014 (Validation), T023b/T023c (Descriptor Engineering), and T025/T026 (Model Training). **CRITICAL**: Confirm that T023b/T023c explicitly depend on the output of T013 (`solder_hardness_cleaned.csv`) and that T025/T026 depend on T023b/T023c. Ensure no task attempts to verify FR-X using results from a file that is produced by a later task. **CRITICAL**: This task depends ONLY on task definitions (T006, T012d-Protocol-Doc, T023a, T024b), not their outputs. **CRITICAL**: **Output Artifact**: Generate `data/outputs/task_ordering_audit.json` containing a JSON representation of the dependency graph and a boolean `is_valid` flag. **CRITICAL**: **Schema**: `{"graph": {...}, "is_valid": bool, "issues": [...]}`. **Depends on T006, T012d-Protocol-Doc, T023a, T024b, T013, T014, T023b, T023c, T025, T026**.
- [ ] T059-Stream [US1] **Implement Chunked CSV Loader**: Implement `code/ingestion/stream_loader.py` to process real data in chunks using standard Python `csv` module (for NIST CSVs) and `requests` with pagination (for APIs). **CRITICAL**: Do NOT shrink to a toy dataset. The task must state the exact streaming/sampling rule (e., "process all rows in manageable chunks") and output a warning if a sample is taken. **CRITICAL**: Do NOT use `datasets.load_dataset` as it is not applicable to the defined sources. **CRITICAL**: **Chunk Size**: rows. **CRITICAL**: **Threshold**: > 50MB. **CRITICAL**: **Final Chunk Logic**: Process the final partial chunk normally; do not drop it. **CRITICAL**: **Memory Check**: Use `psutil` to check memory usage before loading a chunk; if > 50MB, switch to streaming mode. **Rationale**: Ensures compliance with the "Large real datasets: STREAM the real data" rule and prevents fabrication. **Depends on T012g**.
- [ ] T059-Integrate [US1] **Integrate Stream Loader**: Integrate `code/ingestion/stream_loader.py` into the ingestion pipeline (`code/ingestion/aggregator.py`). **CRITICAL**: Ensure the pipeline switches to streaming mode if dataset size exceeds memory limits. **Depends on T059-Stream**.

---

## Revision Tasks (Addressing Analysis Findings)

**Purpose**: New tasks added to resolve specific issues identified in the analysis phase.

### Revision: Data Ingestion Robustness

- [ ] T050-API [US1] **Implement Strict API Fetching**: Modify `code/ingestion/api_fetcher.py` to remove ALL `try/except` blocks that fall back to **synthetic data generation**. **CRITICAL**: Retain `try/except` blocks for transient network errors to allow retries or graceful skipping. **CRITICAL**: If a real data fetch fails, raise `DataFetchError` and skip source. **CRITICAL**: Do NOT halt on partial failures unless N = 0. **Depends on `code/ingestion/api_fetcher.py`**.
- [ ] T050-LIT [US1] **Implement Strict Literature Scraping**: Modify `code/ingestion/literature_scraper.py` to remove ALL `try/except` blocks that fall back to **synthetic data generation**. **CRITICAL**: Retain `try/except` blocks for transient errors. **CRITICAL**: If a real data fetch fails, raise `DataFetchError` and skip source. **CRITICAL**: Do NOT halt on partial failures unless N = 0. **Depends on `code/ingestion/literature_scraper.py`**.

### Revision: Model Training & Diagnostics

- [ ] T053 [US2] **Explicitly Document CLR vs. Physical Descriptors**: Update `code/features/descriptor_engine.py` to add inline comments clarifying that CLR transforms are applied to raw percentages for model input, while physical descriptors are computed from the **RAW** percentages as per Plan.md and FR-003/FR-014. **CRITICAL**: Prevents confusion about the dual usage of composition data. **Depends on T023b, T023c**.
- [ ] T055 [US2] **Add Sensitivity Analysis Visualization**: Update `code/evaluation/sensitivity.py` to ensure `data/outputs/sensitivity_plot.png` clearly labels the x-axis as "R² Threshold" and y-axis as "Fraction of Bootstrap Samples Exceeding Threshold". **CRITICAL**: Ensures the visualization meets SC-005 requirements for interpretability. **Depends on T029c**.

---

## Re-plan Section (Audit Trail)

**Purpose**: Record of previously rejected tasks and their resolution status.

**Previously Rejected Tasks (Resolved in this revision)**:
- T012g: [X] Resolved. Now marked pending.
- T016c: [X] Resolved. Now marked pending.
- T023b: [X] Resolved. Now marked pending.
- T023c: [X] Resolved. Now marked pending.
- T027a: [X] Resolved. Now marked pending.
- T029b: [X] Resolved. Now marked pending.
- T029d: [X] Resolved. Now marked pending.
- T029a: [X] Resolved. Now marked pending.
- T029c: [X] Resolved. Now marked pending.
- T030: [X] Resolved. Now marked pending.
- T031b: [X] Resolved. Now marked pending.