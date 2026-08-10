# Tasks: llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

**Input**: Design documents from `/specs/001-llmxive-drift-detection/`
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

## Phase -2: Spec Amendment (Critical Pre‑requisite)

- [ ] T-001-PlanDeviation [S] **Plan Deviation Documentation**: Document the required substitution of `gpto-mini` with `google/flan-t-small` in US‑03 due to memory constraints. **Action**: Update `plan.md` and `tasks.md` to explicitly state this deviation from the spec's baseline. **Rationale**: Aligns the implementation plan with feasible execution while maintaining traceability to the spec (SSOT).

## Phase 0: Scope Verification (Post‑Spec Fix)

- [ ] T000-ScopeVerify [S] [US3] **Verify Plan Deviation**: Confirm `plan.md` and `tasks.md` contain the documented substitution of `gpto-mini` with `google/flan-t5-small`. **Action**: Read `plan.md` and `tasks.md` and assert the updated text is present. **DEPENDS ON**: T-001-PlanDeviation.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001a [S] Initialize project directory structure: Create and verify directories `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, `tests/`, `data/raw/`, `data/processed/`, `data/test/`, `specs/`, `docs/`, and `specs/001-llmxive-drift-detection/`. **Acceptance Criteria**: All directories exist.
- [X] T001b [S] Verify directory structure: Create `tests/test_setup.py` with function `test_directories_exist` that asserts the existence of the directories created in T001a. Run `pytest` to confirm `test_directories_exist` passes. **Acceptance Criteria**: `test_directories_exist` passes. (DEPENDS ON T001a)
- [X] T009 Initialize a Python project with `requirements.txt` (sentence-transformers, scikit-learn, pandas, numpy, datasets, jsonschema, statsmodels, pytest, transformers, accelerate, llama-cpp-python) using a modern, stable Python 3 release.
- [X] T010 [S] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/`. **Acceptance Criteria**:
 1. Create `.ruff.toml` with EXACT content:
 ```toml
 [lint]
 select = ["E", "F", "W", "I"]
 ignore = []
 [format]
 quote-style = "double"
 ```
 2. Create `pyproject.toml` with EXACT content (including project metadata):
 ```toml
 [project]
 name = "agentdog-drift"
 version = "0.1.0"

 [tool.black]
 line-length = 88
 target-version = ['py']
 ```
 3. Verify `.ruff.toml` and `pyproject.toml` exist and are non-empty via `pytest` (test `test_ruff_config_exists` and `test_black_config_exists`).

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T011 [S] Create `config.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to manage random seeds, paths, and batch sizes. **Acceptance Criteria**: File exists, contains `RANDOM_SEED=42`, `MAX_RAM_GB=7`, and `BATCH_SIZE = 64 # See arxiv.org/abs/2410.21676`. Run `pytest` to confirm `test_config.py` passes.
- [ ] T012a [S] Implement `fetch_advbench` and `fetch_hf4` functions in `data_loader.py` using `datasets.load_dataset` with streaming; ensure no synthetic fallbacks. **Timestamp Handling**: If the source dataset lacks a `timestamp` field, generate a deterministic placeholder timestamp via `T012a-timestamp-handling` (see below). **Acceptance Criteria**: Functions raise `ValueError` on fetch failure. Run `pytest` to confirm `test_data_loader.py` passes.
- [ ] T012a-timestamp-handling [S] Generate deterministic, varied placeholder timestamps for records missing a timestamp (e.g., hash UUID modulo a year range). **Acceptance Criteria**: Returns a `datetime` that differs per `log_id`. Used by any task needing timestamps.
- [X] T012b [S] Add checksum verification logic in `data_loader.py` to validate raw data against `data/checksums.json`. **Acceptance Criteria**: Logic raises `ValueError` if checksum mismatch. Run `pytest` to confirm `test_checksums.py` passes. (DEPENDS ON T012a)
- [ ] T012c [S] Generate static test fixture from real data (AdvBench/HF4) to `data/test_static_logs.json` for US‑01 testing; ensure this file contains `log_id`, `text`, `label`, and `timestamp` columns. **Acceptance Criteria**: File exists, valid JSON. **DEPENDS ON T012a**.
- [ ] T012d-fixed [S] **Fetch Taxonomy**: Implement `fetch_taxonomy` in `data_loader.py` to load the fixed AgentDoG safety taxonomy from `. If unreachable or non‑200, raise `FileNotFoundError`. No local fallback. **DEPENDS ON**: T009, T010.
- [ ] T012e-real-proxy [S] [US1] Generate **REAL GROUND TRUTH (PROXY)** fixture from AdvBench/OWASP labels to `data/test/real_ground_truth_proxy.json`. Logic maps known attack labels to `novel` and safe labels to `benign`. Deterministic UUIDs and timestamps are used. **DEPENDS ON T012a, T012d-fixed**.
- [ ] T012e2-novelty-proxy [S] [US1] Generate **NOVELTY PROXY** fixture to `data/test/novelty_proxy.json`. Takes logs from the real proxy and applies controlled perturbations (e.g., synonym replacement, token shuffling) to simulate unseen attacks, assigning label `novel`. Provides a realistic novelty test set. **DEPENDS ON T012e-real-proxy**.
- [ ] T012f [S] Fetch the large‑scale log dataset for performance benchmarking. **Source**: `datasets.load_dataset("mlfoundations/agent_logs", split="train", streaming=False)`. **Action**: Save to `data/raw/agent_logs.csv`. **Constraint**: Required for T045a. **DEPENDS ON T012a**.
- [ ] T014 [S] Create `utils.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` for contract validation helpers and JSON/CSV schema loading. **Acceptance Criteria**: File exists, contains `validate_schema` function. Run `pytest` to confirm `test_utils.py` passes.
- [ ] T015 [S] Setup `checksums.json` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/` for raw data integrity tracking. **DEPENDS ON T009**.
- [ ] T016a [S] Implement `taxonomy_builder.py` to generate centroid embeddings using `all-MiniLM-L-v2` (CPU‑first, dynamic batching to stay <7 GB RAM) with input from `data/raw/taxonomy_agentdog.json` (produced by T012d-fixed). **DEPENDS ON T012d-fixed**.
- [ ] T016b [S] Add runtime memory monitoring in `taxonomy_builder.py` using `tracemalloc`; raise `MemoryError` if peak RAM > 7 GB. **DEPENDS ON T016a**.
- [ ] T016c [S] Save generated taxonomy centroids to `data/processed/taxonomy_centroids.json`. **DEPENDS ON T016a**.

