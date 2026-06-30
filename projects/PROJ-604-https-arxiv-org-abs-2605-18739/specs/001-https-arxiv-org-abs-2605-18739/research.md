# Research: Reproduce & Validate LongLive-2.0 NVFP4 Infrastructure

## 1. Domain Context

**Topic**: Video Generation Infrastructure, Quantization (NVFP4), Long-Video Synthesis.
**Source Material**: "LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation" (Paper/Project).

**Key Challenge**: The paper describes an infrastructure optimized for NVIDIA Blackwell GPUs using NVFP4 (4-bit floating point) quantization. Reproducing this on a CPU-only environment (GitHub Actions free tier) presents a fundamental hardware mismatch. The research goal is not to replicate the *speed* or *exact numerical fidelity* of Blackwell, but to validate the *software infrastructure* (pipeline logic, quantization fallbacks, sequence parallelism) functions without crashing or producing numerical instability.

## 2. Dataset Strategy

**Note**: This project is a *software infrastructure validation*, not a data-driven statistical study. There is no external dataset (e.g., ImageNet, Kinetics) required for the validation of the *infrastructure*. The "data" consists of:
1.  **Synthetic Prompts**: Text strings (e.g., "a cat walking") used as input to the text-to-video pipeline.
2.  **Synthetic Latents**: Randomly initialized noise tensors used as the starting point for diffusion sampling.
3.  **Pre-trained Weights**: The `LongLive-2.0-5B` checkpoint. This is a *dependency*, not a dataset. It must be present in the repository (via git-lfs) or downloaded.

**Verified Sources**:
*   **Model Weights**: The spec assumes weights are available in a submodule or via official download. *Action*: The implementation must verify existence. If the weights are not in the verified list of the user message (which is empty for this specific project context), the plan explicitly states: "Weights must be provided externally; no public URL verified for this specific 5B checkpoint in the provided context."
*   **Library Source**: `fouroversix` library. *Action*: Verify importability. If the library is not on PyPI or a verified GitHub repo in the user message, the plan assumes it is provided via the project's git history or a local path.

**Decision**: No external dataset download is required. The validation uses synthetic inputs and provided weights. This avoids bandwidth limits and ensures the focus remains on the *pipeline* rather than data quality.

## 3. Methodology & Statistical Considerations

**Approach**: Deterministic Software Validation.
Since this is not a statistical hypothesis test on a population, standard statistical metrics (p-values, power analysis) do not apply. Instead, the validation relies on:
*   **Binary Success/Failure**: Pipeline completes (True/False).
*   **Numerical Stability**: Absence of NaN/Inf (True/False).
*   **Resource Constraints**: Peak RAM ≤ 7GB (True/False).
*   **Artifact Validity**: Output file is a valid video container (True/False).

**Validation Scope & Limitations**:
*   **Infrastructure Robustness**: The primary validation target. We verify that the system correctly selects quantization paths, handles fallbacks, and manages memory.
*   **Quantization Fidelity**: **Not Validated**. Validating specific NVFP4 rounding errors on CPU (via FP16 fallback) is impossible. The plan confirms the *code path* exists and the *fallback* is stable.
*   **Long Video Claims**: **Not Validated**. 2-4 frame sequences do not test the "Long Video" parallelism claims. The report will explicitly note this limitation.

**Stability Sampling Strategy**:
To ensure feasibility within 6h on CPU:
* **Latent Space**: Scan **[deferred] of frames** at a fixed stride (e.g., every 10th frame) instead of full scan.
*   **Pixel Space**: Scan **[deferred]** of the final output.
*   **Threshold**: Stability is defined as `count(NaN) == 0` AND `count(Inf) == 0` in the sampled data.
* **Rationale**: Full scan of latent space for a 5B model would exceed 6h time limit on CPU. A [deferred] fixed stride provides a statistically valid sample for detecting gross numerical instability (NaNs/Infs) without prohibitive cost.

