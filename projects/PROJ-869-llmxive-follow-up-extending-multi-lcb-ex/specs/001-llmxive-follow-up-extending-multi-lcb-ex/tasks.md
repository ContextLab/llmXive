# Tasks: llmXive follow‑up – extending “Multi‑LCB: Extending LiveCodeBench to Multiple Programming Languages”

**Inputs**: `specs/001-llmxive-multilingual-logic-transfer/spec.md`, `plan.md`, data‑model, contracts, and any existing verified artifacts.  
**Goal**: Implement a reproducible end‑to‑end pipeline that (1) selects a stratified set of 200 tasks, (2) extracts a Partial Logic Trace from the Python ground‑truth, (3) runs blind and guided code generation, (4) executes the generated snippets in a sandbox with strict timeouts, (5) classifies failures, and (6) produces a statistically‑rigorous report.

---  

## Phase 0 – Project scaffolding & feasibility

- [X] **T001** [US0] Create the project root `projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex/` with the canonical layout  
  `code/src/`, `code/tests/`, `data/raw/`, `data/processed/`, `results/`, `requirements.txt`, `README.md`.  
  **Verification**: `tree` output contains all directories; `git status` shows them as untracked.

- [ ] **T002** [US0] Populate `requirements.txt` with exact, pinned versions of all scientific dependencies (`datasets`, `transformers`, `torch`, `scikit-learn`, `pandas`, `pytest`, `pyyaml`).  
  **Verification**: `pip install -r requirements.txt` succeeds in a fresh venv; `pip freeze` matches the pinned list.

- [X] **T003** [US0] Add linting/formatting configuration files `.ruff.toml` and `pyproject.toml` (Black settings).  
  **Verification**: `ruff .` returns no errors; `black --check .` returns “All done!”.

- [ ] **T004** [US0] Implement `code/src/feasibility_gate.py`   <!-- FAILED-IN-EXECUTION: code/src/feasibility_gate.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/feasibility_gate.py exit=1 -->
  * Loads a small GGUF model with `llama_cpp` (CPU‑only).  
  * Runs a 10‑token sample prompt 5 times, measures average tokens‑per‑second.  
  * Writes `data/feasibility_log.json` containing `{ "throughput_tps": <float>, "decision": "proceed" | "gpu_offload", "adjusted_N": <int|null> }`.  
  * If OOM or throughput < 2 tps, sets `"decision": "gpu_offload"` and suggests a GPU run; otherwise `"proceed"`.  
  **Verification**: File exists, JSON schema matches, and the script exits with status 0.

---  

## Phase 1 – Data preparation & filtering  

- [ ] **T005** [US1] Implement `code/src/data_loader.py`  
  * Streams the Multi‑LCB dataset from HuggingFace (`datasets.load_dataset("multilcb", split="train", streaming=True)`).  
  * Writes raw parquet shards to `data/raw/` and creates `data/raw/manifest.json` with SHA‑256 checksums for each shard.  
  **Verification**: Manifest file lists all downloaded files; checksum verification script passes for every shard.

- [ ] **T006** [US1] Implement `code/src/pool_selector.py`  
  * Reads the raw tasks, filters to tasks where the model previously **failed** in the target language (blind Pass@1 = 0) *and* the Python solution passes its own tests.  
  * Outputs `data/processed/initial_pool.json` (list of task IDs and minimal metadata).  
  **Verification**: File exists; a spot‑check of 5 random entries confirms both conditions hold.

- [ ] **T007** [US1] Implement `code/src/stochastic_filter.py`  
  * Executes the **blind** generation three times on every task in `initial_pool.json` using a fixed seed (`42`) and temperature (`0.0`).  
  * Aggregates failure counts; retains tasks with `blind_fail_count ≥ 2`.  
  * Writes `data/processed/blind_filter_runs.json` (raw logs of the three runs) and `data/processed/filtered_tasks.json` (IDs of selected tasks).  
  **Verification**: `filtered_tasks.json` length ≥ 0; each entry’s `blind_fail_count` field in the logs is ≥ 2.

- [ ] **T008** [US1] Implement `code/src/attrition_handler.py`  
  * If `filtered_tasks.json` contains < 200 tasks, samples replacement tasks from the next‑available pool while preserving the stratification constraints (≤ 30 % per topic, balanced difficulty).  
  * Writes the final, stratified set to `data/processed/final_tasks_enriched.json` (full task objects).  
  **Verification**: File contains exactly 200 tasks; topic‑percentage and difficulty‑balance checks pass (simple script prints “Stratification OK”).

