# Quickstart: Evaluating Robustness of Statistical Methods to Non-Independence

## Prerequisites

- Python 3.10+
- Git
- 7 GB RAM, 14 GB disk (GitHub Actions Free Tier compatible)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd specs/001-evaluating-the-robustness-of-statistical-methods-to-non-independence
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` includes `numpy`, `pandas`, `scipy`, `statsmodels`, `arch`, `yfinance`, `requests`, `pyyaml`, `matplotlib`, `seaborn`, `pytest`, `xarray`.*

3. **Set random seed** (for reproducibility):
   ```bash
   export PYTHONHASHSEED=42
   ```

## Running the Pipeline

### 1. Ingest and Preprocess Data

```bash
python src/main.py --stage ingestion
python src/main.py --stage preprocessing
```
*This downloads datasets from verified sources, fills missing values, applies ADF (unit root) or DFA (long memory), and computes dependence metrics. **A substantial number of shuffled versions per series are generated here**.*

### 2. Generate Synthetic Data

```bash
python src/main.py --stage synthesis
```
*Generates fGn/ARFIMA series with H ∈ {0.5, 0.7, 0.8, 0.9} and **N ∈ {100, 500, 1k, 5k, 10k}**. Creates shuffled null distributions for each.*

### 3. Run Hypothesis Tests

```bash
python src/main.py --stage hypothesis_testing
```
*Runs a sufficient number of Monte Carlo trials for each configuration to ensure statistical robustness. (one-sample t-test, F-test).*

### 4. Perform Regression Analysis

```bash
python src/main.py --stage regression
```
*Regresses error rates against H and log(N_eff) using a non-linear/GLM model, calculates VIF and N_eff.*

### 5. Generate Visualizations

```bash
python src/main.py --stage viz
```
*Produces ACF plots, scatter plots (error rate vs. H), QQ-plots, and VIF curves.*

## Verification

- **Baseline Validity**: Check `results/error_rate_summary.csv` for H=0.5 synthetic data. Observed error rate should be within a Clopper-Pearson confidence interval of a predefined significance level..
- **Shuffling Validation**: Verify `data/processed/` contains a sufficient number of shuffled files per series to support the research question: [Research Question] using the method: [Method] (Citation)..
- **Unit Tests**:
  ```bash
  pytest tests/unit/
  ```
- **Integration Tests**:
  ```bash
  pytest tests/integration/
  ```

## Output Artifacts

- `data/processed/`: Cleaned time series, metrics, and **[deferred] shuffled null distributions per series**.
- `results/test_results_*.csv`: Individual test outcomes.
- `results/error_rate_summary.csv`: Aggregated error rates and regression parameters.
- `results/plots/`: Generated visualizations (ACF, scatter, QQ-plots, VIF curves).

## Troubleshooting

- **Missing Data**: If a dataset fails to download, check the verified URLs in `research.md`.
- **Memory Error**: Ensure no large datasets are loaded entirely into memory; use streaming if needed.
- **ADF/DFA Failure**: If ADF/DFA fails numerically, the pipeline logs a warning and skips that series.
- **Long Memory Preservation**: Verify that stationary series (ADF p >= 0.05) were NOT differenced (check `stationarity_status.method`).