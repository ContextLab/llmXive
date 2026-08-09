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

## Phase 0: Scope Amendment (Critical Pre-requisite)

**Purpose**: Resolve contradictions between Spec and Implementation Plan.

- [ ] T000-ScopeAmend [S] [US3] **Update Spec for Model Substitution**: Amend `specs/001-llmxive-drift-detection/spec.md` to replace the requirement for `gpto-mini` with `google/flan-t5-small` in User Story 03. **Action**: Update the `User Stories` section of `spec.md` to reflect the CPU-tractable model. **Rationale**: Constitution Principle I (SSOT) requires the Spec to match the Implementation Plan. Without this amendment, the project violates the "No silent constitution drift" rule. **DEPENDS ON**: T009 (Environment ready).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [S] Initialize project directory structure: Create and verify directories `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`, `tests/`, `data/raw/`, `data/processed/`, `data/test/`, `specs/`, `docs/`, and `specs/001-llmxive-drift-detection/`. **Acceptance Criteria**: All directories exist.
- [ ] T001b [S] Verify directory structure: Create `tests/test_setup.py` with function `test_directories_exist` that asserts the existence of the directories created in T001a. Run `pytest` to confirm `test_directories_exist` passes. **Acceptance Criteria**: `test_directories_exist` passes. (DEPENDS ON T001a)
- [X] T009 Initialize a Python project with `requirements.txt` (sentence-transformers, scikit-learn, pandas, numpy, datasets, jsonschema, statsmodels, pytest, transformers, accelerate, llama-cpp-python) using a modern, stable Python 3 release.
- [ ] T010 [S] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/`. **Acceptance Criteria**:
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
 target-version = ['py311']
 ```
 3. Verify `.ruff.toml` and `pyproject.toml` exist and are non-empty via `pytest` (test `test_ruff_config_exists` and `test_black_config_exists`).
 **Note**: This task resolves the previous failure where `.ruff.toml` was missing by explicitly defining its content.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 [S] Create `config.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to manage random seeds, paths, and batch sizes. **Acceptance Criteria**: File exists, contains `RANDOM_SEED=42`, `MAX_RAM_GB=7`, and `BATCH_SIZE=64`. Run `pytest` to confirm `test_config.py` passes.
- [ ] T012a [S] Implement `fetch_advbench` and `fetch_hf4` functions in `data_loader.py` using `datasets.load_dataset` with streaming; ensure no synthetic fallbacks. **Timestamp Handling**: If the source dataset lacks a `timestamp` field, generate a deterministic placeholder timestamp (e.g., `datetime(1970, 1, 1)`) to satisfy the Data Model. **Acceptance Criteria**: Functions raise `ValueError` on fetch failure. Run `pytest` to confirm `test_data_loader.py` passes.
- [ ] T012b [S] Add checksum verification logic in `data_loader.py` to validate raw data against `data/checksums.json`. **Acceptance Criteria**: Logic raises `ValueError` if checksum mismatch. Run `pytest` to confirm `test_checksums.py` passes. (DEPENDS ON T012a)
- [ ] T012c [S] Generate static test fixture from real data (AdvBench/HF4) to `data/test_static_logs.json` for US-01 testing; ensure this file contains `log_id`, `text`, `label`, and `timestamp` columns. **Acceptance Criteria**: File exists, valid JSON. **DEPENDS ON T012a**.
- [ ] T012d-fixed [S] [CRITICAL FIX] Implement `fetch_taxonomy` function in `data_loader.py` to load the **fixed AgentDoG safety taxonomy**. **Source**: Fetch from canonical raw GitHub URL `https://raw.githubusercontent.com/AgentDoG/safety-taxonomy/main/taxonomy_agentdog.json`. **Execution Mechanism**: The function MUST execute a network request to this URL. If successful, it MUST write the downloaded content to `data/raw/taxonomy_agentdog.json`. **Constraint**: If the URL is unreachable or returns a non-200 status, the function MUST raise `FileNotFoundError`. **NO LOCAL FALLBACK**: Do not attempt to load a local copy. This ensures strict reproducibility (Constitution Principle I) by guaranteeing the artifact is the canonical one. **FAIL LOUDLY**: Do not attempt to generate synthetic taxonomy. **DEPENDS ON**: T009, T010 (Environment ready). **DO NOT depend on T012a** (Taxonomy is independent of log data).
- [ ] T012e-real-proxy [S] [US1] Generate **REAL GROUND TRUTH (PROXY)** fixture from AdvBench/OWASP labels to `data/test/real_ground_truth_fixture.json` for US-01 MVP testing. **Logic**:
 1. Load AdvBench entries where `label` column equals `'jailbreak'` → map to `{"log_id": <uuid>, "text":..., "label": "novel"}`.
 2. Load HF4 entries where `label` equals `'safe'` → map to `{"log_id": <uuid>, "text":..., "label": "benign"}`.
 3. **Mapping Rules**: Use explicit dictionary `{'jailbreak': 'novel', 'attack': 'novel', 'safe': 'benign'}`. If label is ambiguous or missing, drop the row.
 4. **UUID Strategy**: Use a deterministic hashing method based on a namespace and input string for generating unique identifiers.
 5. **Timestamp Handling**: If source lacks `timestamp`, use `datetime(1970, 1, 1)`.
 6. **Filtering**: Exclude any rows with missing or ambiguous labels.
 7. **Output Schema**: JSON list with keys `log_id` (UUID), `text` (string), `label` (string: `'novel'` or `'benign'`), `timestamp` (datetime).
 **NOTE**: This proxy is used **only** for MVP statistical validation (T025a) and MVP baseline comparison (T039-gpt-run); final validation must use human‑annotated gold standard (T035b). **CRITICAL**: This task enables independent MVP execution; T025a does NOT depend on T035b. (DEPENDS ON T012a)
