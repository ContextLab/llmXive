# Tasks: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

**Input**: Design documents from `/specs/001-doomscrolling-anxiety/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)  
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)  
- Include exact file paths in descriptions.

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root  
- **Web app**: `backend/src/`, `frontend/src/`  
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`  

Paths shown below assume a single‑project layout – adjust based on `plan.md` structure.

---

## Phase 0: Project Initialization (Setup)

**Purpose**: Basic project structure and dependencies.

- [ ] T001b-i [P] Create root directory: `projects/PROJ-540-the-influence-of-social-media-doomscroll/`.
- [ ] T001b-ii BLOCKED BY T001b-i Create subdirectories: `code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `outputs/`.
- [ ] T001b-iii BLOCKED BY T001b-i Create `__init__.py` in the root directory `projects/PROJ-540-the-influence-of-social-media-doomscroll/`.
- [ ] T001b-iv BLOCKED BY T001b-i Create `__init__.py` in every immediate subdirectory (`code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `outputs/`).

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story or data ingestion can begin.

- [ ] T002 [P] Initialize Python 3.11 project with dependencies in `requirements.txt` (e.g., `pandas>=2.0.3`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `matplotlib>=3.7.0`, `seaborn>=0.12.0`, `requests>=2.31.0`, `pyyaml>=6.0.1`, `flake8>=6.1.0`, `black>=23.12.1`).
- [ ] T003a [P] Configure linting: Create `.flake8` config file at repository root with `max-line-length = 88` and `exclude = .git,__pycache__,build,dist`. **BLOCKED BY**: T002.
- [ ] T003b [P] Configure formatting: Create `pyproject.toml` at repository root with `[tool.black]` section setting `line-length = 88` and `target-version = ['py311']`. **BLOCKED BY**: T002.
- [ ] T004 [P] **Implement environment configuration management** in `code/config.py`:
  1. Create function to load dataset URLs and random seeds.
  2. **MUST** verify `seed` variable is not `None` and raise `ValueError` if missing.
  3. **MUST** log the seed at runtime to satisfy Constitution Principle I (Reproducibility). Use format: `LOG: SEED={seed_value} (INFO)` or `LOG: SEED NOT SET (WARNING)`.
  4. **MUST** explicitly pass the seed to `np.random.seed(seed)` for any stochastic preprocessing steps.
  5. **MUST** write the seed to `data/processed/metadata.json` with the exact key `random_seed` (e.g., `{"random_seed": 12345}`) to ensure persistence (Constitution Principle V).
- [ ] T005 [P] Setup error‑handling infrastructure for custom exceptions (`PowerLimitationError`, `MathematicalCouplingError`, `DataAvailabilityError`, `DataIntegrityError`) in `code/exceptions.py`.
- [ ] T006 [P] Create base data models/entities (`SurveyResponse`, `RegressionModel`) in `code/models.py`. **MUST** include fields `instrument_source` and `measurement_timepoint` in `SurveyResponse` to support T019a's schema validation and metadata checks.
- [ ] T007 [P] Configure logging infrastructure to `outputs/analysis.log`.
- [ ] T001c-impl BLOCKED BY T002 **Implement Orchestration Script** in `code/main.py`:
  1. Create the entry point that imports `ingest`, `clean`, `model`, `viz`, and `config`.
  2. **MUST** execute the pipeline in order: `ingest` → `clean` → `model` → `viz`.
  3. **MUST** handle exceptions from any module and log them to `outputs/analysis.log`.
  4. **MUST** return exit code 0 on success, non‑zero on failure.

**Checkpoint**: Foundation ready – data ingestion and user‑story implementation can now begin.

---

## Phase 2: Data Ingestion & Verification (US1)

**Purpose**: Download a public survey dataset, validate schema, and extract required variables.

- [ ] T037a [US1] **Implement Streaming Data Loader** in `code/ingest.py`.
  1. Create function `stream_data_source(url)` using `datasets.load_dataset(..., streaming=True)`.
  2. **MUST** yield the first chunk of data (e.g., first 100 rows) for schema inspection without downloading the full dataset.
  3. **MUST** raise `DataAvailabilityError` on connection errors.
