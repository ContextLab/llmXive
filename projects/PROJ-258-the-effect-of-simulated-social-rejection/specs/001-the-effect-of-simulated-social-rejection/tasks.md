# Tasks: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

**Input**: Design documents from `/specs/001-social-rejection-reward/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are REQUIRED for all User Stories to ensure validation logic is correct.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw/`, `data/interim/`, `data/processed/`, `tests/`)
- [X] T002 Initialize Python 3.11 project with `pandas`, `numpy`, `scipy`, `statsmodels`, `pyyaml`, `requests` in `code/requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` to manage paths, random seeds, α thresholds ({0.01, 0.05, 0.1}), and `MAX_RAM_GB=7`
- [X] T005 [P] Implement `code/__init__.py` and basic logging infrastructure for memory usage tracking
- [X] T006 Create `code/data_model.py` defining `Dataset`, `PreprocessedRecord`, and `AnalysisResult` entities with `design_type` field

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Design Determination (Priority: P1) 🎯 MVP

**Goal**: Download and validate datasets. The system MUST first attempt to find a **Single-Cohort** dataset (both tasks in one file). If found, proceed with Mixed ANOVA. If NOT found (e.g., ds000208 lacks reward task), the system MUST proceed to a **Separate-Streams** strategy (validate ds000208 and ds003392 independently) to enable a Between-Subjects ANOVA. **Merging distinct studies is strictly forbidden.**

**Independent Test**: Execute ingestion script against a mock single-cohort file (pass) and a mock separate-set (pass with design_type=Between-Subjects). Verify script halts with exit code 1 only if NO valid data source exists.

### Tests for User Story 1 (REQUIRED) ⚠️

- [X] T010 [P] [US1] Contract test in `tests/test_ingest.py::test_schema_validates_single_cohort` to assert `exit_code == 0` when single-cohort data is found
- [X] T011 [P] [US1] Integration test in `tests/test_ingest.py::test_download_and_validate_separate` to verify successful ingestion and design switching when single-cohort is missing

### Implementation for User Story 1

- [X] T015a [US1] **Pre-Load Size Estimation**: Implement `estimate_dataset_size_from_api(urls)` in `code/ingest.py`. **Fetches metadata (size, file count) directly from the OpenNeuro API or manifest URLs for BOTH candidate datasets (ds000208, ds003392) BEFORE any download.** **Halt execution with exit code 1 if the estimated combined size > 7 GB** (referencing `config.MAX_RAM_GB=7`). **MUST run BEFORE T012.**
- [X] T012 [US1] Implement `code/ingest.py` with `download_dataset(url)` function. **MUST verify the dataset contains the Cyberball task.** Use verified URLs: `https://openneuro.org/datasets/ds000208` (Cyberball) and `https://openneuro.org/datasets/ds003392` (Reward). **Logic**:
 1. Download the **Single-Cohort candidate** (ds000208) first.
 2. Generate `data/raw/dataset_manifest.json` with schema {url, status, checksum, source_file_count, openneuro_id} for the downloaded file.
 3. **Do NOT set `design_type` here.** Defer to T017d.
 **Output Artifact**: Generate `data/raw/dataset_manifest.json` and verify it exists. **Dependency**: Must run after T015a.
