# Tasks: Evaluating the Robustness of LLM‑Generated Code to Input Perturbations  

**Inputs**: `spec.md`, `plan.md`, existing research artefacts, and the reviewer feedback above.  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `data‑model.md`, `contracts/` directory.  

---  

## Phase 1 – Setup & First End‑to‑End Analysis  

| Goal | Run a minimal, reproducible end‑to‑end pipeline on a tiny real sample before any heavy computation. |
|------|-----------------------------------------------------------------------------------------------|

- [X] **T001** [P] Create `requirements.txt` with pinned versions required for the project.  
  **Path**: `requirements.txt`  
  **Verification**: `pip install -r requirements.txt` exits with code 0 and `pip list` shows the exact versions.

- [X] **T002** [P] Create the data directory hierarchy (`data/raw/`, `data/processed/`, `data/logs/`).  
  **Path**: `data/` subtree  
  **Verification**: `ls -R data/` shows the three sub‑folders and they are writable.

- [ ] **T003** [P] Create `quickstart.md` that documents a single‑command entry point for a sample run.  
  **Path**: `quickstart.md`  
  **Verification**: Running the command shown (`python -m code.main --run‑sample`) finishes within 30 s and prints “Sample run completed”.

- [ ] **T004** [P] Add `code/utils/logging.py` with `setup_logger()` that writes JSON‑lines to `data/logs/app.log`.  
  **Path**: `code/utils/logging.py`  
  **Verification**: Import the module and call `setup_logger()`, then check that `data/logs/app.log` exists and contains at least one JSON line.

- [ ] **T005** [P] Implement `code/model/sandbox.py` – `run_in_sandbox(code: str) → Result` and `execute_with_timeout(code: str, timeout: int) → Result`.  
  **Path**: `code/model/sandbox.py`  
  **Verification**: `python -c "from code.model.sandbox import run_in_sandbox; print(run_in_sandbox('print(1)'))"` returns a `Result` with `status='pass'`.

---  

## Phase 2 – Core Infrastructure (must be complete before any user story)  

| Goal | Provide reusable utilities and contract definitions required by all downstream work. |
|------|--------------------------------------------------------------------------------------|

- [ ] **T006** [P] Create `code/config.py` exposing `MODEL_NAME`, `QUANTIZATION`, `DEVICE`, `GEN_TIMEOUT`, `SEED`.  
  **Path**: `code/config.py`  
  **Verification**: `python -c "import code.config; assert code.config.MODEL_NAME"` succeeds.

- [ ] **T007** [P] Add `code/utils/validate_schema.py` that validates a JSON file against a JSON‑Schema file and exits 1 on failure.  
  **Path**: `code/utils/validate_schema.py`  
  **Verification**: Run the script on a known‑good file; exit code 0. Run on a deliberately broken file; exit code 1.

- [ ] **T008** [P] Create `contracts/perturbation_schema.json` defining the JSON schema for perturbation candidates.  
  **Path**: `contracts/perturbation_schema.json`  
  **Schema fields** (required): `task_id` (string), `perturbation_type` (enum ["synonym","typo","rephrase"]), `raw_score` (number 0‑1), `is_valid` (boolean), `candidate_text` (string).  
  **Verification**: `python code/utils/validate_schema.py --input data/processed/perturbation_candidates_raw.json --schema contracts/perturbation_schema.json` exits with code 0.

- [ ] **T008a** [P] Generate `contracts/perturbation_schema.json` from the canonical YAML (`contracts/perturbation_schema.yaml`) to guarantee schema consistency.  
  **Path**: `contracts/perturbation_schema.json` (generated)  
  **Verification**: The produced JSON validates against the original YAML and the same validator script succeeds.

- [ ] **T009** [P] Create `contracts/calibration_schema.json` matching `specs/.../contracts/calibration_schema.yaml`.  
  **Path**: `contracts/calibration_schema.json`  
  **Verification**: Same validator script succeeds against `data/processed/calibration_report.json`.

---  

## Phase 3 – User Story 1: Data Acquisition & Semantic‑Preserving Perturbation Generation (Priority P1)  

| Goal | Download HumanEval, generate up‑to‑three rule‑based perturbations per task, and retain raw similarity scores. |
|------|--------------------------------------------------------------------------------------------------------------|

