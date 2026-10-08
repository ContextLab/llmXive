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
- [X] T002 Initialize Python 3.11 project with `requirements.txt` pinning `requests`, `pandas`, `scipy`, `networkx`, `matplotlib`, `seaborn`, `pyyaml`, `statsmodels`, `pytest`, `pycodestyle`, `pydantic`, `pdfplumber`.
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools: Create `ruff.toml` and `black.toml` (or `pypy.toml` sections) with project-specific settings to ensure reproducibility.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/utils/seeds.py` to manage random seeds for all sampling and statistical resampling
- [X] T005 Create `code/utils/config.py` defining repo list (`psf/requests`, `microsoft/vscode`, `numpy/numpy`), thresholds, and API settings
- [X] T006 [P] Implement logging infrastructure in `code/utils/logging.py` with file rotation for `data/` and `reports/`
- [X] T007 Create `code/data/fetch_github.py` with a `fetch_batch(repo: str, limit: int, max_retries: int = 3) -> List[dict]` function that implements batch processing (PRs in batches), exponential backoff (2^retry * base_delay), and saves raw JSON to `data/raw/` with SHA-256 checksums. **Dependencies**: T005.
- [X] T008 Implement data checksumming utility in `code/utils/checksum.py` to generate SHA-256 for raw JSON artifacts
- [X] T009 Create `code/audit/manual_validation.py` with a `calculate_sample_size(N_llm: int, min_threshold: int = 10, scaling_factor: float = 0.1) -> int` function and a CLI entrypoint `if __name__ == "__main__":` that prints the calculated sample size. **Dependencies**: None.
- [X] T036a [P] Create `docs/report_template.md` containing placeholders for Executive Summary, Methodology, Results, Discussion, and Limitations. **Dependencies**: None. **Note**: This is a static template created during setup; it does NOT depend on data generation tasks (e.g., T027).

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
- [X] T015c [US1] [FR-007] Create `code/data/detector_params.py` defining the specific entropy thresholds (e.g., appropriate bit-level values), n-gram parameters (e.g., higher-order n-grams), and scoring weights (e.g., a higher weight for entropy than n-gram) for the secondary detector to ensure executability without external data. **Dependencies**: None.
- [X] T015a [US1] [FR-007] Implement `code/data/classify_prs.py` secondary detector: compute code entropy (Shannon entropy of tokenized code) and n-gram anomaly scores (Jaccard similarity of 3-grams against a **hardcoded baseline of common Python tokens and standard library imports**) on PR diffs using **local heuristics only (NO external data)** to validate `llm` labels. **Rationale**: The Plan's claim of "trained on external data" is non-executable without defined external sources; this task implements a deterministic, reproducible heuristic. Output `detector_score`. **Dependencies**: T015c. **Note**: This approach deviates from the Plan but is required for executability; see T015b for documentation.
- [X] T015b [US1] [FR-007] Create `docs/statistical_detector_deviation.md` documenting the deviation from the Plan's "trained on external data" approach to the implemented "local heuristic" approach. **Rationale**: Flags the Plan for a kickback update to align with the Spec's executable constraints.
- [ ] T017 [US1] Create `code/data/save_labeled_dataset.py` to output `data/processed/prs_labeled.csv` with `source_type`, `confidence_score`, `flagged`, `detector_score`, and metadata. **Output Schema**: `pr_id` (int), `source_type` (str), `confidence_score` (float), `flagged` (bool), `detector_score` (float). **Dependencies**: T013, T014, T015a.
- [X] T018 [US1] Implement fallback logic in `code/data/fetch_github.py`: if `llm` count < 10 in current repo, log a warning, update the active repo variable in `config.py` to the next repo in the list, and resume fetching until target count is met or list is exhausted. **Dependencies**: T013.
- [X] T019a [US1] [SC-004] Create `code/audit/manual_audit_checklist.csv` template containing columns: `pr_id`, `diff_summary`, `automated_label`, `human_label` (to be filled by human), `confidence`, `checklist_items` (boolean flags for boilerplate, syntax, etc.). **Dependencies**: None.
- [ ] T019b [US1] [SC-004] Implement `code/audit/manual_validation.py` as a **CLI-based audit runner with file polling**. **Logic**: 1. Load `prs_labeled.csv` and `manual_audit_checklist.csv`. 2. Select stratified sample (size from T009). 3. Generate `audit_input.jsonl` with PR details. 4. **Poll** `audit_input.jsonl` for updates every 10 seconds (max 60s). 5. If updated, read `human_label` and `human_confidence`. 6. **Calculate Error Rate**: Compare `automated_label` (Signature) vs `detector_score` (Ground Truth). 7. **Validate Ground Truth**: Compare `human_label` vs `detector_score` for high-confidence cases. 8. Save results to `data/audit/manual_audit_results.json` and `data/audit/error_rate.json`. **Dependencies**: T019a. **Note**: This is a required manual step for SC-004; the pipeline code is reproducible, but the result depends on this human intervention.
- [ ] T033a [US1] [FR-005] Implement `code/analysis/complexity.py` to compute Cyclomatic Complexity (using `networkx` on AST) and Lines of Code for PR diffs in `data/processed/prs_labeled.csv`. **Dependencies**: T017.
- [ ] T033b [US1] [FR-005] Create `code/analysis/save_complexity_scores.py` to output `data/processed/complexity_scores.csv` with `pr_id` (int) and `complexity_score` (float) columns. **MUST** join on `pr_id` from `data/processed/prs_labeled.csv`. **Dependencies**: T033a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Metric Extraction and Statistical Comparison (Priority: P2)

**Goal**: Calculate review metrics and perform statistical tests (t-tests PRIMARY per FR-004, Mann-Whitney U sensitivity) to compare `llm` vs `human` groups.

**Independent Test**: Run analysis on `data/processed/prs_labeled.csv` and `data/processed/complexity_scores.csv` and verify `data/processed/results.json` contains t-statistics, p-values, and effect sizes for comment density and time-to-merge.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020a [P] [US2] Unit test `test_comment_count_calculation` in `tests/unit/test_metrics.py`
- [X] T020b [P] [US2] Unit test `test_time_to_merge_calculation` in `tests/unit/test_metrics.py`
- [X] T020c [P] [US2] Unit test `test_review_cycles_calculation` in `tests/unit/test_metrics.py`
- [X] T021a [P] [US2] Unit test `test_mann_whitney_u_implementation` in `tests/unit/test_statistical_tests.py`: asserts p-value and statistic output. **Input**: Mock data `{'llm': [1, 2, 3], 'human': [4, 5, 6]}`. **Expected**: `p_value` approx 0.1, `U_statistic` approx 0.0. **Function**: `statistical_tests.mann_whitney_u_test(llm_data, human_data)`.
- [X] T021b [P] [US2] Unit test `test_independent_t_test_implementation` in `tests/unit/test_statistical_tests.py`: asserts p-value, t-statistic, and effect size output. **Input**: Mock data `{'llm': [1, 2, 3], 'human': [4, 5, 6]}`. **Expected**: `p_value` approx 0.05, `t_statistic` approx -2.0, `effect_size` approx 1.5. **Function**: `statistical_tests.t_test(llm_data, human_data)`.

### Implementation for User Story 2

- [ ] T022 [US2] [FR-003] [FR-004] [SC-001] [SC-002] Implement `code/data/extract_metrics.py` to calculate `comment_count`, `time_to_merge_minutes`, `review_cycles` for every PR from `data/processed/prs_labeled.csv` and **Join `data/processed/prs_labeled.csv` and `data/processed/complexity_scores.csv` on `pr_id`** (produced by T033b in Phase 3) to include actual `complexity_score`. **Requires T033b completion.** Output schema: `pr_id` (int), `comment_count` (int), `time_to_merge_minutes` (float), `review_cycles` (int), `complexity_score` (float). **Dependencies**: T033b.
- [ ] T023 [US2] [FR-003] Save processed metrics to `data/processed/prs_metrics.csv` including `pr_id` (int), `comment_count` (int), `time_to_merge_minutes` (float), `review_cycles` (int), and `complexity_score` (float) columns.
- [ ] T024a [US2] [FR-004] [SC-001] [SC-002] Implement `code/analysis/statistical_tests.py` to perform **independent two-sample t-tests as PRIMARY analysis** (per FR-004) comparing `llm` vs `human` groups for comment density and time-to-merge. **MUST include Shapiro-Wilk normality check**: if p < 0.05, log warning "Data non-normal, but t-test forced per FR-004" and **DO NOT** fallback to Mann-Whitney U. **Output Schema**: `data/processed/results.json` must include keys for both `t_test` (p_value, t_statistic, effect_size) and `mann_whitney_u` (p_value, U_statistic) results (Mann-Whitney U is for sensitivity analysis only). **Dependencies**: T022. **Note**: This approach enforces Spec FR-004 over Plan's Mann-Whitney U primary; see T024c for documentation.
- [X] T024b [US2] [FR-008] Implement **Mann-Whitney U tests as sensitivity analysis** in `code/analysis/statistical_tests.py` to verify robustness of t-test results (run regardless of normality).
- [X] T024c [US2] [FR-004] Create `docs/statistical_protocol_deviation.md` documenting the deviation from the Plan's "Mann-Whitney U as primary" stance to the Spec's "t-test as primary" requirement. **Rationale**: Preserves Spec constraint and flags Plan for update.
- [X] T025 [US2] [FR-004] [SC-001] [SC-002] Implement calculation of effect sizes (Cohen's d) and significance determination (α = 0.05) in `code/analysis/statistical_tests.py`. **MUST** include a verification step to confirm that the chosen α aligns with the "no multiple-comparison correction" assumption (from Spec Assumptions) before execution by logging a message "Alpha set to 0.05 per Spec Assumptions". **Dependencies**: T024a. **Note**: Removed Wikipedia URL; using internal constant.
- [~] T035 [US2] [FR-005] [SC-003] Implement correlation analysis in `code/analysis/visualizations.py` to measure relationship between complexity and review metrics (SC-003). **MUST** verify usage of complexity scores in regression/correlation analysis to ensure they are used to control for confounding variables as required by SC-003. Output `data/processed/correlation_results.json`. **Dependencies**: T022.
- [X] T026 [US2] [FR-008] Implement `code/analysis/sensitivity_analysis.py` to re-run tests using only the secondary detector cohort (FR-008)
- [~] T027 [US2] [FR-004] [FR-003] Create `code/analysis/generate_results_report.py` to aggregate findings into `data/processed/results.json` with all statistical outputs. **JSON Schema**: `{ "comment_density": { "p_value": float, "t_statistic": float, "effect_size": float, "is_significant": bool }, "time_to_merge": {... }, "complexity_correlation": float }`. **MUST** read correlation coefficient from `data/processed/correlation_results.json` (produced by T035). **Dependencies**: T035.
- [~] T028 [US2] [FR-004] [FR-003] Implement logic in `code/analysis/generate_results_report.py` to read the error rate from `data/audit/error_rate.json` (produced by T019b) and write a `gate_status` flag to `data/processed/gate_status.json`. **Logic**: If error rate > 0.05, set status to "blocked". If N_LLM < 10, set status to "exploratory". **Do not block Phase 4 execution, only final aggregation.** **JSON Schema for gate_status**: `{ "status": "blocked" | "passed" | "exploratory" }`. **Requires T019b completion.** **CRITICAL**: If `data/audit/error_rate.json` does not exist, raise `FileNotFoundError("Manual audit (T019b) must complete before aggregation.")`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Complexity Scoring and Visualization (Priority: P3)

**Goal**: Score code complexity (already computed in Phase 3) and generate visualizations (boxplots, histograms) to control for confounding variables.

**Independent Test**: Run complexity and visualization scripts on processed data; verify `reports/figures/` contains PDF with boxplots and `data/processed/prs_metrics.csv` includes `complexity_score`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029a [P] [US3] Unit test `test_cyclomatic_complexity_calculation` in `tests/unit/test_complexity.py`
- [ ] T029b [P] [US3] Unit test `test_lines_of_code_calculation` in `tests/unit/test_complexity.py`
- [ ] T030a [P] [US3] Integration test `test_boxplot_generation` in `tests/integration/test_visualizations.py`: assert `os.path.exists("reports/figures/boxplots.pdf")` and verify the PDF file size is > 50KB and contains at least 2 vector paths using `pdfplumber`.
- [ ] T030b [P] [US3] Integration test `test_histogram_generation` in `tests/integration/test_visualizations.py`: assert `os.path.exists("reports/figures/histograms.pdf")` and verify the PDF file size is > 50KB and contains at least 2 vector paths using `pdfplumber`.

### Implementation for User Story 3

- [ ] T031 [US3] [FR-005] [FR-006] Implement `code/analysis/visualizations.py` to generate side-by-side boxplots for comment density and time-to-merge. **Note**: This is the sole producer of visualization artifacts; T034 (duplicate) has been removed.
- [ ] T032 [US3] [FR-005] [FR-006] Implement fallback logic in `code/analysis/complexity.py` to use standard metrics if memory usage > 6GB (Assumption 3) **MUST include a psutil watchdog hook** to trigger fallback automatically.
- [ ] T036b [US3] [FR-006] Implement `code/analysis/generate_report_narrative.py` to inject statistical results from `data/processed/results.json` and `data/processed/gate_status.json` into `docs/report_template.md`. **Dependencies**: T027, T028, T036a.
- [X] T036c [US3] [FR-006] Implement `code/analysis/generate_report_narrative.py` to **synthesize** the 'Discussion' and 'Limitations' text sections based on rule-based analysis of the statistical results (e.g., if p < 0.05, discuss significance; if N_LLM < 10, discuss power limitations). **Dependencies**: T027.
- [ ] T036d [US3] [FR-006] Generate final report PDF in `reports/figures/final_report.pdf` containing all required plots and the synthesized narrative text. **MUST** include sections: Executive Summary, Methodology, Results (with plots), Discussion, Limitations. **Depends on T036b, T036c.**
- [ ] T037 [US3] [FR-005] [FR-006] Implement `code/analysis/generate_final_report.py` to compile all findings, limitations, and visualizations into a research summary; **MUST** read `data/processed/gate_status.json` (from T028). **Logic**: If status is "blocked", raise ValueError("Pipeline blocked: error rate exceeded threshold"). If status is "exploratory", include a note in the report but do not abort. **Depends on T028, T036d.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Update `README.md`: Add installation instructions, usage examples, and a data flow diagram.
- [X] T039 [P] Update API documentation in `docs/`: Document all modules in `code/` with docstrings and examples.
- [ ] T040 [P] Refactor `code/data/fetch_github.py`: Use a single session object; extract common error handling logic (e.g., `handle_rate_limit()`, `handle_404()`) into `code/utils/errors.py` with specific function signatures: `handle_rate_limit(response: Response) -> None` and `handle_404(response: Response) -> None`.
- [ ] T041 [P] Optimize `code/analysis/complexity.py`: Process diffs in chunks (chunk size = 1000 lines); implement parallel processing for metric extraction in `code/data/extract_metrics.py` using `concurrent.futures.ThreadPoolExecutor` for `comment_count` and `time_to_merge`.
- [X] T042 [P] Implement PII filter in `code/utils/pii_scan.py`: Add a function that masks email addresses and usernames in logs; verify no PII in `data/` artifacts via a scan script; output `data/audit/pii_scan_results.txt`.
- [X] T043 [P] Run `quickstart.md` validation and verify all artifacts are checksummed. **Command**: `python code/quickstart_runner.py`. **Outcome**: Verify all artifacts in `data/` have corresponding checksums in `state/`.

---

## Phase O: Review Resolution & Robustness (Revision Pass)

**Purpose**: Improvements and edge-case handling identified in the analysis phase.

- [ ] T044 [US1] [FR-001] Implement **strict fail-on-error** logic in `code/data/fetch_github.py`: Remove any implicit fallbacks to synthetic data; if the GitHub API returns a rate limit error after max retries, or a 404 (repo not found), the script MUST raise a `RuntimeError` with a clear message "RuntimeError: Failed to fetch from {repo} after {retries} retries. Next repo: {next_repo}". **Rationale**: Ensures compliance with the "Fail Loudly" rule and prevents silent fabrication of data.
- [ ] T045 [US1] [FR-001] Implement **streaming/chunked processing** for large PR diffs in `code/analysis/complexity.py` (T031): If a single PR diff exceeds a large size threshold, the complexity scorer must process the diff in chunks (e.g., fixed-size blocks). to Stay within the available RAM limit. without loading the entire payload into memory at once. **Rationale**: Addresses the "Large real datasets" constraint and prevents OOM errors on the CI runner.
- [X] T047 [US2] [FR-008] Implement **effect size interpretation** in `code/analysis/generate_results_report.py` (T027): Add a helper function to classify the magnitude of Cohen's d (e.g., small < 0.2, medium < 0.5, large > 0.8) and append this qualitative interpretation to the JSON output. **Rationale**: Provides necessary context for the "Measurable Outcomes" (SC-001, SC-002) beyond just p-values.
- [ ] T048 [US1] [FR-002] Implement **confidence_score calibration** in `code/data/classify_prs.py` (T014): Ensure the `confidence_score` is derived from a weighted combination of signature match strength and secondary detector score, with the former assigned a higher weight than the latter., not just a binary flag, to provide a continuous metric for the manual audit. **Rationale**: Aligns with the requirement for a `confidence_score` column and improves the granularity of the manual audit (SC-004).
- [ ] T049 [US3] [FR-006] Implement **publication-quality styling** in `code/analysis/visualizations.py` (T034): Configure `seaborn`/`matplotlib` to use a consistent font, color palette, and axis labels that match the project's research theme, and ensure the PDF output is high-resolution for potential inclusion in a paper. **Rationale**: Enhances the "Polish" phase and ensures the visual artifacts are suitable for the final research report.
- [ ] T050 [US1] [FR-007] Implement **deterministic seed** for the secondary statistical detector in `code/data/classify_prs.py` (T015a): Explicitly set the random seed for any n-gram or entropy sampling logic to ensure the `detector_score` is reproducible across runs by calling `set_seed(SEED_VALUE)` at the start of the n-gram calculation function in classify_prs.py. **Rationale**: Satisfies the "Reproducibility" principle (Principle I) and ensures the secondary detector is not stochastic.
- [ ] T051 [US1] [FR-001] [FR-002] Implement **data validation schema** in `code/data/save_labeled_dataset.py` (T017) using **`pydantic`** (added in T002) to strictly validate that every row in `prs_labeled.csv` contains non-null `pr_id`, valid `source_type` ('llm' or 'human'), `confidence_score` in [0.0, 1.0], and `detector_score` in [0.0, 1.0]. If validation fails, raise a `ValueError` with details on the malformed row. **Rationale**: Ensures data integrity before downstream consumption and prevents silent propagation of bad data. **Schema**: `class LabeledPR(BaseModel): pr_id: int; source_type: str; confidence_score: float; detector_score: float; flagged: bool`. **Dependencies**: T002.
- [ ] T052 [US2] [FR-004] [SC-001] Implement **robust outlier handling** in `code/analysis/statistical_tests.py` (T024a): Before running t-tests, implement a check for extreme outliers in `time_to_merge_minutes` (e.g., > 3 IQRs) and log a warning if detected, but do not exclude them automatically to maintain statistical integrity. **Rationale**: Addresses potential skew in time-to-merge data without violating the "fix the code, not the test" rule by altering the dataset.
- [X] T053 [US2] [FR-004] [FR-008] Implement **sensitivity analysis reporting** in `code/analysis/generate_results_report.py` (T027): Add a dedicated section to the JSON output that compares the primary t-test results with the secondary detector-only cohort results, explicitly stating the percentage change in p-values and effect sizes. **Rationale**: Explicitly satisfies FR-008's requirement for a sensitivity analysis and makes the robustness check visible in the final report.
- [ ] T054 [US3] [FR-006] Implement **interactive audit logging** in `code/audit/manual_validation.py` (T019b): Extend the CLI runner to log the exact timestamp and user input for each audit decision to `data/audit/audit_log.jsonl`, including the displayed diff summary and the final `human_label` choice. **Rationale**: Ensures the manual audit process is fully reproducible and auditable, satisfying Constitution Principle I.
- [ ] T055 [US1] [FR-001] Implement **API rate limit monitoring** in `code/data/fetch_github.py` (T013): Add a global counter for API requests and a warning log if the usage approaches the GitHub API limit (e.g., > 80% of the hourly limit), suggesting a pause or switch to the next repo. **Rationale**: Proactive management of API constraints to prevent abrupt job termination and ensure data collection continuity.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`prs_labeled.csv` from T017) AND Complexity output (`complexity_scores.csv` from T033b)
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
- **Audit Compliance**: Manual audit logic must be implemented before final report generation; threshold is set at 5% (SC-004). Ground truth is Detector Score (validated by Human) per SC-004.
- **Data Flow Enforcement**: `code/analysis/complexity.py` (T033a) and `code/analysis/save_complexity_scores.py` (T033b) execute in Phase 3 (US1) to ensure data is ready for T022 (Phase 4).
- **Secondary Detector Integration**: Ensure `code/data/classify_prs.py` (T015a) outputs a distinct `detector_score` column to be consumed by `code/analysis/sensitivity_analysis.py` (T026) without re-computation.
- **Rate Limit Safety**: `code/data/fetch_github.py` (T013) must implement a global watchdog timer to exit gracefully if the job exceeds a predefined time threshold, preventing CI timeout.
- **Assumption about threshold justification**: The task descriptions explicitly reference the "no multiple-comparison correction" assumption from the Spec's Assumptions section (T025) to ensure traceability.
- **Underpowered Data Handling**: T028 and T037 implement conditional logic to mark results as "exploratory" if N_LLM < 10, preventing a hard abort, as required by the Spec's Assumptions.
- **Review Resolution**: Phase O tasks (T044, T045, T047-T050) are mandatory to address specific analysis findings regarding fail-loudly behavior, memory constraints, and statistical robustness.
- **Manual Audit Executability**: T019a and T019b implement a CLI-based interactive loop with file polling for human input, ensuring the manual audit is executable.
- **Report Narrative Executability**: T036a, T036b, T036c define the template and synthesis logic for the final report's narrative sections.
- **Statistical Protocol Deviation**: T024c documents the deviation from the Plan's statistical protocol to align with the Spec.
- **Secondary Detector Executability**: T015a uses local heuristics to ensure the detector is executable without external data.
- **Normality Check Integration**: The Shapiro-Wilk check is now integrated into T024a (Phase 4) to ensure the primary test is robust and complete.
- **New Review Tasks**: T051-T055 address data validation, outlier handling, sensitivity reporting, audit logging, and rate limit monitoring to ensure robust execution.
- **Duplicate Task Removal**: Task T034 has been removed to resolve the duplication with T031. All visualization logic is now consolidated under T031.
