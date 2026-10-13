# Tasks: llmXive follow‑up: extending “Code as Agent Harness”

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, contracts, and the project‑local `tasks.md` template.  
All paths are relative to the repository root.

---

## Phase 1 – Setup & first end‑to‑end analysis  

*Goal*: Establish a runnable skeleton and produce a minimal end‑to‑end result that can be verified on a fresh CPU‑only runner.

- [ ] **T001** [P] Create the canonical project layout (`code/`, `data/`, `tests/`, `docs/`) and record a directory‑tree listing.  
  *Artifacts*  
  `code/` – source scripts (empty placeholders are fine)  
  `data/` – sub‑folders `raw/`, `processed/`, `graphs/`, `logs/` (each contains a `.gitkeep`)  
  `tests/` – sub‑folders `unit/`, `integration/`, `contract/` (each contains a `.gitkeep`)  
  `docs/` – documentation folder (contains a `.gitkeep`)  
  `code/structure_tree.txt` – plain‑text output of `tree -a .` after the folders are created.  
  *Verification*: `tests/integration/test_project_structure.py` checks that the five top‑level directories exist, that each contains at least one file (the `.gitkeep` or `structure_tree.txt`), and that `structure_tree.txt` includes the names of those directories.

- [ ] **T002** [P] Initialize a Python 3.11 project and add a pinned `requirements.txt` containing the exact versions needed for reproducibility:  
  `datasets==2.18.0`  
  `tree-sitter==0.20.1`  
  `tree-sitter-python==0.20.2`  
  `scikit-learn==1.5.0`  
  `pandas==2.2.2`  
  `networkx==3.3`  
  `radon==6.0.1`  
  `pytest==8.2.2`  
  `jsonschema==4.22.0`  
  *Path*: `requirements.txt`  
  *Verification*: `tests/unit/test_requirements.py` parses the file and asserts that each line matches the expected package‑version pattern and that the list contains all required packages.

- [ ] **T003** [P] Configure linting (ruff) and formatting (black) via `pyproject.toml`.  
  *Path*: `pyproject.toml` (must contain `[tool.black]` with `line-length = 88` and `[tool.ruff]` with `select = ["E", "F", "W"]`).  
  *Verification*: `tests/unit/test_pyproject.py` loads the TOML and checks that the required sections and options exist.

- [ ] **T004a** [P] Create `docs/README.md` with a concise project overview, installation instructions (`python -m venv venv && pip install -r requirements.txt`), and a short “Running the pipeline” section that lists the three entry‑point scripts (`ingest.py`, `extract_features.py`, `train_model.py`).  

- [ ] **T004b** [P] Create `docs/quickstart.md` that walks a user through:  
  1. Setting `HF_TOKEN` environment variable.  
  2. Running `python -m code.scripts.ingest`.  
  3. Running `python -m code.scripts.baseline_runner`.  
  4. Running `python -m code.scripts.extract_features`.  
  5. Running `python -m code.scripts.train_model`.  
  The guide must explicitly state that step 2 performs **full‑environment** re‑execution (no “static‑only” shortcut).  

- [ ] **T004c** [P] Create `docs/usage_guide.md` with detailed examples of:  
  * Inspecting `data/processed/ground_truth.csv`.  
  * Visualising a graph JSON (`data/graphs/{task_id}.json`) with `networkx`.  
  * Interpreting `data/processed/threshold_sweep.json` and `model_report.json`.  

- [ ] **T004d** [P] Create `docs/api_reference.md` documenting the public functions in the three pipeline scripts (`ingest()`, `run_baseline()`, `extract_features()`, `train_model()`) including their signatures, required arguments, and return types.

---

## Phase 2 – Foundational (blocking prerequisites)

*Goal*: Provide the schema contracts, data‑model documentation, and supporting infrastructure that all later user‑story tasks depend on.

- [ ] **T005** [P] Create the three JSON‑Schema Draft‑07 files required for validation:  
  1. `contracts/task_artifact.schema.yaml` (already present – verify it matches the spec).  
  2. `contracts/structural_metric.schema.yaml` – must define `semantic_complexity_score` as `null`‑able and include a `oneOf` clause that enforces the presence of `lines_of_code` when `semantic_complexity_score` is `null`.  
  3. `contracts/model_outcome.schema.yaml` (already present – verify it matches the spec).  
  *Verification*: `tests/unit/test_schema_files.py` loads each file with `jsonschema.Draft7Validator` and asserts that they are syntactically valid and contain the required keys.

