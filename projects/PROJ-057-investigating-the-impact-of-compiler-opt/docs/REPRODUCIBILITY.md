# Reproducibility Guide

## Ensuring Reproducible Results

To ensure that results can be reproduced across different runs and environments, the following measures are implemented:

### 1. Deterministic Data Generation

- **Fixed Seeds**: All synthetic tensors are generated with fixed random seeds.
- **Consistent Distributions**: Use of Normal and Uniform distributions with defined parameters.

### 2. High-Precision Reference

- **Decimal Module**: Reference calculations use Python's `decimal` module with 512-bit precision to minimize rounding errors.

### 3. Manifest Generation

- **SHA-256 Hashes**: Every generated artifact (binaries, logs, CSVs, plots) is hashed and recorded in `data/manifest.json`.
- **Verification**: The manifest can be used to verify that all artifacts match the expected state.

### 4. Version Control

- **Compiler Versions**: Log the exact version of the compiler used (GCC/Clang).
- **Python Version**: Record the Python version used for execution.

### 5. Environment Variables

- **LD_LIBRARY_PATH**: Ensure consistent library paths.
- **OMP_NUM_THREADS**: Set to 1 to avoid non-deterministic thread scheduling effects (if applicable).

## Verifying Reproducibility

1. **Run the Experiment**: Execute `python main.py`.
2. **Check Manifest**: Verify `data/manifest.json` contains hashes for all artifacts.
3. **Re-run**: Execute the experiment again on the same environment.
4. **Compare**: Ensure the new hashes match the original manifest.

## Known Variations

- **Hardware Differences**: Results may vary slightly on different CPU architectures due to micro-optimizations.
- **Compiler Versions**: Different compiler versions may produce different binaries, affecting latency.
- **System Load**: Background processes can affect latency measurements. Block averaging helps mitigate this.

## Best Practices

- **Isolated Environment**: Run experiments in a dedicated environment (e.g., Docker container) to minimize external interference.
- **Consistent Configuration**: Use the same configuration file for all runs.
- **Document Changes**: Log any changes to the environment or configuration.
