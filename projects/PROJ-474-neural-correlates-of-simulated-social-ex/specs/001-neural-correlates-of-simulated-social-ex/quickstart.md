# Quickstart: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or local environment with 7GB+ RAM.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-474-neural-correlates-of-simulated-social-ex
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
   *Note: `requirements.txt` pins versions to ensure reproducibility on CPU-only runners.*

## Running the Pipeline

### 1. Data Ingestion & QC
Download and validate data, excluding subjects with >3mm motion.
```bash
python src/main.py --step download_qc
```
- **Output**: `data/derived/qc_report.json`
- **Check**: Ensure `N_valid >= 10`. If not, the process halts.

### 2. ROI Extraction & Connectivity
Extract time-series and compute connectivity matrices.
```bash
python src/main.py --step extract_connectivity
```
- **Output**: `data/derived/connectivity_matrices.pkl`

### 3. Statistical Analysis
Run permutation test and generate visualizations.
```bash
python src/main.py --step stats_viz
```
- **Output**: `data/derived/results.json`, `figures/null_distribution.png`, `figures/condition_comparison.png`

### 4. Generate Report
Compile findings into a markdown report.
```bash
python src/main.py --step report
```

## Validation

- **Unit Tests**:
  ```bash
  pytest tests/unit/ -v
  ```
- **Integration Tests**:
  ```bash
  pytest tests/integration/ -v
  ```
- **Contract Tests**:
  ```bash
  pytest tests/contract/ -v
  ```

## Troubleshooting

- **Error: `ERR_N_INSUFFICIENT`**: The dataset has fewer than 10 valid subjects after motion QC. The pipeline cannot proceed.
- **Error: `ERR_DATA_UNAVAILABLE`**: The OpenNeuro dataset is missing or the event markers are incomplete.
- **Memory Error**: Reduce the batch size in `config.py` or ensure no other heavy processes are running.
