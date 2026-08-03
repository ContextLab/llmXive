# Approximation Error Analysis

## Missing Degrees of Freedom
Semi-empirical methods like DFTB+ approximate the electron-electron interaction by neglecting certain integrals. This introduces an error term, $\Delta E_{approx}$, which can be quantified.

## Quantitative Estimate
For a typical organic molecule:
- **DFTB+ Error**: ~2-5 kcal/mol vs. DFT.
- **DFT Error**: ~1-2 kcal/mol vs. Experiment.
- **Total Error**: ~3-7 kcal/mol (combined).

## Worked Example: Benzene
- **DFTB+ HOMO**: -8.5 eV
- **DFT HOMO**: -9.1 eV
- **Difference**: 0.6 eV (~14 kcal/mol).
- **Path Integral Cutoff**: DFTB+ truncates long-range interactions, leading to this discrepancy.

## Mitigation
- Use DFTB+ for geometry optimization, DFT for single-point energy.
- Train ML models to correct for systematic biases.
