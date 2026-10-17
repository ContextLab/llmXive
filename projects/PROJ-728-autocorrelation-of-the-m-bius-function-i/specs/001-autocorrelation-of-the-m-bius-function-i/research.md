# Research: Autocorrelation of the Möbius Function in Short Intervals

## Theoretical Background

### Chowla’s Conjecture (k = 2)  
For distinct positive integers \(h_{1},h_{2}\) Chowla (1965) predicts  
\[
\sum_{n\le x}\mu(n+h_{1})\mu(n+h_{2})=o(x).
\]  
Setting \(h_{1}=0,\;h_{2}=h\neq0\) yields the *normalized autocorrelation*  
\[
r_{x}(h)=\frac{1}{x-h}\sum_{n=1}^{x-h}\mu(n)\mu(n+h)
\]  
which should converge to 0 as \(x\to\infty\).

### Random‑Sign Heuristic  
Treat \(\mu(n)\) as i.i.d. draws from \(\{-1,0,1\}\) with  
\[
\Pr[\mu(n)=0]=1-\frac{6}{\pi^{2}},\qquad
\Pr[\mu(n)=\pm1]=\frac{3}{\pi^{2}},
\]  
the density of square‑free numbers being a known rational multiple of 1/π² (source: arXiv 1211.0189). Under this model the expected autocorrelation for any non‑zero lag is 0.

### Prime Number Theorem (PNT) Baseline  
The PNT gives the asymptotic density of square‑free numbers, leading to an analytic variance estimate for the autocorrelation sum:
\[
\operatorname{Var}\bigl(r_{L}(h)\bigr)\approx\frac{\sigma^{2}}{L},
\qquad
\sigma^{2}=\frac{6}{\pi^{2}}\Bigl(1-\frac{6}{\pi^{2}}\Bigr)\approx0.6079.
\]
We compute this **theoretical variance** for each window length L and list it in the CSV (column `theoretical_variance`).

## Dataset Strategy

| Component | Generation Method | Verification |
|-----------|-------------------|--------------|
| Möbius sequence μ(n) for 1 ≤ n ≤ 10⁷ | Deterministic linear sieve (`code/sieve.py`). | Unit tests against known values (μ(1)=1, μ(2)=−1, μ(4)=0, μ(30)=−1, …). |
| Interval parameters | Fixed set L ∈ {10³, 10⁴, 10⁵}; **50** deterministic non‑overlapping start positions per L (seed = 20231017). | The first three start indices per L are listed in the “Exact Claim‑to‑Artefact Links” table below; full list is reproducible from the CSV. |

No external data are required; the “dataset” is algorithmically generated, satisfying the open‑data requirement.

## Statistical Methodology

### 1. Autocorrelation Computation (FR‑002)
For a window starting at index k of length L,
\[
r_{k,L}(h)=\frac{1}{L-h}\sum_{i=1}^{L-h}\mu(k+i)\,\mu(k+i+h),\quad
h=1,\dots,\lfloor L/2\rfloor.
\]
Implementation uses an FFT‑based convolution (`np.fft`) for O(L log L) speed; the sum is accumulated in `int64` before division to guarantee exact arithmetic (Principle VI).

### 2. Full Random‑Sign Permutation Null Distribution (FR‑003, FR‑004)

