# Tasks: llmXive follow-up: extending "Visual Generation in the New Era: An Evolution from Atomic Mapping to "

**Input**: Design documents from `/specs/001-llmxive-followup/`
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

- [ ] T001 [Setup] Initialize project structure: Create all required directories defined in plan.md (`data/raw`, `data/derived/physics_constraints`, `data/derived/prompts`, `data/derived/generated_images`, `data/derived/evaluation_results`, `data/processed`, `code/simulation`, `code/generation`, `code/evaluation`, `code/analysis`, `code/utils`, `tests/contract`, `tests/integration`, `tests/unit`, `specs/001-llmxive-followup`, `specs/001-llmxive-followup/contracts`, `state/projects`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pymunk, diffusers, torch-cpu, ultralytics, scikit-learn, pandas, numpy, pyyaml, pillow, scikit-image).
- [X] T003 [P] Create linting and formatting configuration files: `ruff.toml` and `pyproject.toml` (Black configuration).
- [X] T004 [MUST run after T001] Create `code/utils/update_state.py` to calculate SHA-256 hashes of artifacts and update `state/...yaml`.
- [ ] T005 [P] Create `__init__.py` files for all code subdirectories (`simulation`, `generation`, `evaluation`, `analysis`).
- [X] T006 Create `tests/contract/test_schemas.py` to validate JSON against `specs/001-llmxive-followup/contracts/`.
- [ ] T007-config-create [P] Create `code/config.yaml` to manage random seeds, model paths, and configuration settings. Schema must include `seed`, `model_path`, `device`, and `paths` sections.
- [X] T008 Implement `code/main.py` orchestration skeleton with phase flags (sim, gen, eval, analyze).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Physics-Constrained Prompts (Priority: P1) 🎯 MVP

**Goal**: Simulate basic physics on CPU to generate JSON constraints and append natural language descriptors to text prompts.

**Independent Test**: Run `code/simulation/physics_engine.py` on a single CPU core with a sample CSV; verify output JSON files contain valid bounding boxes/collision rules and `code/generation/prompt_engine.py` successfully concatenates them.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [Depends on Phase 2 Completion] [US1] Contract test for `PhysicsConstraint` JSON schema in `tests/contract/test_schemas.py`.
- [X] T010 [Depends on Phase 2 Completion] [US1] Unit test for `pymunk` simulation logic in `tests/unit/test_physics_logic.py` (verify no contradictions).

### Implementation for User Story 1

