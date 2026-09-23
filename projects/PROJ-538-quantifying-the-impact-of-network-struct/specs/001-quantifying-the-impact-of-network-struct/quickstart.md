# Quickstart: Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- `git`

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-538-quantifying-the-impact-of-network-struct
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

### 1. Generate Synthetic Data (Default Mode)
Since no real data is available, run the synthetic generator:
```bash
python code/main.py --mode synthetic --n-snapshots 50 --seed 42
```
This creates `data/raw/synthetic_snapshots.parquet` and `data/audit/audit_log.json`.

### 2. Build Graphs & Extract Metrics
```bash
python code/main.py --step build_graphs --step extract_metrics
```
Outputs: `data/processed/graphs.parquet`, `data/processed/metrics.parquet`.

### 3. Perform Statistical Analysis
```bash
python code/main.py --step analyze_correlations
```
Outputs: `data/processed/correlations.json`, `data/processed/power_analysis.json`.

### 4. Generate Visualizations
```bash
python code/main.py --step generate_plots
```
Outputs: `data/processed/scatter_plots.png`, `data/processed/correlation_heatmap.png`.

## Running Tests

```bash
pytest tests/ -v --cov=code --cov-report=html
```

## Verifying Results

1. Check `data/audit/audit_log.json` for data integrity.
2. Verify `data/processed/correlations.json` for Bonferroni-corrected p-values.
3. Inspect `data/processed/correlation_heatmap.png` (should be 300 DPI).
4. Confirm `state/` file is updated with new artifact hashes.