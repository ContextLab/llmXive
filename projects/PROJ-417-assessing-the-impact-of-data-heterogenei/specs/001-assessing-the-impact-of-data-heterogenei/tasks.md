# Tasks: Assessing the Impact of Data Heterogeneity on Meta‑Analysis Results  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/*.yaml`  

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal, reproducible pipeline on a tiny synthetic input to prove that the data‑flow, schemas and basic calculations work before scaling up. |
|------|------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T001 [P1] [US1] **Generate a deterministic synthetic base meta‑analysis template** using `code/scripts/generate_base.py` and store it at `data/processed/base_template.csv`.   <!-- FAILED-IN-EXECUTION: code/scripts/fetch_openml.py exit=1 -->
  *Verification*:  
  • `python code/scripts/generate_base.py --seed 42 --out data/processed/base_template.csv` exits with status 0.  
  • The output CSV exists, has exactly 20 rows (studies) and columns `study_id, effect, se, n`.  
  • SHA‑256 of the file is recorded in `state/artifact_hashes.yaml` (run `python code/scripts/record_hashes.py data/processed/base_template.csv`).  

- [ ] T002 [P1] [US1] **Implement the synthetic‑dataset generator** in `code/simulation/generator.py`. The generator must accept a `tau_squared` value and a `replicates` count and write `SimulatedDataset` records to `data/results/simulation_raw.jsonl`.  
  *Verification*:  
  • Unit test `tests/unit/test_generator.py` passes (`pytest -q tests/unit/test_generator.py`).  
  • When called with `--tau-squared 0.5 --replicates 900`, the script creates exactly 900 `SimulatedDataset` lines (checked with `jq 'select(.replicate_id != null)'`).  
  • Empirical variance of generated study effects is within ±0.05 of the injected τ².  

- [ ] T003 [P1] [US2] **Implement Fixed‑Effects, DerSimonian‑Laird, and REML estimators** (including Q, I², and REML‑failure handling) in `code/simulation/estimators.py`.  
  *Verification*:  
  • Unit test `tests/unit/test_estimators.py` passes.  
  • For τ² = 0 the Random‑Effects pooled estimate equals the Fixed‑Effects estimate within 1e‑3.  
  • When REML fails to converge the flag `convergence_warning` is set to `true` and the estimated τ² is replaced by a minimal positive value (e.g., 1e‑6).  

- [ ] T004 [P1] [US2] **Add metric‑calculation logic** in `code/analysis/metrics.py` that computes bias and 95 % CI coverage for each `EstimationResult` and writes both `SimulatedDataset` and `EstimationResult` objects to `data/results/simulation_raw.jsonl`.   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  *Verification*:  
  • Unit test `tests/unit/test_metrics.py` passes.  
  • Every line written to `simulation_raw.jsonl` validates against the appropriate JSON schema (`contracts/simulated_dataset.schema.yaml` or `contracts/estimation_result.schema.yaml`).  

- [ ] T005 [P1] [US1] **Run a tiny end‑to‑end pipeline** (10 replicates for τ² ∈ {0, 0.1}) via the entry point `code/main.py`.  
  *Command*: `python -m code.main --tau-squared 0 0.1 --replicates 10 --batch-size 5`  
  *Outputs*: `data/results/simulation_raw.jsonl`, `data/results/sample_estimates.csv`.  
  *Verification*:  
  • `sample_estimates.csv` contains 20 rows (2 τ² levels × 10 replicates) with non‑null numeric columns `pooled_effect, ci_lower, ci_upper, coverage_flag`.  
  • A quick `head` shows matching `tau_squared` values.  

## Phase 2 – Complete the study and validate its evidence  

| Goal | Execute the full primary and sensitivity sweeps, aggregate metrics, test hypotheses, and produce the final scientific figures. |
|------|------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T006 [P2] [US1] **Run the primary simulation sweep** (τ² ∈ {0, 0.1, 0.5, 1.0, 2.0}, 900 replicates each) with batch processing.  
  *Command*: `python -m code.main --tau-squared 0 0.1 0.5 1.0 2.0 --replicates 900 --batch-size 100`  
  *Outputs*: `data/results/simulation_raw.jsonl` (≈ 13 500 lines) and log `logs/primary_sweep.log`.  
  *Verification*:  
  • `jq 'select(.replicate_id != null)' data/results/simulation_raw.jsonl | wc -l` returns 4500 (SimulatedDataset lines).  
  • `jq 'select(.estimator_type != null)' data/results/simulation_raw.jsonl | wc -l` returns 9000 (EstimationResult lines).  
  • Log shows `Peak RAM ≤ 7 GB` and `Elapsed time ≤ 10800 s` (3 h).  

