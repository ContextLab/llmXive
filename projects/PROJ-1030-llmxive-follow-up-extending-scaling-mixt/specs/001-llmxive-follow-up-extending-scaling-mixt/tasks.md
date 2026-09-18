# Tasks: llmXive follow-up: extending "Scaling Mixture-of-Experts Video Pretraining for Embodied Intelligence"

**Input**: Design documents from `/specs/001-llmxive-physical-validator/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: `mkdir -p code code/utils data/raw data/processed tests/unit tests/integration docs/figures state`
- [X] T002 Initialize Python 3.11 project: Create `code/requirements.txt` containing pinned versions of [torch-cpu, transformers, datasets, pybullet, scikit-learn, opencv-python-headless, monodepth2, shap, huggingface-hub, pytest, ruff, black]
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools with pre-commit hooks

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `code/utils/memory_manager.py` for chunking and frame subsampling logic (FR-006)
- [X] T005 [P] Implement `code/utils/physics_sim.py` wrapper for PyBullet (scale normalization, error handling)
- [X] T006 [P] Setup `code/utils/prior_audit.py` to check for shared priors between depth and video models
- [ ] T006.3 [P] Define the 'Prior Audit' metric and threshold: Specify the algorithm to compare model priors (e.g., Pearson correlation of flattened weight matrices of initial layers) and set the explicit failure threshold (e.g., correlation > 0.1 indicates shared priors). This task defines the constants and criteria used by T006.4 and T006.5.
- [ ] T006.4 [P] Implement the core logic for `code/utils/prior_audit.py`: Implement the algorithm defined in T006.3 to calculate the correlation between the depth model and video model's initial layers. The task MUST return a boolean result (True if shared priors detected, False otherwise) based on the threshold defined in T006.3.
- [ ] T006.5 [P] Implement execution logic to run `code/utils/prior_audit.py` and record the pass/fail result in `state/manifest.yaml` (SC-005). The task MUST consume the output of T006.4. It MUST verify that the physics engine labels are mechanically decoupled from the video model's internal state generation process by ensuring the audit returns 'pass' (no shared priors). This task is responsible for writing the final `status` (pass/fail), the specific correlation metric value, and `details` to the manifest.
- [X] T007 [P] Create base data model `code/models/video_clip.py`: Define class `VideoClip` with fields [id, frames, duration, source_url]
- [ ] T007.1 [P] Create base data models in `code/models/`: Define classes `VideoClip`, `EstimatedState3D` (fields: positions, velocities, orientations, confidence_score), `ActivationPattern` (fields: latent_vector, expert_mask, layer_id), and `PhysicalLabel` (fields: clip_id, label, reason) in a single file to ensure consistency.
- [ ] T008 Configure error handling and logging infrastructure (including "FAIL LOUDLY" for data fetch)
- [X] T009 Setup environment configuration management and `data/.checksums.json` structure

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Feature Extraction from LingBot-Video (Priority: P1) 🎯 MVP

**Goal**: Download pre-trained LingBot-Video model and video subset, extract latent activation vectors and expert masks on CPU.

**Independent Test**: A script runs on CPU, downloads model/data, extracts features, and saves non-empty NumPy arrays within 2 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for memory chunking logic in `tests/unit/test_memory_manager.py`
- [X] T011 [P] [US1] Integration test for feature extraction flow in `tests/integration/test_extract_features.py`

### Implementation for User Story 1

- [ ] T012.0 [US1] Curate and define the specific set of video clips containing known physical violations. Use metadata keywords (e.g., 'collision', 'fall', 'drop') and heuristic frame-difference checks (e.g., > 15% motion between frames) on the source dataset to identify candidate clips. This creates a 'violation candidate list' used for stratified sampling in T012.2, avoiding circular dependency on the future physics labels. The task MUST verify that at least N clips are found; if not, fail loudly.
- [ ] T012.1 [US1] Implement `code/extract_features.py` to download LingBot-Video model (HF) and video clips (streaming); ensure extraction logic skips full video decoding/generation and only accesses intermediate DiT layers
- [ ] T012.2 [US1] Implement logic to select/stream a specific subset of video clips using a **stratified sampling strategy** based on the 'violation candidate list' from T012.0. Ensure a representative mix of valid and invalid physical states (using the metadata proxy), meeting memory and time constraints (FR-001, FR-006). The task MUST explicitly verify class balance based on the heuristic proxy from T012.0 before extraction begins, acknowledging the limitation that ground truth labels do not yet exist.
- [ ] T013 [US1] Implement `torch.no_grad()` inference to extract latent vectors and binary expert masks from intermediate DiT layers
- [ ] T014 [US1] Implement frame subsampling/temporal chunking strategy to stay within 7 GB RAM limit (FR-006)
- [ ] T015 [US1] Add logic to handle download failures with exponential backoff, then fail gracefully (no synthetic fallback)
- [ ] T016 [US1] Save extracted features as `data/processed/features.npy` with metadata JSON
- [ ] T017 [US1] Add logging for extraction progress and memory usage

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Independent Ground-Truth Labeling via 3D Reconstruction (Priority: P2)

**Goal**: Generate ground-truth labels ("valid"/"invalid") by reconstructing 3D states and running CPU physics simulation.

**Independent Test**: Script processes video clips, runs depth estimation and PyBullet simulation, outputs binary labels CSV/JSON.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for physics simulation wrapper in `tests/unit/test_physics_sim.py`
- [X] T019 [P] [US2] Integration test for labeling pipeline in `tests/integration/test_generate_labels.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/generate_labels.py` to run monocular depth/pose estimator (e.g., monodepth2) on video clips
- [ ] T021 [US2] Implement 3D state reconstruction logic to extract positions/velocities from depth maps
- [X] T022 [US2] Integrate `code/utils/physics_sim.py` to simulate reconstructed states in PyBullet
- [ ] T023 [US2] Implement logic to assign "valid"/"invalid" labels based on physics constraints (e.g., gravity, collision)
- [ ] T024 [US2] Implement a **labeling step** for samples with reconstruction confidence < 0.9 or simulation failures: **Exclude these samples from the primary training dataset** (`data/processed/labels.csv`). **Write** the excluded sample IDs and reasons to `data/processed/excluded_samples.log` as a side-effect of this exclusion. If no samples are excluded, create an empty `excluded_samples.log` file to ensure the artifact exists for hashing. This log file is required for audit and hashing in T036. Do NOT include these rows in the CSV. (FR-008)
- [ ] T025 [US2] Save valid labels to `data/processed/labels.csv` and metadata (confidence scores) to `data/processed/metadata.json`
- [ ] T026 [US2] Add logging for simulation errors and excluded samples

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Lightweight Classifier Training & Evaluation (Priority: P3)

**Goal**: Train shallow MLP/Random Forest on CPU to predict physical validity, report metrics and feature importance.

**Independent Test**: Training script ingests features/labels, trains model in <30 mins, outputs F1-score ≥ 0.75 (or null result report).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for classifier training logic in `tests/unit/test_train_classifier.py`
- [ ] T028 [P] [US3] Integration test for end-to-end evaluation in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/train_classifier.py` to load `features.npy` and `labels.csv`
- [ ] T030 [US3] Implement data preprocessing: temporal split for train/test sets. **Filter out "null" labels** (if any remain from simulation failures not caught in T024) from the training and test sets. Generate a report `data/processed/filtering_report.json` with the schema: `{\"total_samples\": int, \"excluded_by_confidence\": int, \"excluded_by_simulation\": int, \"retained\": int}` to ensure data hygiene and verify the filtering logic. **Do not calculate baselines here**; this task is strictly for data preparation and splitting.
- [ ] T031 [US3] Implement training of shallow MLP or Random Forest on CPU with limited grid search (FR-004)
- [ ] T032.1 [US3] Implement computation of the baseline distribution of expert activations across the dataset and save to `data/processed/activation_distribution.json` (SC-002)
- [ ] T032 [US3] Implement evaluation metrics calculation (F1, precision, recall) on held-out test set (FR-005). **Explicitly calculate and report the "random guessing" baseline** using the F1-score of a majority-class predictor on the **filtered** test set (as prepared by T030) in `metrics.json` to serve as the comparison reference required by SC-001. This is the authoritative source for the SC-001 baseline. Verify that the baseline calculation uses the exact same sample IDs as the evaluation set.
- [ ] T033 [US3] Implement feature importance analysis (e.g., SHAP) comparing results against the baseline distribution from T032.1 to identify predictive sub-networks (FR-007, SC-002)
- [ ] T034 [US3] Add logic to explicitly frame results as ASSOCIATIONAL (avoid causal claims)
- [ ] T035 [US3] Generate visualization of feature importance and save metrics to `data/processed/metrics.json`
- [ ] T036 [US3] Implement `code/main_pipeline.py` to orchestrate full pipeline and update `state/manifest.yaml` with SHA-256 hashes for **all artifacts**. The specific artifacts to hash are: `data/processed/features.npy`, `data/processed/labels.csv`, `data/processed/metadata.json`, `data/processed/metrics.json`, `data/processed/activation_distribution.json`, and `data/processed/excluded_samples.log`. (FR-005). **Note**: This task depends on T024 to ensure `excluded_samples.log` exists (even if empty). **Note**: If `excluded_samples.log` is missing, create an empty file before hashing.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (README, usage guide)
- [ ] T038 Run `quickstart.md` validation to ensure reproducibility
- [ ] T039 [P] Performance optimization: Add timing wrapper to `code/main_pipeline.py` that asserts total runtime < 21600s
- [ ] T040 [P] Performance optimization: Optimize memory chunking logic in `code/extract_features.py` to minimize peak RAM usage
- [ ] T041 [P] Additional unit tests in `tests/unit/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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

### Specific Task Dependencies

- **T012.0** must complete before **T012.2** (curation before sampling).
- **T006.3** must complete before **T006.4** (definition before implementation).
- **T006.4** must complete before **T006.5** (audit logic before verification/logging).
- **T024** must complete before **T036** (log file generation before hashing).
- **T030** must complete before **T031** and **T032** (data prep before training/metrics).
- **T032** is the authoritative source for SC-001 baseline; T032.1 handles SC-002.
- **T036** depends on T024 completion to ensure `excluded_samples.log` exists (even if empty).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
