# Tasks: llmXive Follow‑up: Context Fidelity vs. Model Scaling Trade‑offs  

**Input**: The active `spec.md`, `plan.md`, original research idea, existing artifacts, and concrete verification/reviewer feedback.  

This is a research implementation plan. Below are the concrete tasks required to satisfy the specification.  
Tasks are grouped by research phase and user story; each task follows the canonical checklist format.

---

## Phase 0 – Critical Pre‑requisites (Must Run First)  

**Goal**: Validate environment feasibility and resource constraints before any data processing or execution.  

- [ ] T001 [TASK] **Project scaffolding** – Create the missing directory structure, `__init__.py` files, `requirements.txt` (must contain `pyyaml` in addition to `transformers`, `datasets`, `scikit‑learn`, `statsmodels`, `networkx`, `pytest`, `ruff`, `black`, `huggingface_hub`), and configuration files `.ruff.toml` and `pyproject.toml` inside `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/`.  
  - **Verification**: Run `scripts/verify_scaffolding.sh` which checks (1) all required directories exist, (2) each directory contains an `__init__.py`, (3) `requirements.txt` lists the required packages (including `pyyaml`), (4) `.ruff.toml` and `pyproject.toml` exist and pass `ruff check` and `black --check`.  

- [ ] T042 [TASK] **Quantization calibration** – Implement `QuantizationCalibration` in `analysis/calibration.py`. Run a pilot inference on a tiny synthetic sample using Q4_K_M quantization on CPU with a strict 60‑minute timeout. Write `state/quantization_penalty.json` containing `{"penalty": <value>, "reason": "calibrated"}` (or timeout info).  
  - **Verification**: `state/quantization_penalty.json` exists, logs show “TIMEOUT” or “SUCCESS”, and the code explicitly sets `device='cpu'` with Q4_K_M flags.

**Checkpoint** – Environment feasibility confirmed; proceed to Phase 1.

---

## Phase 1 – Setup (Shared Infrastructure)

- [ ] T002 [ ] **Create `__init__.py` files** – Add an `__init__.py` to every package under `projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/`.  
  - **Verification**: `find … -type d -exec test -f {}/__init__.py \; -print | wc -l` matches the number of directories.

- [ ] T003 [ ] **Populate `requirements.txt`** – Ensure `requirements.txt` contains the full dependency list (including `pyyaml`).  
  - **Verification**: File exists and `pip check` reports no conflicts.

- [ ] T004a [ ] **Add lint/format config** – Create `.ruff.toml` and `pyproject.toml` for linting and formatting.  
  - **Verification**: Both files exist; `ruff check …` and `black --check …` return clean.

---

## Phase 2 – Foundational (Blocking Prerequisites)

*All tasks below must be completed before any user‑story work can begin.*

- [ ] T004c [ ] [US1 US2 US3] **Config module** – Add `config.py` with `RANDOM_SEED`, `BASELINE_N_LINES` (default 2048) and token‑limit logic.  
  - **Verification**: `python -c "import config; print(config.RANDOM_SEED)"` prints the seed; the file contains `BASELINE_N_LINES = min(BASELINE_N_LINES, token_limit)`.

- [ ] T004d [ ] [US1] **Baseline experiment seeds** – Update `experiments/run_baseline.py` to import and use `config.RANDOM_SEED`.  
  - **Verification**: Source contains `random.seed(config.RANDOM_SEED)`.

- [ ] T004e [ ] [US2 US3] **High‑fidelity experiment seeds** – Update `run_high_fidelity.py` and `run_7b_experiments.py` to use `config.RANDOM_SEED`.  
  - **Verification**: Both scripts call `random.seed(config.RANDOM_SEED)`.

- [ ] T005 [ ] **Deterministic logging** – Implement `utils/logger.py` with `setup_logger()` and `log_error()`.  
  - **Verification**: `pytest tests/unit/test_logger.py::test_logger_initialization` passes.

