# Tasks: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments

**Input**: Design documents from `/specs/001-visual-distraction-cognitive-control/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001 [P] Initialize project structure: Create `code/`, `data/`, `results/`, `tests/`, and `specs/001-visual-distraction-cognitive-control/` directories at repository root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create `code/requirements.txt` with pinned dependencies (pandas, numpy, scikit-learn, scipy, opencv-python-headless, ultralytics, matplotlib, seaborn, Pillow, pytest, statsmodels)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools. **Verification**: Run linting on all code files; ensure no errors.
- [ ] T004 [P] Setup data directory structure (`data/raw`, `data/processed`) and results directory (`results/statistics`, `results/plots`, `results/sensitivity`). **Note**: Aligned strictly with plan.md 'Project Structure'; methodology artifacts will be placed in `results/statistics` or `results/report.md`.
- [X] T005 [P] Implement logging infrastructure in `code/utils.py` (handlers, formatters)
- [X] T006 [P] Implement checksumming logic (sha256) in `code/utils.py`
- [X] T007 [P] Implement global random seed management (pinned seeds) in `code/utils.py`
- [X] T008 [P] Implement error handler in `code/utils.py` to log specific errors: 'unmatched_participant_ids' and 'image_processing_failures' with structured JSON messages as per Edge Cases in spec.md
- [X] T009 [P] Implement contract test in `tests/contract/test_error_logging.py` to verify that `code/utils.py` logs the specific keys 'unmatched_participant_ids' and 'image_processing_failures` when triggered
- [ ] T010 [P] Create dataset schema definition in `specs/001-visual-distraction-cognitive-control/contracts/dataset.schema.yaml`. **Verification**: Validate against sample data.
- [ ] T011 [P] Create analysis output schema definition in `specs/001-visual-distraction-cognitive-control/contracts/analysis_output.schema.yaml`. **Verification**: Validate against sample output.
- [ ] T012 [P] Implement contract tests in `tests/contract/` to validate JSON/CSV outputs against schemas. **Verification**: Run tests; ensure they pass.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Acquire or generate synthetic participant-level data linking cognitive metrics and workspace images, ensuring N ≥ 100 and ≤5% missing values.

