# Quickstart: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

## Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace Hub (for datasets)

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   git clone <repo-url>
   cd projects/PROJ-558-consciousness-bootstrapping-self-aware-a
   ```

2. **Create a virtual environment** and install dependencies.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

3. **Verify dataset access** (optional but recommended).
   ```bash
   python -c "from datasets import load_dataset; load_dataset('openai/gsm8k', 'main', split='test', streaming=True)"
   ```

## Running the Pipeline

The pipeline consists of three stages: Training, Evaluation, and Analysis.

### Step 1: Training
Train both the recursive and baseline models.
```bash
python code/training/train_loop.py --mode all --seeds 0 1 2 3 4
```
- This will download the `arXiv` subset of The Pile (streamed).
- It will train multiple models across several seeds and architectures.
- Checkpoints are saved to `data/checkpoints/`.

### Step 2: Evaluation
Evaluate the trained models on GSM8K and MMLU.
```bash
python code/evaluation/runner.py --checkpoints data/checkpoints/ --benchmarks gsm8k mmlu
```
- This generates `EvaluationResult` JSON files in `data/results/`.
- It handles multiple reasoning paths (5 per question) and calculates metrics.

### Step 3: Analysis
Perform statistical tests and generate the report.
```bash
python code/analysis/stats.py --results data/results/
```
- This produces `data/results/statistical_report.json` with p-values and effect sizes.

## Expected Outputs

- `data/checkpoints/`: Model weights for all seeds and architectures.
- `data/results/eval_results_*.json`: Raw evaluation metrics per seed.
- `data/results/statistical_report.json`: Final statistical analysis.
- `code/`: Source code with `__init__.py` files in all directories.

## Troubleshooting

- **OOM Error**: If training fails with `CUDA out of memory` or `CPU OOM`, the system will attempt to offload to a Kaggle GPU if configured. If not, reduce `batch_size` in `code/training/train_loop.py`.
- **Dataset Errors**: Ensure you have accepted the HuggingFace terms of service for the datasets if required.

## Verification

To verify the installation and data integrity:
```bash
pytest tests/
```
This runs unit tests for metrics and integration tests for the training loop.