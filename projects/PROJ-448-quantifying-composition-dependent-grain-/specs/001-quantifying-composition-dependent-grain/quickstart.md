# Quickstart: Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys

## Prerequisites

- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or local environment for testing.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-448-quantifying-composition-dependent-grain-
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline consists of three stages: Data Preparation, Segregation Calculation, and Analysis.

### 1. Data Preparation
This step downloads (or loads) the required data.
```bash
python code/cli/run_pipeline.py --stage data_prep
```
- **Output**: `data/raw/calphad_params.json`, `data/raw/dft_energies.json`, `data/data_manifest.json`, `research/data_sources.md`.

### 2. Segregation Calculation
Computes equilibrium concentrations using the McLean isotherm.
```bash
python code/cli/run_pipeline.py --stage calc_segregation
```
- **Output**: `data/processed/segregation_profiles.parquet`.

### 3. Analysis & Regression
Fits the multicomponent model and performs cross-validation.
```bash
python code/cli/run_pipeline.py --stage analyze
```
- **Output**: `data/processed/regression_results.json`, `data/processed/heatmaps/`.

## Visualizing Results

To generate heatmaps of segregation energy vs. composition:
```bash
python code/cli/run_pipeline.py --stage visualize
```
- **Output**: `data/processed/heatmaps/segregation_energy_heatmap.png`.

## Testing

Run the full test suite:
```bash
pytest tests/
```

## Data Manifest

All data sources are documented in `data/data_manifest.json`. This file includes:
- `source_type`: e.g., "CALPHAD", "DFT", "APT".
- `source_id`: Unique identifier.
- `doi` / `url`: Link to the source.
- `status`: "verified", "mocked", "simulated".

## Data Sources Document

The `research/data_sources.md` file contains the required JSON object with `source_id`, `doi`, `url`, and `status` for all data sources, including NIST APT accession IDs and literature DOIs.