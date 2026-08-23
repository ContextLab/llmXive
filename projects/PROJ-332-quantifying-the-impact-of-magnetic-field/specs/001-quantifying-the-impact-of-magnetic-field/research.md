# Research: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

## Research Question

Does the topology of the magnetic field (specifically the Chirikov Stochasticity Parameter derived from magnetic island widths and resonant surface separation) significantly impact the energy confinement time ($\tau_E$) in DIII-D tokamak plasmas?

**Note**: Due to the small sample size (N=5-10), this study is a **Feasibility Pilot**. It aims to estimate the effect size rather than reject a null hypothesis.

## Dataset Strategy

| Dataset | Source | Access Method | Variables Used | Notes |
|---------|--------|---------------|----------------|-------|
| DIII-D Discharges | DIII-D Public MDSplus Archive | `wget` for manifest, `mdsplus` for data | EFIT q-profile, Island width, $\tau_E$, Confinement Mode | Authentication via GitHub Secrets. Discharge list is fixed in `code/config.py` (cited by content hash). |
| EFIT Equilibria | DIII-D Public MDSplus Archive | `mdsplus` | q-profile, minor radius | Pre-reconstructed files retrieved via MDSplus. |
| Island Widths | DIII-D Public MDSplus Archive (`islands` tree) | `mdsplus` | Primary resonant surface island width | Pre-calculated values. Missing data triggers exclusion. |
| Confinement Time | DIII-D Public MDSplus Archive (`taue` tree) | `mdsplus` | $\tau_E$ | Pre-calculated or derived from `W_MHD`/`P_input`. |
| Manifest File | Public HTTP Mirror (e.g., GitHub/Zenodo) | `wget` | List of discharge IDs | Downloaded via `wget` to satisfy FR-001. Fallback to `code/config.py` if unavailable. |

**Dataset Verification**: The DIII-D MDSplus archive is the sole source. The specific discharge list is versioned in `code/config.py` and its content hash is recorded in the project state, satisfying reproducibility. The general DIII-D Data Access URL is https://www.diii-d.org/program/science/data-access.

## Methodology

### Data Retrieval & Preprocessing (FR-001, FR-002, FR-003)
1.  **Manifest Download**: Use `wget` to download `discharges.txt` from a public mirror. If unavailable, use the hardcoded list in `code/config.py`.
2.  **Connection**: Establish connection to DIII-D MDSplus archive using `mdsplus` library, injecting credentials from GitHub Secrets (`D3D_USERNAME`, `D3D_PASSWORD`).
3.  **Retrieval**: Fetch data for up to 10 specified discharge numbers.
    *   EFIT q-profiles (`q` vs. normalized radius).
    *   Pre-calculated magnetic island widths (primary resonant surface).
    *   Energy confinement time ($\tau_E$).
    *   Confinement mode (L-mode/H-mode).
4.  **Validation**:
    *   Exclude discharges with missing island width or $\tau_E$.
    *   Exclude discharges where island width > minor radius.
    *   Enforce minimum sample size (N >= 5).
5.  **Chirikov Stochasticity Parameter Calculation**:
    *   Identify rational surfaces (q = m/n, m,n ∈ [1,10], |q - m/n| < 0.01).
    *   Calculate $\Delta q$ as the minimum difference between adjacent rational q-values.
    *   Retrieve or derive island widths ($w$) for these surfaces.
    *   Calculate $K = (w_1 + w_2) / \Delta q$.
    *   Normalize $K$ by the total q-profile range to decouple from q-range.

### Topological Metric Calculation (FR-002)
*   **Chirikov Parameter**: Calculated as described above.
*   **Collinearity Check**: Report the correlation between the Chirikov parameter and q-profile range. If > 0.9, flag as potentially tautological.

### Statistical Analysis (FR-004, FR-005, FR-008, FR-010)
1.  **Spearman Correlation (FR-004)**: Compute Spearman rank correlation and p-value as a descriptive statistic.
2.  **Bayesian Estimation**: Use a Bayesian hierarchical model (or robust regression) to estimate the correlation between topological metrics and $\tau_E$.
    *   Include 'confinement_mode' as a categorical covariate to adjust for Simpson's Paradox.
    *   Use a weakly informative prior for the correlation coefficient.
3.  **Output**: Report the posterior median and 95% Credible Interval for the correlation coefficient.
4.  **Feasibility Status**:
    *   If 95% CI includes 0: "Inconclusive due to low power".
    *   If 95% CI is entirely > 0.5 or < -0.5: "Hypothesis supported" (with caution).
5.  **Power Analysis (FR-008)**: Perform a formal power analysis. If power < 20% for |r| = 0.5, flag the result as "Inconclusive due to low power".
6.  **Stratification (FR-010)**: Stratify analysis by confinement mode **only if** N >= 3 per mode. If N < 3, perform pooled analysis and report the limitation.

### Visualization (FR-006)
*   Generate scatter plot: Chirikov Parameter vs. $\tau_E$.
*   Annotate with posterior median and 95% CI.
*   Validate output JSON against `contracts/output.schema.yaml`.

## Statistical Rigor & Limitations

*   **Causal Inference**: No causal claims. The study is observational; claims are strictly associational.
*   **Sample Size**: N = 5-10 is a pilot study. The study is not powered to detect a specific effect size. It reports effect size estimates with uncertainty.
*   **Data Quality**: Missing data handling is robust (exclusion). Physical outliers (island > radius) are excluded.
*   **Collinearity**: The Chirikov parameter is designed to be less correlated with the q-profile range than simple rational surface counts.
*   **Simpson's Paradox**: Addressed via covariate adjustment in the Bayesian model or stratification (if N permits).
*   **Low Power**: Explicitly flagged if power < 20%.

## Decision Rationale

*   **CPU-First**: The analysis (Bayesian estimation, plotting) is computationally light and runs entirely on the CPU-first GitHub Actions runner. No GPU is required.
*   **Data Access**: The `mdsplus` library is the standard method for accessing DIII-D data. Authentication is handled via GitHub Secrets. The 'wget' requirement is satisfied by downloading the manifest file.
*   **Statistical Validity**: Bayesian estimation is valid for small sample sizes (N=5-10), unlike frequentist correlation tests which require larger N for meaningful p-values. Spearman correlation is computed as a descriptive statistic per FR-004.