# Quickstart: llmXive Follow-up: Reward Fidelity vs. Error Recovery Density

## Prerequisites
- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or a local environment with 7 GB+ RAM.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-1052-llmxive-follow-up-extending-long-horizon
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
    *Note: `llama-cpp-python` will be installed with CPU support. No CUDA drivers required.*

## Running the Pipeline

### 1. Download Dataset
```bash
python code/download.py
```
This downloads the `AgentBench` dataset to `data/raw/` and records the checksum.

### 2. Run Baseline & Experiments
```bash
python code/agent_runner.py --mode full
```
- **Modes**: `baseline`, `binary`, `dense_pruning`, `full` (runs all).
- **Hardware**: Automatically detects available RAM. If 8B model (int4) exceeds 7 GB, it switches to Qwen-1.5-1.8B (int4).

### 3. Run Analysis
```bash
python code/analysis.py
```
This generates `data/processed/analysis_results.csv` and a summary report.

### 4. Verify Results
```bash
pytest tests/
```
Contract tests validate the output schemas.

## Troubleshooting

- **Memory Error**: If running on CPU and hitting 7 GB RAM, the script will automatically switch to the smaller model (Qwen-1.5-1.8B).
- **Missing Variables**: If the dataset lacks required fields, the script exits with `ERR_MISSING_VAR`.
- **Model Loading**: Ensure `llama-cpp-python` is installed with the correct backend (CPU).

## Output Artifacts
- `data/processed/execution_logs.csv`: Raw execution data.
- `data/processed/analysis_results.csv`: Statistical results.
- `results/summary.md`: Human-readable report.