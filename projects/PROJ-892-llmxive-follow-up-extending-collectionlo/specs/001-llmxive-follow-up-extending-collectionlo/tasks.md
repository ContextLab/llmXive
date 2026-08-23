---
description: "Task list template for feature implementation"
---

# Tasks: Quantization Robustness of Multi-Effect LoRA Adapters

**Input**: Design documents from `/specs/001-lora-quantization-robustness/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Pre-Phase Gate: Plan Ratification

**Purpose**: Ensure the project plan is legally ratified against the Constitution before any implementation begins.

- [X] T034a [Gate] Create `code/verify_plan.py` script that reads `plan.md` and checks for the presence of "Amendment 001" or "Bayesian Hierarchical Model" text. If found, write `{"status": "RATIFIED", "timestamp": "<now>"}` to `state/ratification.yaml`. If not found, raise `ValueError`. This task is the mechanism that transitions the plan from "Pending" to "Ratified". **Dependencies: None**

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, validation, and basic structure

- [X] T001a [P] Create `code/` directory at repository root
- [X] T001b [P] Create `data/` directory at repository root
- [X] T001c [P] Create `state/` directory at repository root
- [X] T001d [P] Create `tests/` directory at repository root
- [X] T002 [P] Create empty `__init__.py` files in `code/`, `data/`, `state/`, `tests/` to ensure Python package recognition

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Note**: T009a (Key Discovery) and T016 (Quantization) must run SEQUENTIALLY to avoid OOM on the 16GB runner. Do NOT run them in parallel.

- [X] T003 [P] Initialize Python project with pinned dependencies in `code/requirements.txt` (must include: `torch`, `diffusers`, `transformers`, `clip`, `lpips`, `numpy`, `pandas`, `pymc`, `arviz`, `scikit-learn`)
- [ ] T004 [P] Create `code/config.yaml` containing the EXACT, FIXED list of test prompts and seed values to ensure reproducibility. **YAML Schema**:
  ```yaml
  prompts:
    - "oil painting"
    - "watercolor"
    - "cyberpunk"
    - "pencil sketch"
    - "ink wash"
    - "acrylic"
    - "charcoal"
    - "pastel"
    - "digital art"
    - "concept art"
  seeds:
    - 42
    - 123
    - 456
    - 789
    - 101112
  ```
  This file is the single source of truth for all generation tasks (FR-009, FR-003). **Dependencies: T034a** (Note: This task depends on the Pre-Phase Gate T034a to ensure the plan is ratified before defining experimental parameters. The task description explicitly defines the prompt list and seed values to ensure self-containment and reproducibility.) **Validation**: The task MUST include a logic step to verify that the hardcoded prompt list covers at least 3 distinct effect categories (e.g., texture, lighting, medium) as mandated by the research hypothesis (FR-009). If diversity is insufficient, the task must raise a `ValueError` and halt.
- [X] T006 [P] Implement `code/state_manager.py` to handle SHA-256 hashing of artifacts and `state/artifacts.yaml` updates (FR-013)
- [ ] T007b-1 [P] Implement logic in `code/data_loader.py` to download the CollectionLoRA adapter from the verified public HuggingFace repository `stabilityai/collection-lora`. Logic MUST: 1. Verify the repository exists using `huggingface_hub.list_repo_files`. 2. Attempt to download the specific file `adapter_fp.safetensors` (or the first available `.safetensors` file if the exact name is not found) to `data/models/adapter_fp16.safetensors`. 3. If the primary repository does not exist or the file cannot be found, implement logic to construct a synthetic adapter by merging 5 verified single-effect LoRAs (e.g., from `stabilityai/diffusers` examples or other public single-effect adapters) to satisfy Spec Assumption 011. The merge logic must be deterministic and logged. 4. **Fallback (Synthetic Construction)**: If both primary and secondary sources fail, raise a `ValueError` with the message "Failed to download or construct CollectionLoRA adapter from verified source. Aborting." to enforce a "Fail Loudly" policy. **Dependencies: T003** (Note: The known hash for verification is defined as a constant in `code/config.yaml`. No fallback to synthetic data is permitted unless the primary source is missing, in which case the synthetic construction logic MUST be used.)
- [ ] T007b-2 [P] Implement logic in `code/data_loader.py` to compute the SHA-256 hash of `data/models/adapter_fp16.safetensors` and record it in `state/artifacts.yaml` (FR-013, FR-010). **Dependencies: T007b-1**
- [X] T007c [P] Implement logic in `code/data_loader.py` to download the base model (Stable Diffusion 1.5) from `runwayml/stable-diffusion-v1-5` and compute its SHA-256 hash, recording it in `state/artifacts.yaml` (FR-013). If the download fails from the primary source, attempt a verified secondary mirror. If both fail, raise a `ValueError` with the message "Failed to download base model from primary source. Aborting." **Dependencies: T003**
- [X] T007d [P] Implement logic in `code/data_loader.py` to validate that the downloaded adapter contains at least 5 distinct effects. Use regex `r"lora_unet_.*_(.+)_lora"` to identify unique effect prefixes. If an insufficient number of unique prefixes are found, raise `ValueError`. **Dependencies: T007b-2**
- [X] T008a [P] [Rev] Implement `code/error_handler.py` with a function `handle_memory_error(e: MemoryError)` that logs "Quantization Failure" and returns a skip flag. **Dependencies: T003**
- [X] T008b [P] [Rev] Integrate `handle_memory_error` into `code/main.py` wrapper logic to catch in-process `MemoryError` exceptions and handle subprocess Exit Code 137 (SIGKILL) by logging "Quantization Failure" and gracefully skipping the affected quantization level (FR-008). **Dependencies: T008a**
- [ ] T009a [Foundational] Implement `code/data_loader.py` function to perform Key Discovery & Extraction. **Logic**: 1. Iterate over the state dict keys of `data/models/adapter_fp16.safetensors` to identify per-effect LoRA weight matrices using regex patterns (e.g., `r"lora_unet_.*_(.+)_lora"`). 2. If no specific pattern matches, use a generic key-splitting logic based on known CollectionLoRA naming conventions. 3. **Validation**: If no matrices are found, log a warning, set a flag `rank_extraction_failed = True`, and explicitly set the hypothesis status for FR-007 to "Not Testable" in `data/subspace_ranks.json`. Do NOT raise a hard error here. **Dependencies: T007d**
- [ ] T009b [Foundational] Implement `code/data_loader.py` function to perform SVD Computation & Rank Calculation. **Logic**: 1. If `rank_extraction_failed` is True (from T009a), set all subspace ranks to a constant value (e.g., 0) and flag the FR-007 hypothesis test as "Not Testable" in `data/subspace_ranks.json`. 2. Otherwise, compute Singular Value Decomposition (SVD) on each extracted matrix to determine effective subspace rank. 3. **Validation**: Ensure at least 5 distinct effects are found. If not, raise `ValueError`. 4. **Tolerance Verification**: Implement a validation step to verify the `tolerance` threshold against the noise floor of the LoRA weights (e.g., by checking the decay of singular values). If the threshold is arbitrary and unjustified, log a warning and adjust dynamically or document the justification. 5. Save the computed subspace ranks to `data/subspace_ranks.json`. **Output Schema**: `{"effect_name": rank_value,...}`. 6. **Versioning**: Immediately compute the SHA-256 hash of `data/subspace_ranks.json` and record it in `state/artifacts.yaml` (FR-010, FR-013). **Dependencies: T009a**
- [X] T009c [P] [Rev] Implement logic to load the subspace ranks from `data/subspace_ranks.json` (produced by T009b), validate the tolerance threshold used, and ensure the file is checksummed in `state/artifacts.yaml` (FR-010, FR-007). **Dependencies: T009b**
- [X] T009d [P] Create `code/metrics.py` stub with imports for CLIP, LPIPS, and NumPy. **Dependencies: T003**
- [ ] T016 [Foundational] Implement `code/data_loader.py` function to apply zero-shot post-training quantization (higher-precision floating-point to lower-precision integer formats) using `torch.ao.quantization` with **dynamic** quantization mode on CPU for the LoRA weight matrices only. **Config**: Use `torch.ao.quantization.get_default_qconfig("qnnpack")` or equivalent for dynamic quantization. **Logic**: 1. Create `data/quantized/` directory if missing. 2. Quantize *only* the LoRA weight matrices (not the base model) using dynamic quantization. 3. **Constraint**: NO calibration data, NO fine-tuning, NO gradient updates. 4. **Integrity Check**: Immediately after quantization, generate a small sample (1 image) and compute LPIPS and cosine similarity. If LPIPS > 0.8 or similarity < 0.1, log "Quantization Failure: Catastrophic Collapse" and mark the level as "Not Testable" (FR-002, FR-008). 5. Serialize the quantized state dict to `data/quantized/adapter_int8.safetensors` and `data/quantized/adapter_int4.safetensors` using a custom format that preserves quantization parameters. 6. **Verification**: Load the resulting quantized adapter to verify it loads successfully on CPU and shapes match before saving. 7. **Error Handling**: Wrap the quantization logic in a `try/except` block. If `torch.ao.quantization` backend is unavailable (e.g., `RuntimeError`), log "Backend Unavailable" and skip the specific quantization level without crashing the pipeline (FR-008). 8. **Fallback**: If quantization produces invalid weights (detected by Integrity Check), attempt to skip the level and mark as "Not Testable" rather than crashing. **Output**: Save quantized adapters to `data/quantized/adapter_int8.safetensors` and `data/quantized/adapter_int4.safetensors` (FR-002). **Dependencies: T007b-2, T009b** (Note: Run sequentially after T009b to avoid OOM; this task is NOT marked [P] to enforce sequential execution.)
- [X] T039 [P] [Rev] Create `code/validate_data.py` script to verify that the loaded CollectionLoRA adapter contains at least 5 distinct effects (identified by unique key prefixes in the state dict) as required by Assumption 011, failing fast if the threshold is not met. **Dependencies: T007b-2**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.
**Gate**: Phase 3 requires T039 to pass (validation). T016 (Quantization) can run in parallel with Phase 3 once T007b-2 is done.

---

## Phase 3: User Story 1 - Baseline Fidelity Measurement (Priority: P1) 🎯 MVP

**Goal**: Generate FP16 baseline images, extract CLIP embeddings, and compute cosine similarity to establish ground truth.

**Independent Test**: Can be fully tested by running the generation pipeline on the CPU-only runner with FP16 weights and verifying `data/results.csv` contains multiple rows with non-null similarity scores.

### Implementation for User Story 1

- [ ] T010b [US1] Implement `code/data_loader.py` function to load the verified FP16 adapter (`data/models/adapter_fp16.safetensors` from T007b-1) and base model (from T007c) into CPU memory. **Logic**: Use `device_map='cpu'` and `torch_dtype=torch.float16` when calling `from_pretrained` or `load_state_dict` to ensure models are loaded on CPU and not GPU (FR-001). **Dependencies: T007b-2, T007c**
- [X] T011 [US1] Implement `code/generator.py` function to generate images using the FIXED prompt list from `code/config.yaml` (explicitly defined seeds and prompts) with the FP16 adapter loaded in T010b (FR-003, FR-009). **Dependencies: T010b, T004** (Note: T011 depends on T004 to load the prompt list and seeds from `code/config.yaml`.)
- [X] T011c [US1] Implement `code/generator.py` function to generate and save a set of "FP16 ReferenceImages" for *ALL* 10 effect prompts defined in T004, using **ALL 5 seeds** from `code/config.yaml`. **Configuration**: Use `resolution=512x512`, `sampler="euler"`, `steps=20`. Save to `data/references/fp16_refs/`. Organize these into a lookup table keyed by effect category and seed. These are required for CESR calculation in US2 (FR-011, US-2). **Dependencies: T011** (Note: These reference images are generated for all 5 seeds to ensure statistical validity for CESR calculation across all quantized generations.)
- [X] T011d [US1] Implement `code/data_loader.py` function to organize `data/references/fp16_refs/` into a lookup table keyed by effect category and seed (e.g., `{"oil_painting": {42: img1, 123: img2,...}}`) to enable target-exclusion logic in T018. **Dependencies: T011c**
- [X] T012 [US1] Implement `code/metrics.py` function to extract CLIP image embeddings and compute cosine similarity with prompt text embeddings (FR-004)
- [X] T013 [US1] Implement `code/metrics.py` function to compute LPIPS distance between generated FP16 images (from T011) and the FP16 ReferenceImages (from T011c). **Purpose**: This is a self-consistency check for US1 to verify the generation pipeline is functional, distinct from the FR-005 metric (Quantized vs FP16) computed in T019. **Dependencies: T011, T011c** (Note: This task computes a self-consistency check for US1, not the primary LPIPS metric for quantization comparison.)
- [ ] T014a [US1] Implement `code/main.py` logic to run FP16 generation loop, compute metrics, and save initial `data/results.csv` and `data/generated/` images. **CSV Schema**: The `results.csv` file MUST have the following columns: `prompt`, `seed`, `quantization_level`, `similarity_score`, `lpips_distance`, `cesr_score`, `image_path`. **Dependencies: T013, T012, T011, T011c, T009b, T009a** (Note: Explicitly depends on T011, T011c, T009b, and T009a to ensure images, references, and subspace ranks are available.)
- [ ] T014b [US1] Implement `code/main.py` logic to aggregate results and verify SHA-256 hashes of generated images in `state/artifacts.yaml`. **Dependencies: T014a**
- [X] T015 [US1] Add logging for baseline generation steps and verify SHA-256 hashes of generated images in `state/artifacts.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantization Impact Analysis (Priority: P2)

