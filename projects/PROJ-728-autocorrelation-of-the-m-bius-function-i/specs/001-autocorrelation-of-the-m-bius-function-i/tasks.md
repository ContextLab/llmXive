# Tasks: Autocorrelation of the Möbius Function in Short Intervals  

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer/verifier feedback.  

**Revision note (R2)** – This revision addresses the outstanding reviewer concerns:  

1. Re‑open and correct the **sensitivity analysis** (T012 → T027‑T030).  
2. Re‑open the **visualisation** task (T014) and implement the required zero‑line, confidence‑band overlay, and pixel‑level PNG checks.  
3. Re‑open the **research‑report linking** task (T016) and provide concrete row identifiers for every claim.  
4. Re‑open the **orchestrator** (T017) – now fault‑isolated and writing a detailed `pipeline_status.json`.  
5. Ensure all checksum, state‑file, and resource‑guard tasks are present and correctly referenced.  

The tasks below are ordered to respect data‑flow dependencies and are grouped into three research phases. Checked boxes (`[x]`) indicate work that has already passed verification; unchecked boxes (`[ ]`) denote work that still needs to be completed or re‑executed.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal, reproducible pipeline on real Möbius data using the final window‑sampling contract. |
|------|---------------------------------------------------------------------------------------------------|

- [ ] T001 [P] [US-1] **Create `quickstart.md`** – document project layout, Python 3.11 version, pinned `requirements.txt`, and the demo command `python -m code.main --demo`.  
  *Path*: `quickstart.md`  
  *Verification*: `grep --color=never '--demo' quickstart.md` and manual run of the command produces the expected demo files.

- [ ] T002 [P] [US-1] **Implement linear‑time Möbius sieve** (`code/sieve.py`) that computes μ(n) for `1 ≤ n ≤ 10⁷` and writes an `int8` array to `data/raw/mobius_array.npy`.  
  *Verification*: unit test `tests/unit/test_sieve.py` passes for known values and the array contains only `{-1,0,1}`.

- [ ] T003 [P] [US-1] **Add unit tests for the sieve** (μ(1)=1, μ(2)=−1, μ(4)=0, μ(30)=−1, μ(3025)=0) and a property test that all entries lie in `{-1,0,1}`.  
  *Path*: `tests/unit/test_sieve.py`  
  *Verification*: `pytest -q tests/unit/test_sieve.py` → all tests pass.

- [ ] T004 [P] [US-1] **Generate Möbius array, pack to 2‑bit, and sample windows** –  
  1. Save the working `int8` array (`data/raw/mobius_array.npy`).  
  2. Pack it into a 2‑bit ternary array `data/raw/mobius_2bit.npy` (FR‑001).  
  3. With seed = 20231017, select **100 non‑overlapping windows per L ∈ {10³,10⁴,10⁵}** (step = L, contiguous tiling from a seeded random offset).  
  4. Emit exact start indices to `data/processed/window_index.csv` (columns `interval_start`, `interval_length`, `window_id`).  
  *Path*: `code/sieve.py`, `data/raw/mobius_array.npy`, `data/raw/mobius_2bit.npy`, `data/processed/window_index.csv`  
  *Verification*: `wc -l data/processed/window_index.csv` = 300 and a script asserts non‑overlap.

- [ ] T005 [P] [US-1] **Demo autocorrelation** – compute the normalized autocorrelation for the first sampled window (`L=10³`, lag = 1) and write the result to `data/processed/demo_autocorr.csv`. Include a sanity check against a hand‑computed reference for that window.  
  *Path*: `code/autocorrelation.py`, `data/processed/demo_autocorr.csv`  
  *Verification*: CSV contains a single row with at least six decimal places; value matches the manual reference within 1e‑9.

- [ ] T006 [P] [US-1] **Demo pipeline integration test** – run the full demo (`python -m code.main --demo`) and assert that `demo_autocorr.csv` and `window_index.csv` exist, contain the correct number of rows, and that the checksum manifest is updated.  
  *Path*: `tests/integration/test_demo_pipeline.py`  
  *Verification*: `pytest -q tests/integration/test_demo_pipeline.py` passes.

- [ ] T000 [P] **Record SHA‑256 checksum of the generated Möbius array** – after `T004` finishes, compute the checksum of `data/raw/mobius_array.npy` and append it to `data/checksums/manifest.sha256`.  
  *Path*: `code/main.py` (checksum helper) and `data/checksums/manifest.sha256`  
  *Verification*: `sha256sum data/raw/mobius_array.npy` matches the entry in the manifest.

