# Predicting Plant Stress Resilience from Publicly Available Metabolomic Data

## Installation

1. Ensure Python 3.11 is installed.
2. Navigate to the project root directory.
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Generation (Synthetic)

The project uses a mechanism-guided synthetic data generator for initial development and testing.
To generate the synthetic dataset:
```bash
python code/main.py --seed 42
```
This will produce `data/raw/synthetic_[stress_type]_[seed].parquet` and subsequent processed files.

## Execution Command

Run the full pipeline (Generation -> Preprocessing -> Training -> Validation):
```bash
python code/main.py
```
Optional arguments:
- `--seed`: Set the random seed for reproducibility (default: 42).
- `--use-real-data`: Attempt to fetch real data from NCBI GEO (requires `--use-real-data` flag and network access).

## Expected Output

Upon successful execution, the following artifacts will be generated generated:
- `data/raw/synthetic_[stress_type]_[seed].parquet`: Raw synthetic metabolomic data.
- `data/processed/mapped_data.parquet`: Data with KEGG IDs mapped.
- `data/results/model_metrics.json`: Performance metrics for trained models (Random Forest, SVM).
- `code/logs/pipeline.log`: Detailed execution logs including validation results.

The pipeline logs will confirm:
- "Pipeline completed successfully"
- KEGG mapping validation status (including any unmapped IDs detected by T049).
- Model performance metrics (R² or Pearson r).

## Validation & Testing

Run unit tests:
```bash
pytest tests/unit/
```
Run integration tests:
```bash
pytest tests/integration/
```

## Project Structure

- `code/`: Source code for the pipeline.
- `data/`: Raw, processed, and result data files.
- `tests/`: Unit, integration, and contract tests.
- `contracts/`: Schema definitions for data models.
- `specs/`: Feature specifications and design documents.