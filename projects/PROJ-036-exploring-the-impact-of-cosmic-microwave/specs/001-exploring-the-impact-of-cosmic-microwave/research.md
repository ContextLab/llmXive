# Research: Exploring the Impact of Cosmic Microwave Background Anomalies on Early Universe Simulations

## 1. Problem Statement & Scientific Context

The Cosmic Microwave Background (CMB) exhibits statistical anomalies, most notably the "Cold Spot" and a low quadrupole amplitude, which deviate from the standard ΛCDM predictions. While these anomalies are observed in the CMB temperature maps (Planck PR3), their potential impact on the subsequent formation of Large-Scale Structure (LSS) remains an open question. This research investigates whether incorporating these specific anomalies as modified initial conditions in N-body simulations leads to measurable deviations in LSS statistics (matter power spectrum, void size distributions) compared to standard ΛCDM simulations.

The core hypothesis is that the low-ℓ power deficit/excess in the CMB propagates through the linear regime and manifests as measurable differences in the non-linear LSS statistics at z=0, specifically in the void population and large-scale power.

## 2. Dataset Strategy

The research relies on the **Planck Legacy Archive (PR3)** for CMB temperature maps. The plan strictly adheres to the verified datasets provided in the user message.

### Verified Datasets

- **Dataset Name**: Planck PR3 Commander/SMICA CMB Temperature Maps
- **Source**: Planck Legacy Archive (Public)
- **Access Method**: Programmatic download via `requests` from the official Planck server endpoints (URL: ` for Commander, or SMICA equivalent).
- **Variables Required**: Full-sky temperature anisotropy maps (Nside ≥ 256), specifically the low-ℓ region (ℓ ≤ 30) and the Cold Spot coordinates.
- **Validation**: MD5/SHA256 checksums against official Planck hashes.

**Constraint**: If the Planck Legacy Archive is temporarily unavailable, the system retries up to 3 times with 60-second backoff (Edge Case). If the dataset lacks specific variables (e.g., only high-ℓ data), the plan will flag this as a fatal mismatch and abort.

**Note on PR4**: The Planck PR4 release is not yet publicly available. This plan uses **Planck PR3 (2018)**, which is the current public release.

## 3. Methodological Approach

### 3.1 Data Preprocessing & Validation
- **Download**: Fetch Commander or SMICA maps (Nside=2048) from the Planck archive (PR3).
- **Validation**: Verify file integrity using official checksums (FR-001).
- **Masking**: Apply a galactic latitude mask (|b| > 5°) to remove foreground contamination.
- **Anomaly Identification**: Confirm the presence of the Cold Spot and low quadrupole in the loaded maps by calculating the angular power spectrum up to ℓ=30.

### 3.2 Initial Condition Generation (Phase-Injected Mode)
- **Tool**: CAMB (or CLASS) linear perturbation code.
- **Method**:
 1. Calculate the standard ΛCDM power spectrum.
 2. **Phase Injection**: Extract the specific phase configuration (Fourier phases) of the Cold Spot and low-ℓ modes (ℓ=2,3) from the Planck map.
 3. **Transfer Function Mapping**: Use the linear transfer function to map these 2D CMB phases to the 3D matter initial conditions, preserving the spatial structure of the anomaly.
 4. **Finite Volume Approximation**: Since the box (250 Mpc/h) cannot contain the full wavelength of the quadrupole ([deferred] Mpc/h), the anomaly is injected as a **local gradient** or a low-k mode that fits within the box. This is a boundary condition approximation, explicitly acknowledging the finite volume confound.
 5. Generate initial condition files in GADGET-2 or nbodykit format.
- **Validation**: Ensure IC files are ≤ 500 MB and conform to format specs (FR-003).

### 3.3 N-body Simulations
- **Tool**: GADGET-2 (compiled for CPU) or `nbodykit` (Python-based, CPU-only).
- **Configuration**:
 - Box size: 250 Mpc/h (downsized from 500 for CI feasibility)
 - Particles: 128³ (downsized from 256 for CI feasibility)
 - Redshift: z=0 (output)
 - Cosmology: Standard ΛCDM parameters (Planck 2018).
- **Execution**: Run two simulations:
 1. **Control**: Standard ΛCDM initial conditions.
 2. **Anomaly**: Anomaly-modified initial conditions (Phase-Injected).
- **Constraints**: Total runtime ≤ 12 hours; Peak RAM ≤ 7 GB. If the simulation exceeds memory, the particle count or box size will be reduced (fallback), but this is noted as a limitation.

### 3.4 Statistical Analysis (Diagnostic Comparison)
- **Metrics**:
 - Matter Power Spectrum P(k) at z=0.
 - Void size distribution (radius, underdensity contrast).
- **Tests**:
 - **Kolmogorov-Smirnov (KS)**: Compare the *delta* (anomaly - control) power spectrum against the standard ΛCDM reference mock.
 - **Chi-squared**: Compare the *delta* void size distribution against the reference mock.
- **Correction**: Apply Bonferroni or Benjamini-Hoch correction for multiple comparisons (FR-006).
- **Classification**: All results are framed as **associational** (observational design) since CMB anomalies are not randomized (FR-007).
- **Interpretation**: Due to N=1, the p-values are **diagnostic metrics** indicating the magnitude of deviation, not inferential evidence of significance. The plan explicitly states that "statistical power" is zero for N=1, and the results are a "Case Study" rather than a statistical survey.

## 4. Statistical Rigor & Limitations

### 4.1 Multiple Comparison Correction
Since multiple tests (power spectrum bins, void size bins) are performed, the plan explicitly implements the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR) or Bonferroni for family-wise error rate, as required by FR-006.

### 4.2 Sample Size & Power (Critical Limitation)
- **Justification**: The spec assumes 5 realizations for power ≥ 0.80. However, the CI constraints (12h, 7GB RAM) limit us to **N=1** (one paired run).
- **Power Limitation**: With N=1, it is **impossible** to estimate the variance of the 'delta' distribution. Therefore, standard hypothesis testing (p-values for significance) is **statistically invalid**.
- **Resolution**: The plan reframes the Success Criteria (SC-001, SC-002) as **Diagnostic Checks**. The output will include the KS/Chi-squared statistic and p-value, but the interpretation is explicitly limited to "Descriptive Metric of Deviation" rather than "Statistical Significance". The plan acknowledges that N=1 has **zero statistical power** to distinguish the anomaly signal from cosmic variance.
- **Spec-Root Cause Flag**: The spec's Success Criteria (SC-001, SC-002) explicitly mandate "output the p-value" implying statistical significance. This contradicts the N=1 limitation. The plan implements the output as a diagnostic metric but flags this as a "Spec-Root Cause" contradiction requiring a kickback to update the spec text to reflect the "Diagnostic Metric" nature.
- **Mitigation**: The Phase-Injected Mode strategy maximizes the signal-to-noise ratio on the specific spatial modes of interest, but the lack of ensembles remains a fundamental limitation.

### 4.3 Causal Inference
The study is **observational**. The CMB anomalies are not randomized; they are features of our specific universe. Therefore, the plan strictly frames all claims as **associational** (FR-007). No causal claims (e.g., "The Cold Spot *caused* X void distribution") will be made.

### 4.4 Measurement Validity
- **Instruments**: Planck PR3 Commander/SMICA maps are the gold standard for CMB temperature anisotropies.
- **Validation**: The plan validates the maps by comparing the calculated power spectrum to the official Planck 2018 results (Planck 2018 Results Paper VII) for ℓ ≤ 30.

### 4.5 Predictor Collinearity
The anomaly-modified power spectrum is derived from the standard ΛCDM spectrum by injecting specific phases. The predictors (anomaly modes) are not independent of the background cosmology. The plan will report the relationship descriptively and acknowledge the collinearity in the interpretation of the delta values.

### 4.6 Finite Volume Confound
- **Issue**: The CMB quadrupole (ℓ=2) has a wavelength ~18,000 Mpc/h. The simulation box cannot contain this mode.
- **Approximation**: The anomaly is injected as a **local gradient** or a low-k mode that fits within the box. This simulates the *local effect* of the anomaly, not the global mode.
- **Limitation**: This is a known finite volume confound. The results are interpreted as "Local Gradient Effect" rather than "Global Mode Propagation".

## 5. Compute Feasibility Plan

- **Hardware**: GitHub Actions free-tier (multi-core CPU, limited RAM, 14GB Disk).
- **Strategy**:
 - **No GPU**: All simulations run on CPU.
 - **Memory Management**: The 128³ particle simulation is designed to fit within 7GB RAM. If memory usage spikes, the code will stream data or reduce the particle count (with a note in the results).
 - **Runtime**: The time limit is tight. The plan prioritizes the simulation of the anomaly and control runs. If the runtime is exceeded, the simulation will be aborted, and the error logged.
 - **Libraries**: `nbodykit` is preferred over GADGET-2 if it offers a more Pythonic, memory-efficient interface for small boxes. If GADGET-2 is required for accuracy, it will be compiled with OpenMP for CPU parallelization.

## 6. Decision Rationale

- **Why Phase-Injected Mode?**: The Cold Spot is a specific spatial phase configuration, not a global amplitude change. Global modulation fails to test the specific anomaly hypothesis. Phase injection preserves the non-Gaussian spatial structure required for the Cold Spot test.
- **Why Finite Volume Approximation?**: The box cannot contain the full wavelength of the CMB quadrupole. The approximation simulates the *local gradient* effect, acknowledging the limitation.
- **Why Diagnostic Statistics?**: N=1 makes inferential statistics impossible. The p-values are descriptive metrics of deviation magnitude, not evidence of significance.
- **Why CPU-only?**: The target platform (GitHub Actions free-tier) has no GPU. The plan is designed to be CPU-tractable.
- **Why Downsized Simulation?**: 256³/500 Mpc/h exceeds CI constraints. 128³/250 Mpc/h is the maximum feasible configuration.