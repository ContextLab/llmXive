# Quickstart Guide

This guide walks you through running the Chess Elo Analysis Pipeline from start to finish.

## Prerequisites

- Python 3.8+
- pip

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-283-statistical-analysis-of-publicly-availab
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. (Optional) Set up a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

## Running the Pipeline

The pipeline is orchestrated by `src/main.py`. You can run the entire pipeline or specific stages.

### Full Pipeline Run

To run the entire pipeline (download, process, model, validate, report):

```bash
python src/main.py
```

This will:
1. Download a subset of Lichess games (if `data/raw/selected_ids.txt` exists).
2. Parse the games and extract features.
3. Fit Beta and Ridge regression models.
4. Validate the processed dataset against the schema contract.
5. Generate diagnostic plots and reports.

### Running Specific Stages

You can run individual stages by passing the corresponding flags:

- **Download Stage**:
 ```bash
 python src/main.py --download
 ```

- **Processing Stage**:
 ```bash
 python src/main.py --process
 ```

- **Modeling Stage**:
 ```bash
 python src/main.py --model
 ```

- **Validation Stage**:
 ```bash
 python src/main.py --validate --input data/processed/games.parquet --schema specs/contracts/game_record.schema.yaml
 ```

- **Reporting Stage**:
 ```bash
 python src/main.py --report
 ```

### Manual Stage Execution

Some stages can also be run directly via their respective scripts:

- **Download**:
 ```bash
 python src/data/download.py --sample-size 100 --output data/raw/sample_games.parquet
 ```

- **Validation**:
 ```bash
 python src/validation/validate_contracts.py --data data/processed/games.parquet --contracts specs/contracts/game_record.schema.yaml
 ```

### Expected Outputs

After a successful run, you should see the following files:

- `data/raw/selected_ids.txt`: List of game IDs selected for processing.
- `data/raw/sample_games.parquet`: Downloaded PGN data (if download stage ran).
- `data/processed/games.parquet`: Processed dataset with extracted features.
- `data/results/inclusion_metrics.json`: Metrics on data inclusion rate.
- `data/results/model_metrics.json`: Model coefficients, p-values, R², AIC, etc.
- `data/results/diagnostics.json`: Diagnostic report with validation status and plots.
- `figures/`: Directory containing diagnostic plots (e.g., `predicted_vs_actual.png`, `residuals.png`).

## Troubleshooting

- **URL 401 Error**: If you encounter a 401 error during download, ensure the dataset URL is correct and accessible. The pipeline uses the verified HuggingFace dataset `Lichess/standard-chess-games`.
- **Validation Failure**: If validation fails, check the logs for schema mismatches. Ensure the input data matches the schema defined in `specs/contracts/game_record.schema.yaml`.
- **Missing Files**: If expected output files are missing, ensure all stages were run successfully. Check the logs for errors.

## Next Steps

- Explore the `data/processed/games.parquet` file to analyze the extracted features.
- Review the model metrics in `data/results/model_metrics.json`.
- Examine the diagnostic plots in the `figures/` directory.
- Customize the pipeline by modifying the configuration in `config.yaml` or the source code.