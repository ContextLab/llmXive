# Quickstart: Exploring the Relationship Between Cosmic Ray Composition and Solar Activity Cycles

## Prerequisites

- Python 3.11+
- `git`
- Access to the GitHub Actions runner (or local environment with similar resources)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd <repo-name>
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

### 1. Data Retrieval & Alignment
```bash
python code/main.py --stage retrieve
```
This step fetches AMS-02 and NOAA data, aligns them, and saves to `data/processed/aligned_data.csv`. **Note:** Gaps are excluded, not interpolated.

### 2. Composition Ratio Calculation
```bash
python code/main.py --stage ratios
```
Computes He/p and Fe/p ratios and saves to `data/processed/ratios.csv`.

### 3. Correlation Analysis
```bash
python code/main.py --stage correlation
```
Performs time-lagged correlation analysis with effective degrees of freedom correction and saves results to `results/correlation_matrix.csv`.

### 4. Bootstrap Resampling
```bash
python code/main.py --stage bootstrap
```
Runs a sufficient number of Moving Block Bootstrap iterations to ensure robust confidence interval estimation and saves the results to `results/bootstrap_ci.json`.

### 5. Model Fitting
```bash
python code/main.py --stage model
```
Fits the rigidity-dependent diffusion model using sliding-window harmonic regression and saves parameters to `results/model_fit.json`.

### 6. Full Pipeline
```bash
python code/main.py --stage all
```
Runs all stages in sequence.

## Output Files

- `data/processed/aligned_data.csv`: Unified time-series dataset.
- `data/processed/ratios.csv`: Composition ratios.
- `results/correlation_matrix.csv`: Correlation coefficients and p-values (with $N_{eff}$ correction).
- `results/bootstrap_ci.json`: Moving Block Bootstrap confidence intervals.
- `results/model_fit.json`: Diffusion model parameters.

## Troubleshooting

- **Data Retrieval Failed**: Check network connectivity and the availability of the AMS-02 and NOAA/SWPC repositories. If the official sources are unreachable, the pipeline will log the error and halt.
- **Memory Error**: The pipeline is designed to run within 7 GB RAM. If memory errors occur, reduce the number of rigidity bins or the bootstrap iterations in `code/utils/config.py`.
- **Zero Flux Events**: These are automatically excluded from ratio calculations. Check `data/processed/ratios.csv` for logged exclusions.
- **Data Granularity Warning**: If the AMS-02 data is not available at daily resolution, the pipeline will log a warning and proceed with the available resolution (e.g., weekly/monthly).