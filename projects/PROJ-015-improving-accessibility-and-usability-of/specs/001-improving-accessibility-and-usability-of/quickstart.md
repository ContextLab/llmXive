# Quickstart: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

## 1. Prerequisites
- Python 3.11+
- `pip`
- A modern web browser
- (Optional) Docker (for containerized execution)

## 2. Installation

1. **Clone the repository** (or navigate to the project directory):
 ```bash
 cd projects/PROJ-015-improving-accessibility-usability-of
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` includes `streamlit`, `scipy`, `pandas`, `seaborn`, `pyyaml`, `statsmodels`.*

## 3. Running the Simulator (Data Collection)

To collect data from participants, launch the Streamlit simulator:

```bash
streamlit run code/app.py
```

- The app will open in your browser (default: `).
- **Instruction**: Recruit participants via disability advocacy groups. Provide them with the URL.
- **Data Output**: Session data is saved to `data/raw/` automatically as participants complete tasks.
- **Counterbalancing**: The app automatically assigns the order (Traditional->Explainable or vice versa) based on a Latin Square logic.
- **Pilot Study**: Run a pilot with N=5 participants first to validate task difficulty.

## 4. Running the Analysis Pipeline

Once you have collected data (minimum N=30 sessions recommended), run the analysis:

```bash
python code/analysis.py
```

This script will:
1. Load and validate all sessions in `data/raw/`.
2. Filter out incomplete sessions (including those with missing SUS items).
3. Compute SUS scores and metrics (including explanation engagement time).
4. Check normality (Shapiro-Wilk) and run Repeated Measures ANOVA or Friedman Test.
5. Apply Holm-Bonferroni correction.
6. Compute observed power.
7. Generate `data/processed/metrics_summary.csv`.
8. Generate `figures/completion_time.png`, `figures/error_count.png`, `figures/sus_score.png`, `figures/explanation_engagement.png`.
9. Generate `docs/power_report.md`.

## 5. Running Tests

To ensure the pipeline is working correctly (including validation logic):

```bash
pytest tests/ -v
```

- **Note**: Unit tests may use synthetic data fixtures to verify logic, but the final analysis must use real data from `data/raw/`.

## 6. Reproducibility Check

To verify reproducibility (Constitution Principle I):

1. Delete `data/processed/`, `figures/`, and `docs/power_report.md`.
2. Re-run `python code/analysis.py`.
3. Verify that the output files are identical (checksums match).

## 7. Troubleshooting

- **Missing Dependencies**: Ensure you activated the virtual environment before running commands.
- **Port Conflict**: If `streamlit run` fails due to port 8501, use `streamlit run code/app.py --server.port 8502`.
- **Validation Errors**: If the pipeline fails, check `data/raw/invalid_sessions.json` to see which sessions were rejected and why.
- **Power Warning**: If the power report indicates low power (<0.8), the study may need more participants.
- **Non-Normal Data**: If Shapiro-Wilk indicates non-normality, the script will automatically switch to the Friedman Test and log the change.