# Research: Quantifying the Impact of Data Resolution on Gravitational Wave Signal Detection

## 1. Dataset Strategy

### Verified Datasets
The project relies on real gravitational wave strain data from the **Gravitational Wave Open Science Center (GWOSC)**. The specific dataset URLs and access methods are:

| Dataset Name | Description | Verified URL / Access Method |
| :--- | :--- | :--- |
| **GWOSC O1/O2 Noise** | Clean, calibrated strain data from LIGO Hanford/Livingston and Virgo. | `gwosc` Python library (via `gwosc.api`). No direct raw URL required; fetched via API. |
| **GW150914 Event** | Reference event for template validation (optional). | `gwosc` library (event: `GW150914`). |

**Note**: The provided "Verified datasets" block in the prompt contains HuggingFace links for *JWST/High-SNR* data which are **irrelevant** to this gravitational wave project. The plan strictly adheres to the **GWOSC** requirement in the spec (US-2, FR-003). The `gwosc` library is the verified programmatic loader.

### Dataset Variable Fit
- **Required**: Strain time-series ($h(t)$), GPS time, sampling rate (native 16384 Hz or 4096 Hz).
- **Available**: GWOSC provides calibrated strain data at high sampling rates (up to 16384 Hz).
- **Fit Confirmation**: The dataset contains the exact variable needed (strain) at a resolution sufficient to down-sample to 4096 Hz and lower. No missing predictors.

## 2. Methodological Rigor

### Statistical Power & Sample Size (Two-Stage Pilot)
- **Goal**: Detect a [deferred] SNR degradation with power $\ge 0.8$ ($\alpha=0.05$).
- **Assumed Variance**: In the absence of prior data, we assume a conservative standard deviation of **$\sigma_{rel} = 0.05$** for the relative SNR degradation. This is a worst-case estimate based on typical GW noise fluctuations.
- **Pilot Strategy**:
  1.  **Stage 1**: Run a small pilot ($N=20$) at all resolution levels using the assumed $\sigma_{rel}=0.05$.
  2.  **Stage 2**: Calculate the empirical standard deviation ($\sigma_{emp}$) from the pilot. If $\sigma_{emp} > 0.05$, recalculate the required $N$ using the larger variance. If $\sigma_{emp} < 0.05$, proceed with the pilot $N$ (conservative) or a reduced $N$ if time permits.
  3.  **Execution**: Run the full study with the finalized $N$.
- **Constraint**: Due to the 6-hour CI limit, $N$ will be capped at 200 per resolution level. A sensitivity analysis will be reported if the theoretical $N$ exceeds this cap.
- **Stratification**: All power calculations and tests are performed within **SNR bins** (e.g., 8-12, 12-20, >20) to ensure the 5% degradation threshold is detectable across signal strengths.

### Multiple Comparisons & Trend Testing
- **Primary Hypothesis (Monotonic Decline)**: To test SC-001 (monotonic decline), we use the **Jonckheere-Terpstra test**. This non-parametric test is specifically designed for ordered alternatives (4096 > 2048 > ... > 256) and is more powerful than multiple pairwise t-tests.
- **Secondary Hypothesis (Pairwise)**: Welch's t-tests with Bonferroni correction ($\alpha_{adj} = 0.05/4 = 0.0125$) will be performed **only between adjacent resolutions** (4096 vs 2048, 2048 vs 1024, etc.). This reduces the number of comparisons from a higher count to a lower count, minimizing the penalty.
- **Normality Check**: Normality will be tested via Shapiro-Wilk. If normality fails (common for low SNR), the primary test for that bin switches to the **Mann-Whitney U test** (non-parametric) rather than treating it as a fallback.

### Causal/Associational Claims & Filter Correction
- **Nature**: Observational simulation. We are observing the *effect* of resolution on SNR in a controlled simulation.
- **Filter Confound Control**: The anti-aliasing FIR filter introduces amplitude attenuation. To isolate the effect of resolution from filter distortion:
  1.  The theoretical frequency response $H(f)$ of the FIR filter is calculated for each target resolution.
  2.  The injected waveform amplitude is pre-scaled by $1/|H(f_{peak})|$ before injection.
  3.  This ensures that any observed SNR degradation is due to the loss of high-frequency information (resolution), not the filter's attenuation.
