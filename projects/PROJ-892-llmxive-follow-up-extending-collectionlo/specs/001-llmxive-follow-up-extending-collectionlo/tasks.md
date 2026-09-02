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

## Phase 0: Adapter Synthesis & Verification
*Goal: Construct a valid multi-effect adapter and compute intrinsic source ranks.*

- [X] T001a [Foundational] Implement `code/data_loader.py` function to load a set of 5 verified single-effect LoRAs (e.g., `lykon/dreamshaper-lora`, `cagliostrolab/animagine-xl`, etc.) OR generate 5 procedural low-rank matrices if none are available. **Logic**: 1. Define a list of 5 distinct effect categories (e.g., "oil painting", "watercolor", etc.). 2. Attempt to download verified LoRAs for these effects. 3. If download fails, generate procedural matrices. **Dependencies: T003** <!-- FAILED: unspecified -->
- [X] T001b [Foundational] Implement `code/data_loader.py` function to perform Compatibility Check. **Logic**: Verify all source LoRAs share the same base model architecture and rank. If incompatible, fallback to procedural generation for the specific incompatible effect. **Dependencies: T001a** <!-- ATOMIZE: requested -->
- [X] T001c [Foundational] Implement `code/data_loader.py` function to perform SVD Computation & Rank Calculation on **pre-merge** source matrices. **Logic**: 1. Compute Singular Value Decomposition (SVD) on each extracted source matrix to determine effective subspace rank. 2. Use a sufficiently small tolerance threshold. 3. **Validation**: Ensure at least 5 distinct effects are found. 4. Save the computed subspace ranks to `data/subspace_ranks.json`. **Output Schema**: `{"effect_name": rank_value,...}`. 5. **Versioning**: Immediately compute the SHA-256 hash of `data/subspace_ranks.json` and record it in `state/artifacts.yaml` (FR-010, FR-013). **Dependencies: T001b**
- [ ] T002 [Foundational] Implement `code/data_loader.py` function to merge source matrices into a single CollectionLoRA adapter using **Weighted Linear Addition with Orthogonal Projection (WLA-OP)**. **Logic**: 1. Project each source matrix onto an orthogonal basis before addition to minimize cross-talk. 2. Save the merged adapter to `data/models/collection_lora.safetensors`. 3. Compute SHA-256 hash and record in `state/artifacts.yaml`. **Dependencies: T001c** <!-- FAILED: unspecified -->

---

## Pre-Phase Gate: Plan Ratification

**Purpose**: Ensure the project plan is legally ratified against the Constitution before any implementation begins.

- [X] T034a [Gate] Create `code/verify_plan.py` script that reads `plan.md` and `constitution.md`. The script MUST validate that the plan explicitly references and complies with Constitutional Principles I (Reproducibility), III (Data Hygiene), V (Versioning), and VI (Quantization Noise Isolation). It must check for the presence of specific section headers or keywords corresponding to these principles (e.g., "Reproducibility", "Data Hygiene", "Quantization Noise", "Versioning") in `constitution.md` and verify the plan addresses them. If all required principles are addressed, write `{"status": "RATIFIED", "timestamp": "<now>"}` to `state/ratification.yaml`. If any principle is missing or vague, raise `ValueError`. This task is the mechanism that transitions the plan from "Pending" to "Ratified". **Dependencies: None**

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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. This phase includes the mandatory "Adapter Synthesis" workflow.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Note**: T016 (Quantization) must run SEQUENTIALLY after T002 (Merge) to avoid OOM on the 16GB runner. Do NOT run them in parallel.

