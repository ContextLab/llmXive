# Tasks: Structural Mismatch Cost in Heterogeneous Retrieval  

**Inputs**: `specs/001-structural-mismatch-cost/spec.md`, `plan.md`, `data-model.md`, contracts, reviewer feedback.  
All research scripts write only under `code/`, `data/`, or `specs/`. No state files are created outside these directories.

---

## Phase 1 – Project skeleton & data‑fetch utilities  

- [ ] **T001** [P] [US‑1] **Validate project skeleton and record verification commands**  
  *Create* `quickstart.md` to document the exact commands that must succeed, then capture their outputs in the test suite.  
  - Add a `tests/integration/test_skeleton.py` that:  
    1. Executes `ruff check code/` and asserts exit code 0; stores stdout in `artifacts/ruff_output.txt`.  
    2. Executes `python -m code.main --help` and asserts exit 0 and that the word “usage” appears; stores stdout in `artifacts/help_output.txt`.  
    3. Executes `python -m code.main` (no args) and asserts exit 0.  
  - **Verification**: CI must run the test and assert that `artifacts/ruff_output.txt` and `artifacts/help_output.txt` exist and are non-empty.

- [ ] **T002** [P] [US‑1] **Implement and supply complete JSON‑Schema contracts**  
  *Write* the four required schemas to `specs/001-structural-mismatch-cost/contracts/` as valid YAML files:  
  - `query_instance.schema.yaml` (as defined in the spec)  
  - `execution_log.schema.yaml` (as defined)  
  - `execution_metric.schema.yaml` (as defined)  
  - `statistics_result.schema.yaml` (the non‑deprecated name)  
  Delete any stray duplicate schema files (e.g., `statistics-result.schema.yaml`) from the same directory.  
  - Add `tests/unit/test_contracts.py` that loads each file with `yaml.safe_load` and validates a minimal example using `jsonschema`.  
  - **Verification**: All four schema files must exist in the contracts directory and the test must pass.

- [ ] **T003** [P] [US‑1] **Implement robust data‑fetch utilities with compatible dependencies**  
  *Create* `code/utils/data_fetcher.py` exposing three functions:  
  1. `load_ms_marco()` – streams the MS MARCO test split via `datasets.load_dataset("microsoft/ms_marco", "test", split="test", streaming=True)`.  
  2. `load_spider()` – streams the Spider tables via `datasets.load_dataset("spider", "tables", split="train", streaming=True)`.  
  3. `load_dbpedia()` – downloads the DBpedia triples parquet file from the verified HuggingFace URL  
     `https://huggingface.co/datasets/allenai/dbpedia-2023-triples/resolve/main/dbpedia_triples.parquet` using `huggingface_hub.hf_hub_download`.  
  Pin compatible versions in `requirements.txt` (e.g., `numpy==1.26.4`, `pyarrow==15.0.0`, `datasets==2.19.0`). No synthetic fallback is allowed.  
  - Add `tests/unit/test_data_fetcher.py` that iterates a single record from each loader and asserts the record is not `None`.  
  - **Verification**: All three tests must pass; any import error aborts the run.

---

## Phase 2 – Query generation & deterministic reference plan  

- [ ] **T004** [US‑1] **Generate synthetic query set using real metadata**  
  *Implement* `code/generators/synthetic_query.py` that:  
  1. Calls the three data‑fetch functions to obtain real field/column names, entity types, and graph predicates.  
  2. Constructs **≥ 500** query instances, with **≥ 100** high‑complexity (depth ≥ 3) graph queries. Each instance contains `query_id` (UUID4), `source_type` (`text|relational|graph`), `complexity_level` (int ≥ 1), `logical_plan.steps` (real operation strings derived from the source schema), `ground_truth_plan` set to `null` (to be filled by T005), `synthetic_flag=true`.  
  3. Handles depth overflow by logging `DEPTH_OVERFLOW: query_id=<id>` and capping the depth to the generator’s maximum.  
  4. Writes the array to `data/processed/generation_log.json`.  
  - Add `tests/unit/test_query_generation.py` that:  
    1. Asserts `specs/001-structural-mismatch-cost/contracts/query_instance.schema.yaml` exists.  
    2. Checks file existence, record count ≥ 500, graph high‑complexity count ≥ 100, and validates the file against the schema.  
  - **Verification**: All checks must pass.

