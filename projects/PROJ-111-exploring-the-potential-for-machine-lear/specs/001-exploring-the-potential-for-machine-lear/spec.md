# Feature Specification: Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-14  
**Status**: Draft  
**Input**: User description: "Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1)

The researcher needs to acquire Monte Carlo simulation data for the 2D J1-J2 Heisenberg model (and optionally the XY model) and preprocess it into a standardized tensor format suitable for CPU-based unsupervised learning.

**Why this priority**: Without valid, normalized input data spanning the critical temperature range, no model can be trained, and no latent space analysis can occur. This is the foundational data layer.

**Independent Test**: A Python script can be executed to download/generate raw spin configurations, normalize them to unit length, reshape them into `[batch, 3, L, L]` tensors, and split them into stratified train/validation sets. The test verifies data integrity, shape correctness, and temperature stratification without needing a trained model.

**Acceptance Scenarios**:

1. **Given** a raw Monte Carlo configuration file for the J1-J2 model at L=16, **When** the preprocessing script is executed, **Then** the output is a NumPy array of shape `(N_samples, 3, 16, 16)` with all vectors normalized to unit length.
2. **Given** a dataset covering temperatures T=0.1 to T=3.0, **When** the split operation is performed, **Then** the training set and validation set both contain a representative distribution of samples from every temperature bin, defined as a **max absolute difference in sample count between any two temperature bins ≤ 5**.
3. **Given** a system size L=24, **When** the pipeline attempts to load data, **Then** the memory footprint of the loaded dataset does not exceed 6 GB RAM on a standard runner, ensuring CPU feasibility.

---

### User Story 2 - Unsupervised VAE Training and Convergence (Priority: P2)

The researcher needs to train a Variational Autoencoder (VAE) on the preprocessed spin configurations to learn a compressed latent representation without using labeled phase information.

**Why this priority**: This is the core analytical engine. The VAE must successfully converge to reconstruct inputs while forming a structured latent space; if the model fails to train or overfits, the subsequent phase transition detection is impossible.

**Independent Test**: A training loop can be run for a fixed number of epochs (e.g., 50) on the CPU. The test independently verifies that the reconstruction loss decreases and stabilizes, the KL divergence remains within a reasonable bound, and the model does not diverge or crash due to memory constraints.

**Acceptance Scenarios**:

1. **Given** the preprocessed training dataset, **When** the VAE is trained for 50 epochs with early stopping, **Then** the validation reconstruction loss converges to a stable value defined as **|Loss_t - Loss_{t-1}| < 1e-3** for **5 consecutive epochs**.
2. **Given** a batch of spin configurations from the validation set, **When** the trained encoder processes them, **Then** the output latent vectors have a mean of **|mean| < 1e-4** per component and a variance structure that is not degenerate (e.g., not all zeros).
3. **Given** the 2 CPU core constraint of the runner, **When** the training job runs, **Then** the total research execution time (training + analysis) does not exceed **6 hours**. If the time limit is exceeded, the system MUST report partial results (e.g., T* for L=16 only) with a status flag indicating "Time Budget Exceeded".

---

### User Story 3 - Latent Space Analysis and Critical Point Detection (Priority: P3)

The researcher needs to analyze the trained VAE's latent space across different temperatures to identify a sharp change in variance or structure that indicates a phase transition, validated against independent physical observables. The analysis MUST perform Finite-Size Scaling (FSS) using data from L=16 and L=24 to extrapolate the critical temperature $T^*$ to the thermodynamic limit ($L \to \infty$).

**Why this priority**: This is the scientific output. It transforms the trained model into a diagnostic tool, identifying the critical temperature $T^*$ and validating the hypothesis that unsupervised representations capture critical fluctuations, using rigorous statistical methods and physical ground truth.

**Independent Test**: A post-training analysis script can be run on the saved model weights. It independently calculates the total latent variance for each temperature bin, applies a **peak-finding algorithm with derivative analysis**, and identifies $T^*$. The test verifies that a specific temperature $T^*$ is flagged as the point of maximum fluctuation **without prior knowledge of the location**, and that this result correlates with the magnetic susceptibility peak. The test MUST also verify that the FSS extrapolation to $L \to \infty$ is performed.

