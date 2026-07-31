# Tasks: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `state/`)
- [X] T002 Initialize Python project with `requirements.txt` (transformers, scikit-learn, pandas, tree-sitter, networkx, requests, pyyaml, bitsandbytes, sentence-transformers, pytest, radon, statsmodels)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Implement `src/utils/config.py` with seeds, paths, runtime thresholds (hourly limit, gigabyte RAM cap), and the list of candidate LLMs. (FR-002, SC-005).
- [ ] T004a Implement `src/utils/model_selector.py` to implement a deterministic model selection strategy based on the candidate list in T004. **Logic**: The selection must be deterministic (e.g., based on a fixed seed or a static configuration) and logged. **Constraint**: Do NOT use runtime RAM checks for selection to ensure reproducibility (Constitution Principle I: Reproducibility). The selected model must be compatible with all languages in the stratified sample. If the primary list fails, allow fallback to other CPU-compatible models if they are logged and deterministic. (FR-002, Constitution I). **Dependency**: Depends on: T004 (file I/O completion). **Note**: Ensure the logging mechanism is thread-safe if T004a is run in a parallel context with other tasks.
- [X] T005 [P] Implement `src/utils/validate_urls.py` to validate dataset URLs against `research.md` manifest (Constitution II). **Constraint**: This task MUST complete before T011 starts.
- [X] T006 [P] Implement `src/utils/logger.py` with structured logging for pipeline stages
- [ ] T007a [P] Create `contracts/dataset.schema.yaml` defining the `CodeSnippet` schema. **Content**:
```yaml
type: object
properties:
 id: {type: string}
 language: {type: string, enum: [C, Python, JavaScript]}
 source_code: {type: string}
 ground_truth_label: {type: string}
 ground_truth_category: {type: string}
required: [id, language, source_code, ground_truth_label, ground_truth_category]
```
**Priority**: P1.
- [ ] T007b [P] Generate base `CodeSnippet` dataclass in `src/models/code_snippet.py` FROM `contracts/dataset.schema.yaml` using `pydantic`. **Constraint**: Do NOT manually implement fields; ensure schema drift is prevented by generating from the contract. (Constitution IV, Plan Project Structure). **Dependency**: Depends on: T007a. **Pre-check**: Verify T007a exists before generation. **Sub-steps**: 1. Write/Execute generation script. 2. **Verify**: Explicitly check that `src/models/code_snippet.py` exists and that the generated fields match `contracts/dataset.schema.yaml`. If verification fails, abort.
- [ ] T007c [P] **Run Generator**: Execute the schema-to-code generation script for `contracts/dataset.schema.yaml` and verify the output `src/models/code_snippet.py` exists and matches the schema. **Constraint**: This task MUST run after T007b. (Constitution IV).
- [ ] T008a [P] Create `contracts/feature.schema.yaml` defining the `FeatureVector` schema. **Content**:
```yaml
type: object
properties:
 ast_depth: {type: integer}
 cyclomatic_complexity: {type: integer}
 node_count: {type: integer}
 taint_api_count: {type: integer}
 sanitization_present: {type: boolean}
 embedding_similarity_score: {type: number}
required: [ast_depth, cyclomatic_complexity, node_count, taint_api_count, sanitization_present, embedding_similarity_score]
```
**Priority**: P1.
- [ ] T008b [P] Generate base `FeatureVector` dataclass in `src/models/feature_vector.py` FROM `contracts/feature.schema.yaml` using `pydantic`. **Constraint**: Do NOT manually implement fields; ensure schema drift is prevented by generating from the contract. (Constitution IV, Plan Project Structure). **Dependency**: Depends on: T008a. **Pre-check**: Verify T008a exists before generation. **Sub-steps**: 1. Write/Execute generation script. 2. **Verify**: Explicitly check that `src/models/feature_vector.py` exists and that the generated fields match `contracts/feature.schema.yaml`. If verification fails, abort.
- [ ] T008c [P] **Run Generator**: Execute the schema-to-code generation script for `contracts/feature.schema.yaml` and verify the output `src/models/feature_vector.py` exists and matches the schema. **Constraint**: This task MUST run after T008b. (Constitution IV).
- [ ] T009a [P] Create `contracts/prediction.schema.yaml` defining the `PredictionResult` schema. **Content**:
```yaml
type: object
properties:
 snippet_id: {type: string}
 predicted_label: {type: string}
 predicted_category: {type: string}
 is_correct: {type: boolean}
 inference_time_ms: {type: number}
required: [snippet_id, predicted_label, predicted_category, is_correct, inference_time_ms]
```
**Priority**: P1.
- [ ] T009b [P] Generate base `PredictionResult` dataclass in `src/models/prediction_result.py` FROM `contracts/prediction.schema.yaml` using `pydantic`. **Constraint**: Do NOT manually implement fields; ensure schema drift is prevented by generating from the contract. (Constitution IV, Plan Project Structure). **Dependency**: Depends on: T009a. **Pre-check**: Verify T009a exists before generation. **Sub-steps**: 1. Write/Execute generation script. 2. **Verify**: Explicitly check that `src/models/prediction_result.py` exists and that the generated fields match `contracts/prediction.schema.yaml`. If verification fails, abort.
- [ ] T009c [P] **Run Generator**: Execute the schema-to-code generation script for `contracts/prediction.schema.yaml` and verify the output `src/models/prediction_result.py` exists and matches the schema. **Constraint**: This task MUST run after T009b. (Constitution IV).
- [ ] T009d [P] Create `contracts/analysis_metric.schema.yaml` defining the `AnalysisMetric` schema. **Content**:
```yaml
type: object
properties:
 metric_name: {type: string}
 feature_name: {type: string}
 value: {type: number}
 p_value: {type: number}
 adjusted_p_value: {type: number}
 method: {type: string}
required: [metric_name, feature_name, value, p_value, adjusted_p_value, method]
```
**Priority**: P1.
- [ ] T009e [P] **Run Generator**: Execute the schema-to-code generation script for `contracts/analysis_metric.schema.yaml` and verify the output `src/models/analysis_metric.py` exists and matches the schema. **Constraint**: This task MUST run after T009d. (Constitution IV).
- [X] T010 [P] Implement `src/utils/hash_artifacts.py` for checksum generation and state file updates (Constitution V)
- [X] T013d [P] Implement `src/utils/memory_monitor.py` to track runtime memory usage. **Logic**: Expose a context manager or utility function to check RAM usage and trigger batch size reduction if a high threshold is approached. (FR-002, SC-005).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Zero-Shot Vulnerability Detection Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest dataset, run zero-shot LLM inference, and generate correctness flags against ground truth.

