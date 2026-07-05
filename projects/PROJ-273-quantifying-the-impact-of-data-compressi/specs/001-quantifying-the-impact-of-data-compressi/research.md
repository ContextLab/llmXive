# Research: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

## 1. Problem Statement & Hypotheses

**Problem**: The storage and transmission of gravitational wave (GW) strain data often require compression. While lossless compression is standard, lossy techniques could offer significant bandwidth savings. However, the impact of lossy compression on the scientific utility of the data—specifically the accuracy of parameter estimation (mass, distance, spin) for Compact Binary Coalescence (CBC) events—is not fully quantified.

**Hypotheses**:
1.  **H1 (Lossless)**: Lossless compression (gzip, LZ4, bzip2) will result in zero reconstruction error (MSE = 0) and no statistically significant bias in parameter estimation compared to uncompressed data.
2.  **H2 (Lossy)**: Lossy compression will introduce measurable SNR degradation and parameter estimation bias, with the magnitude of bias increasing as the compression ratio increases (e.g., 4-bit > 8-bit > 16-bit).
3.  **H3 (Threshold)**: There exists a "tipping point" in lossy compression (e.g., 8-bit quantization or Wavelet thresholding > 90%) beyond which the parameter estimation bias exceeds acceptable scientific thresholds.

## 2. Dataset Strategy

**Constraint**: The "Verified datasets" block contains no Gravitational Wave data. Public GWOSC archives host *detected* events (inferred parameters), not *injection campaigns* with ground truth.

**Strategy**:
1.  **Synthetic Injection**: Use `LALSimulation` to generate CBC waveforms with **known ground truth** parameters (Mass, Spin, Distance).
2.  **Noise Injection**: Inject these synthetic signals into real GW noise fetched from the GWOSC API (e.g., O3 data segments).
3.  **Validation**: Ensure injected signals have SNR > 8 and complete metadata.
4.  **External Baseline**: The `Bias_Original` baseline will be derived from a pre-converged run on an external resource (or a high-fidelity public posterior) to avoid CI convergence issues.

**Critical Data Mismatch Resolution**:
-   **Issue**: No verified GW injection dataset exists.
-   **Resolution**: The project generates its own ground truth via `LALSimulation`. This satisfies FR-010 and SC-003 by providing known true parameters.
-   **Noise Source**: GWOSC API (programmatic access) is used for noise, as no verified static URL exists for GW noise segments.

**Dataset Variables**:
-   **Input**: Strain time series (Hz), Detector names (H1, L1, V1), Injection parameters (Mass1, Mass2, Spin1, Spin2, Distance).
-   **Output**: Compressed strain, Reconstructed strain, Posterior samples (Mass, Distance, Spin).

## 3. Methodology

### 3.1 Compression Pipeline
1.  **Lossless**: Apply `gzip` (levels 1, 5, 9), `lz4`, `bzip2` (levels 1, 5, 9).
2.  **Lossy**:
    -   **Quantization**: Float64 -> Float16, Float8, Float4 (bit-packing).
    -   **Wavelet Thresholding**: Apply Daubechies wavelets (db4) with soft thresholding at 50%, 75%, 90% retention.
    -   **JPEG2000 (Folding Experiment)**: To satisfy FR-003, the 1D strain signal will be folded into a 2D matrix (e.g., using a Hilbert curve or simple row-major folding) before applying JPEG2000 compression. The reconstruction error will include artifacts from both the compression and the folding/unfolding process. This is explicitly labeled as a "Transformation+Compression" artifact in the results.
3.  **Metrics**:
    -   **MSE**: Mean Squared Error between original and reconstructed.
    -   **SNR Degradation**: $\Delta SNR = SNR_{original} - SNR_{compressed}$.

### 3.2 Parameter Estimation (PE)
-   **Baseline**: `Bias_Original` derived from external pre-converged run (Phase 0.5).
-   **CI Execution**: `Bilby` with `Dynesty` nested sampler (Fast PE mode: 5000 samples, reduced likelihood evaluations).
-   **Input**: Original and Compressed strain files.
-   **Constraint**: Runtime capped at 2 hours/event. If non-converged, log as "Inconclusive" and exclude from bias calculation.

