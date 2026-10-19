# Tasks: Assessing the Impact of Data Heterogeneity on Meta‑Analysis Results  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, `contracts/*.yaml`

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal, reproducible pipeline on a tiny real input to prove that the data‑flow, schemas and basic calculations work before scaling up. |
|------|------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T001 [P1] [US1] **Create the canonical project layout, pin exact CPU‑only dependencies, and fetch a verified base meta‑analysis dataset.**   <!-- FAILED-IN-EXECUTION: code/scripts/fetch_openml.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/scripts/fetch_openml.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/scripts/fetch_openml.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/scripts/fetch_openml.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/scripts/fetch_openml.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/scripts/fetch_openml.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/scripts/fetch_openml.py exit=1 -->
  *Files*: `code/requirements.txt`, `code/scripts/fetch_openml.py`, `data/raw/cochrane_base.csv`  
  *Verification*:  
    • `grep -v '^#' code/requirements.txt | sort` contains **only** `numpy`, `pandas`, `scipy`, `matplotlib`, `pyyaml`, `pytest`.  
    • Running `python code/scripts/fetch_openml.py` exits with status 0 and creates `data/raw/cochrane_base.csv` whose SHA‑256 matches the value recorded in `state/artifact_hashes.yaml`.  
    • The script raises `FileNotFoundError` on download failure – no silent fallback.

- [ ] T002 [P1] [US2] **Implement the synthetic‑dataset generator.**  
  *File*: `code/simulation/generator.py`  
  *Verification*: Unit test `tests/unit/test_generator.py` confirms that for a given seed the empirical variance of generated study effects matches the injected τ² within 0.05 and that exactly 900 replicates are produced per τ² level when called with `replicates=900`.

- [ ] T003 [P1] [US3] **Implement Fixed‑Effects, DerSimonian‑Laird, and REML estimators with Q/I² computation and REML‑failure handling.**  
  *File*: `code/simulation/estimators.py`  
  *Verification*: `tests/unit/test_estimators.py` passes; for τ² = 0 the Random‑Effects estimate equals the Fixed‑Effects estimate to ≤ 1e‑3, REML convergence warnings are flagged, and coverage calculations explicitly **exclude** replicates where `convergence_warning=True`.

- [ ] T004 [P1] [US4] **Add metric‑calculation logic (bias & 95 % CI coverage).**  
  *File*: `code/analysis/metrics.py`  
  *Verification*: `pytest -q tests/unit/test_metrics.py` exits with code 0; the script writes both `SimulatedDataset` and corresponding `EstimationResult` objects to `data/results/simulation_raw.jsonl`, each line validated against the appropriate schema.

- [ ] T005 [P1] [US5] **Run a tiny end‑to‑end pipeline (10 replicates, τ² ∈ {0, 0.1}) and produce a proof‑of‑concept results file.**  
  *Command*: `python -m code.main --tau-squared 0 0.1 --replicates 10`  
  *Outputs*: `data/results/simulation_raw.jsonl`, `data/results/estimation_results_sample.csv` (contains pooled effects, CIs, Q, I²).  
  *Verification*: The CSV contains 20 rows (2 estimators × 10 replicates) with non‑null numeric columns; a quick `head` shows matching `tau_squared` values.

## Phase 2 – Complete the study and validate its evidence  

| Goal | Execute the full primary and sensitivity sweeps, aggregate metrics, test hypotheses, and produce the final scientific figures. |
|------|------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T006 [P2] [US6] **Run the primary simulation sweep (τ² ∈ {0, 0.1, 0.5, 1.0, 2.0}, 900 replicates each).**  
  *Command*: `python -m code.main --tau-squared 0 0.1 0.5 1.0 2.0 --replicates 900 --batch-size 100`  
  *Outputs*: `data/results/simulation_raw.jsonl` (≈ 13 500 lines: 4 500 SimulatedDataset + 9 000 EstimationResult), runtime log `logs/primary_sweep.log`.  
  *Verification*:  
    • `jq 'select(.dataset_id != null) | .dataset_id' data/results/simulation_raw.jsonl | wc -l` returns 4500.  
    • `jq 'select(.estimator_type != null) | .estimator_type' data/results/simulation_raw.jsonl | wc -l` returns 9000.  
    • Log contains lines `Peak RAM: <value> GB` and `Elapsed time: <value> s` with RAM ≤ 7 GB and time ≤ 10800 s (3 h).  
    • SHA‑256 of the JSONL file recorded in `state/artifact_hashes.yaml`.

