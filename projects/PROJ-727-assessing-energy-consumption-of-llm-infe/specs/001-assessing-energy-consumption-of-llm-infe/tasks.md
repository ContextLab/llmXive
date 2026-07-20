# Tasks: Assessing Energy Consumption of LLM Inference for Code Completion

**Input**: Design documents from `/specs/001-assessing-energy-consumption/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-727-assessing-energy-consumption-of-llm-infe/`)
- [X] T002 Initialize Python 3.x+ project with `requirements.txt` (transformers, torch-cpu, codecarbon, pandas, numpy, scipy, statsmodels, matplotlib, seaborn, human-eval, huggingface_hub)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes formal amendments to spec/plan for feasibility constraints.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005a [AMEND] Update `spec.md` (FR-001, US-1) to explicitly replace 'StarCoder-base' with 'StarCoder-1B' and authorize this substitution due to RAM constraints. Verify update with `grep 'StarCoder-1B' spec.md`.
- [X] T005b [AMEND] Update `plan.md` to explicitly replace 'StarCoder-base' with 'StarCoder-1B' and authorize this substitution due to RAM constraints. Verify update with `grep 'StarCoder-1B' plan.md`.
- [X] T004 Create `code/config.py` with constants: seeds, model IDs (GPT2-small, CodeBERT, StarCoder-1B), parameter counts, max tokens, temperature=0.0. Ensure data/raw/ directory exists.
- [X] T005 [P] Create `code/download.py` to fetch HumanEval dataset from ` and save to `data/raw/human_eval_data.jsonl`. Ensure data/raw/ directory exists before saving (FR-001).
- [X] T008a [P] Create `tests/test_dummy.py` containing a function `test_dummy_inference` that performs a lightweight import check and a single-token generation using a small dummy prompt (no full model load) to verify environment without OOM risk. **Verification**: Run `pytest tests/test_dummy.py::test_dummy_inference` locally; ensure it exits with code 0.
- [ ] T008b [P] Create `run.sh` script content that orchestrates the pipeline: imports modules, runs T008a test, and exits with code 1 on failure. **Verification**: Ensure `run.sh` is executable and contains the correct logic.
- [X] T008 Create `run.sh` entry point that verifies environment by running `tests/test_dummy.py::test_dummy_inference` (which executes the lightweight dummy test) and exiting with code 1 on failure (FR-007). **Verification**: Run `run.sh` locally; ensure it exits with code 0 and prints "Environment Verified". **Depends on**: T008a, T008b.
- [X] T006 Create `code/calibration.py` implementing a CPU-bound load loop (not matrix multiply) to validate `codecarbon` power draw detection. The script must exit with code 1 or raise an exception if deviation > 10% (FR-010).
- [X] T007 Create `code/versioning.py` to hash artifacts and update project state YAML (Constitution Principle V)
- [ ] T009 Create `data/raw/` directory structure. Implement checksum verification logic: calculate SHA-256 hash of `data/raw/human_eval_data.jsonl` immediately after T005 download and record it in `state/projects/PROJ-727-assessing-energy-consumption-of-llm-infe.yaml` under `artifact_hashes` (Constitution Principle III). **Verify**: The hash is present and verified BEFORE T013 uses the data. **Depends on**: T005.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Energy-to-Token Metrics (Priority: P1) 🎯 MVP

**Goal**: Execute inference for GPT-2-small, CodeBERT, and StarCoder-1B on HumanEval using CPU, logging energy (kWh), runtime, and tokens via `codecarbon`.

**Independent Test**: Run `run.sh` on a fresh GitHub Actions runner; verify `codecarbon` logs exist for all three models and `results.csv` contains non-null values for `model_id`, `tokens_generated`, `energy_kwh`, and `pass_fail_status` for every problem.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/inference.py`: Load models sequentially (GPT2 -> CodeBERT -> StarCoder-1B) with explicit unload logic to free RAM; run `codecarbon` context to measure energy; count tokens generated per problem **using the model's associated tokenizer**; write raw inference logs to `data/processed/energy_inference_raw.csv` with schema: `model_id`, `problem_id`, `tokens_generated`, `energy_kwh`, `runtime_seconds`. **Do NOT include pass_fail_status here**. **Verification**: Ensure `data/processed/energy_inference_raw.csv` exists and contains rows for all three models.
- [ ] T014 [US1] Implement `code/evaluation.py`: Evaluate generated completions against HumanEval test suite, record `pass_fail_status` (0/1), handle timeouts/OOMs gracefully (FR-004). Join results with `energy_inference_raw.csv` to create `data/processed/energy_results_raw.csv` with full schema: `model_id`, `problem_id`, `tokens_generated`, `energy_kwh`, `runtime_seconds`, `pass_fail_status`. **Verification**: Ensure `data/processed/energy_results_raw.csv` exists and contains the joined data.
- [X] T015 [US1] Implement logic in `code/inference.py` to handle edge cases: record `null` energy if calibration fails, record `null` tokens if 0 tokens generated (FR-009).
- [ ] T016 [US1] Implement data aggregation in `code/main.py` to read `energy_results_raw.csv`. **Filter** rows where `energy_kwh` is `null` or `tokens_generated` is 0. **Save** these filtered rows to `data/processed/filtered_rows.csv` to preserve evidence of failure (FR-009, Constitution Principle VI). Write the clean dataset to `data/processed/energy_results_aggregated.csv` with columns: `model_id`, `problem_id`, `tokens_generated`, `energy_kwh`, `runtime_seconds`, `pass_fail_status`. **Verification**: Verify `data/processed/energy_results_aggregated.csv` exists and contains zero rows where `energy_kwh` is null or `tokens_generated` is 0.
- [X] T017 [US1] Add logging for energy metrics and model unload events in `code/inference.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (raw data generated)

---

## Phase 4: User Story 2 - Statistical Analysis of Energy vs. Model Size (Priority: P2)

**Goal**: Perform Repeated-Measures ANOVA, Tukey HSD, and descriptive linear regression on collected data.

**Independent Test**: Execute `code/analysis.py` on `energy_results_aggregated.csv`; verify ANOVA table (p-value), Tukey HSD table, and regression output (slope, R-squared) are printed/saved.

**⚠️ DEPENDENCY**: All tasks in this phase depend on T016 (aggregation) being complete.

### Implementation for User Story 2

- [X] T021 [US2] Implement Repeated-Measures ANOVA with `problem_id` as blocking factor in `code/analysis.py` using data from `energy_results_aggregated.csv` (FR-005)
- [X] T022 [US2] Implement post-hoc Tukey HSD test in `code/analysis.py` (FR-005)
- [X] T023 [US2] Implement descriptive linear regression (Parameter Count vs. Energy/Token) in `code/analysis.py`, explicitly framing as observational (FR-005, FR-008)
- [X] T023b [US2] Write the textual report framing the regression results as **observational** (non-causal) to `data/processed/stats_report.csv` or a dedicated text block, explicitly stating that correlation does not imply causation (FR-008). **Verification**: Verify the text "observational" or "correlation does not imply causation" appears in the report.
- [X] T024a [US2] Implement sensitivity analysis: create a perturbed dataset copy with ±10% energy value perturbation using **random seed=42** for determinism. Re-run ANOVA using **scipy.stats.f_oneway** on this perturbed dataset, and calculate the delta p-values. **Output**: Write the original p-value, perturbed p-value, and delta to `data/processed/sensitivity_delta.csv` (FR-012).
- [X] T024b [US2] Write the sensitivity comparison results (original p-value vs. perturbed p-value, delta, robustness flag) to `data/processed/sensitivity_delta.csv` (FR-012).
- [X] T025 [US2] Write `data/processed/stats_report.csv` containing ANOVA table, Tukey results, regression coefficients, and sensitivity findings with defined column headers (FR-005, FR-012)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (raw data + stats)

---

## Phase 5: User Story 3 - Generate Sustainability Trade-off Visualizations (Priority: P3)

**Goal**: Generate bar plot (Energy/Token vs Model) and scatter plot (Energy/Correct vs Accuracy).

**Independent Test**: Run plotting script; verify existence of two PNG files with correct axes, labels, and legends.

**⚠️ DEPENDENCY**: All tasks in this phase depend on T016 (aggregation) being complete.

### Implementation for User Story 3

- [X] T027 [US3] Implement `code/visualization.py`: Load data strictly from `data/processed/energy_results_aggregated.csv` (clean source) to calculate metrics; do not use raw data (FR-006, Constitution Principle IV)
- [ ] T028 [US3] Generate Bar Plot: Y=Energy per Token (Joules), X=Model ID. **Include error bars** if `standard deviation > 0` (calculate using `numpy.std`), using `matplotlib.pyplot.errorbar`. **Include a legend**. Save the plot to `data/processed/energy_bar.png` (FR-006, US-3-1). **Verification**: Implement a validation step to programmatically confirm the plot file exists and contains a title, x-axis label, y-axis label, and legend.
- [ ] T029 [US3] Generate Scatter Plot: Y=Energy per Correct Solution, X=Pass@1 Accuracy, distinct markers per model. **Include a legend**. Save the plot to `data/processed/tradeoff_scatter.png` (FR-006, US-3-2). **Verification**: Implement a validation step to programmatically confirm the plot file exists and contains a title, x-axis label, y-axis label, and legend.
- [ ] T030b [US3] Calculate and record the slope of the curve connecting the models on the scatter plot in `data/processed/scatter_slope.txt`. **Read the data from `data/processed/energy_results_aggregated.csv`** (not the image file) to calculate the slope between model centroids (FR-006).
- [ ] T030c [US3] Ensure all plots (`data/processed/energy_bar.png`, `data/processed/tradeoff_scatter.png`) include title, axis labels with units, and legend. Implement a validation step to programmatically confirm these elements exist using `matplotlib.pyplot.gca().get_title()` and similar methods. **Verification**: Assert that the generated artifacts meet the spec requirements (FR-006, US-3-3).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates: Update `quickstart.md` with run instructions and expected artifacts. **Verification**: Ensure `quickstart.md` exists and contains steps to run the full pipeline.
- [X] T032 Code cleanup and refactoring of `code/main.py` orchestrator
- [ ] T033 Verify `run.sh` completes full pipeline (Inference + Stats + Plots) within 6 hours on free-tier runner. Record the total execution time in `logs/pipeline_duration.log` and assert it is < 21600 seconds (spec.md Constraints). **Verification**: Run `run.sh` and verify `logs/pipeline_duration.log` exists with a timestamp and duration < 21600s.
- [ ] T034 [P] Final validation: Run `run.sh` on clean GitHub Actions runner to ensure all artifacts are generated and non-null where required. **Verification**: Confirm existence of `data/processed/energy_results_aggregated.csv`, `data/processed/stats_report.csv`, `data/processed/energy_bar.png`, `data/processed/tradeoff_scatter.png`, and `logs/pipeline_duration.log`.

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