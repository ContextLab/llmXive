# Compiler Optimization Benchmark Suite

## Overview

This benchmark suite investigates the impact of compiler optimization flags on LLM inference latency.
It compiles C++ kernels with varying optimization settings, executes them to measure latency,
compares outputs against high-precision reference implementations, and performs statistical analysis.

## Project Structure

```
code/
├── kernels/ # C++ kernel implementations (MatMul, Softmax, LayerNorm)
├── benchmarks/ # Benchmark orchestration, compilation, and execution
├── analysis/ # Stability checks, statistical tests, and visualizations
├── utils/ # Logging and manifest generation utilities
├── main.py # Entry point for the full experiment flow
└── requirements.txt # Python dependencies

data/
├── raw/ # Generated input tensors and reference outputs
├── intermediates/ # Raw execution logs and binary artifacts
└── results/ # Aggregated metrics, statistical reports, and plots

tests/
├── unit/ # Unit tests for individual components
└── integration/ # Integration tests for end-to-end workflows
```

## Key Components

### Kernels (`code/kernels/`)

- **matmul.cpp**: Matrix multiplication kernel (C++17, float32)
- **softmax.cpp**: Softmax activation kernel
- **layernorm.cpp**: Layer normalization kernel

### Benchmark Orchestration (`code/benchmarks/`)

- **config.py**: Configuration manager for compiler flags and tensor dimensions
- **compile_runner.py**: Orchestrates compilation with dynamic flag injection and SHA-256 hashing
- **executor.py**: Runs binaries and measures latency with memory pressure handling
- **tensor_generator.py**: Deterministic synthetic tensor generation with fixed seeds
- **reference.py**: High-precision reference engine using Python `decimal` module (512-bit)

### Analysis (`code/analysis/`)

- **stability_check.py**: NaN detection, L2 relative error, and max absolute difference calculation
- **stats.py**: Block-averaging and Welch's Independent Samples t-test implementation
- **viz.py**: Pareto frontier generation (exploration and final plots)
- **aggregator.py**: Result aggregation and final Pareto frontier generation
- **stability_metrics_generator.py**: Stability metrics CSV generation

### Utilities (`code/utils/`)

- **logger.py**: Logging infrastructure for compiler versions, flags, and warnings
- **manifest_generator.py**: SHA-256 manifest generation for reproducibility

## Usage

### Quick Start

```bash
# Install dependencies
pip install -r code/requirements.txt

# Run the full experiment flow
python code/main.py

# Run specific components
python code/benchmarks/compile_runner.py --test
python code/analysis/stability_check.py
python code/analysis/viz.py
```

### Configuration

Compiler flags supported: `-O0`, `-O1`, `-O2`, `-O3`, `-Os`, `-march=native`, `-ffast-math`, `-funroll-loops`

Tensor dimensions: `768x768`, `512x512` (with automatic downscaling on memory pressure)

### Output Artifacts

- `data/intermediates/raw_logs/*.jsonl`: Raw execution logs with median, p95, iterations
- `data/results/stability_metrics.csv`: Stability metrics per configuration
- `data/results/pareto_frontier_exploration.png`: Pareto frontier including all stable configurations
- `data/results/pareto_frontier_final.png`: Final Pareto frontier excluding unstable configurations
- `data/results/aggregated.csv`: Final aggregated results
- `data/manifest.json`: SHA-256 hashes for all artifacts

## Statistical Methodology

- **Block-Averaging**: Latency distributions are block-averaged for statistical power
- **Welch's t-test**: Used for comparing independent binary configurations (p<0.05 threshold)
- **Stability Threshold**: Configurations with error > 1e-5 are excluded from final results
- **Fixed Iterations**: 1000 iterations per configuration (Constitution Principle VII)

## Reproducibility

All experiments are reproducible via:
- Fixed random seeds for tensor generation
- SHA-256 hashing of compiled binaries
- Comprehensive logging of compiler versions and flag combinations
- Manifest generation for all output artifacts

## Testing

Run unit tests:
```bash
pytest tests/unit/ -v
```

Run integration tests:
```bash
pytest tests/integration/ -v
```

## Notes

- This suite is designed for CPU-only, multi-core, constrained RAM environments
- No GPU acceleration or quantization is used
- All external data is obtained from verified real sources
- The system fails loudly if real data cannot be obtained (no synthetic fallbacks)
