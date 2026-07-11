# Quickstart: llmXive follow-up: extending "MiniMax Sparse Attention"

## Prerequisites

-   **Python**: 3.11+
-   **Hardware**: CPU-only environment (2+ cores, 7+ GB RAM). **No GPU required or allowed.**
-   **Dependencies**: `pip install -r requirements.txt`

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Ensure `llama-cpp-python` is installed with CPU-only backend (no CUDA).*

## Configuration

Set the following environment variables (or edit `config.yaml`):

-   `BLOCK_SIZE`: Default 512.
-   `TOP_K_VALUES`: Default `[10, 20, 30]`.
-   `HEURISTICS`: `["gradient_magnitude", "entropy", "recency_bias"]`.
-   `RULER_DATASET_URL`: `https://huggingface.co/datasets/ruler/ruler`
-   `MODEL_PATH`: Path to MiniMax-M3 GGUF 4-bit model file.

## Running the Benchmark

### 1. Data Download & Preparation
The system automatically downloads and caches the RULER dataset on the first run.
```bash
python code/data/ruler_loader.py --download
```

### 2. Run Full Evaluation (Baseline + Heuristics)
Executes the full RULER suite (N=50 tasks) with all heuristics and the dense baseline.
```bash
python code/main.py --mode full --tasks 50
```
*This command will:*
-   Load the frozen model (GGUF 4-bit).
-   Disable the Index Branch.
-   Run inference with Gradient Magnitude, Entropy, and Recency Bias.
-   Log CPU time and memory usage (separated by component).
-   Save results to `data/processed/results.csv`.

### 3. Run Sensitivity Analysis
Sweeps the Top-k cutoff for the best-performing heuristic.
```bash
python code/main.py --mode sensitivity --heuristic gradient_magnitude --k-values 10,20,30
```

### 4. Run Statistical Analysis
Generates the TOST report and sensitivity curves.
```bash
python code/analysis/stats.py --input data/processed/results.csv
```

## Output

-   `data/processed/results.csv`: Raw evaluation metrics for every task.
-   `data/processed/statistical_summary.json`: Aggregated results, TOST p-values, and equivalence flags.
-   `logs/`: Detailed logs including gradient calculations and memory snapshots.

## Troubleshooting

-   **OOM Error**: Reduce `BLOCK_SIZE` or the number of concurrent tasks. Ensure no GPU processes are running.
-   **GPU Detected**: The script will abort if a GPU is detected. Ensure `CUDA_VISIBLE_DEVICES=""` is set.
-   **Slow Execution**: The gradient calculation is CPU-intensive. If a predefined time threshold is approached, the system will log a warning and may skip remaining tasks.