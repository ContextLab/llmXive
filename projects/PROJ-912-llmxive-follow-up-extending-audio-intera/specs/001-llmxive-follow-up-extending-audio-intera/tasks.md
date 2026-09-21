---
description: "Task list template for feature implementation"
---

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
- [ ] T004c [P] **NEW**: Implement configuration loader in `code/config.py` to load pruning ratios and other deferred parameters from `data/processed/config.yaml` at runtime, satisfying FR-001's "deferred" requirement. **Dependency**: T004.
- [X] T005 [P] Setup error handling and logging infrastructure in `code/utils/logger.py`
- [X] T006 [P] Implement schema validation utilities in `code/utils/validators.py` (for contracts)
- [X] T007 Create base model wrapper class in `code/models/student.py` (empty skeleton for StudentModel entity)
- [X] T008a Create `.github/workflows/ci.yml` with a job to run `pytest` and `lint` on the `code/` directory. **Status**: Complete. **Justification**: Required for Constitution Principle I (Reproducibility). CI enforces reproducibility by running tests on a fresh environment with pinned versions, preventing 'works on my machine' scenarios.
- [X] T008b Configure CI runner environment variables in `.github/workflows/ci.yml` to set `PYTHONUNBUFFERED=1`, `MAX_RAM_GB=7`, and `MAX_CORES=2`. **Status**: Complete. **Justification**: Required for Constitution Principle I.

---

## Phase 2.5: Data Preparation (Prerequisite for US1 & US2)

**⚠️ CRITICAL**: T021a/T021d must complete before T020; T020 must complete before T014a/b/c/e (US1 Training) can start.

**Note on Scope Expansion**: Tasks T021c/T021d implement a "Control Set" of non-subtle classes. This overrides FR-002's strict "subtle only" constraint to ensure valid binary AUC calculation (True Positive vs False Positive), as explicitly authorized by the Plan.md "Complexity Tracking" table and now reflected in the amended spec.md FR-002.

- [X] T021a [Shared] **NEW**: Define audio feature extraction criteria in `code/data/subtle_cue_features.py`. [Plan-Complexity-Tracking] **MUST**: 1) Define criteria: "Subtle Cue" classes are those with dominant frequency > 8kHz OR amplitude < -40dBFS. **Algorithm**: Use `torchaudio.transforms.MelSpectrogram` (n_mels=128, n_fft=2048, hop_length=512, window='hann') to compute frequency bins. 2) Calculate dominant frequency as the argmax of the energy spectrum. 3) Calculate amplitude as RMS over a **100ms window using a Hann window function with [deferred] overlap**. 4) **Output**: Generate a lightweight **class-configuration YAML** `data/processed/class_config_subtle.yaml` containing keys `subtle_classes` (list of int). **Dependency**: None. **Verification**: Ensure atomic write to `data/processed/` and distinct filename.
- [X] T021b [Shared] **NEW**: Execute feature extraction and generate `data/processed/class_config_subtle.yaml` from T021a logic. **Dependency**: T021a.
- [X] T021c [Shared] **NEW**: Define "Control Set" classes in `code/data/control_set_config.py`. [Plan-Complexity-Tracking] **MUST**: 1) Define "Control Set" classes as low-frequency, sustained amplitude classes. 2) **Plan Authorization**: Explicitly state in code comments that this task implements the "Control Set" requirement from Plan.md "Complexity Tracking" to support FR-003 (Binary AUC), overriding FR-002's "subtle only" constraint. 3) Map class names to dataset IDs using a hardcoded mapping table: `['engine hum', 'wind', 'rain', 'babbling', 'chainsaw', 'drilling', 'gunshot', 'jackhammer', 'siren', 'street music']`. 4) Generate `data/processed/class_config_control.yaml`. **Dependency**: None. **Verification**: Ensure atomic write to `data/processed/` and distinct filename.
- [X] T021d [Shared] **NEW**: Execute control set definition and generate `data/processed/class_config_control.yaml` from T021c logic. **Dependency**: T021c.
- [ ] T020 [Shared] Implement filtered data loader in `code/data/loader.py` using `datasets.load_dataset` with `streaming=True`. **MUST**: 1) Consume class definitions from `data/processed/class_config_subtle.yaml` (T021b) and `data/processed/class_config_control.yaml` (T021d) to determine which classes to stream. 2) **Stream-filter** on-the-fly (do NOT load full dataset or create large mask files) to avoid OOM. 3) **Recovery Strategy**: If streaming fails, attempt a local cached download; if that fails, raise a clear error. 4) **Output**: Generate `data/processed/subtle_cue_subset.parquet` with checksum. **Schema**: `columns: audio_path (str), class_id (int), label (int)`. 5) **Verify**: Assert file exists and checksum matches `state/`. 6) **Dataset Variability Watchdog (T048)**: Monitor valid sample count per class; if a subtle class has < 10 samples, log WARN and exclude from AUC calculation. **Dependency**: Depends on T021b, T021d. **Failure Mode**: Must fail loudly if config files are missing. <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Train Compressed Student Models (Priority: P1) 🎯 MVP

