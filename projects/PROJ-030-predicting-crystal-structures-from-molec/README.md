# PROJ-030: Predicting Crystal Structures from Molecular Fingerprints

An automated scientific pipeline to predict crystal structures (space groups and lattice parameters) from molecular fingerprints using machine learning. This project implements a rigorous, reproducible workflow adhering to the Constitution Principles of automated science.

## Overview

This pipeline ingests organic crystal structures from the Crystallography Open Database (COD), processes them into molecular fingerprints (ECFP4), trains machine learning models (Random Forest, Gradient Boosting, Ridge Regression), and performs interpretability analysis to identify predictive chemical substructures.

**Key Features:**
- **Data Ingestion:** Streaming download of the COD organic subset from HuggingFace.
- **Feature Engineering:** Generation of ECFP4 fingerprints and handling of polymorphism (treating unique SMILES/Space Group pairs as distinct samples).
- **Robust Modeling:** Scaffold-based train/test splits to ensure zero structural overlap, handling of class imbalance, and baseline comparisons.
- **Interpretability:** SHAP and permutation importance analysis to map fingerprint bits to chemical substructures.
- **Constitution Compliance:** Strict error handling (no synthetic fallbacks), citation verification, and power analysis integration.

## Prerequisites

- Python 3.11+
- HuggingFace Token (for dataset access)
- System dependencies: `libopenbabel-dev` (for PIFCifRw/OpenBabel)

## Installation

1. **Clone the repository:**
 ```bash
 git clone <repository-url>
 cd PROJ-030-predicting-crystal-structures-from-molec
 ```

2. **Create a virtual environment:**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies:**
 ```bash
 cd code
 pip install -r requirements.txt
 ```

4. **Configure environment:**
 - Copy `.env.example` to `.env` in the `code/` directory.
 - Set your `HF_TOKEN` in `.env` to access the HuggingFace dataset.
 ```bash
 cp.env.example.env
 # Edit.env to add HF_TOKEN=your_token_here
 ```

5. **Verify environment:**
 ```bash
 python code/validate_env.py
 ```

## Usage

### 1. Data Ingestion Pipeline

Downloads, parses, and processes the COD dataset to generate the final training CSV.

```bash
python code/ingestion/run_pipeline.py
```

**Outputs:**
- `data/processed/crystal_dataset.csv`: Final processed dataset with fingerprints.
- `data/validation/fingerprint_check.json`: Validation of fingerprint dimensions and nulls.

### 2. Model Training and Evaluation

Trains models, calculates baselines, and evaluates performance with scaffold splitting.

```bash
python code/modeling/train.py
python code/modeling/evaluate.py
```

**Outputs:**
- `data/models/`: Trained model artifacts (`.pkl`).
- `data/results/`: Baseline metrics, model metrics, and success criterion checks.
- `data/validation/scaffold_overlap_report.json`: Verification of zero scaffold overlap.

### 3. Interpretability Analysis

Generates SHAP values and maps top features to chemical substructures.

```bash
python code/analysis/interpret.py
python code/analysis/generate_report.py
```

**Outputs:**
- `data/results/feature_importance_report.md`: Human-readable report of predictive substructures.
- `data/results/shap_analysis.json`: Detailed SHAP values.

### 4. End-to-End Execution

Run the full pipeline (Ingestion + Training + Analysis) to verify the 6-hour SC-004 limit.

```bash
python code/ingestion/run_pipeline.py && \
python code/modeling/train.py && \
python code/modeling/evaluate.py && \
python code/analysis/interpret.py && \
python code/analysis/generate_report.py
```

## Project Structure

```text
PROJ-030-predicting-crystal-structures-from-molec/
├── code/
│ ├── ingestion/ # Data loading, parsing, fingerprinting
│ ├── modeling/ # Training, splitting, evaluation
│ ├── analysis/ # Interpretability, power analysis
│ ├── config.py # Configuration management
│ ├── logging_config.py# Logging infrastructure
│ └──...
├── data/
│ ├── processed/ # Intermediate and final datasets
│ ├── models/ # Trained model artifacts
│ ├── results/ # Metrics and analysis outputs
│ └── validation/ # Validation reports
├── tests/ # Unit and integration tests
├── specs/ # Feature specifications and design docs
├── logs/ # Execution logs
└── README.md
```

## Key Design Decisions

- **Polymorphism Handling:** Each unique (SMILES, Space Group) pair is treated as a distinct sample to capture polymorphic variations.
- **Scaffold Splitting:** Uses Bemis-Murcko scaffolds to ensure zero structural overlap between training and test sets, preventing data leakage.
- **Error Handling:** The pipeline fails loudly on data fetch errors or memory issues; no synthetic data fallbacks are used (Constitution Principle II & III).
- **Power Analysis:** Sample size requirements are calculated based on the actual dataset size and stored in the config.

## Contributing

1. Ensure all new code passes `ruff` and `black` checks.
2. Add unit tests for new functionality in `tests/`.
3. Update `tasks.md` if new tasks are identified.

## License

[Insert License Here]