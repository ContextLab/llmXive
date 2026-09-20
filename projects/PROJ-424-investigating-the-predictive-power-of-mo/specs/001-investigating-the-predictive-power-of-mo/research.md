# Research: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Summary
This research validates the accuracy of MARTINI force field simulations in predicting self-diffusion coefficients ($D$) for water, ethanol, and acetone. It addresses the critical need to determine the minimum simulation duration required for convergence (1ns vs 5ns vs 10ns). The study uses a rigorous statistical framework (bootstrapping) to estimate uncertainty but explicitly avoids p-value testing due to limited sample sizes (N=5 per condition, or N=3 fallback), adhering to the "Descriptive Trend Analysis" and "CI Overlap Check" requirements.

## Dataset Strategy

The study relies on two primary data sources:

1.  **Experimental Benchmarks (Ground Truth)**:
    *   **Source**: Manually curated values from NIST Standard Reference Database.
    *   **Location**: `data/raw/nist_refs.json`.
    *   **Rationale**: NIST does not provide a programmatic API for this specific subset of diffusion data. Manual curation ensures accuracy and allows for checksumming (Constitution Principle III).
    *   **Variables**: Solvent name, Temperature (K), Experimental Diffusion Coefficient ($m^2/s$).
    *   **Verification**: Values cross-referenced with NIST TRC (Thermodynamics Research Center) data.

2.  **Simulation Trajectories**:
    *   **Source**: Generated in-situ using GROMACS with MARTINI force field.
    *   **Location**: `data/raw/simulations/` (generated) or `data/processed/` (analyzed).
    *   **Rationale**: MARTINI is a coarse-grained force field that accelerates sampling, allowing 10ns simulations to complete within the 6-hour CI budget on CPU (with N=5 or N=3 seeds).
    *   **Variables**: Time (ps), Mean Squared Displacement ($Å^2$), Coordinates.
    *   **Sample Size**: 5 independent seeds per solvent/duration condition (Total N=45). Fallback to N=3 seeds (Total N=27) if time > 5.5h.

### Dataset Strategy Table

| Dataset | Source URL / Path | Access Method | Validation |
| :--- | :--- | :--- | :--- |
| **Experimental Refs** | `data/raw/nist_refs.json` (Local) | `json.load()` | Checksum verification; Manual spot-check against NIST TRC. |
| **Trajectories** | `data/raw/simulations/*.xtc` (Local) | `mdtraj.load()` | GROMACS energy check; MSD linearity ($R^2 \ge 0.95$) on t > 100ps. |

*Note: The "Verified datasets" block in the prompt contains NIST 800-53 security control data, which is irrelevant to this chemistry study. We strictly use the local curated JSON file as defined in the Spec and Constitution.*

## Methodological Approach

### 1. Simulation Protocol
*   **Force Field**: MARTINI 3.0 (validated for transport properties).
*   **System Size**: ~200-500 molecules per box to ensure periodic boundary conditions do not artificially restrict diffusion (finite-size correction applied if necessary).
*   **Durations**: 1 ns, 5 ns, 10 ns.
*   **Ensemble**: NPT (300K, 1 bar).
*   **Seeds**: 5 independent random seeds per condition (Total N=45). Fallback to 3 seeds if time > 5.5h.
*   **Convergence Check**: The Mean Squared Displacement (MSD) is calculated. **The first 100ps of every trajectory is discarded** to avoid the ballistic regime. A linear fit is performed on the MSD vs. time plot for t > 100ps. **Only trajectories with $R^2 \ge 0.95$** (per SC-008 and Constitution Principle VI) are accepted for $D$ calculation.

### 2. Statistical Analysis
*   **Metric**: Mean Absolute Error (MAE) between $D_{sim}$ and $D_{exp}$.
*   **Uncertainty**: 95% Confidence Intervals via Bootstrap Resampling.
    *   **Iterations**: 1000 (FR-004).
    *   **Fallback**: If wall-clock time > 5.5 hours, reduce to 100 iterations (FR-004).
*   **Hypothesis Testing**: **None**. The study does NOT perform difference-of-means tests (t-tests) due to N=5 (or N=3) sample size (SC-005).
*   **Trend Analysis**:
    *   Plot MAE vs. Duration.
    *   **CI Overlap Check**: Compare the 95% CI of the 1ns MAE against the 10ns MAE. **This is a descriptive metric only.** Non-overlapping CIs suggest a potential improvement, but no statistical significance is claimed due to the small sample size.

### 3. Sensitivity Analysis
*   **Variable**: Start time fraction for MSD calculation (0.1, 0.2, 0.3 of total duration).
*   **Goal**: Ensure variance in $D$ values < 5% across start times (SC-002).

## Scaling Factors

MARTINI diffusion coefficients are known to be faster than reality. To enable valid comparison with experimental data, we apply fixed scaling factors derived from literature (Marrink et al., J. Chem. Theory Comput. 2007, 3, 1, 146–156):

*   **Water**: 0.6
*   **Ethanol**: 0.7
*   **Acetone**: 0.7

These factors are hardcoded constants in the analysis pipeline and are not fitted to the current simulation data, avoiding circularity.

## Decision Rationale

*   **CPU-First**: MARTINI simulations of small liquids (water, ethanol, acetone) are computationally cheap. A ns simulation of ~500 particles runs in ~10-15 minutes on 2 CPU cores (including equilibration). This fits within the 6-hour CI limit if N=3 seeds are used, or with a fallback if N=5.
*   **No GPU Required**: The coarse-grained nature of MARTINI reduces the degrees of freedom, making GPU acceleration unnecessary for this specific scale.
*   **Bootstrap vs. T-Test**: With N=5 (or N=3) data points per duration, a t-test is statistically underpowered. Bootstrap resampling on the *error distribution* (MAE) is a more robust non-parametric approach for estimating confidence intervals of the aggregate error metric.
*   **Manual Curation**: Given the lack of an NIST API, manual curation is the only way to ensure the "Verified Accuracy" principle is met without fabricating a fake API endpoint.
*   **Lag-Time Exclusion**: Discarding the first 100ps is critical to avoid the ballistic regime, which would invalidate the linear fit and the resulting diffusion coefficient.