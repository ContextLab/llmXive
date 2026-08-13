# Quickstart: llmXive follow-up: extending "Cosmos 3: Omnimodal World Models for Physical AI"

## Prerequisites

- **Python**: 3.11+
- **RAM**: 7 GB+
- **Disk**: 14 GB+ (for dataset and dependencies)
- **GPU**: Not required (CPU-only execution)

## Installation

1. **Clone the repository** and navigate to the project directory:
   ```bash
   cd projects/PROJ-943-llmxive-follow-up-extending-cosmos-3-omn
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

## Running the Pipeline

The pipeline consists of five sequential steps. Run them in order to reproduce the results. **All commands assume execution from the repository root.**

### Step 1: Data Ingestion & Verification
Download the dataset and verify the schema.
```bash
python code/scripts/download_data.py
```
*Output*: `code/data/raw/bridge_subset.jsonl` (or error if dataset not found or schema mismatch).

### Step 2: Data Transformation
Convert continuous actions to symbolic and physics tokens.
```bash
python code/scripts/transform_actions.py \
  --input code/data/raw/bridge_subset.jsonl \
  --output code/data/processed/symbolic_dataset.jsonl \
  --threshold 0.5
```
*Output*: `code/data/processed/symbolic_dataset.jsonl` with `symbolic_label` and `physics_label` fields.

### Step 3: Symbolic Proxy Model Training
Train the DistilBERT model on CPU for the Symbolic Task.
```bash
python code/scripts/train_symbolic.py \
  --data code/data/processed/symbolic_dataset.jsonl \
  --model distilbert-base-uncased \
  --epochs 5 \
  --batch-size 16
```
*Output*: `code/models/symbolic/best_model/` containing the trained model and training logs.

### Step 4: Evaluation & Analysis
Compare performance and analyze errors.
```bash
python code/scripts/evaluate.py \
  --model code/models/symbolic/best_model \
  --data code/data/processed/symbolic_dataset.jsonl \
  --output code/reports/metrics.json

python code/scripts/analyze_errors.py \
  --model code/models/symbolic/best_model \
  --data code/data/processed/symbolic_dataset.jsonl \
  --output code/reports/error_analysis/
```
*Output*: `code/reports/metrics.json` and `code/reports/error_analysis/` containing visualizations and failure mode taxonomy.

## Verification

To verify the pipeline on the free-tier runner:
1. Ensure the total runtime is < 6 hours.
2. Check memory usage with `htop` or similar; it should not exceed 7 GB.
3. Verify that `code/reports/metrics.json` contains a `significant` flag set to `true` (if significant degradation is found).

## Troubleshooting

- **Memory Error**: Reduce `--batch-size` in `train_symbolic.py` or enable `streaming=True` in the data loader.
- **Dataset Not Found**: Ensure the `BRIDGE_DATASET_URL` environment variable is set or the local path is correct. If no verified URL exists, the script will exit with a clear error.
- **Schema Mismatch**: If the dataset lacks `action` or `physics_reward` fields, the script will exit with a specific error. Ensure the correct dataset version is used.
- **Model Not Converging**: Increase `--epochs` or check the learning rate in `train_symbolic.py`.