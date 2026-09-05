---
description: "Task list for feature implementation"
---

# Tasks: Predicting Material Stiffness from Microstructure Images Using Convolutional Neural Networks

**Input**: Design documents from `/specs/001-predict-stiffness-cnn/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification. [UNRESOLVED-CLAIM: c_ce5105d8 — status=not_enough_info]

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

## Phase 0: Governance & Constitution Verification (Prerequisite)

**Purpose**: Verify that ratified artifacts (Constitution, Spec, Plan) already contain the required text to enable execution.
**⚠️ CRITICAL**: No data generation or training can begin until this phase is complete.
**⚠️ STATUS**: **READY** - Verification tasks are ready to execute immediately.
**Note**: State updates are handled automatically by the Advancement-Evaluator Agent upon task completion; no manual intervention is required.

### Task Status: VERIFICATION (READY)

- [ ] T002v [P] **VERIFY**: **Verify Constitution Principle VI**: Manually inspect `constitution.md` Principle VI to confirm it explicitly states: "The system shall use FFT-based numerical homogenization. The validity range of the analytical bounds used is documented for the specific microstructure topology. " **Action**: If text exists, mark [X] and proceed. If missing, halt and report.
- [ ] T004v [P] **VERIFY**: **Verify Spec Resolution**: Manually inspect `spec.md` FR-001 to confirm it explicitly states "128x128 pixels" and references "US-1 Acceptance Scenario 1". **Action**: If text exists, mark [X] and proceed.
- [ ] T005v [P] **VERIFY**: **Verify Spec/Plan Alignment**: Manually inspect `spec.md` FR-007 and `plan.md` Methodology to confirm they explicitly state "One-way ANOVA and Tukey HSD ". **Action**: If text exists, mark [X] and proceed.

**Gate Status**: **OPEN**. Proceed to Phase 1 immediately after T002v, T004v, T005v are marked [X].

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T007s [P] **READY**: **Install System Dependencies**: Execute: `sudo apt-get update && sudo apt-get install -y libfftw3-dev`. Verify installation with `fftw3-config --version`. **Action**: Required for `pyfftw` compilation on fresh runners. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T006a [P] Create project directories. Execute: `mkdir -p code/{data_generation,training,evaluation,utils} data/{raw,processed} tests/{unit,contract,integration} specs/001-predict-stiffness-cnn/contracts`. Verify the directory tree exists using `tree code data tests specs` and assert exit code 0.
- [X] T006b [P] Create `__init__.py` files. Execute: `touch code/__init__.py code/data_generation/__init__.py code/training/__init__.py code/evaluation/__init__.py code/utils/__init__.py tests/__init__.py tests/unit/__init__.py tests/contract/__init__.py tests/integration/__init__.py`. Verify all files exist.
- [X] T006c [P] Create placeholder files. Execute: `touch code/main.py code/data_generation/generate_microstructures.py code/data_generation/compute_stiffness.py code/training/model.py code/training/train.py code/evaluation/stats_utils.py code/evaluation/evaluate.py docs/constitution_amendment_proposal.md`. Verify all files exist.
- [X] T007 [P] **BLOCKED until T007s is complete**: **Initialize Python + project**. Create `requirements.txt` with the following exact content. **Note**: When installing, use `pip install -r requirements.txt --index-url to ensure the correct CPU-only wheel is selected. **Dependency**: T007s.
 ```text
 torch
 {{claim:c_71840fd9}} (pi, https://en.wikipedia.org/wiki/Pi)
 scipy==1.11.0 [UNRESOLVED-CLAIM: c_fa1ed4d7 — status=not_enough_info]
 numpy==1.24.0 [UNRESOLVED-CLAIM: c_9148a7dd — status=not_enough_info]
 pandas==2.0.0 [UNRESOLVED-CLAIM: c_0fed2f18 — status=not_enough_info]
 {{claim:c_4aed7695}}
 scikit-learn==1.2.0 [UNRESOLVED-CLAIM: c_83d46969 — status=not_enough_info]
 pyfftw==0.13.1 [UNRESOLVED-CLAIM: c_18a1fbb7 — status=not_enough_info]
 ```
