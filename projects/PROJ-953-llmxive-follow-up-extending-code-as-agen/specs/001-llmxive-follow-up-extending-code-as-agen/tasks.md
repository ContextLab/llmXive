# Tasks: llmXive follow‑up – extending “Code as Agent Harness”

**Inputs**: `spec.md`, `plan.md`, current contracts, and the project‑local `tasks.md` template.  
All paths are relative to the repository root.

---

## Phase 1 – Project scaffolding & reproducible environment  

- [ ] T001 [P] Create the canonical project layout (folders `code/`, `data/`, `tests/`, `docs/`, `models/`, `state/`) and record a directory‑tree listing in `code/structure_tree.txt`. Also place an empty `.gitkeep` file in each top‑level folder to satisfy the structure test.  
  *Verification*: `tests/integration/test_project_structure.py` confirms that each top‑level folder exists, contains at least one file (`.gitkeep` or `structure_tree.txt`), and that the listing file enumerates the required directories.

- [ ] T002 [P] Add a pinned `requirements.txt` with the exact package versions needed for reproducibility:  

  ```text
  datasets==2.18.0
  tree-sitter==0.20.1
  tree-sitter-python==0.20.2
  scikit-learn==1.5.0
  pandas==2.2.2
  networkx==3.3
  radon==6.0.1
  pytest==8.2.2
  jsonschema==4.22.0
  ```

  *Verification*: `tests/unit/test_requirements.py` parses the file and asserts the presence and exact version of each required package.

- [ ] T003 [P] Create `pyproject.toml` configuring Black (`line-length = 88`) and Ruff (`select = ["E","F","W"]`).  
  *Verification*: `tests/unit/test_pyproject.py` loads the TOML and checks that the required sections and options are present.

- [ ] T004 [P] Write the core documentation files under `docs/`:  

  * `README.md` – project overview and quick‑start command list.  
  * `quickstart.md` – step‑by‑step guide (set `HF_TOKEN`, run `ingest.py`, `baseline_runner.py`, `extract_features.py`, `train_model.py`).  
  * `usage_guide.md` – how to inspect `ground_truth.csv`, visualise a graph JSON with NetworkX, and interpret `threshold_sweep.json` & `model_report.json`.  
  * `api_reference.md` – signatures of the four pipeline scripts (`ingest()`, `run_baseline()`, `extract_features()`, `train_model()`).  

  *Verification*: `tests/unit/test_docs_presence.py` checks that each markdown file exists and contains at least 20 non‑empty lines.

---

## Phase 2 – Contracts, schema validation, and data‑model documentation  

- [ ] T005 [P] Verify that the three JSON‑Schema files (`task_artifact.schema.yaml`, `structural_metric.schema.yaml`, `model_outcome.schema.yaml`) exist in `contracts/`. The task does not create them (they are provided as reference material) but ensures they are present and syntactically valid.  
  *Verification*: `tests/unit/test_schema_files.py` loads each file with `jsonschema.Draft7Validator` and asserts syntactic validity and presence of the required keys.

- [ ] T006 [P] Write unit test `tests/unit/test_schema_validation.py` containing the function `test_structural_metric_fallback_logic`. The test loads `contracts/structural_metric.schema.yaml` and validates a sample instance where `semantic_complexity_score: null` and `lines_of_code: 42`; it must pass.  
  *Verification*: the test itself fails until `T005` supplies the conditional rule, then passes.

- [ ] T007 [P] Produce `specs/001-llmxive-harness-extension/data-model.md` documenting the full data flow, directory structure, schema definitions, and artifact relationships (mirroring the original data‑model description). The markdown must contain the four top‑level headings: **Data Flow Overview**, **Directory Structure & Artifacts**, **Schema Definitions**, **Artifact Relationships**.  
  *Verification*: `tests/integration/test_data_model_doc.py` parses the file, checks for the four headings, and confirms that each referenced schema file exists on disk.

- [~] T008 [P] Implement `code/scripts/config.py` that reads environment variables `HF_TOKEN` (required) and `SAMPLE_SIZE` (optional, default = 500). Missing `HF_TOKEN` raises `RuntimeError` with a clear message. The module exposes `HF_TOKEN` and `SAMPLE_SIZE` constants.  
  *Verification*: `tests/unit/test_config_loader.py` sets/clears the env vars and asserts correct behaviour.

---

## Phase 3 – Dataset ingestion & ground‑truth generation (User Story 1)  

