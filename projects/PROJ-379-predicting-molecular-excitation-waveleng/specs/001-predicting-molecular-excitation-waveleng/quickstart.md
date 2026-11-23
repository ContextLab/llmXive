# Quickstart Guide: Predicting Molecular Excitation Wavelengths

This guide provides step-by-step instructions to set up the environment, fetch real data, and run the full molecular excitation wavelength prediction pipeline end-to-end.

## Prerequisites

- Python 3.9+
- pip
- 2 vCPU, 7GB RAM (CPU-only execution required)

## 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
cd projects/PROJ-379-predicting-molecular-excitation-waveleng
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install core dependencies
pip install -r requirements.txt
```

**Note**: If `torch` installation fails on your platform, ensure you use the CPU-only version:
```bash
pip install torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu
```

## 2. Data Fetching

The pipeline fetches real UV-Vis spectral data from **PubChem** or **SDBS** as the primary source. If these fail, it attempts to load from the **Hugging Face** dataset `zjunlp/UV-Vis-ML`.

**No synthetic data is generated.** If real data cannot be fetched, the pipeline will fail loudly with a clear error message.

Run the ingestion script to fetch and process data:

```bash
python code/ingest.py
```

This will:
1. Attempt to fetch data from PubChem/SDBS.
2. Validate the presence of `lambda_max_exp` column.
3. Parse SMILES and validate with RDKit.
4. Save cleaned data to `data/processed/cleaned.csv`.

## 3. Data Splitting

Generate Bemis-Murcko scaffolds and split the data into train/val/test sets:

```bash
python code/split.py
python code/merge_split.py
```

This produces:
- `data/processed/split_indices.json`
- `data/processed/train_val_test.csv`

## 4. Model Training

Train the MPNN GNN model and the ECFP+Ridge baseline:

```bash
python code/train.py
```

This will:
- Use CPU-only execution.
- Apply early stopping if loss plateaus.
- Save the trained model to `model.pt`.
- Log timing to `data/processed/timing.json`.

## 5. Evaluation

Evaluate model performance and compute metrics:

```bash
python code/evaluate.py
```

This will:
- Compute MAE, R², and 95% confidence intervals.
- Perform Wilcoxon signed-rank test against baseline.
- Check power analysis (n ≥ 50).
- Save results to `data/processed/metrics_partial.json` and `data/processed/power_analysis.json`.

## 6. Feature Attribution & Sensitivity Analysis

Run collinearity checks and generate attribution masks:

```bash
python code/collinearity_check.py
python code/explain.py
python code/sensitivity.py
```

This produces:
- `data/processed/redundancy_masks.json`
- `data/processed/raw_attribution.json`
- `data/processed/masked_attribution.json`
- `data/processed/sensitivity_report.csv`
- `figures/sensitivity_plot.png`

## 7. Final Results Aggregation

Aggregate all metrics and results into a single report:

```bash
python code/analyze_results.py
```

This generates `data/processed/metrics.json` containing:
- MAE, R², p-values, confidence intervals.
- SC-001 status (PASS/FAIL).
- Collinearity flags and redundancy masks.
- Power analysis results.
- Attribution results.

## 8. Verify Quickstart

Run the validation script to ensure all artifacts are present and correct:

```bash
python code/run_quickstart_validation.py
```

## Expected Output Artifacts

After running the full pipeline, you should have:

- `data/processed/cleaned.csv`
- `data/processed/split_indices.json`
- `data/processed/train_val_test.csv`
- `model.pt`
- `data/processed/metrics_partial.json`
- `data/processed/power_analysis.json`
- `data/processed/redundancy_masks.json`
- `data/processed/masked_attribution.json`
- `data/processed/sensitivity_report.csv`
- `figures/sensitivity_plot.png`
- `data/processed/metrics.json`

## Troubleshooting

- **Data Fetch Fails**: Ensure internet access and check that PubChem/SDBS are reachable. If using Hugging Face, verify `datasets` package is installed.
- **Memory Errors**: The pipeline uses chunked loading and streaming for large datasets. If issues persist, reduce batch size in `code/ingest.py`.
- **CUDA Errors**: This project is CPU-only. Ensure no GPU code is inadvertently executed.
- **Linter/Formatter Errors**: Run `python code/cleanup_linter.py` to fix formatting and remove unused imports.

## Compliance Notes

- **Real Data Only**: All results are derived from real experimental data. No synthetic or placeholder data is used.
- **Fail Loud**: If any step fails (e.g., data fetch, validation), the pipeline halts immediately with a clear error message.
- **CPU Feasibility**: All operations are optimized to run within 2 vCPU and 7GB RAM constraints.
- **Time Budget**: The full pipeline is designed to complete within 6 hours.