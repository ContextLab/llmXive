# Tasks: Quantifying the Impact of Code Authorship Diversity on Software Security

**Input**: Design documents from `/specs/001-quantify-authorship-diversity-security/`
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

- [X] T001 Create project structure per implementation plan. Create the following directories and files: `code/`, `code/__init__.py`, `code/config.py`, `code/data/`, `code/data/__init__.py`, `code/analysis/`, `code/analysis/__init__.py`, `data/`, `data/raw/`, `data/processed/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `requirements.txt`, `README.md`.
- [X] T002 Initialize Python 3.11 project with pinned dependencies. Create `requirements.txt` with exact versions: `pandas==2.1.0`, `statsmodels==0.14.0`, `scikit-learn==1.3.0`, `requests==2.31.0`, `gitpython==3.1.37`, `pyyaml==6.0.1`, `numpy==1.24.0`, `scipy==1.11.0`, `pytest==7.4.0`.
- [X] T003 [P] Configure linting and formatting tools. Create `pyproject.toml` with `[tool.black]` (line-length=88) and `.flake8` (max-line-length=88, exclude=venv) files.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with paths, constants, random seeds, and NVD/GitHub API configuration.
- [X] T005 [P] Setup data directory structure (`data/raw/`, `data/processed/`) and schema definitions in `contracts/`.
- [ ] T006 [P] Implement `code/data/generate_target_list.py` to fetch the **full target list** of GitHub repos via GitHub API. Sort the list by `url` column alphabetically. **Output**: `data/raw/target_list.csv`. **Schema**: Columns must be `url`, `primary_language`, `stars`, `age`. Ensure `primary_language` is explicitly mapped from the API `language` field. **Verification**: Assert file exists and contains exactly `len(target_list)` rows. <!-- FIXED: Output schema column name, added output path and verification step -->
- [X] T007 [P] Implement `code/data/download_nvd.py` to download, merge, and deduplicate NVD/CVE JSON feeds (historical range) with checksum verification. Output `data/raw/nvd_cve_merged.json.gz` and `data/raw/nvd_cve_merged.json.gz.sha256`.
- [ ] T008a [P] [US1] Implement `code/data/extract_github.py` (Part 1: Clone) to perform shallow clones (`--shallow-since=2015-01-01`) for each repo in `target_list.csv`. Output a temporary list of successful clone paths. <!-- FIXED: Atomic split -->
- [ ] T008b [US1] Implement `code/data/extract_github.py` (Part 2: Parse) to parse `git log` from the cloned paths for unique authors (with ≥ 1 line of code committed). **Constraint**: If T008a fails for a repo, the script MUST FAIL LOUDLY (raise exception) and log the error. It MUST NOT fall back to a full `git clone` or `--depth=500` as this violates Constitution Principle VI. **Output**: A temporary CSV with `url` and `unique_authors`. This task MUST run sequentially after T008a failure detection, NOT in parallel. <!-- FIXED: Removed [P], enforced Constitution VI, removed fallback -->
- [ ] T008c [P] [US1] Implement `code/data/extract_github.py` (Part 3: cloc & Merge) to run `cloc --by-file` on cloned paths, calculate `kloc`, and merge with `unique_authors` and `primary_language` (from target list). Output `data/processed/github_raw_metrics.csv` (columns: `url`, `primary_language`, `unique_authors`, `raw_line_count`, `kloc`). <!-- FIXED: Atomic split, enforced schema -->
- [X] T009 [P] Implement `code/data/merge_datasets.py` (Part 1: Merge) to join GitHub metrics with NVD CVE counts using exact URL matching. Output `data/processed/repo_metrics.csv` (columns: `url`, `primary_language`, `unique_authors`, `kloc`, `cve_count`, `project_age`, `release_count`).
- [X] T009b [P] Implement `code/data/merge_datasets.py` (Part 2: Validation) to enforce **exact URL matching** as per FR-002. If a URL in the target list has no exact match in NVD, set `cve_count` to 0. Flag ambiguous matches (e.g., substring matches) in logs but do not merge them.
- [ ] T010 [P] Create unit tests for data ingestion logic:
 - `tests/unit/data/test_download_nvd.py::test_nvd_checksum_verification`: Assert SHA256 matches expected value.
 - `tests/unit/data/test_extract_github.py::test_author_count_calculation`: Mock git log output with lines: "Author A", "Author B", "Author A". Assert unique author count is.
 - `tests/unit/data/test_merge_datasets.py::test_url_matching`: Mock NVD data, assert exact match logic works and ambiguous matches are ignored.
 **Verification**: Run `pytest tests/unit/data/` and assert exit code 0. <!-- FIXED: Added verification step -->
- [X] T013 [P] [US1] Add logging in `code/data/merge_datasets.py` for skipped repositories and ambiguous NVD matches. Use `logging.WARNING` for skips and `logging.ERROR` for ambiguous matches. Log format: `"[REPO_URL] Reason: <reason>"`. Write to `logs/merge_warnings.log`.
- [X] T014 [P] [US1] Implement a validation function in `code/data/merge_datasets.py` that checks `repo_metrics.csv` for null values in `kloc` and `cve_count`. If nulls are found, raise a `ValueError` immediately. Ensure `cve_count` defaults to 0 if missing, not null.
- [X] T030 [P] Implement parallel processing in `code/data/extract_github.py` using `multiprocessing` with `max_workers=2` (to match CI CPU limit) and a memory limit check (abort if RAM > 6GB). Ensure pipeline processes ≥500 repos within 6 hours.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Construction and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest a defined set of public GitHub repositories, extract commit metadata to calculate unique contributors, compute lines of code (KLOC), and retrieve associated vulnerability records from the NVD/CVE database to form the primary analysis dataset.

**Independent Test**: Execute the data pipeline script on a small, fixed seed of repositories (first alphabetically) and verify the output CSV contains non-null values for `unique_authors`, `kloc`, `cve_count`, and `primary_language` for all entries.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py`. Validate columns and types.
- [X] T012 [US1] Integration test for full pipeline on 5-repo seed in `tests/integration/test_data_pipeline.py`. Run T006->T007->T008->T009 and assert output file exists with correct data.

