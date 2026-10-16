# Tasks: Exploring the Role of Network Structure in Superconducting Qubit Coupling

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts in `specs/001‑exploring‑network‑structure/contracts/`  

The list below consolidates the previously rejected and pending work into a minimal, executable research plan that satisfies **all** functional requirements (FR‑001 – FR‑004), user stories (US1 – US3), and non‑functional constraints (CPU‑only, no synthetic data).  
Each task is a self‑contained, verifiable unit; completed tasks are checked, pending tasks are unchecked.  Indented lines describe the artifact paths, verification commands, and any special notes.

---

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Run a reproducible pipeline on real IBM Quantum calibration data from a single snapshot (cross‑sectional design).

- [ ] T001 [US1] **Fetch calibration data with freshness enforcement and no synthetic fallback**  
  *Implementation*: `code/fetcher.py` providing  
  • `fetch_backends_list()` – obtains public backend list via `IBMQ` provider.  
  • `fetch_backend_properties(name)` – downloads `properties` JSON, respects **C‑001** (exponential backoff, max 5 attempts).  
  • `validate_data_freshness(timestamp)` – excludes snapshots older than 30 days (FR‑001).  
  • `extract_performance_metrics(json)` – returns `t1_mean`, `t2_mean`, `cx_error_mean`, `readout_error_mean`, `chip_family`.  
  *Artifacts*: `data/raw/{device_id}_{YYYYMMDD_HHMMSS}.json` (raw JSON snapshots).  
  *Verification*:  
  ```bash
  pytest code/tests/test_fetcher.py -q   # schema validation, backoff, freshness, no‑synthetic‑fallback guard
  python -c "import code.fetcher as f; f.main()"   # writes at least one JSON file
  ```

- [ ] T002 [US1] **Produce `performance_metrics.csv` from the raw snapshots**  
  *Implementation*: Extend `code/fetcher.py` (or add `code/process_raw.py`) to iterate over `data/raw/*.json`, compute per‑device averages, and write `data/processed/performance_metrics.csv`.  
  *Schema*: Validate each row against `specs/001‑exploring‑network‑structure/contracts/performance_metrics.schema.yaml`.  
  *Artifacts*: `data/processed/performance_metrics.csv`.  
  *Verification*:  
  ```bash
  pytest code/tests/test_processed_perf.py -q   # CSV exists, non‑empty, schema‑valid, no NaN/Inf
  head data/processed/performance_metrics.csv
  ```

- [ ] T003 [US2] **Build undirected coupling graphs and compute topological metrics**  
  *Implementation*: `code/graph_builder.py` with CLI  
  ```bash
  python -m code.graph_builder --raw-dir data/raw --out data/processed/graph_metrics.csv
  ```  
  (CLI also accepts the legacy alias `--output`.)  
  Features:  
  • `build_coupling_graph(coupling_map)` – undirected NetworkX graph.  
  • `compute_shortest_path_metrics(G)` – average shortest‑path length & diameter on the largest connected component.  
  • `compute_clustering_and_assortativity(G)` – global clustering coefficient and **degree assortativity** (expected –0.5 for a 3‑node path, matching the unit test).  
  • `compute_edge_betweenness_and_spectral_gap(G)` – spectral gap = 0 for disconnected graphs (C‑002).  
  *Artifacts*: `data/processed/graph_metrics.csv`.  
  *Verification*:  
  ```bash
  pytest code/tests/test_graph_builder.py -q   # corrected assortativity expectation, CSV generation
  wc -l data/processed/graph_metrics.csv
  ```

- [ ] T004 [US3] **Run the primary correlation analysis (cross‑sectional)**  
  *Implementation*: `code/stats_engine.py` exposing a CLI  
  ```bash
  python -m code.stats_engine \
      --perf data/processed/performance_metrics.csv \
      --graph data/processed/graph_metrics.csv \
      --out data/processed/correlation_results.csv
  ```  
  Steps:  
  1. Merge on `device_id`.  
  2. Compute **Spearman** ρ for every `(graph_metric, performance_metric)` pair.  
  3. Apply **Benjamini‑Hochberg** FDR correction (α = 0.05).  
  4. Add `adj_p_value` and `is_significant` columns.  
  5. **Cross‑sectional guard** – raises `RuntimeError` if topology and performance timestamps differ.  
  *Artifacts*: `data/processed/correlation_results.csv`.  
  *Verification*:  
  ```bash
  pytest code/tests/test_stats_engine.py -q   # includes toy‑data sanity check and schema validation
  head data/processed/correlation_results.csv
  ```

