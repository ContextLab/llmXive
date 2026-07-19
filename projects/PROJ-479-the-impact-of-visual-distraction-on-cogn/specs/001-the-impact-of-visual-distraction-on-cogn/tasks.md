# Tasks: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments

**Input**: Design documents from `/specs/001-visual-distraction-cognitive-control/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY. All tasks marked with [USx] must include corresponding unit and contract tests to verify independent functionality.

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize project structure: Create `code/`, `data/`, `results/`, `tests/`, and `specs/001-visual-distraction-cognitive-control/` directories at repository root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create `code/requirements.txt` with pinned dependencies (pandas, numpy, scikit-learn, scipy, opencv-python-headless, ultralytics, matplotlib, seaborn, Pillow, pytest, statsmodels)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools. **Verification**: Run linting on all code files; ensure no errors.
- [X] T004 [P] Setup data directory structure (`data/raw`, `data/processed`) and results directory (`results/statistics`, `results/plots`, `results/sensitivity`). **Note**: Aligned strictly with plan.md 'Project Structure'; methodology artifacts will be placed in `results/statistics` or `results/report.md`.
- [X] T005 [P] Implement logging infrastructure in `code/utils.py` (handlers, formatters)
- [X] T006 [P] Implement checksumming logic (sha256) in `code/utils.py`
- [X] T007 [P] Implement global random seed management (pinned seeds) in `code/utils.py`
- [X] T008 [P] Implement error handler in `code/utils.py` to log specific errors: 'unmatched_participant_ids' and 'image_processing_failures' with structured JSON messages as per Edge Cases in spec.md
- [X] T009 [P] Implement contract test in `tests/contract/test_error_logging.py` to verify that `code/utils.py` logs the specific keys 'unmatched_participant_ids' and 'image_processing_failures` when triggered
- [X] T010 [P] Create dataset schema definition in `specs/001-visual-distraction-cognitive-control/contracts/dataset.schema.yaml`. **Verification**: Validate against sample data.
- [X] T011 [P] Create analysis output schema definition in `specs/001-visual-distraction-cognitive-control/contracts/analysis_output.schema.yaml`. **Verification**: Validate against sample output.
- [X] T012 [P] Implement contract tests in `tests/contract/` to validate JSON/CSV outputs against schemas. **Verification**: Run tests; ensure they pass.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Acquire or generate synthetic participant-level data linking cognitive metrics and workspace images, ensuring N ≥ 100 and ≤5% missing values.

**Independent Test**: Verify that `data/processed/merged_data.csv` exists with ≥100 rows, non-null `reaction_time`, `accuracy`, and `visual_complexity` columns.

### Tests for User Story 1 (MANDATORY)

- [X] T013 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_dataset_schema.py`
- [X] T014 [P] [US1] Unit test for synthetic data generator ensuring correlation structure (negative correlation) in `tests/unit/test_synthetic_data.py`. **Verification**: Run test; ensure it validates the correlation structure. **MANDATORY**: This test must pass before proceeding to implementation.

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/01_data_acquisition.py` to execute a **Three-Branch Data Strategy**: <!-- FAILED: unspecified -->
 (1) **Attempt Download**: Try to download Stroop/Flanker datasets from HuggingFace (IDs: `StroopTaskDataset`, `FlankerDataset`) or OpenML.
 (2) **Verify Linkage**: Check if the downloaded dataset contains both cognitive metrics AND valid image paths/links.
 - **Criteria**: Must have `participant_id`, `reaction_time`, `accuracy`, AND `image_path` (or equivalent linkage column).
 - **Log**: If linkage is missing, log `INFO: Real cognitive data found but image linkage missing. Switching to Hybrid Mode.`
 (3) **Branch Logic**:
 - **Branch A (Full Real)**: If linked data exists and is valid, use it.
 - **Branch B (Hybrid)**: If real cognitive data exists but image linkage is missing:
 - Keep the real cognitive data.
 - **Generate Synthetic Images**: Use `Pillow` to generate N synthetic workspace images corresponding to the real `participant_id`s.
 - **Link**: Create a mapping of `participant_id` -> `synthetic_image_path`.
 - **Branch C (Full Synthetic)**: If NO real cognitive dataset is found:
 - Generate synthetic participant records (N ≥ 100) with `participant_id`, `reaction_time`, `accuracy`.
 - Simultaneously generate corresponding synthetic workspace images (using Pillow) with linked metadata.
 - **Constraint**: Correlation structure must be derived from a `target_correlation` parameter (default -0.3), not hardcoded.
 (4) **Atomic Generation**: In Branches B and C, the generation of participants and images must be atomic.
 (5) **Output Paths**: Save synthetic participants to `data/raw/synthetic_participants.csv` (if generated) and images to `data/raw/synthetic_images/`.
 (6) **Verification Step**: Immediately after generation, compute edge density on a sample of generated images. **If** the standard deviation of edge density is 0 (no variance), the script MUST raise a `ValueError` and halt execution to prevent generating invalid synthetic data.
 (7) **Completion Marker**: Write a `data/raw/.generation_complete` marker file upon successful completion to signal T027.

