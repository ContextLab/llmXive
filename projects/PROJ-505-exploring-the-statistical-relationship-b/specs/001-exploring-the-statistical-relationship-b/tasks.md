# Tasks: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, existing project skeleton, verifier rejection feedback for T002/T004/T005/T006.

**Superseded plan elements (upstream kickback requested)**: The following upstream artifacts are STALE on data sourcing and must be revised to match this tasks.md (the real-data pipeline); until then, this tasks.md is authoritative wherever it conflicts with them:
- `plan.md` Summary / Scope Limitation / Phase 1 / Phase & Task Breakdown still mandate `generate_synthetic_data.py` and an exclusively synthetic dataset. The synthetic generator is DELETED. Real data comes from `pyspedas`/CDAWeb (ACE SWICS + WIND composition, OMNI bulk/indices). Plan's Phase 1 must be replaced by real-data ingestion (T003); its FR coverage table and "covers every FR & SC" claim must be regenerated (they also omit T008's bootstrap CI for SC-001).
- `plan.md` Constitution Check marks Principle VI "PASS (synthetic)" — wrong; the real-data approach (T003) is what satisfies Principle VI.
- `data-model.md` Data Flow Diagram and Data Hygiene sections still describe ingestion via `generate_synthetic_data.py` and provenance from `synthetic_config.yaml`; the real provenance source is the raw CDAWeb files + `data/raw/checksums.yaml` + `code/ingestion/download_real.py` (see T012).
- `spec.md` FR-008 leaves max iterations "[deferred]" — resolved value is 10,000 (T009); SC-002 leaves the percentile range "[deferred]" — resolved value is the 95% percentile range (T010). Spec should record these.
- `plan.md` Compute Feasibility CPU runtime is "[deferred]"; T012 now records measured pipeline runtime against the 6-hour constraint.

**Revision note (addresses verifier rejections and the fabrication gate)**: The prior plan's synthetic-data fallback is removed. The loader must FAIL LOUDLY on fetch failure — no `generate_synthetic_*()` fallback, no synthetic stand-ins. Real data is obtained via installable packages: `pyspedas` (NASA CDAWeb access for ACE SWICS composition, WIND SMS/STICS composition, and OMNI hourly bulk parameters/IMF) and the OMNI hourly dataset which includes Dst and Kp indices. T002 and T004 are reopened to fix the exact defects the verifier reported.

## Phase 1 – Setup, utilities, and first end-to-end analysis

- [ ] T001 [P] Fix `requirements.txt` so that **every** non-comment line matches the pattern `package==major.minor.*`, removing the offending `pyarrow>=15.0.0` line flagged by the verifier (pin it as `pyarrow==15.0.*` or drop it in favor of `fastparquet==2024.*`). Add `pyspedas==1.6.*`, `pytplot==2.2.*`, `cdflib==1.3.*` for real CDAWeb data access. Document the runnable pipeline command in the feature's `quickstart.md`.
  **Verification** – CI regex check: each non-comment line matches `^[a-zA-Z0-9_-]+==[0-9]+\.[0-9]+\.\*$`; `pip install -r requirements.txt` succeeds.

- [X] T002 [P] Refactor `code/utils/io.py` so Parquet I/O does NOT hard-require `pyarrow` (verifier: `save_parquet` forced the pyarrow engine and tests failed with ImportError). Attempt `import pyarrow` inside `try/except`; fall back to `fastparquet`; raise a clear error only if both engines are missing. Provide `load_parquet(path)`, `save_parquet(df, path)`, `sha256_checksum(path)`.
  **Verification** – `pytest tests/unit/test_io.py` passes on a runner without `pyarrow`: `save_parquet` creates a file, `load_parquet` reads it back identically, checksum matches.