**Goal**: Instantiate, compress, and train **facebook/wavvec2-base-960h** (verified substitute for non-existent DeSTA2.5-Audio) into student variants with varying precision levels (FP32, INT8, INT4) and structural pruning using Knowledge Distillation, ensuring CPU-only execution.

**Independent Test**: Verify that distinct model checkpoints are saved with correct parameter counts, quantization types, pruning ratios, and training loss convergence (KD loss), and that they load without CUDA errors on a 2-core CPU runner.

**⚠️ CRITICAL ORDERING NOTE**: Phase 3 tasks (T014a/b/c/e) **MUST NOT** start until Phase 2.5 (T020) is fully complete. T014 tasks depend on BOTH the model compression path (T011->T014d) AND the data path (T020).

### Tests for User Story 1 (Test-First) ⚠️

> **NOTE**: These tests are written TDD-style and MUST be written first to FAIL. **Execution Order**: Implementation tasks (T011-T016) MUST follow these tests.

- [X] T009a [US1] Unit test for INT8 quantization logic in `tests/unit/test_compression.py`. **MUST**: Write `test_quantize_int8` function. **Input**: Pre-trained Wav2Vec2 model weights. **Output**: Quantized model state dict. **Assertion**: `assert model.dtype == torch.qint8` and `assert abs(student_int8_params - expected_params) < 0.01 `. **Dependency**: T011 (for model instance).
- [X] T009b [US1] Unit test for INT4 quantization logic in `tests/unit/test_compression.py`. **MUST**: Write `test_quantize_int4` function. **Input**: Pre-trained Wav2Vec2 model weights. **Output**: Quantized model state dict. **Logic**: If `torch.quint4` is supported, assert `model.dtype == torch.quint4`; else, `pytest.skip("torch.quint4 not supported on CPU")`. **Dependency**: T011 (for model instance).
- [X] T010 [US1] Integration test for model loading in `tests/integration/test_student_load.py`. **MUST**: Write `test_load_substitute_model` function. **Input**: Path to `facebook/wav2vec2-base-960h` checkpoint. **Output**: Loaded model object. **Assertion**: `assert model.device.type == 'cpu'` and `assert 'wav2vec2' in model.config.model_type`. **Dependency**: None.

### Implementation for User Story 1