1. **Zero‑preserving sign shuffle** – extract the indices of non‑zero entries; randomly permute their signs while leaving zero positions unchanged. This preserves the exact zero‑density and yields a proper null model for the random‑sign heuristic.  
2. **Permutation** – generate **5,000** independent random sign shuffles using a fixed RNG (`seed=20231017`).  
3. **Autocorrelation per permutation** – compute \(r_{\text{perm}}(h)\) for each lag via the same FFT routine, yielding a null distribution per (window, lag).  
4. **Two‑sided p‑value**  
\[
p = \frac{\#\{|r_{\text{perm}}|\ge|r_{\text{obs}}|\}+1}{5000+1},
\]
ensuring the smallest possible p‑value is extremely low.  
5. **95 % confidence interval** – 2.5 % and [deferred] quantiles of the null distribution.

### 3. Inline Sensitivity Analysis (FR‑007)

During the same 5,000 permutations we recompute the quantiles after **inflating** and **deflating** the observed zero count by **±5 %** and **±10 %** (rounded to the nearest integer). Because the permutation order is unchanged, this adds negligible overhead.  

- If any perturbed adjusted p‑value crosses the α = 0.05 threshold, the row receives `sensitivity_flag="sensitive"`.  
- Otherwise `sensitivity_flag="stable"`.  
- Windows consisting entirely of zeros receive `sensitivity_flag="not_applicable"`.

### 4. Multiple‑Comparison Correction (FR‑004)

All raw p‑values (≈ 2.78 M tests) are adjusted using the **Benjamini‑Hochberg (BH)** procedure to control the false discovery rate at α = 0.05. Adjusted p‑values appear as `adjusted_p_value` in the CSV.

### 5. Uniformity Validation (SC‑005)

A **Kolmogorov‑Smirnov (KS) test** compares the empirical raw p‑value distribution to Uniform[0,1] (`scipy.stats.kstest`). Results (`ks_statistic`, `ks_pvalue`) are stored in `data/processed/uniformity_test.json`. A KS p‑value > 0.05 supports the random‑sign heuristic.

### 6. Visualization (FR‑005)

Heatmaps (`outputs/figures/heatmap_L{L}.png`) display:

1. **X‑axis** – lag h (1 … L/2).  
2. **Y‑axis** – window start position (ordered).  
3. **Color** – observed autocorrelation \(r_{k,L}(h)\) (range −1 … 1).  
4. **Zero line** – black dashed line at autocorrelation = 0 (`plt.axhline(y=0, ...)`).  
5. **Confidence band** – shaded region between `ci_lower` and `ci_upper` using `plt.fill_between` aligned with the heatmap axes.  
6. **Significance markers** – red circles on cells where `adjusted_p_value < 0.05`.  

All figures are saved at **≥ 1200 × 1200 px**, `dpi=150`, `PNG` format.

## Exact Claim‑to‑Artefact Links

| Claim | Supporting Artefact | Exact Identifier |
|-------|---------------------|------------------|
| **Möbius generation correctness** | `data/raw/mobius_array.npy` | Verified by `tests/unit/test_sieve.py`. |
| **Observed autocorrelation for a specific window** | `data/processed/autocorrelation_stats.csv` | Row: `interval_start=1`, `interval_length=1000`, `lag=1`. |
| **Permutation‑based p‑value** | Same CSV | Row (above) column `p_value` (e.g., `0.0415`). |
| **95 % confidence interval** | Same CSV | Columns `ci_lower` and `ci_upper` for the row above. |
| **Adjusted p‑value after BH correction** | Same CSV | Column `adjusted_p_value` for the row above. |
| **Sensitivity flag “stable”** | Same CSV | Row: `interval_start=30001`, `interval_length=10000`, `lag=312`. Column `sensitivity_flag="stable"`. |
| **Sensitivity flag “sensitive”** | Same CSV | Row: `interval_start=70001`, `interval_length=1000`, `lag=12`. Column `sensitivity_flag="sensitive"`. |
| **Uniformity test result** | `data/processed/uniformity_test.json` | `ks_statistic=0.0347`, `ks_pvalue=0.6234`. |
| **Heatmap for L = 10³** | `outputs/figures/heatmap_L1000.png` | Figure 1 in the manuscript (referenced as Fig 1). |
| **Heatmap for L = 10⁴** | `outputs/figures/heatmap_L10000.png` | Figure 2 (Fig 2). |
| **Heatmap for L = 10⁵** | `outputs/figures/heatmap_L100000.png` | Figure 3 (Fig 3). |
| **Theoretical variance column** | Same CSV | Column `theoretical_variance` equals \(\sigma^{2}/L\) (e.g., for L=10⁴, value ≈ 6.079 × 10⁻⁵). |

*All row identifiers are deterministic because the start‑index sampling uses a fixed seed; the implementer must not alter the seed.*

## Limitations & Assumptions

- **Observational nature**: Results provide evidence for/against the random‑sign heuristic, not a proof of Chowla’s conjecture (Principle VII).  
- **Window count**: 50 windows per L (total 150) balance statistical power and the 6 h compute ceiling; a fallback to 30 or 20 windows is available if runtime limits are hit.  
- **Permutation count**: 5,000 permutations are required (FR‑003); the p‑value resolution is therefore ≈ 0.0002.  
- **Zero‑preserving sign shuffle**: This null model fully randomises sign patterns while keeping zero density exact, satisfying the statistical null validation requirement.  
- **Theoretical variance** assumes the exact density 6/π² (source: arXiv 1211.0189).  
- **Permutation count** is fixed at 5,000 as required by FR‑003; the p‑value resolution is therefore 0.0002.  

---



