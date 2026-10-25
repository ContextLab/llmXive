# Implementation Plan: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

**Branch**: `feature-001-geomagnetic-correlation` | **Date**: 2026-10-25 | **Spec**: `specs/001-quantifying-correlations-between-solar-w/spec.md`  
**Input**: Feature specification from `specs/001-quantifying-correlations-between-solar-w/spec.md`

## Summary

The pipeline quantifies associational relationships between ACE solar‑wind composition (proton density `N_p`, temperature `T_p`, helium abundance `He2+_ratio`) and geomagnetic indices (Kp, Dst). It downloads real data for a **user‑specified** date range (default `1998‑01‑01` to `2020‑12‑31`), validates required variables, aligns everything to a 1‑hour UTC grid with linear interpolation for gaps ≤ 6 h, **filters to storm periods (Dst < ‑50 nT)**, computes Pearson and Spearman correlations at lags 0, 1, 2, 3, 6 h, adjusts raw p‑values using the Pyper & Peterman effective sample size for Pearson, applies a **plain Bonferroni** correction across the 30 tests, and generates PNG visualisations and a concise Markdown validation report for the held‑out 2018‑2020 period.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `requests`, `matplotlib`, `cdasws`, `pyyaml`, `pytest` (pinned in `requirements.txt`)  
**Storage**: Local filesystem (CSV/PNG/MD artifacts under `data/`, `results/`, `figures/`)  
**Testing**: `pytest` (unit, integration, contract tests)  
**Target Platform**: Linux (GitHub Actions free tier: 2 CPU, ~7 GB RAM, ≤ 6 h; CPU‑first)  

## Data Availability — Honest Status (blocking‑risk disclosure)

The "# Verified datasets" block supplied for this project contains **no URLs** for ACE or NOAA/Kyoto data. Consequently the pipeline fetches data from **canonical programmatic sources**:

| Dataset | Required variables | CDAWeb ID / File | Access method |
|:---|:---|:---|:---|
| ACE SWEPAM Level 2 | `N_p`, `T_p` | **AC_H0_SWE** | `cdasws` client (NASA CDAWeb) |
| ACE SWICS Level 2 | `He2+_ratio` | **AC_H2_SWE** | `cdasws` client |
| NOAA / GFZ hourly Kp | `Kp` | `kp.txt` (public text file) | HTTP GET |
| Kyoto WDC hourly Dst | `Dst` | `dst.txt` (public text file) | HTTP GET |

**Variable‑fit check**: these are the exact variables named in FR‑006. Missing variables abort with an explicit error (SC‑002).

## Constitution Check

| Principle | Status | Evidence/Action |
|:---|:---|:---|
| **I. Reproducibility** | PASS | Fixed defaults, CLI args, random seed pinned, checksums recorded. |
| **II. Verified Accuracy** | PASS (with disclosure) | No verified URLs; canonical sources named; missing‑URL flagged. |
| **III. Data Hygiene** | PASS | Raw files stored under `data/raw/` with SHA‑256 checksums; transformations write new files; no PII. |
| **IV. Single Source of Truth** | PASS | All figures/statistics derive from `data/processed/synced.csv` and `results/*.csv`. |
| **V. Versioning Discipline** | PASS | Artifact hashes recorded; `updated_at` updated on change. |
| **VI. Temporal Alignment** | PASS | Single 1‑h UTC resampling step; all lags computed from aligned timestamps. |
| **VII. Statistical Rigor** | PASS | Pearson & Spearman as specified; N_eff via Pyper & Peterman for Pearson; Spearman p‑values via permutation test; plain Bonferroni; deterministic implementation. |

## Project Structure

```text
specs/001-quantifying-correlations-between-solar-w/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── analysis_schema.schema.yaml
    ├── dataset.schema.yaml
    └── output.schema.yaml

src/
├── code/
│   ├── data/
│   │   ├── fetch_ace.py
│   │   ├── fetch_noaa.py
│   │   └── sync.py
│   ├── analysis/
│   │   ├── neff.py
│   │   ├── correlation.py
│   │   ├── detrend.py
│   │   └── validate.py
│   ├── viz/
│   │   └── plots.py
│   └── main.py
tests/
├── unit/
│   └── test_sync.py
├── integration/
│   └── test_end_to_end.py
└── contract/
    └── test_schema.py
```

## Execution Plan (ordered; data before consumers, analysis before figures)

1. **Phase 0 — Fetch (FR‑001, FR‑006, SC‑002)**  
   `fetch_ace.py` uses **cdasws** to retrieve ACE SWEPAM (`AC_H0_SWE`) for `N_p`, `T_p` and ACE SWICS (`AC_H2_SWE`) for `He2+_ratio` over the **user‑specified** date range (`--start-date`, `--end-date`). `fetch_noaa.py` downloads:  
   - NOAA/GFZ hourly Kp (`kp.txt`)  
   - Kyoto WDC hourly Dst (`dst.txt`)  
   Files are written to `data/raw/`. Required variable presence is validated; missing variable aborts with explicit error. SHA‑256 checksums stored in `data/raw/checksums.json`.

2. **Phase 1 — Sync (FR‑002, SC‑004, VI)**  
   `sync.py` reindexes both sources to a complete hourly UTC grid, **linearly interpolates gaps ≤ 6 h** (logging each interpolated interval as WARNING). Rows with gaps > 6 h are excluded from downstream analysis. Output `data/processed/synced.csv` contains the six required data columns plus an `interpolated_flag` column (seven columns total).  