- [ ] T006a [ ] [US1 US2 US3] **TaskInstance model** – Add `models/task_instance.py` dataclass matching the `task_instance.schema.yaml`.  
  - **Verification**: `pytest tests/unit/test_models.py::test_task_instance_init` passes.

- [ ] T006b [ ] [US1 US2 US3] **ContextConfiguration model** – Add `models/context_config.py` dataclass matching `context_configuration.schema.yaml`.  
  - **Verification**: `pytest tests/unit/test_models.py::test_context_config_init` passes.

- [ ] T006c [ ] [US1 US2 US3] **ExecutionResult model** – Add `models/execution_result.py` dataclass matching `execution_result.schema.yaml`.  
  - **Verification**: `pytest tests/unit/test_models.py::test_execution_result_init` passes.

- [ ] T006d‑1 [ ] [US1 US2 US3] **Schema files** – Place `task_instance.schema.yaml`, `context_config.schema.yaml`, `execution_result.schema.yaml` under `specs/001-context-fidelity-scaling-tradeoff/contracts/`.  
  - **Verification**: Files exist and are valid YAML.

- [ ] T006d‑2 [ ] [US1 US2 US3] **Sample data generation** – Run `scripts/generate_sample.py --schema contracts/task_instance.schema.yaml --output data/sample.json`.  
  - **Verification**: `data/sample.json` exists and validates against the schema.

- [ ] T006d‑3 [ ] [US1 US2 US3] **Schema validation** – Execute `python -m jsonschema validate --schema contracts/task_instance.schema.yaml data/sample.json`.  
  - **Verification**: Command returns success.

- [ ] T007 [ ] **Environment variable management** – Add `HF_TOKEN`, `MODEL_PATH`, and `RANDOM_SEED` constants to `config.py`.  
  - **Verification**: `config.py` is importable and contains the variables.

- [ ] T016b [ ] [US1 US2 US3] **BatchExecutor** – Implement `experiments/batch_executor.py` with `submit()` method.  
  - **Verification**: `pytest tests/unit/test_batch_executor.py::test_batch_submit` passes.

- [ ] T016c [ ] [US1 US2 US3] **TimeoutGuard decorator** – Add to `batch_executor.py`.  
  - **Verification**: `pytest tests/unit/test_batch_executor.py::test_timeout_guard` passes.

- [ ] T026a [ ] [US1 US2 US3] **Quantized model loader** – Implement `models/quantization.py` `load_model_q4_k_m()` using `bitsandbytes` for the 1 B model and GGUF for the 7 B model, forcing `device='cpu'`.  
  - **Verification**: Grep finds `device.*cpu`; unit tests load both models and confirm RAM usage ≤ 7 GB.

- [ ] T026b [ ] [US1 US2 US3] **Memory‑pressure handling** – Add explicit RAM checks (via `psutil`) and aggressive fallback quantization.  
  - **Verification**: Code contains `psutil.virtual_memory()` logic and fallback branches.

- [ ] T026c [ ] [US1 US2 US3] **ModelRunner class** – Wrap loading logic for both 1 B and 7 B models with Q4_K_M on CPU.  
  - **Verification**: Smoke‑load of 7 B model succeeds within RAM limits and `device='cpu'` is enforced.

- [ ] T044 [ ] [US1 US2 US3] **RuntimeEstimator** – Read `state/quantization_penalty.json` and estimate total experiment duration; default to 0 penalty if missing. (depends on T042)  
  - **Verification**: Script prints an estimated duration and exits 0.

- [ ] T043 [ ] [US1 US2 US3] **GlobalTimeBudgetEnforcer** – Enforce per‑instance 60 min limit and overall ≤ 72 h wall‑clock budget.  
  - **Verification**: Log contains “Budget Enforced” entries.

- [ ] T008a [ ] [US1 US2 US3] **Schema validator for results** – Implement `analysis/merge_results.py::validate_schema()`.  
  - **Verification**: `pytest tests/unit/test_merge_results.py::test_validate_schema` passes.

