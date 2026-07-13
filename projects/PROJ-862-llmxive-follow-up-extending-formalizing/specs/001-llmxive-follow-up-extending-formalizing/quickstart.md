# Quickstart: llmXive Follow-up: Input Noise Injection for Latent Separability

## Prerequisites

- Python 3.11+
- 8GB RAM (minimum), 16GB recommended for safety.
- Access to HuggingFace Hub (for models and datasets).
- Git.

## 1. Setup Environment

```bash
# Clone the repository
git clone <repo-url>
cd llmxive-follow-up

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Data Preparation

The system automatically downloads verified datasets on first run.

```bash
# Run the data loader to fetch and checksum data
python code/data_loader.py --fetch
```

*Note: This will download BigBench subsets to `data/raw/` and generate `data/checksums.json`.*

## 3. Configuration

Edit `code/config.py` to set:
- `MODEL_NAME`: e.g., `"TinyLlama/TinyLlama-1.1B-Chat-v1.0"`
- `TASK_TYPES`: List of task types to process (e.g., `["causal_judgement", "abstract_narrative_understanding"]`).
- `SIGMA_RANGE`: Tuple `(0.01, 0.20, 0.01)`.
- `BATCH_SIZE`: Integer (start with 1 for safety).
- `SEED`: Integer (e.g., 42).

## 4. Execution

Run the full experiment pipeline:

```bash
python code/main.py
```

**Output**:
- `data/processed/pairs.csv`
- `data/processed/latent_vectors.csv`
- `data/processed/validity_log.csv`
- `data/results/statistical_summary.csv`
- `logs/experiment.log`

## 5. Verification

Run the contract tests to ensure outputs match the schema:

```bash
pytest tests/contract/ -v
```

Run unit tests for noise injection logic:

```bash
pytest tests/unit/ -v
```

## 6. Troubleshooting

- **OOM Error**: Reduce `BATCH_SIZE` in `config.py` or switch to a smaller model.
- **Slow Runtime**: Reduce `SIGMA_RANGE` step size or limit `TASK_TYPES`.
- **No Valid Pairs**: Check `data/processed/validity_log.csv`; if all `is_valid` are False, the noise may be too high or the model too small.
