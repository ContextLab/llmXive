# Quickstart: llmXive follow-up: extending "EvoPolicyGym: Evaluating Autonomous Policy Evolution in Interactive En"

## Prerequisites

*   Python 3.11+
*   `pip` (or `uv`)
*   Access to the `EvoPolicyGym` base code (assumed to be in `../EvoPolicyGym` or installed via `pip`).

## Installation

1.  **Clone and Setup Environment**:
    ```bash
    cd projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `radon`, `statsmodels`, and `transformers` are installed:
    ```bash
    python -c "import radon, statsmodels, transformers; print('Dependencies OK')"
    ```

## Running the Simulation

### 1. Run a Single Test (Unit Test)
Verify the dynamic shift logic works:
```bash
pytest tests/test_env_shift.py -v
```

### 2. Run the Full Evolutionary Harness
Execute the comparison between Baseline and Counterfactual conditions:
```bash
python main.py --mode full --runs-per-condition 5 --seed 42
```
*   `--runs-per-condition`: Number of evolutionary runs per condition (default 5).
*   `--seed`: Global random seed for reproducibility.

### 3. Run Statistical Analysis
After the simulation completes, run the analysis pipeline:
```bash
python main.py --mode analyze
```
This will:
1.  Parse all policy files for complexity.
2.  Aggregate metrics from logs.
3.  Fit the mixed-effects model.
4.  Output `results/statistical_test_results.json` and `figures/generalization_plot.png`.

## Expected Outputs

*   `data/trajectory_logs/`: CSV files for every run.
*   `data/explanation_logs/`: JSON files with generated feedback.
*   `data/policies/`: Python source code for evolved agents.
*   `results/evolution_summary.csv`: Aggregated metrics.
*   `results/statistical_test_results.json`: P-values and effect sizes.

## Troubleshooting

*   **LLM Timeout**: If the explanation generator times out, the system automatically falls back to a template. Check `explanation_logs/run_<id>.json` for `fallback_used: true`.
*   **Memory Error**: If the simulation runs out of RAM, reduce `--runs-per-condition` or the number of steps per episode in `code/utils/config.py`.
*   **Syntax Error in Policy**: If an evolved policy fails to load, it is logged as a "generation error" and excluded from the complexity analysis.
