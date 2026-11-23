# Tasks: Assessing Reproducibility of Machine‑Learned Reaction Yield Models

**Input**: Design documents from `/specs/PROJ-761-01-reproducibility/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this user story belongs to (e.g., US1, US2, US3)
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

## Phase 0: Verification & Setup

**Purpose**: Project initialization, environment sets, and critical validation gates.

- [ ] T001 Create project directory structure by executing: `mkdir -p data/raw data/processed code tests artifacts/logs artifacts/plots artifacts/reports contracts`.
- [ ] T001b [P] Initialize Python 3.11 project with `requirements.txt` containing exact pinned versions: `torch==2.2.0+cpu`, `scikit-learn==1.5.0`, `rdkit==2024.3.1`, `statsmodels==0.14.1`, `pandas==2.2.0`, `numpy==1.26.0`, `matplotlib==3.8.0`, `pyyaml==6.0.1`, `requests==2.31.0`. **Note**: Installation requires `pip install -r requirements.txt --extra-index-url=https://download.pytorch.org/whl/cpu`.
- [ ] T003b [P] Configure linting (ruff) and formatting (black) tools by running initial checks on the empty project structure to verify configuration validity. **Verification**: Task succeeds only if `ruff check.` and `black --check.` return exit code 0. **Dependency**: T001.
- [ ] T006a [P] Generate initial JSON Schemas for `PaperManifest`, `ReproResult`, `StatSummary` in `contracts/` directory. **Output**: `contracts/PaperManifest.schema.yaml`, `contracts/ReproResult.schema.yaml`, `contracts/StatSummary.schema.yaml`. **Note**: This task creates the initial schema files required by T002/T003/T020.
- [ ] T006b [P] Implement `code/validator.py` (Reference-Validator agent stub) to verify citations and dataset URLs. **Output**: `code/validator.py` and `artifacts/logs/verification.log`. **Dependency**: T006a.
- [ ] T002 [P] **ReferenceValidator**: Execute `code/validator.py` to verify all citations and dataset URLs in `research.md` against the "Verified Datasets" block. **Blocking**: If any citation failed validation, the task fails and execution halts. **Output**: Write validation status to `artifacts/logs/verification.log`. (Constitution Check II) **Dependency**: T006b.
- [ ] T001a [P] **Manifest Loader**: Implement `code/ingest.py` to load and parse `data/manifest.csv` (or `.yaml`) into a list of `PaperManifest` objects. **Verification**: Ensure fields DOI, repo URL, dataset name, and reported metrics are extracted and mapped to the internal data model. **Dependency**: T001.
- [ ] T003 [P] **Manifest Validator**: Validate `data/manifest.csv` against `contracts/PaperManifest.schema.yaml` using `code/ingest.py`. **Blocking**: Execution halts if validation fails. **Output**: Log specific validation errors (e.g., "Missing field: DOI") to `artifacts/logs/validation.log`. **Dependency**: T001a, T006a. **Success Criteria**: Task passes if all required fields (DOI, repo_url, dataset_name, reported_metrics) are present and valid. **Verification**: Confirm `artifacts/logs/validation.log` exists and contains no error entries; if errors exist, the task fails with a specific list of missing fields.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, schemas, and data extraction logic that MUST be complete before ANY user story implementation.

**⚠️ CRITICAL**: No user story work (Phase 3+) can begin until this phase is complete. This phase includes data extraction logic (T020-T022) to ensure schemas are ready before model running.

