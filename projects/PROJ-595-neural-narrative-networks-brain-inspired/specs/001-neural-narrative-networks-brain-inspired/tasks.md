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
- [X] T000.1 [DONE] Update `plan.md` Step 2 to explicitly state the baseline is a "TinyLSTM (quantized transformer)" to match spec FR-004, removing all references to "Standard SAE". **Note: plan.md currently still lists 'Standard SAE'; this is a plan-root cause flagged for kickback.** <!-- FIXED: plan updated -->

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create directory `code/`.
- [X] T001b [P] Create directory `data/raw/`.
- [X] T001c [P] Create directory `data/processed/`.
- [X] T001d [P] Create directory `data/results/`.
- [X] T001e [P] Create directory `tests/`.
- [X] T001f [P] Create directory `state/`.
- [X] T001g [P] Create directory `data/text/`.
- [X] T001h [P] Create file `code/__init__.py`.
- [X] T001i [P] Create file `.gitignore` with rules for `data/`, `__pycache__/`, `*.pyc`, `logs/`.
- [X] T002 [P] Create `code/requirements.txt` containing pinned versions for: torch (cpu-only), nibabel, nilearn, scikit-learn, datasets, pandas, numpy, matplotlib, sentence-transformers, ruff, black, pytest.
- [X] T003 [P] Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections defining line-length=88 and target-version='py'.
- [X] T004 [P] Create `.ruff.toml` with specific rule selections (E, F, W) and ignore rules for the project.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Setup data directory structure: `data/raw/`, `data/processed/`, `data/results/`, `data/text/`
- [X] T006 [P] Implement `code/utils/schema_validation.py` with functions `validate_neural_data()`, `validate_text_data()`, and `validate_rsa_output()` that load `specs/001-neural-narrative-networks-brain-inspired/contracts/neural-data.schema.yaml`, `specs/001-neural-narrative-networks-brain-inspired/contracts/text-data.schema.yaml`, and `specs/001-neural-narrative-networks-brain-inspired/contracts/rsa-output.schema.yaml` respectively and return boolean validation results.
- [X] T007 [P] Implement `code/utils/checksums.py` for SHA-256 hashing and state file updates.
- [X] T008 [DONE] Create `code/config.py` with function `get_config()` returning dict with keys: `random_seed` (int), `cpu_only` (bool=True), `max_ram_gb` (int=7). Includes `set_seed()` function that calls `np.random.seed(seed)`, `torch.manual_seed(seed)`, and `random.seed(seed)`.
- [X] T009 Create `code/utils/logging_config.py` initializing a logger that writes to `logs/pipeline.log` and prints specific error codes to stderr: E001 for data corruption/missing files, E002 for empty timepoints/data, E003 for model convergence failure.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download OpenNeuro ds001495 and ROCStories, extract hippocampal/prefrontal timecourses, and format for analysis.

