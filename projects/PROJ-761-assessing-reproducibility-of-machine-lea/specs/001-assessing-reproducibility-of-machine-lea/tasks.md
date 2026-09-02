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

- [ ] T001 Create project structure per implementation plan by executing: `mkdir -p data/raw data/processed code tests artifacts/logs artifacts/plots artifacts/reports contracts`
- [X] T001b [P] Initialize Python 3.11 project with `requirements.txt` containing exact pinned versions: `torch==2.2.0+cpu`, `scikit-learn==1.5.0`, `rdkit==2024.3.1`, `statsmodels==0.14.1`, `pandas==2.2.0`, `numpy==1.26.0`, `matplotlib==3.8.0`, `pyyaml==6.0.1`, `requests==2.31.0`. **Note**: Installation requires `pip install -r requirements.txt --extra-index-url=https://download.pytorch.org/whl/cpu`.
- [X] T003a [P] Create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections configuring line length 88, target-version py311, and specific linting rules (E, F, W, I).
- [ ] T003b [P] Configure linting (ruff) and formatting (black) tools by running initial checks on the empty project structure to verify configuration validity. **Verification**: Task succeeds only if `ruff check .` and `black --check .` return exit code 0.
- [ ] T002 [P] **ReferenceValidator**: Execute the Reference-Validator agent to verify all citations and dataset URLs in `research.md` against the "Verified Datasets" block. **Blocking**: If any citation fails validation, the task fails and execution halts. (Constitution Check II)
- [ ] T003 [P] **Manifest Validator**: Validate `data/manifest.csv` against `contracts/PaperManifest.schema.yaml` using `code/ingest.py`. **Blocking**: Execution halts if validation fails. (Plan Phase 0)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, schemas, and data extraction logic that MUST be complete before ANY user story implementation.

**⚠️ CRITICAL**: No user story work (Phase 3+) can begin until this phase is complete. This phase includes data extraction logic (T020-T022) to ensure schemas are ready before model running.

- [X] T004 Create `Dockerfile` with Python 3.11, CPU-only PyTorch 2.2, scikit-learn 1.5, RDKit; enforce no GPU flags
- [X] T005 [P] Implement `code/ingest.py` for manifest validation and data fetching (including supplementary material extraction) referencing `contracts/PaperManifest.json` for schema validation. Extraction logic must rely on defined patterns in the manifest or standard supplementary file naming conventions (e.g., `*_supp.csv`, `*_data.parquet`).
- [ ] T006 [P] Setup `contracts/` directory and generate JSON Schemas for `PaperManifest`, `ReproResult`, `StatSummary`
- [X] T007 Create `code/metrics.py` with functions for MAE, R², Spearman ρ, and the Deviation Index (S) calculation (FR-009) using the exact formula: `S = 1 – (|ΔMAE|/(|MAE_ref|+ε) + |ΔR2|/(|R2_ref|+ε) + |Δρ|/(|ρ_ref|+ε))/3` where ε = 1e-6. (See spec.md Requirements FR-009)
- [X] T008 Configure environment logging in `code/main.py` to capture Python version, library versions, OS, and Docker hash (FR-012)
- [X] T009 Implement `data/manifest.yaml` loader and validator to ensure DOI, repo URL, dataset name, and reported metrics are present (FR-001)

### Data Extraction & Schema Updates (Prerequisites for Model Runner)
*These tasks are moved here to ensure schema and extraction logic are ready before T013 (Model Runner) begins.*

