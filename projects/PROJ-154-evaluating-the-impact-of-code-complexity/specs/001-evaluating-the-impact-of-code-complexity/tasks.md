# Tasks: Evaluating the Impact of Code Complexity on LLM Code Understanding

**Input**: Design documents from `/specs/001-evaluating-impact-of-code-complexity-on-llm-code-understanding/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: All test tasks are MANDATORY to ensure scientific rigor and reproducibility.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Note on Scope**:
This project implements **all three tasks** (Summarization, Bug Detection, Code Completion) as mandated by FR-003.
- **Bug Detection** ground truth is generated via programmatic bug injection (Plan Requirement Amendment 2).
- **Code Completion** ground truth is generated via code truncation (Plan Requirement Amendment 2).
- **Execution Pass Rate** and **bug line detection (substring match)** metrics are implemented as per FR-004 and Plan Amendment 3.
- The Plan mandates the use of `Phi-3-mini-4k-instruct` (CPU-tractable, **default precision float16/float32**) instead of `codellama/CodeLlama-7b-Instruct-hf` (original Spec FR-003) to ensure feasibility on 7GB RAM CI runners. **No 4-bit/8-bit quantization is used.**

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (as defined in plan.md)
- Paths shown below assume single project - adjusted based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` (code/, data/, results/, tests/)
- [ ] T002 Initialize Python project with `requirements.txt` (radon, transformers, torch, datasets, pandas, scikit-learn, statsmodels, nltk, evaluate, scipy, patsy). **Explicitly exclude 'bitsandbytes' to comply with CPU-only constraints.**
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004.1 [P] Create `config.yaml` to define the memory threshold (e.g., `memory_threshold_percent:`) and other runtime parameters (FR-006). This task explicitly defines the "predefined" threshold required by the spec.
- [ ] T004 [US2] Implement `code/utils/memory_guard.py` with RAM monitoring (FR-006) to abort/downsample if usage exceeds the threshold defined in `config.yaml` (T004.1).
- [ ] T005 [US2] Implement `code/utils/prompts.py` with standardized prompt templates for Summarization, Bug Detection, and Code Completion
- [X] T006 [US3] Create `contracts/analysis_schema.yaml` defining the output structure for statistical results (GLM, Correlation, Stratified Analysis)
- [~] T007 [P] Setup deterministic logging configuration (random seed fixation, radon version recording) per Constitution VI

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Acquisition and Complexity Annotation (Priority: P1) 🎯 MVP

**Goal**: Download CodeSearchNet Python subset, compute complexity metrics using `radon`, preserve ground truth (docstrings), and store in structured CSV.

**Independent Test**: The script runs successfully, producing a CSV where every row has a unique ID, raw code, ground truth, and three valid numeric complexity columns.

### Tests for User Story 1 (MANDATORY)

- [~] T010 [P] [US1] Prerequisites: T001, T002. Unit test for `radon` metric calculation on known code snippets in `tests/unit/test_complexity_calc.py`
- [X] T011 [P] [US1] Prerequisites: T001, T002. Integration test for data download and extraction in `tests/integration/test_data_acquisition.py`

### Implementation for User Story 1

- [~] T012 [US1] Prerequisites: T001, T002. Implement `code/01_data_acquisition.py` to download CodeSearchNet Python subset to `data/raw/` (FR-001). Log `total_raw_snippets` (count of all downloaded snippets) to `data/processed/metadata.json`.
- [X] T013 [US1] Prerequisites: T012. Implement `code/02_complexity_annotation.py` to parse functions, compute Cyclomatic Complexity, Halstead Volume, Maintainability Index, and **preserve the ground_truth (docstring) column** from the raw dataset (FR-002). Log syntax errors and exclude them from the final CSV.
- [ ] T014 [US1] Prerequisites: T013. Add error handling in `02_complexity_annotation.py` to skip snippets with syntax errors and log warnings to `data/processed/exclusions.log` (Edge Case). Ensure `metadata.json` tracks `total_valid_snippets` (excluding syntax errors) and `total_raw_snippets`.
- [ ] T015 [US1] Prerequisites: T014. Implement logic to save processed data to `data/processed/annotated_metrics.csv` with `metadata.json` containing `total_raw_snippets` and `total_valid_snippets` counts (Constitution VI).
- [~] T016 [US1] Prerequisites: T015. Verify all rows in output CSV have valid numeric values for all three metrics (SC-004).
- [ ] T017 [US1] Prerequisites: T015. Implement 'Binning Strategy' logic to define Low/Medium/High tertiles for complexity stratification. **Note: Binning is for descriptive visualization and robustness checks only; the primary analysis uses GLM with splines.** Explicitly write the calculated binning boundaries to `data/processed/metadata.json` (Constitution VII).
- [ ] T018.1 [US1] Prerequisites: T015. Implement `code/02_bug_injection.py` to generate a derived dataset `data/processed/bug_injected.csv` by programmatically injecting bugs (operator swaps) into a subset of snippets. This satisfies the ground truth requirement for Bug Detection (Plan Amendment 2).
- [ ] T018.2 [US1] Prerequisites: T015. Implement `code/02_truncation.py` to generate a derived dataset `data/processed/truncated_code.csv` by truncating functions and storing the *original full function* alongside the truncated version. This provides the ground truth for Code Completion execution validation (Plan Amendment 2).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - LLM Inference and Task Execution (Priority: P2)

