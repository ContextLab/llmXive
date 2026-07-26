# Tasks: The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

**Input**: Design documents from `/specs/001-social-rejection-reward/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are REQUIRED for all User Stories to ensure validation logic is correct.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
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

**Purpose**: Project initialization, basic structure, and documentation. **CRITICAL**: T035a-Install and T035a-Usage MUST be completed before US-1 Independent Tests can be executed, as the tests require the system to be runnable and documented.

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw/`, `data/interim/`, `data/processed/`, `tests/`)
- [X] T002 Initialize Python 3.11 project with `pandas`, `numpy`, `scipy`, `statsmodels`, `pyyaml`, `requests` in `code/requirements.txt`
- [ ] T035a-Install [P] **Documentation**: Update `README.md` with installation steps. **Specifics**: Add "Installation" section with `pip install -r requirements.txt` and environment setup instructions. **Dependency**: Prerequisite for US-1 Independent Test execution.
- [ ] T035a-Usage [P] **Documentation**: Update `README.md` with usage instructions. **Specifics**: Add "Usage" section with a concrete example command `python code/main.py` and expected output paths. **Dependency**: Prerequisite for US-1 Independent Test execution.

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

**Goal**: Download and validate the single verified dataset `ds000208`. The system MUST verify that `ds000208` contains both the 'Rejection' (Cyberball) and 'Control' conditions required for a Within-Subjects (Repeated Measures) design. **If either condition is missing, the system MUST switch to a Between-Subjects design (One-Way ANOVA) rather than halting, as per FR-007.** The previous "Composite Dataset" and "Separate-Streams" strategies involving `ds003392` have been removed as scientifically invalid per the plan.

**Independent Test**: Execute ingestion script against a mock single-cohort file (pass) and a mock single-file missing-reward-task (design switch). Verify script halts with exit code 1 only if required **variables** are missing, but proceeds with Between-Subjects design if conditions are missing. **Note**: This test requires T035a-Install and T035a-Usage to be complete.

### Tests for User Story 1 (REQUIRED) ⚠️

- [X] T010 [P] [US1] Contract test in `tests/test_ingest.py::test_schema_validates_single_cohort` to assert `exit_code == 0` when single-cohort data with both conditions is found
- [X] T011 [P] [US1] Integration test in `tests/test_ingest.py::test_download_and_validate_single_file` to verify successful ingestion and design confirmation when data is valid, and `exit_code == 1` only when a required **variable** is missing (not condition)

### Implementation for User Story 1

