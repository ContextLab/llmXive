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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `code/` directory at repository root
- [X] T001b [P] Create `data/` directory at repository root
- [X] T001c [P] Create `state/` directory at repository root
- [X] T001d [P] Create `tests/` directory at repository root
- [X] T002 [P] Create empty `__init__.py` files in `code/`, `data/`, `state/`, `tests/` to ensure Python package recognition

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (must include: `torch`, `diffusers`, `transformers`, `clip`, `lpips`, `numpy`, `pandas`, `pymc`, `arviz`, `scikit-learn`)
- [X] T004 [P] Create `code/config.yaml` containing a list of distinct effect prompts and seed values for deterministic generation.
- [X] T006 [P] Implement `code/state_manager.py` to handle SHA-256 hashing of artifacts and `state/artifacts.yaml` updates (FR-013)
- [ ] T007 [P] Create `code/data_loader.py` with logic to download base model (SD 1.5/2.1) and CollectionLoRA adapter from HuggingFace without GPU (FR-001)
- [ ] T007b [P] Implement logic in `code/data_loader.py` (or `main.py` setup) to rename/copy the downloaded CollectionLoRA adapter to `data/models/adapter_fp16.safetensors` and immediately compute its SHA-256 hash, recording it in `state/artifacts.yaml` (FR-013, FR-010)
- [ ] T008 [P] Implement `code/main.py` wrapper logic to catch in-process `MemoryError` exceptions and handle subprocess Exit Code 137 (SIGKILL) by logging "Quantization Failure" and gracefully skipping the affected quantization level (FR-008). **Note: This is the sole mechanism for OOM handling; no shell scripts are used.**
- [ ] T009 [P] Implement `code/data_loader.py` function to load `data/models/adapter_fp16.safetensors`, extract per-effect LoRA weight matrices, compute their Singular Value Decomposition (SVD) to determine effective subspace rank (tolerance threshold), and save results to `data/subspace_ranks.json` (FR-010, FR-007). **Dependencies: T007b**
- [X] T009b [P] Create `code/metrics.py` stub with imports for CLIP, LPIPS, and NumPy

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Fidelity Measurement (Priority: P1) 🎯 MVP

**Goal**: Generate FP16 baseline images, extract CLIP embeddings, and compute cosine similarity to establish ground truth.

**Independent Test**: Can be fully tested by running the generation pipeline on the CPU-only runner with FP16 weights and verifying `data/results.csv` contains multiple rows with non-null similarity scores.

### Implementation for User Story 1

