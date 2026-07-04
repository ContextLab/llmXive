# Known Issues

## Current Limitations

1. **Memory Constraints**:
 - The system automatically downsamples from 768x768 to 512x512 if memory allocation fails. This may affect the generalizability of results for larger models.
 - **Workaround**: Run on a system with more RAM or accept downsampled results.

2. **Compiler Version Sensitivity**:
 - Results may vary slightly between different versions of GCC or Clang due to internal optimization changes.
 - **Workaround**: Pin compiler versions in the environment.

3. **Sequential Execution**:
 - The current implementation runs configurations sequentially. This can be slow for large test matrices.
 - **Workaround**: Use external job schedulers (e.g., `multiprocessing`, `slurm`) to parallelize.

4. **Floating-Point Non-Determinism**:
 - Despite fixed seeds, floating-point operations may exhibit minor non-determinism on different CPU architectures or with certain compiler flags (e.g., `-ffast-math`).
 - **Workaround**: Use block averaging to mitigate noise.

5. **Stability Threshold**:
 - The 1e-5 threshold is arbitrary and may need adjustment for different use cases.
 - **Workaround**: Adjust the threshold in `code/analysis/stability_check.py` if necessary.

## Planned Resolutions

- **Parallel Execution**: Implement native parallel execution in a future release.
- **GPU Support**: Add support for GPU-based execution (future roadmap).
- **Advanced Metrics**: Add more stability metrics (e.g., structural similarity) in future versions.

## Reporting New Issues

If you encounter a new issue, please report it with:
- Full error traceback.
- Configuration used (flags, dimensions).
- Compiler and Python versions.
- Steps to reproduce.