- [X] T015a [US1] **Pre-Load Size Estimation**: Implement `estimate_dataset_size_from_api(url)` in `code/ingest.py`. **Fetches metadata (size, file count) directly from the OpenNeuro API for the PRIMARY candidate dataset BEFORE download.** **API Endpoint**: ` Name or service not known)"))]. **JSON Path**: `.files.size` (sum of all files). **If the API is unreachable, proceed to local file check (T015c) without halting.** **Halt execution with exit code 1 only if the estimated size > 7 GB** (referencing `config.MAX_RAM_GB=7` and `config` module). **MUST run BEFORE T012.**
- [X] T012 [US1] Implement `code/ingest.py` with `download_dataset(url)` function. **MUST verify the dataset contains the Cyberball task** by checking for BIDS filenames `task-cyb*` or JSON metadata keys `task: cyb`. Use a verified URL from the OpenNeuro repository for the Cyberball dataset. The research question concerns social exclusion effects in virtual environments. [UNRESOLVED-CLAIM: c_f0391683 — status=not_enough_info] The method involves functional magnetic resonance imaging (fMRI) with a Cyberball paradigm. [UNRESOLVED-CLAIM: c_d3057f73 — status=not_enough_info] References: (). **Logic**:
 1. Download the **Single-Cohort candidate** (ds000208).
 2. Generate `data/raw/dataset_manifest.json` with schema {url, status, checksum, source_file_count, openneuro_id} for the downloaded file.
 3. **Do NOT set `design_type` here.** Defer to T013b.
 4. **Integrated Memory Guard**: Monitor RAM usage during download (T015b logic) and check file size on disk (T015c logic) **integrated into this task**. **Dependency**: Must run after T015a (if API available).
 **Output Artifact**: Generate `data/raw/dataset_manifest.json` and verify it exists.
- [X] T015c [US1] **Post-Download Size Enforcement**: Implement `check_file_size_on_disk(file_path)` in `code/ingest.py`. **MUST verify the downloaded file size does not exceed a predetermined storage threshold**. **Halt with exit code 1 if exceeded.** **Dependency**: Must run after T012 download completes.
- [X] T013 [US1] Implement `validate_schema(df)` in `code/ingest.py` to check for `Condition` (Cyberball), `Reaction Time`, `Mood`. **Exit code 1 if required variables are missing.** **Output Artifact**: Generate `data/interim/validation_report.json` with schema {passed, missing_columns} and verify it exists. **Dependency**: Must run after T012.
- [X] T014 [US1] Implement `verify_single_cohort(df)` in `code/ingest.py` to ensure Participant IDs are consistent within the SINGLE dataset. If consistent, set `design_type="Within-Subjects"`. If inconsistent or missing, proceed to T013b.
- [X] T014b [US1] **Condition Availability Check (Single File)**: Implement `verify_conditions_present(df)` in `code/ingest.py`. **Runs unconditionally after T012 and T013.** **MUST check if BOTH 'Rejection' and 'Control' conditions exist in the single dataset.** **Output Artifact**: Generate `data/processed/condition_report.json` with schema {rejection_present: bool, control_present: bool, status: 'valid' | 'invalid'}. **Dependency**: Must run after T012. **Must trigger T013b upon completion.**
- [X] T017d [US1] **Single-Cohort Constraint Check (Passive)**: Implement `check_single_cohort_constraint(manifest)` in `code/ingest.py`. **MUST verify if the current data source is a Single-Cohort dataset** by checking `source_file_count` in `data/raw/dataset_manifest.json`. **If `source_file_count > 1`, report `is_single_cohort=False` but DO NOT halt.** This task runs **AFTER T014b** to ensure condition validation has occurred. **Dependency**: Must run after T014b.
- [X] T017e [US1] **Participant ID Matching**: Implement `check_participant_id_match(df)` in `code/ingest.py`. **Checks if Participant IDs are identical across the 'Rejection' and 'Control' conditions.** **Output**: Boolean `ids_match`. **Dependency**: Must run after T012.
- [X] T013b [US1] **Design Branch Decision (Central Gate)**: Implement `decide_design_branch(validation_report, condition_report, constraint_check, id_match)` in `code/ingest.py`. **Aggregates signals from T013, T014b, T017d, and T017e to explicitly set the `branch` signal.** **Logic**:
 1. If Single-Cohort Valid (T014) AND Conditions Present (T014b) AND IDs Match (T017e) -> `design_type="Within-Subjects"`.
 2. If Conditions Missing (T014b) OR IDs Mismatch (T017e) -> `design_type="Between-Subjects"`.
 3. If Required Variables Missing (T013) -> **Halt with exit code 1** (FR-001).
 4. If Size Limit Exceeded -> **Halt with exit code 1** (FR-001).
 **Output Artifact**: Generate `data/interim/design_branch.json` with schema {branch: 'single_cohort' | 'between_subjects', design_type: 'Within-Subjects' | 'Between-Subjects', reason: string}. **Dependency**: Must run after T013, T014b, T017d, T017e. **Linear Order**: T013 -> T014b -> T017d -> T017e -> T013b.
- [X] T017f [US1] **Design Switch Logic**: Implement `apply_design_switch(design_type)` in `code/ingest.py`. **If `design_type` is 'Between-Subjects', configure the pipeline for One-Way ANOVA.** **Log the switch.** **Dependency**: Must run after T013b.
- [X] T017c [US1] Implement `handle_data_unavailable()` in `code/ingest.py`. **Halt execution with exit code 1 and log "Data Unavailable" if required variables are missing.**
- [X] T018 [US1] Implement `log_design_switch()` in `code/ingest.py` to explicitly record the transition to "Within-Subjects" or "Between-Subjects" design in `data/processed/metadata.json`. **Schema**: Append entry {event: 'design_confirmed', design_type: str, timestamp:...}. **Dependency**: Must run after T017f.
- [X] T019 [US1] Implement `write_metadata(design_type, used_datasets)` in `code/ingest.py` to write the final `design_type` (Within-Subjects or Between-Subjects) AND the list of `used_datasets` (OpenNeuro IDs) to `data/processed/metadata.json` for downstream consumption.
- [X] T016b [US1] **Verify Checksum Integrity**: Implement `compute_and_verify_checksum(file_path)` in `code/ingest.py`. **MUST explicitly compute SHA-256 hash of the file and verify it against a known good source if available, or simply store the computed hash.** **Dependency**: Must run after T012 download, **BEFORE** T016.
- [X] T016 [US1] **Checksum & State Update**: Implement checksum generation (SHA-256) for downloaded files in `code/ingest.py`. **Write checksums directly to `state/projects/PROJ-258-the-effect-of-simulated-social-rejection.yaml`** in the `artifact_hashes` map per Constitution Principle V. **Structure**: `artifact_hashes: { <openneuro_id>: { sha256: '<hash>', size_bytes: <int> } }`. **CRITICAL**: Must also update the `updated_at` timestamp in the state file. **Dependency**: Must run after T016b and T013b and T019.
- [X] T040 [US1] **Explicit Data Source Citation**: Implement `write_data_citation(metadata)` in `code/ingest.py` to generate `data/raw/CITATION.md`. **Logic**: Read `data/processed/metadata.json` to determine `design_type` and `used_datasets`. **Dynamically cite ONLY the datasets listed in `used_datasets`** (one dataset for Within-Subjects or Between-Subjects). Include DOIs, access dates, and licenses for each. **This file MUST be referenced in the final report's Methods section.** **Dependency**: Must run after T019 and T016.
- [X] T041 [US1] **Fail-Loudly Guard**: Review `code/ingest.py` to ensure **NO** `try/except` blocks catch `requests.exceptions.RequestException` or `FileNotFoundError` to fallback to synthetic data. **If a download fails, the script MUST raise an unhandled exception and exit with code 1.** **Dependency**: Must run after T012.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. The pipeline must support both Within-Subjects and Between-Subjects designs using ds000208.

---

## Phase 4: User Story 2 - Preprocessing and Feature Extraction (Priority: P2)

**Goal**: Clean behavioral data, normalize reaction times, extract summary features (mean RT, avg mood), and **flag** outliers using IQR per Condition group. **Raw data must be preserved unchanged.**

**Independent Test**: Run preprocessing on sample subset; verify output CSV structure, memory logs ≤ 7 GB, and correct IQR outlier flagging. Verify raw data in `data/raw/` is unchanged.

### Tests for User Story 2 (REQUIRED) ⚠️

- [X] T028 [P] [US2] Contract test in `tests/test_preprocess.py::test_outlier_detection_iqr` to assert correct flagging per Condition group (column added, not rows removed)
- [X] T029 [P] [US2] Integration test in `tests/test_preprocess.py::test_memory_usage_under_limit` to verify memory stays ≤ 7 GB

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/preprocess.py` with `clean_data(df)` function
- [X] T021 [US2] Implement `normalize_rt(df)` in `code/preprocess.py` to standardize reaction times
- [X] T022 [US2] Implement `detect_outliers_iqr(df, group_col='Condition')` in `code/preprocess.py` to **add a boolean column `is_outlier`** using a standard interquartile range multiplier per group (FR-002). **DO NOT remove rows.** **Dependency**: Must run after T020.
- [X] T023 [US2] Implement `extract_features(df)` in `code/preprocess.py` to compute `mean_rt` and `avg_mood` per participant/condition
- [X] T024 [US2] Save intermediate data to `data/interim/preprocessed_data.csv` with `design_type` tag. **Ensure raw data in `data/raw/` remains unmodified (Constitution Principle III).** **Dependency**: Must run after T022.
- [X] T042 [US2] **Outlier Audit Trail**: Implement `log_outlier_removal()` in `code/preprocess.py` to write `data/interim/outlier_log.json` containing the count of **flagged** rows per condition and the specific IQR thresholds used. **Schema**: {condition: str, flagged_count: int, iqr_threshold: float}. **This log is required for reproducibility and to verify FR-002.** **Dependency**: Must run after T022.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Execute ANOVA (Repeated Measures for Within-Subjects; One-Way for Between-Subjects), apply FDR, generate sensitivity analysis, and export report. **The design is dynamic based on T013b.**

