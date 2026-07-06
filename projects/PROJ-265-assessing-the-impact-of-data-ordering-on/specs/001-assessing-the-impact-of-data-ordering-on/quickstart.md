# Quickstart: Assessing the Impact of Data Ordering on Bootstrapping Results

## Prerequisites
- Python 3.11+
- Git
- A GitHub account (for running on Actions)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-265-assessing-the-impact-of-data-ordering-on
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

### 1. Synthetic Data Analysis (US-1, US-2)
Run the full synthetic simulation:
```bash
python code/runner.py --mode synthetic --phi-range 0.0 0.9 --sample-sizes 50 100 200 --trials 1000
```
**Output**: `results/coverage_metrics.csv` containing coverage probabilities and McNemar's test p-values.

### 2. Real-World Analysis
**BLOCKED**: The required UCI Power dataset is not available via a verified source. This phase is skipped.

### 3. Unit Tests
Verify the bootstrap logic and data generation:
```bash
pytest tests/
```

## Output Interpretation
- **coverage_metrics.csv**:
  - `coverage_prob`: Expected to be $\approx 0.95$ for $\phi=0.0$ and $< 0.90$ for $\phi > 0.5$ (ordered).
  - `mcnemar_p_value`: Should be $< 0.05$ (after Bonferroni correction) for significant differences between ordered and shuffled.
  - `mcnemar_statistic`: The test statistic for McNemar's test.
- **simulation_logs.json**: Detailed per-trial data for debugging.

## Troubleshooting
- **Missing Dataset**: If the UCI Power download is attempted, the system will halt with an explicit "Blocked: No verified URL" error.
- **Memory Errors**: Reduce `--trials` or `--sample-sizes` if running on a low-RAM machine.
- **Autocorrelation Estimation**: If `statsmodels` fails to fit AR(1), the segment is skipped (status: `skipped`).