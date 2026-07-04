# User Guide

## Introduction

This guide explains how to use the benchmark suite to investigate the impact of compiler optimizations on LLM inference latency.

## Getting Started

1. **Setup**: Follow the installation instructions in `INSTALLATION.md`.
2. **Configuration**: Edit `code/benchmarks/config.py` to select your optimization flags and tensor dimensions.
3. **Run**: Execute `python code/main.py`.
4. **Analyze**: Review the results in `data/results/`.

## Understanding Results

- **Latency**: Lower is better.
- **Stability**: Lower error is better. Error > 1e-5 is considered unstable.
- **Pareto Frontier**: The set of configurations where you cannot improve latency without worsening stability, and vice versa.

## Customizing the Experiment

### Changing Optimization Flags

Edit the `FLAGS` list in `code/benchmarks/config.py`:

```python
FLAGS = ["-O0", "-O2", "-O3", "-ffast-math"]
```

### Changing Tensor Dimensions

Edit the `DIMENSIONS` list in `code/benchmarks/config.py`:

```python
DIMENSIONS = [(768, 768), (512, 512)]
```

## Interpreting Plots

- **Pareto Frontier**: Points on the curve are the optimal trade-offs. Points below and to the left are better.
- **Error Distribution**: Shows the distribution of L2 errors across configurations.

## Next Steps

- **Extend**: Add new kernels or optimization flags.
- **Deep Dive**: Analyze specific configurations in detail using the raw logs.
- **Report**: Use the generated CSVs and plots for your research report.
