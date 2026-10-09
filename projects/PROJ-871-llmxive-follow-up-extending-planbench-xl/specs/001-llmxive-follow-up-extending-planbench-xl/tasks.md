# Tasks: llmXive follow‑up – extending “PlanBench‑XL: Evaluating Long‑Horizon Planning of LLM Tool‑Use Agents”

**Inputs**: `spec.md`, `plan.md`, existing research idea, reviewer feedback.  
**Goal**: Produce a reproducible end‑to‑end experiment that (1) builds the required data artifacts, (2) runs a baseline and an augmented LLM tool‑use agent on the implicit‑failure subset, and (3) reports a statistically‑rigorous comparison while respecting the 6‑hour / 7 GB resource limits.

---  

## Phase 0 – Project scaffolding (foundational, must be completed before any user‑story work)

- [ ] **T001** Create the project root `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/` with sub‑directories `code/`, `data/`, `tests/` (and the nested folders listed in `plan.md`).  
  *Artifact*: empty directories at the paths above.  
  **Verification**: run a script that asserts `code/`, `data/`, and `tests/` exist.

- [ ] **T002** Write `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/requirements.txt` containing the exact pinned versions required for reproducibility:  

  ```text
  datasets==2.14.0
  transformers==4.35.0
  torch==2.1.0
  scikit-learn==1.3.0
  pandas==2.1.0
  pytest==7.4.0
  requests==2.31.0
  scipy==1.11.0
  bitsandbytes==0.41.0
  psutil==5.9.6
  ```

  **Verification**: after `pip install -r requirements.txt`, generate a SHA‑256 checksum file `requirements_checksum.txt` and ensure `pip list` succeeds (log captured in `setup_log.txt`).

- [ ] **T003** Add a `.gitignore` at `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/.gitignore` that excludes large artefacts and virtual‑environment files:  

  ```text
  data/
  *.pyc
  __pycache__/
  venv/
  *.log
  *.jsonl
  ```

  **Verification**: test that the file exists and contains the three patterns above.

- [ ] **T004** Create a Python virtual environment in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/venv/`, install the `requirements.txt` into it, and capture verification output (`python --version` and `pip list`) in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/venv/setup_log.txt`.  
  *Artifact*: the `venv/` directory and the `setup_log.txt` file.  
  **Verification**: assert that `setup_log.txt` contains the expected Python version line and a non‑empty package list.

---  

## Phase 1 – Data acquisition & native subset extraction (prerequisite for all user stories)

- [ ] **T005** Implement `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/loader.py` that streams the official PlanBench‑XL dataset from HuggingFace (`datasets.load_dataset("PlanBench/planbench-xl", streaming=True)`) and writes the raw parquet files to `data/raw/`. The script must raise loudly on any download failure (no silent fallback).   <!-- FAILED-IN-EXECUTION: code/dataset/loader.py exit=1 -->

- [ ] **T006** Implement `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/extractor.py` that:   <!-- FAILED-IN-EXECUTION: code/dataset/extractor.py exit=1 -->

  1. Streams the raw data produced by T005.  
  2. Filters **the native implicit‑failure subset** identified in the benchmark metadata (tasks whose ground‑truth indicates a silent tool failure).  
  3. Writes the filtered records to `data/derived/implicit_failure_subset.jsonl` (JSONL, one task per line).  

  **Verification**: unit test confirms that the output file contains only tasks with `ground_truth == "implicit_failure"`.

- [ ] **T007** Implement `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/dataset/indexer.py` that parses `data/derived/implicit_failure_subset.jsonl`, extracts the failure‑signature patterns **directly from the ground‑truth definitions** (e.g., expected error strings), and creates a static, CPU‑tractable JSON index `data/derived/failure_signatures.json` with schema:  

  ```json
  {
    "tool_id": "<error_pattern>",
    "recovery_strategy": "replan"
  }
  ```

  The index must be deterministic (same seed, same ordering) and validated against a JSON schema.  

  **Verification**: test validates schema compliance and that each entry corresponds to a ground‑truth signature.

---  

## Phase 2 – Agent implementations (user‑story 1 & 2)

- [ ] **T008** Implement the **baseline agent** in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/agents/baseline.py`.  
  *Requirements*:  
  • Use a locally‑hosted, CPU‑only LLM (e.g., `meta-llama/Meta-Llama-3-8B` quantised with `bitsandbytes` 8‑bit).  
  • No access to `failure_signatures.json`.  
  • Provide a `run(task)` method that returns a dict containing at least `task_id`, `final_status` (`"success"`/`"failure"`), and the full LLM reasoning trace.  

  **Verification**: unit test asserts that the module does **not** import `failure_signatures.json`.

- [ ] **T009** Implement the **augmented agent** in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/agents/augmented.py`.  
  *Requirements*:  
  • Same LLM as baseline.  
  • After each tool invocation, load `data/derived/failure_signatures.json` and perform a lightweight exact‑match string check (using `fnmatch` for simple wild‑cards).  
  • On a match, trigger the `"replan"` recovery strategy: issue a new LLM call to generate an alternative plan; do **not** return the ground‑truth answer directly.  
  • Log a boolean `signature_triggered` for each task.  

  **Verification**: unit test confirms that when a signature matches, `signature_triggered` is `True` and a second LLM call is made.