- [ ] T008b [ ] [US1 US2 US3] **Result aggregation** – Implement `analysis/merge_results.py::aggregate_jsonl()` to produce `data/results.csv`.  
  - **Verification**: `pytest tests/unit/test_merge_results.py::test_aggregate_jsonl` passes.

- [ ] T017a [FR-008] [US1 US2 US3] **Failure classifier** – Add `analysis/failure_classifier.py::classify_failure(log: str) -> str` with rule‑based detection of “missing context” and “reasoning error”.  
  - **Verification**: `pytest tests/unit/test_failure_classifier.py::test_detects_file_not_found` passes.

---

## Phase 3 – User Story 1: Context‑Bound Filtering & Baseline Execution (P1)

*Independent test: filter the raw dataset, run a single baseline instance, verify Pass@1 and token metrics.*

- [ ] T010 [ ] [US1] **Loader unit‑test scaffolding** – Create empty test file `tests/unit/test_loader.py` with import stubs for `ClawSweBenchLoader`.  
  - **Verification**: Test file exists.

- [ ] T011 [ ] [US1] **Baseline timeout integration test** – Add `tests/integration/test_baseline_execution.py`.  
  - **Verification**: Test file exists.

- [ ] T012a [FR-001] [US1] **Streaming dataset fetch** – Implement `data/loader.py` using `datasets.load_dataset(..., streaming=True)`.  
  - **Verification**: Source contains `streaming=True` and raises on fetch failure.

- [ ] T012b [FR-001] [US1] **Static analysis for file identification** – In `loader.py`, parse `issue_description` with regex; if none, run frozen CodeBERT (`sentence‑transformers/all‑MiniLM‑L6‑v2`) on CPU to retrieve top‑5 candidate files.  
  - **Verification**: Code uses `re` for regex and a CPU‑only embedding model.

- [ ] T012c‑1 [FR-001] [US1] **Graph traversal & line counting** – Load each identified file, count lines, traverse import graph via `networkx`, summing line counts.  
  - **Verification**: Unit test `test_graph_traversal_sums_lines` passes.

- [ ] T012c‑2 [FR-001] [US1] **Filtering threshold** – Keep only instances where total relevant lines > 500.  
  - **Verification**: Unit test `test_filtering_threshold` passes.

- [ ] T012c‑3 [FR-001] [US1] **Write filtered Parquet** – Output to `data/filtered_swe_bench_v1.parquet` with schema (`instance_id`, `line_count`, `files_in_context`, `issue_description`, `repo_state`). Record checksum in `state/...yaml`.  
  - **Verification**: `python -c "import pandas as pd; df=pd.read_parquet('data/filtered_swe_bench_v1.parquet'); assert (df['line_count']>500).all()"` succeeds.

- [ ] T045 [FR-001] [US1] **Dataset‑size validator** – `analysis/threshold_validator.py` checks row count of the filtered Parquet:  
  - < 200 → exit 1 “Insufficient Context‑Bound Data”.  
  - 200 ≤ N < 800 → log “Exploratory Mode”.  
  - ≥ 800 → log “Confirmatory Mode”.  
  - **Verification**: Script logs row count and exits with the correct code.

- [ ] T014 [ ] [US1] **Baseline truncation strategy** – Implement `context_processors.py::first_n_lines()` using `config.BASELINE_N_LINES`.  
  - **Verification**: Function reads the config constant.

- [ ] T015 [FR-002] [US1] **Configure ModelRunner for 1 B model** – Set up runner to load the quantized 1 B LLM (CPU‑only).  
  - **Verification**: Runner loads the model without error.

- [ ] T016 [FR-002] [FR-005] [US1] **Baseline experiment script** – `experiments/run_baseline.py` iterates over the filtered dataset, applies `first_n_lines`, runs the 1 B model, enforces per‑instance 60 min and total ≤ 72 h via `GlobalTimeBudgetEnforcer`, records Pass@1, token count, and writes `data/intermediate/baseline_run.jsonl`.  
  - **Verification**: If prerequisites (T045, T042) failed, script logs “SKIPPED: Prerequisite Failed”. Otherwise it produces a non‑empty JSONL file, each line validates against `execution_result.schema.yaml`, and `state/time_budget.log` contains “Budget Enforced”.

