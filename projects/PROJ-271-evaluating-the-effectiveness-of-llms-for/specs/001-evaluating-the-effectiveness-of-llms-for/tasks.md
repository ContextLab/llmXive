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

- [X] T001a [P] Initialize project directory structure (`projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/`, `data/raw/`, `data/processed/`, `results/`, `tests/unit/`, `tests/contract/`).
- [X] T001b [P] Configure linting: Create `.flake8` in `code/` directory with settings for max-line-length=88, ignore=E203,W503.
- [X] T001c [P] Configure formatting: Create `pyproject.toml` in `code/` directory with black settings (line-length=88, target-version=py311).

- [X] T002 [P] Initialize Python project with `requirements.txt` containing `datasets`, `pandas`, `radon`, `pylint`, `sentence-transformers`, `llama-cpp-python`, `scikit-learn`, `statsmodels`, `numpy`, and `psutil` (explicitly for FR-008 monitoring requirements).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` defining paths (`data/`, `results/`), random seeds (seed=42 for all phases), and batch size constants (LLM batch ≤ 10).
- [X] T005 [P] Implement `code/__init__.py` and ensure directory structure matches `data/raw`, `data/processed`, `results`.
- [X] T006a [P] Setup logging configuration in `code/config.py` to define log format, file handlers, and levels for metrics (FR-008).
- [X] T006b [P] Implement `code/monitoring.py` to capture RAM usage, CPU utilization, and inference time using `psutil` for use in inference loops, explicitly recording these metrics **per batch executed** to `results/resource_metrics.json` (FR-008). **Note**: Metrics are recorded for every batch to verify the strict **≤10** batch size constraint mandated by the Plan and Constitution.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Data Pipeline and Static Analysis Baseline (Priority: P1) 🎯 MVP

**Goal**: Ingest a sampled subset of `codeparrot/github-code`, compute structural metrics via `radon`, and generate a baseline "smell label" set using Pylint.

**Independent Test**: Run the pipeline on a local subset (e.g., a small number of functions) and verify `data/static_baseline.csv` exists with correct columns (`code`, `loc`, `cyclomatic_complexity`, `static_smell_labels`).

### Implementation for User Story 1

- [X] T007 [US1] Implement `code/data_pipeline.py` to sample functions from `codeparrot/github-code` using HuggingFace `datasets` with **streaming=True**, split='train', and a pinned random seed (seed=42). **Target sample size: A sufficiently large corpus of functions to ensure statistical power and representativeness across diverse codebases.**. Implement a **dynamic runtime check**: process a small batch (e.g., a limited number of functions) to estimate time per function; calculate N = max sample size such that (estimated_time_per_function * N) ≤ 5.5 hours. **If N < 100**, log a CRITICAL warning to `results/sample_report.json` and proceed with N (if N=0, abort). **Deliverable**: `results/sample_report.json` with schema: `{target_count:, actual_count: int, reduction_reason: string | null (default 'none'), estimated_time_hours: float}`. (FR-001)
- [X] T007a [US1] [Depends: T007] Verify the representativeness of the sampled subset if the dynamic reduction in T007 occurs. Compare the distribution of LOC and Cyclomatic Complexity in the reduced sample against the original population statistics (obtained from HuggingFace dataset metadata or a pre-computed histogram if available; otherwise log 'N/A'). Log the comparison to `results/sample_report.json`. (FR-001)
- [X] T008 [US1] Implement structural metric calculation in `code/data_pipeline.py` using `radon` to **calculate LOC, Cyclomatic Complexity, and Nesting Depth** for every sampled function. **Deliverable**: Update `code/data_pipeline.py` to output `nesting_depth` column. **Verification**: Verify `nesting_depth` is present in radon output and included in the processed data structure. (FR-002)
- [X] T009a [US1] Create `contracts/smell_mapping.json` defining a **fixed** mapping from common Pylint codes to canonical smell names derived from the LLM prompt categories (e.g., 'Long Method', 'Complex Logic'). Create the file with at least 5 common Pylint codes (e.g., C0111, R0913) mapped to canonical names before the full pipeline runs. (FR-003)
- [X] T009b [US1] [Depends: T007] Validate and update `contracts/smell_mapping.json` based on the **actual** Pylint error codes found in the sampled data from T007. **Update format**: Append any unmapped codes to the JSON array with `canonical_name: "Unknown"` and `status: "unmapped"`. (FR-003)
- [X] T009 [US1] [Depends: T009a, T009b] Implement the full Pylint normalization pipeline: (1) Load `contracts/smell_mapping.json` created in T009a/T009b; (2) Implement Pylint execution in `code/data_pipeline.py` to generate static smell labels AND normalize raw Pylint codes to canonical smell names using the mapping. Ensure the pipeline logs a warning if an unmapped code is encountered but continues. (FR-003)
- [X] T010 [US1] Implement error handling in `code/data_pipeline.py` to catch `radon` parsing errors, log the file, and exclude from final count (Edge Case).
- [X] T011a [US1] [Depends: T007, T008, T009] Write processed data to `data/static_baseline.csv` containing `code`, `loc`, `cyclomatic_complexity`, `nesting_depth`, and normalized `static_smell_labels` columns. **Data Types**: `loc` (int), `cyclomatic_complexity` (int), `nesting_depth` (int), `code` (string), `static_smell_labels` (string, pipe-delimited). (FR-001, FR-002)
- [X] T011b [US1] [Depends: T011a] Verify schema compliance of `data/static_baseline.csv` (columns: code, loc, cyclomatic_complexity, nesting_depth, static_smell_labels) and data types.
- [X] T012 [US1] [Depends: T011a, T011b] Add validation to ensure `data/static_baseline.csv` contains ≥ 95% of sampled functions with all required columns (FR-001, SC-005).
- [X] T012a [US1] [Depends: T012] Validate the target sample size of 800 against SC-005. Calculate validity percentage as (valid_rows / actual_sample_count) scaled to a standard percentage range.. If actual_sample_count < 800, log a deviation in `results/sample_report.json` and proceed. (SC-005)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Semantic Feature Extraction and LLM Inference (Priority: P2)

**Goal**: Compute semantic embeddings and generate "smell labels" via a CPU-quantized LLM (CodeLlama-7B-GGUF) using a standardized prompt.

**Independent Test**: Process a single function through the embedding model and LLM, verifying a dense vector is produced and the LLM returns a parsable list of smells.

**Depends on**: T011a (US1) must complete to provide `data/static_baseline.csv`.

### Implementation for User Story 2

- [X] T013 [US2] [Depends: T011a] Implement `code/semantic_analysis.py` to load `sentence-transformers/all-MiniLM-L-v2` and compute dense vectors for functions in `data/static_baseline.csv`. **Note**: This task must run sequentially before T014 to avoid RAM contention. (FR-005)
- [X] T014 [US2] [Depends: T013] Implement `code/semantic_analysis.py` to load **`TheBloke/CodeLlama-Instruct-GGUF`** specifically using the **4-bit quantized** variant (file suffix must be `q4_0.gguf` or `Q4_K_M.gguf`). Use `llama-cpp-python` on CPU device. (FR-004)
- [X] T014a [US2] [Depends: T014] Implement a runtime check in `code/semantic_analysis.py` to inspect `model.info.quantization` attribute or file suffix to confirm the model is 4-bit; if not, **raise an explicit error and halt the pipeline**. **Rationale**: This ensures compliance with Constitution Principle VI (Memory Constraint) and FR-004. (FR-004, Constitution Principle VI)
- [X] T015a [US2] Create `contracts/llm_prompt.txt` containing the exact standardized "Code Smell Detection" prompt text to request a JSON list of smell categories (FR-004).
- [X] T015 [US2] [Depends: T015a] Implement the standardized "Code Smell Detection" prompt in `code/semantic_analysis.py` by loading the exact prompt text from `contracts/llm_prompt.txt`. (FR-004)
- [X] T016 [US2] [Depends: T014a, T015] Implement batched inference loop in `code/semantic_analysis.py` with batch size **≤ 10** and explicit `gc.collect()` between batches to manage RAM, and record batch-level metrics (RAM, CPU, time). **Note**: Batch size is a strict resource constraint derived from Plan.md Complexity Tracking and Constitution Principle VI.. (FR-004, FR-008)
- [X] T016a [US2] [Depends: T016] Implement logic in `code/semantic_analysis.py` to handle the '≤50' constraint from FR-008. If the configured batch size is < 50, log a deviation in `results/resource_metrics.json` stating "Batch size < 50 (actual: 10) due to Plan constraint". (FR-008)
- [X] T016b [US2] [Depends: T016] Ensure metrics are recorded for **every batch executed** in `results/resource_metrics.json`, explicitly noting the batch size used (10) against the FR-008 limit (50). (FR-008)
- [X] T017 [US2] Implement JSON parsing and error handling in `code/semantic_analysis.py` to log "Unparseable" for malformed LLM outputs (Edge Case).
- [X] T018 [US2] Implement context window check in `code/semantic_analysis.py` to **truncate functions from the start (preserving the function header/definition)** if they exceed model limits, skip if truncation is insufficient, and log the count (Edge Case). **Rationale**: Preserving the header is critical for code smell detection.
- [X] T019 [US2] [Depends: T013, T014a, T016] Write embeddings and LLM labels to `data/processed/semantic_results.json`. (FR-004, FR-005)
- [X] T020 [US2] [Depends: T006b] Add monitoring in `code/semantic_analysis.py` to record peak RAM, CPU utilization, and inference time per batch to `results/resource_metrics.json` using `code/monitoring.py`. (FR-008)
- [X] T020a [US2] [Depends: T020] Parse `results/resource_metrics.json`, compare peak RAM against the system-imposed memory limit (Constitution Principle VI), and generate `results/compliance_verification.json` with a pass/fail status and specific flags if breached. (FR-008, SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Statistical Analysis and Reporting (Priority: P3)

**Goal**: Correlate features with outcomes, perform McNemar's test, logistic regression (with VIF check), sensitivity analysis, and generate a summary report.

**Independent Test**: Run the analysis script on `data/processed/semantic_results.json` and verify `results/` contains p-values, regression coefficients, and sensitivity reports.

**Depends on**: T019 (US2) must complete to provide `data/processed/semantic_results.json`.

### Implementation for User Story 3

- [ ] T021 [US3] [Depends: T019] Implement `code/statistical_analysis.py` to merge `data/static_baseline.csv` and `data/processed/semantic_results.json` into a unified dataset. **Deliverable**: `data/merged_analysis.json` containing `code`, `metrics`, `static_labels`, `semantic_vectors`, `llm_labels`, and derived flags (`static_only`, `llm_only`, `both`).
- [X] T021a [US3] [Depends: T021, T011a, T007] Validate merged dataset completeness (≥95% rows have all required fields: code, metrics, static labels, semantic vectors, LLM labels) of the **actual** sampled functions. Calculate the validity percentage as (valid_rows / actual_sample_count) * 100 and report the count and percentage to `results/statistical_significance.json` to satisfy SC-005. (SC-005)
- [X] T022 [US3] Implement McNemar's test per smell category (aggregating paired detection outcomes per function) in `code/statistical_analysis.py`. (FR-006)
- [X] T023 [US3] Implement Variance Inflation Factor (VIF) calculation in `code/statistical_analysis.py` for predictors (LOC, Cyclomatic, **Nesting Depth**, Semantic Mean). (FR-010)
- [X] T024 [US3] Implement logistic regression fitting in `code/statistical_analysis.py` that excludes predictors with VIF ≥ 5. **Define specific logic**: If VIF ≥ 5, **EXCLUDE the predictor with the highest VIF**. If the excluded predictor is 'nesting_depth', **log a warning in `results/vif_report.md` explaining the exclusion** to ensure the metric is not silently dropped. If the excluded predictor is the primary predictor of interest, **flag it in the output and proceed without it** (or abort if mandatory). **Flag high-VIF predictors and the chosen action** in the output. (FR-007, FR-010)
- [X] T027 [US3] Generate `results/logistic_regression.json` containing coefficients, VIF scores, and **flagged high-VIF predictors**. (FR-007, SC-001, SC-002)
- [ ] T025 [US3] Implement sensitivity analysis in `code/statistical_analysis.py` sweeping LOC thresholds across the specific numeric range **LOC ∈ {low, medium, high}** as required by FR-009. **Explicitly calculate and report false-positive and false-negative rates** for static-only detections: FP Rate = (Static Only / Total Static Detected), FN Rate = (Missed by Static / Total Detected by LLM). **Write the results to `results/sensitivity_metrics.json` as a list of objects: `[{threshold: int, fp_rate: float, fn_rate: float}]`**. (FR-009)
- [X] T025a [US3] [Depends: T025] **Verification Task**: Explicitly calculate and output the **False-Positive Rate** (Static Only / Total Static Detected) and **False-Negative Rate** (Missed by Static / Total Detected by LLM) for each threshold in the sensitivity sweep. Ensure these specific metrics are written to `results/sensitivity_metrics.json` with the exact schema: `[{threshold: int, fp_rate: float, fn_rate: float}]`. (FR-009)
- [X] T025c [US3] [SC-002] [Depends: T021, T019, T011a] **NEW TASK**: Implement the correlation analysis required by **SC-002**. **Calculate the Pearson correlation** between **mean semantic embeddings** (average of vector components per function) and **LLM-only detection rates** (binary flag: 1 if detected by LLM and not Static, 0 otherwise) using the merged dataset from T021. **Do NOT use regression coefficients**. **Output the correlation coefficient and p-value to `results/semantic_correlation.json` with schema: `{correlation_coefficient: float, p_value: float, method: "pearson"}`**. (SC-002)
- [X] T026 [US3] Generate `results/statistical_significance.json` containing McNemar p-values. (FR-006, SC-003)
- [X] T028 [US3] Generate `results/sensitivity_report.md` listing smells detected *only* by static, *only* by LLM, **and false-positive/false-negative rates**. (FR-009)
- [X] T029 [US3] Verify `results/` artifacts contain valid data for ≥ 95% of the sample. (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T030a [P] Update `README.md` with CLI instructions, usage examples, environment setup, and dependency list.
- [X] T030b [P] Create `quickstart.md` with step-by-step setup and run instructions.
- [X] T030c [P] Update `requirements.txt` with all dependencies.
- [X] T030 [P] [Depends: T030a, T030b, T030c] Consolidate CLI instructions, dependency list, and setup steps into a single task. Write CLI argument description, usage examples, environment setup, and list all dependencies. Create `quickstart.md` with step-by-step setup and run instructions. (Consolidated from T030a, T030b, T030c)

- [X] T031a [P] Remove unused imports from all `code/` modules: Run `autoflake --in-place --remove-all-unused-imports code/**/*.py` and verify exit code 0.
- [X] T031b [P] Apply black formatting to all `code/` modules: Run `black --check code/` and `black code/` to format files.
- [X] T031c [P] Extract helper functions for metric calculation and error handling from `code/statistical_analysis.py` and `code/data_pipeline.py` into `code/helpers.py` with a consistent **snake_case** naming convention.
- [X] T032a [P] Profile and optimize batch loading in `code/semantic_analysis.py` to reduce RAM peak.
- [X] T032b [P] Verify total runtime ≤ 6h via **timing run on a real, representative subset** (e.g., **the a sample of functions**) in `code/`. **Do NOT use mock data**. Execute the pipeline on this subset, record the wall-clock time to `results/runtime_log.json`, and **extrapolate the full runtime** using the formula: `full_runtime = (sample_time / sample_count) * [target_sample_size]` to verify compliance with the ≤6h constraint. (SC-004)

- [X] T033a [P] Add `tests/unit/test_data_pipeline.py::test_radon_metrics`.
- [X] T033b [P] Add `tests/unit/test_semantic_analysis.py::test_parsing`.
- [X] T034 [P] [Depends: T030] Run `quickstart.md` validation: Execute commands in `quickstart.md` in a fresh venv and capture exit code 0 to verify reproducibility.
- [X] T035 [P] [US1] Add `tests/contract/test_static_baseline_schema.py` to enforce CSV schema compliance (columns, types) for `data/static_baseline.csv`. (SC-005)
- [X] T036 [P] [US2] Add `tests/contract/test_llm_output_schema.py` to enforce JSON schema compliance for LLM outputs in `data/processed/semantic_results.json`. (FR-004)
- [X] T037 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_mcnemar_pvalue` to verify McNemar's test calculation logic against a known small dataset.
- [ ] T038 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_vif_calculation` to verify VIF calculation logic and threshold flagging. (FR-010)
- [ ] T039 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_sensitivity_sweep` to verify the sweep logic at representative intervals and FP/FN rate calculation. (FR-009)
- [ ] T040 [P] [US1] Add `tests/unit/test_data_pipeline.py::test_sample_size_limit` to verify the dynamic sample size reduction logic when time constraints are hit. (FR-001)
- [X] T041 [P] [US2] Add `tests/unit/test_semantic_analysis.py::test_context_window_truncation` to verify functions exceeding context limits are truncated/skipped correctly and logged. (Edge Case)
- [X] T042 [P] [US2] Add `tests/unit/test_semantic_analysis.py::test_unparseable_llm_output` to verify that malformed JSON outputs are logged as "Unparseable" and do not crash the pipeline. (Edge Case)
- [ ] T043 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_high_vif_exclusion` to verify that logistic regression correctly excludes or flags predictors with VIF ≥ 5. (FR-007, FR-010)
- [ ] T044 [P] [US1] Add `tests/unit/test_data_pipeline.py::test_pylint_normalization` to verify Pylint codes map correctly to canonical smell names using `contracts/smell_mapping.json`. (FR-003)
- [ ] T045 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_drop_off_rate_calculation` to verify the explicit calculation and reporting of the drop-off rate from the original sample. (SC-005)
- [X] T046 [P] [US2] Refine `contracts/llm_prompt.txt` to explicitly enforce strict JSON output formatting (e.g., "Output ONLY a JSON array, no markdown, no text") to reduce parsing failures identified in T017.
- [ ] T047 [P] [US3] Add `tests/unit/test_statistical_analysis.py::test_complementarity_summary_generation` to verify the logic that identifies smells detected *only* by static vs *only* by LLM. (FR-009, SC-003)

