# Tasks: APPO: Agentic Procedural Policy Optimization

**Input**: Design documents from `/specs/001-appo-agentic-procedural-policy-optimizat/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` with exact paths: `code/app/__init__.py`, `code/app/agent.py`, `code/app/environments.py`, `code/app/metrics.py`, `code/app/stats.py`, `code/cli/train.py`, `code/config/baseline.yaml`, `code/config/default.yaml`, `code/config/ablation.yaml`, `code/tests/test_metrics.py`, `code/tests/test_pipeline.py`.
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pins: `torch==2.1.0+cpu`, `transformers==4.37.0`, `datasets==2.16.0`, `scikit-learn==1.4.0`, `lifelines==0.28.0`, `pandas==2.1.0`, `numpy==1.26.0`, `accelerate==0.26.0`, `llama-cpp-python==0.2.50`, `pytest==7.4.0`, `ruff==0.1.0`, `black==23.12.0`).
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 [P] Implement data loading logic in `code/app/environments.py` to fetch **MATH dataset only** (HotpotQA/WebShop excluded due to unverified URLs) from HuggingFace (`datasets.load_dataset("HuggingFaceH4/MATH")`), cache to `data/raw/` with **SHA-256 checksums**, and save to `data/raw/math_{version}.json`.
- [ ] T011a [P] Log dataset version hashes and validation split info to `data/benchmark_logs/` with SHA-256 checksums as required by Constitution VII.
- [ ] T007 [P] Create `code/app/environments.py`: Synthetic tool-use wrapper for **MATH dataset** (Search/Calculate actions) using loaded data.
- [ ] T007a [P] Implement `code/app/agent.py` model loader: Load Llama 3.1 8B in CPU mode using **4-bit GGUF** via `llama-cpp-python`, sequence length 256, max memory < 7GB (FR-001).
- [ ] T008 [P] Implement `code/app/metrics.py`: Token entropy calculator, Future Value (V(s)) estimator, Branching Score logic.
- [ ] T009 [P] Implement `code/app/stats.py`: Kaplan-Meier estimator, Log-Rank test, Pearson correlation, Variance calculation.
- [ ] T010 [P] Implement `code/cli/train.py`: Entry point with `--config`, `--seed` flags; argument parsing logic.
- [ ] T010a [P] Implement 4-bit GGUF loading logic in `code/cli/train.py` (call T007a loader) with OOM error catching and graceful abort.
- [ ] T010b [P] Implement hard step limit (**50k steps**) enforcement in `code/cli/train.py`, timeout detection, and partial checkpoint saving (FR-008).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline & Score-Default Execution (Priority: P1) 🎯 MVP

**Goal**: Execute training for "No-Score" and "Score-Default" configurations on CPU to establish sample efficiency baseline.

**Independent Test**: Run `python code/cli/train.py --config=baseline --seed=0` and `--config=default --seed=0`. Verify completion within 6h, CSV logs generated, and "steps to 80% threshold" recorded.

### Tests for User Story 1

- [ ] T012 [P] [US1] Write test stubs for Branching Score calculation in `code/tests/test_metrics.py` (verify product of entropy and V(s))
- [ ] T013 [P] [US1] Write test stubs for pipeline completion in `code/tests/test_pipeline.py` (run multiple steps, verify CSV output)

### Implementation for User Story 1

- [ ] T014 [US1] Implement PPO agent logic in `code/app/agent.py` (No-Score baseline mode) with hyperparameters: clip=0.2, gamma=0.99, lambda=0.95.
- [ ] T015 [US1] Implement Branching Score reward bonus injection in `code/app/agent.py` (Score-Default mode: ε=0.1, ε′=0.05, b=0.5).
- [ ] T016 [US1] Implement "steps to reach **0.8** threshold" calculation with linear interpolation in `code/app/metrics.py`; output format: float (Depends on T008).
- [ ] T017 [US1] Implement logging of step-wise metrics (success rate, tool calls, Branching Score) to `results/training_logs.csv` (Depends on T016).
- [ ] T018 [US1] Implement timeout detection and partial checkpoint saving in `code/cli/train.py` (T010b dependency).
- [ ] T019 [US1] Implement OOM error catching and graceful abort in `code/cli/train.py` (T010a dependency).
- [ ] T014a [US1] Implement seed-loop logic for **2 independent seeds** and aggregation of results across seeds for statistical analysis (FR-004, SC-006).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hyperparameter Ablation & Sensitivity Analysis (Priority: P2)

