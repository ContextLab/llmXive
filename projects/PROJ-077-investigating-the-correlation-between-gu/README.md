# PROJ-077: Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

## Getting Started
## Prerequisites
- Python 3.11+
- UK Biobank access credentials

## Data Access
1. Apply for UK Biobank access at https://www.ukbiobank.ac.uk/
2. Download microbiome, cognitive, and dietary data.
3. Place files in `data/raw/` with names: `microbiome.csv`, `cognitive.csv`, `dietary.csv`.

## Installation
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`

## Running the Pipeline
Execute the main pipeline script:
```bash
python code/main.py
```

## Expected Outputs
- `data/processed/cleaned_data.csv`: Preprocessed dataset
- `data/processed/correlation_results.csv`: Spearman correlation results
- `data/processed/regression_results.csv`: Multivariate regression results
- `data/processed/plots/`: Visualization plots (scatter plots, histograms)
- `logs/provenance.log`: Execution log with data provenance information