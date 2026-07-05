# Tasks: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments

**Input**: Design documents from `/specs/001-visual-distraction-cognitive-control/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `results/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scikit-learn, scipy, opencv-python-headless, ultralytics, matplotlib, seaborn, Pillow, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw`, `data/processed`) and results directory (`results/statistics`, `results/plots`, `results/sensitivity`, `results/methodology`)
- [ ] T005 [P] Implement logging infrastructure in `code/utils.py` (handlers, formatters)
- [ ] T006 [P] Implement checksumming logic (sha256) in `code/utils.py`
- [ ] T007 [P] Implement global random seed management (pinned seeds) in `code/utils.py`
- [ ] T008 [P] Implement error handler in `code/utils.py` to log specific errors: 'unmatched_participant_ids' and 'image_processing_failures' with structured JSON messages as per Edge Cases in spec.md
- [ ] T009 [P] Implement contract test in `tests/contract/test_error_logging.py` to verify that `code/utils.py` logs the specific keys 'unmatched_participant_ids' and 'image_processing_failures` when triggered
- [ ] T010 [P] Create dataset schema definition in `specs/001-visual-distraction-cognitive-control/contracts/dataset.schema.yaml`
- [ ] T011 [P] Create analysis output schema definition in `specs/001-visual-distraction-cognitive-control/contracts/analysis_output.schema.yaml`
- [ ] T012 [P] Implement contract tests in `tests/contract/` to validate JSON/CSV outputs against schemas

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Acquire or generate synthetic participant-level data linking cognitive metrics and workspace images, ensuring N ≥ 100 and ≤5% missing values.

**Independent Test**: Verify that `data/processed/merged_data.csv` exists with ≥100 rows, non-null `reaction_time`, `accuracy`, and `visual_complexity` columns.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_dataset_schema.py`
- [ ] T014 [P] [US1] Unit test for synthetic data generator ensuring correlation structure (negative correlation) in `tests/unit/test_synthetic_data.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/01_data_acquisition.py` to attempt download of Stroop/Flanker data from HuggingFace/OpenML; fallback to synthetic generation if no linked dataset exists
- [ ] T016 [US1] Implement synthetic image generation logic in `code/01_data_acquisition.py` using `Pillow` compositing to create diverse workspace images (lighting, room type) for each participant ID
- [ ] T017 [US1] Implement participant-level data merging logic in `code/01_data_acquisition.py` to join cognitive metrics with image paths, excluding unmatched records and logging counts
- [ ] T018 [US1] Add data validation step in `code/01_data_acquisition.py` to ensure ≤5% missing values and raise error if N < 100
- [ ] T019 [US1] Generate `results/methodology/cv_methods.md` containing explicit citations for OpenCV edge detection (Canny/Sobel) and color entropy formulas (Shannon entropy) to satisfy SC-006
- [ ] T020 [US1] Save processed merged dataset to `data/processed/merged_data.csv` and raw artifacts to `data/raw/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Visual Complexity Metric Extraction (Priority: P1)

**Goal**: Compute edge density, color entropy, and object count for all workspace images using CPU-tractable methods.

**Independent Test**: Verify that `results/statistics/visual_metrics.json` contains non-zero standard deviation for all three metrics across the sample.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for edge density calculation (normalized [0,1]) in `tests/unit/test_edge_density.py`
- [ ] T022 [P] [US2] Unit test for color entropy calculation in `tests/unit/test_color_entropy.py`
- [ ] T023 [P] [US2] Unit test for object count handling (NaN assignment on failure) in `tests/unit/test_object_count.py`

### Implementation for User Story 2

- [ ] T024 [P] [US2] Implement edge density calculation in `code/visual_metrics.py` using OpenCV Canny/Sobel edge detection, outputting normalized [0,1] values
- [ ] T025 [P] [US2] Implement color entropy calculation in `code/02_visual_metrics.py` using histogram-based color distribution analysis
- [ ] T026 [US2] Implement object count calculation in `code/02_visual_metrics.py` using `ultralytics` YOLOv5n/tiny (CPU mode) with fallback to NaN on detection failure
- [ ] T027 [US2] Create `code/02_visual_metrics.py` main execution block to process all images in `data/raw/`, compute metrics, and save to `data/processed/visual_metrics_intermediate.csv` (intermediate file). **Depends on T020 completion.**
- [ ] T028 [US2] Implement merge logic in `code/02_visual_metrics.py` to join `visual_metrics_intermediate.csv` with `data/processed/merged_data.csv` (from US1) into `data/processed/final_analysis_data.csv`, ensuring US2 waits for US1 completion. **Depends on T020 completion.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P2)

