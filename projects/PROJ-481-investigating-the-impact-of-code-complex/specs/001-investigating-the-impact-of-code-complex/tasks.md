# Tasks: Investigating the Impact of Code Complexity on LLM Code Understanding

**Input**: Design documents from `/specs/001-code-complexity-llm-impact/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw`, `data/derived`, `results/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `radon`, `transformers`, `datasets`, `scikit-learn`, `statsmodels`, `seaborn`, `llama-cpp-python`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Note: While T005-T007 can be developed in parallel, the *execution* of downstream scripts (T012, T017, T024) is strictly blocked until these utility modules are committed and importable.

- [ ] T004 Create `data/` directory structure and `.gitkeep` files for raw/derived artifacts
- [ ] T005 [P] Implement `code/utils/metrics.py` with Radon wrappers (Cyclomatic, Halstead, Cognitive) and error handling for invalid syntax
- [ ] T006 [P] Implement `code/utils/inference.py` with CPU-optimized LLM loading (GGUF via `llama-cpp-python`), batching logic, and timeout/fail-fast mechanisms
- [X] T007 [P] Implement `code/utils/stats.py` with segmented regression (change-point detection), bootstrap CI calculation, and correlation functions
- [~] T008 Configure environment variables for dataset paths and model paths in `.env` example file
- [~] T009 Create base script runners (`00_download_data.py`, `01_compute_metrics.py`, `02_run_inference.py`, `03_analyze_results.py`) with argument parsing and logging
- [X] T011a [P] [US1] Implement `code/00_download_data.py` to fetch **BigCodeBench** (primary target) or **CodeSearchNet** (fallback) using `datasets.load_dataset`. Must include checksumming and verification of the downloaded file.
- [X] T011b [P] [US1] Implement schema verification in `code/00_download_data.py` to check for the presence of ground truth annotations required for FR-003. Log the presence of 'summarization' and 'bug detection' fields.
- [X] T011c [P] [US1] Implement the 'Reconstruction-Only' fallback logic in `code/00_download_data.py`. If independent annotations are missing, flag the dataset configuration as 'Reconstruction-Only' and log this scope change explicitly.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel (code development only; execution blocked until dependencies met)

---

## Phase 3: User Story 1 - Compute Static Complexity Metrics on Code Corpus (Priority: P1) 🎯 MVP

**Goal**: Ingest a public code dataset, parse functions, and compute static complexity metrics (Cyclomatic, Halstead, Cognitive).

**Independent Test**: Run on a small subset (50 functions) and verify output CSV matches manual `radon` calculations.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T010 [P] [US1] Unit test for metric calculation edge cases (empty functions, zero complexity) in `code/tests/test_metrics.py`
- [~] T010b [US1] Run the 'Independent Test' pipeline: Execute `code/01_compute_metrics.py` on a 50-function subset and verify `data/derived/metrics.csv` matches manual `radon` calculations. **Deliverable**: Generate `tests/outputs/us1_validation_report.md` containing the diff summary and pass/fail status.

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/01_compute_metrics.py` to parse functions from the raw dataset, compute metrics using `code/utils/metrics.py`, and save results to `data/derived/metrics.csv`. **Execution of this task is blocked until T011a completes.**
- [X] T013 [US1] Add robust error handling in `code/01_compute_metrics.py` to skip invalid syntax functions without crashing the pipeline and log errors
- [X] T014 [US1] Add a statistical summary step in `code/01_compute_metrics.py` to verify the distribution of complexity scores (low to high range) in the generated CSV
- [X] T015 [US1] Implement logic in `code/01_compute_metrics.py` to cap sampling at N=1,000 (per Plan constraints) and append a `sampling_log.txt` entry confirming the final count and the cap applied.
- [X] T015b [US1] Generate a 'Statistical Power Justification' document in `results/statistical_power_justification.md` explaining why N=1,000 is sufficient given the runtime constraints, addressing SC-003's N≥5,000 target.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute LLM Code Understanding Tasks and Record Accuracy (Priority: P2)

**Goal**: Run CPU-tractable LLMs on the computed dataset for code understanding tasks (summarization, bug detection, reconstruction) and calculate accuracy.

**Independent Test**: Run on a fixed subset with known ground truth and verify accuracy metrics (ROUGE-L, F1, BLEU) are calculated correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for hallucination detection and score assignment (score=0) in `code/tests/test_inference.py`

### Implementation for User Story 2

