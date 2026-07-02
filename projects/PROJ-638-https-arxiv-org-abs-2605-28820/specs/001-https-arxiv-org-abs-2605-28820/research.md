# Research: Reproduce & Validate NEO-ov One-Vision Model

## Executive Summary

This research phase investigates the feasibility of reproducing the "NEO-ov" (Native One-Vision) model on CPU-only infrastructure, addressing the specific constraints of the project (2 CPU cores, ~7 GB RAM, 6-hour limit) and the methodological critique regarding the "at Scale" claim in the paper title. The primary finding is that while the "at Scale" claim implies quantitative scaling laws (exponents, power laws), the manuscript does not perform such analysis. Therefore, the validation scope is strictly limited to **functional reproduction** on a fixed-size model and dataset subset, with explicit documentation of this limitation.

## Dataset Strategy

The validation relies on the **MMBench** dataset, a standard benchmark for multimodal understanding. The dataset is selected because it is verified, publicly available, and compatible with the `VLMEvalKit` framework used by the NEO-ov codebase.

| Dataset Name | Source URL | Format | Sample Size | Relevance |
| :--- | :--- | :--- | :--- | :--- |
| MMBench (Dev/Test) | https://huggingface.co/datasets/HuggingFaceM4/MMBench_dev/resolve/main/data/train-00000-of-00001-28992cf4da792fdc.parquet <br> https://huggingface.co/datasets/HuggingFaceM4/MMBench/resolve/main/data/test-00000-of-00001-147b3b3e74778350.parquet | Parquet | 500-1000 (subset) | Primary benchmark for validation; contains image-text pairs required for inference. |
| VLMEvalKit (Test Mini) | https://huggingface.co/datasets/CaraJ/Mathverse_VLMEvalKit/resolve/main/testmini.tsv | TSV | 5 (Smoke test) | Used for initial smoke testing to verify pipeline initialization and CPU compatibility. |

**Note**: The NEO-ov model weights are not available as a verified external dataset URL. They are assumed to be vendored within the project's submodule or downloadable via the project's internal mechanism. No external URL is cited for the model weights as per the verified datasets list.

## Methodological Analysis

### The "At Scale" Critique
The reviewer (Geoffrey West) highlights a fundamental disconnect: the title "Towards Native One-Vision Models at Scale" suggests a quantitative scaling analysis (e.g., power-law exponents for infrastructure vs. output), yet the manuscript lacks such analysis. In scaling theory, "at Scale" is not an adjective but a quantitative prediction (e.g., sublinear scaling of 0.85 or superlinear scaling of 1.15).

**Decision**: The validation project **will not** attempt to compute scaling exponents or perform power-law fits. This is because:
1.  The manuscript does not provide the necessary data points (performance across multiple model sizes or dataset sizes) to fit such a law.
2.  The project's computational constraints (single model run on a fixed subset) preclude the generation of scaling data.
3.  Attempting to infer scaling laws from a single data point would be scientifically invalid.

**Scope Definition**: For the purpose of this validation, "Scale" is defined strictly as **architectural scale** (i.e., the parameter count of the specific NEO-ov model being tested). The validation confirms that the model *at this specific scale* functions correctly on CPU hardware. The absence of a scaling law analysis is explicitly documented as a limitation.

### Compute Feasibility
The target environment is a GitHub Actions free-tier runner (limited CPU, limited RAM, no GPU).
-   **Memory**: Loading a large vision-language model (VLM) typically requires significant RAM. To stay within 7 GB, the plan utilizes a **sampled dataset** (≤1000 images) and processes images in small batches (≤4) or sequentially.
- **Time**: A stringent time limit is imposed for VLM inference. The plan enforces a hard cap on the number of samples. If the inference time per sample exceeds [deferred] (1000 * 20s = 5.5h), the job may timeout. The smoke test (a small set of samples) is critical to verify the per-sample latency.
-   **Hardware**: No CUDA support is available. The code must rely on `torch` CPU operations. If the model relies on CUDA-specific kernels (e.g., for attention mechanisms), the plan includes a fallback to CPU-compatible implementations or a skip mechanism with logging.

## Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **CUDA Import Error** | High | Critical | The code explicitly checks for CUDA availability and forces CPU device. If `torch` requires CUDA for specific operations, the pipeline will fail early, triggering a warning log. |
| **Memory Overflow (OOM)** | Medium | High | Strict batch size limits (≤4) and sequential processing. The `ulimit` and memory monitoring scripts will be used to detect OOM before crash. |
| **Timeout (>6h)** | Medium | High | Hard sample cap (1000). The script will log a "truncated due to time limit" status if the runtime approaches 5.5 hours. |
| **Missing Weights** | Low | Critical | The script checks for the presence of checkpoint files before execution and exits with a clear error code (1) if missing. |
| **"At Scale" Misinterpretation** | High | Medium | The final report includes a dedicated "Methodological Notes" section explicitly stating that no scaling law analysis was performed. |

## Decision Rationale

The decision to limit the scope to **functional reproduction** rather than **scaling law analysis** is driven by:
1.  **Data Availability**: The manuscript does not provide multi-scale data points required for regression analysis.
2.  **Computational Constraints**: Running the model across multiple scales (different parameter counts or dataset sizes) would exceed the 6-hour CI limit and 7 GB RAM limit.
3.  **Scientific Integrity**: Fitting a power law to a single data point is mathematically invalid. The validation must remain honest about the scope.

By explicitly documenting this limitation, the project addresses the reviewer's critique transparently, transforming a potential "fatal flaw" into a clearly defined boundary of the study.
