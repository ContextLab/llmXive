# Tasks: Autocorrelation of the Möbius Function in Short Intervals  

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer/verifier feedback.  

All tasks respect data‑flow dependencies and are written in the canonical checklist format `- [ ] T### [P] [USx?] description …`.  Checked boxes indicate work that has already passed verification; unchecked boxes are pending (including the four items that were rejected and must be redone).

---  

## Phase 1 – Setup & first end‑to‑end demo  

- [X] T001 [P] [US‑1] **Create `quickstart.md`** – document project layout, Python 3.11 version, pinned `requirements.txt`, and the demo command `python -m code.main --demo`.  
  • Path: `quickstart.md`  
  • Verification: `grep '--demo' quickstart.md` succeeds and the command runs without error, producing the expected demo files.  

- [X] T002 [P] [US‑1] **Implement linear‑time Möbius sieve** (`code/sieve.py`) that computes μ(n) for `1 ≤ n ≤ 10⁷` and writes an `int8` array to `data/raw/mobius_array.npy`.  
  • Path: `code/sieve.py`, `data/raw/mobius_array.npy`  
  • Verification: unit tests `tests/unit/test_sieve.py` check known values (μ(1)=1, μ(2)=−1, μ(4)=0, μ(30)=−1, μ(3025)=0) and assert that every entry lies in `{−1,0,1}`.  

- [ ] T003 [P] [US‑1] **Add 2‑bit packing utilities** – extend `code/sieve.py` with `pack_mu` / `unpack_mu` to create the packed ternary array `data/raw/mobius_2bit.npy` (≈2.5 MB) and round‑trip‑test it over the full array and random slices.   <!-- FAILED-IN-EXECUTION: data/checksums/manifest.sha256 exit=-1 -->
  • Path: `data/raw/mobius_2bit.npy`  
  • Verification: additional tests in `tests/unit/test_sieve.py` confirm exact pack/unpack equality and record SHA‑256 checksums for both files in `data/checksums/manifest.sha256`.  

- [ ] T004 [P] [US‑1] **Generate deterministic window index** – with seed = 20231017 select **100 non‑overlapping windows per interval length** `L ∈ {1000,10000,100000}` (step = L, contiguous tiling from a seeded random offset) and write start indices to `data/processed/window_index.csv`.
  • Path: `data/processed/window_index.csv` (columns `interval_start`, `interval_length`, `window_id`)  
  • Verification: `wc -l data/processed/window_index.csv` returns 300 and a script asserts that windows do not overlap.  

- [ ] T005 [P] [US‑1] **Demo autocorrelation on a single window** – compute the normalized autocorrelation for the first sampled window (`L=1000`, lag = 1) and write the result to `data/processed/demo_autocorr.csv`.  
  • Path: `code/autocorrelation.py`, `data/processed/demo_autocorr.csv`  
  • Verification: the CSV contains a single row with ≥ 6 decimal places; the value matches a hand‑computed reference for that window within `1e‑9`.  

---  

## Phase 2 – Full statistical pipeline (FR‑001 – FR‑006)  

- [ ] T006 [P] [US‑1] **Compute full‑window autocorrelations** – extend `code/autocorrelation.py` to evaluate all lags `h = 1 … ⌊L/2⌋` for every window in `window_index.csv` using an FFT‑based convolution (float64) and write rows (`interval_start`, `interval_length`, `lag`, `autocorrelation`) to a temporary buffer `data/processed/autocorrelation_raw.csv`.  

- [ ] T007 [P] [US‑2] **Permutation engine & null distribution** – implement `code/permutation.py` that, for a given window, keeps zero positions fixed and uniformly shuffles the non‑zero signs, generating **exactly 1 000** permutations (per‑window seed `20231017 + window_id`). Compute autocorrelations for all permutations (batched FFT over a `(1000, L)` matrix) and derive two‑sided p‑values `p = (#{|r_perm| ≥ |r_obs|}+1)/1001` together with the 2.5 % / 97.5 % percentile confidence bounds.   <!-- FAILED-IN-EXECUTION: code/permutation.py exit=1 -->
  • Outputs: `data/processed/autocorrelation_stats.csv` (conforms to `contracts/mobius_stats.schema.yaml`) and optional diagnostic `data/processed/permutation_null.npy`.  
  • Verification: schema validation test passes; edge‑case handling (`p < 0.001` → `p = 0.001`, `p > 0.999` → `p = 0.999`) exercised in `tests/unit/test_permutation.py`.  