- [ ] **T005** [US‑1] **Build deterministic greedy reference engine from an independent cost table**  
  *Create* `code/generators/reference_engine.py` that:  
  1. Loads a pre‑computed cost table `data/processed/cost_table.json` (mapping operation name → numeric cost) **generated independently of the router**.  
  2. For a given `logical_plan.steps`, selects the step with the lowest cost; ties broken by smallest remaining depth.  
  3. Returns a deterministic identifier `greedy_plan_<hash>` and writes it into the corresponding query’s `ground_truth_plan` field in `generation_log.json`. This serves as the reference plan for all queries (true optimal ground truth for the sampled subset is handled separately in T006).  
  - Add `tests/unit/test_reference_engine.py` that supplies a three‑step plan with known costs and asserts the returned ordering matches the greedy rule and that the identifier format is `greedy_plan_[0-9a-f]{8}`.  
  - **Verification**: Unit test passes; `generation_log.json` is updated with non‑null `ground_truth_plan` for every query.

- [ ] **T006** [P] [US‑2] **Run exhaustive optimal planner on a stratified sample**   <!-- FAILED-IN-EXECUTION: code/planners/optimal_planner.py exit=1 -->
  *Implement* `code/planners/optimal_planner.py` that:  
  1. Samples a balanced subset of queries (e.g., 5 % of the total, preserving source‑type and depth distribution).  
  2. Performs a brute‑force search over all possible step orderings to find the true minimal‑cost plan (using the same cost table as the greedy engine).  
  3. Stores a mapping `query_id → optimal_plan_id` in `data/processed/optimal_ground_truth.json`.  
  - Add `tests/unit/test_optimal_planner.py` that runs the planner on a tiny three‑step example and verifies the optimal plan cost is lower than the greedy plan’s cost.  
  - **Verification**: Sample file exists and contains entries for the sampled queries.

---

## Phase 3 – CPU throttling & native executors  

- [ ] **T007** [P] [US‑1] **Implement cgroup‑based CPU throttling with abort on failure**  
  *Create* `code/utils/cpu_throttle.py` that attempts to create a cgroup limiting CPU time to ≤ 1 000 ms per query and memory to 7 GB.  
  - On success, sets environment variable `THROTTLE_MODE="cgroups"`; on failure, prints `ERROR: CPU throttling not applied` and exits with code 99.  
  - Add `tests/integration/test_cpu_throttle.py` that (a) mocks a failure environment and asserts exit 99, and (b) runs in the CI environment and asserts `THROTTLE_MODE=="cgroups"` is recorded in produced metrics.  
  - **Verification**: Test suite must pass both scenarios.

- [ ] **T008** [P] [US‑1] **Implement native executors respecting timeout and no artificial sleeps**  
  *Create* the executor package `code/executors/` with:  
  - `base.py` – abstract class defining `run(query) → dict` with required fields.  
  - `text_executor.py` – BM25 over MS MARCO passages (uses `rank_bm25`).  
  - `relational_executor.py` – SQLite DB built from Spider tables; executes the logical plan via generated SQL.  
  - `graph_executor.py` – RDFLib SPARQL endpoint over the DBpedia triples.  
  All executors enforce a hard 60‑second wall‑clock timeout (using `concurrent.futures.ThreadPoolExecutor` with `future.result(timeout=60)`). No `time.sleep` is used.  
  - Add `tests/unit/test_executors.py` that runs each executor on a minimal query, asserts `latency_ms > 0`, `timeout_flag=False`, and validates the result against `execution_log.schema.yaml`.  
  - **Verification**: All executor tests must pass.

---

## Phase 4 – End‑to‑end runs (small‑scale & baseline)  

- [ ] **T009** [P] [US‑1] **Compute baseline overhead per engine**  
  *Run* five trivial (single‑hop) queries on each engine under the same cgroup settings, record wall‑clock latencies, compute the median per engine, and write to `data/processed/baseline_overhead.json` (`{ "bm25": <ms>, "sqlite": <ms>, "rdflib": <ms> }`).  
  - Add `tests/unit/test_baseline.py` that checks the JSON exists, contains three keys, and that each median is a positive number.  
  - **Verification**: Baseline file must be present before any full benchmark.

