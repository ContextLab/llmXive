# Tasks: Asymptotic Behavior of Random Matrix Eigenvalues with Sparse Perturbations

**Inputs**: Active `spec.md`, `plan.md`, `specs/001-asymptotic-behavior-of-random-matrix-eig/` (data-model.md, contracts/), prior verified artifacts under `code/`, `data/`, and prior reviewer/verifier feedback.

All previously completed foundational tasks (generators, solvers, models, grids, orchestrator, documentation) remain unchanged and verified. The remaining open work focuses on execution, validation, and reproducible reporting.

## Task format and paths

- `- [ ] T### [P?] [USx?] description with exact artifact paths`.
- Paths are relative to the project root. Source lives in `code/`, results in `data/processed/`, figures in `data/figures/`, logs in `data/logs/`. No `state/` paths are used.

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US1] **REDO (rejected artifact)**: Run a single‑run end‑to‑end analysis and record its results to `data/processed/single_run_results.json` by executing  

  ```bash
  code/main.py --mode single --N 1000 --seed 42 --theta 2.5 --k 1 --pattern diagonal
  ```

  The script loads the checksummed raw matrix `data/raw/matrix_N1000_seed42.npy`, builds a rank‑1 diagonal perturbation with spectral norm θ = 2.5, computes the top 10 eigenvalues with ARPACK (`scipy.sparse.linalg.eigsh`), and writes a JSON document that **fully conforms** to the `SimulationRun` and `EigenvalueResult` contracts:

  ```json
  {
    "run_id": "<uuid>",
    "timestamp": "<ISO‑8601>",
    "seed": 42,
    "N": 1000,
    "k": 1,
    "theta": 2.5,
    "pattern_type": "diagonal",
    "support_density": null,
    "computation_time_ms": <float>,
    "empirical_bulk_edge": <float>,
    "eigenvalues": [
      {
        "run_id": "<same uuid>",
        "eigenvalue_index": 1,
        "value": <float>,
        "is_outlier": <bool>,
        "theoretical_bbp": 2.5 + 1/2.5,
        "deviation": <float>
      },
      … (indices 2‑10)
    ]
  }
  ```

  **Verification**:  
  (a) the JSON validates against both `simulation_run.schema.yaml` and `eigenvalue_result.schema.yaml`;  
  (b) `timestamp` is present and ISO‑8601 formatted;  
  (c) each eigenvalue entry contains the matching `run_id`;  
  (d) a deterministic reproducibility check re‑runs the same command and asserts the recorded top eigenvalue matches the newly computed one within 1e‑6;  
  (e) the outlier rule follows FR‑004 (`value > empirical_bulk_edge + 0.05`).  
  The command is also listed in `quickstart.md` and logs are written to `data/logs/simulation_run.log`.

## Phase 2: Complete the study and validate its evidence

- [ ] T002 [US2] **REDO (rejected artifact)**: Execute the theta sweep using `code/analysis/threshold_sweep.py` over the grid:

  - **N** ∈ {100, 500, 1000, 2000}  
  - **θ** ∈ {0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0}  *(includes values below the theoretical BBP threshold)*  
  - **seeds** ∈ {42, 123, 456, 789}  
  - **k** ∈ {1, 2, 5}  
  - **pattern_type** ∈ {diagonal, block-sparse, random-sparse}

  The orchestrator consumes checksummed raw matrices and writes:

  - `data/processed/mc_results.csv` with columns `run_id,N,k,pattern_type,theta,seed,eigenvalue_top,empirical_bulk_edge,computation_time_ms`.  
  - `data/processed/convergence_data.json` recording per‑N bulk‑edge convergence toward ±2.0.

  **Verification**: both files exist, are non‑empty, and the CSV row count equals 4 × 7 × 4 × 3 × 3 = 1008 rows. Every `eigenvalue_top` is a real ARPACK result.

- [ ] T003 [US2] **REDO (rejected artifact)**: Apply the strict‑tolerance outlier rule (FR‑004) to every row of `mc_results.csv` and write `data/processed/validated_sweep_results.csv` with an additional boolean column `outlier_flag` recomputed from `eigenvalue_top` and `empirical_bulk_edge`.  
  **Verification**: file exists, row count matches `mc_results.csv`, and each `outlier_flag` is consistent with the 0.05 rule.

- [ ] T004 [US2] **REDO (rejected artifact)**: Identify the empirical critical threshold `theta_c_empirical` for each configuration group (N, k, pattern_type) by selecting the **smallest** swept θ where the outlier probability (fraction of runs with `outlier_flag=True`) is **≥ 0.5**. Write `data/processed/threshold_identification.json`:

  ```json
  {
    "groups": [
      {"N":100,"k":1,"pattern_type":"diagonal","theta_c_empirical":1.5,"method":"empirical_50pct_crossing"},
      …
    ],
    "overall_theta_c": 1.8
  }
  ```

  **Verification**: JSON is valid, every (N,k,pattern) appears, and each `theta_c_empirical` is one of the swept θ values.

- [ ] T005 [US2] **REDO (rejected artifact)**: Fit a sigmoid curve to the outlier probability vs θ for each (N, k, pattern_type) using **SciPy’s `curve_fit`** (no external scikit‑learn dependency). Perform 5‑fold cross‑validation manually by splitting the seed dimension. Write `data/processed/threshold_statistical.json`:

  ```json
  {
    "groups": [
      {
        "N":100,
        "k":1,
        "pattern_type":"diagonal",
        "theta_c_statistical":1.62,
        "confidence_interval":[1.55,1.69],
        "method":"sigmoid_curve_fit_5cv"
      },
      …
    ]
  }
  ```

  **Verification**: JSON is valid, confidence intervals are finite and ordered, and each `theta_c_statistical` is compared to the empirical value in the aggregation step.