**Acceptance Scenarios**:

1. **Given** the trained VAE and a held-out batch of configurations for each temperature T, **When** the analysis script encodes these batches and applies the peak-finding algorithm, **Then** the total variance of the latent means $\sum \text{Var}(\mu)$ exhibits a **global maximum where the second derivative (calculated after smoothing with a Gaussian process kernel) is < -0.01 (normalized by the global maximum of the variance curve) and the peak height > 2σ above a moving average (window size = 5 points) of the residuals**, identifying $T^*$.
2. **Given** the identified peak temperature $T^*$, **When** a bootstrap resampling test (1000 iterations) is performed **after thinning the dataset by a factor of ≥ 2τ_int**, **Then** the 95% confidence interval for $T^*$ is computed and reported.
3. **Given** the results for the XY model, **When** the same pipeline is applied, **Then** the system identifies a critical signature **without prior knowledge of the location** that **falls within the 95% confidence interval of the literature BKT transition temperature for L=16**, defined as a detected peak with a **p-value < 0.05** when compared against the susceptibility-derived ground truth.

### Edge Cases

- What happens if the latent space variance is flat across all temperatures (indicating the VAE failed to capture relevant physics)?
- How does the system handle a scenario where the critical temperature $T^*$ falls exactly between two sampled temperature bins?
- What occurs if the Monte Carlo data generation fails for a specific temperature due to simulation instability?
- What happens if the Finite-Size Scaling extrapolation fails due to insufficient data points? The system MUST report the pseudo-critical temperatures for L=16 and L=24 with a status flag "FSS Inconclusive".

## Requirements

### Functional Requirements

- **FR-001**: The system MUST generate or download Monte Carlo configurations for the 2D J1-J2 Heisenberg model (L=16, L=24) and the XY model across a temperature range of T=0.1 to T=3.0 in units of J. (See US-1)
- **FR-002**: The system MUST preprocess spin configurations by normalizing vectors to unit length and reshaping them into tensors of shape `[batch, 3, height, width]` with an 80/20 stratified train/validation split. (See US-1)
- **FR-003**: The system MUST implement a Variational Autoencoder (VAE) with 2 convolutional encoder layers and 2 deconvolutional decoder layers, using a latent dimension of 10, trained with MSE reconstruction loss and KL divergence regularization. (See US-2)
- **FR-004**: The system MUST train the VAE on CPU-only hardware using the Adam optimizer (lr=1e-3) for up to 50 epochs with early stopping if validation loss increases, ensuring the total research execution time (training + analysis) does not exceed **6 hours**. If the time limit is exceeded, the system MUST report partial results (e.g., T* for L=16 only) with a status flag indicating "Time Budget Exceeded". (See US-2)
- **FR-005**: The system MUST calculate the total variance of the latent means ($\sum \text{Var}(\mu)$) for each temperature bin and identify the critical temperature $T^*$ using a **peak-finding algorithm with derivative analysis** (specifically: smoothing with a Gaussian process regression using a squared-exponential kernel, then finding the global maximum). The identification of $T^*$ MUST rely **solely on latent space geometry**, not reconstruction error. If the variance curve is flat (no peak detected), the system MUST report "No significant transition detected" with a confidence interval. (See US-3)
- **FR-006**: The system MUST perform a bootstrap resampling test with 1000 iterations to compute the 95% confidence interval for the identified critical temperature $T^*$. **Before bootstrapping, the system MUST calculate the integrated autocorrelation time (τ_int) and thin the dataset by a factor of ≥ 2τ_int.** (See US-3)
- **FR-007**: The system MUST frame all findings regarding the relationship between latent space variance and temperature as associational, **avoiding claims that the VAE *causes* the transition**, while acknowledging that the physical system's causality is validated via independent physical verification. (See US-3)
- **FR-008**: The system MUST compute the **magnetic susceptibility ($\chi$)** directly from the raw spin configurations and use **literature values for critical temperatures** or **extrapolated T* from Finite-Size Scaling** as the **sole ground truth** to validate the ML-derived $T^*$. For the XY model, the system MUST identify the transition **without prior knowledge of the location** (the algorithm must not accept T* as an input parameter; the test suite must verify that T* is derived solely from the input data) and verify the result correlates with the susceptibility peak. (See US-3)
- **FR-009**: The system MUST report the pseudo-critical temperatures for L=16 and L=24 along with the extrapolated $T^*$ to the thermodynamic limit ($L \to \infty$). (See US-3)
- **FR-010**: The system MUST implement a Finite-Size Scaling (FSS) protocol to extrapolate $T^*$ to the thermodynamic limit ($L \to \infty$) using the pseudo-critical temperatures from L=16 and L=24. The extrapolation MUST use the scaling relation $T^*(L) = T_c + a L^{-1/\nu}$ with $\nu=1$ (for 2D Ising/XY universality) or a fitted exponent if the universality class is unknown. (See US-3)

