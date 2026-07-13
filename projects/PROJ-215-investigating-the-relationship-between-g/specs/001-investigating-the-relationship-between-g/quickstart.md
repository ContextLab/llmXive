# Quickstart: Investigating the Relationship Between Gut Microbiome Composition and Mental Health in Public Datasets

## Prerequisites

- Python 3.11+
- Git
- Sufficient disk space (for raw data download and processing)
- GB RAM (minimum)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-215-investigating-the-relationship-between-g
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

### 1. Data Feasibility Check
The pipeline starts by checking for a verified, linked dataset.
```bash
python code/data_ingestion.py --check-only
```
*Note: If no linked dataset is found, this script will output "Data Gap: No linked dataset found" and halt.*

### 2. Data Ingestion
If a linked dataset is found, download and merge it.
```bash
python code/data_ingestion.py --output data/processed/merged_clean.parquet
```

### 3. Preprocessing
Apply rarefaction/VST and calculate diversity metrics.
```bash
python code/preprocessing.py --input data/processed/merged_clean.parquet --output data/processed/diversity_metrics.parquet
```

### 4. Statistical Analysis
Run MaAsLin2-style modeling and PERMANOVA.
```bash
python code/analysis.py --input data/processed/diversity_metrics.parquet --output data/results/associations.csv
```

### 5. Visualization & Reporting
Generate plots and the summary report.
```bash
python code/visualization.py --input data/results/associations.csv --output docs/figures/
python code/report.py --input data/results/associations.csv --output docs/report.md
```

## Verification

- Check `data/processed/merged_clean.parquet` for ≥ 100 valid rows (if data available).
- Verify `docs/report.md` lists significant associations (q < 0.05) or a "Data Gap" message.
- Ensure `docs/figures/pcoa_plot.png` and `docs/figures/heatmap.png` are generated (if data available).

## Troubleshooting

- **Data Gap**: If the pipeline halts with "Data Gap", no analysis will be performed. This is expected if no verified linked dataset exists.
- **Memory Error**: If the pipeline fails due to RAM, reduce the sample size in `code/config.py` (set `MAX_SAMPLES = 500`).
- **GAD-7 Missing**: The pipeline will skip GAD-7 analysis if the column is missing, logging a warning.
- **Unit Tests**: To test the pipeline logic without real data, run `pytest tests/unit/` (uses synthetic data).