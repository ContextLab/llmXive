# Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

This project implements a computational pipeline to quantify the relationship between impurity clustering descriptors (RDF peaks, pair correlations, Voronoi counts) at grain boundary (GB) interfaces and segregation energies. The goal is to determine how the spatial clustering of impurity atoms in the bulk lattice influences the thermodynamic driving force for their segregation to grain boundaries in polycrystalline alloys.

## Project Overview

The pipeline performs the following high-level steps:
1. **Data Acquisition**: Downloads bulk configurations from OQMD and Materials Project.
2. **Structure Generation**: Constructs GB supercells and inserts impurities at the interface.
3. **Descriptor Computation**: Extracts clustering metrics (RDF, pair correlation, Voronoi neighbor counts) specifically from the GB interface region.
4. **Simulation**: Generates segregation energies using NIST EAM potentials via atomistic simulations.
5. **Modeling**: Trains a Linear Regression model to map clustering descriptors to segregation energies, employing k-fold cross-validation and collinearity diagnostics (VIF).
6. **Analysis**: Performs threshold sensitivity analysis and hypothesis testing with multiple-comparison correction.

## Execution Instructions

### Prerequisites
- Python 3.11+
- `pip` and `venv`
- Network access to OQMD and Materials Project.

### Installation
```bash
# Clone the repository and navigate to the project root
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Pipeline
1. **Validate the empirical potential against DFT reference data**:
 ```bash
 python code/data/validate_potential.py
 ```
 This ensures the EAM potential is accurate (MAE < 0.1 eV) before proceeding.

2. **Run the full pipeline**:
 ```bash
 python code/main.py --mode full
 ```
 This executes the entire sequence: download $\rightarrow$ build $\rightarrow$ descriptors $\rightarrow$ simulate $\rightarrow$ train.

3. **Run analysis separately** (if data is already prepared):
 ```bash
 python code/train_model.py --input data/processed/training_set.csv --output results/metrics.json
 ```

## Data Provenance

To ensure reproducibility and scientific integrity, the project tracks data provenance as follows:

- **Bulk Configurations**: Sourced from the Open Quantum Materials Database (OQMD) and the Materials Project. All downloads are validated against a whitelist of verified URLs.
- **Interatomic Potentials**: Uses NIST EAM potentials (e.g., Fe-Cr) downloaded from verified public mirrors.
- **Derived Artifacts**:
 - Grain boundary supercells are generated deterministically using `pymatgen`.
 - Segregation energies are computed via CPU-tractable atomistic simulations using the `ase` library and the NIST EAM potential.
- **Metadata**: All external data sources, including URLs and SHA256 checksums, are recorded in `data/metadata.yaml`.

## Project Structure

- `code/`: Source code for the pipeline (data acquisition, simulation, and modeling).
- `data/raw/`: Original bulk configurations from OQMD/MP.
- `data/processed/`: GB supercells, computed descriptors, and simulation results.
- `data/potentials/`: Stored EAM potential files.
- `results/`: Final model metrics, sensitivity reports, and performance logs.
- `tests/`: Unit and integration tests.
- `contracts/`: Schema definitions for input and output data validation.