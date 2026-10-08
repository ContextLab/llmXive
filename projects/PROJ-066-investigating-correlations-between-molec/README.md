# PROJ-066: Investigating Correlations Between Molecular Descriptors and Drug-Likeness Scores

## Project Overview
This project aims to download, process, and analyze molecular data from the ChEMBL database to investigate correlations between molecular descriptors and drug-likeness scores. The pipeline includes data acquisition, preprocessing, model training, and evaluation.

## Quickstart Instructions
1. **Setup Environment**:
 ```bash
 pip install -r code/requirements.txt
 ```
2. **Run Data Download (T009)**:
 ```bash
 python code/data/download.py
 ```
3. **Run Preprocessing Pipeline (T010-T015)**:
 ```bash
 python code/data/preprocess.py
 ```
4. **Train Models (T017-T020)**:
 ```bash
 python code/models/train.py
 ```
5. **Evaluate Models (T022-T026)**:
 ```bash
 python code/models/evaluate.py
 ```

## Directory Structure
- `data/raw/`: Raw downloaded data (e.g., ChEMBL database)
- `data/processed/`: Processed data ready for modeling
- `code/`: Source code for data processing, modeling, and evaluation
- `tests/`: Unit and integration tests
- `state/`: Project state tracking and artifact hashes

## Dependencies
- Python 3.10+
- RDKit
- scikit-learn
- pandas
- PyYAML
- psutil