- [ ] T022 [P] [US-1] **2‑bit packing / unpacking utilities** – add `pack_mu` and `unpack_mu` functions to `code/sieve.py`, write the packed file (`mobius_2bit.npy`), and extend `tests/unit/test_sieve.py` with round‑trip tests over the full array and random slices. Append both file checksums to the manifest without overwriting existing entries.  
  *Verification*: round‑trip test passes; both checksums appear in `manifest.sha256`.

---

## Phase 2 – Complete the study and validate its evidence  

| Goal | Produce the full statistical analysis, permutation null, sensitivity checks, and calibration. |
|------|----------------------------------------------------------------------------------------------|

- [ ] T007 [P] [US-1] **Full‑window autocorrelation** – extend `code/autocorrelation.py` to compute normalized autocorrelation for **all lags `h = 1 … ⌊L/2⌋`** for every sampled window. Write rows (`interval_start, interval_length, lag, autocorrelation`) to a temporary buffer for later merging.  
  *Path*: `code/autocorrelation.py`  
  *Verification*: spot‑check a random window‑lag pair against a direct `int64` sum (see T024).

- [ ] T008 [P] [US-2] **Permutation engine (FR‑003)** – implement in `code/permutation.py` a function that, for a given window, keeps zero positions fixed and uniformly shuffles the signs of the non‑zero entries, generating **exactly 1 000** permutations using a per‑window seed `20231017 + window_id`.  
  *Verification*: unit test `tests/unit/test_permutation.py` confirms each permutation preserves the zero count and the multiset of non‑zero signs.

- [ ] T010 [P] [US-2] **Null distribution, p‑values & 95 % CI (FR‑004)** – for every window and lag, compute autocorrelations of the 1 000 permutations (batched FFT over a `(1000, L)` matrix), then calculate two‑sided p‑values `p = (#{|r_perm| ≥ |r_obs|} + 1)/1001` and the 2.5 % / 97.5 % percentile confidence bounds.  
  *Outputs*: `data/processed/autocorrelation_stats.csv` (conforms to `contracts/mobius_stats.schema.yaml`).  
  *Verification*: schema validation test passes; edge‑case handling (`p < 0.001` / `p > 0.999`, all‑zero windows) is exercised in `tests/unit/test_permutation.py`.

- [ ] T011 [P] [US-2] **Benjamini–Hochberg FDR correction (α = 0.05)** – apply `statsmodels.multipletests` to all raw p‑values and add the column `adjusted_p_value` to `autocorrelation_stats.csv`.  
  *Verification*: a downstream test confirms that the column exists and that the smallest adjusted p‑value ≤ 0.05 is correctly flagged.

- [ ] T024 [P] [US-1] **Exact int64 cross‑validation (Constitution VI)** –  
  1. Exhaustively recompute Σ μ(k+i)μ(k+i+h) for **all (window, lag) pairs at L = 10³** (100 × 500 = 50 k checks) and assert agreement with the FFT result (relative error < 1e‑9).  
  2. For L = 10⁴ and 10⁵, sample ≥ 100 random (window, lag) pairs per L and perform the same check.  
  3. Record `n_pairs_checked` and `max_relative_error` in `data/processed/pipeline_status.json` under `autocorrelation_crosscheck`.  
  *Verification*: unit test `tests/unit/test_autocorrelation.py` runs the exhaustive L = 10³ check; a random‑sample test runs for larger L.

- [ ] T025 [P] [US-2] **Null‑calibration & empirical uniformity (SC‑005)** – `code/calibration.py` produces two JSON files:  
  1. `calibration_test.json` – chi‑square and KS tests on p‑values from **synthetic random‑sign windows** (200 windows per L). Success requires both p‑values > 0.05.  
  2. `empirical_uniformity.json` – same tests applied to the **real μ p‑values** (research result, not a validation of the test).  
  *Verification*: unit test `tests/unit/test_calibration.py` checks file existence, correct fields, and that the calibration JSON reports p > 0.05.

