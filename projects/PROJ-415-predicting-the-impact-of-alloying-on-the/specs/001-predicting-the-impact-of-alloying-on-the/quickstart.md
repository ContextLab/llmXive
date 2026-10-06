# Quickstart: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Prerequisites

-   Python 3.11+
-   Git
-   Access to a GitHub Actions runner (or local environment for testing)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <project-dir>
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

## Running the Pipeline

### Step 1: Data Ingestion & Curation
This step attempts to download the verified dataset. **If no valid FCC self-diffusion data is found, the pipeline halts.**

```bash
python code/main.py --step ingest
```

*Expected Output*:
-   `data/curated/filtered.csv` (if data found)
-   `data/curated/data_provenance.json`
-   **OR** `ERROR: No verified real dataset found...` (if data missing)

### Step 2: Feature Engineering
Calculates atomic descriptors and size mismatch.

```bash
python code/main.py --step features
```

*Expected Output*: `data/curated/features.csv`, `errors/missing_atomic_data.csv` (if any).

### Step 3: Model Training
Trains RF, GB, and Linear models with Grid Search.

```bash
python code/main.py --step train
```

*Expected Output*: `models/final_rf.pkl`, `models/final_gb.pkl`, `models/linear_coef.json`.

### Step 4: Validation & Reporting
Performs nested CV, sensitivity analysis, and generates the final report.

```bash
python code/main.py --step validate
```

*Expected Output*: `reports/validation_report.json`, `reports/sensitivity_plot.png`.

## Verification

To verify the pipeline on a local machine:
```bash
pytest tests/
```

## Troubleshooting

-   **"No verified real dataset found"**: This is expected behavior if the verified dataset list does not contain FCC metal diffusion data. The pipeline is designed to halt rather than use synthetic data.
-   **Missing Atomic Radius**: Check `errors/missing_atomic_data.csv` for the solute causing the issue.
-   **Memory Error**: Ensure the dataset size is < 10 MB. If streaming is required, verify `streaming=True` is used in `code/data/ingestion.py`.
