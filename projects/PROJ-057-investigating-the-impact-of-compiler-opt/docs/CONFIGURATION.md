# Configuration Reference

## Optimization Flags

The following flags are supported and can be combined in `code/benchmarks/config.py`:

| Flag | Description |
|:--- |:--- |
| `-O0` | No optimization (baseline) |
| `-O1` | Basic optimization |
| `-O2` | Standard optimization |
| `-O3` | Aggressive optimization |
| `-Os` | Optimize for size |
| `-march=native` | Target current CPU architecture |
| `-ffast-math` | Allow aggressive floating-point optimizations (may affect stability) |
| `-funroll-loops` | Unroll loops for performance |

## Tensor Dimensions

- **Default**: 768x768
- **Fallback**: 512x512 (triggered automatically on memory allocation failure)

## Iteration Count

- **Fixed**: 1000 iterations per configuration (Constitution Principle VII).
- **Adaptive Stop**: Secondary check if Coefficient of Variation (CV) ≤ 1% after 30 iterations (safety check only).

## Stability Thresholds

- **L2 Relative Error**: Configurations with error > 1e-5 are marked as unstable.
- **Max Absolute Difference**: Used as a secondary stability metric.

## Logging Configuration

Logging is configured in `code/utils/logger.py`. Logs are written to:
- `data/logs/experiment.log`: General execution logs.
- `data/logs/stability_audit.log`: Specific logs for NaN detection and stability failures.