- [ ] T006 [US2] **REDO (rejected artifact)**: **Aggregate** validated sweep results **per configuration group** (N, k, pattern_type) into `data/processed/threshold_sweep_results.csv` that conforms to the `AggregatedThreshold` contract. For each group we compute:

  - `total_runs` = number of seeds × number of θ values (4 × 7 = 28)  
  - `outlier_count` = sum of runs with any outlier (as identified in T003)  
  - `outlier_probability` = outlier_count / total_runs  
  - `mean_deviation` / `std_deviation` = statistics of `deviation` from `EigenvalueResult` for outlier runs  
  - `theta_c_estimate` / `theta_c_confidence` = values from T005 (repeated for each row of the group)

  The CSV therefore has **one row per (N, k, pattern_type) group** (4 × 3 × 3 = 36 rows). Run `code/analysis/validate_data.py` to instantiate Pydantic models for each row and write `data/logs/validation_log.txt` with PASS/FAIL per row.  
  **Verification**: CSV exists, 36 rows, all rows PASS validation against `aggregated_threshold.schema.yaml`.

- [ ] T007 [US3] **REDO (rejected artifact)**: Execute the density‑sensitivity sweep with `code/analysis/threshold_sweep.py --grid-file data/configs/density_grid.json --grid-type density`. The grid file now contains an explicit specification:

  ```json
  {
    "theta_values": [0.8,1.0,1.2,1.5,2.0,2.5,3.0],
    "densities": [0.1,0.2,0.3,0.4,0.5],
    "N_values": [100,500,1000],
    "k": 1,
    "pattern_type": "random-sparse",
    "seeds": [42,123,456,789]
  }
  ```

  The orchestrator writes:

  - `data/processed/sensitivity_density_sweep.csv` (columns `run_id,N,k,pattern_type,density,theta,seed,eigenvalue_top,outlier_flag`)  
  - `data/processed/sensitivity_metadata.json` recording the `PerturbationConfig` for each run.  

  **Verification**: both files exist, non‑empty, and row count equals 3 × 5 × 7 × 4 = 420 rows.

- [ ] T008 [US3] **REDO (rejected artifact)**: Compute variation of the critical threshold across densities. For each (density, N) pair, use the 50 % crossing rule (as in T004) to obtain `theta_c`. Write `data/processed/sensitivity_variation.csv`:

  ```csv
  density,N,mean_theta_c,std_dev
  0.1,100,1.52,0.00
  0.2,100,1.55,0.00
  …
  ```

  If fewer than three seeds are available for a given (density, N) the `std_dev` column is set to `0.0` with a note that the estimate is based on limited data.  
  **Verification**: file exists, one row per (density,N) (5 × 3 = 15 rows), numeric values present, std_dev ≥ 0.0.

- [ ] T009 [US2/US3] **REDO (rejected artifact)**: Generate figures and a sensitivity report:

  - `data/figures/outlier_probability_vs_theta.png` (outlier probability vs θ per pattern type, from `threshold_sweep_results.csv`).  
  - `data/figures/sensitivity_theta_c_vs_density.png` (θ_c vs density, from `sensitivity_variation.csv`).  
  - `data/processed/sensitivity_report.md` summarizing the empirical and statistical θ_c estimates, stating whether density shifts the threshold and quoting actual numbers.  

  **Verification**: PNGs are non‑trivial image files; the markdown cites concrete values from the CSVs.

## Phase 3: Reproducible results and paper handoff

- [ ] T010 Write a concise methods/results account in `research.md` (preserving existing sections) and add a **Results** section that references the actual artifacts:

  `data/processed/threshold_sweep_results.csv`, `threshold_identification.json`, `threshold_statistical.json`, `sensitivity_variation.csv`, and the two PNGs. Quote the empirical `theta_c` per pattern and the observed density effect, and discuss limitations (finite N, seed count, CPU‑only ARPACK).  

  **Verification**: the document contains hyperlinks to each artifact and includes at least one quoted numeric value from each.

- [ ] T011 Re‑run the documented workflow from `quickstart.md`, confirm all unit and integration tests pass (`tests/unit/`, `tests/integration/test_sweep.py`), and verify the deterministic sanity check (N = 100, θ = 2.5, seed = 42) reproduces the top eigenvalue within 1e‑6 of the baseline. Log the full re‑run under `data/logs/rerun.log`.  

  **Verification**: test suite passes, `rerun.log` exists, and the sanity‑check delta is recorded and ≤ 1e‑6.

## Dependencies and requirement coverage

| Requirement (Spec Objective / Key Assumption) | Tasks |
|---|---|
| Objective 1 (Wigner generation, scaling) | T001, T002 |
| Objective 2 (Sparse perturbations, rank & pattern) | T002, T007 |
| Objective 3 (Top eigenvalue computation) | T001, T002 |
| Objective 4 (θ sweep & critical threshold) | T002–T006 |
| Objective 5 (Sparsity density sensitivity) | T007–T009 |
| FR‑004 (outlier detection rule) | T001, T003, T007, T008 |
| FR‑007 (observational nature) | T010 |
| Validation criteria (semicircle edge, reproducibility) | T001, T011 |
| CPU‑only execution & real data usage | All tasks (explicitly state CPU‑only) |
| No GPU acceleration | All tasks (CPU‑only solvers) |

All tasks respect CPU‑only execution, real data usage, and the constitution’s reproducibility and data‑hygiene principles.
