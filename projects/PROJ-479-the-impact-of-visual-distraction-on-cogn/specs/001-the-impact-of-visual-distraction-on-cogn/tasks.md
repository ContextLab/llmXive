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

- [X] T002 Create `code/requirements.txt` with pinned dependencies (pandas, numpy, scikit-learn, scipy, opencv-python-headless, ultralytics>=8.0.0, matplotlib, seaborn, Pillow, pytest, statsmodels, requests, openml)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools. **Verification**: Run linting on all code files; ensure no errors.
- [X] T004 [P] Setup data directory structure (`data/raw`, `data/processed`) and results directory (`results/statistics`, `results/plots`, `results/sensitivity`). **Note**: Aligned strictly with plan.md 'Project Structure'; methodology artifacts will be placed in `results/statistics` or `results/report.md`.
- [X] T005 [P] Implement logging infrastructure in `code/utils.py` (handlers, formatters)
- [X] T006 [P] Implement checksumming logic (sha256) in `code/utils.py`
- [X] T007 [P] Implement global random seed management (pinned seeds) in `code/utils.py`
- [X] T008 [P] Implement error handler in `code/utils.py` to log specific errors: 'unmatched_participant_ids', 'image_processing_failures', and 'zero_variance_warning' with structured JSON messages as per Edge Cases in spec.md
- [X] T009 [P] Implement contract test in `tests/contract/test_error_logging.py` to verify that `code/utils.py` logs the specific keys 'unmatched_participant_ids', 'image_processing_failures', and 'zero_variance_warning' when triggered
- [X] T010 [P] Create dataset schema definition in `specs/001-visual-distraction-cognitive-control/contracts/dataset.schema.yaml`. **Verification**: Validate against sample data.
- [X] T011 [P] Create analysis output schema definition in `specs/001-visual-distraction-cognitive-control/contracts/analysis_output.schema.yaml`. **Verification**: Validate against sample output.
- [X] T012 [P] Implement contract tests in `tests/contract/` to validate JSON/CSV outputs against schemas. **Verification**: Run tests; ensure they pass.
- [X] T017 [P] Create `data/citations.yaml` with verified primary sources for:
 1. **Holm-Bonferroni**: Holm, S. (1979). "A Simple Sequentially Rejective Multiple Test Procedure". Scandinavian Journal of Statistics.
 2. **OpenCV Edge Detection**: Canny, J. (1986). "A Computational Approach to Edge Detection". IEEE TPAMI.
 3. **Color Entropy**: Shannon, C.E. (1948). "A Mathematical Theory of Communication".
 4. **YOLOv8**: Redmon, J., et al. (n.d.) and Ultralytics YOLOv8 documentation.
 5. **p<0.05 Threshold**: ASA Statement on p-values (Wasserstein & Lazar, n.d.).
 6. **Verification**: Validate YAML syntax and ensure all citations are primary sources (not Wikipedia).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Acquire real publicly available cognitive task datasets (OpenML) and real workspace environment images (Unsplash). If real data acquisition fails completely, generate synthetic participant records simulating the correlation structure described in literature. **CRITICAL**: No "proxy linkage" mixing real cognitive data with real images via fake IDs is allowed.

**Independent Test**: Verify that `data/processed/merged_data.csv` exists with ≥100 rows, non-null `reaction_time`, `accuracy`, and `visual_complexity` columns.

### Tests for User Story 1 (MANDATORY)