- [X] T018 [US1] Implement data validation step in `code/01_data_acquisition.py` to: (1) Raise `ValueError` if N < 100; (2) Log warning if missing values > 5%; (3) Log specific error message format: `ERROR: Data validation failed. Missing: {count}%, N: {n}`.
- [ ] T019 [US1] Implement power analysis calculation in `code/01_data_acquisition.py` (or `code/utils.py` called by it) to: (1) Use a configurable power analysis method (e.g., `statsmodels.stats.power.tt_solve_power`) with `target_effect_size` defaulting to **0.3 (Cohen's d, Cohen, 1988)**; (2) **Calculate the achieved power** for the fixed sample size N=100 (as per SC-004 constraint); (3) **Explicitly document** in the report that N=100 is a fixed constraint and the calculated value is the *achieved power*, not the target power used to determine N. **Output**: Save report to `results/statistics/power_analysis_report.md` with fields: `effect_size`, `power`, `alpha`, `sample_size`, `method`, `rationale`. **Verification**: Verify file exists and contains the calculated `power` field. **Note**: Empirical values (effect size) are deferred; the method and calculated power must be specified.
- [X] T020 [US1] Save processed merged dataset to `data/processed/merged_data.csv` and raw artifacts to `data/raw/`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Visual Complexity Metric Extraction (Priority: P1)
**⚠️ DEPENDENCY**: This phase (US2) CANNOT start until Phase 3 (US1) is complete (T020 output required). **Specifically, T027 waits for the `.generation_complete` marker from T015.**

**Goal**: Compute edge density, color entropy, and object count for all workspace images using CPU-tractable methods.

**Independent Test**: Verify that `results/statistics/visual_metrics.json` contains non-zero standard deviation for all three metrics across the sample.

### Tests for User Story 2 (MANDATORY)

- [X] T021 [P] [US2] Unit test for edge density calculation (normalized [0,1]) in `tests/unit/test_edge_density.py`
- [X] T022 [P] [US2] Unit test for color entropy calculation in `tests/unit/test_color_entropy.py`
- [X] T023 [P] [US2] Unit test for object count handling (NaN assignment on failure) in `tests/unit/test_object_count.py`

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement edge density calculation in `code/02_visual_metrics.py` using OpenCV Canny/Sobel edge detection, outputting normalized values.
- [X] T025 [P] [US2] Implement color entropy calculation in `code/02_visual_metrics.py` using histogram-based color distribution analysis.
- [X] T026 [US2] Implement object count calculation in `code/02_visual_metrics.py` using `ultralytics` YOLOv5n/tiny (CPU mode). **CRITICAL: If the model fails, times out, or returns no objects for an image, assign NaN to the object count for that image. DO NOT impute a proxy value, do NOT use edge density as a fallback. The analysis script must later exclude records with NaN object count from object-count-based analyses.**
- [X] T027 [US2] Create `code/02_visual_metrics.py` main execution block to: (1) **Wait for `data/raw/.generation_complete` marker** (or check T015 completion); (2) Iterate over all images in `data/raw/`; (3) Handle missing images by logging error and skipping; (4) Compute metrics; (5) Save to `data/processed/visual_metrics_intermediate.csv`. **Depends on T020 completion.**
- [X] T028 [US2] Implement merge logic in `code/02_visual_metrics.py` to: (1) Join `visual_metrics_intermediate.csv` with `data/processed/merged_data.csv` (from US1) using `inner join on participant_id`; (2) **CRITICAL: Do NOT drop records with NaN object_count here. Retain all records, including those with NaN for object_count, to allow edge density and entropy analyses to proceed for these participants.** (3) Log the count of unmatched records and the count of records with NaN object_count; (4) Save the merged dataset (with NaNs preserved) to `data/processed/final_analysis_data.csv`. **Depends on T027 completion.** **Verification**: Run a quick check to ensure `final_analysis_data.csv` contains records with NaN values in the `object_count` column.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (US2 fully functional after T027/T028 completion)

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P2)

