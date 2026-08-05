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
- [X] T004 [P] Implement `src/utils/config.py` with seeds, paths, runtime thresholds (hourly limit, gigabyte RAM cap), and the list of candidate LLMs. (FR-002, SC-005)
- [X] T004c [P] **Model Capability Verification**: Verify that candidate models can process C, Python, and JavaScript snippets. **Test Input**: Run inference on the specific string `int x = 0;` (C), `x = 1` (Python), and `var y = 1;` (JS) using the candidate model's tokenizer. **Constraint**: If any language-specific tokenizer fails or returns an error, abort and log to `data/logs/model_capability_check.json`. (Dependency: T004)
- [X] T004a [P] **Deterministic Model Selection**: Select the model for the pipeline. **Logic**: Select the first model in the candidate list (from T004) that passes the capability check in T004c. **Constraint**: Selection must be deterministic and logged. **Verification**: Log the selected model to `data/logs/model_selection.json`. (Dependency: T004, T004c)
- [X] T004b [P] **CPU‑Only Enforcement**: Before any inference runs, check `torch.cuda.is_available()`. If a GPU is detected, abort execution and write a clear error to `data/logs/cpu_check.json`. This guarantees CPU‑only execution as required by FR‑002 and Constitution Principle VI. **Note**: This task runs in parallel with T004c, both depending on T004.
- [X] T005 [P] Implement `src/utils/validate_urls.py` to validate dataset URLs against `research.md` manifest (Constitution II). **Constraint**: This task MUST complete before T011 starts.
- [X] T006 [P] Implement `src/utils/logger.py` with structured logging for pipeline stages
- [X] T007a [P] Create `contracts/dataset.schema.yaml` defining the `CodeSnippet` schema. **Priority**: P1.
- [X] T007b [P] **Generate & Verify CodeSnippet Dataclass**: Write a generation script that reads `contracts/dataset.schema.yaml` and creates `src/models/code_snippet.py` using `pydantic`. The script also verifies that the generated fields exactly match the schema and writes a verification log to `data/logs/code_snippet_generation.json`. (Constitution IV, Plan Project Structure)
- [X] T008a [P] Create `contracts/feature.schema.yaml` defining the `FeatureVector` schema. **Priority**: P1.
- [X] T008b [P] **Generate & Verify FeatureVector Dataclass**: Generate `src/models/feature_vector.py` from `contracts/feature.schema.yaml` and verify against the schema, logging to `data/logs/feature_vector_generation.json`.
- [X] T009a [P] Create `contracts/prediction.schema.yaml` defining the `PredictionResult` schema. **Priority**: P1.
- [X] T009b [P] **Generate & Verify PredictionResult Dataclass**: Generate `src/models/prediction_result.py` from `contracts/prediction.schema.yaml` and verify, logging to `data/logs/prediction_result_generation.json`.
- [X] T009d [P] Create `contracts/analysis_metric.schema.yaml` defining the `AnalysisMetric` schema. **Priority**: P1.
- [X] T009e [P] **Generate & Verify AnalysisMetric Dataclass**: Generate `src/models/analysis_metric.py` from `contracts/analysis_metric.schema.yaml` and verify, logging to `data/logs/analysis_metric_generation.json`.
- [X] T010 [P] Implement `src/utils/hash_artifacts.py` for checksum generation and state file updates (Constitution V)
- [X] T013d [P] Implement `src/utils/memory_monitor.py` to track runtime memory usage. **Logic**: Expose a context manager or utility function to check RAM usage and trigger batch size reduction if a high threshold is approached. **Dependency**: T004 -> T004c & T013d (Parallel). (FR-002, SC-005)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Zero‑Shot Vulnerability Detection Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest dataset, run zero‑shot LLM inference, and generate correctness flags against ground truth.

**Independent Test**: Process a small, fixed subset of known vulnerable and known safe snippets, verifying structured JSON output with predicted label, confidence, and `is_correct` flag.

### Implementation for User Story 1

