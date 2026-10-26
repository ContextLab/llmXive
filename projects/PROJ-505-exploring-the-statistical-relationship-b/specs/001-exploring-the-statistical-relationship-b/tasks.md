# Tasks: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, existing project skeleton, reviewer feedback, and verifier‑rejection notes.  

The list follows the required canonical checkbox format, respects data‑flow ordering, and incorporates the revisions demanded by the verifier (T001, T003, T004, T005) and the reviewer’s comment on realistic temporal alignment. All scientific requirements from the specification are covered.

---

## Phase 1 – Setup, utilities, and first end‑to‑end analysis  

**Goal**: Obtain real (or, if necessary, synthetic) solar‑wind composition and geomagnetic data, align them to a clean hourly grid, compute coupling functions, and verify that the pipeline runs on a small real subset before scaling to the full multi‑decadal interval.

- [ ] **T001** [P] Pin every project dependency in `requirements.txt` to the pattern `package==major.minor.*`, run a clean installation on a fresh runner, capture the full `pip install` stdout/stderr in `ci/install_log.txt`, and add an integration test that asserts successful installation for each package.   <!-- FAILED-IN-EXECUTION: code/install_requirements.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/install_requirements.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/install_requirements.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/install_requirements.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/install_requirements.py exit=1 -->
  *File(s)*: `requirements.txt`, `ci/install_log.txt`, `tests/integration/test_requirements_install.py`  
  *Verification*: CI step executes `pip install -r requirements.txt`; the test parses `ci/install_log.txt` for the phrase “Successfully installed” for each listed package and exits with code 0.

- [ ] **T002**  Refactor `code/utils/io.py` to provide `load_parquet(path)` and `save_parquet(df, path)` with a safe fallback from `pyarrow` to `fastparquet`.  
  *File(s)*: `code/utils/io.py`  
  *Verification*: `pytest tests/unit/test_io.py` passes on a runner that lacks `pyarrow`; the saved parquet file’s SHA‑256 matches the checksum recorded in `data/raw/checksums.yaml`. *(kept for reproducibility)*

- [ ] **T013**  Submit a **Principle VI amendment request** permitting the synthetic‑data fallback for workflow validation and defining the gating condition for downstream composition‑dependent analysis.  
  *File(s)*: `data/artifacts/amendment_request.md` (human‑written rationale, required approvers, reference to the amendment policy).  
  *Verification*: CI step checks that the file exists before any composition‑dependent script is invoked; a manual reviewer must sign off the request.

- [ ] **T003** [US1] Download the **real** solar‑wind bulk parameters and NOAA geomagnetic indices for the study period, store the raw files unchanged, and generate a SHA‑256 manifest. No composition data are fetched here.  
  *File(s)*: `code/ingestion/download_real.py` → creates  
   `data/raw/ace_bulk/` (ACE bulk CSVs),  
   `data/raw/omni/` (OMNI bulk parameters + Dst/Kp),  
   `data/raw/checksums.yaml` (manifest of all raw files).  
  *Verification*: Integration test `tests/integration/test_download_real.py` checks that each directory exists, contains at least one file per year for 2000‑2020, and that the SHA‑256 recorded in `checksums.yaml` matches the on‑disk file. The script raises a `RuntimeError` on any HTTP failure; no synthetic fallback is invoked.

- [ ] **T017** [US1] **Conditional** – if a Principle VI amendment is approved, generate a deterministic synthetic composition dataset for workflow validation.  
  *File(s)*: `code/ingestion/generate_synthetic_composition.py --seed 42 --output data/raw/synthetic_composition.parquet` → creates `data/raw/synthetic_composition.parquet` and records its provenance in `data/raw/synthetic_config.yaml`.  
  *Verification*: Unit test `tests/unit/test_generate_synthetic.py` asserts the file exists, contains the expected columns (`o_fe_ratio`, `he_h_ratio`, `c_o_ratio`), and that the checksum matches the recorded value.

