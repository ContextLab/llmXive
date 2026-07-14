# Research: Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

## Executive Summary

This research investigates the efficacy of unsupervised learning, specifically Variational Autoencoders (VAEs), in detecting phase transitions in isotropic spin systems without labeled data. The hypothesis is that the latent space geometry of a VAE trained on Monte Carlo configurations will exhibit a sharp structural change (peak in variance) at the critical temperature $T^*$. This study focuses on the 2D J1-J2 Heisenberg model and the XY model.

**Methodological Correction**: To ensure scientific rigor, this study replaces Bayesian Change Point Detection (BCPD) with a **Savitzky-Golay smoothing and derivative-based peak detection** algorithm, as phase transitions in finite systems manifest as smooth peaks, not step functions. Additionally, the validation strategy uses the **extrapolated critical temperature $T_c(\infty)$** derived from Finite Size Scaling (FSS) of the magnetic susceptibility, rather than the raw finite-size peak, to avoid circular validation. The primary metric is the **variance of the reconstruction error** (or specific latent dimensions), not the total variance of the mean vector, to ensure construct validity.

## Methodology

### 1. Data Generation & Acquisition

**Dataset Strategy**:
Since no verified external dataset URL exists for the specific J1-J2 Heisenberg configurations required (as per the "Verified datasets" block), the system will generate data programmatically using a standard Metropolis-Hastings algorithm implemented in Python/NumPy. This ensures reproducibility and exact control over temperature and lattice size.

*   **Model**: 2D Heisenberg Model (O(3) symmetry) and XY Model (O(2) symmetry).
*   **Hamiltonian**: $H = J_1 \sum_{\langle i,j \rangle} \vec{S}_i \cdot \vec{S}_j + J_2 \sum_{\langle i,k \rangle} \vec{S}_i \cdot \vec{S}_k$ (for J1-J2).
*   **Lattice Sizes**: $L=16$ (primary for speed), $L=24$, and $L=32$ (if feasible) for Finite Size Scaling.
*   **Temperature Range**: $T \in [0.1, 3.0]$ in units of $J$.
*   **Sampling & Autocorrelation**:
    1.  Calculate the **integrated autocorrelation time** $\tau_{int}$ for the magnetization at each temperature using the time-series of the magnetization.
    2.  Enforce a measurement interval of $> 10 \times \tau_{int}$ to ensure statistical independence of samples. This is critical for valid variance estimation and bootstrap resampling (FR-006).
    3.  Special handling for critical slowing down near $T^*$: if $\tau_{int}$ diverges, increase the interval dynamically.
*   **Checksumming**: Every generated raw data file is immediately checksummed (SHA-256) and recorded in metadata.
*   **Feasibility Check**: Generating ~5000 samples per temperature bin for L=16 on 2 CPU cores is estimated to take < 2 hours. L=32 may be skipped if time constraints are tight.

**Verification of Dataset Fit**:
The generated data contains the raw spin vectors $\vec{S}_i = (S_x, S_y, S_z)$ for every site. This satisfies the requirement for computing magnetic susceptibility ($\chi$) and feeding the VAE. No external variables are missing.

### 2. Model Architecture & Training (VAE)

**Architecture**:
*   **Encoder**: 2 Convolutional layers (in_channels=3, out_channels=[16, 32], kernel=3, stride=2) $\to$ Flatten $\to$ Linear $\to$ $\mu, \log\sigma$ (latent_dim=10).
*   **Decoder**: 2 Transposed Convolutional layers $\to$ Sigmoid/Softmax to reconstruct normalized spins.
*   **Loss**: $L = L_{recon} + \beta L_{KL}$, where $L_{recon}$ is MSE and $L_{KL}$ is KL divergence. $\beta$ will be tuned (default 1.0).

**Training Constraints**:
*   **Hardware**: CPU-only (2 cores).
*   **Optimization**: Adam (lr=1e-3).
*   **Epochs**: Max 50, with early stopping (patience=5) if validation loss increases.
*   **Batch Size**: Dynamically selected to fit ~6 GB RAM (likely 32-64).
*   **Rationale**: Convolutional layers are chosen over fully connected layers to respect the 2D spatial locality of spin interactions, which is crucial for capturing critical fluctuations. The latent dimension is a trade-off between expressivity and overfitting on limited CPU training time.

### 3. Latent Space Analysis & Critical Point Detection

