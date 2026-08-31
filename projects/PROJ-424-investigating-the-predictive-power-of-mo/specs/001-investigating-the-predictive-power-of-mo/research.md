# Research: Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients

## Scientific Background

Diffusion coefficients are critical transport properties in chemistry and biology, often estimated via Molecular Dynamics (MD) simulations. The accuracy of these estimates depends on simulation timescale, force field fidelity, and statistical sampling. Short simulations (–10 ns) may not reach the diffusive regime, leading to biased estimates. This project investigates the relationship between simulation duration and prediction accuracy for simple liquids.

**Critical Methodological Note**: Coarse-grained (CG) force fields like MARTINI systematically overestimate diffusion coefficients (typically by a significant factor) compared to all-atom simulations and experiments due to the smoothing of the energy landscape. Direct comparison of unscaled CG results to experimental values would conflate force field bias with timescale convergence. This project implements a **solvent-specific scaling correction** to isolate the timescale effect.

## Dataset Strategy

| Dataset | Purpose | Source | Verified URL | Access Method |
|---------|---------|--------|--------------|---------------|
| NIST Diffusion Coefficients | Experimental benchmarks (ground truth) for water, ethanol, acetone | NIST Chemistry WebBook | **NO VERIFIED SOURCE** (see note below) | Manual curation → `data/raw/nist_refs.json` with checksum. **Kickback**: FR-001 requires 'download and parse' which is impossible. |
| MARTINI Force Field | Coarse-grained parameters for solvents | Martini Force Field Initiative | https://cgmartini.nl/ | Download from official site; checksummed |
| GROMACS/LAMMPS | MD engine | GROMACS / LAMMPS | https://www.gromacs.org/ | Installed via CI package manager |

> **Critical Note on NIST Data**: The **Verified Datasets** block provided for this project contains NO verified URL for NIST diffusion coefficient data. The NIST Chemistry WebBook does not offer a public API for diffusion coefficients. Therefore, the plan **cannot** automate download as implied by FR-001.  
> **Mitigation**: The system will use a manually curated `data/raw/nist_refs.json` file containing the expected values (water: 2.3×10⁻⁹ m²/s, ethanol: 1.0×10⁻⁹ m²/s, acetone: 4.0×10⁻⁹ m²/s at 298K). This file will be checksummed and treated as the "verified" source. **Kickback**: FR-001 and Constitution Principle I require a spec update to accept manual curation as the canonical source.

## Methodology

### 1. Simulation Setup
- **Force Field**: MARTINI 3 (coarse-grained) to accelerate sampling.
- **System Size**: 500–1000 beads per solvent (reduced system).
- **Timescales**: 1 ns, 5 ns, 10 ns (targeted durations).
- **Temperature**: 298 K (matched to NIST references).
- **Equilibration**: 
  - 100 ps NVT + 100 ps NPT.
  - **Density Convergence Check**: Monitor density stability (±1%) over the first 200 ps of NPT. If not converged, extend equilibration or flag run as invalid. This prevents drift bias in the 1 ns trajectory.

### 2. Diffusion Coefficient Calculation & Scaling
- **MSD Extraction**: `MSD(t) = ⟨|r(t) - r(0)|²⟩` from trajectory.
- **Linear Regression**: Fit `MSD(t) = 6Dt + C` over the linear regime.
- **Validity Check**: Reject if $R^2 < 0.95$ (Constitution Principle VI). **Note**: Spec FR-008 requires 0.99, which is scientifically unsound for short trajectories and risks selection bias. **Kickback**: FR-008 requires update to 0.95.
- **Scaling Correction**: Apply solvent-specific scaling factors to predicted D values before error calculation:
  - Water: A controlled variable.
  - Ethanol:
  - Acetone: a specific concentration to be determined during the implementation phase.
  - *Rationale*: These factors are derived from literature validation of MARTINI 3 against all-atom/experimental data. This step ensures the MAE metric reflects timescale convergence, not force field bias.

### 3. Statistical Analysis
- **Bootstrap Resampling**: 1000 iterations (fallback 100) to estimate 95% CI for MAE.
- **Sensitivity Analysis**: Sweep regression start time ([deferred], [deferred], [deferred] of trajectory). **Kickback**: SC-003 requires explicit definition of these values.
- **Significance Test**: **Descriptive Trend Analysis**. Due to N=3 per group (one per solvent), a bootstrap difference-of-means test (p-value) is statistically unsound. The analysis will report the trend and CI overlap. **Kickback**: SC-005 requires removal of the p-value requirement.

## Decision Rationale

| Decision | Rationale | CPU vs GPU |
|----------|-----------|------------|
| MARTINI force field | Enables 10 ns simulations within 6-hour CI limit | CPU (feasible) |
| Reduced system size (500–1000 beads) | Minimizes computational cost while preserving diffusion physics | CPU (feasible) |
| Manual NIST curation | No programmatic source available; manual entry with checksum ensures reproducibility | N/A |
| Solvent-specific Scaling Factors | Corrects systematic MARTINI bias to isolate timescale effect | N/A |
| Bootstrap resampling (1000 iters) | Non-parametric CI robust to non-normal errors | CPU (feasible) |
| Sensitivity sweep (3 points) | Validates robustness without excessive cost | CPU (feasible) |
| Descriptive Trend Analysis | Statistically sound alternative to p-value test for N=3 | N/A |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| NIST data unavailable | High | Blocking | Manual curation; document values; kickback FR-001 |
| Simulation fails to equilibrate | Medium | High | Monitor density & R²; exclude invalid runs |
| Bootstrap exceeds 6-hour limit | Medium | Medium | Fallback to 100 iterations |
| MARTINI scaling inaccurate | Low | Medium | Cite scaling factor; note limitation |
| Statistical power low (N=3) | High | Medium | Use descriptive trend analysis; kickback SC-005 |

## References

- Marrink, S. J., et al. (2007). "The MARTINI Force Field: Coarse Grained Model for Biomolecular Simulations." *J. Phys. Chem. B*.
- NIST Chemistry WebBook: https://webbook.nist.gov/ (no API for diffusion data).
- GROMACS Documentation: https://manual.gromacs.org/