# Tasks: Non-Neural Approximation of VLA Priors

**Input**: Design documents from `/specs/001-non-neural-vla-approximation/`
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

- [ ] T001a Create directory structure `code/`, `code/utils/`, `code/tests/`, `data/raw/`, `data/processed/`, `data/results/`, `artifacts/models/`
- [ ] T001b Create `code/01_ingest.py`, `code/02_cluster.py`, `code/03_train.py`, `code/04_inference.py`, `code/05_simulate.py`, `code/06_evaluate.py` as empty files
- [ ] T001c Create `requirements.txt` with pinned dependencies: `datasets`, `scikit-learn`, `transformers`, `pybullet`, `pandas`, `numpy`, `scipy`, `pyyaml`, `sklearn-mixture`
- [ ] T001d Initialize `code/utils/seeds.py`, `code/utils/kinematics.py`, `code/utils/validation.py` as empty files
- [ ] T001e Create `code/tests/` placeholder `__init__.py` and `.gitkeep` files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement global seed management in `code/utils/seeds.py` to ensure reproducibility across all scripts (set `random_state`, `torch.manual_seed`)
- [ ] T005 [P] Implement kinematic feature extraction utilities (velocity, acceleration, joint angles) in `code/utils/kinematics.py`
- [ ] T006 Setup environment configuration management for dataset paths, simulation parameters, and **clustering strategy parameters** (e.g., silhouette threshold, k-decrement step, max attempts) in `code/utils/config.py`
- [ ] T007 Create base data validation schema and checksumming logic in `code/utils/validation.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Ingestion and Trajectory Clustering (Priority: P1) 🎯 MVP

**Goal**: Ingest Qwen-VLA dataset, extract text-action pairs, and cluster action sequences into behavioral groups using K-means.

**Independent Test**: Verify output contains up to 50 clusters, minimum 100 samples per cluster (if k>1), and kinematic features are normalized within physical bounds.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for kinematic feature normalization in `code/tests/test_kinematics.py`
- [ ] T011 [P] [US1] Integration test for clustering pipeline with synthetic data in `code/tests/test_cluster.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement dataset ingestion in `code/01_ingest.py`: Download Qwen-VLA/Hy-Embodied from HuggingFace, parse text-action pairs, validate presence, and **FAIL LOUDLY** (raise error) if download fails or data is missing (no synthetic fallback).
- [ ] T013 [US1] Implement streaming data loader in `code/01_ingest.py` to handle datasets >7GB using `datasets.load_dataset(..., streaming=True)` and chunked processing.
- [ ] T014 [US1] Implement kinematic feature extraction and normalization in `code/02_cluster.py`: Calculate velocity, acceleration, and joint angles from action sequences.
- [ ] T015 [US1] Implement K-means clustering in `code/02_cluster.py`: Cluster normalized features into up to 50 groups (k=50), assign samples to clusters.
- [ ] T016 [US1] Implement clustering validation in `code/02_cluster.py`: Calculate silhouette score; if < 0.25, reduce k using parameters (step size, max attempts) loaded from `code/utils/config.py` (as per FR-002a's deferred mechanism) and re-run until valid or k=1 (log warning if k=1 reached).
- [ ] T017 [US1] Save clustering artifacts (cluster centers, assignments, statistics) to `data/processed/clusters.json` and `data/processed/assignments.parquet`.
- [ ] T018 [US1] Verify clustering coverage: Ensure ≥ 98% of ingested samples are assigned to exactly one cluster.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Non-Neural Model Fitting and Inference (Priority: P2)

**Goal**: Fit a **Conditional Gaussian Mixture Model (CGMM)** to each cluster, mapping frozen BERT text embeddings to action distributions, and implement a CPU-only inference engine.

**Independent Test**: Verify held-out R² ≥ 0.6 (for CGMM), valid trajectory generation within 2s/prompt, and no GPU usage on CPU runner.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for BERT embedding generation in `code/tests/test_embeddings.py`
- [ ] T020 [P] [US2] Integration test for model training and inference on sample data in `code/tests/test_train.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement frozen BERT embedding generation in `code/03_train.py`: Load `bert-base-uncased`, encode text instructions, ensure CPU-only execution. (Prerequisite for T021a)
- [ ] T021a [US2] **Generate Training Embeddings**: Run the BERT encoder on the US-01 output (text instructions) to generate and save embeddings to `data/processed/train_embeddings.parquet` for use in T022. (Prerequisite for T022)
- [ ] T022 [US2] Implement **Conditional GMM (CGMM)** training in `code/03_train.py`: Fit a CGMM per cluster mapping BERT embeddings (from T021a) to actions (using `sklearn-mixture` or custom implementation) as the **sole primary model** per Plan deviation. Validate R² ≥ 0.6 and conditional variance.
- [ ] T027 [US2] Save trained CGMM models and BERT encoder to `artifacts/models/`.
- [ ] T023 [US2] Implement cluster selection logic in `code/04_inference.py`: For a new prompt, find nearest cluster based on BERT embedding distance (requires T027).
- [ ] T024 [US2] Implement trajectory sampling in `code/04_inference.py`: Sample from the fitted CGMM for the selected cluster to generate a complete trajectory array.
- [ ] T025 [US2] Implement OOD handling in `code/04_inference.py`: If prompt is far outside cluster distribution, default to nearest cluster and log "low-confidence" flag.
- [ ] T026 [US2] Validate inference performance: Ensure memory < 7GB and 100 prompts processed in ≤ 10 minutes on CPU runner.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Simulation Evaluation and Statistical Comparison (Priority: P3)

**Goal**: Execute generated trajectories in PyBullet, measure success/collision rates, and perform **McNemar's Test** against baselines.

**Independent Test**: Verify CSV output with success/collision flags and valid p-values from McNemar's Test.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for PyBullet simulation step and error handling in `code/tests/test_simulate.py`
- [ ] T029 [P] [US3] Integration test for full evaluation loop with mock data in `code/tests/test_evaluate.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement PyBullet simulation engine in `code/05_simulate.py`: Load robot model, execute trajectories for "grasp", "navigate", "place" tasks.
- [ ] T031 [US3] Implement simulation error handling in `code/05_simulate.py`: Catch kinematic constraint violations, record as "failure", continue to next prompt (do not crash).
- [ ] T032 [US3] Implement baseline generation in `code/05_simulate.py`: Generate random trajectories by uniform sampling within joint limits for comparison.
- [ ] T032a [US3] **Load VLA Proxy Baseline**: Attempt to load the VLA proxy baseline from the path defined in `code/utils/config.py`. If missing, proceed to T032b.
- [ ] T032b [US3] **Generate VLA Proxy Baseline**: If T032a fails to find the baseline, generate it (or raise a clear error if generation is not implemented) and save to the configured path.
- [ ] T033 [US3] Execute simulation loop in `code/05_simulate.py`: Run a set of test prompts per task type for non-neural model, random baseline, and VLA proxy.
- [ ] T034 [US3] Log simulation results to `data/results/simulation_logs.csv` (task type, success flag, collision count, execution time).
- [ ] T035 [US3] Implement **McNemar's Test** in `code/06_evaluate.py`: Perform McNemar's Test for binary success rates comparing non-neural vs. random vs. VLA proxy as the **primary statistical method** (per Plan correction to FR-006/SC-004). Report p-values and confidence intervals.
- [ ] T036 [US3] Calculate trajectory fidelity metric: Percentage of kinematic features within error margin of VLA proxy.
- [ ] T037 [US3] Generate final report in `data/results/evaluation_report.md` with p-values, confidence intervals, fidelity percentage, and complexity reduction factor.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates: Update `quickstart.md` with execution instructions and `research.md` with methodology notes (CGMM, McNemar's Test).
- [ ] T039a Code cleanup: Add type hints to `code/utils/seeds.py`, `code/utils/kinematics.py`, `code/utils/validation.py`.
- [ ] T039b Code cleanup: Remove duplicate imports and unused variables in `code/utils/` modules.
- [ ] T040 [P] Add unit tests for edge cases (OOD prompts, simulation crashes) in `code/tests/`.
- [ ] T041 Run `quickstart.md` validation to ensure end-to-end pipeline executes correctly.

**Note on Spec Alignment**: The Plan identifies a contradiction between the Spec (requiring Decision Trees/T-tests) and the Plan (requiring CGMM/McNemar's). The tasks above implement the **Plan's** methodological corrections. A formal kickback is required to update `spec.md` (FR-003, US-02, FR-006, SC-004) to reflect CGMM and McNemar's Test as the official requirements.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data artifacts (clusters, assignments) and T021a (embeddings)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 generated trajectories and T032b (VLA baseline)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 can start in parallel if US1 data is ready
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel (T022 is single task)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for kinematic feature normalization in code/tests/test_kinematics.py"
Task: "Integration test for clustering pipeline with synthetic data in code/tests/test_cluster.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset ingestion in code/01_ingest.py"
Task: "Implement kinematic feature extraction in code/02_cluster.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (clustering quality, data validity)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Non-neural policy)
4. Add User Story 3 → Test independently → Deploy/Demo (Full evaluation)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data)
   - Developer B: User Story 2 (Model)
   - Developer C: User Story 3 (Simulation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Dataset download tasks MUST fail loudly on error; never fallback to synthetic data.
- **Critical**: Use `streaming=True` for large datasets to fit within 7GB RAM.
- **Critical**: All simulation runs must be CPU-only; no GPU usage.
- **Critical**: T021 must complete before T021a; T021a must complete before T022; T027 must complete before T023-T024.
- **Critical**: T032a must complete before T033. If T032a fails, T032b must run before T033.
- **Critical**: T022 implements **only** CGMM. Decision Trees and Standard GMMs are excluded per Plan.
- **Critical**: T035 implements **only** McNemar's Test. Paired t-tests are excluded per Plan.