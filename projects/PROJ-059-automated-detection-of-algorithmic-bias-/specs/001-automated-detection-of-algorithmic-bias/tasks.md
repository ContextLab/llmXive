# Tasks: Automated Detection of Algorithmic Bias in Public Code Repositories

**Input**: Design documents from `/specs/001-auto-detect-bias/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, P3)
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

## Methodology Correction Note

**CRITICAL UPDATE**: The following Functional Requirements and Success Criteria are amended to reflect the Plan's methodology correction (Methodology-a39d8d77):
- **FR-006 (Amended)**: System MUST compute Spearman's rank correlation coefficients between the aggregated **Textual Bias Scores** and the **Fairness Degradation Slopes** (d(Fairness Metric)/d(Skew)) across the repository dataset.
- **SC-001 (Amended)**: The correlation analysis must successfully compute a Spearman correlation coefficient and a Bonferroni-corrected p-value for the relationship between Textual Bias Scores and **Fairness Degradation Slopes**.
- **FR-016 (Amended)**: The statistical noise threshold MUST be derived from a pilot run OR a cited statistical model.
- **SC-004 (Amended)**: The system must perform a **diff check** (set-difference on normalized token streams) to verify zero token overlap between synthetic data and code tokens.

**Note**: This amendment supersedes the static "Fairness Metrics" definition in `spec.md` for the implementation phase. The tasks below explicitly implement the "Fairness Degradation Slopes" methodology.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: `mkdir -p src/bias_pipeline src/cli data/raw data/processed data/validation tests/unit tests/integration state`
- [X] T002 Initialize Python 3.11 project: Create `pyproject.toml` with dependencies: `numpy`, `pandas`, `scipy`, `vaderSentiment`, `fairlearn`, `datasets`, `pyyaml`, `pytest`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` with `target-version = "py311"`, `line-length = 88`, and `pyproject.toml` with `[tool.black] line-length = 88` and `[tool.pytest]` sections.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Dependency Note**: T009 must complete before T043a/b/c. T043a/b/c can run in parallel with each *other*. T005 must complete before T007. T007 must complete before T013-T017.

- [X] T004 [P] Implement `src/bias_pipeline/utils.py`: Logging, error handling, and `streaming_repo_iterator` for memory-efficient repo processing (respecting GB RAM limit) using `datasets.load_dataset(..., streaming=True)`
- [X] T005 [P] Implement `src/bias_pipeline/config.py`: Load `state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml` and define `CITATION_TITLE_OVERLAP_THRESHOLD`
- [ ] T006 [P] Create `data/` directory structure: `mkdir -p data/raw data/processed data/validation`
- [ ] T006a [P] **Data Acquisition**: Clone 500 Python repositories from `https://huggingface.co/datasets/codeparrot/github-code` into `data/raw` using `datasets.load_dataset('codeparrot/github-code', split='train', streaming=True)` with a filter for Python files. **FAIL LOUDLY** if fetch fails; do not use synthetic fallback.
- [X] T007 Implement `src/bias_pipeline/lexicon.py`: Load curated demographic lexicon from `https://huggingface.co/datasets/some-org/demographic-lexicon/resolve/main/lexicon.csv`. **FAIL LOUDLY** if URL fails; NO hardcoded fallback allowed. **Depends on: T005**
- [X] T008 [P] Implement `src/bias_pipeline/independence_checker.py`: String-hash comparison logic for synthetic data vs code tokens (FR-015)
- [X] T009 Implement `src/bias_pipeline/error_handler.py`: Generic error handling wrapper for pipeline execution (Edge Cases). **Note: This task is NOT [P] and must complete before T043a.**
- [ ] T043a [P] **US1 Integration**: Implement `import error_handler` in `src/bias_pipeline/extractor.py` and wrap `parse_ast_tree`, `match_lexicon`, `analyze_sentiment` with `error_handler.handle_error` (Edge Cases). **Depends on: T009**
- [ ] T043c [P] **US3 Integration**: Implement `import error_handler` in `src/bias_pipeline/analyzer.py` and wrap `compute_spearman_correlation`, `apply_bonferroni_correction` with `error_handler.handle_error` (Edge Cases). **Depends on: T009**

