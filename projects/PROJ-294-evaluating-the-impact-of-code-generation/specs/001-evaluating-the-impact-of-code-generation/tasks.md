# Tasks: Evaluating the Impact of Code Generation Models on Code Testability

**Inputs**: `spec.md`, `plan.md`, current research artifacts, and reviewer feedback.  
**Prerequisites**: None (all tasks are self‑contained, dependencies are indicated in each item).

---

## Phase 1 – Project scaffolding & reproducible infrastructure  

**Goal**: Establish a verifiable file‑system layout and core utilities so that every downstream step can be executed and its artefacts validated.

| ID | Parallel? | Story | Description |
|----|-----------|-------|-------------|

- [ ] **T001a** **[P]** – **Create core project directories**  
  *Create the required top‑level folders and place a `.gitkeep` file in each to make their existence verifiable:*  

  ```
  code/.gitkeep
  data/.gitkeep
  data/raw/.gitkeep
  data/generated/.gitkeep
  data/analysis/.gitkeep
  results/.gitkeep
  tests/.gitkeep
  docs/.gitkeep
  ```  

  **Verification**: `ls -R` must list each directory and the `.gitkeep` file; a CI test checks that `os.path.isdir` returns `True` for each path.

- [ ] **T001b** **[P]** – **Create state directory**  
  *Create a `state/` folder to hold intermediate CI artefacts and place a `.gitkeep` file.*  

  ```
  state/.gitkeep
  ```  

  **Verification**: Same as T001a – CI asserts the directory exists.

- [ ] **T002** **[P]** – **Initialize Python project**  
  *Generate `code/requirements.txt` with pinned dependencies (see `plan.md`).*  
  **Verification**: `pip install -r code/requirements.txt` succeeds without version conflicts.

- [ ] **T003** **[P]** – **Configure linting**  
  *Create `.flake8` and `pyproject.toml` for Black formatting.*  
  **Verification**: `flake8 .` and `black --check .` pass.

- [ ] **T004** **[P]** – **Setup logging infrastructure**  
  *Add `code/utils/logger.py` with timestamp‑ed, task‑ID‑aware logger (FR‑007).*  
  **Verification**: Importing the module returns a logger that writes a line containing ISO‑8601 timestamp and a `task_id` field.

- [ ] **T004b** **[S]** – **Performance instrumentation (hooks)**  
  *Extend `logger.py` to emit structured events `generation_duration_ms` and `tasks_per_minute`.*  
  **Verification**: After a generation run, `data/analysis/performance.json` contains the two keys with numeric values.

- [ ] **T004c** **[P]** – **Performance aggregation & threshold check**  
  *Read `config.yaml` for `throughput_threshold`, aggregate the performance metrics from logs, write `data/analysis/performance.json`, and raise an exception if thresholds are not met.*  
  **Verification**: CI fails if `tasks_per_minute` < threshold.

- [ ] **T005** **[P]** – **SHA256 checksum utility**  
  *Implement `code/utils/hash_utils.py` exposing `sha256_file(path)` (FR‑001, FR‑011).*  
  **Verification**: Unit test hashes a known file and matches expected hash.

- [ ] **T006** **[P]** – **Seed‑pinning utility**  
  *Create `code/utils/seeds.py` that sets `random.seed(SEED)`, `np.random.seed(SEED)`, and `torch.manual_seed(SEED)` at import time. All pipeline scripts must import this module first.*  
  **Verification**: A CI test imports the module and checks that the three RNGs report the configured seed value.

- [ ] **T015a** **[US1]** – **Sandbox execution environment**  
  *Create `code/sandbox.py` with `TestSandbox` context manager that limits memory (2 GB) and enforces a 60‑second timeout per test (FR‑005). Creates `data/sandbox/` if needed.*  
  **Verification**: Running a sample test inside the sandbox either succeeds or raises a timeout error; CI asserts the timeout is triggered for a deliberately long‑running script.

---

## Phase 2 – Data acquisition, generation & metric pipeline (User Story 1, P1)

- [ ] **T010** **[US1]** – **Download HumanEval dataset (pinned commit)**  
  *Script `code/download_data.py` uses `datasets.load_dataset("openai/openai_humaneval", revision="d82884567991811251419242208479796794843")`, saves as `data/raw/humaneval.parquet`, computes SHA‑256, and writes `data/metadata.yaml` with `checksum` and `commit_hash`.*  
  **Verification**: CI checks that the file exists, its hash matches the value recorded in `metadata.yaml`, and a mismatch raises `RuntimeError`.