**Independent Test**: Verify existence of processed `.npy`/`.csv` files for L/R Hippocampus and DLPFC for a representative subject cohort and `data/text/rocstories_sample.jsonl` for a representative story sample without running models.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/test_ingestion.py`
- [X] T011 [P] [US1] Integration test for full download pipeline in `tests/test_ingestion.py`

### Implementation for User Story 1

- [ ] T012 [US1] Download OpenNeuro ds001495 fMRI dataset [UNRESOLVED-CLAIM: c_6e6cc92c — status=not_enough_info] using `datalad` (or direct fetch if datalad unavailable) to `data/raw/openneuro_ds001495/`. **Fallback**: If datalad fails, fetch directly from `. Verify download integrity via checksums. **Output**: `data/raw/openneuro_ds001495/checksums.txt` and expected sub-structure `sub-*/func/sub-*_task-narratives_bold.nii.gz`. Requires T009 (logging).
- [X] T013 [US1] Load Harvard-Oxford masks for Left Hippocampus, Right Hippocampus, and DLPFC using `nilearn.datasets.fetch_atlas_harvard_oxford`. **Fallback**: If fetch fails, generate masks programmatically using `nilearn.image.new_img_like` with coordinates (L/R Hipp: x=+-24, y=, z=-12; DLPFC: x=+-40, y=36, z=28) and a mm sphere radius. If ROI cannot be defined via coordinates, raise Error with exact string: "ROI definition failed: neither precomputed mask nor Harvard-Oxford coordinates available." Save valid mask paths to `data/processed/mask_paths.json` with schema: `{"left_hipp": "path", "right_hipp": "path", "dlpfc": "path"}`. **Paths must be relative to repository root.**
- [ ] T014 [P] [US1] Extract BOLD timecourses for Left Hippocampus from `data/raw/` using masks from T013. **Requires T012, T013**. **If T012 artifacts missing, halt with E001**. Save to `data/processed/roi_left_hipp.npy`. <!-- FAILED: unspecified -->
- [ ] T015 [P] [US1] Extract BOLD timecourses for Right Hippocampus from `data/raw/` using masks from T013. **Requires T012, T013**. **If T012 artifacts missing, halt with E001**. **If timecourses empty, halt with E002**. Save to `data/processed/roi_right_hipp.npy`.
- [ ] T016 [P] [US1] Extract BOLD timecourses for DLPFC from `data/raw/` using masks from T013. **Requires T012, T013**. **If T012 artifacts missing, halt with E001**. **If timecourses empty, halt with E002**. Save to `data/processed/roi_dlpfc.npy`.
- [ ] T017 [P] [US1] Combine extracted timecourses into a single `data/processed/roi_timecourses.csv` with columns: `subject_id`, `roi`, `timepoint`, `signal`. Requires T014, T015, T016 completion. <!-- ATOMIZE: requested -->
- [X] T018 [US1] Implement chunked loading function `load_chunked_fMRI()` in `code/01_data_ingestion.py` to handle files >7GB, verified by OOM test on a large file.
- [ ] T019 [US1] Download ROCStories corpus via HuggingFace `datasets` (ID: `rocstories`) and sample **a subset of stories** to `data/text/rocstories_sample.jsonl`. **Schema**: Each row must have fields `story` (string) and `id` (string/int). If download fails, halt with clear error.
- [X] T020 [US1] Implement validation step in `code/01_data_ingestion.py` to halt on corrupted/incomplete data with specific error codes (E001, E002) logged to `logs/pipeline.log`.
- [ ] T021 [US1] Compute mean BOLD per event using the `event_boundaries` field in `data/text/rocstories_sample.jsonl` to map story events to timepoints. Aggregate BOLD signal per story event by averaging timepoints within event boundaries [UNRESOLVED-CLAIM: c_f5db20fe — status=not_enough_info]. **Verify**: Log the aggregation method as 'mean' and assert the value is computed correctly. Save to `data/processed/event_averages.csv` with columns: `subject_id`, `event_id`, `roi`, `mean_signal`. **Requires T017, T019 completion.** <!-- ATOMIZE: requested -->
- [ ] T022 [US1] Generate `data/processed/derivation_logs.json` documenting the chain of custody for all files in `data/processed/`, including source file hashes, transformation steps, and output file hashes. Then run `utils/checksums.py` to update the state file, **including the newly generated derivation log**. Requires T021 completion. <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Brain-Inspired Model Generation (Priority: P2)

**Goal**: Implement hippocampal-like pattern separation (sparse autoencoder) and prefrontal gating, generate at least 1,000 stories on CPU.

