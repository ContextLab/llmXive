# Tasks: Autocorrelation of the Möbius Function in Short Intervals

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.

---  

## Phase 1: Setup and first end‑to‑end analysis  

**Goal**: Run an executable analysis on a small real input early, proving the pipeline works end‑to‑end.

- [X] T001 [P] [US1] Create a **quickstart.md** that documents the project layout, required Python version, pinned dependencies (`requirements.txt`), and the runnable command `python -m code.main --demo`.  
  *Path*: `quickstart.md`

- [X] T002 [] [US1] Implement a **linear‑time Möbius sieve** that computes μ(n) for `1 ≤ n ≤ 10⁷` and stores the result as an `int8` NumPy array.  
  *Path*: `code/sieve.py`

- [X] T003 [] [US1] Add unit tests for the sieve verifying known values (e.g., μ(1)=1, μ(2)=‑1, μ(4)=0).  
  *Path*: `tests/unit/test_sieve.py`

- [X] T004 [] [US1] Write a script `code/generate_mobius.py` that calls the sieve, saves the array to `data/raw/mobius_array.npy`, and selects **M = 20** stratified random window start indices for each interval length `L ∈ {10³,10⁴,10⁵}` (fixed seed = 42).  
  *Path*: `code/generate_mobius.py`

- [X] T000 [] [US1] Compute and record the SHA‑256 checksum of `data/raw/mobius_array.npy` (and any other generated raw data) after `code/generate_mobius.py` finishes, storing the result in `data/checksums/manifest.sha256`.  
  *Path*: `code/checksum.py`

- [X] T005 [] [US1] Implement **autocorrelation computation** for a single window (`L=10³`, lag `h=1`) and write the normalized result to `data/results/demo_autocorr.csv`. Include a sanity check that the value matches a hand‑computed reference for the chosen window.  
  *Path*: `code/autocorrelation.py`

- [~] T006 [] [US1] Add a focused integration test that runs the demo pipeline (`generate_mobius → autocorrelation`) and asserts that `data/results/demo_autocorr.csv` exists and contains a numeric entry with at least six decimal places.  
  *Path*: `tests/integration/test_demo_pipeline.py`

---  

## Phase 2: Complete the study and validate its evidence  

- [~] T007 [] [US1] Extend `code/autocorrelation.py` to compute **all lags** `h ∈ {1,…,⌊L/2⌋}` for every sampled window of each length `L`. Store the raw matrix in `data/processed/autocorr_raw.csv` (columns: `interval_start, interval_length, lag, autocorrelation`).  
  *Path*: `code/autocorrelation.py`

- [~] T008 [] [US2] Implement **block‑permutation** generation preserving the global zero‑density (block size `b=100`). Create `code/permutation.py` that, for a given window, returns 1 000 permuted sequences.  
  *Path*: `code/permutation.py`

- [~] T009 [] [US2] Add unit tests confirming that each permutation has the same count of `-1, 0, +1` as the original window and that blocks are shuffled, not internally reordered.  
  *Path*: `tests/unit/test_permutation.py`

- [~] T010 [] [US2] Build the **null distribution**: for every window and lag, compute autocorrelation on the 1 000 permuted sequences, then calculate two‑sided p‑values and the 95 % confidence interval (2.5 th / 97.5 th percentiles). Write results to `data/processed/autocorr_stats.csv` with columns `interval_start, interval_length, lag, autocorrelation, p_value, ci_lower, ci_upper, zero_count`.
  *Path*: `code/null_distribution.py`

- [~] T011 [] [US2] Apply the **Benjamini–Hochberg (BH) FDR correction** across all tested `(interval, lag)` pairs, add an `adjusted_p_value` column to `autocorr_stats.csv`.
  *Path*: `code/fdr_correction.py`

