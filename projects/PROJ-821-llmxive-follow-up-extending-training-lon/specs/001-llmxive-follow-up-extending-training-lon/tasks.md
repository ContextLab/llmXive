# Tasks: llmXive follow-up: extending "Training Long-Context Vision-Language Models Effectively with Generali"

**Input**: Design documents from `/specs/001-modality-balance-attention/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Generate and execute `code/scripts/init_dirs.py`: Create a Python script that programmatically creates all required directories (`code/`, `data/`, `data/synthetic/`, `data/synthetic/raw/`, `data/synthetic/short_context/`, `data/results/`, `data/results/logs/`, `data/results/aggregated/`, `tests/`, `models/`, `data/assets/`) and writes a success log to `data/.init_log.txt`. **Verification**: Run `python code/scripts/init_dirs.py` and confirm `data/.init_log.txt` exists.
- [X] T003 [P] Create `code/__init__.py` and `tests/__init__.py`

## Phase 1.5: Asset Preparation

**Purpose**: Ensure deterministic inputs for data generation

- [ ] T004 [P] [US1] Implement `code/scripts/generate_assets.py` to generate 20 fixed 336x336 images using Pillow. Images must be 'technical manual' style diagrams (grayscale gradients with OCR-readable text labels) to simulate complexity uniformly. **Specifics**: Use `PIL.ImageDraw` with a standard font (e.g., `DejaVuSans` or `Arial`), high contrast (black text on white background), and ensure text is legible. Save to `data/assets/img_00.png` to `data/assets/img_20.png`. **Crucial**: Generate `data/assets/manifest.json` listing filenames and SHA hashes for verification. **Verification**: Run script, confirm `manifest.json` exists with a set of entries

The research question, method, and references remain unchanged as no specific values were asserted in the original passage beyond the entry count, which has been generalized., and verify one image using `pytesseract` to ensure text is readable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Model Preparation (moved from Phase 4) to ensure availability for inference.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create `code/config.py` for hyperparameters, seeds, model paths, and Arm selection logic. **Must define `MODEL_ID = "mmpro/MMProLong-7B-1.0"` and `ARM_PRIMARY = "B"`**. **Verification**: Run `grep MODEL_ID code/config.py` and confirm it returns `mmpro/MMProLong-7B-1.0`.
- [X] T006 [P] Implement `code/__init__.py` and base logging infrastructure
- [ ] T007 [P] Setup environment configuration management (load `.env` if present, fallback to defaults)
- [X] T008 [P] Create base data entities: `code/data_generation/synthetic_sample.py` (attributes: `sample_id`, `text_token_count`, `image_count`, `visual_token_count`, `needle_location`, `needle_value`, `arm_type`, `total_context_tokens`). **Note**: `arm_type` added per Plan.md 'Dual-Arm design' requirement. Images are fetched from the fixed set in `data/assets/`. Text is generated via template-based synthetic text.
- [ ] T009 [P] Create base data entities: `code/inference/inference_result.py` (attributes: `sample_id`, `retrieved_value`, `is_correct`, `inference_time_ms`, `peak_memory_mb`)
- [ ] T040 [P] [US2] **Model Preparation**: Implement `code/inference/model_prep.py` to download **`mmpro/MMProLong-7B-1.0`** (per Spec FR-002) from HuggingFace and convert it to `Q4_K_M.gguf` format using `llama.cpp`, saving to `models/mmpro/MMProLong-7B-1.0-Q4_K_M.gguf`. **This task MUST run before T041.** **Verification**: Confirm file exists and has non-zero size.
- [ ] T015 [P] [P2] Implement `code/main.py` with orchestration logic and CLI argument parser (`--arm`, `--max_tokens`, `--dry-run`). **Depends on T005, T008, T011**. **Verification**: Run `python code/main.py --help` and confirm it prints usage help.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation with Controlled Modality Balance (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset where visual density varies across a range. **Arm B (Constant Total) is the PRIMARY arm for the hypothesis test** (per Plan), while Arm A (Constant Text) serves as the control (per Spec).

**Independent Test**: A script runs to generate a batch. Output validation confirms text-only token count variance <1% (Arm A) or total token variance <1% (Arm B), needle difficulty is identical, and visual token count varies exactly as specified.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/data_generation/generator.py` with Dual-Arm logic:
 - **Arm B (Primary)**: Constant total tokens (text + visual), variable images (0–20). **Logic**: Calculate `visual_tokens = image_count * 576` (approx 14x14 patches per 336x336 image at 24px patch size). Set `text_tokens = target_total - visual_tokens`. Use `tiktoken` to verify token counts.
 - **Arm A (Auxiliary)**: Constant text tokens, variable images (0–20). **Logic**: Set `text_tokens` to target value, `visual_tokens = image_count * 576`. Total context varies.
 - Ensure images are fixed resolution (336x336) and "needle" placement is deterministic.
 - **Crucial**: The generator must support a `--max_tokens` flag to handle both long-context (128K+) and short-context (≤4K) generation modes.
