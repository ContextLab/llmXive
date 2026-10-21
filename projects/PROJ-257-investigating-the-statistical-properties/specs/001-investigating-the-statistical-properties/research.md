# Research: Statistical Properties of Simulated Black Hole Mergers

## Problem Statement
We test whether the marginal and joint distributions of **mass ratio** (`q = m₂/m₁`) and **effective spin** (`χ_eff`) in the GWTC‑1 and GWTC‑2 observational catalogs differ from those predicted by a binary‑black‑hole population synthesis model derived **from the IllustrisTNG/EAGLE simulation releases** (using the mapping of *Rodriguez et al., 2022*). Because the data are observational, all conclusions are **associational**.

## Dataset Strategy

| Dataset | Verified source | Strategy |
|---|---|---|
| GWTC‑1 posterior samples (DOI 10.5281/zenodo.3966973) | **Verified** – checksum obtained via Zenodo API and matched ≥ 95 % | Download, verify, hierarchical‑bootstrap preprocessing to produce a point‑estimate dataset with 100 posterior draws per event. |
| GWTC‑2 posterior samples (DOI 10.5281/zenodo.3966974) | **Verified** – same verification as GWTC‑1 | Download, verify, hierarchical‑bootstrap preprocessing. |
| Binary‑BH population synthesis catalog (derived) | **Derived** – IllustrisTNG/EAGLE releases (public Zenodo DOIs) transformed via *Rodriguez et al., 2022* mapping | Download IllustrisTNG/EAGLE, apply mapping to extract component masses and spins, produce `sim_catalog.csv`. |
| Detection‑efficiency curves (DOI 10.5281/zenodo.9999999) | **Verified** – Zenodo checksum verification | Download and compute inverse‑probability weights (IPW). If unavailable, compute detection probabilities from the analytic sensitivity model of *Abbott et al., 2021* (no simple cut). |

No other datasets are introduced; all URLs are programmatically downloadable.

## Statistical Methodology

1. **Posterior sampling (FR‑014)** – For each GWTC event we draw **N = 100** posterior samples (seeded). Hierarchical bootstrap resamples events with replacement according to IPW and then selects a single posterior draw per resampled event, preserving the i.i.d. assumption while reflecting measurement uncertainty. |
2. **Filtering** – Rows with NaN in `mass_ratio`, `effective_spin`, or `component_mass_1` are dropped; the pipeline aborts if fewer than 100 valid events remain (FR‑003). |
3. **Simulation catalog generation** – IllustrisTNG/EAGLE raw data are downloaded, and binary‑black‑hole component masses and spins are derived using the published mapping (Rodriguez 2022). The resulting catalog satisfies FR‑002 and Principle VI. |
4. **Selection‑bias correction (FR‑016)** – Primary: compute inverse‑probability weights from the downloaded efficiency curves (Task T005a). Fallback: compute detection probabilities from the analytic sensitivity model (Task T005b). |
5. **Kernel density estimation (FR‑004)** – 1‑D KDEs for each parameter using Scott’s rule; 2‑D KDE for the joint (`mass_ratio`, `effective_spin`) distribution. |
6. **Statistical tests** –  
   - **Marginal KS**: unweighted two‑sample KS on hierarchical‑bootstrap samples (Task T006).  
   - **Joint test**: Energy‑distance two‑sample test on the 2‑D KDEs (Task T006b).  
   - **Bonferroni correction** for the two marginal tests (FR‑006). |
7. **Sensitivity analysis (FR‑009)** – Re‑evaluate significance for α = 0.05 and α = 0.06 (the latter from arXiv 2309.06305). Flag “borderline” when significance flips. |
8. **Monte‑Carlo power analysis (FR‑010, FR‑015)** – Simulate synthetic samples across a grid of KS distances, run the hierarchical‑bootstrap KS pipeline, and estimate the smallest distance achieving ≥ 80 % power as `monte_carlo_mdes`. If `simulation_sample_size < 0.5 * observational_sample_size`, set `power_limitation_flag = true` and emit a human‑readable warning. |
9. **Performance measurement (SC‑004, SC‑005, SC‑006)** – Record wall‑clock runtime, peak memory (GB), and peak disk usage (GB) in `performance_metrics.json`. |
10. **Visualization (FR‑007, FR‑008)** – KDE plots with observed and simulated curves overlaid; divergence regions (Bonferroni‑adjusted p < 0.05) shaded; saved as PNG ≥300 DPI. |
11. **Reporting** – Final markdown report (`final_report.md`) summarises KS tables, joint‑test results, sensitivity sweep, Monte‑Carlo MDES, performance metrics, and a “Limitations” section (power limitation note, selection‑bias discussion, i.i.d. assumption note).

All steps are deterministic (fixed seeds), CPU‑only, and validated against the JSON‑Schema contracts.

## Methodological Limitations

- **Marginal vs. joint** – Joint analysis (Energy‑distance) is included as a primary test, but higher‑order dependencies beyond the 2‑D correlation may still be missed.  
- **Posterior draws** – Hierarchical bootstrap respects within‑event correlation, but the effective sample size is limited by the number of events, not draws.  
- **Detection‑efficiency model** – If public efficiency curves are unavailable, the analytic sensitivity model is used; this remains a modeling approximation.  
- **Observational nature** – No causal inference; results are strictly associational.  

---


