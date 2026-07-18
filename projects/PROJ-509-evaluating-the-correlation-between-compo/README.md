# Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

This project investigates the relationship between simple compositional descriptors (mean/variance of elemental properties) and the formation energy of inorganic materials using data from the Materials Project (MP-2020.12.1).

## Project Structure

```
.
├── code/ # Python source code
│ ├── config.py # Configuration and path management
│ ├── ingest.py # Data ingestion and filtering
│ ├── descriptors.py # Descriptor computation and outlier handling
│ ├── train.py # Model training
│ ├── evaluate.py # Model evaluation and metrics
│ ├── importance.py # Feature importance and sensitivity analysis
│ ├── plots.py # Visualization generation
│ ├── run_validation.py # Pipeline orchestration
│ └── utils/ # Utility modules
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ ├── elemental_properties/ # Elemental property data
│ ├── processed/ # Processed datasets
│ ├── evaluation/ # Model outputs and metrics
│ └── logs/ # Execution logs
├── contracts/ # Data schemas
├── tests/ # Test suites
├── requirements.txt # Python dependencies
├── README.md # This file
└── quickstart.md # Quick start guide
```

## Prerequisites

- Python 3.8+
- pip
- Sufficient disk space (~10GB for raw data, ~2GB for processed data)
- Sufficient RAM (8GB+ recommended for full dataset processing)

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 git clone <repository-url>
 cd projects/PROJ-509-evaluating-the-correlation-between-compo
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Quick Start

For a detailed walkthrough, see [quickstart.md](quickstart.md).

To run the full pipeline:

```bash
cd code
python run_validation.py
```

This will execute the following steps in order:
1. **Data Ingestion**: Download and filter the MP-2020.12.1 dataset
2. **Descriptor Computation**: Calculate mean/variance descriptors
3. **Model Training**: Train Random Forest and Gradient Boosting models
4. **Evaluation**: Calculate R², MAE, RMSE, and TVD metrics
5. **Feature Importance**: Extract and rank feature importances
6. **Visualization**: Generate Partial Dependence Plots

## Output Artifacts

After successful execution, the following artifacts will be available:

- `data/processed/sampled_raw_data.csv`: Filtered and sampled raw dataset
- `data/processed/computed_descriptors.csv`: Dataset with computed descriptors
- `data/evaluation/trained_models.pkl`: Serialized trained models
- `data/evaluation/model_metrics.json`: Model performance metrics
- `data/evaluation/feature_ranking.json`: Ranked feature importances
- `data/evaluation/permutation_importance.json`: Permutation importance scores
- `data/evaluation/vif_scores.json`: Variance Inflation Factor scores
- `data/evaluation/pdp_plots/`: Partial Dependence Plot visualizations

## Configuration

Configuration is managed via `code/config.py`. Key paths can be customized by modifying the `load_paths()` function or setting environment variables.

## Testing

Run the test suite:

```bash
cd tests
python -m pytest unit/ -v
python -m pytest contract/ -v
```

## License

This project is for research purposes.
