# User Guide

## Getting Started

This guide walks you through using the benchmark suite to investigate compiler optimizations.

### Step 1: Setup

Ensure you have Python 3.8+ and a C++ compiler (GCC 11+ or Clang 14+). Install dependencies:

```bash
cd code
pip install -r requirements.txt
```

### Step 2: Generate Input Data

Run the tensor generator to create deterministic input tensors:

```bash
python benchmarks/tensor_generator.py
```

This creates files in `data/raw/`.

### Step 3: Generate Reference Outputs

Compute high-precision reference outputs:

```bash
python benchmarks/reference.py
```

This also saves to `data/raw/`.

### Step 4: Compile and Execute

Compile kernels with various optimization flags and measure latency:

```bash
python benchmarks/compile_runner.py
python benchmarks/executor.py
```

Results are saved to `data/intermediates/raw_logs/`.

### Step 5: Analyze Stability

Compare optimized outputs against references:

```bash
python analysis/stability_check.py
```

This generates `data/results/stability_metrics.csv`.

### Step 6: Statistical Analysis

Perform Welch's t-test and generate comparison reports:

```bash
python analysis/stats.py
```

### Step 7: Visualization

Generate Pareto frontier plots:

```bash
python analysis/viz.py
```

Outputs include `data/results/pareto_frontier_exploration.png` and `data/results/pareto_frontier_final.png`.

## Understanding Results

- **stability_metrics.csv**: Contains L2 error and max diff per configuration.
- **aggregated.csv**: Block-averaged latency and error data.
- **pareto_frontier_*.png**: Visual trade-offs between latency and error.

## Troubleshooting

- **Memory Pressure**: If 768x768 allocation fails, the executor automatically downsamples to 512x512.
- **NaN Detection**: Unstable configurations are logged but excluded from final analysis.
- **Compiler Issues**: Ensure GCC 11+ or Clang 14+ is installed and in PATH.

## Advanced Usage

- **Custom Flags**: Modify `benchmarks/config.py` to add new compiler flags.
- **Custom Kernels**: Add new `.cpp` files to `code/kernels/` and update the compile runner.
- **Batch Processing**: Use `main.py` to run the entire pipeline in one command.

## Best Practices

- Always run the full pipeline to ensure reproducibility.
- Check `data/manifest.json` to verify output integrity.
- Use `pytest` to validate your setup before running large experiments.
