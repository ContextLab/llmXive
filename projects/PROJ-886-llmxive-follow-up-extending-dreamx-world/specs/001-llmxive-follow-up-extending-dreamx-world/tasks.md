# Tasks: DreamX-Lite: Geometric Priors for 3D Consistency

**Input**: Design documents from `/specs/001-dreamx-lite-geometric-priors/`
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

## Phase 0: Data Verification & Fallback (Pre-Execution)

**Purpose**: Verify data sources and implement fallback logic BEFORE any primary claim generation.

- [ ] T001 Create `projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/` directory structure
- [ ] T002 Create `data/raw/` and `data/derived/` directories
- [ ] T003 Create `code/`, `code/models/`, `code/pipeline/`, `code/analysis/`, `code/utils/` directories
- [ ] T004 [P] Create `tests/unit/` and `tests/integration/` directories
- [ ] T005 Initialize Python 3.10+ project with `requirements.txt` (torch CPU, transformers, datasets, colmap, scipy, pandas, numpy, opencv-python, scikit-learn)
- [ ] T006 Configure environment variables and random seed fixation in `code/utils/config.py` (Sequential: Global seed must be set once)
- [ ] T007 Implement `code/utils/io.py` for data loading, checksumming, and logging
- [ ] T008 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T009 [P] Implement `code/models/__init__.py` and base model loader structure
- [ ] T010 [P] Setup directory structure for `data/raw/`, `data/derived/`, and `code/` submodules (Verification step)
- [ ] T011 [US1] Implement 'Logic Verification' mode switch in `code/utils/io.py`: If DreamX-World data is missing, abort primary claim and switch to ScanNet fallback, marking results as 'Pending Data Access' (Per Plan Phase 0 & Data Fallback Protocol)
- [ ] T012 [US2] Implement data loader in `code/utils/io.py` to fetch DreamX-World subset OR ScanNet fallback (Per T011 logic): MUST fail loudly if NEITHER source is available; MUST NOT use synthetic data

---

## Phase 1: Model Abstraction & Configuration (User Story 1)

**Purpose**: Replace learned E-PRoPE with fixed 4x4 camera projection and verify CPU initialization

**Independent Test**: Load pre-trained weights, apply modification, verify forward pass accepts 4x4 matrices without CUDA errors and parameter count decreases.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Unit test for parameter count reduction in `tests/unit/test_model_ablation.py`
- [ ] T014 [P] [US1] Unit test for deterministic output on fixed input in `tests/unit/test_determinism.py`

### Implementation for User Story 1

- [ ] T015 [P] [US1] Implement `code/models/dreamx_base.py` to load pre-trained DreamX-World 1.0 DiT weights AND define `embedding_dim` constant (e.g., 768)
- [ ] T016 [US1] Implement `code/models/dreamx_lite.py` replacing E-PRoPE with a linear projection layer mapping from a low-dimensional input space to the embedding dimension. (fixed, non-trainable, using `embedding_dim` from T015)
- [ ] T017 [US1] Verify `dreamx_lite` initialization completes without CUDA errors on CPU runner
- [ ] T018 [US1] Implement forward pass wrapper in `code/models/dreamx_lite.py` to accept 4x4 camera extrinsic matrices
- [ ] T019 [US1] Add logging for parameter count delta and layer replacement confirmation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 2: Evaluation Integrity & Independence (User Story 4)

**Purpose**: Ensure metric pipeline is strictly decoupled from generative model internals

**Independent Test**: Static analysis confirms no imports of DiT backbone/attention maps; function signature accepts only frames and extrinsics.

### Implementation for User Story 4

- [ ] T020 [P] [US4] Add static analysis check in CI to verify `code/pipeline/evaluate.py` has no imports of `dit_attention`, `latent_space`, or model internals
- [ ] T021 [US4] Refactor `code/pipeline/evaluate.py` function signatures to accept only `numpy` frames and `4x4` matrices
- [ ] T022 [US4] Document the "Blindness" constraint in `code/pipeline/evaluate.py` docstrings and README

---

## Phase 3: Long-Horizon Rollout & Metric Computation (User Story 2)

**Purpose**: Generate videos, recover trajectories via SfM, and compute MAE/Scale Drift

**Independent Test**: Run inference on 5 trajectories, generate MP4s, run SfM, output JSON/CSV with MAE and convergence flags.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for metric independence (no internal model imports) in `tests/unit/test_metrics.py`
- [ ] T024 [P] [US2] Integration test for end-to-end generation and SfM on a single sample in `tests/integration/test_rollout.py`

### Implementation for User Story 2

