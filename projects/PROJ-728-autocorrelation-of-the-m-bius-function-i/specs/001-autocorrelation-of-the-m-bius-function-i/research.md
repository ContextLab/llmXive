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
| **Permutation null (FR‑003, VII)** | For each length \(L\) we select **20 representative windows** (the first 20 in `window_index.csv`). Within each selected window we generate **Numerous zero‑preserving sign permutations** and compute autocorrelations for **all lags** via a single FFT per permutation, thereby building a **per‑length null distribution**. This null is then applied to **all 300 windows** to obtain p‑values and confidence intervals. | The permutation engine is unit‑tested on a tiny window; the resulting null distribution matches a pre‑computed reference (Monte‑Carlo tolerance). |

No external data are required; all inputs are algorithmically generated, satisfying Constitution I.

## Statistical Methodology

1. **Autocorrelation Computation (FR‑002)**  
   For each window \(W\) of length \(L\) and each lag \(h\le\lfloor L/2\rfloor\):  
   \[
   r_W(h)=\frac{1}{L-h}\sum_{i=1}^{L-h}\mu(k+i)\mu(k+i+h).
   \]  
   Computed via a float64 FFT convolution for speed, then **cross‑validated** against a direct `int64` sum for a seeded random sample of ≥ 100 (window, lag) pairs per \(L\) (Constitution VI). The cross‑validation asserts relative error < 1e‑9; any violation aborts the pipeline.

2. **Permutation Null (FR‑003, VII)** – **as described in the Dataset Strategy**. By fixing zero positions and uniformly shuffling the signs of the non‑zero entries we generate a null distribution that reflects the independent‑sign heuristic while preserving the observed zero density. The null is **constructed from 20 windows per length**, each with **500 permutations**, yielding a p‑value resolution at a high level of precision and avoiding a p‑value of exactly 0.

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
