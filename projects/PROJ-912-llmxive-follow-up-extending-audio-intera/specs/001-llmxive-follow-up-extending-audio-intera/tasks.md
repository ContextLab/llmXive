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
- [X] T002a Create `code/requirements.txt` with core dependencies: `torch==2.1.0`, `torchaudio==2.1.0`, `scikit-learn==1.3.2`, `datasets==2.14.6`, `pandas==2.1.1`, `matplotlib==3.8.0`, `numpy==1.26.0`.
- [X] T002b Create `code/install.sh` script to install dependencies from `requirements.txt` in an isolated virtualenv.
- [X] T003a Configure linting in `code/.ruff.toml`
- [X] T003b Configure formatting in `code/.black.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement global configuration in `code/config.py` (seeds, paths, model aliases, resource limits, pruning ratios schema, threshold values for step-change detection, KD_ALPHA, KD_TEMP). **Defaults**: `STEP_CHANGE_THRESHOLD=0.10`, `PRUNING_RATIOS=[0.1, 0.2, 0.3]`, `KD_ALPHA=0.5`, `KD_TEMP=4.0`, `WEIGHTS_SCORE=[0.5, 0.5]`.
- [X] T005 [P] Setup error handling and logging infrastructure in `code/utils/logger.py`
- [X] T006 [P] Implement schema validation utilities in `code/utils/validators.py` (for contracts)
- [X] T007 Create base model wrapper class in `code/models/student.py` (empty skeleton for StudentModel entity)
- [X] T008a Create `.github/workflows/ci.yml` with a job to run `pytest` and `lint` on the `code/` directory. **Status**: Complete. **Justification**: Required for Constitution Principle I (Reproducibility). CI enforces reproducibility by running tests on a fresh environment with pinned versions, preventing 'works on my machine' scenarios.
- [X] T008b Configure CI runner environment variables in `.github/workflows/ci.yml` to set `PYTHONUNBUFFERED=1`, `MAX_RAM_GB=7`, and `MAX_CORES=2`. **Status**: Complete. **Justification**: Required for Constitution Principle I.

---

## Phase 2.5: Data Preparation (Prerequisite for US1 & US2)

**⚠️ CRITICAL**: T021a/T021d must complete before T020; T020 must complete before T014a/b/c (US1 Training) can start.

**Note on Scope Expansion**: Tasks T021c/T021d implement a "Control Set" of non-subtle classes. This overrides FR-002's strict "subtle only" constraint to ensure valid binary AUC calculation (True Positive vs False Positive), as explicitly authorized by the Plan.md "Complexity Tracking" table.

- [X] T021a [Shared] **NEW**: Implement audio feature extraction in `code/data/subtle_cue_features.py`. [Plan-Complexity-Tracking] **MUST**: 1) Define criteria: "Subtle Cue" classes are those with dominant frequency > 8kHz OR amplitude < -40dBFS. **Algorithm**: Use `torchaudio.transforms.MelSpectrogram` (n_mels=128, n_fft=2048, hop_length=512, window='hann') to compute frequency bins. 2) Calculate dominant frequency as the argmax of the energy spectrum. 3) Calculate amplitude as RMS over a short time window. 4) Generate a lightweight **class-configuration YAML** `data/processed/class_config_subtle.yaml` containing keys `subtle_classes` (list of int). **Dependency**: None. **Verification**: Ensure atomic write to `data/processed/` and distinct filename.
- [X] T021b [Shared] **NEW**: Generate `data/processed/class_config_subtle.yaml` from T021a output. **Dependency**: T021a.
- [X] T021c [Shared] **NEW**: Define "Control Set" classes in `code/data/control_set_config.py`. [Plan-Complexity-Tracking] **MUST**: 1) Define "Control Set" classes as low-frequency, sustained amplitude classes. 2) **Plan Authorization**: Explicitly state in code comments that this task implements the "Control Set" requirement from Plan.md "Complexity Tracking" to support FR-003 (Binary AUC). 3) Map class names to dataset IDs using a hardcoded mapping table: `['engine hum', 'wind', 'rain', 'babbling', 'chainsaw', 'drilling', 'gunshot', 'jackhammer', 'siren', 'street music']`. 4) Generate `data/processed/class_config_control.yaml`. **Dependency**: None. **Verification**: Ensure atomic write to `data/processed/` and distinct filename.
- [X] T021d [Shared] **NEW**: Generate `data/processed/class_config_control.yaml` from T021c output. **Dependency**: T021c.
- [X] T020 [Shared] Implement filtered data loader in `code/data/loader.py` using `datasets.load_dataset` with `streaming=True`. **MUST**: 1) Consume class definitions from `data/processed/class_config_subtle.yaml` (T021b) and `data/processed/class_config_control.yaml` (T021d) to determine which classes to stream. 2) **Stream-filter** on-the-fly (do NOT load full dataset or create large mask files) to avoid OOM. 3) **Recovery Strategy**: If streaming fails, attempt a local cached download; if that fails, raise a clear error. 4) **Output**: Generate `data/processed/subtle_cue_subset.parquet` with checksum. **Schema**: `columns: audio_path (str), class_id (int), label (int)`. 5) **Verify**: Assert file exists and checksum matches `state/`. **Dependency**: Depends on T021b, T021d. **Failure Mode**: Must fail loudly if config files are missing.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Train Compressed Student Models (Priority: P1) 🎯 MVP

**Goal**: Instantiate, compress, and train **facebook/wavvec2-base-960h** (verified substitute for non-existent DeSTA2.5-Audio) into student variants with varying precision levels (FP32, INT8, INT4) and structural pruning using Knowledge Distillation, ensuring CPU-only execution.

**Independent Test**: Verify that distinct model checkpoints are saved with correct parameter counts, quantization types, pruning ratios, and training loss convergence (KD loss), and that they load without CUDA errors on a 2-core CPU runner.

### Tests for User Story 1 (Test-First) ⚠️

> **NOTE**: These tests are written TDD-style and MUST be written first to FAIL. **Execution Order**: Implementation tasks (T011-T016) MUST follow these tests.

- [X] T009 [US1] Unit test for quantization logic in `tests/unit/test_compression.py` (Executes after T012). **MUST**: Write `test_quantize_int8`, `test_quantize_int4` functions. **Dependency**: None (Write before T011/T012).
- [X] T010 [US1] Integration test for model loading in `tests/integration/test_student_load.py` (Executes after T011). **MUST**: Write `test_load_substitute_model` function. **Dependency**: None (Write before T011).

### Implementation for User Story 1

- [X] T011 [US1] **Staged Implementation**: Implement teacher model loader in `code/models/teacher_loader.py`. [Plan-SpecGap] **MUST**: Load `facebook/wav2vec2-base-960h` as verified substitute for non-existent `DeSTA2.5-Audio` per Plan.md "Spec Gap Alert". **Justification**: Plan.md Summary and "Spec Gap Alert" section explicitly authorize this substitution for feasibility, ensuring the task satisfies the intent of FR-001 (loading a pre-trained Audio-Language Model) within the constraints of available public models. **Dependency**: None.
- [X] T012 [US1] Implement compression logic in `code/models/compress.py` using `torch.ao.quantization` for FP32, INT8, INT4 (Dynamic Quantization). **Dependency**: T011.
- [X] T013 [US1] Implement structural pruning logic in `code/models/compress.py`: Read pruning ratios from `code/config.py` and apply magnitude-based pruning to remove weights using these specified ratios. **Output**: Save `pruned_model_{ratio}.pt` to `data/processed/`. **Dependency**: T011.
- [X] T014a [US1] Implement Knowledge Distillation training loop for **quantized** models in `code/models/compress.py` (CPU-only, small batch size). **MUST**: 1) Load teacher model from T011 artifact, 2) Load student model (quantized from T012), 3) **Stream input audio data** from `data/processed/subtle_cue_subset.parquet` (artifact from T020) for the forward pass (Combined Subtle + Control data), 4) Compute KD loss: `Loss = KL_Div(student_logits/T, teacher_logits/T) * KD_ALPHA + CrossEntropy(student_logits, labels) * (1 - KD_ALPHA)`, reading `KD_ALPHA` and `KD_TEMP` from `code/config.py`, 5) **Error Handling**: Implement try/except blocks around streaming reads; log corrupted files to `data/processed/corrupted_files.log` and skip them; fail the job if >5% of files are corrupted. 6) Save `distillation_loss_curve_quant.csv`. **Dependency**: Depends on T020 artifact. Do NOT use standard supervised loss only. **Failure Mode**: Must fail loudly if `data/processed/subtle_cue_subset.parquet` is missing.
- [X] T014b [US1] Implement Knowledge Distillation training loop for **pruned** models in `code/models/compress.py` (CPU-only, small batch size). **MUST**: 1) Load teacher model from T011 artifact, 2) Load student model (pruned from T013 artifact), 3) **Stream input audio data** from `data/processed/subtle_cue_subset.parquet` (artifact from T020) for the forward pass (Combined Subtle + Control data), 4) Compute KD loss: `Loss = KL_Div(student_logits/T, teacher_logits/T) * KD_ALPHA + CrossEntropy(student_logits, labels) * (1 - KD_ALPHA)`, reading `KD_ALPHA` and `KD_TEMP` from `code/config.py`, 5) **Error Handling**: Implement try/except blocks around streaming reads; log corrupted files to `data/processed/corrupted_files.log` and skip them; fail the job if >5% of files are corrupted. 6) Save `distillation_loss_curve_pruned.csv`. **Dependency**: Depends on T013 and T020 artifacts. Do NOT use standard supervised loss only. **Failure Mode**: Must fail loudly if `data/processed/subtle_cue_subset.parquet` is missing.
- [X] T014c [US1] **NEW**: Implement Knowledge Distillation training loop for **FP32 Baseline** model in `code/models/compress.py`. **MUST**: 1) Load teacher model from T011, 2) Load student model (FP32, no compression), 3) **Stream input audio data** from `data/processed/subtle_cue_subset.parquet` (T020) (Combined Subtle + Control data), 4) Compute KD loss: `Loss = KL_Div(student_logits/T, teacher_logits/T) * KD_ALPHA + CrossEntropy(student_logits, labels) * (1 - KD_ALPHA)`, reading `KD_ALPHA` and `KD_TEMP` from `code/config.py`, 5) Save `distillation_loss_curve_fp32.csv`. **Purpose**: Provide the baseline AUC for SC-001/SC-004 breaking point calculation. **Dependency**: Depends on T020.
- [X] T014d [US1] **NEW**: Implement a unified `KDTrainer` class in `code/models/compress.py` to encapsulate the common training logic used by T014a/b/c.
- [X] T015 [US1] Implement checkpoint saving in `code/models/compress.py` (save to `data/processed/` with metadata: bit-width, param count, pruning ratio). **Depends on T014a/T014b/T014c**.
- [X] T016 [US1] Add validation to ensure saved models load successfully on CPU without CUDA errors in `code/models/student.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Feature Robustness on Subtle Cue Dataset (Priority: P2)

