# Structure-Only Surrogate Model for 2D Material Elastic Moduli

> "Don't fool yourself — and you are the easiest person to fool." — Richard Feynman

## Project Overview

This project implements a **Structure-Only Surrogate Model** to predict the elastic moduli (Young's, Shear, and Poisson's ratios) of two-dimensional materials.

**Important Distinction**: This model is a statistical interpolator trained on pre-computed Density Functional Theory (DFT) data. It does **NOT** solve the Schrödinger equation, calculate electron density from the Hamiltonian, or perform first-principles calculations. It learns correlations between structural descriptors and DFT-computed properties to accelerate inference.

## Key Features

- **Surrogate Modeling**: Predicts elastic properties orders of magnitude faster than DFT by interpolating learned patterns from existing datasets.
- **Structure-Only**: Relies exclusively on crystallographic graph representations (nodes = atoms, edges = bonds) without electronic structure inputs.
- **Family-Aware Splitting**: Evaluates generalization to unseen chemical families to prevent overfitting.
- **Reproducibility**: All random seeds are pinned in `code/utils/config.py` to ensure deterministic results across runs.
- **Data Hygiene**: External datasets are fetched from the same canonical source on every run, with SHA256 checksums recorded in `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml`.

## Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
pip install -r code/requirements.txt
```

### Running the Pipeline

1. **Data Ingestion**: Download and process 2D material data
 ```bash
 python code/ingest/pipeline.py
 ```
 Output: `data/processed/graphs_v1.parquet`

2. **Model Training**: Train the lightweight GNN
 ```bash
 python code/model/train.py
 ```
 Output: `data/results/training_logs.json`, `data/processed/test_indices.json`

3. **Evaluation**: Assess generalization performance
 ```bash
 python code/model/generalization_test.py
 ```
 Output: `data/results/generalization_metrics.json`

4. **Feature Importance**: Analyze descriptor contributions
 ```bash
 python code/analysis/aggregate.py
 python code/analysis/report_generator.py
 ```
 Output: `data/results/feature_importance_report.md`

## Methodology

The model uses a Graph Neural Network (GNN) architecture to map material structures to elastic moduli. The training data is derived from existing DFT calculations (e.g., Materials Project), and the model learns to approximate these values based on structural topology and composition.

For a detailed explanation of the distinction between this surrogate approach and true first-principles methods, see `docs/methodology.md`.

## Limitations

- **Extrapolation Failure**: The model cannot predict properties for materials significantly outside the chemical space of the training set.
- **No Physics Discovery**: The model identifies statistical correlations, not fundamental physical laws.
- **DFT Dependency**: Accuracy is bounded by the accuracy of the underlying DFT data used for training.

## License

MIT License

## Citation

If you use this surrogate model in your research, please cite the underlying DFT datasets and acknowledge the limitation that this is an interpolative model, not a first-principles solver.