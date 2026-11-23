# Quickstart: Social Memory Networks

## Prerequisites

-   Python 3.11+
-   `pip` or `conda`
-   Access to Hugging Face (no token required for public datasets)

## Installation

1.  Clone the repository and navigate to the project directory:
    ```bash
    cd projects/PROJ-586-social-memory-networks-modeling-collecti/code/
    ```

2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

## Running the Experiment

The primary interface is `run_experiment.py`.

### Baseline (Full Context)
Run 200 games with full context and 5 agents:
```bash
python run_experiment.py --context full --agents 5 --dataset hanabi
```
*Output*: `data/derived/results_full.csv`

### Limited Context
Run 200 games with limited context (default 256 tokens) and 5 agents:
```bash
python run_experiment.py --context limited --agents 5 --dataset hanabi
```
*Output*: `data/derived/results_limited.csv`

### Sensitivity Analysis (Token Sweep)
Run the sensitivity analysis across token limits {128, 256, 512}:
```bash
python run_experiment.py --context limited --agents 5 --dataset hanabi --token-sweep
```

### Scaling Analysis
Run the scaling analysis for agent counts 3, 5, 7:
```bash
python run_experiment.py --context full --agents 3,5,7 --dataset hanabi --scaling
```
*Output*: `data/derived/scaling_plot.pdf`

## Verifying Results

1.  **Check CSVs**: Ensure `results_*.csv` contains no missing values.
2.  **Check Bounds**: Verify `specialization_index` is between 0 and log₂(N).
3.  **Check Logs**: Review `experiment.log` for errors (FR-010).

## Troubleshooting

-   **OOM (Out of Memory)**: If the process crashes due to memory, reduce the number of agents or use a smaller model. The system defaults to CPU; ensure you are not accidentally loading a GPU model.
-   **Dataset Error**: If the dataset fails to load, check your internet connection. The system uses streaming for large files.
-   **CUDA Error**: If a CUDA error occurs, the script will attempt to offload to Kaggle (if configured) or fall back to a smaller CPU model.