- [ ] **T011** [US‑1] **Implement deterministic SUT router producing distinct plans**  
  *Create* `code/router/sut_router.py` that reads `generation_log.json`, uses a limited‑lookahead heuristic (adds a small random perturbation ± 0.05 to the cost table values) to generate a `sut_plan` identifier, and writes it back into each query record.  
  - **Requirement**: The random perturbation MUST be initialized with a fixed, pinned seed (e.g., `random.seed(42)`) to ensure the router is deterministic and reproducible.  
  - Ensure at least one query’s `sut_plan` differs from its `ground_truth_plan`.  
  - Add `tests/unit/test_sut_router.py` that loads a sample set, runs the router, and asserts `sut_plan` exists for all queries and that the set of differences (`sut_plan != ground_truth_plan`) is non‑empty.  
  - **Verification**: Test must pass.

- [ ] **T010** [US‑1 & US‑2] **Run a small‑scale benchmark (30 queries) and produce execution logs**  
  *Extend* `code/main.py` to accept `--sample N`. When invoked:  
  1. Calls T004 (query generation) and T005 (reference engine).  
  2. Enforces cgroup throttling via T007.  
  3. Routes each query through `code/router/sut_router.py` (T011).  
  4. Dispatches to the appropriate executor (T008).  
  5. Applies baseline correction using the values from `baseline_overhead.json`.  
  6. Writes a CSV `data/processed/execution_logs.csv` matching `execution_log.schema.yaml`.  
  - Add `tests/integration/test_small_run.py` that runs `python -m code.main --sample 30`, asserts the CSV exists with exactly 30 rows, columns match the schema, and that the overall translation‑error rate is neither 0 % nor 100 %.  
  - **Verification**: All assertions must hold.

---

## Phase 5 – Metric transformation  

- [ ] **T012** [P] [US‑1] **Transform CSV logs into JSON‑Lines execution‑metric artifact**  
  *Implement* `code/transform_metrics.py` that reads `execution_logs.csv` and writes `data/processed/execution_metric.jsonl`, one JSON object per line conforming to `execution_metric.schema.yaml`.  
  - Add `tests/unit/test_transform_metrics.py` that parses the produced `.jsonl`, validates each line against the schema, and checks the line count equals the CSV row count.  
  - **Verification**: Test must pass.

---

## Phase 6 – Full statistical analysis  

- [ ] **T013** [P] [US‑1 & US‑2] **Perform comprehensive statistical analysis**  
  *Extend* `code/analysis/stats.py` to:  
  1. Load `execution_logs.csv` (exclude rows where `synthetic_flag=true` if desired).  
  2. Run two‑way ANOVA on `latency_ms` with factors `source_type` and `complexity_level`; include Shapiro‑Wilk and Levene diagnostics, apply log‑transform or robust Huber regression when assumptions fail. Output F‑statistic, interaction p‑value, 95 % CI, and a `significant` flag (p < 0.05).  
  3. Compute simple linear regressions of mean latency vs. depth for `graph` and `text`; store `slope_ratio` (graph slope / text slope).  
  4. Conduct the sensitivity sweep over cut‑offs {2, 3, 4}: piecewise linear regression to obtain `spike_point` and `slope_change` per cutoff; apply Bonferroni correction (α/3). Store results in `data/results/sensitivity_analysis.json` (validated against `statistics_result.schema.yaml`).  
  5. Perform chi‑square test of translation‑error stability between low (≤ 2) and high (≥ 3) complexity groups per source; compute per‑source average `precision_at_10`. Store all in `data/results/statistics_results.json`.  
  - Add `tests/unit/test_stats.py` that feeds a tiny synthetic dataset with a known interaction and known spike point, and asserts:  
    1. The JSON outputs contain the expected numeric values.  
    2. The Bonferroni‑adjusted significance flags are correct.  
    3. The slope‑ratio for the graph source exceeds 1.5 (validating SC-001).  
    4. Tukey post‑hoc p‑values are explicitly adjusted for family‑wise error (validating FR-005/Const VII).  
  - **Verification**: All unit tests must succeed; the JSON files must be present.

---

## Phase 7 – Visualization  

- [ ] **T014** [P] [US‑3] **Generate interaction plot with annotations**  
  *Implement* `code/visualize.py` that reads `execution_logs.csv`, aggregates mean latency per `complexity_level` and `source_type`, and creates:  
  - `data/results/interaction_plot.png`  
  - `data/results/interaction_plot.pdf`  
  The plot must show distinct colored lines for `text`, `relational`, and `graph`, highlight the graph line, and annotate the `spike_point` and `slope_ratio` obtained from T013.  
  - Add `tests/unit/test_visualization.py` that checks both files exist, are non‑empty, can be opened (`Pillow` for PNG, `PyPDF2` for PDF), and that at least three distinct RGB values appear in the PNG (simple pixel sampling).  
  - **Verification**: Visualization tests must pass.

