# Research: Constraining Lorentz Invariance Violation with Fermi Gamma‑Ray Burst Spectra

## Research Question

Can spectral lag measurements from the brightest Fermi-GBM Gamma-Ray Bursts (GRBs) provide a competitive upper bound on the linear Lorentz Invariance Violation (LIV) energy scale ($E_{\rm QG}$), and how robust is this bound against intrinsic source variability and systematic binning effects?

## Literature Context & Methodology

### Theoretical Framework
The standard model of particle physics and general relativity assume Lorentz Invariance (LI). However, some quantum gravity (QG) theories predict a energy-dependent speed of light, leading to a dispersion relation:
$$ v(E) \approx c \left( 1 - \xi \frac{E}{E_{\rm QG}} \right) $$
where $E$ is the photon energy, $E_{\rm QG}$ is the quantum gravity energy scale, and $\xi = \pm 1$ for subluminal/superluminal propagation. For a source at redshift $z$, the time delay $\Delta t$ between photons of energies $E_{\rm high}$ and $E_{\rm low}$ is:
$$ \Delta t_{\rm LIV} = \frac{E_{\rm high} - E_{\rm low}}{E_{\rm QG}} \frac{D(z)}{c} $$
where $D(z)$ is the cosmological distance (comoving distance).

### Existing Constraints
Current limits from Fermi-GBM and LAT (e.g., GRB 090510) typically constrain $E_{\rm QG} > 10^{19}$ GeV for linear LIV. This project aims to refine these bounds using a population-based approach to average out intrinsic source lags.

### Methodology Summary
1.  **Data Ingestion**: Download the **full Fermi GBM Trigger Catalog** via the HEASARC VOTable API (`https://heasarc.gsfc.nasa.gov/cgi-bin/Tools/xTable/xTable.pl?Table=fermi/gbm/triggers`). Filter locally for the top 30 events by **Total Fluence (50-300 keV)**.
2.  **Preprocessing**: Re-bin into low-energy, intermediate, and high-energy bands. Subtract background.
3.  **Lag Measurement**: Compute Cross-Correlation Function (CCF) between 8–50 keV and 200–1000 keV. Identify lag at CCF peak. Estimate uncertainty via bootstrap with a sufficiently large number of resamples.
4.  **Regression**: Fit a **Hierarchical Bayesian Model** where $\Delta t_{\rm obs} = \beta \cdot D(z) + \alpha_i + \epsilon$. $\alpha_i$ (intrinsic lag) is modeled as a random effect with a population distribution $\mathcal{N}(\mu_{\alpha}, \sigma_{\alpha}^2)$. This allows marginalization over intrinsic lag uncertainty and tests for correlation between intrinsic lag and redshift.
5.  **Validation**: Generate 10,000 synthetic datasets by **shuffling photon energy labels** (preserving time structure) to build a null distribution for the **global LIV slope**. Verify the observed limit is not a statistical fluke.

## Dataset Strategy

### Primary Data Source: Fermi-GBM Light Curves
**Status**: The spec requires data from the "Fermi Science Support Center".
**Verified Source**: The **Fermi GBM Trigger Catalog** hosted at HEASARC.
**Strategy**:
1.  **Catalog Retrieval**: The implementation will use the `astroquery` library or direct HTTP requests to the HEASARC VOTable endpoint: `https://heasarc.gsfc.nasa.gov/cgi-bin/Tools/xTable/xTable.pl?Table=fermi/gbm/triggers`. This endpoint returns the full catalog as a VOTable.
2.  **Selection**: The script will sort the full catalog by the column `Total Fluence (50-300 keV)` and select the top 30 events. This ensures a deterministic, reproducible selection based on the primary source.
3.  **Download**: For each selected GRB, download the corresponding light curve files (typically `.fits` or `.csv` time-series) from the FSSC using the GRB ID.
    *   *Note*: The selection is dynamic: the full catalog is retrieved, sorted by fluence, and the top 30 are selected. This ensures reproducibility against the primary source.
4.  **Fallback**: If a direct programmatic download of the "top 30" list fails, the system will download the full trigger catalog and filter locally.

