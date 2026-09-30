# Tasks: Evaluating the Impact of Code Generation on Code Review Quality Using LLMs

**Input**: Design documents from `/specs/001-evaluating-llm-code-review-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [X] T001a Create project directories: `code/`, `code/data/`, `code/analysis/`, `code/audit/`, `code/utils/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/`, `reports/figures/` AND create `__init__.py` files at: `code/__init__.py`, `code/data/__init__.py`, `code/analysis/__init__.py`, `code/audit/__init__.py`, `code/utils/__init__.py`, `data/raw/__init__.py`, `data/processed/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`, `reports/figures/__init__.py`.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` pinning `requests`, `pandas`, `scipy`, `networkx`, `matplotlib`, `seaborn`, `pyyaml`, `statsmodels`, `pytest`, `pycodestyle`
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools: Create `ruff.toml` and `black.toml` (or `pyproject.toml` sections) with project-specific settings to ensure reproducibility.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/utils/seeds.py` to manage random seeds for all sampling and statistical resampling
- [X] T005 Create `code/utils/config.py` defining repo list (`psf/requests`, `microsoft/vscode`, `numpy/numpy`), thresholds, and API settings
- [X] T006 [P] Implement logging infrastructure in `code/utils/logging.py` with file rotation for `data/` and `reports/`
- [X] T007 Create `code/data/fetch_github.py` skeleton with batch processing structure and exponential backoff logic (limited number of retries)
- [X] T008 Implement data checksumming utility in `code/utils/checksum.py` to generate SHA-256 for raw JSON artifacts
- [X] T009 Create `code/audit/manual_validation.py` skeleton for the audit sample size rule (`max(minimum_threshold, ceil(0.10 * N_LLM))`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and LLM Classification (Priority: P1) 🎯 MVP

**Goal**: Automatically download PRs from prioritized repos and classify them as `llm` or `human` based on signatures and secondary detectors.

**Independent Test**: Run `code/data/fetch_github.py` and `code/data/classify_prs.py` against a static snapshot or live API; verify output CSV has a sufficient number of rows (or all available) with valid `source_type`, `confidence_score`, and `detector_score` columns.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010a [P] [US1] Unit test `test_copilot_signature_match` in `tests/unit/test_classification.py`: assert `classify_prs.identify_copilot(user="copilot-bot") == "llm"`.
- [X] T010b [P] [US1] Unit test `test_infrastructure_bot_exclusion` in `tests/unit/test_classification.py`: assert `classify_prs.classify_pr(user="dependabot") == "human"`.
- [X] T010c [P] [US1] Unit test `test_ambiguous_message_confidence` in `tests/unit/test_classification.py`: assert `classify_prs.calculate_confidence(message="Fix typo") < 0.6`.
- [X] T011a [P] [US1] Unit test `test_entropy_calculation` in `tests/unit/test_detection.py`: assert `compute_entropy(code="import random; print(random.random())") > 0.0`.
- [X] T011b [P] [US1] Unit test `test_ngram_anomaly_score` in `tests/unit/test_detection.py`: assert `detect_ngram_anomaly(code="def func(): pass") == True`.
- [X] T012 [P] [US1] Integration test for GitHub API rate-limit handling (backoff) in `tests/integration/test_fetch_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/fetch_github.py` to fetch up to 200 PRs from prioritized list, handling pagination, API backoff, and saving raw JSON payloads to `data/raw/` with SHA-256 checksums (Constitution Principle III)
- [X] T014 [US1] Implement `code/data/classify_prs.py` primary logic: label `llm` or `human` based on commit message/bot signatures; **MUST** populate `confidence_score` (float) for **every** PR (normalized scale) derived from the signature match logic in classify_prs.py; flag ambiguous cases (confidence < 0.6) by adding a 'flagged' boolean column
- [X] T015 [US1] Implement `code/data/classify_prs.py` secondary detector: compute code entropy/n-gram anomaly scores on PR diffs to validate `llm` labels (FR-007) and output `detector_score`
- [X] T017 [US1] Create `code/data/save_labeled_dataset.py` to output `data/processed/prs_labeled.csv` with `source_type`, `confidence_score`, `flagged`, `detector_score`, and metadata. **Output Schema**: `pr_id` (int), `source_type` (str), `confidence_score` (float), `flagged` (bool), `detector_score` (float). **Dependencies**: T013, T014, T015.
- [X] T018 [US1] Implement fallback logic in `code/data/fetch_github.py` to automatically switch to next repo if `llm` count < 10 in current repo
- [X] T019a [US1] Implement `code/audit/manual_validation.py` logic to select a stratified sample of a minimum size that scales with the total LLM dataset size, execute human-judgment checklist, and log results to `data/audit/manual_audit_results.json`. **Output Schema**: `{"pr_id": int, "human_label": str, "confidence": float}`. **Dependencies**: T017.
- [X] T019b [US1] [SC-004] Implement error rate calculation logic in `code/audit/manual_validation.py` to compare manual results against automated labels using **Human Expert Judgment as ground truth** and **secondary detector score as ground truth** per SC-004. Calculate the labeling error rate, write the result to `data/audit/error_rate.json`, and raise a `ValueError` with message "Error rate {rate} exceeds threshold" if the rate exceeds a predefined threshold. **Dependencies**: T019a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Metric Extraction and Statistical Comparison (Priority: P2)

**Goal**: Calculate review metrics and perform statistical tests (t-tests PRIMARY per FR-004, Mann-Whitney U sensitivity) to compare `llm` vs `human` groups.

**Independent Test**: Run analysis on `data/processed/prs_labeled.csv` and `data/processed/complexity_scores.csv` and verify `data/processed/results.json` contains t-statistics, p-values, and effect sizes for comment density and time-to-merge.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020a [P] [US2] Unit test `test_comment_count_calculation` in `tests/unit/test_metrics.py`
- [X] T020b [P] [US2] Unit test `test_time_to_merge_calculation` in `tests/unit/test_metrics.py`
- [X] T020c [P] [US2] Unit test `test_review_cycles_calculation` in `tests/unit/test_metrics.py`
- [X] T021a [P] [US2] Unit test `test_mann_whitney_u_implementation` in `tests/unit/test_statistical_tests.py`: asserts p-value and statistic output
- [X] T021b [P] [US2] Unit test `test_independent_t_test_implementation` in `tests/unit/test_statistical_tests.py`: asserts p-value, t-statistic, and effect size output

### Implementation for User Story 2

- [X] T033 [US1] [US2] Create `code/analysis/save_complexity_scores.py` to output `data/processed/complexity_scores.csv` with `pr_id` (int) and `complexity_score` (float) columns. **MUST** join on `pr_id` from `data/processed/prs_labeled.csv` (produced by T017). This task is a prerequisite for T022. **Dependencies**: T017.
- [X] T022 [US2] [FR-003] [FR-004] [SC-001] [SC-002] Implement `code/data/extract_metrics.py` to calculate `comment_count`, `time_to_merge_minutes`, `review_cycles` for every PR from `data/processed/prs_labeled.csv` and **Join `data/processed/prs_labeled.csv` and `data/processed/complexity_scores.csv` on `pr_id`** (produced by T033) to include actual `complexity_score`. **Requires T033 completion.** Output schema: `pr_id` (int), `comment_count` (int), `time_to_merge_minutes` (float), `review_cycles` (int), `complexity_score` (float).
- [X] T023 [US2] [FR-003] Save processed metrics to `data/processed/prs_metrics.csv` including `pr_id` (int), `comment_count` (int), `time_to_merge_minutes` (float), `review_cycles` (int), and `complexity_score` (float) columns.
- [X] T024a [US2] [FR-004] [SC-001] [SC-002] Implement `code/analysis/statistical_tests.py` to perform **independent two-sample t-tests as PRIMARY analysis** (per FR-004) comparing `llm` vs `human` groups for comment density and time-to-merge, outputting p-values, t-statistics, and effect sizes (Cohen's d). **Mann-Whitney U tests are sensitivity analysis.**
- [X] T024b [US2] [FR-008] Implement **Mann-Whitney U tests as sensitivity analysis** in `code/analysis/statistical_tests.py` to verify robustness of t-test results.
- [X] T025 [US2] [FR-004] [SC-001] [SC-002] Implement calculation of effect sizes (Cohen's d) and significance determination (α = 0.05) in `code/analysis/statistical_tests.py`. **MUST** include a verification step to confirm that the chosen α aligns with the "no multiple-comparison correction" assumption (from Spec Assumptions) before execution.
- [X] T026 [US2] [FR-008] Implement `code/analysis/sensitivity_analysis.py` to re-run tests using only the secondary detector cohort (FR-008)
- [X] T027 [US2] [FR-004] [FR-003] Create `code/analysis/generate_results_report.py` to aggregate findings into `data/processed/results.json` with all statistical outputs. **JSON Schema**: `{ "comment_density": { "p_value": float, "t_statistic": float, "effect_size": float, "is_significant": bool }, "time_to_merge": {... }, "complexity_correlation": float }`. **MUST** read correlation coefficient from `data/processed/correlation_results.json` (produced by T035).
- [X] T028 [US2] [FR-004] [FR-003] Implement logic in `code/analysis/generate_results_report.py` to read the error rate from `data/audit/error_rate.json` (produced by T019b) and write a `gate_status` flag to `data/processed/gate_status.json`. **Logic**: If error rate > 0.05, set status to "blocked". If N_LLM < 10, set status to "exploratory". **Do not block Phase 4 execution, only final aggregation.** **JSON Schema for gate_status**: `{ "status": "blocked" | "passed" | "exploratory" }`. **Requires T019b completion.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Complexity Scoring and Visualization (Priority: P3)

**Goal**: Score code complexity (already computed in Phase 3) and generate visualizations (boxplots, histograms) to control for confounding variables.

**Independent Test**: Run complexity and visualization scripts on processed data; verify `reports/figures/` contains PDF with boxplots and `data/processed/prs_metrics.csv` includes `complexity_score`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029a [P] [US3] Unit test `test_cyclomatic_complexity_calculation` in `tests/unit/test_complexity.py`
- [X] T029b [P] [US3] Unit test `test_lines_of_code_calculation` in `tests/unit/test_complexity.py`
- [X] T030a [P] [US3] Integration test `test_boxplot_generation` in `tests/integration/test_visualizations.py`: assert `os.path.exists("reports/figures/boxplots.pdf")` and verify_plot_types("reports/figures/boxplots.pdf", ["boxplot"])
- [X] T030b [P] [US3] Integration test `test_histogram_generation` in `tests/integration/test_visualizations.py`: assert `os.path.exists("reports/figures/histograms.pdf")` and verify_plot_types("reports/figures/histograms.pdf", ["histogram"])

### Implementation for User Story 3

- [X] T031 [US1] [US3] Implement `code/analysis/complexity.py` to compute Cyclomatic Complexity and Lines of Code for PR diffs.
- [X] T032 [US1] [US3] Implement fallback logic in `code/analysis/complexity.py` to use standard metrics if memory usage > 6GB (Assumption 3) **MUST include a psutil watchdog hook** to trigger fallback automatically.
- [X] T034 [US3] [FR-005] [FR-006] Implement `code/analysis/visualizations.py` to generate side-by-side boxplots for comment density and time-to-merge
- [X] T035 [US3] [FR-005] [FR-006] [SC-003] Implement correlation analysis in `code/analysis/visualizations.py` to measure relationship between complexity and review metrics (SC-003). **MUST** verify usage of complexity scores in regression/correlation analysis to ensure they are used to control for confounding variables as required by SC-003. Output `data/processed/correlation_results.json`.
- [X] T036 [US3] [FR-005] [FR-006] Generate final report PDF in `reports/figures/final_report.pdf` containing all required plots (boxplots for comment density and time-to-merge, histograms) and correlation coefficients. **MUST** include sections: Executive Summary, Methodology, Results (with plots), Discussion, Limitations. **Depends on T028.**
- [X] T037 [US3] [FR-005] [FR-006] Implement `code/analysis/generate_final_report.py` to compile all findings, limitations, and visualizations into a research summary; **MUST** read `data/processed/gate_status.json` (from T028). **Logic**: If status is "blocked", raise ValueError("Pipeline blocked: error rate exceeded threshold"). If status is "exploratory", include a note in the report but do not abort. **Depends on T028.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Update `README.md`: Add installation instructions, usage examples, and a data flow diagram.
- [X] T039 [P] Update API documentation in `docs/`: Document all modules in `code/` with docstrings and examples.
- [X] T040 [P] Refactor `code/data/fetch_github.py`: Use a single session object; extract common error handling logic into `code/utils/errors.py`.
- [X] T041 [P] Optimize `code/analysis/complexity.py`: Process diffs in chunks; implement parallel processing for metric extraction in `code/data/extract_metrics.py`.
- [X] T042 [P] Implement PII filter in `code/utils/pii_scan.py`: Add a function that masks email addresses and usernames in logs; verify no PII in `data/` artifacts via a scan script; output `data/audit/pii_scan_results.txt`.
- [X] T043 [P] Run `quickstart.md` validation and verify all artifacts are checksummed. **Command**: `python code/quickstart_runner.py`. **Outcome**: Verify all artifacts in `data/` have corresponding checksums in `state/`.

---

## Phase O: Review Resolution & Robustness (Revision Pass)

**Purpose**: Address specific reviewer concerns regarding data sourcing, statistical rigor, and edge-case handling identified in the analysis phase.

- [ ] T044 [US1] [FR-001] Implement **strict fail-on-error** logic in `code/data/fetch_github.py`: Remove any implicit fallbacks to synthetic data; if the GitHub API returns a 403 (rate limit) after max retries, or a 404 (repo not found), the script MUST raise a `RuntimeError` with a clear message indicating the specific failure point and the next repo in the fallback list. **Rationale**: Ensures compliance with the "Fail Loudly" rule and prevents silent fabrication of data.
- [ ] T045 [US1] [FR-001] Implement **streaming/chunked processing** for large PR diffs in `code/analysis/complexity.py` (T031): If a single PR diff exceeds 1MB, the complexity scorer must process the diff in chunks (e.g., 100KB blocks) to stay within the 7GB RAM limit without loading the entire payload into memory at once. **Rationale**: Addresses the "Large real datasets" constraint and prevents OOM errors on the CI runner.
- [ ] T046 [US2] [FR-004] [SC-001] Add **normality assumption check** in `code/analysis/statistical_tests.py` (T024a): Before running the primary t-test, perform a Shapiro-Wilk test; if the p-value < 0.05 (indicating non-normality), automatically log a warning and execute the Mann-Whitney U test as a robustness check, reporting both results in `data/processed/results.json`. **Rationale**: Ensures statistical validity given the small sample size assumption and aligns with the plan's mention of non-normality.
- [ ] T047 [US2] [FR-008] Implement **effect size interpretation** in `code/analysis/generate_results_report.py` (T027): Add a helper function to classify the magnitude of Cohen's d (e.g., small < 0.2, medium < 0.5, large > 0.8) and append this qualitative interpretation to the JSON output. **Rationale**: Provides necessary context for the "Measurable Outcomes" (SC-001, SC-002) beyond just p-values.
- [ ] T048 [US1] [FR-002] Implement **confidence_score calibration** in `code/data/classify_prs.py` (T014): Ensure the `confidence_score` is derived from a weighted combination of signature match strength AND secondary detector score, not just a binary flag, to provide a continuous metric for the manual audit. **Rationale**: Aligns with the requirement for a `confidence_score` column and improves the granularity of the manual audit (SC-004).
- [ ] T049 [US3] [FR-006] Implement **publication-quality styling** in `code/analysis/visualizations.py` (T034): Configure `seaborn`/`matplotlib` to use a consistent font, color palette, and axis labels that match the project's research theme, and ensure the PDF output is high-resolution (300 DPI) for potential inclusion in a paper. **Rationale**: Enhances the "Polish" phase and ensures the visual artifacts are suitable for the final research report.
- [ ] T050 [US1] [FR-007] Implement **deterministic seed** for the secondary statistical detector in `code/data/classify_prs.py` (T015): Explicitly set the random seed for any n-gram or entropy sampling logic to ensure the `detector_score` is reproducible across runs. **Rationale**: Satisfies the "Reproducibility" principle (Principle I) and ensures the secondary detector is not stochastic.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review Resolution (Phase O)**: Can run in parallel with Polish; depends on US1 and US2 implementations.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`prs_labeled.csv` from T017) AND Complexity output (`complexity_scores.csv` from T033)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 metrics

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before Services/Logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase O tasks can be distributed among developers working on US1 and US2.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test test_copilot_signature_match in tests/unit/test_classification.py"
Task: "Unit test test_infrastructure_bot_exclusion in tests/unit/test_classification.py"

# Launch all data logic for User Story 1 together:
Task: "Implement code/data/fetch_github.py"
Task: "Implement code/data/classify_prs.py"
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
 - Developer A: User Story 1 (Data & Classification)
 - Developer B: User Story 2 (Metrics & Stats)
 - Developer C: User Story 3 (Complexity & Viz)
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
- **Data Integrity**: Ensure `code/data/fetch_github.py` fails loudly on API errors; no synthetic fallbacks allowed.
- **Statistical Rigor**: **Independent two-sample t-tests are PRIMARY** per FR-004; Mann-Whitney U tests are sensitivity analysis. **Plan alignment confirmed (Spec overrides Plan).**
- **Audit Compliance**: Manual audit logic must be implemented before final report generation; threshold is set at 5% (SC-004). Ground truth is Human Expert Judgment AND secondary detector score per SC-004.
- **Data Flow Enforcement**: `code/analysis/complexity.py` (T031) and `code/analysis/save_complexity_scores.py` (T033) execute in Phase 3 (US1) to ensure data is ready for T022 (Phase 4).
- **Secondary Detector Integration**: Ensure `code/data/classify_prs.py` (T015) outputs a distinct `detector_score` column to be consumed by `code/analysis/sensitivity_analysis.py` (T026) without re-computation.
- **Rate Limit Safety**: `code/data/fetch_github.py` (T013) must implement a global watchdog timer to exit gracefully if the job exceeds a predefined time threshold, preventing CI timeout.
- **Assumption about threshold justification**: The task descriptions explicitly reference the "no multiple-comparison correction" assumption from the Spec's Assumptions section (T025) to ensure traceability.
- **Underpowered Data Handling**: T028 and T037 implement conditional logic to mark results as "exploratory" if N_LLM < 10, preventing a hard abort, as required by the Spec's Assumptions.
- **Review Resolution**: Phase O tasks (T044-T050) are mandatory to address specific analysis findings regarding fail-loudly behavior, memory constraints, and statistical robustness.