- [ ] T048 [P] [US1] **Review Concern: Data Source Verification**: Implement a pre-flight check in `code/data_pipeline.py` to verify the `codeparrot/github-code` dataset is accessible and contains the `train` split before attempting to stream. If the dataset is unreachable, raise a `ConnectionError` immediately with a clear message pointing to the dataset ID, ensuring no synthetic fallback is attempted. (Constitution Principle II)
- [X] T049 [P] [US2] **Review Concern: Model Integrity**: Add a checksum verification step in `code/semantic_analysis.py` (T014) to validate the integrity of the downloaded `CodeLlama-7B-Instruct-GGUF` file against the HuggingFace Hub checksum before loading, preventing silent corruption of the 4-bit model. (Constitution Principle III)
- [ ] T050 [P] [US3] **Review Concern: Statistical Robustness**: Implement a bootstrap resampling procedure in `code/statistical_analysis.py` (T022) to calculate confidence intervals for the McNemar's test p-value, ensuring the statistical significance is robust against the specific sample size variations observed in T007.
- [X] T051 [P] [US3] **Review Concern: Multicollinearity Handling**: Extend T024 to automatically generate a `results/vif_report.md` that visualizes the correlation matrix of predictors and explicitly documents the residualization or exclusion steps taken for any predictor with VIF ≥ 5, ensuring full transparency of the statistical model selection process. (FR-010)
- [X] T052 [P] [Polish] **Review Concern: Reproducibility**: Create a `results/run_metadata.json` file that captures the exact environment hash (from `pip freeze`), dataset version commit ID, and the random seed used for the sample, ensuring that every result set can be exactly reproduced. (Constitution Principle I)
- [ ] T053 [US1] **Review Concern: Sample Bias**: [Depends: T007] **Implement** a **deterministic random sampling strategy** in `code/data_pipeline.py` (T007) that selects a representative subset of functions (target 800, or reduced count) using a **pinned random seed** (seed=42) and the `datasets` streaming API. This ensures reproducibility and avoids the memory overhead of stratified sampling. **Verification**: Log the distribution of languages in the final sample to `results/sample_report.json` and compare it to the global distribution to confirm representativeness. (FR-001)
- [X] T054 [P] [US2] **Review Concern: Prompt Consistency**: Add a unit test in `tests/unit/test_semantic_analysis.py` that verifies the loaded prompt in `contracts/llm_prompt.txt` matches the exact string template used in the inference loop, preventing drift between the contract and implementation. (FR-004)
- [ ] T055 [P] [US3] **Review Concern: Outlier Handling**: Add a data cleaning step in `code/statistical_analysis.py` (T021) to identify and flag statistical outliers in structural metrics (e.g., LOC > 5000) before running regression, and provide an option to run the analysis both with and without these outliers to assess their impact on the VIF and regression coefficients.
- [X] T056 [P] [US3] **Review Concern: Sensitivity Analysis Granularity**: Extend T025 to include a secondary sensitivity sweep for **Cyclomatic Complexity thresholds** (e.g., CC ∈ {5, 10, 15}) in addition to LOC, to determine if structural complexity metrics provide a more stable predictor for static-only detection than line count alone, and report these findings in `results/sensitivity_report.md`. (REMOVED: Unapproved scope)
- [X] T057 [P] [US2] **Review Concern: Context Window Optimization**: Implement an adaptive truncation strategy in `code/semantic_analysis.py` (T018) that prioritizes preserving the **function body and docstring** over the header if the function is extremely long, and log the specific truncation strategy used per function to `results/truncation_log.json` to analyze if header loss impacts smell detection accuracy.
- [X] T058 [P] [US3] **Review Concern: Complementarity Visualization**: Generate a `results/complementarity_matrix.png` (using `matplotlib`) that visually plots the overlap of detected smells between Static and LLM modes (Venn diagram or UpSet plot) to provide an intuitive summary of the complementarity findings for the final report. (REMOVED: Plot type not specified)
- [ ] T059 [P] [Polish] **Review Concern: Error Recovery**: Implement a retry mechanism with exponential backoff in `code/data_pipeline.py` (T048) for transient network failures when streaming from HuggingFace, ensuring the pipeline can recover from temporary connectivity issues without failing the entire run.
- [ ] T060 [P] [US3] **Review Concern: Outlier Handling**: Add a data cleaning step in `code/statistical_analysis.py` (T021) to identify and flag statistical outliers in structural metrics (e.g., LOC > 5000) before running regression, and provide an option to run the analysis both with and without these outliers to assess their impact on the VIF and regression coefficients.
- [ ] T061 [P] [US3] **Review Concern: Statistical Power Analysis**: Implement a power analysis calculation in `code/statistical_analysis.py` to estimate the minimum detectable effect size for the McNemar test given the final sample size (post-drop-off) and the observed proportions, and report this in `results/power_analysis.json`. (REMOVED: Unapproved scope)
- [ ] T062 [P] [US3] **Review Concern: False Discovery Rate Control**: Apply the Benjamini-Hochberg procedure to the p-values generated from the multiple McNemar tests (one per smell category) in `code/statistical_analysis.py` to control the False Discovery Rate (FDR), and report the adjusted p-values in `results/fdr_adjusted_significance.json`. (REMOVED: Unapproved scope)
- [ ] T063 [P] [US1] **Review Concern: Data Leakage Prevention**: Add a strict check in `code/data_pipeline.py` to ensure that the random seed used for sampling is different from any seed used in the LLM inference or statistical analysis phases, and log these distinct seeds to `results/run_metadata.json` to prevent accidental data leakage or pseudo-determinism. (REMOVED: Contradicts Constitution Principle I)
- [X] T064 [P] [US2] **Review Concern: Temperature Sensitivity**: Implement a controlled experiment in `code/semantic_analysis.py` that runs the LLM inference on a fixed subset of functions with varying temperature settings (e.g., 0.0, 0.5, 0.7) to quantify the variance in smell detection outputs, and report the standard deviation of detection counts in `results/temperature_sensitivity.json`. (FR-004)
- [ ] T065 [P] [US3] **Review Concern: Non-Linear Feature Interactions**: Extend `code/statistical_analysis.py` to include an interaction term between structural metrics (e.g., LOC * Cyclomatic Complexity) in the logistic regression model if VIF permits, and report if this interaction significantly improves model fit (AIC/BIC comparison). (FR-007)
- [X] T066 [P] [Polish] **Review Concern: Artifact Versioning**: Implement a script `tools/version_artifacts.py` that automatically generates a SHA-256 hash for every output file in `data/` and `results/` after a successful run, and appends these hashes to a cumulative `artifacts_manifest.json` to track the evolution of results across runs. (Constitution Principle III, V)
- [ ] T067 [P] [US3] **Review Concern: False Discovery Rate Control**: Apply the Benjamini-Hochberg procedure to the p-values generated from the multiple McNemar tests (one per smell category) in `code/statistical_analysis.py` to control the False Discovery Rate (FDR), and report the adjusted p-values in `results/fdr_adjusted_significance.json`. (REMOVED: Unapproved scope)
- [ ] T068 [P] [US1] **Review Concern: Dataset Diversity Check**: Implement a stratification check in `code/data_pipeline.py` to ensure the sampled functions are not dominated by a single file extension or repository type, and log the diversity metrics (entropy of file types) to `results/sample_report.json`. (REMOVED: Unapproved scope)
- [ ] T069 [P] [US2] **Review Concern: Embedding Dimensionality Reduction**: If the semantic vectors are too large for downstream analysis or visualization, implement PCA or t-SNE in `code/statistical_analysis.py` to reduce the dimensionality of the embeddings to 2D/3D for the `complementarity_matrix.png` (T058) while preserving variance, and report the explained variance ratio. (FR-005)
- [ ] T070 [P] [US3] **Review Concern: Robustness to Noise**: Add a synthetic noise injection test in `tests/unit/test_statistical_analysis.py` where random noise is added to the structural metrics to verify that the VIF calculation and logistic regression coefficients remain stable and do not diverge unexpectedly. (FR-010)
