# Research: Statistical Properties of Simulated Black Hole Mergers

## Problem Statement

Do the empirical distributions of `mass_ratio` and `effective_spin` in the GWTC‑1 and GWTC‑2 observational catalogs differ significantly from the “Power‑law mass with independent spin” population model? The analysis is strictly associational (observational data, no randomization).

**Data Availability Requirement**: If the GWTC‑1/2 posterior‑sample downloads fail validation, the pipeline aborts with an explicit error (per the specification’s assumptions). No synthetic observational stand‑in is used in the primary scientific run.

## Dataset Strategy

| Dataset | Verified source | Strategy |
|---|---|---|
| GWTC‑1 posterior samples (10.5281/zenodo.3966973) | **NO verified source found** | Attempt download with strict content validation; on failure abort the pipeline. |
| GWTC‑2 posterior samples (10.5281/zenodo.3966974) | **NO verified source found** | Same as GWTC‑1. |
| BBH population‑synthesis catalog (synthetic) | N/A (generated) | Generate a synthetic catalog from the “Power‑law mass with independent spin” hypothesis (mass‑power‑law index = ‑2.35, spin uniformly in [‑0.5, 0.5]) with a pinned seed. |
| Detection‑efficiency curves | N/A (optional) | If provided, use for inverse‑probability weighting; otherwise apply matched detection‑space cuts to **both** observational and simulated catalogs. |

No dataset URL outside the verified block is cited.

## Statistical Methodology

1. **Posterior extraction (FR‑003, FR‑014)**: For each GWTC event, draw a **single** posterior sample per event (preserving i.i.d. across events). Filter out rows with NaN in `mass_ratio`, `effective_spin`, or `component_mass_1`. Abort if fewer than 100 valid events remain.
2. **Synthetic catalog generation (FR‑002)**: Produce ≥ 100 simulated events from the power‑law mass (index = ‑2.35) and independent uniform spin (‑0.5 → 0.5) hypothesis, using a pinned random seed.
3. **Selection‑bias correction (FR‑016)**: Apply inverse‑probability weighting when detection‑efficiency data are present; otherwise restrict **both** the observational and simulation catalogs to the same detection‑space region (e.g., a minimum detectable chirp mass) to ensure a fair comparison.
4. **Weighted KS tests (FR‑004, FR‑005, FR‑006)**: Compute 1‑D KDEs (Scott’s rule). Perform a weighted two‑sample KS test with B = 1000 bootstrap iterations. **p‑value** is defined as the proportion of bootstrap KS statistics **greater than or equal to** the observed KS statistic. Apply Bonferroni correction across the two parameters.
5. **Sensitivity analysis (FR‑009)**: Re‑evaluate significance for α = 0.05 and α = 0.06 (α = 0.06 per arXiv 2309.06305). Flag “borderline” results where significance flips between the two thresholds.
6. **Power analysis (FR‑010, FR‑015)**: Compute the Minimum Detectable Effect Size (MDES) for the KS test as the minimum Kolmogorov distance D detectable with 80 % power at α = 0.05 using the asymptotic formula D = √[‑0.5 ln(α/2)·((n₁+n₂)/(n₁·n₂))]. Log a power limitation note if the simulation sample size is < 50 % of the observational sample size.
7. **Visualization (FR‑007, FR‑008)**: Produce KDE plots with overlaid obs & sim curves; annotate divergence regions where the Bonferroni‑adjusted p‑value < 0.05.

All steps are deterministic, CPU‑only, and validated against JSON‑Schema contracts.

## Methodological Limitations

- Only 1‑D marginals (`mass_ratio`, `effective_spin`) are tested; joint dependencies are not examined.
- KS tests have reduced sensitivity in distribution tails.
- If detection‑efficiency information is unavailable, results are limited to the observable detection‑space region.
- The analysis is observational; no causal claims are made.