- [ ] T007 [P2] [US7] **Aggregate metrics and perform statistical tests (exact binomial, Bonferroni‑adjusted α=0.01, Kruskal‑Wallis).**  
  *File*: `code/analysis/stats.py`  
  *Outputs*: `data/results/aggregated_metrics.csv`, `data/results/coverage_tests.json`.  
  *Verification*:  
    • CSV header matches `contracts/aggregated_metric.schema.yaml`.  
    • Each row contains `binomial_p_value` ≤ 1 and `bias_test_p_value` ≤ 1.  
    • Code contains `alpha = 0.05/5` and uses `scipy.stats.binom_test` (or `binomtest`) for exact coverage testing.  
    • Running `python -c "import pandas as pd; df=pd.read_csv('data/results/aggregated_metrics.csv'); assert len(df)==15"` passes (3 estimators × 5 τ² levels).  
    • Kruskal‑Wallis test is performed via `scipy.stats.kruskal` and results stored in `bias_test_p_value`.

- [ ] T008 [P2] [US8] **Execute the sensitivity sweep (τ² ∈ {0.05, 0.1, 0.5}, 900 replicates each) and produce a stability‑analysis report.**  
  *Command*: `python -m code.main --tau-squared 0.05 0.1 0.5 --replicates 900 --batch-size 100 --sweep-type sensitivity`  
  *Outputs*: additional 2 700 SimulatedDataset lines (and 5 400 EstimationResult lines) appended to `data/results/simulation_raw.jsonl`, `data/results/stability_analysis.json`.  
  *Verification*:  
    • Total line count after append is 18 000 (13 500 + 4 500).  
    • `stability_analysis.json` contains keys `tau_squared`, `primary_coverage`, `sensitivity_coverage`, `coverage_diff`; all `coverage_diff` values are ≤ 0.07.  
    • Log `logs/sensitivity_sweep.log` shows runtime ≈ 1.5 h and RAM < 6 GB.

- [ ] T009 [P2] [US9] **Create the required visualisations.**  
  *File*: `code/visualization/plots.py`  
  *Outputs*: `data/results/coverage_vs_tau2.png`, `data/results/mean_bias_vs_tau2.png`.  
  *Verification*:  
    • `ls data/results/*.png` lists both files.  
    • Each PNG has dimensions ≥ 600 × 400 pixels and file size ≥ 10 KB (checked via `os.path.getsize`).  
    • Automated check parses the image with Pillow to confirm that the x‑axis label contains the substring `"τ²"`.

- [ ] T010 [P2] [US10] **Generate the final report with correct framing and accurate REML‑failure counts.**  
  *File*: `code/reporting/report_gen.py` → `data/results/report.md`  
  *Verification*:  
    • The report header contains the line `Framing: associational`.  
    • The section “REML convergence failures” reports the integer `n_failures = <value>` that exactly matches `len(json.load(open('data/results/reml_failures.json')))` .  
    • All figure/table citations point to existing files (`coverage_vs_tau2.png`, `aggregated_metrics.csv`).  
    • Running `python -m code.reporting.report_gen` exits with code 0.

## Phase 3 – Reproducible results and paper hand‑off  

| Goal | Demonstrate that the entire pipeline can be reproduced from a clean environment and hand the evidence to the downstream paper stage. |
|------|-------------------------------------------------------------------------------------------------------------------------------|

