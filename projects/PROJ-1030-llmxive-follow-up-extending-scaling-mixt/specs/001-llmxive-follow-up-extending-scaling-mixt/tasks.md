# Tasks: llmXive follow-up: extending "Scaling Mixture-of-Experts Video Pretraining for Embodied Intelligence"

**Input**: Design documents from `/specs/001-llmxive-physical-validator/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: `mkdir -p code code/utils data/raw data/processed tests/unit tests/integration docs/figures state`
- [X] T002 Initialize Python 3.11 project: Create `code/requirements.txt` containing pinned versions of [torch-cpu, transformers, datasets, pybullet, scikit-learn, opencv-python-headless, monodepth2, shap, huggingface-hub, pytest, ruff, black]
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools with pre-commit hooks

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `code/utils/memory_manager.py` for chunking and frame subsampling logic (FR-006)
- [X] T005.1.1 [P] Implement frame subsampling logic: Create `code/utils/memory_chunker.py` function `subsample_frames` that reduces frame count while preserving temporal resolution.
- [X] T005.1.2 [P] Implement temporal chunking logic: Create `code/utils/memory_chunker.py` function `chunk_temporal` that splits long clips into manageable segments.
- [X] T005.1.3 [P] Write unit tests for memory chunking: Create `tests/unit/test_memory_chunker.py` to verify subsampling and chunking logic.
- [X] T005 [P] Implement `code/utils/physics_sim.py` wrapper for PyBullet (scale normalization, error handling)
- [X] T007 [P] Create base data models in `code/models/data_models.py`: Define classes `VideoClip`, `EstimatedState3D`, `ActivationPattern`, and `PhysicalLabel` in a single file to ensure consistency.
- [X] T008.1 [P] Implement "FAIL LOUDLY" logging infrastructure: Create `code/utils/logging.py` with a `fail_loudly` function that raises exceptions on data fetch failures instead of falling back to synthetic data. Artifact: `code/utils/logging.py`.
- [X] T008.2 [P] Implement exponential backoff logic: Create `code/utils/retry.py` with a `retry_with_backoff` function for download failures. Artifact: `code/utils/retry.py`.
- [X] T009 Setup environment configuration management and `data/.checksums.json` structure

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Feature Extraction from LingBot-Video (Priority: P1) 🎯 MVP

**Goal**: Download pre-trained LingBot-Video model and video subset, extract latent activation vectors and expert masks on CPU.

**Independent Test**: A script runs on CPU, downloads model/data, extracts features, and saves non-empty NumPy arrays within 2 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for memory chunking logic in `tests/unit/test_memory_manager.py`
- [X] T011 [P] [US1] Integration test for feature extraction flow in `tests/integration/test_extract_features.py`

### Implementation for User Story 1

- [ ] T012.0.1 [P] [US1] Define sampling strategy: Create `code/utils/sampling_strategy.py` to define the stratified sampling logic based on 'action type'. Artifact: `code/utils/sampling_strategy.py`.
- [ ] T012.0.2 [ ] [US1] Generate sample list artifact: Create `data/raw/sample_list.csv` using the strategy from T012.0.1. Artifact: `data/raw/sample_list.csv`.
- [ ] T012.0.3 [P] [US1] Download LingBot-Video weights: Download the pre-trained LingBot-Video model weights from HuggingFace to `data/external/lingbot_weights/`. Artifact: `data/external/lingbot_weights/`.
- [ ] T012.0.4 [ ] [US1] Verify class balance: Create `code/utils/verify_balance.py` to ensure the sample list from T012.0.2 has a representative mix of action types. Artifact: `code/utils/verify_balance.py`. **Depends on** T012.0.2.
- [ ] T012.2.1 [P] [US1] Implement selection logic: Create `code/utils/select_clips.py` to select/stream clips based on the sample list. Artifact: `code/utils/select_clips.py`.
- [ ] T012.2.2 [P] [US1] Verify class balance: Run `code/utils/verify_balance.py` to confirm the selected clips meet diversity requirements. Artifact: `data/processed/balance_report.json`.
- [ ] T014 [US1] Implement frame subsampling AND temporal chunking strategy to stay within 7 GB RAM limit (FR-006). The task MUST implement both strategies: subsample frames if the clip is short, but chunk temporally if the clip is long to prevent OOM. (Reuses T005.1.1/T005.1.2). **Output Artifact**: `data/processed/chunking_config.json` (strategy config) and `data/processed/memory_log.json` (via T017.1).
- [ ] T014.2 [US1] Integrate memory chunking into extraction: Create `code/extraction/memory_integration.py` that explicitly calls T005.1.1 and T005.1.2 functions within the extraction pipeline logic. This task MUST ensure T012.1 imports and uses this module. **Dependency**: T014 must be complete.
- [ ] T012.1 [US1] Implement `code/extract_features.py` to download LingBot-Video model (HF) and video clips (streaming); ensure extraction logic uses T014.2 for memory management and skips full video decoding/generation, accessing only intermediate DiT layers. **Artifact**: Script that outputs to `data/processed/features.npy`. **Dependency**: T014.2, T012.0.3.
- [ ] T013 [US1] Implement `torch.no_grad()` inference to extract latent vectors and binary expert masks from intermediate DiT layers. **Deliverable**: Save extracted vectors and masks to `data/processed/features.npy`. **Verification**: Verify file exists and is non‑empty with expected dimensions (e.g., shape tuple).
- [X] T015 [US1] Add logic to handle download failures with exponential backoff, then fail gracefully (no synthetic fallback). **Artifact**: Implement retry logic in `code/extract_features.py` using `code/utils/retry.py`. **Verification**: Unit test in `tests/unit/test_retry_logic.py` confirms exponential backoff behavior.
- [ ] T016 [US1] Save extracted features as `data/processed/features.npy` with accompanying metadata JSON.
- [ ] T017 [US1] Add logging for extraction progress and memory usage. **Artifact**: Generate `data/processed/extract.log`. **Verification**: Log contains memory usage entries for each chunk. Verify `data/processed/memory_log.json` contains peak RAM entries for each chunk.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Independent Ground-Truth Labeling via 3D Reconstruction (Priority: P2)

**Goal**: Generate ground‑truth labels ("valid"/"invalid") by reconstructing 3D states and running a CPU physics simulation.

**Independent Test**: Script processes video clips, runs depth estimation and PyBullet simulation, outputs binary labels CSV/JSON.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for physics simulation wrapper in `tests/unit/test_physics_sim.py`
- [X] T019 [P] [US2] Integration test for labeling pipeline in `tests/integration/test_generate_labels.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/generate_labels.py` to run monocular depth/pose estimator (e.g., monodepth2) on video clips.
- [ ] T021.1 [US2] Implement 3D reconstruction logic: Create `code/labeling/reconstruct_3d.py` to extract positions **and velocities** from depth maps. **Artifact**: Save `EstimatedState3D` vectors to `data/processed/recon_states.npy`. **Verification**: Verify dimensions include velocity components.
- [ ] T021.2 [US2] Implement Kinematic Consistency Check: Create `code/labeling/kinematic_check.py` to filter trajectories that are kinematically impossible (e.g., negative depth). **Artifact**: `data/processed/kinematic_filter_log.json`.
- [ ] T021.3 [US2] Validate `EstimatedState3D` schema: Produce `data/processed/estimated_state_schema.json` confirming presence of position **and** velocity fields. **Artifact**: JSON schema file.
- [X] T022 [US2] Integrate `code/utils/physics_sim.py` to simulate reconstructed states in PyBullet.
- [ ] T023.1 [US2] Generate ground‑truth labels: Run reconstructed 3D states through PyBullet **and** apply synthetic perturbations (e.g., upward velocity boost) to a subset to create the "invalid" class. Labels are derived from the simulation outcome (valid/invalid). **Artifact**: Save provisional labels to `data/processed/raw_labels.csv`.
- [ ] T024 [US2] Separate low‑confidence / failed samples:  
    1. For clips with reconstruction confidence < 0.9 or simulation failure, write a row to `data/processed/null_labels.csv` (columns: clip_id, reason, confidence_score).  
    2. Merge only non‑null rows from `raw_labels.csv` into the final `data/processed/labels.csv` (columns: clip_id, label, confidence_score).  
    3. Create an empty `data/processed/excluded_samples.log` if no samples are excluded (ensures hashing).  
    **Artifact**: `null_labels.csv`, `labels.csv`, `excluded_samples.log`.
- [ ] T024.1.1 [P] [US2] Implement verification script: Create `code/labeling/verify_filtering.py` to confirm that every row in `null_labels.csv` is absent from `labels.csv` and that `excluded_samples.log` matches the null set.
- [ ] T024.1.2 [P] [US2] Generate verification report: Run `code/labeling/verify_filtering.py` to produce `data/processed/filtering_verification.json`.
- [X] T025 [US2] Save valid labels (including confidence scores) to `data/processed/labels.csv` and overall metadata to `data/processed/metadata.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Lightweight Classifier Training & Evaluation (Priority: P3)

