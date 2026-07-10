# Quickstart: Predicting the Impact of Alloying on High-Temperature Oxidation Resistance

## Prerequisites

- Python 3.11+
- `pip` (or `conda`)
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-277-predicting-oxidation-resistance
    ```

2.  **Install dependencies**:
    ```bash
    cd code
    pip install -r requirements.txt
    ```

3.  **Verify Environment**:
    Ensure no GPU is detected (or that the code runs on CPU):
    ```bash
    python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
    # Expected: CUDA available: False (or True, but code will force CPU)
    ```

## Running the Pipeline

### Mode 1: CI / Production (Restricted)
Runs with a dataset cap of a limited subset size, optimized for speed and reproducibility.
**Note**: If no real data is found, this mode will trigger the Synthetic Fallback and generate a "Data Gap Report".
```bash
cd code
python main.py --mode ci
```
*Output*: `../data/processed/predictions_ci.csv`, `../data/processed/gap_analysis_report.json`, or `../data/processed/data_gap_report.txt`

### Mode 2: Local / Sensitivity Analysis
Runs with up to 1000 rows, allowing for deeper sensitivity analysis.
```bash
cd code
python main.py --mode local
```
*Output*: `../data/processed/predictions_local.csv`, `../data/processed/gap_analysis_report.json`

## Generating Reports

After the pipeline completes, generate the interpretability report:
```bash
python main.py --mode local --task interpret
```
*Output*: `../data/processed/shap_summary_plot.png`, `../data/processed/feature_importance_table.csv`

## Troubleshooting

- **Memory Error**: Ensure you are running in `--mode ci` or have reduced the dataset size in `config.yaml`.
- **Missing Data**: If the pipeline halts with `EXIT_CODE_DATA_VALIDATION_FAILURE`, check `../data/processed/missing_data_report.txt` for excluded rows.
- **No Microstructural Data**: If the gap analysis reports "INCONCLUSIVE", it means fewer than a sufficient number of samples with microstructural annotations were found (or generated). The report will include a calculated power value.
- **Data Gap**: If the pipeline outputs `data_gap_report.txt`, it means no real-world alloy dataset was found. The project is currently in "Pipeline Validation Mode".