- [ ] T017b [FR-005] [US1] **Annotate baseline failures** – Run `classify_failure()` on `baseline_run.jsonl` and add `failure_mode` field.  
  - **Verification**: Updated JSONL contains the new field.

---

## Phase 4 – User Story 2: High‑Fidelity Context Strategies (P2)

*Independent test: run TF‑IDF on a subset, verify context differs from baseline and produces a distinct output.*

- [ ] T018 [ ] [US2] **TF‑IDF unit test** – `tests/unit/test_context_processors.py::test_tfidf_retrieval`.  
  - **Verification**: Test file exists.

- [ ] T019 [ ] [US2] **Keyword‑proxy unit test** – `tests/unit/test_context_processors.py::test_keyword_proxy_window`.  
  - **Verification**: Test file exists.

- [ ] T020 [FR-003] [US2] **TF‑IDF/BM25 module** – Implement in `context_processors.py` using `scikit‑learn` `TfidfVectorizer(sublinear_tf=True, max_df=0.95)`.  
  - **Verification**: Vectorizer instantiated with the specified parameters.

- [ ] T021 [FR-003] [US2] **Heuristic Keyword‑Proxy** – Search relevant files for keywords (`fix`, `bug`, `error`, `TODO`), include a configurable sliding window, and log a critical audit entry noting this is a construct‑validity limitation.  
  - **Verification**: Log contains `LIMITATION: Heuristic Keyword‑Proxy used as diff‑aware proxy`.

- [ ] T022 [FR-003] [US2] **Rule‑based semantic summarization** – Extract the first sentence of each paragraph and the last sentence of each function block, concatenate with `...`, and truncate to the context window.  
  - **Verification**: Unit test `test_semantic_summarization` confirms heuristic behavior and truncation.

- [ ] T023 [FR-003] [FR-005] [US2] **Run all high‑fidelity strategies (1 B model)** – `experiments/run_high_fidelity.py` calls `run_strategy()` for Baseline, TF‑IDF, Keyword‑Proxy, and Summarization, respects the 60 min / 72 h budget via `GlobalTimeBudgetEnforcer`, and writes `data/intermediate/hf_run_1b.jsonl`.  
  - **Verification**: JSONL exists, contains records for all four strategies, validates against the schema, and `state/time_budget.log` shows enforcement.

- [ ] T023b [US2] **Entry‑point** – Add `main()` in `run_high_fidelity.py` to orchestrate the run.  
  - **Verification**: Script executes without error.

- [ ] T024 [US2] **Fallback on empty retrieval** – `context_processors.py::fallback_strategy()` returns `first_n_lines` when a retrieval module yields zero snippets; logs the event to `data/audit_logs/fallbacks.jsonl`.  
  - **Verification**: Test `test_fallback_on_empty_result` passes and log entry is created.

- [ ] T024a [US2] **Fail loudly on synthetic fallbacks** – Remove any `try/except` that would silently generate synthetic data; ensure the loader aborts with a clear error.  
  - **Verification**: Grep finds no `generate_synthetic` or `mock_` calls.

- [ ] T017c [FR-005] [US2] **Annotate high‑fidelity failures** – Apply `classify_failure()` to `hf_run_1b.jsonl`.  
  - **Verification**: Updated JSONL includes `failure_mode`.

---

## Phase 5 – User Story 3: Model Scaling & Interaction Analysis (P3)

*Independent test: run the 7 B model on all strategies, aggregate results, and perform a GLM with interaction term.*

- [ ] T030 [ ] [US3] **GLM test scaffolding** – `tests/unit/test_glm_analyzer.py` placeholder.  
  - **Verification**: Test file exists.

