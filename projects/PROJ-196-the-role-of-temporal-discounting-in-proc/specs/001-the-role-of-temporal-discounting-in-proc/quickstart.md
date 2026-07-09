# Quickstart: The Role of Temporal Discounting in Procrastination on Cognitive Tasks

## 1. Prerequisites
- Python 3.11+
- pip / venv

## 2. Installation

```bash
# Navigate to project code directory
cd projects/PROJ-196-the-role-of-temporal-discounting-in-proc/code/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt** (Pinned for CPU compatibility):
```text
pandas==2.1.0
numpy==1.24.0
scipy==1.11.0
statsmodels==0.14.0
scikit-learn==1.3.0
pytest==7.4.0
```

## 3. Data Preparation
Since no verified real-world dataset exists for the specific variable combination, the pipeline includes a **Synthetic Data Generator** based on the DGP defined in `research.md`.

```bash
# Generate synthetic data (for initial testing)
# This creates data with a known ground truth interaction effect of a specified magnitude.
python code/ingestion.py --mode generate --n [N] --seed 42, where N represents a sufficiently large sample size to ensure statistical power for the study.
```

*Note: If you have real CSV/ARFF files, place them in `data/raw/` and run `python code/ingestion.py --mode load`. The pipeline will attempt to merge them, but full moderation analysis requires all three constructs.*

## 4. Running the Analysis

Execute the full pipeline (Ingestion → Modeling → Robustness):

```bash
python code/main.py
```

This will:
1.  Load/Generate data (with DGP ground truth if synthetic).
2.  Fit hyperbolic models for $k$.
3.  Run OLS moderation regression.
4.  Perform a sufficient number of bootstrap resamples.
5.  Generate `data/processed/analysis_results.json`.

## 5. Verification
Check the output JSON:
```bash
cat data/processed/analysis_results.json
```
Verify:
- `interaction_effect_size` is present.
- `dgp_recovery` (if synthetic) shows the 95% CI contains the ground truth (-3.0).
- `vif_scores` are all < 5.
- `excluded_count` is < 10% of total sample.

## 6. Testing
Run the test suite to ensure data integrity and model assumptions:
```bash
pytest tests/ -v
```