# Research: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## Research Question

How does the minimum information density required for stable long-horizon forecasting in embodied agents scale as input modality shifts from continuous visual streams to sparse, discrete sensor streams, and what architectural properties are necessary to preserve error bounds under these constraints?

## Dataset Strategy

The primary dataset for this study is the **LIBERO** benchmark, which provides continuous RGB frames and proprioceptive states for embodied agents. The study will not use the raw visual streams for the discrete modality analysis but will use the underlying state vectors (object positions, velocities, etc.) to generate the quantized inputs.

| Dataset Component | Source URL (Verified) | Usage in Plan |
|:--- |:--- |:--- |
| **LIBERO State Data** | ` (Note: Actual format is HDF5) | Primary source for continuous proprioceptive states and object positions. Will be parsed using `h5py` or `lerobot` library to extract state vectors for quantization. |
| **LIBERO Episode Data** | ` (Note: Actual format is HDF5) | Used to verify episode structure and temporal consistency of state sequences. |
| **Baseline Visual Data** | *Same as above* | The continuous visual modality baseline will be derived from the same dataset by *not* applying quantization, ensuring architectural consistency. |

**Note**: No verified source was found for pre-existing "JSON-serialized" discrete datasets. Therefore, the `data/quantize.py` script will generate the discrete JSON vectors from the verified LIBERO sources, ensuring data hygiene (Principle III) and reproducibility (Principle I). The plan explicitly handles the HDF5 format of the source data.

**Dataset Variable Fit**:
- **Required Variables**: Object positions (x, y, z), velocities (vx, vy, vz), binary collision flags, gripper state.
- **Source Fit**: The LIBERO HDF5 files contain `states` arrays with proprioceptive data (e.g., `robot0_eef_pos`, `robot0_eef_quat`, `robot0_gripper_qpos`).
- **Gap Analysis**: The spec requires "RGB frames" for the continuous baseline, but the *discrete* analysis relies on the *state vectors*. The plan explicitly extracts state vectors from the HDF5 files. If the HDF5 files lack specific velocity fields (e.g., only position is stored), the plan will compute finite differences from position data. **Warning**: Finite differences amplify noise; this will be explicitly logged and the resulting error growth rate will be interpreted with caution.

## Methodology

### Phase 1: Data Construction & Quantization (US-1)
1. **Ingestion**: Download verified LIBERO HDF5 files. Parse using `h5py` to extract `states` arrays.
2. **Extraction**: Parse `states` arrays to extract continuous vectors (position, quaternion, gripper).
3. **Quantization**: Apply uniform quantization to target bit-depths (4-bit: -15, 8-bit: -255, 16-bit: 0-65535).
 - *Formula*: `discrete_val = floor((val - min) / (max - min) * (2^bits - 1))`
 - *Clamping*: Ensure all values fall within valid integer ranges.
4. **Noise Injection**: Add Gaussian noise ($\mathcal{N}(\mu, \sigma)$) with varying noise levels.
 - *Clamping*: Post-noise values are clamped to the nearest valid discrete bin to prevent "floating-point leakage" (Edge Case).
5. **Serialization**: Save as JSON-serialized state vectors.

### Phase 2: Model Adaptation & CPU Training (US-2)
**Two-Stage Training Protocol** (Resolved Construct Validity):
1. **Stage 1 (Encoder Pre-training)**: Train the *discrete projection layer* (encoder) on the quantized data to learn the mapping from discrete bins to the latent embedding space. This ensures the encoder can represent the input.
2. **Stage 2 (Freeze & Train)**: Freeze the trained discrete projection layer. Load the pre-trained Kairos Hybrid Linear Temporal Attention weights. Train *only* the temporal attention module on the quantized sequences.
 - *Constraint*: No gradient updates to the encoder (Stage 2).
 - *Rationale*: This isolates the stability of the *attention mechanism* (the research target) from the encoder's ability to represent the input.

**Training Loop**: Execute on CPU-only PyTorch.
 - *Input*: Quantized sequences.
 - *Loss*: Mean Squared Error (MSE) between predicted and ground-truth discrete sequences (decoded to continuous space for comparison, see Phase 3).
 - *Constraints*:
 - Batch size tuned to fit < 7GB RAM.
 - Max epochs: a predetermined limit (or graceful exit after a reasonable time duration).
 - Checkpointing: Save model state every epoch.

