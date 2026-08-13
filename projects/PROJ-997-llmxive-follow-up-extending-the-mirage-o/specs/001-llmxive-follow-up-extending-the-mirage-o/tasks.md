# Tasks: llmXive follow-up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

**Input**: Design documents from `/specs/001-llmxive-mipu-gap-bounds/`
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

- [ ] T001 Create project structure: Create directories `src/`, `tests/`, `data/raw/`, `data/processed/`, `data/models/`, `docs/reports/`, `src/lib/`, `src/services/`, `src/cli/`, `src/config/`, `src/models/` AND create `__init__.py` files in each directory to ensure valid Python package structure.
- [X] T002 Create `requirements.txt` containing: `transformers>=4.30.0`, `llama-cpp-python>=0.2.0`, `scikit-learn>=1.3.0`, `datasets>=2.14.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `torch>=2.0.0`, `pytest>=7.0.0`, `einops>=0.6.0`, `seaborn>=0.12.0`, `matplotlib>=3.7.0`
- [ ] T003 [P] Configure linting and formatting: Create `.ruff.toml` with ruff config and `pyproject.toml` with `[tool.black]` section

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure: `data/raw/`, `data/processed/`, `data/models/`
- [X] T005 [P] Implement `src/lib/streaming_utils.py` for chunked dataset loading and checksumming
- [X] T006 [P] Create `src/lib/error_handling.py` with strict failure modes (no synthetic fallbacks)
- [X] T007 Define `TrainingSample` and `GapPredictionResult` classes in `src/models/entities.py`
- [X] T008 Create `src/config/logging_config.py` that configures a FileHandler to `logs/pipeline.log` with JSON formatting
- [X] T009 Create `src/config/env_config.py` with a `load_config()` function reading from `.env` and create `.env.example` with keys for MODEL_PATH, DATASET_ID

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Hardware-Validated Gap Dataset Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a dataset pairing full-precision training signals with ground-truth policy divergence measured by CPU-based quantized inference.

**Independent Test**: A CSV/Parquet file exists containing rows with `input_id`, `gradient_norms`, `local_curvature`, `quantized_logits`, and `calculated_kl_divergence`. The `calculated_kl_divergence` column must be non-zero for a statistically significant portion of the dataset.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for KL divergence calculation edge cases (zero-divergence) in `tests/unit/test_gap_calculator.py`
- [X] T011 [P] [US1] Integration test for data streaming and schema validation in `tests/integration/test_data_generation.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `src/services/feature_extractor.py`: Load full-precision Llama-8B, extract gradient norms (L2) and local curvature (Hutchinson's estimator) for GSM8K/Ultrachat samples
- [X] T013 [P] [US1] Implement `src/services/quantized_inference.py`: Wrap `llama-cpp-python` to run INT4, INT8, and FP8 inference on CPU; **explicitly catch** `llama_cpp.LlamaError` and `OSError`, **log the error** with a specific format (e.g., "Error loading quantization: {error}"), **skip the sample**, and **continue to the next sample** to ensure partial completion; **verify** that the final dataset is not empty and log the count of skipped samples.
- [X] T014 [US1] Implement `src/services/gap_calculator.py`: Compute exact KL divergence between full-precision and quantized logits; add epsilon for numerical stability
- [ ] T015 [US1] Implement `src/cli/generate_dataset.py`: Orchestrate streaming of GSM8K/Ultrachat prompts; **for every sample**, execute feature extraction (T012) and quantized inference (T013) **in a paired loop** to ensure alignment, then write `data/processed/training_sample.parquet` with columns: `input_id`, `gradient_norms`, `local_curvature`, `quantized_logits`, `calculated_kl_divergence`, `quantization_level`
- [X] T016 [US1] Modify `src/cli/generate_dataset.py` to append a summary log entry at the end of execution recording the **actual observed proportion** of samples with non-zero `calculated_kl_divergence` and report it in the pipeline log
- [ ] T017 [US1] Add logging for data generation progress, skipped samples, and quantization errors
- [X] T018 [US1] Implement `src/services/vif_checker.py`: Calculate Variance Inflation Factor (VIF) for gradient norms and curvature on the generated dataset; log results to `logs/pipeline.log` to validate the Assumption before model training
- [ ] T018A [US1] Implement `src/cli/validate_features.py`: Load `training_sample.parquet`, run VIF diagnostic using `src/services/vif_checker.py`, and **log a warning** (do not raise an error) if collinearity exceeds threshold (VIF > 10) to ensure features are valid before training; log results to `logs/pipeline.log`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

**Explicit Internal Dependencies for T015**: T015 depends on T012, T013, and T014 being complete to ensure feature extraction, quantized inference, and gap calculation services are available for the paired loop.

---

## Phase 4: User Story 2 - Training-Signal Predictor Model (Priority: P2)

**Goal**: Train a lightweight regression model (KRR) to predict the hardware-measured policy gap using only training-side features.

**Independent Test**: A trained model artifact exists that outputs a predicted divergence value. The model achieves a Pearson correlation coefficient (r) of > 0.8 on a held-out validation set.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for KRR training pipeline and hyperparameter grid in `tests/unit/test_predictor.py`
- [X] T020 [P] [US2] Integration test for model evaluation against test set in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T021A [US2] Implement `src/cli/prepare_data_split.py`: Load `training_sample.parquet`, **stratify by quantization level** (column name: `quantization_level`), and **concatenate stratified splits into a single training set**; write train/val/test splits to `data/processed/split_{set}.parquet`; **ASSERT** that each split contains samples from all three levels, raising an error if not (ensuring FR-004)
- [ ] T021 [US2] Implement `src/cli/train_predictor.py`: Load stratified `train.parquet` (output of T021A), train KRR, and save model artifact to `data/models/gap_predictor.pkl`
- [X] T022 [US2] Implement evaluation logic in `src/services/evaluator.py`: Calculate Pearson correlation (r) and MAE between predicted and actual divergence on test set
- [ ] T022A [US2] Implement `src/cli/evaluate_on_test.py`: Load `test.parquet` (output of T021A), load `gap_predictor.pkl` (output of T021), and run the evaluation logic from T022 against the test set; report metrics to `data/processed/test_metrics.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bound Verification & Statistical Validation (Priority: P3)

**Goal**: Verify theoretical bounds across quantization levels and statistically compare proxy vs. baseline MIPU loops.

**Independent Test**: A report exists showing correlation > 0.8 for at least one quantization level and a paired t-test result (p > 0.05) comparing policy acceptance rates.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for report schema in `tests/contract/test_report_schema.py`
- [X] T025 [P] [US3] Integration test for end-to-end statistical validation in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [ ] T026A [US3] Implement `src/cli/synchronize_inputs.py`: Generate a fixed set of input prompts with a **fixed random seed (seed=42)** and write them to `data/processed/synchronized_inputs.json`; this artifact serves as the single source of truth for both T027 and T028 to ensure paired t-test validity; **generate a set of prompts**.
- [X] T026 [US3] Implement `src/cli/orchestrate_baseline_proxy.py`: Load `test.parquet`, set a **fixed random seed**, and **synchronize input prompts** from T026A; trigger T027 (baseline) and T028 (proxy) with these shared inputs to ensure valid paired comparison
- [ ] T027 [US3] Implement `src/cli/run_baseline_sync.py`: Execute the **full-hardware-sync baseline** by running actual quantized inference for every sample in the test set (using the same quantization levels as the dataset); calculate ground-truth acceptance rates and final reasoning scores; output results to `data/processed/baseline_metrics.json`; this task provides the ground-truth baseline for T028
- [X] T028 [US3] Implement `src/cli/run_proxy_loop.py`: Simulate MIPU loop (Proxy Policy vs. **Baseline from T027**) on test set; **execute the script** against the synchronized inputs to generate `proxy_metrics.json`; calculate acceptance rates and final reasoning scores; perform paired t-test comparing Proxy vs. Baseline (FR-006)
- [ ] T029 [US3] Implement statistical comparison in `src/services/statistical_tester.py`: Perform paired t-test on acceptance rates and final scores; apply Bonferroni correction; **generate `t_test_results.json`** artifact.
- [ ] T031 [US3] Implement `src/services/bound_verifier.py`: Verify `|predicted - actual| < 0.1` holds **separately for INT4, INT8, and FP8 levels**; **calculate and report** the "percentage of samples satisfying the bound across ALL three levels" to a machine-readable artifact `data/processed/consistency_report.json`
- [ ] T032 [US3] Implement `src/cli/aggregate_consistency.py`: Aggregate results from T031 to **verify consistency** across all three levels (INT4, INT8, FP8); report correlation coefficient per level and a summary consistency metric (SC-004) in `data/processed/consistency_report.json`
- [ ] T030 [US3] Implement `src/services/latency_meter.py`: Measure time for **policy evaluation step** (KRR prediction) vs. **full inference latency of the quantized engine** (from T027); **calculate `latency_reduction_percentage`** using formula: `(baseline_time - proxy_time) / baseline_time * 100`; write `proxy_time`, `baseline_time`, `reduction_percentage` to `data/processed/latency_metrics.json` to verify SC-002 (≥90% reduction target)
- [X] T033 [US3] Generate final research report with all metrics, plots, and statistical conclusions in `docs/reports/001-llmxive-mipu-gap-bounds.md`, including **latency_reduction_percentage** for the **policy evaluation step** (SC-002), consistency findings, **Bonferroni correction method**, and adjusted alpha threshold
- [ ] T034 [US3] Update `state/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o.yaml` to set `updated_at` to current ISO timestamp and populate `artifact_hashes` with checksums of `data/processed/*.parquet` and `data/models/*.pkl`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035A [P] Update `README.md` with installation steps: Add specific instructions for installing dependencies, setting up environment variables, and running the pipeline.
- [ ] T035B [P] Update `docs/api.md` with function signatures: Document key functions in `src/services/`, `src/cli/`, and `src/models/` including parameters and return types.
- [ ] T036A [P] Remove unused imports: Scan all Python files and remove any unused imports.
- [ ] T036B [P] Optimize loops in `generate_ground_truth.py`: Reduce memory usage by optimizing data loading and processing loops.
- [ ] T037A [P] Ensure streaming works correctly: Verify chunked processing reduces peak memory usage to < 7GB for datasets > 7GB.
- [ ] T038 [P] Additional unit tests for edge cases (flat loss landscape, zero gradients) in `tests/unit/`
- [ ] T039 Security hardening (ensure no PII in logs or datasets)
- [ ] T040 Run `quickstart.md` validation to ensure reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`training_sample.parquet`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output (`gap_predictor.pkl`) and US1 data

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
Task: "Unit test for KL divergence calculation edge cases in tests/unit/test_gap_calculator.py"
Task: "Integration test for data streaming and schema validation in tests/integration/test_data_generation.py"

# Launch all models/services for User Story 1 together:
Task: "Implement src/services/feature_extractor.py"
Task: "Implement src/services/quantized_inference.py"
Task: "Implement src/services/gap_calculator.py"
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
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Validation)
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
- **Critical Constraint**: Data loaders MUST fail loudly on fetch errors; no synthetic fallbacks allowed.
- **Critical Constraint**: Streaming must be used for all dataset loading to avoid OOM on GitHub Actions runners.
- **Critical Constraint**: Quantized inference must use `llama.cpp` on CPU; if too slow, reduce sample size, do not simulate.
- **Critical Constraint**: Baseline comparison (T028) MUST use the full-hardware-sync execution from T027, not a static rule.
- **Critical Constraint**: Data splitting (T021A) MUST stratify by quantization level to ensure joint training (FR-004).
- **Critical Constraint**: Bound verification (T031/T032) MUST report consistency across all three levels (INT4, INT8, FP8).
- **Critical Constraint**: Latency measurement (T030) MUST isolate the 'policy evaluation step' and record the specific metric for SC-002.
- **Critical Constraint**: T015 MUST pair feature extraction and inference for every sample.
- **Critical Constraint**: T026 MUST synchronize seeds and inputs for T027/T028.
- **Critical Constraint**: T021A MUST assert all quantization levels are present in splits.