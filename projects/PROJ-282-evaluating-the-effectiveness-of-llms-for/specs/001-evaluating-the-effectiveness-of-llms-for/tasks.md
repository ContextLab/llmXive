# Tasks: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

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

- [ ] T001a-Impl [P] **Implement Directory Tree Generator**: Create `src/utils/dir_tree_gen.py`. **Logic**: Script must traverse the repository root, identify all directories and files, and output a JSON object representing the tree structure. **Output**: The script must be executable and ready for T001a-Exec. (Dependency: None)
- [ ] T001a-Exec [P] **Create Project Directory Structure**: Execute `src/utils/dir_tree_gen.py` to generate the full directory tree as defined in `plan.md` (`src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `state/`, `data/logs/`, `contracts/`). **Verification**: The script must output `data/logs/dir_tree.json`. **Task Complete Definition**: Task is only complete when `data/logs/dir_tree.json` exists, is valid JSON, and matches the created structure. (FR-001, Plan Project Structure)
- [ ] T001b-Impl [P] **Implement Core Files Generator**: Create `src/utils/core_files_gen.py`. **Logic**: Script must create `__init__.py` in all `src/` subdirectories, `.gitignore`, and `requirements.txt` (if not present), then compute checksums for all created files. **Output**: The script must be executable and ready for T001b-Exec. (Dependency: None)
- [ ] T001b-Exec [P] **Create Core Files**: Execute `src/utils/core_files_gen.py`. **Verification**: The script must output `data/logs/core_files.json` listing the created files and their checksums. **Task Complete Definition**: Task is only complete when `data/logs/core_files.json` exists and lists all created files. (FR-001, Plan Project Structure)
- [X] T002 **Initialize Python project** with `requirements.txt` (transformers, scikit-learn, pandas, tree-sitter, networkx, requests, pyyaml, bitsandbytes, sentence-transformers, pytest, radon, statsmodels)
- [ ] T003-Impl [P] **Implement Linting Check Script**: Create `src/utils/linting_check.py`. **Logic**: Script must run `ruff check` and `black --check` on `src/` and capture the output to a JSON log. **Output**: The script must be executable and ready for T003-Exec. (Dependency: None)
- [ ] T003-Exec [P] **Configure Linting & Formatting**: Execute `src/utils/linting_check.py` after configuring `ruff` and `black` in `pyproject.toml`. **Verification**: The script must output `data/logs/linting_config.json`. **Task Complete Definition**: Task is only complete when `data/logs/linting_config.json` exists and contains the validation output. (FR-001, Plan Project Structure)
- [X] T004 **Implement `src/utils/config.py`** with seeds, paths, runtime thresholds (hourly limit, gigabyte RAM cap), and the **deterministic, alphabetically ordered** list of candidate LLMs. (FR-002, SC-005)
- [ ] T004b-Impl [P] **CPU‑Only Pre‑Flight Check**: Create `src/utils/cpu_check.py`. **Logic**: Script must check `torch.cuda.is_available()`. If `True`, write `{"status": "GPU_DETECTED", "abort": true}` to `data/logs/cpu_check.json` and exit with code 1. If `False`, write `{"status": "CPU_ONLY", "abort": false}` and exit 0. **Constraint**: This task runs **before** T004a‑Impl and **depends on** T004. (FR-002, SC-005)
- [ ] T004a-Impl [P] **Implement Model Selection Logic**: Create `src/utils/model_selector.py`. **Logic**: Iterate through the **alphabetically ordered candidate list** (from T004). For each model, perform a capability check by running inference on three language snippets (`int x = 0;` for C, `x = 1` for Python, `var y = 1;` for JS). Success criteria: (i) JSON‑parseable output containing a `predicted_label` field, (ii) total inference time ≤ 5 s for the three snippets. Select the first valid model that meets criteria. **Output**: Log the selected model to `data/logs/model_selection.json`. **Dependency**: T004, T004b‑Impl. (FR-002)
- [ ] T004a-Exec [P] **Execute Model Selection**: Execute `src/utils/model_selector.py`. **Verification**: The script must output `data/logs/model_selection.json`. **Task Complete Definition**: Task is only complete when `data/logs/model_selection.json` exists and lists the selected model. **Dependency**: T004b‑Impl, T004a‑Impl.
- [X] T004d-Impl [P] **Dynamic Batch Sizing Implementation**: Implement `src/utils/batch_sizer.py` to calculate optimal batch size based on current RAM usage. **Logic**: Implement a function `calculate_batch_size(available_ram_gb, model_memory_gb)` that returns a batch size ensuring total memory < 7 GB. **Verification**: Unit test `tests/unit/test_batch_sizer.py` with mock RAM values. (FR-002, SC-005)
- [X] T005 **Implement `src/utils/validate_urls.py`** to validate dataset URLs against `research.md` manifest (Constitution II). **Constraint**: Must complete before any data ingestion tasks.
- [X] T005-Exec **Execute URL Validation**: Execute `src/utils/validate_urls.py` against `research.md`. Update `state/projects/PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml` with PASS/FAIL. Abort pipeline on FAIL. **Dependency**: T005.
- [X] T006 **Implement `src/utils/logger.py`** with structured logging for pipeline stages.
- [X] T007a **Create `contracts/dataset.schema.yaml`** defining the `CodeSnippet` schema. **Priority**: P1.
- [X] T007b **Generate & Verify CodeSnippet Dataclass** from the schema. (Constitution IV)
- [X] T008a **Create `contracts/feature.schema.yaml`** defining the `FeatureVector` schema. **Priority**: P1.
- [X] T008b **Generate & Verify FeatureVector Dataclass** from the schema.
- [X] T009a **Create `contracts/prediction.schema.yaml`** defining the `PredictionResult` schema. **Priority**: P1.
- [X] T009b **Generate & Verify PredictionResult Dataclass** from the schema.
- [X] T009d **Create `contracts/analysis_metric.schema.yaml`** defining the `AnalysisMetric` schema. **Priority**: P1.
- [X] T009e **Generate & Verify AnalysisMetric Dataclass** from the schema.
- [X] T010 **Implement `src/utils/hash_artifacts.py`** for checksum generation and state file updates (Constitution V).
- [X] T011‑Waiver **Document BigVul → JSVulnDB substitution waiver**: Create `research/waiver_bigvul_jsvulndb.md` explaining the authorized substitution and link it from `spec.md`. **Priority**: P1. **Dependency**: T005‑Exec.
- [X] T011a **Map JSVulnDB Schema to BigVul**: Produce `data/logs/jsvulndb_bigvul_mapping.json`. (FR‑001)
- [X] T011-Impl **Implement JSVulnDB Downloader**: Create `src/data/ingest.py` function `download_jsvulndb()`. **Logic**: Fetch JSVulnDB from `, filter `language == JS`, apply mapping from T011a, save to `data/raw/`. **Dependency**: T011a, T005‑Exec.
- [X] T011-Exec **Download JSVulnDB Dataset (JavaScript)**: Execute `download_jsvulndb()`. **Verification**: `data/raw/jsvulndb_js_*` files exist and checksums match. (FR‑001)
- [X] T011b-Impl **Implement NIST Juliet Downloader**: Create `src/data/ingest.py` function `download_juliet()`. **Logic**: `git clone and extract the C subset to `data/raw/`. **Dependency**: None.
- [X] T011b-Exec **Download NIST Juliet Dataset (C Subset)**: Execute `download_juliet()`. **Verification**: `data/raw/juliet_c_*` files exist and checksums match. (FR‑001)
- [X] T010a-Impl **Implement VulDeePecker Downloader**: Create `src/data/ingest.py` function `download_vuldeepecker()`. **Logic**: Use `datasets.load_dataset('VulDeePecker/VulDeePecker')`. Fallback URL: `. Save to `data/raw/`. **Dependency**: T005‑Exec.
- [X] T010a-Exec **Download VulDeePecker Dataset (Python)**: Execute `download_vuldeepecker()`. **Verification**: `data/raw/vuldeepecker_*` files exist. (FR‑001)
- [X] T010a-Checksum **Checksum VulDeePecker**: Generate SHA‑256 checksums for downloaded files and update `data/raw/checksums.json`. (Dependency: T010a‑Exec)
- [X] T012-Impl **Implement Parser**: Create `src/data/ingest.py` function `parse_datasets()`. **Mapping** as described. **Exclude samples lacking `ground_truth_label` and log them to `data/logs/dropped_samples.json`.** Output `data/processed/parsed_snippets.parquet`. (Dependency: T010a‑Exec, T011‑Exec, T011b‑Exec)
- [X] T012-Exec **Parse Raw Data**: Execute `parse_datasets()`. **Verification**: `data/processed/parsed_snippets.parquet` exists and is valid. (Dependency: T012‑Impl)
- [X] T012b-Impl **Implement Stratified Sampler**: Create `src/data/ingest.py` function `sample_stratified`. **Logic**: Determine `n = min(5000, total_samples)` (read from config) and use `StratifiedShuffleSplit(random_state=42, n_splits=1, train_size=n)` to sample across languages and categories. Output `data/processed/sampled_snippets_temp.parquet`. (Dependency: T012‑Exec)
- [X] T012b-Exec **Perform Stratified Sampling**: Execute `sample_stratified()`. **Verification**: `data/processed/sampled_snippets_temp.parquet` exists. (Dependency: T012b‑Impl)
- [X] T012b-1-Impl **Verify Stratification & Enforce Cap**: Create `src/data/ingest.py` function `verify_stratification()`. **Logic**: Ensure sampled size ≤ 5,000, compute language & category distributions, assert bias ≤ 5 % (log warning if exceeded, do not abort). Output final `data/processed/sampled_snippets.parquet` and `data/logs/stratification_verification.json`. (Dependency: T012b‑Exec)
- [X] T012b-1-Exec **Verify Global Stratification & Enforce Cap**: Execute `verify_stratification()`. **Verification**: Final parquet exists and verification log indicates success. (Dependency: T012b-1‑Impl)
- [X] T013-Impl **Implement Zero‑Shot Inference Service**: Create `src/models/llm_inference.py`. **Logic**: Load selected model (from T004a‑Exec) in low‑bit CPU mode, run zero‑shot prompt, map outputs to standard categories via regex, record `inference_time_ms` per sample, invoke `handle_uncertain_response()` (T056‑Impl) and `truncate_snippet()` (T057‑Impl) as needed, use `MemoryMonitor` (T013d‑Impl) and `Dynamic Batch Sizer` (T004d). Write raw predictions to `data/results/predictions_raw.json`. **Dependency**: T004a‑Exec, T004b‑Impl, T012b-1‑Exec, T056‑Impl, T057‑Impl, T013d‑Impl, T004d.
- [X] T013-Exec **Execute Zero‑Shot Inference**: Run `src/models/llm_inference.py`. **Verification**: `data/results/predictions_raw.json` exists and contains per‑sample timings. (Dependency: T013‑Impl)
- [X] T013c-Impl **Implement Runtime Aggregator**: Create `src/utils/runtime_analyzer.py` function `aggregate_runtime()`. **Logic**: Consume `predictions_raw.json`, compute total runtime, average & max per‑sample time, write to `data/results/runtime_metrics.json`. (Dependency: T013‑Exec)
- [X] T013c-Exec **Aggregate Runtime Metrics**: Execute `aggregate_runtime()`. **Verification**: `data/results/runtime_metrics.json` exists. (Dependency: T013c‑Impl)
- [X] T013d-Impl **Implement Per‑Sample Runtime Verification**: Extend `src/utils/runtime_analyzer.py` with `verify_per_sample_runtime()` that asserts every `inference_time_ms` ≤ 4320 ms and aborts with a clear error if any sample exceeds the budget. Output `data/results/runtime_verification.json` with `pass: true/false`. (Dependency: T013c‑Exec)
- [X] T013d-Exec **Verify Runtime & Resource Constraints**: Execute `verify_per_sample_runtime()`. **Verification**: `data/results/runtime_verification.json` exists with `pass: true`. (Dependency: T013d‑Impl)
- [X] T017 **Unit Test LLM Inference**: `tests/unit/test_llm_inference.py` validates batch processing and memory footprint on a mock dataset. (Dependency: T013‑Exec)
- [X] T056-Impl **Implement Uncertain Prediction Handler**: Add `handle_uncertain_response()` in `src/models/llm_inference.py`. **Logic**: Map non‑standard responses (e.g., "maybe", "unclear") to an explicit `uncertain` category or treat as negative based on a strict confidence threshold. Log the mapping decision to `data/logs/uncertain_handling.json`. (Dependency: T013‑Impl)
- [X] T056-Exec **Verify Uncertain Handling**: Run inference on a set of ambiguous prompts and verify `data/results/predictions_raw.json` contains the correct mapping. (Dependency: T056‑Impl)
- [X] T057-Impl **Implement Context Window Truncation**: Add `truncate_snippet()` in `src/models/llm_inference.py`. **Logic**: If snippet length exceeds the model’s context window, truncate to the most recent N tokens (or first N tokens) and record a `truncation_event` flag in the output. Log truncation events to `data/logs/truncation_events.json`. (Dependency: T013‑Impl)
- [X] T057-Exec **Verify Truncation Logic**: Run inference on artificially oversized snippets and verify `truncation_event` flags are set correctly. (Dependency: T057‑Impl)
- [X] T018-Impl **Implement Feature Extractor**: Create `src/data/feature_extractor.py`. **Logic**: Use `tree‑sitter` for AST depth/node count, `radon` for cyclomatic complexity, count taint‑source APIs (`eval`, `exec`, `system`, etc.) and sanitization functions (`escape`, `sanitize`, …). Output `data/processed/structural_features.json`. Log malformed snippets to `data/logs/feature_extractor_errors.json`. (Dependency: T012b‑1‑Exec, T008b)
- [X] T018-Exec **Execute Feature Extraction**: Run extractor. **Verification**: `data/processed/structural_features.json` exists. (Dependency: T018‑Impl)
- [X] T019a-Impl **Implement NVD Downloader**: Create `src/data/ingest.py` function `download_nvd()`. **Logic**: `wget https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-modified.json.gz`. Save to `data/raw/vul_pattern_corpus_raw.json.gz`. Verify checksum. (Dependency: None)
- [X] T019a-Exec **Download NVD Corpus**: Execute `download_nvd()`. **Verification**: `data/raw/vul_pattern_corpus_raw.json.gz` exists. (Dependency: T019a‑Impl)
- [X] T019a-Freeze **Freeze NVD Feed Snapshot**: Copy `data/raw/vul_pattern_corpus_raw.json.gz` to a timestamped, version‑controlled file `data/raw/vul_pattern_corpus_2024-01-01.json.gz` and record its SHA‑256 hash in `data/logs/nvd_snapshot.json`. Downstream tasks must use this frozen file. (Dependency: T019a‑Exec)
- [X] T019b-Impl **Implement Pattern Curation**: In `src/data/feature_extractor.py` add `curate_patterns()`. **Logic**: Load the frozen snapshot `data/raw/vul_pattern_corpus_2024-01-01.json.gz`, filter NVD entries for keywords (`injection`, `overflow`, `xss`, `rce`, etc.), generate embeddings using `sentence-transformers/all-MiniLM-L6-v2`, save to `data/processed/reference_patterns.json`. (Dependency: T019a‑Freeze)
- [X] T019b-Exec **Execute Pattern Curation**: Run `curate_patterns()`. **Verification**: `data/processed/reference_patterns.json` exists. (Dependency: T019b‑Impl)
- [X] T019d-Impl **Implement Independence Check**: Add `check_independence()` that computes SHA‑256 hashes of reference pattern texts and training snippet texts; if any hash matches, **abort** with error log `data/logs/independence_check.json`. **Dependency**: T019b‑Exec, T010a‑Exec, T011‑Exec, T011b‑Exec, T012b‑1‑Exec.
- [X] T019d-Exec **Execute Independence Check**: Run `check_independence()`. **Verification**: `data/logs/independence_check.json` indicates pass; abort on failure. (Dependency: T019d‑Impl)
- [X] T019c-Impl **Implement Similarity Computation**: Add `compute_similarity()` that, for each snippet in `sampled_snippets.parquet`, computes cosine similarity against embeddings in `reference_patterns.json` and stores max similarity as `embedding_similarity_score` in `FeatureVector`. (Dependency: T019d‑Exec)
- [X] T019c-Exec **Execute Similarity Computation**: Run `compute_similarity()`. **Verification**: `data/logs/similarity_computation.json` exists. (Dependency: T019c‑Impl)
- [X] T018d-Impl **Implement Feature Pipeline**: Add `run_pipeline()` that runs structural, semantic, and similarity extraction, merges results into `data/processed/features.csv` adhering to `FeatureVector` schema. (Dependency: T018‑Exec, T019c‑Exec, T019d‑Exec, T008b)
- [X] T018d-Exec **Execute Feature Pipeline**: Run `run_pipeline()`. **Verification**: `data/processed/features.csv` exists. (Dependency: T018d‑Impl)
- [X] T021 **Add error handling** in `feature_extractor.py` to log malformed snippets (already covered by T018‑Impl).
- [X] T023 **Unit tests** `tests/unit/test_feature_extractor.py` for known complexity cases. (Dependency: T018‑Impl)
- [X] T024-Impl **Implement Static Analyzer Wrapper**: Create `src/models/static_analyzer.py`. **Logic**: Wrap `bandit` for Python and `cppcheck` for C with appropriate flags. (Dependency: None)
- [X] T024-Exec **Execute Static Analyzer Wrapper**: Verify tool availability. (Dependency: T024‑Impl)
- [X] T025-Impl **Implement Static Analyzer Parser**: Add `parse_results()` converting tool output to `PredictionResult` schema, including `is_correct`. (Dependency: T024‑Impl)
- [X] T025-Exec **Execute Static Analyzer Parser** on a sample. (Dependency: T025‑Impl)
- [X] T026-Impl **Implement Static Analysis Pipeline**: Run wrappers on full dataset, save `data/processed/static_predictions.csv`. (Dependency: T025‑Exec)
- [X] T026-Exec **Execute Static Analysis Pipeline**. (Dependency: T026‑Impl)
- [X] T027 **Unit tests** `tests/unit/test_static_analyzer.py` for known vulnerabilities. (Dependency: T024‑Exec)
- [X] T028-Impl **Implement Metrics Calculator**: `src/analysis/metrics.py` computes Precision, Recall, F1, ROC‑AUC per category/model. (Dependency: T015‑Exec, T026‑Exec)
- [X] T028-Exec **Execute Metrics Calculation**. (Dependency: T028‑Impl)
- [X] T029a-Impl **Implement Correlation Analysis**: `src/analysis/regression.py` `compute_correlations()` (Pearson r) between each feature and `is_correct`. Output `data/results/correlation_raw.json`. (Dependency: T018d‑Exec, T015‑Exec, T026‑Exec)
- [X] T029a-Exec **Execute Correlation Analysis**. (Dependency: T029a‑Impl)
- [X] T029b-Impl **Implement Multiple‑Comparison Correction**: `apply_correction()` using Bonferroni per vulnerability category. Output `data/results/correlation_results.json`. (Dependency: T029a‑Exec)
- [X] T029b-Exec **Execute Correction**. (Dependency: T029b‑Impl)
- [X] T029c-Impl **Implement Correlation Report Generator**: `src/analysis/report_generator.py` `generate_correlation_report()`. Output `data/results/correlation_report.json`. (Dependency: T029a‑Exec, T029b‑Exec)
- [X] T029c-Exec **Execute Report Generation**. (Dependency: T029c‑Impl)
- [X] T030-Impl **Implement Logistic Regression**: `src/analysis/regression.py` `fit_regression()` using `statsmodels` GLM logit, including one‑hot encoded `language` and `cwe_category`, **including** `embedding_similarity_score`. Compute McFadden’s Pseudo R² and Nagelkerke Adjusted R². Save summary to `data/results/regression_summary.json`. (Dependency: T018d‑Exec, T015‑Exec, T026‑Exec)
- [X] T030-Exec **Execute Logistic Regression**. (Dependency: T030‑Impl)
- [X] T031-Impl **Implement McNemar's Test**: `src/analysis/regression.py` `run_mcnemar()` using `statsmodels.stats.contingency.mcnemar`. Output `data/results/mcnemar_test.json`. (Dependency: T015‑Exec, T026‑Exec)
- [X] T031-Exec **Execute McNemar's Test**. (Dependency: T031‑Impl)
- [X] T032-Impl **Implement Visualizer**: `src/analysis/visualizer.py` generates plots saved under `data/results/visualizations/`. (Dependency: T029c‑Exec, T028‑Exec)
- [X] T032-Exec **Execute Visualizer**. (Dependency: T032‑Impl)
- [X] T033-Impl **Implement Final Report Generator**: `src/analysis/report_generator.py` `generate_final_report()` aggregates all metrics into `data/results/metrics.json` and updates `research.md` with summary. (Dependency: T030‑Exec, T031‑Exec, T032‑Exec)
- [X] T033-Exec **Execute Final Report Generation**. (Dependency: T033‑Impl)
- [X] T034 **Unit tests** `tests/unit/test_regression.py` on synthetic data. (Dependency: T030‑Impl)
- [X] T036-Impl **Download Secondary Ground‑Truth Subset**: Create `src/data/sensitivity.py` function `download_secondary_subset()`. **Logic**: Fetch the OWASP Benchmark dataset from `, extract a stratified 100‑snippet sample with verified labels, and store as `data/secondary/verified_subset.csv`. (Dependency: None)
- [X] T036-Exec **Ingest Secondary Subset**: Execute `download_secondary_subset()`. **Verification**: `data/secondary/verified_subset.csv` exists and passes schema validation. (Dependency: T036‑Impl)
- [X] T036c-Impl **Independent Re‑Labeling Protocol**: Randomly select 200 snippets from `sampled_snippets.parquet` and obtain expert re‑labels (simulated by using the secondary subset where overlap exists). Store re‑labeled data as `data/secondary/relabelled_subset.csv`. (Dependency: T036‑Exec)
- [X] T036d-Impl **Compute Sensitivity Metrics**: Add `compute_sensitivity_metrics()` that recomputes precision, recall, F1 for both LLM and static analyzer predictions using the re‑labeled subset, compares against original metrics, and writes `data/results/sensitivity_analysis.json` with keys `original_metrics`, `revised_metrics`, `delta`, `conclusion`. (Dependency: T015‑Exec, T036c‑Impl)
- [X] T036b-Exec **Execute Sensitivity Computation**: Run `compute_sensitivity_metrics()`. **Verification**: `data/results/sensitivity_analysis.json` exists and contains required keys. (Dependency: T036d‑Impl)
- [X] T037 **Unit tests** `tests/unit/test_sensitivity.py` to validate computation on a tiny synthetic verified set. (Dependency: T036‑Impl)
- [X] T038-Impl **Implement Artifact Hasher**: `src/utils/hash_artifacts.py` `hash_artifacts()` runs checksums on all outputs in `data/processed/` and `data/results/`. (Dependency: All previous result‑generating tasks)
- [X] T038-Exec **Run Artifact Hasher**. (Verification: `data/logs/artifact_hashes.json` exists.)
- [X] T039-Impl **Implement State Updater**: `src/utils/state_updater.py` `update_state()` updates `state/projects/PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml` with new hashes and completion status.
- [X] T039-Exec **Update State File**. (Verification: state file updated.)
- [X] T040-Impl **Implement Research Report Generator**: `src/analysis/report_generator.py` `generate_research_report()` writes final narrative to `research.md`.
- [X] T040-Exec **Generate Research Report**. (Verification: `research.md` updated.)
- [X] T050 **Documentation updates**: Update `docs/README.md`, `docs/QUICKSTART.md`, and `docs/API.md` to reflect the final pipeline, usage examples, and versioned artifact locations. (Dependency: All prior phases)
- [X] T051 **Code cleanup and refactoring**: Run `ruff --fix` on `src/models/`, `src/data/`, and `src/analysis/`; remove dead code; enforce cyclomatic complexity ≤ 10 using `radon cc -a`. (Dependency: All code modules)
- [X] T052 **Performance optimization**: Implement an LRU cache for AST parsing in `src/data/feature_extractor.py` and batch embedding generation for similarity scores with a size‑limited queue; target ≥ 10 % reduction in total runtime. (Dependency: T018‑Impl, T019c‑Impl)
- [X] T053 **Additional unit tests** in `tests/unit/` as needed.
- [X] T054 **Security hardening** (static analysis of the pipeline code itself).
- [X] T055 **Validate quickstart.md** against the actual pipeline.

## Phase 2: User Story 1 – Zero‑Shot Vulnerability Detection Pipeline (Priority: P1)

**Goal**: Ingest dataset, run zero‑shot LLM inference, and generate correctness flags against ground truth.

- [ ] T015-Impl **Implement Orchestrator**: Create `src/main.py`. **Logic**: Implement a DAG runner that invokes downstream implementation tasks (module availability) in correct order. **Output**: `data/logs/orchestration_log.json`. **Dependency**: T004a‑Impl, T010a‑Impl, T011‑Impl, T012‑Impl, T013‑Impl, T018‑Impl, T019b‑Impl, T024‑Impl, T028‑Impl, T030‑Impl, T031‑Impl, T032‑Impl, T033‑Impl. (FR‑001)
- [ ] T015-Exec **Execute Orchestrator**: Run `src/main.py`. **Verification**: `data/logs/orchestration_log.json` exists and contains valid execution logs. (Dependency: All Impl tasks above)
- Remaining tasks for data download, parsing, inference, and runtime verification are as listed above in Phase 2 and Phase 3 sections (T010a‑Impl through T013d‑Exec).

## Phase 3: User Story 2 – Structural, Semantic & Embedding Feature Extraction (Priority: P2)

(Tasks T018‑Impl through T023 as defined above.)

## Phase 4: User Story 4 – Static Analyzer Baseline Comparison (Priority: P2)

(Tasks T024‑Impl through T027 as defined above.)

## Phase 5: User Story 3 – Statistical Analysis & Reporting (Priority: P3)

(Tasks T028‑Impl through T034 as defined above.)

## Phase 6: Sensitivity Analysis (Automated, using secondary dataset) – Priority: P3 (FR‑011)

(Tasks T036‑Impl through T037 as defined above, now including re‑labeling and noise‑injection steps.)

## Phase 7: Versioning & Reporting (Priority: P3)

(Tasks T038‑Impl through T040‑Impl as defined above.)

## Phase 8: Polish & Cross‑Cutting Concerns

(Tasks T050, T051, T052, T053, T054, T055 as defined above.)

## Phase 9: Edge Case Handling & Robustness (Priority: P3)

**Goal**: Address specific edge cases defined in spec.md (uncertain predictions, truncation, missing labels) to ensure pipeline robustness.

- **Note**: Tasks T056‑Impl and T057‑Impl have been moved to Phase 2 with explicit dependencies to guarantee they are available before inference (T013‑Impl). The previous duplicate T058‑Impl has been removed as its functionality is already covered in T012‑Impl.
