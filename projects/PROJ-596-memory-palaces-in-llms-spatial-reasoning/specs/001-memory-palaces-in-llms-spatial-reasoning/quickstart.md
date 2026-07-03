# Quickstart: Memory Palaces in LLMs

## 1. Prerequisites

- Python 3.11+
- Sufficient RAM (recommended for smooth operation, though a lower threshold is the hard limit for the code).
- Internet access (for dataset download).

## 2. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 3. Data Download

The `code/main.py` script will automatically download datasets from verified HuggingFace sources:
- bAbI Task 3
- LAMBADA
- Story Cloze

Datasets are cached in `data/raw/`. Checksums are recorded in `state.yaml`.

## 4. Running the Experiment

```bash
# Run the full pipeline (train, evaluate, report)
python code/main.py

# Optional: Run a single seed for debugging
python code/main.py --seed 0 --dataset babi_task3
```

## 5. Expected Outputs

- `artifacts/results/recall_accuracy.csv`: Accuracy per seed, dataset, and model.
- `artifacts/results/interference_distance.csv`: Interference metrics.
- `artifacts/results/coordinate_variance.csv`: Spatial distribution metrics.
- `artifacts/results/statistical_tests.json`: P-values, CIs, effect sizes, power analysis.
- `logs/training.log`: Detailed training progress and memory usage.

## 6. Troubleshooting

- **OOM Error**: The script automatically reduces batch size to a minimal level. If it still fails, it will subsample the dataset (top [deferred] by length). Check `logs/training.log` for the "Memory Constraint" message.
- **Dataset Missing**: Ensure internet access. The script will retry a limited number of times before failing.
- **Statistical Test Failure**: If normality assumptions are violated, the script switches to Wilcoxon signed-rank test. This is logged.

## 7. Reproducibility

- Random seeds are pinned (-4).
- Datasets are fetched from canonical HuggingFace sources.
- Code is deterministic (no random operations without seeding).