- [X] T011 [US1] **Staged Implementation**: Implement teacher model loader in `code/models/teacher_loader.py`. [Plan-SpecGap] **MUST**: Load `facebook/wav2vec2-base-960h` as verified substitute for non-existent `DeSTA2.5-Audio` per Plan.md "Spec Gap Alert". **Justification**: Plan.md Summary and "Spec Gap Alert" section explicitly authorize this substitution for feasibility, ensuring the task satisfies the intent of FR-001 (loading a pre-trained Audio-Language Model) within the constraints of available public models. **Dependency**: None.
- [X] T012 [US1] Implement compression logic in `code/models/compress.py` using `torch.ao.quantization` for FP32, INT8, INT4 (Dynamic Quantization). **MUST**: Read quantization levels and pruning ratios from `code/config.py` (loaded by T004c) to support the "deferred" requirement of FR-001. **Dependency**: T011.
- [X] T013 [US1] Implement structural pruning logic in `code/models/compress.py`: Read pruning ratios from `code/config.py` (loaded by T004c) and apply **`torch.nn.utils.prune.l1_unstructured`** to remove weights using these specified ratios. **Output**: Save `pruned_model_{ratio}.pt` to `data/processed/`. **Dependency**: T011.
- [ ] T014d [US1] **NEW**: Implement a unified `KDTrainer` class in `code/models/compress.py` to encapsulate the common training logic used by T014a/b/c/e. **Dependency**: T012, T013.
- [ ] T014a [US1] Implement Knowledge Distillation training loop for **quantized** models in `code/models/compress.py` (CPU-only, small batch size). **MUST**: 1) Load teacher model from T011 artifact, 2) Load student model (quantized from T012), 3) **Stream input audio data** from `data/processed/subtle_cue_subset.parquet` (artifact from T020) for the forward pass (Combined Subtle + Control data), 4) Compute KD loss using `KDTrainer` (T014d) with `KD_ALPHA` and `KD_TEMP` from `config.py`, 5) **Error Handling**: Implement try/except blocks around streaming reads; log corrupted files to `data/processed/corrupted_files.log` and skip them; fail the job if >5% of files are corrupted. 6) Save `distillation_loss_curve_quant.csv`. **Dependency**: Depends on T020 artifact, T014d. **Note**: T020 must be complete before this starts. **Failure Mode**: Must fail loudly if `data/processed/subtle_cue_subset.parquet` is missing.
- [ ] T014b [US1] Implement Knowledge Distillation training loop for **pruned** models in `code/models/compress.py` (CPU-only, small batch size). **MUST**: 1) Load teacher model from T011 artifact, 2) Load student model (pruned from T013 artifact), 3) **Stream input audio data** from `data/processed/subtle_cue_subset.parquet` (artifact from T020) for the forward pass (Combined Subtle + Control data), 4) Compute KD loss using `KDTrainer` (T014d) with `KD_ALPHA` and `KD_TEMP` from `config.py`, 5) **Error Handling**: Implement try/except blocks around streaming reads; log corrupted files to `data/processed/corrupted_files.log` and skip them; fail the job if >5% of files are corrupted. 6) Save `distillation_loss_curve_pruned.csv`. **Dependency**: Depends on T013 and T020 artifacts, T014d. **Note**: T020 must be complete before this starts. **Failure Mode**: Must fail loudly if `data/processed/subtle_cue_subset.parquet` is missing.
- [ ] T014c [US1] **NEW**: Implement Knowledge Distillation training loop for **FP32 Baseline** model in `code/models/compress.py`. **MUST**: 1) Load teacher model from T011, 2) Load student model (FP32, no compression), 3) **Stream input audio data** from `data/processed/subtle_cue_subset.parquet` (T020) (Combined Subtle + Control data), 4) Compute KD loss using `KDTrainer` (T014d) with `KD_ALPHA` and `KD_TEMP` from `config.py`, 5) Save `distillation_loss_curve_fp32.csv`. **Purpose**: Provide the baseline AUC for SC-001/SC-004 breaking point calculation. **Dependency**: Depends on T020, T014d. **Note**: T020 must be complete before this starts.
- [ ] T014e [US1] **NEW**: Implement Knowledge Distillation training loop for **Combined (Pruned + Quantized)** models in `code/models/compress.py`. **MUST**: 1) Load teacher model from T011, 2) Load student model (Pruned from T013 + Quantized from T012), 3) **Stream input audio data** from `data/processed/subtle_cue_subset.parquet` (T020), 4) Compute KD loss using `KDTrainer` (T014d) as above, 5) Save `distillation_loss_curve_combined.csv`. **Purpose**: Address the matrix of combinations requirement in FR-001. **Dependency**: Depends on T012, T013, T020, T014d. **Note**: T020 must be complete before this starts.
- [ ] T015 [US1] Implement checkpoint saving in `code/models/compress.py` (save to `data/processed/` with metadata: bit-width, param count, pruning ratio). **Depends on T014a/T014b/T014c/T014e**.
- [X] T016 [US1] Add validation to ensure saved models load successfully on CPU without CUDA errors in `code/models/student.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Feature Robustness on Subtle Cue Dataset (Priority: P2)

**Goal**: Run inference on a curated subset of ESC-50/AudioSet containing high-frequency transients and low-amplitude events (Subtle Cue) AND a Control Set of non-subtle classes using all student models to measure AUC.

**Independent Test**: Execute evaluation script on a small sample, confirming AUC score calculation for each model variant against ground-truth labels, with valid True Positive/False Negative discrimination.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for data filtering logic in `tests/unit/test_filter.py`. **MUST**: Write `test_filter_subtle_classes` and `test_filter_control_classes` functions. **Input**: Sample dataset with class IDs. **Output**: Filtered list. **Assertion**: `assert filtered_ids == expected_subtle_ids` and `assert filtered_ids == expected_control_ids`.
- [ ] T019 [P] [US2] Unit test for AUC calculation and independence in `tests/unit/test_metrics.py`. **MUST**: 1) Generate synthetic logits and labels. 2) Calculate AUC using `sklearn.metrics.roc_auc_score`. 3) **Verify** that the CI runner environment is constrained to exactly 2 cores during measurement (via `os.cpu_count()` or CI env vars). 4) Compare against GitHub Actions constraints (≤6h, ≤7GB), logging a pass/fail status per FR-004 and SC-002. **Assertion**: `assert auc > 0.5` and `assert auc < 1.0`.

### Implementation for User Story 2

- [ ] T022 [US2] Implement CPU inference runner in `code/inference/runner.py` (Batch processing to fit RAM, handle OOM gracefully). **MUST**: 1) Wrap inference loop in `try/except MemoryError`. 2) If OOM, log model as "OOM" and continue. 3) **Resource Exhaustion Watchdog (T050)**: Log detailed memory stats on OOM and trigger a retry with smaller batch size if possible. 4) **Dependency**: T015, T020.
- [ ] T023 [US2] Implement metrics calculation in `code/inference/metrics.py` (AUC, latency, peak RAM usage). **MUST**: 1) Calculate AUC using `sklearn.metrics.roc_auc_score` on logits vs labels. 2) Measure latency using `time.perf_counter()`. 3) Measure peak RAM using **`psutil` (RSS)** to capture total process memory including C++ extensions. 4) **Verify** that the CI runner environment is constrained to exactly 2 cores during measurement. 5) Compare against GitHub Actions constraints (≤6h, ≤7GB), logging a pass/fail status per FR-004 and SC-002. 6) **Input**: Consume the combined dataset (Subtle + Control) from T020. 7) **Assertion**: Assert process completed within 6h and RAM < 7GB. **Output**: Return dict `{auc, latency_ms, ram_gb}`. **Dependency**: Depends on T015, T020.
- [ ] T024 [US2] Integrate inference and metrics to generate `data/processed/robustness_metrics.csv`. **MUST**: 1) Ensure schema: `model_id` (str), `auc` (float, 4 decimal places), `latency_ms` (float, 2 decimal places), `ram_gb` (float, 2 decimal places). 2) **Verify**: Assert CSV has correct columns and row count > 0. 3) **Input**: Consume the combined dataset (Subtle + Control) from T020. 4) **Assertion**: Assert total execution time < 6h. **Dependency**: Depends on T022, T023, T015. **Spec Amendment**: Explicitly state in code comments that this task implements the "Control Set" requirement from Plan.md "Complexity Tracking" to support FR-003 (Binary AUC), overriding FR-002's "subtle only" constraint.
- [X] T026 [US2] Add logging for inference performance and resource usage

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Robustness Curve and Sensitivity Report (Priority: P3)

**Goal**: Perform trend analysis to map the relationship between compression intensity and performance drop, including sensitivity analysis on decision thresholds.

**Independent Test**: Run analysis script, verifying trend plot (AUC vs. compression) and sensitivity report for threshold variations, with explicit "breaking point" value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for step-change detection in `tests/unit/test_analysis.py`. **MUST**: Write `test_step_change_detection` function. **Input**: List of AUC scores sorted by compression intensity. **Output**: Index of first drop > 10%. **Assertion**: `assert breaking_point_index == expected_index`.
- [ ] T028 [P] [US3] Unit test for sensitivity sweep in `tests/unit/test_sensitivity.py`. **MUST**: Write `test_threshold_sweep` function. **Input**: Logits and labels. **Output**: Dict of FPR/FNR for thresholds {0.01, 0.05, 0.1}. **Assertion**: `assert len(results) == 3` and `assert all(fpr >= 0 for fpr in results.values())`.

### Implementation for User Story 3

- [ ] T029 [US3] Implement robustness curve analysis in `code/analysis/robustness_curve.py`. **MUST**: 1) Consume `robustness_metrics.csv` from T024, 2) Output raw correlation data (bits/params vs AUC) to `data/processed/correlation_data.json` for consumption by T030. **Schema**: `correlation_data.json` MUST contain a list of objects: `[{ "model_id": str, "bit_width": int, "auc": float, "params": int }]`. **Dependency**: Depends on T024.
- [ ] T030 [US3] Implement step-change detection in `code/analysis/robustness_curve.py`. **MUST**: 1) Consume `correlation_data.json` from T029, 2) Identify the "breaking point" where relative AUC drop exceeds **>10%** (read threshold from `config.py`). **Algorithm**: Compute a `compression_intensity_score` for each model: `score = (- bits/32) * 0.5 + (1 - params/baseline_params) * 0.5` (weights read from `config.py` as `WEIGHTS_SCORE`), sort by `compression_intensity_score` ascending, compute pairwise AUC drop, and flag the first instance where drop > threshold. 3) **Verify**: Assert and output `threshold_violated` flag (true if drop > 10%) in `data/processed/breaking_point.json` containing bit-width, drop %, and `threshold_violated` flag. **Note**: The `baseline_params` MUST be the parameter count of the **Distilled FP32 Student (T014c)**, not the Teacher. 4) **Output Requirement**: Explicitly identify the specific compression level (e.g., "INT4") as the breaking point in the JSON. **Dependency**: Depends on T029.
- [ ] T031 [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py`. **MUST**: 1) Sweep thresholds over the **fixed set {0.01, 0.05, 0.1}** as mandated by FR-006 and SC-003. 2) Report the variation in false-positive and false-negative rates for each model variant. **Dependency**: Depends on T024.
- [ ] T032a [US3] Generate AUC vs. Compression plot in `code/analysis/robustness_curve.py`. **MUST**: 1) Use `matplotlib.pyplot` to create a scatter plot. 2) X-axis: `bit_width`, Y-axis: `auc`. 3) Output `data/processed/robustness_curve.png`. 4) **Verification**: Assert file exists and contains > 0 pixels. **Dependency**: Depends on T029/T030.
- [ ] T032b [US3] Generate sensitivity report in `code/analysis/sensitivity.py`. **MUST**: 1) Output `data/processed/sensitivity_report.csv` with **schema**: `threshold`, `fpr`, `fnr`, `auc`, `model_id`. **Dependency**: Depends on T031.
- [X] T033 [US3] **REMOVED** (See concern coverage-727da8d5).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Execute Ablation Study on Architectural Components (Priority: P4)

