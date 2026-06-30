# Quickstart: Evaluating the Sensitivity of Common Statistical Tests to Dataset Size

## Prerequisites

- Python 3.11 or higher
- Git
- (Optional) Docker (for containerized execution)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-org/your-repo.git
    cd your-repo
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

## Running the Simulation

### Full Simulation (Recommended)

Run the complete simulation pipeline (generates data, calculates error rates, identifies thresholds, and validates against public datasets).

```bash
python code/main.py
```

This will:
1.  Generate synthetic data for all conditions.
2.  Run a sufficient number of iterations per condition to ensure statistical convergence and robustness of the results.
3.  Calculate Type I and Type II error rates.
4.  Identify reliability thresholds.
5.  Validate against available public datasets (UCI HAR, Shopper).
6.  Generate visualizations in `output/`.

### Custom Simulation

Run a subset of the simulation (e.g., only t-test, n=5..50).

```bash
python code/main.py --test t-test --min-n 5 --max-n 50 --iterations 1000
```

### Validation Only

Run only the validation step against public datasets.

```bash
python code/main.py --mode validation
```

## Output

After completion, the following files will be generated in the `data/` directory:

- `simulation/error_rates.csv`: Empirical error rates and confidence intervals.
- `simulation/thresholds.json`: Identified reliability thresholds.
- `validation/results.csv`: Comparison with real-world data.
- `simulation_metadata.json`: Configuration and seeds.

Visualizations will be saved in `output/`:
- `error_rate_curves.png`: Sample size vs. error rate for all tests.
- `threshold_annotations.png`: Highlighted reliability thresholds.
- `validation_comparison.png`: Simulation vs. real-world data.

## Verification

To verify reproducibility:

1.  **Check seeds**: Ensure `data/simulation_metadata.json` contains the seed used.
2.  **Re-run**: Execute `python code/main.py` again.
3.  **Compare**: The output files should be identical (checksums in project state should match).

## Troubleshooting

- **Memory Error**: Reduce `--iterations` or run in batches.
- **Dataset Not Found**: The validation step may fail if a public dataset is not accessible. Check the logs for specific errors.
- **Timeout**: The full simulation may take up to 6 hours. Ensure the runner has sufficient resources.

## Next Steps

- **Analyze Results**: Review the visualizations and threshold metrics.
- **Extend**: Add new test types or effect sizes.
- **Publish**: Generate the final report and paper.