- [X] T013 [US1] Implement `validate_schema(df)` in `code/ingest.py` to check for `Condition` (Cyberball), `Condition` (Reward), `Reaction Time`, `Mood`. **Exit code 1 if required variables are missing AND no fallback dataset is available.** **Output Artifact**: Generate `data/interim/validation_report.json` with schema {passed, missing_columns} and verify it exists. **Dependency**: Must run after T012.
- [X] T014 [US1] Implement `verify_single_cohort(df)` in `code/ingest.py` to ensure Participant IDs are consistent within the SINGLE dataset. If consistent, set `design_type="Within-Subjects"`. If inconsistent or missing, proceed to T017d.
- [ ] T014b [US1] **Explicit ID Matching Logic (Single-Cohort Only)**: Implement `match_ids_set_intersection(df)` in `code/ingest.py`. **Performs a set intersection of Participant IDs** from the SINGLE dataset to confirm validity for Within-Subjects. **CRITICAL**: This function is ONLY called if `design_type` is tentatively "Within-Subjects" (Single-Cohort) to confirm validity. **If the design is Separate-Streams, this task is skipped.** **Dependency**: Must run after T012 (for Single-Cohort path) ONLY.
- [X] T015b [US1] **Runtime Memory Guard**: Add memory guard in `code/ingest.py` to monitor **runtime RAM usage** using `psutil`. **Halt execution with a non-zero exit code if the process memory footprint exceeds `config.MAX_RAM_GB` (7 GB).** This check occurs **AFTER** design determination (T013/T014) to allow fallback to smaller separate datasets if the single-cohort path is too large. **Dependency**: Must run after T015a.
- [X] T017d [US1] **Single-Cohort Constraint Check (Gatekeeper)**: Implement `check_single_cohort_constraint(manifest)` in `code/ingest.py`. **MUST verify if the current data source is a Single-Cohort dataset** by checking `source_file_count` in `data/raw/dataset_manifest.json`. **If `source_file_count > 1` (distinct studies), FORCE `design_type="Between-Subjects"` regardless of ID matching.** This task runs **IMMEDIATELY AFTER T016b** and determines the flow branch. **Dependency**: Must run after T016b.
- [ ] T017a [US1] **Separate-Streams Validation**: Implement `validate_separate_datasets(df_rejection, df_reward)` in `code/ingest.py`. **MUST validate ds000208 and ds003392 independently WITHOUT merging.** If both are valid, proceed to T017b. If either is missing/invalid, proceed to T017c. **Dependency**: Must run after T015a AND T017d (ONLY if T017d sets design_type="Between-Subjects").
- [ ] T017b [US1] **ID Validation for Separate-Streams**: Implement `validate_separate_id_availability(df_rejection, df_reward)` in `code/ingest.py`. **MUST check if Participant IDs exist in BOTH datasets** to ensure the Between-Subjects comparison is valid. **CRITICAL**: If datasets are distinct (per T017d), **MUST NOT** set `design_type="Within-Subjects"` even if IDs match. Only set `design_type="Between-Subjects"`. **Output Artifact**: Write `data/processed/id_match_status.json` with schema {match_count, design_type}. **Dependency**: Must run after T017d AND T017a (ONLY if T017d sets design_type="Between-Subjects").
- [X] T017c [US1] Implement `handle_data_unavailable()` in `code/ingest.py`. **Halt execution with exit code 1 and log "Data Unavailable" if no valid dataset or valid separate datasets are found.**
- [X] T018 [US1] Implement `log_design_switch()` in `code/ingest.py` to explicitly record the transition from "Single-Cohort attempt" to "Separate-Streams Fallback" in `data/processed/metadata.json`. **Schema**: Append entry {event: 'design_switch', from: 'Single-Cohort', to: 'Separate-Streams', timestamp:...}. **Dependency**: Must run after T017d.
- [X] T019 [US1] Implement `write_metadata(design_type, used_datasets)` in `code/ingest.py` to write the final `design_type` (Within-Subjects or Between-Subjects) AND the list of `used_datasets` (OpenNeuro IDs) to `data/processed/metadata.json` for downstream consumption.
- [X] T016 [US1] **Checksum & State Update**: Implement checksum generation (SHA-256) for downloaded files in `code/ingest.py`. **Write checksums directly to `state/projects/PROJ-258-the-effect-of-simulated-social-rejection.yaml`** in the `artifact_hashes` map per Constitution Principle V. **Key Format**: `artifact_hashes.{openneuro_id}` (e.g., `artifact_hashes.ds000208`). **Structure**: `artifact_hashes.<openneuro_id>: {sha256: '<hash>', size_bytes: <int>}`. **Dependency**: Must run after T016b.
- [X] T016b [US1] **Verify Checksum Integrity**: Implement `verify_checksum(file_path, expected_hash)` in `code/ingest.py`. **MUST explicitly verify** the computed hash matches the file content **BEFORE** T016 writes it to the state file. **If verification fails, raise an exception and halt.** **Dependency**: Must run after T012 download, before T016 and T017d.
- [ ] T040 [US1] **Explicit Data Source Citation**: Implement `write_data_citation(metadata)` in `code/ingest.py` to generate `data/raw/CITATION.md`. **Logic**: Read `data/processed/metadata.json` to determine `design_type` and `used_datasets`. **Dynamically cite ONLY the datasets listed in `used_datasets`** (one dataset for Within-Subjects, two for Between-Subjects). Include DOIs, access dates, and licenses for each. **This file MUST be referenced in the final report's Methods section.** **Dependency**: Must run after T019.
- [ ] T041 [US1] **Fail-Loudly Guard**: Review `code/ingest.py` to ensure **NO** `try/except` blocks catch `requests.exceptions.RequestException` or `FileNotFoundError` to fallback to synthetic data. **If a download fails, the script MUST raise an unhandled exception and exit with code 1.** **Dependency**: Must run after T012.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. The pipeline must support both Within-Subjects (if found) and Between-Subjects (fallback) paths without merging distinct studies.

