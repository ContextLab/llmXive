# Tasks: Assessing the Impact of Data Heterogeneity on Meta‑Analysis Results  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/*.yaml`  

## Phase 1 – Data acquisition and synthetic dataset generation (US1)

- [ ] T001 [P1] [US1] **Fetch real Cochrane meta‑analysis data** using `code/scripts/fetch_cochrane.py` (download URL `[UNRESOLVED-CLAIM: https://raw.githubusercontent.com/MetaAnalysisData/Cochrane/master/meta_data.csv` — HTTP 404]) and store it at `data/raw/cochrane_base.csv`.  
  *Verification*:  
  • Running `python code/scripts/fetch_cochrane.py --out data/raw/cochrane_base.csv` exits with status 0.  
  • The file exists and its SHA‑256 hash is recorded via `code/scripts/record_hashes.py data/raw/cochrane_base.csv`.  

- [ ] T002 [P1] [US1] **Create deterministic base template** from the fetched Cochrane data (`code/scripts/create_base_template.py`) producing exactly 20 studies with columns `study_id,effect,se,n` saved to `data/processed/base_template.csv`.  
  *Verification*:  
  • Running `python code/scripts/create_base_template.py --in data/raw/cochrane_base.csv --out data/processed/base_template.csv` exits with status 0.  
  • The CSV contains exactly 20 rows.  
  • Its SHA‑256 hash is recorded via `code/scripts/record_hashes.py data/processed/base_template.csv`.  

- [ ] T003 [P1] [US1] **Generate synthetic meta‑analysis datasets for primary and sensitivity sweeps** (`code/simulation/generator.py`). Accepts `--tau-squared` list, `--replicates`, `--sweep-type`, `--out data/results/us1_simulation_raw.jsonl`, uses `data/processed/base_template.csv` as the study‑size/SE backbone, injects the specified τ², and writes one `SimulatedDataset` per replicate.  
  *Verification*:  
  • Unit test `tests/unit/test_generator.py` passes.  
  • CLI call `python -m code.simulation.generator --tau-squared 0.5 --replicates 900 --sweep-type primary --out data/results/us1_simulation_raw.jsonl` creates exactly 900 lines, each a valid `SimulatedDataset` with `tau_squared = 0.5` and empirical between‑study variance within ±0.05 of 0.5.  

## Phase 2 – Estimation and metric calculation (US2)

- [ ] T016 [P1] [US2] **Fetch real Cochrane data for US2** using the same script as T001, storing at `data/raw/cochrane_us2.csv`.  
  *Verification*: Same as T001 but targeting the new path.

- [ ] T017 [P1] [US2] **Create base template for US2** (`code/scripts/create_base_template.py`) reading `data/raw/cochrane_us2.csv` and writing `data/processed/base_template_us2.csv` (20 studies).  
  *Verification*: Same as T002 but targeting the US2 paths.

- [ ] T018 [P1] [US2] **Generate synthetic datasets for US2** (`code/simulation/generator.py`) outputting to `data/results/simulation_raw.jsonl`. Parameters identical to T003 but used by estimator pipeline.  
  *Verification*: Same as T003, targeting the US2 output file.

- [ ] T004 [P2] [US2] **Implement Fixed‑Effects, DerSimonian‑Laird, and REML estimators** (`code/simulation/estimators.py`). Includes Q, I², and REML convergence handling (fallback τ² = 1e‑6, flag `convergence_warning`).  
  *Verification*:  
  • Unit tests `tests/unit/test_estimators.py` pass.  
  • For τ² = 0 the Random‑Effects pooled estimate equals the Fixed‑Effects estimate within 1e‑3.  
  • When REML fails to converge, `convergence_warning` is set to `true` and τ² is replaced by 1e‑6.  

- [ ] T005 [P2] [US2] **Compute bias and coverage for each replicate** (`code/analysis/metrics.py`). Reads `simulation_raw.jsonl`, applies each estimator, and appends the resulting `EstimationResult` objects to the same file.  
  *Verification*:  
  • After execution, every line in `data/results/simulation_raw.jsonl` validates against either `contracts/simulated_dataset.schema.yaml` or `contracts/estimation_result.schema.yaml`.  

- [ ] T006 [P2] [US2] **Run a tiny end‑to‑end pipeline** (`code/main.py`) with 10 replicates for τ² ∈ {0, 0.1}.  
  Command: `python -m code.main --tau-squared 0 0.1 --replicates 10 --batch-size 5 --out data/results/`  
  *Outputs*: `data/results/simulation_raw.jsonl` and `data/results/sample_estimates.csv` (20 rows).  
  *Verification*:  
  • `sample_estimates.csv` contains exactly 20 rows with columns `replicate_id,tau_squared,estimator_type,pooled_effect,ci_lower,ci_upper,coverage_flag`.  
  • Script exits with status 0 and logs “End‑to‑end tiny run completed”.  

