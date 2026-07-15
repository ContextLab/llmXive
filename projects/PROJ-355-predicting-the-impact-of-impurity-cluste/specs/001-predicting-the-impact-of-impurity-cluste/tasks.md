# Tasks: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Input**: Design documents from `/specs/001-impurity-clustering-segregation/`
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

**Purpose**: Project initialization, basic structure, and core validation utilities required by downstream tasks.

- [X] T001 [P] Initialize project structure by creating root directory `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/` and subdirectories `code/`, `data/raw/`, `data/processed/`, `results/`, `tests/unit/`, `tests/integration/` idempotently.
- [ ] T002 Create `requirements.txt` with pinned versions: `The plan specifies using pymatgen version 2024.1.1. `, `{{claim:c_362e5c97}} `, `{{claim:c_80d0456f}} `, `{{claim:c_6971ed96}} `, `{{claim:c_2dfdce10}} `, `{{claim:c_a4cfd971}} `, `{{claim:c_82f22382}} `, `{{claim:c_a19926d3}} `
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-355-predicting-the-impact-of-impurity-cluste/`
- [X] T004a [P] Implement `contracts/dataset.schema.yaml` defining required fields: `bulk_config_id`, `impurity_species`, `segregation_energy`, `clustering_descriptors`
- [X] T004b [P] Implement `contracts/output_schema.schema.yaml` defining required fields: `r2`, `rmse`, `p_values`, `confidence_intervals`
- [X] T004c Implement `code/validators.py` with function `def validate_citations(url: str, metadata_path: str) -> bool`. Logic:
 1. Parse `metadata_path` (data/metadata.yaml) to extract URLs.
 2. Check extracted URLs against a hardcoded whitelist: `['https://materialsproject.org', '']`.
 3. Verify the URL exists via HTTP HEAD request.
 4. Return `True` if the URL is in the whitelist and reachable, `False` otherwise.
 5. If `False`, raise a `ValueError` with message `[DATA_UNAVAILABLE] URL=<url>`.
 **Note**: Title-token-overlap is NOT used here as it is reserved for literature citations per Constitution Principle II. This task provides the mandatory implementation for the Reference-Validator Agent logic required by FR-001 and Constitution Principle II. **Dependency**: Must be completed before T013.
- [X] T005 [P] Create `code/config.py` for paths, random seeds, hyperparameters, and the `VALIDATED_SOURCE_WHITELIST` list (MP/OQMD URLs).
- [X] T005b [P] Generate the methodology sketch in `docs/methodology.md` defining the k-fold CV procedure, random seed (fixed), and LOOCV fallback logic
- [X] T006 [P] Setup `code/data/__init__.py` and `code/modeling/__init__.py`
- [ ] T008 [P] Setup `data/raw/`, `data/processed/`, and `results/` directory structure with `.gitkeep`
- [ ] T009 [P] Create `tests/unit/` and `tests/integration/` scaffolding

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes the pipeline skeleton.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 [P] [US1] Implement `code/main.py` pipeline orchestration with error handling and logging. Logic:
 1. Define the *logical* sequence: `download_bulk_configs` -> `build_gb_supercells` -> `compute_descriptors` -> `run_simulation`.
 2. **Note**: This task defines the orchestration flow. The actual implementation of `download.py` (T013), `gb_builder.py` (T014), etc., occurs in Phase 3. The code in T007 will call these modules once they are implemented.
 3. Ensure the script handles the `[DATA_UNAVAILABLE]` error from T013 gracefully by logging and exiting cleanly.
- [ ] T010 [P] [US1] Unit test for retry logic in `tests/unit/test_download_retry.py`
- [ ] T011 [P] [US1] Unit test for interface-region descriptor filtering in `tests/unit/test_descriptor_interface.py`
- [~] T012 [P] [US1] Integration test for full data pipeline in `tests/integration/test_data_pipeline.py` <!-- FAILED: unspecified -->
- [ ] T012a [P] [US1] Unit test for segregation energy generation verification in `tests/unit/test_energy_generation.py`. Logic: Verify that `simulate_energy.py` produces non-empty results and logs the count of generated energies. Tag [FR-003]. <!-- FAILED: unspecified -->

**Checkpoint**: Foundation and testing scaffolding ready.

---

## Phase 3: User Story 1 - Data Pipeline and Clustering Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Download bulk configurations (MP/OQMD), construct GB supercells, compute clustering descriptors (RDF, pair correlation, Voronoi-based neighbor counts) in the interface region, and generate segregation energies via simulation (since energies are NOT in MP/OQMD).

**Independent Test**: Can be fully tested by executing the data pipeline script on a representative sample of bulk configurations, verifying that GB supercells are constructed, impurities are inserted at the interface, descriptors are computed from the interface region, and segregation energies are generated via simulation, with non-empty values saved to disk.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/download.py` with function `def download_bulk_configs(url: str, max_retries: int = 3) -> Path`.
 1. MUST invoke `validate_citations(url, 'data/metadata.yaml')` from `code/validators.py` (T004c) **after T004c is completed**.
 2. MUST log `[DATA_UNAVAILABLE] URL=<url> attempts=3` after 3 failed attempts.
 This task fetches bulk structures from MP/OQMD. **Dependency**: Requires T004c completion.