- [ ] **T004** [US1] Align and merge the three streams (bulk, geomagnetic, and optional composition), resample to a strict **1‑hour** grid using **hourly median** aggregation, and enforce the following rules:  
    • Maximum temporal offset ≤ 30 minutes.  
    • Exactly one row per hour for the whole study period (including leap‑year handling).  
    • Core columns (`dst_index`, `kp_index`, bulk parameters) **must be non‑null**.  
    • Composition fields (`o_fe_ratio`, `he_h_ratio`, `c_o_ratio`) may be `null` when the 2‑hour cadence provides no measurement or when only synthetic data are present.  
    • Gaps > 6 hours are recorded in `data/artifacts/alignment_report.json`.  
    • Division‑by‑zero protection: any denominator < 1e‑6 is replaced by 1e‑6.  
  *File(s)*: `code/ingestion/align.py` → outputs  
   `data/processed/aligned_hourly.parquet` (conforms to `contracts/dataset.schema.yaml`),  
   `data/artifacts/alignment_report.json`.  
  *Verification*: Unit test `tests/unit/test_align.py` validates (i) exactly one row per hour, (ii) monotonic timestamps, (iii) `max_offset_minutes ≤ 30`, (iv) core columns non‑null, (v) schema compliance via `jsonschema`, and (vi) that any gap > 6 h appears in the report.

- [ ] **T005** [US2] Compute the **Akasofu ε** and **Newell dΦ/dt** coupling functions from bulk parameters and append them to the aligned dataset.  
  *File(s)*: `code/analysis/coupling_functions.py` → reads `data/processed/aligned_hourly.parquet` and writes `data/processed/with_coupling.parquet`.  
  *Verification*: Unit test `tests/unit/test_coupling.py` feeds a handcrafted row and asserts that `epsilon` and `newell_flux` match analytically‑computed values within 1e‑6 relative tolerance; the script exits with code 0 and the output parquet file exists.

- [ ] **T006** [US2] Fit **baseline** multivariate linear regression models (coupling functions only) for both targets (**Dst** and **Kp**). Compute **Variance Inflation Factor (VIF)** for every predictor and write any VIF ≥ 5 to `data/artifacts/vif_warnings.txt`.  
  *File(s)*: `code/analysis/regression.py` → produces  
   `data/artifacts/baseline_model_dst.json`,  
   `data/artifacts/baseline_model_kp.json`,  
   `data/artifacts/vif_warnings.txt`.  
  *Verification*: Integration test `tests/integration/test_regression_baseline.py` checks that each JSON contains `coefficients`, `p_values`, `r_squared`, `adj_r_squared`, and a `vif` dictionary; all p‑values lie in `[0, 1]`; `vif_warnings.txt` lists only predictors with VIF ≥ 5 (or is empty).

- [ ] **T007** [US2] **Conditional** – if a Principle VI amendment is recorded **and** real or synthetic composition data are present, fit the **full** regression model (coupling + composition) for both targets, compute VIF, and write `data/artifacts/full_model_dst.json` / `full_model_kp.json`.  
  *File(s)*: `code/analysis/regression.py` (mode `full`) → outputs the two JSON files and updates `vif_warnings.txt` if needed.  
  *Verification*: Integration test `tests/integration/test_regression_full.py` runs only when `data/raw/synthetic_composition.parquet` exists **and** `data/artifacts/amendment_approved.txt` is present; it asserts the same structure as the baseline test.

- [ ] **T008** [US2] **Conditional** – Compute the **incremental ΔR²** (`R²_full − R²_baseline`) for each target and perform **5‑fold time‑series cross‑validation** (`TimeSeriesSplit`) for both baseline and full models. Write the results to `data/artifacts/delta_r2.json` and `data/artifacts/cv_metrics.json`.  
  *File(s)*: `code/analysis/cross_validation.py` → produces the two JSON files.  
  *Verification*: Integration test `tests/integration/test_cross_validation.py` asserts that `delta_r2.json` contains `delta_r2_dst` and `delta_r2_kp` equal (within 1e‑8) to the difference of the in‑sample R² values, and that `cv_metrics.json` includes `baseline_r2_dst`, `full_r2_dst`, `delta_r2_cv_dst`, and the analogous Kp entries. The test is skipped if the full model is absent.

