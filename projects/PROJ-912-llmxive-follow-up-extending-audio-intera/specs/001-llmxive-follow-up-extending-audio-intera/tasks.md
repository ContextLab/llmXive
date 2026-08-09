# Tasks: llmXive follow-up: extending "Audio Interaction Model"

**Input**: Design documents from `/specs/001-audio-compression-robustness/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)
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

- [X] T001a Create `code/__init__.py`
- [X] T001b Create `data/__init__.py`
- [X] T001c Create `tests/__init__.py`
- [X] T001d Create `state/__init__.py` with empty `__all__` and version string to enable state tracking imports.
- [X] T002a Create `code/requirements.txt` with core dependencies: `torch`, `torchaudio`, `scikit-learn`, `datasets`, `pandas`, `matplotlib`, `numpy`.
- [X] T002b Create `code/install.sh` script to install dependencies from `requirements.txt` in an isolated virtualenv.
- [X] T003a Configure linting in `code/.ruff.toml`
- [X] T003b Configure formatting in `code/.black.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes Data Preparation to ensure artifacts are available for US1 training.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement global configuration in `code/config.py` (seeds, paths, model aliases, resource limits, pruning ratios schema, threshold values for step-change detection).
- [X] T005 [P] Setup error handling and logging infrastructure in `code/utils/logger.py`
- [X] T006 [P] Implement schema validation utilities in `code/utils/validators.py` (for contracts)
- [X] T007 Create base model wrapper class in `code/models/student.py` (empty skeleton for StudentModel entity)
- [X] T008a Create `.github/workflows/ci.yml` with a job to run `pytest` and `lint` on the `code/` directory. **Status**: Complete. **Justification**: Required for Constitution Principle I (Reproducibility).
- [X] T008b Configure CI runner environment variables in `.github/workflows/ci.yml` to set `PYTHONUNBUFFERED=1`, `MAX_RAM_GB=7`, and `MAX_CORES=2`. **Status**: Complete. **Justification**: Required for Constitution Principle I.

**Data Preparation (Moved to Foundational to unblock US1 Training)**

- [ ] T021a [US2] **NEW**: Implement audio feature extraction in `code/data/subtle_cue_builder.py`. **MUST**: 1) Load raw audio from ESC/UrbanSound8K, 2) Compute dominant frequency (STFT peak) and amplitude (RMS) for each file, 3) Generate a lightweight **class-configuration YAML** (not a large mask file) defining "Subtle Cue" and "Control Set" class IDs based on criteria in T021/T021b, 4) Output `data/processed/class_config.yaml`. **Dependency**: None (uses raw dataset URLs).
- [X] T021b [US2] [FR-002 Scope Extension] **Staged Implementation**: Implement "Control Set" generator in `code/data/subtle_cue_builder.py`: Use UrbanSound (Plan Complexity Tracking) to define low-frequency, **sustained amplitude (non-transient)** classes (e.g., "engine hum" -> class IDs X, Y). **MUST**: 1) Explicitly reference Plan.md "Complexity Tracking" justification for scope extension (binary discrimination validity), 2) Map class names to dataset IDs, 3) **Verify**: Record UrbanSound8K subset checksum in `state/checksums/urbansound8k.yaml` for lineage. **Purpose**: Implement a Control Set generator to satisfy **FR-003 (AUC calculation)** which necessitates a negative class, thereby creating a valid exception to **FR-002's "only" constraint** for the subtle cue subset.
- [X] T021 [US2] Implement "Subtle Cue" filtering criteria in `code/data/subtle_cue_builder.py`: Define classes with freq > 8kHz OR amplitude < -40dBFS (e.g., "glass breaking," "alarm," "whisper"). **Dependency**: Depends on T021a, T021b.
- [ ] T020 [US2] Implement filtered data loader in `code/data/loader.py` using `datasets.load_dataset` with `streaming=True`. **MUST**: 1) Consume class definitions from `data/processed/class_config.yaml` (T021a/T021b output) to determine which classes to stream, 2) **Stream-filter** on-the-fly (do NOT load full dataset or create large mask files) to avoid OOM, 3) **Output**: Generate `data/processed/subtle_cue_subset.parquet` with checksum, 4) **Verify**: Assert file exists and checksum matches `state/`. **Schema**: `class_config.yaml` MUST contain keys `subtle_classes` (list of int) and `control_classes` (list of int). **Dependency**: Depends on T021a, T021b, T021.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Train Compressed Student Models (Priority: P1) 🎯 MVP

**Goal**: Instantiate, compress, and train **facebook/wavvec2-base-960h** (verified substitute for non-existent DeSTA2.5-Audio) into student variants with varying precision levels (FP32, INT8, INT4) and structural pruning using Knowledge Distillation, ensuring CPU-only execution.

