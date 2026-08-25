# Tasks: Predicting the Impact of Cold Rolling Reduction on Texture Evolution in FCC Metals

**Input**: Design documents from `/specs/001-predicting-cold-rolling-texture/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

- [ ] T001a [P] Create `code/` directory. **Verify**: Ensure directory exists via `pathlib.Path(__file__).parent.joinpath('code').is_dir()`.
- [ ] T001b [P] Create `data/` directory. **Verify**: Ensure directory exists via `pathlib.Path(__file__).parent.joinpath('data').is_dir()`.
- [ ] T001c [P] Create `tests/` directory. **Verify**: Ensure directory exists via `pathlib.Path(__file__).parent.joinpath('tests').is_dir()`.
- [ ] T001d [P] Create `docs/` directory. **Verify**: Ensure directory exists via `pathlib.Path(__file__).parent.joinpath('docs').is_dir()`.
- [ ] T002 [P] Create `.gitignore` for Python, data, and IDE files.
- [X] T003 [P] Initialize Python project with `requirements.txt` (pinning `orix`, `scikit-learn`, `shap`, `pandas`, `numpy`, `pyyaml`, `requests`, `pytest` with explicit version specifiers, e.g., `>=1.0.0`, to ensure reproducibility per Constitution Principle I). **Verify**: Ensure file exists and contains pinned versions.
- [X] T004 [P] Configure linting (flake8/black) and formatting tools. **Verify**: Ensure config files (e.g., `.flake8`, `pyproject.toml` for black) exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create subdirectories `raw`, `processed`, `interim` within the existing `data/` folder with `.gitkeep` (Required by Plan.md Project Structure and FR-001 Data Hygiene). **Verify**: Ensure all subdirectories and `.gitkeep` files exist.
- [X] T006 [P] Implement base configuration loader for environment variables and seed management (`code/__init__.py`).
- [X] T007 [P] Setup logging infrastructure to track data lineage and processing steps (`code/utils/logging.py`).
- [X] T008a [P] Implement Pydantic model for 'EBSD Sample' (`code/data/models.py`).
- [X] T008b [P] Implement Pydantic model for 'Texture Descriptor' (`code/data/models.py`).
- [X] T009a [P] Implement unit tests for base schema validation in `tests/unit/test_models.py`. **Logic**:
 1. `test_EBSDSample_rejects_confidence_0.0`: Verify that an EBSD Sample with confidence index < 0.1 raises ValueError.
- [ ] T009b [P] Implement unit test for system-level mass balance aggregation in `tests/unit/test_mass_balance.py`. **Logic**:
 1. `test_aggregated_mass_balance`: Verify that the sum of Brass, Copper, S, Goss, and random components equals 1.0 ± 0.01 for an aggregated dataset; raise ValueError if outside tolerance. (Spec US-2 Scenario 2).

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

- [ ] T012 [US1] Implement `code/data/download.py` to fetch EBSD data. **Logic**:
 1. **Prerequisites**: This task requires `research.md` to exist (if it exists). If `research.md` is missing, proceed with the fallback logic.
 2. **Primary Sources**: Attempt to fetch from Materials Project (API endpoint: `https://materialsproject.org/rest/v2/...`) and MTData repositories.
 3. **Fallback**: If primary sources fail (network error, 404), attempt to fetch from a verified HuggingFace dataset (e.g., `huggingface.co/datasets/materials/ebsd_fcc_reductions`) ONLY if the dataset is documented to contain the specific 'reduction' metadata variable. The verification of the fallback source MUST be explicit (check `research.md` for a pinned URL or verify the dataset metadata programmatically).
 4. **Synthetic Generation**: If ALL real sources fail, invoke T012b (Synthetic Generator) to generate a verified synthetic EBSD dataset with reduction metadata. **DO NOT** raise `DataUnavailableError` unless BOTH real fetch AND synthetic generation fail. (FR-001, Constitution Principle I, Plan.md Technical Context).
 5. **Graceful Degradation**: If a specific source fails but others succeed, or if specific reduction levels are missing, **log a warning** and **continue processing** available data. Do NOT raise an error for partial data availability. Only raise an error if NO data is available at all. (US-1 Scenario 3, Edge Cases).
 6. **Reduction Levels Resolution**:
 - **Attempt 1**: Check if `research.md` exists in the project root. If it does, parse it for a `reduction_levels` key (list of integers).
 - **Attempt 2 (Fallback)**: If `research.md` is missing, unreadable, or lacks the key, use the hardcoded default list: `[0, 10, 20, 30, 40, 50, 60, 70, 80]`.
 - **Execution**: Use the resolved list to filter or request data. If a specific level is missing in the source data, log a warning and proceed with available levels. If ALL levels for a specific metal are missing, log a warning and proceed with available metals/levels.
 7. **Data Hygiene**: Ensure all downloaded files are checksummed upon receipt. (FR-001).
