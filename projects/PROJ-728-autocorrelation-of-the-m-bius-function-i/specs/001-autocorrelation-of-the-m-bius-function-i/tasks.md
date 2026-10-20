# Tasks: Autocorrelation of the Möbius Function in Short Intervals  

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer/verifier feedback.  

All tasks respect data‑flow dependencies and use the canonical checklist format `- [ ] T### [P] [USx?] …`. Checked boxes indicate work that has already passed verification; unchecked boxes are pending (including the items that were rejected and must be redone).

---  

## Phase 1 – Setup & first end‑to‑end demo  

- [X] T001 [P] [US‑1] **Create `quickstart.md`** – document project layout, Python 3.11 version, pinned `requirements.txt`, and the demo command `python -m code.main --demo`.  
  • Path: `quickstart.md`  
  • Verification: `grep '--demo' quickstart.md` succeeds and the command runs without error, producing the expected demo files.  

- [ ] T002 [P] [US‑1] **Implement linear‑time Möbius sieve** (`code/sieve.py`) that computes μ(n) for `1 ≤ n ≤ 10⁷` and writes an int8 array to `data/raw/mobius_array.npy`.  
  • Path: `code/sieve.py`, `data/raw/mobius_array.npy`  
  • Verification: unit tests `tests/unit/test_sieve.py` check known values (μ(1)=1, μ(2)=−1, μ(4)=0, μ(30)=−1, μ(3025)=0) and assert every entry lies in `{−1,0,1}`.  

- [ ] T003 [P] [US‑1] **Add 2‑bit packing utilities** – extend `code/sieve.py` (or a new module `code/pack.py`) with `pack_mu` and `unpack_mu` to create the packed ternary array `data/raw/mobius_2bit.npy` (≈ 2.5 MB) and a round‑trip test over the full array and random slices.  
  • Path: `code/pack.py`, `data/raw/mobius_2bit.npy`  
  • Verification: tests in `tests/unit/test_pack.py` confirm that `unpack_mu(pack_mu(arr))` equals the original `arr` for the whole dataset and for 100 random sub‑arrays; SHA‑256 hashes of both files are recorded in `data/checksums/manifest.sha256`.  

- [ ] T004 [P] [US‑1] **Generate deterministic window index** – with seed = 20231017 select **100 non‑overlapping windows per interval length** `L ∈ {1000,10000,100000}` (step = L, contiguous tiling from a seeded random offset) and write start indices to `data/processed/window_index.csv`.  
  • Path: `data/processed/window_index.csv` (columns `interval_start`, `interval_length`, `window_id`)  
  • Verification: `wc -l data/processed/window_index.csv` returns 300; a script asserts that windows do not overlap and that the file is reproducible (same hash on repeated runs).  

- [ ] T005 [P] [US‑1] **Demo autocorrelation on a single window** – extract the first window (`L=1000`, start = first `interval_start` in `window_index.csv`), compute the normalized autocorrelation for lag = 1, and write a single‑row CSV `data/processed/demo_autocorr.csv`.  
  • Path: `code/demo_autocorr.py`, `data/processed/demo_autocorr.csv`  
  • Verification: the CSV contains exactly one row with columns `interval_start,interval_length,lag,autocorrelation`; the `autocorrelation` value has ≥ 6 decimal places and matches a hand‑computed reference (−0.047047047047) within absolute tolerance 1e‑9.  

---  

## Phase 2 – Full statistical pipeline (FR‑001 – FR‑006)  

- [ ] T006 [P] [US‑1] **Compute full‑window autocorrelations** – extend `code/autocorrelation.py` to evaluate all lags `h = 1 … ⌊L/2⌋` for every window listed in `window_index.csv` using a float64 FFT‑based convolution (O(L log L) per window). Write rows (`interval_start`, `interval_length`, `lag`, `autocorrelation`, `zero_count`) to `data/processed/autocorrelation_raw.csv`.  
  • Path: `code/autocorrelation.py`, `data/processed/autocorrelation_raw.csv`  
  • Verification: script prints a summary line “written N rows”; a test `tests/integration/test_autocorr_raw.py` checks that the row count equals Σₗ 100·⌊L/2⌋ (≈ 5.55 M) and that every `autocorrelation` lies in [−1, 1].  

- [ ] T007 [P] **Exact int64 cross‑validation (Constitution VI)** – for a random sample of ≥ 100 (window, lag) pairs per length, recompute the autocorrelation sum via pure integer arithmetic (`int64`) and compare to the FFT result. Record `n_pairs_checked` and `max_relative_error` in `data/processed/pipeline_status.json` under key `autocorrelation_crosscheck`.  
  • Path: `code/cross_validate_autocorrelation.py`, `data/processed/pipeline_status.json`  
  • Verification: unit test `tests/unit/test_crossvalidate.py` asserts that `max_relative_error < 1e‑9`; the JSON entry must exist and contain the two fields.  

