# Quickstart: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

## Prerequisites

*   Python 3.11+
*   Git
*   Access to HuggingFace (optional, for private datasets if needed, but public URLs used here)
*   Sufficient disk space (for model weights + dataset + results)

## Setup

1.  **Clone the repository** (or navigate to the project root).
    ```bash
    cd projects/PROJ-869-llmxive-follow-up-extending-multi-lcb-ex
    ```

2.  **Create a virtual environment** and install dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

3.  **Download the dataset** (automated by `code/dataset.py` or manually).
    ```bash
    # The script will download and checksum the parquet files
    python -m code.dataset download
    ```
    *Note: This fetches from verified HuggingFace URLs.*

4.  **Verify the environment**.
    ```bash
    pytest tests/unit/
    ```

## Running the Pipeline

The main pipeline is orchestrated by `code/main.py`.

### Step 1: Dataset Filtering & Stratification
Selects a representative set of tasks meeting the criteria (blind failure, stratification).
```bash
python -m code.dataset filter --output data/processed/filtered_tasks.jsonl
```

### Step 2: Logic Anchor Extraction
Parses Python solutions to extract the initial algorithmic steps.
```bash
python -m code.logic_anchor extract --input data/processed/filtered_tasks.jsonl --output data/processed/anchors.jsonl
```

### Step 3: Inference & Execution (Blind + Guided)
Runs the model (CPU-only) and sandbox. **This may take several hours.**
```bash
# Run Blind Condition
python -m code.main run --condition blind --input data/processed/filtered_tasks.jsonl --output data/results/blind_results.csv

# Run Guided Condition
python -m code.main run --condition guided --input data/processed/filtered_tasks.jsonl --output data/results/guided_results.csv
```
*Note: The script enforces time-based timeouts and handles errors gracefully.*

### Step 4: Statistical Analysis
Computes Pass@1, McNemar's test, and error categorization.
```bash
python -m code.stats analyze --blind data/results/blind_results.csv --guided data/results/guided_results.csv --output data/results/stats.yaml
```

### Step 5: Report Generation
Generates a human-readable summary.
```bash
python -m code.stats report --input data/results/stats.yaml --output docs/report.md
```

## Verification

To verify the pipeline on a small subset of tasks for debugging:
```bash
python -m code.main run --condition guided --input data/processed/filtered_tasks.jsonl --limit 1 --output debug_results.csv
```

## Troubleshooting

*   **OOM (Out of Memory)**: If the model fails to load, reduce `model_size` in `code/config.py` to a 3B parameter model.
*   **Timeouts**: If the sandbox hangs, check `code/sandbox.py` timeout settings.
*   **Dataset Missing**: Ensure `data/raw/` contains the parquet files. Re-run `python -m code.dataset download`.
