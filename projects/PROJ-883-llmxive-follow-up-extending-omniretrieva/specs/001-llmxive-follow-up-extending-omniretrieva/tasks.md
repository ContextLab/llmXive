# Tasks: Structural Mismatch Cost in Heterogeneous Retrieval

**Inputs**: `specs/001-structural-mismatch-cost/spec.md`, `plan.md`, `data-model.md`, contracts, reviewer feedback.  
All research scripts write only under `code/`, `data/`, or `specs/`. No state files are created outside these directories.

---

## Phase 1 – Setup & first end‑to‑end analysis  

| Goal | Run an executable, fully‑real end‑to‑end pipeline on a small, verified input set. |
|------|-----------------------------------------------------------------------------------|

- [ ] **T001** [P] **Validate project skeleton & quickstart**  
  - Ensure `code/` package, `requirements.txt`, `pyproject.toml`, `.ruff.toml` exist and are non‑empty.  
  - Add a `quickstart.md` in `specs/001-structural-mismatch-cost/` describing the command `python -m code.main --help`.  
  - **Verification**:  
    1. Run `ruff check code/`; exit code 0.  
    2. Run `python -m code.main --help`; exit code 0 and help text printed.  
    3. Record both command outputs in `tests/integration/test_skeleton.py` and assert they succeed.

- [ ] **T002** [P] **Create and validate required JSON‑Schema contracts**  
  - Add the four canonical schemas under `specs/001-structural-mismatch-cost/contracts/`: `query_instance.schema.yaml`, `execution_log.schema.yaml`, `execution_metric.schema.yaml`, `statistics_result.schema.yaml`.  
  - Remove any deprecated duplicate schemas from the repository.  
  - **Verification**: `tests/unit/test_contracts.py` loads each file with `yaml.safe_load` and validates a minimal example against it using `jsonschema`. All tests must pass.

- [ ] **T003** [P] **Implement reliable data‑fetch utilities**  
  - `code/utils/data_fetcher.py` must provide three functions: `load_ms_marco()`, `load_spider()`, `load_dbpedia()`.  
  - Use `datasets.load_dataset(..., streaming=True)` for MS MARCO and Spider, pin compatible versions (`numpy>=1.26.0,<2.0.0`, `pyarrow==15.0.0`).  
  - Download DBpedia triples from a real URL (e.g., `https://huggingface.co/datasets/allenai/dbpedia-2023-triples/resolve/main/dbpedia_triples.parquet`).  
  - **Verification**: `tests/unit/test_data_fetcher.py` calls each loader, fetches at least one record, and asserts the result is non‑empty. Any failure must raise, never fall back to synthetic data.

- [ ] **T004** [US-1] **Generate synthetic query set using real metadata**  
  - `code/generators/synthetic_query.py` reads the real metadata produced by T003 and creates **≥ 500** query instances, of which **≥ 100** are high‑complexity (depth ≥ 3) graph queries.  
  - Each instance includes `query_id` (UUID), `source_type` (`text|relational|graph`), `complexity_level` (integer ≥ 1), `logical_plan.steps` (real operation names derived from the source schema), `ground_truth_plan` (populated later), and `synthetic_flag=true`.  
  - Depth overflow (depth > generator max) must log `DEPTH_OVERFLOW: query_id=<id>` and cap or drop the query.  
  - Persist to `data/processed/generation_log.json` and validate against `query_instance.schema.yaml`.  
  - **Verification**: `tests/unit/test_query_generation.py` checks file existence, record count, presence of ≥ 100 high‑complexity graph queries, and schema compliance.

- [ ] **T005** [US-1] **Implement deterministic greedy reference engine (ground‑truth for non‑optimal subset)**  
  - `code/generators/reference_engine.py` loads a **pre‑computed cost table** (`data/processed/cost_table.json`) that maps each operation type to an estimated cost independent of the router’s model.  
  - For a given `logical_plan.steps`, it selects the next step with the lowest cost (tie‑break by shortest remaining depth) and returns a deterministic plan identifier string (e.g., `greedy_plan_<hash>`).  
  - **Verification**: `tests/unit/test_reference_engine.py` supplies a three‑step plan with known costs and asserts the returned order matches the expected greedy sequence.

- [ ] **T006** [US-1] **Implement unified router producing system‑generated plans (`sut_plan`)**  
  - `code/router/sut_router.py` reads each query from `generation_log.json`, applies a limited‑lookahead heuristic (depth‑1 cost estimate) to produce a `sut_plan` string, and writes it back into the same JSON file under the key `sut_plan`.  
  - The router must *not* simply copy the greedy plan; it should be a distinct algorithmic choice.  
  - **Verification**: `tests/unit/test_sut_router.py` loads a sample query, runs the router, and asserts that `sut_plan` is present, non‑null, and differs from the greedy plan for at least one query.

