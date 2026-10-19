# Tasks: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, existing project skeleton.  

## Phase 1 – Project scaffolding & foundational utilities  

- [ ] T001 [P] Create the full project directory tree under `projects/PROJ-505-exploring-the-statistical-relationship-b/`  

  ```text
  projects/PROJ-505-exploring-the-statistical-relationship-b/
  ├─ code/
  │  ├─ ingestion/
  │  ├─ analysis/
  │  └─ utils/
  ├─ data/
  │  ├─ raw/
  │  ├─ processed/
  │  └─ artifacts/
  └─ tests/
     ├─ unit/
     └─ integration/
  ```  

  **Verification** – Run `find … -type d` and confirm that every directory listed above exists (exit code 0).

- [ ] T002 [P] Fix `requirements.txt` so that **every** line follows the pattern `package==major.minor.*` (no version ranges, no extra packages).  

  **File**: `requirements.txt` (project root) – must contain only the pinned core scientific stack, e.g.:  

  ```
  pandas==2.2.*
  numpy==2.0.*
  scikit-learn==1.5.*
  statsmodels==0.14.*
  scipy==1.14.*
  pytest==8.3.*
  fastparquet==2024.*
  pyarrow==15.0.*   # optional fallback, still pinned
  ```  

  The previously‑present line `pyarrow>=15.0.0` has been removed/changed to the pinned format.  

  **Verification** – CI runs a regex check: each non‑comment line must match `^[a-zA-Z0-9_-]+==[0-9]+\.[0-9]+\.\*$`.

- [ ] T003 [P] Add a lightweight configuration module defining the random seed and canonical data‑path constants.  

  **File**: `code/config.py`  

  ```python
  from pathlib import Path

  SEED = 42
  RAW_DIR   = Path(__file__).resolve().parents[2] / "data" / "raw"
  PROC_DIR  = Path(__file__).resolve().parents[2] / "data" / "processed"
  ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "data" / "artifacts"
  ```  

  **Verification** – `python -c "import code.config; assert code.config.SEED == 42"` succeeds.

- [ ] T004 [P] Refactor `code/utils/io.py` so that Parquet I/O works even when `pyarrow` is unavailable.  

  *Implementation notes* – attempt `import pyarrow` inside a `try/except`; if unavailable, fall back to `fastparquet`. Provide the functions `load_parquet(path)`, `save_parquet(df, path)`, and `sha256_checksum(path)` that raise a clear error **only if both engines are missing**.  

  **Verification** – Unit tests `tests/unit/test_io.py` must pass on a runner without `pyarrow`; they check that `save_parquet` creates a file, `load_parquet` reads it back identically, and the checksum matches.

## Phase 2 – Data ingestion & alignment (User Story 1, **P1**)  

- [ ] T005 [US1] Implement robust real‑data download scripts for ACE composition and NOAA geomagnetic indices.  

  **Files**: `code/ingestion/download_ace.py`, `code/ingestion/download_noaa.py`  

  *Behavior* – each script performs an HTTP GET to the official CDAWeb/NOAA endpoint, writes the raw response bytes unchanged to `data/raw/` (e.g., `ace_YYYYMMDD.cdf`), parses the needed columns, and raises `ConnectionError` on any network failure.  

  **Verification** – Integration test `tests/integration/test_download_real.py` asserts that on successful download a raw file exists with matching SHA‑256 checksum and that parsing yields the three composition columns without NaNs. When the endpoint is unreachable the script must raise `ConnectionError` (checked via a mock‑failure test).

- [ ] T006 [US1] Implement a deterministic synthetic data generator that produces a 20‑year hourly dataset conforming to the `SolarWindGeomagneticDataset` schema.  

  **File**: `code/ingestion/generate_synthetic_data.py`  

  *Key points* – uses `np.random.default_rng(SEED)`, stores generation parameters in `data/raw/synthetic_config.yaml`, writes `data/processed/synthetic_aligned.parquet`. All required columns are present, contain no NaNs, and respect realistic physical ranges (e.g., velocity 300‑800 km s⁻¹).  

  **Verification** – After execution, `tests/unit/test_synthetic.py` loads the parquet file, runs a schema validation against `contracts/dataset.schema.yaml`, and confirms the row count ≈ 175 k (20 yr × 8760 h) and absence of missing values.

