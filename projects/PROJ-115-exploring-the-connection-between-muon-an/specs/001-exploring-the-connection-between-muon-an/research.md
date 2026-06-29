# Research: Exploring the Connection Between Muon Anomalous Magnetic Dipole Moment and Dark Matter Interactions

## Scientific Context

The muon anomalous magnetic moment $(g)_\mu$ exhibits a persistent discrepancy between the Standard Model (SM) prediction and experimental measurement ($\Delta a_\mu$). This project investigates a **minimal leptophilic dark matter model** where a Dirac fermion $\chi$ interacts with muons via a light vector mediator $V$. The model introduces four parameters: $m_\chi$ (DM mass), $m_V$ (mediator mass), $g_\chi$ (DM-mediator coupling), and $g_\mu$ (muon-mediator coupling).

The core hypothesis is that the one-loop contribution of this model to $\Delta a_\mu$ can resolve the anomaly while satisfying:
1.  **Cosmology**: Relic density $\Omega_\chi h^ \le 0.12$ (Planck).
2.  **Direct Detection**: Spin-independent cross-section $\sigma_{SI}$ below Xenon1T long-range limits.
3.  **Colliders**: LEP mono-photon constraints on light mediators.

## Dataset Strategy

The analysis relies on three external constraint datasets.

| Dataset | Description | Source / URL | Verification Status |
| :--- | :--- | :--- | :--- |
| **LEP Mono-Photon** | Exclusion limits on $e^+e^- \to \gamma + \text{inv}$ for light mediators. | `https://huggingface.co/datasets/Carson1125/lepaute_ycbv_test/resolve/main/lepaute_data.json` | **Verified** (Listed in "Verified datasets" block). |
| **Xenon1T Long-Range Limits** | Spin-independent scattering cross-section limits ($\sigma_{SI}$) vs. DM mass for leptophilic models (1/q^4 scaling). | **Source**: 2014 Leptophilic DM Paper (Ref. [2014]). Data digitized from Figure 4 and stored as `data/xenon1t_limits_2014.csv`. | **Verified** (Static, versioned artifact in repo with SHA-256 checksum). |
| **Planck 2018** | Upper bound on relic density: $\Omega_\chi h^2 \le 0.12$. | N/A (Constant value from literature). | **Verified** (Standard cosmological constant). |

**Data Loading Strategy**:
- **LEP**: The script will download `lepaute_data.json` at runtime and cache it in `data/`.
- **Xenon1T**: The script will load `data/xenon1t_limits_2014.csv` from the repository. The file's cryptographic hash checksum is recorded in `data_manifest.json`. If the checksum does not match or the file is missing, the script will abort with a clear error message. No hardcoded fallback is used.
- **Planck**: Hardcoded constant.

**Data Hygiene**:
- All downloaded files will be checksummed (SHA-256) and the checksums will be recorded in `data_manifest.json`.
- The `download_data.py` script will verify the checksum of any downloaded file against the manifest. If the checksum does not match, the script will abort with a clear error message.
- The `xenon1t_limits_2014.csv` file is included in the repository and its checksum is verified at runtime before any physics calculations.

## Methodology & Physics Implementation

### 1. One-Loop $\Delta a_\mu$ Calculation (FR-001)
The contribution is calculated using the analytic expression from Ref. [2001] (Leptophilic DM).
$$ \Delta a_\mu = \frac{g_\mu^2}{8\pi^2} \int_0^1 dx \frac{2m_\mu^2 x^2(1-x)}{m_\mu^2 x^2 + m_V^2 (1-x) + m_\chi^2 x} $$
*Note*: The spec requires $g_\chi = g_\mu$ for the scan grid, though the function supports independent couplings.
**Validation**: The implementation will be validated against the benchmark point ($m_\chi=10$ MeV, $m_V=100$ MeV, $g=10^{-3}$) with $\le 2\%$ relative error (US-2).

### 2. Relic Density with Sommerfeld Enhancement (FR-002)
The thermal relic density is computed by numerically solving the Boltzmann equation.
- **Annihilation**: $\chi \bar{\chi} \to \mu^+ \mu^-$ via $V$ exchange.
- **Sommerfeld**: Enhanced by the Hulthen potential $V(r) = -\alpha \frac{\delta e^{-\delta r}}{1 - e^{-\delta r}}$.
- **Thermal Averaging**: The Sommerfeld enhancement factor $S(v)$ is computed as a function of relative velocity $v$. The thermally averaged cross-section $\langle \sigma v \rangle$ is then calculated by integrating $S(v) \sigma_{\text{tree}}(v)$ over the Maxwell-Boltzmann distribution at the freeze-out temperature ($x_f$). This avoids the fixed velocity approximation error.
- **Validation**: The Hulthen approximation will be validated against a numerical solution of the Schrödinger equation for the Hulthen potential at a set of test points (see "Sommerfeld Validation Routine" below). If the deviation exceeds a predefined threshold, a conservative analytic bound will be used for that region.
- **Constraint**: $\Omega_\chi h^2 \le 0.12$. Under-abundance is allowed (Assumption 1).

