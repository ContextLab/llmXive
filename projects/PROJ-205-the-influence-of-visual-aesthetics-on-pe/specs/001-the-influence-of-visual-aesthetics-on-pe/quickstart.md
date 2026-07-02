# Quickstart: The Influence of Visual Aesthetics on Perceived Credibility of Online Information

## Prerequisites

-   Python 3.11+
-   `pip` or `conda`
-   Git

## 1. Environment Setup

Clone the repository and install dependencies:

```bash
cd projects/PROJ-205-the-influence-of-visual-aesthetics-on-pe
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r code/requirements.txt
```

*Note: `requirements.txt` will pin versions for `streamlit`, `pandas`, `numpy`, `scipy`, `statsmodels`.*

## 2. Running the Survey (Data Collection)

To simulate the survey for testing (US-0, US-1):

```bash
cd code/survey
streamlit run app.py
```

1.  **Consent**: Verify the IRB consent form appears.
2.  **Stimuli**: Confirm that multiple stimuli load in a Latin Square order.
3.  **Ratings**: Submit ratings for credibility and professionalism.
4.  **Validation**: Attempt to submit with missing ratings (should fail).

*To run in production (GitHub Actions):*
The `survey/app.py` is configured to log data to `data/raw/participants.csv` upon submission.

## 3. Running the Analysis Pipeline

Once data is collected (or using a sample dataset):

```bash
cd code/analysis

# Step 1: Run Repeated-Measures ANOVA (or Friedman if assumptions violated)
python 01_anova.py --input ../../data/raw/participants.csv --output ../../data/processed/anova_results.json

# Step 2: Run Pairwise Comparisons (if ANOVA significant)
python 02_pairwise.py --input ../../data/raw/participants.csv --output ../../data/processed/pairwise_results.json

# Step 3: Run Mixed-Effects Robustness Check
python 03_mixed_effects.py --input ../../data/raw/participants.csv --output ../../data/processed/mixed_effects_results.json
```

## 4. Verification

-   Check `data/processed/` for JSON result files.
-   Verify `anova_results.json` contains F-statistic, p-value, and partial $\eta^2$.
-   Verify `pairwise_results.json` contains Bonferroni-adjusted p-values.
-   Verify `mixed_effects_results.json` contains coefficients for age and education.

## 5. Troubleshooting

-   **Missing Stimuli**: Ensure `code/stimuli/` contains all HTML files and `text_content.txt`.
-   **Data Format Error**: Ensure `participants.csv` has headers matching the Raw Data Schema.
-   **Memory Error**: If running on CI, ensure data is subset to < 7GB RAM (expected for N=250).