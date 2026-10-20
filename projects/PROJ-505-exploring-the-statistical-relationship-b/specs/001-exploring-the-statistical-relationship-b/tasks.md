# Tasks: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, existing project skeleton, verifier rejection feedback for T001‑T007.

---

## Phase 1 – Setup, utilities, and first end‑to‑end analysis  

**Goal**: Obtain real solar‑wind composition and geomagnetic data, align them to a clean hourly grid, and verify that the pipeline runs on a small real subset before scaling to the full 20‑year interval.

- [ ] **T001** [P] Ensure reproducibility by pinning every dependency in `requirements.txt` to the pattern `package==major.minor.*`.
  *Updates*: pin `pyarrow` as `pyarrow==15.0.*` (or replace with `fastparquet==2024.*`), add `pyspedas==1.6.*`, `pytplot==2.2.*`, `cdflib==1.3.*`.  
  *Verification*: `pip install -r requirements.txt` succeeds on a clean runner; CI regex check confirms each line matches `^[a-zA-Z0-9_-]+==[0-9]+\.[0-9]+\.\*$`. This task supports Constitution Principle I (Reproducibility) and provides traceability for all downstream scientific tasks.

- [X] **T002** [P] Refactor `code/utils/io.py` so Parquet I/O does **not** hard‑require `pyarrow`. Implement a safe fallback to `fastparquet` and raise a clear error only if both engines are unavailable. Provide `load_parquet(path)` and `save_parquet(df, path)`.  
  *Verification*: `pytest tests/unit/test_io.py` passes on a runner without `pyarrow`; a parquet file is written, read back identically, and its SHA‑256 checksum matches.

- [ ] **T003** [US1] Conditional real‑data ingestion from NASA CDAWeb via **pyspedas** (requires approved Constitution VI amendment).   <!-- FAILED-IN-EXECUTION: code/ingestion/run_download_real.py exit=1 -->
  *If amendment approved*: fetch ACE SWICS ion fluxes (O, Fe, He, H, C charge‑states), WIND SMS/STICS ion fluxes, and OMNI hourly bulk parameters plus Dst/Kp for 2000‑2020. Store raw CDF files unchanged under `data/raw/ace_swics/`, `data/raw/wind_sms/`, `data/raw/omni/`. Generate `data/raw/checksums.yaml`. Script must raise on any download failure (no synthetic fallback).  
  *If amendment not approved*: invoke synthetic fallback task **T015**.  
  *File*: `code/ingestion/download_real.py`.  
  *Verification*: `pytest tests/integration/test_download_real.py` passes (checks existence of raw directories, validates checksums, confirms required columns). Offline‑failure test asserts a `RuntimeError` propagates.

- [ ] **T004** [US1] Align and merge the three streams, resample to a strict **1‑hour** grid using **hourly median** aggregation, and enforce:  
  * maximum temporal offset ≤ 30 min,  
  * **exactly one row per hour** for the entire study period (including leap‑year handling); any missing hour must cause a verification failure,  
  * flag any gap > 6 h in `data/artifacts/alignment_report.json`,  
  * apply an epsilon floor = 1e‑6 for division when velocity or IMF ≈ 0,  
  * compute composition ratios **O/Fe**, **He/H**, **C/O** (allow `null` when underlying fluxes are missing).  
  *Rows* must exist for every hour; core columns (`dst_index`, `kp_index`) must be non‑missing, composition fields may be null.  
  *Outputs*: `data/processed/aligned_hourly.parquet` and `data/artifacts/alignment_report.json`.  
  *File*: `code/ingestion/align.py`.  
  *Verification*: `pytest tests/unit/test_align.py` passes (one row per hour, monotonic timestamps, `max_offset_minutes ≤ 30`, schema validation, core columns non‑null, alignment report lists any >6 h gaps).

- [ ] **T005** [US2] Derive the **Akasofu ε** and **Newell dΦ/dt** coupling functions from bulk parameters (velocity, density, IMF magnitude, Bz) and append them to the aligned dataset.   <!-- FAILED-IN-EXECUTION: code/analysis/coupling_functions.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/analysis/coupling_functions.py exit=1 -->
  *Output*: `data/processed/with_coupling.parquet`.  
  *File*: `code/analysis/coupling_functions.py` (function signatures `compute_epsilon(row)` and `compute_newell(row)` must match spec).  
  *Verification*: `pytest tests/unit/test_coupling.py` passes (hand‑crafted row yields ε and Newell values within 1e‑6 relative tolerance); script produces the parquet file without errors.

