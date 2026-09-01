# Tasks: Predicting the Impact of Cold Rolling Reduction on Texture Evolution in FCC Metals

**Input**: Design documents from `/specs/001-predicting-cold-rolling-texture/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md (required for reduction levels)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can be developed in parallel (different files, no logical dependency)
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

- [X] T001a [P] Create `code/` directory. **Verify**: Ensure directory exists via `pathlib.Path.cwd().joinpath('code').is_dir()`.
- [X] T001b [P] Create `data/` directory. **Verify**: Ensure directory exists via `pathlib.Path.cwd().joinpath('data').is_dir()`.
- [X] T001c [P] Create `tests/` directory. **Verify**: Ensure directory exists via `pathlib.Path.cwd().joinpath('tests').is_dir()`.
- [X] T001d [P] Create `docs/` directory. **Verify**: Ensure directory exists via `pathlib.Path.cwd().joinpath('docs').is_dir()`.
- [X] T002 [P] Create `.gitignore` for Python, data, and IDE files.
- [X] T003 [P] Initialize Python project with `requirements.txt` (pinning `orix`, `scikit-learn`, `shap`, `pandas`, `numpy`, `pyyaml`, `requests`, `pytest` with explicit version specifiers, e.g., `>=1.0.0`, to ensure reproducibility per Constitution Principle I). **Verify**: Ensure file exists and contains pinned versions.
- [X] T004 [P] Configure linting (flake8/black) and formatting tools. **Verify**: Ensure config files (e.g., `.flake8`, `pyproject.toml` for black) exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create subdirectories `raw`, `processed`, `interim` within the existing `data/` folder with `.gitkeep` (Required by Plan.md Project Structure and FR-001 Data Hygiene). **Verify**: Ensure all subdirectories and `.gitkeep` files exist.
- [X] T006 [P] Implement base configuration loader for environment variables and seed management (`code/__init__.py`).
- [X] T007 [P] Setup logging infrastructure to track data lineage and processing steps (`code/utils/logging.py`).
- [X] T008a [P] Implement Pydantic model for 'EBSD Sample' (`code/data/models.py`).
- [X] T008b [P] Implement Pydantic model for 'Texture Descriptor' (`code/data/models.py`).
- [X] T009a [P] [US1] Unit test for point filtering logic in `tests/unit/test_preprocess.py`. **Logic**:
 1. `test_filter_points_below_confidence`: Verify that `code/data/preprocess.py` filters out individual data points with confidence index < 0.1 while keeping the sample object valid.
 2. `test_sample_rejection_not_triggered`: Verify that a sample with mixed confidence values (some < 0.1, some >= 0.1) is NOT rejected entirely, but processed with the valid points only. (US-1 Scenario 2, FR-002).
 3. **Dependency**: This task tests the logic implemented in T014 (`code/data/preprocess.py`).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel
**Dependency Note**: T012 and T014 are strictly blocked until T008a and T008b are complete.

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, filter, and standardize EBSD datasets for Al, Cu, and Ni across specific cold-rolling reductions to ensure the analysis is based on high-quality, crystallographically consistent data.

**Independent Test**: The pipeline can be tested by running the data acquisition script against the specified public repositories and verifying that the output is a tidy CSV/Parquet file containing only valid orientations with confidence indices ≥ 0.1, properly re-indexed to FCC symmetry.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests marked [P] can be written in parallel with implementation, but execution depends on the implementation being complete.

- [X] T010 [P] [US1] Contract test for data schema in `tests/contract/test_data_schema.py`
- [X] T011 [P] [US1] Write test stubs and assertions for the download and filter flow (can be written in parallel with T012 implementation) in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [X] T012b [US1] Implement `code/data/generate_synthetic.py` to create a verified synthetic EBSD dataset. **Logic**:
 1. **Purpose**: Provide a fallback data source when real data is unavailable, ensuring the pipeline does not crash (Plan.md Technical Context).
 2. **Generation**: Generate synthetic orientation data for Al, Cu, and Ni across the resolved reduction levels using a deterministic seed.
 3. **Metadata**: Ensure the generated data includes 'reduction' percentage and 'confidence' index fields.
 4. **Output**: Save to `data/raw/synthetic_ebsd.parquet`. (FR-001).
 5. **Dependency**: T012 depends on T012b.

- [X] T012 [US1] Implement `code/data/download.py` to fetch EBSD data. **Logic**:
 1. **Prerequisites**: This task requires `research.md`. **CRITICAL**: If `research.md` is missing or does not contain a valid `reduction_levels` list, the script MUST raise a `ValueError` with a clear message: "Missing reduction_levels in research.md. Define reduction levels (e.g., [0, 20, 40, 60, 80]) in research.md to proceed." **DO NOT** use hardcoded defaults. (FR-001, Spec US-1).
 2. **Primary Sources**: Attempt to fetch from Materials Project (API endpoint: `https://materialsproject.org/rest/v2/...`) and MTData repositories.
 3. **Fallback**: If primary sources fail (network error, 404), invoke the `generate_synthetic` function from `code/data/generate_synthetic.py` (T012b) to generate a verified synthetic EBSD dataset with reduction metadata. **DO NOT** raise `DataUnavailableError` unless BOTH real fetch AND synthetic generation fail. (FR-001, Constitution Principle I, Plan.md Technical Context).
 4. **Graceful Degradation**: If a specific source fails but others succeed, or if specific reduction levels are missing, **log a warning** and **continue processing** available data. Do NOT raise an error for partial data availability. Only raise an error if NO data is available at all. (US-1 Scenario 3, Edge Cases).
 5. **Reduction Levels Resolution**:
 - **Attempt 1**: Check if `research.md` exists in the project root. If it does, parse it for a `reduction_levels` key (list of integers) in YAML format.
 - **Attempt 2 (Failure)**: If `research.md` is missing, unreadable, or lacks the `reduction_levels` key, **FAIL THE TASK** with a clear error message requesting the user to define these levels. **DO NOT** proceed with arbitrary defaults. (Spec Edge Cases, SC-001).
 - **Execution**: Use the resolved list to filter or request data. If a specific level is missing in the source data, log a warning and proceed with available levels. If ALL levels for a specific metal are missing, log a warning and proceed with available metals/levels.
 6. **Data Hygiene**: Ensure all downloaded files are checksummed upon receipt. (FR-001).