**Independent Test**: Process a small, fixed subset of known vulnerable and known safe snippets, verifying structured JSON output with predicted label, confidence, and `is_correct` flag.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `src/data/download.py` to fetch **VulDeePecker** (Python), **BigVul** (C and JavaScript), and **official NIST Juliet repository** for C/C++. **CRITICAL**: **Primary Mandate**: NIST Juliet for C/C++. **Constraint**: The script MUST attempt to fetch NIST Juliet for C/C++ first. **Fallback Logic**: If NIST Juliet fetch fails (HTTP 404, network timeout, checksum mismatch), the script MUST automatically fallback to fetching **BigVul** for C/C++ analysis as explicitly required by `plan.md` 'Dataset Substitution' and `spec.md` FR-001. **Fail-Loudly Policy**: ONLY if BOTH NIST Juliet AND BigVul fetches fail for C/C++, the script MUST raise an exception and halt execution. Log the error to `data/logs/error.log` and exit with a non-zero code. **Spec Amendment Step**: If the NIST fetch fails, the script MUST log a warning and **update `spec.md` FR-001** (or a derived config) to explicitly state: "NIST Juliet unavailable; using BigVul as sanctioned substitution." This ensures the spec reflects reality before execution proceeds. **Output**: Save downloaded data to `data/raw/vuldeepecker.parquet`, `data/raw/bigvul_c.parquet`, `data/raw/bigvul_js.parquet`. (FR-001). **Dependency**: **Depends on: T005** (URL validation must occur before fetch).
- [ ] T012 [US1] Implement `src/data/preprocess.py` to parse raw datasets, extract code snippets, and map to `CodeSnippet` entity; **EXPLICITLY EXTRACT AND PRESERVE** the `language` field for every sample. **Stratified Sampling**: Implement stratified sampling by `language` and `ground_truth_category` to select up to 5,000 samples, ensuring proportional representation. **Edge Case Handling**: Samples with missing ground-truth labels MUST be **EXCLUDED from the predictions.csv** (accuracy calculation) but **INCLUDED in the features.csv** with a `label_missing: true` flag. **CRITICAL**: For these samples, perform **FULL feature extraction** (no nulls for features). The `NaN` value is ONLY to be used if the code snippet itself is malformed and parsing fails, NOT for missing labels. This satisfies the spec's requirement to extract features for *every* code snippet to serve as predictors. **Output**: Save to `data/processed/predictions.csv` and `data/processed/features.csv`. (FR-001). **Dependency**: **Depends on: T011** (data must be downloaded first).
- [X] T013 [US1] Implement `src/services/llm_inference.py` **Zero-Shot Inference Service**. **Sub-steps**: 1. **Model Loading**: Load the selected model (from T004a) in low-bit quantized mode on CPU. 2. **Inference Loop**: Enforce **Zero-Shot** methodology (prompt: "Identify any security vulnerability in the following code: {code}."). 3. **Response Parsing**: Map LLM responses to categories: "SQLi", "sql injection" -> "SQLi"; "buffer overflow", "overflow" -> "Buffer Overflow"; "none", "no vulnerability" -> "none"; "maybe", "unclear", "possibly", "likely", "unknown error", "potential risk", "vulnerability detected", or any unmapped string -> "uncertain". 4. **Memory Safety**: Use the `MemoryMonitor` from T013d to track usage. 5. **Circuit Breaker**: If runtime > 90% of 6 hours, **REDUCE DATASET SIZE** via stratified sampling to **[deferred]** of remaining samples to ensure ALL features are computed for the reduced set, preserving FR-006. Log `timeout_risk: true`. **Dependency**: Depends on T004, T013d. (FR-002, SC-003, FR-007).
- [ ] T015 [US1] Implement `src/data/ingest_pipeline.py` to orchestrate download, preprocessing, and LLM inference in batches. **Validation**: Ensure output file `data/processed/predictions.csv` strictly conforms to the `PredictionResult` schema. **Memory Safety**: Implement dynamic batch size adjustment based on T013d's memory monitoring. **Logic**: This task orchestrates the execution of T011, T012, and T013 in sequence. **Dependency**: **Depends on: Implementation of modules T011, T012, T013** (i.e., `src/data/download.py`, `src/data/preprocess.py`, `src/services/llm_inference.py` must exist and be runnable). **Note**: This is an orchestrator task, not a data producer.
- [X] T017 [US1] Implement `tests/unit/test_llm_inference.py` to verify batch processing and memory footprint on a mock dataset.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Structural, Semantic & Embedding Feature Extraction (Priority: P2)

