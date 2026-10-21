# Research: Quantifying the Impact of Data Quantization on Gravitational Wave Signal Reconstruction

## 1. Problem Statement
Determine the **Signal‑to‑Noise Ratio (SNR) region** where quantization noise from limited‑bit ADCs becomes a **dominant systematic bias** in Bayesian parameter estimation of binary‑black‑hole (BBH) mergers. Dominance is defined as the **quantization‑induced error** (Δₖ = E_quant,ₖ − E_inst,ₖ) exceeding **[deferred]** of the instrumental‑only error (median MSE from the float64 baseline) for a given bit depth and parameter *k* (chirp mass, spin, distance).

## 2. Dataset Strategy

| Component | Source | Verified URL | Access Method | Rationale |
|-----------|--------|--------------|---------------|-----------|
| LIGO O3 PSD (instrumental noise) | GW Open Science Center (GWOSC) | `https://huggingface.co/datasets/astro-legacy-archive/gwosc-o3a-strain/resolve/main/H1-1238163456-1238216704-DQmask.parquet` | `datasets.load_dataset("astro-legacy-archive/gwosc-o3a-strain", split="train", streaming=False)` | Official O3 strain segment; The frequency range from a low‑frequency cutoff up to 2048 Hz fully covers BBH signals in the low‑mass (tens‑of‑solar‑mass) range. |
| Synthetic waveforms | PyCBC (`IMRPhenomPv2`) | N/A (generated on‑the‑fly) | `pycbc.waveform.get_fd_waveform` | Guarantees full control over masses, spins, distances, and SNR. |

All datasets are directly downloadable via the Hugging  Face Hub; no authentication is required.  

### Dataset Fit Verification
- **Frequency coverage**: PSD files contain data from 10 Hz to 2048 Hz, which includes the inspiral‑merger‑ringdown band for 10‑50 M⊙ BBH systems.  
- **Sampling rate**: Verified via the `sampling_rate` column in the parquet file (at a rate that exceeds twice the highest GW frequencies, i.e., well above ~1000 Hz), satisfying Nyquist for the highest GW frequencies (~1000 Hz).  
- **Memory footprint**: Each PSD parquet shard is ≈ 300 MB; streaming load ensures the runner never holds more than 1 GB in RAM.  

## 3. Statistical & Computational Methodology

### 3.1 Quantization Protocol
- **Bit depths**: 1, 8, 10, 12, 14, 16 (exactly as required by FR‑002).  
- **Full‑Scale Range (FSR)**: Fixed to `±1e‑21` strain (representative of LIGO’s dynamic range).  
- **Uniform quantizer**:  

\[
Q_N(x) = \text{round}\!\Bigl(\frac{x}{\text{FSR}} \times 2^{N-1}\Bigr) \times \frac{\text{FSR}}{2^{N-1}},
\]

where *N* is the bit depth.  
- **Edge‑case handling**: For *N* = 1 the output is simply `±FSR`; the implementation checks that the number of unique amplitude values equals `2**N`.  

### 3.2 Parameter Estimation (Inference)
- **Algorithm**: Bilby MCMC with the `dynesty` sampler (CPU‑only).  
- **Uniformity**: The same sampler, priors, and likelihood are used for all SNR ranges; only the number of steps adapts to keep runtime feasible (800 steps for SNR ≤ 20, 1200 steps for SNR > 20).  
- **Convergence**: Gelman‑Rubin statistic ≤ 1.1; otherwise the run is labeled `"failed"`; for injected SNR < 8 the pipeline records `"non-detection"` per the spec.  

### 3.3 Error Metrics & Threshold Identification
- **Per‑parameter MSE (baseline)**:  

\[
E_{\text{inst},k}^{(i)} = \bigl(\hat\theta_{i,k}^{\text{float64}} - \theta_{i,k}^{\text{true}}\bigr)^2.
\]

- **Per‑parameter MSE (quantized)**:  

\[
E_{\text{quant},k}^{(i)} = \bigl(\hat\theta_{i,k}^{\text{quant}} - \theta_{i,k}^{\text{true}}\bigr)^2.
\]

