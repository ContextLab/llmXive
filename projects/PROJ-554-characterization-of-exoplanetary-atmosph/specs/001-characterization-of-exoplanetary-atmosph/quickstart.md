# Quickstart: Characterization of Exoplanetary Atmospheres through Advanced Spectroscopic Techniques

## 1. Prerequisites

*   **Python**: 3.11 or higher.
*   **System**: Linux environment (or WSL2 on Windows).
*   **Disk Space**: ~2 GB for dependencies and temporary data.
*   **Network**: Access to the NASA Exoplanet Archive API.

## 2. Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This will install `petitRADTRANS` in CPU-only mode. Ensure you do not install `torch` with CUDA support.*

## 3. Configuration

Create a `config.yaml` in the root directory (or use the default `config.default.yaml`):

```yaml
paths:
  raw_data: "data/raw"
  processed_data: "data/processed"
  output: "results"

retrieval:
  mode: "cpu"
  max_iterations: 1000
  convergence_threshold: 1e-4

analysis:
  bootstrap_iterations: 1000
  random_seed: 42
```

## 4. Running the Pipeline

Execute the full pipeline:

```bash
python code/main.py
```

This will:
1.  Download spectra and metadata from the NASA Exoplanet Archive.
2.  Run `petitRADTRANS` retrieval on each spectrum.
3.  Merge data and perform statistical analysis (Akritas-Theil-Sen, Tobit regression).
4.  Generate diagnostic plots and save results.

### Running Individual Stages

*   **Download only**:
    ```bash
    python code/download.py --output data/raw
    ```
*   **Retrieval only** (requires existing raw data):
    ```bash
    python code/retrieval.py --input data/raw --output data/processed
    ```
*   **Analysis only** (requires existing processed data):
    ```bash
    python code/analysis.py --input data/processed/analysis_dataset.csv --output results
    ```

## 5. Verifying Results

1.  Check `data/processed/analysis_dataset.csv` for the merged dataset.
2.  Review `results/statistics.json` for correlation coefficients and regression p-values.
3.  Inspect `results/plots/` for the water abundance vs. temperature scatter plot with error bars/limits.

## 6. Troubleshooting

*   **`petitRADTRANS` convergence failure**: The script will log the failure and attempt to derive an upper limit. Check `logs/retrieval.log` for details.
*   **Missing metallicity**: Planets with missing [Fe/H] will be excluded from the regression but included in the bivariate correlation.
*   **Memory error**: Reduce the `max_iterations` in `config.yaml` or process planets in smaller batches.
*   **Collinearity warning**: If VIF > 5 is detected, the system will automatically switch to Ridge Regression; check `results/statistics.json` for the model type used.