**Independent Test**: Verify that `data/processed/merged_data.csv` exists with ≥100 rows, non-null `reaction_time`, `accuracy`, and `visual_complexity` columns.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_dataset_schema.py`
- [ ] T014 [P] [US1] Unit test for synthetic data generator ensuring correlation structure (negative correlation) in `tests/unit/test_synthetic_data.py`. **Verification**: Run test; ensure it validates the correlation structure.

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/01_data_acquisition.py` to: (1) Attempt download of Stroop/Flanker data from HuggingFace (specific IDs: `StroopTaskDataset`, `FlankerDataset`) or OpenML; (2) If a linked dataset with participant-level image paths is found and successfully downloaded, use it; (3) If download fails or NO linked dataset exists (verified by check), set a `synthetic_fallback` flag. **CRITICAL: This task MUST NOT generate synthetic data. It only attempts download and sets the flag.**
- [X] T015b [US1] Implement `code/01_data_acquisition.py` (fallback block) to: (1) Execute ONLY if `synthetic_fallback` flag is set; (2) Generate synthetic participant records (N ≥ 100) simulating the negative correlation structure described in literature using a configurable `target_correlation` parameter (default a negative value) and a `literature_source` parameter; (3) Simultaneously generate corresponding synthetic workspace images (using Pillow) with linked metadata (lighting, room type, demographic) in a single execution step. **CRITICAL: Ensure participant IDs in the CSV match the filenames of the generated images exactly. The correlation structure must be derived from the `target_correlation` parameter, not hardcoded. The generation of participants and images must be atomic.**
- [X] T018 [US1] Implement data validation step in `code/01_data_acquisition.py` to: (1) Raise `ValueError` if N < 100; (2) Log warning if missing values > 5%; (3) Log specific error message format: `ERROR: Data validation failed. Missing: {count}%, N: {n}`.
- [X] T019 [US1] Implement power analysis calculation in `code/01_data_acquisition.py` (or `code/utils.py` called by it) to: (1) Use a configurable power analysis method (e.g., Cohen's guidelines, statsmodels.stats.power.tt_solve_power) with configurable `target_effect_size` (default not hardcoded, specified as a parameter); (2) Calculate power for the specified effect size; (3) Generate report documenting method and assumptions to satisfy SC-004. **Output**: Save report to `results/statistics/power_analysis_report.md` with fields: `effect_size`, `power`, `alpha`, `sample_size`, `method`. **Note**: Empirical values (effect size) are deferred; the method must be specified.
- [X] T020 [US1] Save processed merged dataset to `data/processed/merged_data.csv` and raw artifacts to `data/raw/`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Visual Complexity Metric Extraction (Priority: P1)
**⚠️ DEPENDENCY**: This phase (US2) CANNOT start until Phase 3 (US1) is complete (T020 output required).

**Goal**: Compute edge density, color entropy, and object count for all workspace images using CPU-tractable methods.

**Independent Test**: Verify that `results/statistics/visual_metrics.json` contains non-zero standard deviation for all three metrics across the sample.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for edge density calculation (normalized [0,1]) in `tests/unit/test_edge_density.py`
- [ ] T022 [P] [US2] Unit test for color entropy calculation in `tests/unit/test_color_entropy.py`
- [ ] T023 [P] [US2] Unit test for object count handling (NaN assignment on failure) in `tests/unit/test_object_count.py`

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement edge density calculation in `code/02_visual_metrics.py` using OpenCV Canny/Sobel edge detection, outputting normalized values.
- [X] T025 [P] [US2] Implement color entropy calculation in `code/02_visual_metrics.py` using histogram-based color distribution analysis.
- [X] T026 [US2] Implement object count calculation in `code/02_visual_metrics.py` using `ultralytics` YOLOv5n/tiny (CPU mode). **CRITICAL: If the model fails, times out, or returns no objects for an image, assign NaN to the object count for that image. DO NOT impute a proxy value, do NOT use edge density as a fallback. The analysis script must later exclude records with NaN object count from object-count-based analyses.**
- [X] T027 [US2] Create `code/02_visual_metrics.py` main execution block to: (1) Iterate over all images in `data/raw/`; (2) Handle missing images by logging error and skipping; (3) Compute metrics; (4) Save to `data/processed/visual_metrics_intermediate.csv`. **Depends on T020 completion.**
- [X] T028 [US2] Implement merge logic in `code/02_visual_metrics.py` to: (1) Join `visual_metrics_intermediate.csv` with `data/processed/merged_data.csv` (from US1) using `inner join on participant_id`; (2) Log count of unmatched records; (3) Save to `data/processed/final_analysis_data.csv`. **Depends on T027 completion.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (US2 fully functional after T027/T028 completion)

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P2)

**Goal**: Perform Pearson correlation, linear regression, and generate visualizations with strict associational framing.

