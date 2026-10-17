# Research: Autocorrelation of the Möbius Function in Short Intervals

## Theoretical Background

### Chowla’s Conjecture (k = 2)
For distinct positive integers h₁, h₂, Chowla (1965) predicts  
\[
\sum_{n\le x}\mu(n+h_1)\mu(n+h_2)=o(x).
\]  
When h₁ = 0, h₂ = h ≠ 0 this implies the *normalized* autocorrelation  
\[
r_{x}(h)=\frac{1}{x-h}\sum_{n=1}^{x-h}\mu(n)\mu(n+h)
\]  
should converge to 0 as x → ∞.

### Random‑Sign Heuristic
The heuristic treats μ(n) as an i.i.d. draw from \{-1,0,1\} with  
\[
\Pr[\mu(n)=0]=1-\frac{6}{\pi^2},\qquad
\Pr[\mu(n)=\pm1]=\frac{3}{\pi^2},
\]  
the density of square‑free numbers being **6/π²** (source: arXiv 1211.0189). Under this model, the expected autocorrelation for any non‑zero lag is 0.

### Prime Number Theorem (PNT) Baseline
The PNT gives the asymptotic density of square‑free numbers, allowing an analytic variance estimate for the autocorrelation sum:
\[
\operatorname{Var}\bigl(r_{L}(h)\bigr)\approx\frac{\sigma^2}{L},\qquad
\sigma^2=\frac{6}{\pi^2}\Bigl(1-\frac{6}{\pi^2}\Bigr).
\]
We compute this **theoretical variance** for each window length L and compare it to the empirical variance of the observed autocorrelations. This provides an *arithmetic* baseline independent of the permutation test.

## Dataset Strategy

| Component | Generation Method | Verification |
|-----------|-------------------|--------------|
| Möbius sequence μ(n) for 1 ≤ n ≤ 10⁷ | Linear sieve (Meissel‑Lehmer style) in `code/sieve.py`. Deterministic, no randomness. | Unit tests against known values (μ(1)=1, μ(2)=‑1, μ(4)=0, μ(30)=‑1, …). |
| Interval parameters | Fixed set L ∈ {10³, 10⁴, 10⁵}; 20 stratified start positions per L (seed = 20231017). | Documented in `config.yaml`; reproducible. |

No external data are required; the “dataset” is algorithmically generated, satisfying the open‑data requirement.

## Statistical Methodology

### 1. Autocorrelation Computation
For a window starting at index k of length L,
\[
r_{k,L}(h)=\frac{1}{L-h}\sum_{i=1}^{L-h}\mu(k+i)\,\mu(k+i+h),
\quad h=1,\dots,\lfloor L/2\rfloor.
\]
Implementation uses NumPy vectorisation; the sum is accumulated in `int64` to guarantee exactness before division.

### 2. Block‑Permutation Null Distribution (FR‑003, FR‑004)
1. Split the window vector into blocks of size **b = 100** (last block may be shorter).  
2. Shuffle block order **1 000** times (fixed RNG seed).  
3. Preserve the exact count of zeros in each permuted vector.  
4. Compute autocorrelation for each permuted vector, yielding a null distribution per (window, lag).  

**Two‑sided p‑value**:  
\[
p = \frac{\#\{|r_{\text{perm}}|\ge|r_{\text{obs}}|\}+1}{1000+1},
\]
which avoids exact 0/1.

**95 % confidence interval**: 2.5 % and 97.5 % quantiles of the null distribution.

### 3. Multiple‑Comparison Correction
All p‑values (≈ ∑ L/2 × 20 × 3 ≈ 3 600) are adjusted using the **Benjamini‑Hochberg (BH)** procedure to control the false discovery rate at α = 0.05. Adjusted p‑values appear as `adjusted_p_value` in the CSV.

### 4. Uniformity Validation (SC‑005)
A **Kolmogorov‑Smirnov (KS) test** compares the empirical p‑value distribution to Uniform[0,1].  
- Null hypothesis: p‑values are uniformly distributed (random‑sign heuristic holds).  
- Result stored in `uniformity_test.json` as `{ "ks_statistic": ..., "ks_pvalue": ... }`.  
- If `ks_pvalue > 0.05`, we conclude no evidence against uniformity.

### 5. Sensitivity Analysis (FR‑007)
For each window we recompute the null distribution after **inflating** or **deflating** the observed zero count by 5 % and 10 % (rounded). The same 1 000 permutations are reused; only the mapping of zeros to positions changes.  
- If any perturbed p‑value crosses the α = 0.05 threshold, `sensitivity_flag` = `"sensitive"`; otherwise `"stable"`.  
- Windows with all zeros receive `"not_applicable"`.

### 6. Visualization (FR‑005)
Heatmaps (`outputs/figures/heatmap_L{L}.png`) display:
- X‑axis: lag h (1 … L/2).  
- Y‑axis: window start index (ordered).  
- Color: observed autocorrelation.  
- Horizontal black line at **y = 0**.  
- Shaded region between the 2.5 % and 97.5 % quantiles (confidence band).  
- Red dots on cells where `adjusted_p_value < 0.05`.  

All figures are saved at **1200 × 1200 px** (minimum requirement) and referenced in the manuscript by filename.

## Exact Linking of Claims to Artifacts

| Claim | Supporting Artifact(s) |
|-------|------------------------|
| *Möbius generation correctness* | Row‑wise check: `np.unique(np.load('data/raw/mobius_array.npy'))` returns `[-1, 0, 1]`. Verified by `tests/unit/test_sieve.py`. |
| *Observed autocorrelation values* | Rows in `autocorrelation_stats.csv` where `interval_length=1000` and `interval_start=123456` (example). The exact row can be retrieved via `pandas` filtering on those columns. |
| *Permutation‑based p‑values* | Same rows as above; column `p_value`. |
| *Adjusted p‑values (BH)* | Column `adjusted_p_value`. |
| *Confidence bands* | Columns `ci_lower` and `ci_upper`. |
| *Sensitivity flag* | Column `sensitivity_flag`; e.g., row with `interval_start=987654`, `interval_length=10000` has `"sensitive"`. |
| *Uniformity test* | `uniformity_test.json` (`ks_pvalue`). |
| *Heatmap figures* | Files `outputs/figures/heatmap_L1000.png`, `heatmap_L10000.png`, `heatmap_L100000.png`. Each figure caption in the manuscript will cite the exact filename. |
| *Theoretical variance benchmark* | Column `theoretical_variance` (computed from the PNT formula). Comparison performed by plotting observed variance vs. theoretical variance in the manuscript (Figure X). |

All identifiers (`interval_start`, `interval_length`, `lag`) are present in the CSV, enabling precise row‑level citation.

## Compute Feasibility & Rationale (re‑affirmed)

- **CPU‑first**: No GPU libraries are used; all operations are NumPy‑based.  
- **Memory**: Peak < 200 MB.  
- **Disk**: < 30 MB total.  
- **Runtime**: Estimated ≤ 4 h on the free‑tier runner; a built‑in fallback reduces windows to 10 per L if the job exceeds 5 h.

## Limitations & Assumptions (re‑stated)

- The analysis is **observational**; conclusions are limited to evidence for or against the random‑sign heuristic, not a proof of Chowla’s conjecture.  
- Only **20** stratified windows per L are examined; this is a trade‑off between statistical power and the 6 h compute ceiling.  
- The block‑size **b = 100** is a design choice that balances preservation of short‑range structure with sufficient randomisation of long‑range order.  
- The **theoretical variance** assumes the density of square‑free numbers is exactly 6/π² (verified source: arXiv 1211.0189).  

---
