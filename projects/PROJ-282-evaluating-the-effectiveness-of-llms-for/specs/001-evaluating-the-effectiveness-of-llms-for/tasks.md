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
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (transformers, scikit-learn, pandas, tree-sitter, networkx, requests, pyyaml, bitsandbytes, sentence-transformers, pytest, radon, statsmodels)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Initialize `src/utils/config.py` with seeds, paths, runtime thresholds (hourly limit, gigabyte RAM cap), and the list of candidate LLMs. (FR-002, SC-005).
- [ ] T004a Implement `src/utils/model_selector.py` to implement a deterministic model selection strategy based on the candidate list in T004. **Logic**: The selection must be deterministic (e.g., based on a fixed seed or a static configuration) and logged. **Constraint**: Do NOT use runtime RAM checks for selection to ensure reproducibility (Constitution I). The selected model must be compatible with all languages in the stratified sample. (FR-002, Constitution I).
- [ ] T005 [P] Implement `src/utils/validate_urls.py` to validate dataset URLs against `research.md` manifest (Constitution II)
- [ ] T006 [P] Implement `src/utils/logger.py` with structured logging for pipeline stages
- [ ] T007 [P] Create base `CodeSnippet` dataclass in `src/models/code_snippet.py` with `id`, `language`, `source_code`, `ground_truth_label`, `ground_truth_category`
- [ ] T008 [P] Create base `FeatureVector` dataclass in `src/models/feature_vector.py` with `ast_depth`, `cyclomatic_complexity`, `node_count`, `taint_api_count`, `sanitization_present`, `embedding_similarity_score`, `language`
- [ ] T009 [P] Create base `PredictionResult` dataclass in `src/models/prediction_result.py` with `snippet_id`, `predicted_label`, `predicted_category`, `is_correct`, `inference_time_ms`
- [ ] T010 [P] Implement `src/utils/hash_artifacts.py` for checksum generation and state file updates (Constitution V)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Zero-Shot Vulnerability Detection Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest dataset, run zero-shot LLM inference, and generate correctness flags against ground truth.

**Independent Test**: Process a small, fixed subset of known vulnerable and known safe snippets, verifying structured JSON output with predicted label, confidence, and `is_correct` flag.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `src/data/download.py` to fetch VulDeePecker and Juliet datasets via `wget`/`git clone` to `data/raw/` with checksum verification. **CRITICAL**: Ensure the script fails loudly if the real fetch fails; do NOT implement a fallback to synthetic/mock data.
- [ ] T012 [US1] Implement `src/data/preprocess.py` to parse raw datasets, extract code snippets, and map to `CodeSnippet` entity; **EXPLICITLY EXTRACT AND PRESERVE** the `language` field for every sample; exclude samples with missing labels. (FR-001).
- [ ] T013 [US1] Implement `src/services/llm_inference.py` for **Zero-Shot LLM Inference**. **CRITICAL**: This task MUST enforce **Zero-Shot** methodology as per Spec FR-002. Load the selected model (from T004a) in 4-bit quantized mode on CPU. **Memory Safety**: Implement a `MemoryMonitor` class in `src/utils/memory_monitor.py` to track runtime memory usage; if RAM usage approaches a high threshold, dynamically reduce batch size (default small) or pause to satisfy the GB RAM constraint. **Stratified Compatibility**: Verify the selected model is valid for ALL languages in the current stratified batch before inference. **Prompt**: Use the prompt template: "Identify any security vulnerability in the following code: {code}." **Parsing Logic**: Implement regex-based parsing to map the LLM's free-text response to the required `PredictionResult` schema: map "SQLi", "sql injection" to "SQLi"; "buffer overflow", "overflow" to "Buffer Overflow"; "none", "no vulnerability" to "none"; and "maybe", "unclear", "possibly", "likely", "unknown error", or any non-matching response to "uncertain". (FR-002, SC-003). **Deliverable**: `src/services/llm_inference.py` and `src/utils/memory_monitor.py`.
- [ ] T014 [US1] Add logic to `llm_inference.py` to handle context window truncation (log `truncation_event`) and map ambiguous responses ("maybe", "unclear", "possibly", "likely", "unknown error") to "uncertain" or negative using regex matching.
- [ ] T016 [US1] Add timing logic to `llm_inference.py` to log per-sample inference time and ensure total runtime < 6 hours (FR-007); implement circuit breaker logic: if runtime exceeds 90% of 6 hours, reduce batch size and optimize, but **DO NOT ABORT** the pipeline. (FR-007).
- [ ] T015 [US1] Implement `src/data/ingest_pipeline.py` to orchestrate download, preprocessing, and LLM inference in batches. **Validation**: Ensure output file `data/processed/predictions.csv` strictly conforms to the `PredictionResult` schema. **Memory Safety**: Implement dynamic batch size adjustment based on T013's memory monitoring. **Dependency**: Calls T013 functions (semantic dependency, not data-flow). **Explicit Dependency**: Depends on: T011, T012, T013, T014, T016.
- [ ] T017 [US1] Implement `tests/unit/test_llm_inference.py` to verify batch processing and memory footprint on a mock dataset.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Structural, Semantic & Embedding Feature Extraction (Priority: P2)

**Goal**: Extract structural (AST), semantic (taint API), and embedding features for every code snippet.

**Independent Test**: Run parser on a single file with known complexity and verify JSON output contains non-null numeric values for AST depth, complexity, and embedding score.

### Implementation for User Story 2

