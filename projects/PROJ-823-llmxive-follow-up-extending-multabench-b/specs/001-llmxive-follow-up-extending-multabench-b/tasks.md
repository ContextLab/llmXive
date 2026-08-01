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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan in `code/`, `tests/`, `data/`
- [X] T002 Initialize a Python project with `pyproject.toml` dependencies (torch-cpu, transformers, sentence-transformers, scikit-learn, pandas, pyarrow, numpy, requests, pyyaml)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for global config, seeds (`random_seed=42`), and paths
- [X] T005 [P] Implement `code/utils/memory_monitor.py` to track peak RAM usage (memory limit)
- [X] T006 [P] Implement `code/utils/logging.py` for structured pipeline logging
- [X] T007 Create `code/data_loader.py` for MulTaBench ingestion with local checksum verification (SHA-256)
- [X] T008 Create `data/README.md` with instructions for local data ingestion and checksum validation. **CRITICAL**: This file MUST include explicit instructions on how to obtain the `data/raw/multabench_baselines.csv` file required for T032a, as no public URL exists.
- [X] T008b [P] Implement `code/pipelines/fetch_baselines.py` to validate the presence of `data/raw/multabench_baselines.csv`. **Logic**: If the file is missing or empty, the script MUST exit with code 1 and a clear error message. It must NOT generate synthetic data or attempt to parse arXiv links. **Dependency**: Refer to `data/README.md` (T008) for instructions on obtaining this file.
- [X] T008c [P] Update `data/README.md` to explicitly document the manual steps required to acquire `data/raw/multabench_baselines.csv` (e.g., "Download from MulTaBench supplementary material, unzip, and place in data/raw/").
- [X] T009a [P] Create `contracts/frozen_embedding.schema.yaml` defining the schema for frozen embeddings (fields: run_id, dataset_id, vector, model_type)
- [X] T009b [P] Create `contracts/tabular_metadata.schema.yaml` defining the schema for tabular metadata (fields: dataset_id, cardinality, missingness, sparsity, variance)
- [X] T009c [P] Update `data-model.md` to reference the new contract files and define `run_id` propagation logic for all downstream artifacts
- [X] T010 Create `code/models/__init__.py` and base model structures
- [X] T024 [P] [US3] Implement `code/analysis/metadata_stats.py` to compute cardinality, missingness, sparsity, and variance for tabular features for **ALL available datasets**. Output must be a single summary CSV: `data/processed/metadata_stats_summary.csv` with columns [dataset_id, cardinality, missingness, sparsity, variance]. **Aggregation Logic**: 'Variance' must be computed as the mean variance across all tabular features per dataset. **Verification**: Verify row count in output matches count of datasets in `data/raw/`. This task is a shared prerequisite for US2 and US3 and must complete before T025 and T033.
- [X] T045 [US1/US2] **Data Integrity Check**: Implement `code/pipelines/verify_data_integrity.py` to cross-check that every dataset ID in `data/processed/metadata_stats_summary.csv` (T024) exists in `data/raw/` and has non-zero variance in at least one tabular feature. **Dependency**: Must run after T024 completion. **Logic**: If a dataset has zero variance, skip it in the analysis and log to `data/artifacts/data_integrity_report.json` with a 'skipped' status. **Output**: `data/artifacts/data_integrity_report.json` containing a list of skipped dataset IDs and the reason (e.g., "zero_variance"). **Constraint**: This task MUST run before T033 to ensure zero-variance datasets are excluded from the correlation analysis.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Tractable Baseline Generation (Priority: P1) 🎯 MVP

**Goal**: Generate frozen embeddings for images and text using CLIP ViT-B/32 and Sentence-BERT on CPU without gradient tracking.

