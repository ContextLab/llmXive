# Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Project ID:** PROJ-355

## Overview
This project investigates the relationship between impurity clustering descriptors (RDF peaks, pair correlation, Voronoi counts) and grain boundary segregation energies. The pipeline ingests bulk configurations from materials databases, constructs grain boundary supercells, computes clustering descriptors, and performs regression analysis to predict segregation impact.

## Project Structure
- `code/`: Source code for data processing, simulation, and modeling.
- `data/`:
 - `raw/`: Original downloaded data (bulk configurations).
 - `processed/`: Derived data (supercells, descriptors, energies).
- `results/`: Final analysis outputs, metrics, and reports.
- `tests/`: Unit and integration tests.
- `contracts/`: Data and output schema definitions.

## Prerequisites
- Python 3.9+
- `pip`
- Required dependencies listed in `requirements.txt` (to be generated).

## Installation
1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Execution
The main pipeline is orchestrated via `code/main.py`.

### Running the Full Pipeline
```bash
cd projects/PROJ-355-predicting-the-impact-of-impurity-cluste
python code/main.py
```

### Running Individual Stages
- **Download Data:** `python code/data/download.py`
- **Build GB Supercells:** `python code/data/gb_builder.py`
- **Compute Descriptors:** `python code/data/descriptors.py`
- **Simulate Energies:** `python code/data/simulate_energy.py`
- **Train Model:** `python code/modeling/train.py`
- **Evaluate & Analyze:** `python code/modeling/evaluate.py`

## Configuration
Configuration parameters (paths, seeds, hyperparameters) are managed in `code/config.py`.

## Data Sources
- Bulk configurations are sourced from the Materials Project (MP) and/or OQMD.
- Segregation energies are generated via simulation using EAM potentials.

## License
[Project License Placeholder]