- [ ] T037b [US1] **Implement Schema Validator** in `code/ingest.py`.
  1. Create function `validate_schema(chunk_df, required_columns)` that checks presence of required columns.
  2. **REQUIRED COLUMNS**: `news_exposure_freq`, `anxiety_score`, `baseline_anxiety`, `age`, `gender`.
  3. **MAPPING RULES**: (NHANES, GSS, Pew, YouGov) – see original spec.
  4. Return a boolean and list of missing columns.
- [ ] T037c-1 [US1] **Implement Source Iterator** in `code/ingest.py`.
  1. Function `get_fallback_sources()` returns ordered list: `['Pew', 'GSS', 'NHANES_2017_2018', 'YouGov']`.
- [ ] T037c-2 [US1] **Implement Schema Validation Loop** in `code/ingest.py`.
  1. Iterate through sources from T037c-1.
  2. Stream first chunk, validate schema, estimate sample size.
  3. **HALT** with `PowerLimitationError` if estimated N < 30 for the current source.
  4. **HALT** with `DataAvailabilityError` only if *all* sources fail schema or power checks.
  5. **OUTPUT**: `data/processed/metadata.json` with `source_url`, `verified_columns`, and `random_seed`.
- [ ] T037c-3 [US1] **Write Metadata Output** in `code/ingest.py`.
  1. Write final `metadata.json` containing `source_url`, `verified_columns`, and `random_seed`.
- [ ] T010a [US1] Implement data download in `code/ingest.py`: function `download_data(url, output_path)` that fetches data to `data/raw/` and raises on 404/timeout. **NO** synthetic fallback.
- [ ] T010b [US1] Implement data parsing & schema validation in `code/ingest.py`: function `parse_and_validate(raw_path)` that reads the file, checks required columns, raises `ValueError` if missing, and writes to `data/raw/parsed_data.csv`.
- [ ] T012 [US1] **Implement listwise deletion and power check** in `code/clean.py`.
  - Remove rows with missing `news_exposure_freq` or `anxiety_score`.
  - **HARD STOP** with `PowerLimitationError` if resulting N < 30.
  - Log a **Low Power** warning if 30 ≤ N < 100.
- [ ] T013 [US1] Save cleaned dataset to `data/processed/analysis_data.csv`.
- [ ] T014 [US1] Add logging for row counts, missing‑value stats, and power‑check results (info/warning/error as specified).

**Checkpoint**: User Story 1 fully functional and testable.

---

## Phase 3: Statistical Modeling (US2)

**Goal**: Fit a multiple linear regression, verify construct validity, compute correlations, and run diagnostics.

- [ ] T015 [P] [US2] Unit test in `tests/test_model.py`: verify Pearson correlation logic against a handcrafted synthetic dataset.
- [ ] T016 [P] [US2] Unit test in `tests/test_validity.py`: verify `MathematicalCouplingError` is raised when `baseline_anxiety` and `anxiety_score` share the same instrument/timepoint.
- [ ] T019a [US2] Implement construct‑validity check in `code/validity.py`.
  - Read `metadata.json`, detect coupling.
  - If coupling detected, **DROP** `baseline_anxiety`, set `coupling_risk = true`, log warning, and write `formula_variables` to `metadata.json`.
- [ ] T017 [US2] Implement Pearson/Spearman correlation calculation in `code/model.py`.
- [ ] T018a [US2] **Implement Formula Construction** in `code/model.py`.
  - Read `formula_variables` from `metadata.json`.
  - Build formula string dynamically (e.g., `anxiety_score ~ news_exposure_freq + age + gender`).
- [ ] T018b [US2] **Implement OLS Regression Fitting** in `code/model.py`.
  - Reusable `fit_regression_model(formula, df)` using `statsmodels.formula.api.ols`.
- [ ] T019b [US2] Implement assumption checks in `code/model.py`.
  - Linearity (scatter), Homoscedasticity (Breusch‑Pagan), Normality (Shapiro‑Wilk).
  - Output diagnostic metrics and PASS/FAIL status.
- [ ] T047a [US2] **Implement VIF Flagging Logic** in `code/model.py`.
  - Compute VIF for each predictor.
  - If any VIF > 10, add `"High VIF"` to `flags`, set the offending coefficient to `null` in the output JSON, and log details.
