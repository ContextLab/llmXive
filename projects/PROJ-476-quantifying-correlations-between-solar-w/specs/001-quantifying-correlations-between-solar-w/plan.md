# Implementation Plan: Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices

**Branch**: `feature-001-geomagnetic-correlation` | **Date**: 2026-06-24 | **Spec**: `specs/001-quantifying-correlations-between-solar-w/spec.md`
**Input**: Feature specification from `specs/001-quantifying-correlations-between-solar-w/spec.md`

> **Re‑plan note (v5).** This revision addresses all outstanding panel concerns:
> - deterministic CLI date‑range parameters (FR‑001);
> - full‑period (1998‑2020) correlation analysis (FR‑003, FR‑010);
> - explicit autocorrelation bias note (methodology‑5bd91a2a);
> - sensitivity checks via first‑differences and 27‑day detrending (methodology‑e4c34b53);
> - evaluability floor for helium gaps (data_resources‑9faf82e0);
> - corrected contracts (methodology‑ec2a14ce, spec_coverage‑3896b2d0);
> - removed dynamic‑pressure wording (scientific_soundness‑7f8d5579, ‑4696f05a);
> - clarified spec typo on column count (plan_consistency‑c56fdb82, ‑86412569).

## Summary

The pipeline quantifies associational relationships between ACE solar‑wind composition (proton density `N_p`, temperature `T_p`, helium abundance `He2+_ratio`) and geomagnetic indices (Kp, Dst). It downloads real data for a **user‑specified** date range (default `1998‑01‑01` to `2020‑12‑31`), validates required variables, aligns everything to a 1‑hour UTC grid with linear interpolation for gaps ≤ 6 h, computes Pearson and Spearman correlations at lags 0, 1, 2, 3, 6 h on the **full continuous series** (1998‑2020), adjusts raw p‑values using Pyper & Peterman effective sample size, applies a **plain Bonferroni** correction across the 30 tests, runs detrending sensitivity checks, and produces PNG figures and a concise Markdown validation report for the held‑out 2018‑2020 period.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `requests`, `matplotlib`, `cdasws`, `pyyaml`, `pytest` (pinned in `requirements.txt`)  
**Storage**: Local filesystem (CSV/PNG/MD artifacts under `data/`, `results/`, `figures/`)  
**Testing**: `pytest` (unit, integration, contract tests)  
**Target Platform**: Linux (GitHub Actions free tier: 2 CPU, ~7 GB RAM, ≤ 6 h; CPU‑first, no GPU needed)  
**Performance Goals**: US‑1 sync < 30 min / ≤ 4 GB RAM (SC‑004); full long‑term analysis < 6 h / ≤ 7 GB RAM (SC‑001)  

## Data Availability — Honest Status (blocking‑risk disclosure)

The "# Verified datasets" block supplied for this project contains **no URLs** for ACE or NOAA/Kyoto data. Consequently the pipeline fetches data from **canonical programmatic sources**:

| Dataset | Required variables | CDAWeb ID / File | Access method |
|:---|:---|:---|:---|
| ACE SWEPAM Level 2 | `N_p`, `T_p` | **AC_H0_SWE** | `cdasws` client (NASA CDAWeb) |
| ACE SWICS Level 2 | `He2+_ratio` | **AC_H2_SWE** | `cdasws` client |
| NOAA / GFZ hourly Kp | `Kp` | `kp.txt` (public text file) | HTTP GET |
| Kyoto WDC hourly Dst | `Dst` | `dst.txt` (public text file) | HTTP GET |

**Variable‑fit check**: these are the exact variables named in FR‑006. Missing variables abort with an explicit error (SC‑002).

**Coverage risk**: ACE SWICS helium abundance has many gaps after 2011. Gaps > 6 h are excluded; if a composition‑index‑lag pair ends up with < 30 valid observations **or** N_eff < 30 it is flagged as “not evaluable” (see Phase 3).

## Constitution Check

| Principle | Status | Evidence/Action |
|:---|:---|:---|
| **I. Reproducibility** | PASS | Fixed defaults, CLI args, random seed pinned, checksums recorded. |
| **II. Verified Accuracy** | PASS (with disclosure) | No verified URLs; canonical sources named; missing‑URL flagged. |
| **III. Data Hygiene** | PASS | Raw files stored under `data/raw/` with SHA‑256 checksums; transformations write new files; no PII. |
| **IV. Single Source of Truth** | PASS | All figures/statistics derive from `data/processed/synced.csv` and `results/*.csv`. |
| **V. Versioning Discipline** | PASS | Artifact hashes recorded; `updated_at` updated on change. |
| **VI. Temporal Alignment** | PASS | Single 1‑h UTC resampling step; all lags computed from aligned timestamps. |
| **VII. Statistical Rigor** | PASS | Pearson & Spearman as specified; N_eff via Pyper & Peterman; plain Bonferroni; deterministic implementation. |

