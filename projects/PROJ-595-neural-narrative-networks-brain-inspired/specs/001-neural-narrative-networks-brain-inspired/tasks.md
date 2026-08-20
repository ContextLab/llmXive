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

## Phase 0: Plan Alignment

**Purpose**: Resolve cross-artifact contradictions before implementation begins

- [X] T000 [DONE] Update `plan.md` Summary and Technical Context to explicitly reference OpenNeuro dataset `ds001495` (matching spec FR-001), removing all references to `ds000208`. Verify change by checking `plan.md` text for `ds001495`. <!-- FIXED: plan updated to ds001495 -->

---

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
- [X] T006 [P] Implement `code/utils/schema_validation.py` with functions `validate_neural_data()`, `validate_text_data()`, and `validate_rsa_output()` that load `specs/001-neural-narrative-networks/contracts/neural-data.schema.yaml`, `specs/001-neural-narrative-networks/contracts/text-data.schema.yaml`, and `specs/001-neural-narrative-networks/contracts/rsa-output.schema.yaml` respectively and return boolean validation results.
- [X] T007 [P] Implement `code/utils/checksums.py` for SHA-256 hashing and state file updates.
- [X] T008 [DONE] Create `code/config.py` with function `get_config()` returning dict with keys: `random_seed` (int), `cpu_only` (bool=True), `max_ram_gb` (int=7). Includes `set_seed()` function that calls `np.random.seed(seed)`, `torch.manual_seed(seed)`, and `random.seed(seed)` to ensure reproducibility.
- [X] T009 Create `code/utils/logging_config.py` initializing a logger that writes to `logs/pipeline.log` and prints specific error codes (e.g., E001 for data corruption) to stderr.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download OpenNeuro dataset [specific identifier to be determined during implementation] and ROCStories, extract hippocampal/prefrontal timecourses, and format for analysis.

**Independent Test**: Verify existence of processed `.npy`/`.csv` files for L/R Hippocampus and DLPFC for a representative subject cohort and `data/text/rocstories_sample.jsonl` for a representative story sample without running models.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/test_ingestion.py`
- [X] T011 [P] [US1] Integration test for full download pipeline in `tests/test_ingestion.py`

### Implementation for User Story 1

- [ ] T013 [US1] Load Harvard-Oxford masks for Left Hippocampus, Right Hippocampus, and DLPFC using `nilearn.datasets.fetch_atlas_harvard_oxford`. If fetch fails, trigger fallback logic. Save mask paths to `data/processed/mask_paths.json`.
- [ ] T013.5 [P] [US1] Implement fallback logic: if primary mask fetch fails, load Harvard-Oxford atlas coordinates and generate masks programmatically. If ROI cannot be defined, raise Error with exact string: "ROI definition failed: neither precomputed mask nor Harvard-Oxford coordinates available." Save valid mask paths to `data/processed/mask_paths.json`.
- [ ] T014 [P] [US1] Extract BOLD timecourses for Left Hippocampus from `data/raw/` using masks from T013. If masks missing, halt with E001. Save to `data/processed/roi_left_hipp.npy`.
- [ ] T015 [P] [US1] Extract BOLD timecourses for Right Hippocampus from `data/raw/` using masks from T013. If masks missing, halt with E001. If timecourses empty, halt with E002. Save to `data/processed/roi_right_hipp.npy`. <!-- FAILED: unspecified -->
- [ ] T016 [P] [US1] Extract BOLD timecourses for DLPFC from `data/raw/` using masks from T013. If masks missing, halt with E001. If timecourses empty, halt with E002. Save to `data/processed/roi_dlpfc.npy`.
- [ ] T017 [P] [US1] Combine extracted timecourses into a single `data/processed/roi_timecourses.csv` with columns: `subject_id`, `roi`, `timepoint`, `signal`. Requires T014, T015, T016 completion.
- [X] T018 [US1] Implement chunked loading function `load_chunked_fMRI()` in `code/01_data_ingestion.py` to handle files >7GB, verified by OOM test on a large file.
- [ ] T019 [US1] Download ROCStories corpus via HuggingFace `datasets` and sample a representative subset of stories to `data/text/rocstories_sample.jsonl`. If download fails, halt with clear error.
- [ ] T019.5 [P] [US1] Implement story event boundary alignment logic using semantic similarity (sentence-transformers) to map fMRI timepoints to ROCStories events, saving alignment map to `data/processed/event_alignment.json`.
- [X] T020 [US1] Implement validation step in `code/01_data_ingestion.py` to halt on corrupted/incomplete data with specific error codes (E001, E002) logged to `logs/pipeline.log`.
- [ ] T021 [US1] Compute mean BOLD per event using alignment from T019.5 and save to `data/processed/event_averages.csv` with columns: `subject_id`, `event_id`, `roi`, `mean_signal`. Requires T017, T019.5 completion. <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [ ] T022 [US1] Run `utils/checksums.py` after data processing and update state file.
- [ ] T022.5 [US1] Generate `data/processed/derivation_logs.json` documenting the chain of custody for all files in `data/processed/`, including source file hashes, transformation steps, and output file hashes, as required by Constitution Principle III.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Brain-Inspired Model Generation (Priority: P2)

**Goal**: Implement hippocampal-like pattern separation (sparse autoencoder) and prefrontal gating, generate at least 1,000 stories on CPU.

**Independent Test**: The system verifies SAE sparsity is less than 20%. [UNRESOLVED-CLAIM: c_f539436b — status=not_enough_info]; Verify peak RAM < 7GB..

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Contract test for story uniqueness and format in `tests/test_model.py`
- [X] T024 [P] [US2] Integration test for memory constraints in `tests/test_model.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement class `SparseAutoencoder` in `code/models/sparse_autoencoder.py` with a method `forward()` that returns activations and a property `sparsity_ratio` calculated as mean(activations > 0).
- [X] T026 [US2] Implement verification script in `code/verify_sparsity.py` to measure and log the sparsity ratio against the ≤0.20 constraint, raising an error if violated.
- [X] T027 [US2] Implement Prefrontal Gating Module in `code/models/gating_module.py` distinguishing plot (coherence) vs memory (episodic trace).
- [X] T028 [US2] Implement TinyLSTM baseline architecture with quantization (e.g., int or lower) using `torch.quantization` (CPU backend only) in `code/models/baseline.py` for comparison, ensuring it runs on CPU and respects the 7GB RAM limit. Verify no CUDA kernels are invoked.
- [ ] T029 [US2] Implement core training loop with retry logic (multiple retries, seed +1) to ensure SAE convergence (sparsity < 0.20). If sparsity constraint not met after 3 retries, raise Error with code E003.
- [ ] T029.1 [US2] Wrap training loop with execution logic to train the model and save weights; Requires T029 completion. Ensure T029 is fully implemented and tested before starting.
- [ ] T029.2 [US2] Verify Convergence: Run `code/verify_sparsity.py` on trained weights from T029.1. If sparsity >= 0.20, halt with E003. If passed, create `data/results/convergence_verified.json` with timestamp and seed. Requires T029.1 completion.
- [ ] T030 [US2] Implement generation loop to produce at least 1,000 unique stories using the Brain-Inspired model. Requires T029.2 completion. If training artifacts missing, halt with error. Verify sparsity < 0.20. Save to `data/results/brain_stories.jsonl`. <!-- FAILED: unspecified -->
- [ ] T031 [US2] Run generation loop to produce at least 1,000 unique stories using the Baseline (TinyLSTM) model and save to `data/results/baseline_stories.jsonl`. Ensure uniqueness via hash deduplication. Requires T029.1 completion. <!-- FAILED: unspecified -->
- [ ] T032 [US2] Implement memory monitoring to log peak usage and ensure < 7GB limit.
- [ ] T033 [US2] Run `utils/checksums.py` after generation and update state file.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Neural Similarity Analysis and Validation (Priority: P3)

