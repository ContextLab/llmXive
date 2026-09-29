# Research Document: Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains

## Scaling Ansatz

The central hypothesis of this research concerns the scaling behavior of the entanglement entropy $S(L)$ for a block of length $L$ in a one-dimensional quantum spin chain with random nearest-neighbor couplings.

Two distinct regimes are expected based on the disorder strength $\delta$:

1. **Critical Regime (Weak Disorder):**
 In the clean limit or weak disorder, the system exhibits critical behavior described by Conformal Field Theory (CFT). [UNRESOLVED-CLAIM: c_690e4c76 — status=not_enough_info] The entanglement entropy scales logarithmically with the block size:
 $$ S(L) \approx \frac{c_{eff}}{3} \log L + s_0 $$
 where $c_{eff}$ is the effective central charge and $s_0$ is a non-universal constant.

2. **Localized Regime (Strong Disorder):**
 In the presence of strong disorder, the system is expected to enter a Many-Body Localized (MBL) phase or an Infinite Randomness Fixed Point. According to the seminal work by Refael and Moore, the entanglement entropy follows a "log-squared" or modified logarithmic scaling due to the random singlet phase, but for the purpose of distinguishing area-law vs. volume-law in the context of this specific XXZ perturbation model, we test against the area law and the Refael-Moore logarithmic prediction:
 $$ S(L) \approx \frac{\ln 2}{3} \log L + \text{const} $$
 In the deeply localized regime, the entropy may saturate to an area law (constant) or grow sub-logarithmically, depending on the specific nature of the localization.

**Primary Scaling Ansatz:**
We posit that the entanglement entropy follows a power-law form $S(L) \propto L^\alpha$ or logarithmic form $S(L) \propto \log L$, where the exponent $\alpha$ or the prefactor of the logarithm distinguishes the phase:
- **Area Law (Localized):** $\alpha \approx 0$ (or $S(L) \approx \text{const}$)
- **Logarithmic Scaling (Critical/Random Singlet):** $S(L) \propto \log L$
- **Volume Law (Thermal/High Energy):** $S(L) \propto L$ ($\alpha \approx 1$)

## Citations

- **Refael-Moore (2004):** G. Refael and J. E. Moore, "Entanglement Entropy of Random Quantum Critical Points in One Dimension," *Physical Review Letters* **93**, 260602 (2004). [DOI: 10.1103/PhysRevLett.93.260602]
 - *Relevance:* Establishes the theoretical prediction for logarithmic entanglement scaling in random singlet phases, providing the baseline for the critical regime analysis in this project.

- **Huse et al. (2011):** D. A. Huse, R. Nandkishore, and V. Oganesyan, "Phenomenology of fully many-body-localized systems," *Physical Review B* **90**, 174202 (2014).
 - *Relevance:* Discusses the area-law scaling of entanglement entropy in the many-body localized phase.

## Hypothesis

We hypothesize that $S(L) \propto L^\alpha$ where the exponent $\alpha$ serves as an order parameter for the phase transition:
- In the **localized regime** (high disorder $\delta$), $\alpha \approx 0$, indicating an area law (entropy saturates with system size).
- In the **critical regime** (low disorder $\delta$), the system exhibits logarithmic scaling $S(L) \propto \log L$, which corresponds to $\alpha \approx 0$ in a power-law fit over a limited range but is distinguished by the specific logarithmic prefactor predicted by Refael-Moore.
- In the **thermal regime** (vanishing disorder), $\alpha \approx 1$, indicating a volume law (entropy grows linearly with system size).

Specifically, we test the prediction that for the randomly perturbed XXZ chain, the transition from logarithmic scaling to area-law scaling occurs at a critical disorder strength $\delta_c$, and that the effective central charge $c_{eff}$ extracted from the logarithmic fit matches the theoretical value of $\ln 2$ (or related constants) in the random singlet limit.

## Verification Protocol

To validate these hypotheses, we will:
1. Generate ground states for XXZ chains with varying disorder strengths $\delta$ using TEBD (Time-Evolving Block Decimation).
2. Compute the von Neumann entanglement entropy $S(l)$ for all bipartitions $l$ across the chain.
3. Perform model selection using the Akaike Information Criterion (AIC) to distinguish between linear (volume law), logarithmic, and constant (area law) scaling models.
4. Bootstrap resampling will be used to estimate the confidence intervals of the scaling exponents and prefactors.
5. A toy model verification with small system sizes ($L=10$) will be performed to visually confirm the scaling behavior before running the full grid scan.

## Toy Model Validation

As suggested by reviewer Richard Feynman, a specific "toy model" verification step is included:
- A short chain ($L=10$) with random couplings will be constructed.
- Entanglement entropy will be computed via exact diagonalization (for $L=10$) or TEBD.
- The resulting $S(L)$ vs $\log L$ plot will be generated to explicitly demonstrate the slope and validate the numerical pipeline before scaling to larger $L$.
- This ensures that the "random arrows" (couplings) conspire to produce the predicted logarithmic growth in the critical regime.