**Independent Test**: Verify `results/statistics/statistics.json` contains r-values, p-values, and adjusted p-values (Holm-Bonferroni) for all metric pairs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for statistics output schema in `tests/contract/test_analysis_schema.py`
- [X] T030 [P] [US3] Unit test for Holm-Bonferroni correction logic in `tests/unit/test_multiplicity_correction.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement Pearson correlation and linear regression in `code/03_analysis.py` for each predictor-outcome pair (A series of tests will be conducted.).
- [X] T032 [US3] Implement Variance Inflation Factor (VIF) calculation in the analysis script to diagnose collinearity among the three visual complexity metrics. **Output**: Save VIF scores to `results/statistics/vif_report.json`.
- [X] T033 [US3] Implement PCA generation in `code/03_analysis.py` to: (1) Fit PCA on visual complexity metrics; (2) Extract `pca_component_1`; (3) Save results to `data/processed/pca_results.json`. **Trigger**: Execute if VIF ≥ 5 for any predictor.
- [X] T034 [US3] Implement conditional regression logic in `code/03_analysis.py` to: (1) Read VIF status; (2) **CRITICAL**: If VIF ≥ 5, re-run Pearson correlation (FR-006) and bootstrap resampling (FR-009) using `pca_component_1` as the predictor; (3) Overwrite the primary results in `results/statistics/statistics.json` with these new PCA-based statistics; (4) Else use raw metrics. **Depends on T032, T033.**
- [X] T034a [US3] **Critical Addition**: If VIF ≥ 5, explicitly re-run Pearson correlation (FR-006) and bootstrap resampling (FR-009) using `pca_component_1` as the predictor, and update `results/statistics/statistics.json` to reflect these as the primary results. **This ensures the 'primary predictor' is used across all primary statistics.**
- [X] T035 [US3] Implement Holm-Bonferroni family-wise error correction in `code/03_analysis.py` using `scipy.stats.multitest.multipletests(method=holm)`.
- [X] T036 [US3] Generate `results/statistics/multiplicity_table.csv` with columns: `test_name`, `raw_p`, `adjusted_p`, `metric_pair`. **CRITICAL**: Ensure this table is embedded as a Markdown table in the final `results/report.md` under a "Threshold Justification" section and explicitly cited as the evidence for the p<0.05 threshold justification to satisfy SC-005. **Note**: `results/report.md` is the final output file defined in T045.
- [X] T037 [US3] Implement logic in `code/03_analysis.py` to: (1) Frame all findings as associational (no causal claims) in output documentation; (2) Generate a dedicated text justification for the p<0.05 significance threshold as a community-standard convention, citing 'Wilkinson, L., & Task Force on Statistical Inference. (1999)' or equivalent standard. **Output**: Save justification to `results/statistics/alpha_threshold_justification.md`. **Template**: The justification must include: (a) Introduction to the p-value concept, (b) Explanation of the 0.05 threshold as a community standard, (c) Citation of the standard source, (d) Conclusion. **Minimum length**: 150 words. Include citations for OpenCV edge detection and color entropy formulas directly in the final `results/statistics/statistics.json` and `results/report.md`.
- [X] T038 [US3] Implement scatter plot generation in `code/04_visualization.py` with trend lines for significant correlations (p<0.05) and save to `results/plots/`. **Depends on T031-T037 completion.**
- [X] T039 [US3] Save final statistics to `results/statistics/statistics.json` ensuring all required fields (r, p, beta, CI, adjusted_p) are present. <!-- ATOMIZE: requested -->

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Sensitivity Analysis and Robustness Checks (Priority: P3)

**Goal**: Conduct bootstrap resampling and alternative binning strategies to validate robustness.

**Independent Test**: Verify `results/sensitivity/bootstrap_results.json` shows directional consistency and `results/sensitivity/binning_results.csv` shows magnitude stability (<0.1 change).

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [X] T040 [P] [US4] Unit test for bootstrap resampling logic (≥1000 iterations) in `tests/unit/test_bootstrap.py`

### Implementation for User Story 4

- [X] T041 [US4] Implement bootstrap resampling (≥1000 iterations) in `code/03_analysis.py` using `scipy.stats.bootstrap` to compute 95% confidence intervals for correlation coefficients. **Output**: Save to `results/sensitivity/bootstrap_results.json`.
- [X] T042 [US4] Implement alternative binning strategies (quartiles, deciles) in `code/03_analysis.py` to re-calculate correlations.
- [X] T043 [US4] Generate `results/sensitivity/binning_results.csv` with columns: `binning_strategy`, `predictor`, `outcome`, `pearson_r`, `p_value` (satisfies FR-010).
- [X] T044 [US4] Save bootstrap confidence intervals to `results/sensitivity/bootstrap_results.json`.
- [X] T045 [US4] Add final report generation step that summarizes sensitivity analysis findings, confirms robustness, and **includes the citations, associational framing, and alpha threshold justification** in the final `results/report.md` document. **Dependencies**: T039 (US3), T044 (US4), T037 (Alpha justification). **Note**: `results/report.md` is the canonical final report file, defined here.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Documentation updates: Ensure `quickstart.md` explains the synthetic data fallback and associational framing. **Requirement**: Add a "Data Source Selection" section explaining how to switch between real and synthetic data, and an "Interpretation of Results" section explaining the associational framing. **Specific Content**: 
  - **Data Source Selection**: 
    - Header: `## Data Source Selection`
    - Content: Explain the logic for choosing between real and synthetic data. Include a subsection `### Real Dataset Path` detailing the verification steps and fallback mechanism if a real dataset is found. Include a subsection `### Synthetic Data Path` detailing the generation process.
  - **Interpretation of Results**: 
    - Header: `## Interpretation of Results`
    - Content: Explain the associational nature of the findings, emphasizing that no causal claims are made. Include a subsection `### Real Dataset Interpretation` and `### Synthetic Data Interpretation` if applicable.