- [X] T008 [P] Configure linting and formatting. Create `pyproject.toml` with `ruff` and `black` configuration. Enable rules for `E`, `F`, `W`, `I`, and `N`. Execute `ruff check.` and `black --check.` to verify configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Implement core FFT-based homogenization solver in `code/utils/fft_homogenization.py` (CPU-optimized, no CUDA). Note: Constitution Principle VI has been verified to permit this method (T002v). **Status**: BLOCKED until Phase 0 is complete.
- [X] T010 [P] Implement utility metrics functions (`MAE`, `MSE`, `R2`) in `code/utils/metrics.py`
- [X] T011 Setup k-fold cross-validation utilities in `code/training/kfold_utils.py`
- [ ] T012 [P] **READY**: **Create data schema validation contracts**: Create `specs/001-predict-stiffness-cnn/contracts/dataset.schema.yaml`. **Content**:
 ```yaml
 type: object
 required:
 - image_path
 - stiffness_tensor
 - inclusion_density
 - topology_type
 - shape_factor
 - connectivity
 - seed
 properties:
 image_path:
 type: string
 description: "Path to the 128x128 PNG image"
 stiffness_tensor:
 type: array
 items:
 type: number
 description: "Effective elastic stiffness tensor components"
 inclusion_density:
 type: number
 description: "Volume fraction of inclusions"
 topology_type:
 type: string
 enum: ["random", "aligned", "percolating"]
 description: "Topological classification"
 shape_factor:
 type: number
 description: "Calculated using scikit-image morphology (perimeter^2 / (4 * pi * area))"
 connectivity:
 type: number
 description: "Calculated using scikit-image morphology (Euler number or component count)"
 seed:
 type: integer
 description: "Random seed used for generation"
 ```
 **Action**: Create file with content above. **Dependency**: None. **Note**: Defines calculation logic for shape_factor/connectivity.
- [ ] T013 [P] **READY**: **Create model output schema contracts**: Create `specs/001-predict-stiffness-cnn/contracts/model-output.schema.yaml`. **Content**:
 ```yaml
 type: object
 required:
 - model_version
 - prediction
 - error
 - density_bin
 properties:
 model_version:
 type: string
 description: "Version string of the trained model"
 prediction:
 type: array
 items:
 type: number
 description: "Predicted stiffness tensor"
 error:
 type: number
 description: "Absolute error of the prediction"
 density_bin:
 type: string
 description: "Density bin label (e.g., 'low', 'medium', 'high')"
 ```
 **Action**: Create file with content above. **Dependency**: None.
- [X] T017b [P] **READY**: **Calculate Topological Metrics**: Implement utility functions in `code/utils/topology_metrics.py` to calculate `shape_factor` and `connectivity` for a given microstructure image. **Calculation**: Use `skimage.measure.morphology` to compute perimeter, area, and Euler number. **Purpose**: Record for Data Hygiene (Constitution Principle III) and Generalization Boundary Disclosure (Principle VII), NOT for stratification. **Note**: These metrics are recorded but NOT used for stratification (stratification is strictly by density and topology per FR-005). **Dependency**: None. **Status**: READY (Unblocks T019, T031).
- [ ] T017c [P] **READY**: **Define Topology Type Labels**: Implement logic in `code/data_generation/generate_microstructures.py` to assign `topology_type` labels ("random", "aligned", "percolating") as **input parameters** to the generator, NOT derived from the image. **Action**: Ensure the generator accepts `topology_type` as an argument and records it in `data/raw/metadata.json`. **Purpose**: Provide the stratification key required by FR-005. **Dependency**: None. **Note**: This task produces the `topology_type` label used for stratification, distinct from T017b's metrics.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation and Ground Truth Calculation (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic microstructure images with known ground truth stiffness (US-1) with varying void/inclusion densities and compute their effective elastic stiffness tensors using FFT-based numerical homogenization.

