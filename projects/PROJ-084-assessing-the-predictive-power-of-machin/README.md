# Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes

This project implements an automated pipeline to assess the predictive power of machine learning models (Random Forest, SVM) on organic reaction outcomes using the USPTO dataset.

## Prerequisites

- Python 3.11+
- pip

## Quickstart

### 1. Install Dependencies

Install the required Python packages:

```bash
pip install -r code/requirements.txt
```

### 2. Project Structure

The project follows this directory structure:

```
.
├── code/ # Source code
│ ├── config.py # Configuration and hyperparameter grids
│ ├── preprocessing/ # Data ingestion and feature extraction
│ ├── modeling/ # Model training and evaluation
│ ├── utils/ # I/O and memory utilities
│ └── requirements.txt # Python dependencies
├── data/
│ ├── raw/ # Raw downloaded data (USPTO)
│ ├── processed/ # Cleaned and feature-engineered data
│ └── results/ # Model outputs, reports, and figures
├── tests/ # Test suites
├── specs/ # Feature specifications and contracts
└── README.md # This file
```

### 3. Run the Pipeline

The pipeline is executed in stages. Ensure you have sufficient CPU resources and memory (≤ 7GB RAM).

#### Step 1: Data Ingestion and Preprocessing

Download, sanitize, and generate fingerprints for the USPTO dataset:

```bash
python code/preprocessing/ingest.py
```

This script produces:
- `data/raw/uspto_raw.parquet`
- `data/processed/cleaned_reactions.parquet`
- `data/processed/scaffold_groups.parquet`
- `data/results/data_quality_report.json`

#### Step 2: Data Splitting

Create stratified train/validation/test splits using scaffold grouping to prevent leakage:

```bash
python code/modeling/split.py
```

This script produces:
- `data/processed/split_indices.parquet`
- `data/processed/validation_set.parquet`

#### Step 3: Model Training

Train Random Forest and SVM models with hyperparameter optimization:

```bash
python code/modeling/train.py
```

This script produces:
- `data/results/best_models/` (containing saved model artifacts and hyperparameters)

#### Step 4: Evaluation and Analysis

Evaluate models on the held-out test set and perform feature importance analysis:

```bash
python code/modeling/evaluate.py
```

This script produces:
- `data/results/final_report.json`
- Per-class metrics and feature importance rankings

### 4. Running Tests

Run the test suite to verify correctness:

```bash
cd tests
pytest
```

### 5. Linting and Formatting

Ensure code quality with `ruff` and `black`:

```bash
ruff check code/
black code/
```

## Configuration

Modify `code/config.py` to adjust:
- Random seeds
- File paths
- Hyperparameter grids
- Memory limits

## License

This project is for research purposes.