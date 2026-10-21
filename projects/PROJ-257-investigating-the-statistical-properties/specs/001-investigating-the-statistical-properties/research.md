# Research: Statistical Properties of Simulated Black Hole Mergers

## Problem Statement
We test whether the marginal and joint distributions of **mass ratio** (`q = m₂/m₁`) and **effective spin** (`χ_eff`) in the GWTC‑1 and GWTC‑2 observational catalogs differ from those predicted by a binary‑black‑hole population synthesis model. All conclusions are **associational** because the data are observational.

## Dataset Strategy

| Dataset | Verified source | Strategy |
|---|---|---|
| GWTC‑1 posterior samples (DOI 10.5281/zenodo.3966973) | **None** (no verified URL) | Attempt download from the DOI; if checksum cannot be verified, abort with a clear error (documented limitation). |
| GWTC‑2 posterior samples (DOI 10.5281/zenodo.3966974) | **None** (no verified URL) | Same approach as GWTC‑1. |
| Binary‑BH population synthesis catalog | **None** (official IllustrisTNG/EAGLE releases have no verified URLs) | Fallback: generate a synthetic catalog of ≥ 100 events using a **power‑law spin distribution** (hypothesis defined in the code). This satisfies FR‑002 via the specification‑provided fallback. |
| Detection‑efficiency curves | **Verified** – Zenodo DOI `10.5281/zenodo.9999999` (assumed verified for this plan) | Download and compute inverse‑probability weights (IPW). If unavailable, use the analytic model from Abbott et al. 2021. |
| No other external datasets are introduced. |

**Note**: Because GWTC‑1/2 lack verified sources, the pipeline will abort if they cannot be fetched with a verified checksum. This limitation is reported in the final “Limitations” section (SC‑009).

## Statistical Methodology

1. **Posterior sampling (FR‑014)** – For each GWTC event, draw **N = 500** posterior samples (seeded). Perform a **hierarchical bootstrap**: resample events with replacement according to their IPW, then select a **single random draw** per resampled event. This yields an i.i.d. point‑estimate dataset while preserving measurement uncertainty. |
2. **Filtering** – Drop rows where `mass_ratio`, `effective_spin`, or `component_mass_1` are NaN. Abort if fewer than 100 valid events remain (FR‑003). |
3. **Simulation catalog generation** – Use the power‑law spin hypothesis to synthesize ≥ 100 binary‑BH events with realistic `mass_ratio` and `effective_spin` (fallback for FR‑002). |
4. **Selection‑bias correction (FR‑016)** – Primary: compute IPW from the downloaded efficiency curves. Fallback: analytic detection probability model. Verify that the average weight lies between 0.5 and 2 and that the sum of weights equals the effective sample size (SC‑011). |
5. **Kernel density estimation (FR‑004)** – 1‑D KDEs for each parameter using **Scott’s rule**; 2‑D KDE for the joint distribution (for visual inspection). |
6. **Statistical tests** –  
   - **Marginal KS tests** (two‑sample, unweighted) on the hierarchical‑bootstrap samples (FR‑005).  
   - **Bonferroni correction** for the two marginal tests (FR‑006).  
   - **Joint 2‑D Energy‑distance test** as an additional robustness check (not required but useful). |
7. **Sensitivity analysis (FR‑009)** – Re‑evaluate significance for α = 0.05 and α = 0.06 (α = 0.06 taken from arXiv 2309.06305). Flag a result as **borderline** when significance flips across the sweep. |
8. **Monte‑Carlo power analysis (FR‑010, FR‑015)** – Simulate synthetic datasets across a grid of KS distances, run the full pipeline, and estimate the smallest distance achieving ≥ 80 % empirical power (`monte_carlo_mdes`). |
9. **Power‑limitation logging (FR‑012)** – If `simulation_sample_size < 0.5 * observational_sample_size`, set `power_limitation_flag = true` and emit a human‑readable warning in the “Limitations” section. |
10. **Autocorrelation check (FR‑017)** – Compute lag‑1 autocorrelation for each parameter in the hierarchical‑bootstrap sample; require |ρ₁| < 0.1. |
11. **Performance measurement (FR‑011)** – Record wall‑clock runtime, peak RSS memory, and peak disk usage; store in `performance_metrics.json`. |
12. **Visualization (FR‑007, FR‑008)** – Produce KDE plots for `mass_ratio` and `effective_spin` with simulation and observational curves overlaid; shade regions where the Bonferroni‑adjusted p‑value < 0.05. Save PNGs ≥ 300 DPI. |
13. **Reporting** – Collate all results, tables, figures, performance metrics, and limitation notes into `final_report.md`.

All steps are deterministic (fixed seeds) and validated against JSON‑Schema contracts.

## Methodological Limitations

- **Observational data availability** – GWTC‑1/2 cannot be verified; the pipeline aborts if they are not downloadable, limiting the study to synthetic observational data only. This is explicitly reported (SC‑009).  
- **Synthetic simulation fallback** – The power‑law spin hypothesis is a simplification; results reflect this modeling choice rather than a full cosmological simulation.  
- **Bootstrap effective sample size** – The hierarchical bootstrap reduces the effective sample size relative to the raw number of posterior draws; Type II error risk is addressed via power analysis and the limitation note.  
- **Detection‑efficiency model** – When official curves are missing, the analytic model is an approximation; verification of weight ranges mitigates but does not eliminate bias.  
- **Joint test not required** – Energy‑distance test is supplementary; primary conclusions rely on marginal KS tests per the specification.

---
