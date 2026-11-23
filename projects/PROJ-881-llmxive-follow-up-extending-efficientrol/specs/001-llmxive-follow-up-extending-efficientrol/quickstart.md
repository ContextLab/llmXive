# Quickstart: llmXive Follow-up: Entropy-Guided Validity Prediction in RL Rollouts

## Prerequisites

- Python 3.11+
- Git
- Access to Hugging Face Hub (free account)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-881-llmxive-follow-up-extending-efficientrol
   ```

2. **Set up the environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

3. **Run the setup script**:
   ```bash
   bash scripts/setup.sh
   ```
   *Note: `setup.sh` creates all required directories (`code/`, `data/`, `docs/`, `scripts/`, `tests/`, `results/`) and logs them to `project_structure.log`.*

## Execution

### Step 1: Download Datasets
```bash
python code/src/data/download.py --task gsm8k --limit 500
python code/src/data/download.py --task minigrid --limit 500
```

### Step 2: Generate Ground Truth & Labels
```bash
python code/src/generation/generation.py --model Qwen/Qwen1.5-0.5B --task gsm8k --output data/processed/gsm8k_labels.jsonl
python code/src/generation/generation.py --model Qwen/Qwen1.5-0.5B --task minigrid --output data/processed/minigrid_labels.jsonl
```

### Step 3: Extract Entropy Profiles
```bash
# Note: Uses single-sequence streaming to avoid OOM. If --batch-size is provided, it is ignored for entropy extraction.
python code/src/analysis/entropy_calc.py --input data/processed/gsm8k_labels.jsonl --output data/processed/gsm8k_entropy.jsonl
python code/src/analysis/entropy_calc.py --input data/processed/minigrid_labels.jsonl --output data/processed/minigrid_entropy.jsonl
```

### Step 4: Run Analysis
```bash
python code/src/analysis/regression.py --input data/processed/gsm8k_entropy.jsonl data/processed/minigrid_entropy.jsonl --output data/results/regression_results.json
```

### Step 5: Verify Results
```bash
pytest tests/
```

## Troubleshooting

- **Memory Error**: Ensure the model is `Qwen/Qwen1.5-0.5B`. If OOM occurs, the system automatically falls back to single-sequence processing. Do not use 1.5B models with batching.
- **CUDA Error**: This project is CPU-first. If a CUDA error occurs, verify `torch` is installed with CPU support only (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
- **Dataset Download Failure**: Verify internet connection and Hugging Face Hub access. Check `data/raw/` for partial downloads.