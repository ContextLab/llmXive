# Tasks: Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation

**Inputs**: The active `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.

---

## Phase 1 – Setup and first end‑to‑end analysis

- [ ] T001a Create directory structure: `src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/prompts/`, `data/evaluation/`, `state/`, `state/checksums/`.  
  *Verification:* Run a script that asserts each directory exists; log success in `logs/setup.log`.
- [ ] T001b Create `.gitignore` to exclude `data/raw/`, `data/processed/`, `data/evaluation/`, `__pycache__/`, `*.pyc`, `venv/`.  
  *Verification:* Check that `git status` does not show ignored paths.
- [ ] T001c Create initial `requirements.txt` and `package.json` placeholder files.  
  *Verification:* Ensure both files exist and contain at least one pinned dependency; CI installs them without error.

## Phase 2 – Foundational (blocking prerequisites)

- [ ] T009 Implement `src/utils/timeout_utils.py` providing `api_timeout(seconds)` and `test_timeout(seconds)` helpers for enforcing a 120 s API timeout and a 10 s test timeout.  
  *Verification:* Unit tests `tests/unit/test_timeout_utils.py` assert correct exception raising on timeout.
- [ ] T013 Implement `src/ingestion/download_datasets.py` to fetch `codeparrot/code-trans-py-js` and `bigcode/evaluation` via the `datasets` library, caching raw files under `data/raw/`.  
  *Verification:* Contract test `tests/contract/test_dataset_fetch.py` confirms both datasets are downloaded.
- [ ] T013b Implement validation in `src/ingestion/preprocess_corpus.py` to exclude entries with missing or malformed code and log exclusions.  
  *Verification:* Unit test `tests/unit/test_preprocess_validation.py` checks that malformed entries are omitted.
- [ ] T013c Implement streaming sampling in `src/ingestion/preprocess_corpus.py` to produce `data/processed/corpus.csv` with **≥ 200** valid Python‑JS pairs while keeping peak RAM ≤ 7 GB.  
  *Verification:* Integration test `tests/integration/test_preprocess_memory.py` asserts RAM usage stays below 7 GB and row count ≥ 200.
- [ ] T014 Add a post‑processing assertion that `data/processed/corpus.csv` contains at least 200 rows.  
  *Verification:* Script checks row count and fails if < 200.
- [ ] T015 Integrate `src/utils/checksum_artifacts.py` to hash raw files before preprocessing.  
  *Verification:* `state/checksums/` contains SHA‑256 files for each raw dataset file.
- [ ] T006 Implement `src/utils/checksum_artifacts.py` to generate SHA‑256 hashes for files in `data/raw/` and write results to `state/checksums/`.  
  *Verification:* All raw files have corresponding checksum files; checksum script exits with zero status.
- [ ] T007 Implement `src/utils/update_state.py` to track artifact hashes and update `state/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e.yaml`.  
  *Verification:* After any artifact change, the YAML `artifact_hashes` map is updated; unit test `tests/unit/test_update_state.py` validates this.
- [ ] T010 Implement creation of the four prompt template files in `data/prompts/` with concrete, non‑placeholder content.  
  *Verification:* Each file exists and contains at least 10 words (checked by `tests/contract/test_prompts_exist.py`).  
  **Sub‑tasks:**  
  - [ ] T010a Create `data/prompts/zero_shot_basic.txt` containing a concise instruction to translate Python to JavaScript without style constraints. Example content:  
    ```
    Translate the following Python function to equivalent JavaScript. Preserve functionality and variable names. Do not add comments or extra code.
    ```  
  - [ ] T010b Create `data/prompts/zero_shot_style.txt` adding an explicit style specification (use ES6 syntax, prefer const/let, avoid var). Example content:  
    ```
    Translate the following Python function to JavaScript using modern ES6 syntax. Use const/let, arrow functions where appropriate, and avoid var. Preserve functionality.
    ```  
  - [ ] T010c Create `data/prompts/few_shot_basic.txt` that includes the zero‑shot instruction plus two short example Python‑JS pairs drawn from the corpus. Example content:  
    ```
    Translate the following Python function to JavaScript.

    Example 1:
    Python: def add(a, b): return a + b
    JavaScript: function add(a, b) { return a + b; }

    Example 2:
    Python: def square(x): return x * x
    JavaScript: function square(x) { return x * x; }

    Now translate:
    ```  
  - [ ] T010d Create `data/prompts/few_shot_style.txt` combining the style specification with the same two examples as in T010c. Example content:  
    ```
    Translate the following Python function to JavaScript using modern ES6 syntax. Use const/let, arrow functions where appropriate, and avoid var.

    Example 1:
    Python: def add(a, b): return a + b
    JavaScript: const add = (a, b) => a + b;

    Example 2:
    Python: def square(x): return x * x
    JavaScript: const square = x => x * x;

    Now translate:
    ```  

## Phase 3 – User Story 1: Dataset Acquisition & Preprocessing (Priority P1)

- [ ] T011 Contract test `tests/contract/test_dataset_fetch.py` verifies that `src/ingestion/download_datasets.py` fetches both HuggingFace datasets.  
  *Verification:* Test passes when both datasets are present under `data/raw/`.
- [ ] T012 Integration test `tests/integration/test_preprocess_memory.py` checks that preprocessing respects the 7 GB RAM ceiling.  
  *Verification:* Test monitors memory usage during `preprocess_corpus.py` execution.
- [ ] T016 Log memory usage and excluded‑entry counts to `logs/dataset_preprocess.log`.  
  *Verification:* Log file contains numeric memory peak and exclusion count entries.

## Phase 4 – User Story 2: Prompt Condition Execution (Priority P2)

- [ ] T018 Contract test `tests/contract/test_api_client.py` validates request construction in `src/execution/api_client.py`.  
  *Verification:* Test confirms correct headers, payload, and endpoint URL.
- [ ] T019 Integration test `tests/integration/test_inference_retry.py` checks timeout and exponential‑backoff behavior.  
  *Verification:* Simulated rate‑limit triggers three retries with back‑off; test asserts final status.
- [ ] T020 Implement `src/execution/api_client.py` with exponential backoff (max 3 retries), 120 s timeout using `src/utils/timeout_utils.py`, and robust error handling for malformed responses. Target endpoint: `[UNRESOLVED-CLAIM: https://api-inference.huggingface.co/models/codellama/CodeLlama-7b-Instruct-hf` — ConnectionError: HTTPSConnectionPool(host='api-inference.huggingface.co', port=443): Max retries exceeded with url: /models/codellama/CodeLlama-7b-Instruct-hf%60 (Caused by NameResolutionError("HTTPSConnection(host='api-inference.huggingface.co', port=443): Failed to resolve 'api-inference.huggingface.co' ([Errno -5] No address associated with hostname)"))].  
  *Verification:* Unit tests `tests/unit/test_api_client_error_handling.py` cover malformed JSON and timeout cases.
- [ ] T021 Implement `src/execution/run_inference.py` to iterate over `data/processed/corpus.csv`, apply each of the four prompt files from `data/prompts/`, and invoke `src/execution/api_client.py`.  
  *Verification:* End‑to‑end run creates output directories and logs; CI runs the script on a small sample and checks for success.
- [ ] T022 Ensure deterministic execution by pinning `seed=42`, `temperature=0.0` and logging for every request: prompt text, model version, seed, timestamp. Logs written to `logs/inference.log`.  
  *Verification:* Unit test `tests/unit/test_determinism.py` asserts identical logs on repeated runs.
- [ ] T023 Store generated JavaScript files under `data/evaluation/raw_translations/<condition_name>/<snippet_id>.js`, creating the required sub‑directory hierarchy.  
  *Verification:* Contract test `tests/contract/test_output_hierarchy.py` checks that each condition folder contains the expected number of `.js` files.
- [ ] T024 Detect non‑code responses (e.g., empty string, “I cannot do that”) and record a `failed_translation` entry in `logs/failed_translations.log`.  
  *Verification:* Unit test `tests/unit/test_failed_translation.py` validates that such responses are logged.
- [ ] T025b Implement `src/evaluation/generate_translations_log.py` to aggregate prompts, seeds, raw LLM responses into `data/evaluation/raw_translations_log.csv` (excluded from git via `.gitignore`).  
  *Verification:* Log file contains one row per request with all required columns.
- [ ] T025c Implement `src/evaluation/generate_metadata_log.py` to produce a version‑controlled CSV `data/evaluation/metadata_log.csv` containing columns `snippet_id`, `condition_name`, `prompt_path`, `seed`, `timestamp`. Commit the CSV to git.  
  *Verification:* Contract test `tests/contract/test_metadata_log.py` checks schema and presence of all rows.

## Phase 5 – User Story 3: Functional Correctness & Quality Analysis (Priority P3)

- [ ] T025 Contract test `tests/contract/test_test_translation.py` validates the test‑translation pipeline.  
  *Verification:* Test passes when `translate_tests.py` produces a JavaScript test suite that can be executed.
- [ ] T026 Integration test `tests/integration/test_node_runner.py` ensures the Node.js runner respects the 10 s timeout.  
  *Verification:* Test runs a deliberately hanging JS file and asserts timeout handling.
- [ ] T027a Document deterministic test‑translation strategy in `data/evaluation/transpiler_strategy.md` (choose `transcrypt` or an LLM fallback with pinned prompts).  
  *Verification:* File exists and outlines chosen method.
- [ ] T027 Implement `src/evaluation/translate_tests.py` following the strategy in `transpiler_strategy.md`.  
  *Verification:* Unit test `tests/unit/test_translate_tests.py` checks that a Python test file is correctly turned into JavaScript.
- [ ] T028 Implement `src/evaluation/run_node_tests.py` to execute translated tests against generated JavaScript, recording `pass/fail/timeout/skipped` in `data/evaluation/validation_results.csv`.  
  *Verification:* Contract test `tests/contract/test_validation_results_schema.py` validates CSV schema.
- [ ] T029 Implement `src/evaluation/compute_quality.py` using ESLint’s complexity plugin to compute `complexity_score` and `lines_of_code` for each generated JS file; output to `data/evaluation/quality_metrics.csv`.  
  *Verification:* Unit test `tests/unit/test_compute_quality.py` asserts numeric values for a sample file.
- [ ] T030 Implement `src/evaluation/statistical_analysis.py` to perform:  
  - Chi‑square tests for correctness across the four conditions,  
  - Repeated‑measures ANOVA for cyclomatic complexity and lines‑of‑code,  
  - Bonferroni correction for multiple comparisons,  
  - Optional logistic regression to assess snippet‑difficulty confounding.  
  Results written to `data/evaluation/statistical_summary.csv`.  
  *Verification:* Unit test `tests/unit/test_statistical_analysis.py` checks that the CSV contains expected columns and that p‑values are numeric.
- [ ] T031 Produce `data/evaluation/statistical_summary.csv` conforming to `specs/001-evaluating-the-effectiveness-of-prompt-e/contracts/statistical_summary.schema.yaml`.  
  *Verification:* Contract test `tests/contract/test_statistical_summary_schema.py` validates schema compliance.
- [ ] T032 Extend `src/utils/update_state.py` (if not already) to record a state hash after evaluation completes and write a timestamp to `state/projects/...`.  
  *Verification:* After pipeline run, the YAML file’s `updated_at` timestamp reflects the latest evaluation.
- [ ] T032b Implement `src/utils/measure_runtime.py` to log total pipeline execution time against the 6‑hour budget.  
  *Verification:* Unit test `tests/unit/test_measure_runtime.py` asserts existence of `logs/runtime.log` with a numeric runtime ≤ 21600 s.
- [ ] T033 Implement `src/evaluation/classify_failures.py` to label each translation as `syntax_error`, `semantic_hollow`, `rigidity`, or `confabulation` and write to `data/evaluation/failure_classification.csv`.  
  *Verification:* Contract test `tests/contract/test_classify_failures.py` checks CSV schema and that each row has a non‑empty classification.
- [ ] T034 Generate `data/evaluation/failure_topology_report.csv` summarizing counts per condition and failure type.  
  *Verification:* Contract test `tests/contract/test_failure_topology_report.py` validates file existence and required columns.
- [ ] T035 Merge failure‑topology metrics into `data/evaluation/statistical_summary.csv` where appropriate.  
  *Verification:* Integration test `tests/integration/test_merge_summary.py` diffs the summary before/after merge and asserts new rows are added.
- [ ] T036 Implement `src/evaluation/analyze_failure_topology.py` to produce a qualitative markdown report `data/evaluation/failure_topology_analysis.md`.  
  *Verification:* Contract test `tests/contract/test_analyze_failure_topology.py` checks that the markdown file is non‑empty.
- [ ] T037 Implement `src/utils/changelog.py` to append pipeline changes to `data/evaluation/changelog.md` with timestamps and rationales.  
  *Verification:* Unit test `tests/unit/test_changelog.py` appends a dummy entry and asserts its presence.
- [ ] T038 Implement `src/evaluation/sensitivity_analysis.py` to sweep α values, compute robustness metrics, and append results to `data/evaluation/sensitivity_report.csv`.  
  *Verification:* Contract test `tests/contract/test_sensitivity_report.py` validates CSV schema and that at least three α values are recorded.

## Phase 6 – Polish & Cross‑Cutting Concerns

- [ ] T039 Update documentation in `docs/quickstart.md` with commands to run the full pipeline end‑to‑end.  
  *Verification:* Run the commands from the markdown on a fresh checkout; all expected CSV artifacts appear.
- [ ] T040 Refactor error‑handling paths in `src/utils/error_handling.py` to consolidate exception classes and improve messages. Add unit test `tests/unit/test_error_handling.py` to verify new behavior.  
  *Verification:* Test suite passes and coverage for error handling reaches 100 %.
- [ ] T041 Optimize API request batching where rate limits permit by implementing `src/execution/batching.py`. Add unit test `tests/unit/test_batching.py`.  
  *Verification:* Test confirms that batch size respects a configurable limit and that total request count is reduced.
- [ ] T042 Add additional unit tests for utility functions under `tests/unit/`.  
  *Verification:* CI reports ≥ 90 % coverage for `src/utils/`.
- [ ] T043 Validate that `quickstart.md` reproduces the full analysis and generates all expected CSV artifacts.  
  *Verification:* End‑to‑end run from `quickstart.md` succeeds on CI.