- [ ] T018 [US2] Implement `src/data/feature_extractor.py` using `tree-sitter` to compute structural metrics (AST depth, node count, cyclomatic complexity).
- [ ] T019 [US2] Implement semantic metric extraction in `feature_extractor.py` to count taint-source APIs and detect sanitization functions (record 0 if none found).
- [ ] T019a [US2] Implement `src/data/corpus_validator.py` to validate the vulnerability pattern corpus source against `research.md`. **CRITICAL**: If `research.md` does not contain a verified entry for the vulnerability pattern corpus, the script MUST fail with exit code 1 and a clear error message. **Constraint**: This task ensures FR-004 and Constitution Principle II are met before any download occurs.
- [ ] T019a1 [US2] Implement `src/data/corpus_downloader.py` to download the **verified vulnerability pattern corpus** from the **exact** URL: ` with SHA256 checksum `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (placeholder, replace with actual). **CRITICAL**: Use the exact URL and checksum; do not use placeholders or 'e.g.'. Save to `data/raw/nvd_patterns.json.gz`. (FR-004).
- [ ] T019a2 [US2] Implement `src/data/corpus_filter.py` to filter the downloaded NVD JSON for vulnerability-related keywords (e.g., "injection", "overflow", "vulnerability") and transform it into `data/canonical_patterns.json`. (FR-004).
- [ ] T019b [US2] Implement `src/data/embedding_loader.py` to initialize the pre-trained code encoder `sentence-transformers/all-MiniLM-L6-v2` and load canonical vulnerable patterns from `data/canonical_patterns.json` (produced by T019a2). **Deliverable**: A loaded encoder object and a list of pattern vectors. **Dependency**: **Depends on: T019a2**.
- [ ] T020 [US2] Implement embedding similarity calculation in `feature_extractor.py` using the encoder initialized in T019b to compare snippets against the loaded canonical patterns and compute the `embedding_similarity_score` vector. **Dependency**: **Depends on: T019b** and patterns from T019a2.
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
- [ ] T029 [US3] Implement correlation analysis in `src/analysis/regression.py` to compute **Pearson correlation coefficient** (r) between each feature and the per-sample binary `is_correct` outcome, applying **Benjamini-Hochberg (preferred) or Bonferroni** correction to the family of tests for each category as required by FR-005 and SC-004. Depends on: T015 (predictions.csv), T022 (features.csv).
- [ ] T030 [US3] Implement **Binary Logistic Regression** (GLM) fitting in `src/analysis/regression.py` using `statsmodels` to predict per-sample binary `is_correct` from features, **including 'language' as a categorical predictor** to control for confounding, as required by FR-006. **Deliverable**: `data/results/regression_summary.json` MUST contain coefficients for the 'language' variable and report the Pseudo R² (e.g., McFadden's) and coefficient significance. Depends on: T015 (predictions.csv), T022 (features.csv).
- [ ] T031 [US3] Implement McNemar's test in `src/analysis/regression.py` using `statsmodels.stats.contingency.mcnemar` (exact binomial method) to compare LLM vs. Static Analyzer predictions on the same samples. Depends on: T015 (predictions.csv), T026 (static_predictions.csv).
- [ ] T032 [US3] Implement `src/analysis/visualizer.py` to generate plots for feature correlations and ROC curves.
- [ ] T033 [US3] Implement `src/analysis/report_generator.py` to aggregate all metrics into `data/results/metrics.json`.
- [ ] T034 [US3] Implement `tests/unit/test_regression.py` to verify statistical outputs on synthetic data.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase 6: Human Verification & Sensitivity Analysis (Priority: P3 - FR-011)

**Goal**: Validate the impact of ground-truth label noise on metrics using a real human-verified subset.

**Implementation**

- [ ] T035 [P] Implement `src/analysis/sensitivity.py` to select a random subset of n=100 samples and export them to `data/human_review/export.csv` for manual review.
- [ ] T035b [P] **External Human Review Step**: This step requires manual human intervention to annotate labels in `data/human_review/verified_labels.csv` (snippet_id, verified_label). **CRITICAL**: Implement a schema validation script in `src/analysis/sensitivity.py` to validate the structure of `verified_labels.csv` upon arrival. **Logic**: If `verified_labels.csv` is missing, the script MUST check for a secondary verified dataset (as hinted in FR-011). If the secondary dataset is also missing, the pipeline MUST fail with a clear error (exit 1) and **MUST NOT proceed with a placeholder**. This ensures FR-011 is mandatory. (FR-011).
- [ ] T036 [P] Implement `src/analysis/sensitivity.py` to ingest `data/human_review/verified_labels.csv` (produced by the external human review step). **Dependency**: **Depends on: T035b**. **Assumption**: This task assumes T035b has already validated the file or failed if not available.
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
 - **Human Review Constraint**: T036 checks for the existence of `data/human_review/verified_labels.csv` (external process) but does not block the pipeline if missing.
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

- **Setup**: T001, T003, T004 can run in parallel.
- **Data Processing**: T011 (Download), T018 (Feature Extract), T024 (Static Analyzer) can run in parallel once data is available.
 - **Note**: T019a, T019a1, T019a2, T019b, and T020 are **sequential** (T019a -> T019a1 -> T019a2 -> T019b -> T020) due to artifact dependencies and cannot be parallelized with each other.
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
- **Data Integrity**: Never synthesize fake data; always use the real VulDeePecker/Juliet datasets.
- **Verification**: Ensure tests fail before implementing.
- **Commit**: Commit after each task or logical group.
- **Stop**: Stop at any checkpoint to validate story independently.
- **Spec Precedence**: Where the Plan conflicts with the Spec (e.g., "Quantization-aware training" vs "Zero-Shot"), the Spec takes precedence per Constitution Principle II.