- **Claim**: "Down-sampling causes SNR degradation" is a causal claim within the simulation context, valid because the only manipulated variable is the sampling rate, and filter effects are explicitly corrected.

### Measurement Validity
- **Instrument**: `pycbc.waveform` (IMRPhenomD or similar non-spinning model).
- **Validation**: Standard in the field; validated against numerical relativity simulations.
- **Re-weighted SNR**: Uses the corrected formula (Allen et al. 2012):
  $$ \hat{\rho} = \frac{\rho}{\sqrt{1 + \left(\frac{\chi^2}{df}\right)^2}} $$
  where $\chi^2$ is calculated with $p=16$ frequency bins, and $df = 2p - 2 = 30$.
  *Note: The source spec (FR-008) contains a malformed formula missing the leading '1'. The implementation will strictly follow the corrected Allen et al. (2012) formula.*

### Predictor Collinearity
- **Issue**: Mass and distance are independent parameters in the generation.
- **Note**: SNR is a function of both. We do not claim independent effects of mass on SNR degradation; we aggregate by mass bins.

## 3. Compute Feasibility & Resource Strategy

### Hardware Constraints
- **Target**: GitHub Actions Free Tier (2 vCPU, 7GB RAM, ~14GB Disk).
- **Risk**: `pycbc` can be memory-intensive if template banks are large.
- **Mitigation**:
  1.  **No GPU**: Use `pycbc` with `--cpu` flag (default).
  2.  **Resolution-Matched Template Bank**: Generate a **distinct template bank at EACH resolution level** (256, 512, etc.) covering only the specific injected mass range (10–50 M⊙). This prevents template mismatch errors.
  3.  **Chunking**: Process injections in batches of 10–20 to keep memory < 5GB.
  4.  **Sampling**: Down-sampled data (at a reduced sampling rate) is substantially smaller than 4096 Hz, reducing I/O and memory pressure.

### Library Selection
- `pycbc`: Core waveform and matched-filter engine.
- `scipy.signal`: FIR filter design (`firwin`) and resampling.
- `gwosc`: Data fetching.
- `memory-profiler`: CPU/Memory profiling.
- `scipy.stats`: Jonckheere-Terpstra test implementation.

## 4. Computational Task Ordering

1.  **Fetch Noise**: Download GWOSC segments (10–30s) to `data/raw/`.
2.  **Generate Waveforms**: Create 4096 Hz waveforms for all mass/distance combinations.
3.  **Down-sample**: Apply FIR filter, calculate amplitude correction factor, and resample to 2048, 1024, 512, 256 Hz.
4.  **PSD Re-estimation**: Estimate the Power Spectral Density (PSD) from the **down-sampled** noise segment for each resolution.
5.  **Template Bank Generation**: Generate a template bank at the **specific resolution** of the data being filtered.
6.  **Inject**: Add corrected waveforms to noise at random offsets.
7.  **Matched Filter**: Run `pycbc` matched filter using the resolution-matched template bank and PSD.
8.  **Profile**: Record CPU time and memory peak for each resolution.
9.  **Analyze**: Compute detection rates, Jonckheere-Terpstra tests (stratified by SNR), and plots.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **CI Timeout (>6h)** | High | Limit number of injections; use smaller template bank; parallelize independent injections (if allowed). |
| **Memory Overflow** | High | Process in small batches; stream data; **abort job if >6GB** (hard stop). |
| **Aliasing Artifacts** | High | Strict verification of filter cutoff; check spectral content (SC-004). |
| **Glitch Contamination** | Medium | Use re-weighted SNR; exclude segments with known glitches (if metadata available). |
| **Filter Distortion** | Medium | **Amplitude correction** applied to injected signal to isolate resolution loss. |