- [ ] **T011** **[US1]** – **Extract human reference solutions**  
  *Read `data/raw/humaneval.parquet`, write each `canonical_solution` to `data/generated/human_samples.jsonl` (JSON Lines) with fields `task_id`, `code`, `source="human"`.*  
  **Verification**: File contains 164 lines; each line validates against `human_samples.schema.yaml`.

- [ ] **T012** **[US1]** – **Generate code with primary model (codegen‑mono‑4B, CPU‑first)**  
  *`code/generate_code.py` loads `Salesforce/codegen-mono-4b` (8‑bit quantized) on `device="cpu"`. Implements exponential‑backoff retry and 60 s per task. If OOM or load failure, automatically falls back to `Salesforce/codegen-mono-350M`. Writes results to `data/generated/codegen_samples.jsonl` with fields `task_id`, `generated_code`, `model`, `status`, `generation_time`.*  
  **Verification**: CI parses the JSONL and confirms exactly 164 entries, each with non‑null `generated_code` for successful rows and correct `status`.

- [ ] **T013** **[US1]** – **Generation error logging**  
  *Extend `generate_code.py` to catch `RuntimeError`, `TimeoutError`, `MemoryError`, log details to `code/errors.log`, and record failed entries with `status="failed"` and `generated_code=null`.*  
  **Verification**: After a forced failure (e.g., invalid model name), the log contains the task ID and exception message; the output file reflects the failure status.

- [ ] **T014** **[US1]** – **Static metric extraction (complexity & Halstead)**  
  *`code/analyze_metrics.py` runs `radon cc --json` and `radon hal --json` on both human and generated samples, producing `cyclomatic_complexity`, `halstead_volume`, `halstead_difficulty`, `halstead_effort`. Results are merged into a temporary structure.*  
  **Verification**: Unit test runs the function on a tiny synthetic snippet and asserts the numeric fields are ≥ 0.

- [ ] **T015** **[US1]** – **Dynamic test execution & pass‑rate calculation**  
  *Using `TestSandbox` from T015a, execute each HumanEval test suite against the corresponding code (human and LLM). Record `pass_rate = passed_tests / total_tests` (float 0‑1) and `dynamic_branch_coverage` via `coverage.py`.*  
  **Verification**: For a known passing sample, `pass_rate` == 1.0; for a known failing sample, < 1.0.

- [ ] **T016** **[US1]** – **Static branch‑coverage potential**  
  *Run `radon` to compute `branch_coverage_potential` (static estimate between 0 and 1) for every sample and store the value.*  
  **Verification**: CI checks that the field `branch_coverage_potential` exists, is numeric, and lies in [0,1] for all 164 records.

- [ ] **T017a** **[US1]** – **Aggregate full‑sample metrics**  
  *Combine static and dynamic results into `data/analysis/metrics.json` (schema `analysis.schema.yaml`). Includes fields: `task_id`, `source_type` (`human` | `codegen`), `model_name`, `metrics` (all required sub‑fields), `status`, `error_message` (null on success).*  
  **Verification**: JSON validates against `analysis.schema.yaml`; no `null` in required numeric fields.

- [ ] **T017b** **[US1]** – **Create filtered valid‑task artefacts**  
  *Read `metrics.json`, filter where `pass_rate ≥ 0.80`, write `data/analysis/valid_task_metrics.json` (same schema) and `data/analysis/valid_task_ids.json` (list of strings).*  
  **Verification**: Count of IDs matches number of records in the filtered file; all `pass_rate` values satisfy the threshold.

---

## Phase 3 – Statistical comparison & sensitivity analysis (User Story 2, P2)

- [ ] **T020** **[US2]** – **Wilcoxon Signed‑Rank tests (paired)**  
  *`code/statistical_tests.py` loads `metrics.json`, pairs human vs. codegen entries by `task_id`, and runs `scipy.stats.wilcoxon` on `cyclomatic_complexity`, `halstead_volume`, and `branch_coverage_potential`. Uses two‑tailed α = 0.05.*  
  **Verification**: Output JSON contains `wilcoxon_p_value` and `wilcoxon_statistic` for each metric; a unit test with a tiny handcrafted dataset yields the expected statistic.

- [ ] **T024** **[US2]** – **MDES & achieved power calculation**  
  *Within the same script, compute Minimum Detectable Effect Size for N = 164, α = 0.05, target power = 0.80 (using `statsmodels.stats.power.tt_ind_solve_power`). Also compute post‑hoc achieved power and 95 % CI for the observed effect size.*  
  **Verification**: `statistical_results.json` contains keys `mdes`, `achieved_power`, `effect_size_ci_lower`, `effect_size_ci_upper`; a test verifies that `achieved_power` ≥ 0.8 for a simulated large effect.