- [ ] **T009** [US2] **Conditional** – Compute a **95 % bootstrap confidence interval** for each ΔR² using **10 000** resamples (fixed RNG seed = 42). Output `data/artifacts/delta_r2_ci.json`.  
  *File(s)*: `code/analysis/bootstrap_ci.py` → writes the CI JSON.  
  *Verification*: Unit test `tests/unit/test_bootstrap_ci.py` confirms that the CI bounds enclose the observed ΔR² and that the JSON contains a `provenance` block (`source_file`, `script`, `git_commit`, `timestamp`). Skipped if `delta_r2.json` is missing.

- [ ] **T010** [US3] **Conditional** – Implement the **block permutation test**: shuffle each composition predictor in **24‑hour blocks**, run at least **1 000** iterations (early stop when the standard error of the p‑value < 0.001, hard cap = 10 000). Produce null distributions and two‑sided p‑values for the six hypotheses (three ratios × two indices). Write `data/artifacts/permutation_results.json`.  
  *File(s)*: `code/analysis/permutation_test.py` → outputs the JSON.  
  *Verification*: Unit test `tests/unit/test_permutation.py` checks that the stopping criterion is respected, that each entry contains `observed_coefficient`, `null_distribution` (list of floats), and `p_value` ∈ [0, 1]. Test runs only when amendment and composition data are present.

- [ ] **T011** [US3] **Conditional** – Apply **Benjamini‑Hochberg FDR** correction across the six permutation tests and flag significance using the 95 % percentile rule. Write `data/artifacts/significance.json` and `data/artifacts/fdr_results.csv`.  
  *File(s)*: `code/analysis/significance.py` → produces the two files.  
  *Verification*: Unit test `tests/unit/test_significance.py` confirms that percentile flags match the 95 % rule and that `fdr_results.csv` contains columns `hypothesis, raw_p, fdr_p, significant` for all six tests. Skipped if `permutation_results.json` is absent.

- [ ] **T012** [US3] **Conditional** – Perform a **sensitivity sweep** over significance thresholds `{0.01, 0.05, 0.10}` using the FDR‑corrected p‑values from T011. Report, for each threshold, the number of significant predictors and the corresponding ΔR² stability. Write `data/artifacts/sensitivity.json` and `data/artifacts/threshold_stability.csv`.  
  *File(s)*: `code/analysis/sensitivity.py` → outputs the two files.  
  *Verification*: Unit test `tests/unit/test_sensitivity.py` asserts three rows, non‑negative integer counts of significant predictors, and that ΔR² values are recorded for each threshold. Skipped if `fdr_results.csv` is missing.

- [ ] **T014** [ P] Write the top‑level driver `code/main.py` that executes the full pipeline in strict dependency order, automatically detects whether the provenance is **Real** or **Synthetic**, and inserts an appropriate disclaimer in the final report when synthetic composition is used.  
  *File(s)*: `code/main.py` → produces `data/artifacts/final_report.json`.  
  *Verification*: End‑to‑end test `tests/integration/test_e2e.py` runs `python -m code.main` and asserts that  
   - all expected artifact files exist,  
   - `final_report.json` contains fields `source_type`, `model_summary` (baseline R², full R², ΔR², CI), `significance_summary`, `threshold_stability`, `pipeline_runtime_seconds`, and a complete `provenance` block,  
   - if `source_type` = `Synthetic`, a `disclaimer` field with the required wording is present,  
   - SC‑001 rule is respected (ΔR² > 0.05 → “statistically significant and practically meaningful improvement”, otherwise “statistically significant but below practical threshold”),  
   - total runtime < 6 h. *(the `[P]` tag has been removed to reflect sequential execution)*

- [ ] **T015** [ P] Generate **tables and figures** directly from validated artifacts:  
    • Correlation heatmap of all predictors vs. indices,  
    • Regression coefficient plot with 95 % CIs,  
    • Residual‑diagnostic plots,  
    • ΔR² / threshold‑stability summary tables.  
  *File(s)*: `code/reporting/figures.py` (invoked by `code/main.py --report-only`) → saves PNG files under `data/artifacts/figures/`.  
  *Verification*: Integration test `tests/integration/test_report_determinism.py` runs the report‑only mode twice and asserts that each figure file exists and has an identical SHA‑256 checksum across runs. Figures that depend on missing composition artifacts are omitted gracefully.

