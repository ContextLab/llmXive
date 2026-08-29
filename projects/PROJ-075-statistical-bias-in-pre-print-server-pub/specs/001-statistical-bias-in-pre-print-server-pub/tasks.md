# Tasks: Statistical Bias in Pre-Print Server Publication Trends

**Input**: Design documents from `/specs/001-statistical-bias-in-pre-print-server-pub/`
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create `code/` directory structure and `__init__.py`
- [ ] T001b [P] Create `data/` directory structure (`raw/`, `processed/`, `results/`) and `data/.gitkeep`
- [X] T001c [P] Create `tests/` directory structure (`unit/`, `integration/`) and `tests/__init__.py`
- [X] T002 [P] Initialize Python project with dependencies: `pandas`, `scipy`, `numpy`, `requests`, `pdfplumber`, `datasets`, `regex`, `rapidfuzz`, `pytest`, `statsmodels`, `pypcurve==1.0.0` in `code/requirements.txt`. **Note**: `pypcurve` is pinned to version 1.0.0 to ensure deterministic builds.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/.ruff.toml` and `code/.black.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/stats_helpers.py` with:
 - `convert_inequality_to_bounds(inequality_str: str) -> tuple[float, float, str]`: Parses strings like "p < 0.05" into (0.0, 0.05, "inequality")
 - `fit_tobit_model(X: np.ndarray, y: np.ndarray, lower: float, upper: float) -> statsmodels.duration.hazard_regression.TobitReg`: Wrapper using `statsmodels.duration.hazard_regression.TobitReg`. **Note**: If `TobitReg` is not found in this module (API mismatch), attempt import from `statsmodels.regression.linear_model` or use `statsmodels.censored` if available.
 - **Input**: `X` (numpy array of shape (n, p)), `y` (numpy array of shape (n,)), `lower` (float), `upper` (float).
 - **Logic**: Convert interval-censored data into left/right censoring flags and bounds compatible with `TobitReg`.
 - **Output**: Fitted `TobitReg` model instance.
- [X] T005 [P] Implement `code/utils/matching.py` with fuzzy matching logic using `rapidfuzz` for title/author similarity scoring
- [X] T006 [P] Implement `code/utils/pdf_parser.py` with robust regex/NLP extraction logic for p-values and effect sizes, including handling of LaTeX formatting
- [X] T008 [P] Setup logging configuration in `code/main.py` to track extraction failures and unmatched pairs
- [X] T009 [P] Implement `code/main.py` orchestration skeleton:
 - `fetch_step()` to handle data acquisition
 - `match_step()` to handle pairing logic
 - `extract_and_analyze_step()` to handle extraction and analysis

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Matched Dataset Construction and Extraction (Priority: P1) 🎯 MVP

**Goal**: Automatically identify pairs of pre-print and peer-reviewed journal articles, extract their reported p-values and effect sizes, and store them in a structured dataset.

**Independent Test**: Run the scraping and matching script on a small, known subset of pre-print/journal pairs and verify the output CSV contains a corresponding number of rows with non-null p-value and effect-size fields for both versions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for matching logic in `tests/unit/test_matching.py` (verify fuzzy match thresholds)
- [X] T011 [P] [US1] Unit test for PDF parser in `tests/unit/test_extraction.py`. **Specifics**: Implement `test_parse_inequality` (asserts "p < 0.05" -> (0.0, 0.05, "inequality")) and `test_extract_cohen_d` (asserts extraction of "d = 0.5 [0.2, 0.8]" -> value=0.5, ci_lower=0.2, ci_upper=0.8).
- [X] T012 [P] [US1] Integration test for -pair subset in `tests/integration/test_pipeline_us1.py`. **Specifics**: Use fixture `tests/fixtures/us1_subset.csv`. Assert `row_count == 10` AND `all(p_value is not null)`.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/01_fetch_and_match.py` to scrape arXiv/bioRxiv metadata (recent years) and query OpenAlex S3 dumps via `datasets.load_dataset` to match pre-prints with DOIs using `code/utils/matching.py`
- [X] T013b [US1] **Data Acquisition & Match Rate Validation**: Implement logic in `code/01_fetch_and_match.py` to:
 1. Calculate the required initial query size using Cochran's formula for proportions: `n = (Z^2 * p * (1-p)) / E^2`, where Z=1.96 (95% CI), p=0.6 (target match rate), E=0.05 (margin of error).
 2. Execute the fetch/match process.
 3. Calculate the final match rate.
 4. Log the match rate and any deviation from the target in `data/raw/acquisition_validation.log`.
 5. **Note**: If the match rate is < 60%, log a warning but DO NOT fail the pipeline; this is a planning target, not a functional gate.
