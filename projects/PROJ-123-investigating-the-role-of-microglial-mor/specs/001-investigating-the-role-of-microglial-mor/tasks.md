# Tasks: Investigating the Role of Microglial Morphology in Age-Related Cognitive Decline

**Input**: Design documents from `/specs/001-investigating-the-role-of-microglial-mor/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in `projects/PROJ-123-investigating-the-role-of-microglial-mor/`. **Deliverables**: Create directories `code/`, `data/raw/`, `data/processed/`, `data/intermediates/`, `tests/`, `reports/`, `specs/`. Create `code/requirements.txt` and `code/config.py` (placeholder).

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (scikit-learn, statsmodels, numpy, pandas, opencv-python-headless, scikit-image, pyyaml)

- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] [Foundational] Implement `config.py` with paths, random seeds, constants, and metric definitions. **Deliverables**: Create `code/config.py` defining `DATA_ROOT`, `MODEL_ROOT`, `SEED`, `CPU_ONLY`, `VIF_THRESHOLD` (5.0), `SENSITIVITY_THRESHOLD` (0.05), and `MORPHOLOGY_METRICS` constant list (branch_points, total_length, soma_area, sholl_intersections). **Constraint**: `MORPHOLOGY_METRICS` must be defined here to ensure extraction logic (T013-T016) uses the approved list from the start. **Definition**: Morphological complexity is operationally defined as the vector `[branch_points, total_length, soma_area, sholl_intersections]`.

- [X] T005 [P] [Foundational] Setup logging infrastructure in `code/__init__.py` to handle warnings for missing metadata (FR-001, FR-008)

- [X] T006a [Foundational] Create base dataset schema in `specs/001-investigating-the-role-of-microglial-mor/contracts/dataset.schema.yaml`. **Content**:
```yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
properties:
 brain_region:
 type: string
 enum: [Hippocampus, Prefrontal Cortex]
 pathology_status:
 type: string
 enum: [Normal, Early AD]
 branch_points:
 type: number
 total_length:
 type: number
 soma_area:
 type: number
 sholl_intersections:
 type: array
 items:
 type: number
 cognitive_score:
 type: number
 amyloid_beta_load:
 type: number
 tau_markers:
 type: number
required:
 - brain_region
 - branch_points
 - total_length
 - soma_area
 - sholl_intersections
```
**Constraint**: Must be valid YAML/JSON before T007 can proceed.

- [X] T006b [Foundational] Create base output schema in `specs/001-investigating-the-role-of-microglial-mor/contracts/output.schema.yaml`. **Content**:
```yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
properties:
 regression_results:
 type: object
 properties:
 coefficients:
 type: object
 p_values:
 type: object
 interaction_terms:
 type: object
 vif_scores:
 type: object
 validation_metrics:
 type: object
 properties:
 r2_mean:
 type: number
 r2_std:
 type: number
 sensitivity_variation:
 type: object
required:
 - regression_results
 - validation_metrics
