# Tasks: Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation

**Inputs**: `spec.md`, `plan.md`, data‑model contracts, verifier‑rejected task list, reviewer feedback. All tasks write only project‑owned paths (`code/`, `data/`, `paper/`, `specs/`, `figures/`). State‑updates are handled by the platform.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [P] [US1] Implement `code/src/ingestion/download_datasets.py` that streams **both** HuggingFace datasets `codeparrot/code-trans-py-js` **and** `bigcode/evaluation` via `datasets.load_dataset(..., streaming=True)`. Write raw rows under `data/raw/` and raise on any fetch failure. Record dataset ID, split, and row count in `data/raw/ingestion_log.json`.
  *Verification:* `pytest code/tests/contract/test_dataset_fetch.py` asserts real rows are present and that a forced fetch failure raises.

- [ ] T002 [US1] Implement `code/src/ingestion/preprocess_corpus.py` that iterates the streamed raw data in chunks, filters entries with missing or syntactically invalid Python (`ast.parse`) or JavaScript, logs excluded entries to `data/logs/dataset_preprocess.log`, samples **≥ 200** valid pairs with a fixed seed, and writes `data/processed/corpus.csv` conforming to `dataset.schema.yaml`. Ensure peak memory ≤ 7 GB.
  *Verification:* `pytest code/tests/integration/test_preprocess_memory.py` asserts ≥ 200 rows, schema conformance, and RSS < 7 GB.

- [ ] T003 [US2] Create the four prompt template files in `data/prompts/` with complete, non‑placeholder text: `zero_shot_basic.txt`, `zero_shot_style.txt`, `few_shot_basic.txt`, `few_shot_style.txt`. Few‑shot files must contain two concrete Python→JavaScript example pairs sampled from `data/processed/corpus.csv` with a fixed seed.
  *Verification:* `pytest code/tests/contract/test_prompts_exist.py` confirms existence, ≥ 10 words each, and that few‑shot files contain both Python and JavaScript example blocks.

- [ ] T004 [US2] Implement core inference in `code/src/execution/run_inference.py`. Load `data/processed/corpus.csv` and the four prompt files; for each (snippet, condition) call the HuggingFace Inference API with model `codellama/CodeLlama-7b-Instruct-hf`, `seed=42`, `temperature=0.0`. Enforce a 30 s request timeout, exponential backoff (≤ 3 retries) for rate limits, and detect non‑code responses (log as failure). Write generated JavaScript to `data/evaluation/raw_outputs/<condition_name>/<snippet_id>.js`. Write the **raw LLM response** to `data/evaluation/raw_responses/<condition_name>/<snippet_id>.txt`. Log each attempt in `data/evaluation/metadata_log.csv` with columns `snippet_id`, `condition_name`, `prompt_path`, `prompt_text`, `model_version`, `seed`, `timestamp`, `response_status`, `raw_response_path`. The `raw_response_path` points to the file created above, satisfying FR‑006 and US‑2 scenario 3.
  *Verification:* `pytest code/tests/unit/test_timeout_utils.py`, `code/tests/unit/test_failed_translation.py`, `code/tests/contract/test_metadata_log.py`, `code/tests/contract/test_output_hierarchy.py`.

- [ ] T005 [P] Run a thin end‑to‑end analysis on a small real sample (`N=5` snippets × 4 conditions) using T001–T004. Verify real JavaScript files, populated `metadata_log.csv`, and that `code/src/main.py --sample 5` reproduces the artifacts. Document the command in `specs/001-evaluating-the-effectiveness-of-prompt-e/quickstart.md`.
  *Verification:* The command executes and `data/evaluation/raw_outputs/` contains ≥ 20 non‑empty `.js` files.

## Phase 2: Complete the study and validate its evidence

- [ ] T006 [US3] Implement `code/src/evaluation/translate_python_tests.py` that translates the original Python unit tests for each snippet to JavaScript using the same LLM (or a verified transpiler). Store translated test files under `data/evaluation/translated_tests/<snippet_id>_test.js`. Log any translation failures (e.g., refusal, malformed output) in `data/logs/test_translation_errors.log`.
  *Verification:* `pytest code/tests/contract/test_test_translation.py` checks that for each snippet a corresponding `.js` test file exists (or a failure is logged) and that the file is syntactically valid JavaScript.

- [ ] T007 [US3] Implement `code/src/evaluation/run_js_validation.py` that executes each generated JavaScript file against its translated test suite using Node.js with a 10 s per‑test timeout (via `timeout_utils`). Record binary pass/fail (plus `timeout`/`skipped` statuses) and execution time in `data/evaluation/validation_results.csv` conforming to `translation_result.schema.yaml`.
  *Verification:* `pytest code/tests/contract/test_translation_result_schema.py` and `code/tests/contract/test_js_validation.py` validate schema and correct handling of passing, failing, and timeout cases.

- [ ] T008 [US3] Implement `code/src/evaluation/compute_quality.py` that runs the ESLint complexity plugin on every generated `.js` file. For files that fail to parse, record `complexity_score = 0`. Write results to `data/evaluation/quality_metrics.csv` (`snippet_id`, `condition_name`, `complexity_score`, `lines_of_code`).
  *Verification:* `pytest code/tests/unit/test_compute_quality.py` and `code/tests/contract/test_quality_metrics_schema.py` assert numeric scores and schema compliance.

