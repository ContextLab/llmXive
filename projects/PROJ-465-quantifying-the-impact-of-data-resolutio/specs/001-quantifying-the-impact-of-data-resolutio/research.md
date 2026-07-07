# Research: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

## Research Question

How does reducing the sampling rate and bit depth of gravitational wave strain data degrade the accuracy of binary black hole mass and spin estimates?

## Background

Gravitational wave (GW) detectors like LIGO and Virgo record strain data at high sampling rates and high bit depths (typically standard floating-point precision). Storage and transmission constraints often necessitate downsampling and quantization. While the Nyquist theorem guarantees signal reconstruction if the sampling rate exceeds twice the highest frequency component, the *parameter estimation* (PE) accuracy—specifically for mass and spin—may degrade non-linearly as resolution decreases. This degradation could manifest as increased bias (systematic shift from ground truth) or inflated uncertainty (wider posteriors).

## Dataset Strategy

This project relies on verified gravitational wave event data from the Gravitational Wave Open Science Center (GWOSC) and simulated injections.

| Dataset Name | Description | Verified URL / Source | Usage |
|:--- |:--- |:--- |:--- |
| **GWOSC GW150914** | The first direct detection of GWs. High SNR (~24). Includes strain data and catalog parameters. | ` (via `gwpy` client) | Primary test case for downsampling and inference. |
| **GWOSC Catalog** | Official parameter estimates and uncertainties for confirmed events. | ` | Reference estimates for consistency checks (NOT ground truth). |
| **Simulated Injections** | Synthetic GW signals with known injected parameters. | Generated locally via `bilby`/`gwsignal` | Ground truth for Absolute Accuracy (Bias) calculation. |

*Note: No other datasets are used. All data is fetched programmatically via `gwpy` to ensure reproducibility and checksum verification.*

## Methodology

### 1. Data Acquisition & Preprocessing
- **Source**: `gwpy` fetches strain data for GW150914 (and potentially 1-2 other high-SNR events) from GWOSC.
- **Validation**: Checksums verified against GWOSC records.
- **Downsampling**: `scipy.signal.decimate` with anti-aliasing filter (IIR) applied to target rates: 4096 Hz, 2048 Hz, 1024 Hz.
- **Quantization**: Float data converted to Float16 (16-bit) and kept as Float32 (32-bit) to simulate storage constraints.

### 2. Parameter Estimation (Inference)
- **Pipeline**: `bilby` framework.
- **Waveform**: `IMRPhenomPv2` (phenomenological waveform approximant for precessing binaries).
- **Sampler**: `dynesty` (nested sampling) configured for CPU-only execution.
- **Convergence**:
 - Target: `dlogz` (evidence tolerance) < 0.1.
 - Hard Limit: A predefined maximum number of iterations.
 - **Inconclusive Flag**: If `dlogz` >= 0.1 after [deferred] iterations, the run is marked "inconclusive".
 - *Note: Gelman-Rubin is inapplicable to nested sampling and is not used.*

### 3. Metric Calculation
- **Divergence (Information Loss)**: Hellinger distance between the downsampled posterior and the high-resolution baseline posterior. This measures how much information is lost due to resolution reduction.
- **Consistency Deviation (Catalog Data)**: Absolute difference between the median of the downsampled posterior and the catalog reference estimate. This is reported as "Deviation from Baseline Estimate", NOT as "Bias from Truth", because catalog parameters are estimates, not ground truth.
- **Absolute Accuracy (Simulated Data ONLY)**: Bias calculated as the absolute difference between the median of the downsampled posterior and the *known injected parameters*. This is the only valid measure of "Bias".
- **Posterior Width Analysis**: Calculation of the ratio (Posterior Width / Prior Width) to measure how resolution loss increases uncertainty. Events with wide posteriors are *not* excluded; instead, this metric is analyzed as a primary outcome.
- **Trend Identification**: Aggregation across events to identify sampling rates where divergence or deviation increases significantly. The "[deferred] majority rule" is removed; instead, the analysis reports "Event-Specific Sensitivity" and visualizes trends.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: Since multiple sampling rates and bit depths are tested, the aggregation phase will apply a Bonferroni correction or report family-wise error rates where applicable to avoid false positives in trend identification.
- **Power/Sample Size**: The study is limited by the number of high-SNR events available in GWOSC (N=1-3). We will explicitly state the limitation and frame conclusions as "indicative trends for high-SNR events" rather than universal laws. The "[deferred] majority rule" is removed as statistically invalid for N<5.
- **Causal Inference**: This is an observational simulation study. We simulate resolution loss; we do not claim causal effects on real astrophysical events. Claims are restricted to "degradation of estimation accuracy under simulated conditions."
- **Measurement Validity**: `IMRPhenomPv2` is a standard, validated waveform model for binary black hole parameter estimation. `gwpy` and `bilby` are community-validated tools.
- **Collinearity**: Mass and spin parameters are correlated in GW data. The analysis will report joint posteriors and marginal distributions, acknowledging that independent bias estimates for mass and spin are descriptive, not independent causal claims.

## Compute Feasibility (CPU-Only)

- **Constraints**: GitHub Actions free tier (2 CPU, 7 GB RAM, 6h limit).
- **Strategy**:
 - Use `dynesty` with a reduced number of live points (e.g., 50-100) to ensure convergence within 10,000 iterations on CPU.
 - Data subset: Only the short-duration window around the merger for a representative binary black hole event (approx. 4096 samples at 4096 Hz) to minimize I/O and memory.
 - No GPU acceleration; all operations use standard `numpy`/`scipy` CPU paths.
 - `bilby` configured to skip GPU checks.

## Decision Rationale

- **Waveform Choice**: `IMRPhenomPv2` chosen for computational efficiency on CPU compared to full numerical relativity surrogates, while maintaining sufficient accuracy for mass/spin estimation in high-SNR regimes.
- **Metric Choice**: Hellinger distance is preferred over KL divergence as it is symmetric and bounded, making it suitable for comparing posteriors with potentially different support or heavy tails.
- **Inconclusive Handling**: Explicitly handling the [deferred]-iteration limit as "inconclusive" (per corrected methodology) prevents reporting biased results from non-converged chains, maintaining statistical integrity.
- **Sampler Choice**: `dynesty` is chosen over `emcee` because it is more efficient for high-dimensional GW parameter spaces and has a well-defined convergence metric (`dlogz`) that does not require Gelman-Rubin.

## References

1. **GWOSC**: The Gravitational Wave Open Science Center. `
2. **Bilby**: Ashton, G., et al. "Bilby: A user-friendly Bayesian inference library for gravitational-wave astronomy." *The Astrophysical Journal Supplement Series* 241.2 (2019): 27.
3. **IMRPhenomPv2**: Khan, S., et al. "Phenomenological model for the gravitational wave signal from precessing binary black holes." *Physical Review D* 93.4 (2016): 044007.
4. **GW150914**: Abbott, B. P., et al. "Observation of Gravitational Waves from a Binary Black Hole Merger." *Physical Review Letters* 116.6 (2016): 061102.
5. **Dynesty**: Speagle, J. S. "dynesty: a dynamic nested sampling package for estimating Bayesian posteriors and evidences." *Monthly Notices of the Royal Astronomical Society* 493.3 (2020): 3132-3158.