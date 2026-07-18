# Tasks: llmXive follow-up: extending "Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based R"

**Input**: Design documents from `/specs/001-llmxive-followup/`
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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: Create directories `code/`, `data/raw`, `data/processed`, `tests/`, `tests/unit`, `tests/integration`, `contracts/`. Create files `requirements.txt`, `.gitignore`, `README.md`, `code/__init__.py`.
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scipy`, `requests`, `pyyaml`, `jsonschema`, `pytest` in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create data directory structure (`data/raw`, `data/processed`) and `.gitignore` rules for large data files
- [ ] [P] T005 Implement data validation contract schema (`contracts/trajectory_schema.json`, `contracts/metrics_schema.json`)
- [X] T006 Create base utility module for file I/O and checksumming (`code/utils/io_utils.py`)
- [X] T007 Configure environment configuration management for data paths and hyperparameters (`code/config.py`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ingest CHERRL Trajectories and Compute Divergence Gap (Priority: P1) 🎯 MVP

**Goal**: Ingest CHERRL logs, compute $G(t)$ and $\Delta G(t)$, and aggregate data across seeds.

**Independent Test**: Run ingestion on a small subset of CHERRL logs and verify output CSV contains $G(t)$ and $\Delta G(t)$ columns with correct math.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for $G(t)$ calculation logic in `tests/unit/test_ingestion_math.py`
- [X] T011 [P] [US1] Unit test for $\Delta G(t)$ derivative logic in `tests/unit/test_ingestion_math.py`
- [ ] T013b [P] [US1] Unit test for download script validation logic in `tests/unit/test_download_validation.py`. **Logic**: Verify that the script correctly parses the arXiv paper to find the data link, handles invalid links by raising the correct error, and exits with code 2. **Assertion**: Assert that a valid link returns success and an invalid link triggers the specific error message.
- [ ] T012 [US1] Integration test for multi-seed aggregation in `tests/integration/test_ingestion_pipeline.py`. **Logic**: Run the full aggregation pipeline on a small set of mock logs. **Assertions**: Assert merged CSV has expected row count, assert `seed_id` distribution matches input, assert `G(t)` and `dG(t)` columns exist and are numeric.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `download_cherrl_logs.py` to fetch real data. **Logic**: 1. Fetch and parse arXiv:2606.04923 to locate the official data repository link. 2. If link points to HuggingFace, use `datasets.load_dataset('cherrl-rewards', split='train')` (or the specific ID found). 3. If link points elsewhere, fetch via `requests`. 4. **Fail Loud**: If fetch fails or link is invalid, log "ERROR: Data source unreachable" and exit with code 2 (data_missing). **NO** synthetic fallback allowed. This ensures the pipeline halts visibly if data is missing, making the failure mode testable.
- [ ] T014 [US1] Implement `code/ingestion.py` to load logs and compute $G(t) = |J_{\text{biased}} - J_{\text{unbiased}}|$ (FR-001). **Dependency**: Requires T013 to complete successfully and produce raw logs.
- [ ] T015 [US1] Implement `code/ingestion.py` to compute $\Delta G(t)$ (discrete derivative), rolling z-score (FR-002), and handle edge cases. **Edge Case Logic**: Use `linear interpolation` for missing timesteps. If variance of $G(t)$ is zero, set z-score to 0 (using epsilon=1e-9 floor for division). **Dependency**: Requires T014.
- [ ] T016 [US1] Implement aggregation logic to merge multiple seed logs into `data/processed/trajectories_divergence.csv` preserving `seed_id` and `bias_type`. **Dependency**: Requires T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Detect Hacking via Statistical Thresholding (Priority: P2)

**Goal**: Implement the detector module to flag "hacked" timesteps based on z-score and rate-of-change thresholds.

**Independent Test**: Feed a synthetic dataset with a known spike and verify the detector flags the spike while ignoring noise.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for z-score thresholding logic in `tests/unit/test_detector.py`
- [ ] T019 [P] [US2] Unit test for $\Delta G(t)$ dynamic thresholding logic in `tests/unit/test_detector.py`
- [ ] T020 [P] [US2] Integration test with synthetic spike data in `tests/integration/test_detector_pipeline.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/detector.py` to calculate sliding window z-score ($W=20$, min 5 samples) per FR-002, reading from `data/processed/trajectories_divergence.csv`.
- [ ] T022 [US2] Implement logic in `code/detector.py` to flag "hacked" if $z(G(t)) > 3.0$ OR if $\Delta G(t)$ exceeds a dynamic threshold. **Config**: Load `DYNAMIC_THRESHOLD_MULTIPLIER` from `code/config.py` (default 2.0). **Baseline**: Calculate baseline noise floor as the standard deviation of the first 10 timesteps (or all available if <10).
- [ ] T023 [US2] Generate `data/processed/trajectories_labeled.csv` by appending `hacked_label` column to the US1 output, preserving separation of concerns (FR-001 vs FR-003).
- [ ] T024 [US2] Add error handling for NaN values in standard deviation calculations.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluate Generalization and Statistical Significance (Priority: P3)

**Goal**: Evaluate detector performance against ground truth ($J_{\text{gold}}$ drops) and perform statistical significance testing.

**⚠️ GATE**: Wait for Phase 3 completion (T014/T015 verified) before attempting T030a/T030b.

**Independent Test**: Run evaluation on a pre-labeled test set and verify confusion matrix, F1-scores, and p-value output.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for ground-truth derivation logic ($J_{\text{gold}}$ drops) in `tests/unit/test_ground_truth.py`
- [ ] T026 [P] [US3] Unit test for independence check (Pearson correlation) in `tests/unit/test_ground_truth.py`
- [ ] T027 [P] [US3] Unit test for Paired t-test implementation in `tests/unit/test_evaluation.py`
- [ ] T028 [P] [US3] Integration test for full evaluation pipeline in `tests/integration/test_evaluation_pipeline.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/ground_truth.py` to derive labels from $J_{\text{gold}}$ drops (≥0.1 decrease over 50 steps, sustained 3 steps) per FR-004. **Traceability**: The fixed-step window is defined in **Spec Assumption 6**. (Note: Spec FR-004 should be updated to include this window size for full traceability).
- [ ] T030a [US3] Implement `code/ground_truth.py` to check Pearson correlation for $J_{\text{unbiased}}$ vs $J_{\text{gold}}$ (FR-006). **Logic**: If correlation is **greater than or equal to** `CORRELATION_THRESHOLD` (default 0.8), raise `RuntimeError` with message "CIRCULAR_VALIDATION: Correlation >= threshold" and exit with code 1 immediately. Do not proceed. **Dependency**: Requires T014, T015 (data ingestion).
- [ ] T030b [US3] Implement `code/ground_truth.py` to check Pearson correlation for $J_{\text{biased}}$ vs $J_{\text{gold}}$ as a **Plan Extension** (not Spec Requirement). **Logic**: Same threshold and exit behavior as T030a. This is an additional safety check mandated by Plan.md Complexity Tracking.
- [ ] T031 [US3] Implement `code/evaluation.py` to calculate Precision, Recall, F1 per bias type (Lexical, Format, Tone, Self-praise) per FR-005. **Baseline Generation**: Generate a "Static-threshold baseline" label set (flags last [deferred] of training steps as hacked) to be used by T032a.
- [ ] T032a [US3] Implement `code/evaluation.py` to perform a **Paired t-test** (Primary, per FR-005) comparing the detector's F1-scores against the **Static-threshold baseline** (generated in T031). **Output**: Report p-value and effect size.
- [ ] T032b [US3] Implement `code/evaluation.py` to perform a **Wilcoxon signed-rank test** (Secondary) comparing the detector's F1-scores against **Neutral baselines** for robustness. **Baseline Logic**: Generate random-guess labels (uniform 0/1, p=0.5) and mean-divergence labels (flag if G(t) > mean(G)). **Output**: Report p-value and effect size.
- [ ] T033 [US3] Implement `code/evaluation.py` to check SC-003 (F1 std dev ≤ 0.15); if failed, trigger logic to call `code/tune_rubric_specific.py` for grid search per rubric type (Lexical, Format, Tone, Self-praise). **Inputs**: Pass per-rubric F1 scores and raw data path. **Output**: JSON with optimized thresholds per rubric.
- [ ] T034 [US3] Implement `code/tune_rubric_specific.py` for grid search per rubric type. **Inputs**: Raw data path and per-rubric F1 scores. **Output**: JSON with optimized thresholds per rubric.
- [ ] T035 [US3] Generate final `data/processed/metrics.csv` and evaluation report with p-values and F1 scores.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T037 Code cleanup and refactoring
- [ ] T038 Implement sequential seed processing in `code/main.py` to ensure memory safety and runtime < 4 hours (process seeds one by one if needed).
- [ ] T039 [P] Additional unit tests for edge cases (missing data, zero variance) in `tests/unit/`
- [ ] T040 Run quickstart.md validation and verify all artifacts are checksummed

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
- **User Story 2 (P2)**: Depends on US1 (requires $G(t)$ data)
- **User Story 3 (P3)**: Depends on US1 and US2 (requires divergence data and ground truth labels)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion (T013) MUST precede math computation (T014)
- Ground truth derivation (T029) MUST precede evaluation (T031)
- Independence check (T030a/T030b) MUST run before any ground truth is used for metrics

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (if dependencies allow, e.g., US2/US3 can start once US1 data format is known)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for G(t) calculation logic in tests/unit/test_ingestion_math.py"
Task: "Unit test for dG(t) derivative logic in tests/unit/test_ingestion_math.py"

# Launch implementation tasks (sequential dependency):
Task: "Download CHERRL logs to data/raw/" (T013)
Task: "Implement ingestion logic to compute G(t) and dG(t)" (T014, T015)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ingestion + Divergence)
4. **STOP and VALIDATE**: Test ingestion on real data and verify $G(t)$ calculation
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Implement detector logic → Test independently → Deploy/Demo
4. Add User Story 3 → Implement evaluation and statistical tests → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Detector Logic) - can start once T013 (download) is done
 - Developer C: User Story 3 (Evaluation) - can start once T029 (ground truth logic) is defined
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Ensure all data download tasks (T013) validate the source against the arXiv paper (arXiv:2606.04923) before fetching. No fake data generation is allowed.
- **CRITICAL**: Ensure T030a (independence check) runs before T031 (evaluation) to prevent circular validation. T030a must check J_unbiased vs J_gold and halt if correlation >= 0.8. T030b is an extension for J_biased.
- **CRITICAL**: If SC-003 fails (F1 std dev > 0.15), T033/T034 must be executed to attempt rubric-specific tuning for Lexical, Format, Tone, and Self-praise types.
- **CRITICAL**: T032a uses Paired t-test as the PRIMARY method per FR-005. T032b uses Wilcoxon as a secondary check.
- **CRITICAL**: T013 must implement a "fail loud" strategy: if the real fetch fails, the script MUST exit with code 2 and log "ERROR: Data source unreachable". It must NOT contain any `try/except` block that falls back to synthetic data generation or mock data.
- **CRITICAL**: T022 and T030a/b must load empirical constants (multiplier, correlation threshold) from `code/config.py` rather than hardcoding them, to defer empirical specifics as per Spec Assumptions.