# Quickstart: llmXive follow-up: extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

## Prerequisites

-   Python 3.11+
-   `pip`
-   Git

## Installation

1.  **Clone the repository** (or navigate to the project root):
    ```bash
    cd projects/PROJ-920-llmxive-follow-up-extending-masking-stal
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
    *Note: `requirements.txt` pins versions to ensure reproducibility on CI.*

## Running the Pipeline

The pipeline consists of three sequential steps. Run them in order.

### Step 1: Generate Synthetic Data
Generates a substantial set of trajectories with controlled semantic density.
```bash
python code/generate_trajectories.py --output data/raw/trajectories.json --seed 42 --count 2000
```
-   **Output**: `data/raw/trajectories.json`
-   **Time**: [deferred]
-   **Check**: Verify file size is < 200 MB.

### Step 2: Run Agent Simulation
Simulates agent performance across retention horizons (1 to T) using the Focus Decay model.
```bash
python code/simulate_agent.py \
  --input data/raw/trajectories.json \
  --output data/processed/simulation_logs.csv \
  --seed 42
```
-   **Output**: `data/processed/simulation_logs.csv`
-   **Time**: [deferred]
-   **Check**: Verify CSV contains columns `trajectory_id`, `retention_horizon`, `success`, `evidence_age`, `decay_factor`.

### Step 3: Statistical Analysis & Visualization
Performs logistic regression and generates the 3D surface plot.
```bash
python code/analyze_results.py \
  --input data/processed/simulation_logs.csv \
  --output-dir output/
```
-   **Output**:
    -   `output/regression_results.json` (coefficients, p-values)
    -   `output/plots/surface_plot.png` (3D surface)
-   **Time**: [deferred]
-   **Check**: Verify `surface_plot.png` exists and is < 5 MB.

## Verification

To ensure the pipeline is working correctly, run the unit tests:
```bash
pytest tests/ -v
```
Expected output:
-   `test_entropy_calculation`: PASSED
-   `test_simulator_logic`: PASSED
-   `test_regression_output`: PASSED

## Troubleshooting

-   **OOM Error**: If you encounter "MemoryError", ensure you are not loading the entire JSON into RAM. The scripts are designed to stream; check if you modified the code.
-   **Plot Generation Failed**: Ensure `matplotlib` and `seaborn` are installed. The plot requires a non-interactive backend for CI; the script sets `Agg` backend automatically.
-   **Regression Convergence Warning**: This may occur if the data is perfectly separable. The increased sample size should mitigate this. If issues persist, reduce the number of spline degrees of freedom in `analyze_results.py`.