**Independent Test**: Run analysis on preprocessed data; verify output report contains p-values, effect sizes, sensitivity tables, and correct test selection logic.

### Tests for User Story 3 (REQUIRED) ⚠️

- [X] T025 [P] [US3] Contract test in `tests/test_analysis.py::test_anova_selection_logic` to assert correct ANOVA type selection (Repeated Measures vs One-Way)
- [X] T026 [P] [US3] Integration test in `tests/test_analysis.py::test_fdr_and_sensitivity` to verify FDR correction and sensitivity sweep

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `code/analysis.py` with `run_anova(df, design_type)` to select **Repeated Measures ANOVA** (`statsmodels.stats.anova.AnovaRM`) if `design_type="Within-Subjects"`, OR **One-Way ANOVA** (`scipy.stats.f_oneway`) if `design_type="Between-Subjects"`. **Input format**: Long format for Repeated Measures, Wide/Grouped for One-Way. **Dependency**: Must run after T024.
- [X] T028 [US3] Implement `apply_fdr(p_values)` in `code/analysis.py` using Benjamini-Hochberg method (FR-004)
- [X] T035 [US3] Implement `sensitivity_sweep(df, alpha_set={0.05, 0.1})` in `code/analysis.py` (FR-006) to sweep α and report result consistency.
- [X] T035b [US3] **Sensitivity Report Verification**: Implement `test_sensitivity_coverage()` in `tests/test_analysis.py`. **Assert that `reports/final_report.md` includes a Markdown table with header 'alpha' and contains valid result rows for EACH of the alpha values: 0.05, 0.1.** **Output Artifact**: Generate `tests/results/sensitivity_verification.json` with schema {passed: bool, missing_alphas: list}. **Failure Condition**: If verification fails, exit code 1. **Dependency**: Must run after T035.
- [X] T030 [US3] Implement `generate_report_logic(results, design_type)` in `code/report.py`. **Depends on T017/T019 (reads data/processed/metadata.json) and T035/T035b.** **Inject the phrase "associational" into the Limitations section.** **Output Artifact**: Generate `reports/final_report.md`. **Verification**: Assert report contains "associational", excludes "causal", and includes sensitivity table for α ∈ {0.01, 0.05, 0.1}.
- [X] T031 [US3] Implement `handle_convergence_warnings()` in `code/analysis.py`: **Add try/except block to catch convergence errors when N < 30 and output effect size confidence intervals.** **Output Format**: Append {convergence_warning: true, ci_95: [lower, upper]} to `data/processed/final_results.json`.
- [X] T033 [US3] Implement `save_final_results(results, design_type)` in `code/report.py` to write `data/processed/final_results.json` ensuring the `p_fdr` column is present (SC-003) and `design_type` is recorded (FR-008).
- [X] T034 [US3] Implement `verify_report_constraints()` in `tests/test_report.py` to assert that `reports/final_report.md` contains the exact phrase "associational" in Limitations and excludes "causal" in Results (FR-003).
- [X] T032 [US3] Save final results to `data/processed/final_results.json` and `reports/final_report.md`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T045 [P] **Documentation**: Generate `docs/api.md` from code docstrings.
- [X] T036 Code cleanup and refactoring in `code/`
- [X] T037a [P] **Performance CI**: Add timeout assertion to GitHub Actions workflow (`.github/workflows/ci.yml`) to enforce -hour limit (SC-002).
- [X] T037b [P] **Benchmarking**: Implement `code/benchmark.py` to generate `data/processed/performance_log.json` with runtime metrics for N=500.
- [X] T037c [US3] **CI Runtime Verification**: Implement `verify_ci_runtime()` in `code/benchmark.py`. **Runs the full pipeline on the target GitHub Actions runner (simulated via a dedicated CI job) and asserts that total execution time is < 6 hours.** **Output**: `data/processed/ci_runtime_verification.json` with `passed: true/false`. **Dependency**: Must run after T033 and T035, before T037a CI gate.
- [X] T038 [P] Additional unit tests in `tests/unit/`
- [X] T039 Run `quickstart.md` validation
- [X] T043 [US1] **Instrument Validation**: Implement `validate_mood_instruments(df)` in `code/ingest.py`. **Checks for presence of specific mood instruments (e.g., PANAS) in the dataset schema.** **Output**: Boolean `has_panas` and list of available instruments. **Dependency**: Must run after T012.
- [X] T044 [P] **Reproducibility Checklist**: Create `docs/reproducibility_checklist.md` verifying that all random seeds are set, all data sources are cited, and all "associational" constraints are met. **Format**: Markdown table with columns: Item, Status, Evidence. **This checklist must be completed before any final release.**

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
Task: "Integration test in tests/test_ingest.py::test_download_and_validate_single_file"