- [ ] T009 [US2] Execute the full experimental domain (all ≥ 200 snippets × 4 conditions) using the pipeline T001–T008. Monitor wall‑clock time; if the extrapolated total exceeds 6 h, invoke the checkpoint/fallback task (T018) to switch to the N=50 fallback and record the decision in `data/logs/runtime.log`. On any unrecoverable API failure, abort loudly (no Ollama substitution). Produce the full set of CSVs (`metadata_log.csv`, `validation_results.csv`, `quality_metrics.csv`) and the runtime log.
  *Verification:* All CSVs contain rows for the executed sample; `runtime.log` reports ≤ 21600 s or a documented fallback decision.

- [ ] T010 [US3] Implement `code/src/evaluation/statistical_analysis.py` that:
  1. Performs a chi‑square test of correctness rates across the four prompt conditions (primary test, baseline = zero_shot_basic).  
  2. Runs repeated‑measures ANOVA for cyclomatic complexity and lines of code across conditions.  
  3. Applies Bonferroni correction to all pairwise comparisons.  
  4. Computes effect sizes (Cohen’s h for chi‑square, eta‑squared for ANOVA) and post‑hoc observed power.  
  5. Emits `data/evaluation/statistical_summary.csv` conforming to `statistical_summary.schema.yaml`.  
  6. If any comparison’s observed power < 0.80, adds a `power_limitation` row.
  *Verification:* `pytest code/tests/unit/test_statistical_analysis.py` checks required columns, correct correction method, and presence of baseline comparisons.

- [ ] T011 [US3] Generate summary tables and figures directly from the validated CSVs:
  - `data/results/summary_table.csv` (pass rates, mean complexity, mean LOC per condition with 95 % CIs).  
  - `figures/correctness_by_condition.png` and `figures/quality_by_condition.png` via matplotlib.
  *Verification:* `code/tests/contract/test_summary_table.py` re‑derives the table and matches; figure files exist and are non‑empty.

- [ ] T012 [US3] Write `paper/methods_and_results.md` linking every reported number to its source CSV cell, including a short “error taxonomy” subsection classifying failed translations (syntax error, runtime error, wrong output, refusal/timeout). Reference the deviation changelog (T016) for any spec departures (e.g., fallback policy). Ensure all FR/SC claims are traceable.
  *Verification:* Manual/automated review confirms every numeric claim maps to an existing CSV cell and that no placeholder numbers remain.

- [ ] T013 [P] Re‑run the documented workflow end‑to‑end (`code/src/main.py` per `quickstart.md`), confirm all pytest suites pass, runtime ≤ 6 h, memory ≤ 7 GB, and record the paper‑stage handoff in `paper/methods_and_results.md`.
  *Verification:* Full `pytest code/tests/` passes; `runtime.log` ≤ 21600 s; quickstart reproduces all result artifacts.

## Phase 3: Supporting infrastructure and compliance

- [ ] T014 [P] Implement `code/src/utils/checksum_artifacts.py` that computes SHA‑256 checksums for **every file** under `data/raw/` and writes a manifest `data/raw/checksums.json`. This satisfies Constitution III (data hygiene) by recording hashes in a project‑owned location.
  *Verification:* `pytest code/tests/contract/test_checksum_artifacts.py` validates that the manifest contains an entry for each raw file and that hashes match file contents.

- [ ] T015 [P] Create a pinned `requirements.txt` (Python) and ensure `package.json`/`package-lock.json` are present at the project root, enumerating exact versions of all dependencies (including ESLint, statsmodels, etc.). This fulfills reproducibility (Constitution I) and the missing dependency‑pinning requirement.
  *Verification:* `pip install -r requirements.txt` succeeds; `npm ci` reproduces the exact Node environment.

- [ ] T016 [P] Write `data/changelog/deviations.md` documenting any deviation from the original specification or constitution (e.g., replacement of translated‑unit‑test evaluation with I/O‑pair extraction if ever used, policy change regarding Ollama fallback). This satisfies Constitution VII’s requirement to record justified deviations.
  *Verification:* Presence of the file is checked by `code/tests/contract/test_deviation_changelog.py`.

- [ ] T017 [P] Implement `code/src/utils/metadata_schema_validator.py` that validates `data/evaluation/metadata_log.csv` against the expected schema, ensuring the `raw_response_path` column exists and points to a real file. Run as part of the pipeline after inference.
  *Verification:* `pytest code/tests/contract/test_metadata_schema.py` confirms schema compliance.

- [ ] T018 [P] Implement a checkpoint/fallback logic script `code/src/utils/checkpoint_fallback.py` that monitors elapsed wall‑clock time during T009, predicts total runtime, and if > 5.5 h triggers a fallback to the N=50 sample size, recording the decision in `data/logs/runtime.log`. This task is referenced by T009.
  *Verification:* Unit test `code/tests/unit/test_checkpoint_fallback.py` simulates elapsed times and checks correct fallback activation.

- [ ] T019 [P] Add a script `code/src/utils/raw_response_persistence.py` that, given the raw LLM response string, writes it to the appropriate `data/evaluation/raw_responses/<condition>/<snippet_id>.txt` and returns the file path for inclusion in `metadata_log.csv`.
  *Verification:* `pytest code/tests/unit/test_raw_response_persistence.py` confirms file creation and correct path returned.

- [ ] T020 [P] Implement `code/src/evaluation/check_paper_traceability.py` that parses `paper/methods_and_results.md`, extracts all numeric values, and verifies each originates from a cell in one of the CSV artifacts. Report any unmatched numbers.
  *Verification:* `pytest code/tests/contract/test_paper_traceability.py` passes when all numbers are traceable.