- [ ] T020 [P] [US1] Update `contracts/ReproResult.json` schema to include new fields: `experimental_replicates` (integer, nullable), `reaction_conditions` (object with optional keys: temperature, solvent, catalyst_loading), and `yield_std_dev` (float, nullable). **Definition**: `experimental_replicates` is integer or null; `reaction_conditions` is object with optional number fields; `yield_std_dev` is float or null. This addresses reviewer concerns regarding experimental rigor.
- [ ] T021 [P] [US1] Extend `code/ingest.py` to parse supplementary materials and raw data files specifically for `experimental_replicates` count and `reaction_conditions` metadata (temperature, solvent, catalyst loading). **Logic**: Read required covariates from the `PaperManifest` for each paper. **Execution**: For PDFs, extract text using PyPDF2/pdfplumber first, then apply regex patterns `r'Temperature:\\s*([\\d.]+)\\s*°C'`, `r'Solvent:\\s*(\\w+)'`, `r'Yield.*?([\\d.]+)%'` to the extracted text stream. If missing, log "Missing Replicate Data" and set fields to null.
- [ ] T022 [P] [US1] Modify `code/model_runner.py` to compute and record the standard deviation of yields (`yield_std_dev`) across experimental replicates found in the dataset. **Logic**: If covariates are missing, **exclude the paper from deviation calculation** (set reproduced metrics to null) but **include the paper in the results log** with a specific failure flag "covariate_missing" and null deviations. **Verification**: Verify `yield_std_dev` is present in `ReproResult` for paper X (or null if missing). If replicates are not present, explicitly log `yield_std_dev` as `null` and flag the "Missing Replicate Data" failure mode. **CRITICAL**: Do NOT exclude the paper from the results log; record the missing data and flag as unreproducible to satisfy FR-003.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproduce Reported Metrics (Priority: P1) 🎯 MVP

**Goal**: For each paper, retrieve data, re-implement the model on CPU, and compute reproduced metrics with deviations.

