# Quick Start Guide: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

This guide provides installation instructions and a "Hello World" example to run the data ingestion pipeline on a sample dataset.

## Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- A Unix-like environment (Linux/macOS) or WSL on Windows

## Installation

1. **Clone the repository** (if not already done):
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
 Ensure you have the `requirements.txt` file populated with the necessary packages.
 ```bash
 pip install -r requirements.txt
 ```

 *Note: The `requirements.txt` should include: pandas, scipy, statsmodels, numpy, pyyaml, openml, datasets, requests, pytest, black, ruff.*

4. **Verify directory structure**:
 Ensure the following directories exist. If not, run the setup script:
 ```bash
 python code/setup_dirs.py
 ```
 Expected directories:
 - `data/raw/`
 - `data/processed/`
 - `data/results/`
 - `data/stimuli/`
 - `contracts/`
 - `code/`
 - `tests/`
 - `paper/`

## Running the Ingestion Pipeline (Hello World)

This example demonstrates how to run the ingestion pipeline. The pipeline will attempt to fetch real data from the canonical source (OpenML or HuggingFace). If real data is unavailable, it will fall back to generating simulation data as per the project's Methodological Simulation protocol.

### Step 1: Run the Orchestration Script

Execute the main pipeline script:

```bash
python code/main.py
```

**What this does:**
1. Attempts to fetch real data from the configured source.
2. If real data fetch fails, it triggers the simulation fallback (`code/task_t010d_generate_simulation.py`).
3. Validates the schema of the raw data.
4. Filters and cleans the data (age >= 65, score validation).
5. Generates the final cleaned dataset and exclusion logs.

### Step 2: Verify Output

After the script completes successfully, verify the generated artifacts in the `data/` directory:

- **Raw Data**: `data/raw/raw_dataset.csv` (or `data/raw/metadata.json` if simulation mode)
- **Processed Data**:
 - `data/processed/cleaned_age_filtered.csv`
 - `data/processed/cleaned_score_filtered.csv`
 - `data/processed/cleaned_dataset.csv` (Primary)
 - `data/processed/cleaned_dataset_no_mmse.csv` (Robustness)
 - `data/processed/final_cleaned_dataset.csv`
- **Logs & Metadata**:
 - `data/raw/metadata.json`
 - `data/processed/exclusion_counts.json`
 - `data/processed/exclusion_log.json`
 - `data/processed/mmse_flag.json`

### Expected Console Output

You should see log messages indicating the pipeline stages:
```text
INFO: Fetching data...
INFO: Data fetched successfully.
INFO: Validating schema...
INFO: Schema valid.
INFO: Filtering by age...
INFO: Filtering by score...
INFO: Processing MMSE flags...
INFO: Pipeline completed successfully.
```

If real data is unavailable, you will see:
```text
INFO: Real data fetch failed. Falling back to simulation.
INFO: Generating synthetic WCST data...
INFO: Simulation data saved to data/raw/raw_dataset.csv
```

## Next Steps

- **Statistical Analysis**: Once the ingestion pipeline is complete, proceed to User Story 2 to run the statistical analysis (`code/analysis.py`).
- **Sensitivity Analysis**: Run User Story 3 for robustness checks.
- **Report Generation**: Review the generated reports in `data/results/`.

## Troubleshooting

- **Missing Dependencies**: If you encounter `ModuleNotFoundError`, ensure all packages in `requirements.txt` are installed.
- **Data Fetch Errors**: If the pipeline fails to fetch real data and simulation is not desired, check your internet connection and the canonical source configuration in `code/config.py`.
- **Schema Validation Errors**: Ensure the input data (or simulation output) matches the schema defined in `contracts/dataset.schema.yaml`.

## Support

For issues or questions, refer to the project's `README.md` or open an issue in the repository.