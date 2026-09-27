# Tasks: llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

**Input**: Design documents from `/specs/PROJ-924/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The specification explicitly requires statistical validation and contract tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (depends on specific prior task in same phase)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/`
- Paths shown below assume single project structure per `plan.md`

## Phase -1: Spec Amendment & Deviation Logging

- [X] T-000-RatifySpecAmendment [S] **Ratify Spec Amendment**: Update `specs/PROJ-924/spec.md` to reflect the substitution of `gpt-4o-mini` with `google/flan-t5-small` in US‑03 Acceptance Criteria. **Action**: Modify `specs/PROJ-924/spec.md` to replace `gpt-4o-mini` with `google/flan-t5-small` in US-03. Verify the change is present. **DEPENDS ON**: None.
- [X] T-001-DeviationLog [S] **Log Plan Deviation**: Create `docs/plan_deviation_log.md` documenting the substitution of `gpt-4o-mini` with `google/flan-t5-small` in US‑03 due to memory constraints on GitHub Actions free-tier. **Action**: Write a formal log entry citing the constraint (limited RAM capacity) and the selected alternative. **DEPENDS ON**: T-000-RatifySpecAmendment.
- [X] T-002-AmendUS03 [S] **Amend US-03 Acceptance Criteria**: Update `specs/PROJ-924/spec.md` US-03 to explicitly state: "The system runs a zero-shot LLM classifier (google/flan-t5-small) on a subset of logs. " Update AUC-ROC comparison criteria to: "The drift-based method is flagged as a 'computationally efficient alternative' if its AUC is within 0.10 of the Flan-T5 baseline." **Action**: Modify `specs/PROJ-924/spec.md` text to reflect the new model and criteria. **DEPENDS ON**: T-000-RatifySpecAmendment.

## Phase 0: Scope Verification (Post‑Spec Fix)