- [ ] **T005a** [US2] Write a unit test `tests/unit/test_schema_validation.py` containing the function `test_structural_metric_fallback_logic`. The test must:  
  1. Load `contracts/structural_metric.schema.yaml`.  
  2. Validate a sample instance where `semantic_complexity_score: null` and `lines_of_code: 42`.  
  3. Assert that validation **passes** because the fallback rule is satisfied.  
  *Verification*: The test must initially **fail** (because the schema is missing the conditional rule) and pass after `T005` is completed.

- [ ] **T005b** [P] Write `specs/001-llmxive-harness-extension/data-model.md` documenting the full data flow (ingestion → baseline → feature extraction → modeling), listing all artifact relationships, and embedding references to the three contract schemas. The file must contain the sections: *Data Flow Overview*, *Directory Structure & Artifacts*, *Schema Definitions*, and *Artifact Relationships* (mirroring the original data‑model description).  
  *Verification*: `tests/integration/test_data_model_doc.py` parses the markdown, checks for the four required headings, and confirms that each referenced schema file exists on disk.

- [ ] **T006** [P] Implement `code/scripts/update_state.py` that walks `data/` and `models/`, computes a SHA‑256 checksum for every file, and writes a manifest `state/artifact_hashes.yaml` with the mapping `{relative_path: checksum}`.  
  *Verification*: `tests/unit/test_update_state.py` runs the script on a temporary folder containing two dummy files and asserts that the manifest contains exactly those two entries with correct SHA‑256 values.

- [ ] **T007** [P] Create placeholder `.gitkeep` files in `data/raw/`, `data/processed/`, `data/graphs/`, `tests/unit/`, `tests/integration/`, and `tests/contract/` to guarantee the directories exist in the repository.  
  *Verification*: `tests/unit/test_gitkeep_presence.py` checks that each target directory contains a `.gitkeep` file.

- [ ] **T008** [P] Add a lightweight configuration loader `code/scripts/config.py` that reads environment variables `HF_TOKEN` (required) and `SAMPLE_SIZE` (optional, default = 500). If `HF_TOKEN` is missing, the loader raises `RuntimeError` with a clear message.  
  *Verification*: `tests/unit/test_config_loader.py` sets/clears the env vars and asserts the correct behaviour (exception vs. successful load).

---

## Phase 3 – User Story 1: Dataset ingestion & ground‑truth generation (Priority P1)

- [ ] **T009** [P] Contract test `tests/contract/test_ingest.py` that verifies `code/scripts/ingest.py` calls `datasets.load_dataset` with a non‑empty `HF_TOKEN`, streams the data, and writes two parquet files under `data/raw/`.  
  *Verification*: The test mocks the HuggingFace API and asserts that the parquet files are created.

- [ ] **T010** [P] Unit test `tests/unit/test_timeout_handler.py` that confirms any task whose execution time exceeds 600 s is recorded with the literal outcome `"Timeout/Fail"` in the JSON outcome file produced by `baseline_runner.py`.  
  *Verification*: The test injects a mock task with a long‑running function and checks the JSON entry.

- [ ] **T011** [US1] Implement `code/scripts/ingest.py` to:  
  1. Stream the SWE‑bench and AgentBench datasets via `datasets.load_dataset(..., streaming=True)`.  
  2. Sample **exactly 500** tasks (or stop early if RAM > 6 GB) and log the chosen sample size in `data/logs/ingest_sample_log.json`.  
  3. Extract `task_id`, `code_diff`, `original_code`, and `dataset_name`; write two parquet files: `data/raw/swe_bench_subset.parquet` and `data/raw/agentbench_subset.parquet`.  
  4. Add a `status` column set to `"Unparseable"` for any record where `tree‑sitter` fails to parse the `code_diff`.  
  *Verification*: `tests/integration/test_ingest_output.py` checks that both parquet files exist, contain a total of 500 rows, and have no nulls in `code_diff`.

- [ ] **T011a** [US1] Generate a human‑readable justification file `data/logs/sampling_justification.md` that explains why 500 tasks were chosen (pilot size, RAM budget, statistical‑power note) and references the `SAMPLE_SIZE` config value.  
  *Verification*: `tests/unit/test_sampling_justification.py` reads the markdown and asserts that it contains the phrase “500 tasks”.

