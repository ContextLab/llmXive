# Tasks: llmXive Follow-up: Extending "Full Attention Strikes Back"

**Input**: Design documents from `/specs/001-llmxive-static-sparsification/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Research Pipeline**: `code/data/`, `code/models/`, `code/evaluation/`, `code/lib/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create base project directories: `code/`, `tests/`, `data/`, `code/lib/`, `code/data/`, `code/models/`, `code/evaluation/`, `data/results/`, `data/logs/`, `data/intermediate/`, `data/config/`. **Implementation**: Create `code/scripts/init_dirs.sh` with `mkdir -p` commands for all 11 paths. **Verification**: Assert `os.path.isdir(...)` for all paths.
- [X] T001b [P] Verify directory structure and capture `tree` output. **Deliverables**: Create `data/logs/structure_verification.txt` containing the `tree` output. **Verification**: Assert `structure_verification.txt` exists and is non-empty.
- [X] T001c [P] Create `data/config/streaming_params.yaml` defining chunk sizes for data loading. **Content**: `chunk_size: 1000`, `max_chunk_size_mb: 50`. **Verification**: Assert file exists and contains valid YAML.
- [X] T002a [P] Create base `code/requirements.txt` with unpinned dependencies for: transformers, torch, datasets, scikit-learn, spacy, kenlm, numpy, pandas, llama-cpp-python, ruff, black, pytest, psutil, tracemalloc. **Content**: List exact package names one per line without version specifiers.
- [X] T002b [P] Pin versions in `code/requirements.txt` by running `pip freeze` in a clean virtualenv and saving output. **Verification**: Assert `requirements.txt` contains `==` for all packages.
- [X] T003a [P] Configure linting and formatting tools. **Deliverables**: Create `.ruff.toml` (content: `max-line-length = 88`) and `pyproject.toml` (content: `[tool.black]` section with `line-length = 88`). **Verification**: Assert `.ruff.toml` and `pyproject.toml` exist and contain specified content.
- [X] T003b [P] Run linting and formatting checks. **Verification**: Run `ruff check. --exit-zero` and `black --check.` successfully.
- [X] T004 [P] Initialize pytest configuration and create empty test suite structure. **Deliverables**: Create `pyproject.toml` (tool.pytest section) and `code/tests/conftest.py`. **Verification**: Run `pytest --collect-only` and verify 0 errors.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: Only T005 and T006 are blocking prerequisites for user story work. T007/T008 are optional utilities that do NOT block T011/T012 execution. T046 is a new blocking prerequisite for T013.

- [X] T005 [P] Implement memory-efficient data loader in `code/lib/data_loader.py` that streams RULER dataset chunks, enforces GB RAM limit, and includes a **unit test asserting peak memory usage < 7GB ** in `tests/unit/test_data_loader.py::test_peak_memory`. **Input Scope**: The test MUST use a **100-document sample** from the RULER validation split using `datasets.load_dataset(..., split='validation')[:100]`. **Implementation**: Use `tracemalloc` and `psutil` for memory profiling. **Verification**: Run `pytest tests/unit/test_data_loader.py::test_peak_memory` and assert it passes.
- [X] T006 [P] Create base data entities (`TokenUnit`, `AttentionMap`, `StaticHeuristic`) in `code/lib/entities.py`.
- [X] T007 [P] [Optional] Implement attention map visualization and debugging utilities in `code/lib/attention_utils.py`.
- [X] T008 [P] [Optional] Setup logging infrastructure to track pipeline stages and memory usage in `code/lib/logging_config.py`.
- [X] T046 [P] [Review Fix] Add **validation for KenLM model availability** in `code/data/compute_features.py` to fail loudly with a clear error message if the KenLM model file is missing, rather than attempting to load a non-existent model and crashing later. **Verification**: Assert script exits with code 1 and prints "KenLM model not found" if the file is missing. **Dependency**: Must be completed before T013.
- [ ] T046b [P] [Review Fix] **Generate Deterministic Document Manifest**. Create a script `code/data/generate_manifest.py` that uses a fixed seed (42) to select the first 50 documents from the RULER validation split and saves the list of document IDs to `data/config/document_manifest.json`. **Verification**: Assert `document_manifest.json` exists, contains exactly 50 unique IDs, and is deterministic across runs. **Dependency**: T011 must be able to read this file.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ground Truth Extraction & Static Feature Computation (Priority: P1) 🎯 MVP

