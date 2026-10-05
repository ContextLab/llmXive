# Quickstart: Assessing the Validity of Statistical Significance in Randomized Controlled Trials with Missing Data

## Prerequisites

- Python 3.11+
- `pip` or `poetry`
- Access to the internet (to download datasets from OpenML)

## Installation

1. **Clone the repository** (or navigate to the project root).
   ```bash
   cd projects/PROJ-436-assessing-the-validity-of-statistical-si
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` includes `scikit-learn`, `statsmodels`, `scipy`, `pandas`, `numpy`, `seaborn`, `matplotlib`, `requests`, `openml`, and `miceforest`.*

## Running the Simulation

### 1. Download Datasets
The system will automatically download the required OpenML datasets on first run. To force a download or verify integrity:
```bash
python code/main.py --action download
```
*This creates the `data/raw/` directory and stores checksums.*

### 2. Run the Full Simulation
Execute the complete pipeline (download, permute, simulate, analyze, aggregate):
```bash
python code/main.py --action run --dataset openml_42803 --iterations 2000
```
*Flags:*
- `--dataset`: Choose from `openml_42803`, `openml_451`, or `openml_151`.
- `--iterations`: Number of Monte Carlo iterations (default 2000).
- `--mechanism`: Run a specific mechanism (`MCAR`, `MAR`, `MNAR`) or `all`.
- `--rate`: Run a specific missingness rate (e.g., `0.15`) or `all` ([deferred] to [deferred]).

### 3. View Results
Results are saved in `data/processed/`.
- **Error Metrics**: `data/processed/error_metrics.parquet` (raw p-values).
- **Aggregated Results**: `data/processed/comparison_results.json` (Type I error rates).
- **Tipping Points**: `data/processed/tipping_points.csv` (identified thresholds).

### 4. Generate Visualizations
To generate plots (Type I error curves, tipping point flags):
```bash
python code/main.py --action visualize --output figures/
```
*Outputs:*
- `figures/type1_error_by_mechanism.png`
- `figures/tipping_point_analysis.png`
- `figures/method_comparison.png`

## Testing

Run the unit and integration tests:
```bash
pytest tests/ -v
```

## Troubleshooting

- **Memory Error**: If the dataset is too large, reduce the number of iterations or use `--stream` flag (if implemented) to process in chunks.
- **Missing Columns**: If the dataset lacks required columns (e.g., `age`), the system will generate synthetic covariates automatically (per FR-009). Check logs for "Synthetic covariate generated" messages.
- **Dataset Not Found**: Ensure you have internet access and the OpenML IDs are reachable. The system will retry with fallback datasets.