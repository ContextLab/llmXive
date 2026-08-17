# Tasks: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [ ] T001a-Impl [P] **Implement Directory Tree Generator**: Create `src/utils/dir_tree_gen.py`. **Logic**: Script must traverse the repository root, identify all directories and files, and output a JSON object representing the tree structure. **Output**: The script must be executable and ready for T001a-Exec. (Dependency: None)
- [ ] T001a-Exec [P] **Create Project Directory Structure**: Execute `src/utils/dir_tree_gen.py` to generate the full directory tree as defined in `plan.md` (`src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `state/`, `data/logs/`, `contracts/`). **Verification**: The script must output `data/logs/dir_tree.json`. **Task Complete Definition**: Task is only complete when `data/logs/dir_tree.json` exists, is valid JSON, and matches the created structure. (FR-001, Plan Project Structure)
- [ ] T001b-Impl [P] **Implement Core Files Generator**: Create `src/utils/core_files_gen.py`. **Logic**: Script must create `__init__.py` in all `src/` subdirectories, `.gitignore`, and `requirements.txt` (if not present), then compute checksums for all created files. **Output**: The script must be executable and ready for T001b-Exec. (Dependency: None)
- [ ] T001b-Exec [P] **Create Core Files**: Execute `src/utils/core_files_gen.py`. **Verification**: The script must output `data/logs/core_files.json` listing the created files and their checksums. **Task Complete Definition**: Task is only complete when `data/logs/core_files.json` exists and lists all created files. (FR-001, Plan Project Structure)
- [X] T002 Initialize Python project with `requirements.txt` (transformers, scikit-learn, pandas, tree-sitter, networkx, requests, pyyaml, bitsandbytes, sentence-transformers, pytest, radon, statsmodels)
- [ ] T003-Impl [P] **Implement Linting Check Script**: Create `src/utils/linting_check.py`. **Logic**: Script must run `ruff check` and `black --check` on `src/` and capture the output to a JSON log. **Output**: The script must be executable and ready for T003-Exec. (Dependency: None)
- [ ] T003-Exec [P] **Configure Linting & Formatting**: Execute `src/utils/linting_check.py` after configuring `ruff` and `black` in `pyproject.toml`. **Verification**: The script must output `data/logs/linting_config.json`. **Task Complete Definition**: Task is only complete when `data/logs/linting_config.json` exists and contains the validation output. (FR-001, Plan Project Structure)
- [X] T004 [P] Implement `src/utils/config.py` with seeds, paths, runtime thresholds (hourly limit, gigabyte RAM cap), and the **deterministic, alphabetically ordered** list of candidate LLMs. (FR-002, SC-005)
- [ ] T004b [P] **CPU‑Only Pre‑Flight Check**: Create `src/utils/cpu_check.py`. **Logic**: Script must check `torch.cuda.is_available()`. If `True`, write `{"status": "GPU_DETECTED", "abort": true}` to `data/logs/cpu_check.json` and exit with code 1. If `False`, write `{"status": "CPU_ONLY", "abort": false}` and exit 0. **Constraint**: This task runs BEFORE T004a-Impl. If it exits 1, the pipeline halts. (FR-002, SC-005)
- [ ] T004a-Impl [P] **Implement Model Selection Logic**: Create `src/utils/model_selector.py`. **Logic**: Iterate through the **alphabetically ordered candidate list** (from T004). For each model, perform a capability check by running inference on `int x = 0;` (C), `x = 1` (Python), and `var y = 1;` (JS). **Constraint**: Assume CPU-only environment (enforced by T004b). Select the first valid model that completes within the time budget. **Output**: Log the selected model to `data/logs/model_selection.json` upon execution. **Dependency**: T004. (FR-002)
- [ ] T004a-Exec [P] **Execute Model Selection**: Execute `src/utils/model_selector.py`. **Verification**: The script must output `data/logs/model_selection.json`. **Task Complete Definition**: Task is only complete when `data/logs/model_selection.json` exists and lists the selected model. (Dependency: T004b, T004a-Impl). (FR-002)
- [X] T004d [P] **Dynamic Batch Sizing Implementation**: Implement `src/utils/batch_sizer.py` to calculate optimal batch size based on current RAM usage. **Logic**: Implement a function `calculate_batch_size(available_ram_gb, model_memory_gb)` that returns a batch size ensuring total memory < 7GB. **Verification**: Unit test `tests/unit/test_batch_sizer.py` with mock RAM values. (FR-002, SC-005)
- [X] T005 [P] Implement `src/utils/validate_urls.py` to validate dataset URLs against `research.md` manifest (Constitution II). **Constraint**: This task MUST complete before T010a, T011, T011b start.
- [X] T005-exec [P] **Execute URL Validation**: Execute `src/utils/validate_urls.py` against `research.md` before data ingestion. **Verification**: Update `state/projects/PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml` with the validation result (PASS/FAIL). **Constraint**: If FAIL, abort pipeline. (Dependency: T005, T010a, T011, T011b)
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
- [X] T013d [P] **Memory Monitor Implementation**: Implement `src/utils/memory_monitor.py` to track runtime memory usage. **Logic**: Expose a context manager or utility function to check RAM usage and trigger batch size reduction if a high threshold is approached. **Dependency**: T004 -> T004c & T013d (Parallel). (FR-002, SC-005)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Zero‑Shot Vulnerability Detection Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest dataset, run zero‑shot LLM inference, and generate correctness flags against ground truth.

**Independent Test**: Process a small, fixed subset of known vulnerable and known safe snippets, verifying structured JSON output with predicted label, confidence, and `is_correct` flag.

### Implementation for User Story 1

- [ ] T015-Impl [P] **Implement Orchestrator**: Create `src/main.py`. **Logic**: Implement a DAG runner that resolves task dependencies and executes them in order. The script must import and call downstream tasks (T010a-Exec, T011-Exec, T011b-Exec, T012-Exec, T012b-Exec, T012b-1-Exec, T013-Exec, T013c-Exec, T013-Verify-Exec, T018d-Exec, T024-Exec, T026-Exec, T028-Exec, T029a-Exec, T029b-Exec, T030-Exec, T031-Exec) based on the dependency graph. **Output**: The script must write `data/logs/orchestration_log.json` upon completion, containing the execution status of each task. **Dependency**: T004a-Exec, T009b, T010a-Impl, T011-Impl, T011b-Impl, T012-Impl, T012b-Impl, T012b-1-Impl, T013-Impl, T013c-Impl, T013d. (FR-001)
- [ ] T015-Exec [P] **Execute Orchestrator**: Execute `src/main.py`. **Verification**: The script must output `data/logs/orchestration_log.json`. **Task Complete Definition**: Task is only complete when `data/logs/orchestration_log.json` exists and contains valid execution logs. (Dependency: T015-Impl, T010a-Exec, T011-Exec, T011b-Exec, T012-Exec, T012b-Exec, T012b-1-Exec, T013-Exec, T013c-Exec, T013-Verify-Exec, T018d-Exec, T024-Exec, T026-Exec, T028-Exec, T029a-Exec, T029b-Exec, T030-Exec, T031-Exec). (Dependency: T015-Impl)
- [ ] T010a-Impl [P] **Implement VulDeePecker Downloader**: Create `src/data/ingest.py` function `download_vuldeepecker()`. **Logic**: Fetch the **VulDeePecker dataset** (Python) using `datasets.load_dataset('VulDeePecker/VulDeePecker')` (verified ID) OR fallback `wget https://raw.githubusercontent.com/vuldeepecker/vuldeepecker/main/data/vuldeepecker_python.csv`. **Constraint**: This is the PRIMARY source for Python as per FR-001. Save raw files to `data/raw/`. **Output**: Script ready for T010a-Exec. (Dependency: None)
- [ ] T010a-Exec [P] **Download VulDeePecker Dataset (Python)**: Execute `src/data/ingest.py` function `download_vuldeepecker()`. **Verification**: Ensure files are downloaded successfully. **Task Complete Definition**: Task is only complete when `data/raw/vuldeepecker_*` files exist. (FR-001, Plan Complexity Tracking)
- [ ] T010a-1 [US1] **Checksum VulDeePecker**: Generate checksums for files downloaded in T010a and update `data/raw/checksums.json`. **Dependency**: T010a-Exec. (FR-001)
- [ ] T011a [US1] **Map JSVulnDB Schema to BigVul**: Generate a mapping document `data/logs/jsvulndb_bigvul_mapping.json` that explicitly maps JSVulnDB fields (e.g., `type`) to BigVul schema fields (e.g., `ground_truth_category`). **Constraint**: This document is a mandatory input for T011 to ensure traceability to FR-001. (FR-001, Plan Complexity Tracking)
- [ ] T011-Impl [P] **Implement JSVulnDB Downloader**: Create `src/data/ingest.py` function `download_jsvulndb()`. **Logic**: Fetch the **JSVulnDB dataset** (substituted for BigVul per Plan Risks & Mitigations: JSVulnDB contains the same vulnerability categories for JavaScript as BigVul). Extract the **JavaScript subset** (Filter where `language == JS`). **Constraint**: This is the PRIMARY source for JavaScript as per Plan. Use the mapping from T011a to align schemas. Save raw files to `data/raw/`. **Output**: Script ready for T011-Exec. (Dependency: T011a)
- [ ] T011-Exec [P] **Download JSVulnDB Dataset (JavaScript)**: Execute `src/data/ingest.py` function `download_jsvulndb()`. **Verification**: Ensure files match the checksums in `data/raw/checksums.json`. **Task Complete Definition**: Task is only complete when `data/raw/jsvulndb_js_*` files exist and `data/raw/checksums.json` is updated. (FR-001, Plan Complexity Tracking)
- [ ] T011b-Impl [P] **Implement NIST Juliet Downloader**: Create `src/data/ingest.py` function `download_juliet()`. **Logic**: Fetch the **official NIST Juliet repository** using `git clone` and extract the **C/C++ (C focus) subset** from `c_testcases/`. **Constraint**: This is the PRIMARY source for C as per FR-001. Save raw files to `data/raw/`. **Output**: Script ready for T011b-Exec. (Dependency: None)
- [ ] T011b-Exec [P] **Download NIST Juliet Dataset (C Subset)**: Execute `src/data/ingest.py` function `download_juliet()`. **Verification**: Ensure files match the checksums in `data/raw/checksums.json`. **Task Complete Definition**: Task is only complete when `data/raw/juliet_c_*` files exist and `data/raw/checksums.json` is updated. (FR-001, Plan Complexity Tracking)
- [ ] T012-Impl [P] **Implement Parser**: Create `src/data/ingest.py` function `parse_datasets()`. **Logic**: Parse raw datasets (VulDeePecker, JSVulnDB JS, NIST Juliet C) into `CodeSnippet` entities. **Mapping**: Explicitly map columns:
 - **VulDeePecker**: `lang` -> `language`, `cwe` -> `ground_truth_category`
 - **JSVulnDB**: `language` -> `language`, `type` -> `ground_truth_category` (using T011a mapping)
 - **NIST Juliet**: `lang` -> `language`, `testcase` -> `ground_truth_category`
 Output `data/processed/parsed_snippets.parquet`. **Constraint**: Exclude samples missing `ground_truth_label` from accuracy calculation, **BUT** log these dropped samples to `data/logs/dropped_samples.json`. **Output**: Script ready for T012-Exec. (Dependency: T010a-Exec, T011-Exec, T011b-Exec)
- [ ] T012-Exec [P] **Parse Raw Data**: Execute `src/data/ingest.py` function `parse_datasets()`. **Verification**: Ensure `data/processed/parsed_snippets.parquet` exists. **Task Complete Definition**: Task is only complete when `data/processed/parsed_snippets.parquet` exists and contains valid `CodeSnippet` entities. (Dependency: T012-Impl)
- [ ] T012b-Impl [P] **Implement Stratified Sampler**: Create `src/data/ingest.py` function `sample_stratified()`. **Logic**: Perform stratified sampling (≤5,000 samples) by language and vulnerability category using `sklearn.model_selection.StratifiedShuffleSplit` with `random_state=42` on `data/processed/parsed_snippets.parquet`. **Output**: `data/processed/sampled_snippets_temp.parquet`. **Output**: Script ready for T012b-Exec. (Dependency: T012-Exec)
- [ ] T012b-Exec [P] **Perform Stratified Sampling**: Execute `src/data/ingest.py` function `sample_stratified()`. **Verification**: Ensure `data/processed/sampled_snippets_temp.parquet` exists. **Task Complete Definition**: Task is only complete when `data/processed/sampled_snippets_temp.parquet` exists. (Dependency: T012b-Impl)
- [ ] T012b-1-Impl [P] **Implement Verification & Cap Enforcer**: Create `src/data/ingest.py` function `verify_stratification()`. **Logic**: Verify that the sampling logic in T012b preserves the proportional representation of *both* language and vulnerability category across the *combined* dataset (Python, C, JS). Compute distribution stats and log to `data/logs/stratification_verification.json`. **Constraint**: **Assert that `len(df) <= 5000`** after sampling; if the split exceeds the cap, reduce the split ratio or sample size until the cap is met. **Output**: Final `data/processed/sampled_snippets.parquet`. **Abort** if bias exceeds 5%. **Output**: Script ready for T012b-1-Exec. (Dependency: T012b-Exec)
- [ ] T012b-1-Exec [P] **Verify Global Stratification & Enforce Cap**: Execute `src/data/ingest.py` function `verify_stratification()`. **Verification**: Ensure `data/processed/sampled_snippets.parquet` exists and `data/logs/stratification_verification.json` shows pass. **Task Complete Definition**: Task is only complete when `data/processed/sampled_snippets.parquet` exists and `data/logs/stratification_verification.json` indicates success. (Dependency: T012b-1-Impl)
- [ ] T013-Impl [P] **Implement Zero‑Shot Inference Service**: Create `src/models/llm_inference.py`. **Logic**: Load the selected model (from T004a-Exec) in low‑bit quantized CPU mode. Enforce zero‑shot prompt. Parse responses into standard categories using the **Standard Category Map**: `SQLi`, `XSS`, `Buffer Overflow`, `RCE`, `Path Traversal`, `Command Injection`, `None`. **Mapping Logic**: Use regex to map LLM output (e.g., "sql injection" -> "SQLi", "buffer overflow" -> "Buffer Overflow"). Handle "uncertain" mapping to "None". Record `inference_time_ms` per sample. **Constraint**: If the primary model exceeds the time budget, **automatically switch to a smaller fallback model** (e.g., TinyLlama) to ensure the [deferred] sample cap is met. **Circuit Breaker**: If the fallback model also fails to meet the time limit, **ABORT PIPELINE** with exit code 1. **Do NOT skip samples**. Use `MemoryMonitor` (from T013d in Phase 1) and **Dynamic Batch Sizer** (T004d) to respect RAM limits. **Write raw per-sample timing data to `data/results/runtime_raw.json`**. **Output**: Script ready for T013-Exec. (Dependency: T004a-Exec, T004b, T012b-1-Exec, T013d, T004d)
- [ ] T013-Exec [P] **Execute Zero‑Shot Inference**: Execute `src/models/llm_inference.py`. **Verification**: Ensure `data/results/runtime_raw.json` exists. **Task Complete Definition**: Task is only complete when `data/results/runtime_raw.json` exists and contains valid timing data. (Dependency: T013-Impl)
- [ ] T013c-Impl [P] **Implement Runtime Aggregator**: Create `src/utils/runtime_analyzer.py` function `aggregate_runtime()`. **Logic**: Consume `data/results/runtime_raw.json`. Compute total runtime, average per-sample time, and max per-sample time. Write structured summary to `data/results/runtime_metrics.json` for SC-005 verification. **Output**: Script ready for T013c-Exec. (Dependency: T013-Exec)
- [ ] T013c-Exec [P] **Aggregate Runtime Metrics**: Execute `src/utils/runtime_analyzer.py` function `aggregate_runtime()`. **Verification**: Ensure `data/results/runtime_metrics.json` exists. **Task Complete Definition**: Task is only complete when `data/results/runtime_metrics.json` exists. (Dependency: T013c-Impl)
- [ ] T013-Verify-Impl [P] **Implement Verification Logic**: Create `src/utils/runtime_analyzer.py` function `verify_runtime()`. **Logic**: Read `data/results/runtime_metrics.json` and `data/processed/sampled_snippets.parquet`. **Constraint**: Assert `len(df) == 5000` (or max available if <5000) AND `total_runtime <= 6h`. If either fails, **ABORT PIPELINE**. **Output**: `data/results/runtime_verification.json` with `pass: true/false` and `message`. **Output**: Script ready for T013-Verify-Exec. (Dependency: T013c-Exec)
- [ ] T013-Verify-Exec [P] **Verify Sample Cap & Runtime**: Execute `src/utils/runtime_analyzer.py` function `verify_runtime()`. **Verification**: Ensure `data/results/runtime_verification.json` exists and shows pass. **Task Complete Definition**: Task is only complete when `data/results/runtime_verification.json` exists and indicates success. (Dependency: T013-Verify-Impl)
- [ ] T012a-1 [US1] **Re-balance & Power Report**: **Conditional Task**: If T013-Verify fails (e.g., max available < 5000), calculate the 'effective N' and 'power loss' and log to `data/results/power_analysis.json`. **Note**: This task does NOT trigger a re-run of T013; it reports the power loss. (Dependency: T013-Verify-Exec)
- [ ] T017 [US1] Implement `tests/unit/test_llm_inference.py` to verify batch processing and memory footprint on a mock dataset.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Structural, Semantic & Embedding Feature Extraction (Priority: P2)

**Goal**: Extract structural (AST), semantic (taint API), and embedding features for every code snippet.

**Independent Test**: Run parser on a single file with known complexity and verify JSON output contains non‑null numeric values for AST depth, complexity, and embedding score.

### Implementation for User Story 2

- [ ] T018-Impl [P] **Implement Feature Extractor**: Create `src/data/feature_extractor.py`. **Logic**: Use `tree-sitter` to compute **AST Depth, Node Count, Cyclomatic Complexity** (via `radon`), and **Semantic Metrics**. **Semantic Logic**: Count occurrences of **Taint-Source APIs**: `eval`, `exec`, `system`, `popen`, `subprocess`, `os.system`, `shell`. Count occurrences of **Sanitization Functions**: `escape`, `sanitize`, `quote`, `filter`, `htmlspecialchars`. Consume `data/processed/sampled_snippets.parquet` from T012b-1-Exec. Output `data/processed/structural_features.json` (merged). **Constraint**: Run sequentially to avoid race conditions. **Error Handling**: Log malformed code snippets as null/invalid and continue, writing details to `data/logs/feature_extractor_errors.json`. **Output**: Script ready for T018-Exec. (Dependency: T012b-1-Exec, T008b)
- [ ] T018-Exec [P] **Execute Feature Extraction**: Execute `src/data/feature_extractor.py`. **Verification**: Ensure `data/processed/structural_features.json` exists. **Task Complete Definition**: Task is only complete when `data/processed/structural_features.json` exists. (Dependency: T018-Impl)
- [ ] T019a-Impl [P] **Implement NVD Downloader**: Create `src/data/ingest.py` function `download_nvd()`. **Logic**: Retrieve the **NVD JSON Feeds** (external reference set) using `wget https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-modified.json.gz`. **Constraint**: This is the source for the reference set, **NOT BigVul** (which is the JS training set). Save raw files to `data/raw/vul_pattern_corpus.json`. Verify checksum against `data/raw/checksums.json`. **Output**: Script ready for T019a-Exec. (Dependency: None)
- [ ] T019a-Exec [P] **Download NVD Corpus**: Execute `src/data/ingest.py` function `download_nvd()`. **Verification**: Ensure `data/raw/vul_pattern_corpus.json` exists. **Task Complete Definition**: Task is only complete when `data/raw/vul_pattern_corpus.json` exists. (Dependency: T019a-Impl)
- [ ] T019b-Impl [P] **Implement Pattern Curation**: Create `src/data/feature_extractor.py` function `curate_patterns()`. **Logic**: Filter the NVD corpus for vulnerability keywords: `injection`, `overflow`, `xss`, `rce`, `sqli`, `command injection`, `path traversal`, `buffer overflow`. **Ensure** this set is distinct from the training data. **Generate embeddings** for this filtered set using `sentence-transformers/all-MiniLM-L6-v2` and save to `data/processed/reference_patterns.json`. **This filtered set serves as the external, fixed reference set for FR-004**. **Output**: Script ready for T019b-Exec. (Dependency: T019a-Exec)
- [ ] T019b-Exec [P] **Execute Pattern Curation**: Execute `src/data/feature_extractor.py` function `curate_patterns()`. **Verification**: Ensure `data/processed/reference_patterns.json` exists. **Task Complete Definition**: Task is only complete when `data/processed/reference_patterns.json` exists. (Dependency: T019b-Impl)
- [ ] T019d-Impl [P] **Implement Independence Check**: Create `src/data/feature_extractor.py` function `check_independence()`. **Logic**: Compare IDs and content in `data/processed/reference_patterns.json` against training datasets (VulDeePecker, JSVulnDB, NIST Juliet). **If any overlap is detected, LOG WARNING and trigger T019e (Fallback)**. **Do NOT abort**. This satisfies the plan's independence requirement while ensuring feasibility. **Dependency**: T019b-Exec, T010a-Exec, T011-Exec, T011b-Exec. **Output**: Script ready for T019d-Exec.
- [ ] T019d-Exec [P] **Execute Independence Check**: Execute `src/data/feature_extractor.py` function `check_independence()`. **Verification**: Ensure `data/logs/independence_check.json` exists and indicates pass or fallback trigger. **Task Complete Definition**: Task is only complete when `data/logs/independence_check.json` exists. (Dependency: T019d-Impl)
- [ ] T019e-Impl [P] **Implement Fallback Reference Set Generator**: Create `src/data/feature_extractor.py` function `generate_fallback()`. **Trigger**: If T019d detects overlap. **Action**: Fetch the **CVE Details JSON** (real-world, distinct from NVD/Training) as a fallback reference set. Filter for vulnerability keywords and generate embeddings. Save to `data/processed/reference_patterns_fallback.json`. **Constraint**: This fallback MUST be real data, not synthetic. **Output**: Script ready for T019e-Exec. (Dependency: T019d-Exec)
- [ ] T019e-Exec [P] **Execute Fallback Generation**: Execute `src/data/feature_extractor.py` function `generate_fallback()`. **Verification**: Ensure `data/processed/reference_patterns_fallback.json` exists. **Task Complete Definition**: Task is only complete when `data/processed/reference_patterns_fallback.json` exists. (Dependency: T019e-Impl)
- [ ] T019c-Impl [P] **Implement Similarity Computation**: Create `src/data/feature_extractor.py` function `compute_similarity()`. **Logic**: For each code snippet (from `data/processed/sampled_snippets.parquet` produced by T012b-1-Exec), compute cosine similarity against the **reference embeddings** (from T019b-Exec or T019e-Exec) and store the maximum similarity as `embedding_similarity_score` in `FeatureVector`. **Logic**: If T019d detected overlap, use T019e-Exec output; otherwise, use T019b-Exec output. Log progress to `data/logs/similarity_computation.json`. **Output**: Script ready for T019c-Exec. (Dependency: T019d-Exec, T019e-Exec, T012b-1-Exec, T008b)
- [ ] T019c-Exec [P] **Execute Similarity Computation**: Execute `src/data/feature_extractor.py` function `compute_similarity()`. **Verification**: Ensure `data/logs/similarity_computation.json` exists. **Task Complete Definition**: Task is only complete when `data/logs/similarity_computation.json` exists. (Dependency: T019c-Impl)
- [ ] T018d-Impl [P] **Implement Feature Pipeline**: Create `src/data/feature_extractor.py` function `run_pipeline()`. **Logic**: Run structural, semantic, and similarity extraction on the full dataset (from T012b-1-Exec), producing `data/processed/features.csv` (including `language`, and all metric columns). **Dependencies**: T018-Exec, T019c-Exec, T019d-Exec, T012b-1-Exec, T008b (Must validate FeatureVector schema before execution). **Output**: Script ready for T018d-Exec.
- [ ] T018d-Exec [P] **Execute Feature Pipeline**: Execute `src/data/feature_extractor.py` function `run_pipeline()`. **Verification**: Ensure `data/processed/features.csv` exists. **Task Complete Definition**: Task is only complete when `data/processed/features.csv` exists. (Dependency: T018d-Impl)
- [ ] T021 [US2] Add error handling in `feature_extractor.py` to log malformed code snippets as null/invalid and continue processing remaining batches, writing details to `data/logs/feature_extractor_errors.json`.
- [ ] T023 [US2] Implement `tests/unit/test_feature_extractor.py` to verify metric calculation on known test cases (e.g., deeply nested function).

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

---

## Phase 4: User Story 4 - Static Analyzer Baseline Comparison (Priority: P2)

**Goal**: Execute static analysis tools (Bandit, cppcheck) on the dataset to establish a baseline for comparison.

**Independent Test**: Run Bandit on a known vulnerable Python script and verify it flags the vulnerability and outputs a structured result file.

### Implementation for User Story 4

- [ ] T024-Impl [P] **Implement Static Analyzer Wrapper**: Create `src/models/static_analyzer.py`. **Logic**: Wrap `bandit` (flags: `-r -ll -ii`) for Python snippets and `cppcheck` (flags: `--enable=all --inconclusive --error-exitcode=1`) for C snippets. **Output**: Script ready for T024-Exec.
- [ ] T024-Exec [P] **Execute Static Analyzer Wrapper**: Run `src/models/static_analyzer.py` to verify tool availability and basic parsing. **Verification**: Ensure script runs without error. **Task Complete Definition**: Task is only complete when the script executes successfully. (Dependency: T024-Impl)
- [ ] T025-Impl [P] **Implement Static Analyzer Parser**: Create `src/models/static_analyzer.py` function `parse_results()`. **Logic**: Add parsing logic to convert static analyzer output into `PredictionResult` schema (including `is_correct` flag based on ground truth). **Output**: Script ready for T025-Exec. (Dependency: T024-Impl)
- [ ] T025-Exec [P] **Execute Static Analyzer Parser**: Run `src/models/static_analyzer.py` function `parse_results()` on a sample. **Verification**: Ensure output matches `PredictionResult` schema. **Task Complete Definition**: Task is only complete when sample output is valid. (Dependency: T025-Impl)
- [ ] T026-Impl [P] **Implement Static Analysis Pipeline**: Create `src/data/static_analysis_pipeline.py`. **Logic**: Run analyzers on the full dataset and save `data/processed/static_predictions.csv`. **Output**: Script ready for T026-Exec. (Dependency: T025-Exec)
- [ ] T026-Exec [P] **Execute Static Analysis Pipeline**: Run `src/data/static_analysis_pipeline.py`. **Verification**: Ensure `data/processed/static_predictions.csv` exists. **Task Complete Definition**: Task is only complete when `data/processed/static_predictions.csv` exists. (Dependency: T026-Impl)
- [ ] T027 [US4] Implement `tests/unit/test_static_analyzer.py` to verify correct flagging of known vulnerabilities in Python and C.

**Checkpoint**: At this point, User Story 4 should be fully functional and testable independently

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Compute metrics, correlations, regression, and McNemar's test to derive scientific findings.

**Independent Test**: Provide a synthetic CSV of features and labels; verify script outputs correlation matrix, regression summary, and McNemar's test statistic.

### Implementation for User Story 3

- [ ] T028-Impl [P] **Implement Metrics Calculator**: Create `src/analysis/metrics.py`. **Logic**: Calculate Precision, Recall, F1, and ROC‑AUC per category and model. **Output**: Script ready for T028-Exec. (Dependency: T015-Exec, T026-Exec)
- [ ] T028-Exec [P] **Execute Metrics Calculation**: Run `src/analysis/metrics.py`. **Verification**: Ensure `data/results/metrics_raw.json` exists. **Task Complete Definition**: Task is only complete when `data/results/metrics_raw.json` exists. (Dependency: T028-Impl)
- [ ] T029a-Impl [P] **Implement Correlation Analysis**: Create `src/analysis/regression.py` function `compute_correlations()`. **Logic**: Compute Pearson r between each feature and `is_correct`. Output `data/results/correlation_raw.json`. **Output**: Script ready for T029a-Exec. (Dependency: T018d-Exec, T015-Exec, T026-Exec)
- [ ] T029a-Exec [P] **Execute Correlation Analysis**: Run `src/analysis/regression.py` function `compute_correlations()`. **Verification**: Ensure `data/results/correlation_raw.json` exists. **Task Complete Definition**: Task is only complete when `data/results/correlation_raw.json` exists. (Dependency: T029a-Impl)
- [ ] T029b-Impl [P] **Implement Multiple-Comparison Correction**: Create `src/analysis/regression.py` function `apply_correction()`. **Logic**: Apply Bonferroni correction **per vulnerability category** (family-wise error control for each category's set of features). Output `data/results/correlation_results.json` with adjusted p‑values and a flag for non‑significant results. **Output**: Script ready for T029b-Exec. (Dependency: T029a-Exec)
- [ ] T029b-Exec [P] **Execute Correction**: Run `src/analysis/regression.py` function `apply_correction()`. **Verification**: Ensure `data/results/correlation_results.json` exists. **Task Complete Definition**: Task is only complete when `data/results/correlation_results.json` exists. (Dependency: T029b-Impl)
- [ ] T029c-Impl [P] **Implement Correlation Report Generator**: Create `src/analysis/report_generator.py` function `generate_correlation_report()`. **Logic**: Aggregate raw and corrected results into a final report. **Output**: Script ready for T029c-Exec. (Dependency: T029a-Exec, T029b-Exec)
- [ ] T029c-Exec [P] **Execute Report Generation**: Run `src/analysis/report_generator.py` function `generate_correlation_report()`. **Verification**: Ensure `data/results/correlation_report.json` exists. **Task Complete Definition**: Task is only complete when `data/results/correlation_report.json` exists. (Dependency: T029c-Impl)
- [ ] T030-Impl [P] **Implement Logistic Regression**: Create `src/analysis/regression.py` function `fit_regression()`. **Logic**: Fit a GLM (logit) using `statsmodels` to predict `is_correct` from all features **including `language` (one-hot encoded) and `cwe_category` (one-hot encoded) to control for confounding**, **excluding `embedding_similarity_score` (to prevent tautology)**. Compute **McFadden's Pseudo R²** AND **Adjusted R² using the Nagelkerke method**. **Requirement**: Explicitly report **McFadden's Pseudo R²** as the primary metric for the SC-002 (>0.10) check. **Output**: Save the fitted model coefficients and summary statistics to `data/results/regression_summary.json` (do NOT save the model object). **Output**: Script ready for T030-Exec. (Dependency: T018d-Exec, T015-Exec, T026-Exec)
- [ ] T030-Exec [P] **Execute Logistic Regression**: Run `src/analysis/regression.py` function `fit_regression()`. **Verification**: Ensure `data/results/regression_summary.json` exists. **Task Complete Definition**: Task is only complete when `data/results/regression_summary.json` exists. (Dependency: T030-Impl)
- [ ] T031-Impl [P] **Implement McNemar's Test**: Create `src/analysis/regression.py` function `run_mcnemar()`. **Logic**: Use `statsmodels.stats.contingency.mcnemar` (exact binomial) to compare LLM vs. static analyzer predictions. Output `data/results/mcnemar_test.json`. **Output**: Script ready for T031-Exec. (Dependency: T015-Exec, T026-Exec)
- [ ] T031-Exec [P] **Execute McNemar's Test**: Run `src/analysis/regression.py` function `run_mcnemar()`. **Verification**: Ensure `data/results/mcnemar_test.json` exists. **Task Complete Definition**: Task is only complete when `data/results/mcnemar_test.json` exists. (Dependency: T031-Impl)
- [ ] T032-Impl [P] **Implement Visualizer**: Create `src/analysis/visualizer.py`. **Logic**: Generate plots for feature correlations and ROC curves, saved under `data/results/visualizations/`. **Output**: Script ready for T032-Exec. (Dependency: T029c-Exec, T028-Exec)
- [ ] T032-Exec [P] **Execute Visualizer**: Run `src/analysis/visualizer.py`. **Verification**: Ensure `data/results/visualizations/` contains plots. **Task Complete Definition**: Task is only complete when plots exist. (Dependency: T032-Impl)
- [ ] T033-Impl [P] **Implement Report Generator**: Create `src/analysis/report_generator.py` function `generate_final_report()`. **Logic**: Aggregate all metrics into `data/results/metrics.json` and draft a summary section in `research.md`. **Note**: Report `pseudo_r2_adjusted_nagelkerke` as "Adjusted R²" and `pseudo_r2_mcfadden` as "McFadden's Pseudo R²". **Output**: Script ready for T033-Exec. (Dependency: T030-Exec, T031-Exec, T032-Exec)
- [ ] T033-Exec [P] **Execute Final Report Generation**: Run `src/analysis/report_generator.py` function `generate_final_report()`. **Verification**: Ensure `data/results/metrics.json` exists and `research.md` is updated. **Task Complete Definition**: Task is only complete when `data/results/metrics.json` exists. (Dependency: T033-Impl)
- [ ] T034 [US3] Implement `tests/unit/test_regression.py` to verify statistical outputs on synthetic data.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase 6: Human Verification & Sensitivity Analysis (Priority: P3 - FR‑011)

**Goal**: Validate the impact of ground‑truth label noise on metrics using a real human‑verified subset.

### Implementation

- [ ] T036-Impl [P] **Implement Sensitivity Acquirer**: Create `src/data/sensitivity_acquirer.py`. **Logic**: Script must generate a `guidelines.md` for human reviewers and a `labeling_template.csv` (columns: `snippet_id`, `original_label`, `verified_label`, `reviewer_notes`) for the stratified subset (n=100). **Output**: The script must be executable and ready for T036a-Exec. (Dependency: None)
- [ ] T036-Exec [P] **Check for Verified Labels**: Execute `src/data/sensitivity_acquirer.py` function `check_labels()`. **Logic**: Check for the existence of `data/human_review/verified_labels.csv`. **If missing**: Log `human_review_required` status to `data/logs/sensitivity_status.json` and **trigger T036a-Exec** to initiate manual re-labeling. **If present**: Proceed to T036b-Exec. **Constraint**: This task MUST NOT abort the pipeline; it must always result in a report. (Dependency: T015-Exec, T036-Impl)
- [ ] T036a-Impl [P] **Implement Sensitivity Acquirer (Manual)**: Create `src/data/sensitivity_acquirer.py` function `prepare_manual_review()`. **Logic**: Generate `guidelines.md` and `labeling_template.csv` (columns: `snippet_id`, `original_label`, `verified_label`, `reviewer_notes`). **Output**: The script must be executable and ready for T036a-Exec. (Dependency: None)
- [ ] T036a-Exec [P] **Manual Re-labeling Protocol**: **Trigger**: If T036-Exec finds no verified labels. **Action**: **Execute `src/data/sensitivity_acquirer.py` function `prepare_manual_review()`** to prepare the re-labeling kit. **Mandatory**: A human reviewer MUST re-label the n=100 subset using the provided guidelines and template. **Constraint**: The pipeline **CANNOT PROCEED** to T036b-Exec or T036c-Exec until `data/human_review/verified_labels.csv` is manually populated by a human. **Do NOT** attempt to download a secondary dataset or use synthetic noise. **Output**: `data/results/sensitivity_analysis.json` with structure: `{ "original_metrics": {}, "revised_metrics": {}, "delta": {}, "conclusion": "" }`. (Dependency: T036-Exec, T036a-Impl)
- [ ] T036b-Impl [P] **Implement Verified Labels Ingestor**: Create `src/data/sensitivity_acquirer.py` function `ingest_verified_labels()`. **Logic**: Ingest `data/human_review/verified_labels.csv`. Validate its schema (`snippet_id`, `verified_label`). If the file is missing or invalid, **trigger T036a-Exec** (re-initiate manual labeling) instead of attempting recovery. **Output**: Script ready for T036b-Exec. (Dependency: T036a-Exec)
- [ ] T036b-Exec [P] **Ingest Verified Labels**: Execute `src/data/sensitivity_acquirer.py` function `ingest_verified_labels()`. **Verification**: Ensure `data/human_review/verified_labels.csv` is valid. **Task Complete Definition**: Task is only complete when the file is valid. (Dependency: T036b-Impl)
- [ ] T036c-Impl [P] **Implement Sensitivity Metrics Computation**: Create `src/data/sensitivity_acquirer.py` function `compute_sensitivity_metrics()`. **Logic**: Recompute precision, recall, and F1 using the new labels and write a comparison report to `data/results/sensitivity_analysis.json`. **Schema**: The report MUST include keys: `original_metrics` (dict), `revised_metrics` (dict), `delta` (dict), `conclusion` (string). **Constraint**: This task depends on T015-Exec (predictions) and T036b-Exec (verified labels). Log verification steps to `data/human_review/verification_log.json`. **Output**: Script ready for T036c-Exec. (Dependency: T036b-Exec, T015-Exec)
- [ ] T036c-Exec [P] **Compute Sensitivity Metrics**: Execute `src/data/sensitivity_acquirer.py` function `compute_sensitivity_metrics()`. **Verification**: Ensure `data/results/sensitivity_analysis.json` exists and contains the required keys. **Task Complete Definition**: Task is only complete when `data/results/sensitivity_analysis.json` exists. (Dependency: T036c-Impl)
- [ ] T037 [P] Output final sensitivity report `data/results/sensitivity_analysis.json` with adjusted metrics and a clear note on the source (must be real human-labeled data). **Dependency**: T036a-Exec (if T036a runs) OR (T036b-Exec AND T036c-Exec). (Note: If T036a runs, T036c is skipped until T036b completes).

**Checkpoint**: Sensitivity analysis complete (or pipeline completed with skip report)

---

## Phase 7: Versioning & Reporting (Priority: P3)

**Goal**: Finalize artifacts and update state.

**Implementation**

- [ ] T038-Impl [P] **Implement Artifact Hasher**: Create `src/utils/hash_artifacts.py` function `hash_artifacts()`. **Logic**: Run checksums on all outputs in `data/processed/` and `data/results/`. **Output**: Script ready for T038-Exec.
- [ ] T038-Exec [P] **Run Artifact Hasher**: Execute `src/utils/hash_artifacts.py` function `hash_artifacts()`. **Verification**: Ensure `data/logs/artifact_hashes.json` exists. **Task Complete Definition**: Task is only complete when `data/logs/artifact_hashes.json` exists. (Dependency: T038-Impl)
- [ ] T039-Impl [P] **Implement State Updater**: Create `src/utils/state_updater.py` function `update_state()`. **Logic**: Update `state/projects/PROJ-282-evaluating-the-effectiveness-of-llms-for.yaml` with new hashes and completion status. **Output**: Script ready for T039-Exec.
- [ ] T039-Exec [P] **Update State File**: Execute `src/utils/state_updater.py` function `update_state()`. **Verification**: Ensure state file is updated. **Task Complete Definition**: Task is only complete when state file is updated. (Dependency: T039-Impl)
- [ ] T040-Impl [P] **Implement Research Report Generator**: Create `src/analysis/report_generator.py` function `generate_research_report()`. **Logic**: Generate final research report summarizing findings in `research.md`. **Output**: Script ready for T040-Exec.
- [ ] T040-Exec [P] **Generate Research Report**: Execute `src/analysis/report_generator.py` function `generate_research_report()`. **Verification**: Ensure `research.md` is updated. **Task Complete Definition**: Task is only complete when `research.md` is updated. (Dependency: T040-Impl)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **User Stories (Phase 2‑6)**: All depend on Foundational phase completion
 - **Data Flow Constraint**: Phase 2 (Inference), Phase 3 (Feature Extraction), and Phase 4 (Static Analysis) can run in parallel but **MUST** complete before Phase 5 (Analysis).
 - **Analysis Constraint**: Phase 5 cannot run until `data/processed/predictions.csv`, `data/processed/features.csv`, and `data/processed/static_predictions.csv` exist.
 - **Human Review Constraint**: T036 handles missing data gracefully; no hard abort.

### User Story Dependencies

- **User Story 1 (P1)**: Core pipeline. Depends on Foundational.
- **User Story 2 (P2)**: Feature extraction. Depends on Foundational. Can run parallel to US1.
- **User Story 4 (P2)**: Static analysis. Depends on Foundational. Can run parallel to US1/US2.
- **User Story 3 (P3)**: Statistical analysis. **Depends on US1, US2, and US4 completion** (requires predictions and features).
- **Sensitivity (Phase 6)**: Depends on US1 completion (requires predictions) and external human review (non‑blocking, but requires real data or skip report).

### Within Each User Story

- Models/Classes before Logic
- Logic before Pipelines
- Pipelines before Tests

### Parallel Opportunities

- **Setup**: T001a-Impl, T001b-Impl, T003-Impl, T004 can run in parallel. T007a‑T009e (generation & verification) can run concurrently.
- **Data Processing**: T010a-Exec, T011-Exec, T011b-Exec (Downloads), T018-Exec (Feature Extract), T024-Exec (Static Analyzer) can run in parallel once data is available.
 - **Note**: T019 (Vulnerability Pattern Pipeline) is split into T019a‑T019e; these run sequentially but independently of the main dataset flow.
- **Analysis**: T029a-Exec, T029b-Exec, T029c-Exec, T030-Exec, T031-Exec can be implemented in parallel, though execution order respects dependencies. T030-Exec and T031-Exec are parallel consumers of their respective upstream tasks.

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability to specific user stories
- **Memory Constraint**: All LLM tasks must use low‑bit quantization and dynamic batch sizing to stay under constrained memory limits.
- **Time Constraint**: The pipeline must complete within 6 hours; per‑sample inference ≤ 4.32s. Outliers exceeding this are handled by model fallback, not skipping.
- **Data Integrity**: Never synthesize fake data; always use the real VulDeePecker (Python), JSVulnDB (JS), and NIST Juliet (C) datasets as primary sources.
- **Verification**: Ensure tests fail before implementing.
- **Commit**: Commit after each task or logical group.
- **Stop**: Stop at any checkpoint to validate story independently.
- **Spec Precedence**: Where the Plan conflicts with the Spec (e.g., "Quantization‑aware training" vs "Zero‑Shot"), the Spec takes precedence per Constitution Principle II.