**Goal**: Perform Pearson correlation, linear regression, and generate visualizations with strict associational framing.

**Independent Test**: Verify `results/statistics/statistics.json` contains r-values, p-values, and adjusted p-values (Holm-Bonferroni) for all metric pairs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for statistics output schema in `tests/contract/test_analysis_schema.py`
- [ ] T030 [P] [US3] Unit test for Holm-Bonferroni correction logic in `tests/unit/test_multiplicity_correction.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement Pearson correlation and linear regression in `code/analysis.py` for each predictor-outcome pair (6 tests total)
- [ ] T032 [US3] Implement Variance Inflation Factor (VIF) calculation in the analysis script to diagnose collinearity among the three visual complexity metrics
- [ ] T033 [US3] Implement PCA generation in `code/03_analysis.py` to create `pca_component_1` if VIF ≥ 5 for any predictor, storing results in `data/processed/pca_results.json`
- [ ] T034 [US3] Implement conditional regression logic in `code/03_analysis.py` to read VIF status and **switch** the regression predictor to `pca_component_1` if VIF ≥ 5, otherwise use raw metrics (satisfies FR-012)
- [ ] T035 [US3] Implement Holm-Bonferroni family-wise error correction in `code/03_analysis.py`
- [ ] T036 [US3] Generate `results/statistics/multiplicity_table.csv` with columns: `test_name`, `raw_p`, `adjusted_p`, `metric_pair` (satisfies SC-005)
- [ ] T037 [US3] Implement logic in `code/03_analysis.py` to frame all findings as associational (no causal claims) in output documentation
- [ ] T038 [US3] Implement scatter plot generation in `code/04_visualization.py` with trend lines for significant correlations (p<0.05) and save to `results/plots/`
- [ ] T039 [US3] Save final statistics to `results/statistics/statistics.json` ensuring all required fields (r, p, beta, CI, adjusted_p) are present

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Sensitivity Analysis and Robustness Checks (Priority: P3)

**Goal**: Conduct bootstrap resampling and alternative binning strategies to validate robustness.

**Independent Test**: Verify `results/sensitivity/bootstrap_results.json` shows directional consistency and `results/sensitivity/binning_results.csv` shows magnitude stability (<0.1 change).

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T040 [P] [US4] Unit test for bootstrap resampling logic (≥1000 iterations) in `tests/unit/test_bootstrap.py`

### Implementation for User Story 4

- [ ] T041 [US4] Implement bootstrap resampling (≥1000 iterations) in `code/03_analysis.py` to compute 95% confidence intervals for correlation coefficients
- [ ] T042 [US4] Implement alternative binning strategies (quartiles, deciles) in `code/03_analysis.py` to re-calculate correlations
- [ ] T043 [US4] Generate `results/sensitivity/binning_results.csv` with columns: `binning_strategy`, `predictor`, `outcome`, `pearson_r`, `p_value` (satisfies FR-010)
- [ ] T044 [US4] Save bootstrap confidence intervals to `results/sensitivity/bootstrap_results.json`
- [ ] T045 [US4] Add final report generation step that summarizes sensitivity analysis findings and confirms robustness

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Documentation updates: Ensure `quickstart.md` explains the synthetic data fallback and associational framing
- [ ] T047 Code cleanup and refactoring to ensure PEP8 compliance
- [ ] T048 Performance optimization: Verify total runtime ≤ 6 hours on 2 CPU cores (profile `01_data_acquisition.py` and `02_visual_metrics.py`)
- [ ] T049 [P] Additional unit tests for edge cases (image failure, zero variance) in `tests/unit/`
- [ ] T050 [P] Run `quickstart.md` validation to ensure end-to-end pipeline execution

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Requires US1 data output (T020)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Requires US1 & US2 data output (T028)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Requires US3 analysis results

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
Task: "Contract test for merged dataset schema in tests/contract/test_dataset_schema.py"
Task: "Unit test for synthetic data generator in tests/unit/test_synthetic_data.py"

# Launch all models for User Story 1 together:
Task: "Implement 01_data_acquisition.py download/fallback logic"
Task: "Implement 01_data_acquisition.py synthetic image generation"
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
- **Critical Constraint**: All tasks must run on CPU-only CI (cores, limited RAM). No GPU models, no 8-bit quantization, no large LLMs.
- **Critical Constraint**: Synthetic data must use real distributions exhibiting a negative correlation. and real image generation logic (Pillow), not hardcoded placeholders.
- **Critical Constraint**: VIF/PCA logic MUST occur in the Analysis phase (T032-T034), not Metric Extraction, to satisfy FR-012.
- **Critical Constraint**: Summary table of p-values (T036) and binning results (T043) must be generated as explicit CSV artifacts with specified columns.