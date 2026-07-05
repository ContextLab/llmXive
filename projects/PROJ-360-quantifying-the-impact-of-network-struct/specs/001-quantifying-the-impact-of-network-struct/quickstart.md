# Quickstart: Quantifying the Impact of Network Structure on Heat Diffusion in Crystalline Solids

## Prerequisites

*   Python 3.11+
*   `pymatgen` (requires API key for Materials Project)
*   `networkx`, `pandas`, `scikit-learn`, `numpy`, `statsmodels`
*   Valid `MP_API_KEY` environment variable.

## Installation

1.  **Clone the repository** and navigate to the project root.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
4.  **Set API Key**:
    ```bash
    export MP_API_KEY="your_api_key_here"
    ```

## Execution Steps

### Step 1: Download Data
Run the download script to fetch CIF files and metadata.
```bash
python code/download.py --limit 50 --output data/raw/cif/
```
*Expected Output*: `data/raw/cif/` populated with `.cif` files and `data/metadata.yaml`.

### Step 2: Construct Networks
Process CIFs into network graphs.
```bash
python code/construct_network.py --input data/raw/cif/ --output data/processed/networks/
```
*Expected Output*: Pickle files in `data/processed/networks/` and a log of skipped materials.

### Step 3: Compute Metrics
Calculate graph metrics and aggregate with thermal conductivity and physical descriptors.
```bash
python code/compute_metrics.py --input data/processed/networks/ --output data/processed/metrics.csv
```
*Expected Output*: `data/processed/metrics.csv` (includes volume, mass, atom count).

### Step 4: Analyze & Model
Run correlation, regression, and power analysis.
```bash
python code/analyze.py --input data/processed/metrics.csv --output results/
```
*Expected Output*: `results/correlations.json`, `results/model_performance.json`, `results/power_analysis.log`.

### Step 5: Generate Report
Generate the final report with mandatory limitations text.
```bash
python code/report.py --input results/ --output results/final_report.md
```
*Expected Output*: `results/final_report.md` containing the "Limitations" section.

## Verification

Check the `results/` directory for the expected JSON files and report.
*   `correlations.json`: Should contain 3 entries (degree, path, clustering) with Bonferroni-adjusted p-values.
*   `model_performance.json`: Should contain R² and RMSE from 5-fold CV.
*   `final_report.md`: Must contain the mandatory "Limitations" text block.

## Troubleshooting

*   **API Rate Limit (429)**: The script automatically retries. If it fails, check your API key or wait.
*   **No Bonds Found**: Check `logs/construct_network.log` for materials skipped due to "Disconnected/No Bonds".
*   **Memory Error**: The pipeline is designed for < 7 GB RAM. If OOM occurs, reduce the `--limit` in Step 1.
*   **NaN in Path Length**: If many materials are disconnected, check `results/power_analysis.log` for warnings on reduced sample size.