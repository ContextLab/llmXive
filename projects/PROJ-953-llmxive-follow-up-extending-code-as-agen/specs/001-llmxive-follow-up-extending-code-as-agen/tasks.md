# Tasks: llmXive follow‑up: extending “Code as Agent Harness”

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, contracts, and the project‑local `tasks.md` template.  
All paths are relative to the repository root.

---

## Phase 1 – Setup & first end‑to‑end analysis  

*Goal*: Establish a runnable skeleton and produce a minimal end‑to‑end result that can be verified on a fresh CPU‑only runner.

| ID | Parallel? | Description |
|----|-----------|-------------|
- [ ] **T001** [P] Create the canonical project layout (`code/`, `data/`, `tests/`, `docs/`) and record a directory tree listing.  
  *Artifacts*:<br> `code/structure_tree.txt` – plain‑text tree generated with `tree -a .` after directories are created.  
  *Verification*: A CI test `tests/integration/test_project_structure.py` checks that each required folder exists and that the tree file contains the expected top‑level entries.  

- [ ] **T002** [P] Initialize a Python 3.11 project and add a pinned `requirements.txt` containing `datasets`, `tree‑sitter`, `scikit‑learn`, `pandas`, `networkx`, `radon`, `pytest`, `jsonschema`.  
  *Path*: `requirements.txt`  

- [ ] **T003** [P] Configure linting (ruff) and formatting (black) via `pyproject.toml`.  
  *Path*: `pyproject.toml`  

- [ ] **T004a** [P] Create `docs/README.md` with project overview, installation steps, and CLI usage for `ingest.py`, `extract_features.py`, `train_model.py`.  

- [ ] **T004b** [P] Create `docs/quickstart.md` that walks a user through environment setup, dataset download, baseline execution, and model training. The quick‑start must explicitly invoke the full‑environment re‑execution baseline (no “static‑only” shortcut).  

- [ ] **T004c** [P] Create `docs/usage_guide.md` with detailed examples of running each pipeline stage, interpreting the decision‑boundary JSON, and visualising results.  

- [ ] **T004d** [P] Create `docs/api_reference.md` documenting public functions in `code/scripts/` (e.g., `ingest()`, `extract_features()`, `train_model()`).  

---

## Phase 2 – Foundational (blocking prerequisites)  

*Goal*: Provide the schema contracts, data‑model documentation, and supporting infrastructure that all later user‑story tasks depend on.

- [ ] **T005a** [US2] Write a unit test `tests/unit/test_schema_validation.py::test_structural_metric_fallback_logic` that loads `contracts/structural_metric.schema.yaml` and asserts that when `semantic_complexity_score` is `null` the record still validates because `lines_of_code` is present.  
  *Verification*: The test must initially **fail** (schema missing) and pass after `T005` is completed.  

- [ ] **T005** [P] Create the three YAML schema files required for validation:  
  * `contracts/task_artifact.schema.yaml` (already provided in the repo)  
  * `contracts/structural_metric.schema.yaml` – must define `semantic_complexity_score` as `null`‑able and include a `oneOf` rule that requires `lines_of_code` when the former is `null`.  
  * `contracts/model_outcome.schema.yaml` (already provided)  
  * All schemas must be valid JSON‑Schema Draft‑07 documents.  

- [ ] **T005b** [P] Write `specs/001-llmxive-harness-extension/data-model.md` that documents the full data flow (ingestion → baseline → feature extraction → modeling), lists all artifact relationships, and embeds the three contract schemas by reference.  
  *Verification*: CI runs `tests/integration/test_data_model_doc.py` which parses the markdown for expected section headings and validates that each referenced schema file exists.  

- [ ] **T006** [P] Implement `code/scripts/update_state.py` to write a SHA‑256 checksum manifest (`state/artifact_hashes.yaml`) for every file under `data/` and `models/`.  

- [ ] **T007** [P] Create placeholder `.gitkeep` files in `data/raw/`, `data/processed/`, `data/graphs/` to guarantee the directories exist in the repository.  

- [ ] **T008** [P] Add a lightweight configuration loader `code/scripts/config.py` that reads environment variables (e.g., `HF_TOKEN`, `SAMPLE_SIZE`) and raises a clear exception if required variables are missing.  

**Checkpoint** – All foundational artifacts must exist and pass their respective schema / documentation tests before any user‑story work begins.

---

## Phase 3 – User Story 1: Dataset ingestion & ground‑truth generation (Priority P1)

