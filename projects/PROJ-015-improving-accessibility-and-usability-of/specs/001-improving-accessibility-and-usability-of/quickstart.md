# Quickstart: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

## Prerequisites
- Python 3.11+
- pip

## 1. Installation
Clone the repository and install dependencies:
```bash
pip install -r code/requirements.txt
```
*Note: `requirements.txt` includes `streamlit`, `pandas`, `scipy`, `statsmodels`, `pyyaml`.*

## 2. Running the Simulator (Data Collection)
To collect human participant data:
```bash
cd code/simulator
streamlit run app.py
```
- Open the URL provided in the terminal.
- Participants will complete tasks and fill out the SUS survey.
- Data is saved to `data/raw/` as JSON files.

## 3. Running the Analysis Pipeline
To clean data and perform statistical analysis:
```bash
cd code
python main.py
```
This script performs:
1. **Validation**: Checks raw JSON against `contracts/session.schema.yaml`.
2. **Cleaning**: Filters incomplete sessions, imputes SUS scores (FR-005).
3. **Statistics**: Runs Repeated Measures ANOVA and Holm-Bonferroni correction (FR-002).
4. **Power Analysis**: Computes power and generates `power_report.md` (FR-006).

## 4. Verifying Reproducibility
To ensure the pipeline is reproducible (NFR-001):
```bash
# Run the CI workflow locally (requires act or similar, or just check the script)
python code/utils/checksum.py --verify
```
This verifies that all processed files match their recorded checksums.

## 5. Viewing Results
- **Cleaned Data**: `data/processed/cleaned_sessions.csv`
- **Metrics Summary**: `data/processed/metrics_summary.csv`
- **Statistical Report**: `data/processed/power_report.md`
- **Visualizations**: Generated in `data/figures/` (if applicable).

## 6. Troubleshooting
- **Missing Data**: If `cleaned_sessions.csv` is empty, check `data/raw` for valid sessions. Ensure participants completed the survey.
- **Schema Errors**: If validation fails, check `contracts/session.schema.yaml` and ensure raw JSON matches.
- **Power Issues**: If power < 0.8, the report will indicate that N=30 was insufficient for the observed effect size.
