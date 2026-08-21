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
**Note**: T009a (SVD) and T016 (Quantization) must run SEQUENTIALLY to avoid OOM on the 16GB runner. Do NOT run them in parallel.

- [X] T003 [P] Initialize Python project with pinned dependencies in `code/requirements.txt` (must include: `torch`, `diffusers`, `transformers`, `clip`, `lpips`, `numpy`, `pandas`, `pymc`, `arviz`, `scikit-learn`)
- [X] T004 [P] Create `code/config.yaml` containing the EXACT, FIXED list of test prompts and seed values to ensure reproducibility. **Prompt List**: `["oil painting", "watercolor", "cyberpunk", "pencil sketch", "ink wash", "acrylic", "charcoal", "pastel", "digital art", "concept art"]`. **Seed List**: `[42, 123, 456, 789, 101112]`. This file is the single source of truth for all generation tasks (FR-009, FR-003). **Dependencies: T034a** (Note: This task depends on the Pre-Phase Gate T034a to ensure the plan is ratified before defining experimental parameters. The task description explicitly defines the prompt list and seed values to ensure self-containment and reproducibility.)
- [X] T006 [P] Implement `code/state_manager.py` to handle SHA-256 hashing of artifacts and `state/artifacts.yaml` updates (FR-013)
- [ ] T007b-1 [P] Implement logic in `code/data_loader.py` to download the CollectionLoRA adapter from HuggingFace repository `stabilityai/stable-diffusion-1-5-lora-collection`. Logic MUST dynamically verify the repository exists. If the primary download fails, the script MUST raise a `ValueError` with the message "Failed to download CollectionLoRA adapter from primary source. Aborting." to enforce a "Fail Loudly" policy. Save the specific file `adapter_fp.safetensors` to `data/models/adapter_fp16.safetensors`. **Dependencies: T003** (Note: The known hash for verification is defined as a constant in `code/config.yaml`. No fallback to mirror URLs is permitted.)
- [ ] T007b-2 [P] Implement logic in `code/data_loader.py` to compute the SHA-256 hash of `data/models/adapter_fp16.safetensors` and record it in `state/artifacts.yaml` (FR-013, FR-010). **Dependencies: T007b-1**
- [X] T007c [P] Implement logic in `code/data_loader.py` to download the base model (Stable Diffusion 1.5) and compute its SHA-256 hash, recording it in `state/artifacts.yaml` (FR-013). If the download fails, raise a `ValueError` with the message "Failed to download base model from primary source. Aborting." **Dependencies: T003**
- [X] T007d [P] Implement logic in `code/data_loader.py` to validate that the downloaded adapter contains at least 5 distinct effects. Use regex `r"lora_unet_.*_(.+)_lora"` to identify unique effect prefixes. If an insufficient number of unique prefixes are found, raise `ValueError`. **Dependencies: T007b-2**
- [X] T008a [P] [Rev] Implement `code/error_handler.py` with a function `handle_memory_error(e: MemoryError)` that logs "Quantization Failure" and returns a skip flag. **Dependencies: T003**
- [X] T008b [P] [Rev] Integrate `handle_memory_error` into `code/main.py` wrapper logic to catch in-process `MemoryError` exceptions and handle subprocess Exit Code 137 (SIGKILL) by logging "Quantization Failure" and gracefully skipping the affected quantization level (FR-008). **Dependencies: T008a** <!-- FAILED: unspecified -->
- [ ] T009a [US3] Implement `code/data_loader.py` function to load `data/models/adapter_fp16.safetensors`. **Logic**: 1. **First**, extract per-effect LoRA weight matrices by grouping keys using regex `r"lora_unet_.*_(.+)_lora"` and splitting by the captured effect name. 2. Compute Singular Value Decomposition (SVD) on each matrix to determine effective subspace rank (tolerance=1e-5). 3. Save the computed subspace ranks directly to `data/subspace_ranks.json` in JSON format: `{"effect_name": rank_value,...}`. **Output Schema**: `{"oil_painting": 12, "watercolor": 8,...}`. 4. **Versioning**: Immediately compute the SHA-256 hash of `data/subspace_ranks.json` and record it in `state/artifacts.yaml` (FR-010, FR-013). **Dependencies: T007d** (Note: Run sequentially after validation to avoid OOM; do not run in parallel with T016. This task is NOT marked [P] to enforce sequential execution.) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T009b [P] [US3] Implement logic to load the subspace ranks from `data/subspace_ranks.json` (produced by T009a), validate the tolerance threshold used (1e-5), and ensure the file is checksummed in `state/artifacts.yaml` (FR-010, FR-007). **Dependencies: T009a**
- [X] T009c [P] Create `code/metrics.py` stub with imports for CLIP, LPIPS, and NumPy. **Dependencies: T003**
- [ ] T016 [US2] Implement `code/data_loader.py` function to apply zero-shot post-training quantization (higher-precision floating-point to lower-precision integer formats) using `torch.ao.quantization` with **static** quantization mode on CPU. **Config**: Use `qconfig=torch.ao.quantization.get_default_qconfig('x86')` and `backend='x86'`. **Logic**: 1. Create `data/quantized/` directory if missing. 2. Apply quantization to the ENTIRE LoRA adapter structure. 3. **Verification**: Load the resulting quantized adapter to verify it loads successfully on CPU and shapes match before saving. 4. **Error Handling**: Wrap the quantization logic in a `try/except` block. If `torch.ao.quantization` backend is unavailable (e.g., `RuntimeError`), log "Backend Unavailable" and skip the specific quantization level without crashing the pipeline (FR-008). **Output**: Save quantized adapters to `data/quantized/adapter_int8.safetensors` and `data/quantized/adapter_int4.safetensors` (FR-002). **Dependencies: T007b-2, T009a** (Note: Run sequentially after T009a to avoid OOM; this task is NOT marked [P] to enforce sequential execution.) <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T039 [P] [Rev] Create `code/validate_data.py` script to verify that the loaded CollectionLoRA adapter contains at least 5 distinct effects (identified by unique key prefixes in the state dict) as required by Assumption 011, failing fast if the threshold is not met. **Dependencies: T007b-2**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.
**Gate**: Phase 3 requires T039 to pass (validation). T016 (Quantization) can run in parallel with Phase 3 once T007b-2 is done.

