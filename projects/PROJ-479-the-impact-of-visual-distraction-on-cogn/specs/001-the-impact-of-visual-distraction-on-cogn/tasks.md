---
description: "Task list template for feature implementation"
---

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
- [X] T014 [P] [US1] Unit test for synthetic data generator ensuring independent distributions in `tests/unit/test_synthetic_data.py`. **Verification**: Run test; ensure it validates that `reaction_time` and `visual_complexity` are statistically independent (p-value > 0.05 for correlation test). **MANDATORY**: This test must pass before proceeding to implementation.

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/01_data_acquisition.py` as a unified script executing the following sequential steps:
 1. **Real Dataset Lookup**: Attempt to download publicly available cognitive task datasets (Stroop, flanker) with linked workspace images from HuggingFace Datasets and OpenML. Use verified IDs or search for "linked cognitive workspace" datasets. If a valid linked dataset is found, download and parse it. **Validation**: Verify the dataset contains `participant_id`, `reaction_time`, `accuracy`, and `image_path` columns. If valid, save to `data/raw/real_participants.csv`.
 2. **Fallback Simulation**: If no linked dataset is found after exhaustive search (log "No linked public dataset found"), proceed to synthetic generation. **Do NOT** simulate failure with placeholder IDs; explicitly document the search attempt.
 3. **Synthetic Generation**: Generate synthetic participant records (N ≥ 100) with `participant_id`, `reaction_time`, `accuracy`.
 4. **Ecological Image Generation**: Generate N synthetic workspace images using `Pillow` compositing that reflects "typical home office conditions" with metadata on `lighting_condition`, `room_type`, and `demographic_group`.
 - **Algorithm**: Layer a background (wall color), furniture (rectangles/shapes representing desks/chairs), and lighting (gradients). Randomize parameters within realistic ranges (e.g., lighting: a realistic brightness range).
 - **Metadata**: For each image, generate and store metadata JSON: `{"lighting_condition": "...", "room_type": "...", "demographic_group": "..."}`.
 5. **Independence**: Generate `reaction_time` and `visual_complexity` as **INDEPENDENT** random variables (no correlation matrix). This ensures the pipeline tests the ability to detect null correlations, avoiding tautology.
 6. **Validation**: Verify N ≥ 100. Log warning if missing values > 5%.
 7. **Marker**: Write `data/processed/.ready` marker file upon successful completion.
 8. **Error Handling**: If validation fails, raise `ValueError` with message: `ERROR: Data validation failed. Missing: {count}%, N: {n}`.
 9. **Output Paths**: Save synthetic participants to `data/raw/synthetic_participants.csv` and images to `data/raw/synthetic_images/`. Merge with images to create `data/processed/merged_data.csv`.
 **Verification**: Immediately after generation, compute edge density on a sample. If std dev is 0, raise `ValueError`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Visual Complexity Metric Extraction (Priority: P1)
**⚠️ DEPENDENCY**: This phase (US2) CANNOT start until Phase 3 (US1) is complete (T015 output required). **Specifically, T027 waits for the `.ready` marker from T015.**

**Goal**: Compute edge density, color entropy, and object count for all workspace images using CPU-tractable methods.

**Independent Test**: Verify that `results/statistics/visual_metrics.json` contains non-zero standard deviation for all three metrics across the sample.

### Tests for User Story 2 (MANDATORY)

- [X] T021 [P] [US2] Unit test for edge density calculation (normalized [0,1]) in `tests/unit/test_edge_density.py`
- [X] T022 [P] [US2] Unit test for color entropy calculation in `tests/unit/test_color_entropy.py`
- [X] T023 [P] [US2] Unit test for object count handling (NaN assignment on failure) in `tests/unit/test_object_count.py`

### Implementation for User Story 2

- [ ] T026-impl [US2] **IMPLEMENT MISSING CODE**: Implement `code/02_visual_metrics.py`. This file is currently missing and is required for FR-004 and SC-006.
 1. **Edge Density**: Implement using OpenCV Canny/Sobel edge detection, outputting normalized values [0, 1].
 2. **Color Entropy**: Implement using `np.histogram` on flattened RGB channels (bins=256) to compute entropy as `-sum(p * log2(p))`.
 3. **Object Count**: Implement using `ultralytics` YOLOv5n/tiny (CPU mode). **CRITICAL**: If the model fails, times out, or returns no objects for an image, assign NaN to the object count for that image. DO NOT impute a proxy value.
 4. **Verification**: Ensure all three functions exist and pass unit tests T021, T022, T023.
 **DEPENDS ON: T015 (Marker File)**.

- [ ] T026-verify [US2] **VERIFY IMPLEMENTATION**: Run unit tests T021, T022, T023 against the newly implemented `code/02_visual_metrics.py`. Mark [X] only if all tests pass and the file exists.
 **DEPENDS ON: T026-impl**.

- [ ] T027 [US2] Create `code/02_visual_metrics.py` main execution block to:
 1. **Wait for `data/processed/.ready` marker** (from T015).
 2. Iterate over all images in `data/raw/synthetic_images/` (if synthetic) or `data/raw/` (if real).
 3. Handle missing images by logging error and skipping.
 4. Compute metrics using the functions from T026-impl.
 5. Save to `data/processed/visual_metrics_intermediate.csv`.
 **DEPENDS ON: T026-verify (Verification Complete)**.

- [ ] T028 [US2] Implement merge logic in `code/02_visual_metrics.py` to:
 1. Join `visual_metrics_intermediate.csv` with `data/processed/merged_data.csv` (from US1) using `inner join on participant_id`.
 2. **CRITICAL**: Do NOT drop records with NaN object_count here. Retain all records, including those with NaN for object_count, to allow edge density and entropy analyses to proceed for these participants.
 3. Log the count of unmatched records and the count of records with NaN object_count.
 4. Save the merged dataset (with NaNs preserved) to `data/processed/final_analysis_data.csv`.
 **DEPENDS ON: T027 completion**. **Verification**: Run a quick check to ensure `final_analysis_data.csv` contains records with NaN values in the `object_count` column.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (US2 fully functional after T027/T028 completion)

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P2)

**Goal**: Perform Pearson correlation, linear regression, VIF/PCA, bootstrap, multiplicity correction, and generate visualizations with strict associational framing.

**Independent Test**: Verify `results/statistics/statistics.json` contains r-values, p-values, and adjusted p-values (Holm-Bonferroni) for all metric pairs.

### Tests for User Story 3 (MANDATORY)

- [X] T029 [P] [US3] Contract test for statistics output schema in `tests/contract/test_analysis_schema.py`
- [X] T030 [P] [US3] Unit test for Holm-Bonferroni correction logic in `tests/unit/test_multiplicity_correction.py`

### Implementation for User Story 3

- [ ] T031-impl [US3] **IMPLEMENT MISSING CODE**: Implement `code/03_analysis.py`. This file is currently missing and is required for FR-006, FR-007, FR-009, FR-008, FR-010, FR-011, FR-012.
 1. **VIF Calculation**: Compute VIF for edge_density, color_entropy, object_count. Save to `results/statistics/vif_report.json`.
 2. **PCA Decision**: If max(VIF) >= 5, perform PCA and extract `pca_component_1`. Add to dataframe.
 3. **Correlation & Regression**: Perform Pearson correlation and linear regression for each predictor-outcome pair. Use `pca_component_1` if VIF >= 5, else use raw metrics.
 4. **Visualization (FR-008)**: Generate scatter plots for significant correlations (p<0.05) with trend lines and save to `results/plots/`. **Note**: T038 logic is integrated here but T038 is a separate task for final verification.
 5. **Holm-Bonferroni**: Apply correction to all p-values.
 6. **Bootstrap**: Implement bootstrap resampling (≥1000 iterations) for CIs.
 7. **Binning**: Implement alternative binning strategies (quartiles, deciles) for sensitivity analysis.
 8. **Output**: Save `r`, `p`, `beta`, `ci_lower`, `ci_upper`, `adjusted_p`, and sensitivity tables to `results/statistics/` and `results/sensitivity/`.
 **DEPENDS ON: T028**.

- [ ] T031-verify [US3] **VERIFY IMPLEMENTATION**: Run unit tests for correlation, VIF, PCA, Holm-Bonferroni, and bootstrap logic against the newly implemented `code/03_analysis.py`. Mark [X] only if all tests pass and the file exists.
 **DEPENDS ON: T031-impl**.

- [ ] T035 [US3] Implement Holm-Bonferroni family-wise error correction in the analysis script using `scipy.stats.multitest.multipletests(method=holm)`. **Note**: Logic integrated into T031-impl, but this task ensures the specific method is verified.
 **DEPENDS ON: T031-verify**.
 **Verification**: Run unit test T030; verify corrected p-values match expected values for a sample set.

- [ ] T036 [US3] Generate `results/statistics/multiplicity_table.csv` with columns: `test_name`, `raw_p`, `adjusted_p`, `metric_pair`. **CRITICAL**: Generate a text snippet explicitly stating: " (Wikipedia: Holm–Bonferroni method, https://en.wikipedia.org/wiki/Holm–Bonferroni_method)" **Do NOT write to `results/report.md` here.** Instead, save the CSV and the text snippet to `results/statistics/`. **Verification**: Verify `results/statistics/multiplicity_table.csv` exists and the text snippet contains the phrase "Holm-Bonferroni". **Note**: The final embedding into `results/report.md` is handled by T045.
 **DEPENDS ON: T031-verify**.

- [ ] T019 [US3] **Power Analysis**: Implement power analysis in `code/03_analysis.py` using `statsmodels.stats.power.FTestPower` (or equivalent for correlation) to calculate achieved power for the sample size N (from `final_analysis_data.csv`) and the observed effect size (Pearson's r). **Output**: Save `power_analysis_report.md` to `results/statistics/` with the calculated power value, sample size, effect size, and rationale. **Verification**: Verify power value is calculated and report contains method description. **DEPENDS ON: T031-verify**.

- [ ] T037a [US3] **Inline Justification Generation**: Generate the p<0.05 threshold justification content directly within `code/03_analysis.py` (to be used by T045).
 1. Frame all findings as associational (no causal claims) in output documentation.
 2. Load citation content from `data/citations.yaml` (verified by Reference-Validator) for the p<0.05 justification.
 3. **Template**: The justification must include:
 - (a) Introduction to the p-value concept.
 - (b) Explanation of the 0.05 threshold as a community standard.
 - (c) Citation: Load from `citations.yaml`.
 - (d) Conclusion.
 4. **Minimum length**: 150 words.
 5. **Output**: Store the content in a variable `alpha_threshold_justification` to be passed to T045. Do NOT write to an intermediate file.
 **DEPENDS ON: T031-verify**.

- [ ] T037b [US3] **Inline Citations Generation**: Generate `methods_citations` variable content directly within `code/03_analysis.py` (to be used by T045).
 1. Load citation content from `data/citations.yaml` for:
 - OpenCV Edge Detection
 - Color Entropy
 - YOLOv5
 2. **Output**: Store the content in a variable `methods_citations` to be passed to T045. Do NOT write to an intermediate file.
 **DEPENDS ON: T031-verify**.

- [ ] T039b [US3] Save final statistics (including PCA results if applicable) to `results/statistics/statistics.json` ensuring all required fields (r, p, beta, CI, adjusted_p) are present. **Note**: Logic integrated into T031-impl. This task ensures the final JSON is written correctly.
 **DEPENDS ON: T031-verify**.

- [ ] T038 [US3] **Generate Scatter Plots**: Generate scatter plots for each significant correlation (p<0.05) with trend line overlay and axis labels. **Verification**: Verify `results/plots/` contains at least one scatter plot per significant metric pair. **DEPENDS ON: T031-verify**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Sensitivity Analysis and Robustness Checks (Priority: P3)

**Goal**: Conduct bootstrap resampling and alternative binning strategies to validate robustness.

**Independent Test**: Verify `results/sensitivity/bootstrap_results.json` shows directional consistency and `results/sensitivity/binning_results.csv` shows magnitude stability (<0.1 change).

### Tests for User Story 4 (MANDATORY)

- [X] T040 [P] [US4] Unit test for bootstrap resampling logic (≥1000 iterations) in `tests/unit/test_bootstrap.py`

### Implementation for User Story 4

- [ ] T041 [US4] Implement bootstrap resampling (≥1000 iterations) in `code/03_analysis.py` using `scipy.stats.bootstrap` with arguments `vectorized=True, confidence_level=0.95, n_resamples=1000` to compute % confidence intervals for correlation coefficients. **Output**: Save to `results/sensitivity/bootstrap_results.json` with keys `mean_r`, `ci_lower`, `ci_upper`, `n_resamples`.
 **DEPENDS ON: T031-verify**.

- [ ] T042 [US4] Implement alternative binning strategies (quartiles, deciles) in `code/03_analysis.py` to re-calculate correlations. **CRITICAL**: Iterate over **all 6 predictor-outcome pairs** (3 metrics × 2 outcomes) to ensure full coverage of FR-010.
 **DEPENDS ON: T031-verify**.

- [ ] T043 [US4] Generate `results/sensitivity/binning_results.csv` with columns: `binning_strategy`, `predictor`, `outcome`, `pearson_r`, `p_value`. **CRITICAL**: Ensure exactly **6 rows** are generated for each binning strategy (one for each predictor-outcome pair) to satisfy FR-010.
 **DEPENDS ON: T042**.

- [ ] T044 [US4] Save bootstrap confidence intervals to `results/sensitivity/bootstrap_results.json`.
 **DEPENDS ON: T041**.

- [ ] T045 [US4] **Final Report Generation**: Create `results/report.md` as the canonical final report.
 1. **Wait for T019, T036, T039b, T044 completion**.
 2. **Read** `results/statistics/power_analysis_report.md` (from T019), `results/statistics/multiplicity_table.csv` (from T036).
 3. **Generate** the "Methods Citations" section content using the `methods_citations` variable generated internally by T037b (now part of T039b flow).
 4. **Generate** the "Threshold Justification" section content using the `alpha_threshold_justification` variable generated internally by T037a (now part of T039b flow).
 5. **Embed** the generated citations and justification text directly into the report.
 6. **Render** the table from `multiplicity_table.csv` as a Markdown table under a section `## Multiplicity Correction`.
 7. **Explicitly include** the text snippet from T036 naming "Holm-Bonferroni" in the report.
 8. **Append** the random seed used (from T052) to the Methods section.
 9. **Include** the power analysis report content in the Methods section.
 10. **Verification**: Verify `results/report.md` exists and contains the full text of the generated sections and the "Holm-Bonferroni" declaration.
 **DEPENDS ON: T019, T036, T039b, T044**. (Note: T037a and T037b are internal steps of the analysis flow, not separate blocking tasks).

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Documentation updates: Create `specs/001-visual-distraction-cognitive-control/quickstart.md` explaining the synthetic data fallback and associational framing. **Requirement**: Add a "Data Source Selection" section explaining how to switch between real and synthetic data, and an "Interpretation of Results" section explaining the associational framing. **Specific Content**:
 - **Data Source Selection**:
 - Header: `## Data Source Selection`
 - Content: Explain the logic for choosing between real and synthetic data. Include a subsection `### Real Dataset Path` detailing the verification steps and fallback mechanism if a real dataset is found. Include a subsection `### Synthetic Data Path` detailing the generation process.
 - **Interpretation of Results**:
 - Header: `## Interpretation of Results`
 - Content: Explain the associational nature of the findings, emphasizing that no causal claims are made. Include a subsection `### Real Dataset Interpretation` and `### Synthetic Data Interpretation` if applicable.
 - **Verification**: Verify file exists at `specs/001-visual-distraction-cognitive-control/quickstart.md` and contains the required headers and sections.