**Goal**: Run inference on a curated subset of ESC-50/AudioSet containing high-frequency transients and low-amplitude events (Subtle Cue) AND a Control Set of non-subtle classes using all student models to measure AUC.

**Independent Test**: Execute evaluation script on a small sample, confirming AUC score calculation for each model variant against ground-truth labels, with valid True Positive/False Negative discrimination.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for data filtering logic in `tests/unit/test_filter.py`. **MUST**: Write `test_filter_subtle_classes`, `test_filter_control_classes` functions.
- [X] T019 [P] [US2] Unit test for AUC calculation and independence in `tests/unit/test_metrics.py`. **MUST**: 1) Calculate values,) **Verify** that the CI runner environment is constrained to exactly 2 cores during measurement (via `os.cpu_count()` or CI env vars), 3) Compare against GitHub Actions constraints (≤6h, ≤7GB), logging a pass/fail status per FR-004 and SC-002.

### Implementation for User Story 2

- [X] T022 [US2] Implement CPU inference runner in `code/inference/runner.py` (Batch processing to fit RAM, handle OOM gracefully). **Dependency**: T015.
- [X] T023 [US2] Implement metrics calculation in `code/inference/metrics.py` (AUC, latency, peak RAM usage). **MUST**: 1) Calculate values, 2) **Verify** that the CI runner environment is constrained to exactly 2 cores during measurement (via `os.cpu_count()` or CI env vars), 3) Compare against GitHub Actions constraints (≤6h, ≤7GB), logging a pass/fail status per FR-004 and SC-002. 4) **Input**: Consume the combined dataset (Subtle + Control) from T020 to ensure binary discrimination. 5) **Assertion**: Assert process completed within 6h and RAM < 7GB. **Dependency**: T015.
- [X] T024 [US2] Integrate inference and metrics to generate `data/processed/robustness_metrics.csv`. **MUST**: 1) Ensure schema: `model_id` (str), `auc` (float, 4 decimal places), `latency_ms` (float, 2 decimal places), `ram_gb` (float, 2 decimal places). 2) **Verify**: Assert CSV has correct columns and row count > 0. 3) **Input**: Consume the combined dataset (Subtle + Control) from T020. 4) **Assertion**: Assert total execution time < 6h. **Dependency**: Depends on T022, T023, T015.
- [X] T026 [US2] Add logging for inference performance and resource usage

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Robustness Curve and Sensitivity Report (Priority: P3)

