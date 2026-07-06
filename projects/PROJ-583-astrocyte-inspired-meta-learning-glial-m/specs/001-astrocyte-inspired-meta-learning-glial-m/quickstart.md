# Quickstart: Astrocyte-Inspired Meta-Learning

## Prerequisites

- Python 3.10 or higher.
- pip (Python package installer).
- Git.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd <project-root>
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
    *Note: This installs CPU-optimized PyTorch and necessary libraries.*

## Running the Experiments

### 1. Basic Run (Omniglot, Astrocyte Mode)
Runs the validation subset with the astrocyte module enabled.
```bash
python -m src.cli.run_experiment --config config/default.yaml --mode astrocyte
```
*Output*: `results/metrics.csv`, `results/stat_test.json`.

### 2. Baseline Comparison
Runs the vanilla MAML baseline for comparison.
```bash
python -m src.cli.run_experiment --config config/default.yaml --mode baseline
```

### 3. Ablation Study (Sensitivity Sweep)
Runs the experiment with different homeostatic scale parameters.
```bash
python -m src.cli.run_experiment --config config/default.yaml --mode ablation --params 0.01,0.05,0.1
```

### 4. Statistical Analysis Only
If you have existing result files, run the statistical test independently.
```bash
python -m src.analysis.stats --input results/metrics.csv
```

## Verifying the Results

1.  **Check Logs**: Ensure `results/metrics.csv` contains columns `mean_plasticity_score_5` and `mean_stability_score`.
2.  **Check Plasticity Breakdown**: Verify that the training logs contain `plasticity_score_1`, `plasticity_score_5`, and `plasticity_score_10` for each episode.
3.  **Check ODE**: Verify `Ca_t` values are clamped between 0 and 1 in the logs.
4.  **Check Statistics**: Ensure `results/stat_test.json` contains a `verdict` and `p_value`. Primary test should be "Permutation Test"; secondary reference may include "Hotelling's T-squared".
5.  **Check Buffer Independence**: Verify that the calcium history buffer does not include tasks N-1 or N; the Meta-Test Buffer is separate.

## Troubleshooting

- **OOM (Out of Memory)**: Omniglot is designed to fit in a compact size suitable for efficient storage and transfer. If OOM occurs, check system RAM availability or reduce `episodes_per_seed` in the config.
- **CUDA Error**: Ensure you are using the CPU version of PyTorch. The code should not attempt to use CUDA.
- **Statistical Singularity**: If the covariance matrix is singular, the code automatically applies a ridge penalty. If this fails, the result will be marked "undefined" or "singular".
- **Inconclusive Result**: With N=5 seeds, statistical power is limited. If the result is "inconclusive" with reason "insufficient_power", this is expected. Full-scale validation requires N ≥ 20 seeds.
- **Mini-ImageNet Not Available**: Mini-ImageNet is not supported on GitHub Actions free-tier. For local/cloud execution, identify a verified Mini-ImageNet source and update the `datasets.name` in the config.