- [ ] T008 [P] [US‑2] **Benjamini–Hochberg FDR correction** – apply `statsmodels.stats.multitest.multipletests` (α = 0.05) to all raw p‑values and add the column `adjusted_p_value` to `autocorrelation_stats.csv`.  
  • Verification: a downstream unit test confirms the column exists and that at least one row has `adjusted_p_value ≤ 0.05` when appropriate.  

- [ ] T009 [P] **Exact int64 cross‑validation (Constitution VI)** – **exhaustively** recompute `Σ μ(k+i)μ(k+i+h)` via integer arithmetic for **every** `(window, lag)` pair for **all** interval lengths `L = 1000, 10000, 100000`. Assert agreement with the FFT result (relative error < 1e‑9) and record `n_pairs_checked` and `max_relative_error` in `data/processed/pipeline_status.json` under `autocorrelation_crosscheck`.   <!-- FAILED-IN-EXECUTION: code/cross_validate_autocorrelation.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/cross_validate_autocorrelation.py exit=1 -->
  • Verification: `tests/unit/test_autocorrelation.py` runs the exhaustive checks for all three L values; any failure aborts the pipeline.  

---  

## Phase 3 – Validation & sensitivity (FR‑007, SC‑005)  

- [ ] T010 [P] **Null‑calibration on synthetic windows (SC‑005)** – `code/calibration.py` generates 200 synthetic random‑sign windows per `L` (preserving the observed zero density), runs the full permutation test on each, and performs (a) a chi‑square goodness‑of‑fit on binned p‑values and (b) a Kolmogorov–Smirnov test on a small independent subsample. Write results to `data/processed/calibration_test.json`.  
  • Success criterion: both `chi2_pvalue` > 0.05 and `ks_pvalue` > 0.05.  

- [ ] T011 [P] **Empirical uniformity test on real data** – reuse the same statistical checks on the raw p‑values from `autocorrelation_stats.csv` and write `data/processed/empirical_uniformity.json`. This file is a *research result* (not a test of the methodology).  
  • Verification: unit test `tests/unit/test_calibration.py` confirms file existence and that the JSON fields are present.  

- [ ] T012 [P] **Zero‑density sensitivity analysis (FR‑007)** – redesign `code/sensitivity.py` to **process all three interval lengths** (`L = 1000, 10000, 100000`) without any runtime guard that could skip the largest windows. For each original window create four adjusted versions (`+5 %`, `‑5 %`, `+10 %`, `‑10 %` zero count) by randomly converting ±1 entries to 0 (insertion) or 0 entries to ±1 (deletion) while keeping total length `L` constant. For each adjusted window generate **1 000** zero‑preserving permutations (batched FFT) and compute autocorrelations. Compare raw p‑values (`p < 0.05`) with those of the original window; set `significant_change` = True iff any lag flips its raw‑significance status. Record the list of affected lags and, additionally, which of those were also BH‑significant.  
  • Path: `data/processed/sensitivity_summary.csv` (columns `interval_start`, `interval_length`, `adjustment`, `significant_change`, `affected_lags`, `affected_lags_fdr_significant`).  
  • Verification: `tests/unit/test_sensitivity.py` asserts correct zero‑count adjustments, correct boolean flagging, and proper operation of the time‑guard (mocked to trigger).  

---  

## Phase 4 – Visualization (FR‑005, SC‑006)  

- [ ] T013 [P] **Generate heatmap figures** – rewrite `code/viz.py` to:  
  1. Load `autocorrelation_stats.csv` and group by `interval_length`.  
  2. For each `L ∈ {1000,10000,100000}` render a heatmap (`plt.imshow`) of autocorrelation values (X = lag, Y = window index).  
  3. Overlay a **black dashed contour at autocorrelation = 0** using `plt.contour(..., levels=[0.0], colors='black', linestyles='--')`.  
  4. Add a confidence‑band panel (sharing the lag axis) with the 2.5 % / 97.5 % percentiles shaded (`plt.fill_between`).  
  5. Mark cells where `adjusted_p_value < 0.05` with red circles (`plt.scatter`).  
  6. Save PNGs `outputs/figures/heatmap_L{L}.png` at **≥ 1200 × 1200 px**, DPI 150, using the `Agg` backend.  
  • Verification: `tests/unit/test_viz.py` checks (a) file existence and resolution, (b) presence of the zero‑contour artist, (c) alignment of the confidence‑band axes, and (d) that at least one red‑circle marker appears where appropriate.  

---  

## Phase 5 – Orchestration, resource guards & reproducibility  

