# Tasks: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

**Inputs**: `spec.md`, `plan.md`, `specs/001-asymptotic-behavior-of-random-matrix-eig/` (data‑model.md, contracts), existing source under `code/`, data under `data/`, and any reviewer feedback.

All previously verified foundational work (generators, solvers, basic orchestration) remains unchanged. The list below focuses on the remaining scientific work, fixing the issues highlighted by the verifier and completing the end‑to‑end study.

---

## Phase 1 – Foundations, schema validation & first end‑to‑end run  

- [ ] **T001** [US1] **Add missing contract files and schema‑validation test**  
  *Create the three JSON‑Schema files referenced in the specification ( `simulation_run.schema.yaml`, `eigenvalue_result.schema.yaml`, `aggregated_threshold.schema.yaml` ) under `contracts/`. Add a pytest module `tests/contract/test_schemas.py` that loads every file produced in `data/processed/` and validates it against the appropriate schema using `jsonschema`. The test must exit 0 on success.*  
  **Verification**:  
  · All three schema files exist at `contracts/…`.  
  · Running `pytest -q tests/contract/test_schemas.py` passes (exit 0).  

- [X] **T002** [US1] **Implement a reproducible single‑run end‑to‑end analysis with memory monitoring**  
  *Update `code/main.py` (or the current CLI entry point) so that the command*  

  ```bash
  python -m code.main --mode single --N 1000 --seed 42 --theta 2.5 --k 1 --pattern diagonal
  ```  

  *does the following:*  
  1. Generates (or loads) a Wigner matrix `data/raw/matrix_N1000_seed42.npy` using the scaling \(1/\sqrt N\).  
  2. Constructs a rank‑1 diagonal perturbation with spectral norm θ = 2.5.  
  3. Calls `scipy.sparse.linalg.eigsh` (ARPACK, `tol=1e-10`) to obtain the top 10 eigenvalues.  
  4. Determines `is_outlier` **solely by the theoretical rule** `value > 2.0 + 0.05`.  
  5. Writes a single JSON file `data/processed/single_run_results.json` that contains **both** a `SimulationRun` record and an array of ten `EigenvalueResult` records (nested under the same `run_id`).  
  6. Writes a checksum entry for the raw matrix in `data/checksums.yaml`.  
  7. Logs the full run to `data/logs/single_run.log`, including the peak memory usage (RSS) measured via `psutil` or `resource`.  
  8. **Enforce SC-001**: The script must raise an error and fail if the peak memory usage exceeds 7 GB.  
  9. Updates `quickstart.md` with the exact command line shown above.  

  **Verification** (performed by the CI after this task):  
  · `single_run_results.json` validates against the three schemas (via the test added in T001).  
  · `timestamp` is ISO‑8601, all required fields are present.  
  · A repeat of the command produces an identical top eigenvalue within 1e‑6.  
  · `data/logs/single_run.log` contains a "Peak Memory" entry $\le 7$ GB.  

- [ ] **T003** [US1] **Run the single‑run analysis and confirm reproducibility**  
  Executed `python -m code.main …` as specified in T002; top eigenvalue `2.901642355090901` reproduced on a fresh run; JSON validated; logs and checksum created.  

---

## Phase 2 – Full parameter sweep, validation, and aggregation  

- [X] **T004** [US2] **Correct the theta‑sweep script to use the theoretical outlier rule**  
  *Modify `code/analysis/threshold_sweep.py` so that every row written to `data/processed/mc_results.csv` records `outlier_flag` based on `value > 2.0 + 0.05` (the theoretical edge) rather than the empirical bulk edge. The script must also write the unchanged columns `run_id,N,k,pattern_type,theta,seed,eigenvalue_top,computation_time_ms`.*  
  **Verification**:  
  · `mc_results.csv` exists, row count equals 4 × 7 × 4 × 3 × 3 = 1008.  
  · A spot‑check of a few rows shows `outlier_flag` consistent with the theoretical rule.  