# Launch all models for User Story 1 together:
Task: "Implement code/ingest.py with download_dataset(url) function (verify single-cohort)"
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
- **CRITICAL**: The pipeline is now strictly single-dataset. **Merging distinct studies is forbidden.**
- **CRITICAL**: Data loading must fail loudly if the real source is unavailable; no synthetic fallbacks are permitted.
- **CRITICAL**: For large datasets, the system halts with exit code 1; no streaming logic is required for N ≤ 500.
- **CRITICAL**: All data sources must be real, verified, and explicitly cited. Synthetic data is forbidden for research results.
- **CRITICAL**: Memory guard (T015a) MUST run before data loading (T012) to prevent RAM overflow by fetching remote metadata.
- **CRITICAL**: Single-Cohort check (T017d) MUST run after condition validation (T014b) to prevent invalid Within-Subjects claims.
- **CRITICAL**: New tasks T040, T041, T042, T014b (updated), T016b, T037c, T035a-Install, T035a-Usage, T035b, T043 address reviewer concerns regarding data citation, fail-loudly guards, outlier audit trails, single-file condition validation, checksum verification, CI runtime verification, specific README content, and instrument validation.
- **CRITICAL**: T013b (Design Branch Decision) is the central gate for all design logic, resolving signals from T013, T014b, T017d, and T017e to enforce the single-dataset constraint and support the Between-Subjects fallback.
- **CRITICAL**: T015-MemorySafety (Consolidated) ensures memory constraints are enforced before, during, and after ingestion in a single logical flow.
- **CRITICAL**: T035b (Sensitivity Report Verification) mandates generating `tests/results/sensitivity_verification.json` to ensure SC-004 is met.
- **CRITICAL**: T037c (CI Runtime Verification) runs before T037a CI gate to verify SC-002 on the target environment.
- **CRITICAL**: T035a-Install and T035a-Usage are now in Phase 1 to ensure MVP executability.
- **CRITICAL**: Linear Order for Phase 3: T013 -> T014b -> T017d -> T017e -> T013b -> T017f.
- **CRITICAL**: T016b (Verify) MUST precede T016 (Write State).
- **CRITICAL**: T040 (Citation) MUST run after T016 (State Update) to ensure verified accuracy.