# Quickstart: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

## Prerequisites

- Python 3.11+
- `pip`
- Sufficient RAM available (for bootstrapping)
- Substantial disk space

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-138-the-effects-of-gamified-habit-tracking-o
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Execution

### 1. Generate Synthetic Data & Consent
Run the data generation script to create the synthetic dataset and the required consent artifact.
```bash
python code/data/synthetic_generator.py
```
*Output*: `data/raw/synthetic_data.csv`, `data/consent/consent_record.json`

### 2. Ingest and Validate
Run the ingestion pipeline to validate the data and aggregate daily logs into weekly bins.
```bash
python code/data/ingestion.py
```
*Output*: `data/processed/merged_data.csv`

### 3. Run Analysis
Execute the full modeling and robustness pipeline.
```bash
python code/analysis/modeling.py
python code/analysis/robustness.py
```

### 4. Generate Report
Generate the final HTML report.
```bash
python code/reports/generate_report.py
```
*Output*: `data/reports/final_analysis.html`

### 5. Verify
Run the quickstart validation script to ensure all artifacts exist.
```bash
bash quickstart.sh
```
*Expected Exit Code*: 0
*Expected Output*: "All checks passed. Data and reports generated successfully."

## Troubleshooting

- **Error: "Data Insufficiency"**: The generated dataset has a limited number of users. Check `synthetic_generator.py` seed or parameters.
- **Error: "Missing Consent"**: The `data/consent/` directory is empty. Ensure `synthetic_generator.py` ran successfully.
- **Error: "VIF > 5"**: The model detected high collinearity. `need_for_achievement` will be dropped automatically. Check `code/analysis/modeling.py` logs.
- **Error: "Insufficient Events"**: dropout events detected. Survival analysis will be skipped; descriptive stats will be reported.
