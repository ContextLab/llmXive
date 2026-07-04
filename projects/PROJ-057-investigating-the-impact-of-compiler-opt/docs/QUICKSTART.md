# Quick Start Guide

This guide provides a step-by-step walkthrough to get the benchmark suite running on a fresh environment.

## 1. Environment Setup

Ensure you have Python 3.8+ and a C++ compiler (GCC 11+ or Clang 14+) installed.

```bash
# Clone the project
cd projects/PROJ-057-investigating-the-impact-of-compiler-opt

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Verify Compiler Availability

The system requires a C++ compiler to build kernels dynamically.

```bash
g++ --version
# or
clang++ --version
```

## 3. Run the Full Experiment

Execute the main pipeline script. This will:
- Generate synthetic data.
- Compile kernels with default flags.
- Run benchmarks (1000 iterations per config).
- Analyze stability.
- Generate plots.

```bash
cd code
python main.py
```

**Expected Output**:
- Logs in `data/logs/`
- Raw logs in `data/intermediates/raw_logs/`
- Results in `data/results/` (CSVs and PNGs)

## 4. Inspect Results

- **Stability Metrics**: `data/results/stability_metrics.csv`
- **Aggregated Data**: `data/results/aggregated.csv`
- **Pareto Frontier**: `data/results/pareto_frontier_final.png`

## 5. Run Tests

Verify the installation and logic with the test suite:

```bash
pytest tests/
```

## Troubleshooting

- **Memory Error**: If the process fails due to memory, the system will automatically downsample to 512x512. Check the logs for "Memory Pressure".
- **Compiler Not Found**: Ensure `g++` or `clang++` is in your `PATH`.
- **NaN Detection**: If a configuration produces NaNs, it will be flagged in `stability_metrics.csv` with status "UNSTABLE".
