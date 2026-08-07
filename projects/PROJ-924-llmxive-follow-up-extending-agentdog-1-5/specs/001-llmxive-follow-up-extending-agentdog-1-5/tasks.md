# Tasks: llmXive Follow-up: Extending AgentDoG 1.5 with Zero-Shot Drift Detection

**Input**: Design documents from `/specs/001-llmxive-drift-detection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The specification explicitly requires statistical validation and contract tests. [UNRESOLVED-CLAIM: c_80e7803d — status=not_enough_info]

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (depends on specific prior task in same phase)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/`
- Paths shown below assume single project structure per `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001-structure [P] Initialize project directory structure: Create and verify directories `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, `tests/`, `data/raw/`, `data/processed/`, `data/test/`, `specs/`, `docs/`, and `specs/001-llmxive-drift-detection/`
- [X] T009 Initialize a Python project with `requirements.txt` (sentence-transformers, scikit-learn, pandas, numpy, datasets, jsonschema, statsmodels, pytest, transformers, accelerate, llama-cpp-python) using a modern, stable Python 3 release.
- [ ] T010 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/`. **Acceptance Criteria**:
 1. Create `.ruff.toml` with EXACT content:
 ```toml
 [lint]
 select = ["E", "F", "W", "I"]
 ignore = []
 [format]
 quote-style = "double"
 ```
 2. Create `pyproject.toml` with EXACT content:
 ```toml
 [tool.black]
 line-length = 88
 target-version = ['py311']
 ```
 3. Verify `.ruff.toml` and `pyproject.toml` exist and are non-empty via `pytest` (test `test_ruff_config_exists` and `test_black_config_exists`).
 **Note**: This task resolves the previous failure where `.ruff.toml` was missing by explicitly defining its content.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 [S] Create `config.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to manage random seeds, paths, and batch sizes. **Acceptance Criteria**: File exists, contains `RANDOM_SEED=42`, `MAX_RAM_GB=7`, and `BATCH_SIZE=64`. Run `pytest` to confirm `test_config.py` passes.
