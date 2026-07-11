# Quickstart Guide

This guide provides step-by-step instructions for setting up the environment and running the first task for the **Predicting Molecular Halide Binding Affinities** project.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## 1. Project Setup

Ensure you are in the project root directory:
```bash
cd projects/PROJ-446-predicting-molecular-halide-binding-affi
```

## 2. Environment Setup

### Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies

Install the required Python packages defined in `code/requirements.txt`:

```bash
pip install -r code/requirements.txt
```

This will install:
- `scikit-learn`: For machine learning models
- `rdkit`: For molecular descriptor generation
- `pandas` & `numpy`: For data manipulation
- `requests` & `beautifulsoup4`: For web scraping
- `pyyaml`: For configuration handling
- `pytest`: For testing

## 3. Running the First Task

The first executable task in the pipeline is the **Data Ingestion** step (User Story 1). This task scrapes data, validates it, and prepares it for downstream modeling.

### Run the Data Pipeline

Execute the following command from the project root:

```bash
python code/01_data_ingestion.py
```

**What this does:**
1. Attempts to scrape experimental halide binding data from NIST/PubChem.
2. Validates and cleans the data (parsing SMILES, standardizing units).
3. Filters for hosts with measurements across multiple halides.
4. **Fallback:** If insufficient real data is found (<50 hosts), it automatically triggers the simulated data fallback mechanism as per the project specifications.
5. Outputs the processed dataset to `data/processed/halide_binding_data.csv` (or creates simulated data files if required).

### Expected Output

Upon successful completion, you should see:
- Console logs indicating the number of records processed.
- A new file at `data/processed/halide_binding_data.csv` (if real data was sufficient) OR
- Files in `data/simulated/` and a state flag indicating simulated mode was activated.

## 4. Verification

To verify the data pipeline ran correctly:

1. Check the log files in the `logs/` directory (if logging is configured).
2. Inspect the output CSV:
 ```bash
 head data/processed/halide_binding_data.csv
 ```
3. If simulated mode was triggered, check the state file:
 ```bash
 cat data/simulated/state.json
 ```

## Next Steps

Once the data pipeline is complete, proceed to **User Story 2** (Model Training) by running:
```bash
python code/03_model_training.py
```