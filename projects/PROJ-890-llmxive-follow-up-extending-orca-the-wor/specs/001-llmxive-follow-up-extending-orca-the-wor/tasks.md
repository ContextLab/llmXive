# Tasks: llmXive follow-up: extending "Orca: The World is in Your Mind"

**Input**: Design documents from `/specs/001-llmxive-orca-counterfactual/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-890-llmxive-follow-up-extending-orca-the-wor/`)
- [ ] T002 Initialize Python 3.11 project with pinned `requirements.txt` (CPU-only torch, scikit-learn, datasets, mujoco/pybullet)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup global config module (`code/config.py`) with paths, seeds, and memory limits (memory guardrail)
- [ ] T005 [P] Implement audit logging infrastructure (`code/utils/audit_logger.py`) to capture skipped files and ambiguous prompts (FR-008)
- [ ] T006 Create base data models/entities (`code/data/models.py`) for `PhysicalScenario`, `LatentVector`, `CounterfactualEdit`
- [ ] T007 Setup memory profiling utility (`code/utils/memory_guard.py`) to dynamically adjust batch sizes based on `psutil` usage
- [ ] T008 Initialize `data/` directory structure (`raw/`, `processed/`, `validation/`) with checksum verification scripts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Latent Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Prepare the dataset and extract frozen latent vectors from the Orca model without GPU resources.

**Independent Test**: The pipeline can be tested by verifying that the script successfully downloads the subset of the Orca dataset, filters for physical interaction clips, and outputs a CSV containing the video IDs, the manually annotated counterfactual prompts, and the corresponding frozen latent vectors (shape verified) without requiring GPU resources.

### Tests for User Story 1