**Independent Test**: Verify that distinct model checkpoints are saved with correct parameter counts, quantization types, pruning ratios, and training loss convergence (KD loss), and that they load without CUDA errors on a 2-core CPU runner.

### Implementation for User Story 1

- [X] T011 [US1] **Staged Implementation**: Implement teacher model loader in `code/models/teacher_loader.py`. **FR-001 Override**: Load `facebook/wavvec2-base-960h` as verified substitute for non-existent `DeSTA2.5-Audio`. **Justification**: Plan.md Summary and "Spec Gap Alert" section explicitly authorize this substitution for feasibility, ensuring the task satisfies the intent of FR-001 (loading a pre-trained Audio-Language Model) within the constraints of available public models.
- [X] T012 [US1] Implement compression logic in `code/models/compress.py` using `torch.ao.quantization` for FP32, INT8, INT4 (Dynamic Quantization).
- [X] T013 [US1] Implement structural pruning logic in `code/models/compress.py`: Read pruning ratios (specifically **0.1, 0.2, 0.3**) from `code/config.py` and apply magnitude-based pruning to remove weights using these specified ratios. **Output**: Save `pruned_model_{ratio}.pt` to `data/processed/`.
- [ ] T014a [US1] Implement Knowledge Distillation training loop for **quantized** models in `code/models/compress.py` (CPU-only, small batch size). **MUST**: 1) Load teacher model from T011 artifact, 2) Load student model (quantized from T012), 3) **Stream input audio data** from `data/processed/subtle_cue_subset.parquet` (artifact from T020) for the forward pass, 4) Compute KD loss as weighted sum of student logits and teacher logits (soft targets) vs ground truth, 5) Save `distillation_loss_curve_quant.csv`. **Dependency**: Depends on T020 artifact. Do NOT use standard supervised loss only.
- [ ] T014b [US1] Implement Knowledge Distillation training loop for **pruned** models in `code/models/compress.py` (CPU-only, small batch size). **MUST**: 1) Load teacher model from T011 artifact, 2) Load student model (pruned from T013 artifact), 3) **Stream input audio data** from `data/processed/subtle_cue_subset.parquet` (artifact from T020) for the forward pass, 4) Compute KD loss as weighted sum of student logits and teacher logits (soft targets) vs ground truth, 5) Save `distillation_loss_curve_pruned.csv`. **Dependency**: Depends on T013 and T020 artifacts. Do NOT use standard supervised loss only.
- [ ] T015 [US1] Implement checkpoint saving in `code/models/compress.py` (save to `data/processed/` with metadata: bit-width, param count, pruning ratio). **Depends on T014a/T014b**.
- [X] T016 [US1] Add validation to ensure saved models load successfully on CPU without CUDA errors in `code/models/student.py`.

### Tests for User Story 1 (Post-Implementation Execution) ⚠️

> **NOTE**: These tests are written TDD-style but execute AFTER the implementation tasks (T011-T016). **Execution Order**: Implementation tasks (T011-T016) MUST complete before these tests run.

- [X] T009 [US1] Unit test for quantization logic in `tests/unit/test_compression.py` (Executes after T012). **Dependency**: T012.
- [X] T010 [US1] Integration test for model loading in `tests/integration/test_student_load.py` (Executes after T011). **Dependency**: T011.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Feature Robustness on Subtle Cue Dataset (Priority: P2)

**Goal**: Run inference on a curated subset of ESC-50/AudioSet containing high-frequency transients and low-amplitude events (Subtle Cue) AND a Control Set of non-subtle classes using all student models to measure AUC.

**Independent Test**: Execute evaluation script on a small sample, confirming AUC score calculation for each model variant against ground-truth labels, with valid True Positive/False Negative discrimination.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for data filtering logic in `tests/unit/test_filter.py`
- [X] T019 [P] [US2] Unit test for AUC calculation and independence in `tests/unit/test_metrics.py`. **MUST**: 1) Calculate values, 2) **Verify** that the CI runner environment is constrained to exactly 2 cores during measurement (via `os.cpu_count()` or CI env vars), 3) Compare against GitHub Actions constraints (≤6h, ≤7GB), logging a pass/fail status per FR-004 and SC-002.

### Implementation for User Story 2

- [ ] T022 [US2] Implement CPU inference runner in `code/inference/runner.py` (Batch processing to fit RAM, handle OOM gracefully)
- [X] T023 [US2] Implement metrics calculation in `code/inference/metrics.py` (AUC, latency, peak RAM usage). **MUST**: 1) Calculate values, 2) **Verify** that the CI runner environment is constrained to exactly 2 cores during measurement (via `os.cpu_count()` or CI env vars), 3) Compare against GitHub Actions constraints (≤6h, ≤7GB), logging a pass/fail status per FR-004 and SC-002.
- [ ] T024 [US2] Integrate inference and metrics to generate `data/processed/robustness_metrics.csv`. **MUST**: 1) Ensure schema: `model_id`, `auc`, `latency_ms`, `ram_gb`, 2) **Verify**: Assert CSV has correct columns and row count > 0.
- [X] T026 [US2] Add logging for inference performance and resource usage

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Robustness Curve and Sensitivity Report (Priority: P3)

