# Research: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

## Objective
To determine the threshold of data compression (lossless vs. lossy) at which gravitational wave parameter estimation (mass, distance, spin) becomes statistically biased compared to uncompressed data. The study uses **two distinct workflows**:
1. **Real GW Events**: Measures **Posterior Instability** (distributional shift) via KL divergence.
2. **Simulated Injections**: Measures **Parameter Bias** (systematic error) via MAE against ground truth.

## Dataset Strategy

| Dataset Name | Source/Loader | Verification Status | Usage |
|--------------|---------------|---------------------|-------|
| GWOSC CBC Events (O3a/O3b) | GWOSC Catalog URLs: ` and ` | **Verified** (Official GWOSC Release Pages) | Primary real-world data for compression testing (US-1). |
| Simulated Injections (Ground Truth) | Generated via `lalsimulation` (O3b CBC Population Model) | **Verified** (Reference: `LIGO-P2100123-v15` O3b Population) | Ground truth for bias measurement (US-4). |
| Compression Validation (1D) | Generated via `lalsimulation` (Synthetic Strain) | **Verified** (Internal Generation) | Used to validate JPEG2000 and quantization pipelines on 1D-like data (spectrograms). |

**Note on GWOSC**: Data is accessed via the `gwosc` Python package, which queries the official API endpoints linked to the verified O3a/O3b catalogs.

## Dataset-Variable Fit Analysis

- **Required Variables**: Strain time series (h(t)), detector network (LLO, LHO, V1), event timestamp, parameter posteriors (mass, distance, spin components).
- **GWOSC Availability**: The `gwosc` API provides strain data and event metadata. However, **full 3D spin reconstruction is not supported** by standard public data; only effective spin parameters (`chi_eff`, `chi_p`) are available.
 - *Mitigation*: The plan explicitly flags this limitation (FR-008) and limits analysis to available spin parameters.
- **Simulated Injections**: Generated with full ground-truth parameters (mass, distance, full spin vector) using the **O3b CBC population model** to ensure representativeness. This allows precise bias calculation (US-4).
- **JPEG2000 Fit**: JPEG2000 is a 2D image codec. To apply it to 1D GW strain, we convert the signal to a **spectrogram** (time-frequency representation) using `scipy.signal.spectrogram`. This ensures the compression artifacts are relevant to the signal modality.

## Statistical Rigor & Methodology

### Hypothesis Testing
- **Null Hypothesis ($H_0$)**: Compression method $C$ does not alter the posterior distribution or introduce bias compared to uncompressed data.
- **Test 1 (Real Events)**: **Repeated-measures ANOVA** on **KL Divergence** (Posterior Instability) across events for each parameter.
 - *Rationale*: KL divergence measures distributional shift, not bias. This test determines if compression causes significant instability in the posterior.
- **Test 2 (Injections)**: **Repeated-measures ANOVA** on **Mean Absolute Error (MAE)** (Parameter Bias) across events for each parameter.
 - *Rationale*: MAE measures systematic error against ground truth. This test determines if compression introduces significant bias.
- **Correction**: Bonferroni or Benjamini-Hochberg (FDR) correction applied for multiple comparisons across 3 parameters and multiple compression levels (SC-004).
- **Post-hoc**: If ANOVA is significant, pairwise **paired t-tests** with Bonferroni correction are performed.

### Power & Sample Size
- **Limitation**: With ~12 real events and 50 injections, the study is **underpowered** to detect very small effect sizes (<0.2 Cohen's d).
- **Acknowledgement**: Results will be framed as **estimation-focused** (reporting effect sizes and confidence intervals) rather than strict hypothesis testing for small effects. The power analysis (calculated in `code/05_analysis.py`) will be explicitly reported.
- **Strategy**: 50 injections are used to maximize power for the bias measurement (US-4), while real events are limited by data availability.

### Causal Framing
- **Observational**: Compression is applied systematically, but the "treatment" is algorithmic. Claims will be framed as "compression-induced bias" rather than causal effects of astrophysical phenomena.

### Measurement Validity
- **SNR**: Calculated via matched filtering with a template bank (LALInference standard).
- **Bias**: Measured as Mean Absolute Error (MAE) against ground truth for injections.
- **Instability**: Measured as KL divergence for real events (where ground truth is unknown).
- **Convergence**: Gelman-Rubin (R-hat) diagnostic used to ensure MCMC chains have converged (R-hat < 1.1). Events failing convergence are excluded from bias analysis.

## Computational Feasibility

- **Hardware Constraints**: 2 CPU cores, 7GB RAM, 6h time limit.
- **Strategy**:
 1. **Data Subsampling**: If a single event's waveform exceeds memory, the analysis will downsample the time series (preserving Nyquist frequency) or process in chunks.
 2. **LALInference CPU**: Use `lalapps` with `--cpu` flag. Minimum **[deferred]** iterations to ensure convergence.
 3. **No GPU**: All compression and statistical operations use CPU-native libraries (`numpy`, `scipy`, `glymur`, `lz4`, `bzip2`).
 4. **Parallelization**: Run compression of different events in parallel (using `multiprocessing`), but limit concurrency to 2 to avoid OOM.
 5. **Injection Generation**: Generate 50 injections in a batch to amortize overhead.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| Use `gwosc` API + Catalog URLs | API is canonical; URLs provide verified citation for the data source (O3a/O3b). |
| Simulated injections for ground truth | Real GW events lack known truth; injections allow precise bias measurement (US-4). |
| KL Divergence for real events | Allows comparison of distributions without a known "true" parameter value (measures instability). |
| MAE for injections | Allows direct measurement of bias against known ground truth. |
| CPU-only LALInference | Matches CI constraints; GPU acceleration is unavailable and unnecessary for small event sets. |
| Bonferroni Correction | Strict control of family-wise error rate required by SC-004. |
| [deferred] MCMC iterations | Required for posterior convergence (R-hat < 1.1) to ensure bias is not sampling noise. |
| 50 Simulated Injections | Required for statistical power to detect bias across the parameter space. |
| Spectrogram for JPEG2000 | JPEG2000 is 2D; GW strain is 1D. Spectrogram provides a domain-appropriate 2D representation. |
| Glymur for JPEG2000 | `Pillow` has limited JPEG2000 support; `glymur` is the standard Python library. |
| Numpy Quantization | No dedicated library for 4/8/16-bit float quantization; `numpy` is robust and standard. |