**Pre-US Sub-Phase (Blocking)**:
- [ ] T0410 [P] **US1, US4 Integration**: Generate `data/validation/labels.csv` containing 200 manually labeled comments by fetching a real subset from `datasets.load_dataset('nab', streaming=True)` and applying a deterministic heuristic labeling script with fixed seed (42).
- [ ] T0411 [P] **US4 Integration**: Run script to generate labeled comments in `data/validation/labels.csv` (if T0410 is split).
- [ ] T0412 [P] **Pre-condition Check**: Verify `data/raw` contains the required number of repositories before proceeding.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Static Code Artifact Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract and quantify "Textual Bias Scores" (variable names and comments) from target Python repositories without executing code.

**Independent Test**: Run parser on a known repository (e.,g., one with intentional biased variable names) and verify output JSON contains correct normalized tokens and sentiment scores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for AST normalization (camelCase/snake_case) in `tests/unit/test_extractor.py`
- [X] T011 [P] [US1] Unit test for VADER sentiment thresholds in `tests/unit/test_extractor.py`
- [X] T012 [P] [US1] Integration test for empty/binary-only repos in `tests/integration/test_extractor.py`

### Implementation for User Story 1

- [ ] T012a [P] [US1] Create `src/bias_pipeline/extractor.py` skeleton file with imports and empty function stubs.
- [ ] T013 [P] [US1] Implement `parse_ast_tree` function in `src/bias_pipeline/extractor.py`: AST parsing for variables, functions, and string literals (FR-001). **Depends on: T012a**. **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T014 [P] [US1] Implement `normalize_tokens` function in `src/bias_pipeline/extractor.py`: Token normalization (camelCase/snake_case). **Depends on: T012a**. **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T015 [P] [US1] Implement `match_lexicon` function in `src/bias_pipeline/extractor.py`: Demographic lexicon matching for "Textual Bias Score" (FR-002). **Depends on: T012a**. **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T016 [P] [US1] Implement `analyze_sentiment` function in `src/bias_pipeline/extractor.py`: VADER sentiment analysis for code comments (FR-003). **Depends on: T012a**. **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T017 [US1] Implement `aggregate_repo_score` function in `src/bias_pipeline/extractor.py`: Aggregation logic to compute repository-level score (mean of file scores, excluding 0-token files) (FR-009). **Depends on: T012a**.
- [ ] T018 [US1] Implement `handle_syntax_error` function in `src/bias_pipeline/extractor.py`: Error handling for syntax errors (log and skip, do not crash) using `src/bias_pipeline/error_handler.py` (Edge Case). **Depends on: T012a**.
- [ ] T019 [US1] Implement CLI entry point logic in `src/cli/main.py` to trigger extraction on a list of repo paths. **Depends on: T017**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Simulated Bias Injection & Fairness Proxy (Priority: P2)

**Goal**: Generate domain-neutral synthetic datasets and simulate bias injection to compute fairness metrics (Demographic Parity, Equalized Odds) as ground truth proxies.

