# Tasks: llmXive follow-up: extending "AnyFlow: Any-Step Video Diffusion Model with On-Policy Flow Map Distil"

**Input**: Design documents from `/specs/001-gene-regulation/`
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
  - Delivered as a MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create root directory `projects/PROJ-812-llmxive-follow-up-extending-anyflow-any/`
- [ ] T001b [P] Create `code/`, `data/`, `tests/`, `docs/` directories
- [ ] T001c [P] Create `data/raw/`, `data/processed/`, `data/annotations/`, `code/pipeline/`, `code/models/`, `code/utils/` subdirectories
- [ ] T002 Initialize Python 3.11 project with dependencies: `onnxruntime`, `opencv-python`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `tqdm`, `pyyaml`, `decord`, `psutil` in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data schema definition for US3.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` with global seeds, thresholds, and timeout constants (a fixed duration per clip, a total duration spanning multiple hours)
- [ ] T004c [P] [US2] Document statistical power justification for N=60 sample size in `code/config.py` comments and `docs/research.md`, citing plan deviation from Spec N=500. **Specifics**: Must include power analysis for Pearson correlation (alpha=0.05, beta=0.2, effect size=0.3).
- [ ] T004d [P] Define the schema and validation logic for human labels: Create `code/utils/schema.py` defining the expected CSV schema (`clip_id`, `rater_id`, `label`) and validation rules (Multiple distinct raters per clip). Do NOT generate data; this task defines the contract for manual data creation.
- [ ] T004f [P] Update `state/projects/PROJ-812-llmxive-follow-up-extending-anyflow-any.yaml` artifact hash and timestamp to reflect the major scope change from N=500 to N=60, satisfying Constitution Principle V (Versioning Discipline). **Requirement**: Must update the `updated_at` field and specifically update the `artifact_hashes` map entry for `plan.md` with the new content hash of the plan file.
- [ ] T004g [P] [US2] Document statistical limitations of the N=60 pilot study in `docs/research.md`. **Specifics**: Explicitly state that the pilot is for feasibility and correlation direction only, and that the small held-out set limits the statistical power for the threshold model (FR-004).
- [ ] T005 [P] Implement `code/utils/logging.py` for CPU/Memory logging (FR-005) with `psutil` integration
- [ ] T006 [P] Setup `code/pipeline/__init__.py` and directory structure for `loader`, `feature_extractor`, `divergence`, `analyzer`
- [ ] T007 Create base data models/entities (`VideoClip`, `StatisticalFeature`, `DivergenceMetric`) in `code/models/` (or dataclasses in `code/pipeline/`)
- [ ] T008 Configure error handling infrastructure to catch and log `VideoClip` corruption (FR-006) without terminating batch
- [ ] T009 Setup environment configuration management for dataset paths and output directories

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Flow-Map Divergence Measurement (Priority: P1) 🎯 MVP

**Goal**: Automatically compute the "flow-map divergence" (L2 distance) for video clips using the AnyFlow model in CPU-only mode.

**Independent Test**: A script runs on a single video clip file and outputs a single floating-point divergence value, verifiable against manual Euler rollout calculations.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for `code/pipeline/divergence.py` L2 calculation logic in `tests/unit/test_divergence.py`
- [ ] T011 [P] [US1] Integration test for single clip processing flow in `tests/integration/test_divergence_flow.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/pipeline/loader.py` for video loading, corruption handling, and `decord` seek (FR-006)
- [ ] T013 [P] [US1] Implement `code/models/anyflow_onnx.py` to load frozen AnyFlow model via ONNX runtime (CPU-only, no CUDA)
- [ ] T014 [US1] Implement `code/pipeline/divergence.py` to execute high-resolution Euler rollout and compute L2 distance (FR-001). Must populate `DivergenceMetric` entity.
- [ ] T015 [US1] Implement timeout logic in `code/pipeline/divergence.py`: if >15 mins, log "timeout" and exclude from primary analysis. **Implements Plan deviation**: excludes timeouts instead of fallback to preserve metric integrity. Record exclusion in `data/processed/timeout_log.csv` and set `VideoClip.status` to "timeout".
- [ ] T016 [US1] Add logging of CPU utilization and execution time per clip (FR-005)
- [ ] T017 [US1] Add error handling for corrupted frames/black frames to skip gracefully (Edge Cases)
- [ ] T017c [US1] Implement logic in `code/pipeline/divergence.py` to detect numerical non-convergence of the Euler rollout. Flag such clips as "failed ground truth" and exclude from correlation analysis. **Requirement**: Must log the specific reason for non-convergence (e.g., 'divergence threshold exceeded' vs 'numerical overflow') to `data/processed/convergence_fail_log.csv` to satisfy Single Source of Truth.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Feature Extraction & Correlation Analysis (Priority: P2)

**Goal**: Extract statistical features from clips and correlate them with divergence values to identify instability predictors.

**Independent Test**: A dataset of clips with pre-computed divergence values yields a correlation matrix and regression model verifiable via `scipy`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for optical flow and MSE calculation in `tests/unit/test_feature_extractor.py`
- [ ] T019 [P] [US2] Integration test for correlation analysis pipeline in `tests/integration/test_correlation_flow.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/pipeline/feature_extractor.py` to calculate optical flow magnitude variance, frame-to-frame MSE, and temporal gradient sparsity (FR-002). Must populate `StatisticalFeature` entity.
- [ ] T021 [US2] Implement `code/pipeline/analyzer.py` for Multiple Linear Regression and Pearson Correlation (FR-003)
- [ ] T022 [US2] Implement data aggregation logic to join populated `VideoClip` raw data, `StatisticalFeature` vectors (from T020), and `DivergenceMetric` (from T014) into a single analysis DataFrame. **Dependencies**: Must explicitly depend on completion of T015 (timeout exclusion) and T017c (convergence exclusion) and T020. Exclude clips marked "timeout" or "failed ground truth".
- [ ] T023 [US2] Add logic to handle small sample sizes (<10 clips) by warning and skipping regression (Edge Cases)
- [ ] T024 [US2] Generate output JSON at `data/processed/correlation_results.json` with schema: `feature`, `pearson_r`, `p_value`, `ci_lower`, `ci_upper`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Instability Threshold Validation & Sensitivity Sweep (Priority: P3)

**Goal**: Determine an optimal divergence threshold for "stable" vs "unstable" classification and validate via sensitivity analysis.

**Independent Test**: Running with varied thresholds shows how precision/recall shift, confirming boundary stability.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for F1-score maximization and sensitivity sweep logic in `tests/unit/test_threshold_model.py`
- [ ] T026 [P] [US3] Integration test for end-to-end threshold validation in `tests/integration/test_threshold_flow.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/utils/metrics.py` with function `compute_cohen_kappa(rater_a_labels: list, rater_b_labels: list) -> float`. **Logic**: This function validates the actual human-labeled pilot dataset by computing kappa on the provided labels. If kappa < 0.8, it MUST raise a `ConfigurationError`. Do NOT assert on test data; this function is strictly for validating the real human annotation data.
- [ ] T027a [P] [US3] Generate a synthetic test dataset for unit testing T027 logic. This dataset is for unit tests only and does not represent the human-labeled N=60 pilot data.
- [ ] T030a [P] [US3] Implement CSV import mechanism for human labels: Read `data/annotations/ratings.csv` (schema: `clip_id, rater_id, label`). Validate that at least two distinct `rater_id`s exist per clip. **Input**: Accepts output from T042 (CLI Annotation Interface) or manually created CSV.
- [ ] T030b [P] [US3] Implement validation logic to ensure exactly two distinct `rater_id`s per `clip_id` in the imported CSV (FR-007). Raise `ConfigurationError` if not met.
- [ ] T030c [US3] Enforce inter-annotator agreement: After T030a/b, compute Cohen's kappa using T027. If kappa < 0.8, raise a `ConfigurationError` or flag the dataset as "Invalid" in the final report, halting further threshold analysis (FR-007).
- [ ] T028b [P] [US3] Implement data splitting logic: Split the N=60 pilot dataset (after T030c validation) into training ([deferred]) and validation ([deferred]) sets using stratified sampling based on the divergence metric distribution. Output: `data/processed/train_set.csv`, `data/processed/val_set.csv`. **Requirement**: Explicitly define split ratio (majority/minority) to prevent data leakage and ensure a held-out set for FR-004.
- [ ] T028 [US3] Implement `code/pipeline/analyzer.py` function to determine optimal threshold maximizing F1-score on the held-out validation set (from T028b) (FR-004). Input: `data/processed/val_set.csv` (generated by T028b) containing the human labels and divergence values.
- [ ] T029 [US3] Implement sensitivity sweep logic to test thresholds ±0.05 and report variation in false-positive/negative rates (FR-004).
- [ ] T031 [US3] Generate final report including optimal threshold, precision, recall, and sensitivity analysis plots/tables.

**Checkpoint**: All user stories should now be independently functional

---

## Phase O: Data Acquisition & Annotation (Critical Path for Real Data)

**Purpose**: Ensure real, reachable datasets are fetched and human labels are collected before analysis tasks run.

- [ ] T038 [P] [US1/US2] Implement `code/pipeline/data_fetcher.py` to download a subset of Kinetics-400 or UCF101 clips. 
    - **Requirement**: Must use a real, reachable URL (e.g., via `datasets.load_dataset` or direct HTTP GET to `ucimlrepo` or `kinetics` mirrors). 
    - **Constraint**: Do NOT use placeholder paths or generate synthetic video frames. 
    - **Output**: Save raw clips to `data/raw/` and log checksums in `data/raw/.manifest.json`.
- [ ] T039 [P] [US1/US2] Implement validation logic in `code/pipeline/data_fetcher.py` to verify that downloaded clips are non-empty, decodable by `decord`, and contain at least 16 frames. Skip invalid clips and log to `data/raw/invalid_clips.log`.
- [ ] T040 [P] [US3] Create a manual annotation guide and template in `docs/annotation_guide.md` to instruct human raters on how to label clips as "stable" or "unstable" based on visible artifacts.
- [ ] T041 [P] [US3] Create a sample `data/annotations/ratings_template.csv` with the correct schema (`clip_id, rater_id, label`) and example rows to guide manual data entry. **Do not** generate random labels; this is a template for human input.
- [ ] T042 [US3] Implement CLI Annotation Interface: Create a command-line tool (`code/cli/annotate.py`) that facilitates the collection of labels from two independent raters. 
    - **Logic**: The tool must prompt Rater 1 to label all clips in the dataset sequentially, saving intermediate results. Then, it must prompt Rater 2 to label the same clips. 
    - **Constraint**: The tool must enforce that exactly two distinct raters label every clip before generating the final `data/annotations/ratings.csv`. 
    - **Output**: Generates `data/annotations/ratings.csv` in the format required by T030a. This task satisfies the FR-007 requirement for a "manual annotation interface" to collect labels.
- [ ] T042a [US3] Implement CSV Import Mechanism: Create a utility (`code/cli/import_annotations.py`) to load pre-existing label files (e.g., from manual entry in a spreadsheet). 
    - **Logic**: Parse a CSV file, validate the schema (T030a), check for exactly two raters per clip (T030b), and compute kappa (T027). 
    - **Requirement**: This provides the "import mechanism" alternative to the CLI interface in T042, fully satisfying FR-007.

**Dependencies & Execution Order (Updated)**

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup. **Must complete before** Phase 3, 4, 5 to ensure real data exists.
- **User Stories (Phase 3+)**: Depend on Foundational AND Data Acquisition (for real input data).

### User Story Dependencies (Updated)

- **User Story 1 (P1)**: Depends on Data Acquisition (T038, T039) to have real clips to process.
- **User Story 2 (P2)**: Depends on US1 output and Data Acquisition.
- **User Story 3 (P3)**: Depends on US2 output and manual annotation (T040, T041, **T042**, **T042a**) completed by humans.

### Parallel Opportunities

- Data fetching (T038) can run in parallel with Setup/Foundational tasks.
- Manual annotation (T040, T041) is a human task and can proceed in parallel with code implementation of US1 and US2.
- **T042** (CLI Interface) and **T042a** (Import Mechanism) must be implemented before T030a/b/c can be fully utilized for data collection, but T030a/b/c logic can be developed in parallel.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] Update `docs/quickstart.md` with CLI usage examples and installation steps
- [ ] T032b [P] Update `docs/research.md` with methodology details, sample size justification (N=60), and spec deviations (FR-008 override)
- [ ] T032c [P] Add API documentation for `code/pipeline/divergence.py` and `code/utils/metrics.py`
- [ ] T033a [P] Refactor `code/pipeline/divergence.py` to extract the Euler rollout loop into a separate method for improved testability.
- [ ] T033b [P] Refactor `code/pipeline/analyzer.py` to remove duplicate correlation logic and consolidate into a single utility function.
- [ ] T034a [P] Profile `code/pipeline/divergence.py` to identify the primary bottleneck in the -step Euler rollout (e.g., memory vs CPU).
- [ ] T034b [P] Optimize the identified bottleneck in T034a (e.g., batch processing, memory optimization) to ensure 60 clips < 6h total.
- [ ] T035 [P] Additional unit tests in `tests/unit/`
- [ ] T036 Security hardening (input validation for video paths)
- [ ] T037 Run quickstart.md validation and verify execution on free-tier runner constraints

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (divergence values) for correlation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (features + divergence) for thresholding AND T030c (Human Ground Truth) AND T042/T042a (Annotation Interface)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Loaders before Services/Calculators
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
Task: "Unit test for L2 calculation logic in tests/unit/test_divergence.py"
Task: "Integration test for single clip processing flow in tests/integration/test_divergence_flow.py"

# Launch all models for User Story 1 together:
Task: "Implement video loader in code/pipeline/loader.py"
Task: "Implement ONNX wrapper in code/models/anyflow_onnx.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Stories independently (compute divergence on clips)
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
   - Developer A: User Story 1 (Divergence)
   - Developer B: User Story 2 (Feature Extraction)
   - Developer C: User Story 3 (Thresholding + Annotation Interface)
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
- **Critical Constraint**: Ensure all tasks run on CPU-only (no CUDA/8-bit quantization).
- **Critical Constraint**: Clips timing out >15 mins are excluded, not replaced with 20-step surrogates (Plan Deviation).
- **Critical Constraint**: All statistical analyses must consume real data fetched from the URLs defined in T038; no synthetic data generation.
- **Critical Constraint**: Human labels must be collected via T042 (CLI Interface) or T042a (Import Mechanism) or manually entered, ensuring two distinct raters per clip.