- [ ] T012f [S] Fetch the large-scale log dataset for performance benchmarking. **Source**: Use `datasets.load_dataset("mlfoundations/agent_logs", split="train", streaming=False)`. **Action**: Save to `data/raw/agent_logs_100k.csv`. **Constraint**: This file is required for T045a. **DEPENDS ON T012a** (Environment ready).
- [ ] T014 [S] Create `utils.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` for contract validation helpers and JSON/CSV schema loading. **Acceptance Criteria**: File exists, contains `validate_schema` function. Run `pytest` to confirm `test_utils.py` passes.
- [ ] T015 [S] Setup `checksums.json` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/` for raw data integrity tracking. **DEPENDS ON T009**.
- [ ] T016a [S] Implement `taxonomy_builder.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to generate centroid embeddings using `all-MiniLM-L-v2` (CPU-first, dynamic batching to fit <7GB RAM) using the taxonomy loaded by T012d-fixed (input: `data/raw/taxonomy_agentdog.json`). **DEPENDS ON T012d-fixed**
- [ ] T016b [S] Implement runtime memory monitoring logic in `taxonomy_builder.py` using `tracemalloc` to profile centroid generation and enforce a strict peak RAM limit of < 7GB; raise an exception if exceeded. **Acceptance Criteria**: Logic raises `MemoryError` if peak RAM > 7GB. Run `pytest` to confirm `test_memory.py` passes. (DEPENDS ON T016a execution)
- [ ] T016c [S] Save the generated taxonomy with embeddings to `data/processed/taxonomy_centroids.json` as a persistent artifact for reproducibility (input: output of T016a). **DEPENDS ON T016a**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Shot Drift Scoring (Priority: P1) 🎯 MVP

**Goal**: Implement the core drift scoring mechanism to compute cosine distances between logs and taxonomy centroids.

