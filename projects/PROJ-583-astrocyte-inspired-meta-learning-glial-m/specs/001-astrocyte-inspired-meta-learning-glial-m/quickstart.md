# Quickstart: Astrocyte-Inspired Meta-Learning

## 1. Prerequisites

-   Python 3.10+
-   pip / venv
-   Git
-   7GB+ free disk space (for datasets and logs)

## 2. Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-583-astrocyte-inspired-meta-learning-glial-m/code/
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This installs CPU-compatible versions of PyTorch and other libraries.*

## 3. Data Preparation

The system automatically downloads **Omniglot** via `torchvision`.
For **Mini-ImageNet**, ensure the dataset is available locally or via a verified HuggingFace mirror.
-   If using Mini-ImageNet, place the `mini_imagenet` folder in `data/raw/`.

## 4. Running the Experiments

### 4.1 Core Training (Omniglot)
Run the baseline MAML and Astrocyte-modulated MAML on Omniglot:
```bash
python train.py --dataset omniglot --model astrocyte --seeds 5 --episodes 100
```
*Output*: Logs in `results/logs/` and summaries in `results/run_summary_*.csv`.

### 4.2 Statistical Evaluation
Compare the results of the Astrocyte model against the Baseline:
```bash
python evaluate.py --baseline results/run_summary_baseline_*.csv --astrocyte results/run_summary_astrocyte_*.csv
```
*Output*: `results/stat_test_*.json` with p-values and significance verdict.

### 4.3 Sensitivity Analysis
Sweep the homeostatic scale parameter:
```bash
python ablation.py --dataset omniglot --scale-params 0.01 0.05 0.1
```

### 4.4 Ablation (Constant Mode)
Disable the dynamic ODE:
```bash
python train.py --dataset omniglot --model astrocyte --ablation-constant
```

## 5. Verification

To verify the installation and data integrity:
```bash
pytest tests/unit/
pytest tests/integration/test_training_loop.py
```
Ensure all tests pass before proceeding to full training runs.

## 6. Troubleshooting

-   **CUDA Error**: Ensure `torch` is installed without CUDA support. Use `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
-   **Memory Error**: Reduce `--batch-size` or use only Omniglot.
-   **Download Failure**: Check network connectivity; the script retries automatically.