- [ ] T012a [S] Implement `fetch_advbench` and `fetch_hf4` functions in `data_loader.py` using `datasets.load_dataset` with streaming; ensure no synthetic fallbacks. **Acceptance Criteria**: Functions raise `ValueError` on fetch failure. Run `pytest` to confirm `test_data_loader.py` passes.
- [X] T012b [S] Add checksum verification logic in `data_loader.py` to validate raw data against `data/checksums.json`. **Acceptance Criteria**: Logic raises `ValueError` if checksum mismatch. Run `pytest` to confirm `test_checksums.py` passes. (DEPENDS ON T012a)
- [ ] T012c [S] Generate static test fixture from real data (AdvBench/HF4) to `data/test_static_logs.json` for US-01 testing; ensure this file contains `log_id`, `text`, and `label` columns. **Acceptance Criteria**: File exists, valid JSON. **DEPENDS ON T012a**.
- [ ] T012d-fixed [S] [CRITICAL FIX] Implement `fetch_taxonomy` function in `data_loader.py` to load the **fixed AgentDoG safety taxonomy**. **Source**: Fetch from canonical raw GitHub URL `. **Execution Mechanism**: The function MUST execute a network request to this URL. [UNRESOLVED-CLAIM: c_536568f3 — status=not_enough_info] If successful, it MUST write the downloaded content to `data/raw/taxonomy_agentdog.json`. **Fallback**: If the URL is unreachable or returns a non-200 status, the function MUST attempt to load `data/raw/taxonomy_agentdog_local.json` (a versioned local copy committed to the repo). If both fail, raise `FileNotFoundError`. **Constraint**: This ensures strict reproducibility (Constitution Principle I) by guaranteeing the artifact exists even if the network is unavailable. **FAIL LOUDLY**: Do not attempt to generate synthetic taxonomy. **DEPENDS ON**: T009, T010 (Environment ready). **DO NOT depend on T012a** (Taxonomy is independent of log data).
- [ ] T012e-real-proxy [S] [US1] Generate **REAL GROUND TRUTH (PROXY)** fixture from AdvBench/OWASP labels to `data/test/real_ground_truth_fixture.json` for US-01 MVP testing. **Logic**:
 1. Load AdvBench entries where `label` column equals `'jailbreak'` → map to `{"log_id": <uuid>, "text":..., "label": "novel"}`.
 2. Load HF4 entries where `label` equals `'safe'` → map to `{"log_id": <uuid>, "text":..., "label": "benign"}`.
 3. **Mapping Rules**: Use explicit dictionary `{'jailbreak': 'novel', 'attack': 'novel', 'safe': 'benign'}`. If label is ambiguous or missing, drop the row.
 4. **UUID Strategy**: Use `uuid.uuid5(uuid.NAMESPACE_DNS, f"{text}:{label}")` for deterministic IDs.
 5. **Filtering**: Exclude any rows with missing or ambiguous labels.
 6. **Output Schema**: JSON list with keys `log_id` (UUID), `text` (string), `label` (string: `'novel'` or `'benign'`).
 **NOTE**: This proxy is used **only** for MVP statistical validation (T025a) and MVP baseline comparison (T039-gpt-run); final validation must use human‑annotated gold standard (T035-real). **CRITICAL**: This task enables independent MVP execution; T025a does NOT depend on T035-real. (DEPENDS ON T012a)
- [ ] T012f [S] Fetch the large-scale log dataset for performance benchmarking. **Source**: Use `datasets.load_dataset("mlfoundations/agent_logs_100k", split="train", streaming=False)`. **Action**: Save to `data/raw/agent_logs_100k.csv`. **Constraint**: This file is required for T045a. **DEPENDS ON T012a** (Environment ready).
- [ ] T014 [S] Create `utils.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` for contract validation helpers and JSON/CSV schema loading. **Acceptance Criteria**: File exists, contains `validate_schema` function. Run `pytest` to confirm `test_utils.py` passes.
- [ ] T015 [P] Setup `checksums.json` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/` for raw data integrity tracking
- [ ] T016a [S] Implement `taxonomy_builder.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to generate centroid embeddings using `all-MiniLM-L-v2` (CPU-first, dynamic batching to fit <7GB RAM) using the taxonomy loaded by T012d-fixed (input: `data/raw/taxonomy_agentdog.json`). **DEPENDS ON T012d-fixed**
- [ ] T016b [S] Implement runtime memory monitoring logic in `taxonomy_builder.py` using `tracemalloc` to profile centroid generation and enforce a strict peak RAM limit of < 7GB; raise an exception if exceeded. **Acceptance Criteria**: Logic raises `MemoryError` if peak RAM > 7GB. Run `pytest` to confirm `test_memory.py` passes. (DEPENDS ON T016a execution)
- [ ] T016c [P] Save the generated taxonomy with embeddings to `data/processed/taxonomy_centroids.json` as a persistent artifact for reproducibility (input: output of T016a)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Shot Drift Scoring (Priority: P1) 🎯 MVP

**Goal**: Implement the core drift scoring mechanism to compute cosine distances between logs and taxonomy centroids.

**Independent Test**: The system can be tested by feeding a static JSON file of a sufficient number of known benign logs and a comparable number of known novel attack logs (where novelty is defined by the **REAL GROUND TRUTH (PROXY)** from T012e-real-proxy) and verifying that the "Drift Score" distribution is statistically distinguishable between the two groups with p < 0.05 and an effect size (Cohen's d) ≥ 0.5. **CRITICAL**: Statistical validation (T025a) uses the **REAL GROUND TRUTH (PROXY)** for MVP. T025b (Final) requires the Human-Annotated Gold Standard (T035-real).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T018 [P] [US1] Contract test for `drift_scoring.py` output schema: implement `test_drift_score_schema_matches_drift_result_yaml` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_contracts.py` validating against `specs/001-llmxive-drift-detection/contracts/drift_result.schema.yaml` (from T009)
- [X] T019 [P] [US1] Unit test for empty/whitespace log handling: implement `test_empty_log_returns_drift_score_2_0` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_drift_scoring.py` using `data/test_empty_log.json` and {{claim:c_2f0ac9f1}}. **Justification**: The score near the upper bound is the theoretical maximum for cosine distance (bounded range), assigned by design to represent the "maximum possible distance" for empty inputs, as defined in the spec's "maximum distance" requirement. This range accounts for floating point precision.
- [X] T020 [P] [US1] Integration test for batch processing memory limits: implement `test_batch_memory_limit_7gb` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/integration/test_end_to_end.py` using a dataset of logs and asserting `peak_memory < 7GB`

