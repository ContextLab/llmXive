# Tasks: Extending FastContext with Deterministic Retrieval (FastContext‑Lite)

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and the current `tasks.md` template.  
All tasks are written as checklist items with unique IDs, required artifact paths, and explicit verification steps.

---

## Phase 1 – Project Setup & Infrastructure (User Story 0)

- [ ] **T001** [US0] Create the project directory hierarchy under `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/`  

  ```
  projects/PROJ-905-llmxive-follow-up-extending-fastcontext/
  ├─ data/
  │   ├─ raw/
  │   ├─ processed/
  │   └─ results/
  ├─ code/
  ├─ tests/
  │   ├─ unit/
  │   └─ integration/
  ├─ specs/
  │   └─ contracts/
  └─ state/
  ```

  **Verification**: Run `tree -L 3 projects/PROJ-905-llmxive-follow-up-extending-fastcontext/ > data/processed/dir_structure.txt` and then assert that `data/processed/dir_structure.txt` exists and contains entries for the five top‑level directories (`data`, `code`, `tests`, `specs`, `state`).  

- [ ] **T002** [US0] Add a pinned `requirements.txt` at `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/requirements.txt` containing the exact package list required for the study (CPU‑only wheels only).

  ```text
  datasets==2.19.0
  scikit-learn==1.5.0
  pandas==2.2.2
  numpy==1.26.4
  tiktoken==0.7.0
  networkx==3.3
  scipy==1.13.0
  tqdm==4.66.5
  huggingface-hub==0.23.2
  ```

  **Verification**: `pip install -r …/requirements.txt` completes without requesting CUDA or non‑CPU wheels (inspect the log for “cpu” only).

- [ ] **T003a** [US0] Create a lint‑configuration file `.ruff.toml` in `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/` with the rule set `["E", "F", "I", "W"]` and `target-version = "py311"`.

  ```toml
  [tool.ruff]
  target-version = "py311"
  select = ["E", "F", "I", "W"]
  ```

  **Verification**: `ruff check projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/` runs without configuration errors (exit code 0).

- [ ] **T003b** [US0] Create `pyproject.toml` in `projects/PROJ-905-llmxive-follow-up-extending-fastcontext/code/` with Black configuration (`line-length = 88`, `target-version = ["py311"]`).

  ```toml
  [tool.black]
  line-length = 88
  target-version = ["py311"]
  ```

  **Verification**: `black --check .` reports “All done!” (exit code 0).

- [ ] **T004** [US0] Implement `code/versioning.py` that computes SHA‑256 hashes for every file under `data/` and `code/` and writes a manifest to `state/projects/PROJ-905-llmxive-follow-up-extending-fastcontext.yaml`.

  **Verification**: Running `python -m code.versioning` creates the YAML file; the file contains a top‑level key `files` mapping relative paths to 64‑character hex digests.

- [ ] **T005** [US0] Add `code/__init__.py` and copy the JSON schema files from `specs/contracts/` into `code/schemas/` for easy import.

  **Verification**: `ls code/schemas/` lists all four schema `.yaml` files; importing `code.schemas.execution_schema` succeeds without `FileNotFoundError`.

- [ ] **T006** [US0] Create `code/config.py` exposing constants for dataset identifiers, TF‑IDF hyper‑parameters, and weighting factors (`W_DIR=0.4`, `W_TEST=0.3`, `W_IMPORT=0.3`, `DEFAULT_SCORE=0.0`).

  **Verification**: `python -c "import code.config as cfg; assert hasattr(cfg, 'W_DIR')"` exits cleanly.

- [ ] **T007** [US0] Implement `code/data_loader.py` that streams the SWE‑bench Lite dataset via  

  ```python
  from datasets import load_dataset
  ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test", streaming=True)
  ```

  The script must verify the SHA‑256 checksum of each downloaded shard (using the `datasets` built‑in `download_checksums` if available) and raise an exception on mismatch – **no synthetic fallback**.

  **Verification**: Running `python -m code.data_loader` prints the first three `instance_id`s and exits with status 0; deliberately corrupting a shard causes a `RuntimeError`.

