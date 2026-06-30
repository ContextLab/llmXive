# Research: Reproduce & Validate VideoKR

## Objective

To validate the feasibility of reproducing the VideoKR training pipeline on a CPU-only, free-tier CI environment by subsampling the dataset and using a lightweight model, ensuring all core logic (data prep, model loading, training step) executes without GPU-specific errors.

## Dataset Strategy

The VideoKR dataset is the primary source. However, the full dataset is too large for the target environment (7 GB RAM). The strategy relies on a **subsampled** version of the dataset.

| Dataset Name | Source/URL | Verification Status | Usage in Plan |
| :--- | :--- | :--- | :--- |
| **VideoKR (Subsampled)** | *NO verified source found* in the provided list. The spec assumes the raw data is accessible via a vendored submodule. | **Unverified URL** (Per spec: "raw VideoKR dataset is accessible via the vendored submodule"). | The plan will use a local subsample (≤100 examples) derived from the vendored submodule. If the submodule is empty or missing, the plan switches to **Synthetic Mock Mode** using the `videokr_subsample` schema to generate dummy data that mimics the VideoKR format. |

**Note on Data Availability**: The provided "# Verified datasets" block does not contain a URL for the VideoKR dataset. The implementation plan explicitly handles this by assuming the data is present in the repository's submodule or by generating a minimal mock dataset to test the pipeline logic, as per the spec's assumption: "The raw VideoKR dataset is accessible via the vendored submodule, but a full download is not performed."

### Submodule Integrity Check
Before data preparation, the script will attempt to verify the `VideoKR` submodule:
1. Check if the submodule path exists.
2. Check if it contains at least one video file or metadata file.
3. If the check fails, the script will log "Submodule missing or empty. Switching to Synthetic Mock Mode." and generate synthetic data that adheres to the `videokr_subsample` schema.
4. **Distinction**: This step validates the *presence* of data, not the *completeness* of the dataset. If the submodule is empty, the plan validates the *loader logic* against synthetic data, explicitly acknowledging that *real-world data distribution* is not tested.

### Synthetic Mock Mode
If real data is unavailable, the plan will generate synthetic data:
- **video_path**: A placeholder string (e.g., "synthetic_video_001.mp4").
- **video_tensor_shape**: A dummy 3D numpy array (e.g., `(16, 224, 224, 3)`) to test the video-decoding logic.
- **question**, **answer**, **rationale**: Randomly generated text strings.
This ensures the data loader's video-decoding logic (frame extraction, temporal sampling) is exercised against a known-good tensor, validating the *code path* without needing 100GB of real video files. **Limitation**: This mode validates the *API contract* and *tensor shape handling* but does not validate the *actual video I/O bottlenecks* or *temporal sampling logic* on real video files.

### Video I/O Stress Test (If Real Data Available)
If the submodule check passes, the plan will attempt to decode a single real video frame to verify the temporal sampling logic (e.g., `temporal_sample_rate`, `num_frames`). This step explicitly validates the *real video I/O* path. If this fails, the plan logs "Real video I/O validation failed" but proceeds with Synthetic Mode for the rest of the pipeline.

## Model Strategy

To satisfy the 7 GB RAM constraint, a small Vision-Language Model (VLM) is required.

| Model | Source/URL | Verification Status | Usage in Plan |
| :--- | :--- | :--- | :--- |
| **Qwen2-1.5B-Instruct** | `Qwen/Qwen2-1.5B-Instruct` (Hugging Face Hub) | **Verified** (Standard HF model, CPU compatible via `transformers`) | **Primary Fallback**: Selected for high probability of fitting within 7 GB RAM. |
| **Qwen2-VL-2B-Instruct** | `Qwen/Qwen2-VL-2B-Instruct` (Hugging Face Hub) | **Verified** (Standard HF model, CPU compatible via `transformers`) | **Best Effort**: Attempted first. If pre-flight check fails, falls back to Qwen2-1.5B. |

