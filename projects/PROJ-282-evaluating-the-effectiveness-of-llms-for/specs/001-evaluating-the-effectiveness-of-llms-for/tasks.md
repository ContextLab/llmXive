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
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (transformers, scikit-learn, pandas, tree-sitter, networkx, requests, pyyaml, bitsandbytes, sentence-transformers, pytest, radon, statsmodels)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Implement `src/utils/config.py` with seeds, paths, runtime thresholds (hourly limit, gigabyte RAM cap), and the list of candidate LLMs. (FR-002, SC-005).
- [ ] T004a [P] Implement `src/utils/model_selector.py` to implement a deterministic model selection strategy based on the candidate list in T004. **Logic**: The selection must be deterministic (e.g., based on a fixed seed or a static configuration) and logged. **Constraint**: Do NOT use runtime RAM checks for selection to ensure reproducibility (Constitution I). The selected model must be compatible with all languages in the stratified sample. (FR-002, Constitution I). **Dependency**: Depends on: T004.
- [ ] T005 [P] Implement `src/utils/validate_urls.py` to validate dataset URLs against `research.md` manifest (Constitution II). **Constraint**: This task MUST complete before T011 starts.
- [ ] T006 [P] Implement `src/utils/logger.py` with structured logging for pipeline stages
- [ ] T007a [P] Create `contracts/dataset.schema.yaml` defining the `CodeSnippet` schema (id, language, source_code, ground_truth_label, ground_truth_category). **Content**: Must include type definitions for all fields.
- [ ] T007b [P] Generate base `CodeSnippet` dataclass in `src/models/code_snippet.py` FROM `contracts/dataset.schema.yaml` using `pydantic` or a code generator. **Constraint**: Do NOT manually implement fields; ensure schema drift is prevented by generating from the contract. (Constitution IV, Plan Project Structure). **Dependency**: Depends on: T007a.
- [ ] T008a [P] Create `contracts/feature.schema.yaml` defining the `FeatureVector` schema (ast_depth, cyclomatic_complexity, node_count, taint_api_count, sanitization_present, embedding_similarity_score). **Content**: Must include type definitions for all fields.
- [ ] T008b [P] Generate base `FeatureVector` dataclass in `src/models/feature_vector.py` FROM `contracts/feature.schema.yaml` using `pydantic` or a code generator. **Constraint**: Do NOT manually implement fields; ensure schema drift is prevented by generating from the contract. (Constitution IV, Plan Project Structure). **Dependency**: Depends on: T008a.
- [ ] T009a [P] Create `contracts/prediction.schema.yaml` defining the `PredictionResult` schema (snippet_id, predicted_label, predicted_category, is_correct, inference_time_ms). **Content**: Must include type definitions for all fields.
- [ ] T009b [P] Generate base `PredictionResult` dataclass in `src/models/prediction_result.py` FROM `contracts/prediction.schema.yaml` using `pydantic` or a code generator. **Constraint**: Do NOT manually implement fields; ensure schema drift is prevented by generating from the contract. (Constitution IV, Plan Project Structure). **Dependency**: Depends on: T009a.
- [ ] T010 [P] Implement `src/utils/hash_artifacts.py` for checksum generation and state file updates (Constitution V)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Zero-Shot Vulnerability Detection Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest dataset, run zero-shot LLM inference, and generate correctness flags against ground truth.

**Independent Test**: Process a small, fixed subset of known vulnerable and known safe snippets, verifying structured JSON output with predicted label, confidence, and `is_correct` flag.

### Implementation for User Story 1

