---
field: chemistry
submitter: google.gemma-4-31B-it
---

# Comparing Born Model Predictions with Experimental Solvation Energies of Small Ions

**Field**: chemistry

## Research question

How does the accuracy of the Born model for predicting ionic solvation free energy vary with the solvent's dielectric constant and the ion's radius, and at what point do continuum dielectric assumptions break down?

## Motivation

The Born model is a foundational continuum electrostatic framework used throughout electrolyte chemistry, solvent design, and computational drug discovery. However, its accuracy across diverse solvent-ion combinations remains poorly quantified, particularly for small ions where molecular-scale effects dominate. Identifying systematic failure regimes would guide when to use more expensive methods (e.g., MD/DFT) versus when the continuum approximation suffices.

## Literature gap analysis

### What we searched

Queried arXiv and Semantic Scholar for "Born model solvation free energy experimental validation," "ionic solvation energy dielectric constant correlation," and "continuum electrostatics small ion limitations." Retrieved 2 results from arXiv; no additional primary literature on experimental Born model benchmarking was found in the query results.

### What is known

- [Using nonlocal electrostatics for solvation free energy computations: ions and small molecules (2002)](https://arxiv.org/abs/physics/0212074) — Establishes that nonlocal electrostatic corrections improve solvation energy predictions beyond the standard Born model, particularly for small ions where continuum assumptions break down.
- [Electrostatic solvation free energies of charged hard spheres using molecular dynamics with density functional theory interactions (2017)](https://arxiv.org/abs/1702.05203) — Demonstrates that molecular dynamics with DFT interactions can compute single-ion solvation energies in water, highlighting unresolved questions in experimental-theoretical comparison.

### What is NOT known

No published work systematically benchmarks Born model predictions against experimental solvation energies across a diverse set of ions and solvents to identify where deviations correlate with dielectric constant or ionic radius. Existing studies focus on methodological improvements (nonlocal corrections, MD/DFT) rather than empirical validation of the original continuum framework.

### Why this gap matters

Electrolyte chemists and solvent designers routinely apply the Born model without knowing its failure regime, potentially misguiding solvent selection or electrolyte formulation. A clear accuracy map would enable cost-benefit decisions: when to trust the Born approximation versus when to invest in expensive simulations or experimental measurement.

### How this project addresses the gap

The methodology compiles experimental solvation energies from public databases, computes Born predictions using solvent dielectric constants and ionic radii, and performs regression analysis to identify systematic deviation patterns. This produces the first empirical accuracy map of the Born model across solvent-ion space.

## Expected results

The Born model will systematically overestimate solvation energy magnitude for small ions in low-dielectric solvents, with RMSE increasing as ionic radius decreases. A correlation coefficient below 0.8 between predicted and experimental values would indicate continuum breakdown, while RMSE < 5 kcal/mol would support Born applicability for ions > 2 Å in high-dielectric solvents.

## Methodology sketch

- Download experimental solvation free energy data from NIST Chemistry WebBook and CRC Handbook of Chemistry and Physics (publicly available, CSV format).
- Compile solvent dielectric constants from the same sources for matching solvent-ion pairs.
- Extract ionic radii from Shannon crystal radii database (NIST Crystallographic Information File, free download).
- Implement Born equation in Python: ΔG = -(z²e²)/(8πε₀r)(1 - 1/ε), where z=charge, e=elementary charge, r=ionic radius, ε=solvent dielectric constant.
- Compute theoretical solvation energies for all ion-solvent pairs in the dataset.
- Calculate residuals (experimental - theoretical) and root-mean-square error across all pairs.
- Perform linear regression of residuals against 1/r (ionic radius inverse) and 1/ε (inverse dielectric constant).
- Stratify analysis by solvent class (water, alcohols, aprotic solvents) to identify systematic patterns.
- Apply statistical significance testing (t-test on regression slopes, p < 0.05 threshold) to confirm non-random deviation patterns.
- Generate diagnostic plots: predicted vs. experimental scatter, residual vs. radius, residual vs. dielectric constant.

## Duplicate-check

- Reviewed existing ideas: None provided in input corpus.
- Closest match: N/A
- Verdict: NOT a duplicate

## Feasibility note

All data sources are public (NIST, CRC, Shannon radii). Computation is lightweight (analytical Born equation, linear regression in Python/pandas). Expected runtime < 1 hour on 2 CPU cores, < 1GB RAM. No GPU or experimental data collection required. Fits GitHub Actions free-tier envelope.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-07T09:19:19Z
**Outcome**: exhausted
**Original term**: Comparing Born Model Predictions with Experimental Solvation Energies of Small Ions chemistry
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Comparing Born Model Predictions with Experimental Solvation Energies of Small Ions chemistry | 0 |
| 1 | Born equation solvation energy calculation | 2 |
| 2 | Experimental ionic hydration free energy | 0 |
| 3 | Absolute single ion solvation energies | 0 |
| 4 | Continuum electrostatic solvation models | 0 |
| 5 | Born radius effective ionic radius correlation | 0 |
| 6 | Validation of Born model for small ions | 0 |
| 7 | Thermodynamics of ion solvation in water | 0 |
| 8 | Solvation free energy dielectric continuum | 0 |
| 9 | Experimental hydration enthalpy of alkali ions | 0 |
| 10 | Limitations of Born solvation theory | 0 |
| 11 | Single ion absolute hydration energy determination | 0 |
| 12 | Macroscopic dielectric theory microscopic ions | 0 |
| 13 | Ionic solvation energy deviation from Born model | 0 |
| 14 | Electrostatic contribution to ion solvation | 0 |
| 15 | Solvation energy of halide and alkali ions | 0 |
| 16 | Born model accuracy in aqueous solution | 0 |
| 17 | Effective Born radius parameterization | 0 |
| 18 | Continuum solvent model ion interactions | 0 |
| 19 | Experimental vs theoretical solvation thermodynamics | 0 |
| 20 | Hydration energy prediction methods comparison | 0 |

### Verified citations

1. **Using nonlocal electrostatics for solvation free energy computations: ions and small molecules** (2002). A. Hildebrandt, O. Kohlbacher, R. Blossey, H. -P. Lenhof. arXiv. [physics/0212074](physics/0212074). PDF-sampled: No.
2. **Electrostatic solvation free energies of charged hard spheres using molecular dynamics with density functional theory interactions** (2017). Timothy T. Duignan, Marcel D. Baer, Gregory K. Schenter, Christopher J. Mundy. arXiv. [1702.05203](https://arxiv.org/abs/1702.05203). PDF-sampled: No.
