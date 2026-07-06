# Quick Start Guide

## Prerequisites

- Python 3.11+
- pip

## Installation

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

Execute the full pipeline from data extraction to final report:

```bash
python -m code.main
```

## Output Artifacts

- `data/processed/filtered_alloys.csv`: Cleaned dataset
- `models/rf_model.pkl`: Trained Random Forest model
- `docs/outputs/model_metrics.json`: Performance metrics
- `docs/outputs/final_report.md`: Comprehensive analysis report
