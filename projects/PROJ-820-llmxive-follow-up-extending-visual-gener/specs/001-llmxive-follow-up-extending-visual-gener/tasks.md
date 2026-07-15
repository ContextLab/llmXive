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

- [X] T001a [Setup] Create `data/raw` directory.
- [X] T001b [Setup] Create `data/derived/physics_constraints` directory.
- [X] T001c [Setup] Create `data/derived/prompts` directory.
- [X] T001d [Setup] Create `data/derived/generated_images` directory.
- [X] T001e [Setup] Create `data/derived/evaluation_results` directory.
- [X] T001f [Setup] Create `data/processed` directory.
- [ ] T001g [Setup] Create `code/simulation` directory.
- [ ] T001h [Setup] Create `code/generation` directory.
- [ ] T001i [Setup] Create `code/evaluation` directory.
- [ ] T001j [Setup] Create `code/analysis` directory.
- [ ] T001k [Setup] Create `code/utils` directory.
- [ ] T001l [Setup] Create `tests/contract` directory.
- [~] T001m [Setup] Create `tests/integration` directory.
- [~] T001n [Setup] Create `tests/unit` directory.
- [~] T001o [Setup] Create `specs/001-llmxive-followup` directory.
- [~] T001p [Setup] Create `specs/001-llmxive-followup/contracts` directory.
- [~] T001q [Setup] Create `state/projects` directory.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pymunk, diffusers, torch-cpu, ultralytics, scikit-learn, pandas, numpy, pyyaml)
- [~] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [MUST run after T001a-T001q] Create `code/utils/update_state.py` to calculate SHA-256 hashes of artifacts and update `state/...yaml`
- [X] T005a [P] Create `code/simulation/__init__.py`
- [X] T005b [P] Create `code/generation/__init__.py`
- [X] T005c [P] Create `code/evaluation/__init__.py`
- [X] T005d [P] Create `code/analysis/__init__.py`
- [X] T006 Create `tests/contract/test_schemas.py` to validate JSON against `specs/001-llmxive-followup/contracts/`
- [~] T007 Setup environment configuration management for random seeds and model paths
- [X] T008 Implement `code/main.py` orchestration skeleton with phase flags (sim, gen, eval, analyze)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Physics-Constrained Prompts (Priority: P1) 🎯 MVP

**Goal**: Simulate basic physics on CPU to generate JSON constraints and append natural language descriptors to text prompts.

**Independent Test**: Run `code/simulation/physics_engine.py` on a single CPU core with a sample CSV; verify output JSON files contain valid bounding boxes/collision rules and `code/generation/prompt_engine.py` successfully concatenates them.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [Depends on Phase 2 Completion] [US1] Contract test for `PhysicsConstraint` JSON schema in `tests/contract/test_schemas.py`
- [X] T010 [Depends on Phase 2 Completion] [US1] Unit test for `pymunk` simulation logic in `tests/unit/test_physics_logic.py` (verify no contradictions)

### Implementation for User Story 1

- [ ] T011 [US1] Create `data/raw/scene_descriptions.csv` with a curated set of 100 scene descriptions (N=100 scope). Fetch from a real, physics-inferable source (e.g., `datasets.load_dataset('coco-captions', split='train', trust_remote_code=True)` filtered for object interaction scenes). If fetch fails, execute a deterministic script using a fixed seed and predefined interaction templates (e.g., "A on B", "A next to B") to generate valid scenes, ensuring no hallucinated external datasets.
- [~] T012 [US1] [Depends on T011] Implement `code/simulation/physics_engine.py`: Load scene, run `pymunk` simulation, detect logical contradictions (cycles, impossible overlaps, A above B AND B above A), output `data/derived/physics_constraints/{scene_id}.json`. Log any contradictions to `data/derived/physics_constraints/contradiction_log.json`.
- [X] T013 [US1] [Depends on T011] Implement `code/generation/prompt_engine.py`: Read scene description + physics JSON, generate natural language descriptor, output `data/derived/prompts/{scene_id}_{group}.txt` (Baseline, Experimental).
- [X] T013b [US1] [Depends on T011] Implement `code/generation/prompt_engine.py` (Control): Read scene description, generate length-matched random noise descriptor, output `data/derived/prompts/{scene_id}_control.txt`.
- [~] T014 [US1] Add validation logic in `physics_engine.py` to exclude contradictory scenes and log them as "Invalid Physics Rules" (FR-006).
- [~] T015 [US1] Add error handling for missing scene descriptions or simulation failures.
- [ ] T016 [US1] [Depends on T012] Implement logic to aggregate contradiction logs from `data/derived/physics_constraints/contradiction_log.json`, calculate contradiction rate percentage, and verify it is < 5% (SC-004); if rate > 5%, flag the study (soft fail) but continue to allow downstream analysis to halt the pipeline if required.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Generate Image Baselines and Experimental Groups (Priority: P2)

