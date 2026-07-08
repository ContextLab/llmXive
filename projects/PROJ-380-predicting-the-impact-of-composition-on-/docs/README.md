# PROJ-380: Predicting the Impact of Composition on Shear Modulus

## Overview
This project implements a machine learning pipeline to predict the shear modulus of Bulk Metallic Glasses (BMGs) based on their chemical composition.

## Structure
- `code/`: Source code for data ingestion, feature engineering, and modeling.
- `data/`: Raw, processed, and artifact data.
- `tests/`: Unit and integration tests.
- `docs/`: Documentation.
- `state/`: Provenance and state tracking.

## Usage
Run the setup script to initialize directories:
```bash
python code/setup_data_dirs.py
```

Run the full pipeline via Make (see Makefile).