- [ ] **T009** [P] Contract test `tests/contract/test_ingest.py` verifies that `ingest.py` calls the HuggingFace API with a valid token and writes parquet files under `data/raw/`.  

- [ ] **T010** [P] Unit test `tests/unit/test_timeout_handler.py` confirms that tasks exceeding the 600 s limit are recorded with the literal outcome `"Timeout/Fail"` in the JSON outcome file.  

- [ ] **T011** [US1] Implement `code/scripts/ingest.py` to:  
  1. Stream the SWE‑bench and AgentBench datasets via `datasets.load_dataset(..., streaming=True)`.  
  2. Sample **exactly 500** tasks (or stop earlier if RAM > 6 GB) and log the chosen sample size in `data/logs/ingest_sample_log.json`.  
  3. Extract `task_id`, `code_diff`, `original_code` and write two parquet files: `data/raw/swe_bench_subset.parquet` and `data/raw/agentbench_subset.parquet`.  
  4. Add a `status` column set to `"Unparseable"` for any record where `tree‑sitter` fails to parse the `code_diff`.  
  *Verification*: `tests/integration/test_ingest_output.py` checks that both parquet files exist, contain 500 rows total, and have no nulls in `code_diff`.  

- [ ] **T011a** [US1] Validate the sampling strategy. Read `data/logs/ingest_sample_log.json` and generate a human‑readable justification file `data/logs/sampling_justification.md` that explains why 500 tasks were chosen (pilot size, RAM budget, statistical power note).  

- [ ] **T013** [US1] Implement `code/scripts/baseline_runner.py` that:  
  1. Reads the parquet files from `T011`.  
  2. For each task, creates an isolated Python virtual environment (no Docker, pure CPU) and executes the `code_diff` against the `original_code`.  
  3. Records `"Pass"`, `"Fail"`, or `"Timeout/Fail"` in `data/processed/raw_outcomes.json`.  
  4. Enforces **no CUDA** usage – any attempt to import `torch.cuda` raises an exception.  

- [ ] **T011b** [US1] Merge ingestion data with baseline outcomes:  
  1. Load both parquet files and `raw_outcomes.json`.  
  2. Join on `task_id` to produce `data/processed/ground_truth.csv` with columns `task_id`, `code_diff`, `status`, `dynamic_execution_outcome`.  
  3. Ensure every row has a non‑null `dynamic_execution_outcome` (or `"Unparseable"` status).  

- [ ] **T015** [US1] Validate `ground_truth.csv` completeness: a pytest script `tests/integration/test_ground_truth_completeness.py` asserts that the file contains exactly the sampled number of rows, that the `dynamic_execution_outcome` column has only the three allowed values, and that any `"Unparseable"` rows are correctly flagged.  

**Checkpoint** – A verified ground‑truth CSV is available for downstream feature extraction.

---

## Phase 4 – User Story 2: Structural feature extraction & graph construction (Priority P2)

- [ ] **T017** [P] Unit test `tests/unit/test_tree_sitter.py` parses a known Python snippet and asserts that the generated AST contains the expected function‑call nodes.  

- [ ] **T018** [P] Unit test `tests/unit/test_fallback_metrics.py` forces `semantic_complexity_score` to be `null` and checks that `lines_of_code`, `dependency_depth`, and `cyclomatic_complexity` are still produced.  

- [ ] **T019** [US2] Implement `code/scripts/extract_features.py` to:  
  1. Load `data/processed/ground_truth.csv`.  
  2. Skip rows where `status == "Unparseable"`.  
  3. Use `tree‑sitter` to build an in‑memory dependency graph for each `code_diff`.  
  4. Compute `dependency_depth`, `cyclomatic_complexity` (via `radon`), `semantic_complexity_score` (if semantic nodes exist), `lines_of_code`, `node_count`, `edge_count`.  
  5. Output a per‑task JSON graph to `data/graphs/{task_id}.json`.  

- [ ] **T019a** [US2] Validate graph‑mapping integrity: generate `data/logs/graph_mapping_audit.json` that stores a SHA‑256 hash of each `code_diff` alongside the hash of its serialized graph, and a script `tests/integration/test_graph_hashes.py` confirms the two hashes match for every task.  

- [ ] **T020** [US2] Serialize all graphs and create the final feature table `data/processed/features.csv` by merging the metric columns with `ground_truth.csv`. The CSV must contain no missing values; rows lacking `semantic_complexity_score` must have a non‑null `lines_of_code`.  