- [ ] T020 [US2] Implement proxy‑flagging logic in `code/model.py` for use of `general_anxiety` as a proxy. Add `"Proxy Used"` to `flags`.
- [ ] T021 [US2] Save regression results to `outputs/regression_results.json` (conforms to `contracts/output.schema.yaml`) including `flags`, VIF scores, and assumption checks.
- [ ] T022 [US2] Save correlation results to `outputs/correlation_results.json`.
- [ ] T022b [US2] Generate diagnostic plots (`outputs/diagnostics_residuals.png`, `outputs/diagnostics_qq.png`) with test statistics in titles/legends.

**Checkpoint**: User Stories 1 & 2 operational.

---

## Phase 4: Robustness Check & Visualization (US3)

**Goal**: Produce final visualizations and a conditional robustness analysis.

- [ ] T023 [P] [US3] Unit test in `tests/test_robustness.py`: verify top‑25 percentile filtering logic.
- [ ] T024 [P] [US3] Integration test in `tests/test_viz.py`: verify plot file exists and contains regression line.
- [ ] T025b-1 [US3] **Check Correlation Condition** in `code/robustness.py`.
  - If `social_media_engagement` exists, compute `r = corr(social_media_engagement, news_exposure_freq)`.
  - Proceed only if `r > 0.3`; otherwise log warning and set `"Robustness Skipped (r ≤ 0.3)"` flag.
- [ ] T025b-2 [US3] **Run Subset Model** in `code/robustness.py` (only when condition met).
  - Select top 25 percentile of `social_media_engagement`.
  - Re‑fit OLS using formula from T018a.
- [ ] T025b-3 [US3] **Generate Comparison Output** in `code/robustness.py`.
  - Write `outputs/robustness_results.json` with `status` (`RUN`, `SKIPPED_R_LOW`, etc.), `subset_n`, `coefficient`, `p_value`.
- [ ] T028 [US3] Implement scatter plot with regression line & 95 % CI in `code/viz.py`.
- [ ] T029 [US3] Save plot to `outputs/plot.png`.
- [ ] T030 [US3] **Generate Final Report** in `code/viz.py`.
  - Sections: Executive Summary, Methods, Results (regression, correlation, VIF flags), Robustness Check (results or skip reason), Limitations, Conclusion.
  - Cite JSON outputs and include metadata from `metadata.json`.
- [ ] T029b [US3] Implement robustness visualization in `code/viz.py` → `outputs/robustness_comparison.png` (only if robustness run).

**Checkpoint**: All user stories now independently functional.

---

## Phase 5: Polish & Cross‑Cutting Concerns

- [ ] T031 [P] **Documentation updates** in `README.md` and `docs/`.
  1. Usage section with command `python code/main.py`.
  2. Data section describing expected schema and verified dataset source.
  3. Generation of `quickstart.md` with step‑by‑step instructions.
- [ ] T032 [P] Code cleanup and refactoring: remove unused imports, extract helper functions. **Verification**: Run `flake8` and `black --check` on `code/` and verify 0 errors/violations.
- [ ] T033 [P] **Performance Benchmark (Real Data Only)**:
  1. Function `run_benchmark` in `code/main.py` runs the full pipeline on a streamed sample (first 10 000 rows) of the verified dataset.
  2. Measures total runtime, writes `benchmark.log`.
  3. Verifies `"PASS: Runtime < 60s"` in the log.
- [ ] T034 [P] Add unit tests for `code/config.py` (seed verification) and `code/robustness.py` (conditional logic).
- [ ] T041-impl [P] **Implement Validation Script** in `code/validation.py`:
  1. Reads `outputs/success_criteria_validation.json`, `outputs/regression_results.json`, `outputs/robustness_results.json`, and `benchmark.log`.
  2. **ASSERT SC-001**: `p_values['news_exposure_freq'] < 0.05`.
  3. **ASSERT SC-003**: Check that `sign(coefficients['news_exposure_freq']) == sign(robustness_result['coefficient'])` AND `robustness_result['p_value'] < 0.05`.
  4. Check SC‑002, SC‑004, SC‑005.
  5. Outputs a JSON report with PASS/FAIL for each.
  6. Handles missing files gracefully (reports FAIL).
- [ ] T035 [P] **Run quickstart.md validation**: execute the steps in `quickstart.md` and verify the pipeline runs without manual intervention. **Deliverable**: Generate `outputs/quickstart_validation.log`.

