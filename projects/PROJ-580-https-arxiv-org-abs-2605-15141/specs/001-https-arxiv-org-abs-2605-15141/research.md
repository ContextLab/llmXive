# Research: Causal Forcing++ Reproduction & Validation

## 1. Objective
Validate the `Causal-Forcing` implementation for the `wan_t2v_1_3B` model on a CPU-only, free-tier CI environment. The goal is to verify the *mechanism* of the pipeline (inference and training loops) without validating the *scientific quality* of the output.

## 2. Dataset Strategy
**No external datasets are required.**
- **Inference**: Uses built-in text prompts (e.g., "A cat walking") defined in the config. No video data needed.
- **Training**: Uses a synthetic/dummy data loader generating random tensors of shape `(batch, channels, height, width, frames)`.
- **Rationale**: Downloading video datasets (e.g., WebVid, Kinetics) exceeds the 14GB disk limit and 6-hour runtime of the free runner. The validation scope (FR-004) only requires verifying loss computation and gradient flow, which works with random data.

## 3. Compute Feasibility Analysis

### Hardware Constraints (GitHub Actions Free)
- **CPU**: 2 vCPUs (Intel Xeon Platinum).
- **RAM**: ~7 GB.
- **Disk**: ~14 GB.
- **GPU**: None.
- **Time Limit**: 6 hours.

### Model Memory Estimation
- **Model**: `wan_t2v_1_3B` (1.3 Billion parameters).
- **Precision**: FP16 (2 bytes/param) -> ~2.6 GB for weights.
- **Overhead**: PyTorch runtime, activation buffers, video encoder/decoder buffers, OS overhead.
- **Total Estimation**: ~2.6GB (weights) + ~2GB (activations/buffers) + ~1.5GB (OS/Python) = ~6.1 GB.
- **Verdict**: **Tight but feasible** if memory fragmentation is low and activation checkpointing is used. If the library forces FP32 (4 bytes/param), it will require ~5.2GB for weights alone, likely causing OOM.
- **Strategy**: Force `torch.float16` or `bfloat16` where possible. If the library does not support CPU FP16, the plan will fail gracefully with an OOM error. **Fallback Strategy**: If FP16 fails, attempt `bitsandbytes` quantization (INT8) or reduce resolution to 128x128.

### Time Estimation
- **Inference**: 16 frames, 2 steps. CPU diffusion is slow. Estimated ~-10 minutes.
- **Training**: 5 steps. Each step involves forward/backward pass. Estimated ~-15 minutes.
- **Total**: < 30 minutes. Well within the 6-hour limit.

## 4. Algorithmic Verification Strategy

### Inference (FR-003)
- **Goal**: Verify the forward pass of the AR-Diffusion pipeline.
- **Method**: Run `demo.py` with `--num_steps 2`.
- **Validation**: Check for `.mp4` file > 1KB.
- **Caveat**: The video will likely be low quality (noise) if weights are missing or if the model is not properly initialized. This is acceptable as long as the *pipeline* runs.

### Training (FR-004) - Algorithmic Sanity Check
- **Goal**: Verify the `causal_cd` or `dmd` loss computation and gradient backpropagation.
- **Method**: Run `train.py` with `--max_steps 5` and a dummy data loader.
- **Validation Criteria**:
  1. **Loss Finite**: All 5 loss values must be finite (not NaN or Inf).
  2. **Gradient Non-Zero**: The L2-norm of the model gradients must be > 0.0 (confirming backpropagation is active).
  3. **Checkpoint Valid**: Saved `.pt` file must contain valid `state_dict`.
- **Limitation**: Using random data validates *structural integrity* (code runs, gradients flow) but **cannot** validate the *scientific efficacy* of the distillation (e.g., convergence to a meaningful solution). A decreasing loss trend is not expected with random data; the focus is on non-zero gradients and finite loss.

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use Synthetic Data** | Real data download exceeds CI limits; structural validation does not require real data. |
| **Target `wan_t2v_1_3B`** | `14B` model is impossible on 7GB RAM. `1.3B` is the smallest viable candidate. |
| **Fail Fast on Missing Weights** | Generating random noise without weights produces invalid artifacts. The spec requires a "valid checkpoint" or specific error. |
| **CPU-Only Execution** | Mandatory for free-tier CI. No GPU fallback available. |
| **No Quality Metrics (VBench)** | VBench requires heavy models (CLIP, etc.) and GPU. Out of scope for this validation. |
| **Gradient Sanity Check** | Essential to distinguish a working backprop loop from a broken one that outputs random numbers. |

## 6. Verified Datasets
*No external datasets are used in this validation plan.*
- **Inference**: Uses internal prompt strings.
- **Training**: Uses `torch.utils.data.TensorDataset` with random tensors.

## 7. References
- **Causal-Forcing**: Vendored in `external/Causal-Forcing`.
- **Wan Model**: Referenced in `external/Causal-Forcing` documentation.
- **GitHub Actions Limits**: [GitHub Actions documentation](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners).