# Quickstart: Network Topology Energy Transfer

## Prerequisites
*   Python 3.9+
*   `pip`
*   (Optional) `virtualenv` or `conda`

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # or
    .\venv\Scripts\activate   # Windows
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Dependencies include: `networkx`, `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`.*

## Running the Simulation

### 1. Configure Parameters
Edit `code/config.yaml` to set:
*   `topology_classes`: List of classes to generate (e.g., `['er', 'sw', 'sf']`).
*   `graph_count`: Number of graphs per class (default: 35 to reach 100+ total).
*   `node_count`: Number of nodes per graph (default: 500).
*   `simulation_steps`: Time steps (default: 100).
*   `clustering_target`: Target range for SW graphs (e.g., `0.3-0.5`).

### 2. Execute the Pipeline
Run the main orchestration script:
```bash
python code/main.py --config code/config.yaml --output data/
```
This will:
1.  Generate synthetic graphs (saving to `data/raw/`).
2.  Run energy simulations (saving to `data/analysis/`).
3.  Perform statistical regression and ANOVA.
4.  Generate figures in `paper/`.

### 3. Verify Results
Check the `data/analysis/results_summary.json` for:
*   Number of valid graphs generated (Target: ≥100).
*   Diffusion rates and correlation coefficients.
*   P-values (corrected).

## Testing
Run unit tests to verify graph generation and simulation stability:
```bash
pytest code/tests/
```

## Troubleshooting
*   **Simulation Divergence**: If logs show `[SIMULATION_DIVERGENCE]`, check `config.yaml` for energy scaling factors or reduce `simulation_steps`.
*   **Clustering Target Failure**: If many graphs are flagged `[CLUSTERING_DEVIATION]`, adjust the `clustering_target` range in `config.yaml` or increase the retry limit in code.
