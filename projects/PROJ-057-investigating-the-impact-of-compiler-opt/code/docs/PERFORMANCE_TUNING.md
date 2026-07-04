# Performance Tuning Guide

## Optimizing the Benchmark Itself

### 1. Compiler Flags
- Use `-O3` for maximum performance in the benchmark runner itself (not the kernels being tested).
- Ensure `march=native` is set for the benchmark runner to leverage CPU-specific instructions.

### 2. Memory Management
- If running on a system with limited RAM, rely on the automatic downsampling feature.
- Monitor `Memory Pressure` logs to understand when downscaling occurs.

### 3. Parallel Execution
- The current implementation is sequential. For parallel execution, consider wrapping the `executor.py` in a job scheduler (e.g., `multiprocessing`, `slurm`).
- Ensure that each process has its own temporary directory for binaries to avoid conflicts.

### 4. I/O Optimization
- Use `mmap` or direct I/O for large tensor files if I/O becomes a bottleneck.
- Minimize logging verbosity during large-scale runs to reduce I/O overhead.

### 5. Statistical Efficiency
- Adjust block size in `stats.py` if the number of iterations needs to be reduced (not recommended).
- Ensure that the number of iterations (1000) is sufficient for the desired statistical power.

## Optimizing the Kernels

The kernels themselves are the subject of the study. However, for future extensions:
- **Loop Unrolling**: Use `-funroll-loops` to reduce loop overhead.
- **Vectorization**: Ensure compilers can auto-vectorize by avoiding data dependencies.
- **Cache Blocking**: Implement manual cache blocking for large matrices to improve cache hit rates.

## Monitoring Performance

- Use `perf` or similar tools to profile the compiled binaries.
- Analyze `data/intermediates/raw_logs/` for latency distributions and outliers.
- Check `data/results/pareto_frontier_final.png` for optimal configurations.