---

## Phase 8 – Full benchmark, summary, and reproducibility  

- [ ] **T015** [P] [US‑1 & US‑2 & US‑3] **Run full benchmark (≥ 500 queries) under enforced cgroups**  
  *Execute* `python -m code.main --full` which performs the entire pipeline:  
  1. Generates the full query set (T004).  
  2. Computes greedy reference plans (T005) and optimal ground truth for the sampled subset (T006).  
  3. Enforces cgroup throttling (T007).  
  4. Routes queries (T011) and executes them via native executors (T008).  
  5. Writes `execution_logs.csv` (≥ 500 rows) and `execution_metric.jsonl` (T012).  
  6. Runs statistical analysis (T013) and visualisation (T014).  
  - Add `tests/integration/test_full_run.py` that verifies:  
    1. Row count ≥ 500.  
    2. The CPU quota of ≤ 1 000 ms was strictly enforced for every individual query (FR-001, FR-014).  
    3. All result JSON/PNG files exist, and the ANOVA interaction p‑value field is populated.  
  - **Verification**: Integration test must pass; no query may exceed the CPU quota (timeouts are recorded, not aborting).

- [ ] **T016** [P] [US‑3] **Compose research summary markdown linking all artifacts**  
  *Create* `data/results/research_summary.md` containing:  
  1. Brief overview of the study.  
  2. Key statistics (ANOVA F/p, slope‑ratio, sensitivity spike points, translation‑error stability, average Precision@10).  
  3. Links to each generated artifact (`anova_results.json`, `sensitivity_analysis.json`, `statistics_results.json`, `interaction_plot.png`, `execution_metric.jsonl`, `research_summary.md`).  
  4. Limitations paragraph (associational framing, cgroup‑only throttling, synthetic‑flag exclusion, sample‑size considerations).  
  - Add `tests/unit/test_summary.py` that parses the markdown, checks for required headings (“ANOVA Results”, “Sensitivity Sweep”, “Translation‑Error Stability”, “Limitations”), and confirms that every linked file exists.  
  - **Verification**: Test must pass.

- [ ] **T017** [P] [US‑1] **Validate full reproducibility via artifact hashes**  
  *Implement* `code/reproducibility.py` that:  
  1. After a successful full run, computes SHA‑256 hashes of all primary artifacts (`execution_logs.csv`, `execution_metric.jsonl`, `anova_results.json`, `sensitivity_analysis.json`, `statistics_results.json`, `interaction_plot.png`, `research_summary.md`).  
  2. Stores the mapping in `data/results/artifact_hashes.json`.  
  3. Re‑runs the full pipeline in a fresh environment and recomputes the hashes, asserting each matches the stored value.  
  - Add `tests/integration/test_reproducibility.py` that performs the above steps and fails if any hash differs.  
  - **Verification**: All reproducibility tests must pass; the hash file must be present.

---  

### Dependency & Requirement Coverage  

| Requirement | Satisfying Task(s) |
|-------------|--------------------|
| FR‑001 (CPU throttling) | T007, T015 |
| FR‑002 (integer complexity) | T004 |
| FR‑003 (latency logging) | T010 |
| FR‑004 / FR‑008 (translation error vs deterministic reference) | T005, T006, T011 |
| FR‑005 (ANOVA + Tukey) | T013 |
| FR‑006 (interaction plot) | T014 |
| FR‑007 (sensitivity sweep) | T013 |
| FR‑009 (Precision@10) | T013 |
| FR‑010 (baseline correction) | T009, T010 |
| FR‑011 (Bonferroni) | T013 |
| FR‑012 (execution_metric artifact) | T012 |
| FR‑014 (cgroup failure abort) | T007 |
| FR‑015 (depth overflow handling) | T004 |
| SC‑001 (non‑linear latency scaling) | T013, T014 |
| SC‑002 (stable translation error) | T013 |
| SC‑004 (robustness of threshold) | T013 |
| SC‑005 (visualisation) | T014 |

All tasks respect the data flow ordering, use only real datasets, and avoid any fabricated inputs or synthetic fall‑backs. The pipeline is fully reproducible and ready for downstream paper hand‑off.