- [ ] T007 [US1] Create the alignment/orchestration script that  

  1. Tries `download_ace.py` and `download_noaa.py`;  
  2. On any `ConnectionError` invokes `generate_synthetic_data.py`;  
  3. Merges composition and geomagnetic streams;  
  4. Resamples to a strict 1‑hour grid using **hourly median**;  
  5. Enforces a maximum temporal offset ≤ 30 minutes;  
  6. Flags any gap > 6 h;  
  7. Applies a small epsilon floor (`1e‑6`) to avoid division‑by‑zero in ratio calculations.  

  **File**: `code/ingestion/align.py`  

  **Verification** – `tests/unit/test_align.py` checks that the output DataFrame (`aligned.parquet`) has exactly one row per hour, monotonic timestamps, `max_offset_minutes ≤ 30`, and that any > 6 h gaps are recorded in `data/artifacts/alignment_report.json`.

- [ ] T021 [US1] Generate an alignment verification report (`data/artifacts/alignment_report.json`) summarizing the maximum temporal offset, any > 6 h gaps, and confirming the ≤ 30 min constraint is satisfied.  

  **Verification** – Unit test asserts the JSON contains fields `max_offset_minutes` (≤ 30) and `gap_hours` (list, each ≤ 6).

## Phase 3 – Feature engineering & regression (User Story 2, **P2**)  

- [ ] T016 [US2] Produce a dedicated aligned dataset for regression (`data/processed/aligned_for_us2.parquet`).  

  **Verification** – Same checks as T007; the file must exist and pass schema validation.

- [ ] T008 [US2] Derive the two standard coupling functions (Akasofu ε and Newell F) from bulk solar‑wind parameters.  

  **File**: `code/analysis/coupling_functions.py`  

  **Verification** – `tests/unit/test_coupling.py` validates that for a hand‑crafted input row the computed ε and Newell values match published formulas to within `1e‑6`.

- [ ] T009 [US2] Fit baseline and full multivariate linear regression models, compute VIF for every predictor, and emit a warning artifact for any VIF ≥ 5.  

  **File**: `code/analysis/regression.py`  

  *Outputs* – `data/artifacts/baseline_model.json`, `data/artifacts/full_model.json`, `data/artifacts/vif_warnings.txt`.  

  **Verification** – `tests/integration/test_regression.py` asserts both JSON files exist, contain coefficient dictionaries for all predictors, and that `vif_warnings.txt` is empty or lists only predictors with VIF ≥ 5.

- [ ] T010 [US2] Perform 5‑fold time‑series cross‑validation for both models, compute out‑of‑sample R², and calculate the incremental ΔR².  

  **File**: `code/analysis/cross_validation.py`  

  *Output* – `data/artifacts/cv_metrics.json` with keys `baseline_r2`, `full_r2`, `delta_r2`.  

  **Verification** – Unit test checks that `delta_r2` equals `full_r2 - baseline_r2` within `1e‑8`.

- [ ] T018 [US2] Compute a 95 % confidence interval for ΔR² via bootstrap (10 000 resamples) and store results in `data/artifacts/delta_r2_ci.json`.  

  **Verification** – Test confirms the JSON contains `ci_lower`, `ci_upper`, and that `ci_lower < delta_r2 < ci_upper`.

## Phase 4 – Significance testing & sensitivity (User Story 3, **P3**)  

- [ ] T017 [US3] Run baseline and full regressions specifically for the permutation‑test stage, persisting the fitted model objects.  

  **Outputs** – `data/artifacts/regression_us3_baseline.pkl`, `data/artifacts/regression_us3_full.pkl`.  

  **Verification** – Test loads both pickles and checks that each has a `params` attribute containing the expected coefficient names.

- [ ] T011 [US3] Implement a block permutation test (24‑hour blocks, ≥ 1 000 iterations) that stops early when the standard error of the p‑value falls below 0.001 or when 10 000 iterations are reached.  

  **File**: `code/analysis/permutation_test.py`  

  *Outputs* – `data/artifacts/permutation_o_fe.json`, `permutation_he_h.json`, `permutation_c_o.json` (each with `observed_coef`, `null_distribution`, `p_value`).  

  **Verification** – `tests/unit/test_permutation.py` confirms the stopping criterion and that each JSON file contains the required fields.

- [ ] T019 [US3] Evaluate significance by checking whether each observed coefficient lies outside the 95 % percentile range of its null distribution; record boolean flags in `data/artifacts/percentile_significance.json`.  

  **Verification** – Test asserts that for each ratio the flag matches the percentile‑range rule.