---

## Phase 3: User Story 1 - Baseline Fidelity Measurement (Priority: P1) 🎯 MVP

**Goal**: Generate FP16 baseline images, extract CLIP embeddings, and compute cosine similarity to establish ground truth.

**Independent Test**: Can be fully tested by running the generation pipeline on the CPU-only runner with FP16 weights and verifying `data/results.csv` contains multiple rows with non-null similarity scores.

### Implementation for User Story 1

- [ ] T010b [US1] Implement `code/data_loader.py` function to load the verified FP16 adapter (`data/models/adapter_fp16.safetensors` from T007b-1) and base model (from T007c) into CPU memory. **Logic**: Use `device_map='cpu'` and `torch_dtype=torch.float16` when calling `from_pretrained` or `load_state_dict` to ensure models are loaded on CPU and not GPU (FR-001). **Dependencies: T007b-2, T007c** <!-- FAILED: unspecified -->
- [X] T011 [US1] Implement `code/generator.py` function to generate images using the FIXED prompt list from `code/config.yaml` (explicitly defined seeds and prompts) with the FP16 adapter loaded in T010b (FR-003, FR-009). **Dependencies: T010b, T004** (Note: T011 depends on T004 to load the prompt list and seeds from `code/config.yaml`.)
- [X] T011c [US1] Implement `code/generator.py` function to generate and save a set of "FP16 ReferenceImages" for *ALL* 10 effect prompts defined in T004. **Configuration**: Use `seed=43` (distinct from baseline seed (fixed random seed)), `resolution=512x512`, `sampler="euler"`, `steps=20`. Save to `data/references/fp16_refs/`. Organize these into a lookup table keyed by effect category. These are required for CESR calculation in US2 (FR-011, US-2). **Dependencies: T011** (Note: These reference images are generated with a different seed (43) than the baseline generation (seed 42) to ensure they are distinct samples.)
- [X] T011d [US1] Implement `code/data_loader.py` function to organize `data/references/fp16_refs/` into a lookup table keyed by effect category (e.g., `{"oil_painting": [img1, img2],...}`) to enable target-exclusion logic in T018. **Dependencies: T011c** <!-- FAILED: unspecified -->
- [X] T012 [US1] Implement `code/metrics.py` function to extract CLIP image embeddings and compute cosine similarity with prompt text embeddings (FR-004)
- [X] T013 [US1] Implement `code/metrics.py` function to compute LPIPS distance between generated FP16 images (from T011) and the FP16 ReferenceImages (from T011c). **Purpose**: This is a self-consistency check for US1 to verify the generation pipeline is functional, distinct from the FR-005 metric (Quantized vs FP16) computed in T019. **Dependencies: T011, T011c** (Note: This task computes a self-consistency check for US1, not the primary LPIPS metric for quantization comparison.)
- [ ] T014 [US1] Implement `code/main.py` logic to run FP16 generation, compute metrics, and save initial `data/results.csv` and `data/generated/` images. **CSV Schema**: The `results.csv` file MUST have the following columns: `prompt`, `seed`, `quantization_level`, `similarity_score`, `lpips_distance`, `cesr_score`, `image_path`. **Dependencies: T013, T012**
- [X] T015 [US1] Add logging for baseline generation steps and verify SHA-256 hashes of generated images in `state/artifacts.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantization Impact Analysis (Priority: P2)

**Goal**: Apply INT8/INT4 quantization, generate images, and measure concept adherence drop and concept bleeding (CESR).

**Independent Test**: Can be fully tested by running the quantization pipeline on the CPU runner, generating images, and verifying the delta in cosine similarity is recorded in `data/results.csv`.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/generator.py` function to generate images for INT8 and INT4 adapters using the same prompt list (FR-003). **Dependencies: T016**
- [X] T018 [US2] Implement `code/metrics.py` function to compute Cross-Effect Similarity Ratio (CESR) by comparing quantized output embeddings against the FP16 ReferenceImages (from `data/references/fp16_refs/` produced by T011c) for *other* effect prompts. **Logic**: Load lookup table from T011d, filter out the target prompt using string equality (`if ref.effect != target_prompt`), and compute cosine similarity. **Explicit Constraint**: Ensure the target prompt is strictly excluded from the reference set to prevent self-similarity bias (FR-011). If a reference image for the target prompt is missing, log a warning and skip that specific comparison. **Dependencies: T011d, T017, T016**
- [X] T019 [US2] Implement `code/metrics.py` function to compute LPIPS distance between quantized outputs and FP16 baseline outputs (FR-005). **Dependencies: T011** (Note: This task computes the primary LPIPS metric for quantization comparison, using the images generated by T011, not the metric from T013.)
- [ ] T020 [US2] Implement `code/main.py` logic to run quantized generations, handle `MemoryError` per level (using logic from T008b), compute deltas, and append to `data/results.csv`. **Dependencies: T018, T019**
- [X] T021 [US2] Implement logic to load per-effect LoRA subspace rank from `data/subspace_ranks.json` (produced by T009b) and prepare data for correlation analysis. **Input**: `data/subspace_ranks.json` (FR-010)
- [X] T022 [US2] Add logging for quantization steps and verify SHA-256 hashes of quantized weights and generated images

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bayesian Statistical Analysis (Priority: P3)

