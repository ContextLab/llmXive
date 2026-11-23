# Quickstart Guide: Visual Aesthetics & Credibility Study

This guide outlines the steps to run the full pipeline for the "Influence of Visual Aesthetics on Perceived Credibility" study.

## Prerequisites

- Python 3.10+
- `pip` and `venv`

## 1. Setup Environment

```bash
# Create virtual environment
python -m venv.venv
source.venv/bin/activate # On Windows:.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure IRB Consent

**CRITICAL**: Before running the survey in production, you must manually insert the IRB-approved text.

1. Open `data/consent/irb_approved.txt`.
2. Replace the placeholder `<<INSERT_IRB_APPROVED_TEXT_HERE>>` with the actual approved text.
3. Set the environment variable `IRB_PROTOCOL_ID` to your protocol ID.
 ```bash
 export IRB_PROTOCOL_ID="YOUR_PROTOCOL_ID_HERE"
 ```

## 3. Data Collection (Survey)

Run the Streamlit survey app:

```bash
streamlit run code/survey/app.py
```

*Note: This step requires manual user interaction. To test the data pipeline without collecting real data, proceed to Step 4 with mock data.*

## 4. Generate Mock Data (Optional for Testing Pipeline)

If you have not collected real data yet, generate mock data to test the analysis pipeline:

```bash
python code/utils/generate_mock_data.py
```

This creates `data/raw/submissions.csv` with 250 synthetic participants.

## 5. Preprocessing

Clean the data and prepare it for analysis:

```bash
python code/analysis/01_preprocess.py
```

This generates `data/processed/cleaned_data.csv`.

## 6. Statistical Analysis

Run the ANOVA and pairwise tests:

```bash
python code/analysis/01_anova.py --input../../data/raw/cleaned_data.csv --output../../data/processed/anova_results.json
python code/analysis/02_pairwise.py --input../../data/raw/cleaned_data.csv --output../../data/processed/pairwise_results.json
```

*(Note: The input path for these scripts expects the cleaned data. Adjust paths if your data is in raw format.)*

## 7. Mixed Effects Model

Run the robustness check:

```bash
python code/analysis/04_mixed_effects.py
```

## 8. Duplicate Audit (T022h)

Run the post-hoc duplicate detection:

```bash
python code/analysis/07_duplicate_audit.py
```

This reads `data/raw/submissions.csv` and writes flagged rows to `data/raw/duplicate_audit.csv`.

## 9. Power Analysis

```bash
python code/analysis/06_power_analysis.py
```

## 10. Reporting

Generate the final summary:

```bash
python code/analysis/03_report.py
```