- [X] T003 [P] Initialize Python project with pinned dependencies in `code/requirements.txt` (must include: `torch`, `diffusers`, `transformers`, `clip`, `lpips`, `numpy`, `pandas`, `pymc`, `arviz`, `scikit-learn`)
- [X] T004 [P] Create `code/config.yaml` containing the EXACT, FIXED list of test prompts and seed values to ensure reproducibility. **YAML Schema**:
 ```yaml
 prompts:
 - "oil painting style"
 - "watercolor style"
 - "cyberpunk style"
 - "pencil sketch style"
 - "ink wash style"
 - "acrylic style"
 - "charcoal style"
 - "pastel style"
 - "digital art style"
 - "concept art style"
 seeds:
 - 42
 - 123
 - 456
 - 789
 - 101112
 ```
 **Logic**: This file is the single source of truth for all generation tasks (FR-009, FR-003). **Dependencies: T034a, T001c** (Note: This task depends on T001c to validate that the hardcoded prompts map to the 5 distinct effects in `data/subspace_ranks.json`. The task MUST implement logic to check if each prompt string starts with one of the 5 effect names in `data/subspace_ranks.json`. If a prompt does not map to any effect, raise `ValueError`.)
- [X] T006 [P] Implement `code/state_manager.py` to handle SHA-256 hashing of artifacts and `state/artifacts.yaml` updates (FR-013)
- [ ] T007b-1 [P] Implement logic in `code/data_loader.py` to load the verified CollectionLoRA adapter from `data/models/collection_lora.safetensors` (produced by T002). **Logic**: 1. Verify the file exists. 2. Compute SHA-256 hash and record in `state/artifacts.yaml`. 3. If the file is missing, raise `ValueError` with message "Synthetic adapter T002 not found. Aborting." **Dependencies: T002** (Note: This task no longer attempts to download from HuggingFace; it strictly relies on the synthetic adapter generated in Phase 0.)
- [X] T007c [P] Implement logic in `code/data_loader.py` to download the base model (Stable Diffusion 1.5) from `runwayml/stable-diffusion-v1-5` and compute its SHA-256 hash, recording it in `state/artifacts.yaml` (FR-013). If the download fails from the primary source, attempt a verified secondary mirror. If both fail, raise a `ValueError` with the message "Failed to download base model from primary source. Aborting." **Dependencies: T003**
- [X] T008a [P] [Rev] Implement `code/error_handler.py` with a function `handle_memory_error(e: MemoryError)` that logs "Quantization Failure" and returns a skip flag. **Dependencies: T003**
- [X] Tb [P] [Rev] Integrate `handle_memory_error` into `code/main.py` wrapper logic to catch in-process `MemoryError` exceptions and handle subprocess Exit Code 137 (SIGKILL) by logging "Quantization Failure" and gracefully skipping the affected quantization level (FR-008). **Dependencies: T008a**
- [X] T009c [P] [Rev] Implement logic to load the subspace ranks from `data/subspace_ranks.json` (produced by T001c), validate the tolerance threshold used, and ensure the file is checksummed in `state/artifacts.yaml` (FR-010, FR-007). **Dependencies: T001c**
- [X] T009d [P] Create `code/metrics.py` stub with imports for CLIP, LPIPS, and NumPy. **Dependencies: T003**
- [ ] T016a [Foundational] Implement `code/data_loader.py` function to apply **static** post-training quantization (FP16 -> INT8/INT4) to LoRA weight matrices ONLY. **Config**: Use `torch.ao.quantization.get_default_qconfig("qnnpack")` with `MinMaxObserver`. **Logic**: 1. Load the *merged* CollectionLoRA adapter from `data/models/collection_lora.safetensors` (output of T002). 2. Apply `torch.ao.quantization.prepare_qat` to the LoRA modules. 3. Apply `torch.ao.quantization.convert` with `inplace=True` to freeze weights to INT8/INT4. 4. **Constraint**: NO calibration data, NO fine-tuning, NO gradient updates. 5. **Static Quantization**: Ensure scaling factors are computed and stored with the weights (static), NOT computed at runtime (dynamic). 6. **Integrity Check**: Immediately after quantization, generate a small sample (a limited number of images) and compute LPIPS and cosine similarity. If LPIPS > 0.8 or similarity < 0.1, log "Quantization Failure: Catastrophic Collapse" and mark the level as "Not Testable" (FR-002, FR-008). 7. **Error Handling**: Wrap the quantization logic in a `try/except` block. If `torch.ao.quantization` backend is unavailable (e.g., `RuntimeError`), log "Backend Unavailable" and skip the specific quantization level without crashing the pipeline (FR-008). 8. **Fallback**: If quantization produces invalid weights (detected by Integrity Check), attempt to skip the level and mark as "Not Testable" rather than crashing. **Output**: Save quantized adapters to `data/quantized/adapter_int8.safetensors` and `data/quantized/adapter_int4.safetensors` (FR-002). **Dependencies: T002, T007b-1** (Note: Run sequentially after T002 to avoid OOM; this task is NOT marked [P] to enforce sequential execution.) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T016b [Foundational] Implement logic in `code/data_loader.py` to serialize the quantized state dicts from T016a to `data/quantized/adapter_int8.safetensors` and `data/quantized/adapter_int4.safetensors` using a custom format that preserves quantization parameters (scale, zero-point). **Dependencies: T016a** <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
- [X] T039 [P] [Rev] Create `code/validate_data.py` script to verify that the loaded CollectionLoRA adapter contains at least 5 distinct effects (identified by unique key prefixes in the state dict) as required by Assumption 011, failing fast if the threshold is not met. **Dependencies: T007b-1**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.
**Gate**: Phase 3 requires T039 to pass (validation). T016 (Quantization) can run in parallel with Phase 3 once T007b-1 is done.