- [ ] T012b [US1] Implement `code/data/generate_synthetic.py` to create a verified synthetic EBSD dataset. **Logic**:
 1. **Purpose**: Provide a fallback data source when real data is unavailable, ensuring the pipeline does not crash (Plan.md Technical Context).
 2. **Generation**: Generate synthetic orientation data for Al, Cu, and Ni across the resolved reduction levels using a deterministic seed.
 3. **Metadata**: Ensure the generated data includes 'reduction' percentage and 'confidence' index fields.
 4. **Output**: Save to `data/raw/synthetic_ebsd.parquet`. (FR-001).
- [ ] T014 [US1] Implement `code/data/preprocess.py` to filter confidence index < 0.1 [UNRESOLVED-CLAIM: c_98b937e2 — status=not_enough_info] and re-index orientations to FCC symmetry using `orix`. **Logic**:
 1. Read reduction levels from the resolved list (as determined in T012).
 2. If specific levels are `[deferred]` (from research.md), proceed with available levels and log a warning.
 3. If ALL levels are `[deferred]`, the script will have already failed in T012; this task assumes valid input exists. (FR-002).
 4. Integrate exclusion logic: flag samples where >50% of points are filtered as "low reliability" and EXCLUDE them from the final training set (Edge Case). (FR-001).
 5. **Symmetry Enforcement**: This is the sole mechanism for symmetry enforcement; no custom loss functions are used.
- [ ] T015 [US1] Generate consolidated Parquet output to `data/processed/cleaned_ebsd.parquet` with metadata (material, reduction, confidence). **Logic**:
 1. **Dependency**: This task depends on T012 (Download) and T014 (Preprocess). (T013 was merged into T012/T014).
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
 2. **Search Window**: Implement a configurable search window of ±5 degrees around the central values to account for lattice rotation spread. Do NOT hardcode fixed "approximate" ranges without a configurable window.
 3. **Euler Ranges (phi1, Phi, phi2 in degrees)**:
 - **Brass**: [35, 45, 55, 65] (Approximate: phi1=35-45, Phi=55-65, phi2=0-90)
 - **Copper**: [39, 39, 0, 0] (Approximate: phi1=39, Phi=39, phi2=0)
 - **S**: [59, 37, 63, 63] (Approximate: phi1=59, Phi=37, phi2=63)
 - **Goss**: [0, 45, 90, 0] (Approximate: phi1=0, Phi=45, phi2=90)
 4. **Symmetry**: Re-index orientations to FCC symmetry using `orix` before calculation (FR-002).
 5. **Output**: Calculate and return scalar values for each component. (FR-003).
- [ ] T019 [US2] Implement mass balance check: explicitly verify that the sum of major components (Brass, Copper, S, Goss) plus the "random" fraction equals 1.0 ± 0.01 for every sample. **Requirement**: This task is mandatory to verify spec.md US-2 Scenario 2 acceptance criteria. If the check fails, log an error and exclude the sample.
- [ ] T020a [US2] Output descriptors to `data/processed/descriptors.csv` linked to original sample IDs. **Dependency**: This task depends on T019 to ensure only valid samples are written.
- [ ] T020b [US2] Implement system-level mass balance verification on `data/processed/descriptors.csv`. **Logic**: After generating the CSV, aggregate the data and verify that the sum of Brass, Copper, S, Goss, and random components equals 1.0 ± 0.01 for the aggregated dataset [UNRESOLVED-CLAIM: c_59aa676e — status=not_enough_info]. **Requirement**: This task is mandatory to verify spec.md US-2 Scenario 2 acceptance criteria at the system level, distinct from T009a (schema test).
- [ ] T021 [US2] Add validation to flag samples where texture evolution deviates from standard FCC trends (Edge Case). **Logic**: If a metal's texture evolution does not follow standard FCC trends (e.g., anomalous behavior), flag these outliers during validation rather than forcing a fit. **Requirement**: This task is mandatory to verify spec.md Edge Cases acceptance criteria.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Validation (Priority: P3)

**Goal**: Train predictive models (Polynomial Regression, Gaussian Process) to estimate texture descriptors based on cold-rolling reduction with high accuracy (R² ≥ 0.85).