- [ ] T009 [P] Implement `code/scripts/ingest.py` to:   <!-- FAILED-IN-EXECUTION: code/scripts/ingest.py exit=1 -->

  1. Stream `swe-bench-verified` and `agentbench-os` via `datasets.load_dataset(..., streaming=True)`.  
  2. Sample exactly `SAMPLE_SIZE` tasks (default 500) respecting the RAM budget; log the chosen size in `data/logs/ingest_sample_log.json`.  
  3. Extract `task_id`, `code_diff`, `original_code`, and `dataset_name`; write two parquet files `data/raw/swe_bench_subset.parquet` and `data/raw/agentbench_subset.parquet`.  
  4. Add a `status` column set to `"Unparseable"` for any record where `tree‑sitter` fails to parse `code_diff`.  

  *Verification*: `tests/integration/test_ingest_output.py` checks that both parquet files exist, contain a total of `SAMPLE_SIZE` rows, and have no nulls in `code_diff`.

- [ ] T010 [P] Generate a human‑readable justification file `data/logs/sampling_justification.md` explaining why 500 tasks were chosen (pilot size, RAM budget, statistical‑power note) and referencing the `SAMPLE_SIZE` config value.  
  *Verification*: `tests/unit/test_sampling_justification.py` reads the markdown and asserts it contains the phrase “500 tasks”.

- [ ] T011 [P] Implement `code/scripts/baseline_runner.py` to:  

  1. Load the parquet files from **T009**.  
  2. For each task, create an isolated Python virtual environment (using `venv`) and execute `code_diff` against `original_code`.  
  3. Record `"Pass"`, `"Fail"`, or `"Timeout/Fail"` (if execution exceeds 600 s) in `data/processed/raw_outcomes.json`.  
  4. Enforce **no CUDA** usage – any import of `torch.cuda` raises `RuntimeError`.  

  *Verification*: `tests/integration/test_baseline_runner.py` runs the script on a tiny synthetic parquet (2 tasks) and checks that the JSON contains only the three allowed outcome strings and that a forced CUDA import triggers an error.

- [ ] T012 [P] Merge ingestion data with baseline outcomes to produce `data/processed/ground_truth.csv` (columns: `task_id`, `code_diff`, `status`, `dynamic_execution_outcome`). Ensure every row has a non‑null `dynamic_execution_outcome` (or `"Unparseable"` status).  
  *Verification*: `tests/unit/test_ground_truth_merge.py` asserts that the CSV row count equals `SAMPLE_SIZE` and that the `dynamic_execution_outcome` column contains only the allowed values.

---

## Phase 4 – Structural feature extraction & graph construction (User Story 2)  

- [ ] T013 [P] Implement `code/scripts/extract_features.py` to:  

  1. Load `data/processed/ground_truth.csv`.  
  2. Skip rows where `status == "Unparseable"`.  
  3. Parse each `code_diff` with `tree‑sitter` and build a dependency graph (saved as `data/graphs/{task_id}.json`).  
  4. Compute metrics: `dependency_depth`, `cyclomatic_complexity` (via `radon`), `semantic_complexity_score` (if semantic nodes exist), `lines_of_code`, `node_count`, `edge_count`.  
  5. Write a consolidated feature table `data/processed/features.csv` merging these metrics with the ground‑truth labels.  

  *Verification*: `tests/integration/test_feature_extraction.py` runs the script on a synthetic `ground_truth.csv` (3 tasks) and checks that a JSON graph and a CSV row are produced for each parseable task.

- [ ] T014 [P] Create an audit file `data/logs/graph_mapping_audit.json` that stores a SHA‑256 hash of each `code_diff` alongside the SHA‑256 hash of its serialized graph. Provide a test `tests/integration/test_graph_hashes.py` that loads the audit file and confirms that the hashes match the on‑disk files.  

- [ ] T015 [P] Validate that `data/processed/features.csv` contains **no missing values**; rows lacking `semantic_complexity_score` must have a non‑null `lines_of_code`.  
  *Verification*: `tests/unit/test_features_no_missing.py` loads the CSV and asserts the described invariants.

---

## Phase 5 – Predictive modeling, threshold analysis & reporting (User Story 3)  

- [ ] T016 [P] Implement `code/scripts/train_model.py` to:  

  1. Load `data/processed/features.csv`.  
  2. Split into train/validation (80/20) with `random_state=0`.  
  3. Train **Logistic Regression** (`solver='lbfgs'`, `max_iter=1000`) and **Random Forest** (`n_estimators=200`, `n_jobs=1`, `random_state=0`).  
  4. For each model, sweep decision thresholds `{0.01, 0.05, 0.1}` and compute the false‑negative rate (FNR) on the validation set (a false negative = prediction “Static_Safe” while ground‑truth is `Fail` or `Timeout/Fail`).  
  5. Persist the models to `models/logistic_regression.pkl` and `models/random_forest.pkl`.  
  6. Write `data/processed/threshold_sweep.json` with entries `{model_type, threshold, fnr, unsafe}` where `unsafe` is true if `fnr > 0.001` (0.1 %).  
  7. Compute Pearson correlation coefficients between each structural metric and the binary target “dynamic execution required”; store results in `data/processed/model_report.json` with fields `model_type`, `threshold`, `fnr`, `framing:"associational"`, `safety_flag`, `correlation_coefficient`, and, if no threshold meets the safety constraint, `minimum_achievable_fnr`.  

  *Verification*: `tests/integration/test_model_outputs.py` checks that both model files exist, that `threshold_sweep.json` contains three threshold entries per model, and that `model_report.json` includes all required keys with `framing` equal to `"associational"`.

