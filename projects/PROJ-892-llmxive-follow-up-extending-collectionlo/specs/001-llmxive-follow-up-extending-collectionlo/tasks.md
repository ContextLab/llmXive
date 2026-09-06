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

- [X] T001a [Foundational] Implement `code/data_loader.py` function `load_and_verify_source_loras`. **Logic**: 1. **Primary Path**: Attempt to download a verified *multi-effect* CollectionLoRA adapter from HuggingFace (if available). 2. **Fallback Path**: If no multi-effect adapter is found or download fails, immediately invoke `generate_procedural_source_loras` (T001b logic) to synthesize a set of distinct low-rank matrices. 3. **Size Check**: Verify that the The total weight size of downloaded or synthesized LoRAs is constrained to fit within available system memory.. If size > 16GB, raise `ValueError` with message "Adapter size exceeds 16GB RAM constraint." 4. **Verification**: For downloaded LoRAs, verify they contain distinct effect categories (e.g., "oil painting", "watercolor") by checking key prefixes or metadata. 5. **Output**: Save verified or procedural LoRAs to `data/models/source_loras/`. **Dependencies: None**
- [X] T001b [Foundational] Implement `code/data_loader.py` function `generate_procedural_source_loras`. **Logic**: 1. **Trigger**: Invoked only if T001a fails to find a valid multi-effect adapter. 2. **Generation**: Generate a set of distinct low-rank matrices (rank -16) with random initialization, assigning them distinct effect names (e.g., `proc_effect_1` to `proc_effect_5`). 3. **Size Check**: Verify that the synthesized LoRA weights remain within acceptable memory constraints. If size > 16GB, raise `ValueError`. 4. **Fail-Fast Validation**: Loop until a sufficient number of distinct matrices are successfully generated and saved to `data/models/source_loras/`. If generation fails to produce 5, raise `ValueError` with message "Procedural generation failed to produce 5 distinct effects." 5. **Authorization**: This is a "Verified Synthetic Fallback" authorized by Plan Section 'Key Methodological Update' when no public multi-effect LoRA exists. **Output**: 5 procedural LoRA files in `data/models/source_loras/`. **Dependencies: None**
- [X] T001c [Foundational] Implement `code/data_loader.py` function `check_lora_compatibility`. **Logic**: 1. Verify all source LoRAs (from T001a OR T001b) exist in `data/models/source_loras/`. 2. Check that all source LoRAs share the same base model architecture and rank. 3. **Distinct Effects Check**: Verify that the source LoRAs contain distinct effect categories (e.g., unique key prefixes). If fewer than 5 distinct effects are found, raise `ValueError`. 4. If incompatible, raise `ValueError`. **Dependencies: T001a, T001b**
- [ ] T001d [Foundational] Implement `code/data_loader.py` function `compute_source_ranks`. **Logic**: 1. **Extraction**: Explicitly extract per-effect weight matrices from each source LoRA using key pattern matching (e.g., `lora_A.down.weight`). 2. **SVD**: Compute Singular Value Decomposition (SVD) on each extracted source matrix to determine effective subspace rank. 3. **Tolerance**: Use a sufficiently small tolerance threshold (e.g., `1e-5`). 4. **Output**: Save the computed subspace ranks to `data/subspace_ranks_source.json`. 5. **Versioning**: Immediately compute SHA-256 hash of `data/subspace_ranks_source.json` and record it in `state/artifacts.yaml` (FR-013) *at the moment of creation*. **Dependencies: T001c**
- [X] T002 [Foundational] Implement `code/data_loader.py` function `merge_collection_lora`. **Logic**: 1. Project each source matrix onto an orthogonal basis before addition (WLA-OP) to minimize cross-talk. 2. Save the merged adapter to `data/models/collection_lora.safetensors`. 3. **Validity Check (Fail-Fast)**: Verify the merged adapter contains multiple distinct effects by checking key prefixes (e.g., `effect_oil_`, `effect_water_`). If count != 5, raise `ValueError` with message "Merged adapter does not contain exactly 5 distinct effects." 4. Compute SHA-256 hash and record in `state/artifacts.yaml`. **Dependencies: T001d**

---

## Pre-Phase Gate: Plan Ratification

