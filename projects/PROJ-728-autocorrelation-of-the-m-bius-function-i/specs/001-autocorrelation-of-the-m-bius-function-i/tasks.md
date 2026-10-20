# Tasks: Autocorrelation of the Möbius Function in Short Intervals  

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer/verifier feedback.  

The tasks are ordered to respect data‑flow dependencies and grouped into logical research phases. All tasks use the canonical checklist format `- [ ] T### [P] [US‑x] description …` with indented continuation lines describing the concrete requirement, expected output path, and verification step.

---  

## Phase 1 – Setup & first end‑to‑end demo  

- [ ] T001 [P] [US‑1] **Create `quickstart.md`** – document project layout, Python 3.11 version, pinned `requirements.txt`, and the demo command `python -m code.main --demo`.  
     • Path: `quickstart.md`  
     • Verification: `grep --color=never '--demo' quickstart.md` succeeds and running the command produces the expected demo files without error.  

- [ ] T002 [P] [US‑1] **Implement linear‑time Möbius sieve** (`code/sieve.py`) that computes μ(n) for `1 ≤ n ≤ 10⁷` and writes an `int8` array to `data/raw/mobius_array.npy`.  
     • Path: `code/sieve.py`, `data/raw/mobius_array.npy`  
     • Verification: unit tests in `tests/unit/test_sieve.py` check known values (μ(1)=1, μ(2)=−1, μ(4)=0, μ(30)=−1, μ(3025)=0) and assert that every entry lies in `{−1,0,1}`.  

- [ ] T003 [P] [US‑1] **Add 2‑bit packing utilities** – extend `code/sieve.py` with `pack_mu` / `unpack_mu` to create the packed ternary array `data/raw/mobius_2bit.npy` (≈2.5 MB) and round‑trip test it over the full array and random slices.  
     • Path: `data/raw/mobius_2bit.npy`  
     • Verification: additional tests in `tests/unit/test_sieve.py` confirm exact pack/unpack equality and record SHA‑256 checksums for both files in `data/checksums/manifest.sha256`.  

- [ ] T004 [P] [US‑1] **Generate deterministic window index** – with seed = 20231017 select **100 non‑overlapping windows per interval length** `L ∈ {1000,10000,100000}` (step = L, contiguous tiling from a seeded random offset) and write start indices to `data/processed/window_index.csv`.  
     • Path: `data/processed/window_index.csv` (columns `interval_start`, `interval_length`, `window_id`)  
     • Verification: `wc -l data/processed/window_index.csv` returns 300 and a script asserts that windows do not overlap.  

- [ ] T005 [P] [US‑1] **Demo autocorrelation on a single window** – compute the normalized autocorrelation for the first sampled window (`L=1000`, lag = 1) and write the result to `data/processed/demo_autocorr.csv`.  
     • Path: `code/autocorrelation.py`, `data/processed/demo_autocorr.csv`  
     • Verification: the CSV contains a single row with at least six decimal places; the value matches a hand‑computed reference for that window within `1e‑9`.  

---  

## Phase 2 – Full statistical pipeline (FR‑001 – FR‑006)  

- [ ] T006 [P] [US‑1] **Compute full‑window autocorrelations** – extend `code/autocorrelation.py` to evaluate all lags `h = 1 … ⌊L/2⌋` for every window in `window_index.csv` using an FFT‑based convolution (float64) and write rows (`interval_start`, `interval_length`, `lag`, `autocorrelation`) to a temporary buffer.  
     • Path: `data/processed/autocorrelation_raw.csv` (intermediate)  

- [ ] T007 [P] [US‑2] **Permutation engine & null distribution** – implement `code/permutation.py` that, for a given window, keeps zero positions fixed and uniformly shuffles the non‑zero signs, generating **exactly 1 000** permutations (per‑window seed `20231017 + window_id`). Compute autocorrelations for all permutations (batched FFT over a `(1000, L)` matrix) and derive two‑sided p‑values `p = (#{|r_perm| ≥ |r_obs|}+1)/1001` together with the 2.5 % / 97.5 % percentile confidence bounds.  
     • Outputs: `data/processed/autocorrelation_stats.csv` (conforms to `contracts/mobius_stats.schema.yaml`) and `data/processed/permutation_null.npy` (optional diagnostic).  
     • Verification: schema validation test passes; edge‑case handling (`p < 0.001` → `p = 0.001`, `p > 0.999` → `p = 0.999`) is exercised in `tests/unit/test_permutation.py`.  