- [ ] **T009** [US1] Implement `code/src/anchor_extractor.py`  
  * Parses each task’s `python_solution` with the `ast` module, extracts the first three distinct algorithmic operations (e.g., variable init, loop entry, recursive call).  
  * Serialises each step as **pseudo‑code** (pure Python‑style, no target‑language keywords).  
  * Writes `data/processed/anchors.json` adhering to `anchor.schema.yaml`.  
  * Logs tasks where extraction fails as `"status": "Failed"` and records them in `data/processed/anchor_extraction_errors.log`.  
  **Verification**: JSON validates against the schema; at least 190 anchors have `"status": "Success"`.

---  

## Phase 2 – Inference, execution, and classification  

- [ ] **T010** [US2] Implement `code/src/blind_inference.py`  
  * Loads the CPU‑quantised model (as verified by `feasibility_gate.py`).  
  * Generates code for each task in `final_tasks_enriched.json` **without** any anchor.  
  * Writes per‑task generation objects to `data/results/blind_results.json` (conforms to `generation-result.schema.yaml`).  
  * Also emits a summary `data/results/blind_summary.yaml` containing `{ "total_tasks": 200, "pass_count": <int>, "pass_rate": <float> }`.  
  * **Reproducibility**: Records the fixed random seed (`42`) and temperature (`0.0`) in `results/inference_metadata.yaml`.  
  **Verification**: JSON schema validation passes; summary pass_rate equals `pass_count / total_tasks`; metadata file exists with the correct seed.

- [ ] **T011** [US3] Implement `code/src/power_check.py`  
  * Reads `data/results/blind_summary.yaml`.  
  * Declares the study **powered** if `pass_rate ≥ 0.05` **and** `total_tasks ≥ 50`; otherwise **underpowered**.  
  * Writes `data/results/power_check.yaml` with `{ "status": "powered" | "underpowered", "reason": "<text>" }`.  
  * Writes `data/results/pipeline_state.json` with `{ "mode": "proceed" | "fallback" }` (fallback if under‑powered).  
  **Verification**: Files exist; a sanity‑check script prints the mode.

- [ ] **T012** [US2] Implement `code/src/guided_inference.py`  
  * Builds prompts that include the problem statement, the model’s previous failed output (if any), and the Partial Logic Trace from `anchors.json`.  
  * Generates target‑language code for each task using the same model configuration as the blind run.  
  * Writes `data/results/guided_results.json` (schema‑compliant).  
  * **Gate**: Must abort unless `pipeline_state.json` reports `"mode": "proceed"`; otherwise logs “Guided run skipped – study underpowered”.  
  **Verification**: When powered, file contains 200 entries; when fallback, file is absent and log entry exists. Seed metadata is also recorded in `results/inference_metadata.yaml` (same seed as blind).

- [ ] **T013** [US2] Implement `code/src/sandbox_runner.py`  
  * For every generation (blind + guided) executes the code in the official Multi‑LCB sandbox (language‑specific compile + run).  
  * Enforces a hard **10 s** timeout per test case; captures stdout, stderr, exit code.  
  * Writes `data/results/execution_logs.json` mapping `task_id` → `condition` → `{ "status": "...", "log": "...", "runtime_ms": <int> }`.  
  **Verification**: All entries contain a `"status"` field that is one of the allowed values; at least one entry shows a timeout case.

- [ ] **T014** [US3] Implement `code/src/error_classifier.py`  
  * Consumes `execution_logs.json` and `anchors.json`.  
  * Applies the deterministic rules from **FR‑004** to assign `error_type` (`Syntax`, `Library`, `Runtime`, `Logic Transfer Failure`, **Logic Drift**).  
  * For passes, verifies that all anchor steps appear in the generated code (simple keyword/control‑flow matching) and sets `anchor_verification: true/false`.  
  * Writes `data/results/classified_results.json` conforming to `generation-result.schema.yaml`.  
  **Verification**: JSON schema validation; a spot‑check shows at least one entry of each error category, including “Logic Drift”.

- [ ] **T015** [US3] Implement `code/src/stats_analyzer.py`  
  * Reads `classified_results.json` for both conditions, builds paired Pass/Fail vectors.  
  * Performs **McNemar’s test** (SciPy) and a bootstrap resampling (10 000 samples) to obtain a 95 % CI for the improvement.  
  * Computes the error‑type distribution for the guided condition.  
  * Writes `results/statistical_report.json` adhering to `statistical-report.schema.yaml`.  
  **Verification**: JSON validates; `p_value` field is present and between 0 and 1.

