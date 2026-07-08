# Predicting the Elastic Moduli of 2D Materials: Structure-Only Surrogate Model

**Project ID:** PROJ-169

## Overview
This project implements a **Structure-Only Surrogate Model** to predict the elastic moduli (Young's, Shear, Poisson) of 2D materials. Unlike first-principles calculations that solve the Schrödinger equation, this model acts as a high-fidelity interpolator of existing Density Functional Theory (DFT) data, utilizing Graph Neural Networks (GNNs) to map crystal structures directly to mechanical properties.

## Key Constraints
- **Memory Limit:** 7GB RAM (enforced via dynamic sampling).
- **Data Source:** Existing DFT repositories (Materials Project, AFLOW) only. No new DFT calculations performed.
- **Architecture:** Lightweight GNN (CPU-optimized).

## Project Structure
```
.
├── code/
│ ├── data_models/ # MaterialGraph schema
│ ├── ingest/ # Data download, parsing, filtering
│ ├── model/ # GNN architecture, training, evaluation
│ ├── analysis/ # Feature importance, ablation
│ ├── utils/ # Config, logging, memory management
│ └── requirements.txt # Pinned dependencies
├── data/
│ ├── raw/ # Downloaded CIFs
│ ├── processed/ # Graphs (Parquet)
│ └── results/ # Metrics, logs, reports
├── tests/ # Unit and integration tests
├── specs/ # Feature specifications
├──.ruff.toml # Linting config
├── pyproject.toml # Build & formatting config
└── README.md
```

## Quick Start
1. **Install Dependencies:**
 ```bash
 pip install -r code/requirements.txt
 ```

2. **Run Data Pipeline (US1):**
 ```bash
 python code/ingest/pipeline.py --source materials_project --limit 100
 ```

3. **Train Model (US2):**
 ```bash
 python code/model/train.py --epochs 50
 ```

4. **Run Tests:**
 ```bash
 pytest tests/
 ```

## Terminology Correction
Per reviewer feedback, this project explicitly avoids the term "First-Principles" for the GNN model itself. The model is a **Surrogate** that learns from First-Principles (DFT) data. It does not solve the Hamiltonian; it approximates the mapping learned from it.