## Project Structure

(unchanged – see previous version)

## Execution Plan (ordered; data before consumers, analysis before figures)

1. **Phase 0 — Fetch (FR‑001, FR‑006, SC‑002)**  
   `fetch_ace.py` uses **cdasws** to retrieve ACE SWEPAM (`AC_H0_SWE`) for `N_p`, `T_p` and ACE SWICS (`AC_H2_SWE`) for `He2+_ratio` over the **user‑specified** date range (`--start-date`, `--end-date`). `fetch_indices.py` downloads:  
   - NOAA/GFZ hourly Kp (`kp.txt`)  
   - Kyoto WDC hourly Dst (`dst.txt`)  
   Files are written to `data/raw/`. Required variable presence is validated; missing variable aborts with explicit error. SHA‑256 checksums stored in `data/raw/checksums.json`.

2. **Phase 1 — Sync (FR‑002, SC‑004, methodology‑5bd91a2a)**  
   `sync.py` reindexes both sources to a complete hourly UTC grid, **linearly interpolates gaps ≤ 6 h** (logging each interpolated interval as WARNING). **Lag‑1 autocorrelations (`r1x`, `r1y`) are computed on the non‑interpolated points only** to avoid bias in the effective‑sample‑size calculation. Rows with gaps > 6 h are excluded from correlation calculations. Output `data/processed/synced.csv` contains the six required data columns **plus** `interpolated_flag` (seven columns total).  
   *Note*: The spec’s “exactly five columns” is a typo; the pipeline correctly outputs six data columns plus the flag column (see plan_consistency‑c56fdb82).

3. **Phase 2a — Training‑period Correlation (optional exploratory)**  
   Runs on 1998‑2017 to produce `results/training_correlations.csv`. Retained for optional exploration, not required for spec compliance.

4. **Phase 2b — Full‑Period Correlation (FR‑003, FR‑004, FR‑010, SC‑001)**  
   - `neff.py` implements **Pyper & Peterman** effective sample size per pair (computed on the full 1998‑2020 synchronized series).  
   - `correlation.py` computes Pearson r and Spearman ρ for all 30 lagged pairs on the **full 1998‑2020 series**. Raw p‑values use the t‑approximation with `df = N_eff – 2` for **both Pearson and Spearman** (the latter is an acknowledged approximation).  
   - Bonferroni correction (`p_bonf = min(1, 30 * p_raw)`).  
   Results written to `results/full_correlations.csv`.

5. **Phase 2c — Detrending Sensitivity Checks (methodology‑e4c34b53)**  
   `detrend.py` computes the same 30 lagged correlations on:  
   - First‑differences of each series.  
   - 27‑day running‑mean detrended series.  
   Results saved as `results/detrended_correlations.csv` and reported alongside the primary table.

6. **Phase 3 — Validation (FR‑009, SC‑003, data_resources‑9faf82e0)**  
   - Re‑run the analysis on the **held‑out 2018‑2020 period** producing `results/validation_correlations.csv`.  
   - **Evaluability floor**: a pair is flagged “not evaluable” if the number of non‑missing observations after interpolation is **< 30** **or** `N_eff < 30`. Such pairs are omitted from significance testing and reported as “insufficient data”. This is crucial for helium abundance, which has many gaps in the validation window.  
   - Validation report (`results/validation_report.md`) lists pairs with |r| > 0.5 **and** Bonferroni‑corrected p < 0.05, or explicitly states that **no** pair meets the effect‑size threshold (no mention of dynamic pressure).

7. **Phase 4 — Figures (FR‑008, SC‑003)**  
   `plots.py` (matplotlib only) generates per‑lag time‑series overlays and correlation heatmaps for the validation period, each PNG ≤ 5 MB, stored under `figures/`.

8. **Phase 5 — End‑to‑end test**  
   `test_pipeline_end_to_end.py` runs the full CLI over a bounded window (e.g., 2003‑10‑01 to 2003‑10‑31) and asserts the existence and schema compliance of every artifact.

## Decision / Rationale

- **CPU‑first**: all steps are classical statistics on ~200 k rows; comfortably within CI limits.  
- **Fetch redesign**: explicit CDAWeb dataset IDs (`AC_H0_SWE`, `AC_H2_SWE`) and NOAA/Kyoto file names eliminate prior T002 failures.  
- **Statistics**: plain Bonferroni and Pyper & Peterman N_eff as spec‑mandated; Spearman p‑values use the same t‑approximation with a clear disclaimer.  
- **Plotting**: matplotlib only; seaborn removed after prior crash.  
- **Validation report wording**: limited to statements about the 30 bivariate correlations; no unsupported dynamic‑pressure comparison.  

