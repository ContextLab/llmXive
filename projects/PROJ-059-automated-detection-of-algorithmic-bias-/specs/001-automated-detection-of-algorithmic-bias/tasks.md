# Tasks: Automated Detection of Algorithmic Bias in Public Code Repositories

**Input**: Design documents from `/specs/001-auto-detect-bias/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Methodology Correction Note

**CRITICAL UPDATE**: The following Functional Requirements and Success Criteria are amended to reflect the Plan's methodology correction (Methodology-a39d8d77):
- **FR-006 (Amended)**: System MUST compute Spearman's rank correlation coefficients between the aggregated **Textual Bias Scores** and the **Fairness Degradation Slopes** (d(Fairness Metric)/d(Skew)) across the repository dataset.
- **SC-001 (Amended)**: The correlation analysis must successfully compute a Spearman correlation coefficient and a Bonferroni-corrected p-value for the relationship between Textual Bias Scores and **Fairness Degradation Slopes**.
- **FR-016 (Amended)**: The statistical noise threshold MUST be derived from a pilot run OR a cited statistical model.
- **SC-004 (Amended)**: The system must perform a **diff check** (set-difference on normalized token streams) to verify zero token overlap between synthetic data and code tokens.

**Note**: This amendment supersedes the static "Fairness Metrics" definition in `spec.md` for the implementation phase. Task T051 is added to update `spec.md` to match this methodology.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: `mkdir -p src/bias_pipeline src/cli data/raw data/processed data/validation tests/unit tests/integration state`
- [X] T002 Initialize Python 3.11 project: Create `pyproject.toml` with dependencies: `numpy`, `pandas`, `scipy`, `vaderSentiment`, `fairlearn`, `datasets`, `pyyaml`, `pytest`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Dependency Note**: T005 must be completed before T007 (config required for lexicon loading).

- [X] T004 [P] Implement `src/bias_pipeline/utils.py`: Logging, error handling, and `streaming_repo_iterator` for memory-efficient repo processing (respecting GB RAM limit)
- [X] T005 [P] Implement `src/bias_pipeline/config.py`: Load `state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml` and define `CITATION_TITLE_OVERLAP_THRESHOLD`
- [ ] T006 [P] Create `data/` directory structure: `mkdir -p data/raw data/processed data/validation`
- [ ] T007 Implement `src/bias_pipeline/lexicon.py`: Load curated demographic lexicon from `data/raw/lexicon.csv` (or fetch from verified HuggingFace URL if not present). **Depends on: T005**
- [X] T008 [P] Implement `src/bias_pipeline/independence_checker.py`: String-hash comparison logic for synthetic data vs code tokens (FR-015)
- [X] T009 [P] Implement `src/bias_pipeline/error_handler.py`: Generic error handling wrapper for pipeline execution (Edge Cases)
- [ ] T043 [P] Integrate error handling logic across all phases: Ensure `error_handler.py` is imported and used in US1, US2, US3 implementation tasks (Edge Cases, SC-005, SC-006). **Must be completed before US1/US2/US3 implementation.** **Depends on: T009**
- [ ] T051 [P] **Spec Update**: Update `spec.md` (FR-006, SC-001) to reflect the "Fairness Degradation Slopes" methodology and remove the contradiction with `tasks.md`. **Must be completed before Phase 4 (US2) and Phase 5 (US3) implementation.**

**Pre-US Sub-Phase (Blocking)**:
- [ ] T041 [P] **Data Acquisition**: Acquire a 'Validation Dataset' of manually labeled comments from a verified external source (e.g., a specific HuggingFace dataset ID) OR execute a script to validate a manually curated CSV file. **Do NOT generate synthetic labels.** This task must complete before T038/T039 can run. **Depends on: T006**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Static Code Artifact Extraction (Priority: P1) 🎯 MVP

**Goal**: Extract and quantify "Textual Bias Scores" (variable names and comments) from target Python repositories without executing code.

**Independent Test**: Run parser on a known repository (e.g., one with intentional biased variable names) and verify output JSON contains correct normalized tokens and sentiment scores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for AST normalization (camelCase/snake_case) in `tests/unit/test_extractor.py`
- [X] T011 [P] [US1] Unit test for VADER sentiment thresholds in `tests/unit/test_extractor.py`
- [ ] T012 [P] [US1] Integration test for empty/binary-only repos in `tests/integration/test_extractor.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `parse_ast_tree` function in `src/bias_pipeline/extractor.py`: AST parsing for variables, functions, and string literals (FR-001) **Depends on: T043**
- [ ] T014 [P] [US1] Implement `normalize_tokens` function in `src/bias_pipeline/extractor.py`: Token normalization (camelCase/snake_case) **Depends on: T043**
- [ ] T015 [P] [US1] Implement `match_lexicon` function in `src/bias_pipeline/extractor.py`: Demographic lexicon matching for "Textual Bias Score" (FR-002) **Depends on: T043**
- [ ] T016 [P] [US1] Implement `analyze_sentiment` function in `src/bias_pipeline/extractor.py`: VADER sentiment analysis for code comments (FR-003) **Depends on: T043**
- [ ] T017 [US1] Implement `aggregate_repo_score` function in `src/bias_pipeline/extractor.py`: Aggregation logic to compute repository-level score (mean of file scores, excluding 0-token files) (FR-009) **Depends on: T043**
- [ ] T018 [US1] Implement `handle_syntax_error` function in `src/bias_pipeline/extractor.py`: Error handling for syntax errors (log and skip, do not crash) using `src/bias_pipeline/error_handler.py` (Edge Case) **Depends on: T043**
- [ ] T019 [US1] Implement CLI entry point logic in `src/cli/main.py` to trigger extraction on a list of repo paths **Depends on: T043**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Simulated Bias Injection & Fairness Proxy (Priority: P2)