**Goal**: Perform trend analysis to map the relationship between compression intensity and performance drop, including sensitivity analysis on decision thresholds.

**Independent Test**: Run analysis script, verifying trend plot (AUC vs. compression) and sensitivity report for threshold variations, with explicit "breaking point" value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for step-change detection in `tests/unit/test_analysis.py`. **MUST**: Write `test_step_change_detection` function.
- [X] T028 [P] [US3] Unit test for sensitivity sweep in `tests/unit/test_sensitivity.py`. **MUST**: Write `test_threshold_sweep` function.

### Implementation for User Story 3

- [X] T029 [US3] Implement robustness curve analysis in `code/analysis/robustness_curve.py`. **MUST**: 1) Consume `robustness_metrics.csv` from T024, 2) Output raw correlation data (bits/params vs AUC) to `data/processed/correlation_data.json` for consumption by T030. **Schema**: `correlation_data.json` MUST contain a list of objects: `[{ "model_id": str, "bit_width": int, "auc": float, "params": int }]`. **Dependency**: Depends on T024.
- [X] T030 [US3] Implement step-change detection in `code/analysis/robustness_curve.py`. **MUST**: 1) Consume `correlation_data.json` from T029, 2) Identify the "breaking point" where relative AUC drop exceeds **>10%** (read threshold from `config.py`). **Algorithm**: Compute a `compression_intensity_score` for each model: `score = (- bits/32) * 0.5 + (1 - params/baseline_params) * 0.5` (weights read from `config.py` as `WEIGHTS_SCORE`), sort by `compression_intensity_score` ascending, compute pairwise AUC drop, and flag the first instance where drop > threshold. 3) **Verify**: Assert and output `threshold_violated` flag (true if drop > 10%) in `data/processed/breaking_point.json` containing bit-width, drop %, and `threshold_violated` flag. **Note**: The baseline for comparison MUST be the FP32 model generated in T014c. **Output Requirement**: Explicitly identify the specific compression level (e.g., "INT4") as the breaking point in the JSON. **Dependency**: Depends on T029.
- [X] T031 [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py`. **MUST**: 1) Sweep thresholds over the **fixed set {0.01, 0.05, 0.1}** as mandated by FR-006 and SC-003. 2) Report the variation in false-positive and false-negative rates for each model variant. **Dependency**: Depends on T024.
- [X] T032a [US3] Generate AUC vs. Compression plot in `code/analysis/robustness_curve.py`. **MUST**:) Output `data/processed/robustness_curve.png` (X-axis: bit-width, Y-axis: AUC). **Dependency**: Depends on T029/T030.
- [X] T032b [US3] Generate sensitivity report in `code/analysis/sensitivity.py`. **MUST**: 1) Output `data/processed/sensitivity_report.csv` with **schema**: `threshold`, `fpr`, `fnr`, `auc`, `model_id`. **Dependency**: Depends on T031.
- [X] T033 [US3] Implement causal-language linting rule in `code/utils/linters.py`. **MUST**: 1) Add a regex-based check to the report generator that flags causal terms (e.g., "causes", "proves", "determines") in output text, 2) Fail the build if such terms are detected, ensuring compliance with Spec Assumptions (no causal claims).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Execute Ablation Study on Architectural Components (Priority: P4)

**Goal**: Systematically vary architectural components (freezing attention, pruning FFN) while maintaining constant compression to isolate contributions.

**Independent Test**: Run ablation script, confirming distinct metrics for each configuration with no cross-contamination.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US4] Unit test for ablation config parsing in `tests/unit/test_ablation.py`. **MUST**: Write `test_parse_ablation_config` function.
- [X] T035 [P] [US4] Integration test for ablation execution in `tests/integration/test_ablation_run.py`. **MUST**: Write `test_ablation_execution` function. **Dependency**: T034.

### Implementation for User Story 4

- [X] T036 [P] [US4] Implement ablation configuration parser in `code/analysis/ablation.py` (Config for freeze attention, prune FFN).
- [X] T036b [P] [US4] Implement model cloning utility in `code/models/student.py`: Create a function `clone_model(model)` that returns a deep copy of the model weights to ensure state isolation.
- [X] T037 [US4] Implement component freezing logic in `code/models/student.py`. [Plan-Deviation-SoftPrune] **MUST**: **Soft Pruning (Structural Isolation)**: Set `requires_grad=False` on specific early attention head parameters AND **mask** those parameters (set weights to zero) in the computation graph to ensure no gradients flow, isolating their contribution while maintaining the original architecture's parameter count. **Verification**: Count parameters before and after masking to ensure invariance; log the count to `data/processed/param_counts.csv`. **Justification**: This "soft pruning" preserves the architecture for fair latency comparison (FR-006) while isolating the component's contribution (FR-007). **Depends on T036b**.
- [X] T038 [US4] Implement component pruning logic in `code/models/student.py`. [Plan-Deviation-SoftPrune] **MUST**: **Soft Pruning (Structural Isolation)**: **Mask** specific late feed-forward layers (set weights to zero) in the model architecture (do NOT remove layers) to simulate pruning and isolate contribution while maintaining the original architecture's parameter count. **Verification**: Count parameters before and after masking to ensure invariance; log the count to `data/processed/param_counts.csv`. **Justification**: This "soft pruning" preserves the architecture for fair latency comparison (FR-006) while isolating the component's contribution (FR-007). **Depends on T036b**.
- [X] T039a [US4] **NEW**: Implement re-execution of inference pipeline on ablated models in `code/analysis/ablation.py`. **MUST**: 1) Load ablated models from T037/T038, 2) Run inference on `data/processed/subtle_cue_subset.parquet` (T020 artifact), Output intermediate logits to `data/processed/ablation_logits.parquet`. **Schema**: `ablation_logits.parquet` MUST contain columns `model_id`, `config_id`, `logits_json` (JSON string of a D array of floats, 6 decimal places, where D is dynamically determined by `model.config.num_labels`), `label` (int). **Dependency**: Depends on T037, T038, T020.
- [X] T039b [US4] **NEW**: Implement recalculation of metrics for ablated models in `code/inference/metrics.py`. **MUST**: 1) Consume `ablation_logits.parquet` from T039a, Evaluate AUC, latency, and peak RAM for each ablated configuration (re-measuring on a constrained CPU environment to satisfy Constitution Principle VI), 3) Output to `data/processed/ablation_metrics.csv`. **Schema**: `ablation_metrics.csv` MUST contain columns `config_id`, `auc`, `latency_ms`, `ram_gb`. **Dependency**: Depends on T039a.
- [X] T040 [US4] Integrate ablation with inference runner in `code/analysis/ablation.py`. **MUST**: 1) Load ablation configs (T036), 2) Execute T037/T038 logic to create ablated models, 3) Call T039a/T039b to run inference and calculate metrics. **Dependency**: Depends on T036, T037, T038, T039a, T039b.
- [X] T041 [US4] Generate ablation results in `data/processed/ablation_results.csv`. **MUST**: 1) Transform `ablation_metrics.csv` (T039b) by adding `model_id` and `config_type` columns. 2) Verify file exists and contains columns [config_id, auc, latency]. **Dependency**: Depends on T039b.
- [X] T042a [US4] Add validation to verify gradients are zeroed or layers masked as expected.
- [X] T043 [US4] **NEW**: Implement comparative analysis in `code/analysis/ablation.py`. [SC-005] **MUST**: 1) Load `ablation_results.csv` (T041) and `robustness_metrics.csv` (T024). 2) Compare the "soft pruning" results (constant params) against the "hard pruning" results (variable params from T013/T024) to address the metric gap in SC-004 (compression intensity vs performance drop). Generate `data/processed/ablation_comparison_report.md` describing the joint relationships and isolating the contribution of architectural components to feature loss. **Schema**: Report must include sections: "Joint Relationships", "Component Contribution", "Comparison Summary". **Dependency**: Depends on T041, T024.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042a [P] Update `README.md` with installation and usage sections. **MUST**: 1) Add "Usage" section with command `python code/main.py --mode train`, 2) Add "Data Flow" diagram showing Subtle + Control Set integration.
- [X] T042b [P] Generate API documentation for `code/models/compress.py` and `code/analysis/robustness_curve.py`. **MUST**: 1) Use `sphinx-apidoc` to generate docs in `docs/api/`, 2) Verify `docs/api/index.html` exists.
- [X] T042c [P] Update `quickstart.md` with the specific "Subtle Cue" + "Control Set" data flow
- [X] T043a [P] Format all Python files in `code/` using black and ruff. **MUST**: 1) Run `black code/` and `ruff check --fix code/`, 2) Verify no formatting errors remain.
- [X] T044a1 [P] Optimize data loader batch size: **Metric**: Maximize throughput while keeping peak RAM < 6GB. **Method**: Binary search on batch size. **Parameters**: Search range `start=1, end=128, step=1`. **Stopping Condition**: Stop when RAM < 6GB for 3 consecutive runs. **Output**: Generate `data/processed/batch_size_config.yaml` with optimal batch size.
- [X] T044b [P] Verify streaming efficiency and chunking logic in `code/data/loader.py`
- [X] T045 [P] Additional unit tests: Add tests for `code/data/loader.py` edge cases and `code/analysis/ablation.py`.
- [X] T046 [P] Verify all outputs against schemas in `contracts/`. **MUST**: 1) Verify `data/processed/robustness_metrics.csv` and `data/processed/ablation_results.csv`, 2) Use `jsonschema` tool, 3) Exit code 0 if all schemas match.
- [X] T047 Verify all outputs against schemas in `contracts/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Data Preparation (Phase 2.5)**: Depends on Foundational (Phase 2) - BLOCKS US1 and US2
- **User Stories (Phase 3+)**: All depend on Data Preparation (Phase 2.5) completion
 - US1 (P1) must complete before US2 (P2) can fully utilize models (Data flow: T020 is prerequisite for T014a/T014b/T014c training)
 - US2 (P2) must complete before US3 (P3) can analyze metrics
 - US4 (P4) can run in parallel with US3 once models are available, but depends on US1
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Data Preparation (Phase 2.5) - No dependencies on other stories (except T020 data artifact for training)
- **User Story 2 (P2)**: Can start after Data Preparation (Phase 2.5) - Depends on US1 for model variants (for inference) and T021a/T021c/T020 for data
- **User Story 3 (P3)**: Can start after Data Preparation (Phase 2.5) - Depends on US2 for metrics
- **User Story 4 (P4)**: Can start after Data Preparation (Phase 2.5) - Depends on US1 for model variants and T020 for data

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Data Preparation (Phase 2.5) completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: Data Preparation (CRITICAL - blocks US1)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational + Data Prep → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Data Prep together
2. Once Data Prep is done:
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
- **Distillation**: T014a/T014b/T014c MUST use teacher logits for loss AND stream real audio data from T020; standard supervised loss is insufficient.
- **Ablation**: T037/T038 must be executed with a fresh model instance per configuration (via T036b) to prevent state leakage between "freeze" and "mask" runs. T039a/T039b ensure results are generated. T043 ensures the comparative analysis required by SC-004 is performed.
- **Metrics**: T019 MUST ensure no internal weights are accessed during AUC calculation. T023 MUST verify 2-core constraint.
- **Overrides**: T011 (FR-001) and T021c (FR-002) explicitly acknowledge plan-driven scope extensions/substitutions.
- **Revision Concerns (Data Flow)**: T021a, T021c, T020 now reside in Phase 2.5 (Data Prep) as prerequisites for US1 training.
- **Revision Concerns (Ablation Isolation)**: T037/T038 now emphasize 'soft' modifications and state isolation via model cloning.
- **Revision Concerns (Task Granularity)**: T001 split into atomic tasks for better executability. T021a added for feature computation. T021c added for Control Set. T039a/T039b added for ablation execution. T002 split into T002a/T002b. T032 split into T032a/T032b. T042a1/T042a2 consolidated.
- **Revision Concerns (Causal Language)**: T033 removed as gold-plating.
- **Revision Concerns (CI Status)**: T008a/T008b marked as Complete.
- **Revision Concerns (Threshold Config)**: T030 now reads threshold from `config.py` and uses 0.5/0.5 weights for score.
- **Revision Concerns (Model Copy)**: T037/T038 now explicitly state use of model copies to preserve base architecture.
- **Revision Concerns (Ordering)**: T009/T010 moved after T016; T037/T038 dependencies clarified; T034/T035 swapped.
- **Revision Concerns (Pruning Ratios)**: T013 now specifies 0.1, 0.2, 0.3 ratios.
- **Revision Concerns (Breaking Point)**: T030 now uses unified compression intensity score for sorting, but breaking point defined by AUC drop.
- **Revision Concerns (Formatting)**: T043a1-T043a4 consolidated into T043a.
- **Revision Concerns (Batch Size)**: T044a1 now has specific search range and stopping condition.
- **Revision Concerns (Logits Schema)**: T039a now specifies `logits_json` key and 1D array format.
- **Revision Concerns (FP32 Baseline)**: T014c added to ensure baseline AUC for SC-001/SC-004.
- **Revision Concerns (Control Set)**: T021c added to generate Control Set and explicitly override FR-002.
- **Revision Concerns (Comparative Analysis)**: T043 added to compare soft vs hard pruning results.
- **Revision Concerns (T035 Status)**: T035 status corrected to [ ] to match T034 [ ].
- **Revision Concerns (Test-First)**: T009/T010 moved before implementation tasks to reflect TDD workflow.
- **Revision Concerns (Version Pins)**: T002a now includes specific version pins.
- **Revision Concerns (Algorithm Details)**: T021a, T021c, T014a/b/c now include specific algorithmic details.
- **Revision Concerns (Error Handling)**: T014a/b/c now include explicit error handling for streaming.
- **Revision Concerns (Schema Definitions)**: T024, T039a now include precise schema definitions.
- **Revision Concerns (Dependency Clarity)**: T022/T023/T024, T041 now explicitly depend on T015/T039b.
- **Revision Concerns (File Separation)**: T021a/T021c now write to separate files to avoid race conditions.
- **Revision Concerns (Baseline Reference)**: T030 now explicitly references T014c as the baseline.
- **Revision Concerns (Parameter Verification)**: T037/T038 now include parameter count verification.

- [ ] T048 [P] **NEW**: Implement automated dataset integrity verification in `code/data/loader.py`. [Const-III] **MUST**: 1) Add a checksum validation step for `data/processed/subtle_cue_subset.parquet` against the manifest in `state/` before any training or inference begins. 2) If the checksum fails, raise a `DataIntegrityError` with a clear message indicating the file is corrupted or missing. 3) Log the verification result to `data/processed/integrity_log.txt`. **Rationale**: Addresses reviewer concern regarding "Data Hygiene" and ensures that downstream tasks (T014a/b/c, T022) do not proceed with corrupted or mismatched data artifacts. **Dependency**: Depends on T020.
- [ ] T049 [P] **NEW**: Implement dynamic batch size adjustment logic in `code/inference/runner.py`. [FR-004] **MUST**: 1) Start with a default batch size (e.g., a standard value commonly used in similar architectures).. 2) Monitor peak RAM usage during inference. 3) If RAM usage exceeds a predefined threshold, halve the batch size and retry. the current batch. 4) If RAM usage remains >6GB after 3 reductions, log a warning and skip the batch. 5) Record the final batch size used for each run in `data/processed/inference_config.yaml`. **Rationale**: Addresses reviewer concern regarding "Resource Exhaustion" (Edge Case) and ensures robustness against unexpected memory spikes on the constrained CI runner. **Dependency**: Depends on T022.
- [ ] T050 [P] **NEW**: Implement a "Model Fingerprinting" utility in `code/models/student.py`. [Const-V] **MUST**: 1) Generate a unique hash for each model checkpoint based on its architecture, quantization type, and pruning ratio. 2) Store this fingerprint in the checkpoint metadata. 3) Verify the fingerprint upon loading to ensure the model has not been inadvertently modified. 4) Log the fingerprint to `data/processed/model_fingerprints.csv`. **Rationale**: Addresses reviewer concern regarding "Model State Isolation" and ensures that ablation studies (T037/T038) are performed on distinct, unmodified base models. **Dependency**: Depends on T015.
- [ ] T051 [P] **NEW**: Implement a "Threshold Sensitivity" visualization in `code/analysis/sensitivity.py`. [FR-006] **MUST**: 1) Generate a heatmap plot showing the variation in FPR and FNR across the swept thresholds {0.01, 0.05, 0.1} for each model variant. 2) Output the plot to `data/processed/sensitivity_heatmap.png`. 3) Include a legend identifying each model variant by its compression level. **Rationale**: Addresses reviewer concern regarding "Sensitivity Analysis" (FR-006) and provides a clear visual representation of threshold stability. **Dependency**: Depends on T031.
- [ ] T052 [P] **NEW**: Implement a "Compression Impact" summary report in `code/analysis/robustness_curve.py`. [US-3] **MUST**: 1) Generate a markdown report `data/processed/compression_impact_summary.md` that synthesizes the findings from T030 (breaking point) and T032a (robustness curve). 2) Explicitly state the "safe deployment boundary" based on the 10% AUC drop threshold. 3) Include recommendations for edge deployment based on the results. **Rationale**: Addresses reviewer concern regarding "Research Output" (US-3) and ensures that the final deliverable clearly communicates the practical implications of the findings. **Dependency**: Depends on T030, T032a.