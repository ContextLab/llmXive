# Frequently Asked Questions

## General

### Q: Why use Python's `decimal` module for reference calculations?
**A:** The `decimal` module allows for arbitrary-precision arithmetic (512-bit in this project) [UNRESOLVED-CLAIM: c_157374a1 — status=not_enough_info], which is necessary to establish a high-precision ground truth against which the floating-point (float32) optimized kernels can be compared.

### Q: What is the difference between `pareto_frontier_exploration.png` and `pareto_frontier_final.png`?
**A:** The exploration plot includes all numerically stable configurations, including those that were downsampled due to memory pressure (marked distinctly). The final plot strictly excludes any configuration with an L2 error > 1e-5 [UNRESOLVED-CLAIM: c_e1f8cf61 — status=not_enough_info], representing the validated Pareto frontier.

### Q: Why is Welch's t-test used instead of a paired t-test?
**A:** The configurations being compared are independent binaries compiled with different flags. They do not share the same execution context in a paired manner. Welch's t-test is statistically appropriate for comparing independent samples with potentially unequal variances.

## Technical

### Q: What happens if the system runs out of memory?
**A:** The executor automatically downsamples the tensor dimensions from 768x768 to 512x512, logs a "Memory Pressure" warning, and continues execution. Downsampled runs are included in the exploration plot but marked distinctly.

### Q: How are NaNs handled?
**A:** NaNs are detected in the output tensors. Any run producing NaNs is flagged as unstable, excluded from statistical analysis, and logged for audit.

### Q: Can I add my own optimization flags?
**A:** Yes. Add your flags to the list in `code/benchmarks/config.py`. Ensure they are compatible with the C++ standard (C++17) and your compiler.

### Q: How many iterations are run per configuration?
**A:** A fixed count of 1000 iterations is mandatory [UNRESOLVED-CLAIM: c_ebec3121 — status=not_enough_info] (Constitution Principle VII). An adaptive stop condition (CV ≤ 1% after 30 iterations) is implemented [UNRESOLVED-CLAIM: c_b157f941 — status=not_enough_info] as a secondary safety check but does not override the fixed count.

## Troubleshooting

### Q: My compilation fails. What should I check?
**A:** Ensure you have GCC 11+ or Clang 14+ installed [UNRESOLVED-CLAIM: c_7a7e8b5c — status=not_enough_info] and that the compiler is in your `PATH`. Check the error message in the logs for specific compiler errors.

### Q: Why are some configurations marked as "UNSTABLE"?
**A:** A configuration is marked unstable if its L2 relative error exceeds 1e-5 [UNRESOLVED-CLAIM: c_0c44e8e6 — status=not_enough_info] or if it produces NaN values. This indicates that the optimization flags caused significant numerical drift.

### Q: How do I verify that my results are reproducible?
**A:** Check `data/manifest.json` for SHA-256 hashes of all artifacts. Re-run the experiment and compare the new hashes to the original manifest.
