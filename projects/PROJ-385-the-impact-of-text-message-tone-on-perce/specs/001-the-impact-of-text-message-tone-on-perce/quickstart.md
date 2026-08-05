# Quickstart: The Impact of Text Message Tone on Perceived Emotional Support

## Prerequisites

- Python 3.11+
- `pip`
- Access to Prolific (for data collection)
- GitHub Actions (for automated testing)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-385-the-impact-of-text-message-tone-on-perce
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Dependencies include: `pandas`, `numpy`, `scipy`, `statsmodels`, `pytest`, `pyyaml`.*

## Workflow

### Step 1: Generate Stimuli
Run the script to create the text message variants.
```bash
python code/01_generate_stimuli.py
```
*Output*: `data/raw/stimuli.csv`

### Step 2: Validate Stimuli (Contract Test)
Ensure the generated stimuli meet the schema requirements.
```bash
pytest tests/contract/test_stimuli_schema.py
```

### Step 3: Collect Real Data (External)
*This step requires external action.*
1.  Upload the `stimuli.csv` to your Prolific survey.
2.  Recruit N≥60 participants.
3.  Download the results and save as `data/raw/real_ratings.csv`.
4.  Ensure the CSV contains `participant_id`, `stimulus_id`, `relationship_context`, and `rating_score`.

### Step 4: Clean Data
Run the cleaning script to detect straight-lining and handle missing values.
```bash
python code/04_clean_data.py
```
*Output*: `data/processed/cleaned_ratings.csv`

### Step 5: Run Primary Analysis
Execute the Linear Mixed-Effects Model.
```bash
python code/05_run_lmm.py
```
*Output*: `data/processed/lmm_results.json` (contains estimates, p-values, effect sizes).

### Step 6: Run Sensitivity Analysis
Test robustness with AIC/BIC model comparison.
```bash
python code/06_sensitivity_analysis.py
```
*Output*: `data/processed/sensitivity_report.json`

### Step 7: Verify All Tests
Run the full test suite.
```bash
pytest
```

## Troubleshooting

- **Missing `data/raw/real_ratings.csv`**: The analysis scripts will fail. Ensure you have collected real data from Prolific. Do not use simulated data for the primary analysis.
- **Straight-lining Detected**: If many participants are flagged, check your survey instructions.
- **LMM Convergence Issues**: If the model fails to converge, check for perfect separation or insufficient data per random effect level.

## Data Access

- **Raw Stimuli**: `data/raw/stimuli.csv`
- **Raw Ratings**: `data/raw/real_ratings.csv` (Requires real collection)
- **Cleaned Data**: `data/processed/cleaned_ratings.csv`
- **Consent Logs**: `data/consent/` (Access controlled, PII stripped)