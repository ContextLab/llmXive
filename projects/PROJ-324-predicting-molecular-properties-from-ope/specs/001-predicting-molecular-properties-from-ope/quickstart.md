# Quickstart: Molecular Property Prediction Pipeline

## Prerequisites

- Python 3.10+
- Open Babel installed (CLI: `obabel`)
- Git

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd PROJ-324-predicting-molecular-properties-from-ope
 ```

2. **Create virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

4. **Install Open Babel** (if not already installed):
 - Ubuntu/Debian: `sudo apt-get install openbabel`
 - macOS: `brew install open-babel`
 - Windows: Download from https://openbabel.org/

## Directory Structure

```text
projects/PROJ-324-predicting-molecular-properties-from-ope/
├── code/
│ ├── data/
│ │ ├── download.py
│ │ ├── preprocess.py
│ │ └── fingerprint.py
│ ├── models/
│ │ ├── baseline.py
│ │ └── rf.py
│ ├── analysis/
│ │ ├── stats.py
│ │ └── explainability.py
│ └── main.py
├── data/
│ ├── raw/
│ ├── processed/
│ └── derived/
├── tests/
├── requirements.txt
├── pyproject.toml
└──.ruff.toml
```

## Running the Pipeline

1. **Download Data**:
 ```bash
 python code/data/download.py
 ```
 This fetches [deferred] molecules from PubChem and saves them to `data/raw/`.

2. **Preprocess Data**:
 ```bash
 python code/data/preprocess.py
 ```
 This cleans data, handles missing values, and generates `data/derived/data_quality_report.csv`.

3. **Generate Fingerprints**:
 ```bash
 python code/data/fingerprint.py
 ```
 This generates MACCS, ECFP4, and FP2 fingerprints and saves them to `data/processed/`.

4. **Train Baseline Model**:
 ```bash
 python code/models/baseline.py
 ```
 This computes Crippen predictions and saves them to `data/derived/baseline_predictions.csv`.

5. **Train Random Forest Model**:
 ```bash
 python code/models/rf.py
 ```
 This trains the RF model with nested CV and saves predictions to `data/derived/`.

6. **Run Analysis**:
 ```bash
 python code/analysis/stats.py
 ```
 This computes metrics, performs Wilcoxon test, and generates plots.

7. **Run Explainability**:
 ```bash
 python code/analysis/explainability.py
 ```
 This computes SHAP values and maps them to substructures.

## Testing

Run unit and integration tests:
```bash
pytest tests/
```

## Linting & Formatting

Check code style:
```bash
ruff check code/
black --check code/
```

Format code:
```bash
black code/
ruff check --fix code/
```

## Troubleshooting

- **Open Babel not found**: Ensure `obabel` is in your PATH.
- **PubChem API errors**: Check network connectivity; PubChem may rate-limit requests.
- **Memory errors**: Reduce the number of molecules or features in `code/models/rf.py`.
