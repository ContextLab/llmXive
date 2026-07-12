# Quickstart: llmXive follow-up: extending "From Chatbot to Digital Colleague"

## Prerequisites

- Python 3.11+
- `pip`
- GitHub Actions runner (or local environment matching runner specs: 2 CPU, <7GB RAM)

## Installation

1.  **Clone and Navigate**:
    ```bash
    cd projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/code
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `sentence-transformers` to a CPU-compatible version and excludes `torch` CUDA variants.*

## Running the Experiment

### Step 1: Generate Synthetic Data & Validation Labels
Generates tasks, skills, and the "human-annotated" labels via the Synthetic Oracle + LLM-as-a-Judge pipeline.
```bash
python main.py --mode generate --seed 42
```
*Output*: `data/raw/tasks.csv`, `data/raw/skills.json`, `data/raw/validation_labels.csv`

### Step 2: Run Execution Sweep
Executes the agent across a range of library sizes (with and without pruning).
```bash
python main.py --mode execute --sizes 10,30,50,100 --pruning --timeout 120
```
*Output*: `data/raw/execution_logs.csv`

### Step 3: Analyze Results
Computes metrics and generates statistical tests (including Piecewise Regression).
```bash
python main.py --mode analyze
```
*Output*: `data/processed/metrics.csv`, `data/processed/plots/`

## Verification

To verify the setup locally before pushing to CI:

```bash
# Run unit tests
pytest tests/unit/

# Run contract tests (schema validation)
pytest tests/contract/

# Run a mini-experiment (10 tasks) to check speed
python main.py --mode execute --sizes 10 --tasks 10 --pruning
```

## Troubleshooting

- **Memory Error**: Ensure no other heavy processes are running. The script should fit in available RAM.
- **Timeout Errors**: If tasks frequently timeout, check the `timeout` parameter. The spec mandates a timeout duration sufficient for the intended operations.
- **CUDA Error**: If `ImportError` regarding CUDA occurs, ensure `torch` was installed without `+cu118` suffix (see `requirements.txt`).
- **Pruning Logic Warning**: The implementation corrects the spec's FR-004 (removing low-similarity skills, not high). If you see warnings about "Spec Logic Mismatch", this is expected and intentional.
- **Judge Model Error**: If the LLM-as-a-Judge fails, ensure the model is compatible with CPU (e.g., use a smaller quantized model or a distilled variant).

## Spec Kickback Note
This implementation assumes the Spec has been updated to reflect:
1.  Corrected Pruning Logic (remove low similarity).
2.  Piecewise Regression for threshold detection.
3.  Synthetic Oracle + LLM-as-a-Judge for "human-annotated" labels.