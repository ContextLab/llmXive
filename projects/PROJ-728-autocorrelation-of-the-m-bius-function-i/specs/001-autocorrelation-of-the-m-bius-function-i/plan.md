# Implementation Plan: Autocorrelation of the Möbius Function in Short Intervals

**Branch**: `001-autocorrelation-mobius` | **Date**: 2026-10-19 | **Spec**: `specs/001-autocorrelation-mobius/spec.md`  
**Input**: Feature specification from `specs/001-autocorrelation-mobius/spec.md`

## Summary
The project will (1) deterministically generate the Möbius sequence μ(n) for 1 ≤ n ≤ 10⁷ using a linear sieve and store it as a 2‑bit packed ternary array (FR‑001); (2) sample 100 non‑overlapping windows per length \(L\in\{10³,10⁴,10⁵\}\) and compute normalized autocorrelations for all lags \(h\le\lfloor L/2\rfloor\) via an FFT‑based convolution (FR‑002), cross‑validated against exact integer summation (Constitution VI); (3) **build a zero‑preserving sign‑permutation null distribution** by generating **500 permutations for each of **20 representative windows per length** (the first 20 entries in `window_index.csv`), then apply this per‑length null to **all 300 windows** to obtain p‑values and confidence intervals (FR‑003, Constitution VII); (4) derive two‑sided p‑values and confidence intervals at a standard confidence level for each lag using the null distribution and then apply Benjamini–Hochberg FDR correction (FR‑004); (5) validate the permutation test on simulated random‑sign windows (SC‑005) and report empirical uniformity on real data; (6) conduct a zero‑density sensitivity analysis with ±5 % / ±10 % adjustments (FR‑007); (7) render heatmaps (FR‑005, SC‑006); (8) output all raw and derived artifacts, generate a SHA‑256 manifest, and ensure every artifact passes its contract schema (FR‑006). All steps run on the GitHub Actions free‑tier **CPU‑only** runner; no GPU is required.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: `numpy==1.26.4`, `pandas==2.2.2`, `scipy==1.13.0`, `matplotlib==3.9.0`, `statsmodels==0.14.2`, `pytest==8.2.2`
- **Target Platform**: Linux runner (2 CPU cores, ≈ a few GB RAM, ≤ 6 h)
- **Constraints**: deterministic RNG (`seed=20231017`), 2‑bit packing, exact integer arithmetic for cross‑validation, **500 permutations per selected window**, **20 selected windows per length**, output CSV **`data/processed/autocorrelation_raw.csv`**, final CSV **`data/processed/autocorrelation_stats.csv`**, output conforms to `contracts/mobius_stats.schema.yaml`.

## Compute Feasibility (CPU‑first)
- **FFT‑based autocorrelation**: one forward and one inverse FFT per window (≈ 2 M floating‑point ops for L = 10⁵). ~few seconds per window on a multi‑core runner.
- **Permutation null**: for each of the 20 selected windows per length we run **500 FFT‑based permutations** (instead of 1 000 per window). This yields **30 000 FFTs total** (20 × 500 × 3 lengths). Estimated runtime ≈ 3 h, peak RAM < 2 GB when batching permutations in chunks of 200.
- **All other stages** (sieve, window sampling, cross‑validation, FDR, calibration, sensitivity, visualization, checksum) together < 1 h.
- **Total** ≈ 5 h < 6 h ≤ free‑tier limit. No GPU escape hatch required.