- [ ] T011 [P3] [US11] **Write and pass an integration test that runs the full pipeline from scratch.**  
  *File*: `tests/integration/test_pipeline.py`  
  *Verification*:  
    • `pytest -q tests/integration/test_pipeline.py` exits with 0 and reports `1 passed`.  
    • The test creates a temporary directory, invokes `code/main.py` with the full‑sweep parameters, and asserts that after the run:  
  • `data/results/simulation_raw.jsonl` has 18 000 lines,  
  • `data/results/aggregated_metrics.csv` exists and conforms to its schema,  
  • `data/results/coverage_vs_tau2.png` exists.

- [ ] T012 [P3] [US12] **Compute SHA‑256 checksums for all final artefacts and store them in `state/artifact_hashes.yaml`.**  
  *File*: `state/artifact_hashes.yaml`  
  *Verification*:  
    • Running `python code/scripts/record_hashes.py` rewrites the YAML with entries for each file under `data/results/`.  
    • A subsequent `diff` between the newly generated YAML and the committed version shows **no differences** (i.e., the recorded hashes match the on‑disk files).

- [ ] T013 [P3] [US13] **Write the hand‑off markdown linking every artefact to its scientific requirement.**  
  *File*: `data/results/handoff.md`  
  *Verification*:  
    • The document contains a table with columns `Artifact`, `FR/SC ID`, `Location`.  
    • All rows reference real files (e.g., `simulation_raw.jsonl → FR‑001`, `aggregated_metrics.csv → FR‑004`).  
    • No placeholder tokens such as `{{…}}` remain (`grep '{{'` returns nothing).  
    • The “Results Overview” section reports the observed coverage rates and mean biases **exactly** as they appear in `aggregated_metrics.csv` (validated by a small script in the test suite).

- [ ] T014 [P3] [US14] **Document the reproducibility command‑line in `quickstart.md` and verify it works on a fresh runner.**  
  *File*: `quickstart.md`  
  *Verification*:  
    • The markdown lists the command `python -m code.main --full-sweep`.  
    • A CI step runs this command in a clean container; the step succeeds and the artifacts listed in the quick‑start match those recorded in `state/artifact_hashes.yaml`.

### Dependencies & Requirement Coverage  

| FR/SC | Satisfied by Task(s) | Verification Command |
|------|----------------------|----------------------|
| FR‑001 (generation) | T001, T006, T008 | `jq 'select(.dataset_id != null) | .dataset_id' data/results/simulation_raw.jsonl \| wc -l` |
| FR‑002 (estimators) | T003 | `pytest tests/unit/test_estimators.py` |
| FR‑003 (bias/coverage) | T004, T005 | `pytest -q tests/unit/test_metrics.py` |
| FR‑004 (binomial test) | T007 | `grep binomial_p_value data/results/aggregated_metrics.csv` |
| FR‑005 (plots) | T009 | `ls data/results/*.png` |
| FR‑006 (REML failures) | T003, T010 | `jq . data/results/reml_failures.json` |
| FR‑007 (Bonferroni) | T007 | `grep "alpha = 0.05/5" code/analysis/stats.py` |
| FR‑008 (Kruskal‑Wallis) | T007 | `grep "kruskal" code/analysis/stats.py` |
| SC‑001 (coverage) | T007 | `awk '{print $4}' data/results/aggregated_metrics.csv` (nominal level 0.95) |
| SC‑002 (bias) | T007 | `awk '{print $5}' data/results/aggregated_metrics.csv` |
| SC‑003 (compute limits) | T006, T008 | `grep "Peak RAM" logs/*.log` |
| SC‑004 (sensitivity) | T008 | `cat data/results/stability_analysis.json` |
| SC‑005 (associational framing) | T010 | `grep "associational" data/results/report.md` |

---  

All unchecked tasks remain pending implementation. Checked tasks have been previously validated and remain unchanged because they already satisfy their specifications.  