# Tasks: Quantization Robustness of Multi-Effect LoRA Adapters

**Input**: Design documents from `/specs/001-lora-quantization-robustness/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `state/`, `tests/`)
- [ ] T002 Initialize a Python project with pinned dependencies in `code/requirements.txt` (torch-cpu, diffusers, transformers, clip, lpips, pymc, pandas, numpy, scikit-learn)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes CPU Feasibility Hardening, Data Persistence, and Spec/Plan Resolution.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config.yaml` with a deterministic seed list containing a diverse set of distinct prompts, model paths (SD 1.5/2.1, CollectionLoRA HF ID), and output paths. Create `data/prompts.txt` containing the explicit list of 10 distinct prompts and effect categories to ensure reproducibility (FR-009).
- [ ] T005 [P] Implement `code/data_loader.py` to load base model and CollectionLoRA adapter into CPU memory (FR-001) with OOM handling (FR-008)
- [ ] T006 [P] Implement `code/state_manager.py` to compute SHA-256 hashes for artifacts and manage `state/artifacts.yaml` (FR-013)
- [ ] T007 [P] Create base entity dataclasses in `code/models.py` (EffectAdapter, ReferenceImage, GenerationResult, AnalysisMetric, StateRecord) following the exact schema definitions (fields, types, validation) in `specs/001-lora-quantization-robustness/data-model.md`.
- [ ] T008 [P] Implement `code/main.py` orchestration skeleton: Add `try/except` block catching `MemoryError`, logging "Quantization Failure" to stderr, implementing state logic to skip the affected quantization level and continue the pipeline, returning exit code 0 if other steps succeed or 1 if all fail (FR-008)
- [ ] T009 [P] Implement `code/quantization_utils.py` for zero-shot FP16 -> INT8/INT4 conversion using `torch.ao.quantization` (FR-002, Assumption 6)
- [ ] T009b [P] [Foundational] Implement `code/data_loader.py` function `compute_and_persist_ranks`: Compute effective LoRA subspace rank via SVD on each per-effect weight matrix with tolerance 1e-5 (FR-010). Input: per-effect weight matrices from loaded adapter. Output: `data/subspace_ranks.json` with schema: `{ "effect_id": str, "rank": int, "tolerance": float }`. This must run immediately after model loading to prevent data loss on crash (FR-007).
- [ ] T038 [P] [Foundational] Implement `code/memory_guard.py` with explicit `torch.cuda.empty_cache()` (no-op on CPU) and manual garbage collection triggers after every image generation batch to reclaim RAM before the next quantization level starts (FR-001, Edge Case 1)
- [ ] T038a [P] [Foundational] Implement logic to update `specs/001-lora-quantization-robustness/spec.md` Assumption 1 to explicitly reflect the 7GB Free Tier RAM constraint (replacing the 16GB assumption) to resolve the contradiction between Spec and Plan (FR-001, SC-005).
- [ ] T039 [P] [Foundational] Implement `code/data_loader.py` logic to fetch the CollectionLoRA adapter from a specific HuggingFace URL (e.g., `huggingface_hub.snapshot_download`) rather than a generic "download from UCI" placeholder, ensuring the URL is reachable and the file size is < 2GB (Assumption 4, Data Hygiene)
- [ ] T040 [P] [Foundational] Implement `code/quantization_utils.py` fallback logic: If `torch.ao.quantization` fails due to backend unavailability, automatically switch to `torch.quantization` (deprecated but CPU-safe) OR skip the specific level with a "Backend Unavailable" log entry. If fallback is used, implement a "Noise Validation Check" to verify noise profile matches `torch.ao` (Assumption 6, Edge Case 3, Constitution VI).
- [ ] T043 [P] [Foundational] Implement `code/main.py` function `preflight_memory_check`: Query `psutil.virtual_memory().available` before loading the base model; if < 4GB, abort immediately with a "Insufficient RAM" error to prevent a 6-hour hang (FR-001, Edge Case 1)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Fidelity Measurement (Priority: P1) 🎯 MVP

**Goal**: Generate a set of images using FP16 CollectionLoRA, extract CLIP embeddings, and compute cosine similarity to establish ground-truth baseline.

