# Quickstart: llmXive follow-up: extending "Rethinking Cross-Layer Information Routing in Diffusion Transformers"

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local machine with sufficient RAM).

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-907-llmxive-follow-up-extending-rethinking-c
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline consists of three sequential scripts.

### Step 1: Trace Dynamic Routing
Executes the dynamic model on a representative Trace Set of images one-by-one and saves the aggregated routing patterns.
```bash
python code/src/tracing.py --images 60 --timesteps 100 --batch-size 1
```
*Output*: `data/routing_cache/trace_patterns.npy`

### Step 2: Derive Static Map
Clusters the aggregated patterns and generates the static routing map.
```bash
python code/src/clustering.py --input data/routing_cache/trace_patterns.npy
```
*Output*: `data/routing_cache/static_routing_map.pt` (and logs of silhouette scores).

### Step 3: Benchmark & Analyze
Compares dynamic vs. static models across multiple seeds and performs sensitivity analysis.
```bash
python code/src/benchmark.py --static-map data/routing_cache/static_routing_map.pt --seeds 5 --benchmark-images 40
```
*Output*: `data/benchmarks/benchmark_results.csv`, `data/benchmarks/sensitivity_analysis.json`.

## Verification

To verify the results:
1. Check the `benchmark_results.csv` for the latency reduction and FID difference.
2. Confirm the silhouette score in the clustering logs (should be > 0.25 for distinct phases).
3. Run the unit tests:
   ```bash
   pytest code/tests/
   ```

## Troubleshooting

- **OOM Error**: The script defaults to `--batch-size 1`. If OOM occurs, reduce `--batch-size` to 1 (already default) and ensure no other processes are using memory.
- **Model Load Error**: Ensure the `google/sit-xl-2` or `llmXive` fork is accessible. Check internet connection. If the model is not found, the pipeline will halt with "Data Unavailable".
- **Clustering Null Result**: This is a valid outcome. The script will automatically fall back to global averaging. Check the logs for the "Null Hypothesis" flag.