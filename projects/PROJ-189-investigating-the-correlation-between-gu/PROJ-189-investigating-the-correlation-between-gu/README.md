# Gut Microbiome and Cognitive Decline Analysis

## Project Description

This project investigates the correlation between gut microbiome composition and cognitive decline in older adults. We integrate 16S rRNA sequencing data from the American Gut Project (AGP) with cognitive and demographic metadata from the Health and Retirement Study (HRS).

The analysis pipeline includes:
1. **Data Acquisition**: Fetching raw taxonomic data from AGP and cognitive metadata from HRS.
2. **Preprocessing**: Merging datasets by participant ID, filtering for age ≥ 60, rarefaction to uniform sequencing depth, and collapsing to genus-level relative abundances.
3. **Correlation Analysis**: Computing Spearman rank correlations between genus-level abundances and cognitive scores with FDR correction.
4. **Predictive Modeling**: Training Random Forest regressors with nested cross-validation to predict cognitive scores from microbiome features.

## Setup Instructions

1. Clone the repository and navigate to the project directory.
2. Create and activate a Python 3.11 virtual environment:
 ```bash
 python -m venv venv && source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```
4. Configure environment variables by copying `code/.env.example` to `code/.env` and filling in the required values.

## Execution

Run the full pipeline:
```bash
python code/01_data_ingestion.py
python code/02_preprocessing.py
python code/03_correlation_analysis.py
python code/04_predictive_modeling.py
```

## Project Structure

```
PROJ-189-investigating-the-correlation-between-gu/
├── data/
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Cleaned and transformed data
│ └── models/ # Trained model artifacts
├── code/
│ ├── utils/ # Utility modules (data_fetchers, logging, resource_guard)
│ ├── 01_data_ingestion.py
│ ├── 02_preprocessing.py
│ ├── 03_correlation_analysis.py
│ ├── 04_predictive_modeling.py
│ ├── config.py
│ └──...
├── tests/
│ ├── unit/
│ ├── integration/
│ └── contract/
└── docs/
```

## License

This project is for research purposes only.