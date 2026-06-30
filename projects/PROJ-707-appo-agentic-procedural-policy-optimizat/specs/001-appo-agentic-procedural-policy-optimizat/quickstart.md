# Quickstart: APPO: Agentic Procedural Policy Optimization

## Prerequisites
*   Python 3.11+
*   7GB+ RAM (Free-tier CI compatible)
*   Git

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-707-appo-agentic-procedural-policy-optimizat/code
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    ```bash
    python -c "import torch; import datasets; import scipy; print('OK')"
    ```

## Running the Experiment

### 1. Data Download
Download verified datasets (MATH, Tool-Calling):
```bash
python scripts/download_data.py --benchmarks MATH,ToolCalling
```
*Note: WebShop/HotpotQA are skipped if not in the verified list.*

### 2. Baseline Run (No-Score)
Run 3 seeds of the baseline:
```bash
python training/loop.py --variant No-Score --seeds 1 2 3 --benchmark ToolCalling
```

### 3. Default Run (Score-Default)
Run 3 seeds of the APPO variant:
```bash
python training/loop.py --variant Score-Default --seeds 1 2 3 --benchmark ToolCalling
```

### 4. Ablation Run (Optional)
Run 1 seed for each grid point (12 runs):
```bash
python training/ablation_runner.py --grid --seeds 1
```

### 5. Statistical Analysis
Generate the final report:
```bash
python analysis/stats.py --compare No-Score Score-Default
python analysis/report_gen.py
```

## Output
Results will be located in `results/`:
*   `results/logs/`: Raw training logs.
*   `results/stats/summary.csv`: Aggregated metrics.
*   `results/report.md`: Final human-readable report with p-values, CIs, and effect sizes.

## Troubleshooting
*   **OOM Error**: Reduce `batch_size` in `config/base.yaml` to 1.
*   **Dataset Missing**: Check `data/raw/` for checksums. If missing, re-run `download_data.py`.
*   **Timeout**: The ablation grid is large. Run `ablation_runner.py` with `--seeds 1` for a quick sanity check.