- [X] T000-ScopeVerify [S] [US3] **Verify Spec Amendment**: Confirm `specs/PROJ-924/spec.md` has been updated to reflect the `google/flan-t5-small` substitution and updated acceptance criteria. **Action**: Read `specs/PROJ-924/spec.md` and assert the updated text is present. **DEPENDS ON**: T-002-AmendUS03.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001a [S] **Initialize Project Directories**: Create directories `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, `tests/`, `data/raw/`, `data/processed/`, `data/test/`, `specs/`, `docs/`, and `specs/PROJ-924/`. **Acceptance Criteria**: All directories exist.
- [X] T001b [S] **Verify Directory Structure**: Create `tests/test_setup.py` with function `test_directories_exist` that asserts the existence of the directories created in T001a. Run `pytest` to confirm `test_directories_exist` passes. **Acceptance Criteria**: `test_directories_exist` passes. (DEPENDS ON T001a)
- [X] T009 [S] Initialize a Python project with `requirements.txt` (sentence-transformers, scikit-learn, pandas, numpy, datasets, jsonschema, statsmodels, pytest, transformers, accelerate) using a modern, stable Python 3 release. **Note**: Removed `llama-cpp-python` as it is not used.
- [X] T010a [S] **Create Ruff Config**: Create `.ruff.toml` with EXACT content:
 ```toml
 [lint]
 select = ["E", "F", "W", "I"]
 ignore = []
 [format]
 quote-style = "double"
 ```
 **Acceptance Criteria**: File exists and is non-empty.
- [X] T010b [S] **Create Pyproject Config**: Create `pyproject.toml` with EXACT content (including project metadata and dependencies, excluding Black config):
 ```toml
 [build-system]
 requires = ["setuptools>=61.0", "wheel"]
 build-backend = "setuptools.build_meta"

 [project]
 name = "agentdog-drift"
 version = "0.1.0"
 dependencies = [
 "sentence-transformers",
 "scikit-learn",
 "pandas",
 "numpy",
 "datasets",
 "jsonschema",
 "statsmodels",
 "pytest",
 "transformers",
 "accelerate"
 ]
 ```
 **Acceptance Criteria**: File exists and is non-empty.
- [X] T010c [S] **Create Verification Tests**: Create `tests/test_config_files.py` with functions `test_ruff_config_exists` and `test_pyproject_config_exists`. **Acceptance Criteria**: Functions assert file existence and non-emptiness.
- [X] T010d [S] **Run Verification**: Run `pytest` to confirm `test_ruff_config_exists` and `test_pyproject_config_exists` pass. **Acceptance Criteria**: Tests pass. (DEPENDS ON T010a, T010b, T010c)

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T011a [S] **Initialize Config**: Create `config.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to manage random seeds, paths, and batch sizes. **Acceptance Criteria**: File exists, contains `RANDOM_SEED=42`, `MAX_RAM_GB=7`, and `BATCH_SIZE=64`. **Note**: The batch size 64 is sourced from arxiv.org/abs/2410.21676 (documented in comments). **DEPENDS ON**: T009, T010.
- [X] T011b [S] **Create Config Test**: Create `tests/test_config.py` with function `test_config_constants` that asserts the values in `config.py`. **Acceptance Criteria**: Function asserts correct values. **DEPENDS ON**: T011a.
- [X] T011c [S] **Run Config Test**: Run `pytest` to confirm `test_config.py` passes. **Acceptance Criteria**: Test passes. **DEPENDS ON**: T011b.
- [X] T012a [S] **Fetch and Map Validation Dataset**: Implement `fetch_and_map_atbench` in `data_loader.py`. **Step 1**: Fetch `AI45Research/ATBench` using `datasets.load_dataset` with `streaming=True`. **Step 2**: If `timestamp` is missing, derive it as `int(hashlib.sha256(log_id.encode()).hexdigest(), 16) % 86400` (output: integer seconds since epoch). **Step 3**: Map labels containing 'attack' or 'malicious' to 'novel', and 'safe' or 'benign' to 'benign'. **Action**: Save raw dataset to `data/raw/ATBench_raw.parquet` and mapped dataset to `data/processed/ATBench_mapped.csv`. **Acceptance Criteria**: Functions derive timestamps correctly as integers and map labels correctly. Run `pytest` to confirm `test_data_loader.py` passes. **DEPENDS ON**: T011a. **NOTE**: This task fetches the validation dataset (`AI45Research/ATBench`) required for US-01 and US-03.
- [X] T012b [S] Add checksum verification logic in `data_loader.py` to validate raw data against `data/checksums.json`. **Acceptance Criteria**: Logic raises `ValueError` if checksum mismatch. Run `pytest` to confirm `test_checksums.py` passes. (DEPENDS ON T012a)
- [X] T012d-gen [S] **Define Taxonomy**: Implement `define_taxonomy` in `taxonomy_builder.py` to define the AgentDoG safety taxonomy categories in code using the EXACT definitions from the *AgentDoG 1.5* paper. **Definitions**:
 1. **Safety**: "Harmful content that may cause physical or psychological harm."
 2. **Privacy**: "Exposure of personal identifiable information (PII)."
 3. **Bias**: "Discriminatory or biased language targeting protected groups."
 4. **Jailbreak**: "Attempts to bypass safety filters or generate restricted content."
 **Action**: Save the taxonomy definition to `data/processed/taxonomy_agentdog.json`. **Acceptance Criteria**: File exists with correct categories and definitions. Run `pytest` to confirm `test_taxonomy_def.py` passes. **DEPENDS ON**: T011a. **NOTE**: This task defines the taxonomy locally using the paper's definitions to avoid circularity.
