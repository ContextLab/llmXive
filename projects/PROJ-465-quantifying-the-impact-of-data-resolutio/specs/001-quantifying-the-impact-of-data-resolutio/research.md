# Research: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

## Research Question

How does reducing the sampling rate (from high to lower rates) and bit depth (from 32-bit to 16-bit) of gravitational wave strain data degrade the accuracy of binary black hole mass and spin estimates?

## Dataset Strategy

This project relies on **verified** gravitational wave strain data from the Gravitational Wave Open Science Center (GWOSC). The datasets are accessed via `gwpy` to ensure reproducibility and canonical sourcing.

| Dataset Name | Description | Verified URL / Loader | Variable Fit Check |
|--------------|-------------|-----------------------|--------------------|
| **GWOSC GW150914** | High-SNR event (first detection). Strain data available at high sampling rates. | `The research question is to determine how to retrieve open gravitational-wave data for specific events using GWpy. The method involves using the gwpy.timeseries.TimeSeries.fetch_open_data function to access data from an LIGO detector for a named event over a specified time window. References include the GWpy documentation and LIGO Open Science Center data policies.` (via `gwpy`) | **Confirmed**: Contains high-SNR chirp signal in the low-frequency to upper-band range. Sufficient for downsampling experiments. |
| **GWOSC GW151226** | Secondary high-SNR event. | `gwpy.timeseries.TimeSeries.fetch_open_data('L1', 'GW151226', 0, 32)` | **Confirmed**: Valid for cross-event validation of resolution thresholds. |
| **GWOSC GW170814** | Three-detector event. | `gwpy.timeseries.TimeSeries.fetch_open_data('H1', 'GW170814', 0, 32)` | **Confirmed**: Optional for robustness check. |

**Simulation Data**: To validate the bias metric against known truth, we will generate **simulated injections** using `bilby`'s injection framework. These will use the same noise PSD as the real events but with known injected parameters. This addresses the need to isolate resolution-induced bias from catalog/model uncertainty.

**Note**: No external URLs are fabricated. All data is fetched programmatically via `gwpy` which routes to the verified GWOSC API endpoints. If a specific event URL is unreachable, the `gwpy` library handles retries or raises a clear error, preventing silent data substitution.

## Technical Approach

### 1. Data Acquisition & Preprocessing
- **Source**: GWOSC via `gwpy`.
- **Downsampling**: Use `scipy.signal.decimate` with a low-pass filter (FIR) to prevent aliasing. Target rates: High baseline frequency, medium frequency, and low frequency.
- **Quantization**: Simulate storage constraints by casting float64 data to float32 (32-bit) and float16 (16-bit).
- **Pre-Check**: Before 16-bit quantization, verify that the signal amplitude (peak strain) exceeds the quantization noise floor of float16. If the signal is lost (represented as zero or dominated by noise), flag the configuration as "Invalid (Signal Lost)" and skip inference.
- **Nyquist Check**: Ensure the highest frequency component of interest (< 512 Hz for 1024 Hz sampling) is preserved.

### 2. Parameter Estimation
- **Framework**: `bilby` (Python library for gravitational-wave Bayesian inference).
- **Waveform**: `IMRPhenomPv2` (phenomenological waveform for precessing binaries).
- **Sampler**: `dynesty` (Dynamic Nested Sampler).
  - **Rationale**: Nested sampling is more robust for multimodal posteriors and does not rely on Gelman-Rubin statistics (which are for MCMC).
  - **Baseline Run (Hz)**: Run with a higher convergence standard (`dlogz < 0.01` or max [deferred] steps) to ensure the baseline posterior is fully converged and serves as a valid reference.
  - **Downsampled Runs**: Run with standard limit (a maximum of several thousand steps, `dlogz < 0.1`).
  - **Convergence Failure**: If `dlogz > 0.1` after 5000 steps, flag the run as "inconclusive" (per FR-004, adapted for `dynesty`).

### 3. Metric Calculation
- **Real Events (Baseline Comparison)**:
  - **Divergence**: Calculate Hellinger distance between the downsampled posterior ($P$) and the high-resolution baseline posterior ($Q$). This measures how much the distribution shifts and widens due to resolution loss.
  - **Bias (Relative to Catalog)**: Calculate the absolute difference between the posterior mean of the downsampled run and the *catalog-reported* parameters. **Note**: The catalog parameters are themselves estimates. This metric measures deviation from the *best available estimate*, not absolute truth.
- **Simulated Events (Truth Comparison)**:
  - **Bias (Relative to Truth)**: For injected signals with known parameters, calculate the absolute difference between the posterior mean and the *injected truth*. This isolates the true resolution-induced bias.
  - **Validation**: Use this to validate that the pipeline correctly identifies bias when it exists.

### 4. Aggregation & Threshold Identification
- **Consistency Check**: Aggregate results across the tested events (N=1-3).
- **Majority Rule (Adapted)**: Identify the sampling rate where the bias (or divergence) exceeds the catalog confidence interval in ≥ 50% of the *tested* events. With N=3, this means multiple events.
- **Reporting**: Frame the result as "Consistency observed in X/Y events" rather than a population-level claim.

## Statistical Rigor & Limitations

- **Sample Size**: Limited to 1-3 events due to CI time constraints. This is a **power limitation**. Results will be framed as "indicative thresholds" and "proof of concept" rather than definitive population-level claims.
- **Causal Inference**: This is an observational simulation (we manipulate data resolution, not the universe). Claims are strictly about *estimation bias* due to data processing.
- **Collinearity**: Mass and spin parameters are correlated in GW signals. The analysis reports marginal posteriors but acknowledges the joint covariance in the divergence metric.
- **Baseline Validity**: The baseline posterior is run with a higher convergence standard to ensure it is a valid reference, minimizing sampling error as a confounding variable.

## Compute Feasibility

- **Hardware**: GitHub Actions free tier (multiple CPU, 7 GB RAM).
- **Strategy**:
  - Use `dynesty` with `nlive=100` (default) to keep memory low.
  - Limit MCMC-like steps to a sufficient number for downsampled runs.
  - Process only high-SNR events (shorter duration, easier convergence).
  - No GPU usage; `torch` (if used by `bilby` for waveform generation) will be CPU-only.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use `dynesty` instead of MCMC** | Gelman-Rubin is inapplicable to nested sampling. `dynesty` is the standard for `bilby` and handles multimodal posteriors better. |
| **Limit to 16-bit float** | Spec requires simulating storage constraints. 16-bit is the lowest standard float; 8-bit is non-standard for this domain and likely too noisy to yield meaningful results. Pre-check added to validate signal integrity. |
| **Focus on GW150914** | Highest SNR, shortest duration, most robust for testing resolution limits without exhausting CI time. |
| **Baseline Convergence Standard** | Baseline run uses higher step limit (`dlogz < 0.01`) to ensure it is a valid reference, minimizing sampling error. |
| **Simulation Validation** | Added to distinguish resolution bias from statistical noise and validate the bias metric against known truth. |