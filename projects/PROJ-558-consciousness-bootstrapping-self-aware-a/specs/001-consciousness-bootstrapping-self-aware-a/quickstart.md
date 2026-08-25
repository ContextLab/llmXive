# Quickstart: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

## 1. Prerequisites

- Python 3.11+
- Git
- Sufficient RAM available (for CPU run)
- Internet connection (for dataset streaming)

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-558-consciousness-bootstrapping-self-aware-a

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 3. Running the Experiment

### Step 1: Train Models
Run the training script. This will train both the recursive and baseline models on a large-scale corpus.
```bash
python code/training/train.py --seeds 42 123 456 789 101 --epochs 1 --tokens 100000
```
*Note: This may take up to 4 hours on CPU. If it fails, the system will attempt to offload to Kaggle.*

### Step 2: Evaluate Models
Run the evaluation script on GSM8K and MMLU.
```bash
python code/evaluation/benchmarks.py --seeds 42 123 456 789 101 --dataset gsm8k,mmlu
```
*Note: This script saves both 'first pass' and 'recursive refinement' outputs for T043.*

### Step 3: Statistical Analysis
Run the analysis script to generate the report.
```bash
python code/analysis/stats.py --input-dir artifacts/reports --output artifacts/reports/statistical_report.yaml
```

## 4. Verifying Results

Check the generated `statistical_report.yaml` for p-values and effect sizes.
```bash
cat artifacts/reports/statistical_report.yaml
```

## 5. Troubleshooting

- **OOM Error**: Reduce `--tokens` to 50000 or `--batch-size` to 2.
- **Dataset Download Failure**: Check internet connection; ensure HF token is set if required (not required for public datasets).
- **CUDA Error on CPU**: Ensure `torch` is installed without CUDA support or set `CUDA_VISIBLE_DEVICES=""`.