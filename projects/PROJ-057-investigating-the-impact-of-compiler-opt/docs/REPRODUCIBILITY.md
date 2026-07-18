# Reproducibility

## Overview

This project is designed for full reproducibility. All outputs are hashed and recorded to ensure that results can be verified and replicated.

## Manifest

The `data/manifest.json` file contains SHA-256 hashes for:
- Compiled binaries
- Raw logs
- CSV results
- Generated plots

Verify integrity with:

```bash
python code/utils/manifest_generator.py
```

## Deterministic Inputs

Input tensors are generated with fixed seeds to ensure construct validity.

## Configuration Snapshots

All configuration parameters (flags, dimensions, thresholds) are logged and can be recreated from `benchmarks/config.py`.

## Version Control

- **Python**: Version 3.8+
- **C++**: C++17 standard
- **Compilers**: GCC 11+ or Clang 14+
- **Dependencies**: Listed in `code/requirements.txt`

## Steps to Reproduce

1. Clone the repository.
2. Install dependencies: `pip install -r code/requirements.txt`.
3. Run the full pipeline: `python code/main.py`.
4. Verify outputs against `data/manifest.json`.

## Known Variability

- **Timing**: Latency measurements may vary slightly due to system load. Use block averaging to mitigate.
- **Compiler Versions**: Different compiler versions may produce slightly different binaries.

## Best Practices

- Always commit `data/manifest.json` with your results.
- Use the same compiler version for comparisons.
- Document any deviations from the standard pipeline.