**Primary Metric**: Variance of the **reconstruction error** ($\text{Var}(\|x - \hat{x}\|^2)$) and variance of specific latent dimensions aligned with order parameters. The total variance of the latent means is used only as a fallback if the error variance is flat.
**Hypothesis**: The reconstruction error variance will exhibit a peak at $T^*$.

**Statistical Method**:
*   **Peak Detection (Replaces BCPD)**: Apply **Savitzky-Golay smoothing** to the sequence of variance values across temperature bins to reduce noise. Then, identify the point of maximum first derivative (inflection) and the local maximum of the smoothed curve. This method is theoretically appropriate for identifying the maximum of a smooth, finite-size peak (critical temperature) rather than a step change.
*   **Significance**: A peak is considered significant if it exceeds the noise floor (defined as > 2σ above the moving average) and persists across lattice sizes.
*   **Bootstrap Resampling**: Perform 1000 iterations on the **independent subsamples** (spaced by $10\tau_{int}$) to compute the 95% confidence interval for $T^*$. This ensures valid p-values by respecting the autocorrelation structure.

**Finite Size Scaling (FSS) Protocol**:
*   **Goal**: Distinguish true phase transitions from finite-size artifacts.
*   **Method**: Run simulations for L=16, 24, 32. Fit the pseudo-critical temperatures $T_c(L)$ to the scaling relation:
    $$T_c(L) = T_c(\infty) + a L^{-1/\nu}$$
*   **Ground Truth**: The **extrapolated** $T_c(\infty)$ is used as the validation target, not the raw peak of the finite-size dataset. This breaks the circularity of validating ML against a quantity derived from the same raw data.
*   **Artifact Rejection**: If the detected peak does not sharpen (height increases, width narrows) as L increases, the result is classified as a finite-size artifact.

**Statistical Rigor**:
*   **Multiple Comparisons**: Not applicable as we are testing a single global peak hypothesis per model.
*   **Power Justification**: The sample size per temperature bin will be determined by a pilot run to ensure the standard error of the variance is small enough to resolve a peak. If the peak is too broad or flat, the study will report the limitation.
*   **Causal Claims**: The study will explicitly frame findings as associational. The VAE *identifies* a transition; it does not *cause* it. The causality is physical (Monte Carlo simulation).
*   **Collinearity**: The latent dimensions are learned to be independent (via KL penalty), but if they are highly correlated, the sum of variances will still capture the total energy of the latent distribution. The analysis will check for degeneracy.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Programmatic Data Generation** | No verified external dataset URL exists. Generating data ensures exact control over $T$, $L$, and coupling constants, and guarantees reproducibility (Constitution I). |
| **CPU-Only Training** | Required by CI constraints. Small batch sizes and limited epochs are chosen to fit the 6-hour window. |
| **Savitzky-Golay Peak Detection** | BCPD is unsuitable for peak-shaped curves in finite systems. Peak detection aligns with the physical nature of phase transitions. |
| **Extrapolated Ground Truth** | Using $T_c(\infty)$ via FSS avoids circular validation against the raw finite-size susceptibility peak. |
| **Autocorrelation Correction** | Ensures statistical independence of samples, preventing underestimated confidence intervals and invalid p-values. |
| **Reconstruction Error Variance** | Using reconstruction error variance (or specific latent dimensions) instead of mean variance avoids false negatives due to the VAE prior clustering. |

## Risks & Mitigations

1.  **Risk**: VAE fails to converge on CPU within 6 hours.
    *   *Mitigation*: Use a smaller network (fewer filters), reduce batch size, or reduce the number of temperature bins. Early stopping will prevent wasted compute.
2.  **Risk**: Latent variance is flat (no peak detected).
    *   *Mitigation*: Report the result as "no significant change point detected" and investigate if the latent dimension is too low or the architecture is insufficient. Pivot to reconstruction error variance if mean variance is flat.
3.  **Risk**: Memory overflow with L=32.
    *   *Mitigation*: Prioritize L=16 and L=24. If L=32 is attempted, process data in chunks or reduce samples per bin.
4.  **Risk**: Finite-size artifacts mimic a transition.
    *   *Mitigation*: Apply the FSS protocol. If the peak does not sharpen with increasing L, classify it as an artifact.
5.  **Risk**: BCPD fails to find a change point due to noise.
    *   *Mitigation*: (Replaced) Apply Savitzky-Golay smoothing and derivative analysis, which are more robust to noise in peak detection.