- [X] T014 [US1] Implement `code/data/preprocess.py` to filter confidence index < 0.1 and re-index orientations to FCC symmetry using `orix`. **Logic**:
 1. Read reduction levels from the resolved list (as determined in T012).
 2. If specific levels are missing, proceed with available levels and log a warning.
 3. If ALL levels are missing, the script will have already failed in T012; this task assumes valid input exists. (FR-002).
 4. Integrate exclusion logic: flag samples where >50% of points are filtered as "low reliability" and EXCLUDE them from the final training set (Edge Case). (FR-001).
 5. **Symmetry Enforcement**: This is the sole mechanism for symmetry enforcement; no custom loss functions are used.

- [ ] T015 [US1] Generate consolidated Parquet output to `data/processed/cleaned_ebsd.parquet` with metadata (material, reduction, confidence). **Logic**:
 1. **Dependency**: This task depends on T012 (Download) and T014 (Preprocess).
 2. **Partial Data Handling**: If valid data exists (even if partial), generate the Parquet file with the available rows. Log a summary of excluded/missing entries.
 3. **Zero-Data Handling**: If the input data results in zero valid rows (e.g., all samples excluded due to low confidence or missing data), **fail** the task and do not generate an empty file. Log an error.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Texture Quantification and Descriptor Extraction (Priority: P2)

**Goal**: Convert raw orientation data into specific, quantifiable texture descriptors (Texture Index, Volume Fractions of Brass, Copper, S, and Goss components) to enable statistical modeling.

