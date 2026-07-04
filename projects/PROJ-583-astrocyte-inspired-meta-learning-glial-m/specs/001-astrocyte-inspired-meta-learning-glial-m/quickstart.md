# Quickstart: Astrocyte-Inspired Meta-Learning

## 1. Prerequisites

- Python 3.10 or higher
- Git
- Access to a Linux environment (or WSL on Windows)
- Internet connection (for dataset downloads)

## 2. Installation

### 2.1 Clone the Repository

```bash
git clone https://github.com/your-org/astrocyte-meta-learning.git
cd astrocyte-meta-learning
```

### 2.2 Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` will include:
- `torch` (CPU version)
- `torchvision`
- `datasets`
- `scipy`
- `scikit-learn`
- `pandas`
- `numpy`
- `pytest`

## 3. Data Preparation

The datasets will be downloaded automatically upon the first run of the training script.

- **Omniglot**: Downloaded via `torchvision`.
- **Mini-ImageNet**: Downloaded via custom loader (canonical split).

No manual download is required. The scripts will handle retries and checksums.

## 4. Running the Experiments

### 4.1 Run a Single Seed (Omniglot)

```bash
python code/main.py --dataset omniglot --seed 42 --mode astrocyte --episodes 100
```

This will:
1. Load Omniglot.
2. Initialize the Astrocyte-MAML model.
3. Run 100 episodes.
4. Log metrics to `results/logs/seed_42_run.jsonl`.

### 4.2 Run the Full Experiment (5 Seeds)

```bash
python code/main.py --dataset omniglot --mode astrocyte --seeds 42 43 44 45 46
```

This will run the training loop for 5 seeds and aggregate the results.

### 4.3 Run the Baseline (Vanilla MAML)

```bash
python code/main.py --dataset omniglot --mode baseline --seeds 42 43 44 45 46
```

### 4.4 Run the Statistical Analysis

After running both baseline and astrocyte modes, run the analysis script:

```bash
python code/main.py --mode analyze --baseline-path results/stats/baseline.csv --astrocyte-path results/stats/astrocyte.csv
```

This will perform a **Permutation Test** (10,000 permutations) and output the result to `results/stats/statistical_test.json`.

### 4.5 Run Ablation Study (Sensitivity Analysis)

```bash
python code/main.py --dataset omniglot --mode astrocyte --sweep-scales 0.01 0.05 0.1 --seeds 42
```

This will run the training loop for each scale parameter and report the variation in stability/plasticity.

## 5. Verifying Results

- Check `results/logs/` for episode logs.
- Check `results/stats/` for aggregated CSVs and statistical test results.
- Ensure that `statistical_test.json` contains a `significant` boolean and a `p_value`.

## 6. Troubleshooting

- **Memory Error**: If you encounter a memory error, reduce the number of episodes or use a subset of Mini-ImageNet (50 classes).
- **Download Failure**: The script will retry 3 times. If it fails, check your internet connection.
- **CUDA Error**: Ensure you are using the CPU version of PyTorch. Do not install `torch` with CUDA support.