- [ ] T011a [US1] Implement `src/data/download.py` **NIST Juliet Fetch**. **CRITICAL**: Attempt to fetch the **official NIST Juliet repository** for C/C++ first. **Logic**: If the fetch fails (network error or 404), **log a formal "Scope Deviation" event** (including timestamp and error details) to `data/logs/scope_deviation.log` and **automatically switch** to the BigVul dataset for C-code analysis, documenting this substitution in the output log. **Constraint**: Ensure the script fails loudly if the real fetch fails for *all* sources; do NOT implement a fallback to synthetic/mock data. **Dependency**: **Depends on: T005** (URL validation must occur before fetch). (FR-001).
- [ ] T011 [US1] Implement `src/data/download.py` to fetch **VulDeePecker** (Python) and **BigVul** (C and JavaScript) datasets. **CRITICAL**: Read URLs from `research.md` (validated by T005). **Constraint**: If `research.md` is missing or URLs are invalid, fail with a clear error message. **Dependency**: **Depends on: T011a** (NIST Juliet attempt must complete first). (FR-001, FR-002).
- [ ] T012 [US1] Implement `src/data/preprocess.py` to parse raw datasets, extract code snippets, and map to `CodeSnippet` entity; **EXPLICITLY EXTRACT AND PRESERVE** the `language` field for every sample. **Edge Case Handling**: Exclude samples with missing labels from accuracy calculations BUT **INCLUDE THEM IN THE MAIN FEATURE EXTRACTION LOG** (`data/processed/features.log`) with null/invalid feature values to satisfy edge case handling requirements. (FR-001).
- [ ] T013a [US1] Implement `src/services/llm_inference.py` **Model Loading**. **CRITICAL**: Load the selected model (from T004a) in low-bit quantized mode on CPU. **Dependency**: Uses config from T004. (FR-002).
- [ ] T013b [US1] Implement `src/services/llm_inference.py` **Inference Loop**. **CRITICAL**: This task MUST enforce **Zero-Shot** methodology as per Spec FR-002. **Memory Safety**: Use the `MemoryMonitor` from T013d to track usage. **Stratified Compatibility**: Verify the selected model is valid for ALL languages in the current stratified batch before inference. **Prompt**: Use the prompt template: "Identify any security vulnerability in the following code: {code}." **Dependency**: Depends on T013a, T013d. (FR-002, SC-003).
- [ ] T013c [US1] Implement `src/services/llm_inference.py` **Response Parsing**. **Logic**: Implement regex-based parsing to map the LLM's free-text response to the required `PredictionResult` schema: map "SQLi", "sql injection" to "SQLi"; "buffer overflow", "overflow" to "Buffer Overflow"; "none", "no vulnerability" to "none"; and "maybe", "unclear", "possibly", "likely", "unknown error", or any non-matching response to "uncertain". (FR-002, SC-003).
- [ ] T013d [US1] Implement `src/utils/memory_monitor.py` to track runtime memory usage. **Logic**: Expose a context manager or utility function to check RAM usage and trigger batch size reduction if a high threshold is approached. (FR-002, SC-005).
- [ ] T014 [US1] Add logic to `llm_inference.py` to handle context window truncation (log `truncation_event`) and map ambiguous responses ("maybe", "unclear", "possibly", "likely", "unknown error") to "uncertain" or negative using regex matching.
- [ ] T016 [US1] Add timing logic to `llm_inference.py` to log per-sample inference time and ensure total runtime < 6 hours (FR-007); implement circuit breaker logic: if runtime exceeds 90% of 6 hours, **REDUCE BATCH SIZE TO 1** and **LOG `timeout_risk: true`** explicitly to the runtime log, as mandated by the Plan's Runtime Safety Mechanisms. **CRITICAL CONSTRAINT**: Do NOT skip features or switch models. The system MUST compute **ALL** required features (FR-004) for **EVERY** snippet, even if it requires processing samples one-by-one. Do NOT abort the pipeline; ensure partial data is preserved. (FR-007, FR-004).
- [ ] T015 [US1] Implement `src/data/ingest_pipeline.py` to orchestrate download, preprocessing, and LLM inference in batches. **Validation**: Ensure output file `data/processed/predictions.csv` strictly conforms to the `PredictionResult` schema. **Memory Safety**: Implement dynamic batch size adjustment based on T013d's memory monitoring. **Dependency**: **Depends on: Completion of the llm_inference module (T013a, T013b, T013c, T013d, T014, T016)**.
- [ ] T017 [US1] Implement `tests/unit/test_llm_inference.py` to verify batch processing and memory footprint on a mock dataset.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Structural, Semantic & Embedding Feature Extraction (Priority: P2)

**Goal**: Extract structural (AST), semantic (taint API), and embedding features for every code snippet.

**Independent Test**: Run parser on a single file with known complexity and verify JSON output contains non-null numeric values for AST depth, complexity, and embedding score.

### Implementation for User Story 2