- [ ] T017 [P] Success‑criteria test `tests/integration/test_success_criteria.py` that reads `threshold_sweep.json` and `model_report.json` and asserts:  

  * At least one threshold achieves **FNR ≤ 0.001**.  
  * If none does, `model_report.json` contains `minimum_achievable_fnr` and `safety_flag` is `true`.  
  * `correlation_coefficient` lies in the range [‑1, 1].

- [ ] T022 [P] Compute the reduction in dynamic execution cycles after applying the selected model threshold. The script reads `data/processed/ground_truth.csv` and the chosen threshold from `data/processed/threshold_sweep.json`, determines how many tasks are classified as “Static_Safe”, and writes a summary JSON `data/logs/reduction_metric.json` containing the total task count, number skipped, and percentage skipped.  
  *Verification*: `tests/integration/test_reduction_metric.py` loads the JSON and asserts that `percentage_skipped` is a float between 0 and 100 and that it matches the difference between total tasks and tasks flagged for dynamic execution.

- [ ] T023 [P] Instrument the end‑to‑end pipeline to capture total wall‑clock runtime and peak RAM usage. The script runs the full pipeline (ingest → baseline → feature extraction → model training) while measuring time (using `time.perf_counter`) and memory (using `psutil`). It writes `data/logs/runtime_memory_report.json` with fields `total_seconds`, `peak_memory_gb`, and a boolean `within_limits` that is true only if `total_seconds <= 21600` (6 h) and `peak_memory_gb <= 7`. The task fails if limits are exceeded.  
  *Verification*: `tests/integration/test_runtime_memory_limits.py` executes the monitoring script on a small subset and checks that the JSON fields exist and that `within_limits` correctly reflects the measured values.

---

## Phase 6 – Cross‑cutting utilities & final validation  

- [ ] T018 [P] Add edge‑case unit tests:  

  * `tests/unit/test_empty_dataset.py` – scripts raise `ValueError` on an empty `features.csv`.  
  * `tests/unit/test_parsing_failure.py` – feeding a syntactically broken snippet to `extract_features.py` results in the corresponding row being marked `"Unparseable"` in `ground_truth.csv`.  
  * `tests/unit/test_timeout.py` – simulating a long‑running baseline task records `"Timeout/Fail"` in `raw_outcomes.json`.  

- [ ] T019 [P] Implement a causal‑language filter `code/scripts/causal_filter.py` that scans `data/processed/model_report.json` and `docs/research.md` for prohibited causal verbs (`causes`, `drives`, `leads to`, `results in`). If any are found, the script writes a warning to `data/logs/causal_language_audit.json` and exits with a non‑zero status, causing the pipeline to abort.  

- [ ] T020 [P] Implement an associational‑check script `code/scripts/associational_check.py` that ensures the word “associational” (or the phrase “correlates with”) appears in both `data/processed/model_report.json` and `docs/research.md`. Missing phrasing produces a JSON warning `data/logs/associational_check.json` and a non‑zero exit code.  

- [ ] T021 [P] Generate SHA‑256 checksums for every file under `data/` and `models/`, write them to `state/artifact_hashes.yaml`, and provide `tests/integration/test_checksums.py` that verifies the manifest matches the on‑disk files.  

---

### Dependency mapping (summary)

| Spec/US | Task(s) fulfilling it |
|---------|-----------------------|
| **FR‑001 / US‑1** | T009, T010, T011, T012 |
| **FR‑002 / US‑2** | T013, T014, T015 |
| **FR‑003** | T011 (baseline re‑execution) |
| **FR‑004 / US‑3** | T016, T017 |
| **FR‑005** | T016, T017, T021, T022, T023 |
| **FR‑006** | T019, T020 |
| **Schema contracts** | T005, T006 |
| **Data‑model doc** | T007 |
| **Config handling** | T008 |
| **Documentation** | T004 |
| **Project layout & tooling** | T001, T002, T003 |
| **Cross‑cutting tests & utilities** | T018‑T021 |

All tasks respect the data‑flow ordering and the platform’s constraints.  
