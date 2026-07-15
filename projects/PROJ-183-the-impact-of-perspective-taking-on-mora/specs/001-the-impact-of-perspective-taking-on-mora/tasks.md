# Tasks: The Impact of Perspective-Taking on Moral Outrage in Online Discourse

**Input**: Design documents from `/specs/001-perspective-taking-outrage/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (aligned with plan.md)
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

**Purpose**: Project initialization, resource monitoring setup, and basic structure

- [X] T001 Create project structure per implementation plan: Execute `mkdir -p code data tests contracts data/raw data/processed data/human` and create `__init__.py` in all `code/` subfolders.
- [X] T002 Create virtual environment: Run `python -m venv venv` and verify activation works. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T003 Install dependencies: Run `pip install -r requirements.txt` (pandas, scipy, statsmodels, numpy, requests, pyyaml, jsonschema, vaderSentiment) and verify imports in a fresh shell.
- [X] T004a [P] Create `pyproject.toml` and `.ruff.toml` with explicit rules: Enable E501 (line length), W292 (newline at EOF), and F401 (unused imports). Configure black line-length=88.
- [X] T004b [P] Run `black --check.` and `ruff check.` to verify formatting/linting rules are applied to existing code (if any).
- [X] T041 [P] [US4] Implement resource monitoring in `code/main.py`: Add logging for peak RAM usage (target ≤7 GB) and total runtime (target ≤6 hours). Log warnings if thresholds are approached but do NOT raise errors to avoid aborting the pipeline. (SC-005, FR-007)
- [ ] T042 [P] [US4] Implement resource monitoring in `code/main.py`: Ensure the logging mechanism from T041 is active for the entire pipeline run. Log final metrics to `data/logs/resource_metrics.log`. (SC-005, FR-007)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T005 [P] Create `code/config.py` with random seed pinning, path constants, and dataset URL configuration (verified URL for "Against the Others!" dataset)
- [~] T006 [P] Initialize `data/raw/`, `data/processed/`, and `data/human/` directories with `.gitkeep`
- [~] T007 [P] Create `contracts/stimulus.schema.yaml` and `contracts/participant.schema.yaml` defining data structures
- [~] T008 Create base `code/__init__.py` and analysis `code/analysis/__init__.py` modules
- [~] T009a [P] Implement formal power analysis function in `code/analysis/stats.py` (input: effect_size, power, alpha) returning required N. Do NOT write to config yet.
- [~] T009b [P] Verify fixed N=240: Run T009a function with d=0.5, power=0.8. Write a comment in `code/config.py` at the top of the file: `# Power analysis (d=0.5, power=0.8) confirms N=240 is sufficient. [UNRESOLVED-CLAIM: c_f29cb9d3 — status=not_enough_info] ` Verify the comment exists via `grep` or similar. (FR-009b)
- [~] T010 [P] Setup `tests/` directory structure with `pytest` configuration

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stimulus Curation and Stratified Randomization (Priority: P1) 🎯 MVP

**Goal**: Ingest the "Against the Others!" dataset, filter for posts on controversial topics (climate, immigration), stratify by automated sentiment (VADER), and generate randomized experimental stimuli.

**Independent Test**: The system can be tested by executing the data pipeline script and verifying that the output JSON contains a set of unique posts distributed across the specified topics, each paired with two distinct instruction sets. The test must confirm that the selection was a random sample from a pool of ≥60 posts and that the distribution of automated sentiment scores is balanced across the two instruction conditions.

### Implementation for User Story 1

- [~] T013 [US1] Implement `code/data/ingest.py` to download dataset from verified URL and parse CSV/JSON (FR-001) <!-- FAILED: unspecified -->
- [~] T014 [US1] Implement filtering logic in `code/data/ingest.py` for `topic in ["climate", "immigration"]` and compute VADER scores if missing (FR-001)
- [~] T015 [US1] Add error handling in `code/data/ingest.py` to raise `DATASET_INSUFFICIENT` error (code 400) if <60 posts found after filtering (FR-008, Edge Case 1)
- [~] T016 [US1] Implement stratified sampling logic in `code/data/stimuli.py` to balance moderate/high intensity posts across conditions
- [~] T017 [US1] Implement `code/data/stimuli.py` to generate "Perspective-Taking" and "Control Summarization" prompt templates (FR-002)
- [~] T018 [US1] Save final curated stimuli to `data/processed/stimuli.json` with all metadata, instruction variants, and sentiment scores (FR-002)
- [~] T019 [P] [US1] Add logging for data ingestion, filtering, and stratification steps
- [ ] T051 [US1] Implement a validation report in `code/analysis/stats.py` (or `code/data/stimuli.py`) to verify that the stratification (T016) successfully balanced the VADER sentiment scores between the two experimental conditions. Save the report to `data/processed/stratification_report.json` and log the difference in mean sentiment. Do NOT fail the pipeline if the difference is large; only report it. (SC-006)

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. These validate structures produced by T015/T018.