- [ ] T025 [P] [US2] Implement `code/pipeline/generate.py` to generate 10-second video rollouts for Baseline and DreamX-Lite using identical prompts
- [ ] T026 [US2] Implement `code/pipeline/evaluate.py` to run external COLMAP SfM on generated video frames
- [ ] T027 [US2] Implement Procrustes Alignment logic in `code/pipeline/evaluate.py` to resolve scale/rotation ambiguity; Output: Aligned Trajectory (Input for T028)
- [ ] T028 [US2] Implement MAE calculation (position, rotation) and Scale Drift metric in `code/pipeline/evaluate.py` using aligned trajectories from T027
- [ ] T029 [US2] Implement SfM failure handling in `code/pipeline/evaluate.py`: record `convergence=false`, `sfm_failure_reason`, and a **sentinel MAE value (-1.0)** for position/rotation (Per Spec FR-004)
- [ ] T030 [US2] Create `data/derived/metrics.csv` schema and writer to log results for 50 trajectories (Consumes T029's sentinel schema)

**Checkpoint**: At this point, User Stories 1, 2, AND 4 should work independently

---

## Phase 4: Statistical Significance & Sensitivity Analysis (User Story 3)

**Purpose**: Perform McNemar's test, Wilcoxon signed-rank test, and threshold sensitivity sweep

**Independent Test**: Provide CSV of paired scores, verify output of test statistics, p-values, and sensitivity table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for McNemar and Wilcoxon logic on mock data in `tests/unit/test_stats.py`
- [ ] T032 [P] [US3] Integration test for sensitivity sweep in `tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T033 [P] [US3] Implement `code/analysis/stats.py` with McNemar's test for binary convergence flags; explicitly state null hypotheses (Per Spec US-3)
- [ ] T034 [US3] Implement `code/analysis/stats.py` to calculate and report 'Censoring Rate' for both models (Per Plan Phase 3)
- [ ] T035 [US3] Implement `code/analysis/sensitivity.py` to sweep thresholds including low values such as 0.05 and 0.1, and compute success rates
- [ ] T036 [US3] Implement `code/analysis/stats.py` with Wilcoxon signed-rank test for MAE scores: filter for `convergence=true` trajectories only (Per Spec FR-005); depends on T030 (metrics.csv) which includes T029's sentinel values
- [ ] T037 [US3] Generate `data/derived/statistical_results.json` containing p-values, test statistics, and **Information-Theoretic Sufficiency Ratio** (Per Spec SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `README.md` and `docs/` covering Data Fallback Protocol
- [ ] T039 Code cleanup and refactoring for CPU memory optimization: Refactor `code/pipeline/generate.py` to use streaming if needed to keep peak memory < 6GB (Per NFR-001)
- [ ] T040 Performance optimization: Ensure 50-trajectory run completes within 6 hours on CPU
- [ ] T041 [P] Additional unit tests for edge cases (singularities, extreme rotations) in `tests/unit/`
- [ ] T042 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Setup + Data)**: No dependencies - can start immediately
- **Phase 1 (Model)**: Depends on Phase 0 completion
- **Phase 2 (Integrity)**: Depends on Phase 0 completion
- **Phase 3 (Pipeline)**: Depends on Phase 0 and Phase 1 (Model) completion
- **Phase 4 (Stats)**: Depends on Phase 3 (Metrics) completion
- **Phase 5 (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 0 - No dependencies on other stories
- **User Story 4 (P1)**: Can start after Phase 0 - Ensures US2 implementation is clean
- **User Story 2 (P2)**: Can start after Phase 0 and Phase 1 - Requires US1 model implementation
- **User Story 3 (P3)**: Can start after Phase 0 and Phase 3 - Requires US2 metric outputs

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 0)
- Once Phase 0 completes, US1, US4, and US2 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for parameter count reduction in tests/unit/test_model_ablation.py"
Task: "Unit test for deterministic output on fixed input in tests/unit/test_determinism.py"

# Launch all models for User Story 1 together:
Task: "Implement code/models/dreamx_base.py to load pre-trained DreamX-World 1.0 DiT weights"
Task: "Implement code/models/dreamx_lite.py replacing E-PRoPE with nn.Linear(16, embedding_dim)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Setup + Data Verification
2. Complete Phase 1: User Story 1
3. **STOP and VALIDATE**: Test User Story 1 independently (CPU load, param count)
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 4 → Ensure metric integrity
4. Add User Story 2 → Test independently (Generation + SfM) → Deploy/Demo
5. Add User Story 3 → Test independently (Stats) → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 together
2. Once Phase 0 is done:
   - Developer A: User Story 1 (Model Ablation)
   - Developer B: User Story 4 (Integrity) & User Story 2 (Pipeline)
   - Developer C: User Story 3 (Stats)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Data loaders must implement fallback logic (T011); no synthetic fallbacks allowed (Plan Section: Data Fallback Protocol)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Sentinel Values**: Failed SfM trajectories MUST record MAE = -1.0 (Sentinel), not null (Per Spec FR-004)
- **Statistical Scope**: Wilcoxon test runs ONLY on `convergence=true` trajectories (Per Spec FR-005)