- [ ] **T013** [US1] Implement `code/scripts/baseline_runner.py` to:  
  1. Load the parquet files from `T011`.  
  2. For each task, create an isolated Python virtual environment (using `venv` – no Docker) and execute the `code_diff` against the `original_code`.  
  3. Record `"Pass"`, `"Fail"`, or `"Timeout/Fail"` in `data/processed/raw_outcomes.json`.  
  4. Enforce **no CUDA** usage – any import of `torch.cuda` raises `RuntimeError`.  
  *Verification*: `tests/integration/test_baseline_runner.py` runs the script on a tiny synthetic parquet (2 tasks) and checks that the JSON contains the three allowed outcome strings and that a CUDA import attempt fails.

- [ ] **T011b** [US1] Merge ingestion data with baseline outcomes:  
  1. Load both parquet files and `raw_outcomes.json`.  
  2. Join on `task_id` to produce `data/processed/ground_truth.csv` with columns `task_id`, `code_diff`, `status`, `dynamic_execution_outcome`.  
  3. Ensure every row has a non‑null `dynamic_execution_outcome` (or `"Unparseable"` status).  
  *Verification*: `tests/unit/test_ground_truth_merge.py` asserts that the CSV row count equals the sampled size and that the `dynamic_execution_outcome` column contains only the allowed values.

- [ ] **T015** [US1] Validate `ground_truth.csv` completeness: a pytest script `tests/integration/test_ground_truth_completeness.py` asserts that the file contains exactly the sampled number of rows, that the `dynamic_execution_outcome` column has only `"Pass"`, `"Fail"`, `"Timeout/Fail"` or `"Unparseable"`, and that any `"Unparseable"` rows have `status="Unparseable"`.

---

## Phase 4 – User Story 2: Structural feature extraction & graph construction (Priority P2)

- [ ] **T017** [P] Unit test `tests/unit/test_tree_sitter.py` that parses a known Python snippet (`def foo(): return bar`) and asserts that the generated AST contains a `function_definition` node and a `call` node for `bar`.  

- [ ] **T018** [P] Unit test `tests/unit/test_fallback_metrics.py` that forces `semantic_complexity_score` to be `null` for a synthetic task and checks that the output still contains non‑null `lines_of_code`, `dependency_depth`, and `cyclomatic_complexity`.  

- [ ] **T019** [US2] Implement `code/scripts/extract_features.py` to:  
  1. Load `data/processed/ground_truth.csv`.  
  2. Skip rows where `status == "Unparseable"`.  
  3. Use `tree‑sitter` to build an in‑memory dependency graph for each `code_diff`.  
  4. Compute the metrics: `dependency_depth`, `cyclomatic_complexity` (via `radon`), `semantic_complexity_score` (if semantic nodes exist), `lines_of_code`, `node_count`, `edge_count`.  
  5. Write each graph to `data/graphs/{task_id}.json`.  
  *Verification*: `tests/integration/test_feature_extraction.py` runs the script on a small synthetic `ground_truth.csv` (3 tasks) and checks that a JSON graph and a CSV row are produced for each parseable task.

- [ ] **T019a** [US2] Validate graph‑mapping integrity: generate `data/logs/graph_mapping_audit.json` that stores a SHA‑256 hash of each `code_diff` alongside the SHA‑256 hash of its serialized graph. Provide a test `tests/integration/test_graph_hashes.py` that loads the audit file and confirms that for every entry the two hashes match the on‑disk files.

- [ ] **T020** [US2] Serialize all graphs and create the final feature table `data/processed/features.csv` by merging the metric columns with `ground_truth.csv`. The CSV must contain **no missing values**; rows lacking `semantic_complexity_score` must have a non‑null `lines_of_code`.  
  *Verification*: `tests/unit/test_features_no_missing.py` loads the CSV and asserts that `semantic_complexity_score.isna().sum()` equals the number of rows where `lines_of_code` is non‑null, and that no other columns contain `NaN`.

---

## Phase 5 – User Story 3: Predictive modeling & threshold decision boundary (Priority P3)

- [ ] **T023** [P] Unit test `tests/unit/test_model_training.py` that loads a tiny synthetic `features.csv` (5 rows), trains both a logistic regression (`sklearn.linear_model.LogisticRegression`) and a random forest (`sklearn.ensemble.RandomForestClassifier`) with `random_state=42` and `n_jobs=1`, then pickles the models to temporary files and asserts that unpickling succeeds.

- [ ] **T024** [P] Integration test `tests/integration/test_threshold_sweep.py` that runs `code/scripts/train_model.py` on a miniature dataset (10 rows) and checks that `data/processed/threshold_sweep.json` contains entries for thresholds `0.01`, `0.05`, and `0.1`.

