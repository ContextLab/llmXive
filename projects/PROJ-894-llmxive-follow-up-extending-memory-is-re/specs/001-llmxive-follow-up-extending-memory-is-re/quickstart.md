# Quickstart: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Prerequisites

*   Python 3.11+
*   Access to the verified dataset URLs (internet required).
*   Sufficient disk space (for model weights and data).
*   CPU-only environment (no GPU required, but no GPU support).

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-894-llmxive-follow-up-extending-memory-is-re
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    # Ensure llama-cpp-python is installed with CPU support (no CUDA)
    CMAKE_ARGS="-DLLAMA_METAL=off -DLLAMA_CUDA=off" pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `llama-cpp-python` to a version with CPU wheels.*

3.  **Download Model**:
    Place a 4-bit quantized model (e.g., `Phi-3-mini-Q4_K_M.gguf`) in `code/models/`.
    *   *Source*: HuggingFace (e.g., `MaziyarPanahi/Phi-3-mini-4k-instruct-GGUF`).

## Running the Pipeline

### 1. Data Preparation
Downloads LoCoMo and generates synthetic noisy graphs.
```bash
python -m code.data_loader --download --generate-noisy
```

### 2. Run Baseline (Full Strategy)
Executes the "Full" active reconstruction on LoCoMo.
```bash
python -m code.runner --strategy Full --tasks locomo --timeout 1800
```
*Output*: `data/processed/baseline_full_results.csv`

### 3. Run Heuristics (Lazy & Greedy)
```bash
# Lazy Strategy
python -m code.runner --strategy Lazy --threshold 0.7 --tasks locomo --timeout 1800

# Greedy Strategy
python -m code.runner --strategy Greedy --top_k 5 --tasks locomo --timeout 1800
```
*Output*: `data/processed/lazy_results.csv`, `data/processed/greedy_results.csv`

### 4. Robustness Check (Noisy Graphs)
```bash
python -m code.runner --strategy Lazy --tasks noisy_graphs --timeout 1800
```
*Output*: `data/processed/noisy_lazy_results.csv`

### 5. Statistical Analysis
Runs t-tests, correlation analysis, and threshold detection.
```bash
python -m code.stats --input data/processed/ --baseline baseline_full_results.csv
```
*Output*: `data/processed/statistical_report.json`

### 6. Generate Final Report
```bash
python -m code.report --output docs/results_summary.md
```

## Troubleshooting

*   **Timeout Errors**: If a task exceeds a predefined time threshold, it is logged as `TIMEOUT` and the pipeline proceeds. Check `data/processed/logs.txt` for details.
*   **Memory Errors**: If RAM usage exceeds the available system memory, reduce the batch size in `config.py` or use a smaller model.
*   **Graph Construction Failures**: Degenerate graphs (0 edges) are handled gracefully; check `status` column in results CSV.
