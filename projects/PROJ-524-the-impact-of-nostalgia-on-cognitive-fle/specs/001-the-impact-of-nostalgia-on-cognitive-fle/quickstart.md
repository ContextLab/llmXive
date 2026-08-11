# Quickstart Guide: The Impact of Nostalgia on Cognitive Flexibility

This guide provides instructions for setting up the environment, installing dependencies, and running the data ingestion pipeline on a sample dataset.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Git (optional, for cloning the repository)

## Installation

1. **Clone the repository** (if applicable):
 ```bash
 git clone <repository-url>
 cd PROJ-524-the-impact-of-nostalgia-on-cognitive-fle
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

 The `requirements.txt` file includes the following pinned versions:
 - pandas
 - scipy
 - statsmodels
 - numpy
 - pyyaml
 - openml
 - datasets
 - requests
 - pytest
 - black
 - ruff

4. **Verify linting configuration**:
 Ensure `pyproject.toml` exists and contains valid configuration sections for `black` and `ruff`. You can verify this by running:
 ```bash
 python code/task_t003b_verify_pyproject.py
 ```

## Directory Structure Setup

The pipeline requires specific directories for data storage. Run the following script to create them:

```bash
python code/setup_dirs.py
```

This creates:
- `data/raw/`
- `data/processed/`
- `data/results/`
- `data/stimuli/`
- `contracts/`
- `code/`
- `tests/`
- `paper/`

## Hello World: Running the Ingestion Pipeline

This example demonstrates how to run the data ingestion pipeline on a sample dataset.

### Step 1: Fetch Data

The ingestion pipeline will attempt to fetch real data from OpenML or HuggingFace. If no valid real dataset is found, it will generate a deterministic synthetic dataset for validation purposes.

Run the main ingestion script:

```bash
python code/ingestion.py
```

**What this does:**
- Searches for datasets containing keywords "WCST", "cognitive", "aging", or "executive function".
- Fetches the dataset and saves it to `data/raw/raw_dataset.csv`.
- Validates the schema for required fields: `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`.
- Sets `simulation_mode` in `data/raw/metadata.json` if a fallback synthetic dataset is used.

### Step 2: Validate and Clean Data

The pipeline automatically validates and filters the data:
- Excludes records where `age < 65`.
- Excludes records with missing `stimulus_type` or cognitive metrics.
- Optionally excludes records where `MMSE < 24` (if the `MMSE` column is present).

The cleaned dataset is saved to `data/processed/cleaned_dataset.csv`.

### Step 3: Review Outputs

After the pipeline completes, review the following generated files:

- **`data/raw/metadata.json`**: Contains dataset source information and simulation mode flag.
- **`data/processed/exclusion_log.json`**: Logs the count of excluded records and reasons.
- **`data/processed/validity_metrics.json`**: Shows the percentage of valid records.
- **`data/processed/cleaned_dataset.csv`**: The final cleaned dataset ready for analysis.

## Next Steps

Once the ingestion pipeline is successfully run, you can proceed to:

1. **Statistical Analysis** (User Story 2): Run `code/analysis.py` to perform Welch's t-tests and calculate effect sizes.
2. **Sensitivity Analysis** (User Story 3): Run sensitivity sweeps to check robustness against different thresholds.
3. **Generate Final Report**: Compile results into `paper/001_results.md`.

## Troubleshooting

- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Data Fetch Failures**: If the pipeline cannot fetch real data, it will fall back to a deterministic synthetic dataset and set `simulation_mode=True` in `data/raw/metadata.json`.
- **Schema Validation Errors**: Check that the input dataset contains all required fields as defined in `contracts/dataset.schema.yaml`.

## Configuration

Environment variables can be used to customize the pipeline:
- `MMSE_THRESHOLD`: Minimum MMSE score for inclusion (default: 24).
- `DATA_SOURCE_URL`: Custom URL for data fetching.
- `LOG_LEVEL`: Logging verbosity (default: INFO).

Set these variables before running the pipeline:
```bash
export MMSE_THRESHOLD=26
python code/ingestion.py
```

## Support

For issues or questions, refer to the project documentation or open an issue in the repository.