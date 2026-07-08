# Quickstart: Assessing the Generalizability of Statistical Significance in Pre-Registered Studies

## Prerequisites
- Python 3.11+
- Git
- Access to GitHub Actions (or local environment with 2+ CPU cores, 8GB RAM)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-065-assessing-the-generalizability-of-statis
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

## Data Setup

The system automatically generates synthetic data or downloads verified datasets on the first run.
1. Ensure network access (optional for OSF download, required for HuggingFace if fallback used).
2. Run the ingestion script to fetch/generate data:
   ```bash
   python code/ingestion.py --fetch-verified
   ```
   *Note: This script will first attempt to load real data from OSF. If unavailable, it will generate synthetic data matching the target study properties and save it to `data/raw/`.*

## Running the Analysis

### 1. Full Pipeline
Run the entire pipeline (Ingestion -> Bootstrap -> Meta-Analysis):
```bash
python code/main.py
```
*This will take a moderate amount of time for a subset of studies on a standard CPU. For the full 50 studies, the adaptive runtime engine will ensure completion within 6 hours by reducing iterations or sample size if necessary.*

### 2. Single Study Debug
To test the bootstrap engine on a single study:
```bash
python code/bootstrap_engine.py --study-id <osf_id> --iterations 100
```

### 3. Generate Report
If data is already processed, generate the visual report:
```bash
python code/meta_analysis.py --generate-report
```

## Expected Outputs

- `data/processed/baseline_metrics.csv`: Stability rates for all studies.
- `outputs/figures/forest_plot.png`: Visual comparison of stability rates.
- `outputs/reports/summary_report.pdf`: Full analysis report.

## Troubleshooting

- **Memory Error**: Reduce `--iterations` in `config.py` to a lower, optimized setting.
- **Missing Data**: Check `logs/ingestion.log` for "missing_raw_data" entries. If real data is missing, the system will automatically generate synthetic data.
- **Zero Variance**: If a study has a binary predictor with 0 variance, it will be skipped and logged.
- **Runtime Warning**: If the job is running long, the system will automatically reduce iterations to 500 for remaining studies to ensure completion within 6 hours.