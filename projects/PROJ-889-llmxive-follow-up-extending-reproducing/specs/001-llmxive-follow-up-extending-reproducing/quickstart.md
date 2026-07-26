# Quickstart: llmXive follow-up

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or local environment

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-889-llmxive-follow-up-extending-reproducing
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

3.  **Verify environment**:
    ```bash
    python -c "import pandas, scipy, datasets; print('All imports OK')"
    ```

## Running the Pipeline

### Step 1: Download Data
```bash
python code/download_cherrl_logs.py
```
*Note: This script attempts to load from a verified source (arXiv/HF). If unavailable, it exits with a clear error. No synthetic data is generated.*

### Step 2: Compute Divergence
```bash
python code/compute_divergence.py
```
*Output: `data/processed/divergence_signals.parquet`*

### Step 3: Detect Hacking
```bash
python code/detect_hacking.py
```
*Output: `data/processed/hacking_labels.parquet`*

### Step 4: Evaluate
```bash
python code/evaluate.py
```
*Output: `data/processed/evaluation_report.json`*

### Step 5: Benchmark Runtime
```bash
python code/benchmark_runtime.py
```
*Output: `data/processed/runtime_metrics.json`*

## Running Tests

```bash
pytest tests/ -v
```
*Includes unit tests for edge cases (zero variance, missing timesteps) and integration tests for the full pipeline.*

## Linting & Formatting

```bash
ruff check code/
black --check code/
```

## Troubleshooting

- **Zero Variance**: If $G(t)$ is constant, the z-score is set to 0 (see `utils.py`).
- **Missing Timesteps**: Gaps are skipped/excluded, not interpolated (see `utils.py`).
- **Independence Check Failed**: If $r > 0.8$ between $J_{\text{unbiased}}$ and $J_{\text{gold}}$, the pipeline halts with an error.