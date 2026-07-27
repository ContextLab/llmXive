# Quickstart: llmXive Noise Injection Pipeline

This guide walks you through setting up and running the optimized noise injection pipeline.

## Prerequisites

- Python 3.9+
- 16GB+ RAM (recommended for full dataset)
- CPU-only execution (no GPU required)

## Setup

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd llmxive-follow-up-extending-formalizing
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

4. **Verify installation**
 ```bash
 python -c "import torch; import transformers; print('OK')"
 ```

## Running the Pipeline

### Full Execution

Run the entire pipeline (baseline extraction, noise sweep, analysis):

```bash
python code/main.py
```

This will:
1. Load the `bigbench_lite` dataset
2. Extract baseline latent vectors
3. Perform the noise injection sweep with vectorized operations
4. Run statistical analysis and save results

### Benchmarking Optimization (T036)

To verify the performance improvement of the vectorized implementation:

```bash
python code/benchmark_perturbation.py
```

This script compares the scalar vs. vectorized perturbation methods and outputs:
- Average runtime per method
- Throughput (samples/second)
- Speedup factor

### Output Files

Results are saved to `data/processed/`:

- `baseline_vectors.csv`: Baseline latent vectors
- `perturbed_vectors.csv`: Perturbed vectors for each sigma level
- `validity_log.csv`: Validity check results and collapse points
- `statistical_results.json`: Final analysis results
- `benchmark_results.json`: Performance comparison (if benchmarked)

## Troubleshooting

- **Memory Error**: Ensure you have sufficient RAM. The pipeline enforces a 7GB limit.
- **Dataset Missing**: The pipeline fetches data from HuggingFace. Ensure internet connectivity.
- **CPU Only**: No CUDA support is included. The pipeline runs on CPU by default.