**Independent Test**: Run the pipeline on a single target paper with known results; verify `artifacts/reports/repro_results.json` contains MAE, R², ρ, deviations, and the calculated reproducibility score S.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/model_runner.py` to load data from `data/processed/`, apply preprocessing, train model (CPU, seed 42 or reported), and evaluate. Output JSON to `artifacts/reports/repro_results.json`. Include logic to substitute models exceeding a moderate parameter scale with a Random Forest baseline (n_estimators=100, max_depth=5) and log "Model Substitution/Unavailable" (FR-004, FR-005). **Verification**: Verify log contains "Model Substitution" for any paper with >1M parameters. **Dependency**: Requires T006 (Schema), T020 (Updated Schema), T021, T022 to be complete. **Note**: Explicitly log and record the deviation in the per-paper record when a model is substituted.
- [ ] T014 [US1] Implement logic in `code/model_runner.py` to handle missing seeds (default 42) and flag in results (US-1 Scenario 2)
- [ ] T015 [US1] Implement logic in `code/ingest.py` to verify dataset variables (SMILES, yield, covariates) against the manifest schema. If missing, generate a detailed flag in the results log for the specific missing variables and record in `ReproResult` as "Data Unavailable" (FR-003, Plan Phase 0).
- [ ] T016 [US1] Implement `code/model_runner.py` to enforce the ≤1M parameter limit; log "Model Substitution/Unavailable" if exceeded (Plan Phase 2)
- [ ] T017 [US1] Implement sensitivity analysis in `code/model_runner.py` to sweep seeds `{42, 123, 999}`, compute `metric_std` for each metric, and report the **maximum metric standard deviation** observed (sqrt of variance). Add `max_metric_std_dev` field to the `ReproResult` JSON object. **Clarification**: `max_metric_std_dev` is the specific field required by FR-010 and SC-003. **Dependency**: Requires T006 (Schema) and T007 (Metrics).
- [ ] T018 [US1] Implement `code/main.py` to aggregate individual `ReproResult` objects into `artifacts/reports/repro_results.json` containing deviations and score S (FR-005, FR-009). **Logic**: Merge per-paper JSONs into a list; if a paper is missing, log a warning and skip; output as a JSON array. **Output Structure**: List of objects with keys: `doi`, `mae`, `r2`, `rho`, `deviation_mae`, `deviation_r2`, `deviation_rho`, `score_s`, `max_metric_std_dev`, `flags`, `experimental_replicates`, `reaction_conditions`, `yield_std_dev`. **Verification**: Verify file exists and contains these keys for each entry. **Dependency**: Requires T013, T014, T015, T016, T017 to be complete.
- [ ] T019 [US1] Add logging in `code/main.py` to record environment details (Python, libs, OS, Docker hash) to `artifacts/logs/env.log` (FR-012)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Agreement Across Studies (Priority: P2)

**Goal**: Perform statistical meta-analysis (paired t-test, mixed-effects model, Bland-Altman) on the aggregated results.

**Independent Test**: Run the analysis module on a mock dataset of multiple papers; verify `artifacts/reports/stat_summary.json` contains t-test p-values, mixed-effects model variance components, and that Bland-Altman PNGs are saved.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T052 [P] [US2] Unit test for paired t-test implementation in `tests/unit/test_stats.py` (Renamed from duplicate T022)
- [X] T023 [P] [US2] Unit test for mixed-effects model implementation in `tests/unit/test_stats.py`
- [X] T024 [P] [US2] Integration test for Bland-Altman plot generation in `tests/integration/test_stats.py`
- [X] T050 [P] [US2] Unit test for mixed-effects model fixed effects implementation in `tests/unit/test_stats.py` (Renamed from duplicate T045)
- [X] T051 [P] [US2] Unit test for mixed-effects model random intercepts implementation in `tests/unit/test_stats.py` (Renamed from duplicate T047)

### Implementation for User Story 2

- [X] T025 [P] [US2] Implement `code/stats.py` to run paired t-tests for each metric (MAE, R², ρ) unconditionally, applying Bonferroni correction for family-wise error control. **Primary Test**: This task satisfies Spec SC-002 (paired t-test). (FR-006)
- [X] T026 [US2] Implement `code/stats.py` with TOST (Two One-Sided Tests) for MAE, R², ρ against tolerance delta (use delta=0.1 as defined in plan.md) for supplementary equivalence analysis, including Bonferroni correction. **Supplementary**: This task satisfies Plan Phase 3 but is secondary to T025 for Spec SC-002. (FR-006, Plan Phase 3)
- [X] T027 [US2] Implement `code/stats.py` with a Linear Mixed-Effects Model (LME). **Fixed Effects**: `ModelSubstitution` and `CovariateMissing` (as these are the actual varying factors per Plan Complexity Tracking; note: Spec FR-008 factors are constant in this single-environment run, so we model the available variance to satisfy SC-004). **Random Effects**: `Paper`. **Fallback**: If fixed effects are singular, fall back to random-intercept-only and log the fallback. **Critical Output**: Must compute and report 'variance_explained_fixed_effects' (R² of fixed effects) in `stat_summary.json` to satisfy SC-004. (Overrides Plan Phase 3 "random intercepts only" note to satisfy Spec SC-004).
- [X] T028 [US2] Implement `code/stats.py` to generate Bland-Altman plots for each metric and save as `{metric}_bland_altman.png` in `artifacts/plots/` (FR-007)
- [X] T029 [US2] Implement `code/stats.py` to compute heterogeneity (I²) and pooled effect size. **Logic**: Calculate I² using the Q-statistic on the per-paper **MAE absolute deviations** (the primary effect size), using the between-study variance (tau-squared) derived from the LME results in T027. Output to `artifacts/reports/stat_summary.json` with keys: `I2`, `pooled_effect_size`, `confidence_interval`. (Plan Phase 3) **Verification**: Verify file exists and contains these keys.
- [ ] T030 [US2] Implement logic to compile a qualitative failure log of excluded papers (model substitution, data gaps) and ensure these are explicitly flagged in the results log as per FR-003. Output to `artifacts/logs/failure_log.json` as a list of objects with keys: `paper_doi`, `failure_mode`, `details`. (Plan Phase 3) **Verification**: Verify file exists and contains these keys.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Community Guidelines (Priority: P3)

**Goal**: Synthesize a Markdown checklist of best-practice recommendations based on failure modes and statistical findings.

**Independent Test**: Run the guideline generator; verify `artifacts/reports/reproducibility_checklist.md` contains ≥5 items, each citing a guideline and referencing a specific failure mode.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US3] Unit test for guideline template rendering in `tests/unit/test_guidelines.py`
- [X] T033 [P] [US3] Integration test for checklist generation with mock failure logs in `tests/integration/test_guidelines.py`

### Implementation for User Story 3

- [ ] T034 [US3] Implement `code/guidelines.py` to parse `artifacts/reports/stat_summary.json` and the qualitative failure log at `artifacts/logs/failure_log.json`. **Graceful Handling**: Check if `failure_log.json` exists and is non-empty; if not, generate a checklist based on default best-practice guidelines and log a warning.
- [X] T035 [US3] Implement logic in `code/guidelines.py` to map failure modes (missing seeds, covariate gaps, version mismatches) to specific best-practice recommendations
- [X] T036 [US3] Implement `code/guidelines.py` to generate `artifacts/reports/reproducibility_checklist.md` with ≥5 numbered items, each citing a published guideline and referencing a failure mode (FR-011). **Logic**: Use a template that maps each failure mode to a specific guideline item, citing the relevant guideline and the specific failure mode from the log.
- [X] T037 [US3] Add logic to ensure checklist items are actionable (e.g., "Report random seed", "Version-pin libraries", "Specify reaction conditions") (US-3 Scenario 1)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T039 [P] Documentation updates in `docs/` (README, quickstart): Update README.md with installation instructions and quickstart.md with example usage
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
- **Restored Tasks**: T020, T021, T022, T038 (Experimental metadata extraction) are now fully implemented and marked [ ] to satisfy Spec FR-003 and reviewer feedback. Moved to Phase 2 to resolve dependency ordering.
- **Spec/Plan Conflict**: Task T027 implements fixed effects for `ModelSubstitution` and `CovariateMissing` per Plan Complexity Tracking (since Spec FR-008 factors are constant), overriding Plan Phase 3's "random intercepts only" note to satisfy Spec SC-004. Task T025 is primary (t-test) per Spec SC-002, while T026 (TOST) is supplementary per Plan Phase 3.
- **Ordering**: T020, T021, T022 moved to Phase 2 to precede T013. T017 precedes T018 to ensure variance is computed before aggregation. T013 and T017 are NOT parallel-safe ([P] removed) due to dependencies.
- **Renamed**: Duplicate T022 in Phase 4 Tests renamed to T052. Phase 0 setup task renamed to T001b to avoid collision with T002 (ReferenceValidator).
- **Task Dependencies**: T013 depends on T020, T021, T022 (now in Phase 2). T017 depends on T006 and T007. T018 depends on T013-T017. T029 depends on T027. T030 is independent but required for T034. T034 depends on T030 but handles missing logs gracefully.
- **Output Formats**: T018, T029, T030 now have explicit output format definitions. T017 now outputs `max_metric_std_dev` (standard deviation) to match SC-003.
- **Reviewer Addressed (Linus Pauling & Marie Curie)**: Tasks T020, T021, T022, and T035 specifically address the requirement to extract and report `experimental_replicates`, `reaction_conditions` (temperature, solvent, catalyst loading), and `yield_std_dev` to ensure reproducibility claims are substantiated with quantitative descriptors of experimental rigor.
- **Constraint Preservation**: T022 now correctly excludes papers with missing covariates from *deviation calculation* but includes them in the *results log* with a flag. T027 strictly follows Plan's correction for fixed effects. T017 clarifies variance output. T038 removed; logic integrated into T034/T035 for dynamic derivation.
- **Constitution Check**: T002 and T003 restored to Phase 0 to ensure Verified Accuracy and Manifest Validation are executed. T001b handles setup.