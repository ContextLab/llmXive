# Predicting Crystal Structures from Molecular Fingerprints

**Project ID**: PROJ-030
**Status**: Active Research Pipeline

## Overview

This project implements an automated scientific pipeline to predict crystal structures (Space Groups and Lattice Parameters) from molecular fingerprints (ECFP4). The pipeline ingests data from the Crystallography Open Database (COD), processes CIF files, handles polymorphism, trains machine learning models (Random Forest, Gradient Boosting, Ridge Regression), and performs interpretability analysis using SHAP and permutation importance.

**Key Constraints**:
- **CPU-Only Execution**: All training and inference are restricted to CPU environments (Constitution Principle IV).
- **Real Data Only**: No synthetic data or fallbacks are permitted. The pipeline fails loudly if the real data source is unreachable.
- **Polymorphism Handling**: Distinct (SMILES, Space Group) pairs are treated as unique samples.
- **Scaffold Splitting**: Train/test splits are verified to have zero scaffold overlap.

## Project Structure

```text
.
├── code/
│ ├── ingestion/ # Data loading, parsing, fingerprinting
│ ├── modeling/ # Model training, splitting, evaluation
│ ├── analysis/ # Power analysis, interpretability, reporting
│ ├── utils/ # Utility functions, directory initialization
│ ├── config.py # Path management and configuration
│ ├── exceptions.py # Custom exception definitions
│ ├── logging_config.py# Structured logging setup
│ └── validate_env.py # Environment validation (CPU-only check)
├── data/
│ ├── raw/ # Downloaded raw data (COD subset)
│ ├── processed/ # Intermediate and final processed datasets
│ ├── results/ # Model outputs, metrics, logs
│ ├── validation/ # Validation reports (split checks, etc.)
│ └── models/ # Serialized trained models
├── tests/ # Unit and integration tests
├── specs/ # Feature specifications and design docs
└── README.md
```

## Prerequisites

- Python 3.11+
- HuggingFace Token (`HF_TOKEN`) for dataset access
- Required dependencies (see `code/requirements.txt`)

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
4. Set environment variables:
 ```bash
 export HF_TOKEN="your_huggingface_token_here"
 ```

## Usage

### 1. Initialize Directories

Before running any pipeline steps, initialize the required directory structure:

```bash
python code/utils/init_dirs.py
```

### 2. Validate Environment

Ensure the environment is CPU-only as per project constraints:

```bash
python code/validate_env.py
```

This writes `training_device="cpu"` to `data/results/runtime_config.json`.

### 3. Run the Full Pipeline

Execute the complete ingestion, training, and analysis pipeline:

```bash
python code/ingestion/run_pipeline.py
```

This script orchestrates:
- Streaming the COD organic dataset (`data/raw/`)
- Parsing CIFs and extracting SMILES/lattice parameters
- Generating ECFP4 fingerprints
- Handling polymorphism (distinct SMILES/Space Group pairs)
- Training models and evaluating metrics
- Generating interpretability reports

### 4. Step-by-Step Execution

If you prefer to run steps individually:

**Ingestion**:
```bash
python code/ingestion/load_cod.py --output data/raw/cod_organic_subset.parquet
python code/ingestion/parse_cif.py --input data/raw/cod_organic_subset.parquet --output data/processed/crystal_molecules.parquet
python code/ingestion/fingerprint.py --input data/processed/crystal_molecules.parquet --output data/processed/fingerprinted_dataset.csv
python code/ingestion/dataset_builder.py --input data/processed/fingerprinted_dataset.csv --output data/processed/crystal_dataset.csv
```

**Preprocessing**:
```bash
python code/modeling/group_rare.py --input data/processed/crystal_dataset.csv --output data/processed/grouped_dataset.csv
python code/modeling/split.py --input data/processed/grouped_dataset.csv --output_dir data/processed
python code/modeling/validate_split.py --input data/processed/grouped_dataset.csv --split_indices data/processed/split_indices.json
```

**Training**:
```bash
python code/modeling/train.py --train data/processed/split_indices.json --output data/results
```

**Evaluation & Analysis**:
```bash
python code/modeling/evaluate.py --model_dir data/models --split_indices data/processed/split_indices.json --output data/results/model_metrics.json
python code/analysis/interpret.py --model_path data/models/rf_model.pkl --data data/processed/crystal_dataset.csv --output data/results/feature_importance_report.md
```

## Output Artifacts

The pipeline produces the following key artifacts:

- `data/processed/crystal_dataset.csv`: Final dataset with fingerprints and targets.
- `data/processed/split_indices.json`: Train/test split indices (scaffold-based).
- `data/models/*.pkl`: Trained Random Forest, Gradient Boosting, and Ridge models.
- `data/results/model_metrics.json`: Performance metrics (Accuracy, F1, R², MAE).
- `data/results/feature_importance_report.md`: Interpretability report with substructure mapping.
- `data/validation/scaffold_overlap_report.json`: Verification of zero scaffold overlap.

## Testing

Run unit tests:
```bash
python -m pytest tests/unit/ -v
```

Run integration tests:
```bash
python -m pytest tests/integration/ -v
```

## Configuration

All dynamic configuration (e.g., sample sizes, thresholds) is stored in `data/results/*.json`. Static configuration (paths, seeds) is managed in `code/config.py`. Do not modify `code/config.py` at runtime.

## License

This project is part of the llmXive automated science pipeline. See the main repository for licensing details.