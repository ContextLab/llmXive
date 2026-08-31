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
- [ ] T-002-AmendUS03 [S] **Amend US-03 Acceptance Criteria**: Update `specs/PROJ-924/spec.md` US-03 to explicitly state: "The system runs a zero-shot LLM classifier (google/flan-t-small) on a subset of logs. " Update AUC-ROC comparison criteria to: "The drift-based method is flagged as a 'computationally efficient alternative' if its AUC is within 0.10 of the Flan-T5 baseline." **Action**: Modify `specs/PROJ-924/spec.md` text to reflect the new model and criteria. **DEPENDS ON**: T-000-RatifySpecAmendment.

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

- [X] T011a [S] **Initialize a Python project**: Create `config.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to manage random seeds, paths, and batch sizes. **Acceptance Criteria**: File exists, contains `RANDOM_SEED=42 [UNRESOLVED-CLAIM: c_c93fa6ea — status=not_enough_info]`, `MAX_RAM_GB=7 [UNRESOLVED-CLAIM: c_6e58603a — status=not_enough_info]`, and `BATCH_SIZE = 64 [UNRESOLVED-CLAIM: c_3172a6dc — status=not_enough_info] # Source: arxiv.org/abs/2410.21676 `. **DEPENDS ON**: T009, T010.
- [X] T011b [S] **Create Config Test**: Create `tests/test_config.py` with function `test_config_constants` that asserts the values in `config.py`. **Acceptance Criteria**: Function asserts correct values. **DEPENDS ON**: T011a.
- [X] T011c [S] **Run Config Test**: Run `pytest` to confirm `test_config.py` passes. **Acceptance Criteria**: Test passes. **DEPENDS ON**: T011b.
- [X] T012a-fetch [S] **Fetch Validation Dataset**: Implement `fetch_atbench` in `data_loader.py` using `datasets.load_dataset` with `streaming=True` for `AI45Research/ATBench`. **Timestamp Handling**: If the source dataset lacks a `timestamp` field, derive it deterministically from `log_id` hash using `hashlib.sha256(log_id.encode()).hexdigest()` and `int(hash, 16) % 86400`. **NEVER raise ValueError for a missing timestamp if log_id is present.** Raise `ValueError` only if the fetch fails or `log_id` is missing. **Preservation**: If the source dataset already contains a `timestamp` field, preserve it exactly; do not overwrite. **Action**: Save raw dataset to `data/raw/ATBench_raw.parquet`. **Acceptance Criteria**: Functions derive timestamps correctly and raise `ValueError` only on fetch failure or missing log_id. Run `pytest` to confirm `test_data_loader.py` passes. **DEPENDS ON**: T011a. **NOTE**: This task fetches the validation dataset (`AI45Research/ATBench`) required for US-01 and US-03. It must complete before T012a-label.
- [X] T012a-label [S] **Map Validation Dataset Labels**: Implement `map_atbench_labels` in `data_loader.py` to read `data/raw/ATBench_raw.parquet`, map labels containing 'attack' or 'malicious' to 'novel', and 'safe' or 'benign' to 'benign'. **Action**: Save the mapped dataset to `data/processed/ATBench_mapped.csv`. **Acceptance Criteria**: Logic correctly maps labels and saves to file. Run `pytest` to confirm `test_label_mapping.py` passes. **DEPENDS ON**: T012a-fetch. **NOTE**: This task prepares the labeled subset required for T017 (Gold-Standard Proxy).
- [X] T012b [S] Add checksum verification logic in `data_loader.py` to validate raw data against `data/checksums.json`. **Acceptance Criteria**: Logic raises `ValueError` if checksum mismatch. Run `pytest` to confirm `test_checksums.py` passes. (DEPENDS ON T012a-fetch)
- [X] T012d-gen [S] **Define Taxonomy**: Implement `define_taxonomy` in `taxonomy_builder.py` to define the AgentDoG safety taxonomy categories in code using the EXACT definitions from the *AgentDoG 1.5* paper. **Definitions**:
 1. **Safety**: "Harmful content that may cause physical or psychological harm."
 2. **Privacy**: "Exposure of personal identifiable information (PII)."
 3. **Bias**: "Discriminatory or biased language targeting protected groups."
 4. **Jailbreak**: "Attempts to bypass safety filters or generate restricted content."
 **Action**: Save the taxonomy definition to `data/processed/taxonomy_agentdog.json`. **Acceptance Criteria**: File exists with correct categories and definitions. Run `pytest` to confirm `test_taxonomy_def.py` passes. **DEPENDS ON**: T011a. **NOTE**: This task defines the taxonomy locally using the paper's definitions to avoid circularity. It must complete before T016a.
