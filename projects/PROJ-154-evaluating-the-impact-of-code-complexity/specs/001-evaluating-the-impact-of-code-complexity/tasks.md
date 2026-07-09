# Tasks: Evaluating the Impact of Code Complexity on LLM Code Understanding

**Input**: Design documents from `/specs/001-evaluating-impact-of-code-complexity-on-llm-code-understanding/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: All test tasks are MANDATORY to ensure scientific rigor and reproducibility.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Scope Change Note**: 
This project restricts scope to **Code Summarization** only. 
- **Bug Detection** and **Code Completion** tasks (originally in FR-003, US-2) are **EXCLUDED** per the Plan's decision to avoid construct validity threats associated with synthetic ground truths.
- **Execution Pass Rate** and **bug line detection** metrics (originally in FR-004) are **EXCLUDED**.
- The Plan mandates the use of `Phi-3-mini-4k-instruct` (CPU-tractable) instead of `codellama/CodeLlama-7b-Instruct-hf` (original Spec FR-003) to ensure feasibility on 7GB RAM CI runners.
- A formal Scope Change Justification document will be generated to trace these exclusions.

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
- [ ] T002 Initialize Python project with `requirements.txt` (radon, transformers, torch, datasets, pandas, scikit-learn, statsmodels, nltk, evaluate, bitsandbytes)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/memory_guard.py` with RAM monitoring (FR-006) to abort/downsample if usage > 85% of 7GB
- [ ] T005 Implement `code/utils/prompts.py` with standardized summarization prompt templates
- [ ] T006 Create `contracts/analysis_schema.yaml` defining the output structure for statistical results (GLM, Correlation, Stratified Analysis)
- [ ] T007 Setup deterministic logging configuration (random seed fixation, radon version recording) per Constitution VI

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Acquisition and Complexity Annotation (Priority: P1) 🎯 MVP

**Goal**: Download CodeSearchNet Python subset, compute complexity metrics using `radon`, and store in structured CSV.

**Independent Test**: The script runs successfully, producing a CSV where every row has a unique ID, raw code, and three valid numeric complexity columns.

### Tests for User Story 1 (MANDATORY)

- [ ] T010 [P] [US1] Prerequisites: T001, T002. Unit test for `radon` metric calculation on known code snippets in `tests/unit/test_complexity_calc.py`
- [ ] T011 [P] [US1] Prerequisites: T001, T002. Integration test for data download and extraction in `tests/integration/test_data_acquisition.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_data_acquisition.py` to download CodeSearchNet Python subset to `data/raw/` (FR-001)
- [ ] T013 [US1] Implement `code/02_complexity_annotation.py` to parse functions and compute Cyclomatic Complexity, Halstead Volume, Maintainability Index (FR-002)
- [ ] T014 [US1] Add error handling in `02_complexity_annotation.py` to skip snippets with syntax errors and log warnings (Edge Case)
- [ ] T015 [US1] Implement logic to save processed data to `data/processed/annotated_metrics.csv` with metadata.json (Constitution VI)
- [ ] T016 [US1] Verify all rows in output CSV have valid numeric values for all three metrics (SC-004)
- [ ] T017 [US1] Implement 'Binning Strategy' logic to define Low/Medium/High tertiles for complexity stratification and explicitly write the calculated binning boundaries to `data/processed/metadata.json` (Constitution VII)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - LLM Inference and Task Execution (Priority: P2)

**Goal**: Execute **Code Summarization** only (Bug Detection and Code Completion excluded per Plan) on the annotated dataset using `Phi-3-mini-4k-instruct` (CPU-tractable, 4-bit quantized) and generate results log.

**Independent Test**: The inference pipeline processes a subset, producing a JSONL file with input, output, and ground truth, completing within memory limits.

### Tests for User Story 2 (MANDATORY)

- [ ] T018 [P] [US2] Prerequisites: T001, T002. Unit test for memory guard trigger and batch downsampling in `tests/unit/test_memory_guard.py`
- [ ] T019 [P] [US2] Prerequisites: T001, T002. Integration test for LLM loading and single-inference step in `tests/integration/test_inference_pipeline.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/03_inference.py` to load `Phi-3-mini-4k-instruct` (per Plan) with 4-bit quantization and CPU device mapping. **Note**: Do NOT load `codellama/CodeLlama-7b-Instruct-hf` as per Plan scope change.
- [ ] T021 [US2] Integrate `memory_guard.py` into `03_inference.py` to monitor RAM and abort/downsample if > 85% threshold (FR-006)
- [ ] T022 [US2] Implement batching logic to process `data/processed/annotated_metrics.csv` with context window truncation handling (Edge Case)
- [ ] T023 [US2] Generate `results/inference_logs.jsonl` containing snippet_id, task_type ('summarization'), model_output, reasoning, and ground_truth
- [ ] T024 [US2] Implement metric calculation for **Summarization only** (BLEU-4, ROUGE-L) comparing model output to docstring ground truth. **Note**: Execution Pass Rate and bug detection metrics are excluded per Plan scope change; FR-004 is partially satisfied.
- [ ] T025 [US2] Handle empty/whitespace model responses by recording as "failed" (Edge Case)
- [ ] T026 [US2] Verify inference log contains non-empty responses for ≥ 95% of the **total number of valid input snippets** (including those excluded upstream for syntax errors) (SC-005)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Correlation Reporting (Priority: P3)