- [ ] T008 [P] [US‑2] **Benjamini–Hochberg FDR correction** – apply `statsmodels.stats.multitest.multipletests` (α = 0.05) to all raw p‑values and add the column `adjusted_p_value` to `autocorrelation_stats.csv`.  
     • Verification: a downstream unit test confirms the column exists and that at least one row has `adjusted_p_value ≤ 0.05` when appropriate.  

- [ ] T009 [P] **Exact int64 cross‑validation (Constitution VI)** – for **L = 1000** exhaustively recompute `Σ μ(k+i)μ(k+i+h)` via integer arithmetic for every `(window, lag)` pair (50 000 checks) and assert agreement with the FFT result (relative error < 1e‑9). For **L = 10000** and **L = 100000** sample ≥ 100 random `(window, lag)` pairs per length and perform the same check. Record `n_pairs_checked` and `max_relative_error` in `data/processed/pipeline_status.json` under `autocorrelation_crosscheck`.  
     • Verification: `tests/unit/test_autocorrelation.py` runs the exhaustive L = 1000 check and the sampled checks for larger L; failures abort the pipeline.  

---  

## Phase 3 – Validation & sensitivity (FR‑007, SC‑005)  

- [ ] T010 [P] **Null‑calibration on synthetic windows (SC‑005)** – `code/calibration.py` generates 200 synthetic random‑sign windows per `L` (preserving the observed zero density), runs the full permutation test on each, and performs (a) a chi‑square goodness‑of‑fit on binned p‑values and (b) a Kolmogorov–Smirnov test on a small independent subsample. Write results to `data/processed/calibration_test.json`.  
     • Success criterion: both `chi2_pvalue` > 0.05 and `ks_pvalue` > 0.05.  

- [ ] T011 [P] **Empirical uniformity test on real data** – reuse the same statistical checks on the raw p‑values from `autocorrelation_stats.csv` and write `data/processed/empirical_uniformity.json`. This file is a *research result* (not a test of the methodology).  
     • Verification: unit test `tests/unit/test_calibration.py` confirms file existence and that the JSON fields are present.  

- [ ] T012 [P] **Zero‑density sensitivity analysis (FR‑007)** – in `code/sensitivity.py` create four adjusted windows per original window (`+5 %`, `‑5 %`, `+10 %`, `‑10 %` zero count) by randomly converting ±1 entries to 0 (insertion) or 0 entries to ±1 (deletion) while preserving total length `L`. For each adjusted window generate 1 000 permutations (batched FFT), compute autocorrelations, and compare raw p‑values (`p < 0.05`) with those of the original window. Record `significant_change` (boolean) and the list of affected lags (both raw and BH‑significant) in `data/processed/sensitivity_summary.csv`.  
     • Runtime guard: if cumulative wall‑clock time exceeds **4 h**, automatically restrict the analysis to `L = 1000` and `L = 10000` only; the scope reduction is recorded in `pipeline_status.json`.  
     • Verification: `tests/unit/test_sensitivity.py` asserts that each adjusted window has the exact target zero count, that `significant_change` is true when any lag flips, and that the guard correctly truncates the run when mocked to exceed the time limit.  

---  

## Phase 4 – Visualization (FR‑005, SC‑006)  

- [ ] T013 [P] **Generate heatmap figures** – rewrite `code/viz.py` to:  
  1. Load `autocorrelation_stats.csv` and group by `interval_length`.  
  2. For each `L ∈ {1000,10000,100000}` render a heatmap (`plt.imshow`) of autocorrelation values (X = lag, Y = window index).  
  3. Overlay a **black dashed contour at autocorrelation = 0** (`plt.contour(..., levels=[0.0], colors='black', linestyles='--')`).  
  4. Add a confidence‑band panel (sharing the lag axis) with the 2.5 % / 97.5 % percentiles shaded (`plt.fill_between`).  
  5. Mark cells where `adjusted_p_value < 0.05` with red circles.  
  6. Save PNGs `outputs/figures/heatmap_L{L}.png` at **≥ 1200 × 1200 px**, DPI 150, using the `Agg` backend.  
     • Verification: `tests/unit/test_viz.py` checks (a) file existence and resolution, (b) presence of the zero‑contour artist, (c) alignment of the confidence‑band axes, and (d) pixel‑level detection of the dashed line.  

