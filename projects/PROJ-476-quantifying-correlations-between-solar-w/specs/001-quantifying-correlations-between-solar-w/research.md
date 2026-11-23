# Research: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

## Summary of Scientific Question
We investigate **associational** relationships between solar‑wind composition (proton density `N_p`, proton temperature `T_p`, helium abundance `He2+_ratio`) and geomagnetic disturbance intensity (`Kp`, `Dst`). Analyses are performed on the **full continuous dataset** (1998‑2020) at lagged intervals of 0, 1, 2, 3, 6 h, and are **validated** on an out‑of‑sample period (2018‑2020). An **optional storm‑filtered** analysis (`Dst < -50 nT`) is provided for exploratory insight, with a logged disclaimer about collider bias.

## Dataset Strategy
**Verified‑source status**: the "# Verified datasets" block contains no URLs for the required ACE or NOAA/Kyoto products. Consequently the pipeline uses **canonical, programmatic sources** (non‑verified but openly accessible) and discloses this limitation.

| Dataset | Required variables | Canonical source (named) | Access method |
|:---|:---|:---|:---|
| ACE SWEPAM Level 2 | `N_p`, `T_p` | NASA CDAWeb – dataset **AC_H0_SWE** | `cdasws` Python client (no auth) |
| ACE SWICS Level 2 | `He2+_ratio` | NASA CDAWeb – dataset **AC_H2_SWE** | `cdasws` Python client |
| NOAA / GFZ hourly Kp | `Kp` | NOAA SWPC public text file `kp.txt` | HTTP GET |
| Kyoto WDC hourly Dst | `Dst` | Kyoto WDC public text file `dst.txt` | HTTP GET |

*Variable‑fit check*: these are exactly the variables listed in **FR‑006**. If any variable is missing, the pipeline aborts with an explicit error (covers **SC‑002**).

*Coverage risk*: ACE SWICS helium abundance has gaps after 2011; gaps > 6 h are excluded, and if the valid helium count falls below the evaluability floor the pair is reported as “insufficient data” (per **SC‑003**).

## Statistical Methodology

- **Metrics**: Pearson *r* and Spearman *ρ*.  
- **Lags**: 0, 1, 2, 3, 6 h (composition leads index).  
- **Test family**: A set of hypothesis tests covering the combinations of 3 compositions, 2 indices, and 5 lags.  

### Autocorrelation Adjustment (FR‑010)
Pearson raw p‑values use the **Pyper & Peterman (1979)** effective sample size:

```
N_eff = N * (1 − r1x * r1y) / (1 + r1x * r1y)
```

where `r1x` and `r1y` are lag‑1 autocorrelations of the **non‑interpolated** series after any storm filtering.  
The t‑statistic is `t = r * sqrt((N_eff‑2) / (1‑r²))` with `df = N_eff‑2`.

### Spearman Significance
Spearman p‑values are obtained via a **block‑permutation test** with **10 000 permutations** (as required by FR‑010).  
**Block length** for each series is estimated as  

```
block_len = ceil(1 / (1 - r1))
```

where `r1` is the lag‑1 autocorrelation of that series. This preserves temporal dependence while randomising the order of blocks. The empirical p‑value is the proportion of permuted |ρ| ≥ observed |ρ|.

### Multiple‑Comparison Control (FR‑004)
Plain **Bonferroni** correction across all 30 tests: `p_bonf = min(1, 30 * p_raw)`. A pair is significant when `p_bonf < 0.05`. The same procedure is reapplied on the validation period.