**Independent Test**: The output directory contains at least 2,000 image files. [UNRESOLVED-CLAIM: c_f0dce53d — status=not_enough_info] and a metadata file with stiffness tensors within Voigt-Reuss-Hill bounds.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T014 [P] [US1] Unit test for microstructure generation logic in `tests/unit/test_generation.py`
- [X] T015 [P] [US1] Unit test for FFT homogenization convergence in `tests/unit/test_homogenization.py`
- [X] T016 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (depends on T012)

### Implementation for User Story 1

- [ ] T017 [US1] **BLOCKED until T012 is complete**: **READY**: Implement stratified microstructure generator in `code/data_generation/generate_microstructures.py` (FR-001, uses `scikit-image`, ensures density-topology decoupling). Output: PNG files in `data/raw/` named `micro_{seed}.png` (128x128 pixels, as per verified FR-001 in T004v). **Depends on T012, T017c**. **Note**: Validates output against `dataset.schema.yaml`. **Status**: BLOCKED until Phase 0 and T012 are complete.
- [ ] T018 [US1] **BLOCKED until T012 is complete**: **READY**: Implement stiffness tensor calculator in `code/data_generation/compute_stiffness.py` (FR-002, calls FFT solver, outputs to `data/raw/`). **Depends on T012, T009**. **Note**: Validates output against `dataset.schema.yaml`. **Status**: BLOCKED until Phase 0, T009, and T012 are complete.
- [ ] T019 [US1] **BLOCKED until T012 is complete**: **READY**: Add validation logic to check physical plausibility of generated tensors (Voigt-Reuss-Hill bounds) and schema conformity (depends on T012, T009, T017, T018, T017b). **Trigger Conditions**: Log "Solver Convergence Failure" if `residual > 1e-4` in FFT solver; Log "Unphysical Microstructure" if `stiffness < 0` or `shape_factor` is NaN. **Action**: Flag and exclude. **CRITICAL**: Log the specific reason for exclusion (e.g., "Solver Convergence Failure" or "Unphysical Microstructure") to `data/processed/validation_log.csv`. **Schema**: CSV with columns `entry_id, reason, density, topology`. **Memory Safety**: Implement streaming/chunked processing (batch size calculated to fit within 7GB RAM) and use append-mode CSV writing to avoid loading the entire dataset or log into memory. **Note**: This defines the schema explicitly as required by data hygiene.
- [ ] T020 [US1] **READY**: Create orchestration script `code/main.py` to run generation pipeline end-to-end. CLI args: `--seed`, `--n_samples`. Sequence: generate -> compute -> validate. Exit codes: =success, 1=fail. (depends on T017, T018, T019).
- [ ] T021 [US1] **READY**: Log derivation metadata (seeds, parameters, density values, shape_factor, connectivity) to `data/processed/derivation_log.json` (depends on T020). **Schema**: `{"seeds": [int], "parameters": {"density": float, "topology": str}, "density_values": [float], "topology_types": [str]}`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Optimized CNN Training and Validation (Priority: P2)

**Goal**: Train a shallow Convolutional Neural Network on the generated dataset using PyTorch in CPU-only mode, ensuring completion within 6 hours.

**Independent Test**: Training completes within 6 hours on 2-core CPU. [UNRESOLVED-CLAIM: c_161c7322 — status=not_enough_info], saves model artifact, and reports MSE/R2.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for CNN architecture definition in `tests/unit/test_model.py`
- [ ] T024 [P] [US2] **BLOCKED until T013 is complete**: Contract test for model output schema in `tests/contract/test_output_schema.py` (depends on T013). **Note**: This is a TDD task; write this file first, ensure it fails, then implement T025/T026 to pass.

### Implementation for User Story 2

