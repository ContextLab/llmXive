# Research: Quantifying the Impact of Data Resolution on Simulated Fluid Turbulence

## Dataset Strategy

The analysis relies on high-resolution isotropic turbulence snapshots from the Johns Hopkins Turbulence Database (JHTDB). To ensure reproducibility and compliance with the "Verified Accuracy" constitution, we will utilize the verified HuggingFace mirrors of JHTDB data.

| Dataset Name | Source URL (Verified) | Format | Variables Available | Relevance to Study |
| :--- | :--- | :--- | :--- | :--- |
| JHTDB Isotropic 1024³ | `https://huggingface.co/datasets/thuerey-group/jhtdb-isotropic-turbulence-1024/resolve/main/coarse_t420.hdf5` | HDF5 | 3D Velocity fields ($u, v, w$) | Primary ground truth for 1024³ resolution. |
| JHTDB Metadata | `https://huggingface.co/datasets/dl2-g32/jhtdb/resolve/main/datasets/jhtdb/large_100/metadata_test.csv` | CSV | Snapshot IDs, Reynolds numbers, Grid sizes | Used to select snapshots with sufficient inertial subranges. |

**Dataset Selection Criteria**:
1.  **Reynolds Number**: Snapshots must have a Taylor microscale Reynolds number ($Re_\lambda$) high enough to exhibit a clear $-5/3$ inertial subrange. If the inertial subrange is non-existent (edge case), the system will flag the result as "Inertial Subrange Not Resolved" rather than fitting a spurious power law.
2.  **Grid Size**: Primary analysis on 1024³ grids. 2048³ grids will be avoided unless they can be processed slice-by-slice without exceeding 7 GB RAM; otherwise, 1024³ is the ground truth.
3.  **Quantity**: 5 independent snapshots will be selected to enable bootstrap resampling for confidence intervals (FR-006).

**Memory Feasibility**:
A full 1024³ grid of float32 velocity components (3 components) requires $1024^3 \times 3 \times 4$ bytes $\approx 12$ GB. This exceeds the 7 GB RAM limit.
*   **Strategy**: The `download.py` and `downsample.py` scripts will implement **slice-by-slice processing**. Data will be read in chunks (e.g., 64 slices at a time) into memory, processed, and immediately written to disk or aggregated into statistics. This ensures peak RAM usage remains well below 7 GB.
*   **Fallback**: If a specific snapshot cannot be processed via slicing within the time limit, it will be excluded, and the count reduced to 4 or 3, with the runtime impact documented.

## Statistical Methodology

### 1. Fourier-Mode Truncation (Downsampling)
To generate synthetic lower-resolution data, we apply a sharp spectral filter (Fourier truncation).
*   **Method**: Compute 3D FFT of the velocity field. Zero out all modes where the wavenumber magnitude $k > k_{Nyquist}^{downsampled}$. Inverse FFT to obtain the downsampled field.
*   **Anti-Aliasing**: Strict truncation prevents aliasing by definition (high frequencies are removed, not folded). This satisfies the edge case requirement.
*   **Factors**: 2, 4, 8, 16.

### 2. Energy Spectrum $E(k)$
*   **Definition**: $E(k) = \frac{1}{2} \sum_{k \le |\mathbf{k}| < k+dk} |\hat{\mathbf{u}}(\mathbf{k})|^2$.
*   **Computation**: Binned 3D FFT magnitudes.
*   **Bias Metric**: Relative bias = $(E_{down}(k) - E_{true}(k)) / E_{true}(k)$.
*   **Validity Constraint**: Bias is calculated **only** for $k \le k_{Nyquist}^{downsampled}$. For $k > k_{Nyquist}^{downsampled}$, $E_{down}(k)$ is mathematically zero, and the bias would be -100% by definition. These regions are excluded from the bias curve to avoid tautological results.