- [X] T014 [US1] **Filtering Logic**: Implement filtering logic in `code/01_fetch_and_match.py` to exclude case studies, theoretical papers, and pairs with >20% sample size (N) change (FR-003, FR-006). **Dependency**: This task MUST run AFTER T013 (to access matched pairs) and T013b (to access validation metrics). **Explicitly log** exclusion reasons ("methodological shift", "unmatched", "N_change", "unsupported_type") in a structured CSV column `exclusion_reason` and a dedicated log file `data/raw/exclusion_log.csv` with columns: `preprint_id`, `journal_id`, `reason`, `timestamp`. This task must also handle logging extraction failures for unsupported statistical types as per FR-002. **Verification**: Add an assertion step to verify the final `matched_pairs.csv` contains ZERO rows matching the excluded criteria.
- [X] T015 [US1] Implement `code/02_extract_stats.py` to parse full-text PDFs for matched pairs, extracting p-values (exact and inequalities) and effect sizes (Cohen's d, Hedges' g, etc.) using `code/utils/pdf_parser.py`
- [X] T015a [US1] Implement statistical method extraction in `code/02_extract_stats.py` to identify the primary statistical method (e.g., t-test, ANOVA, regression) used in each paper from the text, storing this in `matched_pairs.csv` to enable FR-003 methodological shift detection.
- [X] T016 [US1] Implement interval-censoring logic in `code/02_extract_stats.py` to record inequalities (e.g., `p < 0.05`) as ranges for general reporting but tag them as `censored: true` in the dataset. These tagged entries must be excluded from p-curve analysis (FR-002).
- [X] T017 [US1] **Generate Matched Dataset**: Generate `data/processed/matched_pairs.csv` containing `MatchedPaperPair` entities with extracted metrics, ensuring 1:1 linkage and flagging pairs with missing data. **Dependency**: This task MUST run AFTER T014, T015, and T016 to consume the `exclusion_log.csv` and ensure only valid pairs with extracted metrics are included.
- [X] T018 [US1] Implement validation in `code/02_extract_stats.py` to assert that `matched_pairs.csv` contains at least one p-value and one effect size for both pre-print and journal versions for included rows. The pipeline MUST fail if this validation is not met.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Distributional and Magnitude Analysis (Priority: P2)

**Goal**: Perform p-curve analysis, density ratio tests, and paired t-tests on effect sizes to quantify the shift between pre-print and journal versions.

**Independent Test**: Run the analysis module on a synthetic dataset with known differences and verify the output correctly flags the distribution shift and calculates the expected mean difference in effect size with a confidence interval excluding zero.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for p-curve analysis in `tests/unit/test_analysis_pcurve.py`. **Specifics**: Implement `test_pcurve_power_estimation` using a synthetic dataset with known power=0.8. Assert the estimated power is within 0.1 of the ground truth.
- [X] T020 [P] [US2] Unit test for paired t-test/Wilcoxon logic in `tests/unit/test_analysis_magnitude.py`

### Implementation for User Story 2