- [ ] T025 [P] [US2] **READY**: Implement shallow CNN architecture (Several convolutional layers, ReLU, global avg pooling) in `code/training/model.py` (FR-003). **Dependency**: T013.
- [ ] T026 [US2] **READY**: Implement training loop with Adam optimizer, batch size 32, and convergence criteria: "convergence when validation loss plateaus for a sufficient number of epochs OR a predefined maximum number of epochs is reached" in `code/training/train.py` (FR-004). **Correction**: Added explicit convergence criteria to satisfy FR-004.
- [ ] T027 [US2] **READY**: Integrate k-fold cross-validation logic into training script (FR-005)
- [ ] T028 [US2] **READY**: Implement data streaming/batching in `code/training/data_loader.py`. Class `MicrostructureDataLoader` with method `__iter__` yielding batches of a size appropriate to respect the available RAM limit.
- [ ] T029 [US2] **READY**: **Add Checkpointing**: Save model weights to `code/models/` on completion. **Dependency**: T026 (Training Loop). **Status**: READY.
- [ ] T030 [US2] **READY**: Implement evaluation on held-out test set to compute MAE, MSE, R2 (FR-006)
- [ ] T031 [US2] **BLOCKED until T013 is complete**: **READY**: **Stratified K-Fold Implementation**: Implement k-fold cross-validation stratified by `inclusion_density` and `topology_type` (as defined in T012 and T017c) in `code/training/train.py`. (FR-005, depends on T011, T017b, T017c, T029, T012). **Note**: Stratification is strictly by density and topology. Do NOT stratify by shape_factor or connectivity. T017b calculates these metrics for OOD analysis (Principle VII), but they are excluded from stratification logic. **Dependency**: T017c (Topology Label Generation). **Status**: READY once Phase 3 is complete and T013 is complete.
- [ ] T032 [US2] **READY**: **Stability Reporting**: Calculate and report the variance/standard deviation of R-squared values across the folds to satisfy SC-005. Output: Append a table row to `data/processed/analysis_report.md` under section "Stability Analysis" with columns: Fold, R2, Deviation.
- [ ] T033 [US2] **READY**: **Stop & Validate: Model Success Criteria**: Compute and report the Mean Absolute Error (MAE) of the model's predictions against the FFT-based numerical ground truth on a held-out test set to verify the % MAE threshold (SC-001). **Action**: If MAE > threshold, exit with code 1 and halt the pipeline. Output: Append specific numeric value to `data/processed/analysis_report.md`. (Note: This task verifies the MODEL's performance. Depends on T029, T020).

**Dependency Health Check**:
- **T031** depends on **T017b** (Phase 2) and **T017c** (Phase 2) and **T012** (Phase 2).
- **T017b** is part of Phase 2 (Foundational).
- **T017c** is part of Phase 2 (Foundational).
- **Action**: Execute Phase 2 (Foundational) before Phase 4 (US-2).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generalization and Statistical Analysis (Priority: P3)

**Goal**: Evaluate model generalization across inclusion densities and perform statistical tests (One-way ANOVA per amended spec T005v) on prediction errors.

**Independent Test**: Verify report shows error degradation for out-of-distribution densities, statistically significant p-values from ANOVA, and degradation rate metric.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US3] Unit test for statistical analysis functions in `tests/unit/test_stats_utils.py`

### Implementation for User Story 3