### Implementation for User Story 1

- [X] T015 [Removed: Placeholder not needed]

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Inference (Priority: P2)

**Goal**: Fit a multivariate Poisson or Negative-Binomial GLM predicting vulnerability counts from author counts and control variables, using `log(kloc)` as an **offset** to normalize for project size, and output coefficient estimates, p-values, and confidence intervals.

**Independent Test**: Run the analysis script on a static, pre-generated CSV of a representative sample size. and verify the output JSON includes an `author_count_coefficient` with a non-null standard error and a A confidence interval will be used to estimate the range of plausible values for the parameter..

### Tests for User Story 2

- [X] T016 [P] [US2] Contract test for model results schema in `tests/contract/test_model_results.py`.
- [ ] T017 [US2] Implement `code/analysis/fit_models.py` to fit a Negative-Binomial GLM with `cve_count` as response, `author_count` + controls as predictors, and `log(kloc)` as **offset** (per FR-004). **Spec vs Plan Resolution**: The Plan suggests using `log(kloc)` as a free predictor, but the Spec (FR-004) mandates it as an offset. Since no Spec Amendment is approved, this task MUST follow the Spec. **Implementation**: Strictly ignore Plan.md's suggestion to use free predictor. Exclude rows where `kloc` is zero (log(0) undefined) with a warning log. Calculate VIF for all predictors. Apply Benjamini-Hochberg correction to the main model p-values. Generate `data/processed/model_results.json` containing coefficients, standard errors, p-values, confidence intervals, adjusted p-values, VIF metrics, and a `convergence_status` boolean (true if converged, false if failed). **Parameters**: Use `family=sm.families.NegativeBinomial()` and `link=sm.families.links.log()` explicitly. <!-- FIXED: Added Spec vs Plan note and explicit offset enforcement -->
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

