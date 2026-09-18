# Quickstart: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

## Prerequisites

-   Python 3.11+
-   `git`
-   Access to the `OxfordPets_test` dataset (public).

## Installation

1.  **Clone and Setup**:
    ```bash
    git checkout 001-llmxive-entanglement-analysis
    cd projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/
    pip install -r requirements.txt
    ```

## Running the Pipeline

### Mode A: Unit Test Only (Synthetic Data)
> **Note**: This mode uses a tiny synthetic dataset to verify the pipeline logic. It does **not** run the full analysis.
```bash
python simulate.py --mode unit-test
python features.py --mode unit-test
python model.py --mode unit-test
```

### Mode B: Full Analysis (OxfordPets + Simulation)
> **Note**: This mode downloads the real OxfordPets dataset and generates synthetic distributions.
```bash
# Step 1: Ingest Real Data
python ingest.py

# Step 2: Generate Synthetic Distributions
python simulate.py --mode full-analysis

# Step 3: Engineer Features
python features.py

# Step 4: Train & Evaluate
python model.py
```

## Validation

Run the test suite:
```bash
pytest tests/
```
-   Checks feature calculations against known values.
-   Verifies data lineage.