---

## Phase 4: User Story 2 - Preprocessing and Feature Extraction (Priority: P2)

**Goal**: Clean behavioral data, normalize reaction times, extract summary features (mean RT, avg mood), and remove outliers using IQR per Condition group.

**Independent Test**: Run preprocessing on sample subset; verify output CSV structure, memory logs ≤ 7 GB, and correct IQR outlier flagging.

### Tests for User Story 2 (REQUIRED) ⚠️

- [X] T018 [P] [US2] Contract test in `tests/test_preprocess.py::test_outlier_detection_iqr` to assert correct flagging per Condition group
- [X] T019 [P] [US2] Integration test in `tests/test_preprocess.py::test_memory_usage_under_limit` to verify memory stays ≤ 7 GB

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/preprocess.py` with `clean_data(df)` function
- [X] T021 [US2] Implement `normalize_rt(df)` in `code/preprocess.py` to standardize reaction times
- [X] T022 [US2] Implement `detect_outliers_iqr(df, group_col='Condition')` in `code/preprocess.py` to flag/cap outliers using a standard interquartile range multiplier per group (FR-002)
- [X] T023 [US2] Implement `extract_features(df)` in `code/preprocess.py` to compute `mean_rt` and `avg_mood` per participant/condition
- [X] T024 [US2] Save intermediate data to `data/interim/preprocessed_data.csv` with `design_type` tag
- [ ] T042 [US2] **Outlier Audit Trail**: Implement `log_outlier_removal()` in `code/preprocess.py` to write `data/interim/outlier_log.json` containing the count of removed rows per condition and the specific IQR thresholds used. **This log is required for reproducibility and to verify FR-002.** **Dependency**: Must run after T022.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Execute ANOVA (Mixed for single-cohort; One-Way for separate), apply FDR, generate sensitivity analysis, and export report. **If the design is Between-Subjects, explicitly drop the "modulation" claim and frame results as "associational group differences".**

**Independent Test**: Run analysis on preprocessed data; verify output report contains p-values, effect sizes, sensitivity tables, and correct test selection logic.

### Tests for User Story 3 (REQUIRED) ⚠️

- [X] T025 [P] [US3] Contract test in `tests/test_analysis.py::test_anova_selection_logic` to assert correct ANOVA type selection
- [X] T026 [P] [US3] Integration test in `tests/test_analysis.py::test_fdr_and_sensitivity` to verify FDR correction and sensitivity sweep

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `code/analysis.py` with `run_anova(df, design_type)` to select Mixed ANOVA (Within) or One-Way ANOVA (Between). **If design_type is Between-Subjects, explicitly drop the "modulation" claim and flag the inability to test it.**
- [X] T028 [US3] Implement `apply_fdr(p_values)` in `code/analysis.py` using Benjamini-Hochberg method (FR-004)
- [X] T035 [US3] Implement `sensitivity_sweep(df, alpha_set={0.01, 0.05, 0.1})` in `code/analysis.py` (FR-006) to sweep α and report result consistency.
- [ ] T035b [US3] **Sensitivity Report Verification**: Implement `verify_sensitivity_coverage()` in `tests/test_analysis.py` or `code/report.py`. **Assert that `reports/final_report.md` includes a Markdown table with header 'alpha' (or similar) and contains valid result rows for EACH of the alpha values: '0.01', '0.05', '0.1'.** **Verification**: Ensure SC-004 is met by checking for non-null p-values for all three alphas. **Dependency**: Must run after T035.
- [X] T030 [US3] Implement `generate_report_logic(results, design_type)` in `code/report.py`. **Depends on T017/T019 (reads data/processed/metadata.json) and T035/T035b.** **If design_type is Between-Subjects, explicitly inject the phrase "associational" into the Limitations section.** **Output Artifact**: Generate `reports/final_report.md`. **Verification**: Assert report contains "associational", excludes "causal", and includes sensitivity table for α ∈ {0.01, 0.05, 0.1}.
- [X] T031 [US3] Implement `handle_convergence_warnings()` in `code/analysis.py`: **Add try/except block to catch convergence errors when N < 30 and output effect size confidence intervals.** **Output Format**: Append {convergence_warning: true, ci_95: [lower, upper]} to `data/processed/final_results.json`.
- [X] T033 [US3] Implement `save_final_results(results, design_type)` in `code/report.py` to write `data/processed/final_results.json` ensuring the `p_fdr` column is present (SC-003) and `design_type` is recorded (FR-008).
- [X] T034 [US3] Implement `verify_report_constraints()` in `tests/test_report.py` to assert that `reports/final_report.md` contains the exact phrase "associational" in Limitations and excludes "causal" in Results (FR-003).
- [X] T032 [US3] Save final results to `data/processed/final_results.json` and `reports/final_report.md`
- [ ] T043 [US3] **Power Analysis Report**: Implement `run_power_analysis(df, design_type)` in `code/analysis.py` to calculate post-hoc power for the observed effect size. **If power < 0.8, append a specific warning to `reports/final_report.md` under a "Statistical Power" subsection.** **Dependency**: Must run after T027.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a-Install [P] **Documentation**: Update `README.md` with installation steps. **Specifics**: Add "Installation" section with `pip install -r requirements.txt` and environment setup instructions.
- [ ] T035a-Usage [P] **Documentation**: Update `README.md` with usage instructions. **Specifics**: Add "Usage" section with a concrete example command `python code/main.py` and expected output paths.
- [X] T035b [P] **Documentation**: Generate `docs/api.md` from code docstrings.
- [X] T036 Code cleanup and refactoring in `code/`
- [X] T037a [P] **Performance CI**: Add timeout assertion to GitHub Actions workflow (`.github/workflows/ci.yml`) to enforce -hour limit (SC-002).
- [X] T037b [P] **Benchmarking**: Implement `code/benchmark.py` to generate `data/processed/performance_log.json` with runtime metrics for N=500.
- [ ] T037c [P] **Local Runtime Verification**: Implement `verify_local_runtime()` in `code/benchmark.py`. **Runs the full pipeline locally (or on a representative subset) and asserts that total execution time is < 6 hours.** **Output**: `data/processed/local_runtime_verification.json` with `passed: true/false`. **Dependency**: Must run before T037a CI gate.
- [X] T038 [P] Additional unit tests in `tests/unit/`
- [X] T039 Run `quickstart.md` validation
- [ ] T044 [P] **Reproducibility Checklist**: Create `docs/reproducibility_checklist.md` verifying that all random seeds are set, all data sources are cited, and all "associational" constraints are met. **This checklist must be completed before any final release.**

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data ingestion
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 preprocessed data

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
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test in tests/test_ingest.py::test_schema_validates_single_cohort"
Task: "Integration test in tests/test_ingest.py::test_download_and_validate_separate"

# Launch all models for User Story 1 together:
Task: "Implement code/ingest.py with download_dataset(url) function (verify single-cohort OR separate)"
Task: "Generate data/raw/dataset_manifest.json immediately after download"
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
- **CRITICAL**: The pipeline must support both Single-Cohort (Within-Subjects) and Separate-Streams (Between-Subjects) paths. **Merging distinct studies is strictly forbidden.**
- **CRITICAL**: Data loading must fail loudly if the real source is unavailable; no synthetic fallbacks are permitted.
- **CRITICAL**: For large datasets, the system halts with exit code 1; no streaming logic is required for N ≤ 500.
- **CRITICAL**: All data sources must be real, verified, and explicitly cited. Synthetic data is forbidden for research results.
- **CRITICAL**: Memory guard (T015a) MUST run before data loading (T012) to prevent RAM overflow by fetching remote metadata.
- **CRITICAL**: Single-Cohort check (T017d) MUST run after checksum verification (T016b) to prevent invalid Within-Subjects claims.
- **CRITICAL**: New tasks T040, T041, T042, T043, T014b, T016b, T037c, T035a-Install, T035a-Usage, T035b address reviewer concerns regarding data citation, fail-loudly guards, outlier audit trails, power analysis, ID matching logic, checksum verification, local runtime verification, and specific README content.