### Implementation for User Story 1

- [ ] T021a [P] [US1] Implement `compute_cosine_distance` function in `drift_scoring.py` to calculate minimum cosine distance to centroids using `- cosine_similarity(L2_normalized_vectors)`.
- [ ] T021b [P] [US1] Implement `batch_process_logs` function in `drift_scoring.py` to handle large datasets within 7GB RAM.
- [ ] T021c [P] [US1] Implement `handle_empty_logs` function in `drift_scoring.py` to assign a Drift Score corresponding to the theoretical maximum cosine distance (>= 1.9) and set `review_flag` to true for empty/whitespace logs.
- [ ] T021d [P] [US1] Implement `export_results` function in `drift_scoring.py` to export to CSV (`data/processed/drift_scores.csv`) with columns `log_id`, `drift_score`, `review_flag`. (DEPENDS ON T016c)
- [ ] T022 [P] [US1] Create `main.py` orchestration script in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run the full scoring pipeline including export (DEPENDS ON T021a-T021d)
- [ ] T025a [S] [US1] Implement **MVP Statistical Validation** logic in `validation.py` to calculate p‑values and Cohen's d for US using the **REAL GROUND TRUTH (PROXY)** from `data/test/real_ground_truth_fixture.json`. Output: `data/processed/us01_mvp_stats.json`. **NOTE**: This step runs **independently** of human Kappa and is used for rapid MVP feedback. **CRITICAL**: This task does NOT depend on T035-real or any human annotation step. It runs as soon as T012e-real-proxy and T021d are complete. **WARNING**: This MVP result validates the *mechanism* of distinguishing safe vs. unsafe, but does NOT satisfy the final acceptance criteria of US-01 (novelty detection) because it uses known attack labels, not human-validated novelty. (DEPENDS ON T012e-real-proxy, T021d)
- [ ] T025b [S] [US1] Implement **Final Statistical Validation** logic in `validation.py` to calculate p‑values and Cohen's d for US‑01 using the **Human‑Annotated Gold Standard** from `data/processed/merged_annotations.csv` (produced by T035-real). Output: `data/processed/us01_final_stats.json`. (DEPENDS ON T035-real)
- [ ] T026 [S] [US1] Implement final validation logic in `validation.py` to confirm US‑01 acceptance criteria are met using the output from T025b; **BLOCKS project advancement if T025b is skipped or fails**. This task ensures the "Novelty Detection" requirement is satisfied by the Human Gold Standard, not the Proxy. (DEPENDS ON T025b)

**Checkpoint**: At this point, User Story 1 MVP is fully functional and testable independently (without human input)

---

## Phase 4: User Story 2 - Human-in-the-Loop Validation (Priority: P2)

**Goal**: Stratify logs for human annotation and perform statistical validation against ground truth.