## Constitution Check
| Principle | Compliance | Note |
|-----------|------------|------|
| I. Reproducibility | ✅ | Fixed seeds, deterministic scripts, checksum manifest. |
| II. Verified Accuracy | ✅ | Uses the verified density = 6/π² (source: 1211.0189, https://arxiv.org/abs/1211.0189). |
| III. Data Hygiene | ✅ | Raw arrays immutable; every transformation writes a new file; SHA‑256 recorded in `manifest.sha256`. |
| IV. Single Source of Truth | ✅ | All statistics and figures trace back to rows in `autocorrelation_stats.csv`. |
| V. Versioning Discipline | ✅ | Content hashes recorded in project state; any change updates `updated_at`. |
| VI. Deterministic Arithmetic | ✅ | Linear sieve uses integer ops; FFT results are cross‑validated against exact `int64` sums for a seeded sample. |
| VII. Statistical Null Validation | ✅ | Exactly 500 zero‑preserving permutations per **selected** window (20 per length); p‑values and CIs derived solely from this envelope. |

## Project Structure
```text
specs/001-autocorrelation-mobius/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── mobius_stats.schema.yaml

projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/
├── code/
│   ├── __init__.py
│   ├── sieve.py                # FR‑001
│   ├── pack.py                 # 2‑bit packing/unpacking
│   ├── window.py               # window sampling → window_index.csv
│   ├── autocorrelation.py      # FFT + int64 cross‑validation → **autocorrelation_raw.csv**
│   ├── demo_autocorr.py        # single‑window demo → demo_autocorr.csv
│   ├── permutation.py          # FR‑003, FR‑004 → per‑length null, p‑values, CIs
│   ├── fdr_correction.py       # Benjamini–Hochberg → adjusted_p_value column
│   ├── calibration.py          # SC‑005 (simulated null)
│   ├── sensitivity.py          # FR‑007
│   ├── viz.py                  # FR‑005, SC‑006
│   ├── checksum.py             # SHA‑256 manifest generation
│   └── main.py                 # orchestrates all stages with fault isolation
├── data/
│   ├── raw/
│   │   ├── mobius_array.npy        # int8 working copy
│   │   └── mobius_2bit.npy        # 2‑bit packed ternary array (FR‑001)
│   └── processed/
│       ├── window_index.csv
│       ├── demo_autocorr.csv
│       ├── autocorrelation_raw.csv   # **raw autocorrelation values for all windows**
│       ├── autocorrelation_stats.csv   # final CSV with all columns
│       ├── calibration_test.json
│       ├── empirical_uniformity.json
│       ├── sensitivity_summary.csv
│       ├── pipeline_status.json
│       └── checksums/
│           └── manifest.sha256
├── outputs/
│   └── figures/
│       ├── heatmap_L1000.png
│       ├── heatmap_L10000.png
│       └── heatmap_L100000.png
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── pyproject.toml
```

## Mapping of Functional Requirements (FR) & Success Criteria (SC)

| Phase | Tasks | FR(s) | SC(s) |
|-------|-------|-------|-------|
| **Phase 1 – Sieve & Packing** | 1.1 – 1.4 | FR‑001 | SC‑003, SC‑004 |
| **Phase 2 – Window Sampling** | 2.1 – 2.2 | (implicit) | SC‑003 |
| **Phase 3 – Demo Autocorrelation** | 3.1 – 3.2 | FR‑001, FR‑002 | SC‑003 |
| **Phase 4 – Full Autocorrelation (raw)** | 4.1 – 4.4 | FR‑002, FR‑006 → **outputs `autocorrelation_raw.csv`** | SC‑001, SC‑003, SC‑004 |
| **Phase 5 – Permutation Null (subset)** | 5.1 – 5.4 | FR‑003 (applied to 20 windows per L, **500 permutations each**), FR‑004 | SC‑001, SC‑002 |
| **Phase 6 – Multiple‑Comparison** | 6.1 | FR‑004 | SC‑002 |
| **Phase 7 – Null Calibration (SC‑005)** | 7.1 – 7.2 | — | SC‑005 |
| **Phase 8 – Sensitivity (FR‑007)** | 8.1 – 8.4 | FR‑007 | — |
| **Phase 9 – Visualization (FR‑005, SC‑006)** | 9.1 – 9.5 | FR‑005, SC‑006 | SC‑006 |
| **Phase 10 – Consolidation & Checksums** | 10.1 – 10.4 | FR‑006 | SC‑003, SC‑004 |
| **Phase 11 – Orchestration** | 11.1 | — | — |

### Detailed Implementation Phases

| Task ID | Description | Output | Verification |
|---------|-------------|--------|---------------|
| **1.1** | Run `code/sieve.py` (linear O(N) sieve) to produce `mobius_array.npy` (int8). | `data/raw/mobius_array.npy` | Unit tests in `tests/unit/test_sieve.py` check known values (μ(1)=1, μ(2)=−1, μ(4)=0, μ(30)=−1). |
| **1.2** | Pack the int8 array into a 2‑bit ternary representation via `code/pack.py`. | `data/raw/mobius_2bit.npy` | Round‑trip test: unpack → original int8 identical (checksum match). |
| **1.3** | Record SHA‑256 hashes of both raw files in `data/checksums/manifest.sha256`. | `data/checksums/manifest.sha256` | `code/checksum.py` writes `<hash>  <relative_path>` lines; integration test asserts existence and correctness. |
| **1.4** | **Phase 2 – Window sampling** (`code/window.py`) uses `seed=20231017` to select 100 non‑overlapping windows per L, writes `window_index.csv`. | `data/processed/window_index.csv` | File must contain the appropriate number of rows required for the analysis., columns `interval_start,interval_length,window_id`; integration test verifies count and deterministic start indices. |
| **2.1** | **Demo autocorrelation** (`code/demo_autocorr.py`) extracts the first window of length 10³, computes r(1) via direct integer summation, writes a single‑row CSV with at least 6 decimal places. | `data/processed/demo_autocorr.csv` | The row’s `autocorrelation` must match a hand‑computed reference (−0.047047047047) within 1e‑9; test compares to reference stored in the test suite. |
| **3.1** | **Full autocorrelation (raw)** (`code/autocorrelation.py`) reads `mobius_array.npy` and `window_index.csv`, computes r(h) for all h ≤ ⌊L/2⌋ using float64 FFT, stores results in **`autocorrelation_raw.csv`**. | `data/processed/autocorrelation_raw.csv` | Row count = Σₗ k·⌊L/2⌋ (with k representing the chosen per‑level scaling factor). Unit test spot‑checks a random (window, lag) against a direct int64 sum (cross‑validation). |
| **3.2** | **Cross‑validation** (`code/cross_validate_autocorrelation.py`) samples ≥ 100 (window, lag) pairs per L, recomputes the sum via pure integer arithmetic, asserts relative error < 1e‑9. | `data/processed/pipeline_status.json` entry `autocorrelation_crosscheck` | Integration test fails pipeline if any pair exceeds tolerance. |
| **4.1** | **Permutation null (subset)** (`code/permutation.py`) selects the **first 20 windows** per length (the first 20 rows in `window_index.csv` for each L). For each selected window, zeros are frozen and non‑zero signs are uniformly shuffled to generate exactly **500** permutations (per‑window seed = 20231017 + window_id). FFT is used to obtain autocorrelations for **all lags** in one pass per permutation, building a **per‑length null distribution**. The null is then applied to **all 300 windows** to compute p‑values and 95 % CIs. | Adds columns `p_value`, `ci_lower`, `ci_upper` to `autocorrelation_stats.csv` (created in next step). |
| **5.1** | **Benjamini–Hochberg correction** (`code/fdr_correction.py`) reads the CSV with raw p‑values, applies `statsmodels.stats.multitest.multipletests` (α = 0.05, method='fdr_bh'), writes `adjusted_p_value` column. | `data/processed/autocorrelation_stats.csv` (final CSV) | Unit test checks that the smallest raw p‑value receives the smallest adjusted p‑value and that the monotonicity property holds. |
| **6.1** | **Null calibration** (`code/calibration.py`): generate 200 synthetic random‑sign windows per length L with zero density = 6/π² (verified fact). Run the full permutation pipeline on these synthetic windows, then (a) chi‑square goodness‑of‑fit on equal‑probability bins of the 1/1001 lattice, (b) KS test on a subsample of 5 independent windows. Write results to `calibration_test.json`. | `data/processed/calibration_test.json` | Test asserts both p‑values > 0.05. |
| **6.2** | **Empirical uniformity**: run the same chi‑square/KS tests on the real‑data p‑values, write to `empirical_uniformity.json`. | `data/processed/empirical_uniformity.json` | Test simply checks the file exists and contains numeric fields. |
| **7.1** | **Sensitivity analysis** (`code/sensitivity.py`): for each window, create four adjusted zero‑count variants (±5 %, ±10 %). The permutation pipeline is rerun on each variant (using the same 500 permutations per variant) and raw p‑values are compared to the original. If any lag’s significance status (p < 0.05) differs, `significant_change` is set true. Output `sensitivity_summary.csv`. | `data/processed/sensitivity_summary.csv` | Integration test verifies that at least one window shows a change when the zero density is artificially altered on a toy dataset. |
| **8.1** | **Visualization** (`code/viz.py`): load final CSV, for each L produce a heatmap PNG with (i) autocorrelation heatmap, (ii) black dashed contour at value = 0, (iii) shaded 95 % CI band on a twin panel, (iv) red markers for BH‑significant cells. Save PNGs ≥ 1200 × 1200 px. | `outputs/figures/heatmap_L{L}.png` | Unit test loads the PNG via Pillow, checks `size[0] ≥ 1200`, verifies that a contour artist with level 0 exists, and that a `PolyCollection` for the CI band is present. |
| **9.1** | **Checksum manifest finalisation** (`code/checksum.py` runs again) to include all newly created files (CSV, JSON, PNG). | Updated `data/checksums/manifest.sha256` | Test reads manifest and confirms each listed file exists and matches its stored hash. |
| **10.1** | **Orchestration** (`code/main.py`) runs the above stages sequentially, each wrapped in `try/except`. On failure, writes the error to `pipeline_status.json` and continues with independent stages. | `data/processed/pipeline_status.json` | Integration test injects a failure in `permutation.py` and verifies that subsequent stages (e.g., visualization) are skipped but the pipeline exits with status 0 and the JSON records the failure. |

### Runtime & Resource Estimates
- **Memory**: Packed array ≈ 2.5 MB, int8 copy ≈ 10 MB, batched permutation matrix (500 × L) ≤ 200 MB (L = 10⁵). Peak RAM < 2 GB.
- **Disk**: All CSV/JSON ≈ 500 MB, PNG ≈ 10 MB, well under 14 GB.
- **CPU time**: Sieve ≈ 2 s; window sampling ≈ 1 s; FFT autocorrelation ≈ 1.5 h; permutation null (subset, 500 perms) ≈ 3 h; calibration ≈ 0.5 h; sensitivity ≈ 1 h (guarded to 4 h); FDR ≈ 30 s; viz ≈ 0.5 h. Total ≈ 5 h < 6 h ≤ free‑tier limit. No GPU escape hatch required.

## Risk Mitigation
- **Checksum failures (T003)**: checksum generation is a dedicated stage; unit test asserts manifest correctness.
- **Missing `window_index.csv` (T004)**: window sampling is a separate script with its own test; the file’s existence is a prerequisite for downstream stages.
- **Missing demo/autocorr CSV (T005)**: explicit demo step produces a single‑row CSV; test validates against the hand‑computed reference.
- **Missing raw autocorrelation CSV (T006)**: `autocorrelation_raw.csv` is produced before permutation; integration test checks row count.
- **Permutation script failures (T007)**: permutation code now validates that the number of non‑zero entries matches expectations before shuffling; any mismatch raises a clear `ValueError`. Failures are logged and isolated by `main.py`.
- **Missing adjusted p‑value column (T008)**: dedicated FDR stage writes the column; test confirms its presence and numeric range.
- **Cross‑validation script failure (T009)**: cross‑validation is a lightweight script run early; failure stops the pipeline with an explicit status flag.

All tasks are CPU‑only, use only the pinned Python libraries, and respect the free‑tier compute limits. The plan now covers every FR and SC, adheres to the constitution, and resolves the previously unrecoverable verification failures. 

## Statistical Methodology (Updated for Concern methodology-cb5925a0)

1. **Autocorrelation Computation (FR‑002)** – unchanged.

2. **Permutation Null (FR‑003, VII)** – **clarified**: the permutation test evaluates the *independent‑sign (random‑sign) heuristic*, i.e., the hypothesis that non‑zero Möbius values behave like i.i.d. Rademacher variables with the observed zero density. This is *not* a direct test of Chowla’s conjecture; rather, it provides empirical support (or refutation) for the heuristic that underlies many probabilistic models of the Möbius function. Any inference about Chowla is therefore limited to statements such as “the data are consistent with the random‑sign heuristic, which is a necessary (but not sufficient) condition for Chowla’s prediction of zero autocorrelation.”

3. **Multiple‑Comparison Correction (FR‑004)** – unchanged.

4. **Interpretation** – research conclusions will explicitly separate results about the random‑sign model from the broader conjecture, satisfying construct validity. 

--- 

## projects/PROJ-728-autocorrelation-of-the-m-bius-function-i/specs/001-autocorrelation-of-the-m-bius-function-i/research.md
# Research: Autocorrelation of the Möbius Function in Short Intervals

## Theoretical Background

### Chowla’s Conjecture (k = 2)
For distinct positive integers \(h_1, h_2\) the conjecture predicts  
\[
\sum_{n\le x}\mu(n+h_1)\mu(n+h_2)=o(x).
\]  
Setting \(h_1=0,\;h_2=h\neq0\) yields the normalized autocorrelation  
\[
r_x(h)=\frac{1}{x-h}\sum_{n=1}^{x-h}\mu(n)\mu(n+h)
\]  
which is expected to converge to 0 as \(x\to\infty\).

### Random‑Sign Heuristic
The Möbius values are modeled as i.i.d. draws from \(\{-1,0,1\}\) with  
\[
\Pr[\mu=0]=1-\frac{6}{\pi^2},\qquad 
\Pr[\mu=\pm1]=\frac{3}{\pi^2},
\]  
the density \(6/\pi^2\) being the verified square‑free density (source: 1211.0189, https://arxiv.org/abs/1211.0189). **Under this heuristic the expected autocorrelation at any non‑zero lag is 0 and the variance is**  
\[
\operatorname{Var}(r_L(h))\approx\frac{\sigma^2}{L},\qquad 
\sigma^2=\frac{6}{\pi^2}\Bigl(1-\frac{6}{\pi^2}\Bigr)\approx0.2384.
\]

**Important Clarification:** The permutation‑null test implemented in this project evaluates the *random‑sign heuristic* described above, **not** Chowla’s conjecture directly. Chowla’s conjecture makes a statement about the true Möbius function; the random‑sign model is a probabilistic approximation that, if valid, is compatible with Chowla’s prediction of zero autocorrelation. Consequently, any claim that “the data support Chowla’s conjecture” is limited to “the data are consistent with the random‑sign heuristic, which is a necessary (but not sufficient) condition for Chowla’s prediction.” This distinction preserves construct validity.

## Dataset Strategy

| Component | Generation Method | Verification |
|-----------|-------------------|--------------|
| Möbius sequence \(\mu(n),\;1\le n\le10^7\) | Deterministic linear sieve (`code/sieve.py`). Stored as 2‑bit packed ternary array (`mobius_2bit.npy`) and as an int8 working copy (`mobius_array.npy`). | Unit tests on known values; SHA‑256 recorded in `manifest.sha256`. |
| Window sampling | 100 non‑overlapping windows per length \(L\in\{10^3,10^4,10^5\}\), seeded (`seed=20231017`). Start indices saved in `window_index.csv`. | Deterministic recreation; integration test checks exact row count (expected total). |
| Synthetic null windows (SC‑005) | Random‑sign windows with zero density \(6/\pi^2\) (verified fact). | Used only for calibration; not reported as a scientific result. |
| **Permutation null (FR‑003, VII)** | For each length \(L\) we select **20 representative windows** (the first 20 in `window_index.csv`). Within each selected window we generate **500 zero‑preserving sign permutations** and compute autocorrelations for **all lags** via a single FFT per permutation, thereby building a **per‑length null distribution**. This null is then applied to **all 300 windows** to obtain p‑values and confidence intervals. | The permutation engine is unit‑tested on a tiny window; the resulting null distribution matches a pre‑computed reference (Monte‑Carlo tolerance). |

No external data are required; all inputs are algorithmically generated, satisfying Constitution I.

## Statistical Methodology

1. **Autocorrelation Computation (FR‑002)**  
   For each window \(W\) of length \(L\) and each lag \(h\le\lfloor L/2\rfloor\):  
   \[
   r_W(h)=\frac{1}{L-h}\sum_{i=1}^{L-h}\mu(k+i)\mu(k+i+h).
   \]  
   Computed via a float64 FFT convolution for speed, then **cross‑validated** against a direct `int64` sum for a seeded random sample of ≥ 100 (window, lag) pairs per \(L\) (Constitution VI). The cross‑validation asserts relative error < 1e‑9; any violation aborts the pipeline.

2. **Permutation Null (FR‑003, VII)** – **as described in the Dataset Strategy**. By fixing zero positions and uniformly shuffling the signs of the non‑zero entries we generate a null distribution that reflects the independent‑sign heuristic while preserving the observed zero density. The null is **constructed from 20 windows per length**, each with **500 permutations**, yielding a p‑value resolution of 0.002 and avoiding a p‑value of exactly 0.

3. **Two‑sided p‑value & 95 % CI (FR‑004)**  
   \[
   p = \frac{\#\{|r_{\text{perm}}(h)|\ge|r_W(h)|\}+1}{501},
   \]  
   guaranteeing a minimum resolution of 0.002 and avoiding a p‑value of exactly 0. The confidence interval is the empirical 2.5th/97.5th percentiles of the null distribution.

4. **Multiple‑Comparison Correction (FR‑004)**  
   Across all \(\approx5.55\) M raw p‑values we apply Benjamini–Hochberg FDR (α = 0.05) using `statsmodels.stats.multitest.multipletests`. The resulting `adjusted_p_value` column drives the significance statements in the paper.

5. **Null Calibration (SC‑005)**  
   The permutation pipeline is validated on **simulated random‑sign windows** (zero density \(6/\pi^2\)). Because the p‑values lie on a discrete 1/501 lattice, we (a) perform a chi‑square goodness‑of‑fit test on equal‑probability bins and (b) a Kolmogorov–Smirnov test on a small subsample of independent windows (as stipulated in the spec). Both tests must yield \(p>0.05\). Results are stored in `calibration_test.json`.  

   The same two tests are applied to the **real** Möbius p‑values; the outcomes are recorded in `empirical_uniformity.json` and explicitly labeled as a research finding about the random‑sign heuristic (not a test validation).

6. **Zero‑Density Sensitivity (FR‑007)**  
   For each window we create four variants with zero counts altered by ±5 % and ±10 % (random insertions/deletions while preserving total length \(L\)). The permutation pipeline is rerun on each variant. A lag is flagged as `significant_change` if the raw p‑value < 0.05 status differs from the original window. The summary table (`sensitivity_summary.csv`) lists the affected lags and also indicates whether any of those lags were BH‑significant in the main analysis. Monte‑Carlo noise (±0.007 near the 0.05 threshold) is acknowledged; flips may arise from stochastic variation.

7. **Visualization (FR‑005, SC‑006)**  
   Heatmaps display autocorrelation values (color) for each lag (x‑axis) and each window (y‑axis). A black dashed contour at value = 0 implements the zero line. A twin panel below the heatmap shows the 2.5th/97.5th percentile bands (confidence envelope). Cells with `adjusted_p_value < 0.05` are overlaid with red circles. PNGs are saved at ≥ 1200 × 1200 px; automated tests verify resolution, presence of the zero contour, and CI band artists.

## Exact Claim‑to‑Artifact Links

All claims in the eventual manuscript will be linked to concrete rows or files generated by the pipeline (Constitution IV). The identifiers below are **filled in at runtime**; placeholders are shown for illustration.

| Claim | Supporting Artifact | Exact Identifier |
|-------|---------------------|------------------|
| Correct Möbius generation & 2‑bit packing | `data/raw/mobius_2bit.npy`, `data/raw/mobius_array.npy` | SHA‑256 hashes recorded in `manifest.sha256`. |
| FFT/int64 cross‑validation passes | `data/processed/pipeline_status.json` entry `autocorrelation_crosscheck` | `"status":"ok","n_pairs_checked":⟨n⟩,"max_relative_error":⟨err⟩`. |
| Demo autocorrelation value (US‑1 test) | `data/processed/demo_autocorr.csv` | Row `interval_start=1,interval_length=1000,lag=1,autocorrelation=-0.047047047047`. |
| Full raw autocorrelation table | `data/processed/autocorrelation_raw.csv` | Row count = Σₗ k·⌊L/2⌋, where k denotes a constant scaling factor.. |
| Permutation p‑values and 95 % CIs | `data/processed/autocorrelation_stats.csv` | Columns `p_value`, `ci_lower`, `ci_upper` for every `(interval_start,interval_length,lag)`. |
| BH‑adjusted p‑values | Same CSV | Column `adjusted_p_value`. |
| CI contains zero for ≥ ⟨fraction⟩ of lags (SC‑001) | Same CSV (aggregated) | Fraction reported in `research.md` after aggregation. |
| Null calibration passes (SC‑005) | `data/processed/calibration_test.json` | `chi2_pvalue>0.05` and `ks_pvalue>0.05`. |
| Empirical uniformity (Labeled Result) | `data/processed/empirical_uniformity.json` | `chi2_pvalue` and `ks_pvalue` values (may be < 0.05, indicating a deviation from the random‑sign heuristic). |
| Sensitivity analysis flagging | `data/processed/sensitivity_summary.csv` | Example row: `interval_start=⟨w⟩,interval_length=10000,adjustment="+[deferred]",significant_change=true,affected_lags="23,57",affected_lags_fdr_significant="23"`. |
| Heatmap figures | `outputs/figures/heatmap_L{L}.png` | PNG files with resolution ≥ 1200 × 1200 px, includes zero contour, CI bands, red significance markers. |
| Checksums for reproducibility | `data/checksums/manifest.sha256` | `<hash>  data/processed/autocorrelation_stats.csv`, etc. |
| Interpretation of results | Research narrative | Explicitly states that conclusions pertain to the random‑sign heuristic, not a direct proof of Chowla’s conjecture. |

## Limitations & Assumptions

* **Associational framing** – The study tests the random‑sign heuristic empirically; no causal claim about Chowla’s conjecture is made.  
* **Window independence** – Non‑overlapping windows are independent under the null; dependence under the true Möbius process is part of what we are measuring.  
* **Permutation resolution** – With 500 permutations the smallest non‑zero p‑value is 0.002; this limits detection of extremely rare events but satisfies the α = 0.05 requirement.  
* **Monte‑Carlo noise** – Near the 0.05 threshold, p‑values have an intrinsic ±0.007 variability; sensitivity flags may capture this stochastic fluctuation.  
* **Power** – For \(L=10^5\) the standard error under the random‑sign model is \(\sqrt{0.2384/L}\approx0.0015\); an effect size of 0.01 is detectable with ≥ 80 % power at α = 0.05 (normal approximation). Smaller L have proportionally larger SE, which is acknowledged in the discussion.  

---


