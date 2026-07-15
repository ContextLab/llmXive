# Tasks: Predict Plant Disease Resistance from Multi‑omics Data

**Input**: Design documents from `/specs/001-predict-plant-disease-resistance/`
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

**Purpose**: Project initialization and basic structure. Tasks are now atomic for parallel execution.

- [X] T001 Create project directory tree: `code/`, `data/`, `data/raw`, `data/processed`, `artifacts/`, `artifacts/models`, `artifacts/reports`, `artifacts/figures`, `tests/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing pinned versions: `pandas==2.0.3`, `numpy==1.24.3`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `pyyaml==6.0.1`, `requests==2.31.0`
- [X] T003 [P] Configure linting (`.flake8` or `pyproject.toml` for black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/exceptions.py` with `EX_DATA_INTEGRITY (02)` and `EX_POWER_INSUFFICIENT (03)` custom classes
- [X] T005 Create `code/config.py` for loading environment variables and default paths
- [X] T006 [P] Setup Dockerfile bundling Python 3.11, `fastp`, `bcftools`, and project dependencies
- [X] T006b [P] Add inline comments to `Dockerfile` explaining build steps and dependencies
- [X] T006c [P] Add Docker build/run commands and usage instructions to `README.md` to satisfy FR-006 documentation requirements
- [ ] T007 Implement `code/utils/logging.py` for structured logging of pipeline steps and sample exclusions
- [X] T008 Create `data/data_manifest.yaml` schema and loader in `code/data/manifest.py`
- [ ] T009 Implement `code/data/generate_synthetic.py` to create ~150 paired samples with injected signal structure: **[deferred] SNPs, metabolites**, **binary phenotype (balanced split)**, effect size=0.1, noise distribution=normal(0,1), SNP-metabolite correlation=0.5 [UNRESOLVED-CLAIM: c_c39f1b62 — status=not_enough_info], {{claim:c_13800645}} (2601.08725, https://arxiv.org/abs/2601.08725)
- [ ] T010 Implement `code/data/download.py` to attempt NCBI SRA/MetaboLights fetch using query "plant AND disease resistance AND (SNP OR metabolite)" with accession list from `data_manifest.yaml`; if **no results found OR HTTP 404/403 after 3 retries**, trigger immediate fallback to synthetic generation (**Simulation Mode ONLY**); bypass halt logic in T019 only if `source == SIMULATED`
- [~] T011 Implement `code/data/preprocess.py` wrappers for `fastp` (variant calling via `bcftools`) and MetaboAnalyst-compatible normalization; explicitly generate aligned feature tables by matching sample IDs across modalities using **exact string match**; if IDs do not match, **drop both samples** and log to `data/processed/exclusion_log.csv` with columns: `sample_id`, `missing_modality`, `timestamp` as mandated by FR-001
- [X] T012 Implement `code/utils/stats.py` with Benjamini-Hochberg correction and Variance Inflation Factor (VIF) calculation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑End Resistance Prediction (Priority: P1) 🎯 MVP

**Goal**: Deliver a reproducible pipeline that downloads/generates data, preprocesses, trains a model, and reports metrics.

**Independent Test**: Execute the pipeline on the synthetic dataset and verify it completes, produces a trained model, and outputs `artifacts/reports/metrics.json` without manual intervention.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. [P] indicates parallel execution of test suites, NOT parallel implementation with code.**

- [X] T013 [P] [US1] Contract test for data alignment in `tests/test_data.py` (verify matching sample IDs across modalities)
- [X] T014 [P] [US1] Integration test for full pipeline run in `tests/test_pipeline.py` (verify runtime < 6h, RAM < 7GB)

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/data/split.py` for stratified sampling based on resistance phenotype (FR-009); **split proportions: [deferred] training, [deferred] hold-out** (resolving spec "[deferred]" via plan.md authority); strictly reserve hold-out set from all training/selection steps
- [X] T016 [US1] Implement `code/analysis/feature_selection.py` with LASSO/RF and sensitivity sweep over thresholds {0.01, 0.05, 0.1}; **run 3 independent iterations per threshold ** to calculate selection frequency; output `selection_frequency.csv` with columns: `feature_id`, `threshold`, `frequency` (aggregated across 3 runs per threshold) (FR-003)
- [X] T017 [US1] Implement `code/analysis/modeling.py` for Elastic-Net (continuous) or Gradient-Boosting (categorical) with 5-fold CV (FR-004)
- [X] T017b [US1] Implement logic in `code/analysis/modeling.py` to generate and train a null model baseline (**random labels**) and compare performance against the primary model; **ensure results are included in `metrics.json`** (FR-004) <!-- FAILED: unspecified -->
- [X] T018 [US1] Implement `code/analysis/validation.py` for **null model baseline comparison on training/CV folds ONLY**; **DO NOT run permutation testing on hold-out set here** (defer to T033) (FR-005)
- [~] T019 [US1] Implement `code/main.py` CLI entry point orchestrating: Fetch -> Preprocess -> Split -> Select -> Train -> Validate; **include logic to check data integrity**: read `source_type` from `data_manifest.yaml`; if `source_type != SIMULATED` and (aligned samples < 100 OR missing modalities), halt with `EX_DATA_INTEGRITY (02)`; if `source_type != SIMULATED` and (samples < 100), halt with `EX_POWER_INSUFFICIENT (03)`; **bypass halt ONLY if `source_type == SIMULATED`** (Simulation Mode exception per plan.md); handle contradictory FR-007/FR-008 by prioritizing FR-008 (Power) then FR-007 (Integrity) with unified error message <!-- FAILED: unspecified -->
- [ ] T022 [US1] Generate `artifacts/reports/metrics.json` containing CV accuracy, AUC/R², null model comparison, and **permutation p-value (from hold-out set, see T033)** <!-- FAILED: unspecified -->
- [ ] T023 [US1] Generate `artifacts/reports/selection_frequency.csv` listing feature IDs, thresholds, and selection frequency (FR-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Biomarker Exploration (Priority: P2)

**Goal**: Examine which SNPs and metabolites drive predictions and assess statistical significance.

**Independent Test**: After a successful run of Story 1, query the output for the ranked list of selected features and verify p-values and effect sizes are provided.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US2] Unit test for BH-adjusted p-value calculation in `tests/test_stats.py`
- [X] T025 [P] [US2] Contract test for `top_features.csv` schema in `tests/test_reports.py`

### Implementation for User Story 2

- [X] T026 [P] [US2] Extend `code/analysis/feature_selection.py` to calculate effect-size coefficients for selected features
- [~] T027 [US2] Implement `code/analysis/biomarker_report.py` to generate `artifacts/reports/top_features.csv` with p-values and effect sizes
- [ ] T028 [US2] Implement logic to filter and rank features based on selection frequency and BH-adjusted p < 0.05
- [ ] T028b [US2] Implement logic to count and verify that **at least 10 SNPs and 10 metabolites** remain significant **across the entire sensitivity sweep (defined as intersection of significant features across all three thresholds)**; **if count < 10, write `success_status: FAILED` to `artifacts/reports/success_criteria.json` and log a warning** (SC-002)
- [ ] T029 [US2] Add VIF flagging logic in `code/analysis/validation.py` to {{claim:c_d690e157}} (Wikidata Q113106917, https://www.wikidata.org/wiki/Q113106917) (FR-005)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Independent Validation (Priority: P3)

**Goal**: Evaluate the trained model on a separate dataset (or the hold-out set) to test generalizability.

**Independent Test**: Provide a hold-out dataset to the pipeline's validation mode and verify that performance metrics are computed and reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Integration test for hold-out evaluation in `tests/test_validation.py`

### Implementation for User Story 3

- [X] T031 [P] [US3] Extend `code/data/split.py` to strictly reserve the hold-out set from training/selection (FR-009) <!-- FAILED: unspecified -->
- [X] T031b [US3] Implement a validation check in `code/data/split.py` to assert that the hold-out set is never used in feature selection or training steps (strict reservation)
- [X] T032 [US3] Implement `code/analysis/validation.py` logic to evaluate the trained model on the independent hold-out set
- [ ] T033 [US3] Implement permutation testing (**n=1000**, **shuffling phenotype labels**, metric: **accuracy/AUC**) specifically on the **independent hold-out test set** to generate **model-level p-value**; output to `artifacts/reports/holdout_metrics.json` (FR-005, SC-003)
- [ ] T034 [US3] Generate `artifacts/reports/holdout_metrics.json` with final accuracy/AUC/R² and permutation p-value
- [ ] T035 [US3] Implement logic to compare hold-out performance against the ≥ 75% target and log a warning to `artifacts/reports/validation.log` if target is not met (as a hypothesis, not a hard halt)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` and `README.md` including Docker usage
- [ ] T037 Code cleanup and refactoring of `code/analysis/` modules
- [ ] T038 Performance optimization to {{claim:c_d2371661}}
- [ ] T038b [P] Implement runtime/memory measurement script in `code/utils/measure_resources.py` to log peak usage
- [ ] T038c [P] Update CI workflow to execute measurement script and log results against FR-006 constraints
- [ ] T039 [P] Additional unit tests for `code/data/preprocess.py` (mocking fastp/bcftools)
- [ ] T040 Run `quickstart.md` validation to ensure pipeline runs end-to-end on GitHub Actions free-tier
- [ ] T041 Verify `artifacts/reports/metrics.json` meets SC-001 (CV ≥ 75% in **Simulation Mode** for injected signal validation) and SC-003 (p ≤ 0.05); explicitly scope this to "Simulation Mode" context

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
- All tests for a user story marked [P] can run in parallel **once code is implemented**
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

**⚠️ CRITICAL SEQUENTIAL NOTE**: Within User Story 1, tasks **T015, T016, T017, T018, and T019 are STRICTLY SEQUENTIAL**. T015 (split) produces the training set consumed by T016 (feature_selection), which produces features consumed by T017 (modeling), which produces a model consumed by T018 (validation). T019 orchestrates all. **DO NOT attempt to run T015-T018 in parallel.**

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data alignment in tests/test_data.py"
Task: "Integration test for full pipeline run in tests/test_pipeline.py"

# IMPORTANT: Implementation tasks for US1 are SEQUENTIAL, NOT PARALLEL.
# T015 (split) must complete BEFORE T016 (feature_selection) can start.
# T015 produces the training set that T016 consumes.
# DO NOT run T015 and T016 in parallel.

# Correct sequential order for implementation:
Task: "Implement code/data/split.py" (T015)
Task: "Implement code/analysis/feature_selection.py" (T016)
Task: "Implement code/analysis/modeling.py" (T017)
Task: "Implement code/analysis/validation.py" (T018)
Task: "Implement code/main.py" (T019)
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

- [P] tasks = different files, no dependencies (for execution)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Simulation Mode**: Synthetic data generation and associated bypasses are strictly for pipeline validation in the absence of real matched data. Real data runs MUST enforce all FR-007/FR-008 halts.