# Quickstart: Socratic Transformers

## Prerequisites

*   Python 3.11+
*   Access to a GitHub Actions runner (free-tier) or local machine with ≥7GB RAM.
*   HuggingFace account (optional, for model access).

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `bitsandbytes` is installed with CPU support:
    ```bash
    python -c "import bitsandbytes; print(bitsandbytes.__version__)"
    ```

## Running the Pipeline

### Step 1: Generate Data
Run the data generation script for the Socratic condition.
```bash
python src/data/generate_dialogue.py \
  --dataset gsm8k \
  --condition socratic \
  --seed 42 \
  --threshold 0.05 \
  --output data/generated/dialogue_socratic_seed42.jsonl
```
*Note: This will download GSMK if not present and generate a representative set of samples.*

### Step 2: Train Model
Train the Phi-1.5 model on the generated data.
```bash
python src/train/train_loop.py \
  --data_path data/generated/dialogue_socratic_seed42.jsonl \
  --condition socratic \
  --seed 42 \
  --output_dir models/socratic_seed42 \
  --max_epochs 3
```
*Warning: This may take several hours on a CPU-only runner.*

### Step 3: Evaluate
Evaluate the trained model on GSM8K test.
```bash
python src/eval/benchmark.py \
  --model_path models/socratic_seed42 \
  --benchmark gsm8k_test \
  --output data/results/eval_seed42.jsonl
```

### Step 4: Analyze
Run the statistical analysis (requires results from multiple seeds).
```bash
python src/analyze/stats.py \
  --input_dir data/results \
  --output data/results/aggregated_stats.csv
```

## Validation

To ensure data integrity, run the contract tests:
```bash
pytest tests/contract/
```

## Troubleshooting

*   **OOM Error**: If you encounter `RuntimeError: CUDA out of memory` (unexpected on CPU) or `MemoryError`, check that `bitsandbytes` is loaded with `cpu` flag. Ensure no other processes are using RAM.
*   **Degenerate Dialogue**: If the log shows `DEGENERATE_DIALOGUE_TRUNCATED`, the model is repeating itself. This is expected behavior; the sample is skipped.
*   **Timeout**: If training exceeds 6 hours, reduce `max_epochs` or `batch_size` in `train_loop.py`.