**Independent Test**: The system verifies SAE sparsity is within an acceptable low range. Verify peak RAM < 7GB.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Contract test for story uniqueness and format in `tests/test_model.py`
- [X] T024 [P] [US2] Integration test for memory constraints in `tests/test_model.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement class `SparseAutoencoder` in `code/models/sparse_autoencoder.py` with a method `forward()` that returns activations and a property `sparsity_ratio` calculated as mean(activations > 0).
- [X] T026 [US2] Implement verification script in `code/verify_sparsity.py` to measure and log the sparsity ratio against the ≤0.20 constraint, raising an error if violated.
- [X] T027 [US2] Implement Prefrontal Gating Module in `code/models/gating_module.py` distinguishing plot (coherence) vs memory (episodic trace).
- [X] T028 [US2] Implement TinyLSTM baseline architecture with quantization (e.g., int or lower) using `torch.quantization` (CPU backend only) in `code/models/baseline.py` for comparison, ensuring it runs on CPU and respects the 7GB RAM limit. Verify no CUDA kernels are invoked.
- [ ] T029a [US2] Implement core training loop in `code/02_model_generation.py` with retry logic: use `config.random_seed` as base_seed; increment seed by `base_seed + retry_count` each retry (a maximum of 3 retries). **Retry Condition**: If mean(sparsity_ratio) over the entire validation epoch > 0.20, retry. If sparsity constraint not met after 3 retries, raise Error with code E003. Save trained weights to `data/results/sae_weights.pt`. **Requires T025, T027 completion.**
- [ ] T029b [US2] Execute training loop from T029a. Verify convergence by running `verify_sparsity.py` and saving `data/results/convergence_verified.json` with timestamp and seed. If T029a raises E003, log the failure and halt. Requires T029a completion.
- [ ] T030 [US2] Implement generation loop to produce at least 1,000 unique stories using the Brain-Inspired model. **Load trained weights from data/results/sae_weights.pt.** **Monitor memory; fail if > 7GB.** Requires T029b completion. Verify sparsity < 0.20. Ensure uniqueness via hash deduplication. Save to `data/results/brain_stories.jsonl`.
- [ ] T031 [US2] Run generation loop to produce at least 1,000 unique stories using the Baseline (TinyLSTM) model and save to `data/results/baseline_stories.jsonl`. **Monitor memory; fail if > 7GB.** Ensure uniqueness via hash deduplication. Requires T028 completion.
- [ ] T032 [US2] Implement memory monitoring to log peak usage and ensure < 7GB limit. Save peak RAM log to `data/results/memory_profile.json` with keys `peak_gb` and `timestamp`. Verify file exists and `peak_gb` < 7.0.
- [ ] T033 [US2] Run `utils/checksums.py` after generation and update state file.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Neural Similarity Analysis and Validation (Priority: P3)

**Goal**: Compute RSA matrices, perform a permutation test with convergence check, generate visualizations comparing alignment.

**Independent Test**: Verify RSA CSV, p-value from permutation test (with convergence check), and heatmaps/bar plots are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T043 [P] [US3] Contract test for RSA output schema in `tests/test_rsa.py`
- [X] T044 [P] [US3] Integration test for permutation test convergence in `tests/test_rsa.py`

### Implementation for User Story 3

- [ ] T036 [US3] Implement `code/03_rsa_analysis.py` to compute RSA matrices for Brain-Inspired (from T030) and Baseline (from T031) models against fMRI BOLD. **Requires T030, T031, T017, and T021 (formatted CSV) completion.** If T030/T031/T017/T021 artifacts missing, halt with error. Save RSA distances to `data/results/rsa_matrix.csv`.
- [ ] T037 [US3] Implement permutation test in `code/03_rsa_analysis.py`. **Start with 1,000 permutations, batch size 500.** Iterate permutations until p-value variance < 0.001 over the **final 1,000 permutations**. If convergence is not met, continue iterating. Save results to `data/results/permutation_test_results.json`.
- [ ] T038 [US3] Validate RSA output against `specs/001-neural-narrative-networks-brain-inspired/contracts/rsa-output.schema.yaml` and save validated output to `data/results/rsa_validated.jsonl`.
- [ ] T039 [US3] Create `code/04_visualization.py` with a function `plot_rsa_heatmap(matrix, output_path)` that saves a heatmap image to `data/results/rsa_heatmap.png`.
- [ ] T040 [US3] Generate bar plot with confidence intervals comparing RSA distances and save to `data/results/rsa_comparison_barplot.png`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T056 [P] Documentation updates: Update `README.md` section "Biological Mechanisms" ensuring clarity on the ds001495 source, the biological mechanisms (sparse autoencoder, gating), and the data lineage.
- [ ] T057 Code cleanup and refactoring for CPU efficiency.
- [ ] T058 [P] Performance optimization for permutation test (parallelization) in T037 to ensure a sufficient number of iterations complete within the runtime limit.
- [ ] T059 [P] Additional unit tests for edge cases (ROI failure, memory overflow, alignment failure, convergence failure) in `tests/unit/`.
- [ ] T060 Run `quickstart.md` validation.
- [ ] T061 [P] Update `README.md` to document the pipeline and biological mechanisms.

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
- **Polish (Phase N)**: Depends on Phase 5 completion.

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
- Phase 6 tasks (T045-T049) can run in parallel as they modify different aspects of the model or analysis.

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

### Review-Driven Iteration

1. After US2 completion, immediately begin Phase 6 tasks (T045-T049) to address specific biological and narrative structure concerns.
2. Validate that the refined model (T047, T048) still meets sparsity constraints (T026).
3. Re-run RSA analysis (T036) with the new variance metrics (T049).

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
- **Biological Fidelity Note**: The architecture implements a sparse autoencoder and gating module as defined in FR-002, FR-003.
- **Constitution Note**: Data derivation logs are generated in T022 to satisfy Constitution Principle III.
- **Scope Note**: All tasks are strictly scoped to Functional Requirements FR-001 through FR-007.
- **Baseline Note**: The baseline model is a TinyLSTM (quantized transformer) as per spec FR-004. **Note: plan.md still lists 'Standard SAE' in Project Steps; this is a plan-root cause flagged for kickback.**
- **Retry Note**: SAE training (T029a) has a hard 3 retry limit using config.random_seed.