- [ ] T011 [US1] **Dataset Download & Checksum Verification**: **Primary**: Fetch the **official NIST Juliet repository** for C/C++ using `git clone (or the specific HTTP endpoint if git is blocked). **Fallback**: ONLY if the NIST Juliet fetch fails (non-zero exit code or timeout), fetch the **BigVul dataset** (C, C++, JavaScript) using `wget. Compute SHA‑256 checksums and compare against `data/raw/checksums.json`. On mismatch, abort and log to `data/logs/download_errors.json`. Save raw files to `data/raw/`. **Justification**: If NIST Juliet is skipped in favor of BigVul, write a mandatory justification to `data/logs/dataset_substitution_justification.json` citing the specific fetch failure. (FR-001, Plan Complexity Tracking)
- [ ] T011a [US1] **Dataset Substitution Logic**: **Conditional Task**: ONLY execute if T011 failed to fetch NIST Juliet and successfully fetched BigVul. Implement the mapping logic to adapt BigVul C/C++ samples to the NIST Juliet schema requirements (if applicable) and document the justification for the substitution. Write the mapping rules and justification to `data/logs/dataset_substitution_justification.json`. **Dependency**: T011 (Conditional). (FR-001, Plan Complexity Tracking)
- [ ] T012 [US1] **Preprocess & Sampling**: Parse raw datasets into `CodeSnippet` entities. **Mapping**: Explicitly map columns `lang` (or `language`) to `language` and `cwe_id` (or `vulnerability_type`) to `ground_truth_category` as defined in `contracts/dataset.schema.yaml`. Perform stratified sampling (≤5,000 samples) by language and vulnerability category using `sklearn.model_selection.StratifiedShuffleSplit` with `random_state=42`. **Constraint**: Exclude samples missing `ground_truth_label` from accuracy calculation, **BUT** log these dropped samples to `data/logs/dropped_samples.json` with the reason (e.g., 'missing_label') to satisfy Spec Edge Cases. Output `data/processed/raw_snippets.parquet` (cleaned, sampled code) and `data/processed/labels.csv` (snippet_id, ground_truth_label, ground_truth_category). **Dependency**: T011, T012a. (FR-001, US1)
- [ ] T012a [US1] **Stratification Verification**: Verify that the sampling logic in T012 preserves the proportional representation of *both* language and vulnerability category. Compute distribution stats and log to `data/logs/stratification_verification.json`. **Abort** if bias exceeds 5%. **Dependency**: T012. (FR-001, US1)
- [X] T013 [US1] **Zero‑Shot Inference Service**: Load the selected model (from T004a) in low‑bit quantized CPU mode. Enforce zero‑shot prompt. Parse responses into standard categories, handling "uncertain" mapping. Record `inference_time_ms` per sample. **Per-Sample Constraint**: If a single sample exceeds 4.32 seconds, **skip that sample**, log the timeout, and continue (do not abort the whole run). **Circuit Breaker**: If cumulative runtime exceeds 90 % of the 6‑hour limit, **reduce batch size** to a minimal value and continue processing remaining samples (do not abort). Write `data/logs/circuit_breaker_state.json` with `"timeout_risk": true`. Use `MemoryMonitor` to respect RAM limits. **Dependency**: T004a, T004b, T012, T012a, T013d. (FR‑002, SC‑003, FR‑007)
- [ ] T015 [US1] **Ingest Pipeline Orchestrator**: Coordinate execution order: **T011 -> T012 -> T013 -> T015**. Validate final `predictions.csv` against `PredictionResult` schema, and ensure batch size adapts based on memory monitor. **Dependency**: T011, T012, T013, T009b. (Dependency: T011, T012, T013)
- [X] T017 [US1] Implement `tests/unit/test_llm_inference.py` to verify batch processing and memory footprint on a mock dataset.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Structural, Semantic & Embedding Feature Extraction (Priority: P2)

**Goal**: Extract structural (AST), semantic (taint API), and embedding features for every code snippet.

**Independent Test**: Run parser on a single file with known complexity and verify JSON output contains non‑null numeric values for AST depth, complexity, and embedding score.

### Implementation for User Story 2