**Goal**: Compute Spearman correlations and GLM analysis to evaluate the relationship between complexity and performance for Summarization tasks, including stratified analysis by complexity bins.

**Independent Test**: The analysis script outputs a table with correlation coefficients, p-values, and GLM statistics, validating against the schema contract.

### Tests for User Story 3 (MANDATORY)

- [ ] T028 [P] [US3] Prerequisites: T001, T002. Unit test for Spearman correlation calculation on dummy data in `tests/unit/test_stats.py`
- [ ] T029 [P] [US3] Prerequisites: T001, T002. Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/04_analysis.py` to load `results/inference_logs.jsonl` (Summarization only) and `data/processed/annotated_metrics.csv`. **Note**: Logic must handle single-task structure without expecting missing columns.
- [ ] T031 [US3] Implement Spearman correlation calculation between complexity metrics and performance scores (FR-005)
- [ ] T032 [US3] Implement VIF check for multicollinearity; if VIF > 5, **generate PCA components and save to `results/pca_components.csv`**, then use PCA components for GLM (Constitution VII)
- [ ] T033 [US3] Implement GLM with logit link to evaluate non-linear relationships (FR-005)
- [ ] T034 [US3] Implement stratified analysis by comparing performance metrics across Low/Medium/High complexity bins (Constitution VII)
- [ ] T035 [US3] Generate `results/analysis_metrics.csv` containing correlation matrix, GLM coefficients, standard errors, p-values, and stratified analysis results (FR-007)
- [ ] T036 [US3] Generate final report visualizing accuracy vs. complexity trend (including bin-based stratification) and stating hypothesis support status (SC-001, SC-002)
- [ ] T037 [US3] Validate output against `contracts/analysis_schema.yaml` before report generation (Constitution VII)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `quickstart.md` and `data-model.md`
- [ ] T039 Code cleanup and refactoring
- [ ] T040 [P] Refactor `code/03_inference.py` to implement dynamic batch sizing using a binary search heuristic starting at batch_size=1, capping at max_memory=6.5GB to maximize throughput while staying under 7GB RAM limit
- [ ] T041 [P] Implement caching in `code/01_data_acquisition.py` to prevent re-downloading if checksums match
- [ ] T042 [P] Run quickstart.md validation and verify CI feasibility (SC-003)
- [ ] T043 [P] Generate `results/scope_compliance_report.md` explicitly listing which FRs are met (Summarization) and which are excluded (Bug Detection, Code Completion) with justification from Plan.md
- [ ] T044 [P] Verify that `results/inference_logs.jsonl` contains ONLY 'summarization' task_type entries and no references to excluded tasks
- [ ] T045 [P] Verify that analysis scripts handle the single-task data structure correctly without expecting missing columns
- [ ] T046 [P] Generate `specs/scope-change-justification.md` formally documenting the exclusion of FR-003 (Bug Detection, Code Completion) and FR-004 (Execution Pass Rate, bug line detection) per Plan decision
- [ ] T047 [P] Update `specs/scope-change-justification.md` to explicitly state that FR-004 metrics (Execution Pass Rate, bug line detection) are excluded due to scope reduction
- [ ] T048 [P] Update `specs/scope-change-justification.md` to explicitly state that User Story 2 acceptance scenarios for Bug Detection and Code Completion are superseded by the Summarization-only scenario
- [ ] T049 [P] Verify that `data/processed/metadata.json` contains the specific Low/Medium/High tertile boundary values generated by T017
- [ ] T050 [P] Verify that `code/04_analysis.py` performs stratified analysis using the bins from T017/T049
- [ ] T051 [P] Verify that `code/04_analysis.py` does not attempt to access columns for excluded tasks (Bug Detection, Code Completion)

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
- **User Story 2 (P2)**: Depends on US1 (requires `data/processed/annotated_metrics.csv`)
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
3. Add User Story 2 → Test independently → Deploy/Demo (requires US1 data)
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
- **Critical Constraint**: All tasks must run on CPU-only CI with a limited number of cores and constrained RAM. No GPU, no 8-bit quantization, no large model loading without strict memory guards.
- **Scope Constraint**: Only Code Summarization is implemented. Bug Detection and Code Completion are excluded per Plan.md.