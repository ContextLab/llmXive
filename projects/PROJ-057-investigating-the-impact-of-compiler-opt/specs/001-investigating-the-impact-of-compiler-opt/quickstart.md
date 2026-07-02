# Quickstart: Investigating the Impact of Compiler Optimizations on LLM Inference Latency

## Prerequisites

-   **OS**: Linux (Ubuntu 20.04+ recommended for GitHub Actions compatibility).
-   **Compilers**: GCC 11+ and Clang 14+ installed.
-   **Python**: 3.11+ with `pip`.
-   **Dependencies**: `numpy`, `scipy`, `matplotlib`, `pyyaml`, `pytest`, `pandas`.

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    cd projects/PROJ-057-investigating-the-impact-of-compiler-opt
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Verify compilers**:
    ```bash
    gcc --version
    clang --version
    ```
    *Ensure versions meet the minimum requirements (GCC 11+, Clang 14+).*

## Running the Benchmark

To run the full experiment (all kernels, all compilers, all flag combinations, 5 seeds, [deferred] iterations):

```bash
cd code
python main.py
```

### Running a Single Configuration (Debug Mode)

To test a specific kernel and flag set (e.g., GCC, MatMul, `-O3`) with a reduced iteration count for debugging:

```bash
python benchmarks/compile_runner.py --compiler gcc --kernel matmul --flags "-O3"
python benchmarks/executor.py --config gcc-O3-matmul --iterations 100 --seeds 42 43 44 45 46
```
*Note: The full experiment requires [deferred] iterations per config as mandated by the Constitution.*

## Analyzing Results

Once the benchmark completes, data will be in `data/results/`.

1.  **View Aggregated Statistics**:
    ```bash
    python -c "import pandas as pd; df = pd.read_csv('data/results/aggregated.csv'); print(df[['config_id', 'median_latency_ns', 'max_l2_error', 'stability_pass']])"
    ```

2.  **Generate Pareto Frontier Plot**:
    ```bash
    python analysis/viz.py --input data/results/aggregated.csv --output data/results/pareto_plot.png
    ```
    *Note: The plot will include both stable (blue) and unstable (red) points.*

3.  **Run Statistical Tests**:
    ```bash
    python analysis/stats.py --input data/results/aggregated.csv --output data/results/significance_report.json
    ```

4.  **Verify Versioning Manifest**:
    ```bash
    cat data/manifest.json
    ```

## Testing

Run the unit and integration tests:

```bash
pytest tests/
```

## Troubleshooting

-   **Compilation Error**: Ensure GCC/Clang versions are sufficient. Check `code/benchmarks/compile_runner.py` for flag compatibility.
-   **Memory Error**: If running on a machine with < 4GB RAM, reduce tensor size in `code/main.py` (e.g., change `768` to `512`).
-   **NaN in Output**: Check if `-ffast-math` is causing instability. The script will log this as "NaN Failure" and plot it as an unstable point.
- **Runtime Error**: If the job times out, ensure the tensor size is not too large. The default 768x768 is optimized for the 6h limit with [deferred] iterations.
