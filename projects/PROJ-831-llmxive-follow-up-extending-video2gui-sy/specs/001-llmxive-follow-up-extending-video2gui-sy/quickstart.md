# Quickstart: 001-tutorial-bias-analysis

## Prerequisites

- Python 3.11+
- Git
- Sufficient RAM available (for CPU inference)
- GB+ disk space

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-831-llmxive-follow-up-extending-video2gui-sy
    ```

2.  **Create virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to CPU-only version and `llama-cpp-python` for efficient quantization.*

## Running the Benchmark

### Step 1: Generate the Benchmark
Generate a set of synthetic tasks.
```bash
python code/main.py --mode generate --output data/benchmarks/tasks.jsonl
```
*Output: `data/benchmarks/tasks.jsonl` containing a curated set of tasks.*

### Step 2: Run Evaluation
Evaluate all three agents on the benchmark.
*Warning: This step may take up to 6 hours.*
```bash
python code/main.py --mode evaluate --benchmark data/benchmarks/tasks.jsonl --agents baseline,wildgui,hybrid --output data/results/
```
*Output: `data/results/trajectories_baseline.jsonl`, `data/results/trajectories_wildgui.jsonl`, etc.*

### Step 3: Run Analysis
Compute statistics and generate the report.
```bash
python code/main.py --mode analyze --results data/results/ --output data/results/stats.json
```
*Output: `data/results/stats.json` containing McNemar's test results, power analysis, and success rates.*

## Verification

Run the contract tests to ensure data integrity:
```bash
pytest tests/contract/
```

## Troubleshooting

- **OOM Error**: If memory exceeds 7GB, reduce the batch size in `config.py` or use a smaller model (e.g., 3B parameters).
- **Timeout**: If the run exceeds a predefined duration threshold, the script will abort. Check `config.py` for `MAX_STEPS` or `MAX_RUNTIME`.
- **Missing Dataset**: If the proxy dataset fails to load, ensure the verified URLs in `research.md` are accessible.