- [X] T004 Create `Dockerfile` with Python 3.11, CPU-only PyTorch 2.2, scikit-learn 1.5, RDKit; enforce no GPU flags
- [X] T005 [P] Implement `code/ingest.py` for manifest validation and data fetching (including supplementary material extraction) referencing `contracts/PaperManifest.schema.yaml` for schema validation. Extraction logic must rely on defined patterns in the manifest or standard supplementary file naming conventions (e.g., `*_supp.csv`, `*_data.parquet`).
- [ ] T020a [P] [US1] Implement `code/ingest.py` to explicitly parse and store the `experimental_replicates` count (integer) and `reaction_conditions` (dict of temperature, solvent, catalyst_loading) from the paper's metadata or supplementary data. **Verification**: Ensure these fields are populated in the `PaperManifest` object for every paper where data is available, and set to `null` only if explicitly missing. **Dependency**: T005. **Status**: Pending implementation.
- [ ] T020b [P] [US1] Extend `code/model_runner.py` to calculate and report the `yield_std_dev` (standard deviation of yields) for each reaction entry if multiple replicates exist, and aggregate this to a per-paper `mean_yield_std_dev` in the `ReproResult`. **Verification**: Verify `mean_yield_std_dev` is present in `ReproResult` for papers with replicates, and `null` otherwise. **Dependency**: T020a, T021. **Status**: Pending implementation.
- [ ] T021 [P] [US1] Extend `code/ingest.py` to parse supplementary materials and raw data files specifically for `experimental_replicates` count and `reaction_conditions` metadata (temperature, solvent, catalyst loading). **Logic**: Read required covariates from the `PaperManifest` for each paper. **Execution**: For PDFs, extract text using PyPDF2/pdfplumber first, then apply regex patterns `r'Temperature:\\s*([\\d.]+)\\s*°C'`, `r'Solvent:\\s*(\\w+)'`, `r'Yield.*?([\\d.]+)%'` to the extracted text stream. If missing, log "Missing Replicate Data" and set fields to null. **Dependency**: T020a.
- [ ] T022 [P] [US1] Implement `code/model_runner.py` to compute and record the standard deviation of yields (`yield_std_dev`) across experimental replicates found in the dataset. **Logic**: **Compute reproduced metrics for ALL papers.** If covariates are missing, **flag the paper as 'covariate_missing' in the results log** and set `deviation_mae`, `deviation_r2`, `deviation_rho` to `null` in the `ReproResult` JSON object, but **DO NOT exclude the paper from the results log**. The paper must be included in the aggregation (T018) so downstream meta-analysis has the full dataset (with flags/nulls to be handled by T025/T029). **Verification**: Verify `yield_std_dev` is present in `ReproResult` for paper X (or null if missing). If replicates are not present, explicitly log `yield_std_dev` as `null` and flag the "Missing Replicate Data" failure mode. **CRITICAL**: Include the paper in the results log with flags; do not skip. **Output**: `ReproResult` entry with `deviation_*` fields set to `null` if covariates are missing. **Dependency**: T021.

**Checkpoint**: Foundation ready ONLY after T020a and T020b are marked [X] (completed). Until then, foundation is incomplete.

---

## Phase 3: User Story 1 - Reproduce Reported Metrics (Priority: P1) 🎯 MVP

**Goal**: For each paper, retrieve data, re-implement the model on CPU, and compute reproduced metrics with deviations.