**Goal**: Generate domain-neutral synthetic datasets and simulate bias injection to compute fairness metrics (Demographic Parity, Equalized Odds) as ground truth proxies.

**Independent Test**: Run simulation with `injected_skew_magnitude=0` and verify fairness disparity ≤ 0.01; verify synthetic data contains no code tokens.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for synthetic data independence (hash check) in `tests/unit/test_simulation.py`
- [ ] T021 [P] [US2] Unit test for `injected_skew_magnitude=0` noise threshold in `tests/unit/test_simulation.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `generate_synthetic_data` function in `src/bias_pipeline/simulation.py`: Synthetic data generator using `numpy` with domain-neutral distributions and realistic class imbalance (FR-004) **Depends on: T043**
- [ ] T023 [US2] Implement `inject_bias_model` function in `src/bias_pipeline/simulation.py`: Bias injection model with `injected_skew_magnitude` parameter (FR-005, FR-012) **Depends on: T043**
- [ ] T024 [US2] Implement `calculate_fairness_metrics` function in `src/bias_pipeline/simulation.py`: Fairness metric calculation (Demographic Parity, Equalized Odds) using `fairlearn` (FR-005) **Depends on: T043**
- [ ] T025 [US2] Implement `compute_degradation_slope` function in `src/bias_pipeline/simulation.py`: Logic to compute the **slope** of the fairness degradation curve (d(Fairness)/d(Skew)) by sweeping `injected_skew_magnitude` (Plan Methodology Correction) **Depends on: T043**
- [ ] T026 [US2] Implement `perform_diff_check` function in `src/bias_pipeline/simulation.py`: Integration with `src/bias_pipeline/independence_checker.py` to verify zero token overlap via set-difference (FR-015, SC-004). **Output**: `data/processed/independence_report.json` with schema `{"overlap_count": int, "status": "PASS" | "FAIL", "pass_fail": bool}`. **Gate**: Exit with non-zero code if `overlap_count > 0`. **Depends on: T043**
- [ ] T027 [US2] Add logic to handle "Insufficient Data" warnings if N < 10 per group (Edge Case) **Depends on: T043**
- [ ] T028 [P] [US2] **Pilot Run**: Implement `src/bias_pipeline/pilot.py` to run a simulation with N=1000 samples to derive the statistical noise threshold (a predetermined value) and write the result to `data/processed/noise_threshold.yaml` (FR-016). **Depends on: T043**
- [ ] T028b [P] [US2] **Fallback Model Citation**: If T028 pilot run is inconclusive, cite a specific statistical model (with ID) and **execute a derived formula** from that model's parameters to compute the threshold value. **Do NOT hardcode.** If no valid derivation exists, raise an error. **Depends on: T028**
- [ ] T029 [US2] Implement `aggregate_slopes` function in `src/bias_pipeline/simulation.py`: Aggregation function to combine per-repo slopes into `data/processed/slopes_dataset.csv` for correlation (Ordering Fix) **Depends on: T043**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation & Statistical Validation (Priority: P3)

**Goal**: Correlate "Textual Bias Scores" with "Simulated Fairness Metrics" (specifically the degradation slope) and apply statistical corrections.

**Independent Test**: Feed pre-calculated (Textual Score, Fairness Metric) pairs and verify Spearman coefficient and Bonferroni-corrected p-values match expected math.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_analyzer.py`
- [ ] T031 [P] [US3] Unit test for Spearman correlation on known datasets in `tests/unit/test_analyzer.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement `compute_spearman_correlation` function in `src/bias_pipeline/analyzer.py`: Spearman rank correlation between aggregated Textual Bias Scores and Fairness Degradation Slopes (FR-006 Amended). **Depends on: T043, T029**
- [ ] T033 [US3] Implement `apply_bonferroni_correction` function in `src/bias_pipeline/analyzer.py`: Bonferroni correction function for multiple comparisons (FR-007) **Depends on: T043**
- [ ] T034 [US3] Implement `run_sensitivity_analysis` function in `src/bias_pipeline/analyzer.py`: Sensitivity analysis function sweeping alpha across a range of significance levels and reporting "High Risk" counts (FR-008, SC-002) **Depends on: T043**
- [ ] T035 [US3] Implement `flag_high_risk` function in `src/bias_pipeline/analyzer.py`: "High Risk" flagging logic based on p < 0.05 threshold (FR-006) **Depends on: T043**
- [ ] T036 [US3] Generate final report output in `data/processed/correlation_results.json` **Depends on: T043**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Manual Validation of VADER Thresholds (Priority: P2)

**Goal**: Validate VADER sentiment thresholds against a manually labeled subset to ensure reliability.

**Independent Test**: Run validation on 'Validation Dataset' and verify Cohen's Kappa ≥ 0.6.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T037 [P] [US4] Unit test for Cohen's Kappa calculation in `tests/unit/test_validator.py`

### Implementation for User Story 4

- [ ] T038 [US4] Implement `load_validation_dataset` function in `src/bias_pipeline/validator.py`: Load 'Validation Dataset' (200 manually labeled comments) from `data/validation/` **Depends on: T041**
- [ ] T039 [US4] Implement `run_vader_validation` function in `src/bias_pipeline/validator.py`: Run VADER on labeled comments and compute Cohen's Kappa score (FR-013) **Depends on: T041**
- [ ] T040 [US4] Implement `validate_threshold` function in `src/bias_pipeline/validator.py`: Threshold validation logic (halt if Kappa < 0.6) (FR-010, FR-013) **Depends on: T041**

**Checkpoint**: Validation logic complete; pipeline can proceed only if Kappa ≥ 0.6

---

## Phase 7: Error Handling & Robustness (Priority: P2)

**Goal**: Ensure pipeline handles syntax errors and execution failures gracefully.

### Implementation for Error Handling

- [ ] T041b [P] **Pre-condition Check**: Verify `data/raw` contains at least 100 repositories before proceeding. **If fewer than 100 exist, log a warning and proceed with available data (graceful degradation) OR fail with a clear error if the minimum viable dataset is not met. Do NOT fetch external sample repos.** (Prerequisite for T042)
- [ ] T042 [P] Implement `generate_error_injection_dataset` function in `src/bias_pipeline/utils.py`: Logic to generate 'Error Injection Dataset' (A set of repositories with syntax errors) by injecting errors into a random sample of repositories from `data/raw` and store as `data/raw/error_injection_set.zip` (FR-014)
- [ ] T045 [US1/US2/US3] **Validation Run**: Execute the full pipeline against the `data/raw/error_injection_set.zip` and verify ≥95% success rate, writing results to `data/processed/error_handling_report.json` (SC-005, SC-006)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T047 Code cleanup and refactoring
- [ ] T048 Performance optimization: Ensure 500 repos process in ≤6h on 2-core CPU (SC-003)
- [ ] T049 [P] Run full integration test suite
- [ ] T050 Update `state/projects/PROJ-059-automated-detection-of-algorithmic-bias-.yaml` with final artifacts and hashes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Internal Dependency**: T005 (Config) MUST precede T007 (Lexicon)
 - **Internal Dependency**: T009 (Error Handler) MUST precede T043 (Integration)
 - **Internal Dependency**: T041 (Data Acquisition) MUST precede T038/T039 (Validation)
 - **Internal Dependency**: T051 (Spec Update) MUST precede Phase 4/5 implementation
 - **Internal Dependency**: T043 (Error Handling Integration) MUST be completed before US1/US2/US3 implementation.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - US1 (P1) and US2 (P2) can run in parallel after Phase 2
 - US3 (P3) depends on outputs from US1 and US2 (specifically `slopes_dataset.csv` from T029)
 - US4 (P2) is independent but recommended before full pipeline run
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 (uses synthetic data)
 - **Output**: Produces `data/processed/slopes_dataset.csv` (T029)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on** US1 (Textual Scores) and US2 (Fairness Metrics/Slopes)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Independent, but validates US1 input quality
 - **Input**: Requires `data/validation/labels.csv` acquired by T041

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before Services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), respecting T005->T007, T009->T043, and T041 availability
- Once Foundational phase completes:
 - **Parallel**: Implement US1 and US2 simultaneously
 - **Parallel**: Implement US4 simultaneously
- US3 must wait for US1 and US2 data generation

### Within Each User Story (Parallel Examples)

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for AST normalization"
Task: "Unit test for VADER sentiment thresholds"

# Launch all models for User Story 2 together:
Task: "Implement synthetic data generator"
Task: "Implement independence checker integration"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Extraction)
4. **STOP and VALIDATE**: Test extraction on a small sample of repos
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Extraction) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Simulation) → Test independently → Deploy/Demo
4. Add User Story 4 (Validation) → Test independently → Deploy/Demo
5. Add User Story 3 (Correlation) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Extraction)
 - Developer B: User Story 2 (Simulation)
 - Developer C: User Story 4 (Validation)
3. Once US1 and US2 are done:
 - All developers: User Story 3 (Correlation & Analysis)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Do not execute target repo code; use `ast` module only.
- **Critical**: Synthetic data must be generated from noise distributions, not code tokens.
- **Critical**: Correlation target is the **slope** of fairness degradation, not a static metric (per Methodology Correction).
- **Critical**: T043 (Error Handling) must be implemented in Phase 2 to be available for US1/US2/US3.
- **Critical**: T051 (Spec Update) must be completed before Phase 4/5 to ensure alignment.
- **Critical**: T041 (Data Acquisition) must load human-verified data, not synthetic labels.
- **Critical**: T028b (Fallback) must derive values programmatically, not hardcode.
- **Critical**: T041b (Data Check) must not fetch external sample repos.