# Research: Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains

## 1. Introduction and Motivation

This project investigates the universal scaling laws of entanglement entropy in one-dimensional quantum spin chains subject to random nearest-neighbor disorder. Specifically, we focus on the XXZ Heisenberg model with random couplings $J_i \sim \mathcal{U}[1-\delta, 1+\delta]$. The primary goal is to distinguish between the Area Law (characteristic of Many-Body Localized phases) and Logarithmic scaling (characteristic of Random Singlet Phases) by analyzing the scaling exponent $\alpha$ in the relation $S(L) \propto L^\alpha$.

## 2. Scaling Ansatz and Theoretical Background

### 2.1 Critical Regime (Clean System)
In a clean, critical one-dimensional system described by Conformal Field Theory (CFT), the entanglement entropy $S(L)$ of a block of length $L$ in an infinite chain scales logarithmically with the block size:
$$S(L) \approx \frac{c}{3} \log L + \text{const}$$
where $c$ is the central charge of the CFT. For the XXZ chain at the isotropic point, $c=1$.

### 2.2 Random Critical Regime (Refael-Moore Scaling)
When disorder is introduced, the system may enter a Random Singlet Phase (RSP). According to the seminal work by Refael and Moore (Phys. Rev. Lett. 93, 207204 (2004)), the entanglement entropy in this regime exhibits a distinct logarithmic scaling behavior, but with an effective central charge determined by the disorder statistics rather than the clean CFT value.

The specific scaling ansatz for the random critical regime is:
$$S(L) \approx \frac{c_{\text{eff}}}{3} \log L$$
where $c_{\text{eff}}$ is an effective central charge. For the infinite-randomness fixed point typical of random singlet phases, theoretical predictions suggest $c_{\text{eff}} = \ln 2 \approx 0.693$. Thus, the expected scaling is:
$$S(L) \approx \frac{\ln 2}{3} \log L$$

This result, derived by Refael and Moore, distinguishes the random critical behavior from the clean critical behavior ($c=1$) and the Area Law behavior ($c_{\text{eff}} \to 0$, i.e., $S(L) \approx \text{const}$) found in the localized phase.

### 2.3 Area Law (Localized Regime)
In the Many-Body Localized (MBL) regime, strong disorder prevents thermalization. The entanglement entropy in this phase obeys an "Area Law," meaning the entropy of a subsystem depends only on the size of its boundary, not its volume. In 1D, the boundary is a point, so:
$$S(L) \approx \text{const}$$
This corresponds to a scaling exponent $\alpha \approx 0$ in the power-law ansatz $S(L) \propto L^\alpha$, or equivalently, a vanishing slope in the log-log plot.

## 3. Hypothesis

Based on the theoretical framework established by Refael and Moore (2004) and subsequent literature on random spin chains, we propose the following hypothesis:

"The entanglement entropy $S(L)$ of the randomly perturbed XXZ chain scales as $S(L) \propto L^\alpha$ (or equivalently $S(L) \approx \frac{c_{\text{eff}}}{3} \log L$), where the exponent $\alpha$ (or effective central charge $c_{\text{eff}}$) serves as an order parameter for the phase transition:
1. **Localized Regime (High $\delta$):** $\alpha \approx 0$ (Area Law), corresponding to $c_{\text{eff}} \to 0$.
2. **Random Critical Regime (Intermediate $\delta$):** $\alpha$ indicates logarithmic scaling consistent with the Random Singlet Phase, specifically $S(L) \approx \frac{\ln 2}{3} \log L$ (Refael-Moore result).
3. **Clean Critical Regime ($\delta = 0$):** $S(L) \approx \frac{1}{3} \log L$ (Standard CFT result).

We further hypothesize that the transition between these regimes can be precisely located by monitoring the evolution of the fitted scaling exponent $\alpha$ (or $c_{\text{eff}}$) as a function of the disorder strength $\delta$."

## 4. Methodology

### 4.1 Model Selection via AIC
To robustly distinguish between the competing scaling laws (Constant, Logarithmic, Linear), we will employ the Akaike Information Criterion (AIC) for model selection, as recommended in the project plan to avoid the pitfalls of $R^2$ in this context.
- **Model 0 (Area Law):** $S(l) = \beta_0$
- **Model 1 (Logarithmic):** $S(l) = \beta_0 + \beta_1 \log l$
- **Model 2 (Volume Law):** $S(l) = \beta_0 + \beta_1 l$

The model with the lowest AIC score will be selected as the best fit for the data.

### 4.2 Statistical Validation
We will use non-parametric bootstrap resampling ($N_{\text{resamples}} \ge 1000$) to estimate the standard error and confidence intervals for the scaling exponent $\alpha$ (or slope $\beta_1$). This ensures that our conclusions about the phase are statistically robust.

### 4.3 Toy Model Verification
To satisfy the requirement for a "concrete numerical example" as suggested by reviewer Geoffrey West, we will implement a "Toy Model" verification step. This involves generating a short chain (e.g., $L=10$) with random couplings, computing the entanglement entropy for all bipartitions, and explicitly plotting $S(l)$ vs $\log l$ to visually confirm the slope. This serves as a sanity check for the numerical pipeline and a pedagogical demonstration of the Refael-Moore scaling.

## 5. References

1. Refael, G., & Moore, J. E. (2004). Criticality and entanglement in random quantum spin chains. *Physical Review Letters*, 93(26), 207204. https://doi.org/10.1103/PhysRevLett.93.207204
2. Hastings, M. B. (2007). Entanglement and the many-body localization transition. *Journal of Statistical Mechanics: Theory and Experiment*, 2007(08), P08024.
3. Vosk, R., Huse, D. A., & Altman, E. (2015). Theory of the many-body localization transition in one-dimensional systems. *Physical Review X*, 5(3), 031032.

## 6. Appendices

### A. Numerical Example (Toy Model)
*See `code/analysis.py` function `generate_toy_model_data` and `generate_entropy_vs_l_plot` for the implementation of the L=4, 8, 16 verification.*

### B. Data Generation Protocol
- System Size ($L$): 20 to 40
- Disorder Strength ($\delta$): 0.0 to 1.0
- Realizations ($N_{\text{real}}$): 50 to 200
- Method: TEBD (TeNPy) for ground state preparation
- Entropy Calculation: von Neumann entropy of reduced density matrices