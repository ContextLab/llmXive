# Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

**Project ID**: PROJ-355
**Status**: Active Research Pipeline

## Overview

This project implements a scientific pipeline to investigate how impurity clustering at grain boundaries (GBs) affects segregation energies. We combine materials data from public repositories (Materials Project, OQMD) with atomistic simulations using NIST EAM potentials to compute clustering descriptors (RDF, pair correlation, Voronoi counts) and model their relationship with segregation energy.

## Data Provenance

- **Bulk Configurations**: Sourced from the Materials Project (MP) and Open Quantum Materials Database (OQMD).
 - MP URL: ` Name or service not known)"))]
 - OQMD URL: ` Name or service not known)"))]
- **Potentials**: NIST Interatomic Potentials Repository (EAM/FS format).
- **Validation**: Ground truth validation performed against a pre-computed DFT subset from NIST/MP benchmarks.
- **Generated Data**: All processed data (GB supercells, descriptors, energies) are generated locally via simulation and stored in `data/processed/`.

## Prerequisites

- Python 3.9+
- Required packages listed in `requirements.txt` (install via `pip install -r requirements.txt`).
- Access to the internet for downloading initial bulk configurations and potentials.

## Execution Instructions

### 1. Setup Environment

```bash
cd projects/PROJ-355-predicting-the-impact-of-impurity-cluste
pip install -r requirements.txt
```

### 2. Run the Pipeline

The main orchestration script is located at `code/main.py`. It executes the following logical sequence:
1. **Download**: Fetches bulk configurations from MP/OQMD.
2. **Build**: Constructs GB supercells and inserts impurities.
3. **Descriptors**: Computes RDF, pair correlation, and Voronoi counts.
4. **Simulate**: Calculates segregation energies using EAM potentials.
5. **Model**: Trains regression models and performs cross-validation.

To run the full pipeline:
```bash
python code/main.py
```

### 3. Run Specific Modules

- **Download Data**:
 ```bash
 python code/data/download.py
 ```
- **Compute Descriptors**:
 ```bash
 python code/run_descriptors.py
 ```
- **Simulate Energies**:
 ```bash
 python code/data/simulate_energy.py
 ```
- **Train Model**:
 ```bash
 python code/modeling/train.py
 ```

### 4. Validation & Testing

- **Ground Truth Validation**:
 ```bash
 python code/data/validate_potential.py
 ```
- **Unit Tests**:
 ```bash
 python -m pytest tests/unit/ -v
 ```
- **Integration Tests**:
 ```bash
 python -m pytest tests/integration/ -v
 ```

## Output Artifacts

Upon successful execution, the following artifacts will be generated:

- `data/processed/gb_supercells/`: Directory containing GB supercell structures.
- `data/processed/descriptors.csv`: Clustering descriptors (RDF, pair_corr, voronoi_count).
- `data/processed/segregation_energies.csv`: Computed segregation energies linked to descriptors.
- `results/metrics.json`: Model performance metrics (R², RMSE, p-values).
- `results/sensitivity_report.json`: Sensitivity analysis results.
- `data/processed/collinearity_report.md`: VIF analysis report.

## Configuration

Configuration parameters (random seeds, paths, hyperparameters) are defined in `code/config.py`.
- **Random Seed**: Fixed in `config.py` for reproducibility.
- **Scope**: Defined in `data/scope_config.yaml` (alloy systems, sample size limits).

## License

This project is part of the llmXive automated science pipeline. See the repository root for license details.

## Contact

For issues or questions, please refer to the project's issue tracker or contact the research team.