# Quickstart: OPID Critical-First Routing Complexity Analysis

## Prerequisites

-   Python 3.11+
-   `pip` or `conda`
-   Git

## Installation

1.  **Clone the repository** (if not already done):
    ```bash
    git clone <repo-url>
    cd projects/PROJ-970-llmxive-follow-up-extending-opid-on-poli
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` will pin `networkx`, `numpy`, `pandas`, `scipy`, `pytest`.*

## Running the Experiment

### 1. Generate Graphs (Optional Pre-step)
To pre-generate and validate the synthetic environments:
```bash
python code/main.py --mode generate --tiers 1 2 3 --seeds 123 456 789
```
This creates `data/raw/graph_seeds.json` and validates path existence.

### 2. Run the Full Sweep
Execute the full experiment (3 tiers × 11 thresholds × a sufficient number of episodes):
```bash
python code/main.py --mode sweep --output data/processed/episode_results.csv
```
-   **Output**: `data/processed/episode_results.csv` containing all episode data.
-   **Time**: Expected < 6 hours on CPU.

### 3. Analyze Results
Run the statistical analysis and generate summary plots:
```bash
python code/main.py --mode analyze --input data/processed/episode_results.csv --output data/processed/summary_stats.csv
```
-   **Output**: `data/processed/summary_stats.csv` and `data/processed/plots/` (PDF/PNG).
-   **Metrics**: Success rates, entropy variance, quadratic regression fits.

## Verifying Results

1.  **Check Data Integrity**:
    ```bash
    python code/utils/validate.py --data data/processed/episode_results.csv
    ```
    This ensures all episodes are present and thresholds are valid.

2.  **Visualize the Non-Monotonic Curve**:
    Open `data/processed/plots/success_rate_vs_threshold.pdf`.
    -   Look for an inverted U-shape in Tier 1 (Success Rate peaks then declines).
    -   Compare with Tier 2 and Tier 3 (expected to be flatter or monotonic).

## Troubleshooting

-   **"No valid path found"**: The graph generator will automatically retry. If it fails after a sufficient number of attempts, check the `seed` or `tier` parameters.
-   **Memory Error**: Ensure you are running sequentially. The `runner.py` should discard trajectory data after each episode.
-   **Timeout**: If running on GitHub Actions, check the logs. If > 5 hours, consider reducing `n_episodes` to 500 (noted as power limitation).
