# Quickstart: llmXive follow-up: extending "Heterogeneous Scientific Foundation Model Collaboration"

## Prerequisites

- Python 3.11+
- pip
- Access to a GitHub Actions free-tier runner (or local environment with a constrained RAM limit).

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `sentence-transformers` to a CPU-compatible version.*

## Running the Experiments

### 1. Generate Synthetic Data
If the "Eywa" benchmark is not available, generate the synthetic dataset:
```bash
python -m code.data.generator --count 500 --warmup 100 --output data/derived/queries.json
```

### 2. Run Baseline Execution
Execute the pipeline without caching to establish the baseline:
```bash
python -m code.pipeline.runner --mode baseline --input data/derived/queries.json --output data/derived/results_baseline.csv
```

### 3. Run Cached Execution (Sensitivity Analysis)
Run the pipeline with the semantic cache enabled at different thresholds:
```bash
# Threshold 0.90
python -m code.pipeline.runner --mode cached --threshold 0.90 --input data/derived/queries.json --output data/derived/results_0.90.csv

# Threshold 0.95
python -m code.pipeline.runner --mode cached --threshold 0.95 --input data/derived/queries.json --output data/derived/results_0.95.csv

# Threshold 0.99
python -m code.pipeline.runner --mode cached --threshold 0.99 --input data/derived/queries.json --output data/derived/results_0.99.csv
```

### 4. Analyze and Visualize
Generate the trade-off curve, statistical reports, and JSON summary:
```bash
python -m code.analysis.visualization --input data/derived/results_*.csv --output figures/trade-off-curve.png
python -m code.analysis.stats --input data/derived/results_*.csv --output reports/statistical_significance.json
```

## Expected Outputs

- `data/derived/queries.json`: The synthetic benchmark dataset.
- `data/derived/results_*.csv`: Execution metrics for each threshold (including similarity scores).
- `figures/trade-off-curve.png`: Visualization of hit-rate vs. accuracy vs. runtime.
- `reports/statistical_significance.json`: P-values from Permutation Test and regression coefficients.

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, ensure you are not running the experiment on a machine with <7GB RAM. The code implements an LRU cache, but large embedding matrices can consume memory.
- **Slow Runtime**: The baseline run may take several hours on a multi-core CPU. This is expected. If it exceeds 6 hours, reduce the `--count` in the generator step.
- **CUDA Error**: Ensure `CUDA_VISIBLE_DEVICES=""` is set if running on a machine with NVIDIA GPUs, to force CPU usage as per the project constraints.