**Independent Test**: The quantification module can be tested by processing a known benchmark dataset and verifying that the calculated volume fractions match published values within ±0.05.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for Brass/Copper/S/Goss calculation logic in `tests/unit/test_descriptors.py`
- [X] T017 [P] [US2] Benchmark test against Rosenstock et al. (2018) values in `tests/unit/test_benchmark_validation.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `code/features/descriptors.py` to calculate Texture Index and volume fractions using MTEX-style search algorithms. **Logic**:
 1. **Reference**: Use the Euler angle ranges defined in Rosenstock et al. as the baseline.
 2. **Search Window**: Implement a configurable search window of ±5 degrees around the central values to account for lattice rotation spread. **Use `orix`'s `Orientation` class symmetry definitions** to ensure alignment with standard FCC symmetry.
 3. **Euler Ranges (phi1, Phi, phi2 in degrees)**: Define ranges as [phi1_min, phi1_max, Phi_min, Phi_max, phi2_min, phi2_max] using `orix`'s standard definitions.
 - **Brass**: [35, 45, 55, 65, 0, 90]
 - **Copper**: [39, 39, 39, 39, 0, 0] (Point component)
 - **S**: [59, 59, 37, 37, 63, 63] (Point component)
 - **Goss**: [0, 0, 45, 45, 90, 90] (Point component)
 4. **Symmetry**: Re-index orientations to FCC symmetry using `orix` before calculation (FR-002).
 5. **Output**: Calculate and return scalar values for each component. (FR-003).
 6. **Artifact**: Output the calculated descriptors to `data/processed/descriptors.csv`.

- [X] T018b [US2] Implement explicit benchmark comparison logic in `code/features/benchmark_validation.py`. **Logic**:
 1. **Purpose**: Explicitly implement the Independent Test for US-2 (Rosenstock et al. validation).
 2. **Input**: Load `data/processed/descriptors.csv` and `data/processed/benchmark_data.json` (fetched by T018c).
 3. **Calculation**: For each matching sample in the dataset, calculate the absolute difference (delta) between the calculated volume fractions and the benchmark values.
 4. **Assertion**: Verify that `delta <= 0.05` for all components (Brass, Copper, S, Goss).
 5. **Output**: Generate a report `data/processed/benchmark_validation_report.json` containing the pass/fail status and delta values. If any delta > 0.05, log an error and flag the sample. (Spec US-2 Independent Test, SC-002).

- [ ] T018c [US2] Download and verify benchmark dataset from canonical source. **Logic**:
 1. **Source**: Fetch the benchmark dataset (Rosenstock et al., 2018) from a verified HuggingFace dataset or UCI repository. If no public dataset exists, generate it via a verified script `code/data/generate_benchmark.py` and save to `data/processed/benchmark_data.json`.
 2. **Validation**: Verify the dataset contains the required fields (Material, Reduction, Brass, Copper, S, Goss).
 3. **Output**: Save to `data/processed/benchmark_data.json`. (SC-002, Constitution Principle IV).

- [ ] T019 [S] [US2] Implement mass balance check: explicitly verify that the sum of major components (Brass, Copper, S, Goss) plus the "random" fraction equals 1.0 ± 0.01 for every sample. **Requirement**: This task is mandatory to verify spec.md US-2 Scenario 2 acceptance criteria. If the check fails, **flag the sample as invalid and exclude it from output**, but **DO NOT halt the pipeline**. Log the exclusion. (Edge Cases). **Output**: Generate `data/processed/mass_balance_report.json` listing excluded samples and reasons. **Dependency**: T019 must run BEFORE T018b and T020a to ensure only valid data is used for benchmarking.

- [ ] T020a [US2] Output descriptors to `data/processed/descriptors.csv` linked to original sample IDs. **Dependency**: This task depends on T019 completion. It must use the **filtered** dataset (excluding samples flagged by T019) to generate the final CSV. **Logic**:
 1. Load the dataset from T018.
 2. Apply the exclusion list from T019 (mass balance failures).
 3. Save the clean, valid samples to `data/processed/descriptors.csv`. (US-2 Scenario 2).

- [ ] T020b [US2] Implement system-level mass balance verification on `data/processed/descriptors.csv`. **Logic**: After generating the CSV, aggregate the data and verify that the sum of Brass, Copper, S, Goss, and random components equals 1.0 ± 0.01 for the aggregated dataset. **Requirement**: This task is mandatory to verify spec.md US-2 Scenario 2 acceptance criteria at the system level, distinct from T009a (schema test). **Output**: Generate `data/processed/system_mass_balance_summary.json`.

- [ ] T021 [US2] Add validation to flag samples where texture evolution deviates from standard FCC trends (Edge Case). **Logic**: If a metal's texture evolution does not follow standard FCC trends (e.g., anomalous behavior), flag these outliers during validation rather than forcing a fit. **Requirement**: This task is mandatory to verify spec.md Edge Cases acceptance criteria.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Validation (Priority: P3)

**Goal**: Train predictive models (Polynomial Regression, Gaussian Process) to estimate texture descriptors based on cold-rolling reduction with high accuracy (R² ≥ 0.85).

**Independent Test**: The model training and validation pipeline can be tested by splitting the dataset and verifying that the R² on the held-out test set meets a satisfactory performance threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T023 [P] [US3] Integration test for k-fold CV pipeline in `tests/integration/test_model_training.py`

### Implementation for User Story 3

- [X] T024 [US3] Implement `code/models/train.py` to fit separate polynomial (degree=2) and joint Gaussian Process (RBF kernel) models. **Mandatory**:
 1. **Hyperparameters**: Use GP length_scale search space [lower bound, upper bound]; Polynomial regularization (alpha) in a range spanning from a small to a moderate magnitude..
 2. **Feature Engineering**: Include 'Material Type' as a categorical feature (one-hot encoded) in the joint model to satisfy FR-008.
 3. **Variance Reporting**: After training, calculate the residual variance attributed to missing microstructural variables using the utility function in `code/analysis/variance_utils.py` (extracted from T032 logic) and **explicitly include this metric in the final model report output** (e.g., `model_report.json`). (FR-008).
 4. **Output**: Return fitted models and training metrics. (FR-004, FR-008).

- [ ] T025 [US3] Implement k-fold cross-validation in `code/models/validate.py` to output RMSE and R² metrics (FR-005)
- [ ] T026 [US3] Implement extrapolation flagging: explicitly check if predictions are made outside the **dynamic** training data range. **Logic**: Calculate the min and max reduction values from the **training set** used for the specific model. If a prediction is made outside `[min_train, max_train]`, flag it as "extrapolated" and apply a confidence penalty factor to the standard error. **Requirement**: This task is mandatory to verify spec.md FR-009 acceptance criteria. Do NOT use a fixed global constant like [0, 80].
- [ ] T027 [US3] Implement "Hold-out Physics Check" in `code/analysis/physics_check.py` to validate that trends (e.g., Brass increase) match known physics AND ensure all output reports explicitly frame findings as associational relationships (FR-006). **Report Template**: Generate a Markdown report with sections: 'Observed Trend', 'Expected Physics', 'Deviation Metric', 'Associational Framing Statement' (must state 'No causal claims; correlation only'). **Note**: This task focuses on trend validation, not symmetry constraints (which are handled in T014).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Model Robustness and Extrapolation Bounds (Priority: P4)

**Goal**: Ensure model stability under data sparsity and quantify the impact of missing microstructural variables.

**Independent Test**: The robustness module can be tested by running sensitivity analysis on interpolation tolerance and verifying R² variation ≤ 0.02.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [US4] Unit test for sensitivity analysis logic in `tests/unit/test_robustness.py`. **Note**: This task is REQUIRED to verify SC-004 and must be implemented.
- [ ] T029 [P] [US4] Integration test for variance decomposition in `tests/integration/test_variance_decomposition.py`

### Implementation for User Story 4

- [ ] T030 [US4] Implement `code/analysis/robustness.py` to perform a sensitivity analysis. **Logic**:
 1. Define the set of interpolation tolerances: `{0.01, 0.05, 0.1}` as mandated by FR-007.
 2. **Sweep Loop**: For each tolerance value `t` in the set:
 - **Query Definition**: `reduction_query` is a specific test point (e.g., from the test set).
 - **Training Definition**: `reduction_train` is the nearest training point to `reduction_query`.
 - **Distance Metric**: Calculate `abs(reduction_query - reduction_train)`.
 - **Filter**: **Filter the dataset** to keep only points where `nearest_neighbor_distance <= t`.
 - Train/evaluate the model on the **filtered** dataset.
 - Record the R² value.
 3. **Stability Check**: Verify that the variation in R² across the swept tolerances is ≤ 0.02. If the variation exceeds 0.02, **FLAG THE REPORT AS UNSTABLE** but **DO NOT FAIL THE TASK**. (FR-007, SC-004).
 4. **Output**: Generate `data/processed/sensitivity_analysis.csv` containing the R² values for each tolerance and a stability flag. (FR-007).

- [ ] T031 [US4] Verify R² variation remains ≤ 0.02 across the swept tolerances {0.01, 0.05, 0.1} using T030 output (US-4 Scenario 2). **Requirement**: This task is mandatory to verify spec.md SC-004 acceptance criteria.
- [ ] T032 [US4] Implement variance decomposition (Shapley values or Hierarchical Modeling) to quantify residual variance from missing microstructural variables (FR-008). **Note**: Logic extracted to `code/analysis/variance_utils.py` for use by T024.
- [ ] T033 [US4] Report the percentage of variance attributable to missing variables (e.g., grain size, SFE) in final metrics (US-4 Scenario 3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Validation & Physical Consistency (Revision Response)

**Purpose**: Address reviewer concern (Rosalind Franklin) regarding crystallographic mechanisms vs. statistical correlation.

**Goal**: Explicitly validate that the ML predictions align with known physical trends (e.g., Brass increase) using scalar descriptors, avoiding the need for full ODF reconstruction.

### Implementation for Physical Validation

- [ ] T034 [US3] Implement `code/analysis/trend_consistency_check.py` to validate predicted texture trends against known physics. **Logic**:
 1. **Input**: Use the `data/processed/descriptors.csv` (predicted) and `data/processed/cleaned_ebsd.parquet` (ground truth). **Dependency**: T018 (Ground Truth Descriptors).
 2. **Trend Validation**: Verify that predicted trends (e.g., Brass increasing with reduction) align with known physics for each metal.
 3. **Mass Balance Check**: Verify that the sum of predicted volume fractions (Brass + Copper + S + Goss + Random) equals 1.0 ± 0.01 for each prediction, ensuring physical plausibility without requiring full ODF reconstruction.
 4. **Threshold**: Flag the model as "Physically Invalid" if trends deviate significantly from known physics or if mass balance is violated. (Reviewer Concern: "Distinguish between physical structure and statistical correlation").
 5. **Dependency**: Depends on T015 (Cleaned Data) and T018 (Descriptor Extraction).
- [ ] T035 [US3] Integrate lattice symmetry constraints into the validation pipeline. **Logic**:
 1. Verify that the predicted texture components strictly adhere to FCC symmetry operations (no "ghost" peaks appearing in forbidden regions).
 2. Implement a check that ensures the sum of intensities in symmetry-equivalent regions matches within a tolerance (e.g., ±2%) using the available volume fractions.
 3. If symmetry violations are detected, raise a `SymmetryViolationError` and exclude the prediction from the final report. (Reviewer Concern: "Explicit constraints on lattice symmetry").
- [ ] T036 [US3] Update `code/analysis/physics_check.py` to document missing microstructural variables. **Logic**:
 1. Explicitly document that dislocation density data (KAM) is not available in the source EBSD files.
 2. State that the model relies on reduction percentage as a proxy and that residual variance is attributed to these unobserved confounders.
 3. Perform a correlation analysis between the predicted texture evolution and available proxies (if any) to ensure the model isn't ignoring microstructural evidence. (Reviewer Concern: "Explicit constraints on... dislocation density").
- [ ] T037 [US3] Generate a "Physical Consistency Report" in `docs/physical_consistency_report.md`. **Content**:
 1. Summary of trend consistency validation accuracy.
 2. Summary of lattice symmetry violation checks.
 3. Discussion of the relationship between predicted texture and available microstructural proxies (None; documented as unobserved confounders).
 4. Explicit statement on whether the model distinguishes physical structure from statistical correlation based on the above evidence.

**Checkpoint**: All user stories and physical validation checks are complete.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] Documentation updates in `docs/` including model limitations, associational framing, the sensitivity analysis methodology, the physics validation results, and the scalar trend validation findings.
- [ ] T046 Code cleanup and refactoring for CPU efficiency (ensure no GPU calls)
- [ ] T047 [P] Additional unit tests for edge cases (missing data, extrapolation, symmetry errors, scalar-based validation failures) in `tests/unit/`
- [ ] T048 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T049 Verify all artifacts (data, models, metrics, scalar descriptors) are derived via script (Constitution Principle IV)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validation (Phase 7)**: Depends on US3 (Modeling) and US4 (Robustness) outputs
- **Polish (Final Phase)**: Depends on all desired user stories, validation, and scalar checks being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T015)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 descriptor output (T020a/T020b)
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US3 model output (T024/T025)
- **Validation (Phase 7)**: Depends on US3 (Modeling) and US4 (Robustness) outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel (development phase only)
- Different user stories can be worked on in parallel by different team members
- Phase 7 (Validation) can run in parallel once US3 is complete

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema in tests/contract/test_data_schema.py"
Task: "Write test stubs and assertions for the download and filter flow in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py" (Note: T012 is NOT parallel-safe with T014 due to reduction_levels resolution)
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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add Validation (Phase 7) → Test independently → Deploy/Demo
7. Add Polish → Final Release
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: User Story 4
 - Developer E: Validation (Phase 7)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no logical dependencies (can be developed in parallel)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Review Update**: Phase 8 (T038-T041) removed as pole figure reconstruction from scalars is mathematically impossible. Replaced with T034 (Trend Consistency) for scalar-based validation.
- **Critical Review Update**: T012 logic corrected to require `research.md` for reduction levels; no hardcoded defaults allowed.
- **Critical Review Update**: T030 updated to explicitly describe the dynamic sweep loop for R² stability verification over `{0.01, 0.05, 0.1}` using nearest-neighbor distance filtering instead of model bandwidth.
- **Critical Review Update**: T018 updated to reference Rosenstock et al. (2018) and implement configurable search window using `orix` symmetry definitions.
- **Critical Review Update**: T026 updated to use **dynamic** training data bounds for extrapolation threshold.
- **Critical Review Update**: T020 split into T020a (output) and T020b (system-level mass balance verification). T020a now depends on T019.
- **Critical Review Update**: Task statuses corrected (T001-T005, T048-T049) to reflect actual artifact existence.
- **Critical Review Update**: T013 merged into T012/T014; T015 dependencies updated.
- **Critical Review Update**: T009 split into T009a (schema) and T009b (aggregation).
- **Critical Review Update**: T036 updated to document missing data rather than extract it.
- **Critical Review Update (Rosalind Franklin)**: Phase 8 (T038-T041) removed. Phase 7 (T034-T037) updated to focus on scalar trend validation.
- **Critical Review Update**: T009b moved to Phase 4 to align with data availability.
- **Critical Review Update**: T019 tag updated to reflect sequential dependency (runs before T018b).
- **Critical Review Update**: T012 updated to remove unauthorized hardcoded fallback and require `research.md` (now graceful degradation with default fallback from Plan.md).
- **Critical Review Update**: T012b moved to **precede** T012 in the task list order to match logical dependency.
- **Critical Review Update**: T024 updated to explicitly report residual variance using shared utility.
- **Critical Review Update**: T009a updated to test `test_filter_points_below_confidence` (testing point filtering in preprocess.py) to verify the correct threshold.
- **Critical Review Update**: T019 updated to **flag and exclude** rather than block the pipeline and to generate a specific report.
- **Critical Review Update**: T030 updated to generate a report instead of failing, resolving the stability check conflict.
- **Critical Review Update**: T018 updated to use `orix` symmetry definitions.
- **Critical Review Update**: T018c added to download benchmark data from canonical source.
- **Critical Review Update**: T009a updated to test point filtering in T014.
- **Critical Review Update**: T009a updated to depend on T014.
- **Critical Review Update**: T020a updated to depend on T019.
- **Critical Review Update**: T034 updated to depend on T018.
- **Critical Review Update**: Phase 8 (T038, T039) removed entirely. References to pole figures removed from Phase 9 (T045, T047).