- [ ] T008 [P] [US‑2] **Permutation null engine (subset strategy)** – implement `code/permutation.py` that **selects the first 20 windows** for each length `L` (taken from `window_index.csv`). For each selected window generate **500 zero‑preserving sign permutations** (seed = 20231017 + window_id). Compute autocorrelations for all lags in a batched FFT, build a per‑length null distribution, and then apply that distribution to **all 300 windows** to obtain two‑sided p‑values and 95 % confidence intervals.  
  • Outputs: temporary null files `data/processed/permutation_null_{L}.npy` (optional) and the enriched CSV `data/processed/autocorrelation_stats.csv` (adds columns `p_value`, `ci_lower`, `ci_upper`).  
  • Verification: schema validation (`contracts/mobius_stats.schema.yaml`) passes; a test `tests/unit/test_permutation.py` checks that `p_value` lies in (0, 1] and that the minimum possible p‑value is 0.002 (i.e., 1/501).  

- [ ] T009 [P] **Benjamini–Hochberg FDR correction** – run `code/fdr_correction.py` which reads `autocorrelation_stats.csv`, applies `statsmodels.stats.multitest.multipletests` (α = 0.05, method='fdr_bh'), and writes the column `adjusted_p_value` back to the same CSV.  
  • Path: `code/fdr_correction.py`, updated `data/processed/autocorrelation_stats.csv`  
  • Verification: unit test `tests/unit/test_fdr.py` confirms the column exists, values are in (0, 1], and that at least one row has `adjusted_p_value ≤ 0.05` when the raw p‑values indicate significance.  

- [ ] T010 [P] **Null‑calibration & empirical uniformity (SC‑005)** – `code/calibration.py` performs two checks:  
    1. **Synthetic calibration** – generate 200 random‑sign windows per length (zero density = 6/π²), run the full permutation pipeline on them, and compute (a) a chi‑square goodness‑of‑fit on equal‑probability bins of the resulting p‑values and (b) a Kolmogorov–Smirnov test on a subsample of 5 windows. Write results to `data/processed/calibration_test.json`.  
    2. **Empirical uniformity** – apply the same chi‑square and KS tests to the *real* p‑values from `autocorrelation_stats.csv` and write `data/processed/empirical_uniformity.json`.  
  • Verification: both JSON files contain fields `chi2_pvalue` and `ks_pvalue` > 0.05 for the synthetic case; the empirical file is present and parsable (its values are recorded for the manuscript).  

- [ ] T011 [P] **Zero‑density sensitivity analysis (FR‑007)** – `code/sensitivity.py` processes every window for each `L`. For each original window create four variants with zero counts altered by ±5 % and ±10 % (random insertions/deletions while preserving total length). For each variant run the permutation engine (500 permutations) and recompute raw p‑values. Set `significant_change = True` if any lag flips its raw‑significance status (`p < 0.05`). Produce `data/processed/sensitivity_summary.csv` with columns `interval_start,interval_length,adjustment,significant_change,affected_lags,affected_lags_fdr_significant`.  
  • Verification: unit test `tests/unit/test_sensitivity.py` checks that the zero‑count adjustments are correct, that the flag is a boolean, and that at least one row shows `significant_change = True` on a toy dataset.  

- [ ] T012 [P] [US‑3] **Generate heatmap figures** – rewrite `code/viz.py` to:  
    1. Load `autocorrelation_stats.csv` and group by `interval_length`.  
    2. For each `L` render a heatmap (`plt.imshow`) of autocorrelation values (X = lag, Y = window index).  
    3. Overlay a black dashed contour at value = 0 (`plt.contour(..., levels=[0], colors='black', linestyles='--')`).  
    4. Add a twin panel showing the 2.5 % / 97.5 % confidence bands (`plt.fill_between`).  
    5. Mark cells with `adjusted_p_value < 0.05` using red circles (`plt.scatter`).  
    6. Save PNGs `outputs/figures/heatmap_L{L}.png` at **≥ 1200 × 1200 px**, DPI 150, using the Agg backend.  
  • Path: `code/viz.py`, `outputs/figures/heatmap_L1000.png`, `heatmap_L10000.png`, `heatmap_L100000.png`  
  • Verification: `tests/unit/test_viz.py` confirms each PNG exists, has the required resolution, contains a contour artist at level 0, a filled confidence‑band artist, and at least one red‑circle marker where `adjusted_p_value < 0.05`.  