- [ ] **T046** **[US2]** – **Validation status block**  
  *Append to `statistical_results.json` a `validation` object indicating whether FR‑004 (significance) and FR‑008 (power) criteria are satisfied.*  
  **Verification**: CI asserts that if any p‑value < 0.05 then `validation.significant=True`; similarly for power.

- [ ] **T026** **[US2]** – **Unit tests for statistical functions**  
  *Create `tests/unit/test_statistics.py` with synthetic datasets that produce known Wilcoxon p‑values and MDES values.*  
  **Verification**: Tests must pass; a failing test indicates a regression.

- [ ] **T027** **[US2]** – **Integration test for full statistical pipeline**  
  *`tests/integration/test_stats_pipeline.py` runs the end‑to‑end pipeline from `metrics.json` through `statistical_results.json` and checks that the output file exists and contains all required keys.*  
  **Verification**: CI runs the integration test after the pipeline scripts.

---

## Phase 4 – Reporting, citation validation & artefact integrity (User Story 3, P3)

- [ ] **T030** **[US3]** – **Figure generation**  
  *`code/report_generator.py` produces histogram and box‑plot PNGs for each continuous metric under `results/figures/`.*  
  **Verification**: Files exist, are non‑empty, and a checksum is recorded in `artifact_hashes.yaml`.

- [ ] **T031a** **[US3]** – **Citation extraction**  
  *Parse the Jinja2 template `results_report.md.j2` and any markdown sources, write `state/citations.yaml` with `title`, `url`, `source` for each citation.*  
  **Verification**: YAML contains at least one entry; schema validation passes.

- [ ] **T031** **[US3]** – **Report compilation**  
  *Render `results_report.md` from the template, injecting figures, tables, and statistical results (including MDES and validation status). Output path: `docs/report.md`.*  
  **Verification**: File exists; a regex search confirms that the MDES value appears in the document.

- [ ] **T031b** **[US3]** – **Report‑figure consistency check**  
  *After rendering, verify that every figure referenced in `report.md` has a matching file in `results/figures/` and that the `source_type` labels (`human`, `codegen`, `llama`) are correctly displayed.*  
  **Verification**: CI fails if any referenced figure is missing.

- [ ] **T056** **[US3]** – **Citation validation wrapper**  
  *`code/validate_citations.py` invokes the external Reference‑Validator Agent (`reference-validator --input state/citations.yaml --output state/validation_report.yaml`). On failure, raises `RuntimeError`.*  
  **Verification**: CI runs the wrapper and asserts `validation_report.yaml` contains `"valid": true`.

- [ ] **T050** **[US3]** – **Artifact hash verification**  
  *`code/validate_artifacts.py` computes SHA‑256 for all files in `data/generated/` and `data/analysis/`, writes `state/artifact_hashes.yaml` following `artifact-hashes.schema.yaml`.*  
  **Verification**: JSON schema validation succeeds; CI checks that the hash for `data/analysis/metrics.json` matches the value stored in the file.

- [ ] **T072** **[US3]** – **Support‑ticket volume measurement (SC‑004)**  
  *Create `code/measure_support_tickets.py` that queries the project's issue tracker (e.g., GitHub Issues API) for tickets opened in the last month, counts them, and writes `data/analysis/support_ticket_volume.json` with fields `month`, `ticket_count`.*  
  **Verification**: CI runs the script (mocked API in tests) and checks that the JSON file exists and contains a non‑negative integer count.

---

## Phase 5 – Sensitivity analysis with CodeLlama (additional requirement FR‑009)

- [ ] **T052** **[US3]** – **Generate CodeLlama samples**  
  *`code/generate_code_llama.py` loads the quantized GGUF model `TheBloke/CodeLlama-3B-Instruct-GGUF` via `llama-cpp-python` (`n_ctx=2048`, `n_threads=4`). Generates code for all 164 tasks, writes `data/generated/llama_samples.jsonl` with `task_id`, `generated_code`, `model="codellama-3b-q4"`, `status`, `generation_time`.*  
  **Verification**: Model file size ≈ 3 B parameters; script asserts `model.n_params` matches expected range, otherwise raises error.

- [ ] **T053a** **[US3]** – **Metric extraction for CodeLlama**  
  *Reuse static (`radon`) and dynamic (`coverage.py`) analysis from T014/T015 on `llama_samples.jsonl`, producing a temporary JSON file `data/analysis/llama_metrics_tmp.json`. Verify the file exists and validates against `analysis.schema.yaml`.*  
  **Verification**: CI checks file existence and runs schema validation; failures cause the task to be marked incomplete.

