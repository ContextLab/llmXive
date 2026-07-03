# Quickstart: Self-improving LLM: recursive architecture refinement and re‑training

## Prerequisites

-   Python 3.11+
-   Git
-   GitHub Actions Runner (or local machine with sufficient RAM and CPU cores)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-561-self-improving-llm-recursive-architectur
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `torch` to a CPU-only build to ensure compatibility with constrained RAM resources.*

## Running the Pipeline

### Single Cycle (Debug Mode)

To test the pipeline with a single cycle:

```bash
python code/main.py --cycles 1
```

### Full Experiment (3 Cycles)

To run the full multi-cycle experiment:

```bash
python code/main.py --cycles 3
```

*Note: If real datasets are unavailable, the system will terminate immediately. No synthetic data is permitted.*

### Output

Results are saved to:
-   `results/trajectory.json`: Main performance and resource metrics.
-   `results/logs/`: Detailed logs for each cycle.
-   `data/models/`: Checkpoints for each cycle (if not deleted).

## Troubleshooting

-   **RAM Error**: If you encounter `MemoryError`, try reducing the `batch_size` in `code/config.py` (default value) to a smaller integer (e.g., 2 or 1).
-   **Dataset Load Error**: If the pipeline fails to load a dataset, it will terminate immediately. Check `results/trajectory.json` for the `dataset_status` field.
-   **Timeout**: The default timeout is set to a predefined duration. If the job times out, reduce the number of cycles or the size of the dataset in `code/config.py`.