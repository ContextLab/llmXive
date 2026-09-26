# Predicting Plant Stress Resilience from Publicly Available Metabolomic Data

This project implements an automated science pipeline to predict plant stress resilience using metabolomic data. It supports both synthetic data generation for testing and ingestion of real public datasets (NCBI GEO, Zenodo).

## Project Structure

- `code/`: Source code for data ingestion, preprocessing, modeling, and analysis.
- `data/`: Raw and processed data artifacts.
- `tests/`: Unit, integration, and contract tests.
- `contracts/`: Schema definitions for data validation.
- `state/`: Project state and checksums.

## Prerequisites

- Python 3.11 or higher
- pip

## Installation

1. Clone the repository and navigate to the project root:
 ```bash
 cd projects/PROJ-455-predicting-plant-stress-resilience-from-
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Generation (Synthetic)

For initial testing and development, the pipeline can generate synthetic metabolomic data that mimics real plant stress responses. This data includes embedded biological pathways (proline, ABA, glutathione) and allows configuration of missing data rates to test rejection logic.

To generate synthetic data directly, you can run the generator script:

```bash
python code/data/generator.py --stress_type drought --seed 42 --samples 500
```

However, the recommended way to run the full pipeline is via the main entry point (see below), which handles data generation automatically if no input data is found.

## Execution Command

The entire pipeline is orchestrated via `code/main.py`. It performs the following steps:
1. Generates synthetic data (or loads existing data).
2. Preprocesses data (filtering, normalization, imputation).
3. Trains Random Forest and SVM models.
4. Validates models using Leave-One-Dataset-Out (LODO) and cross-stress evaluation.
5. Writes results to `data/results/model_metrics.json`.

Run the pipeline:

```bash
python code/main.py --seed 42
```

Optional arguments:
- `--seed`: Random seed for reproducibility (default: 42).
- `--stress_type`: Type of stress for synthetic data (default: 'drought').
- `--samples`: Number of samples for synthetic data (default: 500).

## Expected Output

Upon successful execution, the pipeline produces:

1. **Console Output**:
 - Logs showing data generation, preprocessing steps, and model training metrics.
 - A final message: "Pipeline completed successfully".

2. **Data Artifacts**:
 - `data/raw/synthetic_[stress_type]_[seed].parquet`: Generated raw data.
 - `data/processed/mapped_data.parquet`: Preprocessed and KEGG-mapped data.
 - `data/results/model_metrics.json`: Aggregated metrics including R², feature importance, and validation results.

3. **Validation**:
 - The `data/results/model_metrics.json` file will contain keys such as `rf_r2`, `svm_r2`, `top_features`, and `lodo_cv_results`.

## Testing

Run the test suite:

```bash
pytest tests/ -v
```

## License

This project is part of the llmXive automated science pipeline.