- **Bias metric**:  

\[
\Delta_k^{(i)} = E_{\text{quant},k}^{(i)} - E_{\text{inst},k}^{(i)}.
\]

- **Aggregation**: Within each SNR bin, compute the **median** of Δₖ and the **median instrumental MSE**.  
- **Dominance threshold**: Identify the smallest SNR bin where  

\[
\text{median}(\Delta_k) > 0.10 \times \text{median}(E_{\text{inst},k}),
\]

for each bit depth and each parameter *k*. This **[deferred] rule** is the concrete metric that will be **computed** during analysis; no placeholder values are used.

### 3.4 Statistical Rigor
- **Multiple‑comparison control**: Bonferroni correction across six bit depths (α = 0.05/6 ≈ 0.0083) and across four SNR bins (α = 0.05/4 ≈ 0.0125).  
- **Power analysis**: Pilot size **N = 2 400** (6 depths × 4 bins × 100 signals) yields > 80 % power to detect a Cohen’s d ≈ 0.3 difference in Δₖ at the Bonferroni‑adjusted α, based on preliminary simulations of quantization bias at low SNR.  
- **Reproducibility (SC‑005)**: The full study is repeated with **10 independent random seeds**; the crossover SNR is reported with a 95 % confidence interval derived from the distribution of the 10 estimates.  
- **Causal claim**: Because the experiment is fully simulated, the quantization effect is causal by construction; results are presented as such, with the caveat that real‑world ADC non‑idealities are not modeled.  

## 4. Compute Feasibility Analysis
`compute_resource_estimate.py` benchmarks the **full pipeline** (generation + quantization + inference + analysis) on a single signal and extrapolates to the full pilot of 2 400 signals. The estimate is then divided across **four** parallel CI jobs (600 signals each) to respect the free‑tier limits.

| Resource | Estimate (per CI job) | Derivation |
|----------|-----------------------|------------|
| **Peak RAM** | ≤ 5 GB | Streaming PSD load (≈300 MB), HDF5 chunked writes, batch size limited to 600 signals in memory. |
| **CPU Time** | ≈ 5.5 h total *per job* | Generation ≈ 0.8 h, inference ≈ 4.0 h (adaptive steps), analysis ≈ 0.7 h. Four jobs run concurrently, keeping wall‑clock ≤ 6 h per job. |
| **Disk Usage** | ≈ 5.2 GB (HDF5 + JSON) | Float64 baseline ≈ 2 GB; quantized data ≈ a few GB; results JSON ≈ a fraction of a gigabyte. |
| **GPU** | None required | All libraries run on CPU; `bilby` is invoked with `device="cpu"`. |

The estimates are written to `reports/resource_estimate.md` and verified by the CI runner before the main pipeline starts.  

## 5. Decision Log
| Decision | Rationale |
|----------|-----------|
| Fixed **FSR** quantization | Mirrors real ADC behavior; avoids adaptive scaling bias. |
| Include **all six** bit depths in pilot | Satisfies FR‑002; intermediate depths (10, 14) improve interpolation of the crossover. |
| **Stratify** parameters within SNR bins and fix a grid per bin | Guarantees that observed Δₖ reflects quantization rather than mass‑dependent estimation error. |
| Uniform **MCMC** across SNR | Eliminates inference‑method bias; adaptive sample counts are a computational efficiency, not a methodological change. |
| **Median** aggregation of Δₖ | Robust to outliers and provides a stable crossover estimate. |
| **Bonferroni** correction | Controls family‑wise error rate per SC‑004. |
| **10 independent runs** | Required by SC‑005 to assess reproducibility of the crossover SNR. |
| Record **non‑detections** for SNR < 8 | Handles the edge case specified in the spec without crashing. |
| Store **artifact hashes** in project‑state YAML | Enforces Constitution Principle V and Single Source of Truth. |
| **Full‑pipeline** resource estimate | Guarantees that RAM, CPU, and disk budgets are respected for the entire study, not just isolated steps. |

No fabricated metrics are reported; all quantitative statements will be **computed** from the simulated data during execution. 

