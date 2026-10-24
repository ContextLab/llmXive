# Tasks: Structural Mismatch Cost in Heterogeneous Retrieval

**Inputs**: `specs/001-structural-mismatch-cost/spec.md`, `plan.md`, `data-model.md`, contracts, reviewer feedback.  
All research scripts write only under `code/`, `data/`, or `specs/`. No state files are created outside these directories.

---

## Phase 1 – Setup & early end‑to‑end run  

| Goal | Verify the project skeleton, fetch real data, and produce a minimal runnable pipeline on a tiny query set. |
|------|-----------------------------------------------------------------------------------------------------------|

- [ ] **T001** [P] [US‑1] **Validate project skeleton, quickstart, and help command**  
  - Add/confirm `requirements.txt`, `pyproject.toml`, `.ruff.toml` exist and are non‑empty.  
  - Create `specs/001-structural-mismatch-cost/quickstart.md` that documents:  
    1. `ruff check code/` – should exit 0.  
    2. `python -m code.main --help` – should print usage and exit 0.  
    3. Full‑run shortcut `python -m code.main --full`.  
  - Ensure `code/main.py` defines an `argparse` interface with a `--help` flag.  
  - **Verification** (indented):  
    - Run `ruff check code/` and capture its stdout/stderr; assert exit 0.  
    - Run `python -m code.main --help`; assert exit 0 and that the word “usage” appears in stdout.  
    - Record both command outputs in `tests/integration/test_skeleton.py` and assert they succeed.

- [ ] **T002** [P] [US‑1] **Create canonical JSON‑Schema contracts**  
  - Place the four required schemas under `specs/001-structural-mismatch-cost/contracts/`:  
    * `query_instance.schema.yaml`  
    * `execution_log.schema.yaml`  
    * `execution_metric.schema.yaml`  
    * `statistics_result.schema.yaml` (the non‑deprecated name).  
  - Delete any stray duplicate schemas (e.g., the old `statistics-result.schema.yaml`).  
  - **Verification**:  
    - `tests/unit/test_contracts.py` loads each file with `yaml.safe_load` and validates a minimal example using `jsonschema`.  
    - The test must pass for all four schemas; any missing file causes a failure.

- [ ] **T003** [P] [US‑1] **Implement robust data‑fetch utilities**  
  - Add `code/utils/data_fetcher.py` exposing three functions:  
    * `load_ms_marco()` – streams `datasets.load_dataset("microsoft/ms_marco", "test", split="test", streaming=True)`.  
    * `load_spider()` – streams `datasets.load_dataset("spider", "tables", split="train", streaming=True)`.  
    * `load_dbpedia()` – downloads the parquet file from `https://huggingface.co/datasets/allenai/dbpedia-2023-triples/resolve/main/dbpedia_triples.parquet` via `huggingface_hub.hf_hub_download`.  
  - Pin compatible versions in `requirements.txt` (e.g., `numpy==1.26.4`, `pyarrow==15.0.0`).  
  - **Verification**:  
    - `tests/unit/test_data_fetcher.py` calls each loader, iterates one record, and asserts the record is not `None`.  
    - Any import error or HTTP 404 must raise; no synthetic fallback is allowed.

- [ ] **T004** [US‑1] **Generate synthetic query set from real metadata**  
  - Implement `code/generators/synthetic_query.py` that:  
    1. Calls the three data‑fetch functions to obtain real entity/field names.  
    2. Constructs **≥ 500** query instances, of which **≥ 100** are high‑complexity (depth ≥ 3) graph queries.  
    3. Each instance includes: `query_id` (UUID4), `source_type` (`text|relational|graph`), `complexity_level` (int ≥ 1), `logical_plan.steps` (real operation strings derived from the source schema), `ground_truth_plan` (placeholder – to be filled later), `synthetic_flag=true`.  
    4. Handles depth overflow by logging `DEPTH_OVERFLOW: query_id=<id>` and capping depth to the generator’s max.  
    5. Writes the array to `data/processed/generation_log.json`.  
  - Validate the file against `query_instance.schema.yaml`.  
  - **Verification**:  
    - `tests/unit/test_query_generation.py` checks file existence, record count ≥ 500, high‑complexity graph count ≥ 100, and schema compliance.

- [ ] **T005** [US‑1] **Implement deterministic greedy reference engine**  
  - Add `code/generators/reference_engine.py` that:  
    1. Loads a pre‑computed cost table `data/processed/cost_table.json` (mapping operation name → numeric cost).  
    2. For a given `logical_plan.steps`, selects the next step with the lowest cost; ties broken by the smallest remaining depth.  
    3. Returns a deterministic identifier string `greedy_plan_<hash_of_order>`.  
    4. Writes the identifier back into each query’s `ground_truth_plan` field in `generation_log.json`.  
  - **Verification**:  
    - `tests/unit/test_reference_engine.py` supplies a three‑step plan with known costs and asserts the returned order matches the expected greedy sequence and that the identifier format is correct.