- [ ] T009 [P] [US1] Unit test for data filtering logic in `tests/unit/test_data_filter.py`
- [ ] T010 [P] [US1] Integration test for latent extraction on a single sample clip in `tests/integration/test_latent_extraction.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/data/download_orca.py` to fetch Orca dataset via HuggingFace `datasets` library (real URL only)
- [ ] T012 [US1] Implement filtering logic in `code/data/download_orca.py` to exclude non-physical interaction clips using `optical_flow_magnitude` < `config.OPTICAL_FLOW_THRESHOLD` (from `code/config.py`) on `metadata` field
- [ ] T013 [US1] Implement `code/data/extract_latents.py` to load frozen Orca model on CPU (float32, no quantization)
- [ ] T014 [US1] Implement batch processing logic in `code/data/extract_latents.py` with dynamic batch size adjustment (FR-001, Edge Cases)
- [ ] T015 [US1] Implement latent extraction loop to output `data/processed/latents.csv` with video IDs, prompts, and vector arrays
- [ ] T016 [US1] Add error handling in `code/data/extract_latents.py` to log corrupted/missing files and continue processing (Edge Cases)
- [ ] T017 [US1] Verify output shape and validity of latent vectors in `tests/unit/test_latent_validation.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Counterfactual Readout Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train two distinct models (Latent vs. Pixel) and compare performance to determine if latent space encodes causal priors better.

**Independent Test**: The story is tested by running the training script which produces two accuracy metrics (Latent Model vs. Pixel Baseline) and a paired t-test p-value, all generated on a CPU without GPU acceleration.

### Tests for User Story 2

- [ ] T018 [P] [US2] Contract test for physics engine simulation output format in `tests/contract/test_physics_output.py`
- [ ] T019 [P] [US2] Integration test for end-to-end training and stats comparison in `tests/integration/test_model_comparison.py`

### Implementation for User Story 2

- [ ] T020a [US2] Implement `code/data/physics_verify.py` to generate **Original Manual Labels** for the N=450 subset. This task creates `data/validation/original_labels.csv` with columns `scenario_id`, `counterfactual_prompt`, `original_outcome` (manual annotation). This dataset serves as the ground truth for the main baseline model (FR-004). (FR-009, Plan Shift)
- [ ] T020b [US2] Implement `code/data/physics_verify.py` to generate **Physics-Verified Labels** for the N=50 subset. This task simulates counterfactual conditions (e.g., `gravity=0.0`) using MuJoCo/PyBullet and outputs `data/validation/physics_ground_truth.csv` with columns `scenario_id`, `counterfactual_prompt`, `simulated_outcome`. This dataset is used for vector arithmetic validation and counterfactual analysis. (FR-009, FR-010)
- [ ] T021 [US2] Implement `code/data/extract_latents.py` counterfactual injection logic: apply **vector arithmetic** for clear prompts, **ZeroVectorMask** for ambiguous prompts, to generate $z_{cf}$ for *each* clip. Output `data/processed/latents_cf.csv`. (FR-002)
- [ ] T022 [US2] Implement validation logic in `code/data/extract_latents.py` to flag ambiguous prompts and record in `failed_scenarios.log`. **Output**: Add `ambiguous_flag` column to `data/processed/latents_cf.csv` (0=valid, 1=ambiguous). (Edge Cases, FR-003)
- [ ] T022b [US2] **Filter Ambiguous Clips**: Implement logic in `code/data/extract_latents.py` to read `data/processed/latents_cf.csv`, exclude rows where `ambiguous_flag` == 1, and write the clean dataset to `data/processed/latents_cf_filtered.csv`. This is the single source of truth for training data, ensuring consistency with FR-003. (FR-003)
- [ ] T026a [US2] Implement vector arithmetic validation in `code/data/extract_latents.py` to compare $z_{cf}$ predictions against physics engine results (T020b). **DO NOT halt the pipeline**. Log validation accuracy; if < 90%, log warning but continue to training tasks. Output `data/validation/vector_arithmetic_validation.csv`. (FR-010, SC-008, Edge Cases)
- [ ] T023 [US2] Implement `code/models/train_readout.py` to train `DecisionTreeClassifier` on modified latents (N=450 subset, excluding ambiguous). **Depends on T020a, T022b, and T026a (completion only)**. Note: Training proceeds regardless of T026a validation score; T026a ensures the validation log exists. (FR-003)
- [ ] T024 [US2] Implement `code/models/baseline_pixel.py` to train `DecisionTreeClassifier` on raw downsampled frames using **Original Manual Labels** from T020a (N=450). **Depends on T020a**. This establishes the pixel-based baseline for the full dataset, predicting original physical outcomes. (FR-004)
- [ ] T025 [US2] Implement `code/analysis/stats.py` to perform paired t-test comparing Latent Model (T023) vs. Pixel Baseline (T024) and calculate p-value. (FR-005)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Method Independence and Ablation Verification (Priority: P3)

**Goal**: Verify that the observed advantage is not an artifact of the specific decision tree or "unconscious" latent signals.

**Independent Test**: The story is tested by executing the ablation scripts which regenerate results using a linear probe and a modified latent input (excluding linguistic tokens), confirming if the performance gap persists.

### Tests for User Story 3

- [ ] T028 [P] [US3] Unit test for linear probe implementation in `tests/unit/test_linear_probe.py`
- [ ] T029 [P] [US3] Integration test for ablation study results consistency in `tests/integration/test_ablation.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/models/train_readout.py` Linear Probe (Logistic Regression) training option (FR-006)
- [ ] T031 [US3] Implement logic to isolate "unconscious" latent vectors by **masking a subset of initial indices** (linguistic scaffolding) in `code/data/extract_latents.py`. Output `data/processed/latents_unconscious.csv`. (FR-007)
- [ ] T032 [US3] Implement ablation training loop comparing Full Latents vs. Unconscious Latents (FR-007)
- [ ] T033 [US3] Update `code/analysis/stats.py` to calculate performance gap for Decision Tree vs. Linear Probe (FR-006)
- [ ] T034 [US3] Update `code/analysis/stats.py` to calculate performance gap for Full vs. Unconscious latents (FR-007)
- [ ] T035 [US3] Apply Bonferroni/Holm-Bonferroni correction to p-values for multiple comparisons (Methodological Rigor)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` covering CPU-only constraints and physics engine setup
- [ ] T037a [P] Refactor: Extract batch size logic into `code/utils/memory_guard.py` with function `adjust_batch_size(current_usage: float, max_usage: float) -> int` returning new batch size. (FR-001)
- [ ] T037b [P] Unit tests for `adjust_batch_size` logic in `code/utils/memory_guard.py`
- [ ] T038a [P] Execute end-to-end benchmark on GitHub Actions runner and record execution time in `data/validation/benchmark_log.csv` (SC-005)
- [ ] T042 [P] **Performance Optimization**: Execute optimization strategies (reduce batch size, lower frame resolution, or skip non-critical logging) **IF** T038a runtime > 6 hours to meet the 6h target. **ELSE** log "No optimization needed". (SC-005)
- [ ] T039 [P] Additional unit tests for edge cases (corrupted files, memory limits) in `tests/unit/`
- [ ] T040 Run `quickstart.md` validation to ensure reproducibility on fresh runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 output (latents)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1 and US2 output (latents, baseline results)

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
Task: "Unit test for data filtering logic in tests/unit/test_data_filter.py"
Task: "Integration test for latent extraction on a single sample clip in tests/integration/test_latent_extraction.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download_orca.py to fetch Orca dataset"
Task: "Implement code/data/extract_latents.py to load frozen Orca model"
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
- **Critical Constraint**: All tasks must run on CPU-only CI (limited vCPU, constrained RAM). No GPU, no 8-bit quantization, no large LLM fine-tuning.
- **Methodological Note**: The main baseline (N=450) uses manual labels (T020a) while counterfactual validation (N=50) uses physics simulation (T020b) to balance feasibility with rigor.
- **Validation Note**: T026a (Vector Validation) is a non-blocking check. Training (T023/T024) proceeds if T026a completes, regardless of its accuracy score. Data filtering is handled strictly by T022b.