**Goal**: Execute **all three tasks** (Summarization, Bug Detection, Code Completion) on the annotated dataset using `Phi-3-mini-4k-instruct` (CPU-tractable, **default precision**) and generate results log.

**Independent Test**: The inference pipeline processes a subset, producing a JSONL file with input, output, and ground truth for all three tasks, completing within memory limits.

### Tests for User Story 2 (MANDATORY)

- [ ] T018 [P] [US2] Prerequisites: T001, T002. Unit test for memory guard trigger and batch downsampling in `tests/unit/test_memory_guard.py`
- [ ] T019 [P] [US2] Prerequisites: T001, T002. Integration test for LLM loading and single-inference step in `tests/integration/test_inference_pipeline.py`

### Implementation for User Story 2

- [ ] T020 [US2] Prerequisites: T004, T005, T015. Implement `code/03_inference.py` to load `microsoft/Phi-3-mini-4k-instruct` with **`torch_dtype=torch.float16`** and **`device_map='cpu'`** (Plan Amendment 1). **Explicitly forbid 4-bit/8-bit quantization.** Verify the model loads and runs within 7GB RAM. (FR-003)
- [ ] T021 [US2] Prerequisites: T020. Integrate `memory_guard.py` into `03_inference.py` to monitor RAM and abort/downsample if > threshold defined in `config.yaml` (FR-006)
- [ ] T022 [US2] Prerequisites: T021. Implement batching logic to process `data/processed/annotated_metrics.csv` with context window truncation handling (Edge Case)
- [ ] T023 [US2] Prerequisites: T022. Generate `results/inference_logs.jsonl` containing snippet_id, task_type (summarization/bug_detection/code_completion), model_output, reasoning, and ground_truth
- [ ] T024 [US2] Prerequisites: T023, T018.1, T018.2. Implement metric calculation for **all three tasks**:
 - Summarization: BLEU-4, ROUGE-L (vs docstring)
 - Bug Detection: Substring match for injected bugs (vs `bug_injected.csv` injected bug location)
 - Code Completion: Execution Pass Rate (execute model output against the *original full function* stored in `truncated_code.csv` to verify logical equivalence, as no external unit tests exist)
 (FR-004)
- [ ] T025 [US2] Prerequisites: T024. Handle empty/whitespace model responses by recording as "failed" (Edge Case)
- [ ] T026 [US2] Prerequisites: T024, T015. Verify inference log contains non-empty responses for ≥ 95% of the **total_raw_snippets** (as defined in `data/processed/metadata.json`, including all snippets from the raw dataset, not just those processed if some were skipped) (SC-005).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Correlation Reporting (Priority: P3)

**Goal**: Compute Spearman correlations and GLM analysis (with **natural cubic splines**) to evaluate the relationship between complexity and performance for all three tasks, including stratified analysis by complexity bins.

**Independent Test**: The analysis script outputs a table with correlation coefficients, p-values, and GLM statistics, validating against the schema contract.

### Tests for User Story 3 (MANDATORY)

