# Predicting the Impact of Composition on the Shear Modulus of Bulk Metallic Glasses

This project implements an automated scientific research pipeline to predict the shear modulus of Bulk Metallic Glasses (BMGs) based on their chemical composition. It follows the llmXive automated science methodology, ensuring reproducibility, data provenance, and statistical rigor.

## Project Structure

The project is organized into the following directories:

- `code/`: Source code for the data pipeline, model training, evaluation, and visualization.
- `data/`: Storage for raw data, processed datasets, and generated artifacts.
 - `data/raw/`: Original datasets (e.g., from Materials Project or synthetic generators).
 - `data/processed/`: Cleaned and feature-engineered data ready for modeling.
 - `data/artifacts/`: Final outputs including model reports and visualizations.
- `tests/`: Unit and integration tests for pipeline components.
- `docs/`: Documentation and design specifications.
- `state/`: Provenance tracking and checksums for all generated artifacts.
- `contracts/`: JSON/YAML schemas defining data structures (BMGEntry, ModelPerformance).
- `utils/`: Shared utilities for configuration, logging, and provenance.

## Prerequisites

- Python 3.11+
- `pip` for dependency management

## Installation

1. Clone the repository.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage Instructions

The pipeline is orchestrated via a `Makefile`.

### Running the Full Pipeline

To execute the entire research pipeline from data ingestion to final visualization:

```bash
make all
```

This will:
1. Fetch or generate raw data.
2. Clean and standardize units.
3. Calculate compositional descriptors (δ, ΔHmix, VEC, Δχ).
4. Handle collinearity (VIF/PCA).
5. Split data by alloy family.
6. Train and evaluate models (Linear Regression, Random Forest, Gradient Boosting).
7. Perform statistical comparisons (Corrected Resampled t-test, Wilcoxon, Bayes Factor).
8. Generate feature importance reports and visualizations.

### Running Individual Stages

You can run specific stages of the pipeline independently:

- **Data Ingestion & Cleaning**:
 ```bash
 python code/data/ingest.py
 python code/data/clean.py
 ```

- **Feature Engineering**:
 ```bash
 python code/data/features.py
 ```

- **Model Training & Evaluation**:
 ```bash
 python code/models/train.py
 python code/models/evaluate.py
 ```

- **Feature Importance & Visualization**:
 ```bash
 python code/models/importance.py
 python code/viz/plots.py
 ```

## Data Provenance

This project adheres to strict data provenance principles (Constitution Principle V) to ensure all results are reproducible and traceable.

### How Provenance Works

1. **Checksum Generation**: Every time a data artifact (CSV, JSON, etc.) is generated or modified, its SHA-256 checksum is computed.
2. **State Recording**: These checksums, along with metadata (timestamp, source script, input hashes), are recorded in the canonical state file:
 `state/projects/PROJ-380-predicting-the-impact-of-composition-on-.yaml`
3. **Verification**: The `utils/provenance.py` module provides functions to verify that a file on disk matches its recorded checksum, ensuring data integrity throughout the pipeline.

### Viewing Provenance

To list all recorded artifacts and their checksums:

```bash
python -c "from utils.provenance import list_artifacts; list_artifacts()"
```

To verify a specific artifact:

```bash
python -c "from utils.provenance import verify_artifact; verify_artifact('data/processed/features.csv')"
```

## Data Sources

- **Primary Source**: Materials Project API (via `code/data/ingest.py`).
- **Fallback**: If the API is unavailable, the pipeline falls back to a synthetic data generator (`code/data/synthetic_generator.py`) based on literature-documented BMG composition distributions and Mendeleev elemental properties.

## Statistical Methodology

- **Primary Comparison**: Corrected Resampled t-test (Nadeau & Bengio).
- **Fallback Comparison**: Wilcoxon Signed-Rank Test.
- **Bayesian Fallback**: Bayes Factor calculation for Wilcoxon results.
- **Validation Strategy**: Hybrid Leave-One-Family-Out (LOFO) for large families and GroupKFold for small families.

## License

[Insert License Information Here]