**Goal**: Train shallow MLP/Random Forest on CPU to predict physical validity, report metrics and feature importance.

**Independent Test**: Training script ingests features/labels, trains model in <30 min, outputs F1‑score ≥ 0.75 (or null result report).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for classifier training logic in `tests/unit/test_train_classifier.py`
- [X] T028 [P] [US3] Integration test for end‑to‑end evaluation in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T030.1 [US3] Implement filtering logic: Create `code/classification/filter_data.py` that reads `labels.csv` **and** `null_labels.csv`, excludes null rows, and writes `data/processed/filtered_train.csv` and `data/processed/filtered_test.csv`. **Artifact**: filtered CSV files.
- [ ] T030.2 [US3] Implement report generation: Create `code/classification/generate_filter_report.py` to parse `labels.csv` and `null_labels.csv` and generate `data/processed/filtering_report.json`.
- [ ] T030.3 [US3] Verify report schema: Verify `data/processed/filtering_report.json` matches the required schema.
- [X] T031 [US3] Implement training of shallow MLP or Random Forest on CPU with limited grid search (FR‑004). Artifact: Save trained model weights to `data/processed/classifier.pkl`. Verification: Verify model can load and predict on test set. **Dependency**: T030.1 must be complete.
- [ ] T032.0 [US3] Compute Majority Class Predictor baseline: Create `code/classification/compute_baseline.py` that calculates the majority class in the filtered training set, computes its F1‑score, and writes `data/processed/baseline_f1.json`. **Artifact**: baseline F1 score.
- [ ] T032 [US3] Implement evaluation metrics calculation (F1, precision, recall) on held‑out test set (FR‑005) **and** compare against the baseline F1 from T032.0. Output combined results to `data/processed/evaluation_metrics.json`. **Artifact**: evaluation metrics JSON.
- [ ] T033 [US3] Implement feature importance analysis (e.g., SHAP). Save raw SHAP values to `data/processed/feature_importance.json` and a human‑readable interpretation to `shap_interpretation.md` that explicitly frames findings as associational only (FR‑007). **Artifact**: JSON + markdown.
- [X] T034 [US3] Add logic to explicitly frame results as ASSOCIATIONAL (avoid causal claims). Artifact: Update `docs/results_report.md` with "Associational Framing" section. Verification: Verify section text matches FR‑007 requirements.
- [ ] T035 [US3] Generate visualization of feature importance and save metrics to `data/processed/metrics.json`.
- [ ] T036 [US3] Implement `code/main_pipeline.py` to orchestrate full pipeline, update `state/manifest.yaml` with SHA‑256 hashes for all artifacts, and write a top‑level `pipeline_run_summary.json` summarizing success/failure of each phase.
- [ ] T036.2 [US3] Implement timing wrapper in `code/main_pipeline.py` that measures **the entire pipeline**, including download (T012.0.3), 3D reconstruction (T020), labeling (T023.1), training (T031) and evaluation (T032). Record total wall‑clock time and per‑stage timings in `pipeline_timing.json`. **Dependency**: Must run after all prior tasks are complete.
- [ ] T036.3.1 [US2] Prior Audit: Compute Pearson correlation between depth‑estimation confidence scores and perturbation type (synthetic vs. original) to verify label independence. Save report to `data/processed/prior_audit_report.json`. **Artifact**: Prior audit JSON.
- [ ] T036.3.2 [US3] Latent‑Space Independence Audit: Compute Pearson correlation between activation vectors and physical labels (excluding null rows) to assess hypothesis relevance. Save report to `data/processed/latent_audit_report.json`. **Artifact**: Latent audit JSON.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (README, usage guide). Artifact: Update `docs/README.md` and `docs/usage_guide.md`. Verification: Verify README contains quickstart instructions.
- [ ] T037.1 [P] Generate `results_report.md`: Create `docs/results_report.md` containing the final results. Mandatory Section: This report MUST include a dedicated "Associational Framing" section (FR‑007) explicitly stating that all correlations are associational and not causal, referencing the limitations of the observational data.
- [ ] T038 [P] Implement quickstart.md validation script: Create `scripts/validate_quickstart.py` to ensure reproducibility.
- [ ] T040 [P] Performance optimization: Optimize memory chunking logic in `code/extraction/memory_chunker.py` to minimize peak RAM usage. Artifact: Refactor `code/extraction/memory_chunker.py`. Verification: Verify peak RAM < 7 GB via `memory_log.json`.
- [ ] T041 [P] Additional unit tests in `tests/unit/`. Artifact: Add `tests/unit/test_data_loader.py::test_streaming`.

---

## Phase Dependencies

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

--- 

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