- [ ] T007 [P2] [US2] **Execute the primary simulation sweep** (τ² ∈ {0, 0.1, 0.5, 1.0, 2.0}, 900 replicates each) using `code/main.py` with batch‑size 100.  
  Command: `python -m code.main --tau-squared 0 0.1 0.5 1.0 2.0 --replicates 900 --batch-size 100 --out data/results/`  
  *Outputs*: `data/results/simulation_raw.jsonl` (9 000 `SimulatedDataset` + 27 000 `EstimationResult`) and log `logs/primary_sweep.log`.  
  *Verification*:  
  • `jq 'select(.replicate_id != null)' data/results/simulation_raw.jsonl | wc -l` returns 9 000.  
  • `jq 'select(.estimator_type != null)' data/results/simulation_raw.jsonl | wc -l` returns 27 000.  
  • Peak RAM ≤ 7 GB and elapsed time ≤ 3 h.  

- [ ] T008 [P2] [US2] **Aggregate metrics and perform statistical tests** (`code/analysis/stats.py`). Produces `data/results/aggregated_metrics.csv` (15 rows, all required columns) and `data/results/coverage_tests.json` (one object per estimator/τ² with fields `estimator_type`, `tau_squared`, `p_value`, `alpha_used`, `test_type`).  
  *Verification*:  
  • CSV header matches `contracts/aggregated_metric.schema.yaml`.  
  • CSV contains exactly 15 rows (3 estimators × 5 τ² levels).  
  • `coverage_tests.json` contains 15 JSON objects with the specified fields.  

- [ ] T009 [P2] [US2] **Run the sensitivity sweep** (τ² ∈ {0.05, 0.1, 0.5}, 900 replicates each) with `--sweep-type sensitivity`. Appends results to `simulation_raw.jsonl` and writes `data/results/stability_analysis.json`.  
  *Verification*:  
  • Final line count in `simulation_raw.jsonl` is 12 600 (9 000 primary + 3 600 sensitivity).  
  • `stability_analysis.json` contains keys `tau_squared`, `primary_coverage`, `sensitivity_coverage`, `coverage_diff` with `coverage_diff ≤ 0.07`.  
  • The inclusion of the extra τ² levels is justified as a robustness analysis (see task description).  

## Phase 3 – Reporting and hand‑off (US3)

- [ ] T010 [P2] [US3] **Create visualisations** (`code/visualization/plots.py`). Outputs `data/results/coverage_vs_tau2.png` and `data/results/mean_bias_vs_tau2.png`.  
  *Verification*:  
  • Both PNG files exist (`ls data/results/*.png`).  
  • Each image is at least 600 × 400 px and ≥ 10 KB.  
  • Using Pillow, the x‑axis label contains the substring “τ²”.  

- [ ] T011 [P2] [US3] **Generate the final report** (`code/reporting/report_gen.py`). Produces `data/results/report.md` with header line `Framing: associational` and a “REML convergence failures” section whose `n_failures` matches the length of `data/results/reml_failures.json`.  
  *Verification*:  
  • Report contains the required framing line.  
  • Failure count is exactly `len(json.load(open('data/results/reml_failures.json')))` .  
  • All figure and table citations resolve to existing files.  

- [ ] T012 [P3] [US3] **Write and pass integration test** (`tests/integration/test_pipeline.py`). Runs the full pipeline via `code.main --full-sweep`.  
  *Verification*:  
  • `pytest -q tests/integration/test_pipeline.py` exits with status 0 and reports `1 passed`.  
  • Test asserts `data/results/simulation_raw.jsonl` has 12 600 lines, `aggregated_metrics.csv` exists and conforms to its schema, both PNG figures exist, and `report.md` contains the framing line.  

- [ ] T013 [P3] [US3] **Compute SHA‑256 checksums for all final artefacts** (`code/scripts/record_hashes.py data/results/`). Updates `state/artifact_hashes.yaml`.  
  *Verification*:  
  • Re‑running the script produces an identical YAML file (no diff).  

- [ ] T014 [P3] [US3] **Write hand‑off markdown** (`data/results/handoff.md`) linking each **final** artefact (aggregated metrics, figures, report, checksum file) to its FR/SC ID.  
  *Verification*:  
  • Document contains a table with columns `Artifact`, `FR/SC ID`, `Location`.  
  • No `{{…}}` placeholders remain.  
  • Values in the “Results Overview” section exactly match those in `aggregated_metrics.csv` (validated by a helper script).  

- [ ] T015 [P3] [US3] **Document reproducibility command in `quickstart.md`** and verify on a clean runner.  
  *Verification*:  
  • `quickstart.md` lists the command `python -m code.main --full-sweep --out data/results/`.  
  • CI step runs this command in a fresh container; generated artefacts match the hashes recorded in `state/artifact_hashes.yaml`.  