# Quickstart: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## Prerequisites

- Python 3.11+
- Git
- Access to a terminal with `pip` and `venv` support.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-128-investigating-the-influence-of-network-t
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

The pipeline is executed via a series of scripts in the `code/` directory.

### Step 1: Download Data
```bash
python code/download_data.py
```
- Downloads HCP data from OpenNeuro ds000224.
- Validates checksums and schema.
- Outputs: `data/raw/verified_manifest.json`.

### Step 2: Compute Data Completeness Report
```bash
python code/completeness_report.py
```
- Parses exclusion logs from Phases 0, 1, and 2.
- Generates `data/derived/data_completeness_report.csv`.

### Step 3: Compute Structural Metrics
```bash
python code/structural_metrics.py
```
- Computes graph metrics (efficiency, clustering, modularity).
- Handles sparsity and missing data.
- Outputs: `data/derived/structural_metrics.csv`.

### Step 4: Compute Dynamic Metrics (LOSO)
```bash
python code/dynamic_metrics.py
```
- Extracts dynamic states via LOSO sliding-window and k-means.
- Computes dwell times and visit counts.
- Outputs: `data/derived/dynamic_metrics.csv`.

### Step 5: Correlation Analysis
```bash
python code/correlation_analysis.py
```
- Performs Pearson/Spearman correlations with FDR correction.
- Outputs: `data/derived/correlation_results.csv`.

### Step 6: Sensitivity Analysis
```bash
python code/sensitivity_analysis.py
```
- Re-runs with 20 TR window and ±5% density.
- Outputs: `data/derived/sensitivity_comparison.csv`.

### Step 7: Generate Report
```bash
python code/report_generator.py
```
- Aggregates results and generates `artifacts/final_report.md` and `README.md`.

## Testing

Run unit and integration tests:
```bash
pytest tests/
```

## Troubleshooting

- **Missing Data**: Check `data/derived/data_completeness_report.csv` for excluded subjects and reasons.
- **Convergence Failure**: Check logs in `data/derived/exclusion_log.txt`.
- **Memory Error**: Reduce batch size in `structural_metrics.py` or `dynamic_metrics.py`.
- **Robustness**: Check `data/derived/sensitivity_comparison.csv` for `is_robust` flags.