- [ ] T027 [P] [US-2] **Sensitivity – adjusted‑window construction (FR‑007)** – in `code/sensitivity.py` create four adjusted windows per original window (`+5 %`, `‑5 %`, `+10 %`, `‑10 %` zero count) by randomly converting ±1 entries to 0 (insertion) or 0 entries to ±1 (deletion) while preserving total length L, then reshuffle non‑zero signs. Deterministic seeding is used.  
  *Verification*: a test confirms that each adjusted window has the exact target zero count and unchanged non‑zero sign multiset.

- [ ] T028 [P] [US-2] **Sensitivity – computation & comparison** – for each adjusted window generate 1 000 permutations (batched FFT), compute autocorrelations for all lags, and compare **raw p < 0.05** between the original and adjusted runs. Record both `p_raw` and `adjusted_p_value` status for every lag that flips.  
  *Verification*: unit test checks that `significant_change` is True when any lag flips and that the CSV `sensitivity_summary.csv` contains the expected columns.

- [ ] T029 [P] [US-2] **Sensitivity – output & degradation guard** – write `sensitivity_flag` into `autocorrelation_stats.csv` and produce `data/processed/sensitivity_summary.csv` (columns `interval_start`, `interval_length`, `adjustment`, `significant_change`, `affected_lags`, `affected_lags_fdr_significant`). If cumulative runtime exceeds 4 h, automatically restrict the analysis to L = 10³ and 10⁴, record the restriction in `pipeline_status.json`, and continue without reducing the 1 000‑permutation count.  
  *Verification*: integration test asserts the guard works (by mocking a long runtime) and that the JSON entry reflects the reduced scope.

- [ ] T030 [P] [US-2] **Sensitivity regression test** – unit test that runs the sensitivity stage on L = 10³, asserts total wall‑clock time < 60 s, and verifies deterministic reproducibility of adjusted windows under the fixed seed.  
  *Path*: `tests/unit/test_sensitivity.py`

---

## Phase 3 – Reproducible results, visualisation, and hand‑off  

| Goal | Produce publication‑ready artefacts, ensure rigorous verification, and hand off to the paper pipeline. |
|------|--------------------------------------------------------------------------------------------------------|

- [ ] T014 [P] [US-3] **Heatmap visualisation (FR‑005, SC‑006)** – rewrite `code/viz.py` to:  
  1. Load `autocorrelation_stats.csv` and group by `interval_length`.  
  2. For each L ∈ {10³, 10⁴, 10⁵} render `outputs/figures/heatmap_L{L}.png` (≥ 1200 × 1200 px, DPI 150).  
  3. Overlay a **black dashed contour at autocorrelation = 0** (`plt.contour(..., levels=[0.0], colors='black', linestyles='--')`).  
  4. Add a confidence‑band panel sharing the lag axis, plotting per‑lag `ci_lower`/`ci_upper` as a shaded region.  
  5. Mark cells with `adjusted_p_value < 0.05` using red circles.  
  6. Unit test `tests/unit/test_viz.py` validates: (a) PNG format and resolution ≥ 1000 × 1000 px (via Pillow), (b) presence of the zero‑contour artist, (c) alignment of the CI band axes, and (d) pixel‑level detection of the dashed zero line (search for a row of dark pixels at the expected y‑coordinate).  
  *Verification*: test passes and the three PNG files appear in `outputs/figures/`.

- [ ] T031 [P] [US-1] **Fault‑isolated orchestrator (fixes T017)** – refactor `code/main.py` into a stage‑wise driver where each stage runs inside a `try/except`, logs success/failure, writes per‑stage entries (`status`, `elapsed_seconds`, `error`) to `data/processed/pipeline_status.json`, and continues with dependent stages skipped if a non‑core stage fails. Core stages (sieve, autocorrelation, permutation) cause a non‑zero exit only on failure.  
  *Verification*: running `python -m code.main` with an injected failure (e.g., raise in a dummy stage) yields exit 0 and a populated `pipeline_status.json`.

- [ ] T032 [P] **Resource guards (SC‑003, SC‑004)** – within `code/main.py` monitor wall‑clock time (abort if > 6 h) and peak RAM (abort if > 7 GB, using `psutil`). Record measured `elapsed_seconds` and `peak_memory_mb` for each stage in `pipeline_status.json`.  
  *Verification*: a synthetic long‑running stage triggers the guard and the JSON reflects the abort reason.