- [ ] **T053b** **[US3]** – **Merge CodeLlama metrics**  
  *Append the CodeLlama metrics to `data/analysis/metrics.json` with `source_type="llama"`; also produce `data/analysis/full_sample_metrics.json` containing human, codegen, and llama rows.*  
  **Verification**: JSON schema validation passes; count of distinct `source_type` values is three.

- [ ] **T054** **[US3]** – **Levene’s variance test (codegen vs. llama)**  
  *Extend `statistical_tests.py` to compute Levene’s test on each metric between `codegen` and `llama`. Record `levene_statistic`, `levene_p_value`, and `variance_exceeds_threshold` (true if absolute variance difference > 0.05).*  
  **Verification**: Results appended to `statistical_results.json`; CI asserts the boolean field exists.

- [ ] **T055** **[US3]** – **CPU‑only pipeline entry point**  
  *Create `code/run_cpu_pipeline.py` that orchestrates T052, T053a, T053b, and T054, detecting the presence of a GPU and forcing CPU execution.*  
  **Verification**: Running the script on the CI runner (CPU‑only) completes without OOM and produces the expected artefacts.

---

## Phase 6 – Final verification, bias analysis & hand‑off  

- [ ] **T061** **[US1]** – **Metric naming consistency audit**  
  *Search the codebase for any occurrence of `static_branch_count` or `branch_coverage` and replace with the canonical `branch_coverage_potential`. Update all JSON outputs and documentation.*  
  **Verification**: Grep returns zero matches; CI validates that the field name appears only as `branch_coverage_potential` in all schema‑validated files.

- [ ] **T062** **[US2]** – **Achieved power with confidence intervals**  
  *Enhance `statistical_tests.py` to compute 95 % CI for the observed effect size (using bootstrapping) and include it in `statistical_results.json`.*  
  **Verification**: CI fields `effect_size_ci_lower` and `effect_size_ci_upper` are present and lower ≤ upper.

- [ ] **T063** **[US3]** – **Bias (MCAR) analysis**  
  *Implement `code/bias_analysis.py` that runs Little’s MCAR test on task‑difficulty proxies (e.g., prompt length) comparing included vs. excluded tasks. Produce `data/analysis/bias_report.json` containing `mcar_test_p_value` and a `difficulty_comparison` object with means and p‑value.*  
  **Verification**: JSON validates against `statistical_results.schema.yaml`; a unit test confirms that a perfectly MCAR synthetic dataset yields a high p‑value.

- [ ] **T064** **[US3]** – **Dynamic vs. static coverage sanity test**  
  *Add an integration test `tests/integration/test_coverage_distinction.py` that runs `analyze_metrics.py` on a handcrafted sample containing a conditional branch. Assert that `dynamic_branch_coverage` ≠ `branch_coverage_potential`.*  
  **Verification**: Test passes, confirming that the pipeline truly measures dynamic coverage.

- [ ] **T070** **[Hand‑off]** – **Methods & results documentation**  
  *Write `docs/methods_and_results.md` summarizing the pipeline, datasets, models, statistical outcomes, and limitations. Link to artefacts via their SHA‑256 hashes (from `state/artifact_hashes.yaml`).*  
  **Verification**: File exists; all referenced hashes resolve to existing files.

- [ ] **T071** **[Hand‑off]** – **Re‑run full pipeline from scratch**  
  *Execute the top‑level command `bash run_all.sh` (generated in Phase 1) which sequentially runs T010 → T017a → T020 → T024 → T030 → T031 → T052 → T054 → T070. After completion, CI runs a final sanity check that `docs/report.md` and `docs/methods_and_results.md` are present and parsable.*  
  **Verification**: CI passes end‑to‑end run within the 6‑hour budget.

--- 

### Execution order summary
1. **Phase 1** (T001a‑T006) – must complete before any other task.  
2. **Phase 2** (T010‑T017b) – builds the full dataset and metrics.  
3. **Phase 3** (T020‑T027) – statistical comparison.  
4. **Phase 4** (T030‑T072) – reporting, validation, and SC‑004 measurement.  
5. **Phase 5** (T052‑T055) – CodeLlama sensitivity analysis.  
6. **Phase 6** (T061‑T071) – final audits, bias checks, and hand‑off.

All tasks are listed with explicit file paths, verification steps, and dependencies, satisfying the specification, contracts, and reviewer feedback.  