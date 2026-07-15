# Tasks: The Influence of Visual Priming on Implicit Attitudes Towards Ambiguous Social Stimuli

**Input**: Design documents from `/specs/001-the-influence-of-visual-priming-on-impli/`
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

- [X] T001a [P] Create `data/raw` directory per plan.md
- [X] T001b [P] Create `data/processed` directory per plan.md
- [X] T001c [P] Create `data/primes` directory per plan.md
- [X] T001d [P] Create `data/targets` directory per plan.md
- [X] T002a [P] Create `code/`, `tests/`, `state/` directories per plan.md
- [X] T002b [P] Create `state/projects/PROJ-345/` directory structure
- [ ] T003a [P] Create `requirements.txt` with pinned versions: `pandas==2.0.3`, `numpy==1.24.3`, `statsmodels==0.14.0`, `scikit-learn==1.3.0`, `torch` (CPU-only, pinned via `--index-url https://download.pytorch.org/whl/cpu`), `requests==2.31.0`, `pyyaml==6.0.1`, `pillow==10.0.0`
- [ ] T003b [P] Create Python 3.11 virtualenv and install dependencies from `requirements.txt` <!-- FAILED: unspecified -->
- [ ] T004 [P] Configure linting (ruff), formatting (black), and pre-commit hooks

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Setup `config.py` with paths for `data/raw`, `data/processed`, `data/primes`, `data/targets`, `state` and random seed pinning
- [ ] T006 [P] Implement `code/data/integrity.py` for Principle VI (Distinct Stimulus Set Validation) ensuring primes and targets are never merged prematurely
- [ ] T007 [P] Setup `state/projects/PROJ-345/` structure and `state.yaml` initialization script for Principle V (Versioning)
- [X] T008 [P] Create base data classes/entities for `Trial`, `Participant`, and `Stimulus` in `code/data/models.py`
- [X] T009 [P] Setup logging configuration in `code/main.py`
- [X] T010 [P] Integrate PII scanning hooks in `code/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Stimulus Metadata Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest public IAT datasets, verify visual stimulus availability, and link trial data to stimulus metadata.

**Independent Test**: Run `code/data/ingest.py` against a known OSF repository; verify `data/processed/linked_trials.csv` contains valid response times, trial IDs, and stimulus paths; verify system halts if >10% images are missing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T011 [P] [US1] Unit test for `ingest.py` URL validation and CSV parsing in `tests/unit/test_ingest.py`
- [~] T012 [P] [US1] Integration test for missing image handling (halting vs. warning) in `tests/integration/test_ingest_integration.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/ingest.py` to download IAT data from verified OSF/HF URLs (no fake data) and extract trial-level response times
- [X] T014 [US1] Implement metadata extraction in `code/data/ingest.py` to map trial IDs to stimulus image paths in `data/primes/` and `data/targets/` (respecting T006 separation)
- [X] T015 [US1] Implement "Missing Image" logic in `code/data/ingest.py`:
 - If >10% images missing: Halt and log 'Data Gap: Image files missing for >10% of trials'
 - If ≤10% missing: Log warning, exclude trials, and proceed
- [~] T016 [US1] Implement linkage derivation fallback: If metadata is missing for a trial, attempt derivation by mapping trial ID to nearest image filename via hash. If derivation fails for >10% of trials, halt with 'Data Gap: No linkage data available'. **Verify a high proportion of trials have mapped stimulus_id (or are flagged for exclusion) to meet SC-001**.
- [ ] T017 [US1] Generate `data/processed/linked_trials.csv` with columns: `trial_id`, `response_time`, `stimulus_id`, `prime_condition`, `participant_id`
- [ ] T018 [US1] Add checksum verification for downloaded raw data to `state.yaml` and **calculate/report final 'linked metadata percentage' in logs to verify against SC-001 'vast majority' target (defined as configurable threshold, default 0.95)**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Interaction Testing (Priority: P2)

**⚠️ SPEC OVERRIDE NOTE**:
The Plan's "Critical Design Change #2" (requiring human-rated ambiguity only) is **OVERRIDDEN** by Spec FR-001 and US-1 Acceptance Scenario 2.
**FR-001 mandates**: If ambiguity scores are missing, the system MUST derive them via an annotation pipeline or synthetic generation (See US-1).
**Implementation Rule**: If human-rated ambiguity is unavailable, the system MUST invoke the synthetic derivation pipeline (T020b). If that derivation fails, the analysis halts.
**DO NOT** scope analysis to "valence only" or halt prematurely; synthetic derivation is the required path.

**Goal**: Derive valence/ambiguity scores, check for confounding, and fit Linear Mixed-Effects Models (LMM) with proper random effects structure.

**Independent Test**: Run `code/models/lmm.py` on a sample subset (N=100); verify output includes fixed effects for valence/ambiguity, FDR-corrected p-values, and VIF checks; verify model converges or retries optimizers.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for VIF calculation and collinearity flagging in `tests/unit/test_metrics.py`
- [X] T020 [P] [US2] Integration test for LMM convergence failure handling and optimizer retry logic in `tests/integration/test_lmm_integration.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/data/preprocess.py` to derive prime valence using **CPU-optimized VAD regression models** (per FR-002 and Plan Critical Design Change #5) <!-- ATOMIZE: requested -->
- [X] T022a [US2] Implement `code/data/preprocess.py` to load human-rated ambiguity scores from external verified sources (if available)
- [X] T022b [US2] Implement **synthetic ambiguity derivation pipeline** in `code/data/preprocess.py` (per FR-001):
 - **Trigger**: If human-rated ambiguity (T022a) is unavailable.
 - **Logic**: Use CPU-optimized annotation pipeline or synthetic generation method.
 - **Output**: Write derived ambiguity scores to `data/processed/stimulus_metadata.csv`.
 - **Failure**: If derivation fails, halt with 'Data Gap: Ambiguity derivation failed'.
 - **Dependency**: **T022b must complete before T022 (consumer) and T024 (Modeling) can start.**
- [~] T023 [US2] Implement confounding check in `code/data/preprocess.py` (after T021/T022b) to verify "prime" is not confounded with trial order/block structure. **Output artifact: `data/processed/confounding_report.json` (correlation matrix, trial-order check results)**.
- [X] T024 [US2] Implement `code/models/lmm.py` to aggregate data to `Stimulus` level (mean response time per stimulus per participant) to ensure within-stimulus variance
- [X] T025 [US2] Implement LMM fitting in `code/models/lmm.py`: `mean_response_time ~ prime_valence * stimulus_ambiguity + (1 | participant_id)` (NO `stimulus_id` as random effect)
- [X] T026 [US2] Implement optimizer retry logic in `code/models/lmm.py`: On convergence failure, attempt alternative optimizers before flagging dataset as unsuitable
- [X] T027a [US2] Implement `code/models/metrics.py` to calculate VIF; flag if VIF > 5.0 and refrain from claiming independent effects
- [X] T027b [US2] Implement **model convergence success rate measurement** in `code/models/metrics.py`:
 - **Action**: Measure, log, and report the percentage of models converging within 3 optimizer attempts.
 - **Output artifact**: `state/model_convergence_metrics.json` (contains `convergence_rate`, `total_attempts`, `configurable_threshold`).
 - **Verify**: Against SC-002 design target (configurable threshold, default 0.80).
- [X] T028 [US2] Implement FDR correction (Benjamini-Hochberg) in `code/models/metrics.py` for multiple hypothesis tests
- [~] T029 [US2] Ensure all model outputs frame findings as "associational" (not causal) per FR-003

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reporting and Visualization Generation (Priority: P3)

**Goal**: Generate interaction plots, coefficient tables, and sensitivity analysis summaries in a PDF report.

**Independent Test**: Run `code/reports/generate_report.py`; verify PDF contains interaction plots, coefficient tables with CIs, and alpha sensitivity analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for Cohen's d and partial eta-squared calculation with bootstrapping in `tests/unit/test_metrics.py`
- [X] T031 [P] [US3] Integration test for PDF report generation and artifact completeness in `tests/integration/test_report_generation.py`

### Implementation for User Story 3

- [X] T032 [US3] Implement `code/models/metrics.py` to compute effect sizes (Cohen's d, partial eta-squared) with confidence intervals via bootstrapping
- [X] T033 [US3] Implement `code/viz/plots.py` to generate interaction plots showing response time differences across prime valence conditions
- [X] T034 [US3] Implement `code/viz/plots.py` to generate coefficient tables with p-values and confidence intervals
- [~] T035 [US3] Implement `code/models/metrics.py` for alpha sensitivity analysis: **Sweep significance thresholds (, standard levels, 0.10)** and **generate output artifact `data/processed/sensitivity_analysis.csv` (columns: alpha, significance_rate)** per FR-006
- [X] T036 [US3] Implement `code/reports/generate_report.py` to compile plots, tables, and sensitivity summaries into a single PDF
- [~] T037 [US3] Ensure report explicitly cites the "observational nature" and "derived prime valence" limitations

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T038 [P] Documentation updates in `docs/` and `quickstart.md`
- [~] T039 Code cleanup and refactoring of `data/` and `models/` modules
- [~] T040 Performance optimization: Ensure data chunking/sampling logic handles datasets >7GB RAM
- [~] T041 [P] Additional unit tests for edge cases (missing metadata, high collinearity) in `tests/unit/`
- [~] T042 Security hardening: Verify no PII leakage in `data/processed/` outputs
- [~] T043 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 data output (`linked_trials.csv`)**
 - **CRITICAL**: T021 (Valence) and T022b (Ambiguity) MUST complete before T024 (Modeling).
 - **CRITICAL**: T023 (Confounding Check) MUST complete before T024 and T025 (Modeling).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Hard Blockers (Explicit Execution Order)

- **T016** (Linkage) must complete before **T022b** (Ambiguity) and **T024** (Modeling).
- **T022b** (Synthetic Ambiguity) must complete before **T024** (Modeling).
- **T021** (Valence) must complete before **T024** (Modeling).
- **T023** (Confounding Check) must complete before **T024** and **T025** (Modeling).

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
Task: "Unit test for ingest.py URL validation in tests/unit/test_ingest.py"
Task: "Integration test for missing image handling in tests/integration/test_ingest_integration.py"

# Launch all models for User Story 1 together:
Task: "Implement ingest.py to download IAT data"
Task: "Implement metadata extraction in ingest.py"
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