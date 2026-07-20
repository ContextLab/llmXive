# Tasks: Assessing Energy Consumption of LLM Inference for Code Completion

**Input**: Design documents from `/specs/001-assessing-energy-consumption/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Note**: The substitution of 'StarCoder-base' with 'StarCoder-1B' is authorized by FR-001 in `spec.md`. All tasks must reference FR-001.

- [X] T004 Create `code/config.py` with constants: seeds, model IDs (GPT-small, CodeBERT, StarCoder-1B), parameter counts, max tokens, temperature=0.0. Ensure data/raw/ directory exists.
- [X] T005 [P] Create `code/download.py` to fetch HumanEval dataset from ` (or `datasets.load_dataset("openai_humaneval")`) and save to `data/raw/human_eval_data.jsonl`. **Retry Logic**: Implement exponential backoff (max limited retries) for network failures. **Fail Loudly**: If all retries fail, raise `DataFetchError` and exit with code 1. **Verification**: Ensure `data/raw/` directory exists and `human_eval_data.jsonl` is created with size > 0 bytes.
- [X] T008 [P] Create `run.sh` entry point that verifies environment by running `tests/test_dummy.py::test_dummy_inference` (which executes the lightweight dummy test) and exiting with code 1 on failure (FR-007). **Verification**: Run `run.sh` locally; ensure it exits with code 0 and prints "Environment Verified". **Note**: This task consolidates T008b and T008 from previous versions, creating the script content and verification logic in one step.
- [X] T008a [P] Create `tests/test_dummy.py` containing a function `test_dummy_inference` that performs a lightweight import check and a single-token generation using a small dummy prompt (no full model load) to verify environment without OOM risk. **Verification**: Run `pytest tests/test_dummy.py::test_dummy_inference` locally; ensure it exits with code 0.
- [X] T006 Create `code/calibration.py` implementing a CPU-bound load loop to validate `codecarbon` power draw detection. **Parameters**: Run for a fixed duration.; target power draw > 5W; compare against a known idle power draw baseline. The script must exit with code 1 or raise an exception if deviation > 10% (FR-010).
- [X] T007 Create `code/versioning.py` to hash artifacts and update project state YAML (Constitution Principle V)
- [X] T009 [P] Create `code/checksum.py` to calculate SHA-256 hash of `data/raw/human_eval_data.jsonl` and update `state/projects/PROJ-727-assessing-energy-consumption-of-llm-infe.yaml` under `artifact_hashes` (Constitution Principle III). **Pre-conditions**: Verify T005 exit code is 0 and file size > 0. **Hard Stop**: If file missing, size is 0, or hash calculation fails, exit with code 1. **Verification**: If `data/raw/human_eval_data.jsonl` exists and is valid, run `python code/checksum.py` and verify the hash is recorded in the YAML. If file missing or invalid, script must fail loudly. **Depends on**: T005.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Energy-to-Token Metrics (Priority: P1) 🎯 MVP

**Goal**: Execute inference for GPT-2-small, CodeBERT, and StarCoder-1B on HumanEval using CPU, logging energy (kWh), runtime, and tokens via `codecarbon`.