**Goal**: Generate parallel datasets of RTPurbo-selected tokens and static linguistic features for the RULER corpus subset.

**Independent Test**: Run the extraction pipeline on a representative document sample and verify the output CSV contains valid entropy, POS tags, and binary RTPurbo labels without GPU memory errors.

### Tests for User Story 1 (OPTIONAL)

- [X] T009 [P] [US1] Unit test for feature extraction logic in `tests/unit/test_feature_extraction.py`.
- [X] T010 [P] [US1] Integration test for ground truth generation on small sample in `tests/integration/test_ground_truth.py`.

### Implementation for User Story 1

- [ ] T011 [US1] Implement RULER dataset downloader with streaming support in `code/data/download.py` (FR-001). **Constraint**: Must use `datasets.load_dataset(..., streaming=True)` and **fail loudly** if the real source is unreachable; **NO** synthetic fallbacks or mock data generation. **Sampling Logic**: Must read the document IDs from `data/config/document_manifest.json` (generated by T046b) and filter the streaming dataset to match these IDs exactly. **Verification**: Assert `data/intermediate/downloaded_docs.jsonl` exists and contains exactly the 50 documents listed in the manifest.
- [ ] T012a [US1] [Ground Truth Generation] Implement frozen Llama-3-8B model loading and attention map generation in `code/data/extract_ground_truth.py` (FR-002). **Requirements**: Load model using `llama-cpp-python` bindings with `n_gpu_layers=0` (CPU-only) and `n_ctx=4096` to fit 7GB RAM. Process the **strictly sampled subset of 50 documents** defined in `data/config/document_manifest.json`. Generate full attention maps. **Parameters**: Use **default values** for k=10 and threshold=0.05, but **log these as empirical** in `data/logs/ground_truth_params.yaml`. **Verification**: Assert attention maps are saved to `data/intermediate/attention_maps.h5`. **Dependency**: T011 and T046b.
- [ ] T012c [US1] [Hyperparameter Search] Implement a grid search on a small validation split to find optimal k and threshold for RTPurbo. **Input**: Attention maps from T012a (or a subset). **Output**: Save optimal parameters to `data/config/rtpurbo_params_optimized.yaml`. **Verification**: Assert the file contains valid k and threshold values. **Dependency**: T012a.
- [ ] T012b [US1] [RTPurbo Application & Anomaly Detection] Re-run RTPurbo application with **optimized parameters** from T012c to extract ground-truth labels. **Requirements**: Apply RTPurbo with k and threshold from T012c. Implement anomaly detection: flag documents with zero RTPurbo tokens, log to `data/logs/anomalies.csv`, and **exclude them from the final dataset**. **Output**: `data/intermediate/rtpurbo_labels.parquet`, `data/logs/anomalies.csv`. **Verification**: Assert `data/logs/anomalies.csv` is created and used to filter data in T014. **Dependency**: T012c and T046b.
- [ ] T015 [US1] [Edge Case Handling] Implement edge case handling for ambiguous tokens (special chars, emojis) in `code/data/compute_features.py` (Edge Case 1). **Requirement**: Must assign default "neutral" category or exclude from heuristic logic. **Verification**: Assert no runtime crashes on input with special characters. **Dependency**: Must be completed before T013.
- [ ] T013 [US1] Implement static feature computation (Entropy, POS via spaCy, Position, **local semantic density (defined as perplexity via KenLM)**) in `code/data/compute_features.py` (FR-003). **Input**: Anomaly list from T012b (to exclude rows) AND Edge Case handling from T015. **Definition**: 'local semantic density' is calculated as the **perplexity of the token given its local context using the KenLM model** (to avoid circularity with Llama-3-8B). **Algorithm**: Use KenLM to compute n-gram probabilities; handle boundary conditions by reducing window size. **Verification**: Assert output schema includes `local_semantic_density` column and values are derived from KenLM. **Dependency**: T012b and T015 and T046 and T046b.
- [ ] T014 [US1] Implement dataset merger to join ground truth labels (from T012b, filtered by anomaly list) with static features (from T013) into `data/intermediate/merged_dataset.csv`. **Input**: T012b anomaly list to exclude rows. **Dependency**: T013 must complete before T014. **Verification**: Assert row count matches sum of valid inputs and schema is correct (all expected columns present).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. **T014 must complete before T019 starts.**

