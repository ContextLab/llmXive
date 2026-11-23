# PROJ-412: Predicting Molecular Surface Area from Graph Convolutional Networks

## Project Overview

This project implements an automated scientific pipeline to predict the Solvent Accessible Surface Area (SASA) of molecules using Graph Convolutional Networks (GCNs). The pipeline ingests SMILES strings from the ZINC15 dataset, generates 2D graph representations, constructs 3D conformers, calculates ground-truth SASA values, and trains machine learning models to predict surface area from molecular structure.

The system is designed for reproducibility, robustness, and strict adherence to real-data processing principles, ensuring that all results are derived from actual experimental or computational data sources without synthetic fallbacks.

## Functional Requirements Traceability

This project implements the following functional requirements (FRs):

- **FR-001: Data Ingestion**
 The system ingests SMILES strings from the ZINC15 dataset using streaming to handle large-scale data efficiently. Invalid SMILES and molecules exceeding the atom count threshold (>100 atoms) are filtered and logged.

- **FR-002: Graph Construction**
 Molecules are converted into graph representations with node features (atom type, hybridization, formal charge) and edge features (bond type, conjugation, aromaticity) using RDKit.

- **FR-003: 3D Conformer Generation & SASA Calculation**
 The system generates 3D conformers using the ETKDG method and calculates SASA values using RDKit's surface area algorithms. Conformer generation failures are logged with specific error codes.

- **FR-004: Baseline Comparison**
 The pipeline trains and compares a GCN model against two baselines: a 2D descriptor-based linear regression and a geometry-based (3D descriptors) linear regression.

- **FR-005: Statistical Significance Testing**
 The system performs paired t-tests and calculates effect sizes (Cohen's d) to determine if the GCN model significantly outperforms the geometry-based baseline.

- **FR-006: Sensitivity Analysis**
 The pipeline evaluates model performance across absolute MAE thresholds (0.01, 0.05, 0.1 Å²) as mandated by experimental error margins, reporting success rates for each threshold.

- **FR-007: Multiple Comparison Correction**
 The system applies Bonferroni or False Discovery Rate (FDR) corrections to p-values generated during sensitivity analysis to control for Type I errors.

## Installation

### Prerequisites
- Python 3.9+
- pip
- Git

### Setup Steps

1. **Clone the repository**
 ```bash
 git clone <repository-url>
 cd PROJ-412-predicting-molecular-surface-area-from-g
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install PyTorch and PyTorch Geometric**
 ```bash
 pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu
 pip install torch-geometric==2.4.0 --index-url https://download.pytorch.org/whl/cpu
 ```

4. **Install project dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage

### Quick Start

Run the full pipeline with a fixed seed for reproducibility:

```bash
python code/main.py --mode full --seed 42
```

### Pipeline Stages

The pipeline can be executed in stages or as a full run:

- **Data Ingestion & Preprocessing**:
 ```bash
 python code/data/ingest.py
 python code/data/preprocess.py
 ```

- **Model Training**:
 ```bash
 python code/models/train.py
 python code/models/baseline.py
 ```

- **Evaluation & Sensitivity Analysis**:
 ```bash
 python code/eval/sensitivity.py
 python code/runComparison.py
 ```

### Configuration

Configuration parameters are defined in `code/config.py`:

- `TIME_BUDGET`: Maximum allowed runtime in hours (default: 6.0)
- `MAX_RAM_GB`: Maximum RAM usage threshold (default: 7.0 GB)
- `SENSITIVITY_THRESHOLDS`: List of MAE thresholds for sensitivity analysis (default: [0.01, 0.05, 0.1])

### Output Artifacts

The pipeline produces the following key outputs:

- **Data Artifacts**:
 - `data/raw/chunk_*.parquet`: Ingested raw data chunks
 - `data/processed/paired_dataset.parquet`: Merged dataset with features and labels
 - `data/splits/train_indices.csv`, `data/splits/test_indices.csv`: Split indices

- **Model Artifacts**:
 - `results/baseline/baseline_model_2d.pkl`: 2D baseline model
 - `results/baseline/baseline_model_geometry.pkl`: Geometry-based baseline model
 - `results/predictions/gcn_predictions.parquet`: GCN model predictions

- **Reports**:
 - `results/reports/model_comparison.json`: Model performance comparison
 - `results/reports/sensitivity_analysis.md`: Sensitivity analysis report
 - `results/plots/sensitivity_absolute.png`: Sensitivity curve visualization

## Project Structure

```
.
├── code/
│ ├── data/ # Data ingestion and preprocessing
│ ├── models/ # Model definitions and training
│ ├── eval/ # Evaluation and sensitivity analysis
│ ├── utils/ # Utility functions
│ ├── data_models/ # Data class definitions
│ ├── config.py # Configuration parameters
│ └── requirements.txt
├── data/
│ ├── raw/ # Raw ingested data
│ ├── processed/ # Processed datasets
│ ├── splits/ # Train/test split indices
│ └── schemas/ # Data schema definitions
├── results/
│ ├── reports/ # Analysis reports
│ ├── plots/ # Visualization plots
│ ├── baseline/ # Baseline model artifacts
│ └── predictions/ # Model predictions
├── tests/
│ ├── contract/ # Contract tests
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── logs/ # Execution logs
└── README.md
```

## Reproducibility

- **Seed Pinning**: All random number generators are seeded using `code/utils/seed.py`.
- **Checksum Verification**: Data integrity is verified using SHA-256 checksums stored in `data/raw/checksums.json`.
- **Conformer Parameters**: ETKDG parameters are logged in `data/processed/conformer_params.json` and hashed for traceability.

## License

This project is for research purposes.

## Contributing

Contributions are welcome. Please ensure that all tests pass and that new code adheres to the project's linting and formatting standards (Ruff, Black).