# Quickstart: llmXive follow-up: extending "Trust Region Policy Distillation"

## Prerequisites

*   Python 3.11+ installed.
*   `pip` package manager.
*   (Optional) `git` for cloning the repository.

## Installation

1.  **Navigate to the project directory**:
    ```bash
    cd projects/PROJ-1050-llmxive-follow-up-extending-trust-region/code
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins `numpy`, `scipy`, `pandas`, `matplotlib`, `statsmodels`, and `pytest`.*

## Running the Experiments

### 1. Run a Single Episode (Debug)
To verify the environment and teacher policy:
```bash
python -m experiments.runner --debug --alpha 0.5 --horizon 4 --seed 42
```
*This will print the generated problem, the teacher's path, and the student's trajectory.*

### 2. Run the Full Experimental Grid
To execute the full sweep of $\alpha$ and horizon values (approx. [deferred] episodes):
```bash
python -m experiments.runner --grid
```
*This will:*
1.  Generate 200 episodes for each combination of $\alpha \in \{0.1, 0.3, 0.5, 0.7, 0.9\}$ and horizons.
2.  Save raw logs to `data/raw/`.
3.  Automatically run the **Two-Part Model analysis** (Logistic Regression for collapse + OLS for depth).
4.  Save results to `data/processed/`.

### 3. Reproduce the Analysis
If you have existing raw data and want to re-run the statistical analysis:
```bash
python -m analysis.two_part_model --input data/raw/episodes_*.parquet
```
*This script performs the Logistic Regression on the collapse indicator and the OLS on the uncensored depth subset.*

## Verifying Results

After the grid run completes, check the output in `data/processed/results_*.csv`.
Look for the `collapse_interaction_p_value` column. A value `< 0.05` supports the hypothesis that the interaction between $\alpha$ and horizon significantly impacts the probability of reasoning collapse.

To visualize the collapse rates:
```bash
python -m analysis.plot_results --input data/processed/results_*.csv --output docs/results/collapse_plot.png
```

## Troubleshooting

*   **ImportError**: Ensure you are in the `code/` directory and the virtual environment is active.
*   **Seed Mismatch**: If results differ between runs, check that `--seed` is pinned. The default `main.py` uses a fixed seed for reproducibility.
*   **Memory Issues**: The synthetic environment is lightweight. If memory errors occur, check for infinite loops in the `ReasoningMDP` implementation (unlikely if unit tests pass).
*   **Power Warning**: If the output indicates "Low Power Detected" (interaction p > 0.10), re-run with `--power-increase` to double the episode count per configuration.