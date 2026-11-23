# Quickstart: Self-improving LLM: recursive architecture refinement and re‑training

## 1. Prerequisites

- Python +
- pip
- Git

## 2. Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-561-self-improving-llm-recursive-architectur
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## 3. Configuration

Edit `code/config.py` if you need to adjust:
- `TRAINING_SAMPLES`: Number of samples to use from OpenWebText (default: [deferred], fallback to 1000 if time-constrained).
- `MAX_CYCLES`: Number of refinement cycles (default: 3).
- `BENCHMARK_SUBSETS`: Size of evaluation subsets (GSM8K: 100, ARC: 100, BoolQ: 1000).

## 4. Running the Pipeline

Execute the main script:
```bash
python code/main.py
```

**What happens**:
1. Downloads and checksums datasets (OpenWebText, GSM8K, ARC, BoolQ).
2. Loads the GPT 124M baseline.
3. Runs up to 3 refinement cycles:
   - Prompts model for modification.
   - Validates with Oracle and Distinctness Checker.
   - Retrains on CPU (with fallback to 1k samples if time-constrained).
   - Evaluates on benchmarks.
   - Logs results.
4. Generates `results/trajectory.json` with performance trends, trade-off metrics, and capacity analysis.

## 5. Verifying Results

Check the output files:
- **Logs**: `results/logs/cycle_1.log`, `results/logs/cycle_2.log`, etc.
- **Trajectory**: `results/trajectory.json` (contains regression slope, R-squared, trend direction, and capacity analysis).
- **Models**: `data/processed/cycle_1_checkpoint.pt` (if successful).

## 6. Troubleshooting

- **OOM Error**: Reduce `TRAINING_SAMPLES` or `BATCH_SIZE` in `config.py`.
- **API Rate Limit**: The script automatically implements exponential backoff (FR-011). If it fails, wait and retry.
- **Modification Rejection**: If the model proposes an invalid change, the script will prompt for a new one automatically.
- **Time Exceeded**: The script will automatically reduce the training subset to [deferred] samples to ensure completion.