- [ ] **T006** [US2] Fit **baseline** (coupling functions only) and **full** (coupling + composition ratios) multivariate linear regression models for **both** targets **Dst** and **Kp** on the full 2000‑2020 dataset. Compute **Variance Inflation Factor (VIF)** for all predictors and flag any with VIF ≥ 5.  
  *Outputs*: `data/artifacts/baseline_model.json`, `data/artifacts/full_model.json`, `data/artifacts/vif_warnings.txt`.  
  *File*: `code/analysis/regression.py`.  
  *Verification*: `pytest tests/integration/test_regression.py` passes (JSONs contain coefficient dicts, p‑values ∈ [0,1]; `vif_warnings.txt` lists only predictors with VIF ≥ 5 or is empty).

- [ ] **T007** [US2] Compute the **incremental ΔR²** (`R²_full − R²_baseline`) and perform **5‑fold time‑series cross‑validation** (`TimeSeriesSplit`) for both models, reporting out‑of‑sample R² and the cross‑validated ΔR².  
  *Outputs*: `data/artifacts/delta_r2.json`, `data/artifacts/cv_metrics.json`.  
  *File*: `code/analysis/cross_validation.py`.  
  *Verification*: `pytest tests/integration/test_cross_validation.py` passes (ΔR² equals the difference of the two in‑sample R² values within 1e‑8; CV JSON contains keys `baseline_r2`, `full_r2`, `delta_r2_cv` for each target).

- [ ] **T008** [US2] Compute a **95 % bootstrap confidence interval** for ΔR² using **10 000** resamples (fixed RNG seed).  
  *Output*: `data/artifacts/delta_r2_ci.json`.  
  *File*: `code/analysis/bootstrap_ci.py`.  
  *Verification*: `pytest tests/unit/test_bootstrap_ci.py` confirms the CI bounds enclose the observed ΔR² and a provenance block is present.

- [ ] **T015** [P] Generate a deterministic synthetic solar‑wind and geomagnetic dataset (fallback when real data are unavailable).  
  *Output*: `data/raw/synthetic.parquet` and accompanying `data/raw/synthetic_config.yaml` documenting RNG seed and true underlying coefficients.  
  *File*: `code/ingestion/generate_synthetic_data.py`.  
  *Verification*: `pytest tests/unit/test_synthetic.py` checks reproducibility (identical file hash across runs) and that the schema conforms to `contracts/dataset.schema.yaml`.

- [ ] **T016** [P] Submit a Constitution VI amendment request to permit the synthetic‑data fallback for workflow validation and to define the gating condition for downstream analysis.  
  *Output*: `data/artifacts/amendment_request.md` describing the amendment rationale and required approvals.  
  *Verification*: Manual review; CI checks that the file exists before any real‑data download is attempted.

## Phase 2 – Significance testing and sensitivity analysis  

**Goal**: Validate that any improvement from composition ratios is statistically robust and not an artifact of multiple testing.

- [ ] **T009** [US3] Implement the **block permutation test**: shuffle each composition predictor in **24‑hour blocks**, run ≥ 1 000 iterations (early stop when the standard error of the p‑value < 0.001, with a hard cap of 10 000). Produce null distributions and two‑sided p‑values for each of the six hypotheses (three ratios × two indices).  
  *Output*: `data/artifacts/permutation_results.json`.  
  *File*: `code/analysis/permutation_test.py`.  
  *Verification*: `pytest tests/unit/test_permutation.py` passes (stopping criterion respected, each entry contains `observed_coefficient`, `null_distribution`, `p_value` ∈ [0,1]).

- [ ] **T010** [US3] Evaluate **percentile significance** (observed coefficient outside the 95 % percentile range of its null distribution) and apply the **Benjamini‑Hochberg FDR** correction across the six tests.  
  *Outputs*: `data/artifacts/percentile_significance.json`, `data/artifacts/fdr_results.csv`.  
  *File*: `code/analysis/significance.py`.  
  *Verification*: `pytest tests/unit/test_significance.py` passes (percentile flags match the 95 % rule; `fdr_results.csv` contains columns `hypothesis, raw_p, fdr_p, significant` for all six tests).

- [ ] **T011** [US3] Perform a **sensitivity sweep** over significance thresholds `{0.01, 0.05, 0.10}` using the **FDR‑corrected** p‑values from T010. Report for each threshold the number of significant predictors and the stability of ΔR².  
  *Outputs*: `data/artifacts/sensitivity.json`, `data/artifacts/threshold_stability.csv`.  
  *File*: `code/analysis/sensitivity.py`.  
  *Verification*: `pytest tests/unit/test_sensitivity.py` passes (three rows, non‑negative integer counts, ΔR² stability values recorded).

## Phase 3 – Orchestration, reproducible reporting, and hand‑off  

**Goal**: Tie together all stages, produce final artifacts, and generate a traceable methods/results write‑up.