**Goal**: Apply INT8/INT4 quantization, generate images, and measure concept adherence drop and concept bleeding (CESR).

**Independent Test**: Can be fully tested by running the quantization pipeline on the CPU runner, generating images, and verifying the delta in cosine similarity is recorded in `data/results.csv`.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/generator.py` function to generate images for INT8 and INT4 adapters using the same prompt list (FR-003). **Dependencies: T016**
- [X] T018 [US2] Implement `code/metrics.py` function to compute Cross-Effect Similarity Ratio (CESR) by comparing quantized output embeddings against the FP16 ReferenceImages (from `data/references/fp16_refs/` produced by T011c) for *other* effect prompts. **Logic**: Load lookup table from T011d, filter out the target prompt using string equality (`if ref.effect != target_prompt`), and compute cosine similarity. **Explicit Constraint**: Ensure the reference set is constructed from *distinct* effect prompts (excluding the current target) to prevent self-similarity bias (FR-011). If a reference image for the target prompt is missing, log a warning and skip that specific comparison. **Negative Control**: Generate or load a "Distractor Reference" set (random noise or unrelated images) and compute "Distractor CESR" against these to validate that the metric is not detecting random semantic distance. Log the "Distractor CESR" alongside the primary CESR. **Dependencies: T011d, T017, T016**
- [X] T019 [US2] Implement `code/metrics.py` function to compute LPIPS distance between quantized outputs and FP16 baseline outputs (FR-005). **Dependencies: T011** (Note: This task computes the primary LPIPS metric for quantization comparison, using the images generated by T011, not the metric from T013.)
- [ ] T020a [US2] Implement `code/main.py` logic to run quantized generations, handle `MemoryError` per level (using logic from T008b), compute deltas, and append to `data/results.csv`. **Dependencies: T018, T019, T014a, T011c, T009b** (Note: Explicitly depends on T014a, T011c, and T009b to ensure baseline images, references, and subspace ranks are available.)
- [ ] T020b [US2] Implement `code/main.py` logic to aggregate quantization results and verify SHA-256 hashes of quantized weights and generated images. **Dependencies: T020a**
- [X] T021 [US2] Implement logic to load per-effect LoRA subspace rank from `data/subspace_ranks.json` (produced by T009b) and prepare data for correlation analysis. **Input**: `data/subspace_ranks.json` (FR-010)
- [X] T022 [US2] Add logging for quantization steps and verify SHA-256 hashes of quantized weights and generated images

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bayesian Statistical Analysis (Priority: P3)

**Goal**: Perform Bayesian Hierarchical Model analysis and correlate subspace rank with concept bleeding.

**Independent Test**: Can be fully tested by running the statistical analysis script on `data/results.csv` and verifying `data/analysis_results.json` contains posterior distributions and correlation coefficients. Note: This task depends on the completion of Phase 3 and Phase 4 to ensure full dataset availability.

### Implementation for User Story 3

- [ ] T023 [P] [US3] Implement `code/statistical_analysis.py` to load `data/results.csv`, structure data for Bayesian Hierarchical Model, and EXPLICITLY extract the 'Effect' grouping variable. **Schema Validation**: The task MUST validate that `data/results.csv` contains all required columns (including 'subspace_rank' from T009b). If columns are missing or data is empty, the task must abort gracefully with a "Not Testable" status for the correlation analysis. **Output Structure**: Create a pandas DataFrame with columns: `effect_id`, `similarity_score`, `quantization_level`, `seed`, `subspace_rank`. This structure is required by `pymc`/`bambi` (FR-006, FR-012). **Dependencies: T014b, T020b, T009b, T007d, T009a** (Note: Explicitly depends on T009b, T007d, and T009a to ensure subspace rank data and effect validation are available.)
- [X] T024 [US3] Implement `code/statistical_analysis.py` to define and run the Bayesian Hierarchical Model using `pymc`/`bambi` with PARTIAL POOLING. **Priors**: Weakly informative `Normal(0, 1)` for fixed effects, `HalfNormal(0.5)` for random effects (Plan Section 3.2). Test quantization effects and mitigate small sample size risks (FR-006, FR-012, Plan Section 5). **Model Formula**: `similarity_score ~ quantization_level + subspace_rank + (1 | effect_id)`. **Output**: Must output posterior distributions AND the posterior width for the `Quantization_Effect` coefficient to enable FR-014 flagging (FR-006, FR-012). **Dependencies: T023** (Note: Model formula includes `subspace_rank` as a covariate to explicitly model the correlation.)
- [X] T025 [US3] Implement `code/statistical_analysis.py` to compute correlation between per-effect LoRA subspace rank (from `data/subspace_ranks.json` via T009b) and mean concept bleeding magnitude (derived from T018), explicitly testing significance via the Bayesian posterior distribution and reporting credible intervals (FR-007). **Dependencies: T009b, T018, T014b, T020b** (Note: The dependency on T024 is for the Bayesian correlation significance testing, not the correlation calculation itself.)
- [ ] T026 [US3] Implement `code/statistical_analysis.py` to read posterior width from T024 output; if width > 0.2 for the `Quantization_Effect` coefficient, flag the result as "Underpowered" in `analysis_results.json`. **Decision Rule**: 1. If HDI of quantization effect excludes zero, it is significant. 2. If width > 0.2, flag as underpowered (FR-014). 3. **ESS Check**: Calculate the Effective Sample Size (ESS) for the posterior distribution of the correlation coefficient. If ESS < 200, flag the result as "Unstable Posterior". 4. **Constraint**: If "Underpowered" or "Unstable Posterior" is flagged, the result MUST NOT be labeled as "Significant", even if the HDI excludes zero. **Dependencies: T024**
- [ ] T027a [US3] Implement `code/main.py` logic to execute the analysis script and save `data/analysis_results.json` with posterior means, credible intervals, correlation stats, and stability flags. **JSON Schema**: `{"posterior_mean": float, "credible_interval": [float, float], "correlation_coefficient": float, "correlation_ci": [float, float], "underpowered": bool, "unstable_posterior": bool}`. **Dependencies: T026**
- [ ] T027b [US3] Implement `code/main.py` logic to generate a summary report or console output of the statistical findings. **Dependencies: T027a**
- [X] T028 [US3] Implement logic to generate a summary report or console output of the statistical findings

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T029 [P] Write unit tests for `code/metrics.py` functions (`cosine_similarity`, `lpips_distance`, `cesr_score`) in `tests/test_metrics.py`
- [ ] T030 [P] Write unit tests for `code/data_loader.py` (quantization loading) in `tests/test_quantization.py`
- [ ] T031a [P] [Rev] Define `.github/workflows/ci.yaml` to run the full pipeline. **Environment**: Use `ubuntu-latest` with 16GB RAM. **Setup**: Install dependencies from `code/requirements.txt`, mount data from `data/`. **Verification**: Verify total job duration ≤ 6 hours and generate `data/ci_report.json` with job duration and status. **Memory Reporting**: The `data/ci_report.json` MUST include a `memory_status` key that reports "MemoryLimitExceeded" if Exit Code 137 is detected, otherwise "OK". **Dependencies: T014b, T020b, T027a** (Note: The `data/ci_report.json` file MUST have the following keys: `duration_seconds`, `status`, `timestamp`, `memory_status`.)
- [ ] T031b [P] [Rev] Implement the timing logic in `code/main.py` to record start/end timestamps and write `data/ci_report.json`. **Dependencies: T031a**
- [X] T032 Update `docs/quickstart.md` with instructions for running the pipeline on CPU-only runners
- [X] T033 Final review of `state/artifacts.yaml` to ensure all model weights and data artifacts are checksummed

---

## Phase 7: Revision & Analysis Resolution

**Purpose**: Address specific analysis findings and edge cases identified in prior review cycles.

- [X] T035 [P] [Rev] **REDUNDANT**: Error handling logic for HuggingFace download failures has been integrated into T007b-1 and T007c. This task is no longer required in the active path. **Dependencies: T007b-1**
- [X] T036 [P] [Rev] **REDUNDANT**: Error handling logic for `torch.ao.quantization` backend unavailability has been integrated into T016. This task is no longer required in the active path.
- [X] T037 [P] [Rev] Add validation logic in `code/metrics.py` to ensure that when computing CESR, the target prompt is excluded from the reference set to prevent self-similarity bias, and log a warning if a zero-difference delta is detected (Edge Case: Zero Difference).
- [X] T038 [P] [Rev] Enhance `code/statistical_analysis.py` to include a diagnostic plot of the posterior width for the quantization effect, visually confirming the "Underpowered" flag logic in T026 (FR-014).
- [X] T040 [P] [Rev] **REDUNDANT**: "Fail Loudly" policy logic has been integrated into T007b-1 and T007c. This task is no longer required in the active path. **Dependencies: T007b-1**
- [X] T041 [P] [Rev] Update `code/config.yaml` to explicitly state the streaming/sampling rule if the full dataset cannot be processed, ensuring the sample size and representativeness limitations are documented (Constitution Principle: Real Data + Real Results). **Dependencies: T004**
- [ ] T042 [P] [Rev] Update `code/statistical_analysis.py` to include a check for the "Underpowered" flag in the final report generation, ensuring the `data/analysis_results.json` clearly distinguishes between "Significant" and "Underpowered" results based on FR-014. **Dependencies: T026**
- [X] T043 [P] [Rev] **DELETED**: Dependency correction for T014 was applied directly to T014 in this revision.
- [X] T044 [P] [Rev] **Dependency Correction**: Update `code/main.py` in T020 to explicitly verify the existence of `data/references/fp16_refs/` (from T011c) before attempting CESR calculations in T018, ensuring the reference images are generated before quantization tasks attempt to use it. **Dependencies: T011c, T020** (Note: Resolved by updating T020a dependencies.)
- [X] T045 [P] [Rev] **Real Data Verification**: Update `code/data_loader.py` in T007b-1 to explicitly log the exact HuggingFace commit hash and file size of the downloaded adapter before saving, ensuring the "Real Data" gate can verify the source is not a synthetic or placeholder file. **Dependencies: T007b-1**
- [X] T046 [P] [Rev] **Bayesian Power Analysis**: Update `code/statistical_analysis.py` in T026 to calculate the effective sample size (ESS) for the posterior distribution of the correlation coefficient. If ESS < 200, flag the result as "Unstable Posterior" in addition to "Underpowered" (FR-014). **Dependencies: T024**
- [X] T047 [P] [Rev] **CESR Negative Control**: Update `code/metrics.py` in T018 to implement the "Negative Control" logic described in the Plan (Section 2, Point 2). Generate or load a "Distractor Reference" set and compute CESR against these to validate that the metric is not detecting random semantic distance. Log the "Distractor CESR" alongside the primary CESR. **Dependencies: T011c, T017**
- [X] T048 [P] [Rev] **Quantization Integrity Check**: Update `code/main.py` in T020 to implement the "Model Integrity Check" (Plan Section 5, Point 2). If LPIPS > 0.8 or similarity < 0.1 for a quantized level, log "Quantization Failure: Catastrophic Collapse" and skip the level, ensuring the result is marked 'Not Testable' rather than 'Skipped'. **Dependencies: T019, T016**