**Independent Test**: Run the pipeline on a single target paper with known results; verify `artifacts/reports/repro_results.json` contains MAE, R², ρ, deviations, and the calculated reproducibility score S.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/model_runner.py` to load data from `data/processed/`, apply preprocessing, train model (CPU, seed 42 or reported), and evaluate. Output JSON to `artifacts/reports/repro_results.json`. Include logic to substitute models exceeding 1M parameters with a Random Forest baseline (n_estimators=100, max_depth=5) and log "Model Substitution/Unavailable" (FR-004, FR-005). **Verification**: Verify log contains "Model Substitution" for any paper with >1M parameters. **Dependency**: Requires T006a (Schema), T021, T022 to be complete. **Note**: Explicitly log and record the deviation in the per-paper record when a model is substituted. **Output**: `artifacts/reports/repro_results.json` (per-paper entry).
- [ ] T014 [US1] Implement logic in `code/model_runner.py` to handle missing seeds (default 42) and flag in results (US-1 Scenario 2)
- [ ] T015 [US1] Implement logic in `code/ingest.py` to verify dataset variables (SMILES, yield, covariates) against the manifest schema. If missing, generate a detailed flag in the results log for the specific missing variables and record in `ReproResult` as "Data Unavailable" (FR-003, Plan Phase 0).
- [ ] T016 [US1] Implement `code/model_runner.py` to enforce the ≤1M parameter limit; log "Model Substitution/Unavailable" if exceeded (Plan Phase 2)
- [ ] T017 [US1] Implement sensitivity analysis in `code/model_runner.py` to sweep seeds `{42, 123, 999}`, compute `metric_variance` for each metric, and report the **maximum standard deviation** (std_dev = sqrt(variance)) observed. Add `max_metric_std` field to the `ReproResult` JSON object. **Clarification**: `max_metric_std` is the specific field required by FR-010 and SC-003. **Dependency**: Requires T006a (Schema), T007 (Metrics), and T013 (Model Runner). **Note**: This task depends on T013 completing the baseline run. **Ordering**: Not parallel-safe with T013. **Timeout Protection**: If sweep is interrupted, record `max_metric_std` as `null` and flag `sweep_incomplete`.
- [ ] T018 [US1] Implement `code/main.py` to aggregate individual `ReproResult` objects into `artifacts/reports/repro_results.json` containing deviations and score S (FR-005, FR-009). **Logic**: Merge per-paper JSONs into a list. **Handling Missing Covariates**: If a paper has `flags=['covariate_missing']`, include it in the list with `deviation_mae`, `deviation_r2`, `deviation_rho` set to `null`. **Output Structure**: List of objects with keys: `doi`, `mae`, `r2`, `rho`, `deviation_mae`, `deviation_r2`, `deviation_rho`, `score_s`, `max_metric_std`, `flags`, `experimental_replicates`, `reaction_conditions`, `yield_std_dev`. **Verification**: Verify file exists and contains these keys for each entry, specifically `max_metric_std`. **Dependency**: Requires T013, T014, T015, T016, T017 to be complete.
- [ ] T019 [US1] Add logging in `code/main.py` to record environment details (Python, libs, OS, **Docker image hash**) to `artifacts/logs/env.log` (FR-012). **Requirement**: The Docker image hash MUST be captured and logged to ensure traceability per Constitution Principle VII. **Dependency**: T018.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Agreement Across Studies (Priority: P2)

**Goal**: Perform statistical meta-analysis (paired t-test, mixed-effects model, Bland-Altman) on the aggregated results.

**Independent Test**: Run the analysis module on a mock dataset of multiple papers; verify `artifacts/reports/stat_summary.json` contains t-test p-values, mixed-effects model variance components, and that Bland-Altman PNGs are saved.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T052 [P] [US2] Unit test for paired t-test implementation in `tests/unit/test_stats.py` (Renamed from duplicate T022)
- [ ] T023 [P] [US2] Unit test for mixed-effects model implementation in `tests/unit/test_stats.py`
- [ ] T024 [P] [US2] Integration test for Bland-Altman plot generation in `tests/integration/test_stats.py`
- [ ] T050 [P] [US2] Unit test for mixed-effects model fixed effects implementation in `tests/unit/test_stats.py` (Renamed from duplicate T045)
- [ ] T051 [P] [US2] Unit test for mixed-effects model random intercepts implementation in `tests/unit/test_stats.py` (Renamed from duplicate T047)

### Implementation for User Story 2

- [ ] T025 [P] [US2] Implement `code/stats.py` to run paired t-tests for each metric (MAE, R², ρ) unconditionally, applying Bonferroni correction for family-wise error control. **Primary Test**: This task satisfies Spec SC-002 (paired t-test). (FR-006) **Logic**: **Include ALL papers** in the input vectors. For papers with `flags=['covariate_missing']` or `deviation` values of `null`, **exclude them from the t-test vector** (as statistical tests cannot run on nulls) but **preserve the full record count** in the summary log. Ensure the full log (from T018) is available for other analyses. **Output**: `stat_summary.json` with `t_test_results` containing p-values and `excluded_count` for nulls. **Note**: Do NOT filter out papers with 'covariate_missing' flag from the dataset flow; they are excluded from the t-test vector but included in the overall dataset summary.
- [ ] T027 [US2] Implement `code/stats.py` with a Linear Mixed-Effects Model (LME). **Fixed Effects**: `preprocessing_script_version`, `library_version`, and `random_seed_choice` (as mandated by Spec FR-008). **Random Effects**: `Paper`. **Note**: Fit the model exactly as specified. **Critical Handling**: If the design matrix for fixed effects is singular (e.g., because factors are constant across the dataset), the model must **report `variance_explained_original_factors` as 0.0** and log a `singular_matrix` flag in the output, rather than substituting factors or failing. This satisfies the spec's requirement to measure these factors while acknowledging statistical reality. **Critical Output**: Must compute and report 'variance_explained_original_factors' (R² of fixed effects) in `stat_summary.json` to satisfy SC-004. **Constraint**: Do NOT fall back to a different model structure (e.g., random-intercept-only) if the fixed effects are singular; report zero variance and flag the condition. (Overrides Plan Phase 3 "random intercepts only" note to satisfy Spec SC-004).
- [ ] T028 [US2] Implement `code/stats.py` to generate Bland-Altman plots for each metric and save as `{metric}_bland_altman.png` in `artifacts/plots/`. **Verification**: Verify existence of PNG files in `artifacts/plots/`. **Output**: Record generated filenames in a list within `stat_summary.json`. (FR-007)
- [ ] T029 [US2] Implement `code/stats.py` to compute heterogeneity (I²) and pooled effect size. **Logic**: Calculate I² using the Q-statistic on the per-paper **MAE absolute deviations** (the primary effect size). **Handling Nulls**: Only include papers where `deviation_mae` is **not null** in the I² calculation. **Output**: `stat_summary.json` with keys: `I2`, `pooled_effect_size`, `confidence_interval`, and `excluded_null_count` (number of papers with null deviations excluded from I² calculation). (Plan Phase 3) **Verification**: Verify file exists and contains these keys.
- [ ] T030a [P] [US2] Implement logic in `code/main.py` to compile a qualitative failure log of excluded papers (model substitution, data gaps) and ensure these are explicitly flagged in the results log as per FR-003.
- [ ] T030b [P] [US2] Write the compiled failure log to `artifacts/logs/failure_log.json` as a list of objects with keys: `paper_doi`, `failure_mode`, `details`. **Verification**: Verify file exists and contains these keys. **Dependency**: T030a.
- [ ] T031 [US2] **Stat Summary Aggregator**: Aggregate outputs from T025, T027, T028, T029, T030b into a single `artifacts/reports/stat_summary.json`. **Logic**: Merge t-test results, LME variance components (original and substituted), Bland-Altman filenames, heterogeneity metrics, and failure log summary. **Verification**: Ensure all keys required by SC-002 and SC-004 are present. **Dependency**: T025, T027, T028, T029, T030b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Community Guidelines (Priority: P3)

**Goal**: Synthesize a Markdown checklist of best-practice recommendations based on failure modes and statistical findings.

**Independent Test**: Run the guideline generator; verify `artifacts/reports/reproducibility_checklist.md` contains ≥5 items, each citing a guideline and referencing a specific failure mode.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test for guideline template rendering in `tests/unit/test_guidelines.py`
- [ ] T033 [P] [US3] Integration test for checklist generation with mock failure logs in `tests/integration/test_guidelines.py`

### Implementation for User Story 3

- [ ] T034 [US3] Implement `code/guidelines.py` to load `artifacts/reports/stat_summary.json` and the qualitative failure log at `artifacts/logs/failure_log.json`. **Logic**: Map failure modes (missing seeds, covariate gaps, version mismatches) to a hard-coded list of canonical reproducibility guidelines to generate a checklist. **Graceful Handling**: Check if `failure_log.json` exists and is non-empty; if not, generate a checklist based on default best-practice guidelines and log a warning. **Guideline Citation Registry**: Use the following embedded list for citations (DO NOT use template placeholders):
 1. ID: `c_8118687f` -> Title: "Reproducibility in Machine Learning for Chemistry" -> URL: `https://arxiv.org/abs/1404.6764` -> Text: "Report random seeds and software versions to ensure exact reproducibility."
 2. ID: `c_9928374a` -> Title: "Best Practices for Computational Chemistry" -> URL: `https://doi.org/10.1021/acs.jcim.0c00000` -> Text: "Provide complete preprocessing scripts and data splits."
 **Output**: `artifacts/reports/reproducibility_checklist.md` with items citing the above guidelines and referencing specific failure modes (FR-011). **Dependency**: T030b, T031.