---  

## Phase 5 – Orchestration, resource guards & reproducibility  

- [ ] T014 [P] **Fault‑isolated orchestrator** – refactor `code/main.py` into a stage‑wise driver where each core stage (`sieve`, `window_index`, `autocorrelation`, `permutation`, `calibration`, `sensitivity`, `visualization`) runs inside a `try/except`. Record per‑stage `status`, `elapsed_seconds`, and any `error` in `data/processed/pipeline_status.json`. Non‑core stage failures are logged but do not cause a non‑zero exit; core‑stage failures abort with exit 1.  
     • Verification: injecting a deliberate exception in a dummy non‑core stage yields exit 0 and a populated `pipeline_status.json`; a core‑stage exception yields exit 1.  

- [ ] T015 [P] **Resource guards (SC‑003, SC‑004)** – within `code/main.py` monitor wall‑clock time (abort if total > 6 h) and peak RAM (abort if > 7 GB, using `psutil`). Record `elapsed_seconds` and `peak_memory_mb` for each stage in `pipeline_status.json`.  
     • Verification: a synthetic long‑running stage triggers the guard and the JSON reflects the abort reason.  

- [ ] T016 [P] **Checksums & state recording** – after a successful run compute SHA‑256 checksums for **all files under `data/`** and the three PNG figures, append them to `data/checksums/manifest.sha256`, and copy the map into the project‑state YAML at `state/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i.yaml` (updating `updated_at`). Update `quickstart.md` to list the expected output artefacts.  
     • Verification: `manifest.sha256` contains an entry for every data file and PNG; the state YAML’s `artifact_hashes` field matches the manifest.  

- [ ] T017 [P] **Full‑pipeline integration test with fault injection** – `tests/integration/test_full_pipeline.py` runs `python -m code.main` and checks:  
  1. Presence of all final artefacts (`autocorrelation_stats.csv`, three heatmaps, `calibration_test.json`, `empirical_uniformity.json`, `sensitivity_summary.csv`, `pipeline_status.json`, `manifest.sha256`).  
  2. Schema validation of `autocorrelation_stats.csv` against `contracts/mobius_stats.schema.yaml`.  
  3. Graceful continuation when a non‑core stage fails (inject a failure, verify exit 0 and correct logging).  
     • Verification: `pytest -q tests/integration/test_full_pipeline.py` passes.  

---  

## Phase 6 – Research‑report handoff (US‑1, US‑2, US‑3)  

- [ ] T018 [P] **Write `research.md` with concrete claim‑to‑artifact links** – for every quantitative claim in the manuscript (autocorrelation values, p‑value distributions, confidence‑band coverage, sensitivity flags, calibration results, visual observations) cite the exact identifier:  
  * `(interval_start, interval_length, lag)` triple for rows in `autocorrelation_stats.csv`,  
  * specific `interval_start` values flagged in `sensitivity_summary.csv`,  
  * filenames of the heatmaps (`heatmap_L1000.png`, …),  
  * JSON filenames for calibration and empirical uniformity.  
  The document also reports the measured SC‑001 statistic (percentage of lags whose 95 % CI contains zero) and the `max_relative_error` from the cross‑validation.  
     • Verification: a helper script parses `research.md`, extracts each cited identifier, and confirms that the referenced row or file exists in the corresponding artefact.  

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
| Constitution III/V (checksums, state) | T016 |

All tasks respect the data‑flow order:  

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018.  

The pipeline fits within the GitHub‑Actions free‑tier limits (CPU‑only, ≤ 6 h, < 7 GB RAM) and uses only the allowed scientific Python stack.