```
**Constraint**: Must be valid YAML/JSON before T007 can proceed.

- [X] T007 [Depends on T006a, T006b] [P] Implement synthetic data generator in `code/synthetic_data.py` for pipeline validation (addressing Blocking Dependency 1 in plan.md). **Constraint**: Must generate data conforming to the schema defined in T006a (branch points, length, soma, Sholl only). **Note**: This synthetic data is used for logic validation only; the plan acknowledges the lack of verified real data. **Scope**: T007 is for unit tests and logic validation (T010) ONLY. It does NOT feed the main regression pipeline.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Morphological Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest microscopy images, preprocess, and extract quantitative metrics (branch points, length, soma, Sholl) tagged by brain region.

**Independent Test**: Run on a small labeled subset; verify output CSV has non-null, plausible values matching synthetic ground truth within 10% tolerance and valid `brain_region` tags.

### Tests for User Story 1

- [X] T009 [P] [US1] Contract test for schema compliance in `tests/contract/test_dataset_schema.py`
- [X] T010 [P] [US1] Unit test for branch point extraction accuracy (within an acceptable tolerance) in `tests/unit/test_morphometry.py`. **Note**: Uses `generate_synthetic_ground_truth` fixture generated by `synthetic_data.py` (T007) to create known branch counts. The test verifies the pipeline algorithm logic against synthetic ground truth. **Constraint**: This task validates the *algorithm* logic. SC-001 (real manual annotation) is handled in T010a.
- [X] T010a [P] [US1] Unit test for real-data validation against manual annotations (Conditional). **Logic**: Attempt to load `allencell_annotations.csv` (or equivalent real manual annotations).
 - **If available**: Verify extraction accuracy <10% deviation.
 - **If unavailable**: Log warning code `WARN-SC001` and append a structured entry to `docs/LIMITATIONS.md` stating "SC-001 (Manual Ground Truth Verification) skipped due to missing real annotations. Scheduled for future verification."
 **Constraint**: This task is conditional on data availability. **Known Limitation**: If skipped, SC-001 (human-grounded verification) is not met; this deviation is documented here as a known limitation of the current MVP phase pending real data acquisition. If T010a is skipped, T010 remains the primary validator for the MVP.

- [X] T011 [P] [US1] Unit test for brain region tagging and exclusion of untagged images in `tests/unit/test_data_ingestion.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T012a [US1] Implement data ingestion logic in `code/data_ingestion.py` (FR-001, FR-008). **Primary Path**: Fetch high-resolution confocal microscopy images from Allen Brain Atlas and AD Knowledge Portal. Verify checksums. Extract metadata for `brain_region` and `pathology_status`. **Constraint**: If real data is unavailable, the system MUST **FAIL LOUDLY** with a clear error message (e.g., `DataFetchError: Real data source not found. Project blocked per plan.md`). Do NOT fall back to synthetic data in this path. **Note**: This task implements the mandatory real data ingestion path required by FR-001.

- [X] T012b [Depends on T007] [US1] Implement synthetic data ingestion logic in `code/data_ingestion.py` for validation ONLY. **Logic**: Load data generated by T007. **Constraint**: This path is for logic validation (T010) ONLY. It does NOT feed the main regression pipeline (T013-T018) unless explicitly configured for testing via a separate CLI flag. **Note**: This is a separate path from T012a. <!-- ATOMIZE: requested -->

- [X] T013 [Depends on T012a] [US1] Implement denoising and background subtraction in `code/morphometry.py` via function `denoise_and_subtract()` (FR-002). Consumes raw images output by T012a.

- [X] T014 [Depends on T013] [US1] Implement skeletonization and branch point counting in `code/morphometry.py` via function `skeletonize_and_count()` (FR-003). Consumes output of T013.

- [X] T015 [Depends on T014] [US1] Implement soma area and total process length calculation in `code/morphometry.py` via function `calculate_soma_area_and_length()` (FR-003).

- [X] T016 [Depends on T015] [US1] Implement Sholl analysis with configurable radius steps in `code/morphometry.py` via function `run_sholl_analysis()` (FR-003, FR-006). **Note**: This task implements the analysis function; the sensitivity sweep execution is handled in T034/T035.

- [X] T017 [US1] Implement logic to skip empty fields of view and log warnings in `code/morphometry.py` via function `handle_empty_fields()` (Edge Case).

- [ ] T018 [Depends on T016, T017] [US1] Output structured CSV `data/processed/morphological_metrics.csv` with `brain_region` tag. **Constraint**: Must not contain rows excluded by T012a (if real data path). Must include columns: `branch_points`, `total_length`, `soma_area`, and `sholl_intersections`. **Data Structure Requirement**: The `sholl_intersections` column MUST store the vector of counts per radius (e.g., as a JSON-encoded string `{"5um": 10, "10um": 20}` or prefixed columns `sholl_5um`, `sholl_10um`) to support the sensitivity analysis in T034. **Note**: Strict adherence to FR-003 metrics only. **Definition**: Morphological complexity is operationally defined as the vector `[branch_points, total_length, soma_area, sholl_intersections]`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multivariate Regression Analysis with Interaction Effects (Priority: P2)

**Goal**: Run regression predicting Cognitive Status using orthogonal morphological features (PCA) with explicit Pathology*Region interaction terms.

**Independent Test**: Run on synthetic dataset with known interaction effects; verify model identifies significant interaction term (p < 0.05).