- [~] T010 [US1] Implement `code/data_loader.py` function to load FP16 CollectionLoRA adapter (`data/models/adapter_fp16.safetensors`) and base model into CPU memory. **Extends T007**: Utilizes the download logic from T007 to fetch the adapter if missing, then loads it into CPU memory (FR-001) <!-- ATOMIZE: requested -->
- [~] T011 [US1] Implement `code/generator.py` function to generate images using the fixed prompt list from `config.yaml` with FP16 adapter (FR-003, FR-009) <!-- ATOMIZE: requested -->
- [~] T011b [US1] Implement `code/generator.py` function to generate a single "known reference" image using a fixed seed (from `config.yaml`) and save it to `data/references/baseline_ref.png`. This image serves as the ground truth for LPIPS self-consistency checks in T013 (US-1, FR-005) <!-- FAILED: unspecified -->
- [X] T011c [US1] Implement `code/generator.py` function to generate and save a set of "FP16 ReferenceImages" for *all* effect prompts in `data/references/fp16_refs/`. These are required for CESR calculation in US2 (FR-011, US-2). **Dependencies: T011**
- [X] T012 [US1] Implement `code/metrics.py` function to extract CLIP image embeddings and compute cosine similarity with prompt text embeddings (FR-004)
- [~] T013 [US1] Implement `code/metrics.py` function to compute LPIPS distance between generated FP16 images and the reference image `data/references/baseline_ref.png` (produced by T011b) to verify pipeline functionality (US-1, FR-005). **Dependencies: T011b**
- [~] T014 [US1] Implement `code/main.py` logic to run FP16 generation, compute metrics, and save initial `data/results.csv` and `data/generated/` images
- [X] T015 [US1] Add logging for baseline generation steps and verify SHA-256 hashes of generated images in `state/artifacts.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantization Impact Analysis (Priority: P2)

**Goal**: Apply INT8/INT4 quantization, generate images, and measure concept adherence drop and concept bleeding (CESR).

**Independent Test**: Can be fully tested by running the quantization pipeline on the CPU runner, generating images, and verifying the delta in cosine similarity is recorded in `data/results.csv`.

### Implementation for User Story 2

- [~] T016 [P] [US2] Implement `code/data_loader.py` function to apply zero-shot post-training quantization (FP16 -> INT8/INT4) using `torch.ao.quantization` on CPU. **Output**: Save quantized adapters to `data/quantized/adapter_int8.safetensors` and `data/quantized/adapter_int4.safetensors` (FR-002)
- [X] T017 [US2] Implement `code/generator.py` function to generate images for INT8 and INT4 adapters using the same prompt list (FR-003)
- [X] T018 [US2] Implement `code/metrics.py` function to compute Cross-Effect Similarity Ratio (CESR) by comparing quantized output embeddings against the FP16 ReferenceImages (from `data/references/fp16_refs/` produced by T011c) for *other* effect prompts (excluding the target prompt) to detect concept bleeding (FR-011). **Dependencies: T011c**
- [X] T019 [US2] Implement `code/metrics.py` function to compute LPIPS distance between quantized outputs and FP16 baseline outputs (FR-005). **Dependencies: T011**
- [~] T020 [US2] Implement `code/main.py` logic to run quantized generations, handle `MemoryError` per level (using logic from T008), compute deltas, and append to `data/results.csv`
- [ ] T021 [US2] Implement logic to load per-effect LoRA subspace rank from `data/subspace_ranks.json` (produced by T009) and prepare data for correlation analysis. **Input**: `data/subspace_ranks.json` (FR-010)
- [~] T022 [US2] Add logging for quantization steps and verify SHA-256 hashes of quantized weights and generated images

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bayesian Statistical Analysis (Priority: P3)

**Goal**: Perform Bayesian Hierarchical Model analysis and correlate subspace rank with concept bleeding.

**Independent Test**: Can be fully tested by running the statistical analysis script on `data/results.csv` and verifying `data/analysis_results.json` contains posterior distributions and correlation coefficients. Note: This task depends on the completion of Phase 3 and Phase 4 to ensure full dataset availability.

### Implementation for User Story 3

- [~] T023 [P] [US3] Implement `code/statistical_analysis.py` to load `data/results.csv` and structure data for Bayesian Hierarchical Model (images nested within prompts). **Dependencies: Phase 3, Phase 4**
- [X] T024 [US3] Implement `code/statistical_analysis.py` to define and run the Bayesian Hierarchical Model using `pymc`/`bambi` to test quantization effects (FR-006, FR-012)
- [~] T025 [US3] Implement `code/statistical_analysis.py` to compute correlation between per-effect LoRA subspace rank (from `data/subspace_ranks.json` via T021) and mean concept bleeding magnitude, explicitly testing significance via the Bayesian posterior distribution and reporting 95% credible intervals (FR-007)
- [X] T026 [US3] Implement `code/statistical_analysis.py` to perform posterior width analysis and explicitly flag results as "Underpowered" if credible interval width > 0.2 (FR-014)
- [~] T027 [US3] Implement `code/main.py` logic to execute the analysis script and save `data/analysis_results.json` with posterior means, credible intervals, and correlation stats
- [~] T028 [US3] Implement logic to generate a summary report or console output of the statistical findings

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T029 [P] Write unit tests for `code/metrics.py` functions (`cosine_similarity`, `lpips_distance`, `cesr_score`) in `tests/test_metrics.py`
- [ ] T030 [P] Write unit tests for `code/data_loader.py` (quantization loading) in `tests/test_quantization.py`
- [ ] T031 Run end-to-end validation on `ubuntu-latest` runner to verify total job duration ≤ 6 hours (SC-005)
- [ ] T032 Update `docs/quickstart.md` with instructions for running the pipeline on CPU-only runners
- [ ] T033 Final review of `state/artifacts.yaml` to ensure all model weights and data artifacts are checksummed
- [ ] T034 Draft Constitution Amendment for Principle VII to replace "repeated-measures ANOVA" with "Bayesian Hierarchical Model" and update `plan.md` to reflect "PENDING AMENDMENT" status (FR-006, Constitution Check)

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
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

### Cross-Story Dependencies

- **T020 (US2)** depends on **T018** (CESR logic)
- **T025 (US3)** depends on **T009** (US2) for subspace rank data to perform the correlation analysis.
- **T023 (US3)** depends on **Phase 3** and **Phase 4** completion (Data availability)
- **T018 (US2)** depends on **T011c** (ReferenceImage generation)
- **T013 (US1)** depends on **T011b** (Baseline reference generation)

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