- [ ] T011 [US1] [Independent] Generate `data/raw/scene_descriptions.csv` locally using a deterministic script with `seed=42` and predefined interaction templates (e.g., "A on B", "A next to B", "A under B") to create a 'curated' set of scenes. Do NOT fetch from external datasets. Validate that the generated set contains the necessary prepositions. Output file: `data/raw/scene_descriptions.csv`.
- [X] T012 [US1] [Depends on T011] Implement `code/simulation/physics_engine.py`: Load scene, run `pymunk` simulation, detect logical contradictions (cycles, impossible overlaps, A above B AND B above A), output `data/derived/physics_constraints/{scene_id}.json`. Log any contradictions to `data/derived/physics_constraints/contradiction_log.json`.
- [X] T013 [US1] [Depends on T011] Implement `code/generation/prompt_engine.py`: Read scene description + physics JSON, generate natural language descriptor, output `data/derived/prompts/{scene_id}_baseline.txt` and `data/derived/prompts/{scene_id}_experimental.txt`.
- [X] T013b [US1] [Depends on T011] [FR-011] Implement `code/generation/prompt_engine.py` (Control): Read scene description, generate length-matched random noise descriptor (Authorized by Plan's Matched Control Group requirement), output `data/derived/prompts/{scene_id}_control.txt`.
- [X] T016 [US1] [Depends on T012] Implement validation logic in `physics_engine.py` to exclude contradictory scenes and log them as "Invalid Physics Rules" to `data/derived/physics_constraints/contradiction_log.json` (FR-006). **Output**: `data/derived/physics_constraints/contradiction_log.json` (must be readable by T029-exclusion). Calculate contradiction rate using denominator = 'total valid scenes processed'.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Generate Image Baselines and Experimental Groups (Priority: P2)

**Goal**: Execute image generation using a CPU-optimized diffusion model (LCM-LoRA) with strict seed locking for Baseline, Experimental, and Control groups.

**Independent Test**: Run `code/generation/diffusion_runner.py` with N=5 scenes; verify three distinct image sets (Baseline vs. Exp vs. Control) are produced, seeds match, and process completes within time/memory limits without CUDA errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Integration test for generation pipeline in `tests/integration/test_pipeline.py` (small subset run).

### Implementation for User Story 2

- [X] T018 [US2] [Depends on T013, T013b, T019] Implement `code/generation/diffusion_runner.py`: Load CPU-optimized model ('latent-consistency/lcm-lora-sdv'), set random seeds using the manifest from T019, generate images from Baseline, Experimental, and Control prompt files. Ensure T013 and T013b are complete before execution.
- [ ] T019 [US2] [Depends on T007-config-create] Implement seed locking mechanism: Generate `data/derived/seed_manifest.json` containing identical seeds for Baseline and Experimental groups for each scene ID, and distinct but consistent seeds for the Control group. This artifact satisfies FR-007.
- [ ] T020 [US2] [Depends on T018] Implement retry logic (A limited number of attempts) for generation failures in `diffusion_runner.py`. If exceeded, log "Generation Failure" to `data/derived/generated_images/generation_failure_log.json` and mark the scene as failed (FR-006, Edge Case).
- [ ] T021 [US2] [Depends on T018] Save generated images to `data/derived/generated_images/{group}/{scene_id}.png`. Ensure all three groups (Baseline, Experimental, Control) are fully generated before marking task complete.
- [ ] T022-verify [US2] [Independent] Verify if LCM-LoRA supports deterministic seed locking (approximate vs exact). Output boolean flag to `data/derived/seed_lock_status.json`.
- [ ] T022-fallback [US2] [Depends on T018, T022-verify, T012] [Conditional] If T022-verify indicates approximate seed control, implement fallback: Render a "reference geometry" image (512x512) by projecting `pymunk` JSON bounding boxes onto a virtual canvas. Generate N=5 candidate images per prompt using the same seed. Calculate SSIM between each candidate and the reference geometry (512x512), select the candidate with the highest SSIM score, and save only that single image as `data/derived/generated_images/selected_{scene_id}.png`. Discard the other candidate(s). If T022-verify indicates exact locking, skip this task.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. **Must have generated images for Baseline, Experimental, AND Control groups.**

---

## Phase 5: User Story 3 - Evaluate Geometric Consistency and Statistical Significance (Priority: P3)

**Goal**: Extract bounding boxes using YOLOv8n, compare against physics JSON ground truth, calculate violation rates, and perform statistical analysis.

**Independent Test**: Feed pre-generated images with known violations into `code/evaluation/detector.py`; verify violation counts match manual inspection and `code/analysis/statistics.py` outputs a valid p-value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for `EvaluationResult` schema in `tests/contract/test_schemas.py`.
- [X] T025 [P] [US3] Unit test for Z-test/Fisher's Exact Test logic in `tests/unit/test_statistics.py`.

### Implementation for User Story 3

- [ ] T026 [US3] [Depends on T012, T021] Implement `code/evaluation/detector.py`: Load YOLOv8n (CPU), detect objects, extract bounding boxes, compare against `physics_constraints/{scene_id}.json` (relative to 512x512 output, IoU < 0.5 or Y-offset > 5px). Output bounding boxes to `data/derived/evaluation_results/{scene_id}_boxes.json`.
- [ ] T027 [US3] [Depends on T026] Implement violation logic: Count floating objects/interpenetration; default to violation if object confidence < 0.7 (Edge Case).
- [ ] T028 [US3] [Depends on T027] Save evaluation results to `data/derived/evaluation_results/{scene_id}.json` with violation flags and confidence distributions (FR-010).
- [ ] T029 [US3] [Independent] Implement `code/analysis/statistics.py` Power Analysis and Test Selection: Perform power analysis (effect_size=0.2, alpha=0.05, power_target=0.8) and output `data/processed/power_analysis_report.json`. If power < 0.8, log a WARNING but continue (soft fail) to align with N=100 scope. Check expected cell counts; if < 5, switch to Fisher's Exact Test; otherwise, use two-proportion z-test. Output results to `data/processed/statistical_test_results.json`.
- [ ] T029-exclusion [US3] [Depends on T016, T020, T028] Implement Exclusion Logic and Contradiction Rate Verification: Read contradiction logs from `data/derived/physics_constraints/contradiction_log.json` (produced by T016) and generation failure logs from `data/derived/generated_images/generation_failure_log.json` (produced by T020). Re-calculate contradiction rate. If rate > 5%, raise `StudyInvalidError` (Hard Fail) to halt pipeline. Identify corresponding scene IDs, exclude them from the final statistical denominator. Output exclusion list to `data/processed/exclusion_list.json`. Generate `data/processed/final_analysis.csv` with aggregated stats, p-values, and "Prompt Adherence Rate" labeling (FR-009).
- [ ] T030b [US3] [Depends on T029-exclusion] Implement Metric Labeling Enforcement: Ensure "Prompt Adherence Rate" is explicitly used as the label for violation metrics in `data/processed/power_analysis_report.json`, `data/derived/evaluation_results`, and `data/processed/final_analysis.csv`.
- [ ] T031a-gen [US3] [Independent] Generate `data/raw/validation_scenes.csv` locally using the same deterministic script and templates as T011 (seed=42) to create a held-out validation set of scenes. Output file: `data/raw/validation_scenes.csv`.
- [ ] T031a [US3] [Depends on T026, T031a-gen] Implement Validation Set & Threshold Derivation: Load `data/raw/validation_scenes.csv`, run detector (T026) on these scenes to calculate the detector's False Negative Rate (FNR), and derive the "predefined acceptable threshold" dynamically. Output threshold to `data/derived/evaluation_results/fnr_threshold.json`.
- [ ] T031 [US3] [Depends on T031a] Implement Correction Factor Logic: If the False Negative Rate (FNR) exceeds the derived threshold (from T031a), apply a conservative correction factor or switch to a qualitative 'Pass/Fail' assessment. Log correction to `data/derived/evaluation_results/correction_factor_log.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Update `README.md` with project overview, dependencies, and step-by-step execution instructions for the full pipeline; specifically update the "Results" and "Methodology" sections to reflect the N=100 scope and Control Group inclusion.
- [ ] T034 [P] Update `quickstart.md` with environment setup, CPU-only model download instructions, and N=100 run validation steps; ensure the "Expected Output" section lists the three groups (Baseline, Experimental, Control).
- [ ] T035 [P] Create `scope_justification.md` artifact explaining the deviation from N=500 to N=100 due to compute constraints and citing the plan.md constraints.
- [ ] T036 Code cleanup and refactoring of `code/` modules.
- [ ] T037 Performance optimization for CPU generation batch sizes.
- [ ] T038 [P] Additional unit tests in `tests/unit/`.
- [ ] T039 Security hardening (input validation for prompts).
- [ ] T040 [P] Run `quickstart.md` validation and verify full pipeline on N=100.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (prompts for Baseline, Experimental, AND Control groups)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (images) and US1 output (physics JSON)

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
Task: "Contract test for PhysicsConstraint JSON schema in tests/contract/test_schemas.py"
Task: "Unit test for pymunk simulation logic in tests/unit/test_physics_logic.py"

# Launch all models for User Story 1 together:
Task: "Generate data/raw/scene_descriptions.csv locally"
Task: "Implement code/simulation/physics_engine.py"
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
- **CRITICAL**: All image generation tasks (T018-T021) must strictly adhere to CPU-only constraints (no CUDA, no 8-bit quantization requiring bitsandbytes). Use distilled models (LCM-LoRA) only.
- **CRITICAL**: Dataset download/fetch tasks must use real, reachable URLs or package fetchers (e.g., `datasets.load_dataset`), never synthetic/fake data. **Exception**: T011 and T031a-gen use local deterministic generation to satisfy the 'curated' assumption without external dependencies.
- **CRITICAL**: Task ordering respects data flow: Physics JSON (US1) must be generated before Prompts (US1) which must be generated before Images (US2) which must be generated before Evaluation (US3).
- **CRITICAL**: T004 MUST run after T001 (sequential dependency).
- **CRITICAL**: T009/T010 depend on Phase 2 completion.
- **CRITICAL**: T012/T013 depend on T011.
- **CRITICAL**: T026 depends on T012 and T021.
- **CRITICAL**: T029-exclusion depends on T016 and T020.
- **CRITICAL**: T029 must output `power_analysis_report.json` as a mandatory deliverable.
- **CRITICAL**: T031 must switch to 'Pass/Fail' if FNR > derived threshold.
- **CRITICAL**: T022-fallback must use 512x512 resolution for SSIM calculation.
- **CRITICAL**: T035 must document the N=100 scope reduction.
- **CRITICAL**: T022-fallback must explicitly calculate "reference geometry" by projecting `pymunk` JSON to a virtual canvas (512x512) before calculating SSIM.
- **CRITICAL**: T011 must explicitly use local generation with seed=42.
- **CRITICAL**: T029 must implement a 'soft fail' (warning) if power < 0.8.
- **CRITICAL**: T029-exclusion must enforce a 'hard fail' if contradiction rate > 5%.
- **CRITICAL**: T031a-gen must generate the validation set locally.
- **CRITICAL**: T022-verify must determine if fallback is needed.