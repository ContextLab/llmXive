# Tasks: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

**Input**: Design documents from `/specs/001-cognitive-mechanisms-moral-judgments/`
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

- [X] T001a [P] Create root directories: `code/`, `data/`, `tests/`, `state/`
- [X] T001b [P] Create subdirectories: `data/raw/`, `data/processed/`, `data/logs/`, `reports/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pymc>=5.0.0, pandas, numpy, scikit-learn, pyyaml, requests, seaborn, statsmodels)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T004 [P] Initialize `.gitignore` and CI configuration (GitHub Actions) for CPU-only environment

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create `code/config.py` defining paths, random seeds, and constants
- [X] T006 Implement `code/utils/hashing.py` to calculate SHA-256 checksums and update `state/...yaml` (Constitution Principle V)
- [ ] T007 Create `code/utils/norms.py` to load and reference Gervais et al. (2011) psychometric norms [UNRESOLVED-CLAIM: c_0faae073 — status=not_enough_info] <!-- FAILED: unspecified -->
- [ ] T008a [P] Create directories: `data/raw/`, `data/processed/`, `data/logs/`
- [ ] T008b [P] Implement `code/utils/schema.py` using Pydantic to validate data schemas (MFQ, Stories, VR Logs)
- [ ] T009 Implement base logging infrastructure to capture exclusion reasons and VR mapping logs

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Experimental Construction, and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest real and synthetic MFQ and Moral Stories data, construct VR conditions with salience mapping, and validate psychometric distribution.

**Independent Test**: The pipeline can be tested by running the ingestion and construction scripts against the synthetic data and verifying that the output CSV contains correctly merged rows, valid salience labels, and matches Gervais et al. norms.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. These tasks define the interface for T013-T018.**

- [X] T010 [P] [US1] Unit test for synthetic MFQ generator in `code/tests/test_ingest_mfq.py` (defines interface for simulation)
- [X] T011 [P] [US1] Unit test for salience mapping logic in `code/tests/test_schema.py` (defines interface for preprocess)
- [~] T012 [US1] Unit test for psychometric norm validation in `code/tests/test_ingest_stories.py` (defines interface for norms)

### Implementation for User Story 1

- [~] T013 [US1] Implement `code/data/simulation_mfq.py` to generate synthetic MFQ data based on Gervais et al. (2011) multivariate normal distributions [UNRESOLVED-CLAIM: c_ad8cb909 — status=not_enough_info]
- [~] T014 [US1] Implement `code/data/simulation_stories.py` to generate **Validation-Only** simulated Moral Stories and VR interaction logs (response times, gaze, judgment) with a known `ground_truth_effect` to proxy FR-006 requirements
- [~] T015 [US1] Implement `code/data/ingest.py` to load and merge synthetic MFQ and Moral Stories datasets, handling ID mismatches
- [~] T016 [US1] Implement `code/data/preprocess.py` to map text stories to VR scenes, assigning `salience_level` (low/high) via blend-shape parameters <!-- FAILED: unspecified -->
- [~] T017 [US1] Add validation logic to existing `code/utils/norms.py` to compare synthetic MFQ distribution against published norms (must be within 1 SD) <!-- FAILED: unspecified -->
- [~] T018 [US1] Implement `code/utils/hashing.py` integration to checksum derived CSVs and update `state/...yaml`

### Architecture for Future Real Data (US4 Stub)

- [~] T019a [US4-Stub] Define `code/data/ingest_real.py` architecture: Specify OSF API endpoint, HuggingFace dataset ID, auth method, and data schema for **actual** VR logs (FR-006 compliance) without executing fetch
- [~] T019b [US4-Stub] Implement `code/data/ingest_real.py` fallback: Default execution to load from `data/simulated/` (T014 output) to satisfy Plan's simulation scope while preserving FR-006 architecture

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Bayesian Model Execution and Comparison (Priority: P2)

**Goal**: Execute a Bayesian decision model on the preprocessed data to estimate the effect of visual salience, validating parameter recovery and scientific evidence.

**Independent Test**: The model execution can be tested by running the PyMC3 script on the synthetic data and verifying that the model recovers the `ground_truth_effect` within the 95% credible interval and converges (R-hat < 1.05).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T020 [P] [US2] Unit test for model convergence check in `code/tests/test_model_convergence.py`
- [~] T021 [US2] Unit test for parameter recovery validation in `code/tests/test_model_recovery.py`

### Implementation for User Story 2

- [~] T022 [US2] Implement `code/models/bayesian.py` defining the PyMC3 model structure: Gaussian likelihood, Normal priors, foundation scores as covariates, salience as fixed-effect predictor <!-- FAILED: unspecified -->
- [~] T023 [US2] Implement `code/models/bayesian.py` logic to handle convergence failures (log failure, fallback to MLE, flag as inconclusive)
- [~] T026 [US2] Implement `code/analysis/validation.py` to verify **Parameter Recovery**: check if `ground_truth_effect` is within the 95% credible interval of the posterior (Primary Validation Metric)
- [~] T024 [US2] Implement `code/analysis/model_comparison.py` to calculate AIC and WAIC for the salience-augmented model vs. baseline (no salience)
- [~] T025 [US2] Implement `code/analysis/model_comparison.py` to perform Posterior Predictive Checks (PPC) and visualize fit against observed data
- [~] T027 [US2] Implement `code/analysis/model_comparison.py` to explicitly check and report metrics: Detect `RUN_MODE` from `config.py`; if 'simulation', log "Validation Metric: Parameter Recovery [PASS/FAIL]" and calculate ΔAIC as "Scientific Metric: Deferred"; if 'real', flag 'strong evidence' (ΔAIC > 10) as required by SC-002

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Reporting (Priority: P3)

**Goal**: Perform hierarchical mixed-effects regression with Bonferroni correction and generate the final validation report.

**Independent Test**: The validation step can be tested by running the regression and verifying that the interaction term (salience × foundation) is reported with a Bonferroni-corrected p-value and the report includes the sensitivity analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T028 [P] [US3] Unit test for Bonferroni correction logic in `code/tests/test_model.py`
- [~] T029 [P] [US3] Unit test for sensitivity analysis thresholds in `code/tests/test_model.py`

### Implementation for User Story 3

- [~] T030 [US3] Implement `code/models/regression.py` for hierarchical mixed-effects regression testing the salience × foundation interaction
- [~] T031 [US3] Implement `code/analysis/validation.py` to apply Bonferroni correction to interaction term p-values
- [~] T032 [US3] Implement `code/analysis/validation.py` to conduct sensitivity analysis sweeping decision thresholds over the specific set **{2, 10, 20}** and report model selection stability matrix
- [~] T033 [US3] Implement `code/reports/generate_report.py` to generate the final report summarizing findings (Pipeline Validation: PASSED/FAILED)
- [~] T034 [US3] Ensure `code/reports/generate_report.py` explicitly states "Pipeline Validation Only" while including a clear statement of findings regarding the hypothesis (as per US-3), deferring final scientific claims to Phase 4 by noting "Evidence strength (ΔAIC) calculated but claim deferred per Plan."

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T035 [P] Documentation updates: Add installation instructions, update usage examples, and add data schema reference in `README.md` and `docs/`
- [~] T036 Code cleanup and refactoring
- [~] T037 Performance optimization for CPU-only execution (ensure full pipeline < 6h) <!-- ATOMIZE: requested -->
- [~] T038 [P] Implement `code/data/unity_verification.py` to verify the simulation's fidelity to the actual Unity environment by validating blend-shape parameters against a reference configuration file (addressing spec assumptions without requiring Unity runtime)
- [~] T039 [P] Additional unit tests for edge cases (missing data, convergence failure)
- [~] T040 [P] Run `quickstart.md` validation and verify all artifacts are checksummed

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Simulation/Ingestion before Preprocessing
- Model Definition before Execution
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
Task: "Unit test for synthetic MFQ generator in code/tests/test_ingest_mfq.py"
Task: "Unit test for salience mapping logic in code/tests/test_schema.py"
# T012 is not marked [P] to avoid file conflicts if shared fixtures are used.

# Launch all models for User Story 1 together:
Task: "Implement code/data/simulation_mfq.py to generate synthetic MFQ data"
Task: "Implement code/utils/norms.py validation logic"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Synthetic Data Ingestion & Validation)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify psychometric norms and schema)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (verify parameter recovery) → Deploy/Demo
4. Add User Story 3 → Test independently (verify reporting) → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Bayesian Model)
 - Developer C: User Story 3 (Validation & Reporting)
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
- **Critical Constraint**: All modeling must run on CPU-only CI (no CUDA, no 8-bit quantization). Use default precision (float64).
- **Data Integrity**: Synthetic data must have a known `ground_truth_effect` to validate the pipeline; real data ingestion (T019a/b) must define the fetch logic but defaults to simulation for this phase.