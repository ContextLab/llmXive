# Configuration Guide

## Overview

The benchmark suite is highly configurable via `code/benchmarks/config.py`. This document details the available options.

## Compiler Flags

The following flags are supported:
- `-O0`: No optimization
- `-O1`: Basic optimization
- `-O2`: Standard optimization (default)
- `-O3`: Aggressive optimization
- `-Os`: Optimize for size
- `-march=native`: Optimize for native architecture
- `-ffast-math`: Fast but less precise math
- `-funroll-loops`: Unroll loops

Add or remove flags in `ConfigManager` as needed.

## Tensor Dimensions

Supported dimensions:
- 768x768 (default)
- 512x512

If memory pressure occurs, the executor automatically downsamples to 512x512.

## Iteration Count

- **Fixed**: 1000 iterations per configuration (default).
- **Adaptive**: Secondary stop condition if CV ≤ 1% after 30 iterations.

## Stability Threshold

- **Default**: 1e-5 relative error.
- Configurations exceeding this are flagged as unstable and excluded from final analysis.

## Logging

Logging is configured in `code/utils/logger.py`. Levels:
- `DEBUG`: Detailed internal state
- `INFO`: General progress
- `WARNING`: Non-critical issues
- `ERROR`: Critical failures

## Output Paths

- **Raw Data**: `data/raw/`
- **Intermediate Logs**: `data/intermediates/raw_logs/`
- **Results**: `data/results/`

Modify paths in `config.py` if needed.

## Customization

To add new configurations:
1. Edit `BenchmarkConfig` in `config.py`.
2. Update `create_default_manager()` to include new flags/dimensions.
3. Re-run the pipeline.

## Environment Variables

- `COMPILER_PATH`: Override default compiler path (g++/clang++).
- `MAX_MEMORY`: Set maximum memory usage (default: auto-detect).