- [~] T013b [US1] Verify the `[DATA_UNAVAILABLE]` log format and 3-attempt limit behavior in isolation; ensure log output matches exact format
- [~] T017 [US1] Add contract validation in `code/data/download.py` to validate output against `contracts/dataset.schema.yaml` BEFORE GB construction
- [X] T014 [P] [US1] Implement `code/data/gb_builder.py` to construct GB supercells and insert impurities at the interface
- [~] T015 [US1] Implement `code/data/descriptors.py` to compute RDF peaks (using a defined cutoff from the GB plane), pair correlation statistics, and Voronoi-based neighbor counts specifically within the GB interface region (FR-002); Output: `data/processed/descriptors.csv` with columns [species, rdf_peak, pair_corr, voronoi_count].
 **Constraint**: Do NOT apply PCA. The Plan's mention of PCA in 'Phase 1' is an error; Spec FR-007 mandates retaining raw descriptors and reporting collinearity descriptively only. T015 takes precedence over the Plan's contradictory instruction.
- [X] T015b Implement logic in `code/data/descriptors.py` or a new helper to extract and tag each configuration with its `alloy_system_id` based on impurity species and bulk crystal structure.
 **Logic**: Generate `alloy_system_id` as `f"{crystal_system}_{impurity_species}"` (e.g., 'BCC_Cr'). `crystal_system` must be derived deterministically from the bulk configuration file using pymatgen's `get_space_group_symbol` or `lattice` properties (e.g., 'BCC', 'FCC').
 Output: `data/processed/alloy_systems.json`.
 **Dependency**: Must be completed before T025. **Not [P]** - strictly sequential within US1.
- [X] T016a [US1] Define the 'structurally perturbed representation' logic and 'specific NIST EAM potential' parameters in `code/data/simulate_energy.py` constants:
 1. **Perturbation**: Apply a random atomic displacement to all atoms in the GB supercell (small magnitude to break symmetry). **MUST use a pinned random seed from `code/config.py`** to ensure reproducibility (Constitution Principle I).
 2. **Potential**: The document specifies using a specific NIST EAM potential for Fe-Cr from the NIST repository.
 3. **Rationale**: This minimal perturbation breaks the exact symmetry of the input structure to avoid circularity while remaining physically plausible for a "distinct representation".
 This task explicitly defines the scientific parameters required for T016b. **Dependency**: Requires T014 (GB Builder) to be completed.
