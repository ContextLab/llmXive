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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-890-llmxive-follow-up-extending-orca-the-wor/`) <!-- ATOMIZE: requested -->
- [ ] T002 Initialize Python 3.11 project with pinned `requirements.txt` (CPU-only torch, scikit-learn, datasets, mujoco/pybullet)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup global config module (`code/config.py`) with paths, seeds, memory limits, and `OPTICAL_FLOW_THRESHOLD` parameter (default 0.5)
- [X] T005 [P] Implement audit logging infrastructure (`code/utils/audit_logger.py`) to capture skipped files and ambiguous prompts (FR-008)
- [ ] T006 Create base data models/entities (`code/data/models.py`) for `PhysicalScenario`, `LatentVector`, `CounterfactualEdit`
- [~] T007 Setup memory profiling utility (`code/utils/memory_guard.py`) to dynamically adjust batch sizes based on `psutil` usage
- [~] T008 Initialize `data/` directory structure (`raw/`, `processed/`, `validation/`) with checksum verification scripts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Latent Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Prepare the dataset and extract frozen latent vectors from the Orca model without GPU resources.

**Independent Test**: The pipeline can be tested by verifying that the script successfully downloads the subset of the Orca dataset, filters for physical interaction clips, and outputs a CSV containing the video IDs, the manually annotated counterfactual prompts, and the corresponding frozen latent vectors (shape verified) without requiring GPU resources.

### Tests for User Story 1

- [~] T009 [P] [US1] Unit test for data filtering logic in `tests/unit/test_data_filter.py`
- [ ] T010 [P] [US1] Integration test for latent extraction on a single sample clip in `tests/integration/test_latent_extraction.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/data/download_orca.py` to fetch Orca dataset via HuggingFace `datasets` library (real URL only)
- [ ] T012 [US1] Implement filtering logic in `code/data/download_orca.py` to exclude non-physical interaction clips using `optical_flow_magnitude` < `config.OPTICAL_FLOW_THRESHOLD` on `metadata` field (FR-001)
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

- [ ] T020a [US2] **Extract Original Physical Outcomes (N=450)**: Implement `code/data/extract_original_labels.py` to parse the video metadata from the N=450 curated clips and extract the *original* physical outcomes (e.g., "object fell") as ground truth for Descriptive Analysis. **Output**: `data/processed/original_labels.csv` with columns `scenario_id`, `original_outcome`. This dataset serves as the ground truth for the N=450 Descriptive Baseline (FR-004, Plan Summary).
- [ ] T020b [US2] **Generate Physics-Verified Labels (N=50)**: Implement `code/data/physics_verify.py` to generate **Physics-Verified Labels** for the N=50 subset using full MuJoCo/PyBullet simulation. This task outputs `data/validation/physics_ground_truth_subset.csv` with columns `scenario_id`, `counterfactual_prompt`, `simulated_outcome`. This dataset is used for vector arithmetic validation and Causal Mode training (FR-009, FR-010).
- [ ] T021 [US2] Implement `code/data/inject_counterfactuals.py` to apply **vector arithmetic** for clear prompts, **ZeroVectorMask** for ambiguous prompts, to generate $z_{cf}$ for *each* clip. Output `data/processed/latents_cf_raw.csv`. (FR-002)
- [ ] T022 [US2] Implement ambiguity detection in `code/data/inject_counterfactuals.py` to flag ambiguous prompts and record in `failed_scenarios.log`. **Output**: Add `ambiguous_flag` column to `data/processed/latents_cf_raw.csv` (0=valid, 1=ambiguous). (Edge Cases, FR-003)
- [ ] T026a [US2] Implement vector arithmetic validation gate in `code/data/validate_gate.py`. **Input**: `data/processed/latents_cf_raw.csv` (Subset N=50), `data/validation/physics_ground_truth_subset.csv` (from T020b). **Action**: Compare $z_{cf}$ predictions against physics results. **Output**: Write `data/validation/gate_status.json` with `status: "passed"` (if accuracy >= 90%) or `status: "blocked"`. **Logic**: If `status` is "blocked", the pipeline MUST halt downstream *causal* training tasks (T023, T024 Causal Mode). (FR-010, SC-008, Edge Cases)
- [ ] T022b [US2] **Filter Ambiguous Clips**: Implement logic in `code/data/filter_training_set.py` to read `data/processed/latents_cf_raw.csv`. **Action**: Exclude rows where `ambiguous_flag` == 1 for the **entire dataset** (N=450 + N=50). **Output**: `data/processed/filtered_training_set.csv`. **Note**: This filtering is independent of the N=50 gate status (T026a). The N=50 gate only controls whether the *causal* branch (T023/T024 Causal Mode) proceeds. (FR-003)
- [ ] T023 [US2] Implement `code/models/train_readout.py` to train `DecisionTreeClassifier` on modified latents (N=50 subset if gate passed). **Depends on**: T022b, T026a (Gate Pass). **Mode**: Causal Mode (uses physics labels from T020b). (FR-003)
- [ ] T024 [US2] Implement `code/models/baseline_pixel.py` to train `DecisionTreeClassifier` on raw downsampled frames. **Depends on**: T020a, T020b, T022b. **Action**:
 - **Descriptive Mode**: Train on N=450 using `original_labels.csv` (from T020a) to establish correlation baseline against real video events.
 - **Causal Mode**: Train on N=50 (if gate passed) using `physics_ground_truth_subset.csv` (from T020b) to compare against the causal model.
 (FR-004)
- [ ] T025 [US2] Implement `code/analysis/stats.py` to perform paired t-test comparing Latent Model (T023) vs. Pixel Baseline (T024 Causal Mode) and calculate p-value. (FR-005)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Method Independence and Ablation Verification (Priority: P3)

**Goal**: Verify that the observed advantage is not an artifact of the specific decision tree or "unconscious" latent signals.

**Independent Test**: The story is tested by executing the ablation scripts which regenerate results using a linear probe and a modified latent input (excluding linguistic tokens), confirming if the performance gap persists.

### Tests for User Story 3

- [ ] T028 [P] [US3] Unit test for linear probe implementation in `tests/unit/test_linear_probe.py`
- [ ] T029 [P] [US3] Integration test for ablation study results consistency in `tests/integration/test_ablation.py`

### Implementation for User Story 3

- [ ] T045 [US3] **Concept Localization: Physical Concepts**: Implement `code/data/localize_concepts.py` to probe latent vectors and identify vector dimensions corresponding to *physical concepts* (e.g., gravity, friction) required for counterfactual injection (T021). **Output**: `data/processed/physical_concept_mappings.json` containing the specific index map for physical tokens. (FR-002, T021 Prerequisite)
- [ ] T046 [US3] **Concept Localization: Linguistic Scaffolding**: Implement `code/data/localize_concepts.py` (extended) to probe latent vectors and identify vector dimensions corresponding to *linguistic scaffolding* (conscious tokens). **Output**: `data/processed/linguistic_concept_mappings.json` containing the specific index map for linguistic tokens. (FR-007 Prerequisite)
- [ ] T030 [US3] Implement `code/models/train_readout.py` Linear Probe (Logistic Regression) training option (FR-006)
- [ ] T031 [US3] Implement logic to isolate "unconscious" latent vectors by **masking indices defined in T046** (`data/processed/linguistic_concept_mappings.json`) in `code/data/extract_latents.py`. **Depends on**: T046. Output `data/processed/latents_unconscious.csv`. (FR-007)
- [ ] T032 [US3] Implement ablation training loop comparing Full Latents vs. Unconscious Latents (FR-007)
- [ ] T033 [US3] Update `code/analysis/stats.py` to calculate performance gap for Decision Tree vs. Linear Probe (FR-006)
- [ ] T034 [US3] Update `code/analysis/stats.py` to calculate performance gap for Full vs. Unconscious latents (FR-007)

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
- **Methodological Note**: The N=450 set uses *original video labels* for descriptive analysis (T020a), while the N=50 set uses *physics-verified labels* for causal analysis (T020b). This distinction is critical for valid comparison.
- **Validation Note**: T026a (Vector Validation) is a blocking gate for the *causal* branch only. The descriptive branch (N=450) proceeds independently regardless of the gate status, provided ambiguity filtering (T022b) is applied.