- [ ] **T028** [US3] Implement `code/scripts/train_model.py` to:  
  1. Load `data/processed/features.csv`.  
  2. Split into train/validation (80/20) with `random_state=0`.  
  3. Train **Logistic Regression** (`solver='lbfgs'`, `max_iter=1000`) and **Random Forest** (`n_estimators=200`, `max_depth=None`, `n_jobs=1`).  
  4. For each model, sweep decision thresholds `{0.01, 0.05, 0.1}` and compute the false‑negative rate (FNR) on the validation set (a false negative is a prediction of “Static_Safe” while the ground‑truth label is `Fail`/`Timeout/Fail`).  
  5. Write the trained models to `models/logistic_regression.pkl` and `models/random_forest.pkl`.  
  6. Produce `data/processed/threshold_sweep.json` with the schema: `{model_type, threshold, fnr, unsafe (bool)}` where `unsafe` is true if `fnr > 0.001`.  
  7. Compute Pearson correlation coefficients between each structural metric and the binary target “dynamic execution required” and store them in `data/processed/model_report.json` with fields `model_type`, `threshold`, `fnr`, `framing: "associational"`, `safety_flag`, `correlation_coefficient`.  
  *Verification*: `tests/integration/test_model_outputs.py` checks that both model files exist, that `threshold_sweep.json` contains three threshold entries per model, and that `model_report.json` includes the required keys and that `framing` equals `"associational"`.

- [ ] **T028a** [US3] Success‑criteria test `tests/integration/test_success_criteria.py` that reads `threshold_sweep.json` and `model_report.json` and asserts:  
  • At least one threshold achieves **FNR ≤ 0.001** (0.1 %).  
  • If no such threshold exists, `model_report.json` contains a field `minimum_achievable_fnr` and `safety_flag` is `true`.  
  • `correlation_coefficient` is a numeric value (‑1 ≤ r ≤ 1).  

---

## Phase 6 – Polish & cross‑cutting concerns  

- [ ] **T035a** [SC‑004] Profile `code/scripts/ingest.py` with `cProfile`, identify the top three CPU hotspots, apply straightforward optimisations (e.g., batch‑wise streaming, reduced JSON parsing), and save the profiling report to `data/logs/ingest_profile.log`.  

- [ ] **T035b** [SC‑004] Profile `code/scripts/extract_features.py` similarly and store `data/logs/extract_profile.log`.  

- [ ] **T035c** [SC‑004] Profile `code/scripts/train_model.py` and store `data/logs/train_profile.log`.  

- [ ] **T036** [P] Add edge‑case unit tests:  
  * `tests/unit/test_empty_dataset.py` – ensures scripts raise a clear `ValueError` on an empty `features.csv`.  
  * `tests/unit/test_parsing_failure.py` – feeds a syntactically broken snippet to `extract_features.py` and checks that the corresponding row is marked `"Unparseable"` in `ground_truth.csv`.  
  * `tests/unit/test_timeout.py` – simulates a long‑running baseline task and verifies that `"Timeout/Fail"` is recorded in `raw_outcomes.json`.  

- [ ] **T037** [P] Write a quick‑start validation script `tests/integration/test_quickstart_no_static_shortcut.py` that parses `docs/quickstart.md` and fails if the phrase “static‑only” appears anywhere.  

- [ ] **T038** [P] Generate SHA‑256 checksums for every file under `data/` and `models/`, write them to `state/artifact_hashes.yaml`, and confirm via `tests/integration/test_checksums.py` that the manifest matches the on‑disk files.

---

## Phase 7 – Review & feasibility validation  

- [ ] **T044a** [P] Implement a “causal‑language filter” `code/scripts/causal_filter.py` that scans `data/processed/model_report.json` and `docs/research.md` for prohibited causal verbs (`causes`, `drives`, `leads to`, `results in`). If any are found, the script writes a warning to `data/logs/causal_language_audit.json` and exits with a non‑zero status, causing the pipeline to abort.  

- [ ] **T044b** [P] Positive check `code/scripts/associational_check.py` that ensures the word “associational” (or the phrase “correlates with”) appears in both `data/processed/model_report.json` and `docs/research.md`. Missing phrasing results in a JSON warning `data/logs/associational_check.json` and a non‑zero exit code.  

**Final checkpoint** – All verification scripts must pass; the repository now contains a complete, reproducible end‑to‑end pipeline that answers the research question while satisfying every functional requirement and constitutional rule.
