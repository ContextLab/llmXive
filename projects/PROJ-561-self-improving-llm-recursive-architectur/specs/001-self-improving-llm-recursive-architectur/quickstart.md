# Quickstart: Self-improving LLM: recursive architecture refinement and re‑training

## Prerequisites

- Python 3.11+
- Sufficient RAM (GitHub Actions free-tier compatible)
- Internet access (for HuggingFace datasets)

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-561-self-improving-llm-recursive-architectur
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to CPU-only version (`--index-url https://download.pytorch.org/whl/cpu`).*

## Running the Pipeline

### 1. Run Single Cycle (Baseline + Cycle 1)
```bash
python code/main.py --cycles 1
```
- Downloads GPT.
- Evaluates baseline.
- Proposes and applies one modification.
- Trains and evaluates.
- Outputs `results/trajectory.json` and `results/logs/cycle_1.log`.

### 2. Run Full 3-Cycle Experiment
```bash
python code/main.py --cycles 3
```
- Executes the recursive loop up to 3 times.
- Handles retries and early termination if degradation > 5%.

### 3. Validate Outputs
```bash
pytest code/tests/
```
- Runs unit tests for config, logging, and external validator.
- Verifies that `results/trajectory.json` matches the `contracts/trajectory.schema.yaml`.

## Configuration

Edit `code/config.py` to adjust:
- `BASE_MODEL_NAME`: "gpt2" (default)
- `TRAINING_SAMPLES`: Number of OpenWebText samples (default: 100000)
- `MAX_PARAM_INCREASE`: 0.30
- `SEED`: 42 (fixed for reproducibility)

## Troubleshooting

- **OOM Error**: Reduce `TRAINING_SAMPLES` in `config.py` or enable gradient checkpointing (already default).
- **HF Rate Limit**: The system implements exponential backoff (initial interval, doubling subsequent intervals...). If it fails, wait 5 minutes and retry.
- **Training Failure**: The system automatically retries up to 2 times. If it persists, the cycle is marked "failed" and the pipeline proceeds.
