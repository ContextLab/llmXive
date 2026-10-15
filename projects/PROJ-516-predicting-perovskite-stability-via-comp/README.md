# Predicting Perovskite Stability via Compositional Fingerprints

## Project overview
This repository implements a reproducible data‑science pipeline that predicts the thermal decomposition temperature ($T_d$) of metal‑halide perovskites from their elemental composition. The workflow downloads experimental data from NREL and the Materials Project [UNRESOLVED-CLAIM: c_354a891b — status=not_enough_info], computes compositional descriptors, trains baseline regression models, and evaluates performance both via cross‑validation and external literature validation.

## Installation
```bash
# Clone the repository and navigate to the project root
git clone <repository-url>
cd projects/PROJ-516-predicting-perovskite-stability-via-comp

# Set up a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the pipeline
The pipeline can be executed step‑by‑step using the provided scripts, or end‑to‑end via the driver:

```bash
# Step 1: Data ingestion (fetches NREL and Materials Project data)
python code/data_ingestion.py

# Step 2: Compute compositional descriptors
python code/feature_engineering.py

# Step 3: Train baseline models with cross‑validation
python code/model_training.py

# Step 4: Perform validation and generate reports
python code/validation.py
```

Alternatively, run the full workflow in one command:

```bash
python code/main.py
```

## Documentation
- Detailed usage instructions are available in `docs/quickstart.md`.
- API reference and schema definitions reside in the `code/` and `contracts/` directories respectively.

## License
This project is released under the MIT License. See the `LICENSE` file for full terms.