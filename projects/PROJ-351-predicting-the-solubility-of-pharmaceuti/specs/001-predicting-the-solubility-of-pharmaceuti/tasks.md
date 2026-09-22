# Tasks: Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

**Input**: Design documents from `/specs/001-predict-solubility-gnn/`
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
- **Mobile**: `api/src/`, `android/src/`
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

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `models/`, `results/`, `tests/`)
- [X] T002 Initialize Python project with `requirements.txt` (pinning `rdkit`, `torch` CPU, `torch-geometric` CPU, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `scipy`)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create base data models/entities (`Molecule`, `DatasetSplit`) in `code/models.py` or `code/__init__.py` to support downstream pipeline tasks.
- [X] T004 [P] Implement `code/data/download_esol.py` to fetch ESOL dataset from MoleculeNet repository URL or verified canonical CSV source, validate `logS` column, and save raw CSV to `data/raw/`
- [X] T004b [P] Implement checksumming in `code/data/download_esol.py` or `code/utils/checksum.py` to compute SHA-256 of the raw CSV file and record it in `state/` or `data/logs/checksums.log` before processing. **Depends on:** T004.
- [X] T005 [P] Implement `code/data/preprocess.py` to load raw CSV, parse SMILES with RDKit, exclude invalid SMILES/NaN `logS` *before* split, extract atom/bond features, and save cleaned graphs to `data/processed/`. **Must include:** (1) Error handling for RDKit failures (log count to `data/logs/exclusions.log` and raise warning), (2) Logging of exclusion counts to satisfy FR-001 and Principle VI. **(Note: This task covers the logging/exclusion scope previously assigned to T017).**
- [X] T006 Implement `code/data/split.py` to compute Bemis-Murcko scaffolds using RDKit and perform a scaffold-based split (superseding FR-005 quantile binning) to ensure structural independence. Split data into multiple folds based on unique scaffolds. Save indices to `data/processed/`. **Depends on:** T005.
- [X] T008 [P] Configure logging infrastructure: Create `code/config/logging_config.py` to set up JSON-formatted logging with timestamps, writing to `data/logs/` to satisfy Constitution Principle III. **(Note: This task covers the logging integration scope previously assigned to T017).**
- [X] T009 [P] Setup environment configuration management: Implement random seed pinning for numpy, torch, and random modules in `code/` to ensure reproducibility (Constitution Principle I). Do not prescribe specific file formats; ensure seeds are applied globally before data loading.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline and Baseline Establishment (Priority: P1) 🎯 MVP

**Goal**: Download ESOL, clean invalid SMILES, preprocess to graphs, and train Random Forest baseline to establish a performance floor.

**Independent Test**: The pipeline can be fully tested by running the data download, cleaning, preprocessing, and Random Forest training script, verifying that a model is saved and metrics are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for SMILES validation logic in `tests/unit/test_preprocess.py`
- [X] T011 [P] [US1] Unit test for Scaffold Split logic in `tests/unit/test_split.py`
- [X] T012 [P] [US1] Integration test for full RF baseline pipeline in `tests/integration/test_baseline_pipeline.py`

### Implementation for User Story 1

- [X] T012a [US1] Implement `code/data/featurize.py` to convert cleaned molecular graphs (from T005) into Morgan fingerprints (radius=2, 2048 bits) and save to `data/processed/fingerprints.npz`. **Depends on:** T005, T012b.
- [X] T012b [US1] Implement `code/data/augmentation.py` to generate multiple valid SMILES strings per molecule for data augmentation (SMILES enumeration). This must occur during preprocessing/split phase to prevent overfitting. **Depends on:** T005.
- [X] T013 [US1] Define Random Forest baseline architecture in `code/models/baseline_rf.py` using Morgan fingerprints (radius=2, 2048 bits). **Depends on:** T012a.
- [X] T016 [US1] Implement a K-fold Cross-Validation loop in `code/training/train_baseline_cv.py` to train RF on K folds, aggregate predictions across all folds into a single set, and output per-fold metrics. **Depends on:** T013, T006. This task replaces the single-split training task to ensure robust performance estimation.
- [X] T015 [US1] Log R-squared and RMSE metrics to `results/baseline_metrics.json` after the 5-fold CV completes. **Constraint:** Baseline training is a component of the full pipeline which must complete within 6 hours (SC-003).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Model Training and Evaluation (Priority: P2)

**Goal**: Implement and train a Message Passing Neural Network (MPNN) configured strictly for CPU execution and evaluate against the Random Forest baseline.

**Independent Test**: The GNN training script can be run independently (assuming data exists), and the resulting model must produce a test set RMSE that is recorded and compared to the baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for MPNN architecture (CPU-only verification) in `tests/unit/test_gnn_arch.py`
- [X] T019 [P] [US2] Integration test for GNN training loop with early stopping in `tests/integration/test_gnn_training.py`

### Implementation for User Story 2

