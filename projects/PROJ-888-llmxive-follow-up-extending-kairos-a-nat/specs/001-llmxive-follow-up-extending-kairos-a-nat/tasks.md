# Tasks: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

**Input**: Design documents from `/specs/001-llmxive-kairos-discrete-scaling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project structure per `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project directory structure: `projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/`, `code/`, `tests/`, `data/`, `state/`, `docs/`
- [ ] T001b [P] Initialize `requirements.txt` with pinned versions: torch (CPU), numpy, pandas, datasets, scikit-learn, pyyaml, pytest, h5py, arviz
- [ ] T001c [P] Create `README.md` with project overview and quickstart instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config.py` for seeds, paths, quantization levels (4/8/16-bit), and noise std devs
- [ ] T005 [P] Implement resource monitoring utilities in `code/utils/monitor.py` (RAM, CPU, time tracking)
- [ ] T006 [P] Setup error handling and logging infrastructure in `code/utils/logging.py`
- [ ] T007 Create base data schemas and validation logic in `code/data/schema.py` (DiscreteStateVector, ErrorMetric)
- [ ] T008 Configure checkpointing mechanism for graceful exit at 6h limit in `code/utils/checkpoint.py`
- [ ] T018 [US2] Download, verify checksum, and cache pre-trained Kairos weights from verified HuggingFace repo to `data/models/kairos_base.pt`. **Fallback Strategy**: If fetch fails (network error or missing file), initialize a random-weight adapter and train from scratch for a minimal number of epochs to ensure reproducibility and prevent pipeline blockage (satisfying Reproducibility Principle). Log the fallback trigger explicitly.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Construction and Quantization Pipeline (Priority: P1) 🎯 MVP

**Goal**: Convert continuous LIBERO dataset into discrete, JSON-serialized state vectors with configurable quantization and noise injection.

**Independent Test**: The pipeline can be tested by running the conversion script on a subset of LIBERO data, verifying that the output JSON files contain discrete integer values within the specified bit-depth ranges, and confirming that the total dataset size fits within the available RAM constraint.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for quantized JSON schema in `tests/contract/test_quantized_schema.py`
- [ ] T010 [P] [US1] Integration test for full download-quantize-noise pipeline in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/data/download_libero.py` to fetch HDF5 from verified HuggingFace URL (NO synthetic fallback)
- [ ] T012 [US1] Implement `code/data/quantize.py` to convert HDF5 to discrete JSON vectors (4/8/16-bit) with bin clamping
- [ ] T013 [US1] Implement `code/data/noise.py` to inject Gaussian noise (0.1-0.5 std dev) and clamp to valid discrete bins
- [ ] T014 [US1] Implement `code/main.py` orchestration logic to coordinate download → quantize → noise pipeline with memory monitoring
- [ ] T040 [US1] Implement execution runner for `code/main.py`: MUST include a distinct step to calculate full dataset size via header-only read to validate total size < 7GB RAM constraint, THEN run pipeline on a sample subset with logging
- [ ] T015 [US1] Add validation logic to detect degenerate cases (e.g., 1-bit collapse) and flag as "Invalid Data"
- [ ] T016 [US1] Add logging for quantization levels, noise seeds, and peak RAM usage per task

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Only Model Training and Inference (Priority: P2)

**Goal**: Load pre-trained Kairos weights, replace visual encoder with fixed discrete projection, and execute training/inference on CPU-only environment.

**Independent Test**: The model can be tested by initiating a training run with a fixed random seed, verifying that the loss trend shows convergence, confirming that the total training time is a target ≤ 4 hours (graceful exit if > 6h), and confirming that inference on a long sequence completes without CUDA errors or out-of-memory exceptions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [ ] T041 [P] [US2] Integration test for CPU-only training loop in `tests/integration/test_cpu_training.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/models/kairos_adapter.py` to load pre-trained weights from `data/models/kairos_base.pt` (T018) or initialize random weights if fallback triggered, and replace visual encoder with fixed discrete projection
- [ ] T020 [US2] Implement `code/models/training_loop.py` for CPU-only training with epoch checkpointing and 6h graceful exit
- [ ] T021 [US2] Implement inference engine in `code/models/inference.py` for **100, 250, and 500-step** horizon prediction (per FR-004 and SC-001)
- [ ] T022 [US2] Integrate `code/utils/monitor.py` to enforce < 7GB RAM and log latency per step
- [ ] T023 [US2] Add logic to detect and prevent CUDA/bitsandbytes errors (fail loudly if detected)
- [ ] T024 [US2] Add logging for training convergence (epoch loss change < 5%) and inference latency

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Stability Analysis and Threshold Mapping (Priority: P3)