- [ ] T007 [P2] [US2] **Aggregate metrics and perform statistical tests** in `code/analysis/stats.py`. This script must:  
  1. Compute mean bias and coverage per τ²‑estimator pair.  
  2. Conduct an exact binomial test for coverage (α = 0.01 after Bonferroni correction across 5 τ² levels).  
  3. Perform a Shapiro‑Wilk test on bias distributions; if any p < 0.05 use Kruskal‑Wallis, otherwise ANOVA.  
  *Outputs*: `data/results/aggregated_metrics.csv`, `data/results/coverage_tests.json`.  
  *Verification*:  
  • CSV header matches `contracts/aggregated_metric.schema.yaml`.  
  • CSV has exactly 15 rows (3 estimators × 5 τ² levels).  
  • Each row contains numeric `binomial_p_value` and `bias_test_p_value`.  

- [ ] T008 [P2] [US1] **Execute the sensitivity sweep** (τ² ∈ {0.05, 0.1, 0.5}, 900 replicates each) and append results to the same JSONL file.   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  *Command*: `python -m code.main --tau-squared 0.05 0.1 0.5 --replicates 900 --batch-size 100 --sweep-type sensitivity`  
  *Outputs*: additional 2 700 `SimulatedDataset` lines (and 5 400 `EstimationResult` lines) plus `data/results/stability_analysis.json`.  
  *Verification*:  
  • After append, total line count in `simulation_raw.jsonl` is 18 000.  
  • `stability_analysis.json` contains keys `tau_squared`, `primary_coverage`, `sensitivity_coverage`, `coverage_diff`; all `coverage_diff` ≤ 0.07.  

- [ ] T009 [P2] [US3] **Create the required visualisations** in `code/visualization/plots.py`.  
  *Outputs*: `data/results/coverage_vs_tau2.png`, `data/results/mean_bias_vs_tau2.png`.  
  *Verification*:  
  • Both PNG files exist (`ls data/results/*.png`).  
  • Each image size ≥ 600 × 400 px and file size ≥ 10 KB.  
  • Using Pillow, the x‑axis label contains the substring `"τ²"`.  

- [ ] T010 [P2] [US3] **Generate the final report** with correct framing and accurate REML‑failure counts via `code/reporting/report_gen.py`.  
  *Output*: `data/results/report.md`.  
  *Verification*:  
  • The report header includes the line `Framing: associational`.  
  • The section “REML convergence failures” reports `n_failures = <value>` that exactly matches `len(json.load(open('data/results/reml_failures.json')))` .  
  • All figure and table citations resolve to existing files (`coverage_vs_tau2.png`, `aggregated_metrics.csv`).  

- [ ] T011 [P3] [US2] **Write and pass an integration test** that runs the full pipeline from scratch.  
  *File*: `tests/integration/test_pipeline.py`.  
  *Verification*:  
  • `pytest -q tests/integration/test_pipeline.py` exits with `0` and reports `1 passed`.  
  • The test creates a temporary directory, runs `code/main.py --full-sweep`, and asserts:  
    – `data/results/simulation_raw.jsonl` has 18 000 lines,  
    – `data/results/aggregated_metrics.csv` exists and conforms to its schema,  
    – both PNG figures exist.  

- [ ] T012 [P3] [US2] **Compute SHA‑256 checksums for all final artefacts** and store them in `state/artifact_hashes.yaml` via `code/scripts/record_hashes.py`.  
  *Verification*:  
  • Running `python code/scripts/record_hashes.py data/results/` rewrites the YAML with entries for every file under `data/results/`.  
  • Running `python code/scripts/record_hashes.py data/processed/base_template.csv` adds the checksum for the synthetic base template.  
  • A subsequent `diff` between the regenerated YAML and the committed version shows **no differences**.  

- [ ] T013 [P3] [US3] **Write the hand‑off markdown** linking every artefact to its scientific requirement.  
  *File*: `data/results/handoff.md`.  
  *Verification*:  
  • The document contains a table with columns `Artifact`, `FR/SC ID`, `Location`.  
  • All rows reference real files (e.g., `simulation_raw.jsonl → FR‑001`, `aggregated_metrics.csv → FR‑004`).  
  • No placeholder tokens such as `{{…}}` remain (`grep '{{'` returns nothing).  
  • The “Results Overview” section reports coverage rates and mean biases **exactly** as they appear in `aggregated_metrics.csv` (validated by a small script in the test suite).  

- [ ] T014 [P3] [US1] **Document the reproducibility command‑line in `quickstart.md` and verify it works on a fresh runner**.  
  *File*: `quickstart.md`.  
  *Verification*:  
  • The markdown lists the command `python -m code.main --full-sweep`.  
  • A CI step runs this command in a clean container; the step succeeds and the generated artefacts match the hashes recorded in `state/artifact_hashes.yaml`.  

- [ ] T015 [P3] [US1] **Record checksum of the synthetic base template** produced in T001.  
  *Command*: `python code/scripts/record_hashes.py data/processed/base_template.csv`.  
  *Verification*:  
  • `state/artifact_hashes.yaml` contains an entry for `data/processed/base_template.csv` with its SHA‑256 hash.  
  • A subsequent `diff` shows no changes to the file after recording.  