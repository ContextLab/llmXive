# Quickstart: Exploring the Convergence of Iterated Function Systems with Non-Contractive Maps

## Prerequisites

-   Python 3.11+
-   Git
-   Sufficient RAM available (for intermediate processing)
-   GB+ Disk space

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-550-exploring-the-convergence-of-iterated-fu
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `numpy`, `scipy`, `scikit-learn`, `pandas`, `pytest`.*

## Running the Pipeline

The pipeline is executed sequentially via the main entry point. **Benchmark validation is mandatory before synthetic data processing.**

### 1. Generate Synthetic Data
Generates a substantial set of IFS instances and validates Lipschitz constants.
```bash
python code/generators.py --output data/raw/ifs_instances.parquet --count 500 --seed 42
```

### 2. Run Benchmarks (Mandatory)
Validates methodology against Sierpinski, Barnsley Fern, and da Cunha map.
```bash
python code/benchmarks.py --output data/derived/benchmark_results.parquet
```
*Success Criterion: Box-counting dimensions must match theoretical values within 0.1.*

### 3. Execute Chaos Game
Runs Monte Carlo simulations for all instances (with multi-stage convergence checks).
```bash
python code/chaos_game.py --input data/raw/ifs_instances.parquet --output data/derived/chaos_results.parquet --iterations a sufficiently large number to ensure convergence --seed 42
```

### 4. Compute Topology & Analysis
Calculates box-counting dimensions (and Transient Dimension) and fits the logistic regression model.
```bash
python code/topology.py --input data/derived/chaos_results.parquet --output data/derived/topology_results.parquet
python code/analysis.py --input data/derived/chaos_results.parquet --output data/derived/analysis_summary.csv
```

## Verification

Run the test suite to ensure contract compliance:
```bash
pytest tests/contract/ -v
```

## Expected Outputs

-   `data/derived/analysis_summary.csv`: Contains the logistic regression AUC and sensitivity analysis results.
-   `data/checksums.json`: Integrity manifest for all generated data.
-   Console output: Summary of convergence rates vs. Lipschitz constants.

## Troubleshooting

-   **Memory Error**: Reduce `--count` in `generators.py` or process in smaller batches.
-   **Timeout**: Reduce `--iterations` in `chaos_game.py` (note: this affects SC-002 accuracy).
-   **Benchmark Failure**: Check `code/benchmarks.py` for hardcoded parameter errors.