### Key Entities

- **SpinConfiguration**: Represents a snapshot of the isotropic spin system, characterized by lattice size (L), temperature (T), and a 3D tensor of spin vectors.
- **LatentRepresentation**: The compressed vector output from the VAE encoder for a given spin configuration, characterized by dimensionality (10) and statistical moments (mean, variance).
- **CriticalSignature**: A derived metric indicating the presence of a phase transition, characterized by the temperature $T^*$, the magnitude of variance peak, and the confidence interval.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The variance of the latent space means across temperatures is measured against **literature values for critical temperatures** or **extrapolated T* from Finite-Size Scaling** to validate the method's sensitivity. (See FR-005, FR-008, FR-010, US-3)
- **SC-002**: The reconstruction error stability is measured against the convergence criteria (|Loss_t - Loss_{t-1}| < 1e-3 for 5 epochs) to ensure the model has learned a valid representation. (See FR-003, US-2)
- **SC-003**: The computational resource usage (RAM and CPU time) is measured against the free-tier runner limits (7 GB RAM, 2 CPU cores, 6 hours) to verify feasibility. (See FR-004, US-2)
- **SC-004**: The statistical significance of the detected transition is measured against the 95% confidence interval derived from 1000 bootstrap iterations (after thinning by τ_int) to ensure robustness. (See FR-006, US-3)
- **SC-005**: The method's generality is measured by comparing the detected $T^*$ for the XY model against **literature values for the BKT transition temperature** (extrapolated to L→∞) to ensure robustness. (See FR-008, US-3)

## Assumptions

- The pre-computed Monte Carlo data for the J1-J2 model is available on the Open Science Framework or can be generated within the 6-hour CI limit using a standard Metropolis-Hastings algorithm in Python/NumPy.
- The VAE architecture (2 conv/2 deconv layers, latent dim=10) is sufficiently expressive to capture critical fluctuations in the J1-J2 model without requiring GPU acceleration or 8-bit quantization.
- The critical temperature $T^*$ for the specific J1-J2 coupling ratio used is either known from literature for validation or the study focuses solely on the *detection* of a transition regardless of its absolute value.
- The dataset size (L=16, L=24) fits within the 7 GB RAM limit of the GitHub Actions free-tier runner when loaded as NumPy arrays.
- The latent space variance peak is the primary indicator of criticality, and alternative indicators (e.g., mutual information, clustering metrics) are out of scope for this specific iteration. **Note: If the variance peak is flat, the system falls back to reconstruction error variance as a secondary indicator, as per FR-005.**
- Any threshold introduced for identifying the "peak" (e.g., derivative magnitude) will use a community-standard sensitivity analysis (sweeping $\delta \in \{0.01, 0.05, 0.1\}$) to ensure the result is not an artifact of a specific cutoff choice.
- The magnetic susceptibility calculation assumes the raw spin configurations are sufficient to compute the second moment of the magnetization without additional simulation steps.
- The Finite-Size Scaling protocol assumes a standard power-law scaling relation $T^*(L) = T_c + a L^{-1/\nu}$ with $\nu=1$ for 2D systems, or a fitted exponent if the universality class is unknown.
- The 6-hour time limit includes data generation, training, and analysis. If this limit is exceeded, partial results will be reported as per FR-004.