**Independent Test**: The model training and validation pipeline can be tested by splitting the dataset and verifying that the R² on the held-out test set meets a satisfactory performance threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US3] Contract test for model output schema in `tests/contract/test_model_output.py`
- [ ] T023 [P] [US3] Integration test for k-fold CV pipeline in `tests/integration/test_model_training.py`

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/models/train.py` to fit separate polynomial (degree=2) and joint Gaussian Process (RBF kernel) models. **Mandatory**:
 1. **Hyperparameters**: Use GP length_scale search space [lower bound, upper bound]; Polynomial regularization (alpha) in a range spanning from $10^{-4}$ to $10^{-2}$..
 2. **Feature Engineering**: Include 'Material Type' as a categorical feature (one-hot encoded) in the joint model to satisfy FR-008.
 3. **Output**: Return fitted models and training metrics. (FR-004, FR-008).
- [ ] T025 [US3] Implement k-fold cross-validation in `code/models/validate.py` to output RMSE and R² metrics (FR-005)
- [ ] T026 [US3] Implement extrapolation flagging: explicitly check if predictions are made outside the fixed "0-80% reduction range". **Logic**: Calculate the fixed physical domain as [, 80]. If a prediction is made outside `[0, 80]`, flag it as "extrapolated" and apply a confidence penalty factor to the standard error. **Requirement**: This task is mandatory to verify spec.md FR-009 acceptance criteria. Do NOT use dynamic training data bounds.
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
 - Filter data points where `|reduction_query - reduction_train| > t` (simulating the gap).
 - Train/evaluate the model on the remaining data.
 - Record the R² value.
 3. **Stability Check**: Verify that the variation in R² across the swept tolerances is ≤ 0.02.
 4. **Output**: Generate `data/processed/sensitivity_analysis.csv` containing the R² values for each tolerance. (FR-007).
- [ ] T031 [US4] Verify R² variation remains ≤ 0.02 across the swept tolerances {0.01, 0.05, 0.1} using T030 output (US-4 Scenario 2). **Requirement**: This task is mandatory to verify spec.md SC-004 acceptance criteria.
- [ ] T032 [US4] Implement variance decomposition (Shapley values or Hierarchical Modeling) to quantify residual variance from missing microstructural variables (FR-008)
- [ ] T033 [US4] Report the percentage of variance attributable to missing variables (e.g., grain size, SFE) in final metrics (US-4 Scenario 3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Validation & Physical Consistency (Revision Response)

**Purpose**: Address reviewer concern (Rosalind Franklin) regarding crystallographic mechanisms vs. statistical correlation.

**Goal**: Explicitly validate that the ML predictions align with physical diffraction evidence (pole figures) and lattice symmetry constraints, preventing the model from learning spurious correlations.

### Implementation for Physical Validation

- [ ] T034 [US3] Implement `code/analysis/trend_consistency_check.py` to validate predicted texture trends against known physics. **Logic**:
 1. **Input**: Use the `data/processed/descriptors.csv` (predicted) and `data/processed/cleaned_ebsd.parquet` (ground truth).
 2. **Trend Validation**: Verify that predicted trends (e.g., Brass increasing with reduction) align with known physics for each metal.
 3. **Mass Balance Check**: Verify that the sum of predicted volume fractions (Brass + Copper + S + Goss + Random) equals 1.0 ± 0.01 for each prediction, ensuring physical plausibility without requiring full ODF reconstruction.
 4. **Threshold**: Flag the model as "Physically Invalid" if trends deviate significantly from known physics or if mass balance is violated. (Reviewer Concern: "Distinguish between physical structure and statistical correlation").
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

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] Documentation updates in `docs/` including model limitations, associational framing, the sensitivity analysis methodology, the physics validation results, and the pole figure validation findings.
- [ ] T046 Code cleanup and refactoring for CPU efficiency (ensure no GPU calls)
- [ ] T047 [P] Additional unit tests for edge cases (missing data, extrapolation, symmetry errors, pole figure reconstruction failures) in `tests/unit/`
- [ ] T048 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T049 Verify all artifacts (data, models, metrics, pole figures) are derived via script (Constitution Principle IV)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validation (Phase 7)**: Depends on US3 (Modeling) completion - BLOCKS final report generation
- **Polish (Final Phase)**: Depends on all desired user stories and validation being complete

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
- **Critical Review Update**: Phase 7 (T034-T037) updated to replace infeasible ODF reconstruction with feasible trend consistency and mass balance checks, and to document missing microstructural variables as unobserved confounders.
- **Critical Review Update**: T012 logic corrected to invoke T012b (synthetic generator) if real data fails, resolving the contradiction with the spec's assumption of synthetic data availability.
- **Critical Review Update**: T030 updated to explicitly describe the dynamic sweep loop for R² stability verification over `{0.01, 0.05, 0.1}`.
- **Critical Review Update**: T018 updated to reference Rosenstock et al. (2018) and implement configurable search window.
- **Critical Review Update**: T026 updated to use fixed [0, 80] range for extrapolation threshold [UNRESOLVED-CLAIM: c_132b7b2f — status=not_enough_info].
- **Critical Review Update**: T020 split into T020a (output) and T020b (system-level mass balance verification).
- **Critical Review Update**: Task statuses corrected (T001-T005, T048-T049) to reflect actual artifact existence.
- **Critical Review Update**: Removed Phase 8 to resolve confusion about removed tasks.
- **Critical Review Update**: T013 merged into T012/T014; T015 dependencies updated.
- **Critical Review Update**: T009 split into T009a (schema) and T009b (aggregation).
- **Critical Review Update**: T036 updated to document missing data rather than extract it.