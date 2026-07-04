# Architecture Documentation

## System Overview

The system is designed to evaluate the trade-off between compiler optimization levels and numerical stability in LLM inference kernels. It follows a modular pipeline architecture:

1. **Data Generation**: Synthetic tensors are created with deterministic seeds.
2. **Reference Calculation**: High-precision ground truth is computed using `decimal`.
3. **Compilation & Execution**: C++ kernels are compiled with dynamic flags and executed.
4. **Analysis**: Stability and statistical significance are calculated.
5. **Visualization**: Results are plotted to identify Pareto optimal configurations.

## Module Responsibilities

### `benchmarks/`

- **`config.py`**: Manages optimization flags and tensor dimensions. Validates flag combinations.
- **`tensor_generator.py`**: Generates input tensors (Normal/Uniform distributions) with fixed seeds.
- **`reference.py`**: Implements high-precision MatMul, Softmax, and LayerNorm using `decimal`.
- **`compile_runner.py`**: Handles C++ compilation, binary hashing, and flag injection.
- **`executor.py`**: Runs compiled binaries, measures latency via `std::chrono`, and handles memory pressure (downsampling).

### `analysis/`

- **`stability_check.py`**: Loads raw logs, detects NaNs, calculates L2 error and Max Diff. Flags unstable runs.
- **`stats.py`**: Implements block-averaging and Welch's t-test for independent samples.
- **`viz.py`**: Generates Pareto frontier plots (Exploration vs. Final).
- **`aggregator.py`**: Combines latency and stability metrics into final CSVs.

### `utils/`

- **`logger.py`**: Centralized logging for compiler versions, flags, and runtime warnings.
- **`manifest_generator.py`**: Generates `data/manifest.json` with SHA-256 hashes for reproducibility.

## Data Flow

1. **Input**: `code/benchmarks/config.py` defines the experiment space.
2. **Raw Data**: `code/benchmarks/tensor_generator.py` writes to `data/raw/`.
3. **Intermediate**: `code/benchmarks/executor.py` writes latency logs to `data/intermediates/raw_logs/`.
4. **Stability**: `code/analysis/stability_check.py` produces `data/results/stability_metrics.csv`.
5. **Final**: `code/analysis/aggregator.py` and `viz.py` produce final CSVs and plots in `data/results/`.

## Error Handling

- **Memory Pressure**: If 768x768 allocation fails, the executor auto-downsamples to 512x512, logs "Memory Pressure", and continues.
- **Stability Failures**: Runs with NaNs or error > 1e-5 are excluded from statistical analysis but retained in raw logs for audit.
- **Compilation Failures**: Invalid flags or missing compilers cause immediate failure with clear error messages.

## Extensibility

- **New Kernels**: Add C++ files in `code/kernels/` and register them in `compile_runner.py`.
- **New Flags**: Add to the flag list in `code/benchmarks/config.py`.
- **New Metrics**: Extend `analysis/stability_check.py` and `aggregator.py`.
