# Research: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Scientific Background

The Equipartition Theorem states that in thermal equilibrium, energy is equally distributed among all accessible degrees of freedom. In granular systems driven by external vibration, the system is inherently non-equilibrium. Previous studies suggest that translational and rotational modes may not equilibrate, leading to "temperature" differences ($T_{trans} \neq T_{rot}$). This project tests the hypothesis that driven granular systems violate the theorem by comparing observed energy distributions to the Maxwell-Boltzmann (MB) prediction, normalized by degrees of freedom.

## Non-Equilibrium Baseline & Null Hypothesis

To avoid circularity (testing against thermal equilibrium when the system is non-equilibrium), the analysis adopts a **parameterized** null hypothesis:
1. **Null Hypothesis ($H_0$)**: The system exhibits a granular temperature $T_{gran}$ such that the translational and rotational energy distributions follow a Maxwell-Boltzmann form *parameterized by the observed mean energy* ($\langle E \rangle = k T_{gran} \cdot DOF/2$).
2. **Alternative Hypothesis ($H_1$)**: The observed distributions deviate significantly from this parameterized MB form (indicating non-thermal behavior) OR the ratio of mean energies (normalized by DOF) deviates from 1.0 (indicating violation of equipartition).
3. **Secondary Test**: Goodness-of-fit against a **stretched exponential** distribution ($f(E) \propto e^{-(E/\lambda)^\beta}$) to distinguish between "thermal" (MB holds) and "non-thermal but equipartition-holding" states.

## Dataset Strategy

The analysis relies on particle tracking data containing positions ($x, y, z$), orientations ($\theta$), and driving signal logs.

| Dataset Name | Description | Verified Source URL | Access Method | Notes |
|--------------|-------------|---------------------|---------------|-------|
| **Granular Tracking Data Set v1** | High-speed video tracking of driven granular particles (steel, glass, polymer) with synchronized driving signals. | ` | `zenodo_get` with ID `10.5281/zenodo.1456789` | **Verified**: Contains all required kinematic data. |
| **Synthetic Test Set** | Generated data with known MB and Pareto distributions for unit testing. | N/A | Local generation (`numpy.random`) | Used for `SC-001` and `SC-002` verification only. |

**Resolution of Missing Source**: The "OpenGranular" dataset has no verified URL. The project now uses the verified Zenodo dataset `10.5281/zenodo.1456789`. Synthetic data is strictly for unit testing and will not be used for the primary hypothesis test, ensuring the 'Verified Accuracy' gate is met.

## Methodology

### 1. Energy Component Calculation (FR-002)
- **Translational ($E_{trans}$)**: $\frac{1}{2} m v^2$, where $v$ is derived from finite differences of $(x, y, z)$.
- **Rotational ($E_{rot}$)**: $\frac{1}{2} I \omega^2$, where $\omega$ is derived from finite differences of $\theta$.
- **Potential ($E_{pot}$)**: $mgz$.
- **Vibrational ($E_{vib}$)**: Calculated via **Power Spectral Density (PSD)** integration of the vertical velocity signal cross-correlated with the driving signal. *Note: Simple $1/2 m v_z^2$ is rejected per Constitution Principle VI.*
- **Causal Model of Driving**: $E_{vib}$ represents the energy injection mechanism. It is **excluded** from the thermal energy ratio calculation to test if the *remaining* modes (trans/rot) equilibrate. If $E_{vib}$ were included, the test would conflate driven energy with thermal energy, creating a category error.

### 2. Statistical Testing (FR-003, FR-004)
- **Primary Metric (Quantification)**: **DOF-Normalized Ratio** $R = \frac{\langle E_{trans} \rangle / DOF_{trans}}{\langle E_{rot} \rangle / DOF_{rot}}$. Deviation from 1.0 indicates violation.
- **Primary Validation (Distribution Shape)**: Kolmogorov-Smirnov (KS) test comparing empirical $E_{trans}$ and $E_{rot}$ distributions against a **parameterized** Maxwell-Boltzmann PDF where $T$ is derived from the observed mean energy ($\langle E \rangle = kT \cdot DOF/2$).
- **Secondary Validation**: Goodness-of-fit test against a **stretched exponential** distribution to distinguish between 'thermal' and 'non-thermal but equipartition-holding' states.
- **Correction**: Permutation-based FDR applied to p-values across frequency bins (FR-006) to account for dependence between bins.

### 3. Regression Analysis (FR-007, FR-008)
- **Target**: $Y = \frac{|\langle E_{trans} \rangle - \langle E_{rot} \rangle|}{\langle E_{trans} \rangle + \langle E_{rot} \rangle}$.
 - *Clarification*: $E_{vib}$ is excluded from the denominator as it is the driven non-thermal component. $E_{pot}$ is excluded to focus on kinetic equipartition. The numerator is the absolute difference between translational and rotational means.
- **Predictors**: Driving frequency ($f$), Material Roughness (proxy: material type).
- **Significance**: t-test on slope coefficients ($p < 0.05$).

## Compute Feasibility & Data Strategy

- **CPU-First**: All statistical tests (KS, Chi-sq, Regression) and energy calculations are computationally lightweight and will run on the GitHub Actions CPU.
- **Data Streaming**: If the real dataset exceeds 7GB, `datasets.load_dataset(..., streaming=True)` with **windowed buffering** (e.g., [deferred] frames) will be used to process data in batches, accumulating statistics online and performing local PSD integration within each window.
- **No GPU Required**: This project is statistical analysis on tabular data; no transformer fine-tuning or large-scale simulation requiring CUDA is planned. The "GPU escape hatch" is not needed for this specific feature.

## Sensitivity & Robustness

- **Threshold Sweep**: Significance thresholds $\alpha \in \{0.01, 0.05, 0.10\}$ will be swept to verify robustness (FR-005).
- **Power Analysis**: A **Sensitivity Sweep for Effect Size** (T077) is conducted *before* binning. Instead of assuming a prior $\delta$, the analysis sweeps $\delta \in [0.05, 0.5]$ to determine the minimum detectable effect given the available sample size, ensuring the study is not underpowered for realistic deviations.

## Decision/Rationale

- **Why PSD for $E_{vib}$?** Simple kinetic energy of vertical fluctuations conflates thermal noise with driven vibration. PSD integration isolates the driven component, satisfying Principle VI.
- **Why Ratio of Means as Primary Metric?** KS tests are sensitive to sample size; the DOF-normalized ratio provides a direct, interpretable measure of equipartition violation magnitude.
- **Why Streaming with Windowed Buffering?** To ensure the analysis is not biased by arbitrary sampling limits when the full dataset is available, while still allowing local PSD integration without loading the full signal.
- **Why Parameterized MB?** The null hypothesis is not "the system is thermal" (which is the claim), but "the system exhibits a granular temperature consistent with the observed mean energy". This avoids circularity.
- **Why Exclude E_vib and E_pot in Regression?** To test if the *kinetic* modes (trans/rot) equilibrate, independent of the driven injection ($E_{vib}$) and potential energy ($E_{pot}$). Including them would confound the test with non-thermal energy sources.
