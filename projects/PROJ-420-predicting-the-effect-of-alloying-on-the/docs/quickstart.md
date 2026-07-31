# Quickstart Guide: Predicting Poisson's Ratio of Aluminum Alloys

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Execution

Run the full pipeline to extract data, clean it, train the model, and generate the report:

```bash
python code/main.py
```

### Individual Steps

- **Data Extraction**:
 ```bash
 python code/data/download.py
 ```
 *Produces*: `data/raw/openml_aluminum.json`

- **Data Cleaning**:
 ```bash
 python code/data/clean.py
 ```
 *Produces*: `data/processed/filtered_alloys.csv`

- **Modeling & Analysis**:
 (Included in `main.py`)

## Output Artifacts

- `data/processed/filtered_alloys.csv`: Cleaned dataset.
- `results/final_report.md`: Final analysis report.
- `results/metrics.json`: Model performance metrics.