# PROJ-451: Predicting the Glass Forming Region of Metallic Glass Alloys

This project implements a machine learning pipeline to predict the glass-forming region of metallic glass alloys using atomic-scale descriptors and classification models.

## Overview

- **Objective**: Identify glass-forming regions in alloy composition space.
- **Methodology**: Extract atomic descriptors (e.g., atomic size mismatch, mixing enthalpy) and train ML classifiers (Random Forest, XGBoost).
- **Data Sources**: Materials Project API (v3) and Science Advances dataset.

## Structure

- `code/`: Source code for data ingestion, feature engineering, and model training.
- `data/`: Raw and processed datasets.
- `models/`: Trained model artifacts and evaluation scripts.
- `tests/`: Unit and integration tests.
- `specs/`: Feature specifications and design documents.

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment variables (e.g., `MATERIALS_PROJECT_API_KEY`).
3. Run data ingestion: `python code/main.py`
4. Train models: `python models/train.py`

## License

MIT License
