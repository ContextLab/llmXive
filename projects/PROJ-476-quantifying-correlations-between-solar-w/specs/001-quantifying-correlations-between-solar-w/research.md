# Research: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Summary of Scientific Question

How do variations in solar‑wind composition (proton density, proton temperature, helium abundance) relate associatively to geomagnetic disturbance intensity as measured by Kp and Dst, **during geomagnetic storm intervals (Dst < ‑50 nT)**, at response lags of 0–6 hours, over the 1998–2020 interval? The study computes lagged Pearson and Spearman correlations on the **storm‑filtered dataset**, with Pearson p‑values adjusted for autocorrelation via the Pyper & Peterman effective sample size and **Spearman p‑values obtained from a permutation test** that preserves temporal dependence. Raw p‑values are then subjected to a **plain Bonferroni** correction over the full 30‑test family, validated on a held‑out 2018–2020 period.

## Dataset Strategy

**Verified‑source status (mandatory disclosure)**: the "# Verified datasets" block supplied for this project contains **no URLs** for ACE solar‑wind or geomagnetic‑index data. Consequently the pipeline cites **no external URLs**. The required datasets are accessed through well‑known programmatic channels:

| Dataset | Required variables | Canonical source (named, URL not verified here) | Access method |
|:---|:---|:---|:---|
| ACE SWEPAM Level 2 | `N_p` (cm⁻³), `T_p` (K) | NASA CDAWeb – dataset **AC_H0_SWE** | `cdasws` Python client (official CDAWeb web service; no authentication) |
| ACE SWICS Level 2 | `He2+_ratio` (He²⁺/H⁺ ratio) | NASA CDAWeb – dataset **AC_H2_SWE** | `cdasws` Python client |
| Planetary Kp (hourly, 0–9 in thirds) | `Kp` | NOAA SWPC / GFZ Potsdam – public text file `kp.txt` | Direct HTTP GET of the public text/CSV product |
| Hourly Dst (nT) | `Dst` | Kyoto WDC for Geomagnetism – public text file `dst.txt` | Direct HTTP GET of the public text product |

**Variable‑fit check**: these are the exact variables named in FR‑006 (`N_p`, `T_p`, `He2+_ratio`, `Kp`, `Dst`). If any variable is absent from a downloaded file, the pipeline aborts with an explicit error (SC‑002).

**Coverage risk (data_resources‑9faf82e0)**: ACE SWICS helium abundance has substantial gaps after 2011. In the 2018‑2020 validation window many hourly helium entries are missing; gaps > 6 h are excluded, and if the number of valid helium observations falls below the **evaluability floor** (see Phase 3) the pair is reported as “insufficient data”.

## Statistical Methodology

- **Metrics**: Pearson *r* and Spearman *ρ*.  
- **Lags**: 0, 1, 2, 3, 6 hours (composition leading the index).  
- **Scope**: **storm‑filtered** data (Dst < ‑50 nT) for the full 1998‑2020 period; validation uses the same filter on 2018‑2020.  
- **Test family**: 30 tests (3 composition × 2 indices × 5 lags).

### Autocorrelation adjustment (FR‑010)

Raw p‑values for **Pearson** use the **Pyper & Peterman (1979)** effective sample size:

```
N_eff = N * (1 − r1x * r1y) / (1 + r1x * r1y)
```

where `r1x` and `r1y` are the lag‑1 autocorrelations of the **non‑interpolated** series (computed after storm filtering). The test statistic is  

```
t = r * sqrt((N_eff − 2) / (1 − r²))
```  

with `df = N_eff − 2`.  

### Spearman significance

**Spearman** p‑values are obtained via a **permutation test** (10 000 permutations). To respect temporal dependence, block‑shuffling is performed with a block length equal to the estimated autocorrelation length of the series. The empirical p‑value is the proportion of permuted |ρ| ≥ observed |ρ|.

### Multiple comparisons (FR‑004)

Plain **Bonferroni** correction across all 30 tests:  

```
p_bonf = min(1, 30 * p_raw)
```  

A pair is flagged significant when `p_bonf < 0.05`. The same procedure is recomputed on the validation‑period p‑values.

### Effect‑size benchmark

Pre‑registered threshold |r| > 0.5. For context, prior heliophysics work reported a strong coupling pair with |r| = **0.72** (source: 1105.6272, https://arxiv.org/abs/1105.6272).

### Sensitivity Checks – Detrending (methodology‑e4c34b53)

To guard against spurious correlations driven by solar‑cycle‑scale trends, we also compute the 30 lagged correlations on:
1. **First‑differences** of each series.  
2. **27‑day running‑mean detrended** series (x – rolling_mean_27d, y – rolling_mean_27d).  

These alternative results are saved in `results/detrended_correlations.csv` and reported alongside the primary table.

## Statistical Rigor & Limitations

- **Observational**: findings are associational only.  
- **Power justification**: with typical storm‑filtered series containing > 10 k points, the effective sample size comfortably exceeds 30, yielding > 90 % power to detect the pre‑registered effect size |r| > 0.5 at α = 0.05 (simple power calculation for a two‑sided test). The evaluability floor (≥ 30 observations or N_eff ≥ 30) protects against under‑powered sub‑sets.  
- **Collinearity**: variance‑inflation factors are computed and reported descriptively; no independent‑effect claims are made.  
- **Missing data**: gaps ≤ 6 h are linearly interpolated (logged); gaps > 6 h are excluded, reducing `N_eff`.  
- **Lag scope**: effects beyond 6 h are out of scope (FR‑003).  
- **Evaluability floor**: a composition‑index‑lag pair is marked “not evaluable” if **fewer than 30 valid (non‑missing) observations** remain after interpolation **or** `N_eff < 30`. Such pairs are omitted from significance testing and reported as lacking sufficient data.

## Decision / Rationale

- **CPU‑first**: all computations are classical statistics on ≤ 200 k rows; comfortably within CI limits.  
- **Storm filtering**: directly satisfies FR‑003 and the scientific requirement to focus on geomagnetic storms.  
- **Statistical approach**: Pearson uses the t‑approximation with N_eff; Spearman uses a permutation test that respects autocorrelation, addressing the methodological concern.  
- **Power justification**: added brief power analysis supporting the evaluability floor.  
- **Scope adherence**: removed non‑mandated training‑period and end‑to‑end test phases to stay within the specification.