**Independent Test**: Run simulation with `injected_skew_magnitude=0` and verify fairness disparity ≤ 0.01; verify synthetic data contains no code tokens.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for synthetic data independence (hash check) in `tests/unit/test_simulation.py`
- [ ] T021 [P] [US2] Unit test for `injected_skew_magnitude=0` noise threshold in `tests/unit/test_simulation.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `generate_synthetic_data` function in `src/bias_pipeline/simulation.py`: Synthetic data generator using `numpy` with domain-neutral distributions and realistic class imbalance (FR-004). **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T023 [US2] Implement `inject_bias_model` function in `src/bias_pipeline/simulation.py`: Bias injection model with `injected_skew_magnitude` parameter (FR-005, FR-012). **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T024 [US2] Implement `calculate_fairness_metrics` function in `src/bias_pipeline/simulation.py`: Fairness metric calculation (Demographic Parity, Equalized Odds) using `fairlearn` (FR-005). **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T025 [US2] Implement `compute_degradation_slope` function in `src/bias_pipeline/simulation.py`: Logic to compute the **slope** of the fairness degradation curve (d(Fairness)/d(Skew)) by sweeping `injected_skew_magnitude` (Plan Methodology Correction). **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T026 [US2] Implement `perform_diff_check` function in `src/bias_pipeline/simulation.py`: Integration with `src/bias_pipeline/independence_checker.py` to verify zero token overlap via set-difference (FR-015, SC-004). **Output**: `data/processed/independence_report.json` with schema `{"overlap_count": int, "status": "PASS" | "FAIL", "pass_fail": bool}`. **Gate**: Exit with non-zero code if `overlap_count > 0`. **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T027 [US2] Add logic to handle "Insufficient Data" warnings if N < 10 per group (Edge Case). **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T028 [US2] Implement `src/bias_pipeline/pilot.py` to run a simulation with N=1000 samples to derive the statistical noise threshold (a predetermined value) and write the result to `data/processed/noise_threshold.yaml` (FR-016). **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T029 [US2] Implement `aggregate_slopes` function in `src/bias_pipeline/simulation.py`: Aggregation function to combine per-repo slopes into `data/processed/slopes_dataset.csv` for correlation (Ordering Fix). **Wrap with `error_handler.handle_error` (Edge Cases).**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation & Statistical Validation (Priority: P3)

**Goal**: Correlate "Textual Bias Scores" with "Simulated Fairness Metrics" (specifically the degradation slope) and apply statistical corrections.

**Independent Test**: Feed pre-calculated (Textual Score, Fairness Metric) pairs and verify Spearman coefficient and Bonferroni-corrected p-values match expected math.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_analyzer.py`
- [ ] T031 [P] [US3] Unit test for Spearman correlation on known datasets in `tests/unit/test_analyzer.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement `compute_spearman_correlation` function in `src/bias_pipeline/analyzer.py`: Spearman rank correlation between aggregated Textual Bias Scores and Fairness Degradation Slopes (FR-006 Amended). **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T033 [US3] Implement `apply_bonferroni_correction` function in `src/bias_pipeline/analyzer.py`: Bonferroni correction function for multiple comparisons (FR-007). **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T034 [US3] Implement `run_sensitivity_analysis` function in `src/bias_pipeline/analyzer.py`: Sensitivity analysis function sweeping alpha across a range of significance levels and reporting "High Risk" counts (FR-008, SC-002). **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T035 [US3] Implement `flag_high_risk` function in `src/bias_pipeline/analyzer.py`: "High Risk" flagging logic based on p < 0.05 threshold (FR-006). **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T036 [US3] Generate final report output in `data/processed/correlation_results.json`. **Wrap with `error_handler.handle_error` (Edge Cases).**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Manual Validation of VADER Thresholds (Priority: P2)

**Goal**: Validate VADER sentiment thresholds against a manually labeled subset to ensure reliability.

**Independent Test**: Run validation on 'Validation Dataset' and verify Cohen's Kappa ≥ 0.6.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T037 [P] [US4] Unit test for Cohen's Kappa calculation in `tests/unit/test_validator.py`

### Implementation for User Story 4

- [ ] T038 [US4] Implement `load_validation_dataset` function in `src/bias_pipeline/validator.py`: Load 'Validation Dataset' (200 manually labeled comments) from `data/validation/labels.csv`.
- [ ] T039 [US4] Implement `run_vader_validation` function in `src/bias_pipeline/validator.py`: Run VADER on labeled comments and compute Cohen's Kappa score (FR-013). **Wrap with `error_handler.handle_error` (Edge Cases).**
- [ ] T040 [US4] Implement `validate_threshold` function in `src/bias_pipeline/validator.py`: Threshold validation logic ({{claim:c_38197f32}}) (FR-010, FR-013). **Wrap with `error_handler.handle_error` (Edge Cases).**

**Checkpoint**: Validation logic complete; pipeline can proceed only if Kappa ≥ 0.6

---

## Phase 7: Error Handling & Robustness (Priority: P2)

**Goal**: Ensure pipeline handles syntax errors and execution failures gracefully.

### Implementation for Error Handling

- [ ] T041c [P] **Validation Run**: Execute the full pipeline against the `data/raw/error_injection_set.zip` (generated by injecting syntax errors into a subset of repos) and verify ≥95% success rate, writing results to `data/processed/error_handling_report.json` (SC-005, SC-006). **Note**: This task generates the error injection set if it doesn't exist, by cloning a subset of repos and programmatically injecting syntax errors (e.g., unclosed brackets) using `ast` module.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T047 Code cleanup and refactoring
- [ ] T048 Performance optimization: Ensure 500 repos process in ≤6h on 2-core CPU [UNRESOLVED-CLAIM: c_a9506f8f — status=not_enough_info]. (SC-003)
- [ ] T049 [P] Run full integration test suite
- [ ] T050 Update `state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml` with final artifacts and hashes