- [ ] T011 [P] [US1] Unit test for data ingestion validation in `tests/test_ingest.py` (check n≥60, topic split, error on <60)
- [ ] T012 [P] [US1] Unit test for stimulus generation in `tests/test_stimuli.py` (check 2 variants per ID, sentiment balance)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Participant Response Collection and Data Cleaning (Priority: P2)

**Goal**: Process uploaded raw data from actual participants, enforce attention checks, detect straight-lining, and calculate mean moral outrage scores.

**Independent Test**: The system can be tested by feeding a synthetic CSV of responses (including some failed attention checks and straight-liners) and verifying that the output dataset excludes the failed participants and contains the calculated mean scores for the remaining valid set.

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/data/cleaning.py` to load raw CSV and filter for `consent_given == true`. **Note**: This task implements Constitution Principle VI, which overrides the narrower exclusion criteria in FR-003 regarding consent. (FR-003, Constitution VI)
- [ ] T024 [US2] Implement attention check filter in `code/data/cleaning.py` to exclude participants failing >1 item (FR-003)
- [ ] T025 [US2] Implement straight-lining detection in `code/data/cleaning.py`: Calculate variance of the 7 items of the Moral Outrage Scale for each participant. Exclude any participant exhibiting zero variance across these scale items. (FR-003, Edge Case 2)
- [ ] T026 [US2] Implement mean outrage score calculation in `code/data/cleaning.py` using the 7-item Moral Outrage Scale (FR-004)
- [ ] T027 [US2] Save cleaned dataset to `data/processed/cleaned_participants.csv` with warning if N < 240. **Note**: Ensure raw item-level data is preserved alongside the aggregated mean to support ICC calculation in T032. (FR-003)
- [ ] T028 [P] [US2] Add deterministic seed logging to ensure reproducibility of cleaning runs

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test for attention check filter in `tests/test_cleaning.py` (excludes >1 fail)
- [ ] T021 [P] [US2] Unit test for straight-lining detection in `tests/test_cleaning.py` (excludes zero variance across 7 items)
- [ ] T022 [P] [US2] Unit test for mean calculation in `tests/test_cleaning.py` (aggregates 7 items correctly)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Robustness Verification (Priority: P3)

**Goal**: Calculate ICC to check clustering, execute t-test (FR-005) as primary result, perform LME as robustness check if ICC >= 0.05, report effect sizes, and perform robustness checks.

**Independent Test**: The system can be tested by running the analysis script on the cleaned dataset and verifying that the output report contains the t-statistic (or LME coefficients), p-value, Cohen's d, 95% confidence interval, and the Mann-Whitney U p-value.

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/analysis/stats.py` to calculate Intra-Class Correlation (ICC) on raw, unaggregated data (FR-011). **Note**: Requires raw item-level data preserved in T027.
- [ ] T033 [US3] Implement logic to perform an independent-samples t-test (FR-005) as the primary analysis regardless of ICC. If ICC >= 0.05, ALSO execute a Linear Mixed-Effects (LME) model with random intercepts for participants as a robustness check. (Plan Summary, FR-005, FR-011)
- [ ] T034 [US3] Implement independent-samples t-test in `code/analysis/stats.py` reporting p, Cohen's d, and 95% CI (FR-005)
- [ ] T035 [US3] Implement LME model in `code/analysis/stats.py` with random intercepts for participants if ICC >= 0.05. Ensure reporting of conditional R-squared and fixed effect CIs. (FR-005, Plan Summary)
- [ ] T036 [US3] Implement Mann-Whitney U test in `code/analysis/stats.py` as non-parametric robustness check (FR-006)
- [ ] T037 [US3] Generate final analysis report in `data/processed/analysis_results.json`. **Must include**:
 - T-statistic, p-value, Cohen's d, 95% CI (from t-test).
 - If ICC >= 0.05: LME fixed effects, conditional R-squared, 95% CIs.
 - Explicit statement that findings are framed as the causal effect of the randomized intervention (FR-009).
 - Statement of the model choice (t-test vs LME) and the ICC value. (FR-009, SC-001, SC-002, SC-003, FR-011)
- [ ] T038 [P] [US3] Add visualization logic (optional) for distribution of scores by condition. **Note**: Ensure no external display drivers are required; save to file only.

### Tests for User Story 3