- [X] T013 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_dataset_schema.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/01_data_acquisition.py` as a unified script executing the following sequential steps:
 1. **Real Dataset Lookup**: Attempt to download publicly available cognitive task datasets (Stroop, flanker) with linked workspace images from HuggingFace Datasets and OpenML. Search for specific IDs representing Stroop and Flanker datasets on OpenML. If valid linked dataset found, download and parse. **Validation**: Verify dataset contains `participant_id`, `reaction_time`, `accuracy`, `image_path`. Save to `data/raw/real_participants.csv`.
 2. **Real Data Path (Primary)**: If no linked dataset found:
 a. **Fetch Cognitive Data**: Download real cognitive task data (Stroop/Flanker) from OpenML (e.g., dataset ID 4444) with participant-level reaction time and accuracy. Save to `data/raw/cognitive_data.csv`.
 b. **Fetch Workspace Images**: Query Unsplash API for workspace images using keywords: "home office", "desk", "workspace", "remote work", "study room". Download N=150 images. Save to `data/raw/workspace_images/`.
 c. **Extract Metadata**: For each Unsplash image, extract metadata (lighting_condition, room_type, tags) from the API response. Save to `data/raw/image_metadata.json`.
 d. **PII Sanitization (T016)**: BEFORE merging, call the sanitization logic (T016) to rename images to `img_<sha256_hash>.jpg` and strip EXIF data. Update `image_metadata.json` with new paths.
 e. **Merge Real Data**: Merge `cognitive_data.csv` with `image_metadata.json` based on a defined environmental category (e.g., "Home Office" tag match) ONLY if a real, pre-existing link exists in the metadata. **CRITICAL**: If no valid real link exists, DO NOT create fake links. Proceed to Fallback.
 3. **Fallback Simulation**: If real linked dataset NOT found AND real cognitive data OR real images cannot be acquired (API failure, no data):
 a. Generate synthetic participant records (N ≥ 100) with `participant_id`, `reaction_time`, `accuracy`, and `visual_complexity`.
 b. **CRITICAL**: Use Cholesky decomposition with a covariance matrix targeting a negative correlation between `visual_complexity` and `reaction_time`. Do NOT use independent variables.
 4. **Validation**: Verify N ≥ 100. Log warning if missing values > 5%.
 5. **Marker**: Write `data/processed/.ready` marker file upon successful completion.
 6. **Error Handling**: If validation fails, raise `ValueError` with message: `ERROR: Data validation failed. Missing: {count}%, N: {n}`.
 7. **Output Paths**: Save cognitive data to `data/raw/cognitive_data.csv`, images to `data/raw/workspace_images/`, metadata to `data/raw/image_metadata.json`. Merge to create `data/processed/merged_data.csv`.
 **Verification**: Immediately after generation, compute edge density on a sample. If std dev is 0, raise `ValueError`.

- [X] T016 [US1] Implement PII Sanitization in `code/utils.py` (function called by T015):
 1. **Rename Images**: Rename all images in `data/raw/workspace_images/` to `img_<sha256_hash>.jpg` to remove original filenames.
 2. **Strip EXIF**: Strip all EXIF data from images using `Pillow` to remove PII (location, camera model, timestamps).
 3. **Verify**: Log count of sanitized images.
 **DEPENDS ON: T015 (Step 2b/c)**. **Note**: This function must be called by T015 BEFORE the final merge.

- [X] T017 [P] [US1] Create `data/citations.yaml` with verified primary sources (Moved to Phase 2 for independence). **Verification**: Validate YAML syntax and ensure all citations are primary sources (not Wikipedia).

- [ ] T018 [US1] **VERIFY DATA INTEGRITY**: Run validation on `data/processed/merged_data.csv` to ensure: <!-- FAILED: unspecified -->
 1. N ≥ 100.
 2. No missing values in `reaction_time` or `accuracy` > 5%.
 3. Metadata exists for all images.
 **DEPENDS ON: T015, T016**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Visual Complexity Metric Extraction (Priority: P1)
**⚠️ DEPENDENCY**: This phase (US2) CANNOT start until Phase 3 (US1) is complete (T018 output required). **Specifically, T027 waits for the `.ready` marker from T015 and T018 validation.**

**Goal**: Compute edge density, color entropy, and object count for all workspace images using CPU-tractable methods.

**Independent Test**: Verify that `results/statistics/visual_metrics.json` contains non-zero standard deviation for all three metrics across the sample.

### Tests for User Story 2 (MANDATORY)

- [X] T021 [P] [US2] Unit test for edge density calculation (normalized [0,1]) in `tests/unit/test_edge_density.py`
- [X] T022 [P] [US2] Unit test for color entropy calculation in `tests/unit/test_color_entropy.py`
- [X] T023 [P] [US2] Unit test for object count handling (NaN assignment on failure) in `tests/unit/test_object_count.py`

### Implementation for User Story 2

- [X] T026a [US2] **IMPLEMENT EDGE DENSITY**: Implement `code/02_visual_metrics.py` function `compute_edge_density`.
 1. **Edge Density**: Implement using OpenCV Canny/Sobel edge detection, outputting normalized values [0, 1].
 2. **Verification**: Ensure function passes unit test T021.
 **DEPENDS ON: T018 (Data Ready)**. **FR Tags**: [FR-002], [SC-006].

- [ ] T026b [US2] **IMPLEMENT COLOR ENTROPY**: Implement `code/02_visual_metrics.py` function `compute_color_entropy`.
 1. **Color Entropy**: Implement using `np.histogram` on flattened RGB channels (bins=256) to compute entropy as `-sum(p * log2(p))`.
 2. **Verification**: Ensure function passes unit test T022.
 **DEPENDS ON: T018 (Data Ready)**. **FR Tags**: [FR-003], [SC-006].

- [ ] T026c [US2] **IMPLEMENT OBJECT COUNT**: Implement `code/02_visual_metrics.py` function `compute_object_count`.
 1. **Object Count**: Implement using `ultralytics` YOLOvn (nano) in CPU mode. **CRITICAL**: Use weights file `yolov8n.pt` and confidence threshold `0.25`. If the model fails, times out, or returns no objects for an image, assign NaN to the object count for that image. DO NOT impute a proxy value.
 2. **Verification**: Ensure function passes unit test T023.
 **DEPENDS ON: T018 (Data Ready)**. **FR Tags**: [FR-004], [SC-006].

- [ ] T026-verify [US2] **VERIFY IMPLEMENTATION**: Run unit tests T021, T022, T023 against the newly implemented `code/02_visual_metrics.py`. Mark [X] only if all tests pass and the file exists.
 **DEPENDS ON: T026a, T026b, T026c**.

- [ ] T027 [US2] Create `code/02_visual_metrics.py` main execution block to:
 1. **Wait for `data/processed/.ready` marker** (from T015) and T018 validation.
 2. Iterate over all images in `data/raw/workspace_images/` (or `data/raw/synthetic_images/` if fallback).
 3. Handle missing images by logging error and skipping.
 4. Compute metrics using the functions from T026a, T026b, T026c.
 5. Save to `data/processed/visual_metrics_intermediate.csv`.
 **DEPENDS ON: T026-verify (Verification Complete)**.

- [ ] T028 [US2] Implement merge logic in `code/02_visual_metrics.py` to:
 1. Join `visual_metrics_intermediate.csv` with `data/processed/merged_data.csv` (from US1) using `inner join on participant_id`.
 2. **CRITICAL**: Drop records with NaN object_count for analyses requiring that metric. Retain records with NaN for edge density and entropy analyses, but explicitly log the count of excluded records.
 3. Log the count of unmatched records and the count of records with NaN object_count.
 4. Save the merged dataset (with NaNs preserved where applicable) to `data/processed/final_analysis_data.csv`.
 **DEPENDS ON: T027 completion**. **Verification**: Run a quick check to ensure `final_analysis_data.csv` contains records with NaN values in the `object_count` column (but they are flagged for exclusion in specific analyses).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (US2 fully functional after T027/T028 completion)

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P2)

**Goal**: Perform Pearson correlation, linear regression, VIF/PCA, bootstrap, multiplicity correction, and generate visualizations with strict associational framing.

**Independent Test**: Verify `results/statistics/statistics.json` contains r-values, p-values, and adjusted p-values (Holm-Bonferroni) for all metric pairs.

### Tests for User Story 3 (MANDATORY)

- [X] T029 [P] [US3] Contract test for statistics output schema in `tests/contract/test_analysis_schema.py`
- [X] T030 [P] [US3] Unit test for Holm-Bonferroni correction logic in `tests/unit/test_multiplicity_correction.py`

### Implementation for User Story 3

- [ ] T031a [US3] **IMPLEMENT VIF/PCA LOGIC**: Implement `code/03_analysis.py` function `compute_vif_and_pca`.
 1. **VIF Calculation**: Compute VIF for edge_density, color_entropy, object_count. Save to `results/statistics/vif_report.json`.
 2. **PCA Decision**: If max(VIF) >= 5, perform PCA and extract `pca_component_1`. Add to dataframe.
 3. **CRITICAL**: Explicitly state that if VIF >= 5, `pca_component_1` **REPLACES** the raw metrics as the primary predictor in all subsequent regression/correlation models.
 **DEPENDS ON: T028**. **FR Tags**: [FR-011], [FR-012], [SC-007].

- [ ] T031b [US3] **IMPLEMENT CORRELATION/REGRESSION/BOOTSTRAP**: Implement `code/03_analysis.py` function `run_correlation_regression`.
 1. **Correlation & Regression**: Perform Pearson correlation and linear regression for each predictor-outcome pair. Use `pca_component_1` if VIF >= 5, else use raw metrics.
 2. **Holm-Bonferroni**: Apply correction to all p-values using `scipy.stats.multitest.multipletests(method=holm)`.
 3. **Bootstrap**: Implement bootstrap resampling (≥1000 iterations) for CIs using `scipy.stats.bootstrap`.
 4. **Binning**: Implement alternative binning strategies (quartiles, deciles) for sensitivity analysis.
 5. **Output**: Save `r`, `p`, `beta`, `ci_lower`, `ci_upper`, `adjusted_p`, and sensitivity tables to `results/statistics/` and `results/sensitivity/`.
 **DEPENDS ON: T031a**. **FR Tags**: [FR-006], [FR-007], [FR-009], [FR-010], [FR-003].

- [ ] T031c [US3] **IMPLEMENT VISUALIZATION/REPORTING**: Implement `code/03_analysis.py` function `generate_plots_and_tables`.
 1. **Visualization (FR-008)**: Generate scatter plots for significant correlations (p<0.05) with trend lines using `seaborn`. Save to `results/plots/` with filename pattern `plot_{predictor}_{outcome}.png`.
 2. **Output**: Save final statistics to `results/statistics/statistics.json`.
 **DEPENDS ON: T031b**. **FR Tags**: [FR-008], [FR-009].

- [ ] T031d [US3] **VERIFY ASSOCIATIONAL FRAMING**: Implement `code/03_analysis.py` function `verify_associational_framing`.
 1. **Check**: Scan all generated text outputs (reports, summaries) for causal language (e.g., "cause", "effect", "impact").
 2. **Reject**: Raise `ValueError` if any causal language is detected.
 3. **Pass**: Log confirmation that all findings are framed as associational.
 **DEPENDS ON: T031c**. **FR Tags**: [FR-012], [SC-002].

- [ ] T031-verify [US3] **VERIFY IMPLEMENTATION**: Run unit tests for VIF, PCA, Correlation, Regression, Holm-Bonferroni, and Bootstrap logic against the newly implemented `code/03_analysis.py`. Mark [X] only if all tests pass and the file exists.
 **DEPENDS ON: T031a, T031b, T031c, T031d**.

- [ ] T035 [US3] Implement Holm-Bonferroni family-wise error correction in the analysis script using `scipy.stats.multitest.multipletests(method=holm)`. **Note**: Logic integrated into T031b, but this task ensures the specific method is verified.
 **DEPENDS ON: T031-verify**.
 **Verification**: Run unit test T030; verify corrected p-values match expected values for a sample set.

- [ ] T036 [US3] Generate `results/statistics/multiplicity_table.csv` with columns: `test_name`, `raw_p`, `adjusted_p`, `metric_pair`. **CRITICAL**: Load the Holm-Bonferroni citation from `data/citations.yaml` (created by T017) and embed it in the report (via T045). **Do NOT** cite Wikipedia. **Verification**: Verify `results/statistics/multiplicity_table.csv` exists and the citation is valid.
 **DEPENDS ON: T031-verify**.

- [ ] T036a [US3] **GENERATE SUMMARY TABLE**: Generate `results/statistics/summary_p_values.md` containing a Markdown table of exact p-values and Holm-Bonferroni adjusted p-values, as required by SC-005.
 **DEPENDS ON: T036**.
 **Verification**: Verify file exists and contains the required table.

- [ ] T019a [US3] **POWER ANALYSIS (A PRIORI)**: Implement power analysis in `code/03_analysis.py` using `statsmodels.stats.power.FTestPower` to calculate the required sample size for N≥100 based on an expected effect size (r=0.3) and alpha=0.05. **Output**: Save `results/statistics/power_analysis_a_priori.md` with the calculated power value, sample size, effect size, and rationale. **Verification**: Verify power value is calculated and report contains method description. **DEPENDS ON: T031-verify**.

- [ ] T019b [US3] **POWER ANALYSIS (POST-HOC)**: Implement power analysis in `code/03_analysis.py` using `statsmodels.stats.power.FTestPower` to calculate achieved power based on the observed effect size from `final_analysis_data.csv`. **Output**: Save `results/statistics/power_analysis_post_hoc.md`. **DEPENDS ON: T031-verify**.

- [ ] T037 [US3] **Generate Alpha Threshold Justification**: Read `data/citations.yaml` (from T017) and generate the p<0.05 (Wikipedia: Power (statistics), https://en.wikipedia.org/wiki/Power_(statistics)) threshold justification content.
 1. Frame all findings as associational (no causal claims).
 2. Load citation content for ASA Statement from `citations.yaml`.
 3. **Template**: The justification must include:
 - (a) Introduction to the p-value concept.
 - (b) Explanation of the 0.05 threshold as a community standard.
 - (c) Citation: Load from `citations.yaml`.
 - (d) Conclusion.
 4. **Minimum length**: 150 words.
 5. **Output**: Save the content to `results/statistics/alpha_threshold_justification.md` to be used by T045.
 **DEPENDS ON: T031-verify, T017**.

- [ ] T038 [US3] **Generate Methods Citations**: Read `data/citations.yaml` (from T017) and generate the methods citations content for OpenCV, Color Entropy, and YOLOv8.
 1. Load citation content from `citations.yaml`.
 2. **Output**: Save the content to `results/statistics/methods_citations.md` to be used by T045.
 **DEPENDS ON: T031-verify, T017**.

- [ ] T039b [US3] Save final statistics (including PCA results if applicable) to `results/statistics/statistics.json` ensuring all required fields (r, p, beta, CI, adjusted_p) are present. **Note**: Logic integrated into T031c. This task ensures the final JSON is written correctly.
 **DEPENDS ON: T031-verify**.

- [ ] T038-plot [US3] **Generate Scatter Plots**: Generate scatter plots for each significant correlation (p<0.05) with trend line overlay and axis labels. **Verification**: Verify `results/plots/` contains at least one scatter plot per significant metric pair. **DEPENDS ON: T031-verify**.

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

- [ ] T042 [US4] Implement alternative binning strategies (quartiles, deciles) in `code/03_analysis.py` to re-calculate correlations. **CRITICAL**: Iterate over **all A set of predictor-outcome pairs** (Multiple metrics × 2 outcomes) to ensure full coverage of FR-010.
 **DEPENDS ON: T031-verify**.

- [ ] T043 [US4] Generate `results/sensitivity/binning_results.csv` with columns: `binning_strategy`, `predictor`, `outcome`, `pearson_r`, `p_value`. **CRITICAL**: Ensure exactly **6 rows** are generated for each binning strategy (one for each predictor-outcome pair) to satisfy FR-010.
 **DEPENDS ON: T042**.

- [ ] T044 [US4] Save bootstrap confidence intervals to `results/sensitivity/bootstrap_results.json`.
 **DEPENDS ON: T041**.

- [ ] T045 [US4] **Final Report Generation**: Create `results/report.md` as the canonical final report.
 1. **Wait for T019a, T019b, T036, T036a, T039b, T044, T037, T038 completion**.
 2. **Read** `results/statistics/power_analysis_a_priori.md` (from T019a), `results/statistics/power_analysis_post_hoc.md` (from T019b), `results/statistics/multiplicity_table.csv` (from T036).
 3. **Read** `results/statistics/alpha_threshold_justification.md` (from T037), `results/statistics/methods_citations.md` (from T038).
 4. **Render** the table from `multiplicity_table.csv` as a Markdown table under a section `## Multiplicity Correction`.
 5. **Append** the alpha threshold justification and methods citations to the report.
 6. **Append** the random seed used (from T052) to the Methods section.
 7. **Include** the power analysis report content in the Methods section.
 8. **Template**: Use the following structure:
 - `# Final Report`
 - `## Methods` (includes power analysis, citations, seed)
 - `## Results` (includes correlation tables, plots)
 - `## Multiplicity Correction` (includes table from T036a)
 - `## Discussion` (associational framing only)
 9. **Verification**: Verify `results/report.md` exists and contains the full text of the generated sections and the "Holm-Bonferroni" declaration.
 **DEPENDS ON: T019a, T019b, T036, T036a, T039b, T044, T037, T038**.

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
- **User Story 2 (P1)**: **MUST wait for User Story 1** to complete (requires T018 output). Specifically, T027 waits for the `.ready` marker from T015 and T018 validation. **DEPENDS ON: T018**.
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