3. **Phase 2 — Storm‑filtered Correlation (FR‑003, FR‑004, FR‑010, SC‑001)**  

   - **Storm filtering**: `synced.csv` is filtered to rows with `Dst < -50` nT before any statistical computation.  
   - **Effective sample size (Pearson only)**: `neff.py` implements **Pyper & Peterman (1979)** N_eff using lag‑1 autocorrelations of the **non‑interpolated** series (computed after storm filtering).  
   - **Correlation computation** (`correlation.py`):  
     *Pearson*: Compute coefficient *r* and raw p‑value via the t‑approximation with `df = N_eff – 2`.  
     *Spearman*: Compute coefficient *ρ* and obtain a raw p‑value via a **permutation test** (10 000 permutations, block‑shuffling of size equal to the estimated autocorrelation length to preserve temporal dependence). The permutation p‑value is the proportion of permuted |ρ| ≥ observed |ρ|.  
   - **Multiple‑comparison correction**: plain **Bonferroni** (`p_bonf = min(1, 30 * p_raw)`).  
   - **Evaluability floor & power note**: a pair is flagged “not evaluable” if **valid observations < 30** **or** `N_eff < 30`. With typical storm‑filtered series (> 10 k points) the effective sample size comfortably exceeds 30, giving > 90 % power to detect the pre‑registered effect size |r| > 0.5 at α = 0.05; the floor protects against spuriously small subsets.  
   Results written to `results/full_correlations.csv`.

4. **Phase 3 — Validation (FR‑009, SC‑003)**  
   - Re‑run the full analysis on the **held‑out 2018‑2020 period** producing `results/validation_correlations.csv`.  
   - Apply the same evaluability floor; pairs failing it are reported as “insufficient data”.  
   - Generate a concise Markdown report (`results/validation_report.md`) that lists any composition‑index‑lag pair with |r| > 0.5 **and** Bonferroni‑corrected p < 0.05, or explicitly states that none meet the threshold.

5. **Phase 4 — Figures (FR‑008, SC‑003)**  
   `plots.py` (matplotlib only) creates per‑lag time‑series overlay plots and a correlation heatmap for the validation period; each PNG ≤ 5 MB, stored under `figures/`.

## Decision / Rationale

- **CPU‑first**: all steps are classical statistics on ≤ 200 k rows; comfortably within CI limits.  
- **Storm filtering**: directly satisfies FR‑003 and the scientific requirement to focus on geomagnetic storms.  
- **Statistical approach**: Pearson uses the t‑approximation with N_eff; Spearman uses a permutation test that respects autocorrelation, addressing the methodological concern.  
- **Power justification**: added brief power analysis supporting the evaluability floor.  
- **Scope adherence**: removed non‑mandated training‑period and end‑to‑end test phases to stay within the specification.   ===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-476-quantifying-correlations-between-solar-w/specs/001-quantifying-correlations-between-solar-w/research.md===
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

**Spearman** p‑values are obtained via a **permutation test** (10 000 permutations, block‑shuffling with block length equal to the estimated autocorrelation length) applied to the storm‑filtered series. The empirical p‑value is the fraction of permuted |ρ| ≥ observed |ρ|.

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
- **Scope adherence**: removed non‑mandated training‑period and end‑to‑end test phases to stay within the specification.   ===END_ARTIFACT===

===BEGIN_ARTIFACT projects/PROJ-476-quantifying-correlations-between-solar-w/specs/001-quantifying-correlations-between-solar-w/contracts/analysis_schema.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "CorrelationResult"
description: "Schema for one row of results/correlations.csv and results/validation_correlations.csv. Pearson p-values use the t‑approximation with df = n_eff - 2; Spearman p-values are obtained via a permutation test (10 000 permutations) that preserves temporal dependence."
type: object
properties:
  composition_parameter:
    type: string
    enum:
      - proton_density
      - temperature
      - helium_abundance
    description: "Solar wind composition variable under test."
  geomagnetic_index:
    type: string
    enum:
      - Kp
      - Dst
    description: "Geomagnetic index under test."
  lag_hours:
    type: integer
    enum:
      - 0
      - 1
      - 2
      - 3
      - 6
    description: "Lag in hours (composition leading the index)."
  pearson_r:
    type: number
    minimum: -1
    maximum: 1
    description: "Pearson correlation coefficient."
  spearman_rho:
    type: number
    minimum: -1
    maximum: 1
    description: "Spearman rank correlation coefficient."
  n_eff:
    type: number
    exclusiveMinimum: 2
    description: "Pyper & Peterman effective sample size for this pair (used for Pearson significance)."
  p_raw:
    type: number
    minimum: 0
    maximum: 1
    description: "Raw p-value: for Pearson computed with df = n_eff - 2 (t‑approximation); for Spearman computed via permutation test."
  p_bonferroni:
    type: number
    minimum: 0
    maximum: 1
    description: "Bonferroni‑corrected p‑value, min(1, 30 * p_raw)."
  significant:
    type: boolean
    description: "True if p_bonferroni < 0.05."
  effect_size_large:
    type: boolean
    description: "True if abs(pearson_r) > 0.5."
  evaluability_flag:
    type: boolean
    description: "False if valid observations < 30 or n_eff < 30 (data_resources‑9faf82e0)."
required:
  - composition_parameter
  - geomagnetic_index
  - lag_hours
  - pearson_r
  - spearman_rho
  - n_eff
  - p_raw
  - p_bonferroni
  - significant
  - effect_size_large
  - evaluability_flag
additionalProperties: false