**Goal**: Extract structural (AST), semantic (taint API), and embedding features for every code snippet.

**Independent Test**: Run parser on a single file with known complexity and verify JSON output contains non-null numeric values for AST depth, complexity, and embedding score.

### Implementation for User Story 2

- [ ] T018a [US2] Implement `src/data/feature_extractor.py` using `tree-sitter` to compute structural metrics (AST depth, node count, cyclomatic complexity).
- [ ] T018b [US2] Implement `src/data/feature_extractor.py` to compute **semantic metrics**: 1. **Taint Source Count**: Count the frequency of known taint-source APIs. 2. **Sanitization Presence**: Detect the **boolean presence** (true/false) of known sanitization functions (e.g., `htmlspecialchars`, `mysql_real_escape_string`) using AST pattern matching or regex. **Output**: Populate `taint_api_count` (int) and `sanitization_present` (bool) in the `FeatureVector`. (FR-004).
- [ ] T019a [US2] Implement `src/data/vulnerability_pattern_pipeline.py` (Part 1: Download). **Steps**: 1. **Download**: Fetch the **BigVul CVE Corpus** (fixed, versioned snapshot) from the **exact URL specified in `research.md`** (validated by T005) to `data/raw/cve_corpus.json.gz`. **Constraint**: Do NOT use dynamic API queries with keywords. The reference set must be fixed and deterministic. 2. **Verify**: Compute and verify the checksum of the downloaded file against the expected hash. **Dependency**: Depends on T005.
- [ ] T019b [US2] Implement `src/data/vulnerability_pattern_pipeline.py` (Part 2: Process & Embed). **Steps**: 1. **Filter**: Filter the downloaded corpus for vulnerability-related keywords (e.g., "injection", "overflow", "RCE", "XSS") using a **case-insensitive regex** to create `data/canonical_patterns.json`. 2. **Independence Check**: Verify that the filtered corpus is distinct from the training data (BigVul/VulDeePecker) to ensure independence as required by FR-004. 3. **Embed**: Initialize the pre-trained code encoder `sentence-transformers/all-MiniLM-L6-v2`, load `data/canonical_patterns.json`, and compute embedding vectors for these patterns. **Dependency**: Depends on T019a.
- [ ] T019c [US2] Implement `src/data/vulnerability_pattern_pipeline.py` (Part 3: Compute Similarity). **Steps**: 1. **Compute**: Compute `embedding_similarity_score` for every snippet against these patterns. **Deliverable**: Logic to compute similarity scores. **Dependency**: Depends on T019b.
- [ ] T021 [US2] Add error handling in `feature_extractor.py` to log malformed code snippets as null/invalid and continue processing remaining batches.
- [ ] T022 [US2] Implement `src/data/feature_pipeline.py` to run extraction on the full dataset and save `data/processed/features.csv`. **EXPLICIT REQUIREMENT**: The output CSV MUST include the `language` column to support regression analysis in T030. **Dependency**: **Depends on: T018a, T018b, T019c, T012, T008c**.
- [ ] T023 [US2] Implement `tests/unit/test_feature_extractor.py` to verify metric calculation on known test cases (e.g., deeply nested function).

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

