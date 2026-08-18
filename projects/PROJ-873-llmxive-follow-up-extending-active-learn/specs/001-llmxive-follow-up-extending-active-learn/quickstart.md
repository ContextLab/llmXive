# Quickstart: Active Learners as Efficient PRP Rerankers

## Prerequisites
-   Python 3.11+
-   7GB+ RAM available
-   14GB+ Disk space

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-873-llmxive-follow-up-extending-active-learn
    python -m venv venv
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Key dependencies*: `beir`, `datasketch`, `sentence-transformers`, `scikit-learn`, `psutil`, `llama-cpp-python`.

3.  **Verify Environment**:
    ```bash
    python code/utils.py --check-env
    ```

## Running the Pipeline

### Full Execution (5 Seeds)
Run the complete experiment (Data Loading -> Injection -> Clustering -> Ranking -> Stats):
```bash
python code/main.py --seeds 5
```
-   **Output**: Results will be saved in `data/results/`.
-   **Duration**: ~2-4 hours on CPU.
-   **Resource Watchdog**: The script will automatically abort if memory > 7GB or time > 6h.

### Single Seed Debug
To run a single seed for debugging:
```bash
python code/main.py --seeds 1 --seed 42
```

### Step-by-Step Execution
If you need to inspect intermediate artifacts:
1.  **Load & Inject**:
    ```bash
    python code/injection.py --inject --output data/processed/injected_datasets.json
    ```
2.  **Cluster**:
    ```bash
    python code/cluster_engine.py --input data/processed/injected_datasets.json --output data/processed/clusters.json
    ```
3.  **Rank & Measure**:
    ```bash
    python code/ranker.py --input data/processed/injected_datasets.json --output data/results/wasted_calls.json
    ```

## Verifying Results
Check the statistical report:
```bash
cat data/results/statistical_report.md
```
Verify the Wilcoxon test:
```bash
cat data/results/wilcoxon_wasted_calls.json
```

## Troubleshooting
-   **Memory Error**: Reduce `batch_size` in `code/config.py`.
-   **Timeout**: Ensure the runner has sufficient CPU; the 6h limit is strict.
-   **Dataset Download**: If `beir` fails to download, check internet connectivity or use the manual download URLs in `research.md`.