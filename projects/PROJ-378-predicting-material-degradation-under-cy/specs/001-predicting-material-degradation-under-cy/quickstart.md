# Quickstart: Predicting Material Degradation Under Cyclic Loading

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to the GitHub Actions runner (or local environment with sufficient RAM)

## Installation

1.  **Clone the repository** (or navigate to the project directory):
    ```bash
    cd projects/PROJ-378-predicting-material-degradation-under-cy
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is designed to run end-to-end. Due to the **absence of verified material fatigue data**, the pipeline will perform a data availability check and report a "Coverage Gap" before proceeding to modeling.

### Step 1: Data Ingestion & Validation

Run the ingestion script to attempt loading verified datasets:

```bash
python code/main.py
```

**Expected Output**:
- Logs showing attempts to load NIST/UCI datasets.
- A critical error message: `CRITICAL: Required columns (stress_amplitude, composition) not found in verified datasets. Pipeline halted.`
- A `gap_report.json` file generated in `data/processed/`.
- Exit code: `2` (Data Unavailable).

### Step 2: (Skipped) Preprocessing & Modeling

If the data validation passes (which it will not in this specific configuration), the following commands would run:

```bash
# Preprocessing (Imputation)
python code/preprocessing/impute.py

# Training
python code/modeling/train.py

# Inference & Uncertainty
python code/modeling/inference.py
```

### Step 3: Viewing Results

If the pipeline completes successfully (hypothetically), results would be in:
- `data/processed/unified_dataset.csv`
- `results/model_metrics.json`
- `results/prediction_intervals.csv`

**Current Status**: The pipeline halts at Step 1 due to the lack of verified material science datasets in the allowed source list. The `gap_report.json` will document this failure.

## Troubleshooting

- **Missing Dependencies**: Ensure `requirements.txt` is installed.
- **Memory Errors**: The pipeline automatically subsamples if RAM usage exceeds 7 GB (FR-007).
- **Data Gap**: If you see "Coverage Gap", it means no verified dataset contains the required material fatigue variables. This is an expected outcome given the current "Verified datasets" block.

## Next Steps

To enable the scientific analysis:
1.  A verified URL for a material fatigue dataset (e.g., from Materials Project, NIST Materials Data Repository) must be added to the "Verified datasets" block.
2.  Once a verified URL is available, re-run the pipeline to proceed beyond the ingestion step.