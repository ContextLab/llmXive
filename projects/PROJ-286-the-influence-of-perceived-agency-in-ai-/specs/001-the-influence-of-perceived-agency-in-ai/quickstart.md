# Quickstart: The Influence of Perceived Agency in AI Interactions on Trust

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git (for version control)
- A Prolific/MTurk account (for participant recruitment)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd projects/PROJ-286-the-influence-of-perceived-agency-in-ai-/
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

   **requirements.txt** (pinned versions):
   ```text
   streamlit==1.32.0
   pandas==2.2.0
   numpy==1.26.4
   scipy==1.12.0
   statsmodels==0.14.1
   pingouin==0.5.3
   pytest==8.0.0
   pytest-cov==4.1.0
   ```

## Running the Experiment Interface

1. **Start the Streamlit app**:
   ```bash
   streamlit run code/experiment/app.py
   ```

2. **Recruit participants**:
   - Share the app URL (hosted on Streamlit Cloud or a local server) with participants via Prolific/MTurk.
   - Participants will be randomly assigned to High Agency, Low Agency, or Control conditions.
   - The interface includes:
     - **Manipulation Check**: Post-task survey asking "How much control did you feel you had?"
     - **Debriefing**: "Did you believe the sliders changed the recommendation?"

3. **Export data**:
   - After each session, data is automatically appended to `data/raw/participant_session.csv`.
   - To manually export: Click the "Export Data" button in the app.

## Running the Analysis Pipeline

1. **Clean the data**:
   ```bash
   python code/analysis/data_cleaning.py --attention-threshold 0.80 --time-threshold 60
   ```
   - This generates `data/processed/cleaned_participants.csv`.
   - **Note**: Adherence rate is NOT used as a filter.

2. **Run One-Way ANOVA and Planned Contrasts**:
   ```bash
   python code/analysis/contrasts.py
   ```
   - Outputs planned contrast results to `data/processed/analysis_results.json`.

3. **Run pairwise comparisons with Tukey HSD**:
   ```bash
   python code/analysis/pairwise.py
   ```
   - Outputs pairwise comparisons with adjusted p-values.

4. **Calculate effect sizes**:
   ```bash
   python code/analysis/effect_sizes.py
   ```
   - Outputs Cohen's d for all pairwise comparisons.

5. **Run sensitivity analysis**:
   ```bash
   python code/analysis/sensitivity.py --attention-thresholds 0.75 0.80 0.85 0.90 --time-thresholds 60 90 120
   ```
   - Sweeps attention and completion time thresholds and reports stability of primary findings.

6. **Generate final report**:
   ```bash
   python code/analysis/report.py
   ```
   - Outputs `docs/report.md` with all results, figures, and interpretations.

## Running Tests

1. **Unit tests**:
   ```bash
   pytest code/experiment/tests/ -v
   pytest code/analysis/tests/ -v
   ```

2. **Coverage report**:
   ```bash
   pytest --cov=code --cov-report=html
   ```
   - Opens `htmlcov/index.html` in a browser.

## Reproducibility Check

1. **Reset environment**:
   ```bash
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Re-run analysis**:
   ```bash
   python code/analysis/data_cleaning.py --attention-threshold 0.80 --time-threshold 60
   python code/analysis/contrasts.py
   python code/analysis/pairwise.py
   python code/analysis/effect_sizes.py
   python code/analysis/sensitivity.py --attention-thresholds 0.75 0.80 0.85 0.90 --time-thresholds 60 90 120
   python code/analysis/report.py
   ```

3. **Verify checksums**:
   ```bash
   sha256sum data/raw/participant_session.csv
   sha256sum data/processed/cleaned_participants.csv
   ```
   - Compare checksums with those recorded in `state/projects/PROJ-286-*.yaml`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure virtual environment is activated and dependencies are installed. |
| `Streamlit app crashes` | Check `data/raw/` for valid CSV files; ensure `participant_id` is unique. |
| `Power analysis fails` | Verify sample size in `data/processed/cleaned_participants.csv` is sufficient. |
| `Sensitivity analysis hangs` | Reduce the number of thresholds tested (e.g., `--attention-thresholds 0.80 0.85 0.90`). |

## Next Steps

1. **Recruit participants** via Prolific/MTurk until the target sample size (from power analysis) is reached.
2. **Run the full analysis pipeline** on collected data.
3. **Validate reproducibility** by re-running the pipeline on a fresh GitHub Actions runner.
4. **Submit findings** for review; advance to `research_accepted` if all gates pass.