---

## Phase 4: User Story 2 - Static Predictor Training & Heuristic Derivation (Priority: P2)

**Goal**: Train a CPU-based classifier to predict RTPurbo selection and derive a deterministic rule-based heuristic.

**Independent Test**: Train the model on a training split and evaluate on validation; verify the output includes a specific rule set and baseline accuracy metric.

### Tests for User Story 2 (OPTIONAL)

- [X] T017 [P] [US2] Unit test for rule derivation logic in `tests/unit/test_rule_derivation.py`.
- [X] T018 [P] [US2] Integration test for training pipeline with multiple seeds in `tests/integration/test_training.py`.

### Implementation for User Story 2

- [X] T019-Static [US2] Implement CPU-based classifier training (Decision Tree/Logistic Regression) with **independent random seeds** in `code/models/train_static.py` (FR-004). **Input**: `data/intermediate/merged_dataset.csv` (output of T014). **Output**: trained models saved to `data/intermediate/models/seeds/model_seed_{seed}.pkl`. **Verification**: Run a test to assert model loads and predicts on a dummy input.
- [X] T019a [US2] Implement data splitting logic to create train/test splits from `data/intermediate/merged_dataset.csv` in `code/models/split_data.py`. **Input**: T014 output. **Output**: `data/intermediate/train_split.csv` and `data/intermediate/test_split.csv` using a stratified split. **Verification**: Assert splits exist and sum to original row count.
- [X] T019b [US2] Implement evaluation of the trained static models on the test set to generate **performance scores** (precision/recall) in `code/models/evaluate_static.py` (FR-004). **Logic**: Iterate over the seed models, evaluate each on the test set (from T019a), and save results. **Output**: `data/intermediate/static_eval_scores.json` with schema `{seed_id: int, precision: float, recall: float}`. **Verification**: Assert schema matches.
- [X] T026b-Static [US2] Implement aggregation logic to compute **mean, variance, and standard deviation** of the static evaluation scores from T019b and save to `data/results/static_aggregated.json`. **Schema**: `{mean_metric, std_metric, variance_metric, n_seeds, seed_values: []}` (FR-004). **Verification**: Assert aggregation logic matches manual calculation on a small subset. **Requirement**: Must include variance/std_dev to satisfy SC-001 stability measurement.
- [X] T020 [US2] Implement rule derivation logic to extract hard thresholds from model importance in `code/models/derive_rules.py` (FR-004). **Output Format**: JSON schema `{"rules": [{"condition": "entropy > X", "pos": ["NOUN", "PROPN"]}]}`. **Method**: Extract decision tree paths or analyze feature importance coefficients to derive deterministic rules. **Verification**: Assert output file exists and matches schema.
- [X] T021 [US2] Implement static heuristic application script to reconstruct RTPurbo tokens using only rules in `code/models/apply_heuristic.py` (FR-004).
- [X] T022 [US2] Add metrics calculation (Precision/Recall) for static predictor against ground truth in `code/lib/metrics.py` (FR-004).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sparsification Evaluation & Statistical Comparison (Priority: P3)