- [ ] T014 [P] **Fault‑isolated orchestrator** – refactor `code/main.py` into a stage‑wise driver where each core stage (`sieve`, `window_index`, `autocorrelation`, `permutation`, `calibration`, `sensitivity`, `visualization`) runs inside a `try/except`. Record per‑stage `status`, `elapsed_seconds`, and any `error` in `data/processed/pipeline_status.json`. Non‑core stage failures are logged but do **not** cause a non‑zero exit; core‑stage failures abort with exit 1. The integration test now expects an exit code **0** on successful runs.  
  • Verification: injecting a deliberate exception in a dummy non‑core stage yields exit 0 and a populated `pipeline_status.json`; a core‑stage exception yields exit 1.  

- [ ] T015 [P] **Resource guards (SC‑003, SC‑004)** – within `code/main.py` monitor total wall‑clock time (abort if > 6 h) and peak RAM (abort if > 7 GB, using `psutil`). Record `elapsed_seconds` and `peak_memory_mb` for each stage in `pipeline_status.json`.  
  • Verification: a synthetic long‑running stage triggers the guard and the JSON reflects the abort reason.  

- [ ] T016 [P] **Write `research.md` with concrete claim‑to‑artifact links** – for every quantitative claim in the manuscript (autocorrelation values, p‑value distributions, confidence‑band coverage, sensitivity flags, calibration results, visual observations) cite the **exact identifiers**:  
  * `(interval_start, interval_length, lag)` triples for rows in `autocorrelation_stats.csv`,  
  * specific `interval_start` values flagged in `sensitivity_summary.csv`,  
  * filenames of the heatmaps (`heatmap_L1000.png`, `heatmap_L10000.png`, `heatmap_L100000.png`),  
  * JSON filenames for calibration (`calibration_test.json`) and empirical uniformity (`empirical_uniformity.json`).  
  The document also reports the measured SC‑001 statistic (percentage of lags whose 95 % CI contains zero) and the `max_relative_error` from the cross‑validation.  
  • Verification: a helper script parses `research.md`, extracts each cited identifier, and confirms that the referenced row or file exists in the corresponding artifact.  

- [ ] T017 [P] **Full‑pipeline integration test with fault injection** – `tests/integration/test_full_pipeline.py` runs `python -m code.main` and checks:  
  1. Presence of all final artefacts (`autocorrelation_stats.csv`, three heatmaps, `calibration_test.json`, `empirical_uniformity.json`, `sensitivity_summary.csv`, `pipeline_status.json`, `manifest.sha256`).  
  2. Schema validation of `autocorrelation_stats.csv` against `contracts/mobius_stats.schema.yaml`.  
  3. Graceful continuation when a non‑core stage fails (inject a failure, verify exit 0 and correct logging). The test now expects an exit code **0** on successful pipeline execution.  
  • Verification: `pytest -q tests/integration/test_full_pipeline.py` passes.  

- [ ] T018 [P] **Research‑report handoff** – after `research.md` is finalized (T016), add a short “Data & Code Availability” section that lists the exact artifact paths, their SHA‑256 checksums (from `data/checksums/manifest.sha256`), and the DOI of the Zenodo archive where the repository will be deposited.  
  • Verification: the section is present, the listed checksums match the manifest, and a placeholder DOI (`[UNRESOLVED-CLAIM: 10.5281/zenodo.XXXXX — HTTP 404]`) is included.  

---  

### Dependency & requirement coverage summary  

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 (2‑bit packed array) | T002, T003 |
| FR‑002 (100 windows / FFT) | T004, T006 |
| FR‑003 (1 000 zero‑preserving permutations) | T007 |
| FR‑004 (p‑values & 95 % CI) | T007 |
| FR‑005 (heatmaps) | T013 |
| FR‑006 (CSV output) | T007, T008 |
| FR‑007 (zero‑density sensitivity) | T012 |
| SC‑001 (CI‑coverage) | T018 (reported) |
| SC‑002 (p < 0.05 significance) | T007, T008 |
| SC‑003 (≤ 6 h runtime) | T015 |
| SC‑004 (≤ 7 GB RAM) | T015 |
| SC‑005 (null‑calibration) | T010, T011 |
| SC‑006 (heatmap correctness) | T013 |
| US‑1 (generate μ & autocorr) | T001‑T006 |
| US‑2 (permutation test) | T007‑T012 |
| US‑3 (visualisation) | T013 |
| Constitution VI (exact arithmetic) | T009 |
| Constitution III/V (checksums, state) | T016, T018 |

All tasks are ordered to respect data‑flow:

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T018 → T017  

The pipeline fits within the GitHub‑Actions free‑tier limits (CPU‑only, ≤ 6 h, < 7 GB RAM) and uses only the allowed scientific Python stack.  