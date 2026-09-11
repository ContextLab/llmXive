# Quickstart Guide: The Impact of Nostalgia on Cognitive Flexibility

This guide provides instructions to set up the environment, install dependencies, and run the data ingestion pipeline on a sample dataset.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- A virtual environment (recommended)

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd PROJ-524-the-impact-of-nostalgia-on-cognitive-fle
 ```

2. **Create and activate a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 Ensure you are in the project root directory, then run:
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

4. **Verify installation**:
 ```bash
 python -c "import pandas; import scipy; import openml; print('Dependencies installed successfully.')"
 ```

## Project Structure

Ensure the following directory structure exists. If not, run the setup task `T001` (create directories):

```
.
├── code/
├── data/
│ ├── raw/
│ ├── processed/
│ ├── results/
│ └── stimuli/
├── contracts/
├── specs/001-nostalgia-cognitive-flexibility/
├── tests/
└── paper/
```

## Hello World: Run the Ingestion Pipeline

This example demonstrates how to run the data ingestion pipeline on a sample dataset. The pipeline will:
1. Attempt to fetch real data from OpenML or HuggingFace.
2. If no valid real dataset is found, it will generate a deterministic synthetic dataset for validation.
3. Validate the schema and apply initial filters (age ≥ 65).
4. Save the cleaned dataset and exclusion logs.

### Step 1: Ensure Directories and Configuration

Run the directory setup script (if not already done):
```bash
python code/setup_dirs.py
```

### Step 2: Run the Ingestion Pipeline

Execute the main ingestion script:
```bash
python code/ingestion.py
```

**What happens:**
- The script searches for datasets containing keywords like "WCST", "cognitive", "aging", or "executive function".
- If a match is found, it downloads the data to `data/raw/raw_dataset.csv`.
- If no match is found, it generates a synthetic fallback dataset and sets `simulation_mode=True` in `data/raw/metadata.json`.
- The script filters records where `age >= 65` and logs exclusions to `data/processed/exclusion_log.json`.
- The cleaned dataset is saved to `data/processed/cleaned_dataset_intermediate.csv`.

### Step 3: Verify Outputs

Check the generated files:

- **Raw Data**: `data/raw/raw_dataset.csv`
- **Metadata**: `data/raw/metadata.json` (includes `simulation_mode` flag)
- **Exclusion Log**: `data/processed/exclusion_log.json` (details of excluded records)
- **Cleaned Data**: `data/processed/cleaned_dataset_intermediate.csv`

Example check:
```bash
cat data/raw/metadata.json
```

You should see an entry like:
```json
{
 "dataset_source": "...",
 "simulation_mode": true,
 "stimuli_checksums": null
}
```

## Next Steps

- **Data Validation**: Run `code/task_t012d_mmse_exclusion.py` to handle MMSE filtering.
- **Statistical Analysis**: Once data is cleaned, proceed to User Story 2 (`code/analysis.py`) for statistical testing.
- **Testing**: Run the test suite with `pytest tests/` to ensure all components are functioning correctly.

## Troubleshooting

- **Missing Dependencies**: Re-run `pip install -r requirements.txt`.
- **Directory Errors**: Ensure `data/` and subdirectories exist. Run `python code/setup_dirs.py`.
- **Data Fetch Failures**: The pipeline will automatically fall back to synthetic data and log `SIMULATION_FALLBACK`. Check `data/processed/exclusion_log.json` for details.

For more details, refer to the full documentation in `paper/` or the `README.md`.