- [ ] T029 [P] [US3] Unit test for ICC calculation in `tests/test_stats.py`
- [ ] T030 [P] [US3] Unit test for t-test output accuracy in `tests/test_stats.py` (check p, d, CI)
- [ ] T031 [P] [US3] Unit test for Mann-Whitney U robustness in `tests/test_stats.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Computational Feasibility and Resource Constraints (Priority: P2)

**Goal**: Ensure all analysis operations complete within free-tier CI constraints (CPU-only, ≤7 GB RAM, ≤6 hours). (Note: Monitoring implemented in Phase 1 T041/T042)

**Independent Test**: The system can be tested by running the full pipeline on a constrained environment (e.g., GitHub Actions free runner) and verifying that the process exits successfully with exit code 0 without exceeding memory or time limits.

### Implementation for User Story 4

- [ ] T040 [US4] Verify `requirements.txt` contains NO GPU dependencies (e.g., torch[cuda], bitsandbytes) and raise error if found (FR-007)
- [ ] T043 [P] [US4] Vectorize simulation/cleaning loops in `code/data/` using numpy/pandas to ensure CPU efficiency (Plan: Complexity Tracking)

### Tests for User Story 4

- [ ] T039 [P] [US4] Integration test for resource usage in `tests/test_resources.py` (mock memory/time checks). **Must run after T040-T042**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in `README.md` explaining the pipeline flow, dataset requirements, and CPU constraints
- [ ] T045a [P] Extract VADER logic into `code/utils/vader_sentiment.py` (create file if not exists) to modularize scoring.
- [ ] T045b [P] Extract scale scoring logic into `code/utils/scale_scoring.py` (create file if not exists) to modularize calculations.
- [ ] T046 [P] Additional unit tests for edge cases (e.g., empty dataset, failed attention checks, ICC threshold boundary)
- [ ] T047 Run `pytest --ci` validation and fix any CI failures reported by GitHub Actions
- [ ] T048 Update `state.yaml` with artifact hashes upon successful pipeline completion (Constitution Principle V)

---

## Phase 8: Data Integrity and Real-World Validation (Revision Concerns)

**Goal**: Ensure strict adherence to "Real Data Only" principles, robust error handling for data fetching, and verification of the stratification logic's validity.

**Rationale**: Addressing the critical requirement that the loader must fail loudly on real data fetch failures (never fallback to synthetic), and ensuring the stratification logic is validated against the actual distribution of the real dataset.

### Implementation for Revision Concerns

- [ ] T049 [P] [US1] Implement strict "fail-loud" logic in `code/data/ingest.py`: Remove any `try/except` blocks that might silently fallback to synthetic data if the real URL fails. The script must raise a `ConnectionError` or `FileNotFoundError` immediately if the verified URL is unreachable. (Rule: Loader must FAIL LOUDLY)
- [ ] T050 [P] [US1] Add a pre-flight check in `code/data/ingest.py` to verify the "Against the Others!" dataset URL is reachable and returns a valid HTTP 200 before attempting to parse. If the URL is invalid, raise a `ConfigurationError` with a clear message. (Rule: Real data only)
- [ ] T052 [P] [US2] Add a specific test case in `tests/test_cleaning.py` that simulates a real data fetch failure (e.g., by mocking the URL to return 404) and verifies that the pipeline halts with an error rather than generating synthetic data. (Rule: Loader must FAIL LOUDLY)
- [ ] T053 [P] [US1] Update `code/data/stimuli.py` to explicitly log the exact random seed used for the stratified sampling and the resulting distribution of topics and sentiment scores. This ensures the "random sample" claim is reproducible and auditable. (Constitution I)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Integrity (Phase 8)**: Depends on Foundational phase; T049/T050 must be integrated into US1 tasks before execution; T051 integrated into US3.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 (data flow is parallel: US1 produces stimuli, US2 produces cleaned responses; both needed for US3)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on outputs from US1 (stimuli) and US2 (cleaned participants)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Integrated with US1/US2/US3 implementation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US4 can start in parallel
- US3 depends on US1 and US2 completion
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation for User Story 1 together (if dependencies met):
Task: "Implement code/data/ingest.py"
Task: "Implement code/data/stimuli.py"

# Launch all tests for User Story 1 together (after implementation):
Task: "Unit test for data ingestion validation in tests/test_ingest.py"
Task: "Unit test for stimulus generation in tests/test_stimuli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ≥60 stimuli, balanced sentiment)
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Data Cleaning)
 - Developer C: User Story 4 (Feasibility Checks)
3. Once US1 & US2 complete, Developer D/E: User Story 3 (Analysis)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (unless explicitly noted)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: The dataset URL in `code/config.py` must be verified before running T013. If the URL is unreachable, the pipeline must halt with a clear error.
- **Critical**: Power Analysis (T009) must be completed before any recruitment or simulation to determine sample size N. T009b documents the fixed N=240 assumption.
- **Critical**: ICC calculation (T032) determines the robustness check path (LME vs t-test only) as per Plan Summary and FR-011, but the t-test (FR-005) is always performed.
- **Critical**: All statistical methods must be CPU-only (no GPU, no 8-bit quantization) to satisfy FR-007.
- **Critical**: Real data only - T013 must fetch from a real, reachable URL; synthetic data is ONLY for unit tests (US2 tests), not primary analysis.
- **Critical**: T023 implements Constitution Principle VI (Consent), which overrides the narrower FR-003 criteria.
- **Critical**: T033/T035 implement the LME robustness check mandated by the Plan's Statistical Rigor, while ensuring FR-005's t-test requirement is always met.
- **Critical (Revision)**: T049/T050 ensure the "fail-loud" principle is strictly enforced; no synthetic fallbacks are permitted.
- **Critical (Revision)**: T051 ensures the stratification logic is empirically validated, not just assumed, without blocking valid runs.