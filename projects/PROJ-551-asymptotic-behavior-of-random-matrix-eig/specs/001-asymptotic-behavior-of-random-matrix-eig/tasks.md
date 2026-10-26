# Tasks: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

## Functional Requirements (FR)

| ID   | Description |
|------|-------------|
| FR-001 | Generate large Wigner matrices with standard scaling \(1/\sqrt{N}\). |
| FR-002 | Apply sparse deterministic perturbations of configurable rank, pattern, and support density. |
| FR-003 | Compute top eigenvalues using ARPACK (tol = 1e‑10, maxiter = 1000). |
| FR-004 | Detect outliers using the rule \( \lambda > 2 + \tau(N)\) where \(\tau(N)=\max(0.05, 2N^{-2/3})\). |
| FR-005 | Sweep perturbation norm \(\theta\) over a grid that includes sub‑threshold values. |
| FR-006 | Perform sensitivity analyses for sparsity density and finite‑size effects. |
| FR-007 | Frame the study as observational; no observer model is required. |

## Requirement Coverage Table

| Requirement | Covered by Task(s) |
|-------------|--------------------|
| FR-001 | T002 |
| FR-002 | T002, T007 |
| FR-003 | T002, T003 |
| FR-004 | T002, T004, T007 |
| FR-005 | T004 |
| FR-006 | T007, T008, T009 |
| FR-007 | T011 |
| SC-001 (Memory ≤ 7 GB) | T002 |
| SC-002 (CPU‑only) | All tasks |
| SC-003 (Reproducibility) | T001, T002, T003, T012 |
| SC-004 (ARPACK tol = 1e‑10, maxiter = 1000) | T002, T003 |
| SC-005 (Schema‑conformant artifacts) | T001, T002, T004‑T015 |
| SC-006 (Write‑then‑verify discipline) | T001‑T015 |

## Phase 0 – Artifact‑writing discipline (REPAIR)

- [ ] T001 [US1] **Add canonical artifact writer and comprehensive contract tests** <!-- FAILED-IN-EXECUTION: code/run_tests.py exit=1 -->
  *Create `code/utils/artifacts.py` with `write_artifact(path, data, schema_name)` that validates `data` against the contract in `specs/…/contracts/` before writing, writes JSON, appends SHA‑256 to `data/checksums.yaml`, and prints path + checksum. Add new contracts `threshold_fit.schema.yaml` (ThresholdFit) and `perturbation_verification.schema.yaml` (Verification of θ and sparsity).*
  *Rewrite `code/tests/contract/test_schemas.py` to include ONE test per artifact file:*
  - `single_run_results.json` (SimulationRun + EigenvalueResult array)
  - `convergence_report.json`
  - `sweep_runs.parquet`
  - `aggregated_thresholds.json`
  - `threshold_fit.json`
  - `sensitivity_density_sweep.parquet`
  - `sensitivity_metadata.json`
  - `sensitivity_variation.csv`
  - `sensitivity_variation_notes.json`
  - `finite_size_results.csv`
  *Missing files cause FAIL; no SKIP branches. All tests must load the REAL file and validate against its schema via `jsonschema` or column‑level checks for Parquet/CSV.*

## Phase 1 – Core execution and verification

- [ ] T002 [US1] **Single‑run mode routed through artifact writer and perturbation verification**
  *Update `python -m code.main --mode single --N 1000 --seed 42 --theta 2.5 --k 1 --pattern diagonal` so that each run:*
  1. *Generates Wigner matrix and sparse perturbation Pₙ, then verifies* **‖Pₙ‖₂** *matches the requested θ within 1e‑6 and that the sparsity pattern matches the declared type and support density. Record results in `data/processed/perturbation_verification.json` (validated by `perturbation_verification.schema.yaml`).*
  2. *Writes `data/processed/single_run_results.json` (SimulationRun + `eigenvalue_results` array) via `write_artifact`.*
  3. *Writes the matrix checksum to `data/checksums.yaml`.*
  4. *Writes `data/processed/convergence_report.json` (including ARPACK status, tolerance, maxiter, bulk edge check, matrix checksum, and `schema_validation: "pass"`).*
  5. *Echoes each artifact path and checksum to stdout.*
  *Update `quickstart.md` with the exact command.*

- [ ] T003 [US1] **Reproducibility integration test**
  *Rewrite `code/tests/integration/test_t001.py` to re‑run the reference single‑run configuration and assert:*
  (a) *Top eigenvalue matches 2.901642355091 ± 1e‑6;*
  (b) *Regenerated `single_run_results.json` is byte‑identical to the stored reference after normalizing the `timestamp` field (excluded from comparison).*

## Phase 2 – Parameter sweep, aggregation, and fitting

- [ ] T004 [US2] **Sweep engine writes schema‑validated Parquet** <!-- FAILED-IN-EXECUTION: code/analysis/sweep.py exit=1 -->
  *Modify `code/analysis/sweep.py` to write `data/processed/sweep_runs.parquet` containing both `SimulationRun` rows (1,152 records) **and** associated `EigenvalueResult` rows (11,520 records). Validation is performed column‑wise against the entity field definitions before writing. All θ values (including < 1) are retained. Empty input or failed run raises a clear exception.*

