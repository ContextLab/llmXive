# Research: Statistical Properties of Simulated Black Hole Mergers

## Problem Statement
We assess whether the marginal distributions of **mass ratio** (`q = m₂/m₁`) and **effective spin** (`χ_eff`) in the GWTC‑1 and GWTC‑2 observational catalogs differ from those predicted by a binary‑black‑hole population synthesis model derived from the official IllustrisTNG/EAGLE releases. All conclusions are **associational** because the data are observational.

## Dataset Strategy

| Dataset | Verified source | Strategy |
|---|---|---|
| GWTC‑1 posterior samples (DOI 10.5281/zenodo.3966973) | **Verified** (SHA‑256 checksum available from Zenodo metadata) | Download and verify checksum; abort if verification fails. |
| GWTC‑2 posterior samples (DOI 10.5281/zenodo.3966974) | **Verified** (SHA‑256 checksum available from Zenodo metadata) | Same as GWTC‑1. |
| Binary‑BH population synthesis catalog | **Official IllustrisTNG/EAGLE releases** (no external URL) | Download the official releases; if unavailable or lacking required fields, abort with a clear limitation note (preserves Constitution Principle VI). No synthetic fallback is used. |
| Detection‑efficiency curves | **Analytic model (Abbott et al. 2021)** | Compute inverse‑probability weights; verify average weight ∈ [0.5, 2] and sum = effective sample size. |

*If any source cannot be fetched or verified, the pipeline aborts and logs the issue in the “Limitations” section of the final report (SC‑009).*

## Statistical Methodology

1. **Posterior sampling (FR‑014)** – For each GWTC event, draw **N = 500** posterior samples (seeded). Perform a **hierarchical bootstrap**: resample events with replacement according to their inverse‑probability weights, then **select a single random draw** per resampled event. This yields an i.i.d. point‑estimate dataset suitable for KS testing. |
2. **Filtering** – Drop rows where `mass_ratio`, `effective_spin`, or `component_mass_1` are NaN. Abort if fewer than 100 valid events remain (FR‑003). |
3. **A priori power analysis** – Using Eq. (1) from arXiv 2309.06305 (α = 0.06) compute the Minimum Detectable Effect Size (MDES) and the required simulation sample size. If the available simulation catalog is smaller than this requirement, abort with a power‑limitation flag before proceeding. |
4. **Simulation catalog** – If the official releases are successfully downloaded, extract component masses, mass ratios, and effective spins; otherwise the pipeline aborts (no synthetic fallback). |
5. **Selection‑bias weighting (FR‑016)** – Compute inverse‑probability weights using the analytic detection‑efficiency model; verify average weight ∈ [0.5, 2] and that the sum of weights equals the effective sample size (SC‑011). |
6. **Weighted Kolmogorov‑Smirnov tests (FR‑005, FR‑016 integration)** – Apply a **weighted two‑sample KS test** on the marginal distributions of `mass_ratio` and `effective_spin`, incorporating the selection‑bias weights. |
7. **Bonferroni correction (FR‑006)** – Adjust the two marginal p‑values using Bonferroni (α / 2). |
8. **Kernel density estimation (FR‑004)** – 1‑D KDEs for `mass_ratio` and `effective_spin` using **Scott’s rule**. |
9. **Sensitivity analysis (FR‑009, expanded)** – Sweep significance threshold α over the range **0.01 → 0.10** (step 0.01). Re‑evaluate significance for each α and flag any parameter where the significance status flips across the sweep as “borderline”. |
10. **Monte‑Carlo power analysis (FR‑010, FR‑015)** – After the a priori check passes, optionally run a Monte‑Carlo simulation (default 500 iterations) to estimate the empirical MDES (deferred value). |
11. **Power‑limitation logging (implicit FR‑012)** – If `simulation_sample_size < 0.5 × observational_sample_size`, set `power_limitation_flag = true` and emit a warning in the “Limitations” section. |
12. **Autocorrelation check (FR‑017, clarified)** – Compute lag‑1 autocorrelation on the **final i.i.d. point‑estimate dataset** (after the hierarchical bootstrap). Require |ρ₁| < 0.1; abort with a diagnostic message if violated. |
13. **Visualization (FR‑007, FR‑008)** – Produce KDE plots for `mass_ratio` and `effective_spin` with simulation and observational curves overlaid; shade regions where the Bonferroni‑adjusted p‑value < 0.05. Save PNGs ≥ 300 DPI. |
14. **Performance measurement (FR‑011)** – Record wall‑clock runtime, peak RSS memory, and peak disk usage; store in `performance_metrics.json`. |
15. **Reporting** – Collate all results, tables, figures, performance metrics, and limitation notes into `final_report.md`.

All steps are deterministic (fixed seeds) and validated against JSON‑Schema contracts.

## Methodological Limitations

- **Observational data verification** – GWTC‑1/2 checksums are now verified via Zenodo metadata; if verification fails, the pipeline aborts (addressing SC‑015).  
- **Simulation data availability** – Official IllustrisTNG/EAGLE releases do not provide resolved binary‑BH component masses/spins directly; the pipeline therefore aborts if these releases cannot be obtained, preserving the original scientific construct (no synthetic fallback).  
- **Bootstrap effective sample size** – Hierarchical bootstrap reduces effective sample size; the a priori power analysis (step 3) ensures the simulation catalog is sufficiently large to detect meaningful KS distances.  
- **Detection‑efficiency model** – Analytic model is an approximation; verification of weight ranges mitigates bias (SC‑011).  
- **Joint test** – Energy‑distance test remains supplementary; primary conclusions rely on weighted marginal KS tests per the specification.  

--- 