## Phase 2 – Data Curation (User Story 1)

- [ ] **T008** [US1] Implement `code/static_analysis.py` that, for a given repository path, computes:

  * `dir_score` – consistency of top‑level directories (`src/`, `tests/`, `docs/`).
  * `test_score` – average relative path distance of test files to source files.
  * `import_score` – density of the import‑graph (using `networkx`).

  The composite `regularity_score = W_DIR*dir_score + W_TEST*test_score + W_IMPORT*import_score` (weights from `config.py`). Output a CSV row per repository with columns  
  `instance_id,repo,dir_score,test_score,import_score,regularity_score`.

  **Verification**: Running the script on a fixture repository creates `data/processed/tmp_score.csv` containing the header and at least one row; the `regularity_score` column values lie in [0, 1].

- [ ] **T009** [US1] Add edge‑case handling in `static_analysis.py` (missing test files, empty repo, binary‑only repos). In such cases return a default score defined in `config.py` (`DEFAULT_SCORE = 0.0`) and log a warning.

  **Verification**: Unit test `tests/unit/test_static_analysis.py::test_missing_tests` passes (asserts returned `regularity_score == 0.0`).

- [ ] **T010** [US1] Create `code/stratification.py` that reads the full `regularity_scores.csv` (generated by `static_analysis.py` over the streamed SWE‑bench), sorts by `regularity_score`, and splits into two balanced strata (“Regular” and “Irregular”) of equal size (or as close as possible). Write the result to `data/processed/regularity_scores.csv` with an additional column `split`.

  **Verification**: After execution, `csvstat --count data/processed/regularity_scores.csv` reports the same number of rows for each `split` value (difference ≤ 1).

- [ ] **T027** [US1] Generate `data/processed/ground_truth_annotations.csv` by extracting the ground‑truth relevant file lists from SWE‑bench task annotations.

  **Verification**: The CSV contains columns `instance_id` and `ground_truth_files` (JSON‑encoded list) for every repository present in `regularity_scores.csv`.

- [ ] **T011** [US1] **Pilot validation script** – `code/pilot_validation.py`

  1. Loads the first **20** rows of `data/processed/regularity_scores.csv`.  
  2. For each repository runs a lightweight TF‑IDF keyword‑only retrieval (over file names only) to obtain a **precision** estimate (intersection over union with ground‑truth files from `ground_truth_annotations.csv`).  
  3. Computes the Pearson correlation `r` and two‑tailed p‑value between `regularity_score` and the precision estimates.  
  4. Writes `data/processed/pilot_correlation.json` with exact schema `{ "pearson_r": float, "p_value": float, "n_samples": int }`.

  **Verification**: After running `python -m code.pilot_validation`, the JSON file exists, contains the three keys, and `n_samples == 20`. A quick `jq .pearson_r` prints a number between ‑1 and 1.

## Phase 3 – Deterministic Engine & Baseline (User Story 2)

- [ ] **T012** [US2] Implement `code/fastcontext_lite.py`:

  * Deterministic parser extracts issue‑related keywords from the SWE‑bench task description.  
  * Streams a TF‑IDF index over all repository files (`ngram_range=(1,2)`, `max_features=10000`, chunked reads ≤ 200 KB).  
  * Retrieves the top‑K (K=5) snippets, concatenates them, and computes:
    * `context_precision` (IoU vs. ground‑truth files),
    * `total_tokens` (using `tiktoken` on the concatenated snippet),
    * `latency_ms` (wall‑clock timing).

  Returns a JSON **execution record** adhering to `execution_schema.yaml` with fields: `instance_id`, `split`, `method="FastContext-Lite"`, `context_precision`, `total_tokens`, `latency_ms`, `regularity_score`, `hardware_efficiency`.

  **Verification**: Running the script on a single “Regular” repository produces `lite_log.json` that validates with `jsonschema` against `execution_schema.yaml` and contains all required numeric fields.