- [X] T012f [S] **Fetch Large-Scale Log Dataset**: Implement `fetch_agent_logs` in `data_loader.py` to stream `mlfoundations/agent_logs` (split="train") using `datasets.load_dataset(..., streaming=True)`. **Action**: Stream and save to `data/raw/agent_logs.csv` in chunks. **Constraint**: This task is MANDATORY for T045a (Benchmark). **DEPENDS ON T012a**. **NOTE**: If the dataset is unavailable, raise a `ConnectionError` immediately. Do NOT implement a synthetic fallback.
- [X] T014 [S] Create `contracts/schema_loader.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` for contract validation helpers and JSON/CSV schema loading. **Acceptance Criteria**: File exists, contains `validate_schema` function. Run `pytest` to confirm `test_utils.py` passes.
- [X] T015 [S] Setup `checksums.json` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/` for raw data integrity tracking. **DEPENDS ON T009**.
- [X] T016a [S] Implement `taxonomy_builder.py` to generate centroid embeddings using `all-MiniLM-L6-v2` (CPU‑first, dynamic batching to stay <7 GB RAM) with input from `data/processed/taxonomy_agentdog.json` (produced by T012d-gen). **DEPENDS ON T012d-gen**.
- [X] T016b [S] **Memory Assessment**: Add runtime memory monitoring in `taxonomy_builder.py` using `tracemalloc`; raise `MemoryError` if peak RAM > 7 GB. **Action**: Generate `docs/memory_assessment.md` documenting the peak RAM usage and confirming CPU feasibility. **DEPENDS ON**: T016a.
- [X] T016c [S] Save generated taxonomy centroids to `data/processed/taxonomy_centroids.json`. **DEPENDS ON T016a**.
- [X] T035-real-human [S] **Real Human Ingestion (Production Only)**: Ingest a file `data/processed/human_annotations_for_bins.csv` containing labels for the `log_id`s in `data/processed/annotation_request_bins.csv` from **real human annotators**. **Action**: This file must be generated by a human. Add a `source_type` column set to 'REAL_HUMAN'. **DEPENDS ON**: T030a-Stratify. **NOTE**: This task is moved to Phase 2 to ensure data availability for Phase 3 validation.
- [X] T035-real-human-verify [S] **Real Human Data Verification Gate (Blocking)**: Verify that `data/processed/human_annotations_for_bins.csv` exists and has `source_type`='REAL_HUMAN'. **Action**: If the file is missing or has `source_type`='SIMULATED', raise a `ValueError` and block the build for Final Report generation. **DEPENDS ON**: T035-real-human.
- [X] T017 [S] **Generate Gold-Standard Proxy**: Create `data/processed/gold_standard_proxy.csv` by reading `data/processed/ATBench_mapped.csv` (from T012a), filtering for a balanced set of 'benign' and 'novel' records. **Action**: If the dataset does not contain at least 50 of each class, raise a `ValueError`. Save the filtered subset to `data/processed/gold_standard_proxy.csv`. **Acceptance Criteria**: File exists with a dataset containing both benign and novel records. **DEPENDS ON**: T012a.

## Phase 3: User Story 1 – Zero‑Shot Drift Scoring (Priority: P1)

- [X] T018 [S] [US1] Contract test for `drift_scoring.py` output schema (`drift_result.schema.yaml`). **DEPENDS ON** T014.
- [X] T019 [S] [US1] Unit test for empty/whitespace log handling (`test_empty_log_returns_drift_score_max`). **DEPENDS ON** T014.
- [X] T020 [S] [US1] Integration test for batch memory limits (`test_batch_memory_limit_gb`). **DEPENDS ON** T014.
- [X] T021a [S] [US1] Implement `compute_cosine_distance` in `drift_scoring.py` (minimum cosine distance to centroids). **DEPENDS ON T016c**.
- [X] T021b [S] [US1] Implement `batch_process_logs` handling large datasets within 7 GB RAM. **DEPENDS ON T016c**.
- [X] T021c [S] [US1] Implement `handle_empty_logs` assigning the fixed theoretical maximum cosine distance and setting `review_flag=True`. **DEPENDS ON T016c**.
- [X] T021d [S] [US1] Implement `export_results` to CSV `data/processed/drift_scores.csv` (`log_id`, `drift_score`, `review_flag`). **DEPENDS ON** T016c, T012a.
- [X] T022 [S] [US1] Create `main.py` orchestration script to run full scoring pipeline. **DEPENDS ON** T021a‑T021d.
- [X] T030a-Stratify [S] [US2] **Implement Stratification and Binning**: Implement `stratify_logs` in `validation.py` to read `drift_scores.csv`, generate high/low drift bins (top [deferred] and bottom [deferred] of drift scores), and export `data/processed/annotation_request_bins.csv`. **Action**: This task handles both stratification and bin generation in a single step. **DEPENDS ON** T021d, T012a.
- [X] T031a [S] [US2] Implement blinding logic (remove `drift_score` column) before export. **DEPENDS ON** T030a-Stratify.
- [X] T030b [S] [US2] Generate blinded annotation CSVs (`data/processed/blinded_annotation_batches/*.csv`) from the system-generated bins. **DEPENDS ON** T030a-Stratify, T031a, T021d.
- [X] T032a [S] [US2] Ingest human annotations from `blinded_annotation_batches/*.csv`; raise `ValueError` if too few files. **DEPENDS ON** T030b.
- [X] T032a-annot-id [S] Assign `annotator_id` from filename if missing column. **DEPENDS ON** T032a.
- [X] T031b-Kappa [S] **Compute Cohen's Kappa**: Compute Kappa on the **individual** annotation streams from T032b-SimPanel (simulated) or T032a (real). **Action**: Calculate Kappa between Rater A/B, B/C, A/C. Output `data/processed/kappa_stats.json`. **DEPENDS ON** T032b-SimPanel, T032a.
- [X] T031b [S] Merge annotations, calculate Kappa, output `data/processed/merged_annotations.csv`. **DEPENDS ON** T031b-Kappa.
- [X] T032b-SimPanel [S] **Simulated Human Panel (CI Only)**: Generate multiple simulated rater streams (`rater_A.csv`, `rater_B.csv`, `rater_C.csv`) with distinct noise models (bias=0.1, error_rate=0.15 for A; bias=-0.1, error_rate=0.1 for B; bias=0, error_rate=0.2 for C). **Action**: This task is for CI testing of the Kappa logic ONLY. **DEPENDS ON** T030a-Stratify.
- [X] T035-ci-proxy [S] **CI Simulation Proxy**: Generate `data/processed/human_annotations_for_bins.csv` by simulating 3 human annotators (with distinct bias/noise profiles) on the bins from T030a-Stratify. **Action**: Use a fixed random seed (`RANDOM_SEED=42`). Add a `source_type` column set to 'SIMULATED'. **Acceptance Criteria**: File exists with 'SIMULATED' source_type. **DEPENDS ON**: T030a-Stratify. **NOTE**: This task provides a valid data source for CI validation ONLY. It is NOT used for final statistical gates.
- [X] T035-real-recruit [S] **Define Human Recruitment Protocol**: Create `docs/human_annotation_protocol.md` describing the protocol for recruiting annotators, presenting bins, and collecting labels. **Action**: This document defines the "Human-in-the-Loop" workflow required by US-02 and Constitution Principle VI. **DEPENDS ON** T030a-Stratify.
- [X] T031c-KappaGate [S] [US2] **Kappa Validation Gate**: Validate Cohen's Kappa (κ ≥ 0.6) using output from T031b. **Action**: If Kappa < 0.6, raise a `ValueError` and block advancement. Output `data/processed/kappa_gate_status.json`. **DEPENDS ON** T031b, T035-real-human-verify.
- [X] T031c [S] Perform logistic regression and Mann‑Whitney U tests on `merged_annotations.csv`; output `data/processed/validation_stats.json`. **DEPENDS ON** T031b.
- [X] T032b [S] Generate mock annotation fixtures for unit tests (`data/test/mock_annot_*.csv`). **DEPENDS ON** T021d.
- [X] T025a-proxy [S] [US1] **CI Statistical Validation (Proxy)**: Compute p‑value and Cohen's d using the **Gold-Standard Proxy** from T017. **Label Mapping**: For `AI45Research/ATBench`, map labels containing 'attack' or 'malicious' to 'novel', and 'safe' or 'benign' to 'benign'. Output `data/processed/us01_proxy_stats.json`. **Action**: This task is for CI/Development validation ONLY. It does NOT block the build if it fails, but its results are NOT used for the Final Report. **DEPENDS ON** T017, T021d.
- [X] T025b-final [S] [US1] **Final Statistical Validation (Real Human)**: Compute p‑value and Cohen's d using the **Real Human Data** from T035-real-human. **Label Mapping**: For `AI45Research/ATBench`, map labels containing 'attack' or 'malicious' to 'novel', and 'safe' or 'benign' to 'benign'. Output `data/processed/us01_final_stats.json`. **Action**: If T035-real-human-verify fails (no real data), this task MUST raise a `ValueError` and halt. This task does NOT accept simulated data. **DEPENDS ON** T035-real-human-verify, T021d.
- [X] T026 [S] [US1] Validate US‑01 acceptance (p < 0.05, Cohen's d ≥ 0.5) using output from T025b-final; block advancement if criteria not met. **DEPENDS ON** T025b-final.

## Phase 4: User Story 2 – Human‑in‑the‑Loop Validation (Priority: P2)

- [X] T027 [S] [US2] Unit test for stratification logic (`test_stratification`). **DEPENDS ON** T030a-Stratify.
- [X] T028 [S] [US2] Unit test for Kappa calculation (`test_kappa`). **DEPENDS ON** T031b-Kappa.
- [X] T029 [S] [US2] Unit test for blind export (`test_blind`). **DEPENDS ON** T031a.
- [X] T035-final-validation [S] **Final Validation Swap**: If `data/processed/human_annotations_for_bins.csv` exists (from T035-real-human-verify), re-run T039-gpt-final using real human labels. **Action**: This ensures the final report is based on real human validation. If the file is missing, the task MUST raise a `ValueError` and block the build. Do NOT use simulation for the final US-03 acceptance. **DEPENDS ON** T035-real-human-verify, T039-gpt-final.

## Phase 5: User Story 3 – Baseline Performance Comparison (Priority: P3)

- [X] T037 [S] [US3] Unit test for AUC‑ROC calculation (`test_auc`). **DEPENDS ON** T039-metrics-auc.
- [X] T038 [S] [US3] Unit test for inference time measurement (`test_inference_time`). **DEPENDS ON** T039-metrics-time.
- [X] T039-scope-change-doc [S] Document model substitution (gpt‑o‑mini → google/flan-t5-small). **Action**: Verify that T-002-AmendUS03 has updated `specs/PROJ-924/spec.md`. **DEPENDS ON** T-002-AmendUS03.
- [X] T039-gpt-setup [S] Prepare `flan_config.json` (model name, tokenizer cache, prompt template). Assert plan deviation present. **Schema**: `{"model_name": "google/flan-t5-small", "temperature": 0.0, "prompt_template": "Classify the following text as 'benign' or 'novel': {text}"}`. **DEPENDS ON** T012a, T039-scope-change-doc, T-002-AmendUS03.
- [X] T039-model-runner [S] Implement `run_flant5` to load `google/flan-t5-small`, perform zero‑shot classification on a given dataset, cache outputs. **Action**: Wrap execution in `tracemalloc`. If peak RSS exceeds 7GB, raise `MemoryError` immediately. Do NOT attempt GPU fallback. **DEPENDS ON** T039-gpt-setup.
- [X] T039-model-verify [S] **Flan-T5 Memory Verification**: Verify that `google/flan-t5-small` can be loaded and run within 7GB RAM on the GitHub Actions runner. **Action**: Run a small subset test. Generate `docs/memory_assessment.md` (append to existing) confirming CPU feasibility. If it fails, raise `ValueError` and block T039-gpt-final. **DEPENDS ON** T039-model-runner.
- [X] T039-metrics-auc [S] Implement `calculate_auc_roc` using predictions vs. ground truth. **DEPENDS ON** T039-model-runner.
- [X] T039-metrics-time [S] Implement `measure_inference_time` per log. **DEPENDS ON** T039-model-runner.
- [X] T039-proxy-validation [S] Run quick sanity check of Flan‑T5 against the **REAL GROUND TRUTH (PROXY)** (generated dynamically from T017). Require statistically significant AUC (p < 0.05). **DEPENDS ON** T039-gpt-setup, T039-metrics-auc, T017.
- [X] T039-gpt-run [S] **MVP Baseline Run**: Execute Flan‑T5 on the proxy dataset (T017), store predictions in `data/processed/flan_predictions_proxy.json`. **DEPENDS ON** T039-model-runner, T017, T039-scope-change-doc.
- [X] T039-generate-report [S] Generate MVP comparison report (`data/processed/mvp_comparison_report.json`) containing AUC‑ROC and average inference time for both drift and Flan‑T5 baselines. **DEPENDS ON** T039-gpt-run, T025a-proxy.
- [X] T039-gpt-final [S] **Final Baseline Run (Real Human Path)**: Execute Flan‑T5. **Data Source**: MUST use `data/processed/human_annotations_for_bins.csv` from T035-real-human-verify if available, otherwise use T035-ci-proxy. **Action**: If the file is missing, raise a `ValueError` and fail the task. Do NOT use simulation for the final US-03 acceptance. **DEPENDS ON** T039-model-runner, T035-real-human-verify.
- [X] T040 [S] Implement bootstrap iteration logic for AUC‑ROC stability, output `bootstrap_stats.json`. If CPU time exceeds limit, set `timeout_limited: true`. **DEPENDS ON** T039-gpt-run.
- [X] T040a [S] **Final Timeout Enforcement**: If `timeout_limited` is true in `bootstrap_stats.json` during final report generation, abort with error to satisfy resource‑constrained integrity. **DEPENDS ON** T040.
- [X] T040b-deterministic-cache [S] Add deterministic caching of model outputs to ensure reproducibility. **DEPENDS ON** T039-model-runner.
- [X] T041-mvp [S] Generate MVP Comparison Report (AUC‑ROC, inference time) using proxy data. **DEPENDS ON** T039-generate-report, T025a-proxy.
- [X] T041-final [S] Generate Final Comparison Report using Real Human Data (T035-real-human-verify); require Flan‑T5 AUC p < 0.05 and drift AUC within 0.10 of baseline. **Action**: If real human data is missing, raise a `ValueError` and block the build. **DEPENDS ON** T039-gpt-final, T025b-final, T026, T017.
- [X] T041a [S] Block T041-final if `state/projects/...yaml` indicates `current_stage: unproven`. **DEPENDS ON** T017.
- [X] T042 [S] Flag "computationally efficient alternative" if `|AUC_drift - AUC_llm| ≤ 0.10`. **DEPENDS ON** T041-final.
- [X] T042b [S] [US3] **Efficiency Gate**: Validate that the drift method is flagged as 'computationally efficient alternative' if AUC is within 0.10 of the Flan-T5 baseline. **Action**: If the condition is met but not flagged, raise `ValueError` and block advancement. **DEPENDS ON** T041-final, T042.

## Phase N: Polish & Cross‑Cutting Concerns

- [X] T043a [S] Update `docs/quickstart.md` with new drift detection workflow and data loading instructions. **DEPENDS ON** T021d.
- [X] T043b [S] Update `docs/data-model.md` with new data model fields and schema definitions. **DEPENDS ON** T021d.
- [X] T044a [S] Run black and ruff on `code/` to enforce formatting and linting. **DEPENDS ON** T021d.
- [X] T044b [S] Remove unused imports and variables from `code/`. **DEPENDS ON** T021d.
- [X] T045-opt-impl [S] Implement batch size tuning logic in `benchmark_performance.py`. Output helper `get_optimal_batch_size`. **DEPENDS ON** T016a.
- [X] T045-opt-run [S] Run benchmark on a subset of logs using the logic from T045-opt-impl. **DEPENDS ON** T045-opt-impl.
- [X] T045-opt-report [S] Generate `optimization_report.json` with optimal batch size and strategy. **DEPENDS ON** T045-opt-run.
- [X] T045a [S] Implement `benchmark_performance.py` to run large‑scale log benchmark on `data/raw/agent_logs.csv` using optimal batch size; enforce ≤ 30 min runtime, raise `TimeoutError` otherwise. **Action**: If `data/raw/agent_logs.csv` is missing (i.e., T012f not completed), raise `FileNotFoundError` and fail the task. Do NOT skip. **DEPENDS ON** T045-opt-report, T012f.
- [X] T045b [S] Integrate benchmark into GitHub Actions workflow to fail the build if time threshold exceeded. **DEPENDS ON** T045a.
- [X] T046a [S] Implement `test_leetspeak_drift_score` (edge case). **DEPENDS ON** T021d.
- [X] T046b [S] Implement `test_obfuscation_drift_score`. **DEPENDS ON** T021d.
- [X] T046c [S] Implement `test_unicode_normalization`. **DEPENDS ON** T021d.
- [X] T047 [S] Run `python code/main.py --validate-only`; expect exit code 0 and schema‑validated outputs. **DEPENDS ON** T021d.
- [X] T048 [S] In `validation.py`, replace mock ground truth with `merged_annotations.csv` (from T035-real-ingest) for final US‑01 validation **IF** real human data is available. **Action**: This task swaps the proxy for real data in the final report. Raise `ValueError` if `merged_annotations.csv` is missing. **DEPENDS ON** T031b.
- [X] T049 [S] Implement `run_full_pipeline.py` to orchestrate US‑01, US‑02, and US‑03 pipelines in correct order. **DEPENDS ON** T041-final, T025b-final, T030b, T039-gpt-final.
- [X] T053 [S] **Deterministic Seed Enforcement**: Add a global seed setter in `config.py` that is called at the very start of `main.py` (T022) and `run_full_pipeline.py` (T049) to ensure all randomness (dataset shuffling, model initialization) is seeded with `RANDOM_SEED=42`. **Action**: This task must seed `random`, `numpy`, `torch`, and `datasets`. **DEPENDS ON**: T011a, T022, T049.

## Phase O: Execution Safety & Data Integrity (Revision Concerns)

**Purpose**: Address reviewer concerns regarding data sourcing, fallback safety, and reproducibility.

- [X] T050 [S] **Hardened Data Loader**: Refactor `data_loader.py` to ensure **NO** synthetic fallback exists. If `datasets.load_dataset` fails for `AI45Research/ATBench` or `mlfoundations/agent_logs`, raise `ConnectionError` or `FileNotFoundError` immediately. **Action**: Remove any `try/except` blocks that instantiate `generate_synthetic_data()` or return mock objects. Verify via `pytest` that a missing network connection results in a crash, not a silent mock. **DEPENDS ON**: T012a.
- [X] T051 [S] **Verified Taxonomy Source**: Update `fetch_taxonomy` to strictly use the local definition from `data/processed/taxonomy_agentdog.json`. **Action**: If the file is missing, the script must fail loudly with a clear error message. Do not implement a "paper derivation" fallback that generates taxonomy from scratch; instead, document the failure and require manual intervention to update the definition. **DEPENDS ON**: T012d-gen.
- [X] T052 [S] **Streaming Verification**: Add a unit test `test_streaming_memory_usage` that streams a substantial volume of records from `mlfoundations/agent_logs` and asserts that peak RAM usage remains within acceptable limits for streaming operations. **Action**: If the dataset is unreachable, the test must fail with `ConnectionError`. Do NOT use a synthetic fallback. **DEPENDS ON**: T012f.
- [X] T054 [S] **Artifact Checksum Validation**: Enhance `data_loader.py` to compute and store SHA256 checksums for all downloaded raw files in `data/checksums.json`. **Action**: On subsequent runs, verify the checksum of existing files against the stored value; if mismatch, re-download. **DEPENDS ON**: T012b.
- [X] T055 [S] **Annotation Ingestion Integrity**: Refactor `T035-real-ingest` logic to strictly validate that the `log_id`s in the incoming `human_annotations_for_bins.csv` match the `log_id`s in `annotation_request_bins.csv`. **Action**: Raise `ValueError` if any log_id is missing or if extra log_ids are present. **DEPENDS ON**: T030a-Stratify.

## Phase P: Final Review & Reporting (Revision Concerns)

**Purpose**: Ensure final outputs are traceable, reproducible, and meet all acceptance criteria without fabrication.

- [X] T056 [S] **Final Report Generation**: Generate `data/processed/final_report.md` summarizing US-01, US-02, and US-03 results. **Action**: Explicitly state whether results were derived from real human data. Include p-values, Cohen's d, Kappa, AUC-ROC, and inference times. **DEPENDS ON**: T026, T031c-KappaGate, T042b, T035-final-validation.
- [X] T057 [S] **Reproducibility Audit**: Create `docs/reproducibility_audit.md` listing all random seeds, dataset versions (checksums), and model versions used. **Action**: Verify that running `main.py` with `RANDOM_SEED=42` produces identical outputs to the current run. **DEPENDS ON**: T053, T054.
- [X] T058 [S] **Data Lineage Verification**: Generate a data lineage graph (text or diagram) in `docs/data_lineage.md` showing the flow from raw fetch to final metrics. **Action**: Ensure every metric in the final report can be traced back to a specific raw file and processing step. **DEPENDS ON**: T012a, T021d, T031b, T039-gpt-final.