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
- [ ] T009 [US1] Implement `code/data_curation/download_clips.py` to fetch clips from Kinetics (`datasets.load_dataset`) and UCF101 (`ucimlrepo`). **MUST implement a stratified sampling strategy**: calculate frame-difference MSE for all candidates, sort by MSE, and guarantee that at least 20% of the final curated set (N=500) are selected as 'cuts' (highest MSE) to satisfy FR-001. Output to `data/raw/clips/`.
- [ ] T010 [US1] Implement `code/data_curation/download_ucf101_manual.py` as a fallback for manual download if `ucimlrepo` fails.
- [ ] T011 [US1] Implement `code/data_curation/annotate.py` CLI tool using `rich` library. **MUST enforce strict blinding**: The UI must display ONLY pixel frames and MUST NOT display any model-derived metrics (optical flow, latent vectors, divergence scores). The annotator must record a score [0.0, 1.0] based solely on pixel-space visual inspection to satisfy FR-002. Output CSV `data/raw/annotations.csv` with columns: `video_id`, `file_path`, `score`, `annotator_id`.
- [ ] T012 [US1] Implement `code/data_curation/validate_annotations.py` to ensure `data/raw/annotations.csv` has valid paths and scores in [0.0, 1.0] range.
- [ ] T013 [US1] Implement `code/data_curation/binarize_labels.py` to create binary labels (Continuous < 0.4, Discontinuous > 0.6) from `data/raw/annotations.csv` and output `data/processed/binary_labels.csv`. (Note: Used for auxiliary checks only, not primary sensitivity analysis).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - CPU-Tractable Latent Divergence Calculation (Priority: P2)

**Goal**: Load a frozen AnyFlow model in ONNX Runtime (CPU-only) and compute "flow-map divergence" for every video clip without GPU.

**Independent Test**: A script processes 500 clips on a CPU-only runner, completes in ≤6 hours, uses <7GB RAM, and outputs a CSV with divergence scores.

### Implementation for User Story 2

- [ ] T014 [US2] Implement `code/metric_calculation/load_model.py` to load AnyFlow to ONNX, verify SHA-256 hash, and check layer count/input-output shapes against architecture spec.
- [ ] T015 [US2] Implement `code/metric_calculation/extract_latents.py` to extract latent trajectories for 16-frame sequences using ONNX Runtime (CPU) and write to `data/processed/latents.npy`.
- [ ] T016 [US2] Implement `code/metric_calculation/preflight_check.py` to run the first 5 clips, estimate total runtime, and enforce the time budget constraint

The research question, method, and references remain unchanged as per the planning document requirements. (FR-009). **MUST implement fallback**: If projected runtime > 5.5h, reduce Euler steps to N=200 (if validated) instead of halting.
- [ ] T017 [US2] Implement `code/metric_calculation/compute_divergence.py` to read `data/processed/latents.npy`, use a **custom Explicit Euler implementation** (x_{t+1} = x_t + h * f(x_t)) with fixed N=500 steps (or N=200 if determined by T016), calculate L2 distance, and write `data/processed/divergence_scores.csv` with columns `clip_id`, `divergence`. **Do NOT use `scipy.integrate.ode`**.
- [ ] T018 [US2] Implement batch processing logic in `code/main.py` to iterate clips, clear memory after each, and log progress/errors without crashing. This task drives T017.
- [ ] T019 [US2] Implement error handling for static images (assign baseline divergence) and corrupted files (skip and flag in `data/processed/error_log.csv`).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Correlation Analysis and Threshold Sensitivity (Priority: P3)

**Goal**: Perform Pearson/Spearman correlation between manual continuity scores and divergence metrics, and run sensitivity analysis on classification thresholds.

**Independent Test**: A statistical script reads `data/raw/annotations.csv` (Manual Continuity Scores) and `data/processed/divergence_scores.csv`, outputs Pearson $r$, Spearman $\rho$, p-value, and a sensitivity report for thresholds {0.01, 0.05, 0.1}.

### Implementation for User Story 3

- [ ] T020 [US3] Implement `code/analysis/distribution.py` to calculate variance and histogram of manual scores from `data/raw/annotations.csv`; explicitly report variance (SC-004). Halt if variance < 0.05 (FR-010).
- [ ] T021 [US3] Implement `code/analysis/power_analysis.py` to calculate Minimum Detectable Effect Size (MDES) for N=500, power=0.8, alpha=0.05.
- [ ] T022 [US3] Implement `code/analysis/correlation.py` to read `data/processed/divergence_scores.csv` (from T017) and `data/raw/annotations.csv` (from T011), compute Pearson $r$ and Spearman $\rho$ between **Internal Divergence** and **Manual Continuity Scores** (Ground Truth), and write `data/processed/correlation_results.json` with p-value. This task establishes the primary chain of evidence from T011 to T022, fulfilling FR-005 and SC-001.
- [ ] T023 [US3] Implement `code/analysis/sensitivity.py` to read `data/raw/annotations.csv` (continuous scores) and `data/processed/divergence_scores.csv`, sweep thresholds {, 0.05, 0.1}, and report false-positive/negative rates (SC-003). **Do NOT rely on `data/processed/binary_labels.csv` from T013**.
- [ ] T024 [US3] Implement `code/analysis/report.py` to generate final JSON report including Runtime Environment (SC-005), Provenance Declaration, explicit "CPU-only" statement, and the **mandatory injection** of the string: "The 'flow-map divergence' metric is a proxy for model instability and the correlation analysis tests the hypothesis that this instability correlates with semantic discontinuity." (FR-007, FR-008).
- [ ] T025 [US3] Implement variance check enforcement in `code/main.py` to prevent correlation analysis (T022) and report generation (T024) if `variance_report.csv` indicates insufficient variance. This must run BEFORE T022 and T024.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T026 [P] Documentation updates: Create `docs/quickstart.md` with installation steps and `docs/data-model.md` with new schema.
- [ ] T027 Code cleanup and refactoring for memory efficiency
- [ ] T028 Run full pipeline integration test on CI (verify ≤6h runtime)
- [ ] T029 [P] Additional unit tests for metric logic in `tests/unit/`
- [ ] T030 [P] Verify `run_quickstart.sh` validates all artifacts

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
- **Compute Feasibility**: All inference tasks (T014-T019) are strictly CPU-bound. No CUDA, no GPU quantization, no large model loading. The Euler baseline uses N=500 steps with a preflight check (T016) to fallback to N=200 if necessary to meet the 6-hour budget.
- **Data Integrity**: T009 and T010 ensure real data from verified sources. T011 ensures ground truth is human-annotated and blinded to model metrics. No synthetic data or fake metrics are generated.
- **Ordering**: T017 (Divergence) and T011 (Annotations) must complete before T022 (Correlation). T016 (Preflight) must run before T017. T025 (Variance Check) must run before T022 and T024.