- [ ] T027 [FR-004] [US3] **7 B experiments** – `experiments/run_7b_experiments.py` runs the quantized 7 B model on Baseline, TF‑IDF, Keyword‑Proxy, and Summarization, respects budget via `GlobalTimeBudgetEnforcer`, and outputs `data/intermediate/hf_run_7b.jsonl`.  
  - **Verification**: JSONL exists, validates, contains all four strategies, and logs budget enforcement.

- [ ] T028 [FR-005] [SC-001] [SC-002] [US3] **Aggregate all results** – `analysis/merge_results.py` merges `baseline_run.jsonl`, `hf_run_1b.jsonl`, and `hf_run_7b.jsonl` into `data/results.csv`.  
  - **Verification**: CSV exists, non‑empty, and validates against `aggregated_result.schema.yaml`.

- [ ] T029a [SC-003] [US3] **GLM formula implementation** – `analysis/glm_analyzer.py::run_glm_formula()` builds the model  
  `Pass ~ Model_Size + Context_Strategy + Model_Size:Context_Strategy + Task_Difficulty + Quantization_Penalty`.  
  - **Verification**: Function signature present and formula string matches.

- [ ] T029b [SC-003] [FR-006] [US3] **Firth penalization fallback** – Attempt Firth‑penalized GLM (via `statsmodels` or `firth‑logistic`); on failure, fall back to standard GLM and log “Separation Risk”.  
  - **Verification**: Logs indicate which path was taken; interaction p‑value is numeric.

- [ ] T029c [SC-003] [US3] **Power analysis** – `glm_analyzer.py::power_analysis()` computes statistical power; if N < 800, sets `study_type = "Exploratory"` and ensures the primary reported metric is Odds Ratio with 95 % CI.  
  - **Verification**: Log warns when power < 0.8 and `study_type` flag is set appropriately.

- [ ] T030a [US3] **Pairwise Pass@1 differences** – `glm_analyzer.py::calculate_pairwise_diff()` computes ΔPass@1 between 1 B high‑fidelity and 7 B baseline per strategy.  
  - **Verification**: Function returns a dictionary of differences.

- [ ] T030b [US3] **Significance check** – `glm_analyzer.py::check_significance()` calculates margin, p‑value, and logs them (does not enforce pass/fail).  
  - **Verification**: Unit test confirms correct arithmetic.

- [ ] T030c [SC-004] [US3] **Final comparison report** – Generate `data/analysis_flags.json` (and optional `data/results/comparison_report.md`) containing keys  
  `strategy_found`, `margin`, `p_value`, `odds_ratio`, `ci_lower`, `ci_upper`, `study_type`.  
  - **Verification**: Running `scripts/test_dynamic_flags.py` modifies `results.csv` and asserts the JSON updates accordingly; report includes explicit statement when a strategy meets the ≥ 5 % margin with p < 0.05, otherwise states “No strategy found …”.

- [ ] T017d [FR-005] [US3] **Annotate 7 B failures** – Apply `classify_failure()` to `hf_run_7b.jsonl`.  
  - **Verification**: Updated JSONL includes `failure_mode`.

---

## Phase 6 – Analysis & Reporting (Defect Resolution)

*All tasks below address issues raised by `/speckit.analyze`.*

- [ ] T061 [US1] **Hybrid IR‑Seeding CPU‑only** – Ensure loader uses `sentence‑transformers/all‑MiniLM‑L6‑v2` with `device='cpu'`.  
  - **Verification**: No `cuda`/`gpu` strings in `loader.py`.

- [ ] T062 [US2] **TF‑IDF over‑fitting guard** – Use `TfidfVectorizer(sublinear_tf=True, max_df=0.95)`.  
  - **Verification**: Vectorizer init matches spec.

- [ ] T063 [US3] **Log‑transform task difficulty** – In GLM, `Task_Difficulty = np.log(line_count + 1)`.  
  - **Verification**: Formula string contains `np.log`.