### 3. Structure Functions $S_p(r)$
*   **Definition**: $S_p(r) = \langle |(\mathbf{u}(\mathbf{x} + \mathbf{r}) - \mathbf{u}(\mathbf{x})) \cdot \hat{\mathbf{r}}|^p \rangle$.
*   **Computation Strategy**:
    *   **$S_2(r)$**: Computed via **FFT-based convolution** (Wiener-Khinchin theorem) to avoid $O(N^6)$ complexity. This reduces complexity to $O(N^3 \log N)$ and fits within 2-core CPU limits.
    *   **$S_3(r)$**: Computed via **sparse-grid sampling** of separation vectors to maintain feasibility while preserving statistical accuracy for the inertial subrange.
*   **Scaling Exponents**: Fit $\log(S_p(r)) = \zeta_p \log(r) + C$ in the inertial subrange.
*   **Gibbs Phenomenon Mitigation**: A **Valid Fitting Range** is defined. Scales $r < 2 \times \text{grid\_spacing}_{downsampled}$ are explicitly excluded from power-law fitting to avoid artifacts introduced by the sharp spectral filter.
*   **Theoretical Comparison**: Compare $\zeta_2$ to $2/3$ and spectral slope to $-5/3$.

### 4. Bootstrap Resampling
*   **Method**: Block bootstrap across the 5 independent snapshots.
*   **Iterations**: 1000.
*   **Limitation Acknowledgement**: With N=5, the bootstrap distribution will be sparse. 95% Confidence Intervals will be reported but flagged as "Low Power" and interpreted as descriptive bounds rather than rigorous inferential statistics.
*   **Fallback**: If the bootstrap distribution is too unstable (e.g., >50% of iterations fail to converge), a parametric uncertainty estimation (bootstrapping residuals) will be used instead.

### 5. Ground Truth Definition
*   **Clarification**: The "ground truth" is defined as the highest available resolution dataset (1024³) in this study. We explicitly acknowledge that 1024³ simulations exhibit finite-Reynolds-number effects and numerical dissipation at the highest resolved wavenumbers.
*   **Implication**: The bias measured is "Relative Bias against the Best Available Proxy." The study does not claim to measure absolute physical truth, but rather the systematic error introduced by resolution reduction relative to the 1024³ baseline.

## Computational Feasibility & Constraints

*   **Runtime**: The plan targets ≤ 6 hours.
    *   FFT of a high-resolution grid on 2 cores takes ~1-2 minutes per snapshot.
    *   5 snapshots $\times$ 4 resolutions $\times$ (FFT + Stats) $\approx$ 40-60 minutes for computation.
    *   Bootstrap (multiple iterations) over 5 snapshots is the heaviest step. We will parallelize the iterations across the 2 cores (equally distributed) to minimize wall-clock time.
*   **Memory**: Strictly enforced via chunked I/O. No full array allocation.
*   **Libraries**: `numpy` (CPU), `scipy` (CPU), `h5py` (streaming). No `torch` or GPU-specific libraries.

## Risk Assessment

| Risk | Probability | Mitigation |
| :--- | :--- | :--- |
| **Inertial Subrange Not Resolved** | Medium | Check spectral slope before fitting. If $R^2 < 0.9$ or slope deviates significantly, flag as "N/A" rather than fitting. |
| **Memory Overflow** | Low | Use `h5py` chunked reads. Add explicit `psutil` checks; abort if RSS > 6.5 GB. |
| **Runtime Exceeds 6h** | Medium | Reduce bootstrap iterations to 500 if initial runs show > 3h per snapshot. Document this reduction in the paper. |
| **Dataset Unavailable** | Low | Use the verified HuggingFace mirrors. If one fails, fall back to the other or skip that snapshot. |
| **Statistical Power (N=5)** | High | Explicitly label CIs as "Low Power" and use parametric fallback if necessary. |

## Conclusion

The proposed methodology is robust, reproducible, and strictly adheres to the CPU-only, 7 GB RAM constraints. By using Fourier truncation, FFT-based structure function computation, and slice-by-slice processing, we can generate controlled ground truth variants and quantify resolution bias without fabricating results. The use of bootstrap resampling across multiple snapshots ensures statistical rigor, with explicit caveats regarding sample size limitations.