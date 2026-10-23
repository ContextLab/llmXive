# Tasks: Autocorrelation of the Möbius Function in Short Intervals  

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer/verifier feedback.  

All tasks respect data‑flow dependencies and use the canonical checklist format  
`- [ ] T### [P?] [USx?] …`. Checked boxes indicate work that has already passed verification; unchecked boxes are pending (including items that were rejected and must be redone).

---  

## Phase 1 – Setup & first end‑to‑end demo  

- [ ] T001 [US‑1] **Create `quickstart.md`** – document project layout, Python 3.11 version, pinned `requirements.txt`, and the demo command `python -m code.main --demo`.  
  • Path: `quickstart.md`  
  • Verification: `grep '--demo' quickstart.md` succeeds and the command runs without error, producing the expected demo files. **The generated `quickstart.md` is referenced in T015 (research.md) as the reproducibility hand‑off document.**  

- [ ] T002 [US‑1] **Implement linear‑time Möbius sieve** (`code/sieve.py`) that computes μ(n) for `1 ≤ n ≤ 10⁷` and writes an int8 array to `data/raw/mobius_array.npy`.  
  • Path: `code/sieve.py`, `data/raw/mobius_array.npy`  
  • Verification: unit tests `tests/unit/test_sieve.py` check known values (μ(1)=1, μ(2)=−1, μ(4)=0, μ(30)=−1, μ(3025)=0) and assert every entry lies in `{−1,0,1}`.  

- [ ] T003 [US‑1] **Add 2‑bit packing utilities** – create `code/pack.py` with `pack_mu` and `unpack_mu` that produce the packed ternary array `data/raw/mobius_2bit.npy` (≈ 2.5 MB). Include a round‑trip test for the full array and for 100 random sub‑slices.  
  • Path: `code/pack.py`, `data/raw/mobius_2bit.npy`  
  • Verification: tests `tests/unit/test_pack.py` confirm `unpack_mu(pack_mu(arr)) == arr` for the whole dataset and for random slices; SHA‑256 hashes of both files are recorded in `data/checksums/manifest.sha256`.  

- [ ] T004 [US‑1] **Generate deterministic window index** – with seed = 20231017 select **100 non‑overlapping windows per interval length** `L ∈ {1000,10000,100000}` (step = L, contiguous tiling from a seeded random offset) and write `data/processed/window_index.csv`.  
  • Path: `code/window.py`, `data/processed/window_index.csv` (columns `interval_start`, `interval_length`, `window_id`)  
  • Verification: `wc -l data/processed/window_index.csv` returns 300; a script asserts no windows overlap, the file is non‑empty, and that the file hash is reproducible on repeated runs.  

- [ ] T005 [US‑1] **Demo autocorrelation on a single window** – extract the first window (`L=1000`, start = first `interval_start` in `window_index.csv`), compute the normalized autocorrelation for lag = 1, and write a single‑row CSV `data/processed/demo_autocorr.csv`.  
  • Path: `code/demo_autocorr.py`, `data/processed/demo_autocorr.csv`  
  • Verification: the CSV contains exactly one row with columns `interval_start,interval_length,lag,autocorrelation`; the `autocorrelation` value has ≥ 6 decimal places and matches the hand‑computed reference (−0.047047047047) within absolute tolerance 1e‑9.  

---  

## Phase 2 – Full statistical pipeline (FR‑001 – FR‑006)  

- [ ] T006 [US‑1] **Compute full‑window autocorrelations** – extend `code/autocorrelation.py` to evaluate all lags `h = 1 … ⌊L/2⌋` for every window listed in `window_index.csv` using a float64 FFT‑based convolution (O(L log L) per window). Write rows (`interval_start`, `interval_length`, `lag`, `autocorrelation`, `zero_count`) to `data/processed/autocorrelation_raw.csv`.  
  • Path: `code/autocorrelation.py`, `data/processed/autocorrelation_raw.csv`  
  • Verification: script prints “written N rows”; test `tests/integration/test_autocorr_raw.py` confirms row count equals Σₗ 100·⌊L/2⌋ (≈ 5.55 M), that every `autocorrelation` lies in [−1, 1], and that the row count matches the 300 windows defined in `window_index.csv`.  

- [ ] T007 [US‑1] **Exact int64 cross‑validation (Constitution VI)** – for a random sample of ≥ 100 (window, lag) pairs per length, recompute the autocorrelation sum via pure integer arithmetic (`int64`) and compare to the FFT result. Record `n_pairs_checked` and `max_relative_error` in `data/processed/pipeline_status.json` under key `autocorrelation_crosscheck`.  
  • Path: `code/cross_validate_autocorrelation.py`, `data/processed/pipeline_status.json`  
  • Verification: unit test `tests/unit/test_crossvalidate.py` asserts `max_relative_error < 1e‑9`; the JSON entry must exist and contain the two fields. Failure aborts the pipeline.  