- [ ] **T016** [US3] Generate human‑readable summary `results/summary.md`  
  * Includes total tasks, blind & guided Pass@1 rates, improvement, p‑value, significance flag, and the error distribution table.  
  * If `pipeline_state.json` is `"fallback"`, adds a “Limitations” section explaining the under‑powered study and omits the p‑value.  
  **Verification**: Markdown renders without broken links; contains the required fields.

- [ ] **T039** [US2] **Re‑run blind inference on the final filtered set**  
  * Executes the blind generation (same seed/temperature as T010) on `final_tasks_enriched.json` to obtain an empirical baseline for the paired test.  
  * Writes `data/results/blind_rebaseline.json` (schema‑compliant) and updates `data/results/blind_summary.yaml` accordingly.  
  **Verification**: Output file exists, passes `generation-result.schema.yaml`, and summary reflects the new counts.

- [ ] **T040** [US0] **Measure total pipeline wall‑clock time**  
  * Wraps the entire end‑to‑end run (from T005 through T016) with a timer.  
  * Writes `results/runtime_log.txt` containing the total elapsed seconds.  
  * Fails the pipeline if the total exceeds 21 600 seconds (6 hours).  
  **Verification**: Log file exists; a check asserts the recorded seconds ≤ 21600.

- [ ] **T041** [US0] **Compute Sandbox Stability Rate**  
  * Parses `execution_logs.json` to count tasks where the sandbox completed without a crash or hang.  
  * Calculates `stability_rate = successful_tasks / total_tasks`.  
  * Writes `results/stability_report.md` with the rate and asserts it is ≥ 0.99.  
  **Verification**: Report file exists; a check confirms the rate meets the threshold.

---  

## Phase 3 – Unit & integration tests (verification‑first)  

- [ ] **T017** [US1] Add `code/tests/test_anchor_extractor.py`  
  * Tests that `anchor_extractor` returns exactly three pseudo‑code steps for a known simple Python solution.  
  * Checks that the output schema fields (`task_id`, `anchor_steps`, `extraction_method`, `status`) are present.  
  **Verification**: `pytest -q code/tests/test_anchor_extractor.py` fails before implementation and passes after.

- [ ] **T018** [US2] Add `code/tests/test_sandbox_runner.py`  
  * Supplies a tiny Rust program that loops forever; asserts the sandbox marks it as `Timeout`.  
  * Supplies a syntactically invalid Kotlin file; asserts `Syntax` error detection.  
  **Verification**: Same pytest workflow; tests must fail initially and succeed after `sandbox_runner.py` is complete.

- [ ] **T019** [US3] Add `code/tests/test_error_classifier.py`  
  * Provides a mock execution log with a passing run that omits one anchor step; expects `error_type` = `Logic Drift`.  
  * Provides a compile‑error log; expects `error_type` = `Syntax`.  
  **Verification**: Tests follow the fail‑then‑pass pattern.

---  

## Phase 4 – Polish & CI integration  

- [ ] **T020** [US0] Update `README.md` with a “Quick‑Start” section that lists the exact command sequence to run the full pipeline from data download to final report (e.g., `python -m code.src.feasibility_gate && python -m code.src.data_loader && …`).  
  **Verification**: The commands execute without error on a fresh clone.

- [ ] **T021** [US0] Add a GitHub Actions workflow (`.github/workflows/ci.yml`) that  
  * Installs dependencies, runs the feasibility gate, executes the full pipeline, and fails if `results/summary.md` does not contain the string “p‑value”.  
  * Enforces the **6‑hour** runtime budget by aborting if any step exceeds its expected wall‑clock (using `timeout` utility).  
  **Verification**: Workflow passes on a successful run; fails on intentional timeout injection.

---  

### Dependency & execution order  

| Task | Depends on |
|------|------------|
| T001‑T004 | – |
| T005 | T001‑T004 |
| T006 | T005 |
| T007 | T006 |
| T008 | T007 |
| T009 | T008 |
| T010 | T009, T004 |
| T011 | T010 |
| T012 | T011, T009 |
| T013 | T010, T012 |
| T014 | T013, T009 |
| T015 | T014 |
| T016 | T015, T011 |
| T039 | T008, T004 |
| T040 | T016, T039 |
| T041 | T013 |
| T017‑T019 | T009‑T014 (provide mock data) |
| T020‑T021 | All above (documentation & CI) |

---  

*All tasks are expressed as check‑box items with unique IDs, include the required story label (`[US1]`, `[US2]`, `[US3]`, or `[US0]` for infrastructure), and specify exact artifact paths. The pipeline can be run incrementally, and each task’s verification step guarantees that a real, verifiable artifact is produced before downstream work proceeds.*  