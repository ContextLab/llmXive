# Quickstart: Evaluating the Effectiveness of Differential Privacy in Federated Learning

## Prerequisites

- Python 3.10+
- Git
- (Note: This project runs on CPU-only GitHub Actions runners. No GPU or Kaggle CLI is required.)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-044-evaluating-the-effectiveness-of-differen
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
    *Note*: `requirements.txt` pins PyTorch (CPU), Opacus, `datasets`, `scipy`, `pandas`, `statsmodels`.

## Data Preparation

1.  **Download FEMNIST**:
    ```bash
    python code/data/download.py --dataset femnist
    ```
    *Output*: `data/raw/femnist_train.parquet`, `data/raw/femnist_test.parquet`.

2.  **Verify Checksums**:
    The script automatically generates and stores SHA-256 checksums in `data/checksums.json`.

## Running the Experiments

### Baseline (Non-DP, Homogeneous)
```bash
python code/main.py run --dataset femnist --alpha 1.0 --epsilon 10.0 --seeds 3
```

### DP-FL with Heterogeneity (Critical Threshold)
```bash
python code/main.py run --dataset femnist --alpha 0.1 --epsilon 0.5 --seeds 3
```

### Full Sensitivity Sweep
```bash
python code/main.py sweep --dataset femnist --alphas 0.05,0.1,0.5,1.0 --epsilons 0.1,0.5,1.0,5.0,10.0
```

## Analysis & Visualization

1.  **Run Statistical Tests**:
    ```bash
    python code/analysis/stats.py --input results/raw_results.csv
    ```
    *Output*: `results/final_stats.csv` (p-values, significance flags, LMM results).

2.  **Generate Plots**:
    ```bash
    python code/analysis/plots.py --input results/final_stats.csv
    ```
    *Output*: `figures/accuracy_vs_epsilon.png`, `figures/sensitivity_alpha.png`.

## Troubleshooting

- **Memory Error**: Reduce `--batch-size` in `main.py`.
- **Timeout**: The script will automatically reduce rounds to 20 and flag as "Time-Limited". Time-limited runs are excluded from convergence speed analysis.
- **Shakespeare Missing**: The script will skip Shakespeare if no verified source is found (current state).