---

## Phase 1.5: Distractor & Reference Generation (Moved from Phase 4.5)
*Goal: Generate distractor references and organize 'other effect' subsets.*

- [ ] T035 [P] Implement `code/generator.py` function to generate 10 "Distractor Reference" images using the FP16 adapter but with **unrelated** prompts (e.g., "a random cloud", "a blurry texture", "abstract noise", "a plain wall", etc.) to establish a random semantic distance floor. **Configuration**: Use `resolution=512x512`, `sampler="euler"`, `steps=20`. Save to `data/references/distractor_refs/`. Compute CLIP embeddings for these images and save to `data/references/distractor_embeddings.json`. **Dependencies: T010b, T004** (Note: This task is required by Plan T004 and FR-011 to normalize the CESR metric. Moved to Phase 1 to ensure availability before US2.) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

---

## Phase 3: User Story 1 - Baseline Fidelity Measurement (Priority: P1) 🎯 MVP

**Goal**: Generate FP16 baseline images, extract CLIP embeddings, and compute cosine similarity to establish ground truth.

**Independent Test**: Can be fully tested by running the generation pipeline on the CPU-only runner with FP16 weights and verifying `data/results.csv` contains multiple rows with non-null similarity scores.

### Implementation for User Story 1

- [ ] T010b [US1] Implement `code/data_loader.py` function to load the verified FP16 adapter (`data/models/collection_lora.safetensors` from T002) and base model (from T007c) into CPU memory. **Logic**: Use `device_map='cpu'` and `torch_dtype=torch.float16` when calling `from_pretrained` or `load_state_dict` to ensure models are loaded on CPU and not GPU (FR-001). **Dependencies: T002, T007c** <!-- ATOMIZE: requested -->
- [X] T011 [US1] Implement `code/generator.py` function to generate images using the FIXED prompt list from `code/config.yaml` (explicitly defined seeds and prompts) with the FP16 adapter loaded in T010b (FR-003, FR-009). **Logic**: Iterate over prompts and seeds, generate images, and save to `data/generated/baseline/`. **Dependencies: T010b, T004** (Note: T011 depends on T004 to load the prompt list and seeds from `code/config.yaml`.)
- [X] T011c [US1] Implement `code/generator.py` function to generate and save a set of "FP16 ReferenceImages" for *ALL* 10 effect prompts defined in T004, using **ALL 5 seeds** from `code/config.yaml`. **Configuration**: Use `resolution=512x512`, `sampler="euler"`, `steps=20`. Save to `data/references/fp16_refs/`. Organize these into a lookup table keyed by effect category and seed. These are required for CESR calculation in US2 (FR-011, US-2). **Dependencies: T011** (Note: These reference images are generated for all 5 seeds to ensure statistical validity for CESR calculation across all quantized generations.) <!-- FAILED: unspecified -->
- [X] T011d [US1] Implement `code/data_loader.py` function to organize `data/references/fp16_refs/` into a lookup table keyed by effect category and seed (e.g., `{"oil_painting": {42: img1, 123: img2,...}}`) to enable target-exclusion logic in T018. **Dependencies: T011c**
- [ ] T011e [US1] Implement `code/data_loader.py` function to generate the **'Other-Effect Reference Subset'**. **Logic**: 1. Load the lookup table from T011d. 2. For each effect `E`, create a new list containing reference images from **all other effects** (i.e., `all_effects - {E}`). 3. Save this structure to `data/references/other_effect_refs.json`. **Purpose**: This explicitly pre-filters the target effect to prevent self-similarity bias in T018 (FR-011). **Dependencies: T011d** <!-- FAILED: unspecified -->
- [X] T012 [US1] Implement `code/metrics.py` function to extract CLIP image embeddings and compute cosine similarity with prompt text embeddings (FR-004)
- [X] T013 [US1] Implement `code/metrics.py` function to compute LPIPS distance between generated FP16 images (from T011) and the FP16 ReferenceImages (from T011c). **Purpose**: This is a self-consistency check for US1 to verify the generation pipeline is functional, distinct from the FR-005 metric (Quantized vs FP16) computed in T019. **Dependencies: T011, T011c** (Note: This task computes a self-consistency check for US1, not the primary LPIPS metric for quantization comparison.) <!-- FAILED: unspecified -->
- [ ] T014a [US1] Implement `code/main.py` logic to run FP16 generation loop, compute metrics, and save initial `data/results.csv` and `data/generated/` images. **CSV Schema**: The `results.csv` file MUST have the following columns: `prompt`, `seed`, `quantization_level`, `similarity_score`, `lpips_distance`, `cesr_score`, `image_path`, `subspace_rank`, `effect`. **Logic**: Join `data/subspace_ranks.json` into the DataFrame on the 'effect' column to populate `subspace_rank`. **Derive 'effect' column**: Match the `prompt` string to the effect names in `data/subspace_ranks.json` (using the same prefix-mapping logic as T004). If no match is found, raise `ValueError`. **Dependencies: T013, T012, T011, T011c, T009c, T011e** (Note: Explicitly depends on T011, T011c, T009c to ensure images, references, and subspace ranks are available.)
- [X] T014b [US1] Implement `code/main.py` logic to aggregate results and verify SHA-256 hashes of generated images in `state/artifacts.yaml`. **Dependencies: T014a** <!-- ATOMIZE: requested -->
- [X] T015 [US1] Add logging for baseline generation steps and verify SHA-256 hashes of generated images in `state/artifacts.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantization Impact Analysis (Priority: P2)

**Goal**: Apply INT8/INT4 quantization, generate images, and measure concept adherence drop and concept bleeding (CESR).

**Independent Test**: Can be fully tested by running the quantization pipeline on the CPU runner, generating images, and verifying the delta in cosine similarity is recorded in `data/results.csv`.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/generator.py` function to generate images for INT8 and INT4 adapters using the same prompt list (FR-003). **Dependencies: T016a, T016b**
- [X] T018 [US2] Implement `code/metrics.py` function to compute Cross-Effect Similarity Ratio (CESR) by comparing quantized output embeddings against the **'Other-Effect Reference Subset'** (from `data/references/other_effect_refs.json` produced by T011e) AND the Distractor References (from T035). **Logic**: 1. Load the 'Other-Effect Reference Subset' from T011e. 2. **Filter**: Ensure the reference set for a given `target_effect` EXCLUDES any reference where `ref_effect == target_effect`. 3. Compute `CESR_raw` (similarity to other effect references). 4. Load Distractor References from T035. Compute `CESR_baseline` (mean similarity to Distractor References). 5. Compute `CESR_normalized = CESR_raw - CESR_baseline`. **Explicit constraint**: Ensure the reference set is constructed from *distinct* effect prompts (excluding the current target) to prevent self-similarity bias (FR-011). If a reference image for the target prompt is missing, log a warning and skip that specific comparison. **Negative Control**: Use the Distractor Reference set to validate that the metric is not detecting random semantic distance. Log the "Distractor CESR" alongside the primary CESR. **Dependencies: T011e, T017, T016a, T035**
- [X] T019 [US2] Implement `code/metrics.py` function to compute LPIPS distance between quantized outputs and FP16 baseline outputs (FR-005). **Dependencies: T011** (Note: This task computes the primary LPIPS metric for quantization comparison, using the images generated by T011, not the metric from T013.)
- [ ] T020a [US2] Implement `code/main.py` logic to run quantized generations, handle `MemoryError` per level (using logic from T008b), compute deltas, and append to `data/results.csv`. **Logic**: Join `data/subspace_ranks.json` into the DataFrame on the 'effect' column to populate `subspace_rank`. **Dependencies: T018, T019, T014a, T011c, T009c** (Note: Explicitly depends on T014a, T011c, and T009c to ensure baseline images, references, and subspace ranks are available.)
- [X] T020b [US2] Implement `code/main.py` logic to aggregate quantization results and verify SHA-256 hashes of quantized weights and generated images. **Dependencies: T020a** <!-- FAILED: unspecified -->
- [X] T021 [US2] Implement logic to load per-effect LoRA subspace rank from `data/subspace_ranks.json` (produced by T001c) and prepare data for correlation analysis. **Input**: `data/subspace_ranks.json` (FR-010)
- [X] T022 [US2] Add logging for quantization steps and verify SHA-256 hashes of quantized weights and generated images

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bayesian Statistical Analysis (Priority: P3)

