# Tasks: Evaluating the Effectiveness of LLMs for Detecting Code Smells

**Input**: Design documents from `/specs/001-evaluating-the-effectiveness-of-llms-for/`
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

- [X] T001 [P] Initialize project directory structure (`projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/`, `data/raw/`, `data/processed/`, `results/`, `tests/unit/`, `tests/contract/`) AND configure linting (flake8/black) and formatting tools in `code/` directory. Specifically: Create `.flake8` and `pyproject.toml` with black/flake8 settings.

- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` containing `datasets`, `pandas`, `radon`, `pylint`, `sentence-transformers`, `llama-cpp-python`, `scikit-learn`, `statsmodels`, `numpy`, and `psutil` (explicitly for FR-008 monitoring requirements)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` defining paths (`data/`, `results/`), random seeds, and batch size constants (LLM batch ≤ 10)
- [X] T005 [P] Implement `code/__init__.py` and ensure directory structure matches `data/raw`, `data/processed`, `results`
- [X] T006a [P] Setup logging configuration in `code/config.py` to define log format, file handlers, and levels for metrics (FR-008)
- [X] T006b [P] Implement `code/monitoring.py` to capture RAM usage, CPU utilization, and inference time using `psutil` for use in inference loops, explicitly recording these metrics **per batch executed** to `results/resource_metrics.json` (FR-008). **Note**: Metrics are recorded for every batch regardless of size to verify the general ≤50 constraint.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Data Pipeline and Static Analysis Baseline (Priority: P1) 🎯 MVP

**Goal**: Ingest a sampled subset of `codeparrot/github-code`, compute structural metrics via `radon`, and generate a baseline "smell label" set using Pylint.

**Independent Test**: Run the pipeline on a local subset (e.g., a small number of functions) and verify `data/static_baseline.csv` exists with correct columns (`code`, `loc`, `cyclomatic_complexity`, `static_smell_labels`).

### Implementation for User Story 1

- [X] T007 [US1] Implement `code/data_pipeline.py` to sample functions from `codeparrot/github-code` using HuggingFace `datasets` with **streaming=True**, split='train', and a pinned random seed. Target initial sample size: **800 functions**. Implement a **dynamic runtime check**: process a small batch of functions to estimate time; calculate a max-sample limit such that (estimated_time_per_function * max_samples) ≤ 5.5 hours. **If the reduced sample size is < 100 functions**, **log the deviation and final count** to `results/sample_report.json` with a warning, and **proceed** with the maximum possible sample to satisfy FR-001's compute constraint. Do NOT exit with code 1. (FR-001)
- [X] T007a [US1] [Depends: T007] Verify the representativeness of the sampled subset if the dynamic reduction in T007 occurs. Compare the distribution of LOC and Cyclomatic Complexity in the reduced sample against the original population statistics (if available) or log a warning if the reduction is severe. (FR-001)
- [X] T008 [US1] Implement structural metric calculation in `code/data_pipeline.py` using `radon` to **calculate LOC, Cyclomatic Complexity, and Nesting Depth** for every sampled function. **Explicitly calculate and store `nesting_depth`** as a distinct metric. (FR-002)
- [X] T009a [US1] Create `contracts/smell_mapping.json` defining a **fixed** mapping from common Pylint codes to canonical smell names derived from the LLM prompt categories (e.g., 'Long Method', 'Complex Logic'). Create the file with at least 5 common Pylint codes (e.g., C0111, R0913) mapped to canonical names before the full pipeline runs. (FR-003)
- [X] T009b [US1] [Depends: T007] Validate and update `contracts/smell_mapping.json` based on the **actual** Pylint error codes found in the sampled data from T007. Add any unmapped codes encountered to the contract, extending the fixed canonical mapping. (FR-003)
- [X] T009 [US1] [Depends: T009a, T009b] Implement the full Pylint normalization pipeline: (1) Load `contracts/smell_mapping.json` created in T009a/T009b; (2) Implement Pylint execution in `code/data_pipeline.py` to generate static smell labels AND normalize raw Pylint codes to canonical smell names using the mapping. Ensure the pipeline logs a warning if an unmapped code is encountered but continues. (FR-003)
- [X] T010 [US1] Implement error handling in `code/data_pipeline.py` to catch `radon` parsing errors, log the file, and exclude from final count (Edge Case)
- [X] T011a [US1] [Depends: T007, T008, T009] Write processed data to `data/static_baseline.csv` containing `code`, `loc`, `cyclomatic_complexity`, `nesting_depth`, and normalized `static_smell_labels` columns. **Include `nesting_depth`** to satisfy FR-002 and ensure data availability for downstream analysis. (FR-001, FR-002)
- [X] T011b [US1] [Depends: T011a] Verify schema compliance of `data/static_baseline.csv` (columns: code, loc, cyclomatic_complexity, nesting_depth, static_smell_labels) and data types
- [X] T012 [US1] [Depends: T011a, T011b] Add validation to ensure `data/static_baseline.csv` contains ≥ 95% of sampled functions with all required columns (FR-001, SC-005)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Semantic Feature Extraction and LLM Inference (Priority: P2)

