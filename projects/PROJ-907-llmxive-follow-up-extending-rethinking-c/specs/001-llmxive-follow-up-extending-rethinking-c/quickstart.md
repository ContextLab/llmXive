# Quickstart: llmXive follow-up: extending "Rethinking Cross-Layer Information Routing in Diffusion Transformers"

## Prerequisites

-   Python 3.11+
-   Git
-   (Optional) Kaggle CLI for GPU offload (if CPU fails)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-907-llmxive-follow-up-extending-rethinking-c
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed in three main phases. Ensure you have sufficient disk space for intermediate traces.

### Phase 1: Tracing & Clustering
This phase records routing weights and derives the canonical map.
```bash
python code/src/tracing.py --images 100 --batch-size 10
python code/src/clustering.py --input data/routing_cache/
python code/src/canonical_map.py --input data/routing_cache/cluster_centers.json --output data/routing_cache/canonical_map.json
```

### Phase 2: Benchmarking
This phase compares the dynamic and static models.
```bash
python code/src/benchmark.py --mode dynamic --seed 42 --images 500 --output data/results/benchmark_results.json
python code/src/benchmark.py --mode static --seed 42 --images 500 --output data/results/benchmark_results.json
# Repeat for 5 seeds (script can handle loop)
```

### Phase 3: Statistical Analysis
This phase performs the bootstrap and sensitivity sweep.
```bash
python code/src/stats_analysis.py --input data/results/benchmark_results.json --output data/results/statistical_analysis.json --sweep
```

## Verification

1.  **Check Schemas**:
    ```bash
    python -m json.tool data/routing_cache/canonical_map.json | grep -q "static_weights" && echo "Valid"
    ```
2.  **Verify Memory**: Check `data/results/memory_report.json` to ensure `peak_gb` < 7.0 and `status` is "PASS".
3.  **Check FID**: Ensure `statistical_analysis.json` reports a `significant` flag and `p_value`.

## Troubleshooting

-   **OOM Error**: If you encounter `RuntimeError: CUDA out of memory` or CPU OOM, reduce `--batch-size` in the tracing step or enable the GPU offload flag (if configured).
-   **Dataset 404**: Ensure you are using the `ILSVRC/imagenetk` dataset ID.
-   **Clustering Failure**: If `null_hypothesis` is true, the system automatically falls back to a global average. Check `data/routing_cache/cluster_centers.json` for the `silhouette_score`.
