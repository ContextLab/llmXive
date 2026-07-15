# Tasks: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

**Input**: Design documents from `/specs/001-assessing-uncertainty-quantification-tec/`
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

- [ ] T001a [P] Create directory structure: `data/raw/`, `data/processed/`, `code/models/`, `code/metrics/`, `code/stats/`, `results/`, `tests/unit/`, `tests/integration/`, `code/utils/`
- [ ] T001b [P] Initialize Python 3.11 project with `requirements.txt` (pinned versions: `scikit-learn`, `xgboost`, `torch`, `numpy`, `pandas`, `scipy`)
- [ ] T001c [P] Create `code/__init__.py`, `tests/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites & Spec Amendments)

**Purpose**: Core infrastructure, Spec amendments for alignment, and statistical contracts that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Configure linting (ruff) and formatting (black) tools
- [X] T002a [P] **Spec Amendment**: Update `spec.md` FR-004 to explicitly mandate **Paired Wilcoxon Signed-Rank tests** (replacing the independent-sample requirement) to align with the Constitution and Plan. Document the rationale (same test set, independent methods).
- [X] T002b [P] **Spec Amendment**: Update `spec.md` FR-001 to explicitly substitute **Formation Energy (OQMD)** for **Elastic Modulus (Materials Project)** due to data unavailability. Update Success Criteria SC-005 accordingly.
- [~] T002c [P] **Spec Amendment**: Update `spec.md` SC-005 to list the actual datasets: "Band Gap, Thermal Conductivity, Formation Energy".
- [X] T003 [P] Implement `code/download.py` to fetch real datasets: OQMD (Band Gap), OQMD (Formation Energy - substituted for Elastic Modulus), and AFLOW (Thermal Conductivity). **Endpoints**: OQMD via ` or fallback to pre-processed CSVs in `data/raw/` if API fails. AFLOW via `. **Constraint**: Must handle API rate limits, save to `data/raw/` with checksums, and fallback to local CSVs if API fails.
- [X] T004 [P] Implement `code/featurize.py` using `matminer` (or fallback to `pymatgen` if `matminer` fails) to convert raw compositions/structures to feature vectors. **Constraint**: Must enforce a hard cap of **[deferred] samples** per dataset. Implement a memory-check loop: if RAM usage > 1.8GB during loading, downsample further. Must implement stratified train/validation/test split by property range using quantile-based bins and A fixed random seed will be used..
- [X] T005 Create base data models in `code/__init__.py` (DataClasses for `MaterialsDataset`, `UQMethod`, `EvaluationMetric`)
- [X] T006 Configure error handling and logging infrastructure in `code/utils/logger.py` to capture convergence failures and memory overflows
- [X] T007 Setup environment configuration management (`.env` for API keys, `config.yaml` for hyperparameters)
- [ ] T024 [P] **Statistical Contract**: Implement `code/stats/significance.py` function `run_paired_wilcoxon(metrics_df)`. **Constraint**: Must perform paired test on per-sample errors (same test set) for method pairs within each dataset. **Constraint**: Do NOT use ANOVA or Independent t-test. This task defines the statistical logic required by the amended FR-004.
- [ ] T024a [P] **Schema Contract**: Define and save the `per_sample_errors.csv` schema (columns: `sample_id`, `method`, `prediction`, `lower_bound`, `upper_bound`, `ground_truth`, `dataset`) to `results/`. This contract must be established before T014 runs to ensure correct data generation.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible UQ Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Execute a single orchestrated script that downloads data, trains baseline models, applies 4 UQ methods, and outputs metrics.

**Independent Test**: The system can be tested by running `code/pipeline.py` on a subset of the data; if it completes without error and outputs `results/summary.csv`, the story is complete.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Contract test for `code/pipeline.py` output schema in `tests/unit/test_pipeline_schema.py`
- [ ] T009 [P] [US1] Integration test for full pipeline execution on a 100-sample subset in `tests/integration/test_pipeline_e2e.py`

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement `code/models/gpr.py` using `sklearn.gaussian_process.GaussianProcessRegressor`. **Constraint**: Use RBF kernel, no GPU, no 8-bit quantization. Handle `ConvergenceWarning` by logging and skipping.
- [ ] T011 [P] [US1] Implement `code/models/mc_dropout.py` using PyTorch. **Constraint**: Use a small MLP (≤2M params) or XGBoost wrapper. Enable dropout during inference. **Convergence**: Limit MC passes to a maximum of 200 or until variance of predictions < 1e-4 over 50 consecutive passes.
- [ ] T012 [P] [US1] Implement `code/models/deep_ensemble.py`. **Constraint**: Train 3 small models (XGBoost or small MLP) sequentially, discard weights after inference, and limit ensemble size to 3 to ensure total RAM usage ≤ 2GB.
- [ ] T013 [P] [US1] Implement `code/models/conformal.py` using `conformal` or `scikit-learn` split-conformal logic. **Constraint**: Must work with any baseline regressor.
- [ ] T014 [US1] Implement `code/pipeline.py` orchestration script. Logic: Download → Featurize → Loop (Method x Dataset) → Train → Predict → Generate `per_sample_errors.csv` (schema defined in T024a) → Save intermediate results. **Dependency**: Must depend on T024a (Schema Contract) to ensure correct output format for downstream statistical testing.
- [ ] T015 [US1] Add robust error handling in `pipeline.py`: If any method fails for a dataset, log error, skip, and continue to next method/dataset. Ensure partial results are saved.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Calibration and Sharpness Metric Calculation (Priority: P2)

**Goal**: Calculate Calibration Error and Prediction Interval Sharpness for all test predictions.

**Independent Test**: The system can be tested by feeding synthetic data with known intervals and verifying the calculated metrics match theoretical expectations.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for Calibration Error calculation in `tests/unit/test_metrics.py` (verify |Observed - Nominal|)
- [ ] T017 [P] [US2] Unit test for Sharpness calculation in `tests/unit/test_metrics.py` (verify mean interval width)

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `code/metrics/evaluation.py` function `calculate_calibration_error(predictions, intervals, ground_truth, nominal_level)`.
- [ ] T019 [US2] Implement `code/metrics/evaluation.py` function `calculate_sharpness(intervals)`.
- [ ] T020 [US2] Integrate metrics calculation into `code/pipeline.py` post-inference.
- [ ] T021 [US2] Generate `results/metrics_raw.csv` containing: `dataset`, `method`, `metric_type` (Calibration/Sharpness), `value`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical significance testing (Paired Wilcoxon) and sensitivity analysis on conformal thresholds.

**Independent Test**: The system can be tested by running the statistical module on generated metrics; it must output p-values and a sensitivity report.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US3] Unit test for Paired Wilcoxon implementation in `tests/unit/test_stats.py` (verify p-value calculation on known arrays)
- [ ] T023 [P] [US3] Unit test for sensitivity analysis logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T024 [P] [US3] **Statistical Execution**: Execute `run_paired_wilcoxon` on `per_sample_errors.csv` generated by T014. **Constraint**: Must perform paired test on per-sample errors (same test set) for method pairs within each dataset. **Constraint**: Do NOT use ANOVA or Independent t-test.
- [ ] T025 [US3] Implement `code/stats/significance.py` function `run_sensitivity_analysis(conformal_results, coverage_range)`. **Constraint**: Sweep coverage levels from **0.80 to 0.99** with **step size 0.01**. Report width/error trade-offs.
- [ ] T026 [US3] Update `code/pipeline.py` to call statistical modules after all metrics are generated.
- [ ] T027 [US3] Generate `results/statistical_report.csv` containing: `dataset`, `method_pair`, `test_type`, `p_value`, `significance_flag`.
- [ ] T028 [US3] Generate `results/sensitivity_report.csv` containing: `coverage_level`, `avg_width`, `observed_coverage_error`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] [US1] Documentation updates in `README.md`: Add usage instructions, update dependencies list.
- [ ] T030 [P] [US1] Documentation updates in `docs/`: Add API docs for `code/models/`, `code/metrics/`, `code/stats/`.
- [ ] T031 [P] [US1] Documentation updates: Add contributing guide and code of conduct.
- [ ] T032a [P] Code cleanup: Remove debug prints from `code/pipeline.py`.
- [ ] T032b [P] Code cleanup: Remove debug prints from `code/models/*.py`.
- [ ] T033 Performance optimization: Ensure total pipeline time < 1 hour on CPU-only runner
- [ ] T034 [P] Additional unit tests for edge cases (e.g., dataset < 100 samples) in `tests/unit/`
- [ ] T035 Run `quickstart.md` validation to ensure reproducible execution
- [ ] T036 [US3] Add logic to flag statistical tests as "inconclusive" if test set size < 100 samples (per Assumptions in spec.md)

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (except T024a schema)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for prediction data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for metrics data

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
# Launch all models for User Story 1 together:
Task: "Implement code/models/gpr.py"
Task: "Implement code/models/mc_dropout.py"
Task: "Implement code/models/deep_ensemble.py"
Task: "Implement code/models/conformal.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Spec Amendments)
3. Complete Phase 3: User Story 1 (Data download, featurization, 4 UQ models, pipeline orchestration)
4. **STOP and VALIDATE**: Test User Story 1 independently on a small sample
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
 - Developer A: User Story 1 (Pipeline & Models)
 - Developer B: User Story 2 (Metrics)
 - Developer C: User Story 3 (Stats)
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
- **Critical Constraint**: All models must run on CPU-only (minimal cores and RAM). No GPU, no 8-bit quantization, no large GNNs. Use XGBoost or small MLPs only.
- **Critical Constraint**: Use real datasets (OQMD, AFLOW) via verified URLs. No synthetic/fake data generation for input.
- **Critical Constraint**: Statistical tests must be Paired Wilcoxon (Spec FR-004 amended, Constitution VII), not Independent t-test.
- **Critical Constraint**: Elastic Modulus is substituted with Formation Energy (OQMD) due to data unavailability (Spec FR-001 amended).