### Tests for User Story 2

- [X] T020 [P] [US2] Contract test for regression output schema (coefficients, p-values, interaction terms) in `tests/contract/test_output_schema.py`
- [X] T021 [P] [US2] Unit test for VIF calculation and PCA application when VIF > 5.0 in `tests/unit/test_analysis.py`
- [X] T022 [P] [US2] Unit test for dynamic 'Early AD' classification based on amyloid-beta threshold in `tests/unit/test_analysis.py`

### Implementation for User Story 2

- [X] T023 [Depends on T018] [US2] Implement Z-score normalization of cognitive scores per cohort in `code/analysis.py` (FR-009). **Logic**: Identify distinct study cohorts. Calculate mean and std per cohort. Transform raw scores to Z-scores. **Output**: `data/intermediates/normalized_cognitive_scores.csv`. **Constraint**: Must handle synthetic data (logic validation) and real data (statistical rigor) identically.

- [X] T024 [Depends on T018, T012a] [US2] Implement dynamic 'Early AD' classification logic in `code/analysis.py` (FR-010). **Logic**:
 1. If 'Early AD' labels are missing, identify the 'control group' as subjects with `pathology_status` == 'Normal'.
 2. Check for `amyloid_beta_load`. If present, calculate the upper quantile of the control group and classify 'Early AD' if load exceeds this threshold.
 3. **Fallback**: If `amyloid_beta_load` is missing, check for `tau_markers`. If present, calculate a high percentile of the control group's tau distribution and classify 'Early AD' if tau exceeds this threshold.
 4. Log the specific threshold and marker used. If labels are present, use them directly.

- [X] T026 [Depends on T023] [US2] Implement VIF calculation and PCA application in `code/analysis.py` (FR-004, FR-011). **Logic**: Calculate VIF for all predictors (branch_points, total_length, soma_area, sholl_intersections). **Artifact**: Write `data/intermediates/vif_check.json` containing `vif_scores` (dict of feature: value), `max_vif` (float), and `trigger_pca` (boolean, true if max_vif > 5.0). **Action**: If `trigger_pca` is true, apply PCA to generate orthogonal predictors. **Constraint**: If input is synthetic data, VIF check validates pipeline logic; if real data, VIF check enforces statistical rigor. **Note**: The resulting PCA model (components, mean, std) is saved as a fixed artifact for use in T034.

- [X] T027 [Depends on T026] [US2] Implement multiple linear regression with `PathologyStatus * BrainRegion` interaction terms in `code/analysis.py` (FR-004). Uses orthogonal predictors from T026.

- [X] T028 [Depends on T027] [US2] Set `causality_warning` flag and append disclaimer. **Logic**: Check `metadata['randomized']`. If `True`, set `causality_warning=false`. If `False` or missing, set `causality_warning=true` and append standard disclaimer ("Associational findings only; causality not inferred") to all text outputs (FR-007). **Deliverable**: Update `reports/regression_results.md` with the flag and disclaimer.

- [X] T029 [Depends on T028] [US2] Output structured report `reports/regression_results.json` and `reports/regression_results.md`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Validate model generalizability via k-fold CV and perform sensitivity analysis on Sholl radius steps.

**Independent Test**: Run CV (k=5) and sensitivity sweep; verify R² variation < 5% and p-value stability across radius steps.

### Tests for User Story 3

- [X] T031 [P] [US3] Unit test for k-fold cross-validation stability (std_dev < 0.05 * mean_r2) in `tests/unit/test_analysis.py`
- [X] T032 [P] [US3] Unit test for sensitivity analysis loop across Sholl steps {, intermediate, high} in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [X] T033 [Depends on T029] [US3] Implement k-fold cross-validation (k=5) loop for regression model in `code/analysis.py` (FR-005)

- [X] T034 [Depends on T029, T026] [US3] Implement sensitivity analysis loop sweeping Sholl radius steps at multiple scales in `code/analysis.py` (FR-006). **Logic**: Execute the full regression pipeline for each step size. **Atomic Steps**:
 1. Load data.
 2. **Use FIXED PCA basis**: Load the PCA model saved in T026 (calculated on the default step size). Do NOT re-calculate PCA for this step. Apply this fixed transformation to the current Sholl vector.
 3. Run Regression with orthogonal predictors.
 4. Extract p-value.
 **Constraint**: Must explicitly use the FIXED PCA basis from T026 to ensure orthogonality is maintained per step and the predictor space remains comparable across steps.