- [ ] T064 [US1 US2 US3] **Streaming checksum** – `utils/checksum.py` now streams files in chunks for SHA‑256; verifies filtered Parquet checksum against raw dataset.  
  - **Verification**: `pytest tests/unit/test_checksum.py::test_streamed_checksum` passes.

- [ ] T065 [US3] **Firth separation test** – Add unit test `tests/unit/test_glm_analyzer.py::test_firth_separation` with synthetic perfectly separated data; logs convergence status.  
  - **Verification**: Test passes and logs are present.

- [ ] T066 [US1 US2 US3] **Time‑budget logging** – `time_budget.py` now logs remaining budget and estimated completion before each batch.  
  - **Verification**: Logs contain “Remaining budget:” and “Estimated completion:” lines.

- [ ] T067 [US1 US2 US3] **Prevent data leakage** – Loader excludes any files appearing in `test_patch` or `ground_truth`. Logs count of excluded files.  
  - **Verification**: Loader contains explicit exclusion checks; log entry appears.

- [ ] T068 [US3] **Dynamic quantization‑penalty usage** – GLM reads the actual `penalty` value from `state/quantization_penalty.json` and incorporates it into the model formula.  
  - **Verification**: GLM formula string includes the variable `penalty`.

- [ ] T069 [US1 US2 US3] **Structured JSON logging** – `utils/logger.py` outputs logs as JSON with `timestamp`, `level`, `instance_id`, `strategy`.  
  - **Verification**: Sample log parses as valid JSON and contains required fields.

- [ ] T070 [US1 US2 US3] **Ambiguous failure handling** – `failure_classifier.py` now logs the specific rule triggered when multiple failure indicators are present.  
  - **Verification**: Simulated ambiguous log produces a log entry with `triggered_rule`.

---

## Phase N – Polish & Cross‑Cutting Concerns

- [ ] T035 [ ] **Documentation** – Update `docs/quickstart.md` and `docs/data-model.md` with up‑to‑date usage instructions and entity definitions.  
  - **Verification**: Files contain steps 1‑3 and full data‑model diagram.

- [ ] T036 [ ] **Context‑processor refactor** – Extract model loading to `models/runner.py`; cyclomatic complexity of `context_processors.py` reduced below 10.  
  - **Verification**: Complexity measured with `radon` is ≤ 10.

- [ ] T037 [ ] **Batch executor tuning** – Adjust parallel‑batch parameters to guarantee total wall‑clock ≤ 72 h on the free‑tier runner.  
  - **Verification**: Empirical run stays within budget.

- [ ] T038 [ ] **Additional edge‑case unit tests** – Tests for empty context and timeout in `tests/unit/`.  
  - **Verification**: `pytest tests/unit/` passes.

- [ ] T039 [FR-005 Const‑III] **Checksum & derivation tracking** – Generate SHA‑256 hashes for all major artifacts (`results.csv`, all JSONL files, filtered Parquet) and record them in `state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml`. Produce accompanying `derivation.json` documenting each transformation step.  
  - **Verification**: State file contains the required keys; `derivation.json` is valid JSON.

- [ ] T054 [FR-001 Const‑III] **Representativeness validator** – `analysis/representativeness_validator.py` performs a KS test between `line_count` distributions of raw vs. filtered datasets; logs a warning if KS > 0.1.  
  - **Verification**: Script runs and logs statistic/p‑value.

- [ ] T055 [FR-001 Const‑III] **Construct‑validity audit** – Compute correlation between Hybrid IR‑Seeding scores and TF‑IDF scores; log a critical warning if correlation > 0.3.  
  - **Verification**: Log reports correlation coefficient.

- [ ] T056 [FR-003] **Summarization docstring** – Add explicit comment in `strategies/summarization.py` describing the “first sentence of paragraph / last sentence of function” heuristic as a lower‑bound proxy.  
  - **Verification**: Docstring present.

