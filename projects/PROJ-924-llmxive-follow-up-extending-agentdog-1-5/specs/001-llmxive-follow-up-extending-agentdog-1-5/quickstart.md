# Quickstart: Zero-Shot Drift Detection

## Prerequisites

- Python 3.11+
- Git
- Access to Hugging Face (free account)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

4. **Verify configuration**:
   ```bash
   pytest tests/unit/test_config.py
   pytest tests/unit/test_ruff.py
   ```

## Running the Pipeline

### Step 1: Data Loading
Download the dataset (streaming enabled):
```bash
python code/data_loader.py --download
```

### Step 2: Centroid Generation
Generate safety category centroids:
```bash
python code/embeddings.py --generate-centroids
```

### Step 3: Drift Scoring
Compute drift scores for all logs:
```bash
python code/embeddings.py --score
```

### Step 4: Baseline Comparison (CPU)
Run the Flan-T5 baseline:
```bash
python code/baseline_llm.py --baseline
```

### Step 5: Statistical Validation
Run validation metrics (requires human data if available):
```bash
python code/validation.py --validate
```

## Configuration

Edit `code/config.py` to adjust parameters:
- `RANDOM_SEED = 42`
- `MAX_RAM_GB = 7`
- `BATCH_SIZE = 64`
- `DRIFT_THRESHOLD = 1.5`

**Note**: The `config.py` file must contain these exact constants. If missing, the pipeline will fail.

```python
# code/config.py
import os

RANDOM_SEED = 42
MAX_RAM_GB = 7
BATCH_SIZE = 64
DRIFT_THRESHOLD = 1.5
```

## Troubleshooting

- **Memory Error**: Ensure `BATCH_SIZE` is set to 64 and data is streamed. If OOM occurs, reduce `BATCH_SIZE` to 32 or 16.
- **Model Not Found**: Verify Hugging Face login (`huggingface-cli login`).
- **Validation Failed**: Ensure `data/human_annotations.json` exists and is formatted correctly.