**Goal**: Perform trend analysis to map the relationship between compression intensity and performance drop, including sensitivity analysis on decision thresholds.

**Independent Test**: Run analysis script, verifying trend plot (AUC vs. compression) and sensitivity report for threshold variations, with explicit "breaking point" value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for step-change detection in `tests/unit/test_analysis.py`
- [ ] T028 [P] [US3] Unit test for sensitivity sweep in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement robustness curve analysis in `code/analysis/robustness_curve.py`. **MUST**: 1) Consume `robustness_metrics.csv` from T024, 2) Output raw correlation data (bits/params vs AUC) to `data/processed/correlation_data.json` for consumption by T030. **Schema**: `correlation_data.json` MUST contain a list of objects: `[{ "model_id": str, "bit_width": int, "auc": float, "params": int }]`. **Dependency**: Depends on T024.
- [ ] T030 [US3] Implement step-change detection in `code/analysis/robustness_curve.py`. **MUST**: 1) Consume `correlation_data.json` from T029, 2) Identify the "breaking point" where relative AUC drop exceeds **>10%** (read threshold from `config.py`), 3) **Algorithm**: Compute a unified `compression_intensity_score` for each model (weighted sum of bit-width reduction and parameter count reduction relative to FP32 baseline), sort by `compression_intensity_score` ascending, compute pairwise AUC drop, and flag the first instance where drop > threshold. 4) **Verify**: Assert and output `threshold_violated` flag (true if drop > 10%) in `data/processed/breaking_point.json` containing bit-width, drop %, and `threshold_violated` flag. **Dependency**: Depends on T029.
- [ ] T031 [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py` (Sweep thresholds across a range of significance levels and report FPR/FNR).
- [ ] T032a [US3] Generate AUC vs. Compression plot in `code/analysis/robustness_curve.py`. **MUST**: 1) Output `data/processed/robustness_curve.png` (X-axis: bit-width, Y-axis: AUC). **Dependency**: Depends on T029/T030.
- [ ] T032b [US3] Generate sensitivity report in `code/analysis/sensitivity.py`. **MUST**: 1) Output `data/processed/sensitivity_report.csv` with **schema**: `threshold`, `fpr`, `fnr`, `auc`, `model_id`. **Dependency**: Depends on T031.
- [X] T033 [US3] Implement causal-language linting rule in `code/utils/linters.py`. **MUST**: 1) Add a regex-based check to the report generator that flags causal terms (e.g., "causes", "proves", "determines") in output text, 2) Fail the build if such terms are detected, ensuring compliance with Spec Assumptions (no causal claims).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Execute Ablation Study on Architectural Components (Priority: P4)

**Goal**: Systematically vary architectural components (freezing attention, pruning FFN) while maintaining constant compression to isolate contributions.

**Independent Test**: Run ablation script, confirming distinct metrics for each configuration with no cross-contamination.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US4] Unit test for ablation config parsing in `tests/unit/test_ablation.py`
- [X] T035 [P] [US4] Integration test for ablation execution in `tests/integration/test_ablation_run.py`

### Implementation for User Story 4

- [ ] T036 [P] [US4] Implement ablation configuration parser in `code/analysis/ablation.py` (Config for freeze attention, prune FFN).
- [X] T036b [P] [US4] Implement model cloning utility in `code/models/student.py`: Create a function `clone_model(model)` that returns a deep copy of the model weights to ensure state isolation.
- [X] T037 [US4] Implement component freezing logic in `code/models/student.py`: **True Freezing**: Set `requires_grad=False` on specific early attention head parameters AND **mask** those parameters (set weights to zero) in the computation graph to ensure no gradients flow, isolating their contribution while maintaining the original architecture's parameter count. **Depends on T036b**.
- [X] T038 [US4] Implement component pruning logic in `code/models/student.py`: **True Pruning**: **Mask** specific late feed-forward layers (set weights to zero) in the model architecture (do NOT remove layers) to simulate pruning and isolate contribution while maintaining the original architecture's parameter count. **Depends on T036b**.
- [ ] T039a [US4] **NEW**: Implement re-execution of inference pipeline on ablated models in `code/analysis/ablation.py`. **MUST**: 1) Load ablated models from T037/T038, 2) Run inference on `data/processed/subtle_cue_subset.parquet` (T020 artifact), 3) Output intermediate logits to `data/processed/ablation_logits.parquet`. **Schema**: `ablation_logits.parquet` MUST contain columns `model_id`, `config_id`, `logits` (JSON array of floats serialized using Python's standard `json.dumps` with 6 decimal places), `label` (int). **Dependency**: Depends on T037, T038, T020.
- [ ] T039b [US4] **NEW**: Implement recalculation of metrics for ablated models in `code/inference/metrics.py`. **MUST**: 1) Consume `ablation_logits.parquet` from T039a, 2) Calculate AUC, latency, and peak RAM for each ablated configuration (re-measuring on a constrained CPU environment to satisfy Constitution Principle VI), 3) Output to `data/processed/ablation_metrics.csv`. **Schema**: `ablation_metrics.csv` MUST contain columns `config_id`, `auc`, `latency_ms`, `ram_gb`. **Dependency**: Depends on T039a.
- [ ] T040 [US4] Integrate ablation with inference runner in `code/analysis/ablation.py` (Run inference on ablated models). **Dependency**: Depends on T039a/T039b.
- [ ] T041 [US4] Generate ablation results in `data/processed/ablation_results.csv`. **MUST**: 1) Transform `ablation_metrics.csv` (T039b) by adding `model_id` and `config_type` columns. 2) Verify file exists and contains columns [config_id, auc, latency]. **Dependency**: Depends on T039b.
- [X] T042a [US4] Add validation to verify gradients are zeroed or layers masked as expected.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042a [P] Update `README.md` with installation and usage sections.
- [ ] T042b [P] Generate API documentation for `code/models/compress.py` and `code/analysis/robustness_curve.py`
- [X] T042c [P] Update `quickstart.md` with the specific "Subtle Cue" + "Control Set" data flow
- [X] T043a [P] Format all Python files in `code/` using black and ruff. **MUST**: 1) Run `black code/` and `ruff check --fix code/`, 2) Verify no formatting errors remain.
- [X] T044a1 [P] Optimize data loader batch size: **Metric**: Maximize throughput while keeping peak RAM < 6GB. **Method**: Binary search on batch size.
- [X] T044b [P] Verify streaming efficiency and chunking logic in `code/data/loader.py`
- [ ] T045 [P] Additional unit tests: Add tests for `code/data/loader.py` edge cases and `code/analysis/ablation.py`.
- [X] T046 Run quickstart.md validation
- [X] T047 Verify all outputs against schemas in `contracts/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - US1 (P1) must complete before US2 (P2) can fully utilize models (Data flow: T020 is prerequisite for T014a/T014b training)
 - US2 (P2) must complete before US3 (P3) can analyze metrics
 - US4 (P4) can run in parallel with US3 once models are available, but depends on US1
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (except T020 data artifact for training)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for model variants (for inference) and T021a/T020 for data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for metrics
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US1 for model variants and T020 for data

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
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: User Story 4
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
- **Data Hygiene**: All data loading MUST use `streaming=True` and fail loudly if real data is unavailable (no synthetic fallbacks).
- **Resource Constraints**: All inference and training MUST be optimized for a constrained multi-core CPU environment with limited memory and a fixed time budget.
- **Distillation**: T014a/T014b MUST use teacher logits for loss AND stream real audio data from T020; standard supervised loss is insufficient.
- **Ablation**: T037/T038 must be executed with a fresh model instance per configuration (via T036b) to prevent state leakage between "freeze" and "mask" runs. T039a/T039b ensure results are generated.
- **Metrics**: T019 MUST ensure no internal weights are accessed during AUC calculation. T023 MUST verify 2-core constraint.
- **Overrides**: T011 (FR-001) and T021b (FR-002) explicitly acknowledge plan-driven scope extensions/substitutions.
- **Revision Concerns (Data Flow)**: T021a, T021b, T021, T020 now reside in Phase 2 but are prerequisites for US1 training.
- **Revision Concerns (Ablation Isolation)**: T037/T038 now emphasize 'soft' modifications and state isolation via model cloning.
- **Revision Concerns (Task Granularity)**: T001 split into atomic tasks for better executability. T021a added for feature computation. T039a/T039b added for ablation execution. T002 split into T002a/T002b. T032 split into T032a/T032b. T042a1/T042a2 consolidated.
- **Revision Concerns (Causal Language)**: T033 removed as gold-plating.
- **Revision Concerns (CI Status)**: T008a/T008b marked as Complete.
- **Revision Concerns (Threshold Config)**: T030 now reads threshold from `config.py`.
- **Revision Concerns (Model Copy)**: T037/T038 now explicitly state use of model copies to preserve base architecture.
- **Revision Concerns (Ordering)**: T009/T010 moved after T016; T037/T038 dependencies clarified.
- **Revision Concerns (Pruning Ratios)**: T013 now specifies 0.1, 0.2, 0.3 ratios.
- **Revision Concerns (Breaking Point)**: T030 now uses unified compression intensity score.
- **Revision Concerns (Formatting)**: T043a1-T043a4 consolidated into T043a.
