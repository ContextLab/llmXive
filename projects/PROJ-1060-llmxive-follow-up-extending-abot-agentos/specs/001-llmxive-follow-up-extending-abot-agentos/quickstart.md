# Quickstart: llmXive follow-up: extending "ABot-AgentOS" with Symbolic Memory

## Prerequisites

-   Python 3.11+
-   `pip` package manager
-   Access to the **ALFWorld** dataset (via Hugging Face).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-1060-llmxive-follow-up-extending-abot-agentos
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
    *Note: `requirements.txt` pins versions for `networkx`, `pandas`, `scikit-learn`, `transformers`, `datasets`, `statsmodels`.*

## Data Setup

1.  **Download Data**:
    -   **Primary Source (ALFWorld)**:
        ```bash
        python code/data_loader.py --download --dataset alfworld/alfworld
        ```
    -   **Fallback (Versioned Artifact)**:
        -   If the download fails, the system will attempt to load a versioned, checksummed artifact from `data/raw/alfworld_traces.json`.
        -   **Do not** use ad-hoc user files. The fallback artifact must be generated from a successful download and checksummed.

2.  **Verify Data**:
    ```bash
    python code/data_loader.py --verify
    ```
    *This will check for required columns (dialogue, outcome) and optional columns (spatial_coords, temporal_seq). If spatial coords are missing, it will log a warning and proceed with spatial-only predicates.*

## Running the Experiment

1.  **Run the full pipeline** (Symbolic Construction + Query + Analysis):
    ```bash
    python code/main.py --config config/default.yaml
    ```
    -   This will:
        -   Ingest a representative set of traces from ALFWorld.
        -   Construct the symbolic graph (CPU).
        -   Execute queries.
        -   Run the statistical comparison (Logistic Mixed Effects Model).
        -   Save results to `data/results/`.

2.  **Run with specific parameters** (Sweeping granularity):
    ```bash
    python code/main.py --granularity fine --predicates spatial+temporal
    ```
    *Note: If `spatial_coords` are missing, the `spatial+temporal` condition will be automatically pruned.*

3.  **Run only the baseline comparison** (requires GPU):
    ```bash
    python code/experiment_runner.py --mode baseline-only
    ```
    *Note: This requires the neural baseline code to be present and a GPU environment. The execution stage will auto-offload to Kaggle if needed.*

## Expected Outputs

-   `data/results/metrics.csv`: Aggregated success rates, latency, and memory usage.
-   `data/results/error_analysis.json`: Categorization of failures.
-   `data/results/statistical_report.txt`: Output of the Logistic Mixed Effects Model (fixed effects, p-values).
-   `data/results/run_config.json`: The exact configuration and seeds used for this run.
-   `logs/construction.log`: Detailed logs of graph construction and any warnings (e.g., missing variables).

## Troubleshooting

-   **Error: "No verified data source found"**: Ensure you have run the download command for ALFWorld or placed a versioned, checksummed artifact in `data/raw/`.
-   **Error: "CUDA out of memory"**: The symbolic system is CPU-only. If this error occurs, check if you accidentally invoked the neural baseline on CPU. Use `--mode symbolic-only` to avoid GPU calls.
-   **Warning: "Spatial coordinates missing"**: The system will proceed with spatial-only predicates. This is expected if the dataset lacks fine-grained coordinates. The 'spatial+temporal' condition will be pruned.