## Phase 3: User Story 1 – Zero‑Shot Drift Scoring (Priority: P1)

- [ ] T018 [S] [US1] Contract test for `drift_scoring.py` output schema (`drift_result.schema.yaml`). **DEPENDS ON** T021d.
- [ ] T019 [S] [US1] Unit test for empty/whitespace log handling (`test_empty_log_returns_drift_score_max`). **DEPENDS ON** T021c.
- [ ] T020 [S] [US1] Integration test for batch memory limits (`test_batch_memory_limit_7gb`). **DEPENDS ON** T021b.
- [ ] T021a [S] [US1] Implement `compute_cosine_distance` in `drift_scoring.py` (minimum cosine distance to centroids). **DEPENDS ON T016c**.
- [ ] T021b [S] [US1] Implement `batch_process_logs` handling large datasets within 7 GB RAM. **DEPENDS ON T016c**.
- [ ] T021c [S] [US1] Implement `handle_empty_logs` assigning the dynamic theoretical maximum cosine distance and setting `review_flag=True`. **DEPENDS ON T016c**.
- [ ] T021d [S] [US1] Implement `export_results` to CSV `data/processed/drift_scores.csv` (`log_id`, `drift_score`, `review_flag`). **DEPENDS ON** T016c, T012a.
- [ ] T022 [S] [US1] Create `main.py` orchestration script to run full scoring pipeline. **DEPENDS ON** T021a‑T021d.
- [ ] T025a [S] [US1] **MVP Statistical Validation (Novelty Proxy)**: Compute p‑value and Cohen's d using the **NOVELTY PROXY** (`data/test/novelty_proxy.json`) against benign logs from the real proxy. Output `data/processed/us01_mvp_stats.json`. **DEPENDS ON** T012e2-novelty-proxy, T021d.
- [ ] T025b [S] [US1] **Final Statistical Validation**: Compute p‑value and Cohen's d using the **Human‑Annotated Gold Standard** (`data/processed/merged_annotations.csv`). Output `data/processed/us01_final_stats.json`. **DEPENDS ON** T031b, T035s (or T035-real for final run).
- [ ] T026 [S] [US1] Validate US‑01 acceptance (p < 0.05, Cohen's d ≥ 0.5) using output from T025b; block advancement if criteria not met. **DEPENDS ON** T025b.

## Phase 4: User Story 2 – Human‑in‑the‑Loop Validation (Priority: P2)

- [ ] T027 [S] [US2] Unit test for stratification logic (`test_stratification`). **DEPENDS ON** T030a.
- [ ] T028 [S] [US2] Unit test for Kappa calculation (`test_kappa`). **DEPENDS ON** T031b-Kappa.
- [ ] T029 [S] [US2] Unit test for blind export (`test_blind`). **DEPENDS ON** T031a.
- [ ] T030a [S] [US2] Implement `stratify_logs` reading `drift_scores.csv` and producing high/low drift bins. **DEPENDS ON** T021d, T012a.
- [ ] T030a-streaming [S] [US2] **Streaming Stratification**: `stratify_logs_streaming` reads `drift_scores.csv` line‑by‑line, extracts top/bottom percentiles without loading whole file into memory. **DEPENDS ON** T030a.
- [ ] T031a [S] [US2] Implement blinding logic (remove `drift_score` column) before export. **DEPENDS ON** T030a.
- [ ] T030b [S] [US2] Generate blinded annotation CSVs (`data/processed/blinded_annotation_batches/*.csv`). **DEPENDS ON** T030a, T031a, T021d.
- [ ] T032a [S] [US2] Ingest human annotations from `blinded_annotation_batches/*.csv`; raise `ValueError` if too few files. **DEPENDS ON** T030b.
- [ ] T032a-annot-id [S] Assign `annotator_id` from filename if missing column. **DEPENDS ON** T032a.
- [ ] T031b-Kappa [S] Compute Cohen's Kappa on merged annotations. **DEPENDS ON** T032a-annot-id.
- [ ] T031b [S] Merge annotations, calculate Kappa, output `data/processed/merged_annotations.csv`. **DEPENDS ON** T032a, T031b-Kappa.
- [ ] T035s [S] **Simulated Gold Standard Generation**: Produce a deterministic `merged_annotations.csv` with three synthetic annotators (labels randomly assigned but reproducible via fixed seed). Enables CI testing without real humans. **DEPENDS ON** T021d (to obtain log IDs).
- [ ] T035-real [S] **Real Multi‑Annotator Interface**: Load real annotation files from `blinded_annotation_batches/`. If missing, raise `FileNotFoundError` with clear message. In "research" mode (config flag), allow fallback to simulated file (`T035s`); in "final" mode, require real files. **Note**: Real human annotation is a manual, out-of-band process for research validation; the CI pipeline uses T035s for reproducibility. **DEPENDS ON** T030b, T035s.
- [ ] T031c [S] Perform logistic regression and Mann‑Whitney U tests on `merged_annotations.csv`; output `data/processed/validation_stats.json`. **DEPENDS ON** T031b.
- [ ] T032b [S] Generate mock annotation fixtures for unit tests (`data/test/mock_annot_*.csv`). **DEPENDS ON** T021d.

## Phase 5: User Story 3 – Baseline Performance Comparison (Priority: P3)

- [ ] T037 [S] [US3] Unit test for AUC‑ROC calculation (`test_auc`). **DEPENDS ON** T039-metrics-auc.
- [ ] T038 [S] [US3] Unit test for inference time measurement (`test_inference_time`). **DEPENDS ON** T039-metrics-time.
- [ ] T039-scope-change-doc [S] Document model substitution (gpto‑mini → google/flan‑t5‑small). **DEPENDS ON** T-001-PlanDeviation.
- [ ] T039-gpt-setup [S] Prepare `flan_config.json` (model name, tokenizer cache, prompt template). Assert plan deviation present. **DEPENDS ON** T012e-real-proxy, T039-scope-change-doc, T000-ScopeVerify.
- [ ] T039-model-runner [S] Implement `run_flant5` to load `google/flan-t5-small`, perform zero‑shot classification on a given dataset, cache outputs. **DEPENDS ON** T039-gpt-setup.
- [ ] T039-metrics-auc [S] Implement `calculate_auc_roc` using predictions vs. ground truth. **DEPENDS ON** T039-model-runner.
- [ ] T039-metrics-time [S] Implement `measure_inference_time` per log. **DEPENDS ON** T039-model-runner.
- [ ] T039-proxy-validation [S] Run quick sanity check of Flan‑T5 against the **REAL GROUND TRUTH (PROXY)** (`data/test/real_ground_truth_proxy.json`). Require statistically significant AUC (p < 0.05). **DEPENDS ON** T039-gpt-setup, T039-metrics-auc.
- [ ] T039-gpt-run [S] **MVP Baseline Run**: Execute Flan‑T5 on the proxy dataset, store predictions in `data/processed/flan_predictions_proxy.json`. **DEPENDS ON** T039-model-runner, T012e-real-proxy, T039-scope-change-doc.
- [ ] T039-generate-report [S] Generate MVP comparison report (`data/processed/mvp_comparison_report.json`) containing AUC‑ROC and average inference time for both drift and Flan‑T5 baselines. **DEPENDS ON** T039-gpt-run, T025a.
- [ ] T039-gpt-final [S] **Final Baseline Run**: Execute Flan‑T5 on the **Simulated Gold Standard** (`data/processed/merged_annotations.csv` from T035s). **DEPENDS ON** T035s, T039-model-runner.
- [ ] T040 [S] Implement bootstrap iteration logic for AUC‑ROC stability, output `bootstrap_stats.json`. If CPU time exceeds limit, set `timeout_limited: true`. **DEPENDS ON** T039-gpt-run.
- [ ] T040a [S] **Final Timeout Enforcement**: If `timeout_limited` is true in `bootstrap_stats.json` during final report generation, abort with error to satisfy resource‑constrained integrity. **DEPENDS ON** T040.
- [ ] T040b-deterministic-cache [S] Add deterministic caching of model outputs to ensure reproducibility. **DEPENDS ON** T039-model-runner.
- [ ] T041-mvp [S] Generate MVP Comparison Report (AUC‑ROC, inference time) using proxy data. **DEPENDS ON** T039-generate-report, T025a.
- [ ] T041-final [S] Generate Final Comparison Report using simulated gold standard; require Flan‑T5 AUC p < 0.05 and drift AUC within 0.10 of baseline. **DEPENDS ON** T039-gpt-final, T025b, T035s.
- [ ] T041a [S] Block T041-final if `state/projects/...yaml` indicates `current_stage: unproven`. **DEPENDS ON** T035s.
- [ ] T042 [S] Flag "computationally efficient alternative" if `|AUC_drift - AUC_llm| ≤ 0.10`. **DEPENDS ON** T041-final.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T043a [S] Update `docs/quickstart.md` with new drift detection workflow and data loading instructions. **DEPENDS ON** T021d.
- [ ] T043b [S] Update `docs/data-model.md` with new data model fields and schema definitions. **DEPENDS ON** T021d.
- [ ] T044a [S] Run black and ruff on `code/` to enforce formatting and linting. **DEPENDS ON** T021d.
- [ ] T044b [S] Remove unused imports and variables from `code/`. **DEPENDS ON** T021d.
- [ ] T045-opt-impl [S] Implement batch size tuning logic in `benchmark_performance.py`. Output helper `get_optimal_batch_size`. **DEPENDS ON** T016a.
- [ ] T045-opt-run [S] Run benchmark on a subset of logs using the logic from T045-opt-impl. **DEPENDS ON** T045-opt-impl.
- [ ] T045-opt-report [S] Generate `optimization_report.json` with optimal batch size and strategy. **DEPENDS ON** T045-opt-run.
- [ ] T045a [S] Implement `benchmark_performance.py` to run large‑scale log benchmark on `data/raw/agent_logs_100k.csv` using optimal batch size; enforce ≤ 30 min runtime, raise `TimeoutError` otherwise. **DEPENDS ON** T045-opt-report, T012f.
- [ ] T045b [S] Integrate benchmark into GitHub Actions workflow to fail the build if time threshold exceeded. **DEPENDS ON** T045a.
- [ ] T046a [S] Implement `test_leetspeak_drift_score` (edge case). **DEPENDS ON** T021d.
- [ ] T046b [S] Implement `test_obfuscation_drift_score`. **DEPENDS ON** T021d.
- [ ] T046c [S] Implement `test_unicode_normalization`. **DEPENDS ON** T021d.
- [ ] T047 [S] Run `python code/main.py --validate-only`; expect exit code 0 and schema‑validated outputs. **DEPENDS ON** T021d.
- [ ] T048 [S] In `validation.py`, replace mock ground truth with `merged_annotations.csv` for final US‑01 validation. **DEPENDS ON** T031b.
- [ ] T049 [S] Implement `run_full_pipeline.py` to orchestrate US‑01, US‑02, and US‑03 pipelines in correct order. **DEPENDS ON** T041-final, T025b, T030b, T039-gpt-final.