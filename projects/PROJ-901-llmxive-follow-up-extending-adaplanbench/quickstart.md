# Quickstart Guide: llmXive AdaPlanBench Extension

This guide provides setup instructions, dependency installation, and execution steps to validate the project structure and produce the required research artifacts.

## Prerequisites

- Python 3.9+
- pip
- git

## Setup

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repo-url>
 cd projects/PROJ-901-llmxive-follow-up-extending-adaplanbench
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: If `code/requirements.txt` does not exist, create it with the following:*
 ```text
 transformers
 datasets
 pandas
 statsmodels
 scikit-learn
 pytest
 pyyaml
 torch
 ```

4. **Ensure directory structure**:
 ```bash
 python code/setup_dirs.py
 ```

## Execution Steps

The following steps must be run in order to generate the required artifacts.

### Step 1: Load and Filter Dataset (US1)

This step fetches the AdaPlanBench dataset, filters for tasks with >=5 progressive constraints, and saves the result.

```bash
python code/dataset/loader.py --filter-min-constraints 5 --output data/processed/filtered_tasks.csv
```

*Expected Output*: `data/processed/filtered_tasks.csv` containing filtered tasks.

### Step 2: Add Constraint Count Metadata (US1)

This step adds the `constraint_count` column to the filtered dataset.

```bash
python code/dataset/add_constraint_count.py --input data/processed/filtered_tasks.csv --output data/processed/filtered_tasks.csv
```

*Expected Output*: `data/processed/filtered_tasks.csv` updated with `constraint_count` column.

### Step 3: Validate Subset (US1)

```bash
python code/dataset/validate_subset.py --input data/processed/filtered_tasks.csv
```

### Step 4: Generate Annotation Sample (US3)

```bash
python code/dataset/annotator.py --input data/processed/filtered_tasks.csv --output data/processed/annotation_sample.csv
```

*Expected Output*: `data/processed/annotation_sample.csv` with 50 stratified samples.

### Step 5: Run Monolithic Agent (US2)

```bash
python code/agent/monolithic_runner.py --input data/processed/filtered_tasks.csv --output data/processed/monolithic_logs.json
```

*Expected Output*: `data/processed/monolithic_logs.json`.

### Step 6: Run Dual-Track Agent (US2)

```bash
python code/agent/dual_track_runner.py --input data/processed/filtered_tasks.csv --output data/processed/dual_track_logs.json
```

*Expected Output*: `data/processed/dual_track_logs.json`.

### Step 7: Aggregate Execution Logs (US2)

```bash
python code/analysis/log_aggregator.py --monolithic data/processed/monolithic_logs.json --dual-track data/processed/dual_track_logs.json --output data/processed/execution_traces.csv
```

*Expected Output*: `data/processed/execution_traces.csv`.

### Step 8: Power Analysis (US3)

```bash
python code/analysis/power.py --input data/processed/filtered_tasks.csv --output data/processed/power_report.json
```

*Expected Output*: `data/processed/power_report.json`.

### Step 9: GLMM Analysis (US3)

```bash
python code/analysis/glmm.py --input data/processed/execution_traces.csv --output data/processed/statistical-results.json
```

*Expected Output*: `data/processed/statistical-results.json`.

### Step 10: Agreement Rate Analysis (US3)

```bash
python code/analysis/agreement_rate.py --traces data/processed/execution_traces.csv --annotations data/processed/annotation_sample.csv --output data/processed/agreement_rate_report.json
```

*Expected Output*: `data/processed/agreement_rate_report.json`.

### Step 11: Adherence Verification (US3)

```bash
python code/analysis/adherence_verifier.py --input data/processed/execution_traces.csv --output data/processed/adherence_verification.json
```

*Expected Output*: `data/processed/adherence_verification.json`.

## Validation

Run the quickstart validator to ensure all steps completed successfully:

```bash
python code/quickstart_validator.py
```

This script checks for the existence of all required output files and verifies basic schema compliance.

## Troubleshooting

- **Import Errors**: Ensure you are running scripts from the project root or that `code/` is in your `PYTHONPATH`.
- **Dataset Fetch Failures**: Check your internet connection. The loader will fail loudly if the dataset cannot be fetched from Hugging Face.
- **Memory Errors**: Reduce batch sizes in `code/config.py` if running out of RAM.

## Notes

- All data artifacts are written to `data/processed/`.
- Ensure `data/raw/` is empty or contains only the raw dataset cache if needed.
- Do not modify `data/processed/` files manually; regenerate them using the scripts above.