- [ ] T057 [FR-006] **Power‑analysis reporter** – `glm_analyzer.py` now outputs `study_type` flag (“Exploratory” or “Confirmatory”) in the final JSON report.  
  - **Verification**: Report JSON includes the flag.

- [ ] T058 [FR-007] **Dynamic back‑off for time budget** – `batch_executor.py` aborts remaining instances with a “Timeout” status when estimated remaining time exceeds the 72 h limit.  
  - **Verification**: Log shows “Timeout” and no further processing occurs.

- [ ] T059 [FR-001] **Hybrid IR‑Seeding sanity check** – Unit test ensures loader never reads `test_patch` or `ground_truth`.  
  - **Verification**: Test fails if loader accesses those fields.

- [ ] T060 [FR-008] **Failure‑mode aggregator** – `analysis/failure_classifier.py` produces a summary report of failure‑mode counts per configuration.  
  - **Verification**: Report file exists and matches expected aggregation.

---

## Phase N+1 – Revision & Corrective Actions (Pending)

*These tasks address remaining gaps identified during the latest analysis pass. They are currently unchecked and must be completed before the project can be considered “analyzed”.*

- [ ] T071 [US1 US2 US3] **Streaming chunk aggregation** – Refactor `loader.py` to compute line‑count statistics on‑the‑fly using `datasets.load_dataset(..., streaming=True)`, storing only metadata for filtered instances in a temporary Parquet file.  
  - **Verification**: Memory monitor shows < 7 GB RAM during a dry run; output Parquet contains correct filtered rows.

- [ ] T072 [US1 US2 US3] **Dynamic study‑type adjustment** – Update `threshold_validator.py` to set `study_type` (“Exploratory” vs. “Confirmatory”) based on actual row count and propagate this flag to `glm_analyzer.py`.  
  - **Verification**: Script logs the correct study type.

- [ ] T073 [US2] **Robust fallback for empty context** – Ensure any retrieval module that returns zero snippets triggers `fallback_strategy()` (first‑N‑lines) and logs the event to `data/audit_logs/fallbacks.jsonl`.  
  - **Verification**: Simulated empty result produces a log entry and uses baseline context.

- [ ] T074 [US3] **Robust Firth fallback** – In `glm_analyzer.py`, catch convergence errors, fall back to standard GLM, and log the reason.  
  - **Verification**: Simulated convergence failure results in fallback log.

- [ ] T075 [US1 US2 US3] **Dynamic time‑budget enforcement** – Enhance `time_budget.py` to recompute remaining time before each batch and shrink batch size if needed; log “Timeout” when budget would be exceeded.  
  - **Verification**: Simulated slow batch triggers timeout log and stops further processing.

- [ ] T076 [US1 US2 US3] **Data‑leakage prevention** – Reinforce loader checks that exclude any file appearing in `test_patch` or `ground_truth`; log count of excluded files.  
  - **Verification**: Loader contains explicit exclusion logic; log entry appears.

- [ ] T077 [US3] **Dynamic quantization‑penalty usage** – Ensure GLM reads the exact `penalty` value from `state/quantization_penalty.json` and incorporates it into the model formula.  
  - **Verification**: GLM formula string includes the variable `penalty`.

- [ ] T078 [US1 US2 US3] **Structured logging overhaul** – Refactor `logger.py` so every log entry is JSON‑formatted with `timestamp`, `level`, `instance_id`, `strategy`.  
  - **Verification**: Sample log parses as JSON and contains required fields.

- [ ] T079 [US1 US2 US3] **Ambiguous‑failure handling** – Priority‑based rule system in `failure_classifier.py` logs the specific rule triggered when multiple failure indicators are present.  
  - **Verification**: Simulated ambiguous log produces a log entry with `triggered_rule`.

- [ ] T080 [US1 US2 US3] **Streaming checksum verification** – Update `checksum.py` to compute SHA‑256 on streamed chunks for large files and verify the filtered Parquet checksum matches the raw dataset checksum.  
  - **Verification**: Test `test_streamed_checksum` confirms identical hashes.
