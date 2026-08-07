# Quickstart Guide: EvoPolicyGym Analysis Pipeline

This guide explains how to run the full evolutionary analysis pipeline and generate the required data artifacts.

## Prerequisites

- Python 3.9+
- Installed dependencies (see `requirements.txt`)
- Project root directory

## Installation

```bash
cd projects/PROJ-993-llmxive-follow-up-extending-evopolicygym
pip install -r requirements.txt
```

## Running the Full Pipeline

To execute the full pipeline (Shift Analysis -> Evolution -> Stats -> Final Results), run:

```bash
python code/main.py --run-evolution --seeds 42 --runs 5 --envs GridWorld-0 GridWorld-1 --conditions baseline,counterfactual
```

### Arguments Explained

- `--run-evolution`: Executes the full pipeline.
- `--seeds`: List of random seeds for reproducibility (e.g., `42 123`).
- `--runs`: Number of evolutionary runs per condition (default: 5).
- `--envs`: List of environment IDs to test (e.g., `GridWorld-0`).
- `--conditions`: Comma-separated list of conditions (e.g., `baseline,counterfactual`).

## Running Specific Modules

### Shift Sensitivity Analysis Only

```bash
python code/main.py --run-shift-analysis --seeds 42 --envs GridWorld-0
```
*Output: `data/shift_validation.json`*

### Statistics Analysis Only

```bash
python code/main.py --run-stats
```
*Requires `data/evolution_results.csv` to exist. Output: `data/stats_results.json`*

## Expected Output Artifacts

After a successful run of `--run-evolution`, the following files will be generated in the `data/` directory:

1. **`data/shift_validation.json`**: Results of the dynamic shift validation (p-values, drop rates).
2. **`data/evolution_results.csv`**: Raw metrics from the evolutionary runs (score, complexity, etc.).
3. **`data/stats_results.json`**: Statistical analysis results (mixed-effects model p-value, effect size).
4. **`data/final_results.csv`**: Aggregated summary metrics for the project.

## Troubleshooting

- **Shift Validation Failed**: If `p-value >= 0.05`, the pipeline will abort. This indicates the shift configuration is ineffective. Adjust `shift_step` or environment parameters.
- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Import Errors**: If running directly, ensure `code/` is in your Python path or run from the project root.