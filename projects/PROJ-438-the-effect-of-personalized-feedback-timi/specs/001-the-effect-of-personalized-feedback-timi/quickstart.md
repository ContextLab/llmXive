# Quickstart: The Effect of Personalized Feedback Timing on Skill Acquisition

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for downloading OULAD data)

## Installation

1. **Clone the repository** (or navigate to the project directory).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

The full pipeline can be executed end-to-end via the main script:

```bash
python code/main.py
```

This will:
1. Download data from the verified OULAD sources.
2. Preprocess and filter records.
3. Calculate feedback intervals and bin learners.
4. Fit the Cluster-Robust OLS model.
5. Perform Tukey HSD post-hoc tests.
6. Run the sensitivity analysis sweep.
7. Save all artifacts to `data/processed/`.

### Running Individual Steps

- **Download Data**: `python code/download.py`
- **Preprocess**: `python code/preprocess.py`
- **Model & Test**: `python code/modeling.py`
- **Sensitivity**: `python code/sensitivity.py`

## Validating Results

After running the pipeline, verify the existence of the required artifacts:

```bash
ls -lh data/processed/
# Expected:
# - learners_raw.csv
# - learners_binned.csv
# - results_metrics.csv
# - significance_stability_report.csv
```

Run the test suite to ensure logic correctness:

```bash
pytest tests/ -v
```

## Reproducibility

To ensure reproducibility:
- Random seeds are set in `code/main.py` (default: 42).
- Data sources are hardcoded to the verified URLs in `code/download.py`.
- All outputs are deterministic given the same input data.
