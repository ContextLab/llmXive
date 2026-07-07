# Quickstart Guide

## Prerequisites

- Python 3.11 or higher
- `pip` package manager
- (Optional) `venv` or `conda` for environment management

## 1. Environment Setup

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 2. Data Preparation

### Option A: Use Synthetic Data (Default for Testing)

If no real dataset is available, the pipeline can generate synthetic data that mimics the expected structure.

1. **Consent Verification**:
 The pipeline requires a consent artifact before processing. If using synthetic data, run:

 ```bash
 python code/data/validation.py
 ```

 This will automatically generate a `data/consent/synthetic_consent_record.json` if one does not exist, stating that the data is synthetic and approved for research.

2. **Generate Synthetic Dataset**:
 Execute the synthetic data generator:

 ```bash
 python code/data/synthetic_generator.py
 ```

 This produces `data/raw/synthetic_data.csv` with 100 users (70 gamified, 30 non-gamified), including personality scores and adherence logs. [UNRESOLVED-CLAIM: c_18209dd4 — status=not_enough_info]

### Option B: Use Real Data

1. Place your raw CSV file (e.g., `habitica_data.csv`) in `data/raw/`.
2. Ensure the file contains required columns: `User_ID`, `Gamified`, `Adherence`, `Conscientiousness`, `Need_for_Achievement`, `Date`, `Event_Type`.
3. Ensure a valid consent record exists in `data/consent/`. If using real data without a record, the pipeline will halt.

## 3. Run the Pipeline

The pipeline consists of sequential stages. You can run the full analysis or individual components.

### Full Analysis Pipeline

To run the entire workflow (Ingestion -> Aggregation -> Modeling -> Survival -> Robustness -> Report):

```bash
python code/reports/generate_report.py
```

This script orchestrates the following steps:
1. **Data Ingestion & Validation**: Loads data, checks consent, validates schema.
2. **Weekly Aggregation**: Converts daily logs to weekly adherence flags.
3. **Modeling**: Fits mixed-effects logistic regression with interaction terms.
4. **Survival Analysis**: Analyzes dropout events using Kaplan-Meier and Cox models.
5. **Robustness Check**: Performs bootstrapping for confidence intervals.
6. **Report Generation**: Creates `data/reports/final_analysis.html`.

### Individual Stages

- **Ingestion**: `python code/data/ingestion.py`
- **Aggregation**: `python code/data/aggregation.py`
- **Modeling**: `python code/analysis/modeling.py`
- **Survival**: `python code/analysis/survival.py`
- **Robustness**: `python code/analysis/robustness.py`
- **Report**: `python code/reports/generate_report.py`

## 4. Verify Outputs

After completion, verify the following artifacts:

- `data/processed/merged_data.csv`: Aggregated dataset.
- `data/reports/final_analysis.html`: Final report with visualizations and statistical tables.
- `logs/pipeline.log`: Execution logs for debugging.
- `state.yaml`: Artifact hashes for version control.

## 5. Running Tests

To validate the implementation:

```bash
pytest code/tests/ -v
```

This runs contract and integration tests for ingestion, aggregation, modeling, survival, and report generation.

## Troubleshooting

- **Missing Consent**: If the pipeline halts with "Missing Consent", check `data/consent/`. If using synthetic data, ensure `synthetic_consent_record.json` is generated.
- **Data Insufficiency**: If the non-gamified group has fewer than 30 users, the pipeline will halt. [UNRESOLVED-CLAIM: c_33af73c3 — status=not_enough_info] This is enforced to ensure statistical power.
- **Model Convergence**: If mixed-effects models fail to converge, {{claim:c_1b4f2672}} (Wikidata Q113106917, https://www.wikidata.org/wiki/Q113106917)

## Support

For issues or questions, refer to the project specification in `specs/` or contact the research team.