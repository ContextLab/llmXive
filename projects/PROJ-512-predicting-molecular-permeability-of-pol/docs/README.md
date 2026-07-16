# PROJ-512: Predicting Molecular Permeability of Polymers via Graph Neural Networks

## Project Overview
This project implements a machine learning pipeline to predict the gas permeability
of polymers using Graph Neural Networks (GNNs). The system ingests real polymer data
from NIST/PubChem, constructs molecular graphs, trains GNN models alongside baseline
methods (Random Forest, Linear Regression), and performs rigorous statistical validation.

## User Stories
- **US1 (P1)**: Data Ingestion and Graph Construction
- **US2 (P2)**: Model Training and Baseline Comparison
- **US3 (P3)**: Statistical Validation and Sensitivity Analysis

## Directory Structure
```
projects/PROJ-512-predicting-molecular-permeability-of-pol/
├── code/
│ ├── data/
│ │ ├── ingestion.py # Data fetching and cleaning
│ │ ├── preprocessing.py # Feature extraction and splitting
│ │ ├── save_dataset.py # HDF5 serialization
│ │ └── utils.py # Seed management and logging
│ ├── models/
│ │ ├── polymer_graph.py # Graph entity definition
│ │ ├── permeability_record.py # Data model
│ │ ├── gnn.py # GNN architecture
│ │ ├── baselines.py # RF and Linear Regression
│ │ └── trainer.py # Training loop
│ ├── evaluation/
│ │ ├── metrics.py # R², MAE, Pearson
│ │ ├── stats.py # Wilcoxon, VIF, Sensitivity
│ │ └── report.py # Report generation
│ └── main.py # Entry point
├── data/
│ └── processed/
│ └── polymers.h5 # Cleaned dataset artifact
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
└── docs/ # This documentation
```

## Quick Start
1. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
2. **Run the pipeline**:
 ```bash
 cd projects/PROJ-512-predicting-molecular-permeability-of-pol/code
 python main.py
 ```
3. **Outputs**:
 - `data/processed/polymers.h5`: Cleaned dataset
 - `logs/`: Execution logs
 - `reports/`: Evaluation metrics and statistical reports

## Data Integrity
This project strictly adheres to **FR-001**: All data must be sourced from real
databases (NIST, PubChem). No synthetic or simulated data is permitted. The
ingestion pipeline will fail loudly if real data cannot be fetched.
