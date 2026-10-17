# Research: Autocorrelation of the Möbius Function in Short Intervals

## Theoretical Background

### Chowla's Conjecture (k = 2)
For distinct positive integers h₁, h₂, Chowla predicts Σ_{n≤x} μ(n+h₁)μ(n+h₂) = o(x). With h₁ = 0, h₂ = h ≠ 0 this yields the normalized autocorrelation r_x(h) = (1/(x−h)) Σ_{n≤x−h} μ(n)μ(n+h), expected to vanish as x → ∞.

### Random-Sign Heuristic
Treating μ(n) as i.i.d. draws from {−1, 0, 1} with Pr[μ(n)=0] = 1 − 6/π² and Pr[μ(n)=±1] = 3/π² — the density of square-free numbers being proportional to the reciprocal of π² (source:, https://arxiv.org/abs/1211.0189) — the expected autocorrelation at any non-zero lag is 0. The permutation test operationalizes exactly this null: zero positions fixed, non-zero signs uniformly shuffled.

### Theoretical Variance Baseline
Under the random-sign model, Var(r_L(h)) ≈ σ²/L with **σ² = (6/π²)(1 − 6/π²) ≈ 0.2384** (6/π² ≈ 0.6079; source: 1211.0189, https://arxiv.org/abs/1211.0189). This value is recorded per row as `theoretical_variance` and serves as a sanity check on the permutation envelope width (it is NOT used for inference — Principle VII requires permutation-derived p-values/CIs). Note: the spec's power assumption quotes SE = 0.0032 at L = 10⁵, which corresponds to the more conservative baseline √(1/L); under the σ²/L model the SE is expected to be small. Both are recorded; neither is used for inference.

## Dataset Strategy

| Component | Generation Method | Verification |
|-----------|-------------------|--------------|
| Möbius sequence μ(n), 1 ≤ n ≤ 10⁷ | Deterministic linear sieve (`code/sieve.py`), stored as a 2-bit packed ternary array (`mobius_2bit.npy`, FR-001) with an int8 working copy. | Unit tests against known values (μ(1)=1, μ(2)=−1, μ(4)=0, μ(30)=−1) and exact pack/unpack round-trip. |
| Window sample | 100 non-overlapping windows per L ∈ {10³, 10⁴, 10⁵}, seed = 20231017; start indices written to `data/processed/window_index.csv`. | Deterministic regeneration; CSV cross-check. |
| Synthetic null windows (calibration only) | Random-sign windows with zero density 6/π², seeded. | Used only for SC-005 test calibration; never reported as a result about μ. |

No external dataset is required — the input is algorithmically generated and exactly reproducible (Constitution I). No GPU methods are used; everything runs CPU-only on the free-tier runner.

## Statistical Methodology

1. **Autocorrelation (FR-002)**: r_{k,L}(h) = (1/(L−h)) Σ μ(k+i)μ(k+i+h), h = 1…⌊L/2⌋, computed via float64 FFT convolution and **cross-validated exactly**: for a seeded random sample of ≥ 100 (window, lag) pairs per L, the integer sum is recomputed by direct `int64` summation and asserted to agree within float64 round-off (Principle VI).
2. **Permutation null (FR-003, FR-004, Principle VII)**: exactly **[deferred]** zero-preserving random-sign permutations per window (per-window deterministic seeds); two-sided p-value p = (#{|r_perm| ≥ |r_obs|} + 1)/1001, giving minimum resolution ≈ 0.001; 95 % CI from the 2.5th/97.5th null percentiles. Edge reporting: p < 0.001 / p > 0.999 instead of exact 0/1 (spec Edge Cases).
3. **Multiple comparisons (FR-004)**: Benjamini–Hochberg FDR at α = 0.05 across all ≈ 5.56 M raw p-values; BH-adjusted p-values govern significance claims in the main analysis.
4. **Null calibration (SC-005)**: the permutation test is validated on **simulated random-sign windows** (zero density 6/π², seeded), 200 synthetic windows per L. Because 1,000-permutation p-values lie on a discrete 1/1001 lattice (≈ 501 attainable two-sided values), a KS test against continuous Uniform[0,1] is invalid at large n; calibration uses (a) chi-square goodness-of-fit on binned p-value counts and (b) the spec's "approximate KS test" on a small subsample of independent windows. Results → `calibration_test.json`. Separately, the same tests on the REAL μ p-values are reported in `empirical_uniformity.json` as a labeled research result about the random-sign heuristic — a rejection there indicates the null may be false for μ, not that the test is broken.
5. **Sensitivity (FR-007)**: zero count adjusted by ±5 % and ±10 % via random insertion/deletion of zeros (length L preserved), non-zero signs re-shuffled, 1,000 permutations per adjustment, batched FFT. The significance criterion is the **raw p < 0.05 threshold, deliberately, because FR-007 specifies it verbatim**; this is intentionally more sensitive than the FDR-governed main analysis, so `significant_change` may flag lags never significant after BH adjustment — the affected-lags table reports both raw and FDR status. **MC-noise limitation**: with 1,000 permutations, p-values near 0.05 carry Monte Carlo noise ≈ ±0.007, so borderline flips can occur by resampling chance; the flag partly measures resampling noise in addition to zero-density robustness.
6. **Power**: under the σ²/L variance model, SE(r) ≈ √(0.2384/L) ≈ 0.0015 at L = 10⁵; the spec's assumption quotes the conservative SE = √(1/L) = 0.0032. Under either baseline, an effect of 0.01 is detectable with ≥ 80 % power at α = 0.05 (normal approximation). This is an associational study of empirical autocorrelation structure; it provides evidence about the random-sign heuristic, not a proof of Chowla's conjecture.

## Exact Claim-to-Artifact Links

> **T016 fix**: identifiers below are **concrete**, read programmatically from the CSV after the run. Placeholders in ⟨⟩ are filled by `code/main.py` Phase 8.3 from the actual data — never hand-typed (Constitution IV). The window start indices cited are the deterministic first/three windows from `window_index.csv`.

| Claim | Supporting Artifact | Exact Identifier |
|-------|---------------------|------------------|
| Möbius generation correctness (incl. 2-bit packing round-trip) | `data/raw/mobius_2bit.npy` + `data/raw/mobius_array.npy` (SHA-256 ⟨hash₂bit⟩, ⟨hash_int8⟩) | Verified by `tests/unit/test_sieve.py`. |
| FFT/int64 cross-validation | `data/processed/pipeline_status.json` | Stage `autocorrelation_crosscheck`: `status="ok"`, `n_pairs_checked=⟨n⟩`, `max_relative_error=⟨err⟩`. |
| Observed autocorrelation, first L=10³ window, lag 1 | `data/processed/autocorrelation_stats.csv` | Row `interval_start=⟨w₁⟩, interval_length=1000, lag=1`, column `autocorrelation`. |
| Permutation p-value for that row | Same CSV | Same row, column `p_value` (min resolution 1/1001). |
| 95 % CI for that row | Same CSV | Same row, columns `ci_lower`, `ci_upper`. |
| BH-adjusted p-value | Same CSV | Same row, column `adjusted_p_value`. |
| SC-001 coverage (CI contains 0) | Same CSV | Fraction of rows per L with `ci_lower ≤ 0 ≤ ci_upper`: ⟨fraction₁₀₀₀⟩, ⟨fraction₁₀₀₀₀⟩, ⟨fraction₁₀₀₀₀₀⟩. |
| SC-005 null calibration | `data/processed/calibration_test.json` | `chi2_statistic=⟨v⟩, chi2_pvalue=⟨v⟩, ks_statistic=⟨v⟩, ks_pvalue=⟨v⟩, n_simulated_windows=⟨n⟩`. |
| Empirical uniformity (real data, labeled as result) | `data/processed/empirical_uniformity.json` | `chi2_pvalue=⟨v⟩, ks_pvalue=⟨v⟩`. |
| Sensitivity — stable example | `data/processed/autocorrelation_stats.csv` + `sensitivity_summary.csv` | Window `interval_start=⟨w_stable⟩, interval_length=⟨L⟩`: `sensitivity_flag="stable"`; summary row with `significant_change=false`. |
| Sensitivity — every flagged window | `data/processed/sensitivity_summary.csv` | Complete enumerated list of rows with `significant_change=true`: ⟨enumerated (interval_start, interval_length, adjustment, affected_lags, affected_lags_fdr_significant) tuples⟩; if none, the file contains zero such rows and this is stated. |
| Heatmaps | `outputs/figures/heatmap_L1000.png` (Fig 1), `heatmap_L10000.png` (Fig 2), `heatmap_L100000.png` (Fig 3) | Resolution ≥ 1200 × 1200 px; zero contour at autocorrelation = 0; CI band = 2.5th/97.5th null percentiles. |
| Theoretical variance | Same CSV | Column `theoretical_variance` = σ²/L, σ² = (6/π²)(1 − 6/π²) ≈ 0.2384 (density 6/π², source: 1211.0189, https://arxiv.org/abs/1211.0189). |

## Limitations & Assumptions
- **Associational framing**: results test the random-sign heuristic empirically; no causal or proof-theoretic claim is made.
- **Window count**: 100 non-overlapping windows per L (spec FR-002); windows are disjoint so per-window statistics are independent under the null.
- **Permutation count**: exactly 1,000 (FR-003, Constitution VII); p-value resolution ≈ 0.001, sufficient for α = 0.05 testing. The discreteness of the p-value lattice motivates the chi-square/subsample-KS calibration design (SC-005).
- **Calibration vs. result**: SC-005 uniformity is assessed on simulated random-sign windows (test calibration); the empirical uniformity of real-data p-values is reported separately and labeled as a research result, not as test validation.
- **Multiple comparisons**: with ≈ 5.56 M tests, BH FDR (not per-test α) governs main-analysis significance claims; SC-001/SC-002 report both raw and adjusted views. The sensitivity analysis deliberately uses the raw p < 0.05 threshold per FR-007's literal text; affected lags are reported with both raw and FDR status so raw-threshold flips are not mistaken for FDR-significant deviations. MC noise (±0.007 near p = 0.05 with 1,000 permutations) means borderline sensitivity flips can arise from resampling chance — an acknowledged limitation (spec kickback suggested if a noise-margin criterion is desired).
- **Power**: SE ≈ 0.0015 (σ²/L model) to 0.0032 (conservative √(1/L)) at L = 10⁵; smaller L have proportionally lower power — an acknowledged limitation for L = 10³ (SE ≈ 0.011–0.025 depending on baseline).
- **Sensitivity runtime**: the sensitivity stage carries a documented 4 h degradation guard that may restrict it to L ∈ {10³, 10⁴} on a slow runner; this is an explicit, logged degradation of FR-007 scope recorded in `pipeline_status.json` and reported here — the full-scope run over all three L remains the deliverable whenever runtime permits, and the 1,000-permutation count is never reduced.