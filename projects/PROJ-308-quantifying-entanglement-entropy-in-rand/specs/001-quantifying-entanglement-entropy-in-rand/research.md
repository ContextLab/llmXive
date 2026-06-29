# Research: Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains

## Scientific Background

The project investigates the entanglement properties of the random XXZ Heisenberg spin chain, a canonical model for studying the Many-Body Localization (MBL) transition. In clean, critical 1D systems, the entanglement entropy $S(l)$ of a subsystem of length $l$ follows a logarithmic scaling law predicted by Conformal Field Theory (CFT):
$$ S(l) \approx \frac{c}{3} \ln(l) + c' $$
where $c$ is the central charge (for the XXZ chain at the isotropic point, $c=1$).

In the presence of strong disorder, the system is expected to enter the MBL phase, where entanglement growth is suppressed. Theoretical predictions (Refael and Moore, 2004) suggest a "Griffiths" regime with logarithmic growth but a reduced effective central charge:
$$ S(l) \approx \frac{\ln 2}{3} \ln(l) + \text{const} $$
At very strong disorder, the system may exhibit an **area law** ($S(l) \approx \text{const}$), indicating localization.

This project aims to numerically verify these scaling laws by computing the ground state of the disordered Hamiltonian using Tensor Network methods and fitting the resulting entropy profiles.

## Dataset Strategy

The "dataset" in this computational project is **synthetically generated** via the Hamiltonian simulation. No external static datasets are used.

| Variable | Source | Generation Method | Verification |
| :--- | :--- | :--- | :--- |
| **Couplings $J_i$** | Synthetic | Uniform distribution $\mathcal{U}[1-\delta, 1+\delta]$ per realization | Random seed pinned; distribution verified via histogram in debug mode. |
| **Ground State $|\psi_0\rangle$** | Computed | Imaginary-time TEBD (TeNPy) | Convergence tolerance set to a stringent threshold appropriate for high-precision numerical stability.; energy variance checked. |
| **Entropy $S(l)$** | Computed | Von Neumann formula on MPS Schmidt values | Double-precision arithmetic; boundary checks. |

**Note**: The "Verified datasets" block in the prompt instructions applies to external data sources. Since this project generates its own data, the "Dataset Strategy" here defines the generative process as the source. The reproducibility of this generation is guaranteed by the pinned random seed and the deterministic nature of the TEBD algorithm (given the same Hamiltonian).

## Methodological Approach

### 1. Hamiltonian Construction
The XXZ Hamiltonian with random nearest-neighbor couplings is defined as:
$$ H = \sum_{i=1}^{L-1} J_i (S^x_i S^x_{i+1} + S^y_i S^y_{i+1} + \Delta S^z_i S^z_{i+1}) $$
where $\Delta=1$ (isotropic) and $J_i \sim \mathcal{U}[1-\delta, 1+\delta]$.

### 2. Ground State Calculation
- **Method**: Imaginary-time evolution using the Time-Evolving Block Decimation (TEBD) algorithm.
- **Library**: TeNPy (Tensor Network Python).
- **Precision**: Double (64-bit) floating point.
- **Convergence**: Iterations continue until the energy change is $< 10^{-8}$.
- **Bond Dimension**: **Adaptive**. Start with $\chi=50$. If convergence is not met, increase $\chi$ by a substantial increment up to a predefined hard limit of 400. If convergence fails at $\chi=400$, the realization is flagged as "numerically unresolved" and excluded from the final fit to prevent systematic bias.

### 3. Entropy Calculation
For each bipartition $l \in \{1, \dots, L-1\}$, the reduced density matrix $\rho_A$ is constructed from the Schmidt decomposition, and the von Neumann entropy is computed:
$$ S(l) = -\sum_k \lambda_k^2 \ln(\lambda_k^2) $$
where $\lambda_k$ are the Schmidt coefficients.

### 4. Statistical Analysis & Phase Classification
The analysis employs a **multi-model selection** approach to distinguish phases, addressing the category error of using linear fits for area laws.

- **Model Fitting**: For each disorder realization, fit three models to $S(l)$ vs $l$:
  1.  **Logarithmic (Critical/Griffiths)**: $S(l) = \alpha \ln(l) + c$
  2.  **Constant (Area Law/MBL)**: $S(l) = c$ (equivalent to $\alpha \approx 0$ in log fit, but tested directly as a constant function)
  3.  **Linear (Thermal/Volume Law)**: $S(l) = \beta l + c$ (only for low disorder $\delta \le 0.1$)

- **Model Selection**: Use **Akaike Information Criterion (AIC)** to select the best model.
  - **MBL Identification**: The system is classified as MBL if the **Constant model** has the lowest AIC. A secondary check requires the slope of the Log model to be statistically indistinguishable from zero (p-value > 0.05 in a t-test on $\alpha$).
  - **Critical Identification**: The system is classified as Critical if the **Logarithmic model** has the lowest AIC and $\alpha$ is consistent with theoretical values ($c/3 \approx 0.33$ or $\ln 2 / 3 \approx 0.23$).
  - **Thermal Identification**: The system is classified as Thermal if the **Linear model** has the lowest AIC (for $\delta \le 0.1$).