### Effect‑size Benchmark
Pre‑registered threshold **|r| > 0.5**. For context, a previously reported heliophysics pair achieved |r| = **0.72** (source: 1105.6272, https://arxiv.org/abs/1105.6272).

### Sensitivity Checks – Interpolation Bias (methodology‑4b693a5d)
To assess the impact of linear interpolation on correlations we run a **dual‑run sensitivity analysis**: after Phase 2 we repeat the full correlation pipeline while **dropping any rows where `interpolated_flag=True`**. Results are stored in `results/full_correlations_nointerp.csv` and compared to the primary results; large discrepancies trigger a warning in the log.

### Sensitivity Checks – Detrending (methodology‑e4c34b53)
To guard against solar‑cycle trends we also compute the 30 lagged correlations on:  
1. **First‑differences** of each series.  
2. **27‑day running‑mean detrended** series (`x – rolling_mean_27d`).  

Results are saved in `results/detrended_correlations.csv` and reported alongside the primary table.

### Power & Evaluability (SC‑003)
Typical storm‑filtered series contain > 10 k points; with `N_eff ≥ 30` the two‑sided power to detect |r| > 0.5 at α = 0.05 exceeds 90 %.  
**Evaluability floor**: a composition‑index‑lag pair is marked “not evaluable” if **valid observations < 30** **or** `N_eff < 30`. Such rows receive `evaluability_flag = False` and are omitted from significance testing.

### Collinearity & Causality
Variance‑inflation factors (VIF) are computed for the three composition variables; results are reported descriptively. Findings are framed as **associational** (observational data), not causal.

### Missing Data & Gaps
- Linear interpolation for gaps ≤ 6 h (logged).  
- Gaps > 6 h are excluded, reducing `N_eff`.  
- If a required variable is entirely absent, the pipeline aborts (SC‑002).

## Optional Storm‑Filtered Analysis (Exploratory)
The storm‑filtered branch (Phase 4) runs the same pipeline on the subset `Dst < -50 nT`. A **disclaimer** about collider bias is logged, and the results are written to `results/storm_correlations.csv`. These exploratory results are presented **separately** and are **not** used to support the primary scientific claim (FR‑003).

## Validation (Held‑out 2018‑2020)
We re‑run the full‑dataset correlation pipeline on the 2018‑2020 window, producing `results/validation_correlations.csv`. The validation report (`validation_report.md`) flags any pair with |r| > 0.5 **and** Bonferroni‑corrected p < 0.05, satisfying **FR‑009** and **SC‑003**.

## Decision / Rationale
- **CPU‑first**: Classical statistics and a 10 000‑permutation block test run comfortably on 2 CPU cores; runtime fits CI limits.  
- **Full vs. Storm‑filtered**: Primary scientific claim (FR‑003) uses the full continuous series; the optional storm‑filtered branch satisfies the exploratory requirement while clearly flagged as non‑primary.  
- **Effective Sample Size** and **Block‑Permutation** guarantee valid p‑values under autocorrelation, meeting **VII. Statistical Rigor**.  
- **Interpolation sensitivity** addresses potential bias (methodology‑4b693a5d) via the dual‑run sensitivity analysis.  
- **Permutation count** set to the required 10 000 (FR‑010) with a realistic runtime estimate (data_resources-5730b465).  
- **Dataset sourcing** is transparent; lack of verified URLs is disclosed per **II. Verified Accuracy**.  
- **Reporting** explicitly references FR‑009 and FR‑008, closing the spec‑coverage gap.  

---


## Constitution Check
| Principle | Status | Action / Evidence |
|-----------|--------|--------------------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic pipelines, checksums recorded. |
| II. Verified Accuracy | PASS (with disclosure) | No verified URLs for ACE/NOAA; canonical sources named and disclosed. |
| III. Data Hygiene | PASS | Raw files stored under `data/raw/` with SHA‑256 checksums; transformations write new files; no PII. |
| IV. Single Source of Truth | PASS | All figures/tables trace to rows in `data/processed/synced.csv` and `results/*.csv`. |
| V. Versioning Discipline | PASS | Artifact hashes recorded; `updated_at` updated on change. |
| VI. Temporal Alignment and Lag Consistency | PASS | Single 1‑h UTC grid; all lags computed on aligned timestamps. |
| VII. Statistical Rigor and Multiple‑Comparison Control | PASS | Pearson uses Pyper & Peterman N_eff; Spearman uses block‑permutation (10 000); Bonferroni correction applied. |