### 3.3 Statistical Analysis
-   **Primary Metric**: `Delta_Bias = Bias_Compressed - Bias_Original`.
    -   `Bias = |Posterior_Mean - True_Injection_Parameter|`.
-   **Test Protocol (FR-007 Compliance)**:
    1.  **Attempt**: Run a Hierarchical Bayesian Shift Test on `Delta_Bias` across compression levels.
    2.  **Convergence Check**: If the hierarchical model fails to converge or yields unstable hyperparameters (expected for N < 15), the system will automatically trigger the **Fallback Protocol**.
    3.  **Fallback**: Switch to Paired t-tests or Wilcoxon signed-rank tests to determine statistical significance.
    4.  **Reporting**: The final report will explicitly state that the Hierarchical test was attempted but failed due to sample size, and that the Fallback test was used for the primary conclusion. This satisfies the "MUST perform" requirement of FR-007 while maintaining statistical rigor.
-   **Correction**: Bonferroni or Benjamini-Hochberg for multiple comparisons.

## 4. Statistical Rigor & Limitations

-   **Multiple Comparisons**: With ~ events x ~10 compression levels x 3 parameters, ~90 tests. Family-wise error rate (FWER) control is mandatory.
-   **Power**: The sample size (N=3 events) is small. The study is underpowered for detecting small effect sizes. The Hierarchical Bayesian model is expected to fail convergence. The Fallback protocol (Paired tests) is used to ensure results are still reportable.
-   **Causal Framing**: This is an observational study of compression artifacts. Claims will be framed as "association between compression level and bias," not causal effects.
-   **Collinearity**: Compression levels are ordered. Independent effects cannot be claimed; trends will be reported descriptively.
-   **Measurement Validity**: SNR and posterior overlap are standard metrics in GW astronomy. `Delta_Bias` is the primary metric for compression impact.
-   **JPEG2000 Artifact**: The JPEG2000 results are confounded by the 1D-to-2D transformation. These results are reported separately as a "Proof-of-Concept for Folding" and are not compared directly to Wavelet/Quantization results for scientific utility.

## 5. Compute Feasibility (CI Constraints)

-   **Hardware**: 2 CPU, 7GB RAM, 14GB Disk.
-   **Strategy**:
    -   **No Full LALInference**: Replaced by `Bilby`/`Dynesty` for CI runs.
    -   **External Baseline**: `Bias_Original` is not run on CI to avoid convergence issues.
    -   **Fast PE**: Reduced iterations for CI runs; non-converged runs are excluded.
    -   **Memory**: Process one event at a time. Clear memory after each PE run.
    -   **No GPU**: Strictly CPU-only libraries.

## 6. Decision Rationale

-   **Why Synthetic Injection?** Public GWOSC data lacks ground truth. `LALSimulation` is required to satisfy FR-010 and SC-003.
-   **Why Bilby/Dynesty?** LALInference is too slow for CI. `Bilby` with `Dynesty` is a lighter-weight, CPU-optimized alternative that can produce approximate posteriors within the time limit.
-   **Why Wavelet Thresholding?** Wavelet thresholding is the standard 1D signal compression method for GW data.
-   **Why JPEG2000 Folding?** To satisfy FR-003, we implement a 1D-to-2D folding method. This is explicitly acknowledged as introducing transformation artifacts, distinguishing it from standard compression.
-   **Why Hierarchical Fallback?** The sample size (N<15) is insufficient for robust hierarchical inference. The plan attempts the test (per FR-007) but includes a fallback to Paired tests to ensure valid results are produced, documenting the limitation clearly.
-   **Why External Baseline?** CI hardware cannot produce converged posteriors in 4 hours. Using an external baseline isolates compression artifacts from PE algorithm uncertainty.