**Checkpoint** – `features.csv` and the graph JSONs are ready for modeling.

---

## Phase 5 – User Story 3: Predictive modeling & threshold decision boundary (Priority P3)

- [ ] **T023** [P] Unit test `tests/unit/test_model_training.py` loads a tiny synthetic feature set, trains both a logistic regression and a random forest with a fixed seed, and asserts that model objects can be pickled.  

- [ ] **T024** [P] Integration test `tests/integration/test_threshold_sweep.py` runs `train_model.py` on a mini‑dataset and checks that the generated `threshold_sweep.json` contains entries for thresholds `0.01`, `0.05`, `0.1`.  

- [ ] **T028** [US3] Implement `code/scripts/train_model.py` to:  
  1. Load `data/processed/features.csv`.  
  2. Split into train/validation (80/20) with a deterministic random seed.  
  3. Train a **Logistic Regression** and a **Random Forest** (both CPU‑only, `n_jobs=1`).  
  4. For each model, sweep decision thresholds `{0.01, 0.05, 0.1}` and compute the false‑negative rate (FNR) on the validation set.  
  5. Write the trained models to `models/logistic_regression.pkl` and `models/random_forest.pkl`.  
  6. Produce `data/processed/threshold_sweep.json` containing, for each threshold, the FNR and a boolean `unsafe` flag (true if FNR > 0.001).  
  7. Compute Pearson correlation coefficients between each structural metric and the binary target “dynamic execution required” and store them in `data/processed/model_report.json` alongside the required fields: `model_type`, `threshold`, `fnr`, `framing: "associational"`, `safety_flag`, `correlation_coefficient`.  

- [ ] **T028a** [US3] Verify success criteria: a script `tests/integration/test_success_criteria.py` reads `threshold_sweep.json` and `model_report.json` and asserts that **SC‑001** (FNR ≤ 0.001) is satisfied for at least one threshold; if not, it checks that the reported `minimum_achievable_fnr` is present and that `safety_flag` is set to `true`. It also confirms that `correlation_coefficient` is present and that the `framing` field equals `"associational"`.  

**Checkpoint** – A validated model, its decision boundary, and all safety/association metadata are produced.

---

## Phase 6 – Polish & cross‑cutting concerns  

- [ ] **T035a** [SC‑004] Profile `code/scripts/ingest.py` with `cProfile`, identify the top three CPU hotspots, and apply straightforward optimisations (e.g., batch‑wise streaming, reduced JSON parsing). Save the profile to `data/logs/ingest_profile.log`.  

- [ ] **T035b** [SC‑004] Profile `code/scripts/extract_features.py` similarly and store `data/logs/extract_profile.log`.  

- [ ] **T035c** [SC‑004] Profile `code/scripts/train_model.py` and store `data/logs/train_profile.log`.  

- [ ] **T036** [P] Add edge‑case unit tests:  
  * `tests/unit/test_empty_dataset.py` – ensures scripts raise a clear error on an empty `features.csv`.  
  * `tests/unit/test_parsing_failure.py` – feeds a syntactically broken snippet to `extract_features.py` and checks that the task is marked `"Unparseable"` in the output CSV.  
  * `tests/unit/test_timeout.py` – simulates a long‑running baseline task and verifies `"Timeout/Fail"` is recorded.  

- [ ] **T037** [P] Run a quick‑start validation script that parses `docs/quickstart.md` and asserts that the instructions **do not** contain any “static‑only” shortcut; the test fails if such a phrase is found.  

- [ ] **T038** [P] Generate SHA‑256 checksums for every file under `data/` and `models/`, write them to `state/artifact_hashes.yaml`, and confirm via `tests/integration/test_checksums.py` that the manifest matches the on‑disk files.  

---

## Phase 7 – Review & feasibility validation  

- [ ] **T044a** [P] Implement a “causal‑language filter” that scans `data/processed/model_report.json` and `docs/research.md` for prohibited causal verbs (`causes`, `drives`, `leads to`, etc.). If any are found, write a warning to `data/logs/causal_language_audit.json` and abort the pipeline with a clear error message.  

- [ ] **T044b** [P] Positive check that ensures the phrase “associational” (or “correlates with”) appears in both `model_report.json` and `docs/research.md`. Failure writes to `data/logs/associational_check.json`.  

**Final checkpoint** – All verification scripts must pass; the repository now contains a complete, reproducible end‑to‑end pipeline that answers the research question while satisfying every functional requirement and constitutional rule.
