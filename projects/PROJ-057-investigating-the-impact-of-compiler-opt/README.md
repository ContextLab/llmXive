# Investigating the Impact of Compiler Optimizations on LLM Inference Latency

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project benchmarks the impact of various compiler optimization flags on LLM inference latency
by compiling and executing C++ kernels, measuring performance, and analyzing numerical stability.

## Features

- **Kernel Compilation**: Compile C++ kernels (MatMul, Softmax, LayerNorm) with different optimization flags
- **Latency Measurement**: Execute binaries and measure latency with statistical rigor
- **Stability Analysis**: Compare optimized outputs against high-precision reference implementations
- **Statistical Testing**: Perform Welch's t-test to determine significance of performance differences
- **Visualization**: Generate Pareto frontier plots exploring the latency-accuracy tradeoff

## Quick Start

### Prerequisites

- Python 3.9+
- GCC 11+ or Clang 14+
- CMake (optional, for building dependencies)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-057-investigating-the-impact-of-compiler-opt

# Install Python dependencies
pip install -r code/requirements.txt
```

### Running the Benchmark

```bash
# Run the full experiment flow
python code/main.py

# Run specific components
python code/benchmarks/compile_runner.py --test
python code/analysis/stability_check.py
python code/analysis/viz.py
```

## Project Structure

```
.
 ├── code/
 │ ├── kernels/ # C++ kernel implementations
 │ ├── benchmarks/ # Benchmark orchestration
 │ ├── analysis/ # Analysis and visualization
 │ ├── utils/ # Utility modules
 │ ├── main.py # Entry point
 │ └── requirements.txt # Dependencies
 ├── data/
 │ ├── raw/ # Input tensors and references
 │ ├── intermediates/ # Raw logs and binaries
 │ └── results/ # Final outputs
 ├── tests/
 │ ├── unit/ # Unit tests
 │ └── integration/ # Integration tests
 ├── docs/ # Documentation
 └── README.md # This file
```

## Methodology

1. **Tensor Generation**: Deterministic synthetic tensors with fixed seeds
2. **Reference Implementation**: High-precision (512-bit) reference using Python `decimal` module
3. **Compilation**: Compile kernels with flags: `-O0`, `-O1`, `-O2`, `-O3`, `-Os`, `-march=native`, `-ffast-math`, `-funroll-loops`
4. **Execution**: Run binaries 1000 times per configuration, measure latency
5. **Stability Check**: Calculate L2 relative error and max absolute difference vs reference
6. **Statistical Analysis**: Block-averaging and Welch's t-test for significance
7. **Visualization**: Generate Pareto frontier plots

## Output Artifacts

- `data/results/stability_metrics.csv`: Stability metrics per configuration
- `data/results/pareto_frontier_exploration.png`: Exploration plot (all stable configs)
- `data/results/pareto_frontier_final.png`: Final Pareto frontier (excluding unstable)
- `data/results/aggregated.csv`: Aggregated results
- `data/manifest.json`: SHA-256 hashes for reproducibility

## Configuration

### Compiler Flags

Supported flags: `-O0`, `-O1`, `-O2`, `-O3`, `-Os`, `-march=native`, `-ffast-math`, `-funroll-loops`

### Tensor Dimensions

- 768x768 (default)
- 512x512 (fallback on memory pressure)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/unit/ -v
pytest tests/integration/ -v
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with Python 3.9+
- Uses NumPy, SciPy, Matplotlib, Pandas for analysis
- C++17 for kernel implementations
- GCC/Clang for compilation