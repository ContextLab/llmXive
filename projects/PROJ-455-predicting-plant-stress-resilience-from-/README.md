# Predicting Plant Stress Resilience from Publicly Available Metabolomic Data

This project implements a pipeline to predict plant stress resilience using metabolomic data.
It supports data ingestion (synthetic and real), preprocessing, model training (Random Forest, SVM),
and cross-stress validation.

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository and navigate to the project root.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

**Dependencies**:
- `pandas==2.0.3`
- `scikit-learn==1.3.0`
- `numpy==1.24.0`
- `requests==2.31.0`
- `biopython==1.81`
- `pyyaml==6.0.1`
- `pytest==7.4.0`

## Data Generation (Synthetic)

For development and testing, synthetic metabolomic data can be generated.
This data includes embedded ground-truth pathways for validation.

Run the generator script:

```bash
python code/data/generator.py
```

This will produce a Parquet file in `data/raw/synthetic_*.parquet`.

**Note**: For production runs, use the `ExternalDatasetManager` in `code/data/ingest.py` to fetch
real data from NCBI GEO or Zenodo.

## Execution Command

To run the full pipeline (Ingestion -> Preprocessing -> Training -> Validation):

```bash
python code/run_pipeline.py
```

**Configuration**:
- Ensure `data/raw/synthetic_*.parquet` exists if running with synthetic data.
- Adjust adapter settings in `code/data/ingest.py` to switch between `MockAdapter` and `RealAdapter`.

**Output**:
- Processed data: `data/processed/preprocessed_data.parquet`
- Model results: `data/results/model_metrics.json`
- Validation reports: `data/results/validation_report.json`

## Expected Output

Upon successful execution, the following artifacts will be generated:

1. **Preprocessed Data**: A Parquet file containing normalized metabolomic profiles and recovery indices.
2. **Model Metrics**: A JSON file containing R² or Pearson correlation scores for Random Forest and SVM models.
3. **Feature Importance**: Top 20 predictive metabolites listed in the model results.
4. **Validation Report**: Cross-stress generalizability scores and permutation test p-values.

Example `model_metrics.json`:

```json
{
 "model": "RandomForest",
 "metric": "R2",
 "score": 0.85,
 "top_features": ["Metabolite_A", "Metabolite_B",...]
}
```

## Project Structure

```text
.
├── code/
│ ├── data/ # Ingestion, generation, and preprocessing modules
│ ├── models/ # Training and validation logic
│ ├── analysis/ # Pathway analysis and sensitivity checks
│ ├── utils/ # Logging and error handling
│ └── run_pipeline.py # Main entry point
├── data/
│ ├── raw/ # Raw input data (synthetic or downloaded)
│ ├── processed/ # Normalized and imputed data
│ └── results/ # Model outputs and reports
├── contracts/ # Data schemas (YAML)
├── tests/ # Unit, integration, and contract tests
└── README.md
```

## Testing

Run the test suite:

```bash
pytest tests/
```

Specific test groups:
- `tests/unit/`: Unit tests for individual functions.
- `tests/integration/`: End-to-end pipeline tests.
- `tests/contract/`: Schema validation tests.
- `tests/benchmark/`: Performance timing tests.

## License

MIT License