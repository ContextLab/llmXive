# PROJ-512: Predicting Molecular Permeability of Polymers via Graph Neural Networks

## Overview

This project implements a machine learning pipeline to predict the gas permeability of polymers using Graph Neural Networks (GNNs). The approach relies strictly on 2D topological features (atom type, hybridization, bond type) as defined in the project specifications (FR-001), ensuring CPU-tractability and reproducibility without requiring 3D conformational data.

## Project Structure

```text
projects/PROJ-512-predicting-molecular-permeability-of-pol/
├── code/
│ ├── data/
│ │ ├── raw/ # Raw datasets (NIST or Simulation)
│ │ ├── processed/ # Cleaned HDF5/Parquet files and split indices
│ │ ├── ingestion.py # Data fetching, SMILES parsing, cleaning
│ │ ├── preprocessing.py # Feature extraction, scaffold splitting
│ │ ├── simulation.py # Synthetic data generator (fallback)
│ │ └── utils.py # Seeding, logging, validation
│ ├── models/
│ │ ├── gnn.py # Message-Passing GNN implementation
│ │ ├── baselines.py # RF, Linear, and Topology Control baselines
│ │ ├── trainer.py # Training loop, early stopping, gradient clipping
│ │ ├── polymer_graph.py # Core graph entity definition
│ │ └── permeability_record.py # Data model for labels
│ ├── evaluation/
│ │ ├── metrics.py # R2, MAE, Pearson correlation
│ │ ├── stats.py # Wilcoxon, VIF, Sensitivity analysis
│ │ └── report.py # Final report generation
│ ├── main.py # Entry point
│ └── requirements.txt # Dependencies
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── docs/
│ ├── README.md # This file
│ └── data_dictionary.md # Detailed 2D feature specification
└── specs/
 └── 001-predicting-molecular-permeability/
```

## Key Features

- **2D-Only Graph Representation**: Adheres to FR-001, using only atom type, hybridization, and bond type. No 3D coordinates or physics-based approximations.
- **Robust Data Pipeline**: Supports real data ingestion (NIST/PubChem) with a fallback to synthetic simulation if real data is unavailable.
- **Scaffold Splitting**: Implements Murcko scaffold splitting to ensure strict separation of chemical scaffolds between training and test sets, preventing data leakage.
- **Baseline Comparison**: Includes Random Forest (ECFP4), Linear Regression (RDKit descriptors), and a Randomized Topology Control baseline to verify graph structure learning.
- **Statistical Validation**: Wilcoxon signed-rank tests and Variance Inflation Factor (VIF) analysis for model robustness.

## Quick Start

1. **Install Dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```

2. **Run the Pipeline**:
 ```bash
 cd code
 python main.py
 ```

3. **Outputs**:
 - `data/processed/polymers.h5`: Processed dataset.
 - `data/processed/scaffold_split_indices.json`: Train/Val/Test splits.
 - `evaluation/results/metrics.json`: Model performance metrics.
 - `evaluation/results/sensitivity_sweep.json`: Sensitivity analysis results.

## Documentation

- **Data Dictionary**: See `docs/data_dictionary.md` for a complete list of 2D features, their encodings, and sources.
- **API Reference**: Inline documentation is available in the `code/` modules.

## Constraints

- **CPU Only**: All models and data processing are optimized for CPU execution.
- **No Synthetic Fallback Silence**: If real data fetch fails, the system logs a warning and uses simulation data, but never silently replaces real data with fake values without explicit logging.
- **Reproducibility**: Random seeds are managed via `code/data/utils.py`.

## License

Internal Research Project.
