# Research Log

## 2023-10-27

### Experiment: Compiler Optimization Impact on LLM Kernels

**Objective**: Quantify the trade-off between latency and numerical stability for various compiler optimization flags.

**Methodology**:
1. Generated deterministic synthetic tensors (768x768).
2. Compiled C++ kernels (MatMul, Softmax, LayerNorm) with flags: `-O0`, `-O2`, `-O3`, `-ffast-math`.
3. Executed 1000 iterations per configuration.
4. Compared outputs against 512-bit decimal reference.
5. Performed Welch's t-test on block-averaged latencies.

**Preliminary Findings**:
- `-O3` generally provides the best latency but may introduce stability issues with `-ffast-math`.
- `-O2` offers a good balance between performance and stability.
- `-ffast-math` significantly reduces latency but often exceeds the 1e-5 stability threshold.

**Next Steps**:
- Expand test matrix to include more kernels and flags.
- Analyze the impact of tensor size on stability.
- Refine visualization tools for better interpretation.

**Challenges**:
- Memory pressure on smaller instances required downscaling.
- Compiler version differences affected reproducibility slightly.

**Conclusion**:
The benchmark suite successfully identified the Pareto frontier of optimization strategies. Future work will focus on expanding the kernel set and exploring hardware-specific optimizations.
