# Quickstart Guide: Impact of Nostalgia on Cognitive Flexibility

This guide provides instructions for setting up the environment and running the ingestion pipeline on a sample dataset.

## Prerequisites

- Python 3.9+
- pip (Python package manager)
- Access to the internet (for fetching the dataset)

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
 ```bash
 pip install -r requirements.txt
 ```

 The `requirements.txt` file includes:
 - `pandas`, `numpy`, `scipy`, `statsmodels` (for data processing and analysis)
 - `openml`, `datasets` (for data fetching)
 - `pyyaml`, `requests` (for configuration and HTTP requests)
 - `pytest`, `black`, `ruff` (for testing and linting)

## Project Structure

The project follows this directory structure:

```
.
├── code/ # Source code for ingestion, analysis, and utilities
├── data/
│ ├── raw/ # Raw fetched datasets
│ ├── processed/ # Cleaned and filtered datasets
│ ├── results/ # Statistical reports and analysis outputs
│ └── stimuli/ # Stimulus files (audio clips)
├── contracts/ # JSON/YAML schemas for data validation
├── specs/ # Feature specifications and documentation
├── tests/ # Unit and integration tests
└── paper/ # Drafts and final paper
```

## Running the Ingestion Pipeline (Hello World)

The ingestion pipeline fetches a real dataset, validates it, and saves the raw output.

### Step 1: Run the Ingestion Script

Execute the following command from the project root:

```bash
python code/ingestion.py
```

**What this does:**
- Fetches the canonical dataset (via OpenML or HuggingFace) defined in `code/ingestion/fetcher.py`.
- If the fetch fails, the script raises an exception (fails loudly) unless a fallback mechanism is triggered by `code/main.py`.
- Saves the raw dataset to `data/raw/raw_dataset.csv`.
- Generates `data/raw/metadata.json` with source information and checksums.

### Step 2: Verify the Output

Check that the following files were created:
- `data/raw/raw_dataset.csv`: Contains the raw fetched records.
- `data/raw/metadata.json`: Contains metadata about the dataset source and simulation mode status.

You can inspect the raw dataset using Python:

```python
import pandas as pd
df = pd.read_csv('data/raw/raw_dataset.csv')
print(df.head())
print(f"Total records: {len(df)}")
```

### Expected Output

If successful, you should see a DataFrame with columns including:
- `participant_id`
- `age`
- `stimulus_type`
- `perseverative_errors`
- `categories_completed`
- `MMSE` (optional)

## Next Steps

Once the ingestion pipeline is verified:

1. **Run Data Cleaning**: Execute age and score filtering tasks (`T012a`, `T012b`).
2. **Run Statistical Analysis**: Execute the analysis pipeline (`code/analysis.py`) to generate statistical reports.
3. **Run Sensitivity Analysis**: Execute sensitivity checks (`code/analysis.py` sensitivity functions).

## Troubleshooting

- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Fetch Errors**: If the dataset fetch fails, check your internet connection. The pipeline is designed to fail loudly if the real source is unreachable.
- **File Permissions**: Ensure you have write permissions to the `data/` directory.

## Configuration

Most configuration is handled via environment variables or `code/config.py`.
- `MMSE_THRESHOLD`: Default is 24. Can be overridden via `MMSE_THRESHOLD` env variable.
- `DATA_SOURCE`: Override the default data source if needed.

For advanced configuration, refer to `code/config.py`.