- [ ] T012 [US3] Conduct a sensitivity sweep over significance thresholds `{0.01, 0.05, 0.10}` applying the Benjamini‑Hochberg FDR correction across the six hypothesis tests (three ratios × two indices).  

  **File**: `code/analysis/sensitivity.py`  

  *Output* – `data/artifacts/fdr_results.csv` (`hypothesis, raw_p, fdr_p, significant`).  

  **Verification** – Integration test checks that for each threshold the number of rows with `significant=True` is reported and that the CSV is well‑formed.

- [ ] T020 [US3] Summarize stability of significance findings across the three thresholds, producing `data/artifacts/threshold_stability.csv` with columns `threshold, num_significant_predictors`.  

  **Verification** – Test confirms three rows (one per threshold) and that the counts are non‑negative integers.

## Phase 5 – Orchestration, reporting & documentation  

- [ ] T013 [P] Write the top‑level driver that executes the full pipeline in the correct order, captures any `ConnectionError` to trigger the synthetic fallback, and writes a consolidated JSON report.  

  **File**: `code/main.py`  

  *Key fields in `data/artifacts/final_report.json`* –  

  - `source_type` (`"Synthetic"` or `"Real"`),  
  - `fetch_attempts` (list of URL + status),  
  - `model_summary` (`delta_r2`, `baseline_r2`, `full_r2`, CI bounds),  
  - `significance_summary` (list of significant predictors after FDR),  
  - `threshold_stability` (reference to `threshold_stability.csv`).  

  **Verification** – Running `python -m code.main` exits with status 0 and the JSON contains `source_type` set appropriately (expected `"Synthetic"` for this project) and all top‑level keys.

- [ ] T014 [P] Update project documentation to be transparent about the data gap and the synthetic fallback, and provide a quick‑start guide that runs the pipeline and checks success.  

  **Files**: `README.md`, `quickstart.md`  

  - `README.md` must contain the sentence: “**Data gap**: verified ACE SWICS and NOAA Dst/Kp sources are unavailable; the pipeline therefore uses synthetic data.”  
  - `quickstart.md` lists the single command `python -m code.main` and instructs the verifier to assert that `data/artifacts/final_report.json` exists and contains `source_type`.  

  **Verification** – `tests/integration/test_quickstart.py` runs the command, checks exit code 0, and validates the JSON field.

- [ ] T015 [P] Execute the complete end‑to‑end run on the synthetic dataset and confirm that all expected artefacts are present and internally consistent.  

  **Artifacts to check**:  

  * `data/artifacts/baseline_model.json` & `full_model.json` (contain coefficients for all predictors)  
  * `data/artifacts/cv_metrics.json` (`delta_r2` > 0)  
  * `data/artifacts/permutation_*.json` (each has a `p_value` between 0 and 1)  
  * `data/artifacts/fdr_results.csv` (at least one row marked `significant` for the 0.05 threshold)  
  * `data/artifacts/delta_r2_ci.json` (CI fields present and enclose `delta_r2`)  
  * `data/artifacts/threshold_stability.csv` (three rows)  
  * `data/artifacts/final_report.json` (matches description in T013)  

  **Verification** – Dedicated integration test `tests/integration/test_e2e.py` runs `code/main.py` and asserts existence, schema, and logical consistency of each file (e.g., `delta_r2` equals `full_r2 - baseline_r2`; CI bounds contain `delta_r2`).

## Dependency & execution order summary  

| Task | Depends on |
|------|------------|
| T001–T004 | – (initial scaffolding) |
| T005–T007 | T001–T004 |
| T021 | T007 |
| T016 | T001–T004 (runs its own alignment) |
| T008 | T016 |
| T009 | T008 |
| T010 | T009 |
| T018 | T010 |
| T017 | T001–T004 (independent regression for permutation stage) |
| T011 | T017 |
| T019 | T011 |
| T012 | T011 |
| T020 | T012 |
| T013 | T005–T012, T018, T019, T020 |
| T014 | – (can be written after T013) |
| T015 | T013 (full pipeline) |

All tasks now satisfy every functional requirement (FR‑001 → FR‑011), address all success criteria (SC‑001 → SC‑004), respect the Constitution (raw synthetic files are preserved, no fabricated data), and provide independently shippable units for each user story. Unchecked boxes indicate work that remains to be implemented; once a verification test passes the CI system will automatically mark the task as completed.
