# Tasks: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only if tests requested in the feature specification.

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

- [ ] T001a-Gen [P] **Implement Directory Tree Generator**: Create `src/utils/dir_tree_gen.py`. **Logic**: Script must traverse the repository root, identify all directories and files, and output a JSON object representing the tree structure. **Output**: Write `data/logs/dir_tree.json`. (Dependency: None)
- [ ] T001a-Write [P] **Write Directory Tree File**: Execute `src/utils/dir_tree_gen.py` to generate the full directory tree as defined in `plan.md` (`src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `state/`, `data/logs/`, `contracts/`). **Verification**: `data/logs/dir_tree.json` must exist, be valid JSON, and match the created structure. (FR-001, Plan Project Structure)
- [ ] T001b-Impl [P] **Implement Core Files Generator**: Create `src/utils/core_files_gen.py`. **Logic**: Script must create `__init__.py` in all `src/` subdirectories, a `.gitignore`, and a `requirements.txt` (if not present), then compute checksums for all created files. **Output**: Write `data/logs/core_files.json`. (Dependency: None)
- [ ] T001b-Exec [P] **Create Core Files**: Execute `src/utils/core_files_gen.py`. **Verification**: `data/logs/core_files.json` must exist and list all created files with checksums. (FR-001, Plan Project Structure)
- [X] T002 Initialize Python project with `requirements.txt` (transformers, scikit-learn, pandas, tree-sitter, networkx, requests, pyyaml, bitsandbytes, sentence-transformers, pytest, radon, statsmodels)
- [ ] T003-Impl [P] **Implement Linting Check Script**: Create `src/utils/linting_check.py`. **Logic**: Script must run `ruff check` and `black --check` on `src/` and capture the output to a JSON log. **Output**: Write `data/logs/linting_config.json`. (Dependency: None)
- [ ] T003-Exec [P] **Configure Linting & Formatting**: Execute `src/utils/linting_check.py` after configuring `ruff` and `black` in `pyproject.toml`. **Verification**: `data/logs/linting_config.json` must exist and contain the validation output. (FR-001, Plan Project Structure)
- [X] T004 **Implement `src/utils/config.py`** with seeds, paths, runtime thresholds (hourly limit, gigabyte RAM cap), and the **deterministic, alphabetically ordered** list of candidate LLMs. (FR-002, SC-005)
- [ ] T004b **CPU‑Only Pre‑Flight Check**: Create `src/utils/cpu_check.py`. **Logic**: Script must check `torch.cuda.is_available()`. If `True`, write `{"status":"GPU_DETECTED","abort":true}` to `data/logs/cpu_check.json` and exit with code 1. If `False`, write `{"status":"CPU_ONLY","abort":false}` and exit 0. **Constraint**: This task runs BEFORE model selection. (FR-002, SC-005)
- [ ] T004a-Impl [P] **Implement Model Selection Logic**: Create `src/utils/model_selector.py`. **Logic**: Iterate through the alphabetically ordered candidate list (from T004). For each model, perform a capability check by running inference on three tiny code snippets (C, Python, JS). Select the first model that completes within the time budget on CPU. **Output**: Log the selected model to `data/logs/model_selection.json`. (Dependency: T004b, T004)
- [ ] T004a-Exec [P] **Execute Model Selection**: Execute `src/utils/model_selector.py`. **Verification**: `data/logs/model_selection.json` must exist and list the selected model. (Dependency: T004a-Impl)
- [X] T004d **Dynamic Batch Sizing Implementation**: Implement `src/utils/batch_sizer.py` with function `calculate_batch_size(available_ram_gb, model_memory_gb)`. **Verification**: Unit test `tests/unit/test_batch_sizer.py` with mocked RAM values. (FR-002, SC-005)
- [X] T005 **Implement URL Validation**: Create `src/utils/validate_urls.py` that validates dataset URLs against the manifest in `research.md` using the Reference‑Validator Agent's `CITATION_TITLE_OVERLAP_THRESHOLD` logic (mandating implementation or invocation of the agent's specific threshold check). (Constitution II)
- [X] T005‑Exec **Execute URL Validation**: Run `src/utils/validate_urls.py` and update `state/projects/PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml` with PASS/FAIL. Abort pipeline on FAIL. (Dependency: T005)
- [X] T006 **Implement Structured Logger**: Create `src/utils/logger.py` for JSON‑structured pipeline logs. (FR‑001)
- [X] T007a **Create `contracts/dataset.schema.yaml`** defining the `CodeSnippet` schema. (Priority P1)
- [X] T007b **Generate & Verify `CodeSnippet` Dataclass**: Script reads `contracts/dataset.schema.yaml` and creates `src/models/code_snippet.py` using `pydantic`; writes verification log to `data/logs/code_snippet_generation.json`. (Constitution IV)
- [X] T008a **Create `contracts/feature.schema.yaml`** defining the `FeatureVector` schema. (Priority P1)
- [X] T008b **Generate & Verify `FeatureVector` Dataclass**: Generate `src/models/feature_vector.py` from schema; log to `data/logs/feature_vector_generation.json`. (Constitution IV)
- [X] T009a **Create `contracts/prediction.schema.yaml`** defining the `PredictionResult` schema. (Priority P1)
- [X] T009b **Generate & Verify `PredictionResult` Dataclass**: Generate `src/models/prediction_result.py`; log to `data/logs/prediction_result_generation.json`. (Constitution IV)
- [X] T009d **Create `contracts/analysis_metric.schema.yaml`** defining the `AnalysisMetric` schema. (Priority P1)
- [X] T009e **Generate & Verify `AnalysisMetric` Dataclass**: Generate `src/models/analysis_metric.py`; log to `data/logs/analysis_metric_generation.json`. (Constitution IV)
- [X] T010 **Implement Artifact Hasher**: Create `src/utils/hash_artifacts.py` for checksums of all outputs. (Constitution V)
- [X] T013d **Implement Memory Monitor**: Create `src/utils/memory_monitor.py` exposing a context manager to track RAM usage and trigger batch‑size reduction if a high threshold is approached. (Dependency: T004a‑Exec, T004d)
- [ ] T045-Impl [P] **Implement Strict Real‑Data Loader**: Refactor `src/data/ingest.py` to remove ALL `try/except` blocks that fall back to `generate_synthetic_*()`. Implement a strict `fetch_real_data()` function that raises `RuntimeError` immediately if the verified URL (from `research.md`) fails, ensuring the pipeline fails loudly rather than substituting fake data. (FR‑001, Constitution III)
- [ ] T045-Exec [P] **Verify Strict Failure Mode**: Run the loader against a simulated network failure; verify it exits with a clear error and NO synthetic data files are created. (Dependency: T045-Impl)

## Phase 2: Foundational (Core Orchestrator)

- [ ] T015‑Impl **Implement Orchestrator**: Create `src/main.py`. The script defines a DAG that includes **all** downstream tasks from data ingestion (T010a‑Exec …) through analysis (T028‑Exec …), sensitivity (T036‑Exec …), and final reporting (T040‑Exec). No direct dependency on execution tasks; it simply registers them. **Output**: Write `data/logs/orchestration_log.json` summarising task statuses. (FR‑001)
- [ ] T015‑Exec **Execute Orchestrator**: Run `src/main.py`. **Verification**: `data/logs/orchestration_log.json` must exist and contain valid execution logs for every task in the pipeline. (Dependency: T015‑Impl)
- [ ] T015c‑Impl **Implement Global Runtime Aggregator**: Create `src/utils/runtime_analyzer.py::aggregate_global_runtime()` to sum execution times from `data/logs/` (data loading, feature extraction, inference, analysis). **Output**: Write `data/results/global_runtime_metrics.json`. (Dependency: T013‑Exec, T018d‑Exec, T026‑Exec, T028‑Exec)
- [ ] T015c‑Exec **Verify Global 6‑Hour Constraint**: Execute the aggregator. **Verification**: Assert `total_runtime ≤ 6h` in `data/results/global_runtime_metrics.json`. (Dependency: T015c‑Impl)

## Phase 3: User Story 1 – Zero‑Shot Vulnerability Detection Pipeline (Priority P1)

- [ ] T010a‑Impl **Implement VulDeePecker Downloader**: Add `src/data/ingest.py::download_vuldeepecker()`. Fetch VulDeePecker via `datasets.load_dataset('VulDeePecker/VulDeePecker')` **or** fallback `wget` URL. Save to `data/raw/`. (FR‑001)
- [ ] T010a‑Exec **Download VulDeePecker (Python)**: Execute the function. **Verification**: `data/raw/vuldeepecker_*.csv` must exist. (Dependency: T010a‑Impl, T045‑Exec)
- [ ] T010a‑1 **Checksum VulDeePecker**: Generate checksums for downloaded files and store in `data/raw/checksums.json`. (FR‑001)
- [ ] T011a **Map JSVulnDB Schema to BigVul‑Like Schema**: Create `data/logs/jsvulndb_mapping.json` that maps JSVulnDB fields to the required ground‑truth schema for JavaScript. (FR‑001)
- [ ] T011‑Impl **Implement JSVulnDB Downloader**: Add `src/data/ingest.py::download_jsvulndb()`. Use the verified JSVulnDB source, filter to JavaScript, apply mapping from T011a, and save to `data/raw/`. (Dependency: T011a)
- [ ] T011‑Exec **Download JSVulnDB (JavaScript)**: Execute the function. **Verification**: `data/raw/jsvulndb_*.csv` must exist and match checksums. (Dependency: T011‑Impl, T045‑Exec)
- [ ] T011c‑Impl **Validate JSVulnDB Category Alignment**: Verify that the vulnerability categories present in JSVulnDB exactly match the required JavaScript category list (derived from BigVul's JS subset). Abort with log `data/logs/jsvuln_category_check.json` if mismatched. (Dependency: T011‑Exec)
- [ ] T011c‑Exec **Execute Category Alignment Check**: Run the validation script. **Verification**: `data/logs/jsvuln_category_check.json` must indicate success. (Dependency: T011c‑Impl)
- [ ] T011b‑Impl **Implement NIST Juliet Downloader**: Add `src/data/ingest.py::download_juliet()`. Clone the official Juliet repo, extract C/C++ testcases, save to `data/raw/`. (Dependency: None)
- [ ] T011b‑Exec **Download Juliet (C Subset)**: Execute. **Verification**: `data/raw/juliet_c_*.c` must exist and pass checksum verification. (Dependency: T011b‑Impl, T045‑Exec)
- [ ] T012a‑Impl **Implement Raw Dataset Merger**: Add `src/data/ingest.py::merge_raw_datasets()` to combine `data/raw/vuldeepecker_*.csv`, `data/raw/jsvulndb_*.csv`, and `data/raw/juliet_c_*.c` into a unified `CodeSnippet` DataFrame. **Output**: Write `data/processed/raw_combined.parquet`. (Dependency: T010a‑Exec, T011‑Exec, T011b‑Exec)
- [ ] T012a‑Exec **Execute Raw Dataset Merger**: Run the merger. **Verification**: `data/processed/raw_combined.parquet` must exist. (Dependency: T012a‑Impl)
- [ ] T012‑Impl **Implement Parser**: Add `src/data/ingest.py::parse_datasets()` to read `data/processed/raw_combined.parquet` and produce `CodeSnippet` records. Exclude samples lacking `ground_truth_label` and log them to `data/logs/dropped_samples.json`. Output `data/processed/parsed_snippets.parquet`. (Dependency: T012a‑Exec)
- [ ] T012‑Exec **Parse Raw Data**: Execute parser. **Verification**: `data/processed/parsed_snippets.parquet` must exist. (Dependency: T012‑Impl)
- [ ] T012b‑Impl **Implement Stratified Sampler**: Add `src/data/ingest.py::sample_stratified()` to perform stratified sampling (≤ 5 000 samples) by **language AND vulnerability type (CWE category)** (`random_state=42`). **Output**: Write `data/processed/sampled_snippets_stratified.parquet`. (Dependency: T012‑Exec)
- [ ] T012b‑Exec **Perform Stratified Sampling**: Execute sampler. (Dependency: T012b‑Impl)
- [ ] T012b‑1‑Impl **Implement Verification & Cap Enforcer**: Add `src/data/ingest.py::verify_stratification()` to ensure proportional representation for BOTH language AND vulnerability type and enforce the 5 000 cap; if bias > 5 % reduce sample size. Output final `data/processed/sampled_snippets.parquet` and log `data/logs/stratification_verification.json`. (Dependency: T012b‑Exec)
- [ ] T012b‑1‑Exec **Verify Stratification & Enforce Cap**: Execute verification. (Dependency: T012b‑1‑Impl)
- [ ] T013f‑Impl **Implement Truncation Handler**: Create `src/models/truncation.py::truncate_if_needed(snippet)` that checks snippet length against the LLM context window (e.g., 4 096 tokens), truncates to the first N tokens if necessary, and records each event in `data/logs/truncation_events.json`. (Dependency: T004a‑Exec)
- [ ] T013f‑Exec **Execute Truncation Handler**: Run the truncation handler on a test set to verify event logging. **Verification**: `data/logs/truncation_events.json` must exist and contain recorded events. (Dependency: T013f‑Impl)
- [ ] T013‑Impl **Implement Zero‑Shot Inference Service**: Create `src/models/llm_inference.py`. Load the selected model (from T004a‑Exec) in low‑bit CPU mode, run the truncation handler (T013f‑Exec) on each snippet, perform zero‑shot prompting, map raw LLM output to standard categories (SQLi, XSS, …, None) via regex, record `inference_time_ms` per sample, and write raw results to `data/results/llm_predictions_raw.json`. If any sample exceeds 4.32 s, abort and fall back to a smaller fallback model; log fallback decisions. (Dependencies: T004a‑Exec, T004d, T013d, T013f‑Exec, T012b‑1‑Exec)
- [ ] T013‑Exec **Execute Zero‑Shot Inference**: Run the inference script. **Verification**: `data/results/llm_predictions_raw.json` must exist. (Dependency: T013‑Impl)
- [ ] T013g‑Impl **Enforce Per‑Sample Time Budget**: Create `src/utils/inference_time_check.py` that reads `data/results/llm_predictions_raw.json`, asserts every `inference_time_ms` ≤ 4 320 ms, and aborts with log `data/logs/inference_time_check.json` if violated. (Dependency: T013‑Exec)
- [ ] T013g‑Exec **Run Time‑Budget Verification**: Execute the check. **Verification**: `data/logs/inference_time_check.json` must indicate pass. (Dependency: T013g‑Impl)
- [ ] T013c‑Impl **Implement Runtime Aggregator**: Create `src/utils/runtime_analyzer.py::aggregate_runtime()` to compute total runtime, average, max, and write `data/results/runtime_metrics.json`. (Dependency: T013‑Exec)
- [ ] T013c‑Exec **Aggregate Runtime Metrics**: Execute aggregator. **Verification**: `data/results/runtime_metrics.json` must exist. (Dependency: T013c‑Impl)
- [ ] T013‑Verify‑Impl **Implement Runtime Verification**: Create `src/utils/runtime_analyzer.py::verify_runtime()` that asserts `len(sampled_snippets) ≤ 5 000` and `total_runtime ≤ 6 h`. Write `data/results/runtime_verification.json`. (Dependency: T013c‑Exec)
- [ ] T013‑Verify‑Exec **Verify Sample Cap & Runtime**: Execute verification. **Verification**: `data/results/runtime_verification.json` must indicate success. (Dependency: T013‑Verify‑Impl)

## Phase 4: User Story 2 – Structural, Semantic & Embedding Feature Extraction (Priority P2)

- [ ] T018‑Impl **Implement Feature Extractor**: Create `src/data/feature_extractor.py` that uses `tree-sitter` for AST depth & node count, `radon` for cyclomatic complexity, counts taint‑source APIs (`eval`, `exec`, `system`, …) and sanitization functions, and writes `data/processed/structural_features.json`. Malformed snippets are logged to `data/logs/feature_extractor_errors.json` with `null` feature vectors. (Dependency: T012b‑1‑Exec, T008b)
- [ ] T018‑Exec **Execute Feature Extraction**: Run extractor. **Verification**: `data/processed/structural_features.json` must exist. (Dependency: T018‑Impl)
- [ ] T019pre‑Impl **Pre‑Verify Reference Set Independence**: Before downloading NVD, compare its CVE IDs against all IDs in the three training datasets. Abort if overlap > 5 % and log to `data/logs/reference_independence_check.json`. (Dependency: None)
- [ ] T019pre‑Exec **Run Independence Pre‑Check**: Execute pre‑check. **Verification**: Log must indicate pass. (Dependency: T019pre‑Impl)
- [ ] T019a‑Impl **Implement NVD Downloader**: Download NVD JSON feed (`) to `data/raw/vul_pattern_corpus.json`. (Dependency: T019pre‑Exec)
- [ ] T019a‑Exec **Download NVD Corpus**: Execute downloader. **Verification**: `data/raw/vul_pattern_corpus.json` must exist. (Dependency: T019a‑Impl)
- [ ] T019b‑Impl **Implement Pattern Curation**: Filter NVD for keywords (`injection`, `overflow`, `xss`, `rce`, …), generate embeddings using `sentence-transformers/all-MiniLM-L-v2`, and save to `data/processed/reference_patterns.json`. (Dependency: T019a‑Exec)
- [ ] T019b‑Exec **Execute Pattern Curation**: Run curation. **Verification**: `data/processed/reference_patterns.json` must exist. (Dependency: T019b‑Impl)
- [ ] T019d‑Impl **Implement Independence Check**: Compare IDs/content of `reference_patterns.json` against training data (VulDeePecker, JSVulnDB, Juliet). Log any overlap to `data/logs/independence_check.json`; if overlap detected, trigger fallback generation (T019e). (Dependency: T019b‑Exec, T010a‑Exec, T011‑Exec, T011b‑Exec)
- [ ] T019d‑Exec **Execute Independence Check**: Run check. **Verification**: `data/logs/independence_check.json` must exist. (Dependency: T019d‑Impl)
- [ ] T019e‑Impl **Implement Fallback Reference Set Generator**: If overlap was detected, fetch an alternative CVE corpus (e.g., `) and repeat filtering/embedding, saving to `data/processed/reference_patterns_fallback.json`. (Dependency: T019d‑Exec)
- [ ] T019e‑Exec **Execute Fallback Generation**: Run fallback if needed. **Verification**: Fallback file must exist when triggered. (Dependency: T019e‑Impl)
- [ ] T019c-Pre-Impl **Implement Target Snippet Embedding**: Create `src/data/feature_extractor.py::embed_target_snippets()` to generate embeddings for every snippet in `data/processed/sampled_snippets.parquet` using `sentence-transformers/all-MiniLM-L6-v2 (2607.07974, https://arxiv.org/abs/2607.07974)`. **Output**: Write `data/processed/target_embeddings.json`. (Dependency: T012b-1-Exec)
- [ ] T019c-Pre-Exec **Execute Target Snippet Embedding**: Run the embedding script. **Verification**: `data/processed/target_embeddings.json` must exist. (Dependency: T019c-Pre-Impl)
- [ ] T019c‑Impl **Implement Similarity Computation**: For each snippet in `data/processed/sampled_snippets.parquet`, compute cosine similarity against the chosen reference embeddings (primary if T019d passed, fallback if T019e ran) and store the maximum as `embedding_similarity_score` in the `FeatureVector`. **Logic**: Dynamically select the reference file based on the existence of `reference_patterns_fallback.json`. **Output**: Append `embedding_similarity_score` to `data/processed/features.csv`. Log progress to `data/logs/similarity_computation.json`. (Dependency: T019d‑Exec, T019c-Pre-Exec, T012b‑1‑Exec, T008b)
- [ ] T019c‑Exec **Execute Similarity Computation**: Run similarity script. **Verification**: `data/logs/similarity_computation.json` must exist. (Dependency: T019c‑Impl)
- [ ] T018d‑Impl **Implement Feature Pipeline**: Combine structural, semantic, and similarity features into `data/processed/features.csv` (including `language`). Validate against `FeatureVector` schema before writing. (Dependency: T018‑Exec, T019c‑Exec, T019d‑Exec, T012b‑1‑Exec, T008b)
- [ ] T018d‑Exec **Execute Feature Pipeline**: Run pipeline. **Verification**: `data/processed/features.csv` must exist. (Dependency: T018d‑Impl)

## Phase 5: User Story 4 – Static Analyzer Baseline Comparison (Priority P2)

- [ ] T024‑Impl **Implement Static Analyzer Wrapper**: Create `src/models/static_analyzer.py` with functions to invoke Bandit (Python) and cppcheck (C) with appropriate flags. (Dependency: None)
- [ ] T024‑Exec **Execute Static Analyzer Wrapper**: Run wrapper on a small sanity check sample. **Verification**: Script exits without error. (Dependency: T024‑Impl)
- [ ] T025‑Impl **Implement Static Analyzer Parser**: Add `parse_results()` to convert Bandit/cppcheck output into `PredictionResult` records, including `is_correct` against ground truth. (Dependency: T024‑Impl)
- [ ] T025‑Exec **Execute Static Analyzer Parser**: Parse sample results and verify schema compliance. (Dependency: T025‑Impl)
- [ ] T026‑Impl **Implement Static Analysis Pipeline**: Run the wrappers over the full sampled dataset and write `data/processed/static_predictions.csv`. (Dependency: T025‑Exec)
- [ ] T026‑Exec **Execute Static Analysis Pipeline**: Run pipeline. **Verification**: `data/processed/static_predictions.csv` must exist. (Dependency: T026‑Impl)
- [ ] T027 **Implement Static Analyzer Tests**: Add `tests/unit/test_static_analyzer.py` to verify known vulnerabilities are correctly flagged for Python (Bandit) and C (cppcheck). (Dependency: T026‑Exec)

## Phase 6: User Story 3 – Statistical Analysis & Reporting (Priority P3)

- [ ] T028‑Impl **Implement Metrics Calculator**: Create `src/analysis/metrics.py` to compute precision, recall, F1, ROC‑AUC per category for both LLM and static analyzer predictions. Output `data/results/metrics_raw.json`. (Dependency: T013‑Exec, T026‑Exec)
- [ ] T028‑Exec **Execute Metrics Calculation**: Run calculator. **Verification**: `data/results/metrics_raw.json` must exist. (Dependency: T028‑Impl)
- [ ] T029a‑Impl **Implement Correlation Analysis**: Add `compute_correlations()` in `src/analysis/regression.py` to calculate Pearson r between each feature and `is_correct`. Output `data/results/correlation_raw.json`. (Dependency: T018d‑Exec, T013‑Exec, T026‑Exec)
- [ ] T029a‑Exec **Execute Correlation Analysis**: Run correlation script. **Verification**: `data/results/correlation_raw.json` must exist. (Dependency: T029a‑Impl)
- [ ] T029b‑Impl **Implement Multiple‑Comparison Correction**: Add `apply_correction()` to apply Bonferroni per vulnerability category, producing `data/results/correlation_results.json` with adjusted p‑values. **Requirement**: Explicitly label non-significant adjusted p-values as 'not significant' in the output. (Dependency: T029a‑Exec)
- [ ] T029b‑Exec **Execute Correction**: Run correction. **Verification**: `data/results/correlation_results.json` must exist. (Dependency: T029b‑Impl)
- [ ] T029c‑Impl **Implement Correlation Report Generator**: Create `src/analysis/report_generator.py::generate_correlation_report()` that aggregates raw and corrected results into `data/results/correlation_report.json`. (Dependency: T029a‑Exec, T029b‑Exec)
- [ ] T029c‑Exec **Execute Report Generation**: Run generator. **Verification**: `data/results/correlation_report.json` must exist. (Dependency: T029c‑Impl)
- [ ] T030‑Impl **Implement Logistic Regression**: Add `fit_regression()` in `src/analysis/regression.py` using `statsmodels` GLM (logit) with all features plus one‑hot encoded language and cwe_category. Exclude `embedding_similarity_score` to avoid tautology. Compute McFadden's Pseudo R² and Nagelkerke adjusted R². **Output**: Save summary to `data/results/regression_summary.json` with keys: `coefficients`, `p_values`, `pseudo_r2`, `adjusted_r2`. (Dependency: T018d‑Exec, T013‑Exec, T026‑Exec)
- [ ] T030‑Exec **Execute Logistic Regression**: Run regression. **Verification**: `data/results/regression_summary.json` must exist. (Dependency: T030‑Impl)
- [ ] T031‑Impl **Implement McNemar's Test**: Add `run_mcnemar()` using `statsmodels.stats.contingency.mcnemar` to compare LLM vs. static analyzer predictions. Output `data/results/mcnemar_test.json`. (Dependency: T013‑Exec, T026‑Exec)
- [ ] T031‑Exec **Execute McNemar's Test**: Run test. **Verification**: `data/results/mcnemar_test.json` must exist. (Dependency: T031‑Impl)
- [ ] T032‑Impl **Implement Visualizer**: Create `src/analysis/visualizer.py` to generate plots (feature‑correlation heatmaps, ROC curves) saved under `data/results/visualizations/`. (Dependency: T029c‑Exec, T028‑Exec)
- [ ] T032‑Exec **Execute Visualizer**: Run visualizer. **Verification**: Plots must exist in `data/results/visualizations/`. (Dependency: T032‑Impl)
- [ ] T033‑Impl **Implement Final Report Generator**: Add `generate_final_report()` in `src/analysis/report_generator.py` that aggregates all metrics into `data/results/metrics.json` and updates `research.md` with a summary, including pseudo R² values and 'not significant' labels from T029b-Exec. (Dependency: T030‑Exec, T031‑Exec, T032‑Exec, T029b‑Exec)
- [ ] T033‑Exec **Execute Final Report Generation**: Run generator. **Verification**: `data/results/metrics.json` must exist and `research.md` must be updated. (Dependency: T033‑Impl)
- [X] T034 **Implement Regression Tests**: Add `tests/unit/test_regression.py` to validate statistical outputs on synthetic data. (Dependency: T030‑Exec, T031‑Exec)

## Phase 7: Sensitivity Analysis (FR‑011) – Independent Re‑Labeling Protocol

- [ ] T036‑Impl **Acquire Independent Secondary Labeled Dataset**: Download a vetted secondary ground-truth dataset (e.g., a curated subset of the "CVE‑Annotated Code" corpus) containing **exactly n=100** samples. **Protocol**: Apply a re-labeling protocol (manual review or secondary model consensus) to generate independent labels. Save to `data/secondary/independent_labels.csv`. (Dependency: None)
- [ ] T036‑Exec **Ingest Independent Labels**: Load `independent_labels.csv`, map to existing `snippet_id`s, and produce `data/processed/independent_labels.parquet`. **Verification**: Mapping log written to `data/logs/independent_label_ingest.json`. (Dependency: T036‑Impl)
- [ ] T036b‑Impl **Compute Sensitivity Metrics**: Using the original LLM predictions (`llm_predictions_raw.json`) and the independent labels, recompute precision, recall, and F1; write a comparative report to `data/results/sensitivity_analysis.json` with keys `original_metrics`, `revised_metrics`, `delta`, `conclusion`. (Dependency: T013‑Exec, T036‑Exec)
- [ ] T036b‑Exec **Execute Sensitivity Analysis**: Run the computation. **Verification**: `data/results/sensitivity_analysis.json` must exist and contain the required keys. (Dependency: T036b‑Impl)

## Phase 8: Versioning & Reporting (Priority P3)

- [ ] T038‑Impl **Implement Artifact Hasher**: Create `src/utils/hash_artifacts.py` to checksum all files in `data/processed/` and `data/results/`. (Dependency: All previous result‑producing tasks)
- [ ] T038‑Exec **Run Artifact Hasher**: Execute hasher. **Verification**: `data/logs/artifact_hashes.json` must exist. (Dependency: T038‑Impl)
- [ ] T039‑Impl **Implement State Updater**: Create `src/utils/state_updater.py` to update `state/projects/PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml` with new hashes and pipeline completion status. (Dependency: T038‑Exec)
- [ ] T039‑Exec **Update State File**: Run updater. **Verification**: State file must be updated. (Dependency: T039‑Impl)
- [ ] T040‑Impl **Implement Research Report Generator**: Create `src/analysis/report_generator.py::generate_research_report()` that writes the final research narrative to `research.md`. (Dependency: T033‑Exec, T036b‑Exec)
- [ ] T040‑Exec **Generate Research Report**: Execute report generator. **Verification**: `research.md` must be updated. (Dependency: T040‑Impl)

## Phase 9: Polish & Cross‑Cutting Concerns

- [ ] T041 **Documentation Updates**: Revise `README.md` and `docs/` to reflect the final pipeline, usage instructions, and reproducibility notes. (Dependency: All phases)
- [ ] T042 **Code Cleanup & Refactoring**: Run `ruff` and `black` across the codebase, address any linting warnings, and ensure all modules have type hints. (Dependency: T003‑Exec)
- [ ] T043 **Performance Optimizations**: Profile the inference and feature extraction steps; adjust batch sizes or enable optional GPU offload for embedding generation if a free Kaggle GPU is available. (Dependency: T004a‑Exec, T019b‑Exec)
- [ ] T044 **Additional Unit Tests**: Expand test coverage for edge cases (large snippets truncation, malformed code handling). (Dependency: T018‑Impl, T013f‑Impl)

## Phase 10: Review Resolution & Data Integrity (Revision Pass)

**Purpose**: Address specific reviewer concerns regarding data sourcing, failure modes, and streaming capabilities.

- [ ] T046‑Impl [P] **Implement Streaming Data Processor**: Create `src/data/stream_processor.py` that uses `datasets.load_dataset(..., streaming=True)` for large datasets (e.g., NVD or large code corpora). Implement chunked processing to accumulate statistics (e.g., embedding means) without loading the full dataset into RAM. (FR‑001, SC‑005)
- [ ] T046‑Exec [P] **Execute Streaming Test**: Run the streaming processor on a large subset of the NVD feed; verify memory usage stays within acceptable system limits and results are computed correctly. (Dependency: T046‑Impl)
- [ ] T047‑Impl [P] **Implement Sample Size Declaration**: Update `src/data/ingest.py` to explicitly log the `sample_size`, `sampling_method` (e.g., "stratified"), and `seed` in `data/logs/sampling_metadata.json` whenever a subset is used. **Source**: Read values from `data/logs/stratification_verification.json` (output of T012b‑1‑Exec). (FR‑001, Constitution II)
- [ ] T047‑Exec [P] **Verify Sampling Metadata**: Execute the sampling pipeline and verify `data/logs/sampling_metadata.json` contains the exact sample count and method. (Dependency: T047‑Impl)

---

### Dependencies & Execution Order Summary

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **User Stories (Phases 3‑5)** → **Statistical Analysis (Phase 6)** → **Sensitivity (Phase 7)** → **Versioning & Reporting (Phase 8)** → **Polish (Phase 9)** → **Review Resolution (Phase 10)**
- All tasks now have a single, deterministic ordering; duplicate IDs removed; per‑sample time budget and truncation are enforced; independent reference set and independent re‑labeling protocol are verified before use; manual blocks eliminated; orchestrator runs the entire DAG.
- **Phase 10** tasks are critical for passing the "Real Data" and "No Fabrication" gates and must be completed before any final execution.