**Goal**: Perform Bayesian Hierarchical Model analysis and correlate subspace rank with concept bleeding.

**Independent Test**: Can be fully tested by running the statistical analysis script on `data/results.csv` and verifying `data/analysis_results.json` contains posterior distributions and correlation coefficients. Note: This task depends on the completion of Phase 3 and Phase 4 to ensure full dataset availability.

### Implementation for User Story 3

- [ ] T023 [P] [US3] Implement `code/statistical_analysis.py` to load `data/results.csv`, **aggregate by effect** to compute mean bleeding per effect (N=5), and EXPLICITLY extract the 'Effect' grouping variable. **Schema Validation**: The task MUST validate that `data/results.csv` contains all required columns (including 'subspace_rank' from T001c). If columns are missing or data is empty, the task must abort gracefully with a "Not Testable" status for the correlation analysis. **Data Joining**: The task MUST **first aggregate** `data/results.csv` by `effect` to compute mean bleeding, **THEN** join `data/subspace_ranks.json` to this aggregated DataFrame on the 'effect' column. **Output Structure**: Create a pandas DataFrame with columns: `effect_id`, `mean_bleeding`, `quantization_level`, `subspace_rank`. This structure is required by `pymc`/`bambi` (FR-006, FR-012). **Dependencies: T014b, T020b, T001c, T002** (Note: Explicitly depends on T001c, T002 to ensure subspace rank data and effect validation are available.)
- [X] T024 [US3] Implement `code/statistical_analysis.py` to define and run the Bayesian Hierarchical Model using `pymc`/`bambi` with PARTIAL POOLING. **Priors**: Weakly informative Normal distribution centered at zero for fixed effects, HalfNormal distribution for random effects. (Plan Section 3.2). Test quantization effects and mitigate small sample size risks (FR-006, FR-012, Plan Section 5). **Model Formula**: `similarity_score ~ quantization_level + (1 | effect_id)`. **Output**: Must output posterior distributions AND the posterior width for the `Quantization_Effect` coefficient to enable FR-014 flagging (FR-006, FR-012). **Output Artifact**: Save posterior samples to `data/analysis_results.json` (or `data/posterior_samples.nc` if too large) as specified in T027a. **Dependencies: T023** (Note: Model formula explicitly excludes `subspace_rank` to separate the primary hypothesis test from the correlation analysis.)
- [ ] T025a [US3] Implement `code/statistical_analysis.py` to aggregate `CESR_normalized` to the **effect level** (mean per effect) from `data/results.csv`. **Dependencies: T020b**
- [X] T025b [US3] Implement `code/statistical_analysis.py` to compute correlation between per-effect LoRA subspace rank (from `data/subspace_ranks.json` via T001c) and mean concept bleeding magnitude (from T025a), explicitly testing significance via the Bayesian posterior distribution and reporting credible intervals (FR-007). **Dependencies: T001c, T025a, T024** (Note: The dependency on T024 is for the Bayesian correlation significance testing, not the correlation calculation itself.)
- [X] T026 [US3] Implement `code/statistical_analysis.py` to read posterior width from T024 output; if width > 0.2 for the `Quantization_Effect` coefficient, flag the result as "Underpowered" in `analysis_results.json`. **Decision Rule**: 1. Extract the posterior samples from T024. 2. **Calculate** the [deferred] HDI width for the `Quantization_Effect` coefficient. 3. **Write** `posterior_width` to `analysis_results.json`. 4. If HDI of quantization effect excludes zero, it is significant. 5. If width > 0.2, flag as underpowered (FR-014). 6. **ESS Check**: Calculate the Effective Sample Size (ESS) for the posterior distribution of the correlation coefficient. If ESS < 200, flag the result as "Unstable Posterior". 7. **Constraint**: If "Underpowered" or "Unstable Posterior" is flagged, the result MUST NOT be labeled as "Significant", even if the HDI excludes zero. **Dependencies: T024**
- [ ] T027a [US3] Implement `code/main.py` logic to execute the analysis script and save `data/analysis_results.json` with posterior means, credible intervals, correlation stats, and stability flags. **JSON Schema**: `{"posterior_mean": float, "credible_interval": [float, float], "correlation_coefficient": float, "correlation_ci": [float, float], "underpowered": bool, "unstable_posterior": bool, "posterior_width": float}`. **Dependencies: T026** <!-- FAILED: unspecified -->
- [X] T027b [US3] Implement `code/main.py` logic to generate a summary report or console output of the statistical findings. **Dependencies: T027a**
- [X] T028 [US3] Implement logic to generate a summary report or console output of the statistical findings

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T029 [P] Write unit tests for `code/metrics.py` functions (`cosine_similarity`, `lpips_distance`, `cesr_score`) in `tests/test_metrics.py`
- [X] T030 [P] Write unit tests for `code/data_loader.py` (quantization loading) in `tests/test_quantization.py` <!-- FAILED: unspecified -->
- [ ] Ta [P] [Rev] Define `.github/workflows/ci.yaml` to run the full pipeline. **Environment**: Use `ubuntu-latest` with sufficient RAM. **Setup**: Install dependencies from `code/requirements.txt`, mount data from `data/`. **Verification**: Verify total job duration ≤ 6 hours and generate `data/ci_report.json` with job duration and status. **Memory Reporting**: The `data/ci_report.json` MUST include a `memory_status` key that reports "MemoryLimitExceeded" if Exit Code 137 is detected, otherwise "OK". **Dependencies: T014b, T020b, T027a** (Note: The `data/ci_report.json` file MUST have the following keys: `duration_seconds`, `status`, `timestamp`, `memory_status`.)
- [ ] T031b [P] [Rev] Implement the timing logic in `code/main.py` to record start/end timestamps and write `data/ci_report.json`. **Dependencies: T031a** <!-- FAILED: unspecified -->
- [X] T032 Update `docs/quickstart.md` with instructions for running the pipeline on CPU-only runners
- [X] T033 Final review of `state/artifacts.yaml` to ensure all model weights and data artifacts are checksummed