- [ ] **T013** [US2] Add `code/benchmark_lite.py` that runs `fastcontext_lite.py` on a stratified sample of **50** repositories (25 Regular + 25 Irregular) and records average latency, peak memory (via `tracemalloc`), and token usage in `data/results/lite_benchmark.json`.

  **Verification**: After execution, the JSON file contains keys `avg_latency_ms`, `peak_memory_mb`, `avg_tokens`; each is a non‑negative number.

- [ ] **T014** [US2] Implement `code/baseline_runner.py` (original FastContext 4B model):

  1. Load model `princeton-nlp/fastcontext-4b` with `device_map="cpu"` (torch ≥ 2.2).  
  2. No GPU fallback – the script must abort with a clear error if CUDA is unavailable.  
  3. Log an execution record matching `execution_schema.yaml` with `method="FastContext-Original"` and the same metric fields as T012 (no `hardware` field).

  **Verification**: On the CI runner (CPU‑only) the script completes successfully; the output file `baseline_log.json` validates against `execution_schema.yaml`.

- [ ] **T015** [US2] Create `code/metrics_logger.py` that validates each execution record against `execution_schema.yaml` (using `jsonschema`) before appending to `data/results/exploration_logs.jsonl`.

  **Verification**: Feeding a deliberately malformed record raises a `jsonschema.ValidationError`; a correct record is appended without error.

- [ ] **T016** [US2] Write orchestration script `code/main.py` that:

  * Loads `regularity_scores.csv` to obtain the two splits.  
  * Iterates over every repository, runs **both** `fastcontext_lite.py` and `baseline_runner.py`.  
  * Uses `metrics_logger.py` to store each run’s JSON line in `exploration_logs.jsonl`.

  **Verification**: After `python -m code.main --max-repos 10` finishes, `exploration_logs.jsonl` contains **20** lines (10 repos × 2 methods) and each line validates against the schema.

## Phase 4 – Statistical Comparison & Boundary Detection (User Story 3)

- [ ] **T017** [US3] Implement `code/analysis.py` that:

  1. Loads `exploration_logs.jsonl` and merges Lite vs. Baseline rows by `instance_id`.  
  2. Performs a Shapiro‑Wilk test on the paired differences of `context_precision` for the “Regular” set.  
  3. Chooses a paired **t‑test** if normality (p > 0.05) else a **Wilcoxon signed‑rank** test.  
  4. Computes effect size (Cohen’s d or rank‑biserial).  
  5. Writes `data/results/statistical_summary.json` conforming to `statistical_summary.schema.yaml` (includes `test_type`, `dataset`, `metrics.precision`, `metrics.latency`, and `boundary_analysis` placeholders).  
  6. Checks the p‑value against the deferred significance threshold (to be defined in `specs/quickstart.md`) and records a boolean `significant` field.

  **Verification**: The JSON file validates against `statistical_summary.schema.yaml`; the field `test_type` is either `"paired_t_test"` or `"wilcoxon_signed_rank"` and `significant` is a boolean.

- [ ] **T029** [US3] Extend `analysis.py` to compute the Pearson correlation coefficient `r` and 95 % confidence interval between `regularity_score` and the performance delta (`lite_precision - baseline_precision`) and store them in `statistical_summary.json` under `metrics.precision.correlation_r` and `metrics.precision.ci_95`.

  **Verification**: The JSON contains numeric `correlation_r` between –1 and 1 and a two‑element list `ci_95`.

- [ ] **T030** [US3] Add an optional non‑linear (quadratic) regression of `regularity_score` vs. performance delta; if the adjusted R² improves by ≥ 0.02 over the linear model, record `non_linear_fit=true` and the quadratic coefficients in `statistical_summary.json`.

  **Verification**: Presence of `non_linear_fit` boolean and, when true, a `quadratic_coeffs` array.

- [ ] **T018** [US3] Perform a linear regression of `regularity_score` vs. performance delta over the full dataset. Store `regression_slope` and `r_squared` in `statistical_summary.json` (already part of T017; now explicitly documented).

  **Verification**: After execution, `statistical_summary.json` contains numeric `regression_slope` and `r_squared` (0 ≤ r² ≤ 1).