---  

## Phase 3 – Reproducibility, orchestration & hand‑off  

- [ ] T013 [P] **Fault‑isolated orchestrator** – refactor `code/main.py` into a stage‑wise driver where each core stage (`sieve`, `pack`, `window_index`, `demo_autocorr`, `autocorrelation`, `permutation`, `fdr_correction`, `cross_validate`, `calibration`, `sensitivity`, `viz`) runs inside a `try/except`. For every stage write an entry to `data/processed/pipeline_status.json` with fields `stage`, `status` (`ok`/`failed`), `elapsed_seconds`, and any `error` message. Non‑core failures log a warning but do not abort the whole run; core‑stage failures abort with exit 1.  
  • Verification: integration test injects a deliberate exception in a non‑core stage and expects exit 0 with a populated `pipeline_status.json`; injecting an exception in a core stage yields exit 1.  

- [ ] T014 [P] **Resource guards (SC‑003, SC‑004)** – within `code/main.py` monitor wall‑clock time (abort if > 6 h) and peak RAM (abort if > 7 GB) using `psutil`. Record `elapsed_seconds` and `peak_memory_mb` for each stage in `pipeline_status.json`.  
  • Verification: a synthetic long‑running stage triggers the guard; the JSON contains `status: "aborted"` and a clear `reason: "time_limit_exceeded"` or `reason: "memory_limit_exceeded"`.  

- [ ] T015 [P] **Write `research.md` with concrete claim‑to‑artifact links** – for every quantitative claim in the manuscript (autocorrelation values, p‑value distribution, CI coverage, sensitivity flags, calibration results, heatmap observations) cite the exact identifiers: specific `(interval_start, interval_length, lag)` rows in `autocorrelation_stats.csv`, rows in `sensitivity_summary.csv`, PNG filenames, and JSON files. Also report the measured SC‑001 statistic (percentage of lags whose 95 % CI contains zero) and the `max_relative_error` from cross‑validation.  
  • Verification: a helper script parses `research.md`, extracts each cited identifier, and asserts that the referenced row or file exists in the corresponding artifact.  

- [ ] T016 [P] **Full‑pipeline integration test** – `tests/integration/test_full_pipeline.py` runs `python -m code.main` and checks:  
    1. Presence of all final artefacts (`autocorrelation_stats.csv`, three heatmaps, `calibration_test.json`, `empirical_uniformity.json`, `sensitivity_summary.csv`, `pipeline_status.json`, `manifest.sha256`).  
    2. Schema validation of `autocorrelation_stats.csv` against `contracts/mobius_stats.schema.yaml`.  
    3. Graceful continuation when a non‑core stage fails (inject a failure, verify exit 0 and correct logging).  
  • Verification: `pytest -q tests/integration/test_full_pipeline.py` passes.  

- [ ] T017 [P] **Research‑report handoff** – after `research.md` is finalized (T015), add a “Data & Code Availability” section that lists:  
    * exact artifact paths,  
    * their SHA‑256 checksums (from `data/checksums/manifest.sha256`),  
    * the Zenodo DOI where the repository will be deposited (placeholder `10.5281/zenodo.XXXXX`).  
  • Verification: the section exists, the listed checksums match those in the manifest, and the DOI placeholder follows the pattern `10.5281/zenodo.<digits>`.  

---  

### Dependency & requirement coverage summary  

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 (2‑bit packed array) | T002, T003 |
| FR‑002 (100 windows / FFT) | T004, T006 |
| FR‑003 (zero‑preserving permutations) | T008 |
| FR‑004 (p‑values & 95 % CI) | T008 |
| FR‑005 (heatmaps) | T012 |
| FR‑006 (CSV output) | T008, T009 |
| FR‑007 (zero‑density sensitivity) | T011 |
| SC‑001 (CI‑coverage) | T015 (reported) |
| SC‑002 (p < 0.05 significance) | T008, T009 |
| SC‑003 (≤ 6 h runtime) | T014 |
| SC‑004 (≤ 7 GB RAM) | T014 |
| SC‑005 (null‑calibration) | T010 |
| SC‑006 (heatmap correctness) | T012 |
| US‑1 (generate μ & autocorr) | T001‑T006 |
| US‑2 (permutation test) | T008‑T011 |
| US‑3 (visualisation) | T012 |
| Constitution VI (exact arithmetic) | T007 |
| Constitution III/V (checksums, state) | T015, T017 |

All tasks are ordered to respect data‑flow:

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017  

The pipeline fits within the GitHub‑Actions free‑tier limits (CPU‑only, ≤ 6 h, < 7 GB RAM) and uses only the allowed scientific Python stack.