**Independent Test**: Run `run.sh` on a fresh GitHub Actions runner; verify `codecarbon` logs exist for all three models and `results.csv` contains non-null values for `model_id`, `tokens_generated`, `energy_kwh`, and `pass_fail_status` for every problem.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/inference.py`: Load models sequentially (GPT2 -> CodeBERT -> StarCoder-1B) with explicit unload logic to free RAM (`del model`, `gc.collect()`). **Sequence**: 1. Load Model A. 2. Run Inference. 3. `del model`. 4. `gc.collect()`. 5. **Verify RAM Drop**: Log and assert RAM usage drops by >80% before loading Model B. 6. Load Model B. Run `codecarbon` context to measure energy. Count tokens generated per problem **using the model's associated tokenizer** (`transformers.AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)`). **Edge Case Handling**: Record `null` energy if calibration fails, record `null` tokens if 0 tokens generated (FR-009). Write raw inference logs to `data/processed/energy_inference_raw.csv` with schema: `model_id`, `problem_id`, `tokens_generated`, `energy_kwh`, `runtime_seconds`. **Verification**: 1. **Dry-Run**: Run `python -c "import code.inference; print('Import OK')"`. 2. **Post-Run**: Ensure `data/processed/energy_inference_raw.csv` exists and contains rows for all three models.
- [X] T013a [US1] Implement `tests/test_inference_syntax.py` to verify `code/inference.py` imports and basic structure without loading models. **Verification**: Run `pytest tests/test_inference_syntax.py` and ensure it passes.
- [X] T014 [US1] Implement `code/evaluation.py`: Evaluate generated completions against HumanEval test suite using `evaluate_functional_correctness` with `n_jobs=1`, `timeout=10.0`, `k=[1]`. **Invocation**: Use the specific CLI or API call that avoids deadlocks (e.g., `evaluate_functional_correctness --num_workers 1`). Record `pass_fail_status` (binary) for **ALL** rows in `energy_inference_raw.csv` (including those with zero tokens). Join results with `energy_inference_raw.csv` to create `data/processed/energy_results_raw.csv` with full schema: `model_id`, `problem_id`, `tokens_generated`, `energy_kwh`, `runtime_seconds`, `pass_fail_status`. **Verification**: 1. **Dry-Run**: Run `python -c "import code.evaluation; print('Import OK')"`. 2. **Post-Run**: Ensure `data/processed/energy_results_raw.csv` exists and contains the joined data for all rows.
- [X] T016a [US1] Implement data filtering for aggregation in `code/main.py` (or dedicated script): Read `energy_results_raw.csv`. **Filter**: Remove rows where `energy_kwh` is `null` OR `tokens_generated` is 0. Save the filtered dataset to `data/processed/energy_results_aggregated.csv`. **Requirement**: This artifact strictly satisfies FR-011. **Verification**: 1. **Dry-Run**: Create a mock `energy_results_raw.csv` with 0-token rows, run the script, and verify `energy_results_aggregated.csv` excludes them. 2. **Post-Run**: Verify `data/processed/energy_results_aggregated.csv` exists and contains only valid rows.
- [X] T016c [US1] (New) Preserve raw unfiltered data for statistical integrity: Ensure `data/processed/energy_results_raw.csv` is kept as an immutable artifact for any specific analyses requiring the full dataset (e.g., if ANOVA logic is adjusted to handle 0s differently, though FR-011 mandates filtering for the primary aggregate). **Verification**: Confirm `energy_results_raw.csv` exists and is not deleted or modified after T016a runs.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (raw data generated, filtered aggregate created)

---

## Phase 4: User Story 2 - Statistical Analysis of Energy vs. Model Size (Priority: P2)

**Goal**: Perform Repeated-Measures ANOVA, Tukey HSD, and descriptive linear regression on collected data.

**Independent Test**: Execute `code/analysis.py` on `energy_results_aggregated.csv`; verify ANOVA table (p-value), Tukey HSD table, and regression output (slope, R-squared) are printed/saved.

**⚠️ DEPENDENCY**: All tasks in this phase depend on T016a (aggregation) being complete.

### Implementation for User Story 2

- [X] T021 [US2] Implement Repeated-Measures ANOVA with `problem_id` as blocking factor (subject) in `code/analysis.py` using data from `data/processed/energy_results_aggregated.csv`. **Requirement**: The data must be in 'long' format (one row per model per problem) to treat `problem_id` as the repeated measure. **Verification**: 1. **Dry-Run**: Run with mock data and verify the output contains an ANOVA table. 2. **Post-Run**: Verify `data/processed/stats_report.csv` contains the ANOVA results.
- [X] T022 [US2] Implement post-hoc Tukey HSD test in `code/analysis.py` (FR-005)
- [X] T023 [US2] Implement descriptive linear regression (Parameter Count vs. Energy/Token) in `code/analysis.py`, explicitly framing as observational (FR-005, FR-008). **Requirement**: The output object and the generated report MUST include the text "observational" or "correlation does not imply causation" to satisfy FR-008. **Verification**: 1. **Dry-Run**: Run with mock data and verify the output string contains the required framing. 2. **Post-Run**: Verify `data/processed/stats_report.csv` contains the framing text.
- [X] T024a [US2] Implement sensitivity analysis: create a perturbed dataset copy with ±10% energy value perturbation using **numpy.random.seed()** for determinism. Perturb by adding noise sampled from **Uniform(-0.1, 0.1) * energy_kwh** (where ε=0.1) to satisfy the bidirectional requirement. **Edge Case**: If `energy_kwh <= 0`, set perturbation to 0. Re-run **Repeated-Measures ANOVA** using the implementation from T021 on this perturbed dataset, and calculate the delta p-values. **Output**: Write the original p-value, perturbed p-value, and delta to `data/processed/sensitivity_delta.csv` (FR-012).
- [X] T025 [US2] Write `data/processed/stats_report.csv` containing ANOVA table, Tukey results, regression coefficients, sensitivity findings, **and the slope of the curve connecting model centroids (Energy/Token vs Parameter Count)** (FR-005, FR-012). **Note**: Slope calculation is moved here to ensure data flow correctness.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (raw data + stats)

---

## Phase 5: User Story 3 - Generate Sustainability Trade-off Visualizations (Priority: P3)

**Goal**: Generate bar plot (Energy/Token vs Model) and scatter plot (Energy per Correct Solution vs Accuracy).

**Independent Test**: Run plotting script; verify existence of two PNG files with correct axes, labels, and legends.

**⚠️ DEPENDENCY**: All tasks in this phase depend on T016a (aggregation) being complete.

### Implementation for User Story 3

- [X] T027 [US3] Implement `code/visualization.py`: Load data strictly from `data/processed/energy_results_aggregated.csv` (clean source).
 - **Bar Plot (T028 merged)**: Generate Bar Plot: Y=Energy per Token (Joules), X=Model ID. **Must include** error bars calculated as **a confidence interval** (using `scipy.stats.t.interval`) per model across all problems, a legend, title, and axis labels. Save to `data/processed/energy_bar.png`.
 - **Scatter Plot (T029 merged)**: Generate Scatter Plot: Y=Energy per Correct Solution, X=Pass@1 Accuracy. **Definition**: 'Energy per Correct Solution' = `Total Energy for Model / Count of Passed Problems`. 'Pass@1 Accuracy' = `Count of Passed Problems / Total Problems`. **Edge Case Handling**: If `Count of Passed Problems` is 0, do NOT exclude the point. Instead, plot a distinct marker (e.g., a red 'X') at X=0 with Y labeled as 'N/A' or a specific text annotation to ensure the model is represented in the visualization. **Must include** a legend, title, and axis labels. Save to `data/processed/tradeoff_scatter.png`.
 - **Verification**: 1. **Dry-Run**: Run `python code/visualization.py --mock` to generate plots from a small synthetic CSV. 2. **Post-Run**: Ensure `data/processed/energy_bar.png` and `data/processed/tradeoff_scatter.png` exist with correct labels. 3. **Edge Case**: Verify that if a model has [deferred] accuracy, it appears in the plot with the specific marker/annotation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Documentation updates: Create `quickstart.md` with a template containing run instructions and placeholders for expected artifacts. **Verification**: Ensure `quickstart.md` exists and contains the template structure.
- [X] T033 Code cleanup and refactoring of `code/main.py` orchestrator
- [X] T034 Verify `run.sh` completes full pipeline (Inference + Stats + Plots) within 6 hours on a **GitHub Actions ubuntu-latest** free-tier runner. **Task**: 1. **Estimation**: Implement a function in `code/main.py` that estimates runtime based on model sizes and HumanEval count. 2. **Execution**: Run `time run.sh` on CI and log the result. **Verification**: 1. **Pre-Run**: Verify estimation logic exists. 2. **Post-Run**: Record total execution time using the `time` command to `logs/pipeline_duration.log` and assert it is < 21600 seconds (spec.md Constraints).
- [X] T035 [P] Final validation: Run `run.sh` on clean GitHub Actions runner to ensure all artifacts are generated and non-null where required. **Verification**: Confirm existence of `data/processed/energy_results_aggregated.csv`, `data/processed/stats_report.csv`, `data/processed/energy_bar.png`, `data/processed/tradeoff_scatter.png`, and `logs/pipeline_duration.log`. Validates T014, T016a, T021, T027, T032, T034.

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
- **Feasibility Check**: All tasks assume CPU-only execution (limited cores, constrained RAM). A A smaller variant of the StarCoder model is used instead of StarCoder-base. to prevent OOM... No GPU quantization or 8-bit loading is permitted.
- **Data Integrity**: Tasks explicitly forbid synthetic data. All analysis must consume real HumanEval data and real `codecarbon` logs.
- **Single Source of Truth**: All visualizations and statistics must derive from `data/processed/energy_results_aggregated.csv`.

## Phase 7: Review Remediation (Revision Round 1)

**Purpose**: Address specific gaps identified in the initial analysis of the plan and spec.

**⚠️ CRITICAL**: These tasks address specific reviewer concerns regarding data flow, error handling, and reproducibility. They must be executed before the pipeline is considered production-ready.

### Implementation for Review Remediation

- [X] T036 [P] [Review] **REMOVED**: Logic merged into T005.
- [X] T037 [P] [Review] Add explicit "Model Unload" verification in `code/inference.py` (T013). After `del model` and `gc.collect()`, insert a check to ensure **CPU RAM** usage drops by >80% before loading the next model. Log the memory delta. **Rationale**: Ensures OOM risks are mitigated on the constrained low-RAM runner for the StarCoder-1B task. (Note: Updated to reference CPU RAM only).
- [X] T038 [P] [Review] Refine `code/analysis.py` (T021) to handle the "Long Format" requirement explicitly. Add a validation step that asserts Every `problem_id` has multiple rows (one per model). before running ANOVA. If counts mismatch, raise `DataIntegrityError`. **Rationale**: Prevents statistical errors caused by missing data points in the Repeated-Measures ANOVA.
- [X] T039 [P] [Review] Update `quickstart.md` (T032) to include a "Troubleshooting" section specifically for "Data Fetch Failures" and "OOM Errors". **Rationale**: Provides clear guidance for users encountering the known constraints of the CPU-only environment.
- [X] T040 [P] [Review] Create `tests/test_data_integrity.py` to verify that `data/processed/energy_results_aggregated.csv` contains no synthetic placeholders (e.g., strings like "mock", "synthetic", or 0.0 energy values where non-zero is expected). **Rationale**: Automated guard against accidental data fabrication during pipeline execution.

**Checkpoint**: All review concerns addressed; pipeline robust against common failure modes.