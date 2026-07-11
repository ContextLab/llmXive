# Quickstart: llmXive follow-up: extending "MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models"

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local machine with ≤7GB RAM)

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-826-llmxive-follow-up-extending-memlens-benc
    ```

2.  **Create a virtual environment** and install dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Verify CPU availability**:
    Ensure no CUDA is forced. The code will default to CPU.
    ```bash
    python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
    ```

## Running the Pipeline

The pipeline is orchestrated via `code/main.py`.

### Step 1: Download and Filter Data
```bash
python code/main.py --action download
```
*Downloads MemLens, verifies checksum, and filters for MSR/TR tasks.*

### Step 2: Construct Memory Stores
```bash
python code/main.py --action build-stores
```
*Generates Coarse, Medium, and Fine stores. Includes YOLOv8-Tiny detection.*

### Step 3: Run Inference
```bash
python code/main.py --action infer
```
*Runs the frozen LLM on all three stores. Records latency and RAM.*

### Step 4: Evaluate and Test Statistics
```bash
python code/main.py --action evaluate
```
*Calculates accuracy, runs Wilcoxon test, and generates `metrics.json`.*

## Expected Outputs

- `data/processed/memory_stores/`: JSONL files for each strategy.
- `artifacts/results/metrics.json`: Aggregated performance and statistical results.
- `artifacts/logs/`: Detailed logs of YOLO failures, truncations, and OOM attempts.

## Troubleshooting

- **OOM Error**: Reduce `batch_size` in `code/inference.py` to 1. Ensure no GPU processes are running.
- **YOLO Failure**: Check `artifacts/logs/yolo_errors.log`. The system will automatically fallback to global embeddings.
- **Model Load Error**: If 4-bit loading fails on CPU, the system will auto-switch to 16-bit. Check logs for `quantization_fallback`.