**Goal**: Execute image generation using a CPU-optimized diffusion model (LCM-LoRA) with strict seed locking for Baseline, Experimental, and Control groups.

**Independent Test**: Run `code/generation/diffusion_runner.py` with N=5 scenes; verify three distinct image sets (Baseline vs. Exp vs. Control) are produced, seeds match, and process completes within time/memory limits without CUDA errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Integration test for generation pipeline in `tests/integration/test_pipeline.py` (small subset run)

### Implementation for User Story 2

- [ ] T018 [US2] [Depends on T013, T013b] Implement `code/generation/diffusion_runner.py`: Load CPU-optimized model ('latent-consistency/lcm-lora-sdv1-5'), set random seeds, generate images from Baseline, Experimental, and Control prompt files. Ensure T013 and T013b are complete before execution.
- [~] T019 [US2] Implement seed locking mechanism ensuring Baseline and Experimental groups use identical seeds for the same scene ID (FR-007).
- [~] T019b [US2] Implement seed locking for Control group (distinct from Baseline/Exp but consistent within Control).
- [~] T020 [US2] Implement retry logic (max attempts) for generation failures and log "Generation Failure" if exceeded (FR-006, Edge Case).
- [~] T021 [US2] Save generated images to `data/derived/generated_images/{group}/{scene_id}.png`. Ensure all three groups (Baseline, Experimental, Control) are fully generated before marking task complete.
- [~] T022 [US2] [Depends on T022a] Implement fallback mechanism: If architecture permits only approximate seed control, generate N=5 candidate images per prompt using the same seed. <!-- FAILED: unspecified -->
- [X] T022a [US2] [Depends on T012] Implement `code/generation/reference_geometry.py`: Render a "reference geometry" image by projecting the `pymunk` JSON bounding boxes onto a virtual 512x512 canvas matching the generation resolution.
- [~] T022b [US2] [Depends on T022] Implement selection logic: Calculate SSIM between each of the N=5 candidates and the reference geometry (from T022a), select the candidate with the highest SSIM score, and save only that single image as the final output.
- [ ] T023 [US2] Monitor memory usage and enforce a time limit per batch.

The research question, method, and references remain unchanged as per the planning document requirements.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. **Must have generated images for Baseline, Experimental, AND Control groups.**

---

## Phase 5: User Story 3 - Evaluate Geometric Consistency and Statistical Significance (Priority: P3)

**Goal**: Extract bounding boxes using YOLOv8n, compare against physics JSON ground truth, calculate violation rates, and perform statistical analysis.

**Independent Test**: Feed pre-generated images with known violations into `code/evaluation/detector.py`; verify violation counts match manual inspection and `code/analysis/statistics.py` outputs a valid p-value.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for `EvaluationResult` schema in `tests/contract/test_schemas.py`
- [ ] T025 [P] [US3] Unit test for Z-test/Fisher's Exact Test logic in `tests/unit/test_statistics.py`

### Implementation for User Story 3