---

## Phase 4: User Story 4 - Static Analyzer Baseline Comparison (Priority: P2)

**Goal**: Execute static analysis tools (Bandit, cppcheck) on the dataset to establish a baseline for comparison.

**Independent Test**: Run Bandit on a known vulnerable Python script and verify it flags the vulnerability and outputs a structured result file.

### Implementation for User Story 4

- [ ] T024 [US4] Implement `src/models/static_analyzer.py` to wrap `bandit` (flags: `-r -ll -ii`) for Python snippets and `cppcheck` (flags: `--enable=all --inconclusive --error-exitcode=1`) for C snippets.
- [ ] T025 [US4] Add logic to parse static analyzer output into `PredictionResult` schema (snippet_id, predicted_label, is_correct).
- [ ] T026 [US4] Implement `src/data/static_analysis_pipeline.py` to run analyzers on the full dataset and save `data/processed/static_predictions.csv`.
- [ ] T027 [US4] Implement `tests/unit/test_static_analyzer.py` to verify correct flagging of known vulnerabilities in Python and C.

**Checkpoint**: At this point, User Story 4 should be fully functional and testable independently

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Compute metrics, correlations, regression, and McNemar's test to derive scientific findings.

**Independent Test**: Provide a synthetic CSV of features and labels; verify script outputs correlation matrix, regression summary, and McNemar's test statistic.

### Implementation for User Story 3

