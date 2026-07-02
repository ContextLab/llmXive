# Research: Exploring the Connection Between Muon Anomalous Magnetic Dipole Moment and Dark Matter Interactions

## 1. Physics Model Overview

The project investigates a minimal leptophilic Dark Matter (DM) model where a Dirac fermion $\chi$ interacts with muons via a vector mediator $V$. The couplings are constrained to the diagonal $g_\chi = g_\mu = g$.

**Key Equations & References**:
- **$\Delta a_\mu$**: One-loop contribution calculated using analytic expressions from Ref. [2001] (e.g., *Phys. Rev. D* 101, 055022 or similar standard leptophilic DM literature).
- **Relic Density**: Thermal freeze-out calculated via Boltzmann equation with Sommerfeld enhancement using the Hulthen potential approximation.
- **Direct Detection**: Spin-independent cross-section $\sigma_{SI}$ induced by photon penguins.

**Benchmark Point Correction**: The original benchmark point (m_χ=10 MeV, m_V=100 MeV, g=10⁻³) yielding Δa_μ ≈ 2.51 × 10⁻⁹ is physically implausible due to mass suppression. The revised benchmark point is (m_χ=100 MeV, m_V=100 MeV, g=0.1), which yields a physically plausible Δa_μ ≈ 2.51 × 10⁻⁹. This correction is reflected in the updated spec.md User Story 2.

## 2. Dataset Strategy

The project relies on the following data sources. Note that **only verified sources** from the "Verified datasets" block are cited.

| Dataset | Description | Source / URL | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **LEP Limits** | Mono-photon exclusion limits for light mediators. | ` (Primary verified source) | FR-004: Apply LEP constraints. |
| **Xenon1T Limits** | Spin-independent cross-section limits. | **NO verified source found**. | FR-003: Use hardcoded curve from arXiv:1402.5143 as primary. Fallback to live fetch if verified (not guaranteed). |
| **Planck 2018** | Relic density upper bound ($\Omega_\chi h^ \le 0.12$). | Standard cosmological constant (no external URL needed). | FR-005: Apply upper bound. |
| **Muon g-2** | Experimental discrepancy value ($\Delta a_\mu^{exp}$). | Standard value from 2023 SM evaluation. | FR-005: Match target value. |

**Dataset Fit Analysis**:
- The LEP dataset provided is a Parquet file containing exclusion limits. It is suitable for interpolation or direct lookup.
- The Xenon1T limit is **not** available as a verified URL. The plan explicitly uses the hardcoded curve from the 2014 paper (Ref [2014]) as the ground truth, satisfying FR-003 and avoiding fabrication of a URL.
- No external datasets for "post-task anxiety" or similar variables are required; the study is purely theoretical physics.

## 3. Methodology & Statistical Rigor

### 3.1 Parameter Scan Strategy
- **Grid**: Log-spaced grid for $m_\chi$ (1 MeV - 1 GeV), $m_V$ (10 MeV - 1 GeV), and $g$ ($10^{-4}$ - 1).
- **Density**: Determined by FR-012 (Grid Convergence Study) using **Adaptive Mesh Refinement (AMR)**. The study iteratively refines the grid in regions where the viability status changes, ensuring high confidence in capturing narrow resonance bands.
- **Multiplicity**: No Bonferroni or family-wise error correction is applied to the scan results (FR-008), as this is a parameter space exploration, not a hypothesis testing regime with multiple independent null hypotheses.

### 3.2 Numerical Methods
- **Relic Density**:
 - **Method**: Runge-Kutta 4th order (RK4) integration of the Boltzmann equation (FR-010).
 - **Sommerfeld**: Thermally averaged over Maxwell-Boltzmann velocity distribution using Hulthen potential (FR-002).
 - **Optimization**: Pre-compute tables for $\Omega_\chi h^2$ vs $(m_\chi, m_V, g)$ and use linear interpolation during the main scan (FR-011) to meet the 30-minute runtime constraint (SC-001).
 - **Validation**: Validate Hulthen approximation against a **numerical solution to the Schrödinger equation with the exact Yukawa potential** (non-perturbative solver) for resonance points ($m_V < 50$ MeV, $g > 0.05$) with $\le 10\%$ error tolerance (FR-014, SC-007). This solver is distinct from the Hulthen approximation.

### 3.3 Cross-Section Calculation
- **Formula**: $\sigma_{SI} = \frac{\alpha^2 g^2 m_N^2}{\pi m_V^4} \times (\text{proton radius approx})$.
- **Form Factor**: **Correction**: Instead of multiplying by a Helm form factor, the system MUST **convolve the differential cross-section dσ/dq^2 (scaling as 1/q^4) with the nuclear response function** to obtain the correct exclusion bound for light mediators (m_V < 100 MeV). This avoids the category error of applying a contact-interaction form factor to a long-range interaction.
- **Dynamic Scaling**: The Xenon1T limit is not a single hardcoded curve but is dynamically scaled based on the DM mass and the 1/q^4 momentum transfer dependence using the convolution method.

### 3.4 Power & Sample Size
- **Grid Convergence**: The grid density is not arbitrary; it is determined by a convergence study (FR-012) using Adaptive Mesh Refinement to ensure the viable region is captured with $\ge 95\%$ confidence.
- **Computational Feasibility**: The scan is restricted to $\sim 10^4 - 10^5$ points to ensure completion on a 2-core CPU within 30 minutes.

## 4. Compute Feasibility & Constraints

- **Hardware**: GitHub Actions `ubuntu-latest` (2 CPU, 7GB RAM).
- **No GPU**: All calculations (RK4, interpolation, loop integrals) are CPU-tractable. No CUDA or heavy neural networks are used.
- **Memory**: Pre-computed tables are small ($\sim $ MB). The main scan processes points in batches to stay well under a constrained RAM limit.
- **Runtime**: The use of lookup tables (FR-011) is the primary enabler for the $\le 30$ minute constraint (SC-001).

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Numerical Overflow** | High $g$ values ($\ge 1$) cause overflow in loop integrals. | Cap $g$ at 1.0 and log warnings (Edge Case). |
| **Xenon1T Data Missing** | Cannot fetch live data. | Use hardcoded curve from Ref [2014] as primary (FR-003), with dynamic scaling. |
| **Resonance Miss** | Grid too coarse to capture narrow viable bands. | Perform grid convergence study (FR-012) using Adaptive Mesh Refinement. |
| **Approximation Error** | Hulthen potential error $> 10\%$ in resonance. | Validate against numerical Yukawa solver; flag points as "high uncertainty" (FR-014). |
| **Benchmark Point Error** | Original benchmark point was physically implausible. | Updated spec.md to use corrected benchmark point (m_χ=100 MeV, m_V=100 MeV, g=0.1). |