---

## Phase 7: Revision & Analysis Resolution

**Purpose**: Address specific analysis findings and edge cases identified in prior review cycles.

- [X] T035 [P] [Rev] **DELETED**: This task ID was used for Distractor Generation in Phase 4.5 (now moved to Phase 1.5). The entry in this section was a stale tag referencing error handling logic and has been removed.
- [X] T036 [P] [Rev] **REDUNDANT**: Error handling logic for `torch.ao.quantization` backend unavailability has been integrated into T016a. This task is no longer required in the active path.
- [X] T037 [P] [Rev] Add validation logic in `code/metrics.py` to ensure that when computing CESR, the target prompt is excluded from the reference set to prevent self-similarity bias, and log a warning if a zero-difference delta is detected (Edge Case: Zero Difference).
- [X] T038 [P] [Rev] Enhance `code/statistical_analysis.py` to include a diagnostic plot of the posterior width for the quantization effect, visually confirming the "Underpowered" flag logic in T026 (FR-014).
- [X] T040 [P] [Rev] **REDUNDANT**: "Fail Loudly" policy logic has been integrated into T007b-1 and T007c. This task is no longer required in the active path. **Dependencies: T007b-1**
- [X] T041 [P] [Rev] Update `code/config.yaml` to explicitly state the streaming/sampling rule if the full dataset cannot be processed, ensuring the sample size and representativeness limitations are documented (Constitution Principle: Real Data + Real Results). **Dependencies: T004**
- [~] T042 [P] [Rev] Update `code/statistical_analysis.py` to include a check for the "Underpowered" flag in the final report generation, ensuring the `data/analysis_results.json` clearly distinguishes between "Significant" and "Underpowered" results based on FR-014. **Dependencies: T026** <!-- FAILED: unspecified -->
- [X] T043 [P] [Rev] **DELETED**: Dependency correction for T014 was applied directly to T014 in this revision.
- [X] T044 [P] [Rev] **Dependency Correction**: Update `code/main.py` in T020 to explicitly verify the existence of `data/references/fp16_refs/` (from T011c) before attempting CESR calculations in T018, ensuring the reference images are generated before quantization tasks attempt to use it. **Dependencies: T011c, T020** (Note: Resolved by updating T020a dependencies.)
- [X] T045 [P] [Rev] **Real Data Verification**: Update `code/data_loader.py` in T007b-1 to explicitly log the exact HuggingFace commit hash and file size of the downloaded adapter before saving, ensuring the "Real Data" gate can verify the source is not a synthetic or placeholder file. **Dependencies: T007b-1**
- [X] T046 [P] [Rev] **Bayesian Power Analysis**: Update `code/statistical_analysis.py` in T026 to calculate the effective sample size (ESS) for the posterior distribution of the correlation coefficient. If ESS < 200, flag the result as "Unstable Posterior" in addition to "Underpowered" (FR-014). **Dependencies: T024**
- [X] T047 [P] [Rev] **CESR Negative Control**: Update `code/metrics.py` in T018 to implement the "Negative Control" logic described in the Plan (Section 2, Point 2). Generate or load a "Distractor Reference" set and compute CESR against these to validate that the metric is not detecting random semantic distance. Log the "Distractor CESR" alongside the primary CESR. **Dependencies: T011c, T017, T035**
- [X] T048 [P] [Rev] **Quantization Integrity Check**: Update `code/main.py` in T020 to implement the "Model Integrity Check" (Plan Section 5, Point 2). If LPIPS > 0.8 or similarity < 0.1 for a quantized level, log "Quantization Failure: Catastrophic Collapse" and skip the level, ensuring the result is marked 'Not Testable' rather than 'Skipped'. **Dependencies: T019, T016a**
- [X] T050 [P] [Rev] **Subspace Rank Validation**: Update `code/statistical_analysis.py` in T023 to verify that the `subspace_rank` column in `data/results.csv` is populated with non-null, positive integer values derived from T001c. If the column is missing or contains invalid data, the analysis MUST abort with a clear "Data Integrity Error: Subspace Ranks Missing" message rather than proceeding with a flawed correlation test. **Dependencies: T001c, T023**