- [ ] T028 [US3] Implement `src/analysis/metrics.py` to calculate Precision, Recall, F1, and ROC-AUC per category and model.
- [ ] T029 [US3] Implement correlation analysis in `src/analysis/regression.py` to compute **Pearson correlation coefficient** (r) between each feature and the per-sample binary `is_correct` outcome, applying **Bonferroni** correction (mandatory per FR-005) to the family of tests for each category. **Output Requirement**: The output file MUST explicitly distinguish the correction method used (Bonferroni) and report the **adjusted p-value** for **every** test in the family. Non-significant adjusted p-values MUST be labeled as 'not significant' in the output. Depends on: T015 (predictions.csv), T022 (features.csv), T009e.
- [ ] T030 [US3] Implement **Binary Logistic Regression** (GLM) fitting in `src/analysis/regression.py` using `statsmodels` to predict per-sample binary `is_correct` from features, **including 'language' as a categorical predictor** to control for confounding, as required by FR-006. **Implementation Detail**: Perform **one-hot encoding** (or dummy variables) for the 'language' column before fitting. **Deliverable**: `data/results/regression_summary.json` MUST contain coefficients for the 'language' variable and report **McFadden's Pseudo R²** with the key `adjusted_r2` (explicitly mapping McFadden's to the spec's 'adjusted R²' requirement). **Traceability**: Log a note that McFadden's Pseudo R² is the standard GLM equivalent of adjusted R², satisfying SC-002. **Schema**: Output JSON keys: `coefficients`, `p_values`, `adjusted_r2` (McFadden), `n_samples`, `log_likelihood`. Depends on: T015 (predictions.csv), T022 (features.csv).
- [ ] T030b [US3] Implement `src/analysis/report_generator.py` to document in `research.md` why McFadden's Pseudo R² is the appropriate metric for SC-002 (Logistic Regression) and how it relates to the concept of "Adjusted R²" in linear models.
- [ ] T031 [US3] Implement McNemar's test in `src/analysis/regression.py` using `statsmodels.stats.contingency.mcnemar` (exact binomial method) to compare LLM vs. Static Analyzer predictions on the same samples. **Dependency**: **Depends on: T015 (predictions.csv), T026 (static_predictions.csv)**.
- [ ] T032 [US3] Implement `src/analysis/visualizer.py` to generate plots for feature correlations and ROC curves.
- [ ] T033 [US3] Implement `src/analysis/report_generator.py` to aggregate all metrics into `data/results/metrics.json`.
- [ ] T034 [US3] Implement `tests/unit/test_regression.py` to verify statistical outputs on synthetic data.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase 6: Human Verification & Sensitivity Analysis (Priority: P3 - FR-011)

**Goal**: Validate the impact of ground-truth label noise on metrics using a real human-verified subset or system-generated re-labeling.

**Implementation**

- [ ] T035 [P] Implement `src/analysis/sensitivity.py` to select a random subset of n=100 samples and export them to `data/human_review/export.csv` for manual review.
- [ ] T036 [P] Implement `src/analysis/sensitivity.py` to ingest `data/human_review/verified_labels.csv` (produced by the external human review step). **Logic**: Check for the existence of `verified_labels.csv`. **If missing**: Trigger T036b to handle the missing data by executing a deterministic noise injection protocol. **If present**: Validate the structure (snippet_id, verified_label) and proceed. **Constraint**: Do NOT fail the pipeline if the file is missing; this enforces the non-blocking nature of the sensitivity analysis. (FR-011). **Dependency**: Depends on T035.
- [ ] T036b [P] **Automated Sensitivity Analysis Protocol**: Implement logic in `sensitivity.py` to **handle missing human review**. **Logic**: If `data/human_review/verified_labels.csv` is missing, the system MUST **NOT** generate synthetic labels. Instead, it MUST **inject deterministic noise** (flip [deferred] of labels randomly with seed=42) into a copy of the original labels to simulate noise, then re-calculate metrics. This satisfies the "MUST perform sensitivity analysis" requirement of FR-011 when external human review is unavailable. **Output**: Log "Sensitivity Analysis: Synthetic Noise Fallback (10% flip, seed 42)". (FR-011). **Dependency**: Depends on T036. **Constraint**: [P] tag removed; must wait for T036 to complete its check.
- [ ] T035c [P] **Automated Sensitivity Analysis**: Implement logic in `sensitivity.py` to **re-calculate** metrics (Precision, Recall, F1) using the human-verified labels (if available) or the noise-injected labels (from T036b) and compare them against the original metrics to quantify the impact of label noise. **Dependency**: **Depends on: T036, T036b**.
- [ ] T037 [P] Output `data/results/sensitivity_analysis.json` with adjusted metrics and the noise impact comparison based on the verified subset or noise-injected subset.