---

## Phase 6: Execution Verification & Final Audit (Blocking Completion)

- [ ] T038 [US1] **Execute Full Pipeline on Verified Dataset**:
  1. Run `python code/main.py`.
  2. Verify dataset download & streaming, schema validation, regression output, robustness (or skip) output, all plots, and final report `outputs/final_report.md`.
- [ ] T039 [US1] **Audit for Fabrication**:
  1. Inspect all JSON result files to ensure no hard‑coded or synthetic values.
  2. Verify `flags` correctly list `"Proxy Used"` when applicable and any other limitations.
- [ ] T040 [US1] **Verify Reproducibility**:
  1. Re‑run pipeline with same seed.
  2. Confirm bitwise (or tolerance‑based) equality of `outputs/regression_results.json`, `outputs/correlation_results.json`, `outputs/robustness_results.json`.

---

## Phase 7: Final Validation & Sign‑off

- [ ] T046 [P] **Validate Success Criteria**  
  Run `code/validation.py` (implemented in T041‑impl) to programmatically check SC‑001 – SC‑005 against generated artifacts.  
  - **Output**: `outputs/success_criteria_validation.json` containing `{ "SC-001": {"status":"PASS","value":…}, … }`.  
  - **Verification**: The JSON file exists, each criterion has a `"PASS"` or `"FAIL"` status, and the script logs its actions to `outputs/validation.log`.  
  - **Path**: `code/validation.py`, `outputs/success_criteria_validation.json`, `outputs/validation.log`.

- [ ] T042 [P] **Automated Fabrication Audit**  
  Implement fabrication-detection script in `code/audit.py` that scans all files in `code/` for banned patterns (e.g., `mock_`, `synthetic_`, `random.uniform` used in analysis, or hard-coded result arrays).  
  - **Verification**: `outputs/fabrication_audit.log` exists and reports `"NO FABRICATION DETECTED"`.  
  - **Path**: `code/audit.py`, `outputs/fabrication_audit.log`.

- [ ] T047 [P] **Generate Final Documentation**  
  Update `README.md` with a concise **Results Summary** (key regression coefficient, p‑value, R², any flags), known limitations (e.g., proxy use, low power), and reproducibility instructions (seed, command, data source).  
  - **Verification**: The README contains a **Results Summary** section that references values from `outputs/regression_results.json` and `outputs/robustness_results.json`.  
  - **Path**: `README.md`.

- [ ] T048 [P] **Archive Artifacts**  
  Create a zip archive `artifacts/project_artifact.zip` containing the directories `data/processed/`, `outputs/`, and `code/`.  
  - **Verification**: The zip file exists, can be opened, and includes the three top‑level directories with their contents.  
  - **Path**: `artifacts/project_artifact.zip`.

- [ ] T045 [P] **Sign‑off**  
  1. Generate `outputs/sign_off_report.md` that lists the status of all prior tasks (read from `outputs/task_status_log.json`).  
  2. Determine **Final project state**: `'Success'` if T046 reports all SCs as PASS; otherwise `'Documented Failure'`.  
  3. Include a brief statement of overall outcome and any outstanding limitations.  
  - **Verification**: `sign_off_report.md` exists, contains the task‑status table, and correctly reflects the success/failure outcome.  
  - **Path**: `outputs/sign_off_report.md`.

---

## Dependencies & Execution Order

| Phase | Depends on |
|------|-------------|
| 0 – Setup | – |
| 1 – Foundational | Phase 0 |
| 2 – Data Ingestion | Phase 1 |
| 3 – Modeling | Phase 2 |
| 4 – Robustness & Viz | Phase 3 |
| 5 – Polish | Phases 0‑4 |
| 6 – Execution Audit | Phases 0‑5 |
| 7 – Final Validation & Sign‑off | Phases 0‑6 |

**Parallel Opportunities**

- All `[P]` tasks within a phase can run concurrently as long as they touch different files.
- Different user‑story phases can be worked on in parallel by separate contributors.

---

*All tasks obey the platform’s constitution: real data only, no synthetic fall‑backs, CPU‑only execution (except where conditional GPU off‑load is automatically handled by the platform), and strict adherence to the specification’s functional requirements.*