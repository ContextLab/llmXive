# Quickstart Guide: Gut Microbiome & Sleep Architecture Correlation Pipeline

## ⚠️ CRITICAL: REAL-DATA FIRST WORKFLOW

**This pipeline is strictly "Real-Data Only".**
- **NO** synthetic data generation is allowed for production runs.
- **NO** silent fallbacks to mock data will be tolerated.
- **The pipeline will FAIL immediately** if a verified real dataset is not provided.
- Fabricating results or using placeholder data is a violation of the project constitution and will cause the build to fail.

## Prerequisites

1. **Python 3.11+**
2. **Verified Real Dataset**: You must obtain a real dataset (e.g., from NCBI, Zenodo) that contains the required variables.
 - See `data/config/required_variables.yaml` for the exact list of required predictors (taxa) and outcomes (sleep metrics).
 - The dataset file must be placed at `data/raw/real_data.csv` (or the path specified in your config).
3. **Dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Step 1: Prepare Your Data

You **must** provide a real CSV file containing the required variables.
1. Download a verified dataset (e.g., from a peer-reviewed study with a DOI).
2. Ensure the CSV columns match the schema in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml`.
3. Place the file in the project root:
 ```bash
 # Ensure the directory exists
 mkdir -p data/raw
 # Move your verified file here
 cp /path/to/your/verified_dataset.csv data/raw/real_data.csv
 ```

**If `data/raw/real_data.csv` is missing, the pipeline will abort with:**
> `RealDataFetchError: Real data not found. Aborting pipeline. Please provide a verified real dataset.`

## Step 2: Run the Pipeline

Execute the full analysis pipeline:

```bash
python code/main.py --input data/raw/real_data.csv --output data/results/
```

This command will:
1. **Validate** the presence of all required variables.
2. **Verify** the citation/DOI of the dataset (if applicable).
3. **Process** the data (outlier removal, normalization).
4. **Run** correlation analysis (ZINB/Spearman/Pearson selection).
5. **Generate** diagnostics (VIF, Power, Sensitivity).
6. **Output** the final report and artifacts.

### Expected Outputs
After a successful run, the following files will be generated in `data/results/` and `data/processed/`:
- `data/results/correlation_matrix.json`
- `data/results/final_report.md`
- `data/results/power_analysis.json`
- `data/results/vif_report.json`
- `data/processed/filtered_data.parquet`
- `data/results/timing_evidence.json`

## Troubleshooting

### Error: "Real data not found"
Ensure `data/raw/real_data.csv` exists and is not a placeholder. The pipeline does not support synthetic generation for production analysis.

### Error: "Missing required variables"
Check `data/config/required_variables.yaml` to ensure your dataset contains all required columns.

### Error: "Citation Verification Failed"
Ensure the dataset source includes a valid DOI or citation ID that can be cross-referenced.

## Development Mode (Logic Validation Only)

*Note: Synthetic data is ONLY for validating the logic of the pipeline code, NOT for generating research results.*
To test the pipeline logic without real data (for development/debugging only):
```bash
# This generates synthetic data for code validation ONLY
python code/generate_synthetic_data.py --output data/raw/synthetic_data.csv
# Run pipeline on synthetic data (will skip citation checks)
python code/main.py --input data/raw/synthetic_data.csv --output data/results/
```
**WARNING**: Results from synthetic runs are not scientific findings.
