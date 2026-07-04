# Research: Statistical Properties of Simulated Black Hole Mergers

## Problem Statement

Quantify the statistical divergence between observational binary black hole merger distributions (GWTC-1, GWTC-2) and theoretical population predictions. The core question is whether the empirical distributions of mass ratio ($q$) and effective spin ($\chi_{eff}$) in the observational catalog are consistent with predictions from binary population synthesis models or power-law spin distributions. The analysis explicitly distinguishes between comparing *intrinsic* populations (requiring formal selection functions) and *detection* distributions (unweighted comparison).

## Dataset Strategy

### Observational Data (GWTC)

The project requires posterior samples for GWTC-1 and GWTC-2.
*   **Target**: GWTC-1 (DOI: 10.5281/zenodo.3966973) and GWTC-2 (DOI: 10.5281/zenodo.3966974).
*   **Verified Source Status**: The provided "# Verified datasets" block explicitly states: "NO verified source found" for these specific Zenodo DOIs.
*   **Action Plan**:
    1.  The pipeline will attempt to fetch these files using standard Zenodo API/HTTP GET requests to the canonical DOI URLs.
    2.  If the fetch fails (404/Network), the pipeline will retry with exponential backoff (1s, 2s, 4s) up to 3 times.
    3.  If all retries fail, the pipeline will halt with an explicit error: `FATAL: Unable to retrieve GWTC posterior samples. Verified source unavailable.`
    4.  **Constraint**: No alternative or fabricated URLs will be used. If the data is unreachable, the analysis cannot proceed, preserving the "Verified Accuracy" principle.

### Simulation Data (Synthetic Population)

The project requires a simulation dataset with resolved component masses, mass ratios, and effective spins.
*   **Target**: Dedicated BBH population synthesis catalog (e.g., COSMOS) OR a generated synthetic catalog based on a physical hypothesis.
*   **Verified Source Status**:
    *   "COSMOS (gzip)" URLs in the verified list refer to autonomous vehicle datasets (NVIDIA Cosmos Drive), not astrophysical black hole mergers.
    *   "GWTC-3-like", "IllustrisTNG", and "EAGLE" are explicitly marked as "NO verified source found" or noted in the spec as lacking the required schema.
*   **Action Plan**:
    1.  **Primary**: Attempt to download a dedicated BBH catalog if a verified URL exists (currently none found in the provided list).
    2.  **Fallback (Mandatory)**: Generate a synthetic catalog using a **Power-law Spin Distribution** hypothesis, explicitly citing literature parameters.
        *   **Hypothesis**: The synthetic data represents the *Null Hypothesis* (H0). It is generated using parameters from the GWTC-3 population analysis (e.g., Abbott et al. 2021), specifically a power-law mass distribution $p(m) \propto m^{-\alpha}$ and a power-law spin distribution $p(\chi) \propto \chi^{\beta}$.
        *   **Parameters**: $\alpha$ and $\beta$ will be drawn from the posterior distributions reported in GWTC-3 literature (e.g., $\alpha \approx 1.6$, $\beta \approx 0$) to ensure the synthetic data represents a recognized theoretical baseline, not an arbitrary distribution.
        *   **Implementation**: Use `numpy.random` to generate a sufficient number of events with `component_mass_1`, `component_mass_2`, `mass_ratio`, and `effective_spin`.
        *   **Rationale**: This satisfies FR-002 and US-1b by providing a valid distributional source when no external verified source exists. The KS test will determine if GWTC data is consistent with H0 (Power-law). If H0 is rejected, the analysis proceeds to compare against specific alternative models (e.g., Beta-distribution spin) to distinguish between formation channels, avoiding confirmation bias.

## Statistical Methodology

### Kernel Density Estimation (KDE)
*   **Method**: 1D KDE for `mass_ratio` and `effective_spin`.
*   **Bandwidth**: Scott's rule (default in `scipy.stats.gaussian_kde`) as specified in FR-004.
*   **Rationale**: Non-parametric estimation allows comparison of distribution shapes without assuming Gaussianity.

### Kolmogorov-Smirnov (KS) Test
*   **Method**: Two-sample KS test to compare Empirical CDFs of Observed vs. Simulated.
*   **Dimensions**: `mass_ratio` and `effective_spin`.
*   **Correction**: Bonferroni correction applied for multiple comparisons (2 tests) to control Family-Wise Error Rate (FWER) as per FR-006.
*   **Significance**: $\alpha = 0.05$ (with sensitivity sweep).
*   **Scope**: The primary analysis compares *unweighted* distributions. This tests whether the simulation reproduces the *observed* (detected) sample. If the simulation is intended to represent the *intrinsic* population, a formal selection function correction is required (see below).