**Goal**: Systematically vary architectural components (freezing attention, pruning FFN) while maintaining constant compression to isolate contributions.

**Independent Test**: Run ablation script, confirming distinct metrics for each configuration with no cross-contamination.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US4] Unit test for ablation config parsing in `tests/unit/test_ablation.py`. **MUST**: Write `test_parse_ablation_config` function. **Input**: JSON config string. **Output**: Parsed dict. **Assertion**: `assert parsed['freeze_attention'] == True`.
- [ ] T035 [P] [US4] Integration test for ablation execution in `tests/integration/test_ablation_run.py`. **MUST**: Write `test_ablation_execution` function. **Input**: Model and config. **Output**: Metrics dict. **Assertion**: `assert 'auc' in metrics`. **Dependency**: T034.

### Implementation for User Story 4

- [ ] T036 [P] [US4] Implement ablation configuration parser in `code/analysis/ablation.py` (Config for freeze attention, prune FFN). **MUST**: Define keys `config.ablation.freeze_heads` and `config.ablation.prune_ffn_layers` to specify selected head indices and final feed-forward network layers for ablation.
- [X] T036b [P] [US4] Implement model cloning utility in `code/models/student.py`: Create a function `clone_model(model)` that returns a deep copy of the model weights to ensure state isolation.
- [ ] T037 [US4] Implement component freezing logic in `code/models/student.py`. [Plan-Deviation-SoftPrune] **MUST**: **Soft Pruning (Structural Isolation)**: Set `requires_grad=False` on specific early attention head parameters (defined by `config.ablation.freeze_heads = [0, 1]`) AND **mask** those parameters (set weights to zero) in the computation graph to ensure no gradients flow, isolating their contribution while maintaining the original architecture's parameter count. **Plan Authorization**: Explicitly state in code comments that this task implements the "Soft Pruning" requirement from Plan.md "Complexity Tracking" as a valid proxy for structural pruning to satisfy FR-007. **Justification**: This isolates architectural contribution (feature loss) without structural removal, which is necessary for CPU-only execution where structural removal might be brittle. **Verification**: Count parameters before and after masking to ensure invariance; log the count to `data/processed/param_counts.csv`. **Dependency**: T036b.
- [ ] T038 [US4] Implement component pruning logic in `code/models/student.py`. [Plan-Deviation-HardPrune] **MUST**: **Hard Pruning (Structural Removal)**: Use `torch.nn.utils.prune.remove` to **structurally remove** specific late feed-forward layers (defined by `config.ablation.prune_ffn_layers = [-1, -2]`) to reduce parameter count and measure information loss. **Algorithm**: Apply `l1_unstructured` pruning to the specified layers, then call `prune.remove` to finalize the removal. **Plan Authorization**: Explicitly state in code comments that this task implements the "Hard Pruning" requirement from Plan.md "Complexity Tracking" to satisfy FR-007's intent of parameter reduction. **Verification**: Count parameters before and after removal to ensure reduction; log the count to `data/processed/param_counts.csv`. **Dependency**: T036b.
- [ ] T039a [US4] **NEW**: Implement re-execution of inference pipeline on ablated models in `code/analysis/ablation.py`. **MUST**: 1) Load ablated models from T037/T038, 2) Run inference on `data/processed/subtle_cue_subset.parquet` (T020 artifact) using the inference runner from T022. 3) Output intermediate logits to `data/processed/ablation_logits.parquet`. **Schema**: `ablation_logits.parquet` MUST contain columns `model_id`, `config_id`, `logits_json` (JSON string of a D array of floats, **formatted with decimal places using `'{:.6f}'.format(x)` and `json.dumps(..., allow_nan=True)` to handle NaN/Inf**), `label` (int). **Dependency**: Depends on T037, T038, T020, T022.
- [ ] T039b [US4] **NEW**: Implement recalculation of metrics for ablated models in `code/inference/metrics.py`. **MUST**: 1) Consume `ablation_logits.parquet` from T039a, Evaluate AUC, latency, and peak RAM for each ablated configuration (re-measuring on a constrained CPU environment to satisfy Constitution Principle VI), 2) Output to `data/processed/ablation_metrics.csv`. **Schema**: `ablation_metrics.csv` MUST contain columns `config_id`, `auc`, `latency_ms`, `ram_gb`. **Dependency**: Depends on T039a.
- [ ] T040 [US4] Integrate ablation with inference runner in `code/analysis/ablation.py`. **MUST**: 1) Load ablation configs (T036), 2) Execute T037/T038 logic to create ablated models, 3) Call T039a/T039b to run inference and calculate metrics. **Dependency**: Depends on T036, T037, T038, T039a, T039b.
- [ ] T041 [US4] Generate ablation results in `data/processed/ablation_results.csv`. **MUST**: 1) Transform `ablation_metrics.csv` (T039b) by adding `model_id` and `config_type` columns. 2) **Verify**: Assert CSV has correct columns and row count > 0. **Dependency**: Depends on T039b.
- [X] T042a [US4] Add validation to verify gradients are zeroed or layers masked as expected. **MUST**: 1) Iterate over model parameters. 2) **Assertion**: `assert param.grad is None` for frozen parameters. 3) **Assertion**: `assert torch.allclose(param.grad, torch.zeros_like(param.grad))` for masked parameters. 4) Log results to `data/processed/gradient_check.log`.
- [ ] T042b [US4] **NEW**: Implement comparative analysis in `code/analysis/ablation.py`. [SC-005] **MUST**: 1) Load `ablation_results.csv` (T041) and `robustness_metrics.csv` (T024). 2) Compare the "soft pruning" results (constant params) against the "hard pruning" results (variable params from T013/T024) to address the metric gap in SC-004 (compression intensity vs performance drop). Generate `data/processed/ablation_comparison_report.md` describing the joint relationships and isolating the contribution of architectural components to feature loss. **Schema**: Report must include sections: "Joint Relationships", "Component Contribution", "Comparison Summary". **Dependency**: Depends on T041, T024.
- [ ] T043 [US4] **NEW**: Implement "Collinearity Check" in `code/analysis/ablation.py`. **MUST**: 1) After generating `ablation_results.csv`, calculate the correlation coefficient between "Freeze Attention" and "Prune FFN" performance drops. 2) If correlation > 0.8, append a warning to `ablation_comparison_report.md` stating "High collinearity detected; independent causal effects cannot be claimed." 3) Output the correlation matrix to `data/processed/collinearity_matrix.json`. **Dependency**: Depends on T041.
- [ ] T049 [P] [US4] **NEW**: Implement unit tests for `code/analysis/ablation.py` edge cases. **MUST**: 1) Test invalid config. 2) Test model cloning isolation. **Assertion**: `assert cloned_model is not original_model`. **Dependency**: T041. (Moved from Pending to Phase 6 integration)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Generate API documentation for `code/models/compress.py` and `code/analysis/robustness_curve.py`. **MUST**: 1) Use `sphinx-apidoc` to generate docs in `docs/api/`, 2) Verify `docs/api/index.html` exists.
- [X] T045 [P] Update `quickstart.md` with the specific "Subtle Cue" + "Control Set" data flow
- [X] T046 [P] Format all Python files in `code/` using black and ruff. **MUST**: 1) Run `black code/` and `ruff check --fix code/`, 2) Verify no formatting errors remain.
- [X] T047 [P] Verify streaming efficiency and chunking logic in `code/data/loader.py`
- [ ] T048 [P] **NEW**: Implement unit tests for `code/data/loader.py` edge cases. **MUST**: 1) Test empty stream. 2) Test corrupted file handling. 3) Test missing config file. **Assertion**: `assert raises(DataIntegrityError)`. **Dependency**: T020. (Moved from Pending to Phase 2.5/3 integration)
- [ ] T050 [P] **NEW**: Verify all outputs against schemas in `contracts/`. **MUST**: 1) Verify `data/processed/robustness_metrics.csv` and `data/processed/ablation_results.csv`, 2) Use `jsonschema` tool, 3) Exit code 0 if all schemas match. (Moved from Pending to Phase 4 integration)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Data Preparation (Phase 2.5)**: Depends on Foundational (Phase 2) - BLOCKS US1 and US2
- **User Stories (Phase 3+)**: All depend on Data Preparation (Phase 2.5) completion
 - US1 (P1) must complete before US2 (P2) can fully utilize models (Data flow: T020 is prerequisite for T014a/b/c/e (US1 Training))
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
- **Distillation**: T014a/T014b/T014c/T014e MUST use teacher logits for loss AND stream real audio data from T020; standard supervised loss is insufficient.
- **Ablation**: T037/T038 must be executed with a fresh model instance per configuration (via T036b) to prevent state leakage between "freeze" and "mask" runs.
- **Metrics**: T019 MUST ensure no internal weights are accessed during AUC calculation. T023 MUST verify 2-core constraint.
- **Overrides**: T011 (FR-001) and T021c (FR-002) explicitly acknowledge plan-driven scope extensions/substitutions.
- **Revision Concerns (Data Flow)**: T021a, T021c, T020 now reside in Phase 2.5 (Data Prep) as prerequisites for US1 training.
- **Revision Concerns (Ablation Isolation)**: T037/T038 now emphasize 'soft' modifications and state isolation via model cloning.
- **Revision Concerns (Task Granularity)**: T001 split into atomic tasks for better executability. T021a added for feature computation. T021c added for Control Set. T039a/T039b added for ablation execution. T002 split into T002a/T002b. T032 split into T032a/T032b. T009 split into T009a/T009b. T045 split into T045a/T045b.
- **Revision Concerns (Causal Language)**: T033 removed as gold-plating.
- **Revision Concerns (CI Status)**: T008a/T008b marked as Complete.
- **Revision Concerns (Threshold Config)**: T030 now reads threshold from `config.py` and uses 0.5/0.5 weights for score.
- **Revision Concerns (Breaking Point)**: T030 now uses unified compression intensity score for sorting, but breaking point defined by AUC drop.
- **Revision Concerns (Pruning Ratios)**: T013 now specifies 0.1, 0.2, 0.3 ratios (read from config).
- **Revision Concerns (Edge Cases)**: T020 explicitly addresses the "Dataset Variability" edge case by implementing error handling and logging.
- **Revision Concerns (Resource Exhaustion)**: T022 explicitly addresses the "Resource Exhaustion" edge case by implementing memory error handling.
- **Revision Concerns (Collinearity)**: T043 addresses the "Collinearity in Predictors" edge case by requiring descriptive reporting of joint relationships.
- **Revision Concerns (Failing Loaders)**: Explicitly stated in T020 that loader must fail loudly.
- **Revision Concerns (Control Set Justification)**: T021c/T021d/T024 now explicitly cite Plan.md 'Complexity Tracking' for the FR-002 override.
- **Revision Concerns (Model Substitution Justification)**: T011 now explicitly cites Plan.md 'Spec Gap Alert' for the FR-001 override.
- **Revision Concerns (Soft Pruning Justification)**: T037/T038 now explicitly cite Plan.md 'Complexity Tracking' for the FR-007 override.
- **Revision Concerns (Ordering)**: T014d moved before T014a/b/c. T022, T023, T039a dependencies updated to include T020/T022. T009/T010 contradictions resolved. T014a/b/c explicitly note dependency on T020 completion.
- **Revision Concerns (Executability)**: T019, T023, T032a, T009, T010, T018, T027, T028, T034, T035, T045, T042a updated with specific inputs, outputs, and assertions. T013 updated with `l1_unstructured`. T037/T038 updated with explicit layer indices.
- **Revision Concerns (Config Loading)**: T004c added for dynamic config loading; T013 updated to read from config.
- **Revision Concerns (Combined Training)**: T014e added for Pruned+Quantized training.
- **Revision Concerns (RAM Measurement)**: T023 updated to use `psutil` for RSS.
- **Revision Concerns (JSON Serialization)**: T039a updated with `allow_nan=True` and explicit formatting.
- **Revision Concerns (Layer Indices)**: T037/T038 updated with explicit layer indices and config keys.
- **Revision Concerns (Pruning Algorithm)**: T013 updated with `l1_unstructured`.
- **Revision Concerns (Baseline Params)**: T030 updated to use Distilled FP32 Student as baseline.
- **Revision Concerns (Test Dependencies)**: T009a/b updated to depend on T011.
- **Revision Concerns (Pending Tasks)**: T048, T049, T050 integrated into phases; removed 'Pending' section.
- **Revision Concerns (Spec Amendment)**: FR-002 amended in spec.md to reflect Control Set inclusion.
- **Revision Concerns (Deferred Config)**: T012/T013 updated to read from `config.py`.
- **Revision Concerns (4-bit Quantization)**: T009b updated to skip if unsupported.
