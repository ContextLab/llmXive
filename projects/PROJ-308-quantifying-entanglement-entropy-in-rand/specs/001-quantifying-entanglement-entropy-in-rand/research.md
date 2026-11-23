# Research: Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains

## 1. Introduction and Motivation

The study of entanglement entropy in one-dimensional quantum many-body systems has revealed profound connections between quantum information theory, statistical mechanics, and conformal field theory. In clean, critical systems described by conformal field theory (CFT), the entanglement entropy $S(L)$ of a subsystem of length $L$ scales logarithmically with $L$:
$$ S(L) \approx \frac{c}{3} \log L + \text{const} $$
where $c$ is the central charge of the CFT.

However, the introduction of disorder fundamentally alters this scaling behavior. This research project investigates the scaling laws of entanglement entropy in randomly perturbed XXZ Heisenberg spin chains, specifically focusing on the transition between critical and many-body localized (MBL) regimes.

## 2. Scaling Ansatz

Based on the theoretical framework established by Refael and Moore (Phys. Rev. Lett. 93, 207204 (2004)), we propose the following scaling ansatz for the entanglement entropy $S(L)$ in random spin chains:

### Critical Regime (Weak Disorder)
In the critical regime, the entanglement entropy follows a logarithmic scaling law:
$$ S(L) \approx \frac{c_{\text{eff}}}{3} \log L + \text{const} $$
where $c_{\text{eff}}$ is an effective central charge. For the random singlet phase, Refael and Moore predicted $c_{\text{eff}} = \ln 2 \approx 0.693$, leading to:
$$ S(L) \approx \frac{\ln 2}{3} \log L + \text{const} $$

### Localized Regime (Strong Disorder)
In the many-body localized regime, the system obeys an area law:
$$ S(L) \approx \text{const} $$
with possible sub-logarithmic corrections. This implies that the entanglement entropy saturates to a constant value independent of subsystem size for sufficiently large $L$.

### Generalized Scaling Form
We propose a generalized power-law scaling form to distinguish between regimes:
$$ S(L) \propto L^{\alpha} $$
where the exponent $\alpha$ serves as an indicator of the phase:
- $\alpha \approx 0$: Area law (localized regime)
- $\alpha > 0$ (specifically $\alpha \approx 0$ in log-log space, corresponding to logarithmic growth): Critical regime

## 3. Hypothesis

**Hypothesis:** The entanglement entropy $S(L)$ of a randomly perturbed XXZ spin chain exhibits a universal scaling behavior characterized by the exponent $\alpha$ in the relation $S(L) \propto L^{\alpha}$:
- In the localized regime (high disorder strength $\delta$), $\alpha \approx 0$, indicating an area law.
- In the critical regime (low disorder strength $\delta$), the system exhibits logarithmic scaling $S(L) \propto \log L$, which corresponds to an effective exponent $\alpha \to 0$ in the power-law limit but is distinguished by the specific coefficient $\frac{c_{\text{eff}}}{3}$.

This hypothesis will be tested by computing the entanglement entropy for various system sizes $L$ and disorder strengths $\delta$, and performing model selection (using AIC) to distinguish between area-law, logarithmic, and volume-law scaling.

## 4. Theoretical Background and Citations

### 4.1 Refael-Moore Theory
The primary theoretical reference for this work is:
- **Refael, G., & Moore, J. E. (2004).** Criticality and localization in the random quantum spin chain. *Physical Review Letters*, 93(20), 207204.
 - DOI: 10.1103/PhysRevLett.93.207204
 - Key result: Prediction of the random singlet phase with $c_{\text{eff}} = \ln 2$.

### 4.2 Conformal Field Theory
For clean critical systems:
- **Calabrese, P., & Cardy, J. (2004).** Entanglement entropy and quantum field theory. *Journal of Statistical Mechanics: Theory and Experiment*, 2004(06), P06002.
 - DOI: 10.1088/1742-5468/2004/06/P06002

### 4.3 Many-Body Localization
For the localized regime:
- **Bauer, B., & Nayak, C. (2013).** Area laws in a many-body localized state and its implications for topological order. *Journal of Statistical Mechanics: Theory and Experiment*, 2013(09), P09005.
 - DOI: 10.1088/1742-5468/2013/09/P09005

## 5. Methodology Overview

1. **System Generation:** Generate XXZ Heisenberg Hamiltonians with random nearest-neighbor couplings $J_i \sim \mathcal{U}[1-\delta, 1+\delta]$.
2. **Ground State Computation:** Use imaginary-time TEBD evolution (via TeNPy) to compute ground states for system sizes $L \in [20, 40]$.
3. **Entropy Calculation:** Compute von Neumann entanglement entropy $S(l)$ for all bipartitions $l$.
4. **Model Selection:** Apply AIC-based model selection to distinguish between area-law, logarithmic, and volume-law scaling.
5. **Bootstrap Analysis:** Perform non-parametric bootstrap resampling to estimate confidence intervals for scaling exponents.
6. **Toy Model Verification:** Validate scaling behavior on small systems ($L=10$) with known random couplings.

## 6. Expected Outcomes

- Confirmation of logarithmic scaling $S(L) \propto \log L$ in the critical regime with $c_{\text{eff}} \approx \ln 2$.
- Observation of area-law behavior $S(L) \approx \text{const}$ in the localized regime.
- Quantitative characterization of the transition between regimes as a function of disorder strength $\delta$.
- A robust statistical framework (AIC + bootstrap) for distinguishing scaling laws in finite-size systems.

## 7. Limitations and Future Work

- Finite-size effects may obscure the asymptotic scaling behavior for small $L$.
- The TEBD algorithm may struggle with high entanglement in the critical regime, requiring large bond dimensions ($\chi \le 400$).
- Future work will extend this analysis to higher-dimensional systems and different disorder distributions.

## 8. Verification Checklist

- [x] Scaling ansatz explicitly stated: $S(L) \approx c_{\text{eff}} \log L$ (critical) vs Area Law (localized).
- [x] Citation included: Refael-Moore (Phys. Rev. Lett. 93, 207204 (2004)).
- [x] Hypothesis formulated: $S(L) \propto L^{\alpha}$ with $\alpha$ indicating phase.
- [x] Methodology outlined with specific steps for entropy calculation and model selection.
- [x] Expected outcomes and limitations discussed.

---
*Generated for project PROJ-308: Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains*
*Date: 2026-06-30*
