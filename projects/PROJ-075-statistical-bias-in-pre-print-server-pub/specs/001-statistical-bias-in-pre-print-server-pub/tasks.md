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
- [X] T002 [P] Initialize Python 3.11 project with dependencies: `pandas`, `scipy`, `numpy`, `requests`, `pdfplumber`, `datasets`, `regex`, `rapidfuzz`, `pytest`, `statsmodels`, `pypcurve` in `code/requirements.txt`. **Note**: Use `pypcurve` (or the specific GitHub repo if PyPI is unstable) for p-curve analysis as the standard `pcurve` is R-based.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/.ruff.toml` and `code/.black.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/stats_helpers.py` with:
 - `convert_inequality_to_bounds(inequality_str: str) -> tuple[float, float, str]`: Parses strings like "p < 0.05" into (0.0, 0.05, "inequality")
 - `fit_tobit_model(X: np.ndarray, y: np.ndarray, lower: float, upper: float) -> statsmodels.duration.hazard_regression.TobitReg`: Wrapper using `statsmodels.duration.hazard_regression.TobitReg`.
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
- [ ] T011 [P] [US1] Unit test for PDF parser in `tests/unit/test_extraction.py` (verify parsing of inequalities and effect sizes)
- [ ] T012 [P] [US1] Integration test for 10-pair subset in `tests/integration/test_pipeline_us1.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/01_fetch_and_match.py` to scrape arXiv/bioRxiv metadata (recent years) and query OpenAlex S3 dumps via `datasets.load_dataset` to match pre-prints with DOIs using `code/utils/matching.py`
- [ ] T014 [US1] Implement filtering logic in `code/01_fetch_and_match.py` to exclude case studies, theoretical papers, and pairs with >20% sample size (N) change (FR-003, FR-006). **Explicitly log** exclusion reasons ("methodological shift", "unmatched", "N_change") in a structured CSV column `exclusion_reason` and a dedicated log file `data/raw/exclusion_log.csv` with columns: `preprint_id`, `journal_id`, `reason`, `timestamp`.
- [X] T015 [US1] Implement `code/02_extract_stats.py` to parse full-text PDFs for matched pairs, extracting p-values (exact and inequalities) and effect sizes (Cohen's d, Hedges' g, etc.) using `code/utils/pdf_parser.py`
- [X] T015a [US1] **New**: Implement statistical method extraction in `code/02_extract_stats.py` to identify the primary statistical method (e.g., t-test, ANOVA, regression) used in each paper from the text, storing this in `matched_pairs.csv` to enable FR-003 methodological shift detection.
- [X] T016 [US1] Implement interval-censoring logic in `code/02_extract_stats.py` to record inequalities (e.g., `p < 0.05`) as ranges for general reporting but exclude them from p-curve analysis (FR-002)
- [X] T017 [US1] Generate `data/processed/matched_pairs.csv` containing `MatchedPaperPair` entities with extracted metrics, ensuring 1:1 linkage and flagging pairs with missing data
- [ ] T018 [US1] Implement validation to ensure `matched_pairs.csv` contains at least one p-value and one effect size for both pre-print and journal versions for included rows

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Distributional and Magnitude Analysis (Priority: P2)

**Goal**: Perform p-curve analysis, density ratio tests, and paired t-tests on effect sizes to quantify the shift between pre-print and journal versions.

**Independent Test**: Run the analysis module on a synthetic dataset with known differences and verify the output correctly flags the distribution shift and calculates the expected mean difference in effect size with a confidence interval excluding zero.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for p-curve analysis in `tests/unit/test_analysis_pcurve.py`
- [ ] T020 [P] [US2] Unit test for paired t-test/Wilcoxon logic in `tests/unit/test_analysis_magnitude.py`

### Implementation for User Story 2

- [X] T021a [US2] **New**: Implement explicit exclusion filter in `code/03_analysis.py` to assert and remove all p-values flagged as inequalities before any p-curve analysis runs, ensuring FR-002 compliance. <!-- FAILED: unspecified -->
- [X] T021 [US2] Implement `code/03_analysis.py` p-curve analysis module: Run p-curve analysis on the filtered pre-print p-value distribution and the filtered journal p-value distribution separately using `pypcurve`.
- [X] T021b [US2] **New**: Implement p-curve estimation logic in `code/03_analysis.py` to calculate **power** and **p-hacking prevalence** estimates for the pre-print subset and the journal subset independently using `pypcurve`.
- [X] T022 [US2] Implement density ratio estimation in `code/03_analysis.py` to compare p-value distributions and calculate the magnitude of the density ratio at p=0.05 (FR-004) <!-- FAILED: unspecified -->
- [ ] T022b [US2] **Compare p-curve derived metrics**: Use `pypcurve` to estimate power and p-hacking prevalence for both pre-print and journal versions. Calculate the difference between these estimates and record the result in `data/results/analysis_results.json`. **Method**: Use `pypcurve.estimate_power()` and `pypcurve.estimate_p_hacking()` with permutation testing if available.
- [ ] T022c [US2] **Implement p-curve result comparison logic**: Explicitly calculate the difference in estimated power and p-hacking prevalence between pre-print and journal versions. Output these differences as the primary "p-curve result" metric in `data/results/analysis_results.json` to satisfy FR-004's requirement to compare *results* rather than raw ratios.
- [X] T023a [US2] **New**: Implement data classification logic in `code/03_analysis.py` to tag each row in `matched_pairs.csv` as 'censored' or 'non-censored' based on the presence of interval-censored effect size data, creating a unified routing step.
- [ ] T023 [US2] **Implement standard paired effect-size analysis (non-censored only)**: For pairs tagged as 'non-censored', perform a paired t-test (or Wilcoxon if normality fails) on the difference ($\Delta$ES). **MUST NOT** include pairs with interval-censored data. Exclude pairs where N changes >20% or p-values are identical (FR-004).
- [ ] T023b [US2] **Implement censored effect-size analysis (Tobit)**: For pairs tagged as 'censored', implement a Tobit regression model (using `code/utils/stats_helpers.py`'s `fit_tobit_model`) to estimate the difference ($\Delta$ES) while accounting for interval censoring. Exclude pairs where N changes >20%.
- [ ] T024 [US2] Implement stratification logic in `code/03_analysis.py` to output results by field (e.g., Quantitative Biology) for domain-specific bias detection
- [ ] T025 [US2] Generate `data/results/analysis_results.json` containing `AnalysisResult` entities with test statistics, p-values, and interpretations
- [ ] T026a [US2] **New**: Implement null distribution generation in `code/03_analysis.py` to create a baseline distribution of density ratios via permutation testing (shuffling venue labels) as required by SC-002.
- [ ] T026 [US2] Implement validation to ensure the observed density ratio falls outside the confidence interval of the null distribution (per SC-002) using the data generated in T026a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Robustness Reporting (Priority: P3)

**Goal**: Perform a sensitivity analysis on the p-value inclusion threshold (0.01, 0.05, 0.1) and report how the detected bias rates change.

**Independent Test**: Run the sensitivity module on a fixed dataset and verify that the output report contains three distinct sections with calculated bias rates that vary as expected.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement the sensitivity analysis module to sweep thresholds across a range of values.
- [ ] T029 [US3] Calculate the "significance flip rate" (proportion of pairs where p crosses the threshold in opposite directions) for each threshold (FR-005)
- [ ] T030 [US3] Generate a sensitivity report in `data/results/sensitivity_report.md` explicitly stating the variation in bias rates across thresholds
- [ ] T031 [US3] Verify that the direction of the bias remains consistent across all swept thresholds (SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Update `docs/quickstart.md` with instructions to run the full pipeline and reproduce results
- [ ] T033 Code cleanup: Ensure all random seeds are pinned in `code/` for reproducibility
- [ ] T034 [P] Run `pytest` on full test suite and fix any regressions
- [ ] T035 Update `state/projects/PROJ-075-statistical-bias-in-pre-print-server-pub.yaml` with `updated_at` timestamp and artifact hashes
- [ ] T036 Validate `contracts/` schemas (`matched_pairs.schema.yaml`, etc.) against generated data files

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