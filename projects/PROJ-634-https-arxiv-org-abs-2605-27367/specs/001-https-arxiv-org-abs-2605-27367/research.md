# Research: Reproduce & Validate SpatialBench

## Executive Summary
This research validates the feasibility of reproducing the `SpatialBench` paper's findings on a CPU‑only CI environment. The primary challenge is adapting a GPU‑optimized 3D reconstruction benchmark to run within 7 GB RAM and 6 hours without CUDA. The strategy involves executing a **stratified minimal subset** (5 scenes, 3 models) to verify logic and metric calculation. The plan explicitly distinguishes between **External Baseline Validation** (if paper baselines exist) and **Internal Consistency Validation** (if baselines are missing).

## Dataset Strategy

| Dataset Name | Source / Verification | Usage in Plan | Notes on Fit |
| :--- | :--- | :--- | :--- |
| **DTU (3D Scenes)** | *Vendored in `external/SpatialBench`* (Official DTU repository) | Validation of depth estimation (Abs Rel, δ₁) | **Critical**: The "Verified datasets" block provided in the prompt contains generic HuggingFace links that **do not** contain the DTU 3D reconstruction data. The plan **mandates** that `external/SpatialBench` contains robust data loaders for the official DTU data. **Phase 0 includes a fail‑fast check**: if these loaders are missing, the run halts and flags the spec. |
| **ScanNet (3D Scenes)** | *Vendored in `external/SpatialBench`* (Official ScanNet repository) | Validation of depth estimation across domains | Same as DTU. Requires official 3D scene data. **Phase 0 includes a fail‑fast check** for loaders. |
| **Model Weights** | HuggingFace (e.g., `depth-anything`, `marigold`) | Inference targets | Weights will be loaded in float32 CPU mode. |

**Decision**: Proceed with the assumption that `external/SpatialBench` contains robust data loaders for DTU/ScanNet. **If the code attempts to load from the prompt's verified generic links, the implementation will fail, and the spec must be updated to include the correct data sources.** Phase 0 explicitly verifies this.

## Data Provenance & Baseline Verification

1.  **Version Pinning & Checksum**: Before execution, the plan mandates verifying that the DTU and ScanNet data versions (SHA‑256 checksums) match the hashes recorded in `external/SpatialBench/metadata/` or the paper's supplement. If the checksums differ, the run aborts with a clear error message to ensure construct validity.
2.  **Baseline Source Check**: The plan searches for per‑scene baseline metric files under `external/SpatialBench/reference_results/`.  
    - **If present**: Those values are used for the **External Baseline Validation** (≤5% relative tolerance).  
    - **If absent**: The plan falls back to **Internal Consistency Validation** (run-to-run stability ≤0.1%). This is explicitly flagged as a limitation for SC-004 in the final report.
3.  **Data Loader Verification**: Confirm that `load_dtu.py` and `load_scannet.py` exist and can be imported without raising CUDA errors. Missing loaders trigger an immediate abort with `EXIT_CODE_DATA_MISSING` and a manual‑download fallback URL.

## Feasibility Analysis

### Hardware Constraints (GitHub Actions Free Tier)
- **CPU**: 2 vCPU.
- **RAM**: ~7 GB.
- **Disk**: ~14 GB.
- **Time**: 6 h/job.

### Adaptation Strategy
1.  **Model Loading**: Force `torch.load(..., map_location='cpu')`. Disable any `load_in_8bit` or `bitsandbytes` flags.
2.  **Precision**: Use `float32` (default). Avoid `float16` which may be unstable on CPU.
3.  **Memory Management**:
    - Process scenes sequentially.
    - Explicitly `del` tensors and call `gc.collect()` after each scene.
    - Implement a `psutil` watchdog to kill the process if RSS > `MAX_RAM_MB` (6144 MB).
4.  **Subset Selection**:
    - **Stratified Sampling**: Choose scenes covering low, medium, and high depth ranges, as well as varying point‑cloud densities, across DTU and ScanNet.
    - **Models**: Select 3 representative models (e.g., `MiDaS`, `DepthAnything`, `Marigold`).
    - This reduces compute time substantially compared to the full set of scenes.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| **Dataset Mismatch** | High | Fatal | Phase 0 verifies data loaders; aborts if missing. |
| **OOM on CPU** | Medium | High | Strict `MAX_RAM_MB` limit; sequential processing; downsample if needed. |
| **CUDA Hardcoded** | Medium | High | Wrapper forces CPU; any import error aborts with clear message. |
| **Tolerance Failure** | Low | Medium | 5% tolerance justified (External) or [deferred] stability (Internal). |
| **Baseline Unavailable** | Medium | Medium | Fallback to internal consistency; flag spec limitation. |

## Methodological Rigor

- **Reproducibility**: The plan reproduces the **computational logic** on a stratified subset; it does **not** claim statistical significance for the full dataset.
- **Validity**: Metrics are standard; the plan validates that the code calculates them correctly against verified baselines (if available) or internal references.
- **Limitations**: The subset is not statistically representative of the full scene set.; conclusions are limited to "the code runs correctly on representative scenes and produces metrics within the expected numerical drift."
- **Tolerance Justification**: CPU‑FP32 vs. GPU‑FP16 drift is typically <0.5% (see *Deep Learning on CPUs* 2022). We adopt a conservative relative tolerance for external baselines to cover drift plus a safety margin. For internal consistency, a stringent stability threshold is used.