**Goal**: Run ablation suite to vary ε, ε′, b and perform sensitivity analysis.

**Independent Test**: Run ablation loop over grid. Verify sensitivity report generated showing variance in "episodes to threshold".

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test for grid iteration logic in `code/tests/test_ablation.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement ablation loop in `code/cli/train.py` (iterates over **limited subset (2 configs)** from `ablation.yaml` grid; generate `results/ablation_summary.csv`).
- [ ] T022 [US2] Implement sensitivity analysis report generator in `code/app/stats.py` (variance calculation across grid).
- [ ] T022a [US2] Calculate variance of steps-to-threshold across **executed subset** and compare against **15% threshold** defined in SC-002.
- [ ] T023 [US2] Implement "Best Ablation" selection logic (lowest mean steps-to-threshold with ≥80% success) in `code/app/stats.py`.
- [ ] T024 [US2] Implement Pearson correlation check (|r| < 0.9) and warning logging in `code/app/metrics.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Reporting (Priority: P3)

**Goal**: Generate final report with statistically significant results (p < 0.05) comparing best variant vs baseline.

**Independent Test**: Run analysis script on aggregated CSVs. Verify output includes t-statistics, p-values, confidence intervals, and Kaplan-Meier plots.

### Tests for User Story 3

- [ ] T025 [P] [US3] Unit test for Kaplan-Meier and Log-Rank test in `code/tests/test_stats.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement data aggregation script to parse `results/training_logs.csv` across all seeds/configs.
- [ ] T027 [US3] Implement Kaplan-Meier survival analysis and Log-Rank test in `code/app/stats.py`.
- [ ] T028 [US3] Implement final report generation (`results/summary_report.md`) including **Table 1: Mean steps-to-threshold**, **Figure 1: KM Curve**, and p-values.
- [ ] T028a [US3] Calculate **tool-call efficiency** (average tool calls per episode at threshold crossing) and compare against baseline (SC-003).
- [ ] T029 [US3] Implement censored data handling (flag as ">50k steps" or "censored") in `code/app/metrics.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030a [P] Update `README.md` sections: Installation, Usage, Results.
- [ ] T030b [P] Update `docs/quickstart.md` with step-by-step execution guide.
- [ ] T031a Code cleanup: Extract metrics calculation to separate module in `code/app/metrics.py`.
- [ ] T031b Code cleanup: Refactor imports in `code/app/agent.py` and `code/cli/train.py` for clarity.
- [ ] T032 [P] Additional unit tests for edge cases (censored data, OOM) in `code/tests/`.
- [ ] T033 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **T011 (Data Loading)** is a hard blocker for **T007 (Environment)** and **T007a (Model Loader)**.
  - **T007** and **T007a** can run in parallel after T011 completes.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel **AFTER T011 completes** (T007, T007a).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Write test stubs for Branching Score calculation in code/tests/test_metrics.py"
Task: "Write test stubs for pipeline completion in code/tests/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement PPO agent logic in code/app/agent.py"
Task: "Implement Branching Score reward bonus injection in code/app/agent.py"
Task: "Implement seed-loop and result aggregation for 2 seeds in code/cli/train.py"
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

- [P] tasks = different files, no dependencies (after T011 completion for Phase 2)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Feasibility Note**: All training tasks MUST use 4-bit GGUF model loading via `llama-cpp-python`, limit steps to **50k**, and use **2 seeds** to fit 6h/7GB constraints.
- **Data Note**: Only **MATH** dataset is used; HotpotQA/WebShop excluded due to unverified URLs.