**Checkpoint** – After completing T001–T004, the command `python -m code.main` (documented in `quickstart.md`) must run the full pipeline and leave the four CSV files under `data/processed/`.

---

## Phase 2 – Complete the study, robustness, and power analysis  

- [ ] T005 [US3] **Bootstrap resampling of current performance data and 30‑day historical window comparison**  
  *Implementation*: `code/fetcher.py` adds  
  • `bootstrap_performance_resampling(num_samples=1000, seed=42)` → `data/processed/bootstrap_performance_metrics.csv`.  
  • `fetch_historical_window(days=30)` → stores historical JSON snapshots under `data/raw_historical/`.  
  • `compare_current_vs_historical()` computes a stability score (proportion of bootstrap samples where correlation sign matches the full‑dataset sign). Must be **≥ 0.7** to satisfy SC‑004.  
  *Artifacts*: `data/processed/bootstrap_performance_metrics.csv`, `data/raw_historical/`, `data/processed/stability_score.txt`.  
  *Verification*:  
  ```bash
  pytest code/tests/test_bootstrap.py -q   # function runs, CSV created, stability_score >= 0.7
  cat data/processed/stability_score.txt
  ```

- [ ] T006 [US3] **Robustness checks: Leave‑One‑Device‑Out (LODO) and bootstrap stability**  
  *Implementation* (in `code/stats_engine.py`):  
  • `leave_one_device_out(df)` → `data/processed/robustness_results.csv` (records per‑omission ρ, p‑values, and a `max_influence` flag).  
  • `robustness_check_bootstrap(stability_score)` – asserts the score from T005 meets the ≥ 0.7 threshold.  
  *Artifacts*: `data/processed/robustness_results.csv`.  
  *Verification*:  
  ```bash
  pytest code/tests/test_stats_engine.py -q   # includes LODO count = number of devices, stability check
  head data/processed/robustness_results.csv
  ```

- [ ] T012 [US3] **Full‑covariate partial correlation analysis**  
  *Implementation*: `code/stats_engine.py` adds `partial_correlation_full(df, covariates=['chip_generation','qubit_count','device_age_days','readout_architecture'])` → `data/processed/partial_correlations.csv`.  
  *Artifacts*: `data/processed/partial_correlations.csv`.  
  *Verification*:  
  ```bash
  pytest code/tests/test_partial_corr.py -q   # validates presence of all covariates, schema compliance
  head data/processed/partial_correlations.csv
  ```

- [ ] T007 [US3] **Power / Minimum Detectable Effect Size (MDES) analysis**  
  *Implementation*: `code/stats_engine.py` adds `compute_mdes(n, power=0.8, alpha=0.05)` returning the minimum detectable Spearman ρ. The function writes `data/processed/mdes_report.json` conforming to `specs/001‑exploring‑network‑structure/contracts/mdes_report.schema.yaml`.  
  *Low‑power flag*: set to `"Low Power: MDES > 0.5 (Large Effect Required)"` when the computed MDES exceeds 0.5, otherwise `"Adequate Power"`.  
  *Verification*:  
  ```bash
  python -c "from code.stats_engine import compute_mdes; print(compute_mdes(30))"
  jq . data/processed/mdes_report.json
  ```

- [ ] T008 [US3] **Generate figures and a fully programmatic results report**  
  *Implementation*: `code/viz.py` provides  
  • `generate_scatter_plots(df, out_dir='figures/')` – one PNG per significant adjusted‑p pair, regression line included.  
  • `generate_heatmap(df, out_path='figures/correlation_heatmap.png')`.  
  *Report*: `code/report_generator.py` assembles `data/results/report.md` from `correlation_results.csv`, `robustness_results.csv`, `partial_correlations.csv`, and `mdes_report.json`. The report contains:  
  – Table of all significant correlations (ρ, adj p).  
  – MDES table with numeric values and low‑power flag.  
  – Sections describing the cross‑sectional design (FR‑003) and the bootstrap surrogate for the 30‑day window (FR‑004).  
  *Artifacts*: `figures/*.png` and `data/results/report.md`.  
  *Verification*:  
  ```bash
  python -m code.viz   # creates PNGs
  python -m code.report_generator
  grep -q "cross‑sectional" data/results/report.md
  ```