**Purpose**: Ensure the project plan is legally ratified against the Constitution before any implementation begins.

- [X] T034a [Gate] Create `code/verify_plan.py` script that reads `plan.md` and `constitution.md`. The script MUST validate that the plan explicitly references and complies with Constitutional Principles I, III, V, and VI. It must check for the presence of the specific strings "Principle I", "Principle III", "Principle V", and "Principle VI" in `constitution.md` and verify the plan addresses them. If all required principles are addressed, write `{"status": "RATIFIED", "timestamp": "<now>"}` to `state/ratification.yaml`. If any principle is missing or vague, raise `ValueError`. This task is the mechanism that transitions the plan from "Pending" to "Ratified". **Dependencies: None**

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
**Note**: T016 (Quantization) must run SEQUENTIALLY after T002 (Merge) to avoid OOM on the 16GB runner. Do NOT run them in parallel. The Phase 2 header explicitly forbids parallel execution of T016a with T002.

- [X] T003 [P] Initialize Python project with pinned dependencies in `code/requirements.txt` (must include: `torch`, `diffusers`, `transformers`, `clip`, `lpips`, `numpy`, `pandas`, `pymc`, `arviz`, `scikit-learn`)
- [X] T004a [P] Create `code/config.yaml` containing the EXACT, FIXED list of test prompts and seed values to ensure reproducibility. **YAML Schema**:
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
 distractor_prompts:
 - "a random cloud"
 - "a blurry texture"
 - "abstract noise"
 - "a plain wall"
 - "static pattern"
 ```
 **Logic**: This file is the single source of truth for all generation tasks (FR-009, FR-003). **Dependencies: T034a**
- [ ] T004b [P] Implement `code/data_loader.py` function `map_prompts_to_effects`. **Logic**: 1. Load the fixed prompt list from `code/config.yaml`. 2. Load `data/subspace_ranks_merged.json` (from T001e). 3. **Mapping Mechanism**: Perform **prefix matching** (e.g., "oil painting style" matches "oil_painting"). 4. **Normalization**: Normalize keys (lowercase, strip whitespace) before matching. 5. **Deterministic Filter**: If a prompt does not match any effect name, log a warning "Prompt 'X' does not match any effect; skipping deterministically." 6. **Fallback**: If `subspace_ranks_merged.json` is missing, fallback to `data/subspace_ranks_source.json` (from T001d) to map prompts. 7. **Output**: A filtered list of prompts that successfully map to effects. **Dependencies: T001e, T001d, T004a**
- [ ] T004c [P] Implement `code/data_loader.py` function `validate_prompt_mapping`. **Logic**: 1. Verify that at least one prompt from the fixed list successfully mapped to effects. 2. If fewer than one, raise `ValueError` with message "Insufficient prompt-effect mapping. Aborting." 3. Save the validated prompt list to `data/config/validated_prompts.json`. **Dependencies: T004b**
- [X] T006 [P] Implement `code/state_manager.py` to handle SHA-256 hashing of artifacts and `state/artifacts.yaml` updates (FR-013)
- [ ] T007b-1 [P] [Rev] Implement logic in `code/data_loader.py` to load the verified CollectionLoRA adapter from `data/models/collection_lora.safetensors` (produced by T002). **Logic**: 1. Verify the file exists. 2. Compute SHA-256 hash and record in `state/artifacts.yaml`. 3. If the file is missing, attempt to load the first source adapter from `data/models/source_loras/` as a fallback. 4. If both fail, raise a `ValueError` with the message "Synthetic adapter T002 not found and no fallback available. Aborting." **Dependencies: T002**
- [X] T007c [P] Implement logic in `code/data_loader.py` to download the base model (Stable Diffusion 1.5) from `runwayml/stable-diffusion-v1-5` and compute its SHA-256 hash, recording it in `state/artifacts.yaml` (FR-013). If the download fails from the primary source, attempt a verified secondary mirror. If both fail, raise a `ValueError` with the message "Failed to download base model from primary source. Aborting." **Dependencies: T003**
- [X] T008a [P] [Rev] Implement `code/error_handler.py` with a function `handle_memory_error(e: MemoryError)` that logs "Quantization Failure" and returns a skip flag. **Dependencies: T003**
- [X] T008b [P] [Rev] Integrate `handle_memory_error` into `code/main.py` wrapper logic to catch in-process `MemoryError` exceptions and handle subprocess Exit Code 137 (SIGKILL) by logging "Quantization Failure" and gracefully skipping the affected quantization level (FR-008). **Dependencies: T008a**
- [ ] T009c [P] [Rev] Implement logic to load the subspace ranks from `data/subspace_ranks_merged.json` (produced by T001e), validate the tolerance threshold used, and ensure the file is checksummed in `state/artifacts.yaml` (FR-010, FR-007). **Dependencies: T001e**
- [X] T009d [P] Create `code/metrics.py` stub with imports for CLIP, LPIPS, and NumPy. **Dependencies: T003**
- [ ] T016a [Foundational] Implement `code/data_loader.py` function `quantize_lora_adapters`. **Config**: Use `torch.ao.quantization` with **dynamic quantization** (NO calibration data, NO mock calibration) to convert LoRA modules to low-precision integer formats. **Logic**: 1. Load the *merged* CollectionLoRA adapter from `data/models/collection_lora.safetensors` (output of T002). 2. Apply quantization. 3. **Constraint**: NO calibration data, NO fine-tuning, NO gradient updates, NO mock calibration. 4. **Static Quantization**: Ensure scaling factors are computed and stored with the weights (static). 5. **Integrity Check**: Immediately after quantization, generate a small sample (a minimal set of images) and compute LPIPS and cosine similarity. If LPIPS > 0.8 or similarity < 0.1, **log "Quantization Failure: Catastrophic Collapse" and SKIP this specific quantization level** (do NOT raise `ValueError`), allowing the pipeline to continue for other levels. 6. **Error Handling**: Wrap the quantization logic in a `try/except` block. If `torch.ao.quantization` backend is unavailable (e.g., `RuntimeError`), log "Backend Unavailable" and **skip** this level. 7. **Output**: Save quantized adapters to `data/quantized/adapter_int8.safetensors` and `data/quantized/adapter_int4.safetensors` (FR-002) if successful. **Dependencies: T002, T007b-1** (Note: Run SEQUENTIALLY after T002 and T007b-1 to avoid OOM; this task is NOT marked [P] to enforce sequential execution.)
- [X] T039 [P] [Rev] Create `code/validate_data.py` script to verify that the loaded CollectionLoRA adapter contains at least 5 distinct effects (identified by unique key prefixes in the state dict) AND that their subspace ranks (from T001e) are distinct (not near-identical). **Dependencies: T007b-1, T001e**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.
**Gate**: Phase 3 requires T039 to pass (validation). T016 (Quantization) must run SEQUENTIALLY after T002.

---

## Phase 2.5: Reference Generation (Moved from Phase 1.5)
*Goal: Generate distractor references and organize 'other effect' subsets.*

- [X] T035 [P] Implement `code/generator.py` function `generate_distractor_references`. **Configuration**: Use `resolution=512x512`, `sampler="euler"`, `steps=20`. Generate a set of images using the **fixed** list of `distractor_prompts` from `code/config.yaml` (e.g., "a random cloud", "a blurry texture", etc.) to establish a random semantic distance floor. Save to `data/references/distractor_refs/`. Compute CLIP embeddings for these images and save to `data/references/distractor_embeddings.json` with schema `{"prompt": "embedding_vector"}`. **Versioning**: Immediately compute the SHA-256 hash of `data/references/distractor_embeddings.json` and record it in `state/artifacts.yaml` (Constitution Principle V, FR-013). **Dependencies: T003, T004a**

---

## Phase 3: User Story 1 - Baseline Fidelity Measurement (Priority: P1) 🎯 MVP

**Goal**: Generate FP16 baseline images, extract CLIP embeddings, and compute cosine similarity to establish ground truth.

**Independent Test**: Can be fully tested by running the generation pipeline on the CPU-only runner with FP16 weights and verifying `data/results.csv` contains multiple rows with non-null similarity scores.

### Implementation for User Story 1

- [ ] T010b [US1] Implement `code/data_loader.py` function `load_fp16_adapter`. **Logic**: Load the verified FP16 adapter (`data/models/collection_lora.safetensors` from T002) into CPU memory. Use `device_map='cpu'` and `torch_dtype=torch.float16`. **Dependencies: T002, T007c**
- [ ] T010c [US1] Implement `code/data_loader.py` function `load_base_model`. **Logic**: Load the base model (from T007c) into CPU memory. **Dependencies: T007c**
- [X] T011 [US1] Implement `code/generator.py` function to generate images using the **validated** prompt list from `data/config/validated_prompts.json` (from T004c) with the FP16 adapter loaded in T010b (FR-003, FR-009). **Logic**: Iterate over prompts and seeds, generate images, and save to `data/generated/baseline/`. **Timeout Enforcement**: Track elapsed time; if generation exceeds 5 hours, log "Timeout: Generation loop exceeded 5 hours" and write a 'Timeout' flag to `state/artifacts.yaml`, then abort the pipeline gracefully. **Dependencies: T010b, T010c, T004c**
- [X] T011c [US1] Implement `code/generator.py` function to generate and save a set of "FP16 ReferenceImages" for *ALL* validated effect prompts defined in T004c, using **multiple seeds** from `code/config.yaml`. **Configuration**: Use `resolution=512x512`, `sampler="euler"`, `steps=20`. Save to `data/references/fp16_refs/`. Organize these into a lookup table keyed by effect category and seed. **Embedding Extraction**: Extract CLIP embeddings for these images and save them to `data/references/baseline_embeddings.json` with schema `{"effect": {"seed": "embedding_vector"}}`. These are required for CESR calculation in US2 (FR-011, US-2). **Dependencies: T011, T004c**
- [X] T011e [US1] Implement `code/generator.py` function to generate `data/references/other_effect_refs.json`. **Logic**: 1. Load all generated FP16 ReferenceImages from T011c. 2. Group by effect category. 3. For each effect, create a reference set containing images from *other* effects (excluding the target effect). 4. Save as `data/references/other_effect_refs.json` with schema `{"target_effect": {"ref_effect": "embedding_vector"}}`. **Dependencies: T011c**
- [X] T012 [US1] Implement `code/metrics.py` function to extract CLIP image embeddings and compute cosine similarity with prompt text embeddings (FR-004). **Logic**: 1. Load prompt text and image. 2. Extract CLIP embeddings. 3. Compute cosine similarity. 4. Return scalar score. **Dependencies: T003**
- [X] T013 [US1] Implement `code/metrics.py` function to compute LPIPS distance between generated FP16 images (from T011) and the FP16 ReferenceImages (from T011c). **Purpose**: This is a self-consistency check for US1 to verify the generation pipeline is functional, distinct from the FR-005 metric (Quantized vs FP16) computed in T019. **Dependencies: T011, T011c**
- [ ] T014a [US1] Implement `code/main.py` function `run_baseline_generation_loop`. **Logic**: Run FP16 generation loop, compute metrics (using T012, T013), and save initial `data/results.csv` and `data/generated/` images. **CSV Schema**: The `results.csv` file MUST have the following columns: `prompt`, `seed`, `quantization_level`, `similarity_score`, `lpips_distance`, `cesr_score`, `image_path`, `subspace_rank`, `effect`. **Logic**: Join `data/subspace_ranks_merged.json` into the DataFrame on the 'effect_name' column (from JSON) and 'effect' column (from CSV) to populate `subspace_rank`. **Normalization**: Normalize keys (lowercase, strip whitespace) before joining to avoid silent failures. **Derive 'effect' column**: Match the `prompt` string to the effect names in `data/subspace_ranks_merged.json` (using the same prefix-mapping logic as T004). If no match is found, raise `ValueError`. **Dependencies: T013, T012, T011, T011c, T009c, T001e**
- [ ] T014b [US1] Implement `code/main.py` function `aggregate_baseline_results`. **Logic**: Aggregate results and verify SHA-256 hashes of generated images in `state/artifacts.yaml`. **Dependencies: T014a**
- [ ] T014c [US1] Implement `code/main.py` function `verify_baseline_hashes`. **Logic**: Verify SHA-256 hashes of generated images in `state/artifacts.yaml`. **Dependencies: T014b**
- [X] T015 [US1] Add logging for baseline generation steps and verify SHA-256 hashes of generated images in `state/artifacts.yaml**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantization Impact Analysis (Priority: P2)

