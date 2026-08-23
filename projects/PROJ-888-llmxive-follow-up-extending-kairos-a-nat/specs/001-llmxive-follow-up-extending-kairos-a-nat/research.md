# Research: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## 1. Problem Definition & Hypothesis

**Research Question**: How does the minimum information density required for stable long-horizon forecasting in embodied agents scale as input modality shifts from continuous visual streams to sparse, discrete sensor streams?

**Hypothesis**: There exists a critical quantization threshold (likely between 6-bit and 8-bit for proprioceptive data) where the Total MSE of the discrete modality exceeds the continuous baseline by a statistically significant margin (p < 0.05), indicating a breakdown in the Hybrid Linear Temporal Attention mechanism's ability to preserve error bounds under sparse input.

**Key Variables**:
- **Independent**: Quantization Level (4, 6, 8, 16-bit), Noise Level (0.1 * step), Horizon (100, 500, 1000), Modality (Continuous vs Discrete).
- **Dependent**: Total MSE (normalized by dimensionality), Cumulative Error Rate, MSE Ratio (Discrete/Continuous).
- **Control**: Frozen Continuous Baseline (evaluated on quantized ground truth), Random Seed.

## 2. Dataset Strategy

### 2.1 Source Verification
The study requires the `lerobot/libero_plus` dataset.
- **Status**: **NO VERIFIED SOURCE FOUND** in the provided "Verified datasets" block.
- **Action**: The spec assumes `lerobot/libero_plus` is available. However, the "Verified datasets" block only lists:
  - `gokulraja17/rice-rgb-demo`
  - `maderix/flickr_bw_rgb`
  - `gokulraja17/rice-rgb-demo2`
  - `AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score`
  
  **CRITICAL GAP**: The spec explicitly requires `lerobot/libero_plus` (robotic manipulation data with `observations.positions` and `observations.ee_pos`). None of the verified URLs correspond to this dataset. The `rice-rgb` datasets are image-only; the `MixSub` dataset is text-only.
  
  **Decision**: Since the "Verified datasets" block does not contain `lerobot/libero_plus`, and the plan **cannot** fabricate a URL, we must:
  1.  **Attempt Standard Load**: Use `datasets.load_dataset("lerobot/libero_plus")` assuming it is publicly available on Hugging Face Hub (standard for LeRobot). If this fails due to access restrictions or non-existence, the pipeline must halt.
  2.  **Schema Verification**: Explicitly verify the presence of `observations.ee_pos` and `observations.positions` (or `joint_positions` depending on the specific task subset). If keys are missing, the run fails.
  3.  **Fallback**: If `lerobot/libero_plus` is inaccessible, the study **cannot** proceed as specified because no verified substitute exists in the provided list that contains robotic state vectors (`positions`, `ee_pos`). The plan will proceed with the assumption that the standard HF load works, but the implementation must include a hard fail if the dataset is not found, rather than switching to a fake dataset.
  
  *Note: The plan explicitly relies on the assumption that `lerobot/libero_plus` is publicly fetchable via the `datasets` library, as no verified URL was provided in the input block.*

### 2.2 Data Processing Strategy: 2x2 Factorial Design
To isolate "modality shift" from "telemetry noise," we implement a 2x2 factorial design:
1.  **Continuous + NoNoise**: Raw continuous data (no noise).
2.  **Continuous + Noise**: Continuous data + Gaussian noise (before quantization).
3.  **Discrete + NoNoise**: Quantized data (no noise).
4.  **Discrete + Noise**: Quantized data + Gaussian noise (before quantization).

**Ground Truth Definition**: For a fair comparison, **both** the Continuous and Discrete models are evaluated against the **Quantized Ground Truth** (derived from continuous data). This ensures the MSE measures the model's ability to predict the quantized state, not the impossibility of reconstructing continuous values from discrete inputs.

- **Source Schema**: `observations.positions` (orientation), `observations.ee_pos` (position).
- **Transformation**:
  1.  **Derivation**: Calculate velocity and acceleration via finite differencing on *continuous* float32 arrays.
  2.  **Noise Injection**: Add Gaussian noise ($\sigma = 0.1 \times \text{quantization\_step}$) to continuous values.
  3.  **Quantization**: Map to integer bins [0, $2^N - 1$] for $N \in \{4, 6, 8, 16\}$.
  4.  **Validation**: Check for 1-bit collapse (all values identical).
- **Streaming**: Use `streaming=True` to avoid loading full dataset into RAM; process in chunks.

### 2.3 Compute Feasibility (CPU vs. GPU)
- **Constraint**: GitHub Actions Free Tier (2-core, 7GB RAM, 6h).
- **Method**: 
  - **CPU-First**: All training and inference must run on `device="cpu"`. No CUDA, no mixed precision.
  - **Model Size**: The Kairos Hybrid Linear Temporal Attention module must be loaded in full precision (float32) but with a **heuristic-initialized** discrete projection layer. The model size must be constrained (e.g., limited hidden dimensions or subset of layers) to fit within 7GB RAM.
  - **Sampling**: If the full `lerobot` dataset exceeds 7GB, the plan will sample a fixed number of episodes (e.g., 50-100) to fit the memory budget while maintaining statistical power.
  - **No GPU Escape Hatch Needed**: The spec explicitly forbids GPU acceleration for this study ("CPU-only environment"). The "GPU escape hatch" is not applicable here as the method is designed to be CPU-tractable.

## 3. Statistical Methodology

### 3.1 Power Analysis
- **Goal**: Determine $N$ (number of independent runs) to detect Cohen's $d = 0.5$ with Power $\ge 0.8$, $\alpha = 0.05$.
- **Method**: **LMM-based Simulation**. We will simulate data with the expected variance structure (including random effects for `episode_id` and temporal autocorrelation) to estimate the effective sample size required. This replaces the t-test approximation.
- **Output**: `power_analysis_report.json` with calculated $N$.

### 3.2 Error Analysis
- **Metric**: Total MSE (Discrete) vs. Total MSE (Continuous), both normalized by state space dimensionality ($MSE / D$).
- **Ratio**: $R = \text{MSE}_{\text{discrete}} / \text{MSE}_{\text{continuous}}$.
- **Threshold**: Stability is lost if the 95% CI of $R$ excludes 1.0 (upper bound > 1.0).

### 3.3 Significance Testing
- **Model**: Linear Mixed-Effects Model (LMM).
  - **Fixed Effect**: `modality` (Discrete vs. Continuous).
  - **Random Effect**: `episode_id` (to account for temporal autocorrelation).
  - **Alternative**: Block-bootstrap if LMM convergence fails.
- **Output**: `stats_results.json` with p-values, coefficients, and confidence intervals.

## 4. Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Pre-quantization Derivation** | Prevents amplification of quantization noise in velocity fields. |
| **Heuristic Initialization** | Ensures convergence within 6h; isolates modality shift from initialization artifacts. |
| **LMM over T-test** | Accounts for non-independence of time-series errors within episodes. **Requires Constitution Amendment**. |
| **Total MSE (No Subtraction)** | Adheres to FR-004; avoids theoretical noise floor assumptions. |
| **CPU-Only** | Hard constraint for edge simulation; ensures reproducibility on free-tier CI. |
| **Dataset Source** | `lerobot/libero_plus` is required. No verified URL exists in input; standard HF load attempted. If unavailable, study halts. |
| **Fair Baseline** | Uses **frozen** pre-trained weights evaluated on **quantized ground truth** to ensure valid comparison and CPU feasibility. |