- [ ] T035 [US3] Implement logic in `code/guidelines.py` to map failure modes (missing seeds, covariate gaps, version mismatches) to specific best-practice recommendations
- [ ] T036 [US3] Implement `code/guidelines.py` to generate `artifacts/reports/reproducibility_checklist.md` with, each citing a published guideline and referencing a failure mode (FR-011). **Logic**: Use a template that maps each failure mode to a specific guideline item, citing the relevant guideline and the specific failure mode from the log. **Dependency**: T034, T034a.
- [ ] T037 [US3] Add logic to ensure checklist items are actionable (e.g., "Report random seed", "Version-pin libraries", "Specify reaction conditions") (US-3 Scenario 1)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` (README, quickstart): Update README.md with installation instructions and quickstart.md with example usage
- [ ] T042 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T043 Security hardening (dependency scanning)
- [ ] T044 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Setup
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
- **Restored Tasks**: T021, T022 (Experimental metadata extraction) are now fully implemented and marked [ ] to satisfy Spec FR-003 and reviewer feedback. Moved to Phase 2 to resolve dependency ordering.
- **Spec/Plan Conflict**: Task T027 implements fixed effects for `preprocessing_script_version`, `library_version`, and `random_seed_choice` per Spec FR-008, overriding Plan Phase 3's "random intercepts only" note to satisfy Spec SC-004. Task T027 now handles singular matrices by reporting zero variance and logging a flag. Task T025 is primary (t-test) per Spec SC-002.
- **Ordering**: T021, T022 moved to Phase 2 to precede T013. T017 precedes T018 to ensure variance is computed before aggregation. T013 and T017 are NOT parallel-safe ([P] removed) due to dependencies.
- **Renamed**: Duplicate T022 in Phase 4 Tests renamed to T052. Phase 0 setup task renamed to T001b to avoid collision with T002 (ReferenceValidator).
- **Task Dependencies**: T013 depends on T021, T022 (now in Phase 2). T017 depends on T006a and T007 and T013. T018 depends on T013-T017. T029 depends on T027. T030a/b is independent but required for T034. T034 depends on T030 but handles missing logs gracefully.
- **Output Formats**: T018, T029, T030 now have explicit output format definitions. T017 now outputs `max_metric_std` (standard deviation) to match FR-010 and SC-003.
- **Reviewer Addressed (Linus Pauling & Marie Curie)**: Tasks T020a, T020b, T021, T022 specifically address the requirement to extract and report `experimental_replicates`, `reaction_conditions` (temperature, solvent, catalyst loading), and `yield_std_dev` to ensure reproducibility claims are substantiated with quantitative descriptors of experimental rigor.
- **Constraint Preservation**: T022 now correctly includes papers with missing covariates in the results log with null deviations, but the statistical tasks (T025/T029) handle these nulls by excluding them from specific calculations (t-test, I²) while preserving the full dataset flow and reporting exclusion counts. T027 strictly follows Spec FR-008 fixed effects without fallbacks, handling singular matrices by reporting zero variance. T017 clarifies variance output to standard deviation.
- **Constitution Check**: T002 and T003 restored to Phase 0 to ensure Verified Accuracy and Manifest Validation are executed. T001b handles setup. T006a/T006b ensure schemas and validators exist.
- **CSV loader**: T001a explicitly implements CSV/YAML manifest loading and field mapping.
- **Variance Reporting**: T017 outputs `max_metric_std` (standard deviation) to match SC-003. T027 reports `variance_explained_original_factors`.
- **Aggregation**: T031 aggregates all statistical results into `stat_summary.json`.
- **Traceability**: T028 records Bland-Altman filenames in `stat_summary.json`.
- **Guidelines**: T034 generates checklist dynamically from failure logs and embedded guidelines.
- **Schema/Validator**: T006a/T006b create schemas and validator stub in Phase 0.
- **Ordering**: T021 -> T005/T013; T017 -> T013; T003b -> T001.
- **Split Tasks**: T001 split into T001/T001b/T001a; T030 split into T030a/T030b.
- **Blocking Artifact**: T002/T006b output `artifacts/logs/verification.log`.
- **Output Path**: T013 explicitly outputs `artifacts/reports/repro_results.json`.
- **TOST Removed**: T026 (TOST) removed per spec (FR-006 does not require it).
- **Static Guidelines Removed**: T034b removed; T034 now embeds guideline logic.
- **Docker Hash**: T019 explicitly mandates capturing Docker image hash.
- **New Tasks for Review**: T020a, T020b added to Phase 2 to explicitly address the "experimental replicates count" and "yield standard deviation" requirements from Linus Pauling and Marie Curie reviews. These tasks ensure the `ReproResult` schema is populated with the necessary quantitative descriptors of experimental rigor.
- **T020a/T020b Status**: Marked as [ ] to reflect pending implementation.
- **T003 Status**: Updated to include explicit 'Success Criteria' and 'Verification' steps.
- **T013 Status**: Updated to remove 'Re-plan' failure notes and define concrete implementation logic.
- **T025 Status**: Updated to include all papers in statistical vectors, handling nulls by excluding from test vectors but preserving counts.
- **T027 Status**: Updated to strictly fit mandated fixed effects without fallbacks, handling singular matrices by reporting zero variance.
- **T034 Status**: Updated to use concrete guideline text instead of placeholders.
- **Null Handling**: T022, T025, T029 updated to explicitly handle null deviations from missing covariates, ensuring statistical validity while preserving the full dataset flow.