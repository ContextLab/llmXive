# Quickstart: Kairos: A Native World Model Stack for Physical AI

## Prerequisites

- Python 3.11+
- pip
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-740-kairos-a-native-world-model-stack-for-ph
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
    *Note: Ensure `mujoco` and `torch` are installed for CPU only. Do not install CUDA versions.*

## Running the Baseline Experiment

To train the baseline Transformer and evaluate it:

```bash
python code/main.py --model baseline --epochs 50 --seed 42
```

This will:
1.  Load the BridgeData V2 Kitchen subset.
2.  Train the model.
3.  Run evaluation on a representative set of test trajectories.
4.  Log metrics to `artifacts/logs/baseline_run_42.json`.

## Running the Kairos Experiment

To train the Hybrid Multi-Scale Memory model:

```bash
python code/main.py --model kairos --epochs 50 --seed 42 --sparsity 0.5
```

## Reproducing the Full Study (5 Seeds)

To run the full statistical analysis across 5 random seeds:

```bash
python code/main.py --mode full_study --seeds 0 1 2 3 4
```

This script will:
1.  Train both models for each seed.
2.  Evaluate both models.
3.  Perform the Bootstrap CI and Wilcoxon signed-rank test.
4.  Generate a summary report in `artifacts/reports/final_comparison.md`.

## Verifying Constraints

The system automatically logs resource usage. To verify compliance:

```bash
python code/utils/logger.py --check artifacts/logs/
```

This will report if any run exceeded high RAM usage, 100ms inference (target), or 200ms total loop.

## Troubleshooting

- **OOM Errors**: Reduce `batch_size` in `config.py` or decrease `hidden_dim`.
- **Simulation Crashes**: Check `artifacts/logs/` for physics errors. If frequent, reduce simulation time step or check obstacle placement.
- **Missing Datasets**: If the loader fails to fetch BridgeData V2, the system will exit with a clear error code (no synthetic fallback).