- [ ] **T010** [US1] Download the HumanEval dataset from HuggingFace and store it as Parquet.  
  **Path**: `code/data/download_humaneval.py` → `data/raw/humaneval.parquet`  
  **Verification**: Running the script creates a non‑empty Parquet file; `datasets.load_dataset('openai_humaneval')` succeeds.

- [ ] **T011** [US1] Implement `substitute_synonyms(prompt: str) → str` in `code/data/perturbations.py`.  
  **Verification**: The function returns a string different from the input for at least one non‑keyword token.

- [ ] **T012** [US1] Implement `inject_typos(prompt: str) → str` in `code/data/perturbations.py`.  
  **Verification**: The function returns a string containing at least one character‑level typo.

- [ ] **T013** [US1] Implement `rephrase_syntax(prompt: str) → str` in `code/data/perturbations.py`.  
  **Verification**: The function returns a syntactically different but semantically equivalent sentence (checked manually on a test case).

- [ ] **T014** [US1] Generate **up to three** candidates per HumanEval task (one per transformation) and write the *full* unfiltered list to `data/processed/perturbation_candidates_raw.json`.  
  **Path**: `code/data/generate_perturbations.py` → `data/processed/perturbation_candidates_raw.json`  
  **Logic**:  
  1. Load raw tasks.  
  2. For each task, apply the three transformations in deterministic order (synonym → typo → rephrase).  
  3. For every generated candidate compute a cosine similarity score using `sentence‑transformers/all‑MiniLM‑L6‑v2`.  
  4. Record `task_id`, `perturbation_type`, `candidate_text`, `raw_score`, `is_valid` (always `false` at this stage), and `selected_rank`.  
  5. Enforce the global cap of **656** total candidates (164 tasks × 3).  
  **Verification**: `python - <<EOF\nimport json, collections\nc=json.load(open('data/processed/perturbation_candidates_raw.json'))\ncounts=collections.Counter(x['task_id'] for x in c)\nassert all(v<=3 for v in counts.values()) and len(c)<=656\nprint('OK')\nEOF` prints “OK”.

- [ ] **T014a** [US1] Ensure that `data/processed/perturbation_candidates_raw.json` is written atomically and checksum‑recorded in `state/projects/...yaml`.  
  **Path**: `code/data/generate_perturbations.py` (output step)  
  **Verification**: After run, the file exists, is non‑empty, and its SHA‑256 hash is stored in the project state file.

- [ ] **T015** [US1] Validate semantic similarity (threshold > 0.95) and create the *validated* set `data/processed/perturbation_candidates_validated.json`.  
  **Path**: `code/data/semantic_validator.py` → `data/processed/perturbation_candidates_validated.json`  
  **Logic**: Load the raw JSON, recompute similarity with the same MiniLM model, set `is_valid = (raw_score > 0.95)`, keep the raw score for sensitivity analysis.  
  **Edge‑case handling**: If *no* candidate passes the threshold for the entire corpus, write a warning entry to `data/logs/halt_report.json` (`{"reason":"ZERO_YIELD"}`) and continue with whatever is present.  
  **Verification**: `python -c "import json; d=json.load(open('data/processed/perturbation_candidates_validated.json')); assert all(d_i['is_valid'] for d_i in d if d_i['raw_score']>0.95)"` succeeds; `data/logs/halt_report.json` exists only when appropriate.

- [ ] **T015a** [US1] Record SHA‑256 checksum of `data/processed/perturbation_candidates_validated.json` in the project state file for reproducibility.  
  **Verification**: State file contains matching hash entry.

- [ ] **T016** [US1] Filter the validated candidates to the *primary* analysis set (`is_valid == true`) and write `data/processed/perturbation_candidates.json`.  
  **Path**: `code/data/filter_perturbations.py` → `data/processed/perturbation_candidates.json`  
  **Logic**: Load the validated file, retain only rows where `is_valid` is true. If the resulting count is below the budget cap, emit a warning to `data/logs/halt_report.json` (`{"reason":"INSUFFICIENT_PERTURBATIONS"}`) but still produce the file.  
  **Verification**: `python -c "import json, pathlib; f=pathlib.Path('data/processed/perturbation_candidates.json'); assert f.exists(); d=json.load(open(f)); assert all(item['is_valid'] for item in d)"`.