- [ ] T012 [] [US2] Perform the **zero‑density sensitivity analysis**: rerun the permutation step with the zero count altered by ±5 % and ±10 % (rounded to nearest integer). Compare resulting p‑values to the baseline and set a `sensitivity_flag` (`stable`, `sensitive`, `not_applicable`) in `autocorr_stats.csv`.   <!-- FAILED-IN-EXECUTION: code/sensitivity.py exit=-1 (TIMEOUT) --> <!-- FAILED-IN-EXECUTION: code/sensitivity.py exit=1 -->
  *Path*: `code/sensitivity.py`

- [ ] T014 [] [US3] Generate **heatmap visualizations** for each interval length `L`. Each PNG must show lag on the x‑axis, interval start on the y‑axis, color‑coded autocorrelation, a horizontal zero line, and shaded 95 % confidence bands from the permutation null. Save as `outputs/figures/heatmap_L{L}.png`.  
  *Path*: `code/viz.py`

- [~] T015 [] [] Conduct a **Kolmogorov–Smirnov (KS) uniformity test** on the collection of p‑values under the null hypothesis. Store the KS statistic and its p‑value in `data/processed/uniformity_test.json`.  
  *Path*: `code/uniformity_test.py`

---  

## Phase 3: Reproducible results and paper handoff  

- [ ] T016 [] [] Write a concise **methods & results summary** (`research.md`) that links each scientific claim to the exact rows/figures in the CSV/PNG artifacts, notes any intervals flagged by `sensitivity_flag`, and explains the interpretation of the theoretical variance benchmark.  
  *Path*: `research.md`

- [ ] T017 [] [] Create a **master orchestration script** `code/main.py` that runs the full pipeline in order: sieve → window sampling → autocorrelation → null distribution → FDR correction → sensitivity analysis → visualization → KS test. Add an integration test `tests/integration/test_full_pipeline.py` that invokes `python -m code.main` and verifies the presence of all final artifacts (`autocorr_stats.csv`, three heatmaps, `uniformity_test.json`).   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  *Path*: `code/main.py`

- [ ] T018 [] [] Update `quickstart.md` (Task T001) to point to the new master command (`python -m code.main`) and to list the expected output files for reproducibility checks.  

- [ ] T019 [] [US1] Measure total execution time of `python -m code.main`; abort with a clear error if runtime exceeds 6 hours, thereby enforcing SC‑003.  
  *Path*: `code/runtime_monitor.py`

- [ ] T020 [] [US1] Track peak RAM usage during the pipeline execution; abort with a clear error if memory consumption exceeds 7 GB, thereby enforcing SC‑004.  
  *Path*: `code/memory_monitor.py`

- [ ] T021 [] [US1] After the pipeline completes, compute SHA‑256 checksums for **all** files under `data/` and write a manifest `data/checksums/manifest.sha256` to satisfy Constitution Principle III (Data Hygiene).  
  *Path*: `code/checksums_all.py`

---  

### Dependency / Requirement Mapping  

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001 (linear sieve) | T002 |
| FR‑002 (full‑window autocorrelation) | T005, T007 |
| FR‑003 (1 000 permutations, zero‑preserving) | T008, T010 |
| FR‑004 (p‑values & 95 % CI) | T010 |
| FR‑005 (heatmap visualizations) | T014 |
| FR‑006 (CSV output) | T010, T011, T012 |
| FR‑007 (zero‑density sensitivity) | T012 |
| SC‑001 (compare to zero) | T007, T010, T014 |
| SC‑002 (p‑value vs α=0.05) | T010, T011 |
| SC‑003 (≤ 6 h runtime) | T019 |
| SC‑004 (≤ 7 GB RAM) | T020 |
| SC‑005 (uniformity of null) | T015 |
| Constitution III (checksums) | T000, T021 |

---  

**Checkpoint**: After completing T018, running `python -m code.main` must finish without error, produce all listed artifacts, and all unit/integration tests must pass. This demonstrates a complete, reproducible end‑to‑end study satisfying the specification.  