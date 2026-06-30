# LongLive-2.0 CPU Adaptation

## What was simplified?
The original paper, **LongLive-2.0**, describes a complex infrastructure for **NVFP4** (4-bit floating point) parallel training and inference on **Blackwell GPUs** for long video generation. It relies on:
1.  **NVFP4 Quantization**: Custom CUDA kernels (`.cu` files) for 4-bit GEMM and quantization.
2.  **Sequence Parallelism (SP)**: Distributed training across multiple GPUs.
3.  **Video Generation Models**: Large diffusion models (e.g., Wan 5B) requiring massive VRAM.

**This adaptation cannot run the original code** because:
-   The CI environment has **no GPU** (CPU only).
-   The code requires **Blackwell architecture** for NVFP4 instructions.
-   The models are **too large** for 7GB RAM.

## The Adaptation Strategy
Instead of attempting to run the unrunnable GPU kernels, this script **simulates the core quantitative claim** of the paper:
> "NVFP4 reduces memory cost and accelerates GEMM computation... up to 2.15x speedup in training."

### Implementation Details:
1.  **Synthetic Memory Calculation**:
    -   Calculates theoretical memory usage for BF16 (2 bytes/element) vs. NVFP4 (0.5 bytes/element).
    -   Simulates the impact of sequence length and batch size on memory footprint.
2.  **Simulated Throughput**:
    -   Models the speedup factor based on the paper's reported range (1.6x - 2.3x) relative to memory bandwidth savings.
    -   Uses `numpy` to generate stochastic performance data over multiple iterations.
3.  **Output Artifacts**:
    -   `data/quant_benchmark_results.csv`: Detailed metrics per configuration.
    -   `data/quant_benchmark_summary.json`: Aggregate statistics (avg speedup, memory reduction).
    -   `figures/quant_benchmark_comparison.png`: Visual comparison of memory savings and speedup distribution.

## How to Run
Execute the single script:
```bash
python code/longlive_quant_benchmark.py
```

This will generate the required artifacts in `data/` and `figures/` without needing any GPU or external video datasets.