- [ ] **T016a** [US1] Write checksum of `data/processed/perturbation_candidates.json` to the project state and ensure `data/logs/halt_report.json` is created (even if empty) for downstream tasks to consume.  
  **Verification**: State file updated; halt_report.json present.

---  

## Phase 4 – User Story 2: CPU‑Compatible Model Inference & Sandboxed Execution (Priority P2)  

| Goal | Run a 4‑bit quantised StarCoder2‑3B on CPU, fall back to 1.5 B on OOM, enforce timeouts, and log detailed results. |
|------|----------------------------------------------------------------------------------------------------------------|

- [ ] **T018** [US2] Add OOM and timeout handling utilities:  
  * `handle_oom(task_id)` logs to `model_selection.log` and skips the sample.  
  * `tag_error(exception)` maps exceptions to the required `error_type` enum.  
  **Verification**: Unit tests in `tests/unit/test_inference_error_handling.py` confirm that a simulated `MemoryError` results in a log entry and that the corresponding output entry has `"execution_status":"oom"`.

- [ ] **T017** [US2] Implement `code/model/inference.py` that:  
  1. Loads `bigcode/starcoder2-3b` with `bitsandbytes` 4‑bit quantisation (`device='cpu'`).  
  2. Catches any `MemoryError`/`RuntimeError`; on failure loads `bigcode/starcoder2-1.5b` as fallback and records the event in `data/logs/model_selection.log`.  
  3. For each primary prompt variant (original + validated perturbations) generates code with a hard **30 s** generation timeout.  
  4. Sends the generated code to `code/model/sandbox.run_in_sandbox` for execution, also bounded by a per‑test‑case timeout (30 s).  
  5. Captures **token‑level log probabilities** (`max_token_logprob`, `mean_token_logprob`) from the model’s `generate` output.  
  6. Writes a line‑per‑sample JSON object to `data/processed/inference_logs.json` conforming to `contracts/execution_result.schema.yaml`.  
  **Verification**: After running on a tiny sample (e.g., first 5 tasks) `data/processed/inference_logs.json` exists, each entry contains `task_id`, `variant_id`, `generated_code`, `execution_status`, `error_type`, `generation_time_ms`, `execution_time_ms`, `max_token_logprob`, `mean_token_logprob`.

- [ ] **T017a** [US2] Ensure `data/processed/inference_logs.json` is written atomically and its checksum recorded in the project state for reproducibility.  
  **Verification**: Checksum entry present; file integrity validated on re‑run.

---  

## Phase 5 – User Story 3: Statistical Analysis, Multiplicity Correction & Error Classification (Priority P3)  

| Goal | Produce scientifically sound statistics, sensitivity analysis, and a final research report. |
|------|---------------------------------------------------------------------------------------------|

- [ ] **T019** [US3] Implement `code/analysis/statistics.py` with the following functions:  
  * `calculate_pass_at1(results: List[Dict]) -> float` – computes pass@1 per perturbation type.  
  * `run_cochran_mantel_haenszel(results: List[Dict]) -> Dict` – stratified CMH test (primary hypothesis test).  
  * `apply_bonferroni_correction(p_vals: List[float], alpha: float = 0.05) -> List[float]`.  
  * `run_mixed_effects_logistic_regression(df: pd.DataFrame) -> Dict` – uses `statsmodels` with `(1|TaskID)` random effect.  
  * `run_sensitivity_analysis(raw_candidates_path: str, thresholds: List[float]) -> pd.DataFrame` – rescoring at {0.85,0.90,0.95,0.99} and reporting pass@1 per threshold.  
  * `classify_errors(failures: List[Dict]) -> List[Dict]` – tags up to 50 failures (or all if ≤ 50) into `syntax`, `logic`, `hallucination`.  
  **Path**: `code/analysis/statistics.py`  
  **Verification**: Running the module on the full `inference_logs.json` creates `data/processed/calibration_report.json` that validates against `contracts/calibration_schema.json`.