- [ ] T003 [US1] Implement real-data ingestion from NASA CDAWeb via `pyspedas` (the single verified real source — no hand-rolled guessed URLs, no synthetic fallback): fetch **both** (a) ACE SWICS ion composition (O, Fe, He, H, C charge-state fluxes) and (b) the WIND composition dataset (SMS/STICS ion fluxes), satisfying FR-001's "ACE/WIND archives" requirement and constitution Principle VI's mandate that raw files from BOTH sources be preserved unchanged, plus (c) OMNI hourly data (velocity, density, IMF, Bz, Dst, Kp) for 2000–2020. Write all raw CDF-derived files unchanged to `data/raw/ace_swics/` and `data/raw/wind_sms/` and `data/raw/omni/` with SHA-256 checksums in `data/raw/checksums.yaml`. The loader MUST raise on any fetch failure (no `try/except` that substitutes placeholder data). <!-- FAILED-IN-EXECUTION: code/ingestion/download_real.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingestion/download_real.py exit=1 -->
  **Files**: `code/ingestion/download_real.py`
  **Verification** – `pytest tests/integration/test_download_real.py`: the parse/checksum assertions run against the cached raw files under `data/raw/` as input (skip with `@pytest.mark.skipif(not any(data/raw/**/*.cdf))` when the cache is empty on a fresh offline runner); the mock-failure test (monkeypatched fetch raising) runs fully offline and asserts `ConnectionError`/`RuntimeError` propagates — never a fallback. Test asserts raw files exist for ACE SWICS, WIND SMS, and OMNI, checksums match, and parsed columns include the composition species and Dst/Kp.