- [ ] T021 [US3] Implement `code/analysis/robustness.py` (Part 1: Subsampling) to perform subsampling by language (Python, JavaScript) and re-fit GLMs using the same offset and controls. **Output**: Save raw p-values for each subsample model to `data/processed/robustness_raw_pvalues.csv`. Do NOT apply BH correction here. <!-- FIXED: Output raw p-values -->
- [ ] T022 [US3] Implement `code/analysis/robustness.py` (Part 2: Shannon Entropy) to calculate Shannon entropy for author contributions: `H = -sum(p_i * log(p_i))` where `p_i` is the proportion of **unique commits** by author `i`. **Re-fit GLM** using entropy as the primary predictor. **Report the difference** in the main coefficient compared to the primary model. **Output**: Save raw p-values for the entropy model to `data/processed/robustness_raw_pvalues.csv`. Do NOT apply BH correction here. <!-- FIXED: Added explicit re-fit and report steps -->
- [ ] T023 [US3] Implement `code/analysis/robustness.py` (Part 3: Global BH Correction) to aggregate all p-values (from main model T017, subsamples T021, and entropy T022) from `data/processed/robustness_raw_pvalues.csv` and apply a single Benjamini-Hochberg correction. Update `data/processed/robustness_results.json` with adjusted p-values. **Note**: This task is NOT parallel-safe; it depends on T021 and T022. <!-- FIXED: Restored T023, removed [P], full implementation logic -->
- [X] T024 [US3] Generate `data/processed/robustness_results.json` containing subsample coefficients, entropy model results, and adjusted p-values.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T025 [P] Documentation updates in `README.md`: Add a CLI usage section with example commands, a "Methods" section explaining the GLM offset approach, and a "Data" section describing the pipeline.
- [X] T026 Code cleanup and refactoring: Extract `parse_git_log` and `run_cloc` into separate modules in `code/data/utils.py` to ensure modularity.
- [X] T027 [P] Create benchmark script `tests/unit/test_performance.py` to measure time to process a representative set of repositories. Output format: JSON with `total_time_seconds`. Pass/fail threshold: < 12 minutes (to allow 500 in < 6h).
- [ ] T028 [P] Additional unit tests for edge cases in `tests/unit/analysis/`:
 - `test_zero_kloc_exclusion`: Verify rows with kloc=0 are excluded.
 - `test_empty_nvd_match`: Verify cve_count=0 when no match found.
- [X] T029 [P] Update `code/config.py` to use `os.getenv` for API keys.
- [X] T030 [P] Add test `tests/unit/test_config_no_leak.py` to verify no API keys are logged.
- [X] T031 [P] Create CI script `scripts/validate_quickstart.sh` that executes the pipeline on the seed dataset and exits 0 on success.
- [ ] T032 [P] [US2] Implement lagged variable analysis in `code/analysis/fit_models.py` to mitigate reverse causality: Create a new column `author_count_lagged` (author count from 1 year prior, calculated via `git log --since=2yearsago --until=1yearago` logic) and re-fit the model to check stability of the coefficient. **Note**: This is an optional research extension included per Plan.md's "Critical Note" but not mandated by the Spec. <!-- FIXED: Corrected time window logic -->
- [ ] T033 [P] [US3] Implement interaction term analysis in `code/analysis/robustness.py` to test if the effect of diversity varies by project age (interaction: `author_count * project_age`).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on `repo_metrics.csv` from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on `model_results.json` from US2

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
- **Data Integrity**: All tasks must use real data sources (NVD, GitHub API). No synthetic data fabrication.
- **Causality Warning**: All tasks involving model interpretation must explicitly state that results are observational associations, not causal claims.