- [ ] **T010** Provide two thin runner scripts:  

  • `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/run_baseline.py` – iterates over `data/derived/implicit_failure_subset.jsonl`, invokes `baseline.run`, and writes a line‑delimited JSON log to `data/logs/baseline_execution.jsonl`.  

  • `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/run_augmented.py` – analogous, writing to `data/logs/augmented_execution.jsonl`.  

  Both runners must process tasks sequentially (or in batches ≤ 10) to stay within the 7 GB RAM budget.  

  **Verification**: integration test parses both logs and asserts they are valid JSON and contain the required fields (`task_id`, `final_status`, `signature_triggered` for augmented).

---  

## Phase 3 – Statistical analysis & reporting (user‑story 3)

- [ ] **T011** Implement `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/analysis/log_parser.py` that reads the two execution logs, counts successes for each agent, and returns a tuple `(baseline_success, augmented_success, total_tasks)`.

- [ ] **T012** Implement `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/analysis/stats.py` that:  

  1. Receives the counts from `log_parser`.  
  2. **Always** performs a two‑proportion Z‑test (`scipy.stats.proportions_ztest`).  
  3. Returns a dict containing `test_type` (set to `"z_test"`), `statistic`, `p_value`, `baseline_rate`, `augmented_rate`, and a boolean `significant` (p < 0.05).  

  **Verification**: unit test runs the function on a toy dataset where the expected Z‑test p‑value is known and checks the output structure.

- [ ] **T013** Implement `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/analysis/report.py` that formats the dict from `stats.py` into a human‑readable JSON report saved as `data/results/final_report.json`. The report must also contain the wall‑clock duration (seconds) and peak RAM usage (GB) measured by the orchestrator.  

  **Verification**: schema validation test ensures the report includes `baseline_rate`, `augmented_rate`, `p_value`, `test_type`, `duration_seconds`, and `peak_ram_gb`.

---  

## Phase 4 – End‑to‑end orchestrator & resource monitoring

- [ ] **T014** Implement `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/utils/memory_monitor.py` that uses `psutil` to record peak RSS memory during a function call and returns the value in GB.  

  **Verification**: unit test calls the monitor on a trivial function and asserts the returned float is ≥ 0.0.

- [ ] **T015** Implement `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/run_experiment.py` that orchestrates the full pipeline:  

  1. Calls the data loader (`loader.py`).  
  2. Calls extractor (`extractor.py`) and indexer (`indexer.py`).  
  3. Executes both agents via `run_baseline.py` and `run_augmented.py`.  
  4. Parses logs, runs statistical analysis, and generates the final report.  
  5. Wraps the whole process with a timer (seconds) and the `memory_monitor` to capture peak RAM.  
  6. Writes a short summary to `stdout` and appends the resource metrics to `final_report.json`.  

  The orchestrator must abort with a clear error if any step fails (no silent fall‑backs).  

  **Verification**: CI job asserts that `final_report.json` is produced, contains all required fields, and that the reported `duration_seconds` ≤ 21600 (6 h) and `peak_ram_gb` ≤ 7.0.

---  

## Phase 5 – Verification (tests) & documentation

- [ ] **T016** Add unit tests under `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/tests/unit/` for:  

  • `loader.py` (verifies streaming works on a tiny slice).  
  • `extractor.py` (deterministic extraction, correct `ground_truth` filter).  
  • `indexer.py` (schema compliance).  
  • `baseline.py` (ensures no import of `failure_signatures.json`).  
  • `augmented.py` (signature‑trigger logic).  
  • `stats.py` (Z‑test branch produces expected p‑values on toy data).  

- [ ] **T017** Add integration tests under `tests/integration/` that run the full experiment on a **sampled** subset (e.g., first 5 tasks) to confirm end‑to‑end success and that `final_report.json` contains the required fields.

- [ ] **T018** Write `README.md` and `quickstart.md` at the project root describing:  

  1. How to create and activate the virtual environment.  
  2. The single command to launch the full experiment (`python run_experiment.py`).  
  3. Expected runtime (< 6 h) and memory (< 7 GB).  
  4. Locations of logs, derived data, and the final report.  

  The quickstart must be reproducible on a fresh GitHub‑Actions runner.

- [ ] **T019** Add a CI verification step (e.g., a GitHub Actions job) that asserts the resource constraints: `duration_seconds` ≤ 21600 and `peak_ram_gb` ≤ 7.0 as recorded in `final_report.json`.

- [ ] **T020** Add a CI verification step that validates the JSON schema of `final_report.json` (includes statistical results, duration, RAM).

---  

### Dependency ordering (implicit)

1. **T001–T004** → project scaffold & environment.  
2. **T005–T007** → data acquisition and native subset extraction / index construction.  
3. **T008–T010** → agents and runner scripts (depend on T005–T007).  
4. **T011–T013** → analysis (depend on T010).  
5. **T014–T015** → orchestrator (depends on all prior steps).  
6. **T016–T020** → verification & documentation (run after T015).  

All tasks are now sequentially ordered, have explicit verification steps, and no longer carry unsafe parallel tags. The statistical analysis complies exclusively with the two‑proportion Z‑test as required by the Constitution. The data preparation respects the original implicit‑failure subset, and the failure‑signature index is derived from ground‑truth definitions. Resource‑constraint verification ensures compliance with SC‑004 and SC‑005.  