- [ ] **T005** [US2] **Re‑run the full theta sweep and produce validated CSV**  
  Execute the updated sweep script for the full grid (N ∈ {100,500,1000,2000}, θ ∈ {0.8,1.0,1.2,1.5,2.0,2.5,3.0}, seeds ∈ {42,123,456,789}, k ∈ {1,2,5}, pattern ∈ {diagonal,block‑sparse,random‑sparse}).  
  Output files:  
  · `data/processed/mc_results.csv` (with the new `outlier_flag`).  
  · `data/processed/convergence_data.json` (bulk‑edge convergence diagnostics).  

  **Verification**: same as T004 plus the schema‑validation test (T001) runs without error on the newly generated files.  

- [X] **T006** [US2] **Fit sigmoid curves and store statistical threshold estimates**  
  *Create `code/analysis/threshold_fit.py` (or extend the existing analysis module) that, for each configuration group (N, k, pattern_type), fits a logistic function to `outlier_flag` vs θ using `scipy.optimize.curve_fit`. Perform a 5‑fold cross‑validation over the seed dimension (split seeds into 5 folds, fit on 4, evaluate on 1, average the fitted `θ_c`). Write the results to `data/processed/threshold_statistical.json` following the schema shown in the plan.*  

  **Verification**: JSON is well‑formed, contains an entry for every (N,k,pattern) group (4 × 3 × 3 = 36), and each entry includes `theta_c_statistical` and a finite `confidence_interval`.  

- [ ] **T007** [US2] **Aggregate per‑configuration statistics into a contract‑compliant CSV**   <!-- FAILED-IN-EXECUTION: code/analysis/aggregate_thresholds.py exit=1 -->
  *Read `mc_results.csv` and `threshold_statistical.json`; for each (N,k,pattern) compute the fields required by `AggregatedThreshold` (total_runs, outlier_count, outlier_probability, mean_deviation, std_deviation, theta_c_estimate, theta_c_confidence). Write `data/processed/threshold_sweep_results.csv` (one row per group, 36 rows) and run the Pydantic‑based validator `code/analysis/validate_aggregated.py` which logs PASS/FAIL per row to `data/logs/aggregation_validation.txt`.*  

  **Verification**: CSV has exactly 36 rows; `aggregation_validation.txt` contains “PASS” for every row; the file validates against `aggregated_threshold.schema.yaml`.  

- [ ] **T008** [US3] **Run the density‑sensitivity sweep**  
  *Using the same sweep engine, execute a grid that varies `density` ∈ {0.1,0.2,0.3,0.4,0.5} for the random‑sparse pattern (k = 1, N ∈ {100,500,1000}, θ values as in the main sweep, seeds ∈ {42,123,456,789}). Output:*  
  · `data/processed/sensitivity_density_sweep.csv` (including `density` column and `outlier_flag` based on the theoretical rule).  
  · `data/processed/sensitivity_metadata.json` (records the full `PerturbationConfig` for each run).  

  **Verification**: row count = 3 × 5 × 7 × 4 = 420; schema test passes; a few rows manually inspected for correct `outlier_flag`.  

- [ ] **T009** [US3] **Compute critical‑threshold variation across densities**  
  *For each (density, N) pair, apply the 50 % crossing rule to the density sweep results to obtain `theta_c`. Write `data/processed/sensitivity_variation.csv` with columns `density,N,mean_theta_c,std_dev`. If fewer than three seeds are available for a pair, set `std_dev` to 0.0 and add a note in the CSV comment line.*  

  **Verification**: CSV has 15 rows (5 × 3); numeric columns are non‑negative; a spot‑check matches hand‑computed crossing.  

- [ ] **T010** [US3] **Generate figures and a concise sensitivity report**  
  *Create two PNG figures:*  
  · `data/figures/outlier_probability_vs_theta.png` – plots outlier probability vs θ for each pattern type (using `threshold_sweep_results.csv`).  
  · `data/figures/sensitivity_theta_c_vs_density.png` – plots `mean_theta_c` vs density for each N (using `sensitivity_variation.csv`).  
  *Write `data/processed/sensitivity_report.md` that (i) summarises empirical vs. statistical `θ_c` per pattern, (ii) describes the density effect, and (iii) cites the exact numeric values from the CSVs.*  

  **Verification**: Both PNG files open and contain non‑trivial plots; the markdown file contains at least one quoted number from each CSV.  

