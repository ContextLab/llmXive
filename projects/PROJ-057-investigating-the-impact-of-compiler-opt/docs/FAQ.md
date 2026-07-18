# Frequently Asked Questions

## General

**Q: Why use 512-bit precision for reference?**
A: To ensure the reference output is effectively exact, allowing accurate measurement of numerical drift in optimized kernels.

**Q: What compiler versions are supported?**
A: GCC 11+ or Clang 14+.

**Q: Can I use GPU?**
A: No, this project is CPU-only as per design constraints.

## Technical

**Q: What happens if memory pressure occurs?**
A: The executor automatically downsamples from 768x768 to 512x512 and logs the event.

**Q: How is numerical stability measured?**
A: By calculating L2 relative error and maximum absolute difference against the 512-bit reference.

**Q: Why Welch's t-test instead of paired t-test?**
A: Because the binaries are independent (different compilers/flags), Welch's test is statistically appropriate.

**Q: What is the threshold for instability?**
A: Relative error > 1e-5.

## Usage

**Q: How do I add a new compiler flag?**
A: Edit `benchmarks/config.py` and add the flag to the `BenchmarkConfig` list.

**Q: Can I change the iteration count?**
A: Yes, modify the `ITERATIONS` constant in `benchmarks/executor.py`.

**Q: How do I interpret the Pareto frontier plots?**
A: Points closer to the origin (lower latency, lower error) are better. The frontier represents the optimal trade-offs.

**Q: What if my results look unstable?**
A: Check for NaNs in the logs, ensure your compiler supports the flags, and verify the reference data is generated correctly.

## Troubleshooting

**Q: Compilation fails.**
A: Ensure your C++ compiler is installed and in PATH. Check for syntax errors in the kernel code.

**Q: Execution times out.**
A: Reduce the iteration count or tensor dimensions. Check system resources.

**Q: Tests fail.**
A: Run `pytest -v` for detailed output. Ensure dependencies are installed correctly.
