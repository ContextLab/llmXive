# Tasks: llmXive Follow-up: Extending MulTaBench

**Input**: Design documents from `/specs/001-llmxive-mulTabench-extension/`
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
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in `code/`, `tests/`, `data/`
- [X] T002 Initialize Python 3.11 project with `pyproject.toml` dependencies (torch-cpu, transformers, sentence-transformers, scikit-learn, pandas, pyarrow, numpy, requests, pyyaml)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for global config, seeds (`random_seed=42`), and paths
- [X] T005 [P] Implement `code/utils/memory_monitor.py` to track peak RAM usage (memory limit)
- [X] T006 [P] Implement `code/utils/logging.py` for structured pipeline logging
- [X] T007 Create `code/data_loader.py` for MulTaBench ingestion with local checksum verification (SHA-256)
- [X] T008 Setup `data/README.md` with instructions for local data ingestion and checksum validation
- [ ] T009a [P] Create `contracts/frozen_embedding.schema.yaml` defining the schema for frozen embeddings
- [ ] T009b [P] Create `contracts/tabular_metadata.schema.yaml` defining the schema for tabular metadata
- [ ] T009c [P] Update `data-model.md` to reference the new contract files and define `run_id` propagation
- [ ] T010 Create `code/models/__init__.py` and base model structures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Tractable Baseline Generation (Priority: P1) 🎯 MVP

**Goal**: Generate frozen embeddings for images and text using CLIP ViT-B/32 and Sentence-BERT on CPU without gradient tracking.

**Independent Test**: Verify script completes within 60 mins on a sample of datasets, outputs valid parquet files, and no CUDA errors occur.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for batch processing logic in `tests/test_embeddings.py::test_batch_processing_memory`
- [X] T012 [P] [US1] Unit test for gradient disabling in `tests/test_embeddings.py::test_no_grad_context`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/embeddings/generator.py` with CLIP ViT-B/32 and Sentence-BERT loaders (CPU-only, default precision)
- [X] T014 [US1] Implement `code/embeddings/utils.py` with batch processing logic to ensure memory safety (max batch size)
- [X] T015 [US1] Implement `code/pipelines/run_baseline.py` to generate embeddings for **ALL available datasets** in the pipeline with `random_seed=42`. Output must include `data/processed/embeddings_{run_id}.parquet` with `run_id`, `dataset_id`, and embedding vectors. Ensure deterministic re-computation for all datasets to satisfy FR-001.
- [~] T016 [US1] Add logic to handle datasets with zero variance or missing image/text fields gracefully (skip or impute constant)
- [~] T017 [US1] Implement output serialization to `data/processed/embeddings_{run_id}.parquet` with `run_id` and metadata
- [~] T018 [US1] Add validation to ensure no gradient tracking is enabled during inference
- [X] T019 [P] [US1] Sensitivity analysis script `code/pipelines/run_baseline_sensitivity.py` to generate embeddings for **ALL available datasets** using additional seeds (total seeds including primary). Note: While generation is parallel, aggregation (T019b) depends on completion.
- [X] T019b [US1] Implement `code/pipelines/merge_sensitivity_outputs.py` to merge the 5-seed Parquet files from T019 into a single intermediate file.
- [X] T019c [US1] Implement `code/pipelines/aggregate_sensitivity.py` to compute mean/std of embeddings and metrics from merged files and write to `data/artifacts/frozen_baseline_aggregated_{run_id}.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Tabular-Conditioned Projection Implementation (Priority: P2)

**Goal**: Implement and train a lightweight projection module (MLP/Attention) using normalized tabular features as queries to modulate frozen embeddings.

