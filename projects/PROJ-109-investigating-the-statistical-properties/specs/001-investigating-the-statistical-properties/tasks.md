# Tasks: Investigating Statistical Properties of Simulated Dark Matter Halos

**Input**: Design documents from `/specs/001-dark-matter-halo-statistics/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Verified work (status shown)

- [X] T003 Configure linting/formatting in `pyproject.toml` (black line-length 88, flake8 max-line-length 100)
- [X] T004 [P] Create `code/config.py` with pinned seeds, paths, box sizes, critical density constants
- [X] T006 [P] Logging infrastructure in `code/utils/logging.py`
- [ ] T011 [P] [US1] Integration test `test_full_data_pipeline` in `tests/integration/test_data_pipeline.py`
- [ ] T012 [US1] Implement `code/data/download.py` (real-download attempt with DATA_GAP logging, FR-001)
- [ ] T013 [US1] Halo filtering ≥300 particles in `code/data/preprocess.py` (FR-002)
- [ ] T014 [US1] Chunked streaming writer to `data/processed/filtered_halos.parquet` (FR-002)
- [ ] T016 [US1] Data-gap detection logging in `code/data/download.py`
- [ ] T018–T021 [P] [US2] Unit/integration tests for shape, spin, NFW convergence, metric pipeline
- [ ] T022 [P] [US2] Shape parameter s=c/a from inertia tensor in `code/data/compute_metrics.py` (FR-004)
- [ ] T023 [US2] Spin parameter λ with subsampled Plummer-softened potential (FR-005)
- [ ] T024 [US2] NFW profile fitting via `scipy.optimize.curve_fit` with exclusion logic (FR-006)
- [ ] T025 [US2] Metric range validation in `code/data/compute_metrics.py`
- [ ] T027–T030 [P] [US3] Unit/integration tests for binning, KS, BH correction, Spearman, Bullock comparison
- [X] T031–T035, T037 [US3] Statistical analysis implementation in `code/analysis/stats.py` and `code/analysis/visualize.py` (FR-007 to FR-012)

## Pending tasks (re‑planned)

### Phase 1: Data validation and first end‑to‑end result

- [ ] T101 [US1] **Complete schema validation after filtering**: In `code/data/preprocess.py`, after the ≥300‑particle filter runs, load `code/contracts/halo.schema.yaml` and validate each filtered halo record with `jsonschema.validate`. Raise `ValueError` on the first violation. **Verification**: `python -m code.data.preprocess` completes without errors, validates the filtered dataset, and exits 0; the file contains a visible `jsonschema.validate` (or `Draft7Validator`) invocation on the filtered data. (FR-002)

- [ ] T102 [US2] **Convergence‑rate logging artifact**: In `code/data/compute_metrics.py`, after the NFW fitting loop, aggregate fit outcomes and emit the log line `CONVERGENCE: X% success, Y failed fits`, and write `results/convergence_stats.json` containing `{"total_halos": int, "successful_fits": int, "rate": float}` matching the ConvergenceRate entity (SC‑004). **Verification**: the file exists, parses as JSON, and `rate == 100 * successful_fits / total_halos`. (FR‑006, SC‑004)

- [ ] T103 [US3] **Implement local overdensity computation** (formerly US1): In `code/data/compute_metrics.py`, compute spherical top‑hat overdensity (R_TOP_HAT = 5.0 Mpc h⁻¹) using `scipy.spatial.cKDTree` on a memory‑mapped particle array, applying periodic wrapping via `code/config.BOX_SIZE`; Δ = ρ_local / ρ_critical (FR‑003). **Verification**: `data/processed/` gains an `overdensity_delta` column; all values are finite and positive. **Dependency**: after T101.

- [ ] T104 [US3] **Produce the canonical results artifact**: Add a `run_analysis()` entry point (in `code/analysis/stats.py` or `code/main.py`) that executes the full pipeline – binning (FR‑007), KS tests between low vs. high environment bins for each metric (FR‑008), Benjamini‑Hochberg correction (FR‑009), Spearman correlations (FR‑010) – and writes `results/statistics.json` as a JSON array of records conforming to `code/contracts/results.schema.yaml`. **Verification**: `results/statistics.json` exists, is non‑empty, validates against the schema, and contains exactly three KS records (one per metric, `bin_comparison: "low_vs_high"`). (FR‑007‑010)

- [ ] T105 [US3] **Bullock et al. (2001) comparison**: Add constants `BULLOCK_C200` and `BULLOCK_ALPHA` to `code/config.py` with citation docstrings; implement the analytic c(M) fit in `code/analysis/stats.py`; compute deviation statistics (mean difference, RMSE) between the measured mass‑concentration relation and the fit, and write them to `results/bullock_comparison.json`. **Verification**: the constants are importable, and the JSON file contains finite `rmse` and `mean_difference` fields. (FR‑011, SC‑005)

- [ ] T106 [US3] **Save visualizations to disk**: In `code/analysis/visualize.py`, add explicit `fig.savefig(...)` calls writing PNG files to `results/figures/`: (a) mass‑concentration scatter with Bullock fit overlay, (b) KDE curves per metric per environment bin (histogram fallback for bins with < 30 halos), (c) metric‑correlation heatmap. **Verification**: `results/figures/` contains at least three non‑empty PNG files generated from the validated `results/statistics.json` and processed data. (FR‑012)

- [ ] T107 [US1] **Edge‑case unit tests**: Add tests in `tests/unit/test_edge_cases.py` for (a) a halo with exactly 300 particles is retained, (b) a failed NFW fit is excluded from concentration analysis and counted, (c) a bin with insufficient halos skips KDE and falls back to histogram, (d) missing required column (e.g., `velocity`) causes the pipeline to raise a clear `MissingColumnError` and halt. **Verification**: `pytest tests/unit/test_edge_cases.py` passes with assertions on all four cases. (Edge cases from spec.md)

- [ ] T108 [US3] **End‑to‑end orchestration and timing**: Create `code/main.py` with a `--run-all` mode that chains preprocess → metrics → analysis → visualization, and wrap execution in a timer that records start/stop wall time, total halos processed, and sample‑size justification to `results/timing.json`. **Verification**: `python code/main.py --run-all` completes, regenerates all primary artifacts, and `results/timing.json` contains a numeric field `duration_s` with value < 21600. (FR‑007‑012)

- [ ] T109 [US1] **Document methodology constraints and data status**: Write `docs/architecture_constraints.md` covering (a) the subsampled Plummer‑softened potential approximation for FR‑005, (b) real‑data acquisition status and DATA_GAP fallback behavior, (c) synthetic‑generation parameters (seed, deviation magnitude) if the fallback fired, and (d) the memory‑mapped particle‑stream approach for FR‑003. **Verification**: the document exists and references actual constants/code paths. 

- [ ] T110 **Methods / results write‑up**: Write `specs/001-dark-matter-halo-statistics/results.md` that cites `results/statistics.json`, `results/convergence_stats.json`, `results/bullock_comparison.json`, and each figure in `results/figures/`; report KS p‑values (raw and BH‑corrected), Spearman ρ, Bullock deviation statistics, and NFW convergence rate; describe any negative findings, failed fits, and the synthetic‑fallback limitation honestly. **Verification**: the markdown file exists and contains the required citations.

### Additional tasks to close remaining gaps

- [ ] T111 [US1] **Missing‑column halt behavior**: Implement a check in `code/data/download.py` (or the preprocessing step) that verifies required columns (`mass`, `position`, `velocity`) are present in the loaded catalog; if any are absent, raise a `MissingColumnError` with an explicit error message and abort execution. Unit test added in `tests/unit/test_missing_column.py`. **Verification**: the test triggers the error when a synthetic catalog lacking `velocity` is processed.

- [ ] T112 [US3] **Overdensity‑threshold sensitivity analysis**: Sweep the top‑hat radius R_TOP_HAT over a predefined range (e.g., 3, 5, 7 Mpc h⁻¹); for each radius compute environment classifications and record the fraction of halos classified as “high”. Write results to `results/overdensity_sweep.json` containing `{radius: float, high_fraction: float}` entries. **Verification**: the JSON file exists and contains at least three records with plausible fractions (0 ≤ f ≤ 1).

- [ ] T113 [US1] **Data checksum artifact**: After any synthetic data generation or real download, compute SHA‑256 checksums for all files under `data/raw/` and `data/processed/` and write them to `results/data_checksums.json` as a mapping `{filepath: checksum}`. **Verification**: the JSON file exists and contains a checksum entry for each file in the two directories.

- [ ] T114 [US3] **Pre‑register significance threshold**: Add a constant `ALPHA = 0.05` to `code/config.py`; modify the analysis scripts to compare corrected p‑values against this constant and set the `significance` field accordingly. Add a unit test `tests/unit/test_alpha_threshold.py` that asserts a known p‑value below 0.05 yields `significance: true`. **Verification**: the constant is importable and the test passes.

- [ ] T115 [US2] **Update specification FR-005**: Amend `specs/001-investigating-the-statistical-properties/spec.md` to explicitly sanction the subsampled Plummer‑softened potential approximation for total energy computation (see discussion in T109). This ensures the FR aligns with the implemented method. **Verification**: spec FR-005 mentions the subsampled approach and cites T109 documentation. 