- [ ] T047 Code cleanup and refactoring to ensure PEP8 compliance. **Verification**: Run PEP8 linter; ensure no errors.
- [ ] T048 Performance optimization: Verify total runtime ≤ 6 hours on CPU cores (profile `01_data_acquisition.py` and `02_visual_metrics.py`).
- [ ] T049 [P] Additional unit tests for edge cases (image failure, zero variance) in `tests/unit/`.
- [ ] T050 [P] Run `quickstart.md` validation to ensure end-to-end pipeline execution.

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
- **User Story 2 (P1)**: **MUST wait for User Story 1** to complete (requires T020 output). Cannot start in parallel with US1.
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
- Once Foundational phase completes:
 - User Story 1 can start immediately.
 - **User Story 2 MUST wait for User Story 1 to complete.**
 - User Story 3 and 4 depend on previous stories.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members ONLY if dependency constraints are respected (e.g., US1 and US2 cannot be parallel).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for merged dataset schema in tests/contract/test_dataset_schema.py"
Task: "Unit test for synthetic data generator in tests/unit/test_synthetic_data.py"

# Launch all models for User Story 1 together:
Task: "Implement 01_data_acquisition.py download/fallback logic (including internal synthetic generation)"
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
 - Developer B: User Story 2 (waits for US1 data)
 - Developer C: User Story 3 (waits for US1 & US2)
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
- **Critical Constraint**: Synthetic data must use real distributions exhibiting a negative correlation, and real image generation logic (Pillow), not hardcoded placeholders. The generation of participants and images must be atomic within T015b.
- **Critical Constraint**: VIF/PCA logic MUST occur in the Analysis phase (T032-T034a), not Metric Extraction, to satisfy FR-012.
- **Critical Constraint**: Summary table of p-values (T036) and binning results (T043) must be generated as explicit CSV artifacts with specified columns (including `binning_strategy`) and merged into the final statistics output.
- **Critical Constraint**: Data acquisition (T015) MUST transition to synthetic generation (T015b) ONLY if no linked public dataset exists; it must NOT raise an exception.
- **Critical Constraint**: Object counting (T026) must use the real model but assign NaN on failure, NOT impute a proxy value.
- **Critical Constraint**: Power analysis (T019) must be implemented and reported to satisfy SC-004, with empirical values deferred.
- **Critical Constraint**: Alpha threshold justification (T037) must be explicitly generated in the report with a specific template and minimum word count.
- **Critical Constraint**: Parallel opportunities section updated to reflect US2 dependency on US1.
- **Critical Constraint**: `results/report.md` is the canonical final report file, defined in T045.
- **Constitution Check Note**: Tasks T003, T010, T011, T014, T021-T023, T046, T047 are now defined and actionable. The "Constitution Check PASS" in plan.md is contingent on these tasks being completed and verified.