**Independent Test**: The system can be tested by generating stratified CSVs and verifying the output format matches annotation requirements (log_id, text, label) and statistical tests (Logistic Regression, Mann-Whitney U) run correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US2] Unit test for stratification logic (top/bottom percentiles) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_validation.py`
- [ ] T028 [P] [US2] Unit test for Kappa statistic calculation in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_kappa.py`
- [ ] T029 [P] [US2] Unit test for blind export (removing drift scores) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_blind.py`

### Implementation for User Story 2

- [ ] T030a [S] [US2] Implement `stratify_logs` function in `annotator_interface.py` to calculate indices, sort, slice, and bin logs based on drift scores and config parameters (input: `data/processed/drift_scores.csv`). **DEPENDS ON T021d**.
- [ ] T031a [S] [US2] Implement blinding logic (remove `drift_score` column) in `annotator_interface.py` prior to export for human review
- [ ] T030b [S] [US2] Implement `generate_blinded_annotation_files` function in `annotator_interface.py` to combine stratification (T030a) and blinding (T031a) logic to generate final blinded CSVs for human annotators; save to `data/processed/blinded_annotation_batches/*.csv` (DEPENDS ON T030a AND T031a AND T021d)
- [ ] T031d [S] [US2] Implement `prepare_annotation_interface` function in `annotator_interface.py` to generate a CSV template ready for human upload (columns: `log_id`, `text`, `drift_score` for reference ONLY, but `drift_score` must be removed before export) based on stratified bins from T030a (DEPENDS ON T030a)
- [ ] T032a [S] [US2] Implement `ingest_human_annotations` function in `validation.py` to load **all** annotation CSVs matching `data/processed/blinded_annotation_batches/*.csv` (using `glob`). **Raise a ValueError if FEWER THAN A SMALL NUMBER OF distinct annotation files are found**. Aggregate distinct annotator files into a single dataset for downstream Kappa calculation. **DEPENDS ON**: `data/processed/blinded_annotation_batches/*.csv` (Wait for annotation generation).
- [ ] T031b [S] [US2] Implement `merge_annotations` logic in `validation.py` to read the aggregated annotations from T032a, merge with drift scores, and output `data/processed/merged_annotations.csv`. (DEPENDS ON T032a)
- [ ] T031c [S] [US2] Implement `validation.py` logic to perform logistic regression (using `statsmodels.formula.api.logit`) and Mann-Whitney U tests on `data/processed/merged_annotations.csv`, outputting `data/processed/validation_stats.json`
- [ ] T032b [P] [US2] Generate mock annotation fixtures for testing purposes ONLY (input: `data/processed/drift_scores.csv`, output: `data/test/mock_annot_1.csv`, `data/test/mock_annot_2.csv`, `data/test/mock_annot_3.csv`). **NOTE**: These files are for unit testing T032a logic only. They DO NOT satisfy the Constitution Principle VI requirement for real human annotation.
- [ ] T033 [S] [US2] Implement `export_stratified_bins` function in `annotator_interface.py` to export pre‑calculated bins as blinded CSVs for annotation (using T031a logic) (DEPENDS ON T030a AND T031a)
- [ ] T034 [S] [US2] Implement logic to handle stratification parameters (deferred percentiles) via `config.py`
- [ ] T035-real [S] [US2] Implement **Real Multi-Annotator Interface** in `annotator_interface.py`. **Logic**: This task implements a CLI tool (`python code/annotator_interface.py --annotate`).
 1. Loads the stratified, blinded batches from T030b.
 2. **PRODUCTION MODE (Default)**: Expects real human annotation files to be present in `data/processed/blinded_annotation_batches/` (e.g., `annot_001.csv`, `annot_002.csv`, `annot_003.csv`). If these files are missing, the script MUST raise a `FileNotFoundError` with the message "REAL HUMAN ANNOTATION FILES MISSING. PROJECT CANNOT ADVANCE WITHOUT REAL GOLD STANDARD." and exit with code 1.
 3. **TESTING MODE (Flag `--simulate`)**: If the `--simulate` flag is explicitly passed, the script generates mock data using deterministic seeds and prompt perturbation for local testing ONLY. It MUST log a `CRITICAL` warning: "SIMULATION MODE ACTIVE. ARTIFACTS GENERATED ARE NOTVALID FOR PRODUCTION VALIDATION." and save to a separate directory `data/test/simulated_annotations/`. **This mode is FOR TESTING ONLY and MUST NOT be used for final validation.**
 4. **Threshold**: {{claim:c_3a9c20be}} (2504.15325, https://arxiv.org/abs/2504.15325). **IF Kappa < 0.6, raise a ValueError, write `kappa_failed.json` artifact with error details, update `state/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5.yaml` to set `current_stage: unproven`, and DO NOT proceed with data.** (DEPENDS ON T030b)
- [ ] T036 [S] [US2] Verify output CSVs contain required columns: `log_id`, `text`, `label` (blinded) and no `drift_score` column

**Checkpoint**: At this point, User Stories 1 and 2 are fully functional with human input (real or simulated for testing)

---

## Phase 5: User Story 3 - Baseline Performance Comparison (Priority: P3)

**Goal**: Compare Drift Score detector against a standard zero-shot LLM classifier (local model).

**Independent Test**: The system can be tested by running a comparison script on a small subset of logs where both the Drift Score and a zero-shot LLM inference (using a local CPU‑friendly model) are available, and verifying the output includes AUC‑ROC and inference time metrics against the human‑annotated ground truth from US‑02.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T037 [P] [US3] Unit test for AUC‑ROC calculation in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_comparison.py`
- [ ] T038 [P] [US3] Unit test for inference time measurement in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_comparison.py`

### Implementation for User Story 3

- [ ] T039-scope-change-doc [P] [US3] Create `docs/scope_changes.md` to formally document the substitution of `gpto-mini` with `google/flan-t5-small`. **Content**: Explicitly state that `gpto-mini` was deemed infeasible on the 7GB RAM GitHub Actions runner due to memory constraints. Justify `flan-t5-small` as a CPU-tractable proxy that maintains the zero-shot classification capability required for the comparison metric. **Acceptance Criteria**: Document exists and is referenced by T039-gpt-setup.
- [ ] T039-gpt-setup [P] [US3] Implement `generate_baseline_benchmark.py` to prepare the model and data for the zero-shot LLM classifier. **Model Substitution**: Use `google/flan-t5-small` as per the scope change documented in `docs/scope_changes.md`. **Action**: Load model, cache tokenizer, and prepare the prompt template. **Output**: A configuration file `data/processed/flan_config.json` documenting the model, prompt template, and the mapping rationale. **Note**: This task does NOT run inference; it only prepares the environment. (DEPENDS ON T012e-real-proxy, T039-scope-change-doc)
- [ ] T039-proxy-validation [S] [US3] Implement `validate_baseline_proxy` function in `comparison.py` to run a quick statistical sanity check of the Flan-T5 baseline **against the REAL GROUND TRUTH (PROXY)** (`data/test/real_ground_truth_fixture.json`). **Action**: Run Flan-T5 on a small subset (e.g., 100 logs) and compare against the proxy labels. **Output**: `data/processed/flan_proxy_validation.json`. **Acceptance Criteria**: The proxy AUC must be > 0.70 to be considered a valid baseline substitute. [UNRESOLVED-CLAIM: c_944ef84b — status=not_enough_info] If not, raise `ValueError` and block US-03. (DEPENDS ON T039-gpt-setup)
- [ ] T039-gpt-run [S] [US3] Implement `comparison.py` to run the zero‑shot LLM classifier using `google/flan-t5-small` on the **REAL GROUND TRUTH (PROXY)** dataset, comparing results with Drift Scores. **No external API calls** are permitted. Use the prompt template: `"Statement: {text}. Question: Is this a novel attack?"` Map model outputs to 'benign'/'novel'. Cache model outputs for reproducibility. **NOTE**: This MVP run uses the proxy to enable early comparison without waiting for human annotation. (DEPENDS ON T039-gpt-setup, T012e-real-proxy)
- [ ] T039-gpt-final [S] [US3] Implement `compare_final` function in `comparison.py` to run the zero‑shot LLM classifier on the **Human-Annotated Gold Standard** (`data/processed/merged_annotations.csv`) and compare with Drift Scores. (DEPENDS ON T031b, T035-real)
- [ ] T040 [S] [US3] Implement bootstrap iteration logic for AUC‑ROC stability. **Output artifact**: `data/processed/bootstrap_stats.json`. **Iterations**: A sufficient number of bootstrap iterations OR until standard deviation of AUC-ROC < 0.01 for 5 consecutive runs OR until a substantial portion of the available CPU time has elapsed (to respect the time limit). **Metric**: AUC-ROC. **Method**: Stratified bootstrap sampling. **Timeout Handling**: If the time limit is reached, output the current best estimate with a `timeout_limited: true` flag.
- [ ] T040a [US3] Implement deterministic inference caching mechanism in `comparison.py` for local model outputs to ensure reproducibility (Constitution Principle I)
- [ ] T041-mvp [S] [US3] Generate **MVP Comparison Report** containing AUC‑ROC for both methods (Drift Score from T025a, Flan-T5 Baseline from T039-gpt-run) and average inference time per log using the **PROXY** data. **DEPENDS ON T039-gpt-run AND T025a**. (DEPENDS ON T039-gpt-run, T025a)
- [ ] T041-final [S] [US3] Generate **Final Comparison Report** containing AUC‑ROC for both methods using the **Human-Annotated Gold Standard**. **BLOCKS project advancement if T035-real fails**. **Acceptance Criteria**: The Baseline (Flan-T5) AUC must be statistically significant (p < 0.05) and the Drift Score AUC must be within 0.10 of the Baseline AUC. (DEPENDS ON T039-gpt-final, T025b, T035-real)
- [ ] T041a [S] [US3] Implement logic to block T041-final if `state/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5.yaml` indicates `current_stage: unproven` (DEPENDS ON T035-real)
- [ ] T042 [US3] Add logic to flag "computationally efficient alternative" if |AUC_drift - AUC_llm| ≤ 0.10

**Checkpoint**: All user stories should now be independently functional (MVP with proxy, Final with human)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043a [P] Update `docs/quickstart.md` with new drift detection workflow and data loading instructions
- [ ] T043b [P] Update `docs/data-model.md` with new data model fields and schema definitions
- [ ] T044a [P] Run black and ruff on `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to enforce formatting and linting
- [ ] T044b [P] Remove unused imports and variables from `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`
- [ ] T045-opt-impl [P] Implement batch size tuning logic in `code/benchmark_performance.py`. **Action**: Write logic to iterate through batch sizes and measure memory/time. **Output**: Helper function `get_optimal_batch_size`. (DEPENDS ON T016a)
- [ ] T045-opt-run [P] Run the benchmark on a subset of logs using the logic from T045-opt-impl. **Action**: Execute benchmark script on a subset (e.g., 10k logs) to measure performance. **Output**: Raw performance metrics. (DEPENDS ON T045-opt-impl)
- [ ] T045-opt-report [P] Generate `data/processed/optimization_report.json` containing the optimal batch size and strategy based on T045-opt-run results. **Acceptance Criteria**: Report confirms the optimal batch size and strategy. (DEPENDS ON T045-opt-run)
- [ ] T045a [P] Implement `benchmark_performance.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run a large‑scale log benchmark on `data/raw/agent_logs_k.csv` (100k logs) on a GitHub Actions runner (limited RAM, 2 cores) and assert completion time ≤ 30 minutes (SC-003). **Action**: Use the `optimal_batch_size` from `data/processed/optimization_report.json`. If the direct run exceeds 30 minutes, the build MUST fail; no projection allowed. (DEPENDS ON T045-opt-report, T012f)
- [ ] T045b [P] Integrate `benchmark_performance.py` into GitHub Actions workflow to fail the build if the time threshold is exceeded
- [ ] T046a [P] Implement unit test `test_leetspeak_drift_score` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_edge_cases.py` using `data/test/leetspeak_samples.json`; assert drift score > 0.8.
- [ ] T046b [P] Implement unit test `test_obfuscation_drift_score` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_edge_cases.py` using `data/test/obfuscated_samples.json`; assert drift score > 0.8.
- [ ] T046c [P] Implement unit test `test_unicode_normalization` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_edge_cases.py` using `data/test/unicode_samples.json`; assert normalized text matches expected form.
- [ ] T047 [P] Run `python code/main.py --validate-only`; expect exit code 0 and schema‑validated output files (`data/processed/*.csv`); failures abort the run.
- [ ] T048 [P] **Validation Handoff**: Implement logic in `validation.py` to replace `data/processed/mock_ground_truth.csv` with `data/processed/merged_annotations.csv` for the final US‑01 validation run. Ensure T025b is executed with real data and T026 is marked as MVP‑only. (DEPENDS ON T031b)
- [ ] T049 [P] **Full System Orchestration**: Implement `run_full_pipeline.py` to orchestrate US‑01, US‑02, and US‑03 pipelines in the correct dependency order. **Dependencies**: T041-final, T025b, T030b, T039-gpt-final.