- [ ] T018 [US2] Implement `src/data/feature_extractor.py` using `tree-sitter` to compute structural metrics (AST depth, node count, cyclomatic complexity).
- [ ] T019 [US2] Implement `src/data/vulnerability_pattern_pipeline.py` to handle the full vulnerability pattern feature extraction pipeline. **Steps**: 1. **Download**: Fetch the **verified vulnerability pattern corpus** from the **exact URL specified in `research.md`** (validated by T005) to `data/raw/nvd_patterns.json.gz`. **Constraint**: Do NOT hardcode URLs; use the verified source. 2. **Filter**: Filter the downloaded NVD JSON for vulnerability-related keywords (e.g., "injection", "overflow", "vulnerability") and transform it into `data/canonical_patterns.json`. 3. **Embed**: Initialize the pre-trained code encoder `sentence-transformers/all-MiniLM-L6-v2`, load `data/canonical_patterns.json`, and compute embedding vectors for these patterns. 4. **Compute**: Compute `embedding_similarity_score` for every snippet against these patterns. **Deliverable**: `data/canonical_patterns.json` and the logic to compute similarity scores. **Dependency**: Depends on T005.
- [ ] T020 [US2] Implement embedding similarity calculation in `feature_extractor.py` using the encoder initialized in T019 to compare snippets against the loaded canonical patterns and compute the `embedding_similarity_score` vector. **Dependency**: **Depends on: T019**.
- [ ] T021 [US2] Add error handling in `feature_extractor.py` to log malformed code snippets as null/invalid and continue processing remaining batches.
- [ ] T022 [US2] Implement `src/data/feature_pipeline.py` to run extraction on the full dataset and save `data/processed/features.csv`. **EXPLICIT REQUIREMENT**: The output CSV MUST include the `language` column to support regression analysis in T030. **Dependency**: **Depends on: T020**.
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
- [ ] T029 [US3] Implement correlation analysis in `src/analysis/regression.py` to compute **Pearson correlation coefficient** (r) between each feature and the per-sample binary `is_correct` outcome, applying **Benjamini-Hochberg (preferred) or Bonferroni** correction to the family of tests for each category as required by FR-005 and SC-004. **Output Requirement**: The output file MUST explicitly distinguish which correction method was used. Depends on: T015 (predictions.csv), T022 (features.csv).
- [ ] T030 [US3] Implement **Binary Logistic Regression** (GLM) fitting in `src/analysis/regression.py` using `statsmodels` to predict per-sample binary `is_correct` from features, **including 'language' as a categorical predictor** to control for confounding, as required by FR-006. **Deliverable**: `data/results/regression_summary.json` MUST contain coefficients for the 'language' variable and report **McFadden's Pseudo R²** explicitly labeled as **"adjusted R² (McFadden proxy)"** to satisfy SC-002. **Mapping Note**: The output must explicitly state "McFadden's Pseudo R² reported as adjusted R² proxy per SC-002". Depends on: T015 (predictions.csv), T022 (features.csv).
- [ ] T031 [US3] Implement McNemar's test in `src/analysis/regression.py` using `statsmodels.stats.contingency.mcnemar` (exact binomial method) to compare LLM vs. Static Analyzer predictions on the same samples. **Dependency**: **Depends on: T015 (predictions.csv), T026 (static_predictions.csv)**.
- [ ] T032 [US3] Implement `src/analysis/visualizer.py` to generate plots for feature correlations and ROC curves.
- [ ] T033 [US3] Implement `src/analysis/report_generator.py` to aggregate all metrics into `data/results/metrics.json`.
- [ ] T034 [US3] Implement `tests/unit/test_regression.py` to verify statistical outputs on synthetic data.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase 6: Human Verification & Sensitivity Analysis (Priority: P3 - FR-011)

**Goal**: Validate the impact of ground-truth label noise on metrics using a real human-verified subset.

**Implementation**

- [ ] T035 [P] Implement `src/analysis/sensitivity.py` to select a random subset of n=100 samples and export them to `data/human_review/export.csv` for manual review.
- [ ] T036 [P] Implement `src/analysis/sensitivity.py` to ingest `data/human_review/verified_labels.csv` (produced by the external human review step). **Logic**: Check for the existence of `verified_labels.csv`. **If missing**: Log a "Sensitivity Analysis Skipped" status with a clear warning, **generate a placeholder JSON** (`data/results/sensitivity_analysis.json` with `status: "skipped"`), and **proceed without crashing**. **If present**: Validate the structure (snippet_id, verified_label) and proceed. **Constraint**: Do NOT fail the pipeline if the file is missing; this enforces the non-blocking nature of the sensitivity analysis. (FR-011).
- [ ] T036b [P] **Automated Sensitivity Analysis**: Implement logic in `sensitivity.py` to **re-calculate** metrics (Precision, Recall, F1) using the human-verified labels from T036 and compare them against the original metrics to quantify the impact of label noise. **Dependency**: **Depends on: T036**.
- [ ] T037 [P] Output `data/results/sensitivity_analysis.json` with adjusted metrics and the noise impact comparison based on the verified subset.

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
 - **Human Review Constraint**: T036 checks for the existence of `data/human_review/verified_labels.csv` (external process) but does not block the pipeline if missing (logs skip).
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

- **Setup**: T001, T003, T004 can run in parallel. T007a, T008a, T009a can run in parallel.
- **Data Processing**: T011 (Download), T018 (Feature Extract), T024 (Static Analyzer) can run in parallel once data is available.
 - **Note**: T019 (Vulnerability Pattern Pipeline) is a single atomic task containing sequential steps (Download -> Filter -> Embed).
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