- [ ] T028 [P] [US3] Prerequisites: T001, T002. Unit test for Spearman correlation calculation on dummy data in `tests/unit/test_stats.py`
- [ ] T029 [P] [US3] Prerequisites: T001, T002. Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`

### Implementation for User Story 3

- [ ] T030 [US3] Prerequisites: T015, T023. Implement `code/04_analysis.py` to load `results/inference_logs.jsonl` and `data/processed/annotated_metrics.csv`. Logic must handle all three tasks.
- [ ] T031 [US3] Prerequisites: T030. Implement Spearman correlation calculation between complexity metrics and performance scores for each task (FR-005)
- [ ] T032.0 [US3] Prerequisites: T002. Install and configure `patsy` library. Define natural cubic spline basis parameters (knots, boundaries) for the GLM model (Constitution VII, Plan Statistical Rigor).
- [ ] T032.1 [US3] Prerequisites: T032.0. Implement the GLM model with natural cubic splines as the primary analysis method (Constitution VII, Plan Statistical Rigor). This step must be ready before T032 executes the orchestration.
- [ ] T032 [US3] Prerequisites: T031, T032.1. Implement VIF check for multicollinearity. **Logic:** Calculate VIF. If VIF > 5, generate PCA components (retain [deferred] variance, include all complexity metrics) and save to `results/pca_components.csv`, then run GLM on PCA components. If VIF <= 5, run GLM on original metrics. **Do not skip GLM based on convergence; PCA is mandatory only if VIF > 5.** (Constitution VII)
- [ ] T033 [US3] Prerequisites: T032. Implement stratified analysis by comparing performance metrics across Low/Medium/High complexity bins (Constitution VII). **Note: Use binning for visualization/robustness only; primary results come from GLM with splines.**
- [ ] T034 [US3] Prerequisites: T032, T033. Generate `results/analysis_metrics.csv` containing correlation matrix, GLM coefficients (with splines), standard errors, p-values, and stratified analysis results (FR-007)
- [ ] T035 [US3] Prerequisites: T034. Generate final report visualizing accuracy vs. complexity trend (including bin-based stratification) and stating hypothesis support status for all three tasks (SC-001, SC-002)
- [ ] T036 [US3] Prerequisites: T035. Validate output against `contracts/analysis_schema.yaml` before report generation (Constitution VII)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `quickstart.md` and `data-model.md`
- [ ] T038 Code cleanup and refactoring
- [ ] T039 [P] Refactor `code/03_inference.py` to implement dynamic batch sizing using a binary search heuristic starting at batch_size=1, capping at max_memory=6.5GB to maximize throughput while staying under 7GB RAM limit
- [ ] T040 [P] Implement caching in `code/01_data_acquisition.py` to prevent re-downloading if checksums match
- [ ] T041 [P] Run quickstart.md validation and verify CI feasibility (SC-003)
- [ ] T042 [P] Generate `specs/scope-change-justification.md` formally documenting the implementation of all 3 tasks (Summarization, Bug Detection, Code Completion), the derived dataset generation strategies (bug injection, truncation), and the **Plan Amendment 1** substituting `Phi-3-mini` for `CodeLlama-7b` due to RAM constraints. Explicitly state that no tasks were excluded.
- [ ] T043 [P] Verify that `results/inference_logs.jsonl` contains entries for all three task types (summarization, bug_detection, code_completion)
- [ ] T044 [P] Verify that analysis scripts handle the multi-task data structure correctly and calculate metrics for all three tasks
- [ ] T045 [P] Verify that `data/processed/metadata.json` contains the specific Low/Medium/High tertile boundary values generated by T017
- [ ] T046 [P] Verify end-to-end data flow: T013 preserves ground_truth, T018.1/T018.2 generate derived datasets, T023 generates logs for all 3 tasks, T024 calculates all 3 metrics, T030-T035 perform analysis for all 3 tasks. Ensure schema compliance across all artifacts.
- [ ] T047 [P] [US1] Verify `code/01_data_acquisition.py` uses the canonical HuggingFace `datasets` loader for CodeSearchNet Python to ensure data integrity and reproducibility, avoiding manual URL concatenation
- [ ] T048 [P] [US2] Implement a timeout mechanism in `code/inference.py` to abort individual inference requests exceeding a predefined duration threshold to prevent CI job hangs on complex snippets.
- [ ] T049 [P] [US3] Add a robustness check in `code/04_analysis.py` to handle cases where the GLM fails to converge (e.g., due to perfect separation) by falling back to the Spearman correlation result with a warning flag

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
- **User Story 2 (P2)**: Depends on US1 (requires `data/processed/annotated_metrics.csv`, `bug_injected.csv`, `truncated_code.csv`)
- **User Story 3 (P3)**: Depends on US2 (requires `results/inference_logs.jsonl`)

### Within Each User Story

- Tests (MANDATORY) MUST be written and FAIL before implementation
- Models/Utilities before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (subject to data dependencies)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (ensure T002 is complete first):
Task: "Unit test for radon metric calculation in tests/unit/test_complexity_calc.py"
Task: "Integration test for data download in tests/integration/test_data_acquisition.py"

# Launch all models/utilities for User Story 1 together:
Task: "Implement 01_data_acquisition.py"
Task: "Implement 02_complexity_annotation.py"
Task: "Implement 02_bug_injection.py"
Task: "Implement 02_truncation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify CSV quality)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (requires US1 data file)
4. Add User Story 3 → Test independently → Deploy/Demo (requires US2 logs)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Inference) - *Note: Must wait for US1 data file to exist, but can prepare code*
 - Developer C: User Story 3 (Analysis) - *Note: Must wait for US2 logs, but can prepare code*
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
- **Critical Constraint**: All tasks must run on CPU-only CI with a limited number of cores and constrained RAM. No GPU, **no 4-bit/8-bit quantization**, strict memory caps, deterministic reproducibility.
- **Scope Constraint**: All three tasks (Summarization, Bug Detection, Code Completion) are implemented. Ground truths for Bug Detection and Code Completion are generated via derived datasets (bug injection, truncation) as per Plan Requirement Amendments.
- **Model Constraint**: `Phi-3-mini` is used due to 7GB RAM limit (Plan Amendment 1).