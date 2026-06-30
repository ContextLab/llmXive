# Quickstart: The Influence of Metacognitive Awareness on Reality Testing

## Prerequisites

- Python 3.11+
- Git
- Sufficient free disk space
- Internet access (for dataset download)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-179-the-influence-of-metacognitive-awareness
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### 1. Download Dataset
```bash
python code/download.py
```
This fetches an OpenNeuro dataset to `data/raw/`.  
**Note**: If the dataset is unavailable, the script will exit with an error.

### 2. Validate Data
```bash
python code/validate_data.py
```
**CRITICAL**: This step checks if the dataset contains the required fields (`confidence_rating`, `source_label`).
- **If fields are missing**: The script exits with a `DataUnavailableError`. The project is **BLOCKED**.
- **If fields are present**: The script proceeds to the next step.

### 3. Preprocess Data
```bash
python code/preprocess.py
```
Generates:
- `data/derived/trial_summary.csv`
- `data/derived/confidence_summary.csv` (Type-2 AUC)
- `data/derived/accuracy_summary.csv` (d' on held-out set)
- `data/processed/participant_level.csv`

### 4. Run Analysis
```bash
python code/analysis.py
```
Generates:
- `data/processed/analysis_results.json`
- `report.md` (in the root of the feature directory)

### 5. Validate Results
```bash
pytest tests/
```

## Output

- **report.md**: Contains correlation coefficients, regression results, confidence intervals, and assumption checks.
- **data/processed/analysis_results.json**: Machine-readable statistical outputs.

## Troubleshooting

- **Dataset not found**: Ensure internet access and correct OpenNeuro ID. No fallback dataset is available.
- **Data Validation Failed**: The dataset (ds003386) does not contain the required behavioral data. The project is **blocked**. A valid dataset must be identified.
- **Runtime exceeds 6 hours**: The pipeline will automatically reduce bootstrap resamples to 500 and log a warning.
- **Working memory missing**: The regression will exclude this covariate and report the adjusted model.