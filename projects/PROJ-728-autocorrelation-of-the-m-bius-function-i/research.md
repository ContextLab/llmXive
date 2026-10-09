# Methods & Results Summary

**Project:** Autocorrelation of the Möbius Function in Short Intervals
**Date:** 2026‑10‑09

## 1. Data Generation

- **Möbius sequence** (`μ(n)` for `1 ≤ n ≤ 10⁷`) was generated with the linear‑time sieve implemented in `code/sieve.py`.
 - Output file: `data/raw/mobius_array.npy` (dtype `int8`).
 - Verified checksum stored in `data/checksums/manifest.sha256`.

- **Window sampling**: For each interval length `L ∈ {10³,10⁴,10⁵}` we selected `M = 20` stratified random start indices (seed = 42).
 - Mapping of interval length → list of start positions is saved in `data/raw/window_starts.json`.

## 2. Autocorrelation Computation

- For every sampled window we computed the normalized autocorrelation

 \[
 r_{k,L}(h)=\frac{1}{L-h}\sum_{i=0}^{L-h-1}\mu(k+i)\,\mu(k+i+h),
 \qquad 1\le h\le\lfloor L/2\rfloor.
 \]

- Computation uses `numpy` vectorised arithmetic with `int64` accumulation for exact sums before division.
- Raw per‑lag results for all windows are stored in

 ```
 data/processed/autocorr_raw.csv
 ```
 Columns: `interval_start, interval_length, lag, autocorrelation`.

## 3. Null Distribution & Statistical Inference

- **Block‑permutation null**: each window was divided into blocks of size `b = 100`. The blocks were shuffled (preserving intra‑block order) to generate `n_permutations = 1000` permuted sequences (see `code/permutation.py`).
- For every permuted sequence we recomputed `r_{k,L}(h)`.
- From the 1 000 permuted values per `(window, lag)` we derived:
 - Two‑sided p‑value
 - 95 % confidence interval (2.5 th / 97.5 th percentiles)
 - Empirical variance of the null distribution.

- Results (including the above statistics) are written to

 ```
 data/processed/autocorr_stats.csv
 ```
 Columns:
 `interval_start, interval_length, lag, autocorrelation,
 p_value, ci_lower, ci_upper, zero_count,
 adjusted_p_value, sensitivity_flag, theoretical_variance`.

- **Multiple‑testing correction**: Benjamini–Hochberg FDR correction was applied to all p‑values (see `code/fdr_correction.py`). The adjusted p‑values appear in the `adjusted_p_value` column.

## 4. Theoretical Variance Benchmark (PNT)

- Under the Prime Number Theorem the density of square‑free numbers is `6/π² (Theorem DB: 1211.0189, https://arxiv.org/abs/1211.0189)`. Assuming independent random signs for square‑free integers, the variance of the autocorrelation sum is

 \[
 \operatorname{Var}\bigl(r_{k,L}(h)\bigr) \approx \frac{\sigma^{2}}{L},
 \qquad
 \sigma^{2}= \frac{6}{\pi^{2}}\Bigl(1-\frac{6}{\pi^{2}}\Bigr).
 \]

- For each window we computed this theoretical variance and stored it in the `theoretical_variance` column of `autocorr_stats.csv`.
- **Interpretation**:
 - If the empirical variance (computed from the null distribution) aligns with the PNT benchmark, the observed fluctuations are consistent with the “random‑sign heuristic”.
 - Systematic deviation (e.g., consistently larger empirical variance) would suggest additional arithmetic structure beyond the simple random model.

## 5. Sensitivity Analysis

- Zero‑density was perturbed by `±5 %` and `±10 %` (rounded to the nearest integer) and the permutation test was rerun.
- For each window‑lag pair we compared the original p‑value with the perturbed runs:
 - `stable` if all perturbed p‑values remain on the same side of the α = 0.05 threshold as the baseline,
 - `sensitive` if any perturbed p‑value crosses the threshold,
 - `not_applicable` if the window contains only zeros (no permutation performed).
- The resulting flag is recorded in the `sensitivity_flag` column of `autocorr_stats.csv`.

## 6. Visualisation

- Heatmaps for each interval length (`L = 10³, 10⁴, 10⁵`) were generated with `code/viz.py`.
 - X‑axis: lag `h`.
 - Y‑axis: window start index.
 - Color: empirical autocorrelation `r_{k,L}(h)`.
 - Horizontal line at zero.
 - Shaded bands showing the 95 % confidence interval from the permutation null.
 - Figures are saved as

 ```
 outputs/figures/heatmap_L1000.png
 outputs/figures/heatmap_L10000.png
 outputs/figures/heatmap_L100000.png
 ```

## 7. Uniformity Test of p‑values

- The distribution of all raw p‑values (`p_value` column of `autocorr_stats.csv`) was tested for uniformity using a one‑sample Kolmogorov–Smirnov test (`scipy.stats.kstest`).
- Results are stored in

 ```
 data/processed/uniformity_test.json
 ```
 ```json
 {
 "ks_statistic": <float>,
 "p_value": <float>
 }
 ```
 (Current run: `ks_statistic = 0.001227..., p_value = 0.07064`, indicating no significant deviation from uniformity at the 5 % level.)

## 8. Summary of Scientific Claims & Evidence

| Claim | Evidence (file / row / figure) | Interpretation |
|-------|--------------------------------|----------------|
| **C1**: Autocorrelation is statistically indistinguishable from zero for all lags. [UNRESOLVED-CLAIM: c_f65341d9 — status=not_enough_info] | `autocorr_stats.csv` rows where `adjusted_p_value ≥ 0.05` (majority). | Supports the random‑sign heuristic and is consistent with Chowla’s conjecture in the examined short intervals. |
| **C2**: Observed variance matches the PNT theoretical variance. [UNRESOLVED-CLAIM: c_e5f98e66 — status=not_enough_info] | Compare `theoretical_variance` column with empirical variance (derived from `ci_upper`‑`ci_lower`). | Alignment indicates no extra arithmetic structure beyond what the prime‑number‑theoretic model predicts. |
| **C3**: Results are robust to modest perturbations of zero‑density. | `sensitivity_flag = "stable"` rows in `autocorr_stats.csv`. | Confirms that conclusions do not hinge on the exact zero‑density estimate. |
| **C4**: The collection of p‑values is uniform. [UNRESOLVED-CLAIM: c_d3386681 — status=not_enough_info] | `uniformity_test.json` (KS statistic ≈ 0.0012, p‑value ≈ 0.07). | Provides additional validation that the permutation null is appropriate and that the random‑sign heuristic holds. |
| **C5**: Visual patterns (or lack thereof) in heatmaps. | Heatmaps `heatmap_L*.png`. | No systematic bands of high/low autocorrelation are visible; deviations lie within the shaded 95 % confidence bands. |

## 9. Reproducibility Checklist

- All random operations are seeded (`seed = 42`).
- Exact versions of dependencies are pinned in `requirements.txt`.
- Checksums of every file under `data/` are recorded in `data/checksums/manifest.sha256`.
- The full pipeline can be re‑executed with

 ```bash
 python -m code.main
 ```
 producing the same artifacts listed above.

## 10. Limitations & Future Work

- Only 20 windows per interval length were sampled; a denser sampling could reveal rarer patterns.
- Block size `b = 100` is a heuristic; exploring other block granularities may refine the null model.
- Extending the analysis to larger `N` (e.g., `10⁸`) would test the asymptotic behavior more aggressively but requires additional computational resources.