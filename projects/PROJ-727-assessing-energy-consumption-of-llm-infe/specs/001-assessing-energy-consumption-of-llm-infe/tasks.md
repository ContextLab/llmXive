# Tasks: Assessing Energy Consumption of LLM Inference for Code Completion

**Input**: Design documents from `/specs/001-assessing-energy-consumption/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-727-assessing-energy-consumption-of-llm-infe/`)
- [X] T002 Initialize Python 3.10+ project with `requirements.txt` (transformers, torch-cpu, codecarbon, pandas, numpy, scipy, statsmodels, matplotlib, seaborn, human-eval, huggingface_hub)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes formal amendments to spec/plan for feasibility constraints.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005a [AMEND] Update `spec.md` (FR-001, US-1) and `plan.md` to explicitly replace 'StarCoder-base' with 'StarCoder-1B' and authorize this substitution due to RAM constraints. Ensure the spec text is updated BEFORE any code implementation begins (FR-001, Plan Feasibility Note).
- [X] T004 Create `code/config.py` with constants: seeds, model IDs (GPT2-small, CodeBERT, StarCoder-1B), parameter counts, max tokens, temperature=0.0. Ensure data/raw/ directory exists.
- [X] T005 [P] Create `code/download.py` to fetch HumanEval dataset from ` and save to `data/raw/human_eval_data.jsonl`. Ensure data/raw/ directory exists before saving (FR-001).
- [X] T006 Create `code/calibration.py` implementing a CPU-bound load loop (not matrix multiply) to validate `codecarbon` power draw detection. The script must exit with code 1 or raise an exception if deviation > 10% (FR-010).
- [ ] T007 Create `code/versioning.py` to hash artifacts and update project state YAML (Constitution Principle V)
- [ ] T008 Create `run.sh` entry point that verifies environment by importing `human_eval`, running a specific trivial dummy test case (e.g., `def add(a,b): return a+b`), and exiting with code 1 on failure (FR-007)
- [ ] T009 Create `data/raw/` directory structure and checksum verification logic for HumanEval <!-- ATOMIZE: requested -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Energy-to-Token Metrics (Priority: P1) 🎯 MVP

**Goal**: Execute inference for GPT-2-small, CodeBERT, and StarCoder-1B on HumanEval using CPU, logging energy (kWh), runtime, and tokens via `codecarbon`.

**Independent Test**: Run `run.sh` on a fresh GitHub Actions runner; verify `codecarbon` logs exist for all three models and `results.csv` contains non-null values for `model_id`, `tokens_generated`, `energy_kwh`, and `pass_fail_status` for every problem.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/inference.py`: Load models sequentially (GPT2 -> CodeBERT -> StarCoder-1B) with explicit unload logic to free RAM; run `codecarbon` context; generate completions (temp=0.0); write results to `data/processed/energy_results_raw.csv` with schema: `model_id`, `problem_id`, `tokens_generated`, `energy_kwh`, `runtime_seconds`, `pass_fail_status` (FR-002, FR-003, FR-009). T013 is the exclusive producer of this raw file.
- [ ] T014 [US1] Implement `code/evaluation.py`: Evaluate generated completions against HumanEval test suite, record `pass_fail_status` (0/1), handle timeouts/OOMs gracefully (FR-004)
- [~] T015 [US1] Implement logic in `code/inference.py` to handle edge cases: record `null` energy if calibration fails, record `null` tokens if 0 tokens generated (FR-009)
- [~] T016 [US1] Implement data aggregation in `code/main.py` to read `energy_results_raw.csv`, filter out rows where `energy_kwh` is `null` or `tokens_generated` is 0 (FR-011), and write the clean dataset to `data/processed/energy_results_aggregated.csv` with columns: `model_id`, `problem_id`, `tokens_generated`, `energy_kwh`, `runtime_seconds`, `pass_fail_status`.
- [~] T017 [US1] Add logging for energy metrics and model unload events in `code/inference.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (raw data generated)

---

## Phase 4: User Story 2 - Statistical Analysis of Energy vs. Model Size (Priority: P2)

**Goal**: Perform Repeated-Measures ANOVA, Tukey HSD, and descriptive linear regression on collected data.

**Independent Test**: Execute `code/analysis.py` on `energy_results_aggregated.csv`; verify ANOVA table (p-value), Tukey HSD table, and regression output (slope, R-squared) are printed/saved.

### Implementation for User Story 2

- [~] T021 [US2] Implement Repeated-Measures ANOVA with `problem_id` as blocking factor in `code/analysis.py` using data from `energy_results_aggregated.csv` (FR-005)
- [~] T022 [US2] Implement post-hoc Tukey HSD test in `code/analysis.py` (FR-005)
- [~] T023 [US2] Implement descriptive linear regression (Parameter Count vs. Energy/Token) in `code/analysis.py`, explicitly framing as observational (FR-005, FR-008)
- [~] T024a [US2] Implement sensitivity analysis: create a perturbed dataset copy with ±10% energy value perturbation, re-run ANOVA on this perturbed dataset, and calculate the delta p-values (FR-012).
- [~] T024b [US2] Write the sensitivity comparison results (original p-value vs. perturbed p-value, delta, robustness flag) to `data/processed/sensitivity_delta.csv` (FR-012).
- [~] T025 [US2] Write `data/processed/stats_report.csv` containing ANOVA table, Tukey results, regression coefficients, and sensitivity findings with defined column headers (FR-005, FR-012)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (raw data + stats)

---

## Phase 5: User Story 3 - Generate Sustainability Trade-off Visualizations (Priority: P3)

**Goal**: Generate bar plot (Energy/Token vs Model) and scatter plot (Energy/Correct vs Accuracy).

**Independent Test**: Run plotting script; verify existence of two PNG files with correct axes, labels, and legends.

### Implementation for User Story 3

- [~] T027 [US3] Implement `code/visualization.py`: Load data strictly from `data/processed/energy_results_aggregated.csv` (clean source) to calculate metrics; do not use raw data (FR-006, Constitution Principle IV)
- [~] T028 [US3] Generate Bar Plot: Y=Energy per Token (Joules), X=Model ID, include error bars if applicable (FR-006, US-3-1)
- [~] T029 [US3] Generate Scatter Plot: Y=Energy per Correct Solution, X=Pass@1 Accuracy, distinct markers per model (FR-006, US-3-2)
- [~] T030 [US3] Ensure all plots include title, axis labels with units, and legend; save as `data/processed/` (e.g., `energy_bar.png`, `tradeoff_scatter.png`) (FR-006, US-3-3)
- [~] T030b [US3] Calculate and record the slope of the curve connecting the models on the scatter plot in `data/processed/scatter_slope.txt` to satisfy SC-004 (FR-006, SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T031 [P] Documentation updates: Update `quickstart.md` with run instructions and expected artifacts
- [~] T032 Code cleanup and refactoring of `code/main.py` orchestrator
- [~] T033 Verify `run.sh` completes full pipeline (Inference + Stats + Plots) within 6 hours on free-tier runner
- [~] T034 [P] Final validation: Run `run.sh` on clean GitHub Actions runner to ensure all artifacts are generated and non-null where required <!-- ATOMIZE: requested -->

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation (specifically `energy_results_aggregated.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 aggregated metrics

### Within Each User Story

- Models/Config before Services
- Services before Endpoints/Scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T005a must be first)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (ensure CSV generated with real data)
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
 - Developer A: User Story 1 (Inference)
 - Developer B: User Story 2 (Stats)
 - Developer C: User Story 3 (Plots)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Feasibility Check**: All tasks assume CPU-only execution (limited cores, constrained RAM). A StarCoder-1B model is used instead of StarCoder-base to prevent OOM... No GPU quantization or 8-bit loading is permitted.
- **Data Integrity**: Tasks explicitly forbid synthetic data. All analysis must consume real HumanEval data and real `codecarbon` logs.
- **Single Source of Truth**: All visualizations and statistics must derive from `data/processed/energy_results_aggregated.csv`.