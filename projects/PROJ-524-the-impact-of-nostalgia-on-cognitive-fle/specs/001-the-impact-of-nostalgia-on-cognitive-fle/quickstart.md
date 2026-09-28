# Quickstart Guide: The Impact of Nostalgia on Cognitive Flexibility

This guide provides instructions for setting up the environment and running the ingestion pipeline on a sample dataset to verify the system's functionality.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- A Unix-like environment (Linux or macOS) or WSL on Windows

## Installation

1. **Clone the repository** and navigate to the project root:
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

4. **Verify configuration**:
 Ensure `pyproject.toml` exists and contains the required `[tool.black]` and `[tool.ruff]` sections. You can verify this by running:
 ```bash
 python code/task_t003b_verify_pyproject.py
 ```

## Running the "Hello World" Ingestion Pipeline

This example runs the ingestion pipeline to fetch data (or fall back to synthetic data if the canonical source is unreachable), validate the schema, and produce a cleaned dataset.

### Step 1: Setup Directories and Contracts

Before running the pipeline, ensure the required directory structure and contract schemas are in place.

```bash
python code/setup_dirs.py
python code/setup_contracts.py
```

### Step 2: Run the Ingestion Pipeline

Execute the main ingestion script. This script will:
- Attempt to fetch data from the canonical source (OpenML or HuggingFace).
- If the fetch fails, it will trigger the "Methodological Simulation" fallback to generate a synthetic dataset compliant with the schema.
- Validate the data against the schema (`contracts/dataset.schema.yaml`).
- Filter for participants aged 65+.
- Save the raw and cleaned datasets to `data/raw/` and `data/processed/`.

```bash
python code/ingestion.py
```

**Expected Output**:
- `data/raw/raw_dataset.csv`: The raw dataset (fetched or synthetic).
- `data/raw/metadata.json`: Metadata including `simulation_mode` flag.
- `data/processed/cleaned_dataset.csv`: The final cleaned dataset.
- Console logs detailing the fetch attempt, validation results, and exclusion counts.

### Step 3: Verify Results

After the pipeline completes, verify the output files exist and contain valid data:

```bash
# Check raw data
head data/raw/raw_dataset.csv

# Check cleaned data
head data/processed/cleaned_dataset.csv

# Check metadata
cat data/raw/metadata.json
```

If `simulation_mode` is `true` in `metadata.json`, the system used the fallback synthetic data generation because the real source was unreachable. This is expected behavior for the "Hello World" test in an isolated environment.

## Next Steps

Once the ingestion pipeline is verified, proceed to **User Story 2** (Statistical Analysis) by running the analysis module:

```bash
python code/analysis.py
```

For detailed information on the statistical methods, data model, and full API reference, consult the `specs/` directory and the `paper/` folder.

## Troubleshooting

- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Schema Errors**: If validation fails, check `contracts/dataset.schema.yaml` and ensure the input data matches the required fields (`participant_id`, `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`).
- **Permission Errors**: Ensure write permissions for `data/` and `code/` directories.