- [ ] **T012** [P] Write the top‑level driver `code/main.py` that executes the full pipeline in dependency order on **real** data when available, otherwise on synthetic data. The script must:  
  * Detect data provenance and set `source_type` to `"Real"` or `"Synthetic"` accordingly.  
  * If `source_type` is `"Synthetic"`, automatically prepend a disclaimer in the final report stating that only synthetic composition data were used and no scientific claim about the real Sun‑Earth system is made (satisfying Constitution VI).  
  * Enforce SC‑001: only claim “statistically significant and practically meaningful improvement” when ΔR² > 0.05; otherwise report “statistically significant but below practical threshold”.  
  * Measure wall‑clock runtime (< 21600 s) and write `data/artifacts/final_report.json` containing: `source_type`, `data_coverage`, `model_summary` (baseline R², full R², ΔR², CI bounds), `significance_summary`, `threshold_stability` reference, `pipeline_runtime_seconds`, and a full `provenance` block.  
  *Verification*: `python -m code.main` exits 0; `pytest tests/integration/test_e2e.py` asserts existence and logical consistency of every artifact (ΔR² matches difference, CI encloses ΔR², permutation p‑values ∈ [0,1], runtime < 6 h, disclaimer present when appropriate).

- [ ] **T013** [P] Generate **tables and figures** directly from validated artifacts:  
  * correlation heatmap of all predictors vs. indices,  
  * regression coefficient plot with 95 % CIs,  
  * residual‑diagnostic plots,  
  * ΔR² / threshold‑stability summary tables.  
  *All figures* saved under `data/artifacts/figures/`.  
  *File*: `code/reporting/figures.py` (invoked by `code/main.py --report-only`).  
  *Verification*: `pytest tests/integration/test_report_determinism.py` runs the report‑only mode twice and asserts each figure file exists and has identical SHA‑256 checksum across runs.

- [ ] **T014** Write a concise **methods & results** account in `specs/001-exploring-the-statistical-relationship-b/research.md` that:  
  * references the real (or synthetic) data sources and their provenance,  
  * reports sample size, missing‑data handling, and all quantitative results (ΔR², CI, VIF warnings, significant predictors, sensitivity outcomes) by linking to artifact keys (e.g., `{{artifact:delta_r2.json.delta_r2}}`),  
  * honestly describes any non‑significant findings or limitations (e.g., cadence gaps, composition‑ratio missingness),  
  * updates `quickstart.md` with the single command (`python -m code.main`) and the expected artifact checks, and  
  * documents the hand‑off to the paper stage (location of tables/figures).  
  *Verification*: `pytest tests/integration/test_research_traceability.py` extracts every numeric claim from `research.md` and checks it matches the corresponding value in the JSON/CSV artifacts within `1e‑9`; it also verifies that every figure link resolves to an existing file under `data/artifacts/figures/`.

---

## Dependencies and requirement coverage

| Specification | Task(s) | Demonstrating command |
|---------------|---------|-----------------------|
| FR‑001, FR‑002 (real data download) | T003 (conditional) | `python -m code.ingestion.download_real` |
| FR‑001, FR‑002 (synthetic fallback) | T015 | `python -m code.ingestion.generate_synthetic_data` |
| FR‑003 (hourly median alignment, ≤ 30 min offset) | T004 | `pytest tests/unit/test_align.py` |
| FR‑004, FR‑005 (baseline / full regression) | T006 | `python -m code.main` (produces JSON models) |
| FR‑006 (ΔR²) | T007 | `pytest tests/integration/test_cross_validation.py` |
| FR‑007 (5‑fold CV) | T007 | same as above |
| FR‑008 (block permutation, max 10 000 iters) | T009 | `pytest tests/unit/test_permutation.py` |
| FR‑009 (threshold sweep) | T011 | `pytest tests/unit/test_sensitivity.py` |
| FR‑010 (BH FDR) | T010 | `pytest tests/unit/test_significance.py` |
| FR‑011 (VIF) | T006 | `pytest tests/integration/test_regression.py` |
| SC‑001 (ΔR² CI & practical‑vs‑significant rule) | T008, T012 | `pytest tests/integration/test_e2e.py` |
| SC‑002 (95 % percentile significance) | T010 | `pytest tests/unit/test_significance.py` |
| SC‑003 (threshold stability) | T011 | `pytest tests/unit/test_sensitivity.py` |
| SC‑004 (out‑of‑sample R²) | T007 | `pytest tests/integration/test_cross_validation.py` |

**Execution order** (respecting data flow):  

`T001 → T002 → T016 → T015 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014`.

--- 

*All tasks are unchecked except T002 (already verified).  Each task lists the exact file(s) it creates or modifies, the scientific requirement(s) it satisfies, and a concrete verification step that the CI will run.*