- [ ] T035 [P] [US3] **READY**: Implement One-way ANOVA and Tukey HSD functions in `code/evaluation/stats_utils.py` (Plan Methodology Update - primary verification method for FR-007, per verified spec T005v). **Configuration**: Define significance threshold `alpha = 0.05 (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value)` and Null Hypothesis `H0: mean error is equal across all density groups`. **Action**: If p-value < alpha, reject H0 and report "Significant difference detected".
- [ ] T036a [P] **READY**: **Define Physical Density Bounds**: Create `code/utils/constants.py` and define `The physical density range upper bound is 0.9. [UNRESOLVED-CLAIM: c_acbe38d4 — status=not_enough_info] ` as the prior physical boundary. **Purpose**: Establish a robust OOD threshold independent of training set skew.
- [ ] T036 [US3] **READY**: **OOD Threshold Definition & Active Testing**: Calculate the `min_training_density` and `max_training_density` from the training set metadata (from T021). Define the OOD range as densities outside the `PHYSICAL_DENSITY_RANGE` (from T036a) OR outside [min, max] if the training set is known to cover the full range. **Action**: Generate and test specific samples at densities slightly beyond the established boundaries (e.g., min - a small threshold, max + a small threshold) to explicitly test the "specific density ranges" required by the spec. Report the specific density values tested, the model predictions, and the calculated degradation rate for each point. Store threshold and test points in `data/processed/ood_config.json`. **Note**: This satisfies the "specific density ranges tested" requirement.
- [ ] T037 [US3] **READY**: Calculate and report quantitative 'degradation rate' metric for out-of-distribution densities (SC-002). Formula: slope of (MAE vs. density) for densities > `max_training_density` (from T036). Unit: MAE per % density. **Pass/Fail**: Do NOT halt the pipeline based on a hard-coded threshold. Instead, report the slope and check if a threshold is defined in `spec.md` SC-002. If `spec.md` SC-002 defines a threshold, halt if exceeded. If not, log a warning: "SC-002 threshold not defined; degradation rate reported for manual review." Output: Append specific numeric value to `data/processed/analysis_report.md`. **Note**: This task verifies the MODEL's performance. Depends on T029, T020.
- [ ] T037a [P] **READY**: **Update Spec for Degradation Threshold**: If a degradation rate threshold (e.g., 0.5) is deemed necessary for project success, update `spec.md` SC-002 to explicitly include this threshold. **Action**: If T037 reports a slope that is concerning, create a PR to update SC-002. **Note**: This ensures the project does not fail against a non-existent requirement.
- [ ] T038a [US3] **READY**: **OOD Flagging Logic**: Implement logic to flag instances where `inclusion_density > max_training_density` or `inclusion_density < min_training_density` (from T036) (FR-008). **Correction**: Flag based strictly on the input density value exceeding the defined OOD threshold.
- [ ] T039a [US3] **READY**: Generate analysis report section: Error vs Density plot (matplotlib) to `data/processed/analysis_report.md`.
- [ ] T039b [US3] **READY**: Generate analysis report section: Degradation rate table (numeric values from T037) to `data/processed/analysis_report.md`.
- [ ] T039c [US3] **READY**: Generate analysis report section: ANOVA/Tukey HSD table and p-values (from T035) to `data/processed/analysis_report.md`.
- [ ] T040 [US3] **READY**: Add logic to detect and report out-of-distribution density failures

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041a [P] Update `README.md` with CLI usage, installation instructions, and project overview.
- [ ] T041b [P] Generate API docs for `code/utils/` and `code/data_generation/` using `sphinx` or `pdoc`.
- [ ] T041c [P] Update `docs/research.md` with methodology summary and key findings.
- [ ] T042 Code cleanup and refactoring of data loading utilities
- [ ] T043 Performance optimization of FFT solver for CPU cache efficiency
- [ ] T044 [P] Additional unit tests for edge cases (extreme void density, solver convergence) in `tests/unit/`
- [ ] T045 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T046 Verify full pipeline runtime is ≤ 6 hours on simulated free-tier constraints. [UNRESOLVED-CLAIM: c_d507813a — status=not_enough_info].

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Governance)**: No dependencies - can start immediately. **BLOCKS** all subsequent phases.
- **Setup (Phase 1)**: Depends on Phase 0 completion.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model training

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
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for microstructure generation logic in tests/unit/test_generation.py"
Task: "Unit test for FFT homogenization convergence in tests/unit/test_homogenization.py"

# Launch implementation tasks for User Story 1 together:
Task: "Implement stratified microstructure generator in code/data_generation/generate_microstructures.py"
Task: "Implement stiffness tensor calculator in code/data_generation/compute_stiffness.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Governance & Constitution Verification
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1 (including T017b, T017c)
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add Phase 3 (User Story 1) → Test independently → Deploy/Demo (MVP!)
3. Add Phase 4 (User Story 2) → Test independently → Deploy/Demo
4. Add Phase 5 (User Story 3) → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (including T017b, T017c)
 - Developer B: User Story 2 (waiting for T017b completion)
 - Developer C: User Story 3 (waiting for US-2 completion)
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
- **Critical Path**: Phase 0 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 5