- [ ] T009 [US3] **End‑to‑end integration test on real API data**  
  *Implementation*: `code/tests/test_integration.py` runs the full pipeline (fetch → performance CSV → graph CSV → correlations → robustness → figures → report) on a **small subset** of public backends (e.g., first 3 devices) to keep runtime < 5 min.  
  *Quickstart*: Update `quickstart.md` with the exact command:  
  ```bash
  export IBMQ_TOKEN=YOUR_TOKEN
  python -m code.main --subset 3
  ```  
  *Verification*:  
  ```bash
  pytest code/tests/test_integration.py -q
  # after a fresh run, all expected files exist and are non‑empty
  ```

- [ ] T010 [US3] **Methods & results write‑up + paper‑stage handoff**  
  *Deliverable*: `data/results/report.md` (generated by T008) is supplemented with a concise **Methods** section (data sources, freshness filter, graph construction, statistical pipeline) and a **Results** section (summary of significant findings, MDES interpretation, robustness outcomes, any null results).  
  *Handoff*: Add a `paper/handshake.yaml` file that lists the exact artifact paths the downstream paper pipeline must consume (`correlation_results.csv`, `mdes_report.json`, `robustness_results.csv`, `partial_correlations.csv`, `figures/`). No hand‑typed numbers; every value is referenced via the CSV/JSON files.  
  *Verification*:  
  ```bash
  grep -q "Methods" data/results/report.md
  grep -q "paper/handshake.yaml" -R .
  ```

- [ ] T013 [US3] **Longitudinal drift assessment**  
  *Implementation*: `code/drift_assessment.py` loads the 30‑day historical performance snapshots (from `data/raw_historical/`), aligns them by device, and computes per‑device temporal trends for each performance metric using linear regression. Outputs `data/processed/drift_assessment.csv` with slope, p‑value, and significance flag. Also produces a summary plot `figures/drift_heatmap.png`.  
  *Artifacts*: `data/processed/drift_assessment.csv`, `figures/drift_heatmap.png`.  
  *Verification*:  
  ```bash
  pytest code/tests/test_drift_assessment.py -q   # checks CSV existence, slope sign, significance column
  ls figures/drift_heatmap.png
  ```

## Phase 3 – Reproducible integration and paper‑stage handoff  

- (T009 and T010 already cover integration and handoff; no additional tasks needed.)

---

## Dependencies & Requirement Coverage  

| Requirement | Task(s) | Command demonstrating completion |
|---|---|---|
| FR‑001 (freshness ≤ 30 days) | T001 | `pytest code/tests/test_fetcher.py -q` (stale‑timestamp exclusion) |
| FR‑002 (extract T1/T2, gate/readout errors, coupling map) | T001, T002 | `data/processed/performance_metrics.csv` validates against its schema |
| FR‑003 (cross‑sectional, same snapshot) | T004 | RuntimeError on mismatched timestamps; docstring states cross‑sectional |
| FR‑004 (LODO, bootstrap stability, 30‑day window) | T005, T006, T007, T012, T013 | `bootstrap_performance_metrics.csv` with stability_score ≥ 0.7; LODO CSV produced; drift CSV produced |
| US1 (fetch/parse, no synthetic data) | T001, T002, T005 | All fetcher tests pass; no fallback to synthetic data |
| US2 (undirected graphs, metric suite, disconnected handling) | T003 | Graph metrics CSV validates; spectral gap = 0 for disconnected graphs |
| US3 (Spearman, FDR, robustness) | T004, T006, T007, T008, T012, T013 | Correlation CSV, robustness CSVs, MDES JSON, figures, report |
| C‑001 (rate‑limit backoff) | T001 | Backoff logic covered by unit tests |
| C‑002 (disconnected → spectral gap 0) | T003 | Tested with two‑component graph |

**Execution order** (respecting data flow):  
`T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T012 → T013`.

*All tasks are expressed as canonical checkbox items, each with a unique ID, required artifact paths, and explicit verification steps.  The pipeline can be run from a fresh environment using the quickstart command, producing real, verifiable results without any synthetic data or fabricated placeholders.*  