- [~] T017 [US2] Implement `code/02_run_inference.py` to load a CPU-optimized model (e.g., StarCoder-1B/3B or quantized CodeLlama via GGUF) and process the `data/derived/metrics.csv`. **Execution of this task is blocked until T012 completes.**
- [X] T018a [US2] Implement ground truth retrieval logic in `code/02_run_inference.py` to fetch independent annotations for 'summarization' and 'bug detection' from the dataset schema (BigCodeBench).
- [X] T018b [US2] Implement fallback logic in `code/02_run_inference.py`: If independent annotations are missing, switch to 'Reconstruction-Only' mode (comparing output to original source code) to satisfy FR-003's requirement for accuracy calculation. Log the active mode.
- [X] T018c [US2] Implement hallucination detection in `code/02_run_inference.py` to handle non-code outputs by setting `score=0` and `hallucination_flag=true`.
- [X] T019 [US2] Implement accuracy calculation in `code/02_run_inference.py` using ROUGE-L, F1, and BLEU
- [X] T020 [US2] Add timeout and memory limit handling in `code/02_run_inference.py` to mark specific functions as "timeout/fail" without halting the pipeline
- [ ] T021 [US2] Save results to `data/derived/inference_results.csv` with columns for Function ID, Model ID, Task Type, Generated Text, Accuracy Score, and Hallucination Flag
- [ ] T022 [US2] Implement **stratified sampling (by complexity)** in `code/02_run_inference.py` to ensure the subset is representative. Limit total inference to **N=1,000** to meet the 6-hour runtime constraint on the free-tier runner.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlate Complexity Metrics with Model Accuracy and Identify Thresholds (Priority: P3)

**Goal**: Perform statistical analysis to correlate metrics with accuracy, identify thresholds using change-point detection, and generate visualizations.

**Independent Test**: Run on a mock dataset with pre-defined negative correlation and verify output correlation coefficient and threshold markers.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for segmented regression and p-value calculation in `code/tests/test_stats.py`

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/03_analyze_results.py` to merge `data/derived/metrics.csv` and `data/derived/inference_results.csv` into `data/derived/combined_analysis.csv`
- [ ] T025 [US3] Implement Pearson/Spearman correlation analysis in `code/03_analyze_results.py` between complexity metrics and accuracy scores, calculating p-values and confidence intervals
- [ ] T025b [US3] **Dynamic Baseline & Sensitivity Analysis**: Calculate the dataset's mean accuracy dynamically. Implement a configurable threshold parameter (defaulting to a fraction of the mean). and a sensitivity sweep function that outputs `results/sensitivity_analysis.csv` containing the stability metrics across the ±0.05, ±0.1 range.
- [ ] T026 [US3] Implement segmented regression (change-point detection) in `code/03_analyze_results.py` to identify specific complexity thresholds where accuracy drops. **Deliverables must include**:
 1. The specific complexity value (change-point).
 2. **Bootstrap confidence intervals for the change-point location** (inferential evidence).
 3. **Sensitivity sweep results (±0.05, ±0.1)** as required by FR-005 (input from T025b).
 **Save the change-point and CIs to `results/threshold_detection.json` and the sensitivity sweep to `results/sensitivity_analysis.csv`.**
- [ ] T027 [US3] Apply multiple-comparison error correction (e.g., Bonferroni or FDR) to hypothesis tests across different tasks. **Justification**: Required to support the 'inferential statistical evidence' mandate in FR-005. **Deliverable**: Calculate and report the measured error rate in `results/error_rate_report.md`.
- [ ] T028 [US3] Generate visualizations (scatter plots with threshold markers) using `matplotlib`/`seaborn` and save to `results/plots/`
- [ ] T029 [US3] Generate `results/report.md` containing the statistical summary, correlation coefficients, identified thresholds, and significance statements
- [ ] T029a [US3] **Scope Reconciliation**: Append a "Scope Reconciliation" section to `results/report.md` explicitly citing the Plan's N=1,000 constraint and the statistical power justification from T015b.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `README.md` and `docs/`
- [ ] T031 Code cleanup and refactoring of utility modules
- [ ] T032 Performance optimization of inference batching
- [ ] T033 [P] Additional unit tests for edge cases in `code/tests/`
- [ ] T034 Run `quickstart.md` validation (if available) to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Critical Note**: While T005-T007 (Utils) can be developed in parallel, the **execution** of T012, T017, and T024 is strictly blocked until these utility modules are committed and importable.
 - **T011a/b/c** (Data Fetch/Verify) are now in Phase 2 and must complete before T012.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
 - **User Story 2 (P2)**: **Execution of T017 is blocked until T012 (US1) completes.** Code development can proceed in parallel.
 - **User Story 3 (P3)**: **Execution of T024 is blocked until T012 (US1) and T021 (US2) complete.** Code development can proceed in parallel.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] (T005-T007, T011a-c) can run in parallel for **implementation**, but their **execution** is blocked until committed.
- **Implementation** of US1, US2, and US3 can proceed in parallel (code writing).
- **Execution** of US2 is blocked until US1 data (T012) is ready.
- **Execution** of US3 is blocked until US1 and US2 data (T012, T021) are ready.
- All tests for a user story marked [P] can run in parallel.

### Strict Execution Order (Runtime)

The runner MUST enforce the following sequence:
1. T011a -> T011b -> T011c (Data Fetch/Verify)
2. T012 (Compute Metrics)
3. T010b (US1 Independent Test) - *Optional*
4. T017 (Run Inference)
5. T021 (Save Inference Results)
6. T024 (Merge Data)
7. T025 -> T025b (Correlation & Dynamic Baseline)
8. T026 (Threshold Detection)
9. T027 (Error Rate Correction)
10. T028 -> T029 -> T029a (Viz & Report)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Execution Order**: T011 -> T012 -> T017 -> T021 -> T024 -> T025/25b -> T026 -> T027 -> T028/29/29a