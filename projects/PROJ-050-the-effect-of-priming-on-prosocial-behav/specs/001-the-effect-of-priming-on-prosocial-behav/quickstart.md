# Quickstart: The Effect of Priming on Prosocial Behavior

## Prerequisites

*   Python 3.11+
*   `pip`
*   Internet connection (for API access and package installation)

## Installation

1.  **Clone the repository** (if not already done).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline is executed in sequential steps.

### Step 1: Ingest and Anonymize
Fetches data from Hugging Face, classifies threads, and anonymizes users.
```bash
python code/01_ingest.py
```
*Outputs*: `data/raw/hf_dump.jsonl`, `data/processed/anonymized.csv`, `data/processed/raw_counts.json`.

### Step 2: Score Comments
Computes VADER scores and prosocial intent counts (using distinct lexicon).
```bash
python code/02_score.py
```
*Outputs*: `data/processed/scored.csv`.

### Step 3: Validate (Human Annotation)
Generates the sample for human annotation and computes Kappa (requires `data/processed/annotations.csv` to be populated by real human annotators).
```bash
python code/03_validate.py
```
*Outputs*: `data/processed/validation_report.json`.

### Step 4: Statistical Analysis
Fits the Linear Mixed Model (without `user_tenure`) and outputs results.
```bash
python code/04_analyze.py
```
*Outputs*: `data/processed/model_results.json`, `figures/priming_effect.png`.

## Testing

Run the unit tests to ensure logic correctness (including T011 and T012):
```bash
pytest tests/unit/
```

## Troubleshooting

*   **API Rate Limits**: If `01_ingest.py` fails, wait 60 seconds and retry. The script includes built-in retry logic.
*   **Convergence Failure**: If the LMM fails to converge, check `code/04_analyze.py` for the fallback optimizer settings.
*   **Missing Data**: If N < 4,000 per group, the script will log a warning and proceed with available data.
*   **User Tenure**: Note that `user_tenure` is not included in the model due to data unavailability.
