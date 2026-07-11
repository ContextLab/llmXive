# Quickstart: llmXive follow-up: extending "MiniMax Sparse Attention"

## Prerequisites

- Python 3.11+
- 7 GB RAM available
- Internet connection (for dataset download)

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-937-llmxive-follow-up-extending-minimax-spar
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `torch` to CPU-only versions and `transformers`.*

## Running the Experiment

### 1. Data Download
The script will automatically download the RULER dataset to `data/raw/`.
```bash
python code/main.py --action download
```

### 2. Run Heuristics Evaluation
Execute the full benchmark with default settings (Entropy, Gradient, Recency).
```bash
python code/main.py --action run --heuristic all --threshold 0.05
```
*Flags:*
- `--heuristic`: `entropy`, `gradient`, `recency`, or `all`.
- `--threshold`: Selection threshold (default 0.05).
- `--device`: Force `cpu` (default).
- `--baseline`: `dense` (default) or `learned` (reference only).

### 3. Statistical Analysis
Run the Paired t-test (primary) and Wilcoxon (secondary) on the generated results.
```bash
python code/main.py --action analyze
```

### 4. View Results
Output is saved to `results/benchmark_report.json`.
```bash
cat results/benchmark_report.json
```

## Troubleshooting

- **OOM Error**: Reduce `--context-window` or `--batch-size` in `config.py`.
- **CUDA Error**: Ensure `torch` is installed without CUDA support (`pip install torch --index-url https://download.pytorch.org/whl/cpu`).
- **Missing Needle**: Check `logs/experiment.log` for skipped samples.
- **Long-Window Failure**: If the 128k dataset fails, the experiment aborts (do not switch to 4k).