**Goal**: Compute semantic embeddings and generate "smell labels" via a CPU-quantized LLM (CodeLlama-7B-GGUF) using a standardized prompt.

**Independent Test**: Process a single function through the embedding model and LLM, verifying a dense vector is produced and the LLM returns a parsable list of smells.

**Depends on**: T011a (US1) must complete to provide `data/static_baseline.csv`.

### Implementation for User Story 2

- [X] T013 [US2] [Depends: T011a] Implement `code/semantic_analysis.py` to load `sentence-transformers/all-MiniLM-L-v2` and compute dense vectors for functions in `data/static_baseline.csv`. **Note**: This task must run sequentially before T014 to avoid RAM contention. (FR-005)
- [X] T014 [US2] [Depends: T013] Implement `code/semantic_analysis.py` to load **`CodeLlama-7B-Instruct-GGUF`** specifically using the **4-bit quantized** variant (file suffix must be `q4_0.gguf` or `Q4_K_M.gguf`). Use `llama-cpp-python` on CPU device. (FR-004)
- [X] T014a [US2] [Depends: T014] Implement a runtime check in `code/semantic_analysis.py` to inspect `model.info.quantization` attribute or file suffix to confirm the model is 4-bit; if not, **raise an explicit error and halt the pipeline**. **Rationale**: This ensures compliance with Constitution Principle VI (Memory Constraint) and FR-004. (FR-004, Constitution Principle VI)
- [X] T015a [US2] Create `contracts/llm_prompt.txt` containing the exact standardized "Code Smell Detection" prompt text to request a JSON list of smell categories (FR-004)
- [X] T015 [US2] [Depends: T015a] Implement the standardized "Code Smell Detection" prompt in `code/semantic_analysis.py` by loading the exact prompt text from `contracts/llm_prompt.txt` (FR-004)
- [X] T016 [US2] [Depends: T014, T014a, T015] Implement batched inference loop in `code/semantic_analysis.py` with batch size ≤ 10 (within ≤ 50 constraint) and explicit `gc.collect()` between batches to manage RAM, and record batch-level metrics (RAM, CPU, time) (FR-004, FR-008). **Note**: Batch size of 10 is a resource constraint derived from Plan.md Complexity Tracking, deviating from Spec's ≤50 for safety.
- [X] T017 [US2] Implement JSON parsing and error handling in `code/semantic_analysis.py` to log "Unparseable" for malformed LLM outputs (Edge Case)
- [X] T018 [US2] Implement context window check in `code/semantic_analysis.py` to **truncate functions from the start (preserving the function header/definition)** if they exceed model limits, skip if truncation is insufficient, and log the count (Edge Case). **Rationale**: Preserving the header is critical for code smell detection.
- [X] T019 [US2] [Depends: T013, T014, T016] Write embeddings and LLM labels to `data/processed/semantic_results.json` (FR-004, FR-005)
- [X] T020 [US2] [Depends: T006b] Add monitoring in `code/semantic_analysis.py` to record peak RAM, CPU utilization, and inference time per batch to `results/resource_metrics.json` using `code/monitoring.py` (FR-008)
- [X] T020a [US2] [Depends: T020] Parse `results/resource_metrics.json`, compare peak RAM against the system-imposed memory limit (Constitution Principle VI), and generate `results/compliance_verification.json` with a pass/fail status and specific flags if breached (FR-008, SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis and Reporting (Priority: P3)

**Goal**: Correlate features with outcomes, perform McNemar's test, logistic regression (with VIF check), sensitivity analysis, and generate a summary report.

**Independent Test**: Run the analysis script on `data/processed/semantic_results.json` and verify `results/` contains p-values, regression coefficients, and sensitivity reports.

**Depends on**: T019 (US2) must complete to provide `data/processed/semantic_results.json`.

### Implementation for User Story 3

- [X] T021 [US3] [Depends: T019] Implement `code/statistical_analysis.py` to merge `data/static_baseline.csv` and `data/processed/semantic_results.json` into a unified dataset
- [X] T021a [US3] [Depends: T021, T011a, T007] Validate merged dataset completeness (≥95% rows have all required fields: code, metrics, static labels, semantic vectors, LLM labels) of the **actual** sampled functions (target 800, or reduced count from T007). Calculate the validity percentage as (valid_rows / actual_sample_count) * 100 and report the count and percentage to `results/statistical_significance.json` to satisfy SC-005. (SC-005)
- [X] T022 [US3] Implement McNemar's test per smell category (aggregating paired detection outcomes per function) in `code/statistical_analysis.py` (FR-006)
- [X] T023 [US3] Implement Variance Inflation Factor (VIF) calculation in `code/statistical_analysis.py` for predictors (LOC, Cyclomatic, Semantic Mean) (FR-010)
- [X] T024 [US3] Implement logistic regression fitting in `code/statistical_analysis.py` that excludes predictors with VIF ≥ 5. **Define specific logic**: If VIF ≥ 5, **EXCLUDE the predictor with the highest VIF**. If the excluded predictor is the primary predictor of interest, **flag it in the output and proceed without it** (or abort if mandatory). **Flag high-VIF predictors and the chosen action** in the output (FR-007, FR-010)
- [X] T027 [US3] Generate `results/logistic_regression.json` containing coefficients, VIF scores, and **flagged high-VIF predictors** (FR-007, SC-001, SC-002)
- [X] T025 [US3] Implement sensitivity analysis in `code/statistical_analysis.py` sweeping LOC thresholds across the specific numeric range **LOC ∈ {50, 100, 150}** as required by FR-009, and **calculating and reporting false-positive and false-negative rates** for static-only detections to `results/sensitivity_metrics.json` (FR-009)
- [X] T025c [US3] [SC-002] [Depends: T019, T027] **NEW TASK**: Implement the correlation analysis required by **SC-002**. Calculate the correlation between **semantic embeddings** (mean of vector) and **LLM-only detection rates** by analyzing the **logistic regression coefficients** generated in T027. Specifically, correlate the magnitude of the semantic coefficient with the detection outcome to measure the contribution of semantic features. Output these correlation metrics to `results/statistical_significance.json` or a dedicated `results/semantic_correlation.json`. (SC-002)
- [X] T026 [US3] Generate `results/statistical_significance.json` containing McNemar p-values (FR-006, SC-003)
- [X] T028 [US3] Generate `results/sensitivity_report.md` listing smells detected *only* by static, *only* by LLM, **and false-positive/false-negative rates** (FR-009)
- [X] T029 [US3] Verify `results/` artifacts contain valid data for ≥ 95% of the sample (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030 [P] [Depends: T030b] Update project documentation: Consolidate CLI instructions (`README.md`), dependency list (`requirements.txt`), and setup steps into a single task. Write CLI argument description, usage examples, environment setup, and list all dependencies. Create `quickstart.md` with step-by-step setup and run instructions. (Consolidated from T030a, T030b, T030c)
- [X] T031a [P] Remove unused imports from all `code/` modules: Run `autoflake --in-place --remove-all-unused-imports code/**/*.py` and verify exit code 0.
- [X] T031b [P] Apply black formatting to all `code/` modules: Run `black --check code/` and `black code/` to format files.
- [X] T031c [P] Extract helper functions for metric calculation and error handling from `code/statistical_analysis.py` and `code/data_pipeline.py` into `code/helpers.py` with a consistent naming convention
- [X] T032a [P] Profile and optimize batch loading in `code/semantic_analysis.py` to reduce RAM peak
- [X] T032b [P] Verify total runtime ≤ 6h via **timing run on a real, representative subset** (e.g., **the first 50 functions**) in `code/`. **Do NOT use mock data**. Execute the pipeline on this subset, record the wall-clock time to `results/runtime_log.json`, and **extrapolate the full runtime** based on the sample count to verify compliance with the ≤6h constraint (SC-004). (SC-004)
- [X] T033a [P] Add `tests/unit/test_data_pipeline.py::test_radon_metrics`
- [X] T033b [P] Add `tests/unit/test_semantic_analysis.py::test_parsing`
- [X] T034 [P] [Depends: T030] Run `quickstart.md` validation: Execute commands in `quickstart.md` in a fresh venv and capture exit code 0 to verify reproducibility.
- [X] T035 [P] [US1] Add `tests/contract/test_static_baseline_schema.py` to enforce CSV schema compliance (columns, types) for `data/static_baseline.csv` (SC-005)
- [X] T036 [P] [US2] Add `tests/contract/test_llm_output_schema.py` to enforce JSON schema compliance for LLM outputs in `data/processed/semantic_results.json` (FR-004)
- [X] T037 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_mcnemar_pvalue` to verify McNemar's test calculation logic against a known small dataset
- [X] T038 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_vif_calculation` to verify VIF calculation logic and threshold flagging (FR-010)
- [X] T039 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_sensitivity_sweep` to verify the sweep logic at representative intervals and FP/FN rate calculation (FR-009)
- [X] T040 [P] [US1] Add `tests/unit/test_data_pipeline.py::test_sample_size_limit` to verify the dynamic sample size reduction logic when time constraints are hit (FR-001)
- [X] T041 [P] [US2] Add `tests/unit/test_semantic_analysis.py::test_context_window_truncation` to verify functions exceeding context limits are truncated/skipped correctly and logged (Edge Case)
- [X] T042 [P] [US2] Add `tests/unit/test_semantic_analysis.py::test_unparseable_llm_output` to verify that malformed JSON outputs are logged as "Unparseable" and do not crash the pipeline (Edge Case)
- [X] T043 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_high_vif_exclusion` to verify that logistic regression correctly excludes or flags predictors with VIF ≥ 5 (FR-007, FR-010)
- [X] T044 [P] [US1] Add `tests/unit/test_data_pipeline.py::test_pylint_normalization` to verify Pylint codes map correctly to canonical smell names using `contracts/smell_mapping.json` (FR-003)
- [X] T045 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_drop_off_rate_calculation` to verify the explicit calculation and reporting of the drop-off rate from the original sample (SC-005)
- [X] T046 [P] [US2] Refine `contracts/llm_prompt.txt` to explicitly enforce strict JSON output formatting (e.g., "Output ONLY a JSON array, no markdown, no text") to reduce parsing failures identified in T017
- [X] T047 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_complementarity_summary_generation` to verify the logic that identifies smells detected *only* by static vs *only* by LLM (FR-009, SC-003)

- [X] T048 [P] [US1] **Review Concern: Data Source Verification**: Implement a pre-flight check in `code/data_pipeline.py` to verify the `codeparrot/github-code` dataset is accessible and contains the `train` split before attempting to stream. If the dataset is unreachable, raise a `ConnectionError` immediately with a clear message pointing to the dataset ID, ensuring no synthetic fallback is attempted (Constitution Principle II).
- [X] T049 [P] [US2] **Review Concern: Model Integrity**: Add a checksum verification step in `code/semantic_analysis.py` (T014) to validate the integrity of the downloaded `CodeLlama-7B-Instruct-GGUF` file against the HuggingFace Hub checksum before loading, preventing silent corruption of the 4-bit model (Constitution Principle III).
- [X] T050 [P] [US3] **Review Concern: Statistical Robustness**: Implement a bootstrap resampling procedure in `code/statistical_analysis.py` (T022) to calculate confidence intervals for the McNemar's test p-value, ensuring the statistical significance is robust against the specific sample size variations observed in T007.
- [X] T051 [P] [US3] **Review Concern: Multicollinearity Handling**: Extend T024 to automatically generate a `results/vif_report.md` that visualizes the correlation matrix of predictors and explicitly documents the residualization or exclusion steps taken for any predictor with VIF ≥ 5, ensuring full transparency of the statistical model selection process (FR-010).
- [ ] T052 [P] [Polish] **Review Concern: Reproducibility**: Create a `results/run_metadata.json` file that captures the exact environment hash (from `pip freeze`), dataset version commit ID, and the random seed used for the sample, ensuring that every result set can be exactly reproduced (Constitution Principle I).
- [ ] T053 [P] [US1] **Review Concern: Sample Bias**: Implement a stratified sampling strategy in T007 that ensures the 800 functions (or the reduced count) are distributed proportionally across different file types or repository categories if metadata is available in `codeparrot/github-code`, to prevent bias towards a single code style (FR-001).
- [ ] T054 [P] [US2] **Review Concern: Prompt Consistency**: Add a unit test in `tests/unit/test_semantic_analysis.py` that verifies the loaded prompt in `contracts/llm_prompt.txt` matches the exact string template used in the inference loop, preventing drift between the contract and implementation (FR-004).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US1 (`data/static_baseline.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data output from US1 and US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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