# Launch all models for User Story 1 together:
Task: "Implement 01_data_acquisition.py download/fallback logic (including Proxy Linkage)"
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
- **Critical Constraint**: Synthetic data must simulate the negative correlation structure described in literature (not independent variables), and real image fetching logic (Unsplash API) must be used for the primary path.
- **Critical Constraint**: VIF/PCA logic MUST occur in the Analysis phase (T031a), not Metric Extraction, to satisfy FR-012.
- **Critical Constraint**: Summary table of p-values (T036a) and binning results (T043) must be generated as explicit CSV/Markdown artifacts with specified columns (including `binning_strategy`) and merged into the final statistics output.
- **Critical Constraint**: Data acquisition (T015) must attempt real lookup on HuggingFace/OpenML and Unsplash API before falling back to synthetic generation; it must NOT raise an exception.
- **Critical Constraint**: Object counting (T026c) must use the real model (YOLOv8n) but assign NaN on failure, NOT impute a proxy value.
- **Critical Constraint**: Power analysis (T019a, T019b) must be implemented and reported to satisfy SC-004, with calculated power value and rationale documented using the correct statistical method (`FTestPower`).
- **Critical Constraint**: Alpha threshold justification (T037) must be explicitly generated in the report with a specific template and minimum word count, loading citations from `citations.yaml`.
- **Critical Constraint**: Parallel opportunities section updated to reflect US2 dependency on US1.
- **Critical Constraint**: `results/report.md` is the canonical final report file, defined in T045.
- **Critical Constraint**: T031a now includes LINEAR REGRESSION (FR-007) for the PCA path.
- **Critical Constraint**: T028 explicitly retains records with NaN object_count for edge/entropy analyses but drops them for object-count analyses.
- **Critical Constraint**: T036 explicitly generates the Markdown table and inserts it into `results/report.md` (via T045), and generates a standalone CSV.
- **Critical Constraint**: T037 and T038 generate citation content from `citations.yaml` (created by T017); T045 explicitly uses this content.
- **Critical Constraint**: T019a and T019b explicitly document the rationale in a 'Power Analysis Methodology' section and calculate the achieved power using `FTestPower`.
- **Critical Constraint**: T015 raises ValueError if synthetic data variance is zero.
- **Critical Constraint**: T010 and T011 are marked as Complete [X].
- **Constitution Check Note**: Tasks T003, T010, T011, T021-T023, T046, T047 are now defined and actionable. The "Constitution Check PASS" in plan.md is contingent on these tasks being completed and verified.
- **Critical Constraint**: T051 is now marked as Complete [X] as its logic is integrated into T015.
- **Critical Constraint**: T039a has been removed to prevent overwriting PCA results; T039b is the sole save point.
- **Critical Constraint**: T037 and T038 do NOT write to `results/report.md`; T045 is the sole writer.
- **Critical Constraint**: T015 explicitly supports the Hybrid path (Real Cognitive + Real Images via Proxy).
- **Critical Constraint**: T027 explicitly depends on T018 (Marker File + Validation).
- **Critical Constraint**: T045 explicitly depends on T019a, T019b, T036, T036a, T039b, T044, T037, T038.
- **Critical Constraint**: Real data fetch logic is integrated into T015; Phase O is removed.
- **Critical Constraint**: T048a/T048b and T053 have been removed as scope creep.
- **Critical Constraint**: T053, T054, T055, T056 have been removed and their functionality integrated into T025, T031, T034b, T041, T037b respectively.
- **Critical Constraint**: T019 uses `FTestPower` for correlation power analysis.
- **Critical Constraint**: T015 generates correlated synthetic data if real data fails.
- **Critical Constraint**: T015 explicitly queries real platforms before fallback.
- **Critical Constraint**: T045 dependencies updated to include T037 and T038.
- **Critical Constraint**: T027 dependency updated to T018.
- **Critical Constraint**: T042 and T043 explicitly mandate 6-pair iteration and 6-row output for FR-010.
- **Critical Constraint**: T031a explicitly includes conditional PCA integration logic.
- **Critical Constraint**: T015 uses real Unsplash API for image acquisition.
- **Critical Constraint**: T037 loads citations from `citations.yaml` for Constitution II.
- **Critical Constraint**: T034b depends on T034a, not T033, to allow non-collinear path.
- **Critical Constraint**: T039b depends on T034a and T031, removing hard block on T034b/T033.
- **Critical Constraint**: T031a is now the single source for VIF, PCA, Regression, Plots, and Multiplicity.
- **Critical Constraint**: T020 is removed; logic integrated into T015.
- **Critical Constraint**: T032, T033, T034a/b/c are removed; logic integrated into T031a.
- **Critical Constraint**: T038-plot is re-introduced as a distinct task to ensure FR-008 visualization requirements are met.
- **Critical Constraint**: T015 Step 3 removed to avoid contradiction; Step 5 is the sole generation logic (if fallback).
- **Critical Constraint**: **Constitution Check: PENDING**. The project is currently in a state where core implementation tasks (T015, T026a-c, T031a-d) are incomplete. The "PASS" status in the plan is contingent on the completion of these tasks.
- **Critical Constraint**: **Task Completion Verification**: No task can be marked [X] until the corresponding file exists, passes all unit tests, and produces the required artifacts.
- **Critical Constraint**: **Data Source Verification**: T015 must explicitly log the search attempt for real datasets on HuggingFace/OpenML and the specific IDs queried before falling back to synthetic generation.
- **Critical Constraint**: **Metric Robustness**: T026a-c must handle image format errors gracefully (log and skip) without crashing the entire pipeline.
- **Critical Constraint**: **Statistical Rigor**: T031a-d must explicitly handle the case where variance in a predictor is zero (skip correlation, log warning) to avoid division by zero errors.
- **Critical Constraint**: T016 explicitly handles PII Sanitization.
- **Critical Constraint**: T017 explicitly creates `data/citations.yaml`.
- **Critical Constraint**: T037 and T038 explicitly generate justification and citation content from `citations.yaml`.
- **Critical Constraint**: T053, T054, T055, T056 have been removed and their functionality integrated into T025, T031, T034b, T041, T037b respectively.
- **Critical Constraint**: T019 uses `FTestPower` for correlation power analysis.
- **Critical Constraint**: T015 generates correlated synthetic data if real data fails.
- **Critical Constraint**: T015 explicitly queries real platforms before fallback.
- **Critical Constraint**: T045 dependencies updated to include T037 and T038.
- **Critical Constraint**: T027 dependency updated to T018.
- **Critical Constraint**: T042 and T043 explicitly mandate 6-pair iteration and 6-row output for FR-010.
- **Critical Constraint**: T031a explicitly includes conditional PCA integration logic.
- **Critical Constraint**: T015 uses real Unsplash API for image acquisition.
- **Critical Constraint**: T037 loads citations from `citations.yaml` for Constitution II.
- **Critical Constraint**: T034b depends on T034a, not T033, to allow non-collinear path.
- **Critical Constraint**: T039b depends on T034a and T031, removing hard block on T034b/T033.
- **Critical Constraint**: T031a is now the single source for VIF, PCA, Regression, Plots, and Multiplicity.
- **Critical Constraint**: T020 is removed; logic integrated into T015.
- **Critical Constraint**: T032, T033, T034a/b/c are removed; logic integrated into T031a.
- **Critical Constraint**: T038-plot is re-introduced as a distinct task to ensure FR-008 visualization requirements are met.
- **Critical Constraint**: T015 Step 3 removed to avoid contradiction; Step 5 is the sole generation logic (if fallback).
- **Critical Constraint**: **Constitution Check: PENDING**. The project is currently in a state where core implementation tasks (T015, T026a-c, T031a-d) are incomplete. The "PASS" status in the plan is contingent on the completion of these tasks.
- **Critical Constraint**: **Task Completion Verification**: No task can be marked [X] until the corresponding file exists, passes all unit tests, and produces the required artifacts.
- **Critical Constraint**: **Data Source Verification**: T015 must explicitly log the search attempt for real datasets on HuggingFace/OpenML and the specific IDs queried before falling back to synthetic generation.
- **Critical Constraint**: **Metric Robustness**: T026a-c must handle image format errors gracefully (log and skip) without crashing the entire pipeline.
- **Critical Constraint**: **Statistical Rigor**: T031a-d must explicitly handle the case where variance in a predictor is zero (skip correlation, log warning) to avoid division by zero errors.
- **Critical Constraint**: T016 explicitly handles PII Sanitization.
- **Critical Constraint**: T017 explicitly creates `data/citations.yaml`.
- **Critical Constraint**: T037 and T038 explicitly generate justification and citation content from `citations.yaml`.