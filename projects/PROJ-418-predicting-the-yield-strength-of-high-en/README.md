# Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

This project implements an automated scientific pipeline to predict the yield strength of High-Entropy Alloys (HEAs) using compositional descriptors (δ, Δχ, VEC, mixing entropy, melting temperature variance).

## ⚠️ CRITICAL: Data Source Requirement

**This pipeline does NOT download data automatically.** It requires a **user-provided dataset** to function.

### How to Provide the Dataset

1. Obtain the raw HEA yield strength dataset (CSV format).
2. Place the file at the exact path: `data/raw/heas_raw.csv` relative to the project root.
3. Ensure the file contains the required columns as defined in `contracts/dataset.schema.yaml` (typically: `composition`, `yield_strength`, `unit`, `phase`, `temperature`).

### What Happens if the File is Missing?

If `data/raw/heas_raw.csv` is missing or invalid, the pipeline will **abort immediately** with a clear error message. **No synthetic data will be generated.**

You will see an error similar to:

```
FileNotFoundError: Dataset file not found: data/raw/heas_raw.csv
The pipeline requires a user-provided dataset. Please place the raw CSV file at the expected path and re-run.
```

Or, if the file exists but fails schema validation:

```
ValidationError: Dataset validation failed.
Missing required fields: ['phase', 'temperature']
Please ensure the CSV conforms to the schema defined in contracts/dataset.schema.yaml.
```

## Installation

1. Clone the repository.
2. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Quick Start

1. **Verify Data**: Ensure `data/raw/heas_raw.csv` exists.
2. **Run the Pipeline**:
 ```bash
 python code/main.py
 ```
3. **Check Outputs**:
 - Processed data: `data/processed/hea_descriptors.csv`
 - Metrics: `output/metrics.json`
 - Report: `output/report.md`
 - Plots: `output/plots/`

### Step-by-Step Execution

The pipeline consists of the following stages, executed sequentially by `main.py`:

1. **Data Acquisition**: Validates the user-provided CSV (`code/data/download.py`).
2. **Preprocessing**: Filters single-phase, room-temperature alloys; normalizes units (`code/data/preprocess.py`).
3. **Descriptor Engineering**: Calculates δ, Δχ, VEC, entropy, melting variance (`code/data/descriptors.py`).
4. **Model Training**: Trains Random Forest, Gradient Boosting, and Linear Regression (`code/models/train.py`).
5. **Evaluation**: Computes metrics, permutation importance, bootstrap CI (`code/models/evaluate.py`).
6. **Reporting**: Generates the final markdown report with disclaimers (`code/models/report_generator.py`).

## Project Structure

```
.
├── code/
│ ├── data/
│ │ ├── download.py # Data validation (user-provided)
│ │ ├── preprocess.py # Cleaning and filtering
│ │ ├── descriptors.py # Feature engineering
│ │ └── pipeline.py # Orchestration
│ ├── models/
│ │ ├── train.py # Model training
│ │ ├── evaluate.py # Metrics and validation
│ │ └── report_generator.py
│ └── utils/
│ ├── logging.py
│ ├── config.py
│ └──...
├── data/
│ ├── raw/
│ │ └── heas_raw.csv # <--- USER MUST PROVIDE THIS FILE
│ └── processed/
├── output/
│ ├── metrics.json
│ ├── report.md
│ └── plots/
├── contracts/ # Schema definitions
├── tests/
├── requirements.txt
└── README.md
```

## Dependencies

- Python >= 3.8
- pandas, numpy, scikit-learn, matplotlib, seaborn
- pyyaml, joblib

See `requirements.txt` for the full list.

## Disclaimer

This project is for research purposes only. All plots and reports include a mandatory disclaimer stating that the analysis is associational and does not imply causal inference.

## License

[Insert License Here]