- [ ] T047 [P] Code cleanup and refactoring to ensure PEP8 compliance. **Verification**: Run PEP8 linter; ensure no errors.
- [ ] T049 [P] Additional unit tests for edge cases (image failure, zero variance) in `tests/unit/`.
- [ ] T050 [P] Run `quickstart.md` validation to ensure end-to-end pipeline execution.
- [ ] T051 [P] [US1] **Integrated Validation**: Logic for strict dataset source validation (checking linkage) is now integrated into T015. This task is marked complete [X] as its logic is implemented. **Verification**: Confirm T015 logs the correct linkage validation status.
- [ ] T052 [P] [US3] Add explicit documentation to `results/report.md` (via T045) stating the exact random seed used for the analysis. **Format**: Append to Methods section: `Seed: {value} (pinned in utils.py)`.

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
- **User Story 2 (P1)**: **MUST wait for User Story 1** to complete (requires T015 output). Specifically, T027 waits for the `.ready` marker from T015. **DEPENDS ON: T015**.
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Requires US1 & US2 data output (T028)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Requires US3 analysis results (T031-verify)

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
3. Complete Phase 3: User Story 1 (including real data fetch logic)
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
 - Developer A: User Story 1 (including real data fetch logic)
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
- **Critical Constraint**: Synthetic data must use INDEPENDENT distributions for predictors and outcomes (no correlation), and real image generation logic (Pillow), not hardcoded placeholders. The generation of participants and images must be atomic within T015.
- **Critical Constraint**: VIF/PCA logic MUST occur in the Analysis phase (T031), not Metric Extraction, to satisfy FR-012.
- **Critical Constraint**: Summary table of p-values (T036) and binning results (T043) must be generated as explicit CSV artifacts with specified columns (including `binning_strategy`) and merged into the final statistics output.
- **Critical Constraint**: Data acquisition (T015) must attempt real lookup on HuggingFace/OpenML before falling back to synthetic generation; it must NOT raise an exception.
- **Critical Constraint**: Object counting (T026) must use the real model but assign NaN on failure, NOT impute a proxy value.
- **Critical Constraint**: Power analysis (T019) must be implemented and reported to satisfy SC-004, with calculated power value and rationale documented using the correct statistical method (`FTestPower`).
- **Critical Constraint**: Alpha threshold justification (T037a) must be explicitly generated in the report with a specific template and minimum word count, loading citations from `citations.yaml`.
- **Critical Constraint**: Parallel opportunities section updated to reflect US2 dependency on US1.
- **Critical Constraint**: `results/report.md` is the canonical final report file, defined in T045.
- **Critical Constraint**: T031 now includes LINEAR REGRESSION (FR-007) for the PCA path.
- **Critical Constraint**: T028 explicitly retains records with NaN object_count; T031 filters conditionally.
- **Critical Constraint**: T036 explicitly generates the Markdown table and inserts it into `results/report.md` (via T045), and generates a standalone CSV.
- **Critical Constraint**: T037b generates `methods_citations` content inline; T045 explicitly uses this content.
- **Critical Constraint**: T019 explicitly documents the rationale in a 'Power Analysis Methodology' section and calculates the achieved power using `FTestPower`.
- **Critical Constraint**: T015 raises ValueError if synthetic data variance is zero.
- **Critical Constraint**: T010 and T011 are marked as Complete [X].
- **Constitution Check Note**: Tasks T003, T010, T011, T014, T021-T023, T046, T047 are now defined and actionable. The "Constitution Check PASS" in plan.md is contingent on these tasks being completed and verified.
- **Critical Constraint**: T051 is now marked as Complete [X] as its logic is integrated into T015.
- **Critical Constraint**: T039a has been removed to prevent overwriting PCA results; T039b is the sole save point.
- **Critical Constraint**: T037a and T036 do NOT write to `results/report.md`; T045 is the sole writer.
- **Critical Constraint**: T015 explicitly supports the Hybrid path (Real Cognitive + Synthetic Images).
- **Critical Constraint**: T027 explicitly depends on T015 (Marker File).
- **Critical Constraint**: T045 explicitly depends on T019, T036, T039b, T044. (T037a/T037b are internal).
- **Critical Constraint**: Real data fetch logic is integrated into T015; Phase O is removed.
- **Critical Constraint**: T048a/T048b and T053 have been removed as scope creep.
- **Critical Constraint**: T053, T054, T055, T056 have been removed and their functionality integrated into T025, T031, T034b, T041, T037b respectively.
- **Critical Constraint**: T019 uses `FTestPower` for correlation power analysis.
- **Critical Constraint**: T015 generates independent distributions.
- **Critical Constraint**: T015 explicitly queries real platforms before fallback.
- **Critical Constraint**: T045 dependencies updated to remove T037/T037b.
- **Critical Constraint**: T027 dependency updated to T015 marker.
- **Critical Constraint**: T042 and T043 explicitly mandate 6-pair iteration and 6-row output for FR-010.
- **Critical Constraint**: T031 explicitly includes conditional PCA integration logic.
- **Critical Constraint**: T015 uses ecological compositing with metadata for Constitution VII.
- **Critical Constraint**: T037a loads citations from `citations.yaml` for Constitution II.
- **Critical Constraint**: T034b depends on T034a, not T033, to allow non-collinear path.
- **Critical Constraint**: T039b depends on T034a and T031, removing hard block on T034b/T033.
- **Critical Constraint**: T031 is now the single source for VIF, PCA, Regression, Plots, and Multiplicity.
- **Critical Constraint**: T020 is removed; logic integrated into T015.
- **Critical Constraint**: T032, T033, T034a/b/c are removed; logic integrated into T031.
- **Critical Constraint**: T038 is removed; logic integrated into T031. **NOTE**: T038 has been re-introduced as a distinct task to ensure FR-008 visualization requirements are met.
- **Critical Constraint**: T015 Step 3 removed to avoid contradiction; Step 5 is the sole generation logic.
- **Critical Constraint**: **Constitution Check: PENDING**. The project is currently in a state where core implementation tasks (T015, T026-impl, T031-impl) are incomplete. The "PASS" status in the plan is contingent on the completion of these tasks.
- **Critical Constraint**: **Task Completion Verification**: No task can be marked [X] until the corresponding file exists, passes all unit tests, and produces the required artifacts.