**Independent Test**: Run `python code/main.py --mode baseline` on CPU; verify `data/results.csv` contains 10 rows with non-null cosine similarity scores AND `data/reference_images/` contains FP16 images for all effects AND CESR logic is verifiable within this phase.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test for CLIP embedding extraction in `tests/unit/test_metrics.py`
- [ ] T011 [P] [US1] Unit test for cosine similarity calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/metrics.py` functions: `extract_clip_embedding`, `compute_cosine_similarity` (FR-004)
- [ ] T013 [US1] Implement `code/generator.py` function `generate_baseline_images` (FP16 only) using prompts from `config.yaml` (FR-003, FR-009)
- [ ] T013b [US1] Implement `code/generator.py` function `generate_cross_effect_references`: Generate images for ALL effect prompts using FP16 adapter to create the reference pool for CESR calculation. Logic must read effect list from `data/prompts.txt` or config, distinguish 'test prompts' from 'effect prompts', generate images, and explicitly compute the "other prompt" filter (excluding the target prompt ID) to store ReferenceImages with `target_id` and `other_ids` metadata (FR-011, US-1).
- [ ] T014 [US1] Implement LPIPS distance calculation in `code/metrics.py` for self-consistency check (FR-005)
- [ ] T015a [US1] Implement `code/generation.py` function `generate_fp16_batch`: Generate a set of FP16 images for target prompts, return list of image paths (US-1, FR-003)
- [ ] T015b [US1] Implement `code/metrics.py` function `compute_baseline_metrics`: Compute CLIP cosine similarity and LPIPS for the generated batch, return list of metric dicts (US-1, SC-001)
- [ ] T015c [US1] Implement `code/data_io.py` function `append_baseline_results`: Append the computed baseline metrics to `data/results.csv` (creating file if missing) and verify all rows have non-null cosine similarity scores (US-1, SC-001, FR-008)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantization Impact Analysis (Priority: P2)

**Goal**: Apply INT8/INT4 quantization, generate images, and measure fidelity drop (concept adherence and pixel fidelity).

**Independent Test**: Run `python code/main.py --mode quantize`; verify `data/results.csv` is appended with INT8/INT4 rows and delta metrics are computed.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for quantization loading (INT8/INT4) in `tests/unit/test_quantization.py`
- [ ] T018 [P] [US2] Integration test for quantized generation loop in `tests/integration/test_quantization_flow.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/quantization_utils.py` function `apply_zero_shot_quantization`: Use `torch.ao.quantization.prepare` and `torch.ao.quantization.convert` with default observers to convert FP16 LoRA to INT8/INT4 without gradient updates (FR-002, Assumption 6)
- [ ] T020 [US2] Implement `code/generator.py` function `generate_quantized_images` (loops through INT8/INT4 adapters) (FR-003)
- [ ] T021 [US2] Implement `code/metrics.py` function `calculate_cesr`: Compute Cross-Effect Similarity Ratio by comparing quantized output embeddings to FP16 ReferenceImage embeddings of *other* effect prompts (FR-011, US-2). Note: Uses ReferenceImages generated in T013b with pre-filtered `other_ids`.
- [ ] T021b [US2] Implement `code/metrics.py` helper `filter_other_prompts`: Logic to aggregate pre-computed `other_ids` metadata from T013b (simplified from previous version as filtering is now done in T013b) (FR-011)
- [ ] T021c [US2] Implement `code/metrics.py` helper `aggregate_cesr`: Logic to aggregate similarities across the filtered set of "other" prompts to produce a single CESR score (FR-011)
- [ ] T022a [US2] Implement `code/main.py` function `run_quantization_pipeline`: Load FP16 -> Apply Quantization (INT8/INT4) -> Generate Images. Returns list of image paths and writes results to `data/results.csv` (FR-003)
- [ ] T022b [US2] Implement `code/main.py` function `compute_quantization_metrics`: Compute Cosine Similarity, LPIPS, and CESR for quantized outputs, compute delta vs FP16 baseline (FR-004, FR-005, FR-011)
- [ ] T022c [US2] Implement `code/main.py` function `append_quantization_results`: Append quantized metrics to `data/results.csv` with error handling to skip rows if quantization failed (FR-008)
- [ ] T023 [US2] Implement error handling in generation loop to catch `MemoryError` and log "Quantization Failure" flag instead of crashing (FR-008)
- [ ] T024 [US2] Verify delta calculation (FP16 vs Quantized) handles zero-difference cases without division errors (Edge Case 2)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bayesian Statistical Analysis & Subspace Correlation (Priority: P3)

**Goal**: Perform Bayesian Hierarchical Model analysis and correlate LoRA subspace rank with concept bleeding.

**Independent Test**: Run `python code/statistical_analysis.py`; verify `data/analysis_results.json` contains posterior distributions and correlation coefficients.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for Bayesian model structure in `tests/unit/test_statistics.py`
- [ ] T026 [P] [US3] Unit test for correlation calculation and credible interval extraction in `tests/unit/test_statistics.py`

### Implementation for User Story 3

- [ ] T027a [US3] Implement Constitution Amendment Procedure: Create a PR and Sync Impact Report to formally override Constitution Principle VII (ANOVA) in favor of Bayesian Hierarchical Model (BHM) as required by FR-006 and Plan.md Constitution Check (FR-006, US-3).
- [ ] T027 [P] [US3] Implement `code/data_loader.py` function `load_effect_ranks`: Load pre-computed LoRA subspace ranks from `data/subspace_ranks.json` (computed in T009b) for correlation analysis (FR-010, US-3).
- [ ] T028 [US3] Implement `code/statistical_analysis.py` Bayesian Hierarchical Model (BHM) using `pymc` or `bambi` (US-3, FR-006, FR-012)
- [ ] T029 [US3] Implement correlation analysis in `code/statistical_analysis.py`: Rank vs. Bleeding Magnitude (FR-007, US-3)
- [ ] T030 [US3] Implement Posterior Width Analysis: Check if credible interval width > 0.2; if so, flag result as "Underpowered" (FR-014, SC-003)
- [ ] T031a [US3] Implement `code/statistical_analysis.py` function `load_results_data`: Load and parse `data/results.csv` into a Pandas DataFrame (SC-001)
- [ ] T031b [US3] Implement `code/statistical_analysis.py` function `run_bhm_sampling`: Define BHM model structure and execute sampling (US-3, FR-006)
- [ ] T031c [US3] Implement `code/statistical_analysis.py` function `compute_correlation_analysis`: Compute correlation between rank and bleeding magnitude with 95% credible intervals (FR-007)
- [ ] T031d [US3] Implement `code/statistical_analysis.py` function `serialize_analysis_results`: Save posterior distributions, correlation coefficients, and flags to `data/analysis_results.json` (SC-003, SC-004)
- [ ] T032 [US3] Generate final report summary in `data/report.md` including sections: 'Posterior Means', 'Credible Intervals', 'Correlation Analysis', and 'Underpowered Flags'. Map JSON keys from `data/analysis_results.json` to these sections explicitly (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Run `pytest` suite to ensure all unit and integration tests pass
- [ ] T034 Verify `state/artifacts.yaml` contains valid SHA-256 hashes for all models and generated data (FR-013)
- [ ] T035 Update `quickstart.md` with instructions to run the full pipeline on CPU-only runner
- [ ] T036 Validate total job duration on GitHub Actions `ubuntu-latest` runner is ≤ 6 hours (SC-005)
- [ ] T037 Ensure `data/results.csv` and `data/analysis_results.json` are correctly formatted and traceable to code (Constitution Principle IV)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes CPU Hardening and Spec/Plan Resolution.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Independent Test now includes CESR baseline generation.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 baseline generation for comparison metrics
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 results data. **Requires Constitution Amendment (T027a) first.**

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
Task: "Unit test for CLIP embedding extraction in tests/unit/test_metrics.py"
Task: "Unit test for cosine similarity calculation in tests/unit/test_metrics.py"

# Launch all models for User Story 1 together:
Task: "Implement code/metrics.py functions"
Task: "Implement code/generator.py function generate_baseline_images"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (including CESR baseline)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (includes RAM hardening)
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
   - Developer C: User Story 3 (starts after T027a Constitution Amendment)
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
- **Critical**: Phase 2 now includes all CPU Feasibility and Spec/Plan Resolution tasks to prevent OOM and specification drift.