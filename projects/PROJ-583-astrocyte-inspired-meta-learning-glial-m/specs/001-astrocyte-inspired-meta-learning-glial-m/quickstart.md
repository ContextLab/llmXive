# Quickstart: Astrocyte-Inspired Meta-Learning

## Prerequisites

- Python 3.10+
- Git
- 7GB+ RAM (recommended for Mini-ImageNet)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-583-astrocyte-inspired-meta-learning-glial-m
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

## Data Preparation

The datasets will be automatically downloaded and cached on the first run.

- **Omniglot**: Downloaded via `torchvision`.
- **Mini-ImageNet**: Downloaded via `torchvision` (ensure sufficient disk space).

To manually verify data integrity:
```bash
python code/data_loader.py --verify
```

## Running the Experiments

### 1. Baseline MAML (Vanilla)
Run the vanilla MAML baseline for 5 seeds:
```bash
python code/main.py --mode baseline --seeds 0 1 2 3 4 --dataset omniglot
```

### 2. Astrocyte-Modulated MAML
Run the astrocyte-modulated model:
```bash
python code/main.py --mode astrocyte --seeds 0 1 2 3 4 --dataset omniglot --ode-params "tau=1.0,alpha=0.5,beta=0.1,lambda=0.5"
```

### 3. Ablation Study (Sensitivity Sweep)
Run a sensitivity analysis on the homeostatic scale parameter:
```bash
python code/ablation.py --mode sweep --params "0.01,0.05,0.1" --dataset omniglot
```

### 4. Statistical Analysis
Compute the Permutation Test and generate the final report:
```bash
python code/stats.py --baseline results/baseline/ --astrocyte results/astrocyte/
```

## Output

- **Logs**: `results/` directory contains JSON files for each episode and seed.
- **Report**: `results/stats_test.json` contains the final statistical verdict (Permutation Test).
- **Plots**: (Optional) Use `code/plot_results.py` to generate figures from the logs.

## Troubleshooting

- **OOM Error**: Reduce the number of classes in Mini-ImageNet or use Omniglot.
- **CUDA Error**: Ensure `CUDA_VISIBLE_DEVICES=""` is set; the code is CPU-only.
- **Statistical Power**: If the report says "inconclusive", it means the sample size (seeds) was insufficient for the observed effect size. This is a valid result.
- **Circular Validation**: Ensure the code excludes Task N-1 from the history buffer when calculating the homeostatic factor for Task N.