- [X] T016b [US1] Implement the simulation engine in `code/data/simulate_energy.py` that applies the perturbation logic from T016a and calculates segregation energy using the NIST EAM potential for Fe-Cr defined in T016a. This task implements the engine using the parameters defined in T016a. **Dependency**: Requires T014 (GB Builder) to be completed.
- [~] T016c [US1] Implement `code/data/simulate_energy.py` runner function `run_simulation` to execute the engine on the generated GB supercells and output `data/processed/segregation_energies.csv`. This task depends on T016b. **Dependency**: Requires T014 (GB Builder) to be completed. <!-- FAILED: unspecified -->
- [~] T018 [US1] Implement `code/data/descriptor_filter.py` to compute VIF (Variance Inflation Factor) on descriptors. **Action**: Detect collinearity (VIF ≥ 10 (2005.02245, https://arxiv.org/abs/2005.02245)) and **generate a descriptive report** `data/processed/collinearity_report.md` explaining joint relationships. **Do NOT remove features** in this task; only report. (FR-007). Report format: VIF scores per feature, descriptive text for joint relationships, no feature removal.
- [ ] T019 [US1] Implement filtering logic for bulk configurations with zero impurity atoms; log exclusion count to `data/processed/preprocessing_report.json`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Regression Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a lightweight regression model (Linear Regression for MVP p-values), perform 5-fold CV (or LOOCV), and report R², RMSE, and p-values (coefficients for Linear).

**Independent Test**: Can be fully tested by running the training script on a held-out test set of samples and verifying that R², RMSE, and p-values are computed and saved with valid numeric outputs.

**⚠️ Dependency**: This phase requires completion of Phase 3 (US1), specifically T016c (energies) and T015 (descriptors).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for CV split logic in `tests/unit/test_cv_split.py`
- [X] T021 [P] [US2] Unit test for metric calculation (R², RMSE, p-values) in `tests/unit/test_metrics.py`
- [X] T022 [P] [US2] Integration test for model training and evaluation in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [~] T027 [US2] Add contract validation in `code/modeling/train.py` to validate input against `contracts/dataset.schema.yaml` BEFORE training
- [X] T023 [US2] Implement `code/modeling/train.py` with **Linear Regression** as the primary model for the MVP to satisfy the 'coefficient p-values' requirement (US-2).
 1. **Cross-Validation**: Implement a **manual k-fold CV loop** (or use `sklearn`'s `cross_val_score` with a custom estimator wrapper) to satisfy FR-004. `statsmodels` OLS does not natively support CV loops.
 - Logic: {{claim:c_5c5df125}} (2604.10702, https://arxiv.org/abs/2604.10702). For each fold: Train `statsmodels.api.OLS` with `cov_type='HC3'` on 4 folds, predict on 1 fold. Compute R², RMSE.
 - Aggregate metrics across folds.
 2. **Collinearity**: If `data/processed/collinearity_report.md` (from T018) indicates VIF ≥ 10, log a warning that p-values may be unstable, but proceed with raw data (as per FR-007 "frame, don't remove").
 3. **Confidence Intervals**: Calculate confidence intervals for predictions as required by US-2.
 4. Save metrics to `results/metrics.json` with SHA256 hash recorded in `state/project.yaml` under key `code_version_hash` for provenance.
 **Dependency**: Requires T015 and T016c completion.
- [~] T025 [US2] Implement per-system evaluation logic to report R² values for each alloy system separately. **Dependency**: Requires `alloy_systems.json` from T015b to group samples. Use the `alloy_system_id` format defined in T015b (`f"{crystal_system}_{impurity_species}"`). If `alloy_systems.json` is missing, raise an error.
- [~] T026 [US2] Implement confidence interval calculation for predictions
- [~] T028 [US2] **REMOVED**: Logic merged into T023 to avoid race conditions and redundant writes.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Hypothesis Testing and Sensitivity Analysis (Priority: P3)

**Goal**: Perform sensitivity analysis on decision thresholds (regularization, descriptor perturbation) and hypothesis testing with multiple-comparison correction.

**Independent Test**: Can be fully tested by executing the sensitivity analysis script on a sample of predictions and verifying that at least 3 threshold values are swept and corresponding RMSE variance changes are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`
- [ ] T030 [P] [US3] Unit test for multiple-comparison correction (Bonferroni/FDR) in `tests/unit/test_hypothesis.py`
- [ ] T031 [P] [US3] Integration test for full hypothesis and sensitivity analysis in `tests/integration/test_hypothesis_sensitivity.py`

### Implementation for User Story 3

- [ ] T036 [US3] Add contract validation in `code/modeling/evaluate.py` to validate output against `contracts/output_schema.schema.yaml` BEFORE analysis
- [ ] T032 [US3] Implement `code/modeling/evaluate.py` with sensitivity analysis sweeping over at least 3 concrete threshold values (e.g., lambda=[0.01, 0.1, 1.0]); report RMSE variance and R² stability; output format: JSON with keys [threshold, rmse_variance, r2_stability] [FR-006]
- [ ] T033 [US3] Implement calculation of RMSE variance and R² stability across the threshold sweep
- [ ] T034a [US3] Implement logic to extract predictor significance: If Linear Regression (T023), extract coefficients and standard errors; if RandomForest (not used), compute permutation importance. Output to `results/feature_importance.json`.
- [ ] T034 [US3] Implement hypothesis testing for predictor coefficients (from T034a) with Bonferroni or FDR correction (FR-005) [FR-005]
- [ ] T035 [US3] Implement logic to handle non-significant results (p > 0.05) by documenting null results with p-values in `results/null_results_report.json`
- [ ] T037 [US3] Save sensitivity report to `results/sensitivity_report.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Update `README.md` with execution instructions and data provenance details
- [ ] T039 Code cleanup and refactoring for consistency
- [ ] T040 [P] Add additional unit tests for edge cases (collinearity, missing data) in `tests/unit/`
- [ ] T041 Run quickstart.md validation to ensure all scripts execute correctly on CPU-only runner
- [ ] T042 Verify all tasks run within 6 hours on CPU cores with sampled dataset

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**:
 - **Phase 3 (US1)**: Depends on Foundational (Phase 2).
 - **Phase 4 (US2)**: Depends on **completion of Phase 3 (US1)**, specifically T015, T016c, and T015b.
 - **Phase 5 (US3)**: Depends on completion of Phase 4 (US2).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **MUST wait for US1 data output** (T016c, T015b)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model output from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, **Phase 3 (US1) must complete before Phase 4 (US2) begins**.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only if US1 data is pre-generated or mocked for US2/US3 development, but final execution must be sequential.**

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for retry logic in tests/unit/test_download_retry.py"
Task: "Unit test for interface-region descriptor filtering in tests/unit/test_descriptor_interface.py"
Task: "Integration test for full data pipeline in tests/integration/test_data_pipeline.py"
Task: "Unit test for segregation energy generation verification in tests/unit/test_energy_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py with retry logic"
Task: "Implement code/data/gb_builder.py to construct GB supercells"
Task: "Implement code/data/descriptors.py for interface region descriptors"
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model) - **Can develop logic but must wait for US1 data for final run**
 - Developer C: User Story 3 (Analysis) - **Can develop logic but must wait for US2 output for final run**
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
- **Constraint**: All tasks must run on a CPU-only GitHub Actions runner with limited CPU and memory resources.; no GPU, no 8-bit/4-bit models, no deep learning.
- **Data**: All data must be real (MP/OQMD structures + Simulation energies); no fabrication or synthetic placeholders.
- **Scientific Constraint**: Segregation energies are generated via simulation (T016) because they are not available in MP/OQMD. Bulk structures are sourced from MP/OQMD (T013).
- **Reproducibility**: All random operations (perturbations, splits) MUST use seeds from `code/config.py`.
- **Plan Correction**: The Plan's mention of PCA in 'Phase 1' is an error; Spec FR-007 (report, don't remove) and Task T015 take precedence.