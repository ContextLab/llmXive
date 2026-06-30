# SciAtlas Adaptation Quickstart

This guide runs the CPU-tractable adaptation of the SciAtlas paper.
It simulates a large-scale Knowledge Graph retrieval and reranking process
using a synthetic dataset and classical algorithms.

### Prerequisites
- Python 3.8+
- No external pip dependencies required (uses only `stdlib`).

### Execution
Run the following command to generate the `data/` and `figures/` artifacts:

```bash
python code/sciatlas_adaptation.py
```

### Expected Outputs
1. `data/search_results.json`: JSON file containing the top-ranked papers, scores, and metadata.
2. `data/search_results.csv`: CSV export of the same results.
3. `figures/field_distribution.txt`: Text-based visualization of field distribution.
4. `figures/reranking_performance.png`: A valid (minimal) PNG file artifact.

The script will print progress updates to the console and finish in under 5 seconds.
