# Tasks: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Input**: `spec.md`, `plan.md`, `data-model.md`, existing project skeleton.  
**Goal**: Build a reproducible end‑to‑end pipeline that (a) creates the required directory layout, (b) fetches real data when possible and falls back to a documented synthetic generator, (c) aligns the time series, (d) derives coupling functions, (e) fits baseline and full multivariate regressions, (f) validates significance with block permutation and sensitivity analysis, and (g) produces a final JSON report that explicitly labels the data source. All steps must be verifiable by concrete file‑system artefacts or automated tests.

---

## Phase 1 – Project scaffolding & foundational utilities  

- [X] **T001** [P] Create the full project directory tree under `projects/PROJ-505-exploring-the-statistical-relationship-b/`  

  ```
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

  **Verification** – Run a shell command (e.g. `find … -type d`) and confirm that every directory listed above exists (exit code 0).

- [X] **T002** Initialize a Python project with a pinned `requirements.txt` containing the core scientific stack.  

  **File**: `requirements.txt` (project root)  

  ```
  pandas==2.2.*
  numpy==1.26.*
  scikit-learn==1.5.*
  statsmodels==0.14.*
  scipy==1.13.*
  pytest==8.2.*
  ```  

  **Verification** – File exists and each line matches the pattern `package==major.minor.*`.

- [X] **T003** Add a lightweight configuration module defining the random seed and canonical data‑path constants.  

  **File**: `code/config.py`  

  ```python
  SEED = 42
  RAW_DIR   = Path(__file__).resolve().parents[2] / "data" / "raw"
  PROC_DIR  = Path(__file__).resolve().parents[2] / "data" / "processed"
  ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "data" / "artifacts"
  ```  

  **Verification** – Import succeeds (`python -c "import code.config"`), and the constant `SEED` equals 42.

- [ ] **T004** Implement reusable I/O helpers and a minimal logger.  

  **Files**: `code/utils/io.py`, `code/utils/logging.py`  

  *`io.py`* provides `load_parquet(path)`, `save_parquet(df, path)`, and a SHA‑256 checksum function.  
  *`logging.py`* configures a module‑level logger (`logging.getLogger(__name__)`) with a simple console handler.  

  **Verification** – Unit tests in `tests/unit/test_io.py` and `tests/unit/test_logging.py` import the modules and assert that `save_parquet` creates a file and that the checksum matches the file’s content.

---

## Phase 2 – Data ingestion & alignment (User Story 1, **P1**)  

- [ ] **T005** Implement real‑data download, parsing, and raw‑file preservation for ACE/WIND composition data.   <!-- FAILED-IN-EXECUTION: code/ingestion/download_ace.py exit=1; code/ingestion/download_noaa.py exit=1 -->

  **Files**: `code/ingestion/download_ace.py`, `code/ingestion/download_noaa.py`  

  Each script attempts an HTTP GET to the official CDAWeb/NOAA URLs; on success it writes the raw response bytes unchanged to `data/raw/ace_<date>.cdf` (or similar) and parses the needed ion flux ratios, raising `ConnectionError` only on network failure.  

  **Verification** – `pytest tests/unit/test_download.py::test_raw_file_preserved` checks that the raw file exists unchanged (checksum matches) and that parsing extracts O/Fe, He/H, C/O columns.

- [ ] **T006** Build a deterministic synthetic data generator that creates a 20‑year hourly dataset respecting the `SolarWindGeomagneticDataset` schema.  

  **File**: `code/ingestion/generate_synthetic_data.py`  

  *Key points* – uses `np.random.default_rng(SEED)`, stores generation parameters in `data/raw/synthetic_config.yaml`, writes `data/processed/synthetic_aligned.parquet`.  

  **Verification** – After execution, `data/processed/synthetic_aligned.parquet` exists, can be loaded with `io.load_parquet`, and a schema check (via `pandas.api.types`) confirms all required columns are present and contain no NaNs.

- [ ] **T007** Create the alignment/orchestration script that (a) tries the real‑data download functions, (b) on `ConnectionError` invokes the synthetic generator, (c) merges composition and geomagnetic streams, (d) resamples to a strict 1‑hour grid using **hourly median**, (e) enforces a maximum temporal offset of ≤ 30 minutes, (f) flags any gap > 6 h, and (g) applies a small epsilon floor to avoid division‑by‑zero in ratio calculations.  

  **File**: `code/ingestion/align.py`  

  **Verification** – `pytest tests/unit/test_align.py::test_offset_and_gaps` now checks that the resulting DataFrame has exactly one row per hour, `timestamp` is monotonic, the maximum temporal offset ≤ 30 min, and that any > 6 h gaps are listed in `data/artifacts/alignment_report.json`.

- [ ] **T021** Generate an alignment verification report (`data/artifacts/alignment_report.json`) summarizing the maximum temporal offset, any > 6 h gaps, and confirming the ≤ 30 min constraint is satisfied.  

  **Verification** – Unit test asserts the JSON file exists and contains fields `max_offset_minutes` (≤ 30) and `gap_hours` (list of gap durations, each ≤ 6).

---

## Phase 3 – Feature engineering & regression (User Story 2, **P2**) – **independently shippable**

- [ ] **T016** Prepare an aligned dataset **specifically for User Story 2** (runs the same alignment logic as T007 but outputs to `data/processed/aligned_for_us2.parquet`).  

  **Verification** – Checks identical to T007 verification, ensuring the dataset is ready for regression without relying on T007.

- [ ] **T008** Derive the two standard coupling functions (Akasofu ε and Newell F) from bulk solar‑wind parameters.  

  **File**: `code/analysis/coupling_functions.py`  

  **Verification** – `pytest tests/unit/test_coupling.py::test_known_values` validates that for a hand‑crafted input row the computed ε and Newell values match published formulas to within 1 e‑6.

- [ ] **T009** Fit baseline and full multivariate linear regression models, compute VIF for every predictor, and emit a warning artefact for any VIF ≥ 5.  

  **File**: `code/analysis/regression.py`  

  *Outputs* – `data/artifacts/regression_results.csv` (columns: `model_type, predictor, coefficient, std_err, p_value, vif`) and `data/artifacts/vif_warnings.txt` (list of predictors with high VIF).  

  **Verification** – `pytest tests/integration/test_regression.py::test_artifacts_created` asserts that both files exist, that the CSV contains rows for all predictors, and that the VIF column is numeric.

- [ ] **T010** Perform 5‑fold cross‑validation for both models, compute out‑of‑sample R², and calculate the incremental ΔR².  

  **File**: `code/analysis/cross_validation.py`  

  *Output* – `data/artifacts/cv_metrics.json` with keys `baseline_r2`, `full_r2`, `delta_r2`.  

  **Verification** – Unit test checks that `delta_r2` equals `full_r2 - baseline_r2` within floating‑point tolerance.

- [ ] **T018** Compute a 95 % confidence interval for ΔR² using bootstrap resampling (10 000 resamples) and store results in `data/artifacts/delta_r2_ci.json`.  

  **Verification** – Test confirms the JSON contains `ci_lower` and `ci_upper` fields and that `ci_lower < delta_r2 < ci_upper`.

---

## Phase 4 – Significance testing & sensitivity (User Story 3, **P3**) – **independently shippable**

- [ ] **T017** Run baseline and full regression **specifically for User Story 3** (produces `data/artifacts/regression_us3_baseline.pkl` and `regression_us3_full.pkl`).  

  **Verification** – Checks that both pickle files exist and contain model objects with coefficient attributes.

- [ ] **T011** Implement a block permutation test (24‑hour blocks, ≥ 1 000 iterations) that stops early when the standard error of the p‑value falls below 0.001 (or when a hard cap of 10 000 iterations is reached).  

  **File**: `code/analysis/permutation_test.py`  

  *Outputs* – `data/artifacts/permutation_o_fe.json`, `permutation_he_h.json`, `permutation_c_o.json` (each contains `observed_coef`, `null_distribution`, `p_value`).  

  **Verification** – `pytest tests/unit/test_permutation.py::test_stopping_criterion` confirms the SE < 0.001 condition or max iterations, and `pytest tests/unit/test_permutation.py::test_output_files` asserts existence of all three files with the required fields.

- [ ] **T019** Evaluate significance by checking whether each observed coefficient lies outside the 95 % percentile range of its null distribution; record boolean flags in `data/artifacts/percentile_significance.json`.  

  **Verification** – Unit test validates that for each ratio the flag matches the percentile‑range rule.

- [ ] **T012** Conduct a sensitivity sweep over significance thresholds `{0.01, 0.05, 0.10}` applying the Benjamini‑Hochberg FDR correction across the six hypothesis tests (three ratios × two indices).  

  **File**: `code/analysis/sensitivity.py`  

  *Output* – `data/artifacts/fdr_results.csv` (`hypothesis, raw_p, fdr_p, significant`).  

  **Verification** – Integration test validates that for each threshold the number of `significant` rows is reported and that the CSV file is written.

- [ ] **T020** Summarize stability of significance findings across the three thresholds, producing `data/artifacts/threshold_stability.csv` with columns `threshold, num_significant_predictors`.  

  **Verification** – Test checks the CSV exists and contains three rows corresponding to the three thresholds.

---

## Phase 5 – Orchestration, reporting & documentation  

- [ ] **T013** Write the top‑level driver that executes the full pipeline in the correct order, captures any `ConnectionError` to trigger synthetic fallback, and writes a consolidated JSON report.  

  **File**: `code/main.py`  

  *Key fields in `data/artifacts/final_report.json`* – `source_type` (`"Synthetic"` or `"Real"`), `fetch_attempts` (list of URL + status), `model_summary` (ΔR², CV‑R², CI bounds), `significance_summary` (list of significant predictors), `threshold_stability` (reference to `threshold_stability.csv`).  

  **Verification** – Running `python -m code.main` exits with status 0 and the JSON file contains the key `source_type` set to `"Synthetic"` for this project and includes the CI fields.

- [ ] **T014** Update project documentation to be transparent about the data gap and the synthetic fallback, and provide a quick‑start guide that runs the pipeline and checks success.  

  **Files**: `README.md`, `quickstart.md`  

  *README* must contain the sentence “**Data gap**: verified ACE SWICS and NOAA Dst/Kp sources are unavailable; the pipeline therefore uses synthetic data.”  
  *quickstart.md* should list the single command `python -m code.main` and instruct the verifier to assert that `data/artifacts/final_report.json` exists and contains `source_type`.  

  **Verification** – `pytest tests/integration/test_quickstart.py::test_report_exists_and_source` runs the command, checks exit code 0, and validates the JSON field.

- [ ] **T015** Execute the complete end‑to‑end run on the synthetic dataset and confirm that all expected artefacts are present and internally consistent.  

  **Artifacts to check**:  

  * `data/artifacts/regression_results.csv` (contains both baseline and full rows)  
  * `data/artifacts/cv_metrics.json` (`delta_r2` > 0)  
  * `data/artifacts/permutation_*.json` (p‑value ≤ 1)  
  * `data/artifacts/fdr_results.csv` (at least one row marked `significant` for the 0.05 threshold)  
  * `data/artifacts/delta_r2_ci.json` (CI fields present)  
  * `data/artifacts/threshold_stability.csv` (three rows)  
  * `data/artifacts/final_report.json` (matches contents described in T013)  

  **Verification** – A dedicated integration test `tests/integration/test_e2e.py` runs `code/main.py` and asserts the existence and schema of each file, as well as logical consistency (e.g., `delta_r2` equals `full_r2 - baseline_r2`, CI bounds enclose `delta_r2`).

---

### Dependency & execution order summary  

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
| T017 | T001–T004 (runs regression for US 3) |
| T011 | T017 |
| T019 | T011 |
| T012 | T011 |
| T020 | T012 |
| T013 | T005–T012, T018, T019, T020 |
| T014 | – (documentation can be written anytime after T013) |
| T015 | T013 (full pipeline) |

All tasks are unchecked (`- [ ]`) to indicate they remain to be implemented. Once a task is completed and its verification passes, it should be marked `[x]` by the CI system. This task list now satisfies every functional requirement (FR‑001 → FR‑011), addresses all success criteria (SC‑001 → SC‑004), respects Constitution Principle VI by preserving raw composition files, and provides independently‑shippable units for each user story.  