- [ ] T018a [US2] Implement `src/data/feature_extractor.py` using `tree-sitter` to compute structural metrics (AST depth, node count, cyclomatic complexity). Consume `data/processed/raw_snippets.parquet` from T012.
- [ ] T018b [US2] Extend `feature_extractor.py` to compute semantic metrics: taint‑source API count and sanitization presence (boolean) via AST pattern matching or regex. Populate `taint_api_count` and `sanitization_present` in `FeatureVector`.
- [ ] T019a [US2] **Vulnerability Pattern Corpus Download**: Retrieve the **NVD JSON feed** using the exact endpoint: ` to `data/raw/nvd_corpus.json.gz`. Verify checksum against `data/raw/checksums.json`. Log success/failure to `data/logs/nvd_download.json`. **Filter** entries to ensure no content overlap with VulDeePecker/BigVul training sets (independence check). **Dependency**: T005. (FR-004)
- [ ] T019b [US2] **Pattern Curation**: Filter the NVD feed for vulnerability keywords (e.g., injection, overflow) into `data/canonical_patterns.json`. **Ensure** this set is distinct from the training data. **Dependency**: T019a. (FR-004)
- [ ] T019d [US2] **Independence Check**: Compare IDs and content in `data/canonical_patterns.json` against IDs present in the training datasets (VulDeePecker, BigVul). **If any overlap is detected, abort the pipeline** and write details to `data/logs/independence_check.json`. This satisfies the plan's independence requirement. **Dependency**: T019b. (FR-004)
- [ ] T019c [US2] **Embedding Similarity Computation**: For each code snippet (from `data/processed/raw_snippets.parquet` produced by T012), compute cosine similarity against the canonical pattern embeddings (generated using `sentence-transformers/all-MiniLM-L6-v2`) and store the maximum similarity as `embedding_similarity_score` in `FeatureVector`. Log progress to `data/logs/similarity_computation.json`. **Dependency**: T019d, T012, T008b. (FR-004)
- [ ] T018c [US2] **Feature Pipeline**: Run structural, semantic, and similarity extraction on the full dataset (from T012), producing `data/processed/features.csv` (including `language`, and all metric columns). **Dependencies**: T018a, T018b, T019c, T012, T008b (Must validate FeatureVector schema before execution), T019a, T019b, T019d.
- [ ] T021 [US2] Add error handling in `feature_extractor.py` to log malformed code snippets as null/invalid and continue processing remaining batches, writing details to `data/logs/feature_extractor_errors.json`.
- [ ] T023 [US2] Implement `tests/unit/test_feature_extractor.py` to verify metric calculation on known test cases (e.g., deeply nested function).

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

---

## Phase 4: User Story 4 - Static Analyzer Baseline Comparison (Priority: P2)

**Goal**: Execute static analysis tools (Bandit, cppcheck) on the dataset to establish a baseline for comparison.

**Independent Test**: Run Bandit on a known vulnerable Python script and verify it flags the vulnerability and outputs a structured result file.

### Implementation for User Story 4

- [ ] T024 [US4] Implement `src/models/static_analyzer.py` to wrap `bandit` (flags: `-r -ll -ii`) for Python snippets and `cppcheck` (flags: `--enable=all --inconclusive --error-exitcode=1`) for C snippets.
- [ ] T025 [US4] Add parsing logic to convert static analyzer output into `PredictionResult` schema (including `is_correct` flag based on ground truth).
- [ ] T026 [US4] Implement `src/data/static_analysis_pipeline.py` to run analyzers on the full dataset and save `data/processed/static_predictions.csv`.
- [ ] T027 [US4] Implement `tests/unit/test_static_analyzer.py` to verify correct flagging of known vulnerabilities in Python and C.

**Checkpoint**: At this point, User Story 4 should be fully functional and testable independently

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Compute metrics, correlations, regression, and McNemar's test to derive scientific findings.

**Independent Test**: Provide a synthetic CSV of features and labels; verify script outputs correlation matrix, regression summary, and McNemar's test statistic.

### Implementation for User Story 3

- [ ] T028 [US3] Implement `src/analysis/metrics.py` to calculate Precision, Recall, F1, and ROC‑AUC per category and model.
- [ ] T029 [US3] Implement correlation analysis in `src/analysis/regression.py` to compute Pearson r between each feature and `is_correct`. **Constraint**: Apply Bonferroni correction **per vulnerability category** (family-wise error control for each category's set of features), not globally. Output `data/results/correlation_results.json` with adjusted p‑values and a flag for non‑significant results. (FR-005)
- [ ] T030 [US3] **Binary Logistic Regression**: Fit a GLM (logit) using `statsmodels` to predict `is_correct` from all features, including one‑hot encoded `language`. Produce `data/results/regression_summary.json` (coefficients, p‑values, `log_likelihood`, `n_samples`). (Dependency: T018c, T015, T026)
- [ ] T030a [US3] **McFadden’s Pseudo R² Calculation**: **Run after T030**. Compute McFadden's Pseudo R² from the fitted model. **Output**: Write to `data/results/regression_intermediate.json` with key `pseudo_r2_mcfadden`. **Documentation**: Explicitly note in the output and code comments that this key represents the "McFadden's Pseudo R²" metric. **Do NOT** map this to "Adjusted R²". (Dependency: T030)
- [ ] T030b [US3] **Report Generator Update**: **Run after T030a**. Update `src/analysis/report_generator.py` to explicitly report `pseudo_r2_mcfadden` as "McFadden's Pseudo R²" in the final report, avoiding the conflation with "Adjusted R²". (Dependency: T030a)
- [ ] T031 [US3] Implement McNemar's test in `src/analysis/regression.py` using `statsmodels.stats.contingency.mcnemar` (exact binomial) to compare LLM vs. static analyzer predictions. Output `data/results/mcnemar_test.json`. **Note**: T030 and T031 are parallel consumers of T015/T026.
- [ ] T032 [US3] Implement `src/analysis/visualizer.py` to generate plots for feature correlations and ROC curves, saved under `data/results/visualizations/`.
- [ ] T033 [US3] Implement `src/analysis/report_generator.py` to aggregate all metrics into `data/results/metrics.json` and draft a summary section in `research.md`. **Note**: Report `pseudo_r2_mcfadden` as "McFadden's Pseudo R²" (not "Adjusted R²"). (Dependency: T030b)
- [ ] T034 [US3] Implement `tests/unit/test_regression.py` to verify statistical outputs on synthetic data.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase 6: Human Verification & Sensitivity Analysis (Priority: P3 - FR‑011)

**Goal**: Validate the impact of ground‑truth label noise on metrics using a real human‑verified subset or an independent secondary dataset.

### Implementation

- [ ] T035 [P] **Sensitivity Analysis Setup**: **Check**: Verify the existence of `data/human_review/verified_labels.csv`. **Constraint**: If the file is missing, **ABORT** the pipeline immediately with a hard error. This task MUST NOT proceed to an "unmet" status; FR-011 is non-negotiable. **Requirement**: This analysis MUST use an independent ground-truth source (e.g., a secondary labeled dataset subset) as per FR-011. **Dependency**: T015.
- [ ] T036a [P] **External Data Check**: Check for the existence of `data/human_review/verified_labels.csv`. If missing, trigger T035 (which aborts). If present, proceed to T036. (Dependency: T035)
- [ ] T036 [P] **Ingest Verified Labels**: Ingest `data/human_review/verified_labels.csv` (from a real secondary source). Validate its schema (`snippet_id`, `verified_label`). If the file is missing or invalid, **trigger T035** (abort) instead of attempting recovery. (Dependency: T035, T036a)
- [ ] T036c [P] **Verification of Sensitivity Execution**: After verified labels are available, recompute precision, recall, and F1 using the new labels and write a comparison report to `data/results/sensitivity_analysis.json`. Log verification steps to `data/human_review/verification_log.json`. (Dependency: T036)
- [ ] T037 [P] Output final sensitivity report `data/results/sensitivity_analysis.json` with adjusted metrics and a clear note on the source (must be real independent data). (Dependency: T036c)

**Checkpoint**: Sensitivity analysis complete (or pipeline aborted if data missing)

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
- **User Stories (Phase 2‑6)**: All depend on Foundational phase completion
 - **Data Flow Constraint**: Phase 2 (Inference), Phase 3 (Feature Extraction), and Phase 4 (Static Analysis) can run in parallel but **MUST** complete before Phase 5 (Analysis).
 - **Analysis Constraint**: Phase 5 cannot run until `data/processed/predictions.csv`, `data/processed/features.csv`, and `data/processed/static_predictions.csv` exist.
 - **Human Review Constraint**: T036 requires a real secondary dataset; if unavailable, the pipeline aborts via T035.

### User Story Dependencies

- **User Story 1 (P1)**: Core pipeline. Depends on Foundational.
- **User Story 2 (P2)**: Feature extraction. Depends on Foundational. Can run parallel to US1.
- **User Story 4 (P2)**: Static analysis. Depends on Foundational. Can run parallel to US1/US2.
- **User Story 3 (P3)**: Statistical analysis. **Depends on US1, US2, and US4 completion** (requires predictions and features).
- **Sensitivity (Phase 6)**: Depends on US1 completion (requires predictions) and external human review (non‑blocking, but requires real data).

### Within Each User Story

- Models/Classes before Logic
- Logic before Pipelines
- Pipelines before Tests

### Parallel Opportunities

- **Setup**: T001, T003, T004 can run in parallel. T007a‑T009e (generation & verification) can run concurrently.
- **Data Processing**: T011 (Download), T018 (Feature Extract), T024 (Static Analyzer) can run in parallel once data is available.
 - **Note**: T019 (Vulnerability Pattern Pipeline) is split into T019a‑T019d; these run sequentially but independently of the main dataset flow.
- **Analysis**: T028, T029, T030, T030a, T031 can be implemented in parallel, though execution order respects dependencies. T030 and T031 are parallel consumers of their respective upstream tasks.

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability to specific user stories
- **Memory Constraint**: All LLM tasks must use low‑bit quantization and dynamic batch sizing to stay under constrained memory limits.
- **Time Constraint**: The pipeline must complete within 6 hours; per‑sample inference ≤ 4.32s. Outliers exceeding this are skipped, not the whole run.
- **Data Integrity**: Never synthesize fake data; always use the real BigVul dataset (C/C++/JS) as per Plan.
- **Verification**: Ensure tests fail before implementing.
- **Commit**: Commit after each task or logical group.
- **Stop**: Stop at any checkpoint to validate story independently.
- **Spec Precedence**: Where the Plan conflicts with the Spec (e.g., "Quantization‑aware training" vs "Zero‑Shot"), the Spec takes precedence per Constitution Principle II.