# Investigating the Relationship Between Brain Network Dynamics and Subjective Time Perception

## Installation

This project uses a standard Python virtual environment. The recommended steps are:

```bash
# Clone the repository
git clone
cd PROJ-433-investigating-the-relationship-between-b

# Create a virtual environment
python -m venv venv
source venv/bin/activate # On Windows use `venv\\Scripts\\activate`

# Install exact dependencies
pip install -r requirements.txt
```

The `requirements.txt` file pins exact versions for all scientific libraries
(e.g., `nilearn`, `networkx`, `scikit-learn`, `pandas`, `matplotlib`, `nibabel`,
`scipy`, `pytest`, `dask`, `distributed`, etc.) to guarantee reproducibility.

## Usage

The pipeline is orchestrated through a series of command‑line entry points located in the `code/` directory. A typical end‑to‑end run (quickstart) looks like:

```bash
# Verify data availability
python code/main.py

# Preprocess fMRI data (run on a subset for CI)
python code/preprocess.py --subject sub-01 --mode ci

# Compute connectivity metrics
python code/metrics.py --subject sub-01 --input-dir data/raw

# Perform statistical analysis
python code/analysis.py

# Generate visualisations
python code/viz.py
```

Each script provides its own `--help` output describing required arguments.

## Reproducibility

- **Version control**: All code, configuration files, and documentation are tracked in Git.
- **Pinned dependencies**: `requirements.txt` contains exact version numbers.
- **Randomness control**: The utility `utils.get_seeded_rng(seed)` is used throughout the code base; the default seed is `42`.
- **Logging**: All stages write timestamped entries to log files under `data/` (`preprocess_log.txt`, `analysis_log.txt`, `metrics_log.txt`).
- **Data provenance**: Raw data are stored in `data/raw/` and are never altered in‑place; processed outputs are written to `data/processed/` and results to `data/results/`.
- **Testing**: Unit and integration tests live in the `tests/` directory and can be run with `pytest -v`.

Following these guidelines ensures that any researcher can reproduce the exact results reported in the accompanying manuscript.