### Redshift Data
**Status**: Redshifts are not provided in the light curve files.
**Strategy**:
1.  Cross-reference GRB IDs with the "Fermi GBM Trigger Catalog" (which often includes redshift if known) or the "GCN Circulars" database.
2.  **Strict Exclusion**: As per Spec Edge Cases, any GRB without a known redshift is excluded from the LIV calculation. No imputation.

### Data Feasibility Assessment
*   **Volume**: Light curves for a set of GRBs are small (MB scale). A large number of synthetic datasets for the global statistic are generated in memory. Total memory usage is well within the specified limit.
*   **Compute**: CCF and bootstrap are CPU-intensive but scalable. A substantial number of global null iterations will be performed alongside 30 bursts $\times$ 1000 bootstraps. On a multi-core CPU, this fits comfortably within the established time limit.
*   **Risk**: The primary risk is the availability of redshifts. If < 10 bursts have redshifts, the global regression may be underpowered. The plan must handle this gracefully.

## Statistical Rigor & Methodology Checks

* **Multiple Comparisons**: The analysis focuses on a single global parameter ($E_{QG}$ slope). The null distribution ([deferred] global iterations) effectively controls the family-wise error rate for the global limit.
*   **Power/Sample Size**: The sample size is fixed by the "brightest" selection. The Hierarchical Bayesian model accounts for the uncertainty in the population distribution of intrinsic lags, improving power compared to simple regression.
*   **Causal Inference**: The study is observational. Claims are framed as "constraints on $E_{QG}$ assuming the dispersion relation holds," not causal proof of LIV. The Hierarchical model explicitly controls for intrinsic lags and tests for correlation between intrinsic lag and redshift.
*   **Measurement Validity**: CCF is the standard method for spectral lag. Bootstrap is the standard for uncertainty.
*   **Collinearity**: The regression uses $D(z)$ (distance) and $\Delta E$ (energy difference). The Hierarchical model includes a test for correlation between intrinsic lag and redshift to prevent confounding.

## Confound Control

*   **Intrinsic Lag vs. Redshift**: The Hierarchical Bayesian model includes a term to test for correlation between intrinsic lag (random intercept) and redshift. If a significant correlation is found, the model will include a redshift-dependent term for the intrinsic lag, preventing bias in the LIV slope.
*   **Energy Dependence**: The model explicitly uses $\Delta E$ as a predictor, ensuring the LIV slope is not confounded by energy-dependent intrinsic effects.
*   **Null Hypothesis Validity**: The null test uses **energy label shuffling**. This preserves the intrinsic temporal structure (and thus the intrinsic lag distribution) while randomizing the energy-dependent LIV term. This correctly simulates the null hypothesis of "LIV = 0" in the presence of intrinsic lags, unlike time-shifting which destroys intrinsic correlations.

## Compute Feasibility (CPU-First)

*   **Method**: Pure Python/NumPy/SciPy/PyMC. No GPU required.
*   **Scaling**:
    *   **CCF**: $O(N \log N)$ using FFT. Fast.
    *   **Bootstrap**: Parallelizable across bursts.
    *   **Null Test**: A large number of iterations are performed on the **global statistic** (resampling the set of lags). This is computationally efficient and fits within the 6-hour limit.
*   **Memory**: Streaming is not strictly necessary for the raw data (small), but the synthetic data generation will be done in batches to avoid memory spikes.
*   **GPU Escape Hatch**: Not required. If the CPU time exceeds a predefined threshold, the plan is to reduce the number of MCMC samples or null iterations and document the trade-off.

## Open Questions & Risks

1.  **Data Access**: The "top 30" list is derived dynamically. The script must query the HEASARC VOTable API or download the full catalog.
2.  **Redshift Availability**: If < 10 bursts have redshifts, the global regression may be underpowered. The plan must handle this gracefully (e.g., "Insufficient data for population analysis").
3.  **Background Subtraction**: The spec requires "standard GBM offline tools." The implementation will use a simplified background model (pre-burst interval) if the full offline tools are not available as a Python library, but will document this approximation.