- [ ] **T007** [US-1] **Enforce CPU throttling via cgroups**  
  - `code/utils/cpu_throttle.py` attempts to create a cgroup limiting CPU time to **≤ 1 000 ms** per query and memory to **7 GB**.  
  - If cgroup creation fails (e.g., insufficient permissions), the process must abort with **exit code 99** and emit `ERROR: CPU throttling not applied`.  
  - Record `throttling_mode="cgroups"` in all metric artifacts.  
  - **Verification**: `tests/integration/test_cpu_throttle.py` runs the throttling function in an environment where cgroups are unavailable (mocked) and checks for exit 99; also runs in a normal CI environment and asserts the mode is `"cgroups"`.

- [ ] **T008** [US-2] **Implement native executors with 60‑second wall‑clock timeout**  
  - Create `code/executors/base.py` (abstract executor) and concrete subclasses:  
    - `text_executor.py` → BM25 over MS MARCO passages.  
    - `relational_executor.py` → SQLite DB built from Spider schemas.  
    - `graph_executor.py` → RDFLib SPARQL endpoint over the DBpedia triples.  
  - Each executor must measure real wall‑clock latency, enforce a **60 s timeout** (mark `timeout_flag=true` on expiry), and never use `time.sleep` for artificial delay.  
  - **Verification**: `tests/unit/test_executors.py` runs each executor on a tiny query, checks that latency is recorded, timeout flag behaves correctly, and that the returned schema matches `execution_log.schema.yaml`.

- [ ] **T009** [US-1 & US‑2] **Orchestrate small‑scale benchmark and record execution logs**  
  - `code/main.py` must:  
    1. Load configuration.  
    2. Run T004 (query generation) and T005 (reference engine) to enrich queries with `ground_truth_plan`.  
    3. Apply T007 throttling.  
    4. Route each query through T006 router to obtain `sut_plan`.  
    5. Dispatch to the appropriate executor (T008).  
    6. Compute `translation_error = (sut_plan != ground_truth_plan)`.  
    7. Record all fields required by `execution_log.schema.yaml` (including `timestamp`, `success_flag`, `synthetic_flag`, `throttling_mode`).  
    8. Write **`data/processed/execution_logs.csv`** (header order matches the schema).  
  - Run a **sample batch of ≥ 30 real queries** (covering all source types and depths 1‑4) to verify end‑to‑end execution.  
  - **Verification**: `tests/integration/test_end_to_end.py` executes `python -m code.main --sample 30`, asserts the CSV exists, contains the correct columns, passes schema validation, and that the overall translation‑error rate is neither 0 % nor 100 %.

- [ ] **T010** [P] **Transform CSV to JSON‑Lines execution metric artifact**  
  - `code/transform_metrics.py` reads `execution_logs.csv` and writes `data/processed/execution_metric.jsonl`, each line conforming to `execution_metric.schema.yaml`.  
  - Include fields: `query_id`, `latency_ms`, `translation_error`, `precision_at_10` (computed later by the router), `timeout_flag`, `success_flag`, `timestamp`, `synthetic_flag`, `throttling_mode`.  
  - **Verification**: `tests/unit/test_transform_metrics.py` validates that every line is JSON‑parsable and passes schema validation.

---

## Phase 2 – Complete study & validation  

| Goal | Produce statistically sound evidence and visualisations. |
|------|--------------------------------------------------------|

- [ ] **T011** [US-1] **Two‑way ANOVA with diagnostics, post‑hoc Tukey, and slope‑ratio**  
  - `code/analysis/stats.py` reads `execution_logs.csv` (excluding rows where `synthetic_flag=true`).  
  - Performs:  
    1. Two‑way ANOVA (`latency_ms ~ C(complexity_level) * C(source_type)`).  
    2. Shapiro‑Wilk & Levene tests; if assumptions fail, apply log‑transform or robust Huber regression.  
    3. Extract interaction F‑statistic, p‑value, 95 % CI, and flag `significant` if p < 0.05.  
    4. Compute simple linear regressions of mean latency vs. depth for `graph` and `text`; store `slope_ratio` (graph slope / text slope).  
    5. Run Tukey HSD for all pairwise source‑type contrasts.  
  - Output JSON to `data/results/anova_results.json`.  
  - **Verification**: `tests/unit/test_anova.py` runs the analysis on a tiny synthetic dataset with a known interaction, asserts that the interaction is detected (p < 0.05), and that the JSON contains the required fields.

- [ ] **T012** [US-1] **Sensitivity sweep over complexity cut‑offs (2, 3, 4) with Bonferroni correction**  
  - Extend `stats.py` to: for each cutoff, fit piecewise linear regression on mean latency per depth, compute `spike_point` (depth with maximal absolute latency jump) and `slope_change` (difference between slopes above vs. below the spike).  
  - Apply Bonferroni correction across the three cut‑offs (α / 3).  
  - Store results list in `data/results/sensitivity_analysis.json`, validated against `statistics_result.schema.yaml`.  
  - **Verification**: `tests/unit/test_sensitivity.py` supplies a handcrafted piecewise‑linear series and checks that the recovered `spike_point` and `slope_change` match expectations.

