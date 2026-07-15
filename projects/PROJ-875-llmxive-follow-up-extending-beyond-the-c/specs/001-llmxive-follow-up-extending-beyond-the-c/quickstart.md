# Quickstart: llmXive follow-up: extending "Beyond the Current Observation: Evaluating Multimodal Large Language M"

## Prerequisites

*   Python 3.11+
*   Git
*   Access to a GitHub Actions runner (or local machine with 7GB+ RAM).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-875-llmxive-follow-up-extending-beyond-the-c
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` includes `transformers`, `bitsandbytes` (CPU mode), `scikit-learn`, `datasets`, `sentence-transformers`, and `pyyaml`.*

## Running the Experiment

### 1. Generate & Validate a Single Instance (Test Renderer)
To verify the ASCII renderer (US-1) and check consistency (SC-005):
```bash
python code/main.py --mode render --seed 42 --steps 10 --verify-consistency
```
*Output*: Prints the ASCII grid and JSON log to stdout. If `--verify-consistency` is set, it performs a Levenshtein comparison against the visual ground truth via `utils/renderer_validator.py` and reports zero information loss.

### 2. Run the Full Experiment (Pilot)
To execute the agent loop and calculate metrics (US-2, US-3):
```bash
python code/main.py --mode full --seeds 42,100,200 --model qwen2-3b --runs 20
```
*Output*:
*   `data/processed/` directory with logs.
*   `results/statistical_summary.json` containing the Mann-Whitney U p-value.
*   Automatic checksumming and hashing of `data/processed/` files.

### 3. Run Power Analysis & Scaling (If Needed)
If the pilot shows high variance, run the scaling step:
```bash
python code/main.py --mode scale --runs 64 --model qwen2-3b
```

### 4. Validate Results
Run the test suite to ensure reproducibility:
```bash
pytest tests/
```

### 5. Verify Artifact Integrity
Run the hasher utility to ensure data hygiene and versioning (Constitution V):
```bash
python utils/hasher.py --verify
```
*Output*: SHA-256 checksums for all files in `data/` and updates to `state/...yaml`.

## Troubleshooting

*   **OOM Error**: Reduce `--model` size (e.g., use a 1B model) or reduce `--runs`.
*   **Context Limit**: The system automatically truncates the event log. Check `data/processed/runs/{id}/truncation_log.txt` for details.
*   **CUDA Error**: Ensure `bitsandbytes` is installed in CPU mode (`bitsandbytes-cpu` package) or use `llama-cpp-python`.
*   **Baseline Adapter Failure**: Check `code/baseline_adapter.py` logs for parsing errors if the Baseline output is unstructured.