- **Thermal Slope ($\beta$)**: For low disorder ($\delta \le 0.1$), if the Linear model is preferred, fit $S(l) = \beta l + c$ over the **bulk range** $l \in [L/4, 3L/4]$ to minimize boundary effects. A naive linear fit over the full range is statistically invalid for finite chains due to concavity; the restricted range is a necessary correction to ensure the extracted $\beta$ reflects the bulk thermal entropy density.

- **Bootstrap Resampling**:
  - **Protocol**: 
    1. For each realization $i$, fit the Logarithmic model to obtain $\alpha_i$.
    2. Resample the set of $\{\alpha_i\}$ values (not the raw $S(l)$ points) with replacement a large number of times.
    3. Calculate the mean, standard error, and 95% CI of the mean $\alpha$ from the resampled distribution.
  - **Rationale**: This correctly propagates the uncertainty of the exponent estimate without assuming correlation in the raw data and avoids "double-dipping" errors.

## Statistical Rigor & Constraints

### Multiple Comparisons & Family-Wise Error
The project performs multiple regression fits across different $\delta$ values. While the primary hypothesis is the scaling of $\alpha$ with $\delta$, no formal family-wise error correction (e.g., Bonferroni) is applied to the *individual* fits as they are treated as descriptive statistics of the phase diagram. However, the bootstrap CI provides a robust measure of uncertainty for each point.

### Sample Size & Power (Pilot Study)
- **Pilot Phase**: Before the main grid scan, a pilot study with $N=20$ realizations is performed at each $\delta$.
- **Variance Check**: Calculate the coefficient of variation (CV) of $\alpha_i$. If the CV is high enough that $N=100$ would yield a CI width $> 0.05$ (violating SC-001/SC-002), the plan dynamically increases $N_{\text{real}}$ up to the FR-010 max of 200.
- **Power Justification**: This adaptive approach ensures that the bootstrap analysis estimates the standard error with high precision, allowing detection of deviations from the theoretical $\alpha \approx 0.33$ (critical) or $\alpha \approx 0$ (localized).

### Causal Inference & Assumptions
- **Observational Nature**: This is a numerical experiment. The "disorder strength" $\delta$ is the controlled variable.
- **Identification**: The causal link between $\delta$ and the scaling exponent $\alpha$ is established by the controlled generation of Hamiltonians. No confounding variables exist in the simulation.
- **Measurement Validity**: The entanglement entropy is a direct observable of the quantum state. The TEBD algorithm is a standard, well-validated method for 1D ground states.

### Predictor Collinearity
- **Bipartition Size**: The variable $l$ is deterministic and non-collinear with the disorder realization.
- **Disorder Realizations**: Each realization is independent.
- **Edge Effects**: $l=1$ and $l=L-1$ are boundary cases. They are included in the fit but may exhibit higher variance; the bootstrap accounts for this.

## Methodological Correction Note

**Regarding SC-002 and Area Law Detection**: The success criterion SC-002 states that for strong disorder, the fitted exponent $\alpha$ must be $\le 0.05$ to indicate an area law. Methodologically, fitting a logarithmic model $S(l) = \alpha \ln l + c$ to a constant function (true area law) will mathematically yield $\alpha \approx 0$. Thus, $\alpha \le 0.05$ is a *consequence* of the fit, not a direct physical discovery. To ensure scientific soundness, the plan prioritizes the **AIC preference for the Constant model** as the primary indicator of the MBL phase. The condition $\alpha \le 0.05$ serves as a secondary consistency check. This hierarchy prevents the tautology of "detecting" localization solely by the failure of a log fit.

## Computational Feasibility (CI Constraints)

- **Hardware**: GitHub Actions `ubuntu-latest` (standard CPU allocation, standard RAM).
- **Runtime Limit**: 6 hours.
- **Strategy**:
  - **Chain Length**: $L=30$ (default). $L=40$ is supported but may approach the time limit; the plan includes a timeout check.
  - **Bond Dimension**: Adaptive (50-400). If convergence fails at 400, the realization is excluded (not retried indefinitely) to prevent runtime explosion.
  - **Parallelization**: Disorder realizations are processed sequentially to avoid memory contention on the 7 GB limit, but the TEBD update within a realization is optimized.
  - **Sampling**: $N=100$ realizations is the target. If runtime exceeds a predefined threshold, the job aborts to prevent failure.

## Reviewer Feedback Integration

- **Feynman's Toy Model**: The plan includes a "debug mode" that generates a small chain ($L=10$) with random couplings to visualize the "random arrows" and verify the entropy calculation before running the full $L=30$ set.
- **Refael-Moore Scaling**: The `analysis.py` module explicitly implements the $\frac{\ln 2}{3} \ln(l)$ hypothesis and compares it against the fitted $\alpha$.
- **Concrete Scaling Ansatz**: The `scaling_fit.txt` output will explicitly state the fitted model ($S(l) = \alpha \ln l + c$) and the AIC value, satisfying the request for a concrete ansatz.
- **Phase Classification**: The plan now uses AIC to distinguish between Logarithmic, Constant, and Linear models, resolving the methodological concern about R² comparison.