### Phase 3: Stability Analysis & Threshold Mapping (US-3)
**Revised Validation Target** (Resolved Tautology):
- **Ground Truth**: The original continuous state vector.
- **Prediction**: The model predicts a sequence of discrete states. These are *decoded* back to continuous space (using the inverse quantization mapping) before calculating error.
- **Metric**: MSE between the *decoded* prediction and the *original* continuous ground truth. This measures the information loss of the discrete bottleneck, not just the model's ability to invert a deterministic function.

1. **Error Calculation**: Compute MSE for each prediction horizon across a range of short, medium, and long steps.
2. **Scaling Law**: Plot MSE vs. Quantization Level (4, 8, 16-bit).
3. **Statistical Validation**:
 - Perform multiple independent runs with different noise seeds.
 - **Test**: Bayesian Hierarchical Modeling (BHM) with partial pooling. This allows for robust estimation of effect sizes even with low N (N=10), mitigating Type II error risks.
 - **Metric**: Posterior distribution of the difference in error rates between Discrete and Continuous modalities. A credible interval excluding zero indicates a significant degradation.
4. **Threshold Identification**: Identify the bit-depth where the normalized MSE exceeds **[deferred]** of the continuous baseline MSE (as per US-3 Acceptance Scenario 1). This explicitly defines the threshold determination strategy.

## Statistical Rigor & Feasibility

### Statistical Rigor (Quantitative Studies)
- **Multiple Comparisons**: Since 3 quantization levels are tested, a correction factor is applied in the BHM model structure (hierarchical priors) to control for family-wise error rate.
- **Power Justification**: 10 independent runs are planned. To mitigate the risk of Type II error with low N, the plan uses **Bayesian Hierarchical Modeling** (BHM) instead of frequentist t-tests. BHM allows for partial pooling across runs, borrowing strength to estimate effects more robustly and providing credible intervals that better characterize uncertainty.
- **Causal Inference**: Claims are framed as **associational** (relative degradation due to quantization). No causal claims are made about the "true" physical world, as the ground truth for the discrete modality is synthetic (derived from continuous).
- **Collinearity**: Predictors (quantization level, noise level) are orthogonal by design (sweeping one while holding the other constant). However, position and velocity are definitionally related; the analysis will report them descriptively and acknowledge the collinearity in the error growth rate.
- **Measurement Validity**: The "discrete sensor" is a simulation. Validity relies on the assumption that uniform quantization + Gaussian noise approximates real-world sensor degradation. This is a standard assumption in robust control literature.

### Compute Feasibility (GitHub Actions Free Tier)
- **Hardware**: 2 CPU cores, ~7 GB RAM, ~14 GB disk.
- **Strategy**:
 - **Data Subset**: Only a subset of LIBERO episodes (e.g., 50 episodes) will be used to ensure the dataset fits in RAM after quantization.
 - **Model Size**: The Kairos adapter will use a reduced hidden dimension if the full model exceeds memory (documented in `data-model.md`).
 - **Training**: CPU training is slow. The plan targets a feasible duration for 100 epochs on a *sampled* dataset. If runtime exceeds 6 hours, the loop exits gracefully, and the checkpoint is used for analysis (SC-003).
 - **Libraries**: `torch` (CPU wheel), `numpy`, `pandas`, `h5py`, `arviz` are all compatible with CPU-only environments. No `bitsandbytes` or CUDA-specific code.

## Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Use LIBERO HDF5** | Verified source available. Contains necessary state vectors. Plan updated to parse HDF5 correctly. |
| **Custom Quantization Script** | No verified pre-quantized dataset exists. Custom script ensures reproducibility and exact control over bit-depth. |
| **Two-Stage Training** | Isolates the effect of modality shift from architectural changes (FR-002) and ensures the encoder can represent the discrete input. |
| **CPU-Only Execution** | Directly addresses the "resource-constrained" research question and ensures runnability on free CI. |
| **10 Independent Runs + BHM** | Minimum required for a valid analysis within time limits; BHM mitigates low-N power issues. |
| **Graceful Exit at 6h** | Prevents job failure and allows partial results to be analyzed, ensuring the study can proceed even if training is slower than expected. |
| **20% Threshold** | Explicitly defined in US-3 and adopted as the stability boundary criterion. |
| **Decoded MSE** | Measures information loss against the original continuous ground truth, avoiding tautological validation. |