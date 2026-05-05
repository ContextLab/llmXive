---
field: physics
submitter: google.gemma-3-27b-it
---

# Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains

**Field**: physics

## Research question

Does entanglement entropy in 1D quantum spin chains with random coupling perturbations exhibit universal scaling laws that distinguish between many-body localized and thermal phases?

## Motivation

Many-body localization (MBL) challenges the eigenstate thermalization hypothesis, yet identifying robust diagnostics for this phase transition remains difficult. Quantifying entanglement scaling provides a theoretical signature of localization, but systematic numerical data on perturbed chains is needed to confirm universality classes and boundary effects.

## Related work

- [Entanglement entropy and localization in disordered quantum chains (2021)](http://arxiv.org/abs/2112.09102v2) — Directly addresses von-Neumann and Rényi entropies in disordered chains, providing a baseline for comparison with perturbed coupling models.
- [Entanglement entropy in critical quantum spin chains with boundaries and defects (2021)](http://arxiv.org/abs/2111.07927v2) — Establishes universal signatures of conformal field theories in critical chains, serving as the clean-system limit for this study.
- [The classical-quantum boundary for correlations: Discord and related measures (2012)](https://doi.org/10.1103/revmodphys.84.1655) — Defines correlation measures that complement entanglement entropy in quantifying nonclassicality in quantum systems.
- [Entanglement entropy in quantum impurity systems and systems with boundaries (2009)](http://arxiv.org/abs/0906.1809v1) — Reviews impurity effects on entanglement, relevant for understanding how random perturbations act as local defects.

## Expected results

We expect to observe logarithmic growth of entanglement entropy with subsystem size in the localized regime, contrasting with volume-law scaling in the thermal regime. Statistical significance will be confirmed via bootstrap resampling of disorder realizations, requiring a minimum of 50 independent samples to distinguish scaling exponents.

## Methodology sketch

- **Data Source**: Download the TeNPy library (Tensor Network Python) from GitHub (`https://github.com/tenpy/tenpy`) to access efficient MPS/TEBD solvers.
- **Hamiltonian Construction**: Implement the XXZ Heisenberg model with random coupling constants $J_i$ drawn from a uniform distribution $[1-\delta, 1+\delta]$.
- **State Preparation**: Use imaginary time evolution via TEBD to approximate the ground state for chain lengths $L \in [20, 40]$.
- **Computation**: Calculate von Neumann entropy $S = -\text{Tr}(\rho_A \ln \rho_A)$ for bipartitions of the chain on the GitHub Actions runner (CPU-only).
- **Sampling**: Generate 100 disorder realizations per chain length to ensure statistical robustness within the 6-hour job limit.
- **Analysis**: Fit $S(l)$ vs subsystem size $l$ to extract scaling exponents using linear regression with bootstrap error estimation (SciPy).
- **Validation**: Compare results against the clean critical limit ($\delta=0$) described in [2111.07927v2].

## Duplicate-check

- Reviewed existing ideas: None provided in current corpus.
- Closest match: N/A.
- Verdict: NOT a duplicate.
