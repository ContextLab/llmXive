# Tasks: Evaluating the Effectiveness of Prompt Engineering for LLM‑Based Code Translation  

**Inputs**: `spec.md`, `plan.md`, existing repository artifacts, and reviewer feedback (including the list of rejected tasks).  

The list below consolidates all scientific requirements, fixes the previously rejected items, and groups related work into 15 substantive research tasks.  Each task follows the canonical checklist format, cites the exact file(s) it creates or modifies, and includes an indented verification step.

---

## Phase 1 – Project scaffolding & utility foundation  

- [ ] **T001** [ P ] [ US1 ] Create the required directory layout (`src/`, `tests/`, `data/raw/`, `data/processed/`, `data/prompts/`, `data/evaluation/`, `logs/`) and a `.gitignore` that excludes raw data, processed data, evaluation artefacts, and Python caches.  
  *Verification:* Run `python -c "import pathlib, sys; assert all(pathlib.Path(p).exists() for p in ['src','tests','data/raw','data/processed','data/prompts','data/evaluation','logs']);"`; confirm `git status` shows no ignored files.

- [ ] **T002** [ P ] [ US2 ] Implement `src/utils/timeout_utils.py` providing `api_timeout(seconds: int)` and `test_timeout(seconds: int)` decorators that raise `TimeoutError` when the wrapped call exceeds the limit.  
  *Verification:* `pytest tests/unit/test_timeout_utils.py` must pass, confirming both decorators raise on a deliberately slow function.

- [ ] **T003** [ P ] [ US3 ] Add `src/utils/update_state.py` that (a) computes SHA‑256 hashes of all files under `data/` and `src/`, (b) writes a mapping `artifact_hashes:` into `state/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e.yaml`, and (c) updates an `updated_at` timestamp.  
  *Verification:* After any artifact change, re‑run the script and check that the YAML file contains the new hash and a recent ISO‑8601 timestamp.

---

## Phase 2 – Dataset acquisition & preprocessing  

- [ ] **T004** [ P ] [ US1 ] Implement `src/ingestion/download_datasets.py` to stream‑download the HuggingFace datasets `codeparrot/code-trans-py-js` and `bigcode/evaluation` via the `datasets` library, storing raw files under `data/raw/`.  
  *Verification:* Contract test `tests/contract/test_dataset_fetch.py` asserts both dataset directories exist and contain at least one shard file.

- [ ] **T005** [ P ] [ US1 ] Implement `src/ingestion/preprocess_corpus.py` that (a) iterates the streamed raw datasets, (b) filters out entries with missing or syntactically invalid Python or JavaScript, (c) logs excluded IDs to `logs/dataset_preprocess.log`, (d) samples **≥ 200** valid pairs while keeping peak RAM ≤ 7 GB, and (e) writes `data/processed/corpus.csv` conforming to `dataset.schema.yaml`.  
  *Verification:* Integration test `tests/integration/test_preprocess_memory.py` measures peak memory (≤ 7 GB) and asserts the CSV row count ≥ 200.

- [ ] **T006** [ P ] [ US1 ] Run `src/utils/checksum_artifacts.py` to generate SHA‑256 hashes for every file in `data/raw/` and write them to `state/checksums/` (one `.sha256` file per raw artefact).  
  *Verification:* All files under `data/raw/` have a corresponding `.sha256` file; the script exits with status 0.

---

## Phase 3 – Prompt engineering artefacts  

- [ ] **T007** [ P ] [ US2 ] Create the four prompt template files in `data/prompts/` with complete, non‑placeholder text:  
  - `zero_shot_basic.txt` – simple translate‑only instruction.  
  - `zero_shot_style.txt` – instruction plus ES6 style spec.  
  - `few_shot_basic.txt` – zero‑shot instruction plus two concrete Python‑JS examples.  
  - `few_shot_style.txt` – style‑augmented instruction plus the same two examples.  
  *Verification:* Each file exists, contains ≥ 10 words, and `tests/contract/test_prompts_exist.py` confirms the word count.

- [ ] **T008** [ P ] [ US2 ] Implement deterministic inference in `src/execution/run_inference.py`:  
  - Load `data/processed/corpus.csv` and the four prompt files.  
  - For every `(snippet, condition)` pair, build the full prompt, call the HuggingFace Inference API (`model = "codellama/CodeLlama-7b-Instruct-hf"`), **pin** `seed=42`, `temperature=0.0`, and **log** `prompt_text`, `model_version`, `seed`, and ISO‑8601 `timestamp` to `logs/inference.log`.  
  *Verification:* Re‑run the script on a tiny sample (`N=2`) and assert that `logs/inference.log` contains identical entries on two separate executions (checked by `tests/unit/test_determinism.py`).

- [ ] **T009** [ P ] [ US2 ] Store each generated JavaScript file under `data/evaluation/raw_translations/<condition_name>/<snippet_id>.js` (e.g., `data/evaluation/raw_translations/zero_shot_basic/001.js`).  
  *Verification:* After a successful inference run, `tests/contract/test_output_hierarchy.py` confirms that every condition folder contains a `.js` file for each snippet ID.

- [ ] **T010** [ P ] [ US2 ] Extend the inference pipeline to detect non‑code responses (empty string, “I cannot do that”, malformed JSON). When detected, write a line to `logs/failed_translations.log` with `snippet_id`, `condition_name`, and the raw response; still record the attempt in the metadata log.  
  *Verification:* Inject a mock response that triggers the filter and assert that the log file contains the corresponding entry (`tests/unit/test_failed_translation.py`).