**Causal/Associational Claims**:
*   *Claim*: "The infrastructure supports NVFP4 quantization."
*   *Validation*: If the code path for NVFP4 is executed (even if emulated on CPU) without crashing, the claim is *structurally* validated.
*   *Limitation*: We cannot claim the *performance* (FPS) matches the paper. The report must explicitly state: "FPS on CPU is not comparable to Blackwell; only structural validity is assessed."

**Control Case**:
To distinguish between "pipeline broken" and "quantization noise", a baseline run with `quantization_mode: FP16` and the same `random_seed` will be performed. If both fail, the pipeline is broken. If only the quantization mode fails, the quantization logic is suspect. This addresses the concern that synthetic inputs might not trigger failure modes; if the baseline (FP16) fails, the pipeline is fundamentally broken regardless of quantization.

**Collinearity/Multicollinearity**: Not applicable (no regression models).

**Multiple Comparisons**: Not applicable (single pipeline run per configuration).

## 4. Computational Feasibility (CPU-Only)

**Constraints**: 2 vCPU, 7GB RAM, 14GB Disk, 6h Time.
**Strategy**:
1.  **Model Precision**: Use CPU-compatible `torch` (no CUDA). If `fouroversix` requires CUDA for *import*, the project fails (blocking). If it allows CPU fallback, proceed.
2.  **Memory Management**:
    *   Use `inference_sp.py` (Sequence Parallelism) to split the sequence across CPU cores (if supported) or simply to manage memory allocation more granularly.
    *   Limit frame count to a small set of frames. A "long video" (e.g., 60s) is impossible on CPU within 6h.
    *   **Pre-flight Check**: Estimate RAM before execution. If > 6.5GB, reduce frames or switch to SP mode.
3.  **Quantization**:
    *   NVFP4 on CPU is likely an emulation. Expect slower performance.
    *   If emulation is too slow, fallback to FP16 (standard precision) and log the mode change.
4.  **Libraries**:
    *   `torch`: Pin to a version with CPU wheels (e.g., `torch==2.1.0+cpu`).
    *   `fouroversix`: Verify CPU compatibility. If not available, the plan must flag this as a spec gap.

**Rationale**: The chosen approach (synthetic data, minimal frames, CPU fallback) is the only way to satisfy the 6h/7GB constraints. Any attempt to run full-length generation would result in OOM or timeout.

## 5. Decision Log

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| Use Synthetic Prompts | No external dataset needed; reduces I/O and bandwidth. | Using real video datasets (e.g., UCF101) would require download time and storage, wasting CI resources. |
| Limit to 2-4 Frames | Ensures completion within 6h on CPU. | Generating 30+ frames would likely exceed 6h runtime or 7GB RAM. |
| Fallback to FP16 if NVFP4 fails | Ensures pipeline runs; validates infrastructure logic. | Forcing NVFP4 on CPU without fallback would cause crashes. |
| Explicit Checkpoint Error | Prevents running with random weights (scientific integrity). | Proceeding with random weights would produce meaningless artifacts. |
| Pre-flight Memory Check | Prevents OOM loops by making decisions *before* execution. | Runtime retry loops risk infinite OOM cycles and time limit exhaustion. |
| Stability Sampling ([deferred] fixed stride) | Ensures CPU feasibility for 5B models. | Full scan of latent space would exceed 6h time limit. |
| Control Case (FP16 Baseline) | Distinguishes pipeline errors from quantization noise. | Single run cannot distinguish between "broken pipeline" and "bad quantization". |

## 6. Limitations (Explicit)

*   **Long Video Claims**: The validation uses 2-4 frames, which does not test the "Long Video" parallelism claims. The plan explicitly states this limitation in the final report.
*   **Quantization Fidelity**: The plan does not validate the specific numerical properties of NVFP4 (e.g., rounding errors) on CPU, as these are hardware-specific. The validation is limited to the stability of the fallback path.