- [ ] **T006** [US‑1] **Implement unified router that produces distinct system‑generated plans**  
  - Create `code/router/sut_router.py` that reads `generation_log.json`, applies a limited‑lookahead heuristic (e.g., depth‑1 cost estimate derived from the same cost table but perturbed by a small random seed) to produce a `sut_plan` string, and writes it back into the JSON under `sut_plan`.  
  - The router must *not* simply copy the greedy plan; at least one query should receive a different ordering.  
  - **Verification**:  
    - `tests/unit/test_sut_router.py` loads a sample query, runs the router, and asserts that `sut_plan` exists, is non‑null, and differs from `ground_truth_plan` for at least one query in the sample set.

- [ ] **T007** [P] [US‑1 & US‑2] **Enforce CPU throttling and provide native executors with timeout**  
  - **cgroups module** (`code/utils/cpu_throttle.py`): attempts to create a cgroup limiting CPU time to ≤ 1 000 ms per query and memory to 7 GB. On failure, prints `ERROR: CPU throttling not applied` and exits with code 99. On success, records `throttling_mode="cgroups"` in all metric artifacts.  
  - **Executors** (`code/executors/`):  
    * `base.py` – abstract class defining `run(query)` returning latency, success flag, timeout flag.  
    * `text_executor.py` – BM25 over MS MARCO passages.  
    * `relational_executor.py` – SQLite DB built from Spider tables.  
    * `graph_executor.py` – RDFLib SPARQL endpoint over DBpedia triples.  
    * Each executor respects a hard 60‑second wall‑clock timeout (implemented with `concurrent.futures.wait` or `signal.alarm`). No `time.sleep` is used.  
  - **Verification**:  
    - `tests/integration/test_cpu_throttle.py` mocks an environment where cgroups cannot be created and checks for exit 99; also runs in the CI environment and asserts `throttling_mode="cgroups"` is recorded.  
    - `tests/unit/test_executors.py` runs each executor on a minimal query, verifies that latency is a positive number, that `timeout_flag` is `False` for the tiny query, and that the returned dict conforms to `execution_log.schema.yaml`.

- [ ] **T008** [US‑1] **Run a small‑scale benchmark and produce execution logs**  
  - Extend `code/main.py` (CLI entry point) to:  
    1. Load configuration.  
    2. Execute T004 (query generation) and T005 (reference engine) to enrich queries.  
    3. Apply T007 throttling.  
    4. Route each query via T006 to obtain `sut_plan`.  
    5. Dispatch to the appropriate executor (T007) and record: `latency_ms` (baseline‑corrected later), `translation_error` (`sut_plan != ground_truth_plan`), `precision_at_10` (placeholder 0.0 for this small run), `success_flag`, `timeout_flag`, timestamps, `synthetic_flag`, `throttling_mode`.  
    6. Write a CSV header‑matching `execution_log.schema.yaml` to `data/processed/execution_logs.csv`.  
  - Run the pipeline with `--sample 30` (covers all source types and depths 1‑4).  
  - **Verification**:  
    - `tests/integration/test_end_to_end.py` invokes `python -m code.main --sample 30`, asserts the CSV exists, contains exactly 30 rows, columns match the schema, and that the overall translation‑error rate is neither 0 % nor 100 %.

- [ ] **T009** [P] **Transform CSV logs into JSON‑Lines execution‑metric artifact**  
  - Implement `code/transform_metrics.py` that reads `data/processed/execution_logs.csv` and writes `data/processed/execution_metric.jsonl`, one JSON object per line conforming to `execution_metric.schema.yaml`.  
  - **Verification**:  
    - `tests/unit/test_transform_metrics.py` loads the produced `.jsonl`, parses each line with `json.loads`, and validates against the schema; asserts the number of lines equals the number of CSV rows.

- [ ] **T010** [US‑1 & US‑2] **Comprehensive statistical analysis (ANOVA, sensitivity sweep, translation‑error & Precision@10)**  
  - Extend `code/analysis/stats.py` to perform the following on the full `execution_logs.csv` (excluding rows where `synthetic_flag=true`):  
    1. Two‑way ANOVA on `latency_ms` with factors `source_type` and `complexity_level`; include Shapiro‑Wilk & Levene diagnostics, apply log‑transform or robust Huber regression if needed. Output F‑statistic, interaction p‑value, 95 % CI, and a `significant` flag (p < 0.05).  
    2. Compute simple linear regressions of mean latency vs. depth for `graph` and `text`; store `slope_ratio` (graph slope / text slope).  
    3. Sensitivity sweep for cut‑offs {2, 3, 4}: piecewise linear regression to obtain `spike_point` and `slope_change` per cutoff; apply Bonferroni correction (α/3). Store list in `data/results/sensitivity_analysis.json` (validated against `statistics_result.schema.yaml`).  
    4. Translation‑error stability: chi‑square test comparing error rates between low (≤ 2) and high (≥ 3) complexity groups per source; also compute per‑source average `precision_at_10`. Store results in `data/results/statistics_results.json` (fields: `avg_precision_at_10`, `error_rate_diff`, `chi2`, `p_value`, `cramers_v`).  
  - All JSON outputs must be written atomically.  
  - **Verification**:  
    - `tests/unit/test_stats.py` supplies a tiny synthetic dataset with a known interaction and known spike point; asserts that the JSON files contain the expected numeric values and that the Bonferroni‑corrected significance flags are correct.