- [ ] T026 [US3] [Depends on T012, T021] Implement `code/evaluation/detector.py`: Load YOLOv8n (CPU), detect objects, extract bounding boxes, compare against `physics_constraints/{scene_id}.json` (relative to 512x512 output, IoU < 0.5 or Y-offset > 5px).
- [ ] T027 [US3] Implement violation logic: Count floating objects/interpenetration; default to violation if object confidence < 0.7 (Edge Case).
- [ ] T028 [US3] Save evaluation results to `data/derived/evaluation_results/{scene_id}.json` with violation flags and confidence distributions (FR-010).
- [ ] T029 [US3] [Independent of T016] Implement `code/analysis/statistics.py` Power Analysis: Perform power analysis (effect_size=0.2, alpha=0.05, power_target=0.8) and output `power_analysis_report.json`.
- [ ] T029a [US3] [Depends on T029] Implement Power Verification: Verify that the calculated power (≥0.8) is achieved. [UNRESOLVED-CLAIM: c_eb669cf6 — status=not_enough_info] If power < 0.8, halt the pipeline and flag `power_analysis_report.json` as failed.
- [ ] T029b [US3] Implement Statistical Test Switching Logic: Read the `power_analysis_report.json` and check expected cell counts. If cell counts < 5, switch to Fisher's Exact Test; otherwise, use two-proportion z-test.
- [ ] T029c [US3] [Depends on T016] Implement Exclusion Logic: Read contradiction logs (from T016) and generation failure logs (from T020), identify the corresponding scene IDs, and exclude them from the final statistical denominator.
- [ ] T029d [US3] [Depends on T016] Implement Contradiction Rate Check: Re-calculate the contradiction rate from logs. If rate > 5%, raise a `StudyInvalidError` to halt the pipeline (Hard Fail).
- [ ] T030 [US3] [Depends on T030b] Generate `data/processed/final_analysis.csv` with aggregated stats, p-values, and "Prompt Adherence Rate" labeling (FR-009).
- [ ] T030b [US3] Implement Metric Labeling Enforcement: Ensure "Prompt Adherence Rate" is explicitly used as the label for violation metrics in `power_analysis_report.json`, `evaluation_results`, and `final_analysis.csv`.
- [ ] T031 [US3] [Depends on T031a] Implement Correction Factor Logic: If the False Negative Rate (FNR) exceeds the derived threshold (from T031a), apply a conservative correction factor or switch to a qualitative 'Pass/Fail' assessment.
- [ ] T031a [US3] Implement Validation Set & Threshold Derivation: Load a held-out validation set (defined in `data/raw/validation_scenes.csv`), calculate the detector's FNR, and derive the "predefined acceptable threshold" dynamically.
- [ ] T032a [US3] [Depends on T016] Implement aggregation logic in `code/analysis/statistics.py` to read contradiction logs, calculate the exact contradiction rate percentage, and verify it is < 5% (SC-004); if rate > 5%, raise a `StudyInvalidError` to halt the pipeline.
- [ ] T032b [US3] [Depends on T032a] Update `data/processed/final_analysis.csv` and `code/analysis/statistics.py` to explicitly include the "Contradiction Rate" metric and ensure it is reported in the final summary output.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Update `README.md` with project overview, dependencies, and step-by-step execution instructions for the full pipeline; specifically update the "Results" and "Methodology" sections to reflect the N=100 scope and Control Group inclusion.
- [ ] T034 [P] Update `quickstart.md` with environment setup, CPU-only model download instructions, and N=100 run validation steps; ensure the "Expected Output" section lists the three groups (Baseline, Experimental, Control).
- [ ] T035 [P] Create `scope_justification.md` artifact explaining the deviation from N=500 to N=100 due to compute constraints and citing the plan.md constraints.
- [ ] T036 Code cleanup and refactoring of `code/` modules
- [ ] T037 Performance optimization for CPU generation batch sizes
- [ ] T038 [P] Additional unit tests in `tests/unit/`
- [ ] T039 Security hardening (input validation for prompts)
- [ ] T040 [P] Run `quickstart.md` validation and verify full pipeline on N=100

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
Task: "Create data/raw/scene_descriptions.csv"
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
- **CRITICAL**: All image generation tasks (T018-T023) must strictly adhere to CPU-only constraints (no CUDA, no 8-bit quantization requiring bitsandbytes). Use distilled models (LCM-LoRA) only.
- **CRITICAL**: Dataset download/fetch tasks must use real, reachable URLs or package fetchers (e.g., `datasets.load_dataset`), never synthetic/fake data.
- **CRITICAL**: Task ordering respects data flow: Physics JSON (US1) must be generated before Prompts (US1) which must be generated before Images (US2) which must be generated before Evaluation (US3).
- **CRITICAL**: T004 MUST run after T001a-T001q (sequential dependency).
- **CRITICAL**: T009/T010 depend on Phase 2 completion.
- **CRITICAL**: T012/T013 depend on T011.
- **CRITICAL**: T026 depends on T012 and T021.
- **CRITICAL**: T032a/T032b depend on T016 and aggregate logs from US1.
- **CRITICAL**: T029 must output `power_analysis_report.json` as a mandatory deliverable.
- **CRITICAL**: T031 must switch to 'Pass/Fail' if FNR > derived threshold.
- **CRITICAL**: T022 must use SSIM for similarity calculation.
- **CRITICAL**: T035 must document the N=100 scope reduction.
- **CRITICAL**: T022 must explicitly calculate "reference geometry" by projecting `pymunk` JSON to a virtual canvas (512x512) before calculating SSIM.
- **CRITICAL**: T011 must explicitly handle the N=100 scope reduction in the data fetching logic.
- **CRITICAL**: T022b must explicitly select the best candidate based on SSIM.
- **CRITICAL**: T029a must halt the pipeline if power < 0.8.
- **CRITICAL**: T029b must switch to Fisher's Exact Test if cell counts < 5.
- **CRITICAL**: T030b must ensure "Prompt Adherence Rate" labeling is applied to all reports.
- **CRITICAL**: T029c must exclude contradictory and failed scenes from the statistical denominator.
- **CRITICAL**: T031a must derive the FNR threshold from a held-out validation set.