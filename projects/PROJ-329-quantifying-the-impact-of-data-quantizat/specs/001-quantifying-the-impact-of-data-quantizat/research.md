# Research: Quantifying the Impact of Data Quantization on Gravitational Wave Signal Reconstruction

## 1. Problem Statement
The primary research question is: **At what Signal-to-Noise Ratio (SNR) does data quantization noise become a dominant systematic bias in gravitational wave parameter estimation, exceeding the instrumental noise floor?**

This study focuses on Binary Black Hole (BBH) mergers with component masses 10-50 $M_\odot$ and distances 100-1000 Mpc. The impact is measured by comparing the Mean Squared Error (MSE) of recovered parameters (chirp mass, spin, distance) against a float64 (infinite precision) baseline.

## 2. Dataset Strategy

### 2.1 Noise Source (Instrumental Background)
The study requires realistic detector noise to simulate the "instrumental noise floor."
- **Source**: LIGO O3 Noise Power Spectral Density (PSD).
- **Verified URL**: `
- **Rationale**: This dataset is explicitly listed in the verified datasets block. It provides the necessary statistical properties of O3 noise for injection.
- **Access Method**: Load via `pandas.read_parquet` or `pyarrow`. The data will be converted to a time-series strain compatible with PyCBC's noise injection routines.
- **Constraint**: The dataset is large; only the necessary segment length (e.g., several seconds per injection) will be loaded into memory to fit the 7 GB RAM limit.

### 2.2 Waveform Generation (Synthetic Data)
No external dataset exists for "quantized GW signals" as this is a novel simulation.
- **Method**: Generate waveforms using `pycbc.waveform` with the `IMRPhenomPv2` approximant (standard for BBH).
- **Parameters**:
 - Masses: Uniform distribution [, 50] $M_\odot$.
 - Distance: Log-uniform [lower bound, 1000] Mpc.
 - Spins: Uniform distribution over a symmetric interval centered at zero.
 - SNR Target: Injected to achieve a moderate-to-high signal-to-noise ratio.
- **Baseline**: For every quantized signal, a float64 version is generated to serve as the ground truth for instrumental error.

### 2.3 Dataset Fit Verification
- **Requirement**: The noise dataset must contain sufficient duration and frequency resolution to support the 10-50 $M_\odot$ BBH merger frequencies (approx. 10Hz - 1000Hz).
- **Verification**: The HuggingFace parquet file is known to contain LIGO strain data. We will verify the sampling rate (typically high or intermediate rates) and frequency range during the `data_generation.py` initialization.
- **Gap Handling**: If the parquet file lacks the specific frequency range, we will fall back to generating a theoretical PSD using `pycbc.psd` calibrated to O3 sensitivity curves, as a last resort (though the verified source is preferred).

## 3. Statistical & Computational Methodology

### 3.1 Quantization Protocol
- **Bit Depths**: 1, 8, 10, 12, 14, 16 bits.
- **Method**: Uniform quantization over the dynamic range of the signal + noise.
 - $Q(x) = \text{round}(x \times 2^{N-1} / \text{max\_amp}) \times (\text{max\_amp} / 2^{N-1})$.
- **Edge Case**: 1-bit quantization (sign only) is included to test extreme signal loss.

### 3.2 Parameter Estimation (Inference)
- **Challenge**: Running full MCMC (PyCBC-Inference/Bilby) for [deferred] signals on a 2-core CPU within 6 hours is **not feasible**.
- **Solution**:
 1. **Sampling Strategy**: Instead of [deferred] signals, we will generate a **stratified sample** of a substantial number of signals.
 - A sufficient number of signals per SNR bin (e.g., 8-12, 12-16,..., 48-52).
 - A sufficient number of signals per bit depth (or a subset of bit depths at critical SNR ranges).
 2. **Inference Approximation**:
 - Use `bilby` with a **simplified likelihood** (e.g., fixed spin, reduced parameter space) or a **few-shot MCMC** (limited number of steps) to estimate the posterior mean and variance.
 - Alternatively, use a **Fisher Information Matrix** approximation for high-SNR signals to estimate errors rapidly, reserving MCMC for low-SNR/quantization-affected cases.
 - *Decision*: The plan will implement a **hybrid approach**: Fisher for SNR > 30 (where quantization is negligible), MCMC for SNR < 30 (where quantization matters). This ensures the 6-hour limit is met.
- **Causal/Associational**: This is a simulation study. The "cause" (quantization) is controlled. The "effect" (parameter bias) is measured directly. No observational confounding exists.

### 3.3 Error Metrics & Threshold Identification
- **Instrumental Error**: $E_{inst} = \text{MSE}(\text{float64\_recovered}, \text{truth})$.
- **Quantization Error**: $E_{quant} = \text{MSE}(\text{quantized\_recovered}, \text{truth})$.
- **Bias Metric**: $\Delta = E_{quant} - E_{inst}$.
- **Threshold Condition**: Identify SNR where $\Delta > 0.1 \times E_{inst}$.
- **Statistical Rigor**:
 - **Multiple Comparisons**: When testing multiple bit depths, we will use a Bonferroni correction or report family-wise error rates if hypothesis testing is performed.
 - **Power**: The sample size (N=500-1000) is chosen to detect a [deferred] difference in error with >80% power, assuming a moderate effect size (Cohen's d ~ 0.5).
 - **Collinearity**: SNR and Bit Depth are independent variables in the design. No collinearity issues expected.

## 4. Compute Feasibility Analysis
- **Runner**: GitHub Actions (2 CPU, 7 GB RAM).
- **Memory**:
 - Noise PSD: ~ MB.
 - Waveforms (batch of multiple): substantial data volume.
 - Inference (MCMC): ~GB per chain (parallelized).
 - **Total**: < 4 GB, safe margin.
- **Runtime**:
 - Generation: < 30 mins.
 - Inference (multiple signals, hybrid method): several hours.
 - Analysis/Plotting: < 30 mins.
 - **Total**: [deferred], within 6-hour limit.
- **GPU**: None required. All operations are CPU-native (numpy, scipy, bilby CPU mode).

## 5. Decision Log
| Decision | Rationale |
|:--- |:--- |
| **Hybrid Inference (Fisher + MCMC)** | Full MCMC for [deferred] signals exceeds 6h runtime. Fisher is valid for high-SNR; MCMC reserved for critical low-SNR/quantization zones. |
| **Stratified Sampling (N=500-1000)** | Replaces the spec's "10,000" target to meet CI constraints while maintaining statistical power for threshold detection. |
| **HuggingFace Parquet Source** | Only verified source for O3 noise. Avoids manual download/corruption risks. |
| **No 4-bit/8-bit LLMs** | Spec is about GW signal quantization, not LLMs. No deep learning models used. |
