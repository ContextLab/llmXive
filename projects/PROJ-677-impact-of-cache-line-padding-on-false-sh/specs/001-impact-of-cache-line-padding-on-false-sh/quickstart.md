# Quickstart: Impact of Cache Line Padding on False Sharing in Concurrent Counters

## Prerequisites

- Git
- C++ compiler (g++ with C++17 support)
- Python 3.11+
- pip

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-677-impact-of-cache-line-padding-on-false-sh
   ```

2. **Install Python dependencies**:
   ```bash
   cd code/analysis
   pip install -r requirements.txt
   cd ../..
   ```

## Build the Benchmark

1. **Compile the C++ code**:
   ```bash
   cd code/scripts
   ./build.sh
   ```
   This compiles `code/benchmark/main.cpp` with `-O3 -march=native` and places the executable in `code/benchmark/benchmark`.

2. **Verify compilation**:
   ```bash
   ./code/benchmark/benchmark --threads 1 --config packed --iterations 1000
   ```
   The benchmark should complete quickly and print timing data.

## Run the Experiments

1. **Execute the full benchmark suite**:
   ```bash
   cd code/scripts
   ./run_benchmarks.sh
   ```
   This script runs the benchmark for all thread counts (1, 2, 4, 8) and configurations (packed, padded), with 5 replications each. Raw CSV files are saved to `data/raw/`.

   *Note: This step may take up to 6 hours on a GitHub Actions runner.*

## Analyze the Results

1. **Run the analysis script**:
   ```bash
   cd code/analysis
   python run_analysis.py
   ```
   This script:
   - Reads raw CSV files from `../data/raw/`.
   - Computes aggregated statistics and 95% CIs.
   - Performs t-tests and FDR correction.
   - Generates a plot (`../data/processed/throughput_plot.png`).
   - Saves results to `../data/processed/`.

2. **View the results**:
   - Aggregated results: `../data/processed/aggregated_results.csv`
   - Statistical comparisons: `../data/processed/statistical_comparison.csv`
   - Plot: `../data/processed/throughput_plot.png`

## Run on GitHub Actions

1. **Push to the feature branch**:
   ```bash
   git push origin 001-cache-line-padding-false-sharing
   ```

2. **Trigger the workflow**:
   The `.github/workflows/benchmark.yml` workflow will automatically run the build, experiment, and analysis steps on a GitHub Actions runner.

3. **View results**:
   - Check the "Actions" tab in the repository for workflow logs.
   - Download artifacts (CSVs and plots) from the workflow run summary.