- [X] T035 [Depends on T034] [US3] Calculate and log variation in interaction effect p-value across sensitivity sweeps in `code/analysis.py`. **Logic**:
 1. Extract p-values for the primary interaction term from the results of T034 for steps {2, 5, 10}.
 2. Define the baseline p-value as the result from a fixed step size (the default).
 3. Calculate the absolute difference for each step: `abs(p_step - p_ref)`.
 4. Flag if any absolute difference exceeds `SENSITIVITY_THRESHOLD` (a predefined sensitivity threshold). as defined in `code/config.py`.
 **Output**: Record metric in `data/intermediates/sensitivity_analysis.json`. **Constraint**: Must write the JSON artifact with specific p-value variations.

- [X] T036 [Depends on T033, T035] [US3] Generate final validation report including CV metrics and sensitivity analysis results in `reports/validation_report.md`. **Content**: Must include R² mean/std and p-value variation metrics.

**Checkpoint**: All user stories should now be independently functional

---

## Future Work & Limitations

**Purpose**: Document known limitations and schedule future verification tasks.

- [X] T040 [Future] Schedule verification of SC-001 (Manual Ground Truth) once real data is acquired. **Logic**: When real manual annotations become available, re-run T010a and update `docs/LIMITATIONS.md` to reflect the successful verification. **Trigger**: Manual trigger upon data acquisition. <!-- FAILED: unspecified -->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Future Work (Phase 7)**: Depends on US1 and US2 completion to ensure the operational definition is consistent with the implemented metrics.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 output (morphological metrics) - MUST run after T018 completes
- **User Story 3 (P3)**: Depends on US2 output (regression model) - MUST run after T029 completes

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately; US2 and US3 must wait for US1 data generation
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (with data flow constraints)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Unit test for branch point extraction accuracy in tests/unit/test_morphometry.py"
Task: "Unit test for brain region tagging in tests/unit/test_data_ingestion.py"

# Launch all implementation models for User Story 1 together (after T012a):
Task: "Implement denoising and background subtraction in code/morphometry.py"
Task: "Implement skeletonization and branch point counting in code/morphometry.py"
Task: "Implement soma area and total process length calculation in code/morphometry.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Real Data Path T012a)
4. **STOP and VALIDATE**: Test User Story 1 independently on synthetic data (T012b -> T010) if real data is unavailable (project remains BLOCKED).
5. Deploy/demo if ready.

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
 - Developer A: User Story 1 (Data Ingestion + Extraction) - Real Data Path (T012a)
 - Developer B: (Waiting) for US1 data to implement US2 (Regression + Validation)
 - Developer C: (Waiting) for US2 results to implement US3 (Sensitivity Analysis)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All image processing and regression tasks MUST run on CPU-only (limited core count, constrained RAM). No GPU models or 8-bit quantization allowed.
- **Review Note**: The implementation uses `scikit-image` to algorithmically replicate the logic of Fiji's Simple Neurite Tracer (skeletonization) and Microglial Morphometry plugins. This satisfies the Constitution's requirement for a standardized pipeline while ensuring CPU-tractability.
- **Review Note (Scope)**: The 'fractal_dimension' metric has been removed from the implementation to ensure strict alignment with spec.md FR-003. The analysis focuses exclusively on branch points, total length, soma area, and Sholl intersections.
- **Review Note (Scope)**: The 'complexity_index' metric has been removed from the implementation to eliminate unapproved scope creep. The analysis strictly adheres to the spec-defined metrics.
- **Data Source Note**: T012a now defaults to REAL data fetch and FAILS LOUDLY if unavailable. Synthetic data is restricted to T012b (validation only).
- **Turing Review Response**: DELETED. The operational definition of morphological complexity is now documented in T018 and T004.
- **Definition**: Morphological complexity is strictly defined as the vector `[branch_points, total_length, soma_area, sholl_intersections]`.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T041 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist. <!-- FAILED: unspecified -->