### Sensitivity Analysis
*   **Method**: Sweep $\alpha \in \{0.04, 0.05, 0.06\}$.
*   **Output**: Flag "borderline" results where significance status flips.
*   **Rationale**: Addresses US-2b and FR-009, ensuring conclusions are robust to threshold choices.

### Power Analysis & MDES
*   **Method**: Formal simulation-based power analysis.
    1.  Define a specific alternative hypothesis (e.g., a shifted effective spin distribution or a Beta-distribution spin).
    2.  Simulate datasets of varying sizes ($N_{sim}$) drawn from this alternative.
    3.  For each $N_{sim}$, run the KS test against the observed data (or a reference distribution).
    4.  Calculate the proportion of tests that reject H0 (Power).
    5.  Determine the Minimum Detectable Effect Size (MDES) as the smallest effect size (e.g., shift in mean spin) that yields 80% power at $\alpha=0.05$.
*   **Rationale**: Addresses US-2c, FR-010, and FR-015. This replaces the invalid heuristic sample-size ratio check, providing a quantitative bound on the sensitivity of the KS test.

### Selection Bias Correction
*   **Method**:
    1.  **Primary (Detection Space)**: Perform the KS test on *unweighted* observed vs. simulated distributions. This tests if the simulation reproduces the *observed* sample (which includes selection effects). The conclusion is framed as "agreement in detection space."
    2.  **Secondary (Intrinsic Space - Optional)**: If the specific selection function files (e.g., `selection_function.h5` from the LIGO-Virgo-KAGRA collaboration's GWTC-3 population analysis) are successfully retrieved, apply the formal selection function $V(q, \chi_{eff})$ to re-weight the observed samples.
    3.  **Limitation**: If the formal selection function files are unavailable, the pipeline will **not** apply "simple volume-weighting" (which is scientifically invalid for GWTC's mass-dependent bias). Instead, it will explicitly log a limitation stating that intrinsic population inference is not possible with the available data, and the analysis is restricted to detection-space agreement.
*   **Rationale**: Addresses FR-016 (Selection Bias) by avoiding invalid heuristics and clearly defining the scope of the analysis.

## Computational Feasibility

*   **Hardware**: GitHub Actions free-tier (multi-core CPU, ample RAM, 14GB Disk).
*   **Memory Management**:
    *   Data loaded via `pandas` with `dtype` optimization.
    *   Posterior samples sampled to a fixed number of points per event to create a point-estimate dataset, preventing memory explosion from full posterior matrices.
    *   Intermediate files cleaned up or streamed.
*   **Runtime**:
    *   Downloads: Bounded by network; retries handled.
    *   Analysis: KS tests and KDEs on $N \approx 200-500$ points are computationally trivial (<1 second). Power analysis simulation is bounded to $N_{iter}=100$ to stay within 6h.
    *   Visualization: Matplotlib rendering is fast.
    *   **Total Estimate**: < 30 minutes (well within 6h limit).
*   **Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib` are all CPU-tractable and have pre-compiled wheels for Linux.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **GWTC Data Unavailable** | Pipeline halts with explicit error. No analysis proceeds without verified data. |
| **Simulation Data Schema Mismatch** | Fallback to synthetic generation with strict schema validation (FR-002). |
| **Small Sample Size (Power)** | Formal simulation-based MDES calculation and limitation logging (FR-010). |
| **Multiple Testing (FWER)** | Bonferroni correction applied automatically (FR-006). |
| **Selection Bias** | Primary analysis restricted to detection space; formal correction attempted only if LVK files available; invalid heuristics explicitly rejected. |

## References (Verified)

*   **GWTC-1**: DOI 10.5281/zenodo.3966973 (Source: Zenodo - *Unverified in system block, attempt canonical fetch*).
*   **GWTC-2**: DOI 10.5281/zenodo.3966974 (Source: Zenodo - *Unverified in system block, attempt canonical fetch*).
*   **Synthetic Data Parameters**: Abbott et al. (2021), "Population Properties of Compact Objects from the Second Gravitational-Wave Transient Catalog" (GWTC-3). Parameters for Power-law mass/spin distributions used as H0 baseline.
*   **Selection Function**: LIGO-Virgo-KAGRA Collaboration (GWTC-3) population analysis repository (if available).
*   **Note**: No URLs from the "# Verified datasets" block are used for GWTC or BBH simulation data as none match the required astrophysical domain. The COSMOS URLs provided are for autonomous vehicles and are explicitly excluded.