- [X] T021a [US2] Implement explicit exclusion filter in `code/03_analysis.py` to assert and remove all p-values flagged as `censored: true` (from T016) before any p-curve analysis runs, ensuring FR-002 compliance. **Note**: This is a sequential step, not parallel.
- [X] T021 [US2] Implement `code/03_analysis.py` p-curve analysis module: Run p-curve analysis on the filtered pre-print p-value distribution and the filtered journal p-value distribution separately using `pypcurve`.
- [X] T021b [US2] Implement p-curve estimation logic in `code/03_analysis.py` to calculate **power** and **p-hacking prevalence** estimates for the pre-print subset and the journal subset independently using `pypcurve`. **Verification**: If the input set is empty after filtering (T021a), log a warning "p-curve analysis skipped: empty dataset after censored data removal" and skip the calculation for this subset rather than raising an error.
- [X] T022 [US2] **Calculate Observed Density Ratio**: Implement density ratio estimation in `code/03_analysis.py` to compare p-value distributions and calculate the magnitude of the density ratio at p=0.05 (FR-004). **Output**: Store the observed density ratio value in memory for use in T026a and T026.
- [X] T022b [US2] **Compare p-curve derived metrics**: Use `pypcurve` to estimate power and p-hacking prevalence for both pre-print and journal versions. Calculate the difference between these estimates and record the result in `data/results/analysis_results.json`. **Method**: Use `pypcurve.estimate_power()` and `pypcurve.estimate_p_hacking()` with permutation testing if available.
- [X] T022c [US2] **Implement p-curve result comparison logic (Calculation)**: Explicitly calculate the difference in estimated power and p-hacking prevalence between pre-print and journal versions. Store these delta values in memory for the next step.
- [X] T022d [US2] **Implement p-curve result comparison logic (Output)**: Format the delta values from T022c into `data/results/analysis_results.json` with the specific schema: `{"p_curve_power_diff": <float>, "p_curve_p_hacking_diff": <float>}`.
- [X] T023a [US2] **Classify Data for Effect Size Analysis**: Implement data classification logic in `code/03_analysis.py` to tag each row in `matched_pairs.csv` as 'censored' or 'non-censored' based on the presence of interval-censored effect size data, creating a unified routing step.
- [X] T023 [US2] **Implement standard paired effect-size analysis (non-censored only)**: For pairs tagged as 'non-censored', perform a paired t-test (or Wilcoxon if normality fails) on the difference ($\Delta$ES). **MUST NOT** include pairs with interval-censored data. Exclude pairs where N changes >20% or p-values are identical (within rounding error) (FR-004). **Dependency**: This task runs sequentially after T023a classification.
- [X] T023b [US2] **Implement censored effect-size analysis (Tobit)**: For pairs tagged as 'censored', implement a Tobit regression model (using `code/utils/stats_helpers.py`'s `fit_tobit_model`) to estimate the difference ($\Delta$ES) while accounting for interval-censored data. **Dependency**: This task MUST run AFTER T023a (classification). **Verification**: Check if the Tobit model converged. If not, raise a `RuntimeError` with message "Tobit regression failed to converge for censored effect sizes". Record results in `data/results/analysis_results.json`.
- [X] T024 [US2] Implement stratification logic in `code/03_analysis.py` to output results by field (e.g., Quantitative Biology) for domain-specific bias detection. Results must be written to `data/results/analysis_results.json` with a `field` key.
- [X] T025 [US2] Generate `data/results/analysis_results.json` containing `AnalysisResult` entities with test statistics, p-values, and interpretations
- [X] T026a [US2] **Generate Null Distribution**: In `code/03_analysis.py`, create a baseline distribution of density ratios via permutation testing (shuffling venue labels) as required by SC-002. **Permutation Count**: Perform a sufficient number of permutations to ensure statistical validity. **Dependency**: This task MUST run AFTER T022 to use the observed data parameters to define the permutation space. Store the null distribution in `data/results/null_distribution.json`.
- [X] T026 [US2] **Validate Against Null**: Validate that the observed density ratio (from T022) falls outside the confidence interval of the null distribution generated in T026a. **Logic**: Assert `observed_ratio < ci_lower OR observed_ratio > ci_upper`. **Dependency**: This task MUST run AFTER T022 and T026a. **Output Format**: Record the validation result in `data/results/analysis_results.json` with fields: `{"density_ratio_validation": {"observed": <float>, "ci_lower": <float>, "ci_upper": <float>, "passed": <bool>}}`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Robustness Reporting (Priority: P3)

**Goal**: Perform a sensitivity analysis on the p-value inclusion threshold (ranging from stringent to lenient levels) and report how the detected bias rates change.

**Independent Test**: Run the sensitivity module on a fixed dataset and verify that the output report contains three distinct sections with calculated bias rates that vary as expected.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`. **Specifics**: Test thresholds including conventional significance levels, as well as other relevant significance levels. Assert output structure matches `{"threshold": <float>, "flip_rate": <float>}` for each.

### Implementation for User Story 3

- [X] T028 [US3] Implement the sensitivity analysis module in the analysis code to sweep thresholds across a range of values.
- [X] T029 [US3] Calculate the "significance flip rate" (proportion of pairs where p crosses the threshold in opposite directions) for each threshold (FR-005)
- [X] T030 [US3] Generate a sensitivity report in `data/results/sensitivity_report.md` explicitly stating the variation in bias rates across thresholds
- [X] T031 [US3] Verify that the direction of the bias remains consistent across all swept thresholds (SC-004). **Logging**: Log the actual direction (positive/negative) for each threshold in `data/results/sensitivity_report.md` (e.g., "Threshold 0.01: Bias Direction = Positive", "Threshold 0.05: Bias Direction = Positive").

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Update `docs/quickstart.md` with instructions to run the full pipeline and reproduce results
- [X] T033 Code cleanup: Ensure all random seeds are pinned in `code/` for reproducibility
- [ ] T034 [P] Run `pytest` on full test suite and fix any regressions
- [X] T035 [Polish] **Artifact Hashing & State Update**: Implement `code/utils/hashing.py` to generate SHA-256 hashes for `matched_pairs.csv` and `analysis_results.json`. Update `state/projects/PROJ-075-statistical-bias-in-pre-print-server-pub.yaml` automatically upon successful pipeline completion. **Specifics**: Update the key path `state.projects.PROJ-075-statistical-bias-in-pre-print-server-pub.artifact_hashes` and `state.projects.PROJ-075-statistical-bias-in-pre-print-server-pub.updated_at`.
- [X] T036 Validate `contracts/` schemas (`matched_pairs.schema.yaml`, etc.) against generated data files

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on `matched_pairs.csv` from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on analysis results from US2

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
Task: "Unit test for matching logic in tests/unit/test_matching.py"
Task: "Unit test for PDF parser in tests/unit/test_extraction.py"

# Launch all models for User Story 1 together:
Task: "Implement code/01_fetch_and_match.py"
Task: "Implement code/02_extract_stats.py"
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

- [X] T037 [P] [US1] **Data Source Verification**: Implement `code/01_fetch_and_match.py` to use `datasets.load_dataset("openalex")` with explicit `split="works"` and filter for DOIs matching the arXiv/bioRxiv prefixes. Add a strict `try/except` block that raises a `RuntimeError` with message "Data source load failed: OpenAlex dataset unavailable" if the dataset load fails or returns zero matches, ensuring no synthetic fallback occurs (Constitution Rule: "The loader must FAIL LOUDLY").
- [X] T038 [P] [US1] **Streaming Implementation**: Refactor `code/_fetch_and_match.py` to use `datasets.load_dataset(..., streaming=True)` for the OpenAlex dump to handle large-scale data within the ~GB RAM limit, accumulating matches in chunks and writing to `data/processed/matched_pairs.csv` incrementally.
- [X] T039 [P] [US2] **P-Curve Library Validation**: Add a pre-run check in `code/03_analysis.py` to verify `pypcurve` installation and version compatibility; if the library is missing or incompatible, the script must exit with a clear error message rather than attempting a fallback to a manual implementation (Constitution Rule: "Fix the code, not the test").
- [X] T040 [P] [US3] **Sensitivity Threshold Documentation**: Update `data/results/sensitivity_report.md` to explicitly cite the justification for thresholds {0.05, 0.1} referencing the community standard assumption in `spec.md` and include a plot of the flip-rate curve across the swept range.
- [X] T041 [P] [Polish] **Artifact Hashing**: Implement `code/utils/hashing.py` to generate SHA-256 hashes for `matched_pairs.csv` and `analysis_results.json` and update `state/projects/PROJ-075-statistical-bias-in-pre-print-server-pub.yaml` automatically upon successful pipeline completion. **Specifics**: Update the key path `state.projects.PROJ-075-statistical-bias-in-pre-print-server-pub.artifact_hashes`.
- [ ] T042 [P] [US2] **Robustness Check for Methodological Shift**: Implement a validation task in `code/03_analysis.py` to explicitly verify that pairs flagged with "methodological shift" in `exclusion_log.csv` are indeed excluded from the final effect-size difference calculation, ensuring FR-003 compliance. Log the count of excluded pairs and the specific methods that shifted.
- [ ] T043 [P] [US1] **Extraction Failure Audit**: Add a post-extraction audit task in `code/02_extract_stats.py` to generate a summary report of all `extraction_failures` (unsupported statistical types) logged in `data/raw/exclusion_log.csv`, categorizing them by statistical type (e.g., "odds ratio", "risk ratio") to identify systematic parsing gaps.