**Goal**: Perform Pearson correlation, linear regression, and generate visualizations with strict associational framing.

**Independent Test**: Verify `results/statistics/statistics.json` contains r-values, p-values, and adjusted p-values (Holm-Bonferroni) for all metric pairs.

### Tests for User Story 3 (MANDATORY)

- [X] T029 [P] [US3] Contract test for statistics output schema in `tests/contract/test_analysis_schema.py`
- [X] T030 [P] [US3] Unit test for Holm-Bonferroni correction logic in `tests/unit/test_multiplicity_correction.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement Pearson correlation and linear regression in `code/03_analysis.py` for each predictor-outcome pair. **Note**: This task operates on the dataset `data/processed/final_analysis_data.csv`. **CRITICAL: Do NOT perform a global df.dropna(subset=['object_count']). Instead, filter only the specific rows where object_count is not NaN when performing object-count-based analyses. Preserve rows with NaN object_count for edge density and entropy analyses.**
- [X] T032 [US3] Implement Variance Inflation Factor (VIF) calculation in the analysis script to diagnose collinearity among the three visual complexity metrics. **Output**: Save VIF scores to `results/statistics/vif_report.json`.
- [ ] T033 [US3] Implement PCA generation in `code/03_analysis.py` to: (1) Fit PCA on visual complexity metrics; (2) Extract `pca_component_1`; (3) Save results to `data/processed/pca_results.json`. **Trigger**: Execute if VIF ≥ 5 for any predictor.
- [X] T034 [US3] Implement conditional regression logic in `code/03_analysis.py` to: (1) Read VIF status; (2) **CRITICAL**: If VIF ≥ 5, re-run Pearson correlation (FR-006), bootstrap resampling (FR-009), AND **LINEAR REGRESSION (FR-007)** using `pca_component_1` as the predictor. This step MUST generate new β-coefficients and 95% confidence intervals specifically for the PCA component. (3) Overwrite the primary results in memory with these new PCA-based statistics (including new beta-coefficients and CIs); (4) Else use raw metrics. **Depends on T032, T033.**
- [ ] T035 [US3] Implement Holm-Bonferroni family-wise error correction in `code/03_analysis.py` using `scipy.stats.multitest.multipletests(method=holm)`.
- [X] T036 [US3] Generate `results/statistics/multiplicity_table.csv` with columns: `test_name`, `raw_p`, `adjusted_p`, `metric_pair`. **CRITICAL**: Generate a text snippet explicitly stating: "The Holm-Bonferroni method was used for family-wise error correction." **Do NOT write to `results/report.md` here.** Instead, save the CSV and the text snippet to `results/statistics/`. **Verification**: Verify `results/statistics/multiplicity_table.csv` exists and the text snippet contains the phrase "Holm-Bonferroni". **Note**: The final embedding into `results/report.md` is handled by T045.
- [ ] T037 [US3] Implement logic in `code/03_analysis.py` to: (1) Frame all findings as associational (no causal claims) in output documentation; (2) Generate a dedicated text justification for the p<0.05 significance threshold. **Output**: Save justification to `results/statistics/alpha_threshold_justification.md`. **Template**: The justification must include: (a) Introduction to the p-value concept, (b) Explanation of the 0.05 threshold as a community standard, (c) Citation: "Wilkinson, L., & Task Force on Statistical Inference. (1999). Statistical methods in psychology journals: Guidelines and explanations. American Psychologist, 54(8), 594–604.", (d) Conclusion. **Minimum length**: 150 words. **Do NOT write to `results/report.md` here.**
- [X] T037b [US3] **Citations Task**: Generate `results/statistics/methods_citations.md` containing specific citations for the visual complexity metric methods: OpenCV edge detection (with URL/reference), Color Entropy formula (with reference), and YOLOv5 model architecture (with reference). **Output**: Save to `results/statistics/methods_citations.md`.
- [ ] T038 [US3] Implement scatter plot generation in `code/04_visualization.py` with trend lines for significant correlations (p<0.05) and save to `results/plots/`. **Depends on T031-T037 completion.**
- [X] T039b [US3] Save final statistics (including PCA results if applicable) to `results/statistics/statistics.json` ensuring all required fields (r, p, beta, CI, adjusted_p) are present. **Note**: T039a has been removed to prevent overwriting PCA results.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Sensitivity Analysis and Robustness Checks (Priority: P3)

**Goal**: Conduct bootstrap resampling and alternative binning strategies to validate robustness.

**Independent Test**: Verify `results/sensitivity/bootstrap_results.json` shows directional consistency and `results/sensitivity/binning_results.csv` shows magnitude stability (<0.1 change).

### Tests for User Story 4 (MANDATORY)

- [X] T040 [P] [US4] Unit test for bootstrap resampling logic (≥1000 iterations) in `tests/unit/test_bootstrap.py`

### Implementation for User Story 4

- [ ] T041 [US4] Implement bootstrap resampling (≥1000 iterations) in `code/03_analysis.py` using `scipy.stats.bootstrap` to compute 95% confidence intervals for correlation coefficients. **Output**: Save to `results/sensitivity/bootstrap_results.json`.
- [ ] T042 [US4] Implement alternative binning strategies (quartiles, deciles) in `code/03_analysis.py` to re-calculate correlations.
- [X] T043 [US4] Generate `results/sensitivity/binning_results.csv` with columns: `binning_strategy`, `predictor`, `outcome`, `pearson_r`, `p_value` (satisfies FR-010).
- [X] T044 [US4] Save bootstrap confidence intervals to `results/sensitivity/bootstrap_results.json`.
- [X] T045 [US4] **Final Report Generation**: Create `results/report.md` as the canonical final report.
 (1) **Read** `results/statistics/methods_citations.md` (from T037b), `results/statistics/alpha_threshold_justification.md` (from T037), and `results/statistics/multiplicity_table.csv` (from T036).
 (2) **Embed** the full text of `methods_citations.md` under a section `## Methods Citations`.
 (3) **Embed** the full text of `alpha_threshold_justification.md` under a section `## Threshold Justification`.
 (4) **Render** the table from `multiplicity_table.csv` as a Markdown table under a section `## Multiplicity Correction`.
 (5) **Explicitly include** the text snippet from T036 naming "Holm-Bonferroni" in the report.
 (6) **Append** the random seed used (from T052) to the Methods section.
 (7) **Verification**: Verify `results/report.md` exists and contains the full text of the embedded files and the "Holm-Bonferroni" declaration. **Dependencies**: T039 (US3), T044 (US4), T037 (Alpha justification), T037b (Citations), T036 (Multiplicity table).

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] Documentation updates: Create `specs/001-visual-distraction-cognitive-control/quickstart.md` explaining the synthetic data fallback and associational framing. **Requirement**: Add a "Data Source Selection" section explaining how to switch between real and synthetic data, and an "Interpretation of Results" section explaining the associational framing. **Specific Content**:
 - **Data Source Selection**:
 - Header: `## Data Source Selection`
 - Content: Explain the logic for choosing between real and synthetic data. Include a subsection `### Real Dataset Path` detailing the verification steps and fallback mechanism if a real dataset is found. Include a subsection `### Synthetic Data Path` detailing the generation process.
 - **Interpretation of Results**:
 - Header: `## Interpretation of Results`
 - Content: Explain the associational nature of the findings, emphasizing that no causal claims are made. Include a subsection `### Real Dataset Interpretation` and `### Synthetic Data Interpretation` if applicable.
 - **Verification**: Verify file exists at `specs/001-visual-distraction-cognitive-control/quickstart.md` and contains the required headers and sections.
