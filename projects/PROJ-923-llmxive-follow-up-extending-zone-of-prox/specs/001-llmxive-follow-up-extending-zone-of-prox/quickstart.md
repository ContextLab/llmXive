# Quickstart: llmXive Follow-up: Extending "Zone of Proximal Policy Optimization"

## Prerequisites

*   Python 3.11+
*   Git
*   Access to Hugging Face (for MMLU datasets)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    cd projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox
    ```

2.  **Create a virtual environment** and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Verify Hugging Face access** (if required for private datasets, though MMLU is public):
    ```bash
    huggingface-cli login
    ```

## Running the Simulation

### 1. Generate Synthetic Data

Run the data generation script to create the synthetic rollout logs. This step is deterministic based on the seed.

```bash
python code/data/generators.py --seeds 1 2 3 4 5 6 7 8 9 10 --output-dir data/synthetic
```

*   `--seeds`: List of random seeds to use (default: 1-10).
*   `--output-dir`: Directory to store generated logs.

### 2. Run Baseline (Static ZPPO)

Execute the static baseline simulation for all seeds.

```bash
python code/main.py --variant static --seeds 1 2 3 4 5 6 7 8 9 10 --output-dir data/metrics
```

### 3. Run CAP Variant

Execute the Confidence-Adaptive Pruning simulation for all seeds.

```bash
python code/main.py --variant cap --seeds 1 2 3 4 5 6 7 8 9 10 --output-dir data/metrics
```

*   `--variant`: Either `static` or `cap`.
*   `--epsilon`: (Optional) Override the default pruning threshold (default: 0.1).

### 4. Statistical Analysis

Run the analysis script to compare the two variants.

```bash
python code/analysis/stats.py --input data/metrics/aggregated_results.csv --output data/metrics/report.json
```

This will output a JSON report containing:
*   Mean AUCC for both variants.
*   P-value from the paired t-test.
*   Difference in final accuracy.
*   Average prompt length reduction.

## Viewing Results

The results are stored in `data/metrics/`. Key files:
*   `aggregated_results.csv`: Raw metrics for all runs.
*   `report.json`: Summary of statistical analysis.
*   `plots/`: (If generated) Convergence curves and prompt length distributions.

To generate plots (optional):
```bash
python code/analysis/plotting.py --input data/metrics/aggregated_results.csv --output plots/
```

## Troubleshooting

*   **Missing MMLU Data**: Ensure you have internet access and Hugging Face CLI is logged in.
*   **Empty Prompts**: Check `data/synthetic/run_metadata_*.json` for `edge_cases_triggered`. If high, consider adjusting `--epsilon`.
*   **Non-Convergence**: If the simulation fails to converge, verify the `expert_confidence` distribution in `code/models/expert.py`.

## Reproducibility

To reproduce the exact results:
1.  Pin the random seeds in `config.py`.
2.  Ensure the same version of `numpy` and `pandas` is used (check `requirements.txt`).
3.  Re-run the generation and simulation steps in order.
