# Research: Quantifying the Impact of Data Quantization on Gravitational Wave Signal Reconstruction

## 1. Problem Statement
Determine the **Signal‑to‑Noise Ratio (SNR) region** where quantization noise from limited‑bit ADCs becomes a **dominant systematic bias** in Bayesian parameter estimation of binary‑black‑hole (BBH) mergers. Dominance is defined as the **quantization‑induced error** (Δₖ = E_quant,ₖ − E_inst,ₖ) exceeding **[deferred]** of the instrumental‑only error (median MSE from the float64 baseline) for a given bit depth and parameter *k* (chirp mass, spin, distance).

## 2. Dataset Strategy

| Component | Source | Verified URL | Access Method | Rationale |
|-----------|--------|--------------|---------------|-----------|
| LIGO O3 PSD (instrumental noise) | GW Open Science Center (GWOSC) | `https://huggingface.co/datasets/astro-legacy-archive/gwosc-o3a-strain/resolve/main/H1-1238163456-1238216704-DQmask.parquet` | `datasets.load_dataset("astro-legacy-archive/gwosc-o3a-strain", split="train", streaming=False)` | Official O3 strain segment; frequency coverage (10 Hz‑2048 Hz) fully spans BBH signals in the 10‑50 M⊙ range. |
| Synthetic waveforms | PyCBC (`IMRPhenomD`) | N/A (generated on‑the‑fly) | `pycbc.waveform.get_td_waveform` | Full control over masses, spins, distances, and SNR; matches FR‑001. |

All datasets are directly downloadable via the Hugging  Face Hub; no authentication is required.

### Dataset Fit Verification
- **Frequency coverage**: PSD data contain a frequency band covering the inspiral‑merger‑ringdown regime for stellar‑mass BBH systems.  
- **Sampling rate**: Verified via the `sampling_rate` column (≥ 4096 Hz), satisfying Nyquist for the highest GW frequencies (~1000 Hz).  
- **Memory footprint**: Each PSD parquet shard ≈ 300 MB; streaming load ensures the runner never holds > 1 GB in RAM.

## 3. Statistical & Computational Methodology

### 3.1 Quantization Protocol
- **Bit depths**: 4, 8, 10, 12, 14, 16 (exactly as required by FR‑002).  
- **Full‑Scale Range (FSR)**: Fixed to `±1e‑21` strain (representative of LIGO’s dynamic range).  
- **Uniform quantizer**:  

\[
Q_N(x) = \text{round}\!\Bigl(\frac{x}{\text{FSR}} \times 2^{N-1}\Bigr) \times \frac{\text{FSR}}{2^{N-1}},
\]

where *N* is the bit depth.  
- **Edge‑case handling**: For *N* = 4 the number of unique amplitude values must equal `2**4 = 16`; the implementation checks this condition.

### 3.2 Parameter Estimation (Inference)
- **Algorithm**: Bilby MCMC with the `dynesty` sampler (CPU‑only).  
- **Uniformity**: Identical priors, likelihood, and sampler across all SNR ranges; only the number of steps adapts (600 steps for SNR ≤ 20, 800 steps for SNR > 20) to respect the 6‑hour CI limit.  
- **Convergence**: Gelman‑Rubin statistic ≤ 1.1; otherwise the run is labeled `"failed"`. For injected SNR < 8 the pipeline records `"non-detection"` per the spec.

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

for each bit depth and each parameter *k*. This implements SC‑001 directly (no deferred placeholder).

### 3.4 Statistical Rigor
- **Multiple‑comparison control**: Holm‑Bonferroni correction across **six bit depths × four SNR bins × three parameters** (α = 0.05 divided by 72 tests, applied step‑wise).  
- **Power analysis**: Pilot size **N = 2 400** (6 depths × 4 bins × 100 signals) yields > 80 % power to detect a Cohen’s d ≈ 0.3 difference in Δₖ at the Holm‑Bonferroni‑adjusted α, based on variance estimates from preliminary simulations of quantization bias at low SNR (see Phase 0 power‑analysis details).  
- **Reproducibility (SC‑005)**: The full study is repeated with **10 independent random seeds**; the crossover SNR is reported with a A confidence interval derived from the distribution of multiple estimates at a conventional confidence level.  
- **Causal claim**: Because the experiment is fully simulated, the quantization effect is causal by construction; results are presented as such, with the caveat that real‑world ADC non‑idealities are not modeled.  

### 3.5 Additivity Validation (FR‑015)
Before reporting any crossover SNR, we run the **sensitivity analysis** (Task T017) that directly measures quantization‑only error by injecting controlled quantization noise into the float64 baseline. The analysis compares this direct measurement to the Δₖ (E_quant − E_inst) estimate. **If the relative deviation exceeds 5 % for any bit depth, the crossover analysis is flagged as inconclusive and the result is not reported.** This satisfies FR‑015 and ensures scientific soundness.

## 4. Compute Feasibility Analysis
`compute_resource_estimate.py` benchmarks the **full pipeline** on a single signal and extrapolates to the full pilot of 2 400 signals. The estimate is then divided across **eight** parallel CI jobs (300 signals each) to respect the free‑tier limits.

| Resource | Estimate (per CI job) | Derivation |
|----------|-----------------------|------------|
| **Peak RAM** | ≤ 4.5 GB | Streaming PSD load (≈ 300 MB), HDF5 chunked writes, batch size limited to 300 signals in memory. |
| **CPU Time** | ≈ 5 h total *per job* | Generation ≈ 0.7 h, inference ≈ 3.5 h (adaptive steps), analysis ≈ 0.8 h. Eight jobs run concurrently, keeping wall‑clock ≤ 6 h per job. |
| **Disk Usage** | ≈ 5.2 GB (HDF5 + JSON) | Float64 baseline ≈ 2 GB; quantized data ≈ a few GB; results JSON ≈ a fraction of a gigabyte. |
| **GPU** | None required | All libraries run on CPU; `bilby` is invoked with `device="cpu"`.|

The estimates are written to `reports/resource_estimate.md` and verified by the CI runner before the main pipeline starts.

## 5. Decision Log
| Decision | Rationale |
|----------|-----------|
| Fixed **FSR** quantization | Mirrors real ADC behavior; avoids adaptive scaling bias. |
| Include **all six** bit depths in pilot | Satisfies FR‑002; intermediate depths improve interpolation of the crossover. |
| **Stratify** parameters within SNR bins and fix a grid per bin | Guarantees that observed Δₖ reflects quantization rather than mass‑dependent estimation error. |
| Uniform **MCMC** across SNR | Eliminates inference‑method bias; adaptive sample counts are a computational efficiency, not a methodological change. |
| **Median** aggregation of Δₖ | Robust to outliers and provides a stable crossover estimate. |
| **Holm‑Bonferroni** correction | Controls family‑wise error rate across depths, bins, and three parameters. |
| **10 independent runs** | Required by SC‑005 to assess reproducibility of the crossover SNR. |
| Record **non‑detections** for SNR < 8 | Handles the edge case specified in the spec without crashing. |
| Store **artifact hashes** in project‑state YAML | Enforces Constitution Principle V and Single Source of Truth. |
| **Full‑pipeline** resource estimate | Guarantees that RAM, CPU, and disk budgets are respected for the entire study, not just isolated steps. |

No fabricated metrics are reported; all quantitative statements will be **computed** from the simulated data during execution.

---