- [ ] **T024** [US3] Compute the latency reduction percentage for the “Regular” set:  

  `latency_reduction_pct = 100 * (baseline_latency - lite_latency) / baseline_latency`  

  Verify that the reduction meets or exceeds the deferred target (e.g., 40 %). Record the value and a boolean `meets_target` in `statistical_summary.json`.

  **Verification**: JSON fields `latency_reduction_pct` (float) and `latency_meets_target` (bool) exist.

- [ ] **T025** [US3] Compute token‑consumption variance between methods for the “Regular” set and report the variance ratio and a statistical test (e.g., Levene’s test). Record `token_variance_ratio` and `token_variance_p` in `statistical_summary.json`.

  **Verification**: JSON contains the two numeric fields; `token_variance_p` is between 0 and 1.

- [ ] **T019** [US3] Add degradation calculation for the “Irregular” set:

  * Compute `degradation_pct = 100 * (baseline_precision - lite_precision) / baseline_precision`.  
  * Compare against the 10 % threshold (SC‑004) and record a boolean `degradation_exceeds_threshold`.  
  * Store `degradation_pct` (schema‑compliant) in `statistical_summary.json`.

  **Verification**: The JSON includes `degradation_pct` (float) and `degradation_exceeds_threshold` (bool).

- [ ] **T020** [US3] Validate the final `statistical_summary.json` against `analysis_schema.schema.yaml` using `jsonschema`.

  **Verification**: Running the validation command exits with status 0.

## Phase 5 – Documentation, Cleanup & Final Checks (User Story 0)

- [ ] **T021** [US0] Update `README.md` at the project root with:

  * Installation steps (`python -m venv`, `pip install -r code/requirements.txt`).  
  * Usage examples for the three entry points (`data_loader.py`, `fastcontext_lite.py`, `baseline_runner.py`).  
  * Contribution guidelines (code style, testing).

  **Verification**: `grep -q "Installation" README.md` succeeds; the file renders without markdown errors.

- [ ] **T022** [US0] Generate API documentation in `docs/` for `static_analysis.py`, `fastcontext_lite.py`, and `analysis.py` using `pdoc` (or `mkdocstrings`). Ensure the docs build without import errors.

  **Verification**: Running `pdoc --html code/static_analysis -o docs` creates an `index.html` file; opening it shows the module docstring.

- [ ] **T026** [US0] Create `quickstart.md` describing end‑to‑end execution steps, including the deferred significance threshold and latency‑reduction target placeholders.

  **Verification**: File exists and contains the required sections; `grep -q "Significance threshold" quickstart.md` succeeds.

- [ ] **T023** [US0] Run the end‑to‑end pipeline documented in `quickstart.md` and confirm that:

  1. `data/processed/regularity_scores.csv` is generated with both splits.  
  2. `data/results/exploration_logs.jsonl` contains entries for **both** methods for every repository in the sample.  
  3. `data/results/statistical_summary.json` validates against its schema.  
  4. All unit and integration tests pass (`pytest -q` returns exit code 0).

  **Verification**: The CI job logs “PASS” for each of the four bullet points; `pytest -q` outputs `..` (or more) and ends with `1 passed in …s`.

- [ ] **T028** [US0] Add a final sanity‑check task that ensures `data/processed/dir_structure.txt` (produced by T001) contains the expected five top‑level directories.

  **Verification**: A script reads the file and asserts presence of each directory name; exits with status 0.

## Dependencies & Execution Order

| Phase | Prerequisite Tasks | Blocking Tasks |
|------|--------------------|----------------|
| **Setup** | – | T001 → T002 → T003a → T003b → T004 → T005 → T006 → T007 |
| **User Story 1** | Setup | T008 → T009 → T010 → T027 → T011 |
| **User Story 2** | Setup & US 1 (for split) | T012 → T013 → T014 → T015 → T016 |
| **User Story 3** | US 2 (metrics) | T017 → T018 → T019 → T020 → T024 → T025 → T029 → T030 → T024 → T025 |
| **Polish** | All previous phases | T021 → T022 → T026 → T023 → T028 |

Tasks marked **[P]** can run in parallel when their file targets do not overlap. All other tasks respect the data‑flow order shown above.  

--- 

*End of `tasks.md`.*  