**Goal**: Compute RSA matrices, perform a permutation test with convergence check, generate visualizations comparing alignment.

**Independent Test**: Verify RSA CSV, p-value from permutation test (with convergence check), and heatmaps/bar plots are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T034 [P] [US3] Contract test for RSA output schema in `tests/test_rsa.py`
- [X] T035 [P] [US3] Integration test for permutation test convergence in `tests/test_rsa.py`

### Implementation for User Story 3

- [ ] T036 [US3] Implement `code/03_rsa_analysis.py` to compute RSA matrices for Brain-Inspired (from T030) and Baseline (from T031) models against fMRI BOLD. If T030/T031 artifacts missing, halt with error. Save RSA distances to `data/results/rsa_matrix.csv`.
- [ ] T037 [US3] Implement permutation test in `code/03_rsa_analysis.py`. Run permutations until convergence (p-value variance < 0.001 over final 1,000 permutations) OR until a a hard timeout of several hours is reached. If timeout reached without convergence, flag result as "borderline". Save results to `data/results/permutation_test_results.json`.
- [ ] T038 [US3] Validate RSA output against `specs/001-neural-narrative-networks/contracts/rsa-output.schema.yaml` and save validated output to `data/results/rsa_validated.jsonl`.
- [ ] T039 [US3] Create `code/04_visualization.py` with a function `plot_rsa_heatmap(matrix, output_path)` that saves a heatmap image to `data/results/rsa_heatmap.png`.
- [ ] T040 [US3] Generate bar plot with confidence intervals comparing RSA distances and save to `data/results/rsa_comparison_barplot.png`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T056 [P] Documentation updates in `docs/` ensuring clarity on the ds001495 source, the biological mechanisms (sparse autoencoder, gating), and the data lineage.
- [ ] T057 Code cleanup and refactoring for CPU efficiency.
- [ ] T058 [P] Performance optimization for permutation test (parallelization) in T037 to ensure a sufficient number of iterations complete within the runtime limit.
- [ ] T059 [P] Additional unit tests for edge cases (ROI failure, memory overflow, alignment failure, convergence failure) in `tests/unit/`.
- [ ] T060 Run `quickstart.md` validation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data availability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 model outputs (T030, T031)
- **Polish (Phase N)**: Depends on US3 completion.

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
Task: "Load Harvard-Oxford masks..."
Task: "Extract BOLD... Left Hippocampus"
Task: "Extract BOLD... Right Hippocampus"
Task: "Extract BOLD... DLPFC"
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
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Dataset Note**: This project uses OpenNeuro ds001495 as per spec FR-001.
- **Biological Fidelity Note**: The architecture implements a sparse autoencoder and gating module as defined in FR-002 and FR-003.
- **Constitution Note**: Data derivation logs are generated in T022.5 to satisfy Constitution Principle III.