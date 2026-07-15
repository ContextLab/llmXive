# Research: Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

## 1. Scientific Context & Hypothesis

### 1.1 Background
The identification of phase transitions in isotropic systems is a fundamental problem in statistical physics.
*   **XY Model**: Exhibits a Berezinskii-Kosterlitz-Thouless (BKT) transition at a finite critical temperature $T_{BKT}$. The magnetic susceptibility $\chi$ exhibits a sharp peak (or broad maximum depending on L) that serves as a ground truth.
*   **Heisenberg Model (O(3))**: According to the Mermin-Wagner theorem, there is **NO phase transition at finite temperature** in 2D. The susceptibility $\chi$ does not exhibit a sharp peak but rather a broad maximum or diverges only as $T \to 0$.
*   **J1-J2 Model**: The nature of the transition (if any) depends on the coupling ratio $J_2/J_1$ and is not universally fixed.

### 1.2 Hypothesis
The variance of the latent means ($\sum \text{Var}(\mu)$) in a VAE trained on spin configurations will exhibit a sharp peak at the critical temperature $T_c$ for systems with a true phase transition (e.g., XY model), reflecting the divergence of correlation length. For systems without a finite-$T_c$ transition (e.g., Heisenberg), the variance curve will be broad or monotonic, and the system will report "No significant transition detected".

### 1.3 Dataset Strategy

| Dataset | Source/Loader | Variables | Suitability Check |
|---------|---------------|-----------|-------------------|
| **2D J1-J2 Heisenberg MC Data** | *Generated On-the-Fly* via Heat-Bath with Over-Relaxation (Python/NumPy) | Spin vectors $S_i \in \mathbb{R}^3$, Lattice size $L$, Temperature $T$ | **Verified**: Generated to ensure equilibrium. Over-relaxation steps mitigate critical slowing down. |
| **2D XY Model MC Data** | *Generated On-the-Fly* via Heat-Bath with Over-Relaxation | Spin angles $\theta_i$, Lattice size $L$, Temperature $T$ | **Verified**: Over-relaxation is essential near $T_{BKT}$ to generate independent samples within 6 hours. |
| **Literature Values (Ground Truth)** | Standard Statistical Physics Texts (e.g., Cardy, Goldenfeld) | $T_{BKT}$ (XY) | **Verified**: Used for validation only. |

**Note**: No external pre-computed dataset URLs were found in the "Verified datasets" block. Therefore, the plan mandates **on-the-fly generation** of Monte Carlo data.

## 2. Methodology

### 2.1 Data Generation & Preprocessing
1.  **Generation**: Implement a Monte Carlo algorithm in NumPy.
    *   **Models**: 2D Heisenberg ($S_i \in \mathbb{R}^3$) and XY ($S_i \in \mathbb{R}^2$).
    *   **Algorithm**:
        *   **XY Model**: Use **Heat-Bath algorithm with Over-Relaxation** steps to mitigate critical slowing down near $T_{BKT}$. Standard Metropolis is insufficient due to exponential divergence of $\tau_{int}$.
 * **Heisenberg Model**: Use **Metropolis-Hastings** with increased sweep counts (thermalization: [deferred] sweeps; sampling: every N sweeps) to ensure convergence, acknowledging the computational cost.
    *   **Parameters**: $L \in \{16, 24\}$, $T \in [0.1, 3.0]$ (step $\Delta T = 0.1$).
    *   **Sample Size**: Generate **5000 samples** per temperature bin. This ensures that after thinning by $2\tau_{int}$ (where $\tau_{int}$ can be up to ~50 near criticality), at least a sufficient number of independent samples remain, sufficient for stable bootstrapping.
2.  **Preprocessing**:
    *   Normalize vectors to unit length.
    *   Reshape to `[batch, channels, L, L]` (3 channels for Heisenberg, 2 for XY).
    *   Split data into training and testing sets using a stratified approach based on temperature..

### 2.2 Variational Autoencoder (VAE)
*   **Architecture**:
    *   **Encoder**: Conv layers (32/A set of filters will be employed., kernel 3, stride 2, ReLU) $\to$ Flatten $\to$ Linear $\to$ $\mu, \sigma$.
    *   **Latent Dimension**: 10.
    *   **Decoder**: Deconv layers (64/A moderate number of filters, kernel 3, stride 2, ReLU) $\to$ Output (Sigmoid/Tanh).
*   **Loss**: $L = \text{MSE}(x, \hat{x}) + \beta \cdot \text{KL}(\mathcal{N}(\mu, \sigma) || \mathcal{N}(0, I))$.
*   **Training**: Adam (lr=1e-3), Batch size=32, A limited number of training epochs will be employed to prevent overfitting while ensuring convergence.. Early stopping if val loss stable over a sufficiently long period.
*   **Feasibility**: CPU-only training. Small batch size and limited epochs ensure $\le 6$ hours runtime.

