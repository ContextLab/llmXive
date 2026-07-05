# Quickstart: Assessing the Impact of Data Resolution on Statistical Power

## Prerequisites

-   Python 3.11+
-   `pip` or `poetry`
-   Internet access (for downloading NLCD data)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    cd projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/
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
    *Note: Ensure `pysal`, `rasterio`, and `geopandas` are installed. These are CPU-native.*

## Running the Pipeline

The pipeline is executed via the `main.py` CLI.

### Step 1: Download and Aggregate Data
Download the 30m NLCD data for Colorado and generate coarser resolutions.
```bash
python main.py --action ingest --state CO --output data/derived/
```
*This creates `nlcd_30m_co.tif`, `nlcd_60m_co.tif`, etc.*

### Step 2: Run Analysis
Perform Moran's I tests and power simulations.
```bash
python main.py --action analyze --class-id 41 --permutations 1000 --simulations 1000
```
*`--class-id 41` corresponds to "Deciduous Forest" (example). Adjust as needed.*

### Step 3: Generate Visualization
Plot the power curve and identify the threshold.
```bash
python main.py --action plot --output figures/power_curve.png
```

## Verification

1.  **Check Output Files**:
    -   Verify `data/results/morans_i_results.csv` exists.
    -   Verify `figures/power_curve.png` is generated.
2.  **Check Threshold**:
    -   Inspect the console output or the plot for the resolution where power < 0.80.
    -   Expected output: "Threshold identified at 240m resolution."

## Troubleshooting

-   **Memory Error**: If the runner runs out of RAM, reduce the `--state` area or use a smaller subset.
-   **Timeout**: The 1,000 permutations/simulations are designed to fit within 6 hours. If the job times out, reduce the count to 500 for a pilot run.
-   **Missing Data**: Ensure the HuggingFace URL is accessible. If the primary URL fails, the script will attempt the Parquet fallback.