- [ ] T008 [US‑2] **Permutation null engine (full‑window)** – implement `code/permutation.py` that generates **1,000 zero‑preserving sign permutations for every window** (all 300 windows). Compute autocorrelations for all lags in a batched FFT, build per‑length null distributions, and write `data/processed/autocorrelation_stats.csv` with added columns `p_value`, `ci_lower`, `ci_upper`.  
  • Outputs: optional temporary `data/processed/permutation_null_{L}.npy`; final CSV `data/processed/autocorrelation_stats.csv`.  
  • Verification: schema validation against `contracts/mobius_stats.schema.yaml` passes; test `tests/unit/test_permutation.py` checks that `p_value` ∈ (0, 1] and the smallest possible p‑value is 0.002 (1/501). The task must complete for **all** windows; any failure aborts the pipeline with a clear error.  

- [ ] T009 [US‑2] **Benjamini–Hochberg FDR correction** – run `code/fdr_correction.py` which reads `autocorrelation_stats.csv`, applies `statsmodels.stats.multitest.multipletests` (α = 0.05, method=`'fdr_bh'`), and writes the column `adjusted_p_value` back to the same CSV.  
  • Path: `code/fdr_correction.py`, updated `data/processed/autocorrelation_stats.csv`  
  • Verification: unit test `tests/unit/test_fdr.py` confirms the column exists, all values lie in (0, 1], and that at least one row has `adjusted_p_value ≤ 0.05` when the raw p‑values indicate significance.  

- [ ] T010 [US‑2] **Null‑calibration (SC‑005)** – `code/calibration.py` performs two checks:  
    1. **Synthetic calibration** – generate 200 random‑sign windows per length (zero density = 6/π²), run the full permutation pipeline on them, and compute (a) a chi‑square goodness‑of‑fit on equal‑probability bins of the resulting p‑values and (b) a Kolmogorov–Smirnov test on a subsample of 5 windows. Write results to `data/processed/calibration_test.json`.  
    2. **Empirical uniformity** – apply the same chi‑square and KS tests to the *real* p‑values from `autocorrelation_stats.csv` and write `data/processed/empirical_uniformity.json`.  
  • Path: `code/calibration.py`, `data/processed/calibration_test.json`, `data/processed/empirical_uniformity.json`  
  • Verification: both JSON files contain fields `chi2_pvalue` and `ks_pvalue`; for the synthetic case both > 0.05, and the empirical file is parsable.  

- [ ] T011 [US‑2] **Zero‑density sensitivity analysis (FR‑007)** – `code/sensitivity.py` processes every window for each `L`. For each original window create four variants with zero counts altered by ±5 % and ±10 % (random insertions/deletions while preserving total length). For each variant run the permutation engine (1,000 permutations) and recompute raw p‑values. Set `significant_change = True` if any lag flips its raw‑significance status (`p < 0.05`). Produce `data/processed/sensitivity_summary.csv` with columns `interval_start,interval_length,adjustment,significant_change,affected_lags,affected_lags_fdr_significant`.  
  • Path: `code/sensitivity.py`, `data/processed/sensitivity_summary.csv`  
  • Verification: unit test `tests/unit/test_sensitivity.py` checks that zero‑count adjustments are correct, that the flag is boolean, and that at least one row shows `significant_change = True` on a toy dataset.  

- [ ] T012 [US‑3] **Generate heatmap figures** – rewrite `code/viz.py` to:  
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

- [ ] T013 [P] **Fault‑isolated orchestrator with resource guards** – refactor `code/main.py` into a stage‑wise driver where each core stage (`sieve`, `pack`, `window`, `demo_autocorr`, `autocorrelation`, `cross_validate`, `permutation`, `fdr_correction`, `calibration`, `sensitivity`, `viz`) runs inside a `try/except`. For every stage write an entry to `data/processed/pipeline_status.json` with fields `stage`, `status` (`ok`/`failed`), `elapsed_seconds`, and any `error` message. Additionally, monitor wall‑clock time (abort if > 6 h) and peak RAM (abort if > 7 GB) using `psutil`; record `peak_memory_mb` and `time_limit_exceeded`/`memory_limit_exceeded` flags in the JSON.  
  • Path: `code/main.py`, `data/processed/pipeline_status.json`  
  • Verification: integration test injects a deliberate exception in a non‑core stage and expects exit 0 with a populated `pipeline_status.json`; injecting an exception in a core stage yields exit 1. A synthetic long‑running stage triggers the time/memory guard and the JSON records the appropriate abort reason.  

