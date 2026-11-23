# Evaluating the Correlation Between Compositional Features and Predicted Formation Energy

## Overview
This project evaluates the correlation between compositional features and predicted formation energy in inorganic materials.

## Dependencies
- pymatgen
- scikit-learn
- pandas
- numpy
- matplotlib
- pyyaml
- mpdsapi
- shap
- eli
- statsmodels
- psutil

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
# Run the full pipeline
python code/main.py

# Or run individual steps
python code/ingest.py
python code/descriptors.py
python code/train.py
python code/evaluate.py
python code/importance.py
python code/plots.py
```

## Environment Setup
- Set `MPDS_API_KEY` in environment variables for data download.
- Ensure `data/` directory structure is created (run `python code/setup_structure.py` if needed).

## Output Artifacts
- `data/processed/computed_descriptors.csv`
- `data/evaluation/model_metrics.json`
- `data/evaluation/feature_ranking.json`
- `data/evaluation/permutation_importance.json`
- `data/evaluation/vif_scores.json`
- `data/evaluation/ale_*.png`