---

## Phase 3 – Finite-Size Analysis (N-sweep)

- [ ] **T011** [US4] **Execute finite-size N-sweep analysis**  
  *Implement `code/analysis/finite_size.py` to sweep matrix dimensions $N \in \{500, 1000, 1500, 2000\}$ for a representative subset of $(k, \theta, \text{pattern})$ configurations. For each $N$, compute the empirical bulk edge (99th percentile) and the probability of outlier emergence. Write the results to `data/processed/finite_size_results.csv` with columns `N, k, theta, pattern_type, empirical_bulk_edge, outlier_probability`.*  
  **Verification**:  
  · `finite_size_results.csv` exists and contains entries for all four $N$ values.  
  · The `empirical_bulk_edge` shows a clear convergence trend toward 2.0 as $N$ increases.  

---

## Phase 4 – Reproducible hand‑off  

- [ ] **T012** [US1] **Write the final methods & results manuscript**  
  *Create `research.md` containing:*  
  · A brief Methods section that points to the exact scripts (`code/main.py`, `code/analysis/...`).  
  · A Results section that hyperlinks to `data/processed/threshold_sweep_results.csv`, `threshold_statistical.json`, `sensitivity_variation.csv`, `finite_size_results.csv`, and the two PNGs.  
  · Quoted numeric findings (e.g., “for diagonal perturbations the empirical θ_c ≈ 1.62 ± 0.07”).  
  · A discussion of limitations (finite‑size effects as quantified in T011, seed count, CPU‑only ARPACK tolerance).  

  **Verification**: The markdown file contains at least one hyperlink to each of the six key artifacts and at least one numeric quote from each artifact.  

- [ ] **T013** [US1] **Full reproducibility run & test suite pass**  
  *From a fresh clone, follow the steps in `quickstart.md` (install deps, run `python -m code.main --mode sweep`, then `python -m code.analysis.threshold_fit`, `python -m code.analysis.validate_aggregated`, and `python -m code.analysis.finite_size`).*  
  *Execute the entire pytest suite (`pytest -q`).*  
  *Record the console output and any errors to `data/logs/full_rerun.log`.*  

  **Verification**:  
  · All tests (unit, integration, schema) exit with status 0.  
  · `full_rerun.log` exists and contains the line “Sanity check Δ ≤ 1e‑6”.  
  · All generated artifacts match those referenced in `research.md`.  

---

## Dependencies & Requirement Coverage

| Spec / FR / SC requirement | Satisfying task(s) |
|----------------------------|--------------------|
| **Objective 1** – Wigner generation, scaling | T002, T003 |
| **Objective 2** – Sparse perturbations (rank, pattern) | T002, T008 |
| **Objective 3** – Top‑10 eigenvalues (ARPACK) | T002, T003 |
| **Objective 4** – θ‑sweep & critical threshold | T004, T005, T006, T007 |
| **Objective 5** – Sparsity‑density sensitivity | T008, T009, T010 |
| **FR‑004** – Outlier detection rule (theoretical edge ± 0.05) | T002, T004, T008 |
| **FR‑007** – Observational study (no observer model) | T012 |
| **SC‑001** – Memory ≤ 7 GB (CPU‑only) | T002 (enforcement), All tasks |
| **SC‑002** – CPU‑only execution | All tasks (no CUDA) |
| **SC‑003** – Reproducibility via seeds & checksums | T001, T002, T013 |
| **SC‑004** – Eigenvalue convergence tolerance 1e‑10 | T002, T003 |
| **SC‑005** – Output conforms to JSON/YAML contracts | T001, T002, T005, T006, T007 |
| **SC‑006** – Data‑hygiene (checksums) | T001, T002, T013 |
| **SC‑007** – Numerical stability (ARPACK params) | T002, T003 |
| **Phase 7** – Finite-Size N-sweep analysis | T011 |

All tasks respect the platform’s conventions: outputs reside under `data/processed/`, `data/figures/`, `data/logs/`, and source code under `code/`. No `state/` paths are used, and no GPU resources are requested.