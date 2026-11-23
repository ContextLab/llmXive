# Predicting Avian Foraging Behavior from Public eBird Data and Land Cover Maps

## Project Overview
This project implements a machine learning pipeline to predict avian foraging guilds using public eBird observation data merged with National Land Cover Database (NLCD) land cover maps.

## Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

## Installation
1. Clone the repository
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Pipeline
The pipeline consists of the following stages:
1. **Data Download**: Fetch eBird EBD records and NLCD land cover data
2. **Preprocessing**: Filter species, merge datasets, compute land cover proportions
3. **Model Training**: Train a Random Forest classifier
4. **Evaluation**: Assess model performance with stratified permutation tests
5. **Visualization**: Generate confusion matrices, feature importance plots, and habitat maps

## Running the Pipeline
Execute the full pipeline:
```bash
bash run_pipeline.sh
```

Or run individual stages:
```bash
python code/data/download_ebd.py
python code/data/download_nlcd.py
python code/data/preprocess.py
python code/models/train.py
python code/models/evaluate.py
python code/viz/plot_confusion.py
```

## Output Artifacts
All generated artifacts are stored in the `data/` and `docs/` directories:
- `data/raw/`: Raw downloaded datasets
- `data/processed/`: Cleaned and merged datasets
- `data/models/`: Trained models and metrics
- `docs/results/`: Visualizations and reports

## License
This project is for research purposes only.