- [ ] T014 [ ] **Generate SHA‑256 checksum manifest** – after all data and figure artifacts are produced, run `code/checksum.py` to create `data/checksums/manifest.sha256` containing one line per artifact: `<sha256>  <relative_path>`. This file satisfies Constitution III (Data Hygiene) and is required by downstream reproducibility checks.  
  • Path: `data/checksums/manifest.sha256`  
  • Verification: test `tests/unit/test_checksum.py` asserts the file exists, contains a line for every file listed in the manifest, and that each hash matches the actual file content.  

- [ ] T015 [ ] **Write `research.md` with concrete claim‑to‑artifact links and handoff section** – for every quantitative claim in the manuscript (autocorrelation values, p‑value distribution, CI coverage, sensitivity flags, calibration results, heatmap observations) cite the exact identifiers: specific rows in `autocorrelation_stats.csv`, rows in `sensitivity_summary.csv`, PNG filenames, and JSON files. Also report SC‑001 (percentage of lags whose 95 % CI contains zero) using the result from T016, and the cross‑validation `max_relative_error` from T007. Append a “Data & Code Availability” section listing each artifact path, its SHA‑256 checksum (from `manifest.sha256`), and the Zenodo DOI placeholder `[UNRESOLVED-CLAIM: 10.5281/zenodo.XXXXX — HTTP 404]`. **The earlier `quickstart.md` generated by T001 is referenced here as the reproducibility guide.**  
  • Path: `research.md`  
  • Verification: helper script parses `research.md`, extracts each cited identifier, asserts the referenced row or file exists, checks that the DOI matches `[UNRESOLVED-CLAIM: 10.5281/zenodo — HTTP 404].<digits>`, and that listed checksums match those in the manifest.  

- [ ] T016 [ ] **Compute CI‑coverage metric for SC‑001** – read `autocorrelation_stats.csv`, compute the proportion of lag entries where `ci_lower ≤ 0 ≤ ci_upper`, and write the result (as a JSON file `data/processed/ci_coverage.json` and also update `research.md` via T015).  
  • Path: `code/ci_coverage.py`, `data/processed/ci_coverage.json`  
  • Verification: test `tests/unit/test_ci_coverage.py` checks that the JSON contains a field `ci_coverage` with a value ≥ 0.8 (the concrete target for SC‑001).  

- [ ] T017 [ ] **Update `spec.md` SC‑001 placeholder** – modify `specs/001-autocorrelation-of-the-m-bius-function-i/spec.md` to replace the placeholder “[deferred]” in SC‑001 with a concrete numeric target (e.g., “≥ 80 % of the lags”).  
  • Path: `specs/001-autocorrelation-of-the-m-bius-function-i/spec.md`  
  • Verification: script checks that `SC‑001` now contains a concrete percentage value and no placeholder text.  

- [ ] T018 [ ] **Update `plan.md` permutation count** – edit `plan.md` so that the permutation null section mandates **1,000 zero‑preserving sign permutations for every window**, aligning the plan with FR‑003 and Constitution VII.  
  • Path: `plan.md`  
  • Verification: script parses `plan.md` and asserts the permutation count statement mentions “1,000 permutations per window”.  

---  

### Dependency & requirement coverage summary  

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001 (2‑bit packed array) | T002, T003 |
| FR‑002 (100 windows / FFT) | T004, T006 |
| FR‑003 (1,000 permutations per window) | T008, T018 |
| FR‑004 (p‑values & 95 % CI) | T008 |
| FR‑005 (heatmaps) | T012 |
| FR‑006 (CSV output) | T008, T009 |
| FR‑007 (zero‑density sensitivity) | T011 |
| SC‑001 (CI‑coverage) | T016 |
| SC‑002 (p < 0.05 significance) | T008, T009 |
| SC‑003 (≤ 6 h runtime) | T013 (guard) |
| SC‑004 (≤ 7 GB RAM) | T013 (guard) |
| SC‑005 (null‑calibration) | T010 |
| SC‑006 (heatmap correctness) | T012 |
| US‑1 (generate μ & autocorr) | T001‑T006 |
| US‑2 (permutation test) | T008‑T011 |
| US‑3 (visualisation) | T012 |
| Constitution VI (exact arithmetic) | T007 |
| Constitution VII (statistical null) | T008 |
| Constitution III/V (checksums, state) | T014, T015 |

All tasks are ordered to respect data‑flow:

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018  

The pipeline fits within the GitHub‑Actions free‑tier limits (CPU‑only, ≤ 6 h, < 7 GB RAM) and uses only the allowed scientific Python stack.  

---  

## Phase 4 – Additional notes  

- All random processes use the deterministic seed `20231017` (or derived seeds as documented).  
- Every output file is listed in `data/checksums/manifest.sha256`.  
- The orchestrator (`code/main.py`) can be invoked with `--demo` to run only the demo path (T005) or with no flags to run the full pipeline.  