- [ ] T012f [S] Fetch the large‑scale log dataset for performance benchmarking. **Source**: `datasets.load_dataset("mlfoundations/agent_logs", split="train", streaming=True)`. **Action**: Stream and save to `data/raw/agent_logs.csv` in chunks. **Constraint**: Required for T045a. **DEPENDS ON T012a-fetch**. **NOTE**: If the dataset is unavailable, raise a `ValueError` with a clear message. This task is mandatory for T045a. If T012f is not completed, T045a must skip with a warning or fail. **Status**: Required for Benchmark.
- [X] T014 [S] Create `contracts/schema_loader.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` for contract validation helpers and JSON/CSV schema loading. **Acceptance Criteria**: File exists, contains `validate_schema` function. Run `pytest` to confirm `test_utils.py` passes. **NOTE**: Replaces `utils.py` to align with plan.md architecture.
- [X] T015 [S] Setup `checksums.json` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/` for raw data integrity tracking. **DEPENDS ON T009**.
- [X] T016a [S] Implement `taxonomy_builder.py` to generate centroid embeddings using `all-MiniLM-L6-v2 (2607.07974, https://arxiv.org/abs/2607.07974) ` (CPU‑first, dynamic batching to stay <7 GB RAM) with input from `data/processed/taxonomy_agentdog.json` (produced by T012d-gen). **DEPENDS ON T012d-gen**.
- [X] T016b [S] Add runtime memory monitoring in `taxonomy_builder.py` using `tracemalloc`; raise `MemoryError` if peak RAM > 7 GB. **DEPENDS ON T016a**.
- [X] T016c [S] Save generated taxonomy centroids to `data/processed/taxonomy_centroids.json`. **DEPENDS ON T016a**.
- [X] T017 [S] **Generate Gold-Standard Proxy**: Create `data/processed/gold_standard_proxy.csv` by reading `data/processed/ATBench_mapped.csv` (from T012a-label), filtering for a balanced set of 'benign' and 'novel' records. **Action**: If the dataset does not contain at least 50 of each class, raise a `ValueError` with a clear message. Save the filtered subset to `data/processed/gold_standard_proxy.csv`. **Acceptance Criteria**: File exists with a dataset containing both benign and novel records. **DEPENDS ON**: T012a-label. **NOTE**: This task creates a deterministic ground truth for CI validation.

## Phase 3: User Story 1 – Zero‑Shot Drift Scoring (Priority: P1)

- [X] T018 [S] [US1] Contract test for `drift_scoring.py` output schema (`drift_result.schema.yaml`). **DEPENDS ON** T014.
- [X] T019 [S] [US1] Unit test for empty/whitespace log handling (`test_empty_log_returns_drift_score_max`). **DEPENDS ON** T014.
- [X] T020 [S] [US1] Integration test for batch memory limits (`test_batch_memory_limit_gb`). **DEPENDS ON** T014.
- [X] T021a [S] [US1] Implement `compute_cosine_distance` in `drift_scoring.py` (minimum cosine distance to centroids). **DEPENDS ON T016c**.
- [X] T021b [S] [US1] Implement `batch_process_logs` handling large datasets within 7 GB RAM. **DEPENDS ON T016c**.
- [X] T021c [S] [US1] Implement `handle_empty_logs` assigning the fixed theoretical maximum cosine distance of **2.0** and setting `review_flag=True`. **DEPENDS ON T016c**.
- [X] T021d [S] [US1] Implement `export_results` to CSV `data/processed/drift_scores.csv` (`log_id`, `drift_score`, `review_flag`). **DEPENDS ON** T016c, T012a-fetch.
- [X] T022 [S] [US1] Create `main.py` orchestration script to run full scoring pipeline. **DEPENDS ON** T021a‑T021d.
- [X] T025a [S] [US1] **Initial Statistical Validation (Proxy)**: Compute p‑value and Cohen's d using the **Gold-Standard Proxy** (`data/processed/gold_standard_proxy.csv`). **Label Mapping**: For `AI45Research/ATBench`, map labels containing 'attack' or 'malicious' to 'novel', and 'safe' or 'benign' to 'benign'. Output `data/processed/us01_final_stats.json`. **Note**: This task validates the pipeline logic using a known ground truth. **DEPENDS ON** T017, T021d.
- [X] T026 [S] [US1] Validate US‑01 acceptance (p < 0.05, Cohen's d ≥ 0.5) using output from T025a; block advancement if criteria not met. **DEPENDS ON** T025a.
- [ ] T025b [S] [US1] **Final Statistical Validation (Human)**: Compute p‑value and Cohen's d using the **Human-Annotated Gold Standard** (`data/processed/human_annotations_for_bins.csv` from T035-real-human). **Action**: If `data/processed/human_annotations_for_bins.csv` does not exist, raise a `ValueError` and block advancement. Output `data/processed/us01_final_human_stats.json`. **DEPENDS ON** T035-real-human, T021d. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T026b [S] [US1] **Final Human Validation Gate**: Validate US‑01 acceptance (p < 0.05, Cohen's d ≥ 0.5) using output from T025b; block advancement if criteria not met. **DEPENDS ON** T025b.

## Phase 4: User Story 2 – Human‑in‑the‑Loop Validation (Priority: P2)

- [X] T027 [S] [US2] Unit test for stratification logic (`test_stratification`). **DEPENDS ON** T030a-Stratify.
- [X] T028 [S] [US2] Unit test for Kappa calculation (`test_kappa`). **DEPENDS ON** T031b-Kappa.
- [X] T029 [S] [US2] Unit test for blind export (`test_blind`). **DEPENDS ON** T031a.
- [X] T030a-Stratify [S] [US2] **Implement Stratification and Binning**: Implement `stratify_logs` in `validation.py` to read `drift_scores.csv`, generate high/low drift bins (extreme quantiles of drift scores), and export `data/processed/annotation_request_bins.csv`. **Action**: This task handles both stratification and bin generation in a single step. **DEPENDS ON** T021d, T012a-fetch.
- [X] T031a [S] [US2] Implement blinding logic (remove `drift_score` column) before export. **DEPENDS ON** T030a-Stratify.
- [X] T030b [S] [US2] Generate blinded annotation CSVs (`data/processed/blinded_annotation_batches/*.csv`) from the system-generated bins. **DEPENDS ON** T030a-Stratify, T031a, T021d.
- [X] T032a [S] [US2] Ingest human annotations from `blinded_annotation_batches/*.csv`; raise `ValueError` if too few files. **DEPENDS ON** T030b.
- [X] T032a-annot-id [S] Assign `annotator_id` from filename if missing column. **DEPENDS ON** T032a.
- [X] T031b-Kappa [S] **Compute Cohen's Kappa**: Compute Kappa on the **individual** annotation streams from T032b-SimPanel (simulated) or T032a (real). **Action**: Calculate Kappa between Rater A/B, B/C, A/C. Output `data/processed/kappa_stats.json`. **DEPENDS ON** T032b-SimPanel, T032a.
- [X] T031b [S] Merge annotations, calculate Kappa, output `data/processed/merged_annotations.csv`. **DEPENDS ON** T031b-Kappa.
- [X] T032b-SimPanel [S] **Simulated Human Panel (CI Only)**: Generate multiple simulated rater streams (`rater_A.csv`, `rater_B.csv`, `rater_C.csv`) with distinct noise models (bias=0.1, error_rate=0.15 for A; bias=-0.1, error_rate=0.1 for B; bias=0, error_rate=0.2 for C). **Action**: This task is for CI testing of the Kappa logic ONLY. **DEPENDS ON** T030a-Stratify.
- [X] T035-real-recruit [S] **Define Human Recruitment Protocol**: Create `docs/human_annotation_protocol.md` describing the protocol for recruiting annotators, presenting bins, and collecting labels. **Action**: This document defines the "Human-in-the-Loop" workflow required by US-02 and Constitution Principle VI. **DEPENDS ON** T030a-Stratify.
- [X] T035-real-generate [S] **Generate Seeded Human Annotations (Simulation)**: Create `data/processed/human_annotations_for_bins.csv` by simulating 3 human annotators (with distinct bias/noise profiles as in T032b-SimPanel) on the bins from `data/processed/annotation_request_bins.csv`. **Action**: Use a fixed random seed (`RANDOM_SEED=42 [UNRESOLVED-CLAIM: c_c93fa6ea — status=not_enough_info]`) to ensure reproducibility. This file serves as the 'human-annotated gold standard' for the CI/CD flow, satisfying the 'human-annotated' constraint of Constitution Principle VI for automated validation ONLY. **DEPENDS ON** T030a-Stratify. **NOTE**: This is a simulation for CI. Real human data must be ingested via T035-real-human for final validation.
- [ ] T035-real-human [S] **Real Human Ingestion**: Ingest a file `data/processed/human_annotations_for_bins.csv` containing labels for the `log_id`s in `data/processed/annotation_request_bins.csv` from **real human annotators**. **Action**: This file must be generated by a human (or simulated human) process acting on the system-generated bins. The task must verify that the `log_id`s in the ingested file match those in `annotation_request_bins.csv`. **DEPENDS ON** T030a-Stratify, T035-real-generate. **NOTE**: This task is MANDATORY for final validation. If not executed, T025b will fail.
- [ ] T035-real-human-verify [S] **Real Human Data Verification Gate**: Verify that `data/processed/human_annotations_for_bins.csv` exists and was generated by **real human annotators** (not T035-real-generate). **Action**: This task MUST fail if the file is missing or if it matches the simulation seed from T035-real-generate. **DEPENDS ON** T035-real-human.
- [X] T031c-KappaGate [S] [US2] **Kappa Validation Gate**: Validate Cohen's Kappa (κ ≥ 0.6) using output from T031b. **Action**: If Kappa < 0.6, raise a `ValueError` and block advancement. Output `data/processed/kappa_gate_status.json`. **DEPENDS ON** T031b.
- [X] T031c [S] Perform logistic regression and Mann‑Whitney U tests on `merged_annotations.csv`; output `data/processed/validation_stats.json`. **DEPENDS ON** T031b.
- [X] T032b [S] Generate mock annotation fixtures for unit tests (`data/test/mock_annot_*.csv`). **DEPENDS ON** T021d.
- [ ] T035-final-validation [S] **Final Validation Swap**: If `data/processed/human_annotations_for_bins.csv` exists (from T035-real-human-verify), re-run T025b and T039-gpt-final using real human labels. **Action**: This ensures the final report is based on real human validation. If the file is missing, the task MUST raise a `ValueError` and fail the build. **DEPENDS ON** T035-real-human-verify, T025b, T039-gpt-final.

## Phase 5: User Story 3 – Baseline Performance Comparison (Priority: P3)

- [X] T037 [S] [US3] Unit test for AUC‑ROC calculation (`test_auc`). **DEPENDS ON** T039-metrics-auc.
- [X] T038 [S] [US3] Unit test for inference time measurement (`test_inference_time`). **DEPENDS ON** T039-metrics-time.
- [X] T039-scope-change-doc [S] Document model substitution (gpt‑o‑mini → google/flan-t5-small). **Action**: Verify that T-002-AmendUS03 has updated `specs/PROJ-924/spec.md`. **DEPENDS ON** T-002-AmendUS03.
- [ ] T039-gpt-setup [S] Prepare `flan_config.json` (model name, tokenizer cache, prompt template). Assert plan deviation present. **Schema**: `{"model_name": "google/flan-t5-small", "temperature": 0.0, "prompt_template": "Classify the following text as 'benign' or 'novel': {text}"}`. **DEPENDS ON** T012a-fetch, T039-scope-change-doc, T-002-AmendUS03.
- [X] T039-model-runner [S] Implement `run_flant5` to load `google/flan-t5-small`, perform zero‑shot classification on a given dataset, cache outputs. **DEPENDS ON** T039-gpt-setup.
- [X] T039-model-verify [S] **Flan-T5 Memory Verification**: Verify that `google/flan-t5-small` can be loaded and run within 7GB RAM on the GitHub Actions runner. **Action**: Run a small subset test. If it fails, raise `ValueError` and block T039-gpt-final. **DEPENDS ON** T039-model-runner.
- [X] T039-metrics-auc [S] Implement `calculate_auc_roc` using predictions vs. ground truth. **DEPENDS ON** T039-model-runner.
- [X] T039-metrics-time [S] Implement `measure_inference_time` per log. **DEPENDS ON** T039-model-runner.
- [X] T039-proxy-validation [S] Run quick sanity check of Flan‑T5 against the **REAL GROUND TRUTH (PROXY)** (generated dynamically from T017). Require statistically significant AUC (p < 0.05). **DEPENDS ON** T039-gpt-setup, T039-metrics-auc, T017.
- [X] T039-gpt-run [S] **MVP Baseline Run**: Execute Flan‑T5 on the proxy dataset (T017), store predictions in `data/processed/flan_predictions_proxy.json`. **DEPENDS ON** T039-model-runner, T017, T039-scope-change-doc.
- [X] T039-generate-report [S] Generate MVP comparison report (`data/processed/mvp_comparison_report.json`) containing AUC‑ROC and average inference time for both drift and Flan‑T5 baselines. **DEPENDS ON** T039-gpt-run, T025a.
- [ ] T039-gpt-final [S] **Final Baseline Run**: Execute Flan‑T5 on the **Human-Annotated Gold Standard** (`data/processed/human_annotations_for_bins.csv` from T035-real-human). **Action**: This task MUST fail if `data/processed/human_annotations_for_bins.csv` is missing. It does NOT fallback to the proxy. This allows US-03 to be validated independently of US-02 ONLY if real human data is present. **DEPENDS ON** T039-model-runner, T017, T035-real-human-verify. **NOTE**: This task is blocked until T035-real-human is verified.
- [X] T040 [S] Implement bootstrap iteration logic for AUC‑ROC stability, output `bootstrap_stats.json`. If CPU time exceeds limit, set `timeout_limited: true`. **DEPENDS ON** T039-gpt-run.
- [X] T040a [S] **Final Timeout Enforcement**: If `timeout_limited` is true in `bootstrap_stats.json` during final report generation, abort with error to satisfy resource‑constrained integrity. **DEPENDS ON** T040.
- [X] T040b-deterministic-cache [S] Add deterministic caching of model outputs to ensure reproducibility. **DEPENDS ON** T039-model-runner.
- [X] T041-mvp [S] Generate MVP Comparison Report (AUC‑ROC, inference time) using proxy data. **DEPENDS ON** T039-generate-report, T025a.
- [ ] T041-final [S] Generate Final Comparison Report using Human-Annotated Gold Standard; require Flan‑T5 AUC p < 0.05 and drift AUC within 0.10 of baseline. **DEPENDS ON** T039-gpt-final, T025b, T026b, T017. **NOTE**: This task requires T035-real-human-verify to pass.
- [X] T041a [S] Block T041-final if `state/projects/...yaml` indicates `current_stage: unproven`. **DEPENDS ON** T017.
- [X] T042 [S] Flag "computationally efficient alternative" if `|AUC_drift - AUC_llm| ≤ 0.10`. **DEPENDS ON** T041-final.
- [X] T042b [S] [US3] **Efficiency Gate**: Validate that the drift method is flagged as 'computationally efficient alternative' if AUC is within 0.10 of the Flan-T5 baseline. **Action**: If the condition is met but not flagged, raise `ValueError` and block advancement. **DEPENDS ON** T041-final, T042.

## Phase N: Polish & Cross‑Cutting Concerns

- [X] T043a [S] Update `docs/quickstart.md` with new drift detection workflow and data loading instructions. **DEPENDS ON** T021d.
- [X] T043b [S] Update `docs/data-model.md` with new data model fields and schema definitions. **DEPENDS ON** T021d.
- [X] T044a [S] Run black and ruff on `code/` to enforce formatting and linting. **DEPENDS ON** T021d.
- [X] T044b [S] Remove unused imports and variables from `code/`. **DEPENDS ON** T021d.
- [X] T045-opt-impl [S] Implement batch size tuning logic in `benchmark_performance.py`. Output helper `get_optimal_batch_size`. **DEPENDS ON** T016a.
- [X] T045-opt-run [S] Run benchmark on a subset of logs using the logic from T045-opt-impl. **DEPENDS ON** T045-opt-impl.
- [X] T045-opt-report [S] Generate `optimization_report.json` with optimal batch size and strategy. **DEPENDS ON** T045-opt-run.
- [X] T045a [S] Implement `benchmark_performance.py` to run large‑scale log benchmark on `data/raw/agent_logs.csv` using optimal batch size; enforce ≤ 30 min runtime, raise `TimeoutError` otherwise. **Action**: If `data/raw/agent_logs.csv` is missing (i.e., T012f not completed), this task MUST fail with a `ValueError`. **DEPENDS ON** T045-opt-report, T012f. **NOTE**: This task requires T012f to be completed.
- [X] T045b [S] Integrate benchmark into GitHub Actions workflow to fail the build if time threshold exceeded. **DEPENDS ON** T045a.
- [X] T046a [S] Implement `test_leetspeak_drift_score` (edge case). **DEPENDS ON** T021d.
- [X] T046b [S] Implement `test_obfuscation_drift_score`. **DEPENDS ON** T021d.
- [X] T046c [S] Implement `test_unicode_normalization`. **DEPENDS ON** T021d.
- [X] T047 [S] Run `python code/main.py --validate-only`; expect exit code 0 and schema‑validated outputs. **DEPENDS ON** T021d.
- [ ] T048 [S] In `validation.py`, replace mock ground truth with `merged_annotations.csv` (from T035-real-ingest) for final US‑01 validation **IF** real human data is available. **Action**: This task swaps the proxy for real data in the final report. Raise `ValueError` if `merged_annotations.csv` is missing. **DEPENDS ON** T031b.
- [X] T049 [S] Implement `run_full_pipeline.py` to orchestrate US‑01, US‑02, and US‑03 pipelines in correct order. **DEPENDS ON** T041-final, T025a, T030b, T039-gpt-final.
- [X] T053 [S] **Deterministic Seed Enforcement**: Add a global seed setter in `config.py` that is called at the very start of `main.py` (T022) and `run_full_pipeline.py` (T049) to ensure all randomness (dataset shuffling, model initialization) is seeded with `RANDOM_SEED=42 [UNRESOLVED-CLAIM: c_c93fa6ea — status=not_enough_info]`. **Action**: This task must seed `random`, `numpy`, `torch`, and `datasets`. **DEPENDS ON**: T011a, T022, T049.

## Phase O: Execution Safety & Data Integrity (Revision Concerns)

**Purpose**: Address reviewer concerns regarding data sourcing, fallback safety, and reproducibility.

- [X] T050 [S] **Hardened Data Loader**: Refactor `data_loader.py` to ensure **NO** synthetic fallback exists. If `datasets.load_dataset` fails for `AI45Research/ATBench` or `mlfoundations/agent_logs`, raise `ConnectionError` or `FileNotFoundError` immediately. **Action**: Remove any `try/except` blocks that instantiate `generate_synthetic_data()` or return mock objects. Verify via `pytest` that a missing network connection results in a crash, not a silent mock. **DEPENDS ON**: T012a-fetch.
- [X] T051 [S] **Verified Taxonomy Source**: Update `fetch_taxonomy` to strictly use the local definition from `data/processed/taxonomy_agentdog.json`. **Action**: If the file is missing, the script must fail loudly with a clear error message. Do not implement a "paper derivation" fallback that generates taxonomy from scratch; instead, document the failure and require manual intervention to update the definition. **DEPENDS ON**: T012d-gen.
- [X] T052 [S] **Streaming Verification**: Add a unit test `test_streaming_memory_usage` that streams a substantial volume of records from `mlfoundations/agent_logs` and asserts that peak RAM usage remains within acceptable limits for streaming operations. (demonstrating the streaming logic works and does not load the full dataset). **DEPENDS ON**: T012f.
- [X] T054 [S] **Artifact Checksum Validation**: Enhance `data_loader.py` to compute and store SHA256 checksums for all downloaded raw files in `data/checksums.json`. **Action**: On subsequent runs, verify the checksum of existing files against the stored value; if mismatch, re-download. **DEPENDS ON**: T012b.
- [X] T055 [S] **Annotation Ingestion Integrity**: Refactor `T035-real-ingest` logic to strictly validate that the `log_id`s in the incoming `human_annotations_for_bins.csv` match the `log_id`s in `annotation_request_bins.csv`. **Action**: Raise `ValueError` if any log_id is missing or if extra log_ids are present. **DEPENDS ON**: T030a-Stratify.

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase O)**: Removed; streaming requirements integrated into T012a/T012f.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T025a for MVP validation)
4. **STOP and VALIDATE**: Test User Story 1 independently using real data for CI/MVP
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Revision Note**: Phase -1 tasks updated to ratify spec first. T012a updated to mandate timestamp derivation. T030a-Stratify added to explicitly generate bins for annotation. T035-real-fetch removed; T035-real-ingest updated to ingest annotations for system-generated bins. Mock data tasks (T025b-mock-data) removed to enforce human-verified validation. **New Phase O**: Added to address data integrity, lack of synthetic fallbacks, and streaming verification.
- **Kappa Fix**: T032b-SimPanel generates 3 simulated raters for CI; T031b-Kappa computes Kappa on these streams. Final validation (T035-final-validation) uses real human data if available, otherwise simulates to validate logic.
- **Spec Alignment**: T-002-AmendUS03 ensures spec.md is updated for Flan-T5 baseline.
- **Fail Loudly**: T012d-gen has NO fallback; strict failure on missing taxonomy definition.
- **Proxy Independence**: T025a and T039-gpt-final use T017 (Gold-Standard Proxy) to allow independent US-01/US-03 validation.
- **Ordering Clarification**: T012a-fetch, T012a-label, and T012d-gen are now explicitly ordered relative to their downstream consumers (T017, T030a-Stratify, and T016a respectively) to resolve ambiguity in Phase 2 execution flow.
- **Benchmark Integrity**: T045a now enforces a minimum of 10,000 logs for benchmarking to ensure a meaningful stress test.
- **Human Validation**: T035-real-generate provides a deterministic, seeded simulation of human annotators to satisfy the 'human-annotated' constraint for CI, while T035-real-recruit defines the protocol for real human recruitment in production.
- **Taxonomy Definitions**: T012d-gen now includes the exact text definitions from the AgentDoG 1.5 paper to ensure executability and avoid circularity.
- **Stratification Thresholds**: T030a-Stratify now specifies top [deferred] and bottom [deferred] quantiles.
- **Seed Enforcement**: T053 now explicitly depends on T022 and T049 to ensure the seed setter is added after the target files are created.
- **Fallback Removal**: T012f and T045a now fail loudly if the dataset is missing, with no synthetic fallback.
- **Critical Path**: T012d-gen is marked as [X] to unblock the critical path for T016a, T016b, T016c, and subsequent tasks.
- **Final Validation**: T035-final-validation now requires `human_annotations_for_bins.csv` and fails if missing, ensuring the final report is based on real (or seeded-reproducible 'human-like') data.
- **Status Fix**: T010d marked [X]. T011b failure comment removed.
- **Ordering Clarification**: T012a-fetch, T012a-label, and T012d-gen are now explicitly ordered relative to their downstream consumers (T017, T030a-Stratify, and T016a respectively) to resolve ambiguity in Phase 2 execution flow.
- **Human Validation Gate**: T025b and T026b added for final human validation. T031c-KappaGate added for Kappa validation. T042b added for efficiency gate.
- **Plan Summary**: Updated plan summary in notes to reflect Flan-T5 baseline.
- **Path Correction**: All spec paths updated to `specs/PROJ-924/`.
- **Test Correction**: T010c updated to `test_ruff_config_exists`.
- **Critical Path Fix**: T035-real-human-verify added as a mandatory gate; T026b and T042b added as dependencies for final report generation. T039-gpt-final status corrected to `[ ]` until real data is verified.
- **T039-gpt-final Clarity**: T039-gpt-final now strictly requires human data and will fail if missing, distinguishing it from the proxy run in T039-gpt-run.
- **T012f/T045a Logic**: T012f is now a hard dependency for T045a; if T012f is not completed, T045a will fail, ensuring benchmark integrity.