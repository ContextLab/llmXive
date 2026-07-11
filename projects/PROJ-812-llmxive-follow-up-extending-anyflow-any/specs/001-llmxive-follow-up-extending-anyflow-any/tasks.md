# Tasks: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-anyflow-any/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 [P] Create directory structure: `code/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/`
- [ ] T002 [P] Initialize Python 3.11 project with pinned `requirements.txt` (include `onnxruntime`, `torch`, `scikit-learn`, `pandas`, `opencv-python-headless`, `datasets`, `ucimlrepo`, `raft-torch`, `rich`, `scipy`)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [ ] T004 [P] Setup `pytest` configuration and directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement `code/utils/logging.py` for standardized logging across pipeline
- [ ] T006 [P] Implement `code/utils/memory_utils.py` for explicit CPU memory clearing (garbage collection) after each clip
- [ ] T007 [P] Implement `code/utils/hash_utils.py` for SHA-256 checksumming of raw data and model weights
- [ ] T008 [P] Create base schema definitions in `contracts/` (annotation, metric, result, sensitivity)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Ground-Truth Annotation (Priority: P1) 🎯 MVP

**Goal**: Curate a dataset of short video clips (UCF101, Kinetics, DAVIS) and manually annotate each with a temporal continuity score (0.0 to 1.0).

**Independent Test**: A script ingests raw video URLs, downloads a representative sample (N=500), and outputs a CSV file where every row contains a video ID, file path, and a manual score, verified by spot-check.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `code/data_curation/download_clips.py` to fetch clips from Kinetics (`datasets.load_dataset`) and UCF101 (`ucimlrepo`), ensuring 16-frame clips with mixed motion/cuts. Output to `data/raw/clips/`.
- [ ] T010 [US1] Implement `code/data_curation/download_ucf101_manual.py` as a fallback for manual download if `ucimlrepo` fails.
- [ ] T011 [US1] Implement `code/data_curation/annotate.py` CLI tool using `rich` library to display frames and record scores [0.0, 1.0]. Output CSV `data/raw/annotations.csv` with columns: `video_id`, `file_path`, `score`, `annotator_id`.
- [ ] T012 [US1] Implement `code/data_curation/merge_annotations.py` to merge two annotation CSVs for [deferred] of clips, calculate Krippendorff's Alpha, and output `data/processed/krippendorff_alpha.json`. Halt if alpha < 0.6.
- [ ] T013 [US1] Implement `code/data_curation/binarize_labels.py` to create binary labels (Continuous < 0.4, Discontinuous > 0.6) from `data/raw/annotations.csv` and output `data/processed/binary_labels.csv`.
- [ ] T014 [US1] Implement validation script `code/data_curation/validate_annotations.py` to ensure `data/raw/annotations.csv` has valid paths and scores in [0.0, 1.0] range.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Tractable Latent Divergence Calculation (Priority: P2)

**Goal**: Load a frozen AnyFlow model in ONNX Runtime (CPU-only) and compute "flow-map divergence" and "external optical flow variance" for every video clip without GPU.

**Independent Test**: A script processes 500 clips on a CPU-only runner, completes in ≤6 hours, uses <7GB RAM, and outputs a CSV with divergence scores and optical flow variance.

### Implementation for User Story 2

- [ ] T015 [US2] Implement `code/metric_calculation/load_model.py` to load AnyFlow to ONNX, verify SHA-256 hash, and check layer count/input-output shapes against architecture spec.
- [ ] T016 [US2] Implement `code/metric_calculation/extract_latents.py` to extract latent trajectories for 16-frame sequences using ONNX Runtime (CPU) and write to `data/processed/latents.npy`.
- [ ] T017 [US2] Implement `code/metric_calculation/compute_divergence.py` to read `data/processed/latents.npy`, use `scipy.integrate.ode` for N=1000 step Euler rollout, calculate L2 distance, and write `data/processed/divergence_scores.csv` with columns `clip_id`, `divergence`.
- [ ] T018 [US2] Implement `code/metric_calculation/compute_optical_flow.py` using `raft-small` (CPU) to calculate external flow variance for each clip (auxiliary metric for robustness) and write `data/processed/optical_flow_metrics.csv`.
- [ ] T019 [US2] Implement `code/metric_calculation/quantization_test.py` to run a subset with float16 vs float32; verify correlation stability ($\Delta r < 0.05$) or halt.
- [ ] T020 [US2] Implement batch processing logic in `code/main.py` to iterate clips, clear memory after each, and log progress/errors without crashing.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Threshold Sensitivity (Priority: P3)

**Goal**: Perform Pearson/Spearman correlation between manual continuity scores and divergence metrics, and run sensitivity analysis on classification thresholds.

**Independent Test**: A statistical script reads `data/raw/annotations.csv` (Manual Continuity Scores) and `data/processed/divergence_scores.csv`, outputs Pearson $r$, Spearman $\rho$, p-value, and a sensitivity report for thresholds {0.01, 0.05, 0.1}.

### Implementation for User Story 3

- [ ] T021 [US3] Implement `code/analysis/distribution.py` to calculate variance and histogram of manual scores from `data/raw/annotations.csv`; explicitly report variance (SC-004).
- [ ] T022 [US3] Implement `code/analysis/power_analysis.py` to calculate Minimum Detectable Effect Size (MDES) for N=500, power=0.8, alpha=0.05.
- [ ] T023 [US3] Implement `code/analysis/correlation.py` to read `data/processed/divergence_scores.csv` (from T017) and `data/raw/annotations.csv` (from T011), compute Pearson $r$ and Spearman $\rho$ between **Internal Divergence** and **Manual Continuity Scores** (Ground Truth), and write `data/processed/correlation_results.json` with p-value. This task establishes the primary chain of evidence from T011 to T023, fulfilling FR-005 and SC-001.
- [ ] T024 [US3] Implement `code/analysis/sensitivity.py` to read `data/processed/binary_labels.csv` and `data/processed/divergence_scores.csv`, sweep thresholds {, 0.05, 0.1}, and report false-positive/negative rates (SC-003).
- [ ] T025 [US3] Implement `code/analysis/report.py` to generate final JSON report including Runtime Environment (SC-005), Provenance Declaration, and explicit "CPU-only" statement.
- [ ] T026 [US3] Implement error handling for static images (divergence score assignment) and corrupted files (skip and flag).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Documentation updates: Create `docs/quickstart.md` with installation steps and `docs/data-model.md` with new schema.
- [ ] T028 Code cleanup and refactoring for memory efficiency
- [ ] T029 Run full pipeline integration test on CI (verify ≤6h runtime)
- [ ] T030 [P] Additional unit tests for metric logic in `tests/unit/`
- [ ] T031 Verify `run_quickstart.sh` validates all artifacts

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US1 (Manual Scores) and US2 (Divergence)** for the primary correlation analysis.

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
- **Critical Note on Plan vs. Spec**: The `plan.md` document currently contains a contradiction in its "Technical Approach" and "Phase 2" sections, suggesting correlation with "External Optical Flow Variance". The `spec.md` (FR-005) and `Constitution` (Principle VII) explicitly mandate correlation with **Manual Continuity Scores**. This `tasks.md` follows the `spec.md` and `Constitution` as the source of truth. The `plan.md` must be updated to reflect this correction: Optical Flow is an auxiliary metric, but Manual Scores are the ground truth for the primary hypothesis.