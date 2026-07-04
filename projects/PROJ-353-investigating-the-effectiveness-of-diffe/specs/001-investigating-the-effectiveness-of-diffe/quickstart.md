# Quickstart: Investigating Loss Functions on Small-World Graphs

## Prerequisites

-   Python 3.10+
-   pip

## Installation

1.  Clone the repository and navigate to the project root.
2.  Install dependencies:
    ```bash
    pip install -r code/requirements.txt
    ```
    *(Note: Ensure `torch` is installed with CPU support only. If using `pip install torch`, it defaults to CPU on non-CUDA environments. Explicitly verify `torch.cuda.is_available()` is False).*

## Running the Experiment

The full pipeline is orchestrated by `code/main.py`.

```bash
python code/main.py
```

This script performs the following steps sequentially:
1.  **Generate Data**: Creates 50 Watts-Strogatz graphs with varying $\beta$ and saves them to `data/raw/`.
2.  **Train Models**: Trains a multi-layer GCN on each graph using Cross-Entropy and InfoNCE losses. Logs trajectories to `data/logs/`.
3.  **Analyze**: Computes Pearson correlations and ANCOVA interaction terms. Saves results to `data/analysis/`.

## Reproducing Results

To ensure reproducibility, the random seed is pinned in `code/utils.py`.
To re-run the experiment with a different seed (for robustness checks), modify `SEED` in `code/utils.py` and re-run `main.py`.

## Verifying Outputs

After the script completes, verify the existence of:
-   `data/raw/graphs.jsonl` (50 entries)
-   `data/logs/training_runs.jsonl` (100 entries)
-   `data/analysis/results.json` (1 entry)

You can inspect the results with:
```bash
cat data/analysis/results.json | python -m json.tool
```

## Troubleshooting

-   **Memory Error**: Unlikely with N=100 graphs. If occurring, reduce `N` in `code/data_generation.py`.
-   **CUDA Error**: Ensure `torch` is not installed with CUDA support. Use `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
-   **Convergence Failure**: If many runs are censored (max epochs), the learning rate in `code/train.py` may need adjustment (The default is set to a small, non-zero value.).
