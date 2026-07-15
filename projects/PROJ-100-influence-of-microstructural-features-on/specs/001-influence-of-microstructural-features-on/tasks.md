# Tasks: Influence of Microstructural Features on Fatigue Life in Aluminum Alloys

**Input**: Design documents from `/specs/001-fatigue-microstructure-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

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

 Tasks MUST be organized by user story so each story can:
 - Be implemented independently
 - Be tested independently
 - Be delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create `code/` directory for source code and scripts
- [ ] T001b Create `data/raw/` and `data/processed/` directories for data hygiene
- [ ] T001c Create `results/` and `results/plots/` directories for artifacts
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scikit-learn, opencv-python, scikit-image, matplotlib, seaborn, requests, huggingface_hub, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup `code/utils/config.py` for paths, random seeds (`np.random.seed`, `random.seed`), and hyperparameters
- [X] T005 [P] Implement `code/utils/logging.py` for exclusion logging, fallback events, and methodological notes

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download/generate and preprocess datasets with documented microstructural and fatigue test parameters to produce a clean, validated CSV.

**Independent Test**: Verify pipeline downloads/generates ≥100 records, excludes incomplete ones, and produces a validated CSV with required columns.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data generation logic in `tests/unit/test_data_generation.py`
- [~] T011 [P] [US1] Integration test for data cleaning pipeline in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [X] T007 [US1] **Attempt Real Data Download**: Implement `code/01_data_acquisition.py` to attempt downloading aluminum alloy fatigue data from HuggingFace Datasets and NIST Materials Data Repository. Include retry logic (3 attempts, exponential backoff). **Do NOT trigger fallback here**; if download fails, log failure and exit with error code to trigger T010.
- [X] T010 [US1] **Handle Download Failure**: Implement logic in `code/01_data_acquisition.py` to handle T007 failure. **Default Action**: Halt execution and log error. **Conditional Action**: If `config.allow_synthetic_fallback` is True, log warning and proceed to T008. This enforces FR-001 strictness. <!-- FAILED: unspecified -->
- [X] T008 [US1] **Define Synthetic Generator Schema**: Define the statistical parameters for synthetic data generation in `code/utils/generator_config.py`: mean/std for grain size, secondary phase, dislocation proxy; correlation matrix; and explicit fields for `alloy_batch_id` and `heat_treatment_group` to support grouped CV. Set `random_seed=42`.
- [X] T009 [US1] **Implement Synthetic Generator (Fallback)**: Implement the deterministic synthetic data generator in `code/01_data_acquisition.py`. **ONLY EXECUTE IF T010 TRIGGERS**. Generate N=150 records using the schema from T008. Ensure `alloy_batch_id` and `heat_treatment_group` are included.
- [X] T011 [US1] **Generate Synthetic Voronoi Images**: Implement `code/01_data_acquisition.py` to generate synthetic 512×512 grayscale Voronoi tessellation images for testing the image pipeline. Save to `data/raw/synthetic_images/`. **Required for T020 fallback path**.
- [ ] T012 [US1] **Validate Raw Data**: Validate that the downloaded (T007) or synthetic (T009) data meets statistical properties (mean, std, correlation) and contains all required columns. **Explicitly calculate and log the percentage of records missing specific microstructural features** to verify the ≥80% threshold required by FR-003. Save to `data/raw/validated_data.csv`.
- [ ] T014 [US1] **Clean and Impute Data**: Implement data cleaning in `code/01_data_acquisition.py`. Remove records with missing fatigue cycles or unverified microstructure. **Conditional Logic**: If missing microstructural features < 20% of remaining records, impute using **median**; otherwise, exclude the record. Log the method used (impute/exclude) and counts to `results/exclusion_report.log`.
- [ ] T016 [US1] **Save Cleaned Dataset**: Save the final cleaned dataset to `data/processed/cleaned_aluminum_fatigue.csv` with schema validation. Ensure all required columns are present.
- [ ] T017 [US1] **Document Data Source**: Update `results/data_source_report.md` to explicitly state whether data was real (T007) or synthetic (T009) and log the fallback reason if applicable.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Microstructural Feature Extraction and Model Training (Priority: P2)

**Goal**: Extract quantitative features from images (or use tabular fallback) and train regression models under strict CPU constraints.

**Independent Test**: Run feature extraction and training on sample data; verify `results/metrics.json` contains `r_squared`, `rmse`, `mean_absolute_error`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for image processing fallback in `tests/unit/test_feature_extraction.py`
- [ ] T019 [P] [US2] Integration test for model training pipeline in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T020 [US2] **Implement Feature Extraction Pipeline**: Implement `code/02_feature_extraction.py` to:
 1. **Load** 512×512 microscopy images (real or synthetic Voronoi from T011) and verify dimensions.
 2. **Convert** to grayscale and apply OpenCV thresholding for grain boundary detection.
 3. **Quantify** grain size (equivalent diameter distribution), secondary phase fraction (area %), and dislocation density proxies using **GLCM contrast, energy, and entropy** (texture metrics).
 4. **Output**: Save feature matrix to `data/processed/feature_matrix.csv`. **Explicitly include an `is_proxy` boolean column** for dislocation density features as required by FR-013.
 5. **Fallback**: If images are missing, skip image processing and use tabular data only, logging the event.
- [ ] T021 [US2] **Implement Model Training**: Implement `code/03_model_training.py` to fit Random Forest, Gradient Boosting, and ElasticNet models (≤100 trees/estimators).
- [ ] T022 [US2] **Implement Grouped Cross-Validation**: Implement 5-fold *grouped* cross-validation (stratified by `alloy_batch_id` and `heat_treatment_group` from T008) in `code/03_model_training.py`.
- [ ] T023a [US2] **Implement Memory Profiling**: Implement memory profiling in `code/03_model_training.py` using `tracemalloc` or similar. Log peak usage to `results/memory_profile.log`.
- [ ] T023b [US2] **Enforce RAM Constraints**: Add a check in `code/03_model_training.py` that raises an error if peak memory usage > 7GB, ensuring FR-006 compliance.
- [ ] T024 [US2] **Evaluate Models**: Evaluate models on held-out test data and compute R², RMSE, MAE in `code/03_model_training.py`. **Log whether data source was real or synthetic** for context.
- [ ] T026 [US2] **Label Proxy Features**: Ensure the `is_proxy` boolean flag from T020 is propagated to the final visualization labels and report text to satisfy FR-013.
- [ ] T025 [US2] **Save Metrics**: Save metrics to `results/metrics.json` with defined schema, including the `is_proxy` context from T026.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Results Visualization (Priority: P3)

**Goal**: Perform statistical significance testing, bootstrapping, and generate visualizations to interpret findings.

**Independent Test**: Run statistical analysis; verify `results/anova_summary.csv` exists with `feature`, `p_value`, `significance_flag`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for ANOVA logic in `tests/unit/test_statistical_analysis.py`
- [ ] T031 [P] [US3] Integration test for visualization generation in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [ ] T032 [US3] **Implement ANOVA/Kruskal-Wallis**: Implement `code/04_statistical_analysis.py` to perform ANOVA on log10-transformed fatigue life (or Kruskal-Wallis if normality violated) with α = 0.05.
- [ ] T033 [US3] **Apply Multiple-Comparison Correction**: Implement logic in `code/04_statistical_analysis.py` to **select and document** the multiple-comparison correction method (Bonferroni or Benjamini-Hochberg) based on a configuration choice, ensuring FR-012 flexibility.
- [ ] T034 [US3] **Compute Confidence Intervals**: Compute confidence intervals via bootstrapping (a sufficient number of resamples) for R², RMSE, MAE in `code/04_statistical_analysis.py`.
- [ ] T035 [US3] **Save ANOVA Results**: Save ANOVA results to `results/anova_summary.csv` with `feature`, `p_value`, `significance_flag`.
- [ ] T036a [US3] **Retrain Models Without Proxy**: Implement logic in `code/04_statistical_analysis.py` to retrain the selected model **excluding the dislocation density proxy features** to generate baseline metrics for comparison.
- [ ] T036b [US3] **Implement Sensitivity Analysis**: Compare model performance (R², RMSE) with and without the dislocation density proxy using results from T036a. Save results to `results/sensitivity_proxy_comparison.csv`.
- [ ] T037 [US3] **Generate Visualizations**: Implement `code/05_visualization.py` to generate partial dependence plots and feature importance charts.
- [ ] T038 [US3] **Ensure Plot Sizes**: Ensure all PNG outputs in `results/plots/` are ≤500 KB.
- [ ] T039 [US3] **Frame Findings**: Modify `code/05_visualization.py` to programmatically append an "Associational Only" disclaimer to the caption of every generated plot. Update `results/methodology_report.md` to include a prominent disclaimer paragraph, satisfying FR-011.
- [ ] T040 [US3] **Document Limitations**: Append a "Limitations" section to `results/methodology_report.md` detailing the synthetic data proxy assumptions and the lack of real TEM/XRD validation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure compliance with constraints

- [ ] T041 [P] Documentation updates in `docs/` and `specs/001-influence-of-microstructural-features-on/research.md` regarding synthetic data limitations
- [ ] T042a [P] Refactor `code/01_data_acquisition.py` to reduce cyclomatic complexity < 10
- [ ] T042b [P] Refactor `code/03_model_training.py` to reduce cyclomatic complexity < 10
- [ ] T043 [P] Profile `code/03_model_training.py` and optimize loops to ensure total runtime < 6 hours on 2 CPU cores, logging results to `results/performance_report.md`
- [ ] T044 [P] Additional unit tests for edge cases (missing images, high collinearity) in `tests/unit/`
- [ ] T045 Verify collinearity diagnostics (VIF) are computed and reported, explicitly referencing the 'Assumptions' section in spec.md.
- [ ] T046 Run `quickstart.md` validation to ensure pipeline executes end-to-end

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
- **User Story 2 (P2)**: **Depends on T016** (cleaned CSV from US1) and **T011** (synthetic images for fallback) - Cannot start until US1 data and images are ready.
- **User Story 3 (P3)**: **Depends on T025** (metrics.json from US2) - Cannot start until US2 models are trained.

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
Task: "Contract test for data generation logic in tests/unit/test_data_generation.py"
Task: "Integration test for data cleaning pipeline in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement data generation in code/01_data_acquisition.py"
Task: "Implement exclusion logic in code/01_data_acquisition.py"
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
- **Critical Constraint**: All data processing must be CPU-only (no CUDA/GPU); dislocation density is a proxy; findings are associational; synthetic data used for validation only.
- **Data Flow (Real Path)**: T007 (Download) -> T012 (Validate) -> T014 (Clean) -> T016 (Save) -> T020 (Extract) -> T021 (Train) -> T025 (Metrics) -> T032 (Analyze).
- **Data Flow (Fallback Path)**: T007 (Fail) -> T010 (Halt/Fallback Trigger) -> T008 (Schema) -> T009 (Generate) -> T011 (Gen Images) -> T012 (Validate) -> T014 (Clean) ->... (rest of flow).