- [ ] T012 [P] [US1] Implement `code/data_generation/validators.py` to verify:
 - **Arm A**: Text-only token count variance <1% across samples.
 - **Arm B**: Total token count (text + visual) variance <1% across samples.
 - Visual token count matches image count * (336x336 resolution factor).
 - Needle difficulty score is identical across all samples.
- [ ] T013 [US1] Implement data storage logic in `code/data_generation/storage.py` to save generated samples as JSONL/Parquet in `data/synthetic/raw/` and `data/synthetic/short_context/`.
- [ ] T014 [US1] Add error handling for OOM or generation failures in `code/data_generation/generator.py` (log and skip).
- [ ] T047A [P] [US1] **Generate** the short-context control group (Arm A): 500 samples (≤4K tokens) with 1 image using `generator.py` with `--arm A --max_tokens 4096`, saving to `data/synthetic/short_context/short_control_arm_a.jsonl`. **Verification**: Run `wc -l data/synthetic/short_context/short_control_arm_a.jsonl` (must be 500) and `python code/data_generation/validators.py --file... --check-arm A`.
- [ ] T047B [P] [US1] **Generate** the short-context control group (Arm B): 500 samples (≤4K tokens) with variable images (0-5) using `generator.py` with `--arm B --max_tokens 4096`, saving to `data/synthetic/short_context/short_control_arm_b.jsonl`. **Verification**: Run `wc -l data/synthetic/short_context/short_control_arm_b.jsonl` (must be 500) and `python code/data_generation/validators.py --file... --check-arm B`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Feasible Inference and Retrieval Execution (Priority: P2)

**Goal**: Execute "needle-in-a-haystack" retrieval on the generated dataset using **`mmpro/MMProLong-7B-1.0`** (4-bit quantized via `llama-cpp-python`) on a 2-core CPU runner within 6 hours, with robust OOM handling. **Strictly adheres to Spec FR-002.**

**Independent Test**: A single sample processes end-to-end without OOM, completes within time limits, and outputs a binary retrieval result.

### Implementation for User Story 2

- [ ] T041 [P] [US2] Implement `code/inference/loader.py` to load `models/mmpro/MMProLong-7B-1.0-Q4_K_M.gguf` (generated by T040) with `llama-cpp-python` (CPU only). **Exclusive use of llama-cpp-python required. Model ID must match Spec FR-002: mmpro/MMProLong-7B-1.0.**
- [ ] T042 [US2] Implement `code/inference/runner.py` with:
 - Batch inference loop.
 - **OOM Guardrail**: Wrap inference calls in `try/except` blocks catching `RuntimeError` or `MemoryError`. On failure, log sample ID and memory state to `data/results/logs/oom_errors.log`, skip sample, and continue.
 - **Feasibility Gate**: Implement pilot run logic here to test memory feasibility on a single sample before full batch. **If pilot fails at 128K, automatically reduce target context to 64K and retry pilot. If 64K also fails, abort with error code 1. **
 - **Note**: T042 depends on T041 completion (sequential, not parallel).
- [ ] T043 [US2] Implement `code/inference/metrics.py` to calculate retrieval accuracy (binary match/no match against ground truth needle).
- [ ] T044 [US2] Integrate `code/inference/runner.py` into `code/main.py` to process `data/synthetic/` and write results to `data/results/aggregated/`.
- [ ] T045 [US2] Implement timing logic in `code/inference/runner.py` to ensure average time per sample meets a predefined efficiency threshold relative to the dataset size.
- [ ] T046 [US2] Implement inference logic to process short-context samples from `data/synthetic/short_context/` and write results to `data/results/short_context_raw.jsonl`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis of Modality Saturation (Priority: P3)

**Goal**: Aggregate retrieval accuracy by visual density bucket and perform Logistic Regression (with quadratic terms) and Jonckheere-Terpstra tests to detect non-linear degradation "cliffs".

**Independent Test**: A statistical script runs on mock data and correctly identifies non-linear trends and interaction p-values.

### Implementation for User Story 3

- [ ] T048 [P] [US3] Implement `code/analysis/aggregator.py` to group `InferenceResult` records by `DensityBucket` (e.g., varying image counts). **Note**: Can be developed in parallel with Phase 4, but executes after Phase 4 results are available.
- [ ] T049 [P] [US3] Implement `code/analysis/stats.py` with:
 - Logistic Regression model (Visual Density × Text Length interaction term). **Note**: Interaction term measured using full dataset (Arm A + Arm B) where text length varies (in Arm B) or via Arm B data where text length varies inversely with image count.
 - Quadratic term inclusion to detect "cliffs".
 - Jonckheere-Terpstra test for ordered alternatives.