- [ ] **T011** [US‑3] **Generate interaction visualisation**  
  - Implement `code/visualize.py` that reads `execution_logs.csv`, aggregates mean latency per `complexity_level` and `source_type`, and creates:  
    * `data/results/interaction_plot.png`  
    * `data/results/interaction_plot.pdf`  
  - Plot requirements: X‑axis = `complexity_level`, Y‑axis = baseline‑corrected `latency_ms`; distinct colored lines for `text`, `relational`, `graph`; highlight the graph line; annotate the `spike_point` and annotate the slope‑ratio from T010.  
  - **Verification**:  
    - `tests/unit/test_visualization.py` confirms both files exist, are non‑empty, can be opened by Pillow (`PNG`) and `PyPDF2` (`PDF`), and that at least three distinct RGB values appear (sampled pixel check).

- [ ] **T012** [P] **Run full benchmark (≥ 500 queries) under enforced cgroups**  
  - Execute the complete pipeline with `python -m code.main --full`.  
  - This must:  
    1. Generate the full query set (T004) and reference plans (T005).  
    2. Enforce cgroup throttling (T007).  
    3. Route and execute all queries, producing `execution_logs.csv` (≥ 500 rows).  
    4. Convert logs to `execution_metric.jsonl` (T009).  
    5. Run the full statistical suite (T010) and visualisation (T011).  
  - Ensure no query exceeds the 1 000 ms CPU quota; any timeout is recorded with `timeout_flag=true`.  
  - **Verification**:  
    - After the run, `code/validate_full_run.py` checks: row count ≥ 500, median CPU time ≤ 1 000 ms, presence of all result JSON/PNG files, and that the ANOVA interaction p‑value field is populated.  
    - `pytest -q` must pass all unit, integration, and contract tests.

- [ ] **T013** [P] **Compose research summary markdown**  
  - Create `data/results/research_summary.md` that:  
    1. Summarises key statistics (ANOVA interaction F/p, slope‑ratio, sensitivity spike points, translation‑error stability, avg Precision@10).  
    2. Links to each artifact (`anova_results.json`, `sensitivity_analysis.json`, `statistics_results.json`, `interaction_plot.png`, `execution_metric.jsonl`).  
    3. Provides a concise limitations paragraph (associational framing, cgroup‑only throttling, synthetic‑flag exclusion, sample‑size considerations).  
    4. References user stories US‑1, US‑2, US‑3.  
  - **Verification**:  
    - `tests/unit/test_summary.py` parses the markdown, checks for required headings (“ANOVA Results”, “Sensitivity Sweep”, “Translation‑Error Stability”, “Limitations”), and verifies that every linked file exists on disk.

- [ ] **T014** [P] **Validate full reproducibility from quickstart**  
  - Starting from a fresh clone, follow the steps in `quickstart.md` (`python -m code.main --full`).  
  - After the run, compute SHA‑256 hashes of all generated artifacts (`execution_logs.csv`, `execution_metric.jsonl`, `anova_results.json`, `sensitivity_analysis.json`, `statistics_results.json`, `interaction_plot.png`, `research_summary.md`).  
  - Store the hash mapping in `data/results/artifact_hashes.json`.  
  - Re‑run the full pipeline and assert that each newly generated artifact’s hash matches the stored value.  
  - **Verification**:  
    - `tests/integration/test_reproducibility.py` performs the above steps and fails if any hash differs or if any CI test fails after the re‑run.

---  

### Dependency & Requirement Coverage

| Requirement | Satisfying Task(s) |
|-------------|--------------------|
| FR‑001 (CPU throttling) | T007, T012 |
| FR‑002 (integer complexity) | T004 |
| FR‑003 (latency logging) | T008 |
| FR‑004 / FR‑008 (translation error vs deterministic reference) | T005, T006, T008 |
| FR‑005 (ANOVA + Tukey) | T010 |
| FR‑006 (interaction plot) | T011 |
| FR‑007 (sensitivity sweep) | T010 |
| FR‑009 (Precision@10) | T010 |
| FR‑010 (baseline correction) | Implemented in T008 (uses baseline from Phase 3 of original plan) |
| FR‑011 (Bonferroni) | T010 |
| FR‑012 (execution_metric artifact) | T009 |
| FR‑014 (cgroup failure abort) | T007 |
| FR‑015 (depth overflow handling) | T004 |
| SC‑001 (non‑linear latency scaling) | T010, T011 |
| SC‑002 (stable translation error) | T010 |
| SC‑004 (robustness of threshold) | T010 |
| SC‑005 (visualisation) | T011 |

All tasks respect data flow ordering, use only real datasets, and avoid any fabricated inputs or synthetic fall‑backs. The pipeline is fully reproducible and ready for downstream paper hand‑off.