- [ ] **T011** [ P ] [ US2 ] Generate a version‑controlled metadata CSV `data/evaluation/metadata_log.csv` containing columns: `snippet_id`, `condition_name`, `prompt_path`, `model_version`, `seed`, `timestamp`, `response_status` (success/timeout/failed). Commit the CSV to Git.  
  *Verification:* Schema validation test `tests/contract/test_metadata_log.py` checks column presence and that row count matches the number of inference attempts.

---

## Phase 4 – Functional correctness & quality measurement  

- [ ] **T012** [ P ] [ US3 ] Implement `src/evaluation/extract_io_pairs.py` that executes each Python snippet on a deterministic set of synthetic inputs (five‑element boundary, typical, and mixed cases), records successful `input_json` / `expected_output_json` pairs, and writes `data/evaluation/io_pairs.csv`. Snippets that fail to produce ≥ 5 pairs are excluded and logged.  
  *Verification:* Run the script on the processed corpus and assert that `io_pairs.csv` contains at least 180 rows (allowing for a small exclusion rate); confirm that `logs/io_extraction.log` records the exclusion count.

- [ ] **T013** [ P ] [ US3 ] Implement `src/evaluation/run_js_tests.py` which, for every generated JavaScript file, runs the corresponding I/O pairs using a Node.js runner with a **10 s** per‑test timeout (via `src/utils/timeout_utils.py`). Produce `data/evaluation/validation_results.csv` with columns matching `translation_result.schema.yaml` (`test_pass_status` = pass/fail/timeout/skipped).  
  *Verification:* Contract test `tests/contract/test_validation_results_schema.py` validates the CSV against the schema; an integration test runs the runner on a known‑good snippet and expects a `pass` row.

- [ ] **T014** [ P ] [ US4 ] Implement `src/evaluation/compute_quality.py` that invokes the ESLint complexity plugin on each `.js` file, extracts `cyclomatic complexity` and `lines of code`, and writes `data/evaluation/quality_metrics.csv`.  
  *Verification:* Unit test `tests/unit/test_compute_quality.py` runs the script on a sample file and asserts numeric `complexity_score` ≥ 1 and `lines_of_code` > 0.

---

## Phase 5 – Statistical analysis & reporting  

- [ ] **T015** [ P ] [ US5 ] Implement `src/evaluation/statistical_analysis.py` to:  
  1. Perform a chi‑square test of correctness rates across the four prompt conditions (baseline = `zero_shot_basic`).  
  2. Conduct Repeated‑Measures ANOVA on `complexity_score` and `lines_of_code`.  
  3. Apply Bonferroni correction for all pairwise comparisons.  
  4. Optionally fit a logistic regression on snippet‑difficulty (as defined in the plan) and stratify if significant.  
  5. Write the aggregated results to `data/evaluation/statistical_summary.csv` conforming to `statistical_summary.schema.yaml`.  
  *Verification:* Unit test `tests/unit/test_statistical_analysis.py` checks that the CSV contains the required columns, that all `p_value` entries are floats, and that the `correction_method` column equals `"bonferroni"` for every row.

- [ ] **T016** [ P ] [ US5 ] Create a concise methods‑results markdown handoff `paper/methods_and_results.md` that (a) references the exact artefacts (`metadata_log.csv`, `validation_results.csv`, `quality_metrics.csv`, `statistical_summary.csv`), (b) lists observed effect sizes, confidence intervals, and any power‑limitation notes, and (c) notes the deterministic seed and model version.  
  *Verification:* Manual review confirms that every figure/table reference points to an existing CSV file and that the document contains no placeholder numbers.

---

## Phase 6 – Reproducibility & state finalisation  

- [ ] **T017** [ P ] [ US6 ] Run the full end‑to‑end pipeline from `src/ingestion/download_datasets.py` through `src/evaluation/statistical_analysis.py` on the CI runner, measuring total wall‑clock time and writing `logs/runtime.log` (seconds). The script must abort if runtime > 21600 s (6 h).  
  *Verification:* CI job succeeds and `logs/runtime.log` reports a value ≤ 21600.

- [ ] **T018** [ P ] [ US6 ] Invoke `src/utils/update_state.py` (from **T003**) after the pipeline completes to record a final project state hash and timestamp.  
  *Verification:* The `state/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e.yaml` file’s `artifact_hashes` reflect the latest SHA‑256 values and `updated_at` matches the current time.

- [ ] **T019** [ P ] [ US6 ] Add contract tests for the newly created evaluation scripts:  
  - `tests/contract/test_io_extraction.py` (schema of `io_pairs.csv`)  
  - `tests/contract/test_translation_result_schema.py` (schema of `validation_results.csv`)  
  - `tests/contract/test_quality_metrics_schema.py` (schema of `quality_metrics.csv`)  
  *Verification:* All contract tests pass in CI, guaranteeing that each CSV conforms to its respective schema.

---

### Dependency mapping (summary)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 | T004, T005, T006 |
| FR‑002 | T007, T008, T009, T010, T011 |
| FR‑003 | T012, T013 |
| FR‑004 | T014 |
| FR‑005 | T015 |
| FR‑006 | T008, T011 |
| Data‑model contracts | T012‑T015 (schemas) |
| Reviewer‑rejected items | T002, T007‑T011, T014‑T016, T018‑T019 |

All tasks are unchecked (pending implementation) and ordered to respect data flow: ingestion → preprocessing → checksum → prompts → deterministic inference → storage → logging → I/O extraction → JS validation → quality measurement → statistical analysis → reproducibility handoff.