- [ ] T005 [US2] **Aggregation script (REPAIR of rejected T007)**
  *Fix `code/analysis/aggregate_thresholds.py` to read the sweep Parquet, group by (N, k, pattern_type, θ) **excluding** any θ_c fields, and write `data/processed/aggregated_thresholds.json` via `write_artifact`. On empty input, raise a descriptive error before exiting.*

- [ ] T006 [US2] **Threshold‑fit script (REPAIR of rejected T006)**
  *Update `code/analysis/threshold_fit.py` to read raw sweep records, fit a logistic function*  
  \[
  f(\theta)=\frac{1}{1+\exp[-a(\theta-\theta_c)]}
  \]
  *For each (N, k, pattern_type) group, compute:*
  - *`theta_c_estimate` (MLE of θ_c)*
  - *`theta_c_confidence` (95 % CI half‑width from 5‑fold seed bootstrap)*
  - *`a` (slope)*
  - *`b = a * theta_c_estimate` (intercept for the equivalent form \(1/(1+\exp[-(a\theta+b)])\)), satisfying the `b` field in the schema.*
  *Non‑convergent fits produce `fit_status: "failed"` and null for all numeric fields. Output `data/processed/threshold_fit.json` validated against `threshold_fit.schema.yaml`.*

- [ ] T007 [US2] **Density‑sensitivity sweep**
  *Extend the sweep engine via `code/analysis/sensitivity.py` to vary support density p ∈ {0.1,…,0.5} for the random‑sparse pattern (k=1, N ∈ {100,500,1000}). Write `data/processed/sensitivity_density_sweep.parquet` and `data/processed/sensitivity_metadata.json` via `write_artifact`.*

- [ ] T008 [US3] **Sensitivity‑variation estimator (cross‑threshold)**
  *Create `code/analysis/sensitivity_variation.py` to compute, for each (density, N) pair, the θ value where outlier probability crosses 50 % (linear interpolation). Write:*
  - *`data/processed/sensitivity_variation.csv` (columns: density,N,mean_theta_c,std_dev)*
  - *`data/processed/sensitivity_variation_notes.json` (explanatory notes, schema‑validated).*
  *These outputs are schema‑validated via tasks T014/T015. The sigmoid‑fit estimator (ThresholdFit) is declared the **authoritative** θ_c for the manuscript; the crossing‑rule values are provided for illustration only (see T011).*

- [ ] T009 [US3] **Finite‑size analysis**
  *Implement `code/analysis/finite_size.py` to sweep N ∈ {500,1000,1500,2000} for representative configurations. Write `data/processed/finite_size_results.csv` (columns: N,k,theta,pattern_type,empirical_bulk_edge,outlier_probability) via `write_artifact`. A corresponding schema is added in T015.*

## Phase 3 – Additional schema & contract support

- [ ] T014 [US2] **Create schemas for sensitivity‑variation and finite‑size CSV outputs**
  *Add `sensitivity_variation.schema.yaml` (columns matching the CSV) and `finite_size_results.schema.yaml`. Register them in the contract test suite.*

- [ ] T015 [US2] **Add contract tests for the new CSV/JSON artifacts**
  *Extend `code/tests/contract/test_schemas.py` with validators for `sensitivity_variation.csv`, `sensitivity_variation_notes.json`, and `finite_size_results.csv` using the schemas from T014.*

## Phase 4 – Figures, documentation, and full reproducibility

- [ ] T010 [US4] **Generate figures and evidence summary**
  *Create `code/analysis/figures.py` to produce:*
  - *`data/figures/outlier_probability_vs_theta.png` (from `aggregated_thresholds.json`).*
  - *`data/figures/sensitivity_theta_c_vs_density.png` (mean θ_c from `sensitivity_variation.csv`).*
  - *`data/figures/finite_size_convergence.png` (bulk edge vs N from `finite_size_results.csv`).*
  *Write `data/processed/evidence_summary.md` quoting exact numbers from the source artifacts.*

- [ ] T011 [US1] **Methods & Results manuscript**
  *Write `research.md` with:*
  - *Methods linking to scripts (`code/main.py`, `code/analysis/*.py`).*
  - *Results linking to all validated artifacts, quoting at least one numeric value from each (including the authoritative `theta_c_estimate` from `threshold_fit.json`).*
  - *Limitations discussion referencing Constitution VII (perturbation verification) and finite‑size effects (T009).*

- [ ] T012 [US1] **Full reproducibility run and test‑suite pass**
  *From `quickstart.md`, execute the complete workflow (single run, sweep, aggregation, threshold fit, sensitivity, finite‑size, figures). Run `pytest -q code/tests/`. Capture console output to `data/logs/full_rerun.log`.*

- [ ] T013 [US2] **Perturbation verification artifact**
  *After constructing each perturbation matrix, compute its spectral norm and sparsity statistics, compare to the requested θ and pattern specification, and write `data/processed/perturbation_verification.json` (validated by `perturbation_verification.schema.yaml`). This satisfies Constitution VII.*
