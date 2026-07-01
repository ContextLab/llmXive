# Quickstart: Statistical Analysis of Flight Delay Distributions

## Prerequisites
-   Python 3.11+
-   `pip`
-   ~7 GB RAM available

## Installation

1.  **Clone and Setup**:
    ```bash
    cd projects/PROJ-105-statistical-analysis-of-publicly-availab
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `pandas`, `scipy`, `numpy`, `matplotlib`, `seaborn` are installed.

## Running the Analysis

### Full Pipeline
Run the main orchestration script:
```bash
python code/main.py --year 2022 --output data/results/
```
*Note: If the full 2022 dataset is not available via the verified sources, the script will attempt to load the verified sample and report the limitation.*

### Specific Steps

1.  **Data Download & Preprocessing**:
    ```bash
    python code/data_loader.py --year 2022 --save data/raw/
    python code/preprocessing.py --input data/raw/bts_2022.csv --output data/processed/cleaned_delays.csv
    ```

2.  **Model Fitting**:
    ```bash
    python code/models.py --input data/processed/cleaned_delays.csv --output data/results/models.json
    ```

3.  **Diagnostics & Visualization**:
    ```bash
    python code/diagnostics.py --input data/processed/cleaned_delays.csv --models data/results/models.json --output data/results/diagnostics.json
    python code/visualization.py --input data/results/diagnostics.json --output data/results/plots/
    ```

## Expected Outputs
-   `data/results/models.json`: Comparison of AIC/BIC for all 5 distributions.
-   `data/results/diagnostics.json`: Hill estimator results, x_min, R², Vuong test p-value.
-   `data/results/plots/`: Log-log survival plot, QQ-plots, histograms.
-   `data/results/summary_report.json`: Final summary with pass/fail status.

## Troubleshooting
-   **Memory Error**: If `Memory limit exceeded` is raised, ensure no other heavy processes are running. The pipeline is designed to fail gracefully rather than crash.
-   **Convergence Failure**: If fewer than 3 models converge, check `data/results/models.json` for specific failure reasons. This is expected if the data is heavily zero-inflated or has a very light tail.
-   **No Data**: If the dataset is empty, verify the `--year` argument and network connectivity to the BTS endpoint.