- [X] T020 [US2] Define Message Passing Neural Network (MPNN) architecture in `code/models/gnn_mpnn.py` using PyTorch Geometric, ensuring NO CUDA/GPU calls. Architecture parameters (layers, hidden dim) MUST be configurable via `code/config.py`.
- [X] T021 [US2] Implement a k-fold Cross-Validation loop in `code/training/train_gnn_cv.py` to train MPNN on k folds with early stopping, aggregate predictions across all folds into a single set, and output per-fold metrics. **Depends on:** T020, T006. This task replaces the single-split training task.
- [X] T027 [US2] Implement `code/utils/timeout_handler.py` to enforce a configurable total pipeline limit. This script must wrap the training execution and fail the pipeline if the limit is exceeded. **Depends on:** T016, T021.
- [X] T023 [US2] Implement evaluation script in `code/evaluation/metrics.py` to calculate RMSE and R-squared for GNN on aggregated test set.
- [X] T024 [US2] Save GNN predictions to `results/gnn_predictions.csv` and metrics to `results/gnn_metrics.json`.
- [X] T025 [US2] Implement comparison logic to generate `results/model_comparison.json` containing RMSE delta between Baseline and GNN without arbitrary pass/fail flags. **Depends on:** T016, T021.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Interpretability (Priority: P3)

**Goal**: Perform paired t-test on prediction errors, calculate statistical power, and generate feature importance visualizations.

**Independent Test**: The analysis script takes the prediction files from US-1 and US-2, runs the t-test and power analysis, and generates a plot or table of feature importance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for paired t-test and power analysis logic in `tests/unit/test_stats.py`
- [X] T027 [P] [US3] Unit test for visualization generation (file size > 1KB) in `tests/unit/test_viz.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement `code/evaluation/aggregate_predictions.py` to combine predictions from all 5-fold cross-validation folds (from T016 and T021) into a single set for statistical testing. **Requires:** T016 (RF CV), T021 (GNN CV).
- [X] T028 [US3] Implement `code/evaluation/statistical_test.py` to perform Shapiro-Wilk normality check on absolute errors. If normal, perform paired t-test; if not, perform Wilcoxon Signed-Rank test. Calculate post-hoc power. **Requires:** T033 (Aggregated predictions).
- [X] T029 [US3] Implement `code/evaluation/interpretability.py` to generate attention heatmaps or node importance rankings for sample molecules using GNNExplainer.
- [X] T030 [US3] Ensure visualizations are saved as PNG files: Generate `results/feature_importance_*.png` (minimum 5 files, >1KB each) for sample molecules. Verify file size > 1KB.
- [X] T032 [US3] Implement `code/evaluation/write_metrics.py` to write aggregated RMSE, R², p-value, and power to `results/metrics.json` (SSoT). **Requires:** T028, T024.
- [X] T031 [US3] Implement `code/evaluation/report_generator.py` to compile RMSE, R², p-value, power, and delta into a final summary table reading **only** from `results/metrics.json`. **Requires:** T032.
- [X] T034 [US3] Add logic to detect and report "ceiling effect" if Baseline R² > 0.9 (as per spec Edge Cases): Append `ceiling_effect` flag to `results/final_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `README.md`
- [ ] T036 Performance optimization for GNN training loop (CPU efficiency)
- [ ] T037 [P] Additional unit tests for edge cases (malformed SMILES, non-convergent GNN) in `tests/unit/`
- [ ] T038 Run quickstart.md validation

---

## Phase O: Research & Validation (Post-Implementation Review)

**Purpose**: Address specific research-stage review concerns regarding data integrity, reproducibility, and statistical robustness.

- [ ] T039 [P] **Reproducibility Audit**: Create a `scripts/verify_reproducibility.py` that re-runs the full pipeline with a fixed seed and compares the output checksums of `results/` artifacts against the previous run to ensure bit-for-bit reproducibility. **Depends on:** Successful completion of T038 and all Phase 5 tasks. **Reason**: Addresses Constitution Principle I (Reproducibility) and ensures the "single source of truth" is maintained.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Research & Validation (Phase O)**: Depends on completion of all User Stories (Phase 3-5)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Relies on data pipeline from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on results from US1 and US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004, T004b, T008, T009) can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase O tasks (T039) can run in parallel as they are distinct validation/audit scripts.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for SMILES validation logic in tests/unit/test_preprocess.py"
Task: "Unit test for Scaffold Split logic in tests/unit/test_split.py"

# Launch all models for User Story 1 together:
Task: "Define Random Forest baseline architecture in code/models/baseline_rf.py"
Task: "Log R-squared and RMSE to results/baseline_metrics.json"
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
 - Developer A: User Story 1 (Data + RF)
 - Developer B: User Story 2 (GNN)
 - Developer C: User Story 3 (Stats + Viz)
3. Stories complete and integrate independently
4. Developer (or rotating team): Execute Phase O (Research & Validation) tasks to ensure data integrity and reproducibility.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All GNN tasks must run on CPU-only; no CUDA/GPU calls allowed.
- **Constraint**: All tasks must complete within 6 hours on 2 vCPU.
- **Constraint**: No synthetic data; use real ESOL dataset from MoleculeNet repository or verified canonical source.
- **Critical Rule**: If a real data fetch fails, the script MUST raise an exception. No synthetic fallbacks allowed.
- **Critical Update**: Scaffold Split (T006) is now a mandatory prerequisite in Phase 2, replacing the quantile binning logic.
- **Critical Update**: All training tasks (T016, T021) now implement 5-fold Cross-Validation as per plan, replacing single-split training.