**Independent Test**: The system can be tested by feeding a static JSON file of a sufficient number of known benign logs and a comparable number of known novel attack logs (where novelty is defined by the **REAL GROUND TRUTH (PROXY)** from T012e-real-proxy) and verifying that the "Drift Score" distribution is statistically distinguishable between the two groups with p < 0.05 and an effect size (Cohen's d) ≥ 0.5. **CRITICAL**: Statistical validation (T025a) uses the **REAL GROUND TRUTH (PROXY)** for MVP. T025b (Final) requires the Human-Annotated Gold Standard (T035b).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T018 [S] [US1] Contract test for `drift_scoring.py` output schema: implement `test_drift_score_schema_matches_drift_result_yaml` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_contracts.py` validating against `specs/001-llmxive-drift-detection/contracts/drift_result.schema.yaml` (from T009). **DEPENDS ON T021d**.
- [ ] T019 [S] [US1] Unit test for empty/whitespace log handling: implement `test_empty_log_returns_drift_score_max` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_drift_scoring.py` using `data/test_empty_log.json`. **Justification**: The score must match the theoretical maximum distance calculated by the model. This range accounts for floating point precision. **DEPENDS ON T021c**.
- [ ] T020 [S] [US1] Integration test for batch processing memory limits: implement `test_batch_memory_limit_7gb` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/integration/test_end_to_end.py` using a dataset of logs and asserting `peak_memory < 7GB`. **DEPENDS ON T021b**.

### Implementation for User Story 1

- [ ] T021a [S] [US1] Implement `compute_cosine_distance` function in `drift_scoring.py` to calculate minimum cosine distance to centroids using `- cosine_similarity(L2_normalized_vectors)`. **DEPENDS ON T016c**.
- [ ] T021b [S] [US1] Implement `batch_process_logs` function in `drift_scoring.py` to handle large datasets within 7GB RAM. **DEPENDS ON T016c**.
- [ ] T021c [S] [US1] Implement `handle_empty_logs` function in `drift_scoring.py` to assign a Drift Score equal to the **theoretical maximum cosine distance** for the specific embedding model (calculated dynamically based on model normalization properties, typically 2.0) and set `review_flag` to true for empty/whitespace logs. **Acceptance Criteria**: Function returns the calculated max distance (not hardcoded 2.0). **DEPENDS ON T016c**.
- [ ] T021d [S] [US1] Implement `export_results` function in `drift_scoring.py` to export to CSV (`data/processed/drift_scores.csv`) with columns `log_id`, `drift_score`, `review_flag`. **DEPENDS ON**: T016c (centroids), T012a (log data source).
- [ ] T022 [S] [US1] Create `main.py` orchestration script in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run the full scoring pipeline including export (DEPENDS ON T021a-T021d).
- [ ] T025a [S] [US1] Implement **MVP Statistical Validation** logic in `validation.py` to calculate p‑values and Cohen's d for US using the **REAL GROUND TRUTH (PROXY)** from `data/test/real_ground_truth_fixture.json`. Output: `data/processed/us01_mvp_stats.json`. **NOTE**: This step runs **independently** of human Kappa and is used for rapid MVP feedback. **CRITICAL**: This task does NOT depend on T035b or any human annotation step. It runs as soon as T012e-real-proxy and T021d are complete. **WARNING**: This MVP result validates the *mechanism* of distinguishing safe vs. unsafe, but does NOT satisfy the final acceptance criteria of US-01 (novelty detection) because it uses known attack labels, not human-validated novelty. (DEPENDS ON T012e-real-proxy, T021d)
- [ ] T025b [S] [US1] Implement **Final Statistical Validation** logic in `validation.py` to calculate p‑values and Cohen's d for US‑01 using the **Human‑Annotated Gold Standard** from `data/processed/merged_annotations.csv` (produced by T031b). Output: `data/processed/us01_final_stats.json`. (DEPENDS ON T035-real, T031b)
- [ ] T026 [S] [US1] Implement final validation logic in `validation.py` to confirm US‑01 acceptance criteria are met using the output from T025b; **BLOCKS project advancement if T025b is skipped or fails**. This task ensures the "Novelty Detection" requirement is satisfied by the Human Gold Standard, not the Proxy. (DEPENDS ON T025b)

**Checkpoint**: At this point, User Story 1 MVP is fully functional and testable independently (without human input)

---

## Phase 4: User Story 2 - Human-in-the-Loop Validation (Priority: P2)

**Goal**: Stratify logs for human annotation and perform statistical validation against ground truth.

**Independent Test**: The system can be tested by generating stratified CSVs and verifying the output format matches annotation requirements (log_id, text, label) and statistical tests (Logistic Regression, Mann-Whitney U) run correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [S] [US2] Unit test for stratification logic (top/bottom percentiles) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_validation.py`. **DEPENDS ON T030a**.
- [ ] T028 [S] [US2] Unit test for Kappa statistic calculation in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_kappa.py`. **DEPENDS ON T031b-Kappa**.
- [ ] T029 [S] [US2] Unit test for blind export (removing drift scores) in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_blind.py`. **DEPENDS ON T031a**.

### Implementation for User Story 2

- [ ] T030a [S] [US2] Implement `stratify_logs` function in `annotator_interface.py` to calculate indices, sort, slice, and bin logs based on drift scores and config parameters (input: `data/processed/drift_scores.csv`, log data from T012a). **DEPENDS ON**: T021d, T012a.
- [ ] T031a [S] [US2] Implement blinding logic (remove `drift_score` column) in `annotator_interface.py` prior to export for human review. **DEPENDS ON T030a**.
- [ ] T030b [S] [US2] Implement `generate_blinded_annotation_files` function in `annotator_interface.py` to combine stratification (T030a) and blinding (T031a) logic to generate final blinded CSVs for human annotators; save to `data/processed/blinded_annotation_batches/*.csv` (DEPENDS ON T030a AND T031a AND T021d).
- [ ] T031d [S] [US2] Implement `prepare_annotation_interface` function in `annotator_interface.py` to generate a CSV template ready for human upload (columns: `log_id`, `text`, `drift_score` for reference ONLY, but `drift_score` must be removed before export) based on stratified bins from T030a (DEPENDS ON T030a).
- [ ] T032a [S] [US2] Implement `ingest_human_annotations` function in `validation.py` to load **all** annotation CSVs matching `data/processed/blinded_annotation_batches/*.csv` (using `glob`). **Raise a ValueError if A FEW distinct annotation files are found**. Aggregate distinct annotator files into a single dataset for downstream Kappa calculation. **Annotator ID Logic**: Extract `annotator_id` from the filename (e.g., `annot_001.csv` -> `annot_001`) or from a column in the CSV if present. **DEPENDS ON**: `data/processed/blinded_annotation_batches/*.csv` (Wait for annotation generation).
- [ ] T032a-annot-id [S] [US2] **Annotator ID Assignment**: Explicitly implement the logic in `validation.py` to assign or extract `annotator_id` for every row in the merged dataset. **Action**: If the CSV lacks an `annotator_id` column, infer it from the filename of the source file. **DEPENDS ON T032a**.
- [ ] T031b-Kappa [S] [US2] **Kappa Calculation Implementation**: Implement `calculate_kappa` function in `validation.py` to compute Cohen's Kappa on the merged annotations. **Action**: Use `statsmodels.stats.inter_rater.cohen_kappa` or `sklearn.metrics.cohen_kappa_score`. **DEPENDS ON T032a-annot-id**.
- [ ] T031b [S] [US2] Implement `merge_annotations` logic in `validation.py` to read the aggregated annotations from T032a, merge with drift scores, calculate Kappa (calling T031b-Kappa), and output `data/processed/merged_annotations.csv`. **DEPENDS ON T032a, T031b-Kappa**.
- [ ] T031c [S] [US2] Implement `validation.py` logic to perform logistic regression (using `statsmodels.formula.api.logit`) and Mann-Whitney U tests on `data/processed/merged_annotations.csv`, outputting `data/processed/validation_stats.json`. **DEPENDS ON T031b**.
- [ ] T032b [S] [US2] Generate mock annotation fixtures for testing purposes ONLY (input: `data/processed/drift_scores.csv`, output: `data/test/mock_annot_1.csv`, `data/test/mock_annot_2.csv`, `data/test/mock_annot_3.csv`). **NOTE**: These files are for unit testing T032a logic only. They DO NOT satisfy the Constitution Principle VI requirement for real human annotation. **DEPENDS ON T021d**.
- [ ] T033 [S] [US2] Implement `export_stratified_bins` function in `annotator_interface.py` to export pre‑calculated bins as blinded CSVs for annotation (using T031a logic) (DEPENDS ON T030a AND T031a).
- [ ] T034 [S] [US2] Implement logic to handle stratification parameters (deferred percentiles) via `config.py`. **DEPENDS ON T030a**.
- [ ] T035a-Recruit [S] [US2] **Human Recruitment & Data Collection**: Implement the process to recruit three annotators and distribute data. **Action**:
 1. Generate recruitment email templates and a simple survey form (e.g., Google Form/Typeform) using `code/annotator_interface.py --generate-recruitment`.
 2. Define the script to distribute the blinded CSVs (from T030b) to the recruited annotators (e.g., via email or a shared folder).
 3. Implement the script to collect the returned annotation files into `data/processed/blinded_annotation_batches/`.
 4. **Constraint**: This task represents the external workflow; the code must generate the artifacts (emails, forms, distribution scripts) to facilitate this process. **DEPENDS ON**: T030b (blinded batches ready).
- [ ] T035-real [S] [US2] Implement **Real Multi-Annotator Interface** in `annotator_interface.py`. **Logic**: This task implements a CLI tool (`python code/annotator_interface.py --annotate`).
 1. Loads the stratified, blinded batches from T030b.
 2. **PRODUCTION MODE (Default)**: Expects real human annotation files to be present in `data/processed/blinded_annotation_batches/` (e.g., `annot_001.csv`, `annot_002.csv`, `annot_003.csv`). If these files are missing, the script MUST raise a `FileNotFoundError` with the message "REAL HUMAN ANNOTATION FILES MISSING. PROJECT CANNOT ADVANCE WITHOUT REAL GOLD STANDARD." and exit with code 1.
 3. **Threshold**: Kappa > 0.6. **IF Kappa < 0.6, raise a ValueError, write `kappa_failed.json` artifact with error details, update `state/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5.yaml` to set `current_stage: unproven`, and DO NOT proceed with data.**
 4. **NO SIMULATION**: The `--simulate` flag has been removed. This task strictly enforces real human annotation. (DEPENDS ON T030b)
- [ ] T036 [S] [US2] Verify output CSVs contain required columns: `log_id`, `text`, `label` (blinded) and no `drift_score` column. **DEPENDS ON T030b**.

**Checkpoint**: At this point, User Stories 1 and 2 are fully functional with human input (real only)

---

## Phase 5: User Story 3 - Baseline Performance Comparison (Priority: P3)

**Goal**: Compare Drift Score detector against a standard zero-shot LLM classifier (local model).

**Independent Test**: The system can be tested by running a comparison script on a small subset of logs where both the Drift Score and a zero-shot LLM inference (using a local CPU‑friendly model) are available, and verifying the output includes AUC‑ROC and inference time metrics against the human‑annotated ground truth from US‑02.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T037 [S] [US3] Unit test for AUC‑ROC calculation in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_comparison.py`. **DEPENDS ON T039-metrics-auc**.
- [ ] T038 [S] [US3] Unit test for inference time measurement in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_comparison.py`. **DEPENDS ON T039-metrics-time**.

### Implementation for User Story 3

- [ ] T039-scope-change-doc [S] [US3] Create `docs/scope_changes.md` to formally document the substitution of `gpto-mini` with `google/flan-t5-small`. **Content**: Explicitly state that `gpto-mini` was deemed infeasible on the 7GB RAM GitHub Actions runner due to memory constraints. Justify `flan-t5-small` as a CPU-tractable proxy that maintains the zero-shot classification capability required for the comparison metric. **Acceptance Criteria**: Document exists and is referenced by T039-gpt-setup. **DEPENDS ON T000-ScopeAmend**.
- [ ] T039-gpt-setup [S] [US3] Implement `generate_baseline_benchmark.py` to prepare the model and data for the zero-shot LLM classifier. **Model Substitution**: Use `google/flan-t5-small` as per the scope change documented in `docs/scope_changes.md`. **Action**: Load model, cache tokenizer, and prepare the prompt template. **Output**: A configuration file `data/processed/flan_config.json` documenting the model, prompt template, and the mapping rationale. **Note**: This task does NOT run inference; it only prepares the environment. (DEPENDS ON T012e-real-proxy, T039-scope-change-doc)
- [ ] T039-metrics-auc [S] [US3] Implement `calculate_auc_roc` function in `comparison.py` to compute AUC-ROC from predictions and ground truth. **DEPENDS ON T039-gpt-setup**.
- [ ] T039-metrics-time [S] [US3] Implement `measure_inference_time` function in `comparison.py` to measure inference time per log. **DEPENDS ON T039-gpt-setup**.
- [ ] T039-proxy-validation [S] [US3] Implement `validate_baseline_proxy` function in `comparison.py` to run a quick statistical sanity check of the Flan-T5 baseline **against the REAL GROUND TRUTH (PROXY)** (`data/test/real_ground_truth_fixture.json`). **Action**: Run Flan-T5 on a small subset (e.g., 100 logs) and compare against the proxy labels. **Output**: `data/processed/flan_proxy_validation.json`. **Acceptance Criteria**: The proxy AUC must be > 0.70 to be considered a valid baseline substitute. If not, raise `ValueError` and block US-03. (DEPENDS ON T039-gpt-setup, T039-metrics-auc)
- [ ] T039-gpt-run [S] [US3] Implement `comparison.py` to run the zero‑shot LLM classifier using `google/flan-t5-small` on the **REAL GROUND TRUTH (PROXY)** dataset, comparing results with Drift Scores. **No external API calls** are permitted. Use the prompt template: `"Statement: {text}. Question: Is this a novel attack?"`. **Output Mapping**: Map model outputs 'Yes', 'novel', '1' to 'novel'; 'No', 'benign', '0' to 'benign'; anything else to 'unknown' (exclude from AUC). Cache model outputs for reproducibility. **NOTE**: This MVP run uses the proxy to enable early comparison without waiting for human annotation. **DEPENDS ON**: T039-gpt-setup, T012e-real-proxy, T012a (log data source), T039-metrics-auc, T039-metrics-time.
- [ ] T039-gpt-final [S] [US3] Implement `compare_final` function in `comparison.py` to run the zero‑shot LLM classifier on the **Human-Annotated Gold Standard** (`data/processed/merged_annotations.csv`) and compare with Drift Scores. **CRITICAL**: This task requires T035-real to have completed successfully with Kappa > 0.6. If T035-real failed or is incomplete, this task must raise an error. (DEPENDS ON T031b, T035-real)
- [ ] T040 [S] [US3] Implement bootstrap iteration logic for AUC‑ROC stability. **Output artifact**: `data/processed/bootstrap_stats.json`. **Iterations**: A sufficient number of bootstrap iterations OR until standard deviation of AUC-ROC < 0.01 for Multiple consecutive runs OR until a substantial portion of the available CPU time has elapsed (to respect the time limit). **Metric**: AUC-ROC. **Method**: Stratified bootstrap sampling. **Timeout Handling**: If the time limit is reached, output the current best estimate with a `timeout_limited: true` flag. **DEPENDS ON T039-gpt-run**.
- [ ] T040a [S] [US3] Implement deterministic inference caching mechanism in `comparison.py` for local model outputs to ensure reproducibility (Constitution Principle I). **DEPENDS ON T039-gpt-run**.
- [ ] T041-mvp [S] [US3] Generate **MVP Comparison Report** containing AUC‑ROC for both methods (Drift Score from T025a, Flan-T5 Baseline from T039-gpt-run) and average inference time per log using the **PROXY** data. **DEPENDS ON T039-gpt-run AND T025a**. (DEPENDS ON T039-gpt-run, T025a)
- [ ] T041-final [S] [US3] Generate **Final Comparison Report** containing AUC‑ROC for both methods using the **Human-Annotated Gold Standard**. **BLOCKS project advancement if T035b fails**. **Acceptance Criteria**: The Baseline (Flan-T5) AUC must be statistically significant (p < 0.05) and the Drift Score AUC must be within 0.10 of the Baseline AUC. (DEPENDS ON T039-gpt-final, T025b, T035-real)
- [ ] T041a [S] [US3] Implement logic to block T041-final if `state/projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5.yaml` indicates `current_stage: unproven` (DEPENDS ON T035-real).
- [ ] T042 [S] [US3] Add logic to flag "computationally efficient alternative" if |AUC_drift - AUC_llm| ≤ 0.10. **DEPENDS ON T041-final**.

**Checkpoint**: All user stories should now be independently functional (MVP with proxy, Final with human)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043a [S] Update `docs/quickstart.md` with new drift detection workflow and data loading instructions. **DEPENDS ON T021d**.
- [ ] T043b [S] Update `docs/data-model.md` with new data model fields and schema definitions. **DEPENDS ON T021d**.
- [ ] T044a [S] Run black and ruff on `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to enforce formatting and linting. **DEPENDS ON T021d**.
- [ ] T044b [S] Remove unused imports and variables from `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/`. **DEPENDS ON T021d**.
- [ ] T045-opt-impl [S] Implement batch size tuning logic in `code/benchmark_performance.py`. **Action**: Write logic to iterate through batch sizes and measure memory/time. **Output**: Helper function `get_optimal_batch_size`. (DEPENDS ON T016a)
- [ ] T045-opt-run [S] Run the benchmark on a subset of logs using the logic from T045-opt-impl. **Action**: Execute benchmark script on a subset (e.g., 10k logs) to measure performance. **Output**: Raw performance metrics. (DEPENDS ON T045-opt-impl)
- [ ] T045-opt-report [S] Generate `data/processed/optimization_report.json` containing the optimal batch size and strategy based on T045-opt-run results. **Acceptance Criteria**: Report confirms the optimal batch size and strategy. (DEPENDS ON T045-opt-run)
- [ ] T045a [S] Implement `benchmark_performance.py` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/code/` to run a large‑scale log benchmark on `data/raw/agent_logs_k.csv` (A large-scale collection of logs

The specific value to remove/generalize: 'large-scale'

Rewritten passage:
A large-scale collection of logs) on a GitHub Actions runner (limited RAM, 2 cores) and assert completion time ≤ 30 minutes (SC-003). **Action**: Use the `optimal_batch_size` from `data/processed/optimization_report.json`. **Timeout Logic**: Wrap execution in a timer; raise `TimeoutError` if > 30m. If the direct run exceeds 30 minutes, the build MUST fail; no projection allowed. (DEPENDS ON T045-opt-report, T012f)
- [ ] T045b [S] Integrate `benchmark_performance.py` into GitHub Actions workflow to fail the build if the time threshold is exceeded. **DEPENDS ON T045a**.
- [ ] T046a [S] Implement unit test `test_leetspeak_drift_score` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_edge_cases.py` using `data/test/leetspeak_samples.json`; assert drift score > 0.8. **DEPENDS ON T021d**. **Note**: Defensive test for general edge case of obfuscated text.
- [ ] T046b [S] Implement unit test `test_obfuscation_drift_score` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_edge_cases.py` using `data/test/obfuscated_samples.json`; assert drift score > 0.8. **DEPENDS ON T021d**. **Note**: Defensive test for general edge case of obfuscated text.
- [ ] T046c [S] Implement unit test `test_unicode_normalization` in `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/tests/unit/test_edge_cases.py` using `data/test/unicode_samples.json`; assert normalized text matches expected form. **DEPENDS ON T021d**. **Note**: Defensive test for general edge case of unicode normalization.
- [ ] T047 [S] Run `python code/main.py --validate-only`; expect exit code 0 and schema‑validated output files (`data/processed/*.csv`); failures abort the run. **DEPENDS ON T021d**.
- [ ] T048 [S] **Validation Handoff**: Implement logic in `validation.py` to replace `data/processed/mock_ground_truth.csv` with `data/processed/merged_annotations.csv` for the final US‑01 validation run. Ensure T025b is executed with real data and T026 is marked as MVP‑only. (DEPENDS ON T031b).
- [ ] T049 [S] **Full System Orchestration**: Implement `run_full_pipeline.py` to orchestrate US‑01, US‑02, and US‑03 pipelines in the correct dependency order. **Dependencies**: T041-final, T025b, T030b, T039-gpt-final. **DEPENDS ON T041-final**.

---

## Revision: Addressing Analyze Findings (Phase N+)

**Purpose**: Resolve specific issues raised by `/speckit.analyze` regarding data flow, resource constraints, and edge case handling.

- [ ] T050 [S] [US1] **Data Flow Fix**: Ensure `T025a` (MVP Stats) explicitly depends on `T012e-real-proxy` (Real Ground Truth Proxy) and `T021d` (Export Results). **Action**: Update `tasks.md` dependency graph and add a pre-flight check in `validation.py` that verifies `data/test/real_ground_truth_fixture.json` and `data/processed/drift_scores.csv` exist before attempting statistical calculation. **Rationale**: Prevents race conditions where validation runs before data generation completes.
- [ ] T051 [S] [US2] **Resource Constraint Fix**: Refine `T030a` (Stratification) to handle datasets larger than available RAM by streaming the `drift_scores.csv` file in chunks. **Action**: Implement `stratify_logs_streaming` in `annotator_interface.py` that reads the CSV line-by-line, accumulates scores in a sorted structure (e.g., `heapq` or external sort), and only loads the necessary top/bottom percentiles into memory. **Rationale**: Ensures the system adheres to the <7GB RAM constraint even with 100k+ logs, preventing OOM errors during annotation preparation.
- [ ] T052 [S] [US3] **Edge Case Fix**: Add explicit handling for `T039-gpt-run` when the `google/flan-t5-small` model output is ambiguous or non-binary. **Action**: Implement a `normalize_model_output` function in `comparison.py` that maps any output not strictly 'benign' or 'novel' to a neutral 'unknown' label, and logs a warning. The `AUC-ROC` calculation must then exclude 'unknown' entries or treat them as a third class with specific handling. **Rationale**: Prevents silent failures where ambiguous model outputs corrupt the baseline metric, ensuring the comparison is statistically valid.
- [ ] T053 [S] [US2] **Annotation Integrity Fix**: Enhance `T035-real` to detect and reject annotation files with duplicate `log_id` entries or missing `label` columns. **Action**: Add a `validate_annotation_integrity` step in `ingest_human_annotations` that raises a `ValueError` if the input CSVs contain duplicates or missing required fields. **Rationale**: Prevents corrupted data from entering the Kappa calculation, which could artificially inflate or deflate agreement scores.