**Checkpoint**: Sensitivity analysis complete

---

## Phase 7: Versioning & Reporting (Priority: P3)

**Goal**: Finalize artifacts and update state.

**Implementation**

- [ ] T038 [P] Run `src/utils/hash_artifacts.py` to checksum all outputs in `data/processed/` and `data/results/`.
- [ ] T039 [P] Update `state/projects/PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml` with new hashes and completion status.
- [ ] T040 [P] Generate final research report summarizing findings in `research.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **User Stories (Phase 2-6)**: All depend on Foundational phase completion
 - **Data Flow Constraint**: Phase 2 (Inference), Phase 3 (Feature Extraction), and Phase 4 (Static Analysis) can run in parallel but **MUST** complete before Phase 5 (Analysis).
 - **Analysis Constraint**: Phase 5 (Analysis) cannot run until `data/processed/predictions.csv`, `data/processed/features.csv`, and `data/processed/static_predictions.csv` exist.
 - **Human Review Constraint**: T036 checks for the existence of `data/human_review/verified_labels.csv` (external process) but does not block the pipeline if missing (triggers T036b).
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Core pipeline. Depends on Foundational.
- **User Story 2 (P2)**: Feature extraction. Depends on Foundational. Can run parallel to US1.
- **User Story 4 (P2)**: Static analysis. Depends on Foundational. Can run parallel to US1/US2.
- **User Story 3 (P3)**: Statistical analysis. **Depends on US1, US2, and US4 completion** (requires predictions and features).
- **Sensitivity (Phase 6)**: Depends on US1 completion (requires predictions) and external human review (non-blocking).

### Within Each User Story

- Models/Classes before Logic
- Logic before Pipelines
- Pipelines before Tests

### Parallel Opportunities

- **Setup**: T001, T003, T004 can run in parallel. T007a, T008a, T009a, T009c can run in parallel.
- **Data Processing**: T011 (Download), T018 (Feature Extract), T024 (Static Analyzer) can run in parallel once data is available.
 - **Note**: T019 (Vulnerability Pattern Pipeline) is split into T019a, T019b, T019c (Download -> Filter -> Embed).
- **Analysis**: T028 (Metrics), T029 (Correlation), T031 (McNemar) can be implemented in parallel, though execution order is fixed.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: User Story 1 (Ingestion + Inference)
3. **STOP and VALIDATE**: Verify predictions match ground truth for a small batch.

### Incremental Delivery

1. Complete Setup → Foundation ready
2. Add User Story 1 → Test independently → MVP: Raw predictions generated
3. Add User Story 2 + User Story 4 → Test independently → Features and Baselines generated
4. Add User Story 3 → Test independently → Statistical findings generated
5. Add Sensitivity Analysis → Test independently → Robustness validated (or skipped if human review unavailable)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together.
2. Once Setup is done:
 - Developer A: User Story 1 (LLM Inference)
 - Developer B: User Story 2 (Feature Extraction)
 - Developer C: User Story 4 (Static Analysis)
3. Once all data pipelines are ready:
 - Developer D (or A/B/C): User Story 3 (Statistical Analysis)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability to specific user stories
- **Memory Constraint**: All LLM tasks must use low-bit quantization and dynamic batch sizing to stay under constrained memory limits.
- **Time Constraint**: The entire pipeline must complete within 6 hours; optimize batch sizes and parallelization where possible.
- **Data Integrity**: Never synthesize fake data; always use the real VulDeePecker/BigVul datasets.
- **Verification**: Ensure tests fail before implementing.
- **Commit**: Commit after each task or logical group.
- **Stop**: Stop at any checkpoint to validate story independently.
- **Spec Precedence**: Where the Plan conflicts with the Spec (e.g., "Quantization-aware training" vs "Zero-Shot"), the Spec takes precedence per Constitution Principle II.