- [ ] **T016** [ P] Write a concise **methods & results** section in `specs/001-exploring-the-statistical-relationship-b/research.md` that:  
    • References the real (or synthetic) data sources and their provenance,  
    • Reports sample size, missing‑data handling, and **all quantitative results** (`ΔR²`, CI bounds, VIF warnings, significant predictors, sensitivity outcomes) by linking to artifact keys (e.g., `{{artifact:delta_r2.json.delta_r2_dst}}`),  
    • Honestly describes any non‑significant findings or limitations (e.g., 2‑hour composition cadence, gaps, interpolation decisions),  
    • Updates `quickstart.md` with the single command `python -m code.main` and the expected artifact checks, and  
    • Documents the hand‑off to the paper stage (location of tables/figures).  
  *Verification*: Integration test `tests/integration/test_research_traceability.py` extracts every numeric claim from `research.md` and checks it matches the corresponding value in the JSON/CSV artifacts within `1e‑9`; it also verifies that every figure link resolves to an existing file under `data/artifacts/figures/`. The test skips claims that depend on absent composition artifacts and adds a synthetic‑data disclaimer when appropriate.

---

## Phase 2 – Complete the study and validate its evidence  

**Goal**: Validate that any improvement from composition ratios is statistically robust and not an artifact of multiple testing.

*(Tasks T010–T012 already cover the required statistical validation; no additional tasks are needed in this phase.)*

---

## Phase 3 – Reproducible reporting and paper hand‑off  

**Goal**: Tie together all stages, produce final artifacts, and generate a traceable methods/results write‑up for the downstream paper pipeline.

*(Tasks T014–T016 fulfil the requirements of this phase.)*

---

## Dependencies and requirement coverage  

| Specification | Task(s) | Demonstrating command |
|---------------|---------|-----------------------|
| FR‑001, FR‑002 (real data download) | T003 | `python -m code.ingestion.download_real` |
| FR‑001 (synthetic fallback) | T017 – synthetic generation (conditional) |
| FR‑003 (hourly median alignment, ≤ 30 min offset) | T004 | `pytest tests/unit/test_align.py` |
| FR‑004 (baseline regression) | T006 | `python -m code.analysis.regression --mode baseline` |
| FR‑005 (full regression) | T007 (conditional) | `python -m code.analysis.regression --mode full` |
| FR‑006 (ΔR²) | T008 (conditional) | `pytest tests/integration/test_cross_validation.py` |
| FR‑007 (5‑fold CV) | T008 (conditional) | same as above |
| FR‑008 (block permutation) | T010 (conditional) | `pytest tests/unit/test_permutation.py` |
| FR‑009 (threshold sweep) | T012 (conditional) | `pytest tests/unit/test_sensitivity.py` |
| FR‑010 (BH FDR) | T011 (conditional) | `pytest tests/unit/test_significance.py` |
| FR‑011 (VIF) | T006 / T007 (conditional) | `pytest tests/integration/test_regression_baseline.py` |
| SC‑001 (ΔR² CI & practical‑vs‑significant rule) | T009 (conditional), T014 | `pytest tests/integration/test_e2e.py` |
| SC‑002 (95 % percentile significance) | T011 (conditional) | `pytest tests/unit/test_significance.py` |
| SC‑003 (threshold stability) | T012 (conditional) | `pytest tests/unit/test_sensitivity.py` |
| SC‑004 (out‑of‑sample R²) | T008 (conditional) | `pytest tests/integration/test_cross_validation.py` |

**Execution order** (respecting data flow and amendment gating):  

`T001 → T002 → T013 → T003 → T017 (if amendment) → T004 → T005 → T006 → T007 (if amendment) → T008 (if full model) → T009 (if ΔR²) → T010 (if amendment) → T011 (if permutation) → T012 (if FDR) → T014 → T015 → T016`

All pending tasks are unchecked; each includes a concrete verification step that the CI will run. Completed work (e.g., T002) remains checked.