**Independent Test**: Verify script completes within 60 mins on a sample of datasets, outputs valid parquet files, and no CUDA errors occur.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Unit test for batch processing logic in `tests/test_embeddings.py::test_batch_processing_memory`
- [X] T012 [P] [US1] Unit test for gradient disabling in `tests/test_embeddings.py::test_no_grad_context`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/embeddings/generator.py` with CLIP ViT-B/32 and Sentence-BERT loaders (CPU-only, default precision)
- [X] T014 [US1] Implement `code/embeddings/utils.py` with batch processing logic to ensure memory safety (max batch size)
- [X] T015 [US1] Implement `code/pipelines/run_baseline.py` to generate embeddings for **ALL available datasets** in the pipeline with `random_seed=42`. Output must include `data/processed/embeddings_{run_id}.parquet` with `run_id`, `dataset_id`, `vector`, and `model_type` columns (matching `contracts/frozen_embedding.schema.yaml`). Ensure deterministic re-computation for all datasets to satisfy FR-001.
- [X] T016 [US1] Add logic to handle datasets with zero variance or missing image/text fields gracefully: skip dataset, log warning to `code/utils/logging.py`, and write skipped dataset IDs to `data/artifacts/skipped_datasets.json`.
- [X] T017 [US1] Implement output serialization to `data/processed/embeddings_{run_id}.parquet` with `run_id` and metadata, ensuring schema compliance with `contracts/frozen_embedding.schema.yaml`.
- [X] T018 [US1] Add validation to ensure no gradient tracking is enabled during inference
- [X] T019 [P] [US1] Sensitivity analysis script `code/pipelines/run_baseline_sensitivity.py` to generate embeddings for **ALL available datasets** using **5 total seeds (42, 123, 456, 789, 999)**. **Note**: While generation (T019) is parallel, the subsequent tasks (T019b, T019d, T019c) are sequential consumers of these embeddings.
- [X] T019b [US1] Implement `code/pipelines/merge_sensitivity_outputs.py` to merge the 5-seed Parquet files from T019 into a single intermediate file. **Must run before T019d**.
- [X] T019d [US1] Implement `code/pipelines/train_frozen_baseline_classifier.py` to train a lightweight classifier (e.g., Logistic Regression) on the frozen embeddings from T019b to generate **Frozen Baseline Performance Metrics** (AUC/RMSE) for **ALL available datasets**. **Input**: Must consume the *same* normalized tabular features from `data/processed/normalized_tabular_features.csv` (generated by T024) and use the *exact same* feature engineering logic as T025 (US2) to ensure consistency with the 'CPU-Conditioned' denominator. **Aggregation Logic**: Compute the mean metric across all 5 seeds. Output `data/artifacts/frozen_baseline_metrics_{run_id}.json` containing `dataset_id`, `metric_name`, `metric_value` (mean), and `seed_count`. This task satisfies FR-001's requirement to re-compute the baseline performance and produces the specific artifact consumed by T019c. **Must run after T019b**.
- [X] T019c [US1] Implement `code/pipelines/aggregate_sensitivity.py` to compute mean/std of the **performance metrics** (AUC/RMSE) from `frozen_baseline_metrics_{run_id}.json` (T019d) and write to `data/artifacts/frozen_baseline_aggregated_{run_id}.json`. **Note**: This aggregates metrics, not embeddings vectors, to provide the denominator for the Recovery Ratio. **Must run after T019d**.

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
- [X] T025 [US2] Implement `code/pipelines/run_conditioned.py` to train the projection layer on **ALL available datasets**, consuming metadata stats from T024.
- [X] T026 [US2] Add logic to handle edge cases (e.g., zero variance features) by skipping or imputing constants, ensuring no crash occurs before T025 runs.
- [X] T027 [US2] Implement evaluation logic to record performance metrics (AUC/RMSE) for held-out test sets.
- [X] T028 [US2] Store results in `data/artifacts/metrics_conditioned_{run_id}.json` with `run_id` linkage.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Efficacy Correlation & Statistical Analysis (Priority: P3)

**Goal**: Correlate performance recovery ratio with tabular metadata statistics and perform statistical significance testing.

**Independent Test**: Verify correlation analysis script outputs Pearson coefficients, p-values, and performs t-test/Wilcoxon test correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for correlation calculation in `tests/test_analysis.py::test_correlation_calculation`
- [X] T030 [P] [US3] Unit test for FDR correction implementation in `tests/test_analysis.py::test_benjamini_hochberg`

### Implementation for User Story 3

- [X] T032a [US3] Implement `code/pipelines/validate_baselines.py` to validate the presence of 'GPU-Tuned' baselines for all datasets. **Input**: `data/raw/multabench_baselines.csv` (from T008b). **Output**: `data/artifacts/gpu_tuned_baselines.csv` (validated subset) and `data/artifacts/data_availability_gap_report.json` (listing missing entries). **Logic**: Explicitly exclude datasets missing 'GPU-Tuned' baselines from the list of valid datasets for subsequent correlation tasks (T033, T035). **Dependency**: Must run after T008b.
- [X] T031 [US3] Implement `code/analysis/correlation.py` to calculate "Recovery Ratio" = (CPU-Conditioned - Frozen_Aggregated) / (GPU-Tuned - Frozen_Aggregated). **Input**: `data/artifacts/gpu_tuned_baselines.csv` (T032a), `data/artifacts/frozen_baseline_aggregated_{run_id}.json` (T019c - Performance Metrics), and `data/artifacts/metrics_conditioned_{run_id}.json` (T028). **Dependency**: Must run after T019c, T028, and T032a completion.
- [X] T033 [US3] Perform Pearson correlation between "Recovery Ratio" and metadata features (Cardinality, Missingness, Sparsity, Variance) for the **first 20 available datasets (alphabetically)** with complete data, **excluding those flagged in T032a and T045**. **Dependency**: Requires T024, T032a, and T045 completion. **Logic**: If fewer than 20 datasets are available after exclusions, use all available and flag the shortfall in the report.
- [X] T034 [US3] Implement Benjamini-Hochberg (FDR) correction for multiple comparisons. **Scope**: Apply FDR ONLY to the correlation p-values from T033 (family of tabular metadata features). **Input**: p-values from T033. Do NOT include t-test results (T035) in this correction. Output: JSON with adjusted p-values.
- [X] T035 [US3] Perform one-sample t-test comparing "CPU-Conditioned" performance vs. fixed GPU-Tuned baseline for **ALL valid datasets**. **Implementation**: Use `scipy.stats.ttest_1samp(data, popmean=baseline_value)` where `baseline_value` is the fixed scalar from T032a. **Constraint**: Do NOT treat the baseline as a sample array; treat it as a constant `popmean`.
- [X] T036 [US3] Generate `data/artifacts/correlation_report_{run_id}.json` with coefficients, p-values, and significance flags.
- [X] T037 [US3] Create `code/pipelines/run_analysis.py` to orchestrate the full statistical analysis pipeline.
- [X] T038 [US3] Add "Data Availability Gap" reporting for datasets missing GPU-Tuned baselines to the final report.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Update `code/pipelines/update_state.py` to hash artifacts and update `state/projects/...yaml`
- [X] T040 [P] Code cleanup and refactoring for memory efficiency: Refactor T014 to use generator expressions and optimize T024 metadata calculation to use pandas groupby.
- [X] T041 [US1/US2/US3] Performance optimization to ensure total runtime < 6 hours. Implement adaptive batching in T014 utils.py and dynamic parallelism logic in T025 trainer.py. **Adaptive Logic**: Reduce batch size by [deferred] if memory usage > 6.0GB; reduce by [deferred] again if > 6.5GB. **Verification**: Run full pipeline on all datasets and record total runtime in `data/artifacts/runtime_report.json`.
- [X] T042 [P] Additional unit tests for edge cases (e.g., empty datasets, single-row datasets) in `tests/`
- [X] T043a [P] Generate/Update `quickstart.md` with new pipeline steps (US1, US2, US3) and data ingestion instructions.
- [X] T044 [P] Final integration test of the entire pipeline on a subset of datasets.

---

## Phase 7: Verification & Hardening (Review-Driven)

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical rigor, and pipeline robustness.

- [X] T048 [US1/US2/US3] **Final End-to-End Runtime Validation**: Execute the complete pipeline (US1 → US2 → US3) on the full set of available datasets on a standard GitHub Actions free runner. **Goal**: Verify total execution time is strictly within acceptable limits and peak memory usage never exceeds acceptable thresholds.. **Output**: Generate `data/artifacts/final_validation_report.md` containing the total runtime, peak memory usage, and a pass/fail status for FR-004. If the limit is exceeded, the report must identify the specific bottleneck (e.g., "Embedding generation exceeded 60m on dataset X").

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Verification (Phase 7)**: Depends on completion of all User Story implementations

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Relies on US1 output (embeddings)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on US1 and US2 output (metrics). **CRITICAL**: US3 cannot run in parallel with US2 as it consumes US2's artifacts.

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
- **CRITICAL**: The loader in `code/data_loader.py` MUST fail loudly (raise exception) if real MulTaBench data is missing; no synthetic fallbacks are permitted.
- **CRITICAL**: T008b must explicitly define the source of the 'GPU-Tuned' baseline (local file `data/raw/multabench_baselines.csv`) and must NOT guess, synthesize, or parse external links if the file is missing. Refer to T008 for acquisition instructions.
- **CRITICAL**: T031 must use the **re-computed** frozen baseline performance metrics (from T019c/T019d) as the denominator, not historical paper values.
- **CRITICAL**: T045 must verify that no dataset in the analysis pipeline lacks sufficient variance, as this invalidates the correlation analysis (FR-003).
- **CRITICAL**: T048 is mandatory to verify the project meets the 6-hour/7GB constraints defined in FR-004 before considering the feature complete.

---

## Phase 8: Final Review & Cleanup (Post-Analysis)

**Purpose**: Finalize documentation and address any remaining minor issues found during execution.

- [X] T049 [P] Review `data/artifacts/final_validation_report.md` and `data/artifacts/correlation_report_{run_id}.json` to ensure all FR requirements are met.
- [ ] T050 [P] Update `README.md` in the repository root with a summary of the project's findings, including the Recovery Ratio and key correlations.
- [ ] T051 [P] Archive all generated artifacts in `data/artifacts/` with a clear `run_id` naming convention for future reference.
- [ ] T052 [P] Close any open issues or TODOs in the codebase related to the implementation of US1, US2, and US3.