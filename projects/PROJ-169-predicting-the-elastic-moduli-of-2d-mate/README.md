# Structure-Only Surrogate Model for 2D Material Elastic Moduli

**Project ID**: PROJ-169
**Status**: Active Development

## ⚠️ Critical Disclaimer: Surrogate Model Definition

**This project implements a SURROGATE MODEL that interpolates pre-computed DFT data.**

- **What this model DOES**: It uses Graph Neural Networks (GNNs) to learn statistical correlations between structural descriptors and elastic moduli from existing Density Functional Theory (DFT) calculations.
- **What this model DOES NOT DO**: It does **NOT** solve the Schrödinger equation, perform first-principles calculations, or derive fundamental quantum mechanical properties from the Hamiltonian.

**Terminology Correction**: The term "First-Principles" refers strictly to the underlying DFT data sources (e.g., Materials Project, AFLOW) from which this model learns. The ML model itself is a **curve-fitting interpolator**, not a physics solver.

## Research Question

Can a lightweight Graph Neural Network, trained exclusively on structural graph representations of 2D materials, accurately predict their elastic moduli (Young's, Shear, and Poisson's ratios) by interpolating values from existing DFT datasets, while maintaining generalization to unseen chemical families?

## Methodology Summary

1. **Data Ingestion**: Download CIF structures and elastic tensors from public DFT repositories (Materials Project/AFLOW).
2. **Graph Construction**: Convert crystal structures into `MaterialGraph` objects using `pymatgen`.
3. **Surrogate Training**: Train a CPU-efficient GNN to map structural features to elastic moduli.
4. **Validation**: Evaluate performance against held-out DFT values, specifically testing inter-family generalization.
5. **Analysis**: Use SHAP and ablation studies to identify which structural descriptors correlate most strongly with predicted moduli.

## Project Structure

```
.
├── code/ # Source code
│ ├── analysis/ # Feature importance and ablation
│ ├── data_models/ # Data schemas
│ ├── ingest/ # Data download and parsing
│ ├── model/ # GNN architecture and training
│ └── utils/ # Configuration, logging, memory
├── data/
│ ├── raw/ # Downloaded CIFs and tensors
│ ├── processed/ # Graph representations (Parquet)
│ └── results/ # Training logs, metrics, reports
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── README.md # This file
└── requirements.txt # Python dependencies
```

## Prerequisites

- Python 3.11+
- PyTorch 2.x
- PyTorch Geometric
- `pymatgen`, `shap`, `scikit-learn`

## Quick Start

### 1. Setup Environment

```bash
cd code
pip install -r requirements.txt
```

### 2. Data Ingestion (User Story 1)

Run the pipeline to download, parse, and filter 2D material graphs:

```bash
python ingest/pipeline.py --source materials_project --output data/processed/graphs_v1.parquet
```

*Note: This step requires network access and may take time depending on the dataset size.*

### 3. Model Training (User Story 2)

Train the lightweight GNN surrogate:

```bash
python model/train.py --data data/processed/graphs_v1.parquet --epochs 50
```

Outputs: `data/results/training_logs.json`

### 4. Evaluation & Generalization Test

Assess performance on unseen families:

```bash
python model/generalization_test.py --data data/processed/graphs_v1.parquet
```

Outputs: `data/results/generalization_metrics.json`

### 5. Feature Importance Analysis (User Story 3)

Generate the unified ranked list of structural descriptors:

```bash
python analysis/report_generator.py
```

Outputs: `data/results/feature_importance_report.md`

## Key Constraints & Compliance

- **Memory Limit**: The pipeline is designed to run within 7GB RAM (see `code/utils/memory_utils.py`).
- **Single Source Rule**: Each run must use exactly one canonical data source (Materials Project OR AFLOW) to avoid mixing incompatible DFT methodologies.
- **Terminology**: The term "First-Principles" is strictly forbidden when describing the ML model. Use "Surrogate Model" or "ML Interpolator" only.
- **Disclaimer Injection**: All generated reports and logs explicitly state that results are statistical correlations, not fundamental physics.

## Limitations

- **Extrapolation**: The model cannot predict properties for materials outside the chemical space of the training DFT data.
- **Physics Discovery**: This model does not discover new physical laws; it approximates existing DFT calculations.
- **Data Quality**: Results are limited by the accuracy and coverage of the underlying DFT datasets.

## License

[Insert License Here]

## Citation

If you use this surrogate model or its methodology, please cite the underlying DFT sources (e.g., Materials Project) and this project's documentation.