- [ ] **T013** [US-2] **Translation‑error stability & Precision@10 analysis**  
  - `stats.py` also:  
    1. Compute per‑source average `precision_at_10` (using relevance sets derived from the ground‑truth plan).  
    2. Perform a chi‑square (or Fisher’s exact) test comparing `translation_error` rates between low (complexity ≤ 2) and high (complexity ≥ 3) groups, and specifically for the high‑complexity graph subset.  
    3. Record `avg_precision_at_10` per source, absolute error‑rate differences, χ², p‑value, and Cramér’s V.  
  - Write two JSON files: `data/results/translation_error_summary.json` and `data/results/statistics_results.json`.  
  - **Verification**: `tests/unit/test_translation_error.py` validates that both files exist, contain the required keys, and that the reported differences respect SC‑002 (≤ 0.02).

- [ ] **T014** [US-3] **Generate interaction visualisation**  
  - `code/visualize.py` reads `execution_logs.csv` and creates `data/results/interaction_plot.png` and `data/results/interaction_plot.pdf`.  
  - Plot requirements: X‑axis = `complexity_level`, Y‑axis = baseline‑corrected `latency_ms`; separate colored lines for `text`, `relational`, `graph`; highlight the graph line; annotate the `spike_point` and slope‑difference from T012.  
  - **Verification**: `tests/unit/test_visualization.py` checks that both files are non‑empty, that the PNG can be opened by Pillow, and that at least three distinct colors are present (by sampling pixel values).

- [ ] **T015** [P] **Run full benchmark (≥ 500 queries) under enforced cgroups**  
  - Execute the full pipeline (`python -m code.main --full`) producing:  
    - `data/processed/execution_logs.csv` (full run)  
    - `data/processed/execution_metric.jsonl`  
    - All JSON results from T011‑T014 and the interaction plot.  
  - Ensure the run respects the CPU quota (no query exceeds 1 000 ms CPU time) and that any timeout is recorded correctly.  
  - **Verification**: After the run, `pytest -q` must pass all unit, integration, and contract tests; additionally, a sanity script `code/validate_full_run.py` checks that the number of rows in the CSV ≥ 500 and that the interaction p‑value is present.

---

## Phase 3 – Reproducible results & paper hand‑off  

| Goal | Produce a concise, reproducible research package for downstream paper writing. |
|------|--------------------------------------------------------------------------------|

- [ ] **T016** [P] **Compose research summary markdown**  
  - `data/results/research_summary.md` must:  
    1. Summarise the ANOVA interaction statistics, slope‑ratio, translation‑error stability, precision@10 results, and sensitivity sweep outcomes.  
    2. Include direct links to each JSON/PNG artifact (relative paths).  
    3. Provide a limitations paragraph (associational framing, cgroup‑only throttling, synthetic‑flag exclusions, sample‑size considerations).  
    4. Cite the relevant user stories (US‑1, US‑2, US‑3).  
  - **Verification**: `tests/unit/test_summary.py` parses the markdown, checks that every required heading appears, and that each linked file exists.

- [ ] **T017** [P] **Validate full reproducibility from quickstart**  
  - Starting from a fresh clone, run the commands documented in `quickstart.md` (`python -m code.main --full`) without manually editing any files.  
  - Verify that all artifacts (`execution_logs.csv`, JSON results, plot, summary) are regenerated identically (hashes match the committed versions).  
  - Record the outcome in `tests/integration/test_reproducibility.py`.  
  - **Verification**: The test must assert that the hash of each generated file equals the hash stored in `data/results/artifact_hashes.json` and that all CI tests still pass.

--- 

### Dependency & Requirement Coverage

| Requirement | Satisfying Task(s) |
|-------------|--------------------|
| FR‑001 (CPU throttling) | T007, T015 |
| FR‑002 (integer complexity) | T004 |
| FR‑003 (latency JSON/CSV) | T009, T010 |
| FR‑004 / FR‑008 (translation error vs deterministic reference) | T005, T006, T009 |
| FR‑005 (ANOVA + Tukey) | T011 |
| FR‑006 (interaction plot) | T014 |
| FR‑007 (sensitivity sweep) | T012 |
| FR‑009 (Precision@10) | T013 |
| FR‑010 (baseline correction) | Implemented in T009 (uses baseline from Phase 3 of plan) |
| FR‑011 (Bonferroni) | T012 |
| FR‑012 (execution_metric artifact) | T010 |
| FR‑014 (cgroup failure abort) | T007 |
| FR‑015 (depth overflow handling) | T004 |
| SC‑001 (non‑linear latency scaling) | T011, T014 |
| SC‑002 (stable translation error) | T013 |
| SC‑004 (robustness of threshold) | T012 |
| SC‑005 (visualisation) | T014 |

All tasks are ordered to respect data flow: schema creation → data fetch → query generation → reference engine → router → throttling → executors → logging → transformation → statistical analysis → visualisation → full run → summary → reproducibility.
