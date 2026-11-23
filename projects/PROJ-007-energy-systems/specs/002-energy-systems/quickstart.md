# Quickstart: Developing Novel Solutions to Address Energy Inequity in Low-Income Communities

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment for testing)

## Installation

1. Clone the repository:
 ```bash
 git clone
 cd energy-inequity-project
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. Verify dataset availability (optional, skips download):
 ```bash
 python -c "from src.data.ingest import download_datasets; download_datasets()"
 ```

## Running the Pipeline

### Full Pipeline (Default)
```bash
python src/cli/main.py
```
This runs:
1. Data ingestion and preprocessing (including winsorization/log-transformation)
2. PSM (with balance validation)
3. ATT estimation (or Graceful Halt if PSM fails)
4. Sensitivity sweep
5. Output generation

### Specific Steps
- **Ingest only**: `python src/cli/main.py --step ingest`
- **PSM only**: `python src/cli/main.py --step psm`
- **ATT only**: `python src/cli/main.py --step att`
- **Sensitivity only**: `python src/cli/main.py --step sensitivity`

### Output Files
- `data/outputs/att_results.json`: Primary causal estimate (includes `balance_status`, `placebo_test_result`, `methodology_used`)
- `data/outputs/sensitivity_report.md`: Caliper sweep results (table and plot)
- `data/outputs/balance_report.csv`: Covariate balance (SMD)

## Testing

Run unit and contract tests:
```bash
pytest tests/
```

Run PII scan (via CI):
```bash
detect-secrets scan --baseline.secrets.baseline
```

## Troubleshooting

- **Power Limitation**: If the pipeline halts with "Insufficient sample size", check `data/processed/merged_low_income.csv` for the number of adopters. If < 50, consider relaxing the low-income filter.
- **Balance Failure**: If PSM fails to achieve SMD ≤ 0.1, the system halts with "Causal Identification Failure". **DiD fallback is not attempted** due to cross-sectional data.
- **Placebo Test Failure**: If p < 0.05, the system halts with "Unconfoundedness Violation".
- **Memory Error**: If the dataset exceeds 7 GB RAM, ensure `streaming=True` is enabled in `src/data/ingest.py`.
- **Ecological Fallacy**: Note that `home_value` is a tract-level proxy. Interpret results with caution.