# Tasks: llmXive follow-up: extending "Agentic Abstention: Do Agents Know When to Stop Instead of Act?"

**Input**: Design documents from `/specs/001-llmxive-abstention-meta-critic/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (as per `plan.md` structure)
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

- [ ] T001 Create project structure per `plan.md` (`code/`, `data/`, `tests/`, `state/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (xgboost, sentence-transformers, pandas, scikit-learn, lifelines, pyyaml, numpy)
- [ ] T003 [P] Configure linting (flake8/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `contracts/dataset.schema.yaml` enforcing exclusion of full semantic context text columns
- [ ] T005 Create `contracts/output.schema.yaml` for model metrics and simulation logs
- [ ] T006 [P] Setup `data/` directory structure (`raw/`, `processed/`) and checksum scripts
- [X] T007 Implement `code/__init__.py` and basic logging configuration in `code/logging_config.py`
- [X] T008 Setup environment configuration management (load seeds, paths from `.env` or `config.yaml`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Ingest the "Agentic Abstention" benchmark (or Synthetic Simulator) and extract low-level state features to create a training-ready dataset.

**Independent Test**: The pipeline runs on the subset and produces a CSV/Parquet file with the correct schema (search count, error freq, tokens, turns, embedding distance, label) and no full text context.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test for `code/data/extract_features.py` schema validation in `tests/contract/test_schema.py`
- [X] T010 [P] [US1] Integration test for data ingestion pipeline in `tests/integration/test_ingest_pipeline.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/data/ingest.py` to fetch and verify the REAL "Agentic Abstention" benchmark dataset as the PRIMARY source; ONLY fallback to `code/data/simulator.py` (Synthetic Agent Simulator) if the real benchmark is unavailable or fails verification (per FR-001 and Constitution Principle II). Sequence: 1) Fetch/Verify Benchmark, 2) If fail, fallback to Simulator.
- [X] T012 [US1] Implement `code/oracle/solver.py` to create the independent bounded exhaustive search solver (limited token budget) that determines task impossibility (FR-002)
- [ ] T012.5 [US1] Execute the solver from T012 on the ingested dataset to generate the ground truth "Abstention Label" column and write the results to `data/processed/labels.parquet` (FR-002)
- [X] T013 [US1] Implement `code/data/extract_features.py` to parse interaction trajectories and compute: search count, error frequency, token usage, turn number
- [X] T014 [US1] Implement `code/data/extract_features.py` logic to compute "query-context embedding distance" using `sentence-transformers` (all-MiniLM-L6-v2) as a scalar proxy
- [X] T015 [US1] Implement `code/data/extract_features.py` logic to derive "Abstention Label" by joining with the output from T012.5 (FR-002)
- [~] T016 [US1] Implement `code/data/preprocess.py` to apply mean imputation for missing numeric variables AND implement explicit "halt execution" logic that generates a `data/validation_report.json` flagging the dataset as invalid if >5% of records are missing a critical variable (FR-007)
- [ ] T017 [US1] Verify output file `data/processed/features.parquet` contains no full semantic context strings and matches `dataset.schema.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Meta-Critic Model Training and Evaluation (Priority: P2)

**Goal**: Train a CPU-optimized gradient-boosted tree classifier on the extracted features and evaluate against a full-context baseline.

**Independent Test**: Training completes on 2-core CPU within 6h, producing a model file and a report showing Timely Abstention Recall, Token Consumption, and Latency vs. baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Contract test for `code/models/train_meta_critic.py` output schema in `tests/contract/test_model_output.py`
- [~] T019 [P] [US2] Integration test for simulation loop in `tests/integration/test_simulation_loop.py`

### Implementation for User Story 2

- [ ] T020.0 [US2] Acquire, integrate, and pin the reference CONVOLVE implementation (commit/tag) to `code/simulation/convolve_ref/` to ensure the baseline matches the spec (FR-003)
- [ ] T020 [US2] Implement `code/models/train_meta_critic.py` using XGBoost/LightGBM on CPU to predict abstention labels from state features (FR-002)
- [ ] T020.5 [US2] Implement `code/simulation/simulation_framework.py` to build the agent interaction loop where the meta-critic evaluates state *before* LLM action, integrating the reference baseline from T020.0 (FR-003)
- [ ] T021 [US2] Implement `code/simulation/run_baseline.py` to run the reference CONVOLVE implementation (seed=42, max 20 turns) via the simulation framework from T020.5 (FR-003)
- [ ] T022 [US2] Implement `code/models/evaluate.py` to run the simulation loop (using T020.5) where the Meta-Critic evaluates state *before* LLM action, calculate Timely Abstention Recall, Average Token Consumption, Wall-clock Latency, explicitly calculate the token reduction percentage vs baseline, and verify if reduction >= 40% OR Cohen's d >= 0.5 (FR-004, SC-002)
- [ ] T023 [US2] Add logging for the specific turn number and feature vector when Meta-Critic triggers abstention for auditability
- [ ] T024 [US2] Generate `data/results/baseline_comparison.json` containing metrics for both Meta-Critic and Full-Context conditions

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical significance testing and sensitivity analysis on the abstention threshold.

**Independent Test**: Analysis script generates a report confirming statistical significance (p < 0.05) and visualizes error rate variation across thresholds.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for `code/analysis/statistical_tests.py` output in `tests/contract/test_stats_output.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/analysis/statistical_tests.py` to perform Two-sample Kolmogorov-Smirnov or Mann-Whitney U test on token consumption distributions (FR-005)
- [ ] T027 [US3] Implement `code/analysis/survival_analysis.py` to perform Survival Analysis using the `lifelines` library to handle censored data, WHILE ALSO explicitly implementing the Two-sample Kolmogorov-Smirnov or Mann-Whitney U test required by FR-005 to validate the null hypothesis (FR-005)
- [ ] T028 [US3] Implement `code/analysis/sensitivity_analysis.py` to sweep decision threshold over a range of values and calculate false-positive/negative rates (FR-006)
- [ ] T029 [US3] Implement collinearity diagnostics (VIF) in `code/analysis/statistical_tests.py` to check predictors like turn number vs. token usage
- [ ] T030 [US3] Generate `data/results/statistical_report.md` containing p-values, effect sizes (Cohen's d), survival analysis results, and threshold sensitivity plots
- [ ] T031 [US3] Validate that the null hypothesis (median difference = 0) is rejected with p < 0.05 for token consumption reduction (SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T033 Code cleanup and refactoring of `code/` modules
- [ ] T034 [US2] Performance optimization for CPU training loop: Run training on CI and assert runtime < 6h (verify constraint)
- [ ] T035 [P] Run `pytest` suite and verify all contract/integration tests pass
- [ ] T036 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for feature data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for metrics

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion before feature extraction
- Feature extraction before model training
- Model training before statistical analysis
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
Task: "Contract test for schema validation in tests/contract/test_schema.py"
Task: "Integration test for data ingestion pipeline in tests/integration/test_ingest_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement ingest.py in code/data/ingest.py"
Task: "Implement extract_features.py in code/data/extract_features.py"
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Model)
 - Developer C: User Story 3 (Stats)
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
- **Constraint**: All tasks must run on free CPU-only CI (limited cores, limited RAM, 6h limit). No GPU, no low-bit quantization, no large LLMs.
- **Data**: Use real benchmark data or verified synthetic simulator. No fabricated data.