- [ ] T004 [US1] Implement alignment: merge the ACE SWICS and WIND composition streams (cross-calibrated or treated as separate cohorts per the spec's instrument-version edge case) with the geomagnetic/bulk stream, resample to a strict 1-hour grid using **hourly median** aggregation, enforce maximum temporal offset ≤ 30 minutes, flag any gap > 6 hours in `data/artifacts/alignment_report.json`, apply an epsilon floor (1e-6) for ratio divisions, and compute O/Fe, He/H, C/O ratios from the raw ion fluxes. Rows with composition gaps > 6 h are marked missing (not interpolated across the gap).
  **File**: `code/ingestion/align.py` → `data/processed/aligned_hourly.parquet`
  **Verification** – `pytest tests/unit/test_align.py`: one row per hour, monotonic timestamps, `max_offset_minutes ≤ 30`, schema-valid against `contracts/dataset.schema.yaml`, gaps recorded in the alignment report.

- [ ] T005 [US2] Derive the Akasofu ε and Newell coupling functions from bulk parameters (velocity, density, IMF, Bz), writing `data/processed/with_coupling.parquet`, and run a thin end-to-end first analysis on a 1-year real subset: baseline OLS regression of Dst on coupling functions, producing real coefficient rows under `data/artifacts/`.
  **File**: `code/analysis/coupling_functions.py` (+ minimal driver in `code/main.py`)
  **Verification** – `pytest tests/unit/test_coupling.py`: the test hand-crafts the input row (velocity_km_s=400, density_cm3=5, imf_nT=5, imf_bz_nT=-5) and independently computes the expected ε = v B² sin⁴(θ/2) (l0 = 7/2 Earth radii conversion as in the standard formulation) and Newell dΦ/dt = v^(4/3) B_T^(2/3) sin⁸(θ/2) inside the test from the published formulas, asserting the module's outputs match to within 1e-6 relative tolerance; the first-pass regression artifact exists with real coefficients computed from the aligned real data.

**Checkpoint**: `python -m code.main --quick` executes on real 1-year data and its numerical outputs can be checked. No synthetic or placeholder inputs anywhere.

## Phase 2 – Complete regression study and validation (US2)

- [ ] T006 [US2] Fit baseline (coupling functions only) and full (coupling functions + O/Fe, He/H, C/O) multivariate linear regressions for BOTH targets Dst and Kp on the full 2000–2020 aligned dataset; report coefficients, standard errors, p-values, R², adjusted R²; compute VIF for all predictors, flagging any VIF ≥ 5.
  **File**: `code/analysis/regression.py` → `data/artifacts/baseline_model.json`, `data/artifacts/full_model.json`, `data/artifacts/vif_warnings.txt`
  **Verification** – `pytest tests/integration/test_regression.py`: both JSONs contain coefficient dicts for all predictors, p-values in [0,1]; `vif_warnings.txt` lists only predictors with VIF ≥ 5 (or is empty).

- [ ] T007 [US2] Compute the incremental ΔR² = R²_full − R²_baseline (FR-006) and perform 5-fold time-series cross-validation (`TimeSeriesSplit`) reporting out-of-sample R² for both models and cross-validated ΔR² (FR-007). <!-- FAILED-IN-EXECUTION: code/analysis/cross_validation.py exit=1 -->
  **File**: `code/analysis/cross_validation.py` → `data/artifacts/cv_metrics.json`, `data/artifacts/delta_r2.json`
  **Verification** – Test asserts `delta_r2 == full_r2 − baseline_r2` within 1e-8 and that CV keys exist for both targets.

- [ ] T008 [US2] Compute a 95 % bootstrap confidence interval for ΔR² (10,000 resamples, fixed seed) supporting SC-001's reporting rule (significant + ΔR² > 0.05 vs. significant but below practical threshold). This task supplies the CI component of SC-001 that the (stale) plan phase table omits.
  **File**: `code/analysis/bootstrap_ci.py` → `data/artifacts/delta_r2_ci.json`
  **Verification** – Test confirms `ci_lower < delta_r2 < ci_upper` and provenance block present.

## Phase 3 – Significance testing and sensitivity (US3)

- [ ] T009 [US3] Implement the block permutation test: shuffle composition predictors in 24-hour blocks, ≥ 1,000 iterations (early stop when p-value SE < 0.001, max 10,000 — the resolved value for spec FR-008's deferred placeholder), for each composition ratio × each index (6 tests), producing null distributions and two-sided p-values.
  **File**: `code/analysis/permutation_test.py` → `data/artifacts/permutation_results.json`
  **Verification** – `pytest tests/unit/test_permutation.py` confirms stopping criterion, per-ratio `observed_coef`, `null_distribution`, `p_value` fields, and p-values in [0,1].

- [ ] T010 [US3] Evaluate percentile significance (observed coefficient outside the 95 % percentile range of the null distribution — the resolved value for spec SC-002's deferred placeholder) and apply Benjamini–Hochberg FDR correction across the six hypothesis tests (FR-010).
  **Files**: `code/analysis/significance.py`, `tests/unit/test_significance.py` → `data/artifacts/percentile_significance.json`, `data/artifacts/fdr_results.csv`
  **Verification** – `pytest tests/unit/test_significance.py` asserts percentile flags match the rule and the FDR CSV has columns `hypothesis, raw_p, fdr_p, significant` with six rows per target set.

- [ ] T011 [US3] Sensitivity sweep over thresholds {0.01, 0.05, 0.10} (FR-009, SC-003): report the number of significant predictors and the stability of ΔR² at each threshold. Significance is judged on the **FDR-corrected** p-values from T010's `data/artifacts/fdr_results.csv`, so this task depends on T010, not only T009.
  **Files**: `code/analysis/sensitivity.py`, `tests/unit/test_sensitivity.py` → `data/artifacts/sensitivity.json`, `data/artifacts/threshold_stability.csv`
  **Verification** – `pytest tests/unit/test_sensitivity.py` confirms three threshold rows with non-negative integer counts and ΔR² stability values reported, computed from `fdr_results.csv`.

## Phase 4 – Orchestration, verification, and handoff

- [ ] T012 [P] Write the top-level driver `code/main.py` executing the full pipeline in dependency order on the real data, aggregating all artifacts into `data/artifacts/final_report.json` with keys: `source_type` (must be `"Real"` — no synthetic path exists), `data_coverage` (period, row count, missingness), `model_summary` (delta_r2, baseline_r2, full_r2, CI bounds), `significance_summary` (FDR-significant predictors), `threshold_stability` reference, `pipeline_runtime_seconds` (measured wall-clock of the full run, recorded against the 6-hour constraint that plan.md left deferred), and a `provenance` block per the REAL-data provenance schema: `source_files` (the raw CDAWeb files under `data/raw/ace_swics/`, `data/raw/wind_sms/`, `data/raw/omni/`), `checksums` (from `data/raw/checksums.yaml`), `download_script` (`code/ingestion/download_real.py`), `git_commit`, `timestamp`. (The data-model.md synthetic provenance note is superseded — see header.)
  **Verification** – `python -m code.main` exits 0; `pytest tests/integration/test_e2e.py` asserts existence, schema, and logical consistency of every artifact (e.g., `delta_r2 == full_r2 − baseline_r2`; CI encloses `delta_r2`; permutation p-values in [0,1]; `pipeline_runtime_seconds < 21600`).

- [ ] T013 [P] Generate the specified tables and figures directly from validated artifacts: correlation heatmap of predictors/indices, regression coefficient plot with 95 % CIs, residual diagnostics, and ΔR²/threshold-stability summary tables, saved under `data/artifacts/figures/`. The reporting step must be independently re-runnable via `python -m code.main --report-only`.
  **Files**: `code/reporting/figures.py` (invoked by `code/main.py --report-only`)
  **Verification** – `pytest tests/integration/test_report_determinism.py`: run `python -m code.main --report-only` twice; assert each figure file exists both times and its SHA-256 checksum is identical across the two runs (byte-identical regeneration from the artifact JSON/CSVs).

- [ ] T014 Write a concise methods/results account in `specs/001-exploring-the-statistical-relationship-b/research.md` linked to the actual output cells and figure files produced by T013 (this task runs strictly AFTER T013 — it consumes `data/artifacts/figures/`), stating the real data sources (pyspedas/CDAWeb ACE SWICS + WIND SMS + OMNI), sample size, missingness handling, and — honestly — negative findings, non-significant results, and limitations (observational/associational framing, composition data gaps). Update `quickstart.md` with the single command and expected artifact checks, and document the paper-stage handoff (tables/figures to carry into the paper).
  **Files**: `specs/001-exploring-the-statistical-relationship-b/research.md`, `tests/integration/test_research_traceability.py`
  **Verification** – `pytest tests/integration/test_research_traceability.py`: the test extracts every numeric claim in research.md's results section via a regex over `{{artifact:key.path}}`-style references (or a declared claims table) and asserts each matches the corresponding value in the artifact JSON/CSV files within 1e-9; additionally the test asserts every figure link in research.md resolves to an existing file under `data/artifacts/figures/`.

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstrating command |
|---|---|---|
| FR-001, FR-002 (real data download, ACE + WIND + OMNI) | T003 | `python -m code.ingestion.download_real` |
| FR-003 (hourly median alignment, ≤30 min) | T004 | `pytest tests/unit/test_align.py` |
| FR-004, FR-005 (baseline/full regression) | T005, T006 | `python -m code.main` |
| FR-006 (ΔR²) | T007 | `pytest tests/integration/test_e2e.py` |
| FR-007 (5-fold CV) | T007 | `pytest tests/integration/test_e2e.py` |
| FR-008 (block permutation, max 10,000 iters) | T009 | `pytest tests/unit/test_permutation.py` |
| FR-009 (threshold sweep) | T011 | `pytest tests/unit/test_sensitivity.py` |
| FR-010 (BH FDR) | T010 | `pytest tests/unit/test_significance.py` |
| FR-011 (VIF) | T006 | `pytest tests/integration/test_regression.py` |
| SC-001 (ΔR² CI reporting rule) | T007, T008, T012 | `pytest tests/integration/test_e2e.py` |
| SC-002 (95 % percentile significance) | T010 | `pytest tests/unit/test_significance.py` |
| SC-003 (threshold stability) | T011 | `pytest tests/unit/test_sensitivity.py` |
| SC-004 (out-of-sample R²) | T007 | `pytest tests/integration/test_e2e.py` |

Execution order: T001, T002 (parallel) → T003 → T004 → T005 → T006 → T007 → T008; T009 after T006; **T010 after T009; T011 after T010** (T011 consumes FDR-corrected p-values from T010's `fdr_results.csv`); T012 after all analysis tasks; T013 after T012; **T014 after T013** (T014 links to T013's figure files).

## Revision behavior

- T002/T004 (old numbering) reopened per verifier rejections: requirements.txt pin violation and pyarrow-forced I/O — fixed as T001/T002 above.
- T005/T006 (old) failed execution and the synthetic-generator approach is removed entirely: real data now comes from `pyspedas`/CDAWeb with a fail-loudly loader. All analysis-stage requirements (FR-004–FR-011, SC-001–SC-004) are preserved unchanged; only the data source is corrected.
- This round (R1 revision): WIND composition ingestion added to T003 (FR-001 / Principle VI); T010/T011 test-file deliverables added to match the coverage table; T011 re-sequenced after T010 (FDR-based significance); T013 given a concrete determinism check (`--report-only` + SHA-256); T014 untagged [P] and sequenced after T013 with a machine-executable traceability test; T005 verification given a concrete input row and independent-formula assertion; T003 test given explicit offline/cache behavior; T012 provenance rewritten for the real-data schema and records measured runtime. Upstream plan.md/data-model.md/spec.md staleness is flagged in the header for kickback.
- No completed artifacts are erased; the alignment, regression, CV, permutation, FDR, and sensitivity modules keep their planned paths and acceptance criteria.