# Quickstart Guide: Predicting Insect Pollinator Networks

This guide provides instructions to run the full analysis pipeline for predicting insect pollinator networks from floral trait data.

## Prerequisites

- Python 3.11 or higher
- `pip` package manager
- Internet connection (for downloading Web of Life dataset)

## Installation

1. Clone the repository and navigate to the project root:
 ```bash
 cd PROJ-270-predicting-insect-pollinator-networks-fr
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. (Optional) Set up a virtual environment first:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The main orchestrator script runs the data ingestion, preprocessing, model training, validation, and reporting steps sequentially.

### Full Pipeline Execution

Run the main script from the project root:

```bash
python code/main.py
```

This command will:
1. **Setup Directories**: Ensure `data/raw/`, `data/processed/`, `results/`, and `logs/` exist.
2. **Ingest Data**: Download interaction matrices and trait metadata from the Web of Life database.
3. **Preprocess**: Generate negative samples, impute missing values, normalize features, and assemble the final feature matrix.
4. **Train Model**: Train a Random Forest classifier with stratified k-fold cross-validation.
5. **Validate**: Perform Leave-One-Ecosystem-Out (LOEO) cross-validation and compare against null models.
6. **Report**: Generate `results/report.md`, `results/metrics.json`, and visualization plots.

### Expected Outputs

After successful execution, the following artifacts will be generated:

- `data/processed/feature_matrix.csv`: The unified feature matrix.
- `data/processed/model.pkl`: The trained Random Forest model.
- `results/metrics.json`: Aggregated performance metrics (AUC, precision, recall, trait gap).
- `results/report.md`: A detailed markdown report of the analysis.
- `results/plots/*.png`: Visualization of network discrepancies, PR curves, and ROC curves.
- `logs/main_pipeline.log`: Detailed execution logs.

## Troubleshooting

- **Missing Dependencies**: Ensure all packages in `code/requirements.txt` are installed.
- **Data Download Failures**: The pipeline skips ecosystems if data is unavailable. Check `logs/main_pipeline.log` for warnings.
- **Memory Issues**: If the pipeline fails due to memory constraints, ensure your system has at least 8GB RAM. The code includes streaming logic for large datasets, but may require tuning for very constrained environments.

## Next Steps

- Review `results/report.md` for the final analysis summary.
- Inspect `results/metrics.json` for quantitative metrics.
- Modify `code/config.py` to adjust random seeds or hyperparameters if needed.