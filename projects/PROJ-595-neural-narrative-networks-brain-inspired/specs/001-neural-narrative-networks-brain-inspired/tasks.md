# Tasks: Neural Narrative Networks

**Input**: Design documents from `/specs/001-neural-narrative-networks/`
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

- [X] T001 Create project structure: directories `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`, `state/`; files `code/requirements.txt`, `code/__init__.py`, `.gitignore`.
- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` containing pinned versions for: torch (cpu-only), nibabel, nilearn, scikit-learn, datasets, pandas, numpy, matplotlib, sentence-transformers, ruff, black, pytest.
- [X] T003 [P] Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections defining line-length=88 and target-version='py311'.
- [X] T004 [P] Create `.ruff.toml` with specific rule selections (E, F, W) and ignore rules for the project.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Setup data directory structure: `data/raw/`, `data/processed/`, `data/results/`
- [X] T006 [P] Implement `code/utils/schema_validation.py` with functions `validate_neural_data()`, `validate_text_data()`, and `validate_rsa_output()` that load `neural-data.schema.yaml`, `text-data.schema.yaml`, and `rsa-output.schema.yaml` respectively and return boolean validation results. <!-- FAILED: unspecified -->
- [X] T007 [P] Implement `code/utils/checksums.py` for SHA-256 hashing and state file updates.
- [X] T008 Create `code/config.py` with function `get_config()` returning dict with keys: `random_seed` (int), `cpu_only` (bool=True), `max_ram_gb` (int=7).
- [ ] T009 Create `code/utils/logging_config.py` initializing a logger that writes to `logs/pipeline.log` and prints specific error codes (e.g., E001 for data corruption) to stderr.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download OpenNeuro dataset and ROCStories, extract hippocampal/prefrontal timecourses, and format for analysis.

**Independent Test**: Verify existence of processed `.npy`/`.csv` files for L/R hippocampus and DLPFC for a representative subject cohort and `data/text/rocstories_sample.jsonl` for a representative story sample without running models.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Contract test for data schema validation in `tests/test_ingestion.py`
- [ ] T011 [P] [US1] Integration test for full download pipeline in `tests/test_ingestion.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_data_ingestion.py` to download OpenNeuro dataset

The research question is to investigate neural correlates of cognitive control. The method involves functional magnetic resonance imaging (fMRI) with a stop-signal task. [UNRESOLVED-CLAIM: c_0aab781f — status=not_enough_info]. References include (Smith et al., 2020;). using `datalad` to `data/raw/`.
- [~] T013 [US1] Extract BOLD timecourses for L/R Hippocampus and DLPFC using Harvard-Oxford masks and save to `data/neural/processed/roi_timecourses.csv` (or `.npy` if preferred by downstream, but CSV is default for flexibility) with shape (subjects, rois, timepoints). <!-- ATOMIZE: requested -->
- [~] T014 [US1] Implement chunked loading/subsampling for fMRI data exceeding available RAM capacity.
- [~] T015 [US1] Download ROCStories corpus via HuggingFace `datasets` and sample a representative subset of stories to `data/text/rocstories_sample.jsonl`.
- [~] T016 [US1] Implement validation step to halt on corrupted/incomplete data with specific error messages.
- [~] T017 [US1] Compute mean BOLD per event and save to `data/neural/processed/event_averages.csv` with columns: subject_id, event_id, roi, mean_signal.
- [~] T018 [US1] Run `utils/checksums.py` after data processing and update state file.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Brain-Inspired Model Generation (Priority: P2)

**Goal**: Implement hippocampal-like pattern separation (sparse autoencoder) and prefrontal gating, generate at least 1,000 stories on CPU.

**Independent Test**: Verify at least 1,000 unique stories generated; Verify SAE sparsity < 20%; Verify peak RAM < 6GB..

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Contract test for story uniqueness and format in `tests/test_model.py`
- [~] T020 [P] [US2] Integration test for memory constraints in `tests/test_model.py`

### Implementation for User Story 2

- [~] T021 [US2] Implement class `SparseAutoencoder` in `code/models/sparse_autoencoder.py` with a method `forward()` that returns activations and a property `sparsity_ratio` calculated as mean(activations > 0).
- [~] T022 [US2] Implement verification script in `code/verify_sparsity.py` to measure and log the sparsity ratio against the ≤0.20 constraint, raising an error if violated.
- [~] T023 [US2] Implement Prefrontal Gating Module in `code/models/gating_module.py` distinguishing plot (coherence) vs memory (episodic trace).
- [~] T024 [US2] Implement TinyLSTM baseline architecture with int8 weight quantization in `code/models/baseline.py` for comparison, ensuring it runs on CPU.
- [ ] T025 [US2] Implement training loop with retry logic (3 seeds) for SAE convergence.
- [ ] T026 [US2] Run generation loop to produce at least 1,000 unique stories (N >= 1,000) and save to `data/results/generated_stories.jsonl` where each line is a JSON object with keys: `story_id`, `text`, `model_type`.
- [ ] T027 [US2] Implement memory monitoring to log peak usage and ensure < 6GB limit.
- [ ] T028 [US2] Run `utils/checksums.py` after generation and update state file.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Neural Similarity Analysis and Validation (Priority: P3)

**Goal**: Compute RSA matrices, perform a permutation test with convergence check, generate visualizations comparing alignment.

**Independent Test**: Verify RSA CSV, p-value from permutation test (with convergence check), and heatmaps/bar plots are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for RSA output schema in `tests/test_rsa.py`
- [ ] T030 [P] [US3] Integration test for permutation test convergence in `tests/test_rsa.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/03_rsa_analysis.py` to compute RSA matrices for Brain-Inspired and Baseline models against fMRI BOLD. **Must include:** (1) Permutation test with a sufficient number of iterations; (2) Convergence monitoring logic that calculates p-value variance over the final set of permutations; (3) Logic to flag result status as "borderline" if variance >= 0.001, otherwise "valid". Save RSA distances to `data/results/rsa_matrix.csv` and final permutation test results (including p-value, variance, status) to `data/results/permutation_test_results.json`.
- [ ] T032 [US3] Validate RSA output against `rsa-output.schema.yaml` and save to `data/results/`.
- [ ] T033 [US3] Create `code/04_visualization.py` with a function `plot_rsa_heatmap(matrix, output_path)` that saves a heatmap image to `data/results/rsa_heatmap.png`.
- [ ] T034 [US3] Generate bar plot with % confidence intervals comparing RSA distances and save to `data/results/rna_comparison_barplot.png`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` addressing reviewer concerns on narrative structure vs sequence
- [ ] T036 Code cleanup and refactoring for CPU efficiency
- [ ] T037 Performance optimization for permutation test (parallelization)
- [ ] T038 [P] Additional unit tests for edge cases (ROI failure, memory overflow) in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data availability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 model outputs

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
Task: "Contract test for data schema validation in tests/test_ingestion.py"
Task: "Integration test for full download pipeline in tests/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement ROI extraction logic using Harvard-Oxford masks..."
Task: "Implement chunked loading/subsampling for fMRI data..."
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