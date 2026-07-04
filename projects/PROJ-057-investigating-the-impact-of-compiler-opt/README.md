# PROJ-057: Investigating the Impact of Compiler Optimizations on LLM Inference Latency

## Overview

This project benchmarks the latency and numerical stability of LLM inference kernels (Matrix Multiplication, Softmax, LayerNorm) when compiled with various compiler optimization flags. The goal is to identify the Pareto frontier of performance versus numerical accuracy, specifically for CPU-based execution environments.

## Key Features

- **Deterministic Synthetic Data Generation**: Produces reproducible input tensors using fixed seeds.
- **High-Precision Reference Engine**: Computes ground truth using Python's `decimal` module (512-bit precision).
- **Dynamic Compilation**: Compiles C++ kernels on-the-fly with configurable optimization flags (`-O0` to `-O3`, `-ffast-math`, etc.).
- **Statistical Analysis**: Performs Welch's t-tests on block-averaged latency distributions to determine statistical significance.
- **Stability Auditing**: Detects NaNs and calculates L2 relative error and Max Absolute Difference against the reference.
- **Visualization**: Generates Pareto frontier plots distinguishing stable vs. downsampled configurations.

## Project Structure

```text
code/
├── kernels/ # C++ kernel implementations (matmul, softmax, layernorm)
├── benchmarks/ # Compilation, execution, and configuration logic
├── analysis/ # Statistical tests, stability checks, and visualization
├── utils/ # Logging and manifest generation utilities
├── main.py # Entry point for the full experiment pipeline
└── requirements.txt # Python dependencies

data/
├── raw/ # Generated input tensors and reference outputs
├── intermediates/ # Raw execution logs (JSONL) and binary artifacts
└── results/ # Aggregated CSVs, stability metrics, and plots

tests/
├── unit/ # Unit tests for configuration, stats, and stability
└── integration/ # End-to-end integration tests
```

## Prerequisites

- **Python 3.8+**: Required for running the analysis and orchestration scripts.
- **C++ Compiler**: GCC 11+ or Clang 14+ (required for compiling kernels).
- **Dependencies**: Install via `pip install -r code/requirements.txt`.

## Quick Start

### 1. Setup Environment

```bash
cd code
pip install -r requirements.txt
```

### 2. Run the Full Pipeline

The `main.py` script orchestrates the entire flow:
1. Generate synthetic tensors.
2. Compile kernels with various flags.
3. Execute benchmarks and collect latency data.
4. Compare results against the high-precision reference.
5. Perform statistical analysis and generate visualizations.

```bash
python main.py
```

*Note: The first run will take time as it compiles binaries and runs 1000 iterations per configuration.*

### 3. Run Specific Components

- **Generate Reference Data**:
 ```bash
 python benchmarks/reference.py
 ```

- **Compile and Run Benchmarks**:
 ```bash
 python benchmarks/compile_runner.py --test
 python benchmarks/executor.py
 ```

- **Analyze Stability**:
 ```bash
 python analysis/stability_check.py
 ```

- **Generate Visualizations**:
 ```bash
 python analysis/viz.py
 ```

## Configuration

Optimization flags and tensor dimensions are managed in `code/benchmarks/config.py`.
Supported flags include:
- `-O0`, `-O1`, `-O2`, `-O3`
- `-Os` (Size optimization)
- `-march=native`
- `-ffast-math`
- `-funroll-loops`

Tensor dimensions can be configured (default: 768x768, with auto-downsampling to 512x512 on memory pressure).

## Output Artifacts

Upon successful completion, the following artifacts are generated in `data/results/`:

- `aggregated.csv`: Block-averaged latency and error metrics.
- `stability_metrics.csv`: L2 error and Max Diff per configuration.
- `pareto_frontier_exploration.png`: Visualization including downsampled runs.
- `pareto_frontier_final.png`: Final Pareto frontier excluding unstable runs.

## Statistical Methodology

- **Block Averaging**: Latency measurements are averaged in blocks to reduce noise.
- **Welch's t-test**: Used to compare independent binaries (different flags) to determine statistical significance (p < 0.05).
- **Stability Threshold**: Configurations with L2 relative error > 1e-5 are flagged as unstable and excluded from final statistical analysis.

## Testing

Run the test suite:
```bash
pytest tests/
```

## License

Internal Research Project - PROJ-057
