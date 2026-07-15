# Quickstart: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

## Prerequisites

-   Python 3.11+
-   Git
-   Docker (optional, for sandbox isolation)
-   Access to GitHub Actions (for CI execution)

## Setup

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `llama-cpp-python` will install CPU-only wheels by default on Linux. Ensure no CUDA flags are set.*

3.  **Download the dataset**:
    ```bash
    python code/data_loader.py --download
    ```
    This script fetches the verified LCB datasets from HuggingFace and saves them to `data/raw/`. It also records checksums.

4.  **Configure the model**:
    -   Download a CPU-quantized GGUF model (e.g., `Llama-2-7B-Chat-GGUF` `q4_0`) and place it in `code/models/`.
    -   Update `code/config.py` with the model path and any hyperparameters (temperature, max tokens).

## Running the Pipeline

The full pipeline (Data Filtering → Blind Runs → Guided Runs → Analysis) can be executed via:

```bash
bash run_pipeline.sh
```

This script will:
1.  Load and filter the dataset (applying the Stochasticity Filter).
2.  Run the Blind condition (multiple times per task) to establish the baseline.
3.  Run the Guided condition (1 time per task) using the Partial Logic Trace.
4.  Execute the generated code in the sandbox.
5.  Categorize errors and perform statistical analysis.
6.  Save all results to `data/results/`.

### Individual Steps (for debugging)

-   **Filter Dataset**:
    ```bash
    python code/orchestrator.py --step filter
    ```
-   **Run Blind Condition**:
    ```bash
    python code/orchestrator.py --step blind --runs 3
    ```
-   **Run Guided Condition**:
    ```bash
    python code/orchestrator.py --step guided
    ```
-   **Analyze Results**:
    ```bash
    python code/statistical_analysis.py
    ```

## Verifying Results

1.  Check `data/results/statistical_report.yaml` for the Pass@1 rates and p-value.
2.  Verify that `data/processed/blind_baseline_metrics.yaml` contains the empirical baseline.
3.  Ensure the total runtime (logged in `data/results/execution_logs.csv`) is ≤ 6 hours.
4.  Run the contract tests to validate data schemas:
    ```bash
    pytest tests/contract/
    ```

## Troubleshooting

-   **Out of Memory**: Reduce the batch size in `code/orchestrator.py` or use a smaller GGUF quantization (e.g., `q3_k_m`).
-   **Timeout Errors**: The timeout per test case is strict. If a task consistently times out, it is logged as a "Runtime Error".
-   **Model Loading Failure**: Ensure `llama-cpp-python` is installed with CPU support (`pip install llama-cpp-python --force-reinstall --no-binary :all:` if needed, though binary wheels are preferred).