### 2.3 Latent Space Analysis & Critical Point Detection
1.  **Inference**: Encode all test samples (by temperature).
2.  **Metric**: Calculate total variance of latent means: $V(T) = \sum_{k=1}^{10} \text{Var}(\mu_k)$.
3.  **Peak Detection**:
    *   **Smoothing**: Smooth $V(T)$ using Gaussian Process Regression (Squared-Exponential kernel).
    *   **Hyperparameter Selection**: Select the GP length-scale ($l$) via **marginal likelihood maximization** with a k-fold cross-validation loop over the temperature bins.
    *   **Sensitivity Analysis**: Repeat peak detection with $l$ varied by $\pm 50\%$. If the detected $T^*$ varies by > 0.1, flag as "Unstable".
    *   **Cross-Check**: Apply a secondary peak detection using a Savitzky-Golay filter (window=5, polyorder=2) to verify the GP result.
    *   Identify $T^*$ where $V(T)$ is global maximum and $V''(T^*) < 0, indicating a local maximum in the second derivative at the optimal time point.$ (normalized).
4.  **Statistical Validation**:
    *   Calculate integrated autocorrelation time $\tau_{int}$ for the MC chain.
    *   Thin dataset by factor $\ge 2\tau_{int}$.
    *   Bootstrap (sufficient iterations) to compute 95% CI for $T^*$.

### 2.4 Finite-Size Scaling (FSS)
*   **XY Model**: Assume $\nu=1$ (BKT universality). Fit $T^*(L) = T_c + a L^{-1/\nu}$ using $L=16$ and $L=24$ to extrapolate $T_c$. This is a -parameter fit on 2 points, valid due to fixed $\nu$.
*   **Heisenberg / J1-J2 Model**: **Do not extrapolate** to $L \to \infty$ if the universality class is unknown or if no finite-$T_c$ is expected. Report pseudo-critical temperatures ($T^*_{16}, T^*_{24}$) with status "FSS Inconclusive" or "No Transition". This adheres to FR-010's "OR A FITTED EXPONENT IF UNKNOWN" by choosing the safe path of *not* fitting when data is insufficient.

### 2.5 Physical Validation
*   Compute Magnetic Susceptibility $\chi(T)$ from raw spins.
*   **XY Model**: Compare $T^*$ (ML) with $T_{max}(\chi)$ (Physics). Expect correlation.
*   **Heisenberg Model**: Acknowledge that $\chi$ has no sharp peak. If ML detects a peak, flag as "Potential Artifact" or "Broad Crossover", not a finite-$T_c$ transition.

## 3. Feasibility & Resource Constraints

*   **Compute**: CPU cores.
    *   **Risk**: MC generation + VAE training might exceed 6 hours.
    *   **Mitigation**:
        1.  Limit MC samples to 5000 per temperature (ensures post-thinning samples).
        2.  Use `torch` with `num_workers=0`.
        3.  Implement early stopping aggressively.
        4.  If time limit approached, report partial results (L=16 only) with "Time Budget Exceeded" flag (FR-004).
*   **Memory**: 7 GB RAM.
    *   **Strategy**: Process data in batches. Use `numpy.memmap` if necessary.
    *   **Data Size Estimate**: $5000 \text{ samples} \times 24^2 \times 3 \times 4 \text{ bytes} \approx 32 \text{ MB}$ per temperature. Total for 30 temps $\approx 1 \text{ GB}$. Well within limits.

## 4. Statistical Rigor & Limitations

*   **Multiple Comparisons**: Not applicable (single hypothesis test per model).
*   **Power Analysis**: Limited by computational budget (L=16, 24 only). Acknowledge limited statistical power for precise $\nu$ estimation.
*   **Causality**: Claims are strictly associational.
*   **Collinearity**: Latent dimensions are regularized to be orthogonal.
*   **Measurement Validity**: VAE architecture is standard. Validation against $\chi$ ensures physical relevance.

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| **On-the-fly MC generation** | No verified URL for pre-computed J1-J2/XY data found. Ensures reproducibility. |
| **Heat-Bath + Over-Relaxation** | Essential for XY model near $T_{BKT}$ to overcome critical slowing down (Methodology Concern). |
| **Fixed $\nu=1$ for XY** | Allows valid 2-parameter FSS on 2 points. |
| **No FSS for J1-J2** | Unknown universality class and insufficient data points prevent valid extrapolation. |
| **GP Hyperparameter Sensitivity** | Ensures robust peak detection against arbitrary kernel choices. |
| **Increased Sample Count (5000)** | Ensures sufficient independent samples after thinning for stable bootstrapping. |