- [ ] T033 [P] **Checksums & state‑file recording (Constitution III/V)** – after a successful run, compute SHA‑256 checksums for **all files under `data/`** *and* the three heatmap PNGs, append them to `data/checksums/manifest.sha256`, and also write the same map to the project‑state YAML at `state/projects/PROJ-728-autocorrelation-of-the-m-bius-function-i.yaml` (updating `updated_at`). Update `quickstart.md` to list all expected output artefacts.  
  *Verification*: `manifest.sha256` contains entries for every data file and PNG; the state YAML includes an `artifact_hashes` map matching the manifest.

- [ ] T034 [P] **Full‑pipeline integration test with fault injection** – `tests/integration/test_full_pipeline.py` invokes `python -m code.main`, checks for the presence of every final artefact (`autocorrelation_stats.csv`, three PNGs, `calibration_test.json`, `empirical_uniformity.json`, `sensitivity_summary.csv`, `pipeline_status.json`, `manifest.sha256`), validates the CSV against `contracts/mobius_stats.schema.yaml`, and performs a controlled failure of a non‑core stage to confirm graceful continuation and correct logging.  
  *Verification*: `pytest -q tests/integration/test_full_pipeline.py` passes.

- [ ] T016 [P] **Research‑report with concrete claim‑to‑artifact links (US‑1)** – author `research.md` such that **every quantitative claim** is tied to an explicit identifier:  
  *   Autocorrelation rows are cited by the exact `(interval_start, interval_length, lag)` triple (e.g., “Row 42 → (123456, 10⁴, 57)”).  
  *   Sensitivity flags are listed by the exact `interval_start` values from `sensitivity_summary.csv`.  
  *   Calibration vs. empirical uniformity results are referenced by the JSON filenames.  
  *   The heatmap figures are referenced by their precise filenames (`heatmap_L1000.png`, …).  
  *   The proportion of lags whose 95 % CI contains zero (SC‑001) is reported as a measured statistic (no pass/fail claim because the threshold is deferred).  
  *   All cross‑validation outcomes (exhaustive L = 10³ check, sampled L = 10⁴/10⁵ check) are described with their recorded `max_relative_error`.  
  *Verification*: a script parses `research.md`, extracts each cited identifier, and confirms the corresponding entry exists in the appropriate CSV/JSON/PNG file.

---

## Dependencies & requirement coverage

| Spec requirement | Satisfying task(s) | Demonstration command |
|------------------|-------------------|-----------------------|
| FR‑001 (2‑bit packed Möbius array) | T004, T022 | `pytest tests/unit/test_sieve.py` |
| FR‑002 (100 windows/L, FFT autocorrelation) | T004, T005, T007 | `python -m code.main --demo` |
| FR‑003 (1 000 zero‑preserving permutations) | T008 | `pytest tests/unit/test_permutation.py` |
| FR‑004 (p‑values, 95 % CI) | T010 | schema validation on `autocorrelation_stats.csv` |
| FR‑005 (heatmaps with zero line & CI bands) | T014 | `pytest tests/unit/test_viz.py` |
| FR‑006 (structured CSV output) | T010, T011 | `pytest -q tests/integration/test_full_pipeline.py` |
| FR‑007 (zero‑density sensitivity) | T027‑T030 | `pytest tests/unit/test_sensitivity.py` |
| SC‑001 (CI‑coverage measurement) | T010, T016 | statistic reported in `research.md` |
| SC‑002 (p < 0.05 significance) | T010, T011, T016 | rows in CSV |
| SC‑003 (≤ 6 h runtime) | T032 | `pipeline_status.json` elapsed times |
| SC‑004 (≤ 7 GB RAM) | T032 | `pipeline_status.json` peak memory |
| SC‑005 (null‑calibration uniformity) | T025 | `calibration_test.json` |
| SC‑006 (heatmap correctness) | T014 | `test_viz.py` pixel‑level check |
| US‑1, US‑2, US‑3 | Various tasks above | – |
| Constitution VI (exact arithmetic) | T024 | cross‑validation entries in `pipeline_status.json` |

**Execution order** (enforced by dependencies):  

T001 → T002 → T003 → T004 → T005 → T006 → T000 → T022 → T007 → T008 → T010 → T011 → T024 → T025 → T027 → T028 → T029 → T030 → T014 → T031 → T032 → T033 → T034 → T016  

All tasks respect the data flow and stay within the free‑tier compute limits (CPU‑only, ≤ 6 h, < 7 GB RAM). No GPU resources are required.
