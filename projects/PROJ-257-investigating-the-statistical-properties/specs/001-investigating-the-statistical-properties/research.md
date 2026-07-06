# Research: Statistical Properties of Simulated Black Hole Mergers

## Problem Statement

The project investigates whether the statistical distributions of component masses and effective spins in the GWTC-1 and GWTC-2 observational catalogs align with predictions from a specific theoretical baseline hypothesis: the "Power-law mass with independent spin" model. The core scientific question is: *Do the empirical cumulative distribution functions (ECDFs) of mass_ratio and effective_spin in the observational data differ significantly from those of a theoretical population model?* This is framed as a **Goodness-of-Fit** test against an independent physical model (cited from LVC literature), not a comparison between observation and a distinct, unrelated simulation source.

## Dataset Strategy

### Observational Data (GWTC-1 & GWTC-2)
The project requires posterior sample files for the gravitational-wave transient catalogs to extract component masses and spins.
- **Source**: Zenodo DOIs 10.5281/zenodo.3966973 (GWTC-1) and 10.5281/zenodo.3966974 (GWTC-2).
- **Status**: **NO VERIFIED SOURCE FOUND** in the provided "Verified datasets" block.
- **Action**: The pipeline MUST implement a robust download mechanism targeting the canonical Zenodo DOI URLs. If the specific DOIs are unavailable or return 404, the pipeline MUST fail with an explicit error message rather than fabricating data. The `download.py` script will implement exponential backoff retries (1s, 2s, 4s) up to 3 attempts.
- **Schema Requirement**: Files must contain posterior samples for `mass_ratio`, `effective_spin`, and `component_mass` parameters.

### Simulation Data
The project requires a simulation dataset with the same schema as the observational data for KS testing.
- **Candidate 1: IllustrisTNG / EAGLE**: The Constitution (Principle VI) suggests these. However, the Spec (Assumptions) and verified dataset list confirm these provide galaxy/halo merger rates, **not** resolved binary black hole component masses and spins.
- **Candidate 2: Dedicated Population Synthesis (COSMOS)**: The Spec mentions COSMOS. The "Verified datasets" block lists a "COSMOS (gzip)" entry, but the URLs point to *autonomous vehicle* datasets (NVIDIA PhysicalAI) and unrelated QA tasks. **These are irrelevant to astrophysics.**
- **Conclusion**: No verified external astrophysical simulation dataset with the required schema exists in the provided list.
- **Action**: The pipeline MUST generate a **synthetic catalog** based on a pre-defined physical hypothesis.
  - **Hypothesis**: "Power-law mass with independent spin" (a standard baseline in GW population studies, e.g., based on LIGO-Virgo collaboration population papers such as Abbott et al. 2021).
  - **Generation Method**: 
    - **Mass**: Sample from a power-law distribution $p(m) \propto m^{-\alpha}$ (with $\alpha$ within a typical astrophysical range) within the range [5, 50] solar masses.
    - **Spin**: Sample effective spin from an independent power-law distribution (or uniform distribution) within a bounded range.
    - **Correlation**: Explicitly assume **no correlation** between mass and spin for this baseline hypothesis.
  - **Sample Size**: Generated to be comparable to the observational catalog (target ≥100 events) to ensure statistical power for the KS test.

## Statistical Methodology

### 1. Data Preprocessing & Posterior Extraction
- **Posterior Sampling**: For each event, extract the **median** value and uncertainty from the posterior distribution. **CRITICAL**: Do **not** pool all posterior samples into a single flat list, as this violates the i.i.d. assumption (samples from the same event are correlated). Instead, for each event, sample repeatedly from its posterior distribution to create a distribution of medians. This satisfies FR-014 by reflecting uncertainty in the test input.
- **Filtering**: Remove events with NaN in `mass_ratio`, `effective_spin`, or `component_mass_1`.
- **Selection Bias Correction**: The KS test assumes i.i.d. data. GWTC data is subject to detection efficiency (selection bias). The pipeline MUST apply **Inverse Probability Weighting (IPW)** using the provided GWTC selection efficiency curves (FR-016). 
  - **If curves are unavailable**: The analysis is restricted to the "detection space" (the region where detection probability is high and uniform), and a limitation note is logged. **Uniform weighting is NOT applied** as it would bias the results.

### 2. Hypothesis Testing (Event-Level Bootstrapping with Weighted KS)
- **Method**: Two-sample **Weighted** Kolmogorov-Smirnov (KS) test.
- **Assumption Correction**: To preserve the i.i.d. assumption and propagate measurement uncertainty, the pipeline will perform **event-level bootstrapping**:
  1. For each bootstrap iteration:
     a. Sample a new median value for **every** event from its posterior distribution.
     b. Compute the KS statistic on these new medians.
  2. Repeat to estimate the distribution of the KS statistic under the null hypothesis.
  3. Apply IPW weights to the samples in the KS test calculation (using a weighted KS implementation).