**Independent Test**: Verify training loss converges on a single dataset within 10 epochs on CPU and memory usage < 7GB.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for projection layer gradient isolation in `tests/test_projection.py::test_frozen_backbone_gradients`
- [X] T021 [P] [US2] Integration test for training loop convergence in `tests/test_projection.py::test_training_convergence`

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/models/projection.py` with MLP or single-head attention module accepting tabular features as query
- [X] T023 [US2] Implement `code/models/trainer.py` with training loop that freezes backbone weights and trains only projection layer
- [~] T024 [US2] Implement `code/analysis/metadata_stats.py` to compute cardinality, missingness, sparsity, and variance for tabular features for **ALL available datasets**. Output must be a single summary CSV: `data/processed/metadata_stats_summary.csv` with columns [dataset_id, cardinality, missingness, sparsity, variance]. This task must complete before T025.
- [ ] T025 [US2] Implement `code/pipelines/run_conditioned.py` to train the projection layer on **ALL available datasets**, consuming metadata stats from T024.
- [~] T026 [US2] Add logic to handle edge cases (e.g., zero variance features) by skipping or imputing constants
- [~] T027 [US2] Implement evaluation logic to record performance metrics (AUC/RMSE) for held-out test sets
- [~] T028 [US2] Store results in `data/artifacts/metrics_conditioned_{run_id}.json` with `run_id` linkage

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Efficacy Correlation & Statistical Analysis (Priority: P3)

**Goal**: Correlate performance recovery ratio with tabular metadata statistics and perform statistical significance testing.

**Independent Test**: Verify correlation analysis script outputs Pearson coefficients, p-values, and performs t-test/Wilcoxon test correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for correlation calculation in `tests/test_analysis.py::test_correlation_calculation`
- [X] T030 [P] [US3] Unit test for FDR correction implementation in `tests/test_analysis.py::test_benjamini_hochberg`

### Implementation for User Story 3

- [~] T032a [US3] Implement `code/pipelines/validate_baselines.py` to validate the presence of 'GPU-Tuned' baselines for all datasets. Generate `data/artifacts/gpu_tuned_baselines.csv` with explicit schema (dataset_id, task_type, baseline_value) and a 'Data Availability Gap' report listing missing entries.
- [~] T032b [US3] Implement logic to fetch 'GPU-Tuned' baselines from MulTaBench paper data using the validated CSV from T032a. <!-- FAILED: unspecified -->
- [~] T031 [US3] Implement `code/analysis/correlation.py` to calculate "Recovery Ratio" = (CPU-Conditioned - Frozen_Aggregated) / (GPU-Tuned - Frozen_Aggregated) using the aggregated baseline from T019c and the **deterministic re-computed baseline** for consistency. Input: `data/artifacts/gpu_tuned_baselines.csv` from T032a.
- [~] T033 [US3] Perform Pearson correlation between "Recovery Ratio" and metadata features (Cardinality, Missingness, Sparsity, Variance) for **ALL available datasets with complete data**.
- [~] T034 [US3] Implement Benjamini-Hochberg (FDR) correction for multiple comparisons across metadata features AND for the one-sample t-test results. Input: p-values from T033 (correlation) and T035 (t-test). Output: JSON with adjusted p-values.
- [~] T035 [US3] Perform one-sample t-test (or Wilcoxon if normality fails) comparing CPU-Conditioned performance vs. fixed GPU-Tuned baseline for **ALL valid datasets**.
- [~] T036 [US3] Generate `data/artifacts/correlation_report_{run_id}.json` with coefficients, p-values, and significance flags
- [X] T037 [US3] Create `code/pipelines/run_analysis.py` to orchestrate the full statistical analysis pipeline
- [~] T038 [US3] Add "Data Availability Gap" reporting for datasets missing GPU-Tuned baselines to the final report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Update `code/pipelines/update_state.py` to hash artifacts and update `state/projects/...yaml`
- [~] T040 Code cleanup and refactoring for memory efficiency <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 2, column 1:
 **Key Changes in `code/utils/mem...
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 2, column 2:
 **Key Changes in `code/utils/memo...
 ^) -->
- [~] T041 [US1/US2/US3] Performance optimization to ensure total runtime < 6 hours. Implement adaptive batching and dynamic parallelism to process **ALL available datasets** within the time limit. Do NOT use early termination to skip datasets; instead, adjust batch sizes to ensure full coverage.
- [~] T042 [P] Additional unit tests for edge cases (e.g., empty datasets, single-row datasets) in `tests/`
- [~] T043a [P] Generate/Update `quickstart.md` with new pipeline steps (US1, US2, US3) and data ingestion instructions.
- [~] T044 Final integration test of the entire pipeline on a subset of datasets

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Relies on US1 output (embeddings)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on US1 and US2 output (metrics). **CRITICAL: US3 cannot run in parallel with US2 as it consumes US2's artifacts.**

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
Task: "Unit test for batch processing logic in tests/test_embeddings.py::test_batch_processing_memory"
Task: "Unit test for gradient disabling in tests/test_embeddings.py::test_no_grad_context"

# Launch all models for User Story 1 together:
Task: "Implement code/embeddings/generator.py with CLIP ViT-B/32 and Sentence-BERT loaders"
Task: "Implement code/embeddings/utils.py with batch processing logic"
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
- **CRITICAL**: All tasks must run on CPU-only CI (limited cores, constrained RAM, time-constrained execution). No GPU, no 8-bit quantization, no large model fine-tuning.
- **CRITICAL**: Use real data from MulTaBench. Do not fabricate data or use random values for metrics.
- **CRITICAL**: Ensure data flow order: Embedding Generation (US1) → Projection Training (US2) → Correlation Analysis (US3).
- **CRITICAL**: All data generation tasks (T015, T019, T024, T025) must cover **ALL available datasets** to satisfy the correlation analysis requirements in US-003 and FR-001.