**Goal**: Apply INT8/INT4 quantization, generate images, and measure concept adherence drop and concept bleeding (CESR).

**Independent Test**: Can be fully tested by running the quantization pipeline on the CPU runner, generating images, and verifying the delta in cosine similarity is recorded in `data/results.csv`.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/generator.py` function to generate images for INT and INT4 adapters using the same prompt list (FR-003). **Timeout Enforcement**: Track elapsed time; if generation exceeds 5 hours, log "Timeout: Quantized generation loop exceeded 5 hours" and write a 'Timeout' flag to `state/artifacts.yaml`, then abort the pipeline gracefully. **Dependencies: T016a**
- [ ] T018 [US2] Implement `code/metrics.py` function to compute Cross-Effect Similarity Ratio (CESR) by comparing quantized output embeddings against the **'Other-Effect Reference Subset'** (from `data/references/other_effect_refs.json` produced by T011e) AND the Distractor References (from T035). **Logic**: 1. **Pre-Check**: Verify `data/references/other_effect_refs.json` exists and contains valid entries. If not, log "CESR Pre-Check Failed" and skip. 2. Load the 'Other-Effect Reference Subset'. 3. **Filter**: Ensure the reference set for a given `target_effect` EXCLUDES any reference where `ref_effect == target_effect`. 4. Compute `CESR_raw` (similarity to other effect references). 5. Load Distractor References from T035. Compute `CESR_baseline` (mean similarity to Distractor References). 6. Compute `CESR_normalized = CESR_raw - CESR_baseline`. **Negative Control**: Use the Distractor Reference set to validate that the metric is not detecting random semantic distance. Log the "Distractor CESR" alongside the primary CESR. **Dependencies: T011e, T017, T016a, T035**
- [X] T019 [US2] Implement `code/metrics.py` function to compute LPIPS distance between quantized outputs and FP16 baseline outputs (FR-005). **Dependencies: T011**
- [ ] T020a [US2] Implement `code/main.py` function `run_quantized_generation_loop`. **Logic**: Run quantized generations, handle `MemoryError` per level (using logic from T008b), compute deltas, and append to `data/results.csv`. **Logic**: Join `data/subspace_ranks_merged.json` into the DataFrame on the 'effect_name' column (from JSON) and 'effect' column (from CSV) to populate `subspace_rank`. **Normalization**: Normalize keys (lowercase, strip whitespace) before joining. **Dependencies: T018, T019, T014a, T011c, T009c, T011e**
- [ ] T020b [US2] Implement `code/main.py` function `aggregate_quantized_results`. **Logic**: Aggregate quantization results and verify SHA-256 hashes of quantized weights and generated images. **Dependencies: T020a**
- [ ] T020c [US2] Implement `code/main.py` function `verify_quantized_hashes`. **Logic**: Verify SHA-256 hashes of quantized weights and generated images. **Dependencies: T020b**
- [ ] T021 [US2] Implement logic to load per-effect LoRA subspace rank from `data/subspace_ranks_merged.json` (produced by T001e) and prepare data for correlation analysis. **Input**: `data/subspace_ranks_merged.json` (FR-010)
- [X] T022 [US2] Add logging for quantization steps and verify SHA-256 hashes of quantized weights and generated images

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bayesian Statistical Analysis (Priority: P3)

**Goal**: Perform Bayesian Hierarchical Model analysis and correlate subspace rank with concept bleeding.

**Independent Test**: Can be fully tested by running the statistical analysis script on `data/results.csv` and verifying `data/analysis_results.json` contains posterior distributions and correlation coefficients. Note: This task depends on the completion of Phase 3 and Phase 4 to ensure full dataset availability.

### Implementation for User Story 3

- [ ] T023a [P] [US3] Implement `code/statistical_analysis.py` function `load_bayesian_data`. **Logic**: Load `data/results.csv` and `data/subspace_ranks_merged.json`. **Schema Validation**: The task MUST validate that `data/results.csv` contains all required columns (including 'subspace_rank' from T001e). If columns are missing or data is empty, the task must abort gracefully with a "Not Testable" status for the correlation analysis. **Dependencies: T014b, T020b, T001e, T050**
- [ ] T023b [P] [US3] Implement `code/statistical_analysis.py` function `aggregate_bayesian_data`. **Logic**: 1. **First Aggregate**: Group `data/results.csv` by `effect` to compute the **mean** of `cesr_normalized` (bleeding) for each effect. 2. **Join**: Join the aggregated DataFrame with `data/subspace_ranks_merged.json` on the 'effect' column. 3. **Output Structure**: Create a pandas DataFrame with columns: `effect_id`, `mean_bleeding`, `quantization_level`, `subspace_rank`. This structure is required by `pymc`/`bambi` (FR-006, FR-012). **Dependencies: T023a**
- [X] T023c [P] [US3] Implement `code/statistical_analysis.py` function `validate_bayesian_input`. **Logic**: 1. Load the output of T024 (Bayesian Model). 2. **Check**: Verify that the model status is NOT 'Unstable Posterior' (ESS < 200). 3. **Abort**: If 'Unstable Posterior' is detected, abort the correlation step and flag the result as "Unstable". 4. **Save**: Save the validated aggregated dataset to `data/aggregated_bleeding.csv`. **Dependencies: T023b, T024**
- [ ] T024 [US3] Implement `code/statistical_analysis.py` to define and run the Bayesian Hierarchical Model using `pymc`/`bambi` with PARTIAL POOLING. **Priors**: Weakly informative Normal distribution centered at zero for fixed effects, HalfNormal distribution for random effects. (Plan Section 3.2). Test quantization effects and mitigate small sample size risks (FR-006, FR-012, Plan Section 5). **Model Formula**: `similarity_score ~ quantization_level + (1 | effect_id)`. **Sampling**: `draws=1000`, `tune=1000`, `chains=4`. **Posterior Width Analysis**: 1. Extract posterior samples for `Quantization_Effect` coefficient. 2. Calculate the % HDI width. 3. **Flag**: If HDI width > 0.2, set `underpowered = True`. 4. **ESS Check**: Calculate Effective Sample Size (ESS) for the posterior distribution of the correlation coefficient. If ESS < 200, set `unstable_posterior = True`. 5. **Output**: Save posterior samples to `data/analysis_results.json` (or `data/posterior_samples.nc` if too large) as specified in T027a. **Dependencies: T023c**
- [ ] T025b [US3] Implement `code/statistical_analysis.py` to compute correlation between per-effect LoRA subspace rank (from `data/subspace_ranks_merged.json` via T001e) and mean concept bleeding magnitude (from T023b), explicitly reporting credible intervals as a **descriptive/exploratory** trend (FR-007, Plan Section 'Key Methodological Update'). **Logic**: 1. Compute Pearson correlation coefficient and % credible interval. 2. **No Significance Test**: Do NOT test for statistical significance of the correlation coefficient due to N=5 effects. 3. **Output**: Save correlation coefficient and CI to `analysis_results.json`. **Dependencies: T001e, T023c, T024**
- [ ] T026 [US3] Implement `code/statistical_analysis.py` to read posterior width from T024 output; if width > 0.2 for the `Quantization_Effect` coefficient, flag the result as "Underpowered" in `analysis_results.json`. **Decision Rule**: 1. Extract the posterior samples from T024. 2. **Calculate** the [deferred] HDI width for the `Quantization_Effect` coefficient. 3. **Write** `posterior_width` to `analysis_results.json`. 4. If HDI of quantization effect excludes zero, it is significant. 5. If width > 0.2, flag as underpowered (FR-014). 6. **ESS Check**: Calculate the Effective Sample Size (ESS) for the posterior distribution of the correlation coefficient. If ESS < 200, flag the result as "Unstable Posterior". 7. **Constraint**: If "Underpowered" or "Unstable Posterior" is flagged, the result MUST NOT be labeled as "Significant", even if the HDI excludes zero. **Dependencies: T024**
- [ ] T027a [US3] Implement `code/main.py` function `save_analysis_results`. **Logic**: Execute the analysis script and save `data/analysis_results.json` with posterior means, credible intervals, correlation stats, and stability flags. **JSON Schema**: `{"posterior_mean": float, "credible_interval": [float, float], "correlation_coefficient": float, "correlation_ci": [float, float], "underpowered": bool, "unstable_posterior": bool, "posterior_width": float}`. **Dependencies: T026**
- [ ] T027b [US3] Implement `code/main.py` logic to generate a summary report or console output of the statistical findings. **Dependencies: T027a**
- [X] T028 [US3] Implement logic to generate a summary report or console output of the statistical findings

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T029 [P] Write unit tests for `code/metrics.py` functions (`cosine_similarity`, `lpips_distance`, `cesr_score`) in `tests/test_metrics.py`
- [ ] T030 [P] Write unit tests for `code/data_loader.py` (quantization loading) in `tests/test_quantization.py`. **Test Functions**: `test_quantize_per_channel`, `test_quantize_int4`, `test_quantize_int8`. **Scenarios**: Test successful quantization, test integrity check failure, test backend unavailability. **Dependencies: T016a**
- [ ] T031b [P] [Rev] Implement `code/main.py` function `record_ci_timing`. **Logic**: Record start/end timestamps and write `data/ci_report.json`. **Dependencies: None**
- [X] T032 Update `docs/quickstart.md` with instructions for running the pipeline on CPU-only runners
- [X] T033 Final review of `state/artifacts.yaml` to ensure all model weights and data artifacts are checksummed

---

## Phase 7: Revision & Analysis Resolution

**Purpose**: Address specific analysis findings and edge cases identified in prior review cycles.

- [X] T037 [P] [Rev] Add validation logic in `code/metrics.py` to ensure that when computing CESR, the target prompt is excluded from the reference set to prevent self-similarity bias, and log a warning if a zero-difference delta is detected (Edge Case: Zero Difference).
- [X] T038 [P] [Rev] Enhance `code/statistical_analysis.py` to include a diagnostic plot of the posterior width for the quantization effect, visually confirming the "Underpowered" flag logic in T026 (FR-014).
- [X] T040 [P] [Rev] **REDUNDANT**: "Fail Loudly" policy logic has been integrated into T007b-1 and T007c. This task is no longer required in the active path. **Dependencies: T007b-1**
- [X] T041 [P] [Rev] Update `code/config.yaml` to explicitly state the streaming/sampling rule if the full dataset cannot be processed, ensuring the sample size and representativeness limitations are documented (Constitution Principle: Real Data + Real Results). **Dependencies: T004a**
- [X] T042 [P] [Rev] **DELETED**: Logic integrated into T026 and T027a.
- [X] T043 [P] [Rev] **DELETED**: Dependency correction for T014 was applied directly to T014 in this revision.
- [X] T044 [P] [Rev] **DELETED**: Logic integrated into T020a.
- [ ] T045 [P] [Rev] **Real Data Verification**: Update `code/data_loader.py` in T007b-1 to explicitly log the exact HuggingFace commit hash and file size of the downloaded adapter before saving, ensuring the "Real Data" gate can verify the source is not a synthetic or placeholder file. **Dependencies: T007b-1**
- [X] T046 [P] [Rev] **Bayesian Power Analysis**: Update `code/statistical_analysis.py` in T026 to calculate the effective sample size (ESS) for the posterior distribution of the correlation coefficient. If ESS < 200, flag the result as "Unstable Posterior" in addition to "Underpowered" (FR-014). **Dependencies: T024**
- [X] T047 [P] [Rev] **CESR Negative Control**: Update `code/metrics.py` in T018 to implement the "Negative Control" logic described in the Plan (Section 2, Point 2). Generate or load a "Distractor Reference" set and compute CESR against these to validate that the metric is not detecting random semantic distance. Log the "Distractor CESR" alongside the primary CESR. **Dependencies: T011c, T017, T035**
- [ ] T048 [P] [Rev] **Quantization Integrity Check**: Update `code/main.py` in T020 to implement the "Model Integrity Check" (Plan Section 5, Point 2). If LPIPS > 0.8 or similarity < 0.1 for a quantized level, log "Quantization Failure: Catastrophic Collapse" and skip the level, ensuring the result is marked 'Not Testable' rather than 'Skipped'. **Dependencies: T019, T016a**
- [ ] T050 [P] **Subspace Rank Validation**: Implement `code/statistical_analysis.py` in T023 to verify that the `subspace_rank` column in `data/results.csv` is populated with non-null, positive integer values derived from T001e. If the column is missing or contains invalid data, the analysis MUST abort with a clear "Data Integrity Error: Subspace Ranks Missing" message rather than proceeding with a flawed correlation test. **Dependencies: T001e, T023a**

---

## Phase 8: Execution Readiness & Final Validation

**Purpose**: Final checks to ensure the pipeline is ready for the execution stage and all data flow dependencies are strictly enforced.

- [ ] T051 [P] [Rev] **Data Flow Enforcement**: Implement `code/dependency_checker.py` to perform a pre-flight validation of the entire execution graph. The script must verify that `data/generated/baseline/` exists before `run_quantized_generation_loop` (T020a) is invoked, and that `data/references/other_effect_refs.json` (T011e) is present before CESR calculation (T018). If any dependency is missing, the script must raise a `DependencyError` with a clear message indicating the missing artifact and the task that produced it. **Dependencies: T011e, T020a, T018**
- [ ] T052 [P] [Rev] **Quantization Backend Fallback**: Update `code/data_loader.py` in T016a to include a robust fallback mechanism for `torch.ao.quantization` failures. If the primary backend fails, attempt to use `torch.quantization` (legacy) or log a specific "Backend Unavailable" error with a suggestion to update `requirements.txt`. Ensure the pipeline does not crash but skips the specific quantization level gracefully as per FR-008. **Dependencies: T016a**
- [ ] T053 [P] **Result Aggregation Verification**: Implement `code/validate_results.py` to verify the integrity of `data/results.csv` after all generation loops. The script must check for: 1. Non-empty rows for each quantization level (FP16, INT8, INT4). 2. Non-null values for `similarity_score`, `lpips_distance`, and `cesr_score`. 3. Correct mapping of `effect` to `subspace_rank`. If any validation fails, the script must halt the pipeline and log a "Result Integrity Error". **Dependencies: T014b, T020b**
- [X] T054 [P] **Bayesian Model Convergence Check**: Enhance `code/statistical_analysis.py` in T024 to perform an automatic convergence check (e.g., R-hat < 1.01) before saving results. If the model has not converged, the script must flag the result as "Unconverged" and attempt a re-run with adjusted priors or sampling parameters up to 3 times before failing. **Dependencies: T024**
- [X] T055 [P] **Final Artifact Hashing**: Implement `code/final_hash_check.py` to perform a final sweep of all generated artifacts (images, CSVs, JSONs, weights) and ensure their SHA-256 hashes are correctly recorded in `state/artifacts.yaml`. The script must fail if any artifact is missing a hash or if the hash does not match the file content. **Dependencies: T033, T014c, T020c, T027a**
- [X] T056 [P] **Documentation Consistency**: Update `docs/quickstart.md` to include the exact command sequence for running the pipeline, including the pre-flight checks (T051) and final validation (T055). Ensure the documentation reflects the current state of the `config.yaml` and the expected output structure. **Dependencies: T032, T051, T055**

---

## New Phase 0.5: Merged Adapter Rank Verification (Added for FR-010)

*Goal: Compute SVD ranks on the merged adapter's internal matrices.*

- [ ] T001e [Foundational] Implement `code/data_loader.py` function `compute_merged_ranks`. **Logic**: 1. Load the *merged* CollectionLoRA adapter from `data/models/collection_lora.safetensors` (output of T002). 2. **Extraction**: Explicitly extract per-effect weight matrices from the merged adapter using key pattern matching (e.g., `lora_A.down.weight` with effect prefix like `effect_oil_`, `effect_water_`). **Pattern**: Use regex `lora_A.down.weight.*effect_[a-z]+` to identify distinct effects. 3. **SVD**: Compute Singular Value Decomposition (SVD) on each extracted matrix to determine effective subspace rank. 4. **Tolerance**: Use a sufficiently small tolerance threshold (e.g., `1e-5`). 5. **Validation**: Ensure a set of distinct effects are found and their ranks are distinct. (not near-identical). If count != 5 or ranks are near-identical, raise `ValueError`. 6. **Output**: Save the computed subspace ranks to `data/subspace_ranks_merged.json`. 7. **Versioning**: Immediately compute SHA-256 hash of `data/subspace_ranks_merged.json` and record it in `state/artifacts.yaml` (FR-010, FR-013) *at the moment of creation*. **Dependencies: T002**