**Goal**: Compute MSE, cumulative error growth, and perform statistical validation to identify minimum information density thresholds.

**Independent Test**: The analysis can be tested by running the evaluation script on the model outputs, generating the error-vs-bandwidth curve, and verifying that the statistical tests (t-test/Wilcoxon) produce valid p-values and confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for error metric schema in `tests/contract/test_error_metrics.py`
- [ ] T026 [P] [US3] Integration test for statistical analysis pipeline in `tests/integration/test_stability_analysis.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/analysis/run_baseline.py` to generate continuous visual-modality baseline run and save metrics to `data/results/baseline_metrics.json`
- [ ] T027 [US3] Implement `code/analysis/metrics.py` to calculate MSE normalized by state space dimensionality and cumulative error growth over **100, 250, and 500 steps** (per FR-004 and SC-001)
- [ ] T028 [US3] Implement `code/analysis/stats.py` to perform **paired t-test or Wilcoxon signed-rank test** as the **PRIMARY** statistical validation method (per FR-005 and Constitution Principle VII). Bayesian Hierarchical Modeling (BHM) is permitted only as an optional secondary analysis for N=10 runs, not as a replacement for the required frequentist tests.
- [ ] T029 [US3] Implement sensitivity analysis sweep across **4-bit increments (4, 8, 12, 16)** and report variation in headline error rates (per SC-005)
- [ ] T030 [US3] Implement visualization to generate error-vs-bandwidth curve plot
- [ ] T041 [US3] Implement visualization to generate threshold map visualization
- [ ] T031 [US3] Add logic to explicitly frame stability claims as "relative degradation" against continuous baseline
- [ ] T032 [US3] Add logging for p-values, confidence intervals, and stability boundary identification

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `README.md` and `docs/`
- [ ] T034a [P] Run linting and formatting (ruff/black) on all code
- [ ] T034b [P] Refactor code to remove duplication and improve readability
- [ ] T034c [P] Update documentation based on final implementation
- [ ] T035a [P] Optimize data loading using streaming/chunking to reduce RAM peak
- [ ] T035b [P] Optimize batch sizes to balance throughput and memory usage
- [ ] T035c [P] Profile memory usage and document optimization results
- [ ] T036 [P] Additional unit tests in `tests/unit/`
- [ ] T037 Security hardening (dependency audit)
- [ ] T038 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (DiscreteStateVector)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output (predictions)

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
Task: "Contract test for quantized JSON schema in tests/contract/test_quantized_schema.py"
Task: "Integration test for full download-quantize-noise pipeline in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download_libero.py"
Task: "Implement code/data/quantize.py"
Task: "Implement code/data/noise.py"
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
- **Data Hygiene**: All data loaders MUST fail loudly if real data fetch fails; NO synthetic fallbacks.
- **Resource Constraints**: All training/inference tasks MUST enforce 7GB RAM and 6h time limits via checkpointing.
- **CPU-Only**: All model tasks MUST run on CPU without CUDA/bitsandbytes dependencies.
- **Constitution VII**: Error metrics MUST be normalized by state space dimensionality and calculated over **100, 250, and 500 steps**.
- **FR-005**: Statistical validation MUST use **paired t-test or Wilcoxon signed-rank test** as the primary method.
- **FR-008**: Stability claims MUST be framed as relative degradation against a continuous baseline.
- **SC-005**: Sensitivity analysis MUST sweep quantization in **4-bit increments (4, 8, 12, 16)**.