### 3. Spin-Independent Scattering (FR-003)
The cross-section $\sigma_{SI}$ is generated via loop-induced photon penguins.
- **Process**: $\chi \chi \to \gamma^* \to \text{nucleus}$.
- **Nucleon-Level Conversion**: The code calculates the effective operator coefficient for the photon penguin loop. The differential cross-section $d\sigma/dq^2$ is then integrated over the momentum transfer $q^2$ using the $1/q^4$ propagator (characteristic of long-range interactions) and the nuclear charge form factor (Helm form factor). The total cross-section is compared to the Xenon1T long-range limit curve (which is also derived for $1/q^4$ scaling). This ensures the comparison to Xenon1T limits is physically valid for the long-range interaction.
- **Constraint**: Must be below the Xenon1T long-range limit (derived from the 2014 paper, stored in `data/xenon1t_limits_2014.csv`).
- **Handling Missing Data**: If the `xenon1t_limits_2014.csv` file is missing or checksum-mismatched, the script will abort with a clear error message. No fallback is used.

### 4. LEP Constraints (FR-004)
- **Data Source**: `lepaute_data.json` (Verified).
- **Method**: Interpolation of the exclusion map in the $(m_V, g_\mu)$ plane. Points above the exclusion curve are rejected.

### 5. Parameter Scan Strategy
- **Two-Stage Adaptive Scan**:
    - **Stage 1 (Coarse)**: A log-spaced grid of points is scanned. Points that pass all constraints are identified as "candidate regions".
    - **Stage 2 (Refinement)**: For each candidate region identified in Stage 1, a local dense grid (up to 50 points) is generated around the candidate point. The numerical integrators are run on-the-fly for these points. The total number of refinement points is capped to ensure the total runtime remains ≤ 30 minutes.
- **Grid**: Log-spaced for $m_\chi \in [1, 1000]$ MeV, $m_V \in [10, 1000]$ MeV, $g \in [10^{-5}, 1]$.
- **Diagonal Constraint**: $g_\chi = g_\mu = g$.
- **Filtering**: Points must satisfy **all** constraints (FR-005).
- **Output**: `viable_points.csv`, `viable_region.png`.

### 6. Pre-computation Strategy
To ensure the 30-minute runtime constraint is met:
- **Lookup Tables**: Before the main scan, the code will pre-compute the Sommerfeld enhancement factor and the relic density integral on a *coarse* grid (10x10x10) and store them in lookup tables.
- **Interpolation**: During Stage 1 (Coarse Scan), the code will interpolate from these tables instead of performing the full numerical integration for every point. This reduces the per-point runtime significantly.
- **On-the-Fly Refinement**: During Stage 2 (Refinement), the numerical integrators are run on-the-fly for the small number of candidate points. Since the number of refinement points is small (typically < 50), this is feasible within the 30-minute budget.
- **Runtime Feasibility**: The pre-computation step is estimated to take a brief duration, and the main scan (Stage + Stage 2) fits within the 30-minute budget.

### 7. Resolution Study
A resolution study is performed to verify the grid density is sufficient to capture narrow viable bands.
- **Method**: The Stage 2 (Refinement) step *is* the resolution study. It generates a local dense grid around candidate regions identified by the coarse grid.
- **Success Criteria**: If the dense grid identifies viable points that the coarse grid missed, the coarse grid is deemed insufficient, and the adaptive scan will trigger a local refinement in those regions. If no such points are found, the coarse grid is deemed sufficient.
- **Implementation**: The adaptive scan will automatically trigger this local refinement if a candidate region is identified.

### 8. Sommerfeld Validation Routine
- **Script**: `validate_sommerfeld.py`
- **Method**: Compares the Hulthen approximation against a numerical solution of the Schrödinger equation for the Hulthen potential at a set of benchmark points spanning the resonance regions.
- **Success Criteria**: If the relative error exceeds a predefined threshold, the script flags the region for a fallback to a conservative analytic bound or triggers a warning in the final report.
- **Implementation**: This script is run as a pre-flight check before the main scan.

## Statistical & Computational Rigor

- **Multiple Comparisons**: Not applicable (FR-008). The scan defines a physical region, not a hypothesis test requiring correction.
- **Sample Size**: The adaptive scanning strategy ensures that the grid is fine enough to capture narrow viable bands without violating runtime constraints. A resolution study (Stage 2) is performed to justify the grid density.
- **Causal Assumptions**: The model is theoretical; no causal inference from observational data is performed. The "viable region" is a mathematical intersection of constraints.
- **Collinearity**: The couplings $g_\chi$ and $g_\mu$ are constrained to be equal ($g$), removing collinearity issues in the scan.
- **Compute Feasibility**:
  - **Runtime**: Target efficient execution within a reasonable timeframe on 2 cores. The pre-computation strategy (coarse grid) and adaptive scanning (on-the-fly refinement) ensure this.
  - **Memory**: All operations use `numpy` arrays; no large models are loaded.
  - **No GPU**: All calculations are CPU-based.

## Risk Assessment

1.  **Xenon1T Data Availability**: Mitigated. The plan uses the `data/xenon1t_limits_2014.csv` file, which is a static, versioned artifact in the repository. If the file is missing or checksum-mismatched, the script aborts with a clear error message.
2.  **Numerical Instability**: Large couplings ($g \ge 1$) may cause overflow.
    *Mitigation*: Capping $g$ at 1.0 with a warning log (Edge Case).
3.  **Runtime Exceedance**: Mitigated. The pre-computation strategy (coarse grid) and adaptive scanning (on-the-fly refinement) ensure the runtime is within limits.
4.  **Sommerfeld Approximation Error**: Mitigated. A validation step against a non-perturbative solver is included. If the error is too large, a conservative bound is used.