**Goal**: Perform Bayesian Hierarchical Model analysis and correlate subspace rank with concept bleeding.

**Independent Test**: Can be fully tested by running the statistical analysis script on `data/results.csv` and verifying `data/analysis_results.json` contains posterior distributions and correlation coefficients. Note: This task depends on the completion of Phase 3 and Phase 4 to ensure full dataset availability.

### Implementation for User Story 3

- [ ] T023 [P] [US3] Implement `code/statistical_analysis.py` to load `data/results.csv`, structure data for Bayesian Hierarchical Model, and EXPLICITLY extract the 'Effect' grouping variable. **Output Structure**: Create a pandas DataFrame with columns: `effect_id`, `similarity_score`, `quantization_level`, `seed`. This structure is required by `pymc`/`bambi` (FR-006, FR-012). **Dependencies: T014, T020**
- [X] T024 [US3] Implement `code/statistical_analysis.py` to define and run the Bayesian Hierarchical Model using `pymc`/`bambi` with PARTIAL POOLING. **Priors**: Weakly informative `Normal(0, 1)` for fixed effects, `HalfNormal(0.5)` for random effects (Plan Section 3.2). Test quantization effects and mitigate small sample size risks (FR-006, FR-012, Plan Section 5). **Model Formula**: `similarity_score ~ quantization_level + (1 | effect_id)`. **Output**: Must output posterior distributions AND the posterior width for the `Quantization_Effect` coefficient to enable FR-014 flagging (FR-006, FR-012). **Dependencies: T023** (Note: Model formula: `similarity_score ~ quantization_level + (1 | effect_id)`)
- [X] T025 [US3] Implement `code/statistical_analysis.py` to compute correlation between per-effect LoRA subspace rank (from `data/subspace_ranks.json` via T009b) and mean concept bleeding magnitude (derived from T018), explicitly testing significance via the Bayesian posterior distribution and reporting credible intervals (FR-007). **Dependencies: T009b, T018, T014, T020** (Note: The dependency on T024 is for the Bayesian correlation significance testing, not the correlation calculation itself.)
- [ ] T026 [US3] Implement `code/statistical_analysis.py` to read posterior width from T024 output; if width > 0.2 for the `Quantization_Effect` coefficient, flag the result as "Underpowered" in `analysis_results.json`. **Decision Rule**: 1. If HDI of quantization effect excludes zero, it is significant. 2. If width > 0.2, flag as underpowered (FR-014). **Dependencies: T024**
- [ ] T027 [US3] Implement `code/main.py` logic to execute the analysis script and save `data/analysis_results.json` with posterior means, credible intervals, and correlation stats
- [X] T028 [US3] Implement logic to generate a summary report or console output of the statistical findings

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T029 [P] Write unit tests for `code/metrics.py` functions (`cosine_similarity`, `lpips_distance`, `cesr_score`) in `tests/test_metrics.py`
- [ ] T030 [P] Write unit tests for `code/data_loader.py` (quantization loading) in `tests/test_quantization.py`
- [ ] T031a [P] [Rev] Define `.github/workflows/ci.yaml` to run the full pipeline and add a timing wrapper in `code/main.py` to measure total job duration. Verify duration ≤ 6 hours (SC-005) and generate `data/ci_report.json` with job duration and status. **Dependencies: T014, T020, T027** (Note: The `data/ci_report.json` file MUST have the following keys: `duration_seconds`, `status`, `timestamp`.)
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

---

## Dependencies & Execution Order

### Phase Dependencies

- **Pre-Phase Gate**: No dependencies - can start immediately, but BLOCKS Phase 2.
- **Setup (Phase 1)**: No dependencies - can start immediately (after Gate)
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires FP16 baseline data for delta/CESR calculation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires full dataset from US1 and US2

### Within Each User Story

- Models/Loaders before Generators
- Generators before Metrics
- Metrics before Analysis
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **T016 (Quantization) is now in Phase 2 and can run in parallel with Phase 3 (US1) once T007b-2 is complete.**
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

### Cross-Story Dependencies

- **T020 (US2)** depends on **T018** (CESR logic)
- **T025 (US3)** depends on **T009b** (US2) for subspace rank data to perform the correlation analysis.
- **T023 (US3)** depends on **T014** and **T020** (Data availability)
- **T018 (US2)** depends on **T011c** (ReferenceImage generation) and **T011d** (Organization)
- **T013 (US1)** depends on **T011** (Baseline generation)

### Resource Constraints
- **T009a (SVD)** and **T016 (Quantization)** are NOT marked [P] and should be run **sequentially** on the 16GB runner to avoid OOM errors.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Pre-Phase Gate (T034a)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

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
