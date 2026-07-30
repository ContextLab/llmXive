# Quickstart: Socratic Transformers (PROJ-582)

## 1. Prerequisites

- **Python**: 3.11+
- **System**: Linux (Ubuntu 22.04 recommended) or macOS.
- **Memory**: 8GB+ RAM recommended (7GB minimum for CPU-only run).
- **Disk**: 20GB+ free space.

## 2. Installation

```bash
# Clone the repository
git clone
cd socratic-transformers

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt
```

## 3. Configuration

Set the project root and environment variables:

```bash
export PROJECT_ROOT="projects/PROJ-582-socratic-transformers-dialogue-based-sel"
export PYTHONPATH="$PROJECT_ROOT/code:$PYTHONPATH"
export RANDOM_SEED=42
```

## 4. Running the Pipeline

### Step 1: Download Data
```bash
python -m src.data.download --dataset gsm8k --output data/raw
python -m src.data.download --dataset math --output data/raw
```
*This will verify checksums and store raw data in `data/raw/`.*

### Step 2: Generate Training Data
```bash
# Generate Static Tuples
python -m src.data.static_extractor --input data/raw/gsm8k_train.parquet --output data/processed/static

# Generate Dialogue Tuples (Selection)
python -m src.data.generate_dialogue --input data/raw/gsm8k_train.parquet --output data/processed/dialogue --mode selection

# Generate Ablation Tuples
python -m src.data.ablation --input data/processed/dialogue/gsm8k_dialogue.jsonl --output data/processed/ablation
```

### Step 3: Train Models
```bash
# Train Selection Condition
python -m src.train.train_loop --condition selection --data data/processed/train_splits/selection_train.jsonl --output data/results/selection_model

# Train Ablation Condition
python -m src.train.train_loop --condition ablation --data data/processed/train_splits/ablation_train.jsonl --output data/results/ablation_model

# Train Static Condition
python -m src.train.train_loop --condition static --data data/processed/train_splits/static_train.jsonl --output data/results/static_model
```

### Step 4: Evaluate
```bash
python -m src.utils.metrics --models data/results/ --test-data data/raw/gsm8k_test.parquet --output data/results/metrics.json
```

### Step 5: Analyze Results
```bash
python -m src.utils.stats_analysis --input data/results/metrics.json --output data/results/analysis_report.md
```

## 5. Troubleshooting

- **OOM Error**: If you encounter `CUDA out of memory` or CPU OOM, ensure you are using the 4-bit quantization flag (`--quantize 4bit`). If on CPU, reduce the batch size to 1.
- **Data Download Failure**: Verify network connectivity. The script uses `streaming=True` to avoid large downloads.
- **Quality Gate Failures**: If too many dialogues are discarded, check the `critique_prompt` in `src/data/generate_dialogue.py`.

## 6. Reproducibility

To reproduce the exact results from a previous run:
1. Ensure `RANDOM_SEED=42` is set.
2. Verify `data/raw/` checksums match the `state/` manifest.
3. Run the pipeline in sequence.