- **Null Hypothesis ($H_0$)**: The observational and simulation samples are drawn from the same distribution (i.e., the data fits the Power-law mass with independent spin hypothesis).
- **Parameters**: `mass_ratio` and `effective_spin`.
- **Correction**: Bonferroni correction applied to p-values since 2 tests are performed (FR-006).
- **Significance**: $\alpha = 0.05$ (adjusted).

### 3. Sensitivity Analysis
- **Sweep**: Re-evaluate significance for $\alpha \in \{0.04, 0.05, 0.06\}$.
- **Output**: Flag "borderline" results where significance status flips across the sweep range (FR-009).

### 4. Power Analysis
- **Metric**: Minimum Detectable Effect Size (MDES) calculated for the given sample sizes.
- **Limitation**: If simulation sample size < 50% of observational size, log a power limitation warning regarding Type II error risk (FR-010).

## Methodological Limitations
- **KS Test Sensitivity**: The KS test is less sensitive to differences in the tails of distributions and ignores correlations between parameters. The analysis focuses on 1D marginals due to computational constraints, but the event-level bootstrapping approach addresses the discrete nature of events and the correlated posterior samples. The joint distribution (mass vs. spin) is not tested, which may miss correlations.
- **Selection Bias**: If selection efficiency curves are unavailable, the analysis is restricted to the "detection space," which may limit the generalizability of the results to the intrinsic population.
- **Joint Distributions**: The analysis is limited to 1D marginal distributions (mass_ratio, effective_spin) due to the complexity of implementing a weighted 2D KS test in a CPU-constrained environment. The joint distribution (mass vs. spin) is not tested, which may miss correlations.

## Compute Feasibility Analysis

- **Hardware**: GitHub Actions free-tier (multiple vCPU, ~7 GB RAM, ~14 GB disk).
- **Data Volume**:
 - GWTC-1/2: ~100 events $\times$ 1000 samples $\approx$ [deferred] rows (stored in HDF5).
 - Synthetic: ~100 events $\times$ 1000 samples $\approx$ [deferred] rows.
  - Total memory footprint for arrays: < 50 MB.
- **Compute**:
  - Bootstrapping: $O(B \times N \log N)$ where $B$ is the number of bootstrap iterations. Trivial for $N=100$.
  - Weighted KS Test: $O(N \log N)$; trivial.
  - Sensitivity Sweep: multiple iterations; negligible overhead.
- **Runtime**: Estimated < 30 minutes.
- **Dependencies**: `scipy`, `numpy`, `pandas`, `h5py` are CPU-optimized and standard. No GPU/CUDA required.

## Decision Rationale

**Why generate synthetic data instead of using a real simulation?**
The "Verified datasets" block explicitly lists no astrophysical simulation sources with the required schema. The only "COSMOS" URLs provided are for autonomous driving. Using a real but mismatched dataset (e.g., galaxy merger rates) would violate the scientific validity of the KS test (comparing distributions of incompatible variables). Generating a synthetic dataset based on a standard physical hypothesis (Power-law mass with independent spin) is the only methodologically sound approach to satisfy FR-002 and FR-005 while remaining within the constraints of the verified source list.

**Why not use IllustrisTNG?**
As stated in the Spec Assumptions, IllustrisTNG provides galaxy merger rates, not resolved binary black hole component masses/spins. Using it would be a "fatal, blocking flaw" (dataset-variable fit).

**Why event-level bootstrapping with posterior sampling instead of pooling posterior samples?**
Pooling posterior samples from the same event creates a dataset where samples are highly correlated, violating the i.i.d. assumption of the KS test. This inflates the effective sample size and biases the KS statistic (D) and p-value. Bootstrapping over events, where each iteration samples a new median from the posterior, preserves event-level independence and propagates measurement uncertainty into the test statistic.

**Why Inverse Probability Weighting (IPW) instead of uniform weighting?**
Gravitational wave detection probability is a strong function of mass and spin (more massive/spinning systems are louder). Applying uniform weights or ignoring selection bias when comparing to a synthetic population will result in a biased comparison where the synthetic population (if generated without selection effects) will appear to diverge significantly from the observed data simply due to the detector's sensitivity curve, not astrophysical differences. IPW corrects for this bias.

**Why a Weighted KS test?**
The standard KS test (`scipy.stats.ks_2samp`) assumes unweighted, i.i.d. samples. To incorporate IPW weights, a custom implementation or a library function that supports weighted samples (e.g., `weighted_ks_test`) is required. This ensures the selection bias correction is mathematically integrated into the test statistic.