- [ ] T050 [US3] Implement reporting logic in `code/analysis/stats.py` to output p-values, interaction coefficients, and explicit "non-linear degradation" flags to `data/results/aggregated/statistics.json`.
- [ ] T051 [US3] Create a CLI entry point in `code/main.py` to trigger analysis on `data/results/aggregated/` CSVs.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Short-Context Grounding Check (Priority: P4)

**Goal**: Evaluate short-context samples separately to ensure long-context failure is not due to general visual capability loss.

**Independent Test**: Short-context samples are processed and reported separately with ≥95% accuracy baseline check.

### Implementation for User Story 4

- [ ] T052 [P] [US4] Implement `code/analysis/short_context_reporter.py` to filter results from `data/results/short_context_raw.jsonl` (produced by T046) where `text_token_count` ≤ 4K.
- [ ] T053 [US4] Implement aggregation logic to calculate accuracy for short-context samples and compare against the established baseline.
- [ ] T054 [US4] Add short-context accuracy metrics to the final `data/results/aggregated/statistics.json` report, distinct from long-context metrics.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T055 [P] Documentation updates: Update `README.md` with CLI usage examples for `--arm A`, `--arm B`, and `--max_tokens`; Update `docs/quickstart.md` with the Feasibility Gate logic and short-context generation steps.
- [ ] T056 [P] Refactor `code/inference/runner.py` to use batched loading to optimize memory usage. **Verification**: Code review confirms batched loading implementation.
- [ ] T057 [P] Implement `code/scripts/memory_benchmark.py` to measure peak memory during a representative inference run. **Verification**: Run script and confirm `memory_report.json` shows peak memory < 7GB.
- [ ] T058 [P] Add unit tests for `code/data_generation/validators.py` in `tests/unit/test_validators.py`
- [ ] T059 [P] Add integration tests for inference pipeline in `tests/integration/test_inference_pipeline.py`
- [ ] T060 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T061 [P] Implement `code/main.py` `--hash-artifacts` step to compute SHA-256 for `data/` and `code/` and write to `state/artifact_hashes.json`. **Verification**: Run `python code/main.py --hash-artifacts` and confirm `state/artifact_hashes.json` is created with non-empty SHA-256 values.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (requires generated data) - Can run in parallel with US3 setup if data exists
- **User Story 3 (P3)**: Depends on US2 (requires inference results)
- **User Story 4 (P4)**: Depends on US2 (requires inference results, specifically short-context subset)

### Within Each User Story

- Models/Entities before services/generators
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel **ONLY if they do not share data schema dependencies** (e.g., T008 must complete before T011)
- Once Foundational phase completes, US1 and US2 (setup parts) can start in parallel
- US3 and US4 analysis scripts can be developed in parallel while US2 runs (but execute after)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create base data entities: SyntheticSample in code/data_generation/synthetic_sample.py"
Task: "Create base data entities: InferenceResult in code/inference/inference_result.py"

# Launch generator and validator in parallel (if data exists):
Task: "Implement generator.py in code/data_generation/generator.py"
Task: "Implement validators.py in code/data_generation/validators.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Generation)
4. **STOP and VALIDATE**: Test data generation logic and variable isolation independently
5. Deploy/demo if ready (data generation pipeline)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test data generation → Deploy (MVP!)
3. Add User Story 2 → Test inference pipeline → Deploy (Inference engine ready)
4. Add User Story 3 & 4 → Test analysis → Deploy (Full research pipeline)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Inference Engine & OOM Guards)
 - Developer C: User Story 3 & 4 (Analysis & Reporting)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (for development; execution order may differ)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: All tasks must run on 2-core CPU, ≤7GB RAM, no GPU. No 8-bit/4-bit CUDA dependencies.
- **CRITICAL**: No synthetic/fake data inputs. Use real image references (e.g., from NAB or fixed sample set) or strictly synthetic generation that mimics real distribution without fabricating "fake" results.
- **CRITICAL**: Task ordering respects data flow: Generation → Inference → Analysis.
- **NOTE**: The Plan mandates **Arm B (Constant Total)** as the PRIMARY arm for the hypothesis test. Tasks follow the Plan. **Note: Plan.md must be updated to match Spec FR-002 regarding the model ID.**
- **NOTE**: The Spec mandates `mmpro/MMProLong-7B-1.0` (FR-002). Tasks follow the Spec. **Note: Plan.md must be updated to reflect this model ID.**
- **NOTE**: The `data/assets/` directory must be populated with 20 complex diagrams (Task T004) before generation tasks run.
- **NOTE**: The model must be converted to `.gguf` (Task T040) before inference tasks run.
- **NOTE**: T015 (CLI) depends on T011 and T005. T042 (Runner) depends on T041 (Loader).
- **NOTE**: T008 (Entities) must be completed before T011 (Generator) can be implemented.