# Quick Start Guide: The Impact of Nostalgia on Cognitive Flexibility

This guide provides instructions to set up the environment and run the ingestion pipeline for the "Impact of Nostalgia on Cognitive Flexibility in Aging Adults" project.

## Prerequisites

- Python 3.9 or higher
- `pip` package manager
- Git (for cloning the repository)

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. **Create a virtual environment** (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 Ensure you are in the project root directory.
 ```bash
 pip install -r requirements.txt
 ```
 *Note: `requirements.txt` includes pandas, scipy, statsmodels, numpy, pyyaml, openml, datasets, requests, pytest, black, and ruff.*

4. **Verify installation**:
 Ensure all required Python packages are installed:
 ```bash
 python -c "import pandas; import scipy; import statsmodels; print('Dependencies OK')"
 ```

## Running the Ingestion Pipeline (Hello World)

This project is designed to ingest real-world data or fall back to a methodological simulation if real data is unavailable.

### Step 1: Ensure Directory Structure
The pipeline expects specific directories. Run the setup script to create them:
```bash
python code/setup_dirs.py
```
*This creates `data/raw/`, `data/processed/`, `data/results/`, `data/stimuli/`, `contracts/`, `code/`, `tests/`, and `paper/`.*

### Step 2: Run the Orchestration Script
Execute the main pipeline to fetch data (or generate simulation data), validate, and clean the dataset.

```bash
python code/main.py
```

**Expected Behavior:**
- The script attempts to fetch real data from the configured source (OpenML/HuggingFace).
- If real data fetch fails, it automatically triggers `generate_simulation_data()` to create a valid synthetic dataset for testing purposes.
- It filters for participants aged ≥ 65.
- It validates cognitive metrics (Perseverative Errors, Categories Completed).
- It generates a `cleaned_dataset.csv` in `data/processed/`.

### Step 3: Verify Outputs
After successful execution, check the following files:

1. **Raw Data**: `data/raw/raw_dataset.csv` (or simulation equivalent)
2. **Cleaned Data**: `data/processed/cleaned_dataset.csv`
3. **Exclusion Log**: `data/processed/exclusion_log.json` (details on filtering steps)
4. **Metadata**: `data/raw/metadata.json` (includes source info and simulation flags)

```bash
# Example: View the first few lines of the cleaned dataset
head data/processed/cleaned_dataset.csv
```

## Next Steps

Once the ingestion pipeline is verified, proceed to **User Story 2 (Statistical Analysis)**:

```bash
python code/analysis.py
```

This will run Welch's t-tests, calculate effect sizes, and generate the `statistical_report.json` in `data/results/`.

## Troubleshooting

- **Import Errors**: Ensure you are using the virtual environment activated in Step 2.
- **Missing Directories**: Run `python code/setup_dirs.py` again.
- **Data Fetch Failures**: The pipeline is designed to handle this by generating simulation data. Check `data/raw/metadata.json` for the `simulation_mode` flag. If you require strictly real data, ensure network access to the configured data source is available.