**Rationale**: Qwen-VL-2B is a standard, well-documented model available on Hugging Face. It does not require CUDA-specific kernels for inference on a CPU, making it the ideal candidate for a "validation-only" run. The plan will use the `transformers` library with `torch_dtype=torch.float32` (or `float16` if memory permits) and `low_cpu_mem_usage=True` to ensure CPU compatibility. **Note**: 4-bit quantization (`bitsandbytes`) is explicitly excluded due to CUDA dependency.

### CPU-Optimized Loading Protocol
To ensure the model fits within 7 GB RAM, the plan will use the following loading parameters:
- `device_map='cpu'`: Forces all tensors to CPU.
- `torch_dtype=torch.float32`: Uses full precision (float16 may be attempted if memory permits, but float32 is safer for stability).
- `low_cpu_mem_usage=True`: Minimizes memory overhead during model loading.
- `trust_remote_code=True`: Required for some VLM architectures.

### Pre-flight Memory Budget Check
Before loading the model, the script will estimate the memory footprint:
- **Model Weights**: `Qwen2-VL-2B` in `float32` ≈ 8 GB (too large); `float16` ≈ 4 GB.
- **Tokenizer & Overhead**: ≈ 1 GB.
- **Data Loader & Buffers**: ≈ 1 GB.
- **Total Estimated**: ≈ 6 GB (for 2B in float16) or > 8 GB (for 2B in float32).
- **Abort Threshold**: If the estimated footprint > 6.5 GB, the script will abort model loading for the 2B model and switch to **Qwen2-1.5B** or **Data-Only Validation**. This ensures the pipeline logic is validated even if the 2B model cannot fit.

## Technical Feasibility & Constraints

### 1. Memory Management (7 GB Limit)
- **Data**: The full dataset is excluded. The `prepare_videokr_sft_data.py` script will be invoked with `--limit 100`. This ensures the data loading phase consumes < 100 MB.
- **Model**: Qwen2-VL-2B (2B parameters) in `float16` requires ~4 GB RAM for weights. The plan will use `low_cpu_mem_usage=True` to minimize overhead. If the pre-flight check fails, the plan switches to **Data-Only Validation** or **Qwen2-1.5B**.
- **Dependencies**: `bitsandbytes` and `flash-attn` are explicitly skipped. The `requirements.txt` processing script must detect the absence of `torch.cuda.is_available()` and remove these dependencies before installation.

### 2. Training Loop Validation
- The training loop will be configured for `--max_steps 1` and `--num_train_epochs 0.001`.
- The goal is not to converge the model but to verify that:
  - The data loader yields a batch.
  - The model forward pass executes (if memory permits).
  - The loss is computed.
  - The optimizer step (if any) runs.
  - Logs are written.

### 3. Error Handling
- **Missing Data**: If the submodule path is invalid, the script will exit with code 1 and a specific error message: "Data path not found".
- **GPU Dependencies**: If `bitsandbytes` is imported, the script will catch the `ImportError` and log a warning, then proceed with CPU-only mode.
- **Memory OOM**: If the pre-flight check fails, the script will log "Memory budget exceeded. Switching to Data-Only Validation." and skip the model loading phase.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Subsample Size: 100** | Balances the need for a representative sample with the strict 7 GB RAM limit. A representative set of video-text pairs (even with short clips) will likely fit in memory. |
| **Model: Qwen2-1.5B (Primary Fallback)** | It is the smallest "modern" VLM available that supports the VideoKR task type and is highly likely to fit within 7 GB RAM. Qwen2-VL-2B is attempted first but has a fallback. |
| **Skip GPU Libraries** | The CI runner has no GPU. Installing GPU libraries wastes time and causes import errors. |
| **Dry-Run (1 Step)** | Full training is impossible. One step is sufficient to validate the integration. |
| **Pre-flight Memory Check** | To prevent OOM failures, the plan includes a pre-flight check that aborts model loading if the estimated footprint > 6.5 GB. |
| **Synthetic Mock Mode** | To ensure the pipeline logic is validated even if real data is missing, the plan includes a mode to generate synthetic video tensors. |
| **CPU-Optimized Loading** | To ensure the 2B model fits, specific flags (`device_map='cpu'`, `low_cpu_mem_usage=True`) are used. 4-bit quantization is excluded due to CUDA dependency. |