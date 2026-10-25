# Tasks: Assessing the Impact of Data Heterogeneity on Meta‑Analysis Results  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/*.yaml`  

## Phase 1 – Data acquisition & synthetic dataset generation  

- [X] T001 [P1] [FR-001] **Download a public Cochrane meta‑analysis CSV and generate a deterministic synthetic base template** using `code/scripts/generate_base_template.py` and store it at `data/processed/base_template.csv`.  
  *Verification*:  
  • Running `python code/scripts/generate_base_template.py --out data/processed/base_template.csv` exits with status 0.  
  • The CSV contains exactly 20 rows with columns `study_id,effect,se,n`.  
  • The file exists under `data/processed/` and passes a simple header check (no schema validation required).  

- [ ] T001a [P1] [FR-001] **(Optional) Validate that the downloaded Cochrane CSV is accessible**; if unavailable, the pipeline aborts with a clear error.  
  *Verification*:  
  • The script raises a `FileNotFoundError` if the URL cannot be reached; CI step fails accordingly.  

- [ ] T002 [P1] [FR-001] **Implement the simulation generator** (`code/simulation/generator.py`) that reads `data/processed/base_template.csv` and writes synthetic `SimulatedDataset` records to `data/results/simulation_raw.jsonl`. It must:  
    • Accept `--tau-squared` (comma‑separated list), `--replicates`, `--sweep-type`, `--out`.  
    • Produce **900 replicates per τ² level** for the primary sweep (`0,0.1,0.5,1.0,2.0`) and **900 replicates per τ² level** for the sensitivity sweep (`0.05,0.1,0.5`).  
    • Write each record as a JSON line conforming to `contracts/simulated_dataset.schema.yaml`.  
  *Verification*:  
  • Unit test `tests/unit/test_generator.py` passes.  
  • CLI call `python -m code.simulation.generator --tau-squared 0.5 --replicates 900 --sweep-type primary --out data/results/simulation_raw.jsonl` creates exactly 900 lines, each with `"tau_squared": 0.5` and empirical between‑study variance within ±0.05 of 0.5.  
  • After running the full primary command the file contains **4 500** `SimulatedDataset` lines (5 τ² × 900).  

## Phase 2 – Estimation, metric calculation & full sweeps  

- [ ] T003 [P2] [FR-002] **Implement Fixed‑Effects, DerSimonian‑Laird, and REML estimators** in `code/simulation/estimators.py`. Include computation of pooled effect, 95 % CI, τ² estimate, I², Q, and a `convergence_warning` flag for REML failures (fallback τ² = 1e‑6).  
  *Verification*:  
  • Unit tests `tests/unit/test_estimators.py` pass for all three estimators.  
  • For a dataset with `tau_squared = 0`, the Random‑Effects pooled estimate equals the Fixed‑Effects estimate within 1e‑3.  
  • When REML fails on a high‑heterogeneity replicate, `convergence_warning` is `true` and the estimated τ² is set to 1e‑6.  

- [ ] T005 [P2] [FR-001, FR-002] **Create an end‑to‑end entry point** (`code/main.py`) that accepts the CLI arguments `--tau-squared`, `--replicates`, `--batch-size`, `--sweep-type`, `--out`. With a tiny configuration (`--tau-squared 0,0.1 --replicates 10 --batch-size 5 --sweep-type primary --out data/results/`) it must:  
    • Invoke the simulation generator (T002).  
    • Run all three estimators (T003) on each generated dataset.  
    • Write the combined JSON‑lines file to `data/results/simulation_raw.jsonl`.  
    • Produce `data/results/sample_estimates.csv` containing **exactly 30 rows** (10 replicates × 3 estimators) with columns `replicate_id,tau_squared,estimator_type,pooled_effect,ci_lower,ci_upper,coverage_flag`.  
  *Verification*:  
  • Command `python -m code.main --tau-squared 0 0.1 --replicates 10 --batch-size 5 --sweep-type primary --out data/results/` exits with status 0.  
  • `sample_estimates.csv` has 30 rows and the required columns.  
  • `simulation_raw.jsonl` contains 10 `SimulatedDataset` lines followed by 30 `EstimationResult` lines.  

- [ ] T004 [P2] [FR-003] **Compute bias and coverage per replicate** (`code/analysis/metrics.py`). The script reads `data/results/simulation_raw.jsonl`, extracts each `EstimationResult`, calculates bias (`pooled_effect − true_effect`) and verifies coverage (`true_effect` within CI). It writes these per‑replicate metrics to `data/results/replicate_metrics.jsonl` (each line conforms to a new schema with fields `dataset_id`, `estimator_type`, `bias`, `coverage_flag`).  
  *Verification*:  
  • After execution, every line in `replicate_metrics.jsonl` validates against the new metrics schema.  
  • Bias values are numeric and coverage_flag correctly reflects CI inclusion of the true effect (0.5).  

- [ ] T006 [P2] [FR-001] **Run the full primary sweep** using the entry point from T005 with `--tau-squared 0 0.1 0.5 1.0 2.0 --replicates 900 --batch-size 100 --sweep-type primary --out data/results/`.  
  *Verification*:  
  • `data/results/simulation_raw.jsonl` contains **4 500** `SimulatedDataset` lines and **13 500** `EstimationResult` lines (3 estimators × 4 500).  
  • Peak RAM never exceeds 5 GB (checked via CI logs).  
  • Total wall‑clock time ≤ 3 h on the GitHub Actions free‑tier runner.  

- [ ] T007 [P2] [FR-001] **Run the sensitivity sweep** (`--tau-squared 0.05 0.1 0.5 --replicates 900 --sweep-type sensitivity --batch-size 100 --out data/results/`). Results are appended to the same `simulation_raw.jsonl`.  
  *Verification*:  
  • After completion `simulation_raw.jsonl` contains **7 200** `SimulatedDataset` lines (4 500 primary + 2 700 sensitivity) and **21 600** `EstimationResult` lines.  
  • No duplicate `replicate_id` values exist across primary and sensitivity sweeps.  

- [ ] T008 [P3] [FR-004, FR‑007, FR‑008] **Aggregate metrics and perform statistical tests** (`code/analysis/stats.py`). The script reads the full JSON‑lines file and `replicate_metrics.jsonl`, then produces:  
    • `data/results/aggregated_metrics.csv` – **15 rows** (3 estimators × 5 primary τ² levels) with columns exactly matching `contracts/aggregated_metric.schema.yaml`.  
    • `data/results/coverage_tests.json` – JSON‑lines file containing **15 objects**, each with fields `estimator_type`, `tau_squared`, `p_value`, `alpha_used` (0.01), `test_type` (“binomial”).  
    • `data/results/reml_failures.json` – JSON array listing all REML runs that triggered `convergence_warning`.  
  *Verification*:  
  • CSV header order and types conform to the schema; a pandas validation step passes.  
  • `coverage_tests.json` contains exactly 15 well‑formed JSON objects.  
  • `reml_failures.json` is a JSON array (empty `[]` if no failures).  

## Phase 3 – Visualization, reporting & hand‑off  

- [ ] T009 [P3] [FR-005] **Generate visualisations** (`code/visualization/plots.py`). From `aggregated_metrics.csv` produce:  
    • `data/results/coverage_vs_tau2.png` – plot of observed coverage rate (with Wilson‑score CI) vs. τ² for each estimator.  
    • `data/results/mean_bias_vs_tau2.png` – plot of mean bias vs. τ² for each estimator.  
  *Verification*:  
  • Both PNG files exist, are ≥ 600 × 400 px, and each file size ≥ 10 KB.  
  • The x‑axis label contains the substring “τ²”.  

- [ ] T010 [P3] [SC-005] **Generate the final markdown report** (`code/reporting/report_gen.py`). The report (`data/results/report.md`) must include:  
    • Header line `Framing: associational`.  
    • Summary tables of bias and coverage (pulled from `aggregated_metrics.csv`).  
    • A “REML convergence failures” section reporting `n_failures = len(json.load(open('data/results/reml_failures.json')))` and listing the first five failure `dataset_id`s.  
    • Embedded figures referencing the PNGs created in T009.  
  *Verification*:  
  • The report contains the exact framing line.  
  • The failure count matches the length of `reml_failures.json`.  
  • All figure markdown links resolve to existing PNG files.  

- [ ] T011 [P3] [SC-003] **Write and pass an integration test** (`tests/integration/test_pipeline.py`). The test runs the full pipeline via `python -m code.main --full-sweep --out data/results/` and asserts:  
    • `data/results/simulation_raw.jsonl` has **7 200** `SimulatedDataset` lines.  
    • `aggregated_metrics.csv` exists, has 15 rows, and passes schema validation.  
    • Both PNG figures exist.  
    • `report.md` contains the framing line.  
  *Verification*:  
  • `pytest -q tests/integration/test_pipeline.py` exits with status 0 and reports `1 passed`.  

- [ ] T012 [P3] [SC-003] **Compute SHA‑256 checksums for all final artefacts** (`code/scripts/record_hashes.py data/results/`). The script writes `state/artifact_hashes.yaml`.  
  *Verification*:  
  • Re‑running the script produces an identical YAML file (no diff).  

- [ ] T013 [P3] [SC-003] **Write a hand‑off markdown** (`data/results/handoff.md`) that lists each final artifact (aggregated metrics CSV, coverage tests JSON, both PNGs, report, checksum file) together with the corresponding FR/SC IDs. The document includes a table with columns `Artifact`, `FR/SC ID`, `Location`.  
  *Verification*:  
  • The table contains entries for all six artefacts, and each `Location` path exists.  
  • No placeholder `{{…}}` strings remain.  

- [ ] T014 [P3] [SC-003] **Document the reproducible command in `quickstart.md`** and verify it on a clean runner. The markdown must show the exact command `python -m code.main --full-sweep --out data/results/`.  
  *Verification*:  
  • A CI step runs this command in a fresh container; generated artefacts match the hashes recorded in `state/artifact_hashes.yaml`.  

---  

### Dependency mapping (spec → tasks)

| Spec / Success Criterion | Satisfied by Task(s) |
|--------------------------|----------------------|
| FR‑001 (synthetic datasets) | T001, T001a, T002 |
| FR‑002 (estimators) | T003 |
| FR‑003 (bias & coverage) | T004 |
| FR‑004 (exact binomial test) | T008 |
| FR‑005 (visualisations) | T009 |
| FR‑006 (REML handling) | T003, T008 |
| FR‑007 (Bonferroni) | T008 |
| FR‑008 (Shapiro‑Wilk → KW/ANOVA) | T008 |
| SC‑001 (coverage measurement) | T008 |
| SC‑002 (bias measurement) | T008 |
| SC‑003 (runtime limits) | T006, T007 |
| SC‑004 (sensitivity sweep) | T007 |
| SC‑005 (associational framing) | T010 |
| SC‑003 (checksum & hand‑off) | T012, T013, T014 |