**Goal**: Evaluate static-heuristic sparsification against baselines and perform statistical significance testing.

**Independent Test**: Run evaluation on test set and generate report with perplexity, exact match, and p-values comparing methods.

### Tests for User Story 3 (STRICT PREREQUISITE)

**⚠️ CRITICAL ORDERING**: T023 and T024 MUST be written and verified to fail before any implementation tasks (T025-T032) begin. These are NOT parallel tasks; they are sequential prerequisites to ensure the contract is defined before implementation.

- [X] T023 [US3] Contract test for statistical analysis output format in `tests/contract/test_stats_output.py`. **Verification**: Assert `data/results/statistical_report.txt` contains required fields (p-value, test_type, method_comparison).
- [X] T024 [US3] Contract test for full baseline metrics schema in `tests/contract/test_baseline_schema.py`. **Verification**: Assert that `data/results/full_baseline_metrics.json` *would* contain keys `perplexity`, `exact_match` if it existed. This test defines the schema contract, not the execution. **Note**: This test must be written first and verified to pass (as a schema definition) before T025 is implemented.

### Implementation for User Story 3

- [ ] T025 [US3] Implement full attention baseline runner in `code/evaluation/run_baselines.py` (FR-005). **Output**: `data/results/full_baseline_metrics.json`. **Requirement**: Must compute **BOTH perplexity and exact_match** metrics for the full-attention baseline to satisfy SC-002 and SC-003. **Verification**: Assert output file contains both metrics.
- [ ] T026a-Run [US3] Implement Learned Sparse (RTPurbo) baseline runner to **execute 5 independent random seeds** and save **per-document scores** to `data/intermediate/baseline_seeds/seed_{seed}_per_doc.json` (FR-008/FR-006). **Mechanism**: Use **random subsampling of documents** with `random.seed={seed}` for each of the 5 seeds. **Seeds**: Use fixed seeds `[42, 123, 456, 789, 101]`. **Constraint**: Must use the **same fixed document subset** (from `data/config/document_manifest.json`) for all 5 seeds to ensure paired t-test validity. **Output**: Raw per-document results for each seed. **Schema**: `[{document_id, perplexity, exact_match}]`. **Requirement**: Must compute **BOTH perplexity and exact_match** for every document to satisfy SC-003. **Verification**: Assert schema matches T029 requirements for paired t-test. **Dependency**: T014 and T046b.
- [ ] T026a-Aggregate [US3] Implement aggregation logic to compute **mean and variance** of the Learned seed results from T026a-Run and save to `data/results/learned_aggregated.json`. **Schema**: `{mean_metric, std_metric, n_seeds, seed_values: []}` (FR-008). **Verification**: Assert aggregation logic matches manual calculation on a small subset. **Dependency**: T026a-Run.
- [ ] T027 [US3] Implement static heuristic sparsification runner in `code/evaluation/run_baselines.py` (FR-005). **Input**: Rules from T020. **Output**: **Per-document** Perplexity and Exact Match metrics to `data/intermediate/static_per_document.json` for **5 independent seeds** (to match Learned baseline variance). **Schema**: `[{seed_id, document_id, perplexity, exact_match}]`. **Requirement**: Document IDs must match those in T026a-Run for paired t-test. **Verification**: Assert schema matches T029 requirements and ID alignment. **Dependency**: T020 and T046b.
- [ ] T027a [US3] Implement aggregation logic to compute **mean and variance** of the static evaluation results from T027 and save to `data/results/static_aggregated_per_doc.json`. **Schema**: `{mean_metric, std_metric}`. **Dependency**: T027. **Verification**: Assert aggregation logic matches manual calculation on a small subset.
- [ ] T029 [US3] Implement paired t-test/Wilcoxon test for statistical significance in `code/evaluation/stats_analysis.py` (FR-006). **Input**: Raw per-document scores from T026a-Run (`data/intermediate/baseline_seeds/`) and T027 (`data/intermediate/static_per_document.json`). **Logic**:
 1. For each document, aggregate the 5 Learned seed scores (from T026a-Run) into a single **mean** score (both perplexity and exact_match).
 2. For each document, aggregate the 5 Static seed scores (from T027) into a single **mean** score (both perplexity and exact_match) (using T027a's logic).
 3. Pair the **mean Learned score** with the **mean Static score** for the same document (ensuring `document_id` matches exactly).
 4. Perform a paired t-test on the N document pairs (Mean_Learned - Mean_Static) for each metric.
 5. Use `scipy.stats.ttest_rel` on the list of differences.
 **Library**: Use `scipy.stats.ttest_rel`. **Missing Data**: Exclude document pairs where either score is missing. **Requirement**: Must perform a **paired t-test on aggregated means** to preserve statistical validity. **Output**: Save results to `data/results/statistical_report.json` with schema `{p_value, t_statistic, method_comparison, n_samples}`. **Dependency**: T026a-Run and T027.
- [ ] T031a [US3] Create configuration file `data/config/threshold.yaml` defining the performance drop threshold. **Content**: `value: 0.01`, `status: configurable`, `rationale: 'Default 1% threshold per Constitution Principle VI'`. **Verification**: Assert `data/config/threshold.yaml` exists and contains `value: 0.01`.
- [ ] T031 [US3] Implement Falsifiability Check: Calculate the performance drop `(Learned_Mean - Static_Mean) / Learned_Mean` using metrics from T026a-Aggregate and T027a, compare against the threshold read from `data/config/threshold.yaml` (default 0.01 if null), AND verify the p-value from T029 is > 0.05 (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value) (not statistically significant). **Safeguard**: Include a **zero-division guard**: if `Learned_Mean` is near zero (< 1e-6), log an error and skip the calculation to prevent pipeline crash. **Dependencies**: T027a, T026a-Aggregate, T031a, T029. **Note**: The "negligible" verdict requires BOTH drop < 1% AND p > 0.05 (if threshold is set). **Dependency**: T026a-Aggregate and T029 must complete before T031.
- [ ] T030 [US3] Generate final evaluation report at `data/results/final_report.md` containing: Perplexity, Exact Match, P-values, and Statistical Significance (SC-002, SC-004). **Required Sections**: Executive Summary, Methodology, Results Table, Statistical Significance. **Dependencies**: T025, T026a-Aggregate, T027a, T029, T031, T032b.
- [ ] T032 [US3] Implement pipeline timing instrumentation to log start/end timestamps to `data/results/timing_report.json`. **Requirement**: Must include **network I/O (download time)** in the total pipeline measurement. Log download duration separately. **Scope**: The 6-hour limit applies to the **sampled subset pipeline** as defined in Plan Performance Goals (full-scale runs are out of scope for free tier).
- [ ] T032b [US3] Implement post-execution check script in `code/evaluation/check_timing.py` that reads `timing_report.json` and asserts duration < 21600s (6 hours) for **total pipeline execution time** (including download). Log download time separately. **Scope**: The duration MUST include **total pipeline execution time** but exclude network I/O for the check? No, SC-005 requires total time. **Verification**: Assert script exits with code 0 if duration < 21600s.
- [ ] T034-CrossModel [US3] [Cross-Model Validation] Implement Cross-Model Validation on Gemma-2-9B. **Input**: Rules from T020. **Task**: **Run Gemma-2-9B** to generate attention maps for the same document subset (from `data/config/document_manifest.json`), apply the static rules, and measure performance drop against the Gemma-2 full-attention baseline. **Output**: `data/results/cross_model_metrics.json` containing perplexity and exact_match for Gemma-2 Full, Learned, and Static. **Verification**: Assert output file exists and contains performance drop metric. **Dependency**: T020 and T046b. **Note**: This task implements FR-009 and SC-006 and is REQUIRED.
- [ ] T047 [P] [Review Fix] Implement **data integrity check** in `code/data/merge_dataset.py` to verify that the number of rows in `merged_dataset.csv` exactly matches the number of valid tokens in the input files after anomaly exclusion, preventing silent data loss. **Verification**: Assert a `ValueError` is raised if row counts mismatch. **Dependency**: T014.
- [ ] T048 [P] [Review Fix] Add **unit tests for the paired t-test logic** in `tests/unit/test_stats_analysis.py` using synthetic data with known p-values to ensure `scipy.stats.ttest_rel` is being called correctly and the pairing logic is sound. **Verification**: Assert test passes with expected p-value for synthetic inputs. **Dependency**: T029.
- [ ] T049 [P] [Review Fix] Implement **automatic fallback to CPU-only mode** in `code/evaluation/run_baselines.py` if CUDA is detected but not available, ensuring the pipeline does not crash on CPU-only runners. **Verification**: Assert script runs successfully on a CPU-only environment and logs "Running in CPU-only mode". **Dependency**: T025.
- [ ] T050 [P] [Review Fix] Create **comprehensive README** for the `code/` directory explaining the execution order, dependencies, and how to run each phase independently, addressing the complexity of the research pipeline. **Verification**: Assert `code/README.md` exists and contains step-by-step instructions for each user story.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates in `quickstart.md` and `research.md`.
- [X] T036 Code cleanup and refactoring of data loading logic.
- [X] T037 Performance optimization for streaming pipeline.
- [X] T038 [P] Additional unit tests for edge cases in `tests/unit/`.
- [X] T039 Run quickstart.md validation to ensure reproducibility on free tier.
- [X] T040 [P] [Review Fix] Implement explicit **streaming chunk size configuration** in `code/data/download.py` to ensure no single chunk exceeds a predefined size threshold, preventing OOM on 7GB RAM runners. **Verification**: Assert chunk size logic in `download.py` matches `data/config/streaming_params.yaml` (created in T001c).
- [X] T041 [P] [Review Fix] Add **deterministic seed enforcement** to `code/models/train_static.py` for scikit-learn and numpy to ensure reproducibility across runs, addressing FR-004 variance concerns. **Verification**: Assert `random.seed`, `np.random.seed`, and `model.random_state` are all set to `42` in the script.
- [X] T042 [P] [Review Fix] Implement **document-level ID persistence** in `data/intermediate/merged_dataset.csv` to ensure strict alignment between T026a-Run (Learned) and T027 (Static) for the paired t-test in T029. **Verification**: Assert `document_id` column is present and unique in both input files for T029.
- [X] T043 [P] [Review Fix] Add **error handling for KenLM** in `code/data/compute_features.py` to gracefully skip tokens if the n-gram model fails to load or compute perplexity, logging the specific failure reason to `data/logs/compute_errors.log` instead of crashing. **Verification**: Assert pipeline continues and logs error when KenLM is unavailable.
- [X] T044b [P] [Review Fix] Create `data/config/seeds.json` containing the fixed seed list `[42, 123, 456, 789, 101]` for reproducibility. **Verification**: Assert file exists and contains valid JSON.
- [X] T044 [P] [Review Fix] Create **reproducibility manifest** in `data/results/reproducibility_manifest.json` that records the exact dataset version, random seeds, and library versions used for the run, addressing Constitution Principle I. **Verification**: Assert manifest contains `dataset_hash` (hash of `merged_dataset.csv`), `seeds_used` (read from `data/config/seeds.json` created in T044b), and `dependency_versions` (from `requirements.txt`).
- [X] T045 [P] [Review Fix] Implement **explicit memory profiling** in `code/data/extract_ground_truth.py` to log peak RAM usage per document during Llama-3-8B inference, ensuring the 7GB limit is not exceeded during the ground truth generation phase. **Verification**: Assert `data/logs/memory_profile_gt.csv` is generated with `document_id`, `peak_ram_mb`, and `status` columns.