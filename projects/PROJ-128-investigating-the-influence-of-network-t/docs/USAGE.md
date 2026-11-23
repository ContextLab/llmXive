# Usage Guide: Network Topology Pipeline

## Prerequisites
- Python 3.9+
- 16GB+ RAM (recommended for full HCP dataset)
- CPU-only execution (no GPU required)

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration
Edit `code/config.py` to modify:
- `DATA_ROOT`: Path to data storage
- `WINDOW_LENGTH`: Default 30 TR
- `SENSITIVITY_WINDOW`: 20 TR
- `K_MEANS_K`: Number of dynamic states (default 5)
- `DENSITY_THRESHOLD`: Structural network sparsity

## Running the Pipeline

### Step 1: Data Preparation
Ensure the `data/raw/` directory exists. The pipeline will automatically fetch HCP data if missing.
```bash
python code/setup_data_structure.py
```

### Step 2: Main Execution
Run the full batch processing pipeline:
```bash
python code/main.py
```
This will:
1. Load HCP subjects.
2. Compute structural graph metrics.
3. Compute dynamic functional metrics (LOO K-Means).
4. Aggregate results to CSVs.
5. Log exclusions (sparsity, convergence failures).

### Step 3: Correlation Analysis
```bash
python code/analysis/generate_correlation_results.py
```
Output: `data/processed/correlation_results.csv`

### Step 4: Robustness Check
```bash
python code/analysis/robustness.py
```
Output: `data/processed/sensitivity_results.json`

### Step 5: Report Generation
```bash
python code/reports/generate_report.py
```
Output: `data/reports/final_report.json`

## Output Files
- `data/processed/structural_metrics.csv`: Per-subject graph metrics.
- `data/processed/dynamic_metrics.csv`: Per-subject dynamic state metrics.
- `data/processed/correlation_results.csv`: Structure-function correlations with FDR.
- `data/reports/final_report.json`: Comprehensive summary.
- `data/logs/exclusion_log.json`: List of excluded subjects and reasons.

## Troubleshooting
- **Memory Error**: Reduce `WINDOW_LENGTH` or process fewer subjects per batch.
- **Data Fetch Failure**: Verify internet connection and OpenNeuro availability. The loader will fail loudly if data cannot be retrieved.
- **Convergence Failure**: Increase `MAX_ITER` in `config.py` or adjust `DENSITY_THRESHOLD`.

## Validation
Run the quickstart validation script to ensure all outputs are present:
```bash
python code/validate_quickstart.py
```