- [ ] **T025** [US3] Add `run_aggregated_mcnemar_test(results: List[Dict]) -> Dict` to `statistics.py` that aggregates contingency tables **across all tasks** per perturbation type, computes the classic McNemar χ² test, and returns raw and Bonferroni‑corrected p‑values.  
  **Verification**: Unit test confirms that known contingency data yields the expected p‑value and that the corrected p‑value is stored.

- [ ] **T020** [US3] Create `data/processed/calibration_report.json` by invoking the statistics module on the complete inference logs.  
  **Verification**: `jq '.' data/processed/calibration_report.json` prints a well‑formed JSON object containing keys `baseline_pass_rate`, `perturbation_results`, `statistical_tests`, and `sensitivity_analysis`.

- [ ] **T026** [US3] Extend the calibration report generation to compute the **absolute pass@1 drop** for each perturbation type (baseline – perturbed rate) and store it under `statistical_tests.mcnemar.absolute_drop`. Also store a boolean `significant` that is true only when the Bonferroni‑corrected p‑value ≤ 0.05 **and** the absolute drop ≥ 5 %.  
  **Verification**: The JSON contains the new fields and a downstream script can assert the condition.

- [ ] **T021** [US3] Generate a human‑readable research report `docs/research_report.md` that:  
  1. Summarises baseline and perturbed pass@1 rates.  
  2. Presents **both** CMH and **aggregated McNemar** p‑values (Bonferroni‑adjusted) and marks significance per SC‑001.  
  3. Shows mixed‑effects fixed‑effect coefficient for `perturbation_type` and the random‑effect variance for `TaskID`.  
  4. Includes the sensitivity‑analysis table (threshold vs. pass@1, Δ from baseline).  
  5. Lists error‑classification statistics (counts per error type).  
  6. Explicitly reports the absolute pass@1 drop and states whether the robustness failure criterion is met.  
  **Verification**: Grep for the required section headings (`Pass@1`, `CMH`, `McNemar`, `Mixed‑Effects`, `Sensitivity`, `Error Classification`, `Absolute Drop`) – each must appear at least once; the document length exceeds 500 words; the “Absolute Drop” value matches the number stored in the calibration JSON.

---  

## Phase 6 – Validation, Runtime Checks & Handoff  

| Goal | Ensure the whole pipeline runs end‑to‑end within the resource budget and hand off reproducible artefacts. |
|------|------------------------------------------------------------------------------------------------------------|

- [ ] **T022** [P] Run the *full* pipeline on the complete HumanEval set (164 tasks) using the orchestrator `code/main.py`.  
  **Verification**: After execution:  
  * `data/processed/calibration_report.json` exists and validates.  
  * Total wall‑clock time recorded in `data/logs/runtime.log` is ≤ 6 h.  
  * Peak RAM usage (captured via `psutil` in the orchestrator) is ≤ 7 GB.

- [ ] **T023** [P] Execute the reproducibility check: delete the `data/processed/` folder, then re‑run `code/main.py --from‑scratch`.  
  **Verification**: The run completes without error and produces identical `calibration_report.json` (checksum match) compared to the previous run.

- [ ] **T024** [P] Finalize the paper‑stage handoff by adding a `docs/README.md` that points to `docs/research_report.md`, the calibration JSON, and the exact command to reproduce the study.  
  **Verification**: The README contains a code block with `python -m code.main` and all links are valid.

- [ ] **T027** [P] Archive all generated artifacts (raw/validated perturbations, inference logs, calibration report, runtime logs) into a version‑controlled `artifacts/` directory and record their SHA‑256 hashes in the project state for future audit.  
  **Verification**: `artifacts/` contains the expected files; `state/projects/...yaml` lists matching hashes.

---  

## Dependencies & Execution Order  

| Phase | Dependencies |
|-------|--------------|
| 1 | None (foundational) |
| 2 | Phase 1 |
| 3 | Phase 2 (contracts) |
| 4 | Phase 3 (primary perturbation files) |
| 5 | Phase 4 (inference logs) |
| 6 | Phase 5 (calibration report) |

All tasks marked **[P]** can run in parallel provided their file paths do not overlap. All other tasks respect the data‑flow ordering described above.  

---  

*All tasks above are expressed as markdown checklist items, each with a unique ID, clear artefact paths, and an explicit verification step, satisfying the specification’s scientific and reproducibility requirements.*  