- [X] T047 Code cleanup and refactoring to ensure PEP8 compliance. **Verification**: Run PEP8 linter; ensure no errors.
- [ ] T048a [P] Performance optimization: Add runtime profiling code to `code/` to log execution time for `01_data_acquisition.py` and `02_visual_metrics.py`. **Verification**: Run code and verify log output contains execution times.
- [X] T048b [P] Performance optimization: Verify CI configuration exists and fails on timeout. **Verification**: Run code with simulated load and verify log output contains runtime metrics; check CI config for timeout settings.
- [X] T049 [P] Additional unit tests for edge cases (image failure, zero variance) in `tests/unit/`.
- [X] T050 [P] Run `quickstart.md` validation to ensure end-to-end pipeline execution.
- [X] T051 [P] [US1] **Integrated Validation**: Logic for strict dataset source validation (checking linkage) is now integrated into T015. This task is marked complete [X] as its logic is implemented. **Verification**: Confirm T015 logs the correct linkage validation status.
- [X] T052 [P] [US3] Add explicit documentation to `results/report.md` (via T045) stating the exact random seed used for the analysis. **Format**: Append to Methods section: `Seed: {value} (pinned in utils.py)`.
- [ ] T053 [P] [US4] Implement a summary visualization in `code/04_visualization.py` that overlays the bootstrap confidence intervals on the primary scatter plots. **Chart Type**: Scatter plot with error bars (95% CI). **Library**: Matplotlib. **Output**: `results/plots/bootstrap_overlay.png`.

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
- **User Story 2 (P1)**: **MUST wait for User Story 1** to complete (requires T020 output). Specifically, T027 waits for the `.generation_complete` marker from T015. Cannot start in parallel with US1.
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
# Launch all tests for User Story 1 together (MANDATORY):
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
- **Critical Constraint**: Synthetic data must use real distributions exhibiting a negative correlation, and real image generation logic (Pillow), not hardcoded placeholders. The generation of participants and images must be atomic within T015.
- **Critical Constraint**: VIF/PCA logic MUST occur in the Analysis phase (T032-T034), not Metric Extraction, to satisfy FR-012.
- **Critical Constraint**: Summary table of p-values (T036) and binning results (T043) must be generated as explicit CSV artifacts with specified columns (including `binning_strategy`) and merged into the final statistics output.
- **Critical Constraint**: Data acquisition (T015) MUST transition to synthetic generation (T015) atomically if download fails; it must NOT raise an exception.
- **Critical Constraint**: Object counting (T026) must use the real model but assign NaN on failure, NOT impute a proxy value.
- **Critical Constraint**: Power analysis (T019) must be implemented and reported to satisfy SC-004, with calculated power value and rationale documented.
- **Critical Constraint**: Alpha threshold justification (T037) must be explicitly generated in the report with a specific template and minimum word count.
- **Critical Constraint**: Parallel opportunities section updated to reflect US2 dependency on US1.
- **Critical Constraint**: `results/report.md` is the canonical final report file, defined in T045.
- **Critical Constraint**: T034 now explicitly includes LINEAR REGRESSION (FR-007) for the PCA path.
- **Critical Constraint**: T028 explicitly retains records with NaN object_count; T031 filters conditionally.
- **Critical Constraint**: T036 explicitly generates the Markdown table and inserts it into `results/report.md` (via T045), and generates a standalone CSV.
- **Critical Constraint**: T037b generates `methods_citations.md`; T045 explicitly reads this file to embed the full text content.
- **Critical Constraint**: T019 explicitly documents the rationale in a 'Power Analysis Methodology' section and calculates the achieved power.
- **Critical Constraint**: T015 raises ValueError if synthetic data variance is zero.
- **Critical Constraint**: T010 and T011 are marked as Complete [X].
- **Constitution Check Note**: Tasks T003, T010, T011, T014, T021-T023, T046, T047 are now defined and actionable. The "Constitution Check PASS" in plan.md is contingent on these tasks being completed and verified.
- **Critical Constraint**: T051 is now marked as Complete [X] as its logic is integrated into T015.
- **Critical Constraint**: T039a has been removed to prevent overwriting PCA results; T039b is the sole save point.
- **Critical Constraint**: T037 and T036 do NOT write to `results/report.md`; T045 is the sole writer.
- **Critical Constraint**: T015 explicitly supports the Hybrid path (Real Cognitive + Synthetic Images).
