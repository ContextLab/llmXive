# Predicting Perovskite Stability via Compositional Fingerprints

## Project overview
This repository provides a reproducible end‑to‑end pipeline that predicts the thermal decomposition temperature ( Tₙ ) of metal‑halide perovskites using only compositional descriptors derived from their chemical formulas.

## Installation
```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-516-predicting-perovskite-stability-via-comp

# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

## Running the pipeline
```bash
# Initialise state (required for the first run)
python -m code.utils.